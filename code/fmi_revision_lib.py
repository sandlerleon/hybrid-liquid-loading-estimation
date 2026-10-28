# -*- coding: utf-8 -*-
"""Shared machinery for the revision experiments (Flow Measurement and Instrumentation, revision 1).

The original study (fmi_analysis.py, covariance_analysis.py) is kept exactly as submitted. Everything the
reviewers asked for is built on this module, which differs from the original in three structural ways:

  * Every random primitive is drawn once and re-used by every configuration that is compared (common random
    numbers), so a difference between two methods is a difference between methods and not between samples.
  * The truth-generating over-reading model and the correction model are separate arguments. The correction
    is always the Chisholm multiplier of Eq. (4); the truth can be Chisholm (matched), an independent
    published correlation, or a deliberately perturbed one.
  * The fusion rule is a parameter, so weighting rules and damping thresholds can be compared on equal terms.

With the baseline configuration this module reproduces the ablation of Table 3 to within Monte Carlo error
(check_baseline() in fmi_revision_analysis.py).
"""
import numpy as np
from swcl_physics import (BAR_PER_KGCM2, P_KGCM2, T_C, MW_GAS, RHO_L, gas_density,
                          phi_chisholm, phi_deleeuw)

D_LINE = 0.1541                      # m, 154 mm line (Table 2)
BASE = dict(s1=0.12,                 # thermodynamic flash, relative standard uncertainty
            s2=0.20,                 # diagnostic estimator, relative standard uncertainty
            s2t=0.06,                # diagnostic loop-to-site transfer bias, relative standard deviation
            p=0.25,                  # carryover prevalence
            carry=(0.15, 0.60),      # carryover fraction of the total liquid, uniform
            zmax=3.0,                # acceptance threshold on the consistency index
            k=1.0,                   # damping threshold of Eq. (12)
            sig_model=0.006,         # correlation residual after site calibration (systematic, Table 2)
            sig_base=0.007)          # dry-gas meter and secondary instrumentation


# ------------------------------------------------------------------------------------------ the sampled world
class World:
    """One set of sampled operating conditions and random primitives, shared by every configuration."""

    def __init__(self, n, seed):
        rng = np.random.default_rng(seed)
        self.n = n
        u = lambda: rng.random(n)
        z = lambda: rng.standard_normal(n)
        p_kg = P_KGCM2[0] + (P_KGCM2[1] - P_KGCM2[0]) * u()
        t_c = T_C[0] + (T_C[1] - T_C[0]) * u()
        self.rho_g, _ = gas_density(p_kg * BAR_PER_KGCM2 * 1e5, t_c + 273.15)
        self.rho_l = RHO_L[0] + (RHO_L[1] - RHO_L[0]) * u()
        cgr = 5.0 + 95.0 * u()
        m_l = cgr * 0.158987 * self.rho_l
        m_g = 28316.8 * (MW_GAS / 0.0224136)
        self.X = (m_l / m_g) * np.sqrt(self.rho_g / self.rho_l)
        v_sg = 8.0 + 10.0 * u()
        self.fr = (v_sg / np.sqrt(9.81 * D_LINE)) * np.sqrt(self.rho_g / (self.rho_l - self.rho_g))
        self.u_occ, self.u_mag = u(), u()           # carryover occurrence and magnitude
        self.z1, self.z2, self.zb = z(), z(), z()   # flash error, diagnostic error, transfer bias
        self.z_model, self.z_noise, self.z_rand = z(), z(), z()   # correlation residual, meter, random discrepancy
        self.z_rho = z()                            # independent part of a correlated diagnostic error
        self.cn = (self.rho_l / self.rho_g) ** 0.25 + (self.rho_g / self.rho_l) ** 0.25   # Chisholm C

    def carry(self, p, frac=BASE["carry"]):
        return np.where(self.u_occ < p, frac[0] + (frac[1] - frac[0]) * self.u_mag, 0.0)


def carry_variance(p, frac=BASE["carry"]):
    """Variance of the carryover fraction for a Bernoulli(p) x Uniform(a, b) mixture (the allowance of Eq. 8)."""
    m = 0.5 * (frac[0] + frac[1])
    return p * (1 - p) * m ** 2 + p * (frac[1] - frac[0]) ** 2 / 12.0


# ----------------------------------------------------------------------------------------------- estimators
def estimates(w, p=BASE["p"], p_declared=None, s1=BASE["s1"], s2=BASE["s2"], s2t=BASE["s2t"],
              s2_declared=None, s2t_declared=None, site_bias=None, rho=0.0, frac=BASE["carry"]):
    """E1 (thermodynamic) and E2 (diagnostic) with their declared standard uncertainties.

    p              true carryover prevalence;   p_declared  the prevalence the uncertainty budget assumes
    s2, s2t        actual diagnostic random uncertainty and transfer-bias spread
    s2_declared    declared values of the same (default: equal to the actual ones)
    site_bias      if given, the transfer bias is this fixed number for every realization (one site) instead of
                   being drawn per realization (a population of sites)
    rho            correlation between the random errors of the two estimators
    """
    p_declared = p if p_declared is None else p_declared
    s2_declared = s2 if s2_declared is None else s2_declared
    s2t_declared = s2t if s2t_declared is None else s2t_declared
    carry = w.carry(p, frac)
    X1 = np.clip(w.X * (1.0 - carry) * (1.0 + s1 * w.z1), 1e-5, None)
    u1 = np.sqrt(s1 ** 2 + carry_variance(p_declared, frac)) * X1
    u1_naive = s1 * X1
    e2 = rho * w.z1 + np.sqrt(max(0.0, 1.0 - rho ** 2)) * w.z2 if rho else w.z2
    b2 = (s2t * w.zb) if site_bias is None else np.full(w.n, float(site_bias))
    X2 = np.clip(w.X * (1.0 + b2) * (1.0 + s2 * e2), 1e-5, None)
    u2 = np.sqrt(s2_declared ** 2 + s2t_declared ** 2) * X2
    return dict(X1=X1, u1=u1, u1_naive=u1_naive, X2=X2, u2=u2, carry=carry)


# ---------------------------------------------------------------------------------------------- fusion rules
def fuse(X1, u1, X2, u2, rho=0.0, rule="cauchy", k=BASE["k"], birge=True):
    """Fused estimate, its declared uncertainty and the consistency index.

    Weights are the generalized-least-squares weights of Eq. (9); asymmetric damping (Eq. 12) multiplies the weight of
    the thermodynamic estimate by d and the weights are renormalized. The fused uncertainty is Eq. (10) evaluated with the
    renormalized weights, inflated by the Birge ratio max(1, Z).

      rule 'e1', 'e2'   one estimator alone
      rule 'gls'        symmetric: no damping
      rule 'cauchy'     one-sided Cauchy (Lorentzian) damping, d = 1/(1 + max(0, e - k)^2)    [Eq. 12]
      rule 'cauchy2'    the same damping applied to |e| (two-sided, a control)
      rule 'huber'      one-sided Huber damping, d = min(1, k/e) for e > k
      rule 'hard'       one-sided hard switch: E2 alone when e > k, GLS otherwise
    """
    c = rho * u1 * u2
    var_d = np.clip(u1 ** 2 + u2 ** 2 - 2 * c, 1e-18, None)
    sd = np.sqrt(var_d)
    Z = np.abs(X1 - X2) / sd
    e = (X2 - X1) / sd
    if rule == "e1":
        wt1 = np.ones_like(X1)
    elif rule == "e2":
        wt1 = np.zeros_like(X1)
    else:
        g1 = np.clip((u2 ** 2 - c) / var_d, 0.0, 1.0)
        if rule == "gls":
            d = 1.0
        elif rule == "cauchy":
            d = 1.0 / (1.0 + np.clip(e - k, 0.0, None) ** 2)
        elif rule == "cauchy2":
            d = 1.0 / (1.0 + np.clip(np.abs(e) - k, 0.0, None) ** 2)
        elif rule == "huber":
            d = np.where(e > k, k / np.clip(e, 1e-12, None), 1.0)
        elif rule == "hard":
            d = np.where(e > k, 0.0, 1.0)
        else:
            raise ValueError(rule)
        num = g1 * d
        wt1 = num / np.clip(num + (1.0 - g1), 1e-18, None)
    wt2 = 1.0 - wt1
    Xf = wt1 * X1 + wt2 * X2
    uf = np.sqrt(np.clip(wt1 ** 2 * u1 ** 2 + wt2 ** 2 * u2 ** 2 + 2 * wt1 * wt2 * c, 0, None))
    if birge:
        uf = uf * np.maximum(1.0, Z)
    return Xf, uf, Z, wt1


# ---------------------------------------------------------------------------------- over-reading and errors
def phi_true(w, model="chisholm", scale=1.0, rand=0.0):
    """True over-reading used to generate the simulated meter reading.

    chisholm   the matched case (the correction model itself)
    murdock    Murdock (1962) orifice correlation, phi = 1 + 1.26 X   (an independent published orifice correlation)
    deleeuw    de Leeuw (1997) Venturi form with its Froude-dependent exponent (a functional-form stress test: it is NOT
               a model of an orifice plate)
    scale      systematic multiplier on (phi - 1), a stress scenario (not a measured error bound)
    rand       relative standard deviation of a random multiplier on (phi - 1), realization to realization
    """
    if model == "chisholm":
        base = np.sqrt(1.0 + w.cn * w.X + w.X ** 2)
    elif model == "murdock":
        base = 1.0 + 1.26 * w.X
    elif model == "deleeuw":
        base = phi_deleeuw(w.X, w.rho_g, w.rho_l, w.fr)
    else:
        raise ValueError(model)
    return 1.0 + (base - 1.0) * scale * (1.0 + rand * w.z_rand)


def phi_corr(w, Xhat):
    """The correction model: Chisholm (Eq. 4) evaluated at the estimated liquid loading."""
    X = np.clip(Xhat, 1e-5, None)
    return np.sqrt(1.0 + w.cn * X + X ** 2)


def err(w, Xhat, truth, sig_model=BASE["sig_model"], sig_base=BASE["sig_base"]):
    """Relative error (%) of the corrected gas rate  (Eq. 13)."""
    return ((truth / phi_corr(w, Xhat)) * (1 + sig_model * w.z_model) * (1 + sig_base * w.z_noise) - 1.0) * 100.0


def err_uncorrected(w, truth):
    return (truth - 1.0) * 100.0


def sens_X(w, Xf):
    """Normalized sensitivity of the corrected rate to the liquid-loading estimate, S_X = -dlnphi/dlnX (Chisholm)."""
    X = np.clip(Xf, 1e-5, None)
    phi2 = 1.0 + w.cn * X + X ** 2
    return -X * (w.cn + 2 * X) / (2.0 * phi2)


def declared_u_rel(w, Xf, uf, u_form=0.0, sig_model=BASE["sig_model"], sig_base=BASE["sig_base"]):
    """Declared relative standard uncertainty of the corrected gas rate, first-order propagation:
    u_Q^2/Q^2 = S_X^2 (u_f/X_f)^2 + u_meter^2 + u_corr^2 + u_form^2   (inputs uncorrelated, see Section 3.5.2)."""
    S = sens_X(w, Xf)
    return np.sqrt(S ** 2 * (uf / np.clip(Xf, 1e-5, None)) ** 2 + sig_base ** 2 + sig_model ** 2 + u_form ** 2)


# ------------------------------------------------------------------------------------------------- metrics
def band95(e, mask=None):
    e = e if mask is None else e[mask]
    lo, hi = np.percentile(e, [2.5, 97.5])
    return float(max(abs(lo), abs(hi)))


def metrics(e, mask=None):
    e = e if mask is None else e[mask]
    return dict(n=int(e.size), bias=float(e.mean()), mae=float(np.abs(e).mean()), rmse=float(np.sqrt((e ** 2).mean())),
                maxabs=float(np.abs(e).max()), band95=band95(e))


def coverage(e, u_rel, mask=None, kcov=2.0):
    """Fraction of realizations whose error lies inside the declared +-kcov*u interval (percent units)."""
    if mask is not None:
        e, u_rel = e[mask], u_rel[mask]
    return float((np.abs(e) <= kcov * 100.0 * u_rel).mean())


def confusion(reject, positive):
    """Detector figures of merit; 'positive' = the condition to be detected (e.g. upstream carryover present)."""
    tp = int((reject & positive).sum()); fp = int((reject & ~positive).sum())
    fn = int((~reject & positive).sum()); tn = int((~reject & ~positive).sum())
    return dict(tp=tp, fp=fp, fn=fn, tn=tn,
                sensitivity=tp / max(tp + fn, 1), specificity=tn / max(tn + fp, 1),
                precision=tp / max(tp + fp, 1), fpr=fp / max(fp + tn, 1),
                accuracy=(tp + tn) / (tp + fp + fn + tn), rejection_rate=(tp + fp) / (tp + fp + fn + tn))
