# -*- coding: utf-8 -*-
"""Correlated-estimator analysis.

The diagnostic estimator receives the thermodynamic estimate as a contextual
feature, so the two estimates of X_LM are not statistically independent. That
invalidates two things used in the earlier treatment:

  * the consistency index  Z = |X1 - X2| / sqrt(u1^2 + u2^2), whose denominator
    assumes zero covariance and is therefore too large when rho > 0, making Z
    too small and the acceptance test under-sensitive;
  * inverse-variance weighting, which is only the minimum-variance combination
    for uncorrelated estimates.

Both are generalised here and the cost of ignoring the correlation is quantified.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from swcl_physics import (BAR_PER_KGCM2, P_KGCM2, T_C, MW_GAS, RHO_L,
                          gas_density, phi_chisholm)

OUT = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(20260916)
N = 200_000

U1_REL, U2_REL = 0.12, 0.20
U2_TRANSFER = 0.06
P_CARRY = 0.25
CARRY_FRAC = (0.15, 0.60)
Z_MAX = 3.0
K_DAMP = 1.0
SIGMA_MODEL, SIGMA_BASE = 0.006, 0.007


def sample(n):
    p_kg = RNG.uniform(*P_KGCM2, n)
    t_c = RNG.uniform(*T_C, n)
    rho_g, _ = gas_density(p_kg * BAR_PER_KGCM2 * 1e5, t_c + 273.15)
    rho_l = RNG.uniform(*RHO_L, n)
    cgr = RNG.uniform(5.0, 100.0, n)
    m_l = cgr * 0.158987 * rho_l
    m_g = 28316.8 * (MW_GAS / 0.0224136)
    X = (m_l / m_g) * np.sqrt(rho_g / rho_l)
    return dict(X=X, rho_g=rho_g, rho_l=rho_l)


def estimators(st, rho):
    """Draw the two estimates with correlation rho between their random errors."""
    n = st["X"].size
    carry = np.where(RNG.random(n) < P_CARRY, RNG.uniform(*CARRY_FRAC, n), 0.0)

    e1 = RNG.normal(0, 1, n)
    xi = RNG.normal(0, 1, n)
    e2 = rho * e1 + np.sqrt(max(0.0, 1 - rho**2)) * xi     # Corr(e1, e2) = rho

    X1 = np.clip(st["X"] * (1 - carry) * (1 + U1_REL * e1), 1e-5, None)
    vc = (P_CARRY * (1 - P_CARRY) * (0.5*(CARRY_FRAC[0]+CARRY_FRAC[1]))**2
          + P_CARRY * (CARRY_FRAC[1] - CARRY_FRAC[0])**2 / 12.0)
    u1 = np.sqrt(U1_REL**2 + vc) * X1

    b2 = RNG.normal(0, U2_TRANSFER, n)
    X2 = np.clip(st["X"] * (1 + b2) * (1 + U2_REL * e2), 1e-5, None)
    u2 = np.sqrt(U2_REL**2 + U2_TRANSFER**2) * X2
    return X1, u1, X2, u2, carry


def fuse(X1, u1, X2, u2, rho_assumed):
    """Minimum-variance combination of two correlated estimates.

    With covariance c = rho*u1*u2 the generalised-least-squares weights are
        w1 = (u2^2 - c) / (u1^2 + u2^2 - 2c),   w2 = 1 - w1
    which reduces to inverse-variance weighting at rho = 0.
    """
    c = rho_assumed * u1 * u2
    den = u1**2 + u2**2 - 2*c
    den = np.where(np.abs(den) < 1e-18, 1e-18, den)
    w1 = (u2**2 - c) / den
    w1 = np.clip(w1, 0.0, 1.0)
    Xf = w1 * X1 + (1 - w1) * X2
    uf = np.sqrt(np.clip(w1**2 * u1**2 + (1-w1)**2 * u2**2 + 2*w1*(1-w1)*c, 0, None))
    return Xf, uf


def consistency(X1, u1, X2, u2, rho_assumed):
    """Z with the covariance term retained. var(X1 - X2) = u1^2 + u2^2 - 2c."""
    v = u1**2 + u2**2 - 2*rho_assumed*u1*u2
    v = np.clip(v, 1e-18, None)
    return np.abs(X1 - X2) / np.sqrt(v)


def robust_fuse(X1, u1, X2, u2, rho_assumed, k=K_DAMP):
    v = np.clip(u1**2 + u2**2 - 2*rho_assumed*u1*u2, 1e-18, None)
    excess = (X2 - X1) / np.sqrt(v)
    damp = 1.0 / (1.0 + np.clip(excess - k, 0.0, None)**2)
    c = rho_assumed * u1 * u2
    den = np.clip(u1**2 + u2**2 - 2*c, 1e-18, None)
    w1 = np.clip((u2**2 - c) / den, 0.0, 1.0) * damp
    w2 = 1.0 - np.clip((u2**2 - c) / den, 0.0, 1.0)
    s = w1 + w2
    return (w1 * X1 + w2 * X2) / s


def err(st, Xhat):
    n = st["X"].size
    pt = phi_chisholm(st["X"], st["rho_g"], st["rho_l"])
    ph = phi_chisholm(np.clip(Xhat, 1e-5, None), st["rho_g"], st["rho_l"])
    return ((pt/ph) * (1 + RNG.normal(0, SIGMA_MODEL, n))
            * (1 + RNG.normal(0, SIGMA_BASE, n)) - 1.0) * 100.0


def band(e, mask=None):
    if mask is not None:
        e = e[mask]
    lo, hi = np.percentile(e, [2.5, 97.5])
    return max(abs(lo), abs(hi))


res = {}
print("=" * 78)
print("Correlated-estimator analysis  |  N = %d" % N)
print("=" * 78)

st = sample(N)
rhos = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
out = {"rho": [], "band_naive_w": [], "band_gls_w": [],
       "reject_naive_Z": [], "reject_true_Z": [],
       "spec_naive_Z": [], "spec_true_Z": []}

print("\n[1] Cost of ignoring the correlation")
print("    %-6s %14s %12s | %12s %12s | %11s %11s"
      % ("rho", "band, IV wts", "band, GLS", "reject naive", "reject true",
         "spec naive", "spec true"))
for rho in rhos:
    X1, u1, X2, u2, carry = estimators(st, rho)

    # weights that wrongly assume independence, vs weights that use rho
    Xn = robust_fuse(X1, u1, X2, u2, rho_assumed=0.0)
    Xg = robust_fuse(X1, u1, X2, u2, rho_assumed=rho)

    Zn = consistency(X1, u1, X2, u2, rho_assumed=0.0)   # denominator too large
    Zt = consistency(X1, u1, X2, u2, rho_assumed=rho)

    an, at = Zn <= Z_MAX, Zt <= Z_MAX
    bn, bg = band(err(st, Xn), an), band(err(st, Xg), at)
    rn, rt = 1 - an.mean(), 1 - at.mean()
    sn = (carry[~an] > 0).mean() if (~an).sum() else float("nan")
    stt = (carry[~at] > 0).mean() if (~at).sum() else float("nan")

    out["rho"].append(rho); out["band_naive_w"].append(bn); out["band_gls_w"].append(bg)
    out["reject_naive_Z"].append(rn); out["reject_true_Z"].append(rt)
    out["spec_naive_Z"].append(sn); out["spec_true_Z"].append(stt)
    print("    %-6.2f %13.2f%% %11.2f%% | %11.1f%% %11.1f%% | %10.1f%% %10.1f%%"
          % (rho, bn, bg, 100*rn, 100*rt, 100*sn, 100*stt))

res["correlation_sweep"] = out

print("\n[2] Reading")
i3 = rhos.index(0.3)
print("    At rho = 0.3, ignoring the correlation understates the rejection rate")
print("    (%.1f%% vs %.1f%%) and widens the band (%.2f%% vs %.2f%%)."
      % (100*out["reject_naive_Z"][i3], 100*out["reject_true_Z"][i3],
         out["band_naive_w"][i3], out["band_gls_w"][i3]))

json.dump(res, open(os.path.join(OUT, "covariance_results.json"), "w"), indent=1)
print("\nresults -> covariance_results.json")

# ------------------------------------------------------------------- figure
plt.rcParams.update({"font.size": 8.5, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6})
C1, C2 = "#3E6B8A", "#B5544E"
fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.6))
r = np.array(out["rho"])

ax = axes[0]
ax.plot(r, out["band_naive_w"], "o-", color=C2, lw=1.7, ms=4,
        label="weights assuming independence")
ax.plot(r, out["band_gls_w"], "s-", color=C1, lw=1.7, ms=4,
        label="generalised least-squares weights")
ax.set_xlabel("correlation between estimator errors, $\\rho$")
ax.set_ylabel("95% error band (±%)")
ax.set_title("Effect on the fused estimate", fontsize=9, fontweight="bold")
ax.legend(fontsize=7)

ax = axes[1]
ax.plot(r, 100*np.array(out["reject_naive_Z"]), "o-", color=C2, lw=1.7, ms=4,
        label="$Z$ ignoring covariance")
ax.plot(r, 100*np.array(out["reject_true_Z"]), "s-", color=C1, lw=1.7, ms=4,
        label="$Z$ with covariance term")
ax.set_xlabel("correlation between estimator errors, $\\rho$")
ax.set_ylabel("rejection rate (%)")
ax.set_title("Effect on the acceptance test", fontsize=9, fontweight="bold")
ax.legend(fontsize=7)

fig.suptitle("Cost of treating structurally distinct estimates as independent",
             fontsize=9.5, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(os.path.join(OUT, "figH_covariance.png"), dpi=300,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("figH written")
