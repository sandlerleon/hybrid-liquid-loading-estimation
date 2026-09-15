# -*- coding: utf-8 -*-
"""Computational experiments for the Flow Measurement and Instrumentation paper.

This supersedes the lumped-error treatment used earlier. The estimators are now
modelled separately, so the analysis can answer the questions a metrology
reviewer will ask:

  * what does each estimator contribute on its own, and what does fusing them buy?
  * does the consistency test actually remove the cases where the thermodynamic
    estimator is blind (upstream carryover), or does it just discard data?
  * which input variable limits the corrected-rate uncertainty?
  * over what region of the (X_LM, Fr_g) plane is the correction admissible?

Key structural point: E1 (thermodynamic) is *biased* when liquid arrives as
upstream carryover rather than local condensate, because an EOS flash cannot see
it. E2 (diagnostic) is noisier but observational, so it does. The consistency
index exists to detect exactly that disagreement.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from swcl_physics import (BAR_PER_KGCM2, P_KGCM2, T_C, MW_GAS, RHO_L,
                          gas_density, phi_chisholm)

OUT = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(20260915)
N = 300_000

# ---- estimator characteristics -------------------------------------------
S1_REL = 0.12      # thermodynamic estimator, relative standard uncertainty
S2_REL = 0.20      # diagnostic estimator, relative standard uncertainty
P_CARRY = 0.25     # probability that some liquid is upstream carryover
S2_TRANSFER = 0.06 # E2 loop-to-site transfer bias, relative (systematic per site)
CARRY_FRAC = (0.15, 0.60)   # fraction of total liquid that is carryover
Z_MAX = 3.0        # consistency-index acceptance threshold

SIGMA_MODEL = 0.006   # correlation residual after site calibration
SIGMA_BASE = 0.007    # base meter + secondary instrumentation


def sample(n, X_fixed=None, fr_fixed=None, cgr=(5.0, 100.0)):
    p_kg = RNG.uniform(*P_KGCM2, n)
    t_c = RNG.uniform(*T_C, n)
    rho_g, z = gas_density(p_kg * BAR_PER_KGCM2 * 1e5, t_c + 273.15)
    rho_l = RNG.uniform(*RHO_L, n)
    if X_fixed is None:
        c = RNG.uniform(*cgr, n)
        m_l = c * 0.158987 * rho_l
        m_g = 28316.8 * (MW_GAS / 0.0224136)
        X = (m_l / m_g) * np.sqrt(rho_g / rho_l)
    else:
        X = np.full(n, float(X_fixed))
    D = 0.1541
    v_sg = RNG.uniform(8.0, 18.0, n) if fr_fixed is None else None
    if fr_fixed is None:
        fr = (v_sg / np.sqrt(9.81 * D)) * np.sqrt(rho_g / (rho_l - rho_g))
    else:
        fr = np.full(n, float(fr_fixed))
    return dict(X=X, rho_g=rho_g, rho_l=rho_l, fr=fr, p_kg=p_kg, t_c=t_c, z=z)


def estimators(st):
    """Return E1, E2, their reported standard uncertainties, and the truth."""
    n = st["X"].size
    carry = np.where(RNG.random(n) < P_CARRY, RNG.uniform(*CARRY_FRAC, n), 0.0)

    # E1 sees only the locally condensed part -> biased low by the carryover
    X1 = st["X"] * (1.0 - carry) * (1.0 + RNG.normal(0, S1_REL, n))
    X1 = np.clip(X1, 1e-5, None)

    # The uncertainty E1 *declares* must include an allowance for the carryover it
    # cannot see, or the fusion below will over-weight it. The allowance is the
    # standard deviation of the carryover fraction over the population, which for
    # a Bernoulli(p) x Uniform(a,b) mixture is:
    ec = P_CARRY * 0.5 * (CARRY_FRAC[0] + CARRY_FRAC[1])
    vc = (P_CARRY * (1 - P_CARRY) * (0.5*(CARRY_FRAC[0]+CARRY_FRAC[1]))**2
          + P_CARRY * (CARRY_FRAC[1] - CARRY_FRAC[0])**2 / 12.0)
    s1 = np.sqrt(S1_REL**2 + vc) * X1
    s1_naive = S1_REL * X1               # what a budget omitting carryover would state

    # E2 is observational: it sees all the liquid, but with more scatter. It is a
    # mapping fitted at a flow loop and transferred to site, so it also carries a
    # systematic transfer bias that the fit itself cannot reveal.
    # systematic for a given installation; drawn per realisation so that the
    # reported statistics integrate over the population of installations
    b2 = RNG.normal(0, S2_TRANSFER, n)
    X2 = st["X"] * (1.0 + b2) * (1.0 + RNG.normal(0, S2_REL, n))
    X2 = np.clip(X2, 1e-5, None)
    s2 = np.sqrt(S2_REL**2 + S2_TRANSFER**2) * X2
    return X1, s1, X2, s2, carry, s1_naive


def fuse(X1, s1, X2, s2):
    """Naive inverse-variance fusion (the specification this study started from)."""
    w1, w2 = 1.0 / s1**2, 1.0 / s2**2
    Xf = (X1 * w1 + X2 * w2) / (w1 + w2)
    sf = np.sqrt(1.0 / (w1 + w2))
    Z = np.abs(X1 - X2) / np.sqrt(s1**2 + s2**2)
    return Xf, sf, Z


def fuse_robust(X1, s1, X2, s2, k=1.0):
    """Asymmetric robust fusion.

    The thermodynamic estimator has a one-sided failure mode: a flash calculation
    can only miss liquid that arrived from upstream, never invent liquid that is
    not there. So a significant excess of E2 over E1 is evidence of carryover,
    not of E2 noise, and the weighting should move toward E2 rather than average
    the two. Disagreement in the other direction carries no such asymmetry and is
    treated as ordinary noise.

    The fused uncertainty is inflated by the Birge ratio when the two disagree
    by more than their stated uncertainties allow, which is standard practice for
    reconciling inconsistent estimates in metrology.
    """
    sd = np.sqrt(s1**2 + s2**2)
    Z = np.abs(X1 - X2) / sd
    excess = (X2 - X1) / sd                 # signed: positive means E2 reads higher

    w1, w2 = 1.0 / s1**2, 1.0 / s2**2
    # de-weight E1 smoothly once E2 reads significantly higher
    damp = 1.0 / (1.0 + np.clip(excess - k, 0.0, None)**2)
    w1e = w1 * damp
    Xf = (X1 * w1e + X2 * w2) / (w1e + w2)
    sf = np.sqrt(1.0 / (w1e + w2)) * np.maximum(1.0, Z)   # Birge inflation
    return Xf, sf, Z


def corrected_error(st, X_used):
    """Relative error (%) of the corrected gas rate."""
    n = st["X"].size
    phi_t = phi_chisholm(st["X"], st["rho_g"], st["rho_l"])
    phi_h = phi_chisholm(np.clip(X_used, 1e-5, None), st["rho_g"], st["rho_l"])
    bias = RNG.normal(0, SIGMA_MODEL, n)
    noise = RNG.normal(0, SIGMA_BASE, n)
    return ((phi_t / phi_h) * (1 + bias) * (1 + noise) - 1.0) * 100.0


def metrics(e, accepted=None):
    if accepted is not None:
        e = e[accepted]
    if e.size == 0:
        return dict(n=0)
    lo, hi = np.percentile(e, [2.5, 97.5])
    return dict(n=int(e.size), bias=float(e.mean()), mae=float(np.abs(e).mean()),
                rmse=float(np.sqrt((e**2).mean())), maxabs=float(np.abs(e).max()),
                band95=float(max(abs(lo), abs(hi))))


results = {}
print("=" * 78)
print("FMI computational study  |  N = %d" % N)
print("E1 sigma %.0f%%, E2 sigma %.0f%%, carryover in %.0f%% of cases, Z_max = %.1f"
      % (100*S1_REL, 100*S2_REL, 100*P_CARRY, Z_MAX))
print("=" * 78)

st = sample(N)
X1, s1, X2, s2, carry, s1n = estimators(st)
Xn, _, Zn = fuse(X1, s1n, X2, s2)      # naive budget: carryover omitted
Xf, sf, Z = fuse(X1, s1, X2, s2)       # honest budget
Xr, sr, _ = fuse_robust(X1, s1, X2, s2)
accept = Z <= Z_MAX

# ---------------------------------------------------- Experiment 1: ablation
print("\n[1] Ablation study  (metrics in % of gas rate)\n")
phi_t = phi_chisholm(st["X"], st["rho_g"], st["rho_l"])
rows = [
    ("Uncorrected meter", (phi_t - 1.0) * 100.0, None),
    ("Correlation with known X_LM (oracle)", corrected_error(st, st["X"]), None),
    ("E1 only (thermodynamic)", corrected_error(st, X1), None),
    ("E2 only (diagnostic)", corrected_error(st, X2), None),
    ("Fusion, carryover omitted from E1 budget", corrected_error(st, Xn), None),
    ("Fusion, honest E1 uncertainty budget", corrected_error(st, Xf), None),
    ("Robust asymmetric fusion", corrected_error(st, Xr), None),
    ("SWCL: robust fusion + consistency rejection", corrected_error(st, Xr), accept),
]
abl = {}
hdr = "    %-38s %8s %7s %7s %8s %8s %7s"
print(hdr % ("method", "bias", "MAE", "RMSE", "max|e|", "95% band", "accept"))
for name, e, acc in rows:
    m = metrics(e, acc)
    m["accept_rate"] = float(acc.mean()) if acc is not None else 1.0
    abl[name] = m
    print("    %-38s %+7.2f %7.2f %7.2f %8.2f %8.2f %6.0f%%"
          % (name, m["bias"], m["mae"], m["rmse"], m["maxabs"], m["band95"],
             100*m["accept_rate"]))
results["ablation"] = abl

# does rejection preferentially remove carryover cases?
print("\n    carryover present in %.1f%% of all cases, %.1f%% of accepted, %.1f%% of rejected"
      % (100*(carry > 0).mean(), 100*(carry[accept] > 0).mean(),
         100*(carry[~accept] > 0).mean()))
results["rejection_selectivity"] = dict(
    all=float((carry > 0).mean()), accepted=float((carry[accept] > 0).mean()),
    rejected=float((carry[~accept] > 0).mean()))

# ------------------------------------------- Experiment 2: Z threshold sweep
print("\n[2] Consistency-index threshold sweep")
zs = np.concatenate([np.arange(0.5, 6.01, 0.25), [np.inf]])
zsweep = {"Z": [], "accept": [], "band95": [], "rmse": []}
for zt in zs:
    a = Z <= zt
    if a.sum() < 100: continue
    m = metrics(corrected_error(st, Xr), a)
    zsweep["Z"].append(float(zt) if np.isfinite(zt) else 99.0)
    zsweep["accept"].append(float(a.mean()))
    zsweep["band95"].append(m["band95"]); zsweep["rmse"].append(m["rmse"])
results["z_sweep"] = zsweep
for zt, ar, bb in zip(zsweep["Z"][::4], zsweep["accept"][::4], zsweep["band95"][::4]):
    print("    Z_max %4.1f -> accept %5.1f%%   95%% band ±%.2f%%" % (zt, 100*ar, bb))

# -------------------------------------------- Experiment 3: sensitivity study
print("\n[3] Normalised sensitivity of corrected gas rate  S_i = (dQ/Q)/(dx_i/x_i)")
base = sample(60_000, X_fixed=0.05)
b1, bs1, b2, bs2, _, _ = estimators(base)
bXf, _, _ = fuse_robust(b1, bs1, b2, bs2)


def chain(stt, Xhat, dp_scale=1.0, rho_scale=1.0):
    """Corrected mass rate, up to constants: Q ∝ sqrt(rho_g·dP)/phi."""
    phi_h = phi_chisholm(np.clip(Xhat, 1e-5, None), stt["rho_g"]*rho_scale, stt["rho_l"])
    return np.sqrt(stt["rho_g"] * rho_scale * dp_scale) / phi_h


q0 = chain(base, bXf)
sens = {}
d = 0.01
for label, fn in [
    ("Liquid loading estimate X_LM", lambda: chain(base, bXf * (1 + d))),
    ("Gas density rho_g", lambda: chain(base, bXf, rho_scale=1 + d)),
    ("Differential pressure dP", lambda: chain(base, bXf, dp_scale=1 + d)),
    ("Liquid density rho_l", None),
]:
    if label.startswith("Liquid density"):
        b2s = dict(base); b2s["rho_l"] = base["rho_l"] * (1 + d)
        q1 = np.sqrt(b2s["rho_g"]) / phi_chisholm(np.clip(bXf, 1e-5, None), b2s["rho_g"], b2s["rho_l"])
    else:
        q1 = fn()
    S = float((((q1 - q0) / q0) / d).mean())
    sens[label] = S
    print("    %-32s S = %+.3f" % (label, S))
# pressure and temperature act through gas density
sens["Line pressure P (via rho_g)"] = sens["Gas density rho_g"] * 1.0
sens["Temperature T (via rho_g)"] = -sens["Gas density rho_g"] * (315.0 / 315.0)
results["sensitivity"] = sens

# ---------------------------------------- Experiment 4: admissibility envelope
print("\n[4] Admissibility envelope over (X_LM, Fr_g)")
Xg = np.linspace(0.005, 0.25, 22)
Fg = np.linspace(1.0, 6.0, 20)
band = np.zeros((Fg.size, Xg.size))
arate = np.zeros_like(band)
for i, fr in enumerate(Fg):
    for j, xv in enumerate(Xg):
        s = sample(4000, X_fixed=xv, fr_fixed=fr)
        e1, q1, e2, q2, _, _ = estimators(s)
        xf, _, zz = fuse_robust(e1, q1, e2, q2)
        a = zz <= Z_MAX
        m = metrics(corrected_error(s, xf), a)
        band[i, j] = m.get("band95", np.nan)
        arate[i, j] = a.mean()
results["envelope_map"] = dict(X=Xg.tolist(), Fr=Fg.tolist(),
                               band=band.tolist(), accept=arate.tolist())
green = (band <= 2.0).mean(); amber = ((band > 2.0) & (band <= 3.0)).mean()
print("    cells meeting ±2%%: %.0f%%   ±2–3%%: %.0f%%   >±3%%: %.0f%%"
      % (100*green, 100*amber, 100*(band > 3.0).mean()))


# ------------------------------------ Experiment 5: when is fusion worthwhile?
print("\n[5] Design space: effect of carryover prevalence")
sweep = {"p_carry": [], "E1": [], "E2": [], "robust": []}
_p0 = P_CARRY
for pc in [0.0, 0.05, 0.10, 0.20, 0.30, 0.45, 0.60]:
    P_CARRY = pc
    ss = sample(60_000)
    a1, q1, a2, q2, _, _ = estimators(ss)
    ar, _, zz = fuse_robust(a1, q1, a2, q2)
    sweep["p_carry"].append(pc)
    sweep["E1"].append(metrics(corrected_error(ss, a1))["band95"])
    sweep["E2"].append(metrics(corrected_error(ss, a2))["band95"])
    sweep["robust"].append(metrics(corrected_error(ss, ar), zz <= Z_MAX)["band95"])
    print("    carryover %4.0f%%  ->  E1 ±%.2f%%   E2 ±%.2f%%   SWCL ±%.2f%%"
          % (100*pc, sweep["E1"][-1], sweep["E2"][-1], sweep["robust"][-1]))
P_CARRY = _p0
results["design_sweep"] = sweep

json.dump(results, open(os.path.join(OUT, "fmi_results.json"), "w"), indent=1)
print("\nresults -> fmi_results.json")


# ================================================================= FIGURES
plt.rcParams.update({"font.size": 8.5, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6})
C1, C2, C3 = "#3E6B8A", "#B5544E", "#5C8A5C"


def fig_estimators():
    """E1 vs E2 scatter, showing the carryover cases the consistency test catches."""
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.7))
    k = RNG.choice(N, 4000, replace=False)
    ax = axes[0]
    nc = carry[k] == 0
    ax.scatter(X1[k][nc], X2[k][nc], s=3, alpha=0.25, color=C1, label="local condensate only")
    ax.scatter(X1[k][~nc], X2[k][~nc], s=3, alpha=0.35, color=C2, label="upstream carryover present")
    lim = [0, 0.16]
    ax.plot(lim, lim, "k--", lw=0.9, label="agreement")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("$X_{LM}$ from thermodynamic estimator  $X^{(1)}$")
    ax.set_ylabel("$X_{LM}$ from diagnostic estimator  $X^{(2)}$")
    ax.set_title("Estimator agreement", fontsize=9, fontweight="bold")
    ax.legend(fontsize=6.6, loc="upper left")

    ax = axes[1]
    bins = np.linspace(0, 8, 90)
    ax.hist(Z[carry == 0], bins=bins, color=C1, alpha=0.75, label="local condensate only")
    ax.hist(Z[carry > 0], bins=bins, color=C2, alpha=0.7, label="upstream carryover present")
    ax.axvline(Z_MAX, color="k", ls="--", lw=1.1)
    ax.text(Z_MAX + 0.12, ax.get_ylim()[1]*0.82, "$Z_{max}$", fontsize=8)
    ax.set_xlabel("estimator consistency index  $Z$")
    ax.set_ylabel("count"); ax.set_yticklabels([])
    ax.set_title("Consistency index separates the two populations",
                 fontsize=9, fontweight="bold")
    ax.legend(fontsize=6.6)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figA_estimator_agreement.png"), dpi=300,
                bbox_inches="tight", facecolor="white")
    plt.close(fig); print("figA written")


def fig_ablation():
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    names = [r[0] for r in rows]
    vals = [abl[n]["band95"] for n in names]
    rmses = [abl[n]["rmse"] for n in names]
    y = np.arange(len(names))[::-1]
    ax.barh(y + 0.18, vals, height=0.34, color=C1, label="95% band")
    ax.barh(y - 0.18, rmses, height=0.34, color=C3, label="RMSE")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=7.4)
    ax.axvline(3.0, color="k", ls="--", lw=0.9); ax.axvline(2.0, color="k", ls=":", lw=0.9)
    ax.text(3.05, len(names)-0.6, "±3%", fontsize=7.5)
    ax.text(2.05, len(names)-0.6, "±2%", fontsize=7.5)
    ax.set_xlabel("gas-rate error (%)")
    ax.set_xlim(0, 16)
    ax.set_title("Contribution of each element of the estimator",
                 fontsize=9.5, fontweight="bold")
    ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figB_ablation.png"), dpi=300,
                bbox_inches="tight", facecolor="white")
    plt.close(fig); print("figB written")


def fig_sensitivity():
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    order = ["Liquid loading estimate X_LM", "Gas density rho_g",
             "Differential pressure dP", "Liquid density rho_l"]
    labs = ["$X_{LM}$ estimate", r"gas density $\rho_G$",
            r"differential pressure $\Delta P$", r"liquid density $\rho_L$"]
    vals = [sens[o] for o in order]
    cols = [C2 if abs(v) == max(abs(np.array(vals))) else C1 for v in vals]
    ax.barh(np.arange(len(vals))[::-1], vals, color=cols, height=0.55)
    ax.set_yticks(np.arange(len(vals))[::-1]); ax.set_yticklabels(labs, fontsize=8)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("normalised sensitivity  $S_i = (\\partial Q/Q)\\,/\\,(\\partial x_i/x_i)$")
    ax.set_title("What limits the corrected-rate accuracy ($X_{LM}$ = 0.05)",
                 fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figC_sensitivity.png"), dpi=300,
                bbox_inches="tight", facecolor="white")
    plt.close(fig); print("figC written")


def fig_envelope():
    from matplotlib.colors import ListedColormap, BoundaryNorm
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.6))
    cls = np.zeros_like(band)
    cls[band <= 2.0] = 0
    cls[(band > 2.0) & (band <= 3.0)] = 1
    cls[band > 3.0] = 2
    cmap = ListedColormap(["#BFD8C2", "#F2DFA7", "#E8BFBF"])
    ax = axes[0]
    ax.pcolormesh(Xg, Fg, cls, cmap=cmap, norm=BoundaryNorm([-.5,.5,1.5,2.5], 3), shading="auto")
    ax.set_xlabel("$X_{LM}$"); ax.set_ylabel("gas densiometric Froude number $Fr_G$")
    ax.set_title("Admissibility of the correction", fontsize=9, fontweight="bold")
    ax.grid(False)
    for c, lab, x in [("#BFD8C2", "±2% met", 0.012), ("#F2DFA7", "±2–3%", 0.095),
                      ("#E8BFBF", ">±3%", 0.175)]:
        ax.add_patch(plt.Rectangle((x, 5.55), 0.012, 0.28, facecolor=c, edgecolor="k", lw=0.5))
        ax.text(x + 0.016, 5.69, lab, fontsize=7, va="center")

    ax = axes[1]
    m = ax.pcolormesh(Xg, Fg, 100*arate, cmap="viridis", shading="auto", vmin=50, vmax=100)
    ax.set_xlabel("$X_{LM}$"); ax.set_ylabel("$Fr_G$")
    ax.set_title("Acceptance rate of the consistency test (%)", fontsize=9, fontweight="bold")
    ax.grid(False)
    fig.colorbar(m, ax=ax, pad=0.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figD_envelope.png"), dpi=300,
                bbox_inches="tight", facecolor="white")
    plt.close(fig); print("figD written")



def fig_distribution():
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    eu = (phi_t - 1.0) * 100.0
    es = corrected_error(st, Xr)[accept]
    bins = np.linspace(-8, 20, 140)
    ax.hist(eu, bins=bins, color=C2, alpha=0.78, label="uncorrected meter")
    ax.hist(es, bins=bins, color=C1, alpha=0.82, label="SWCL corrected (accepted)")
    for v in (-3, 3):
        ax.axvline(v, color="#333", ls="--", lw=0.9)
    ax.text(3.2, ax.get_ylim()[1]*0.9, "±3%", fontsize=8)
    ax.set_xlabel("gas-rate error (%)"); ax.set_ylabel("count"); ax.set_yticklabels([])
    ax.set_title("Error distribution before and after correction",
                 fontsize=9.5, fontweight="bold")
    ax.legend(fontsize=7.6)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figE_distribution.png"), dpi=300,
                bbox_inches="tight", facecolor="white")
    plt.close(fig); print("figE written")


def fig_designspace():
    d = results["design_sweep"]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    x = 100*np.array(d["p_carry"])
    ax.plot(x, d["E1"], "o-", color=C3, lw=1.6, ms=4, label="thermodynamic estimator alone")
    ax.plot(x, d["E2"], "s-", color=C2, lw=1.6, ms=4, label="diagnostic estimator alone")
    ax.plot(x, d["robust"], "^-", color=C1, lw=2.0, ms=5, label="proposed method")
    ax.axhline(3.0, color="#444", ls="--", lw=0.9)
    ax.text(61, 3.0, "±3%", fontsize=7.5, va="center")
    ax.set_xlabel("prevalence of upstream liquid carryover (% of operating time)")
    ax.set_ylabel("95% error band (±%)")
    ax.set_title("When is fusion worthwhile?", fontsize=9.5, fontweight="bold")
    ax.set_xlim(-2, 62); ax.set_ylim(2, 7.5)
    ax.legend(fontsize=7.4, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figF_designspace.png"), dpi=300,
                bbox_inches="tight", facecolor="white")
    plt.close(fig); print("figF written")


if __name__ == "__main__":
    fig_estimators(); fig_ablation(); fig_sensitivity()
    fig_envelope(); fig_distribution(); fig_designspace()
