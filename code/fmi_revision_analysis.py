# -*- coding: utf-8 -*-
"""Revision experiments for FLOWMEASINST-D-26-00971 (reviewer comments R2.1-R2.5, R2.8 and R1).

    python fmi_revision_analysis.py

Writes fmi_revision_results.json and figI_modelform.png, figJ_robustness.png, figK_detector.png.
One sampled world (300,000 realizations, fixed seed) is shared by every configuration (common random numbers),
so the differences reported between methods are not sampling noise. Sampling noise itself is reported (batch spread).

    E1  model-form discrepancy      truth over-reading differs from the correction model           -> Table 8, Fig. 10
    E2  fusion robustness           diagnostic uncertainty, transfer bias, carryover prevalence      -> Fig. 11
    E3  weighting rules and k       symmetric / one-sided Cauchy / Huber / hard switch, k sweep      -> Table 9
    E4  detector characterization   confusion matrix, ROC, precision-recall, detection vs magnitude -> Table 7, Fig. 12
    E5  uncertainty propagation     declared interval against realized error (coverage)             -> Table 6, Table 8
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import fmi_revision_lib as L

OUT = os.path.dirname(os.path.abspath(__file__))
SEED = 20261027
N = 300_000
W = L.World(N, SEED)
R = {"seed": SEED, "n": N}
B = L.BASE
ZMAX = B["zmax"]


def method_set(E, truth, w=W, rho=0.0, u_form=0.0, k=B["k"], rule="cauchy"):
    """Error arrays for the configurations of Table 3 under one truth model."""
    X1, u1, X2, u2 = E["X1"], E["u1"], E["X2"], E["u2"]
    out = {}
    out["uncorrected"] = (L.err_uncorrected(w, truth), None, None)
    out["oracle"] = (L.err(w, w.X, truth), None, None)
    out["e1"] = (L.err(w, X1, truth), None, None)
    out["e2"] = (L.err(w, X2, truth), None, None)
    Xn, _, _, _ = L.fuse(X1, E["u1_naive"], X2, u2, rho, "gls")
    out["fusion_naive_budget"] = (L.err(w, Xn, truth), None, None)
    Xg, ug, _, _ = L.fuse(X1, u1, X2, u2, rho, "gls")
    out["fusion_allowance"] = (L.err(w, Xg, truth), None, None)
    Xa, ua, Z, _ = L.fuse(X1, u1, X2, u2, rho, rule, k)
    ea = L.err(w, Xa, truth)
    out["asymmetric"] = (ea, None, L.declared_u_rel(w, Xa, ua, u_form))
    acc = Z <= ZMAX
    out["full"] = (ea, acc, L.declared_u_rel(w, Xa, ua, u_form))
    return out


def summarize(ms):
    res = {}
    for name, (e, acc, u) in ms.items():
        m = L.metrics(e, acc)
        m["accept"] = float(acc.mean()) if acc is not None else 1.0
        if u is not None:
            m["coverage_2u"] = L.coverage(e, u, acc)
        res[name] = m
    return res


# =========================================================================== 0. baseline against the submitted study
def check_baseline():
    E = L.estimates(W)
    ms = method_set(E, L.phi_true(W))
    res = summarize(ms)
    ref = json.load(open(os.path.join(OUT, "fmi_results.json")))["ablation"]
    pairs = [("uncorrected", "Uncorrected meter"), ("oracle", "Correlation with known X_LM (oracle)"),
             ("e1", "E1 only (thermodynamic)"), ("e2", "E2 only (diagnostic)"),
             ("fusion_naive_budget", "Fusion, carryover omitted from E1 budget"),
             ("fusion_allowance", "Fusion, honest E1 uncertainty budget"), ("asymmetric", "Robust asymmetric fusion"),
             ("full", "SWCL: robust fusion + consistency rejection")]
    diff = {a: res[a]["band95"] - ref[b]["band95"] for a, b in pairs}
    # sampling noise of a 95% band: 10 batches of 30,000
    batch = {}
    for name in ("e2", "asymmetric", "full"):
        e, acc, _ = ms[name]
        bands = [L.band95(e[i * 30000:(i + 1) * 30000], None if acc is None else acc[i * 30000:(i + 1) * 30000])
                 for i in range(10)]
        batch[name] = dict(sd_of_30k_batch=float(np.std(bands, ddof=1)), se_300k=float(np.std(bands, ddof=1) / np.sqrt(10)))
    R["baseline"] = dict(rows=res, difference_vs_submitted_band95=diff,
                         max_abs_difference=float(max(abs(v) for v in diff.values())), sampling=batch)
    print("baseline: max |band95 - Table 3| = %.3f pp ; SE(300k) e2 %.3f, asym %.3f, full %.3f"
          % (R["baseline"]["max_abs_difference"], batch["e2"]["se_300k"], batch["asymmetric"]["se_300k"], batch["full"]["se_300k"]))
    return E


# =========================================================================== E1 model-form discrepancy
def exp_modelform():
    E = L.estimates(W)
    pc = np.sqrt(1.0 + W.cn * W.X + W.X ** 2)
    u_form = 0.05 * (pc - 1.0) / pc          # a declared 5% relative uncertainty on the over-reading
    scen = [("matched", dict(model="chisholm")),
            ("Murdock (independent orifice correlation)", dict(model="murdock")),
            ("over-reading -10%", dict(model="chisholm", scale=0.90)),
            ("over-reading -5%", dict(model="chisholm", scale=0.95)),
            ("over-reading -2%", dict(model="chisholm", scale=0.98)),
            ("over-reading +2%", dict(model="chisholm", scale=1.02)),
            ("over-reading +5%", dict(model="chisholm", scale=1.05)),
            ("over-reading +10%", dict(model="chisholm", scale=1.10)),
            ("random discrepancy 5%", dict(model="chisholm", rand=0.05)),
            ("random discrepancy 10%", dict(model="chisholm", rand=0.10)),
            ("de Leeuw form (functional-form stress test only)", dict(model="deleeuw"))]
    res = {}
    for name, kw in scen:
        truth = L.phi_true(W, **kw)
        r0 = summarize(method_set(E, truth, u_form=0.0))
        r1 = summarize(method_set(E, truth, u_form=u_form))
        for key in ("asymmetric", "full"):
            r0[key]["coverage_2u_with_form_term"] = r1[key]["coverage_2u"]
        res[name] = r0
        f, e2 = r0["full"], r0["e2"]
        print("  %-52s full %+.2f/%.2f  e2 %+.2f/%.2f  oracle %.2f  cover(2u) %.1f%% -> %.1f%% with u_form"
              % (name, f["bias"], f["band95"], e2["bias"], e2["band95"], r0["oracle"]["band95"],
                 100 * f["coverage_2u"], 100 * f["coverage_2u_with_form_term"]))
    R["modelform"] = res
    # how large must the declared model-form term be for the declared +-2u interval to cover ~95%?
    fgrid = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
    cov = {}
    for name, kw in [("matched", dict(model="chisholm")), ("Murdock (independent orifice correlation)", dict(model="murdock")),
                     ("over-reading +10%", dict(model="chisholm", scale=1.10)), ("random discrepancy 10%", dict(model="chisholm", rand=0.10))]:
        truth = L.phi_true(W, **kw)
        Xa, ua, Z, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"])
        e = L.err(W, Xa, truth)
        acc = Z <= ZMAX
        cov[name] = {str(f): L.coverage(e, L.declared_u_rel(W, Xa, ua, f * (pc - 1.0) / pc), acc) for f in fgrid}
    R["modelform_coverage_vs_uform"] = dict(f=fgrid, rows=cov)
    print("  coverage vs declared model-form term:", {k: [round(v[str(f)], 3) for f in fgrid] for k, v in cov.items()})
    # does a mismatched truth change which estimator is best?
    best = {n: min(("e1", "e2", "fusion_allowance", "asymmetric", "full"), key=lambda m: v[m]["band95"]) for n, v in res.items()}
    R["modelform_best_method"] = best
    return res


# =========================================================================== E2 fusion robustness
def band_pack(E, truth=None, k=B["k"]):
    truth = L.phi_true(W) if truth is None else truth
    X1, u1, X2, u2 = E["X1"], E["u1"], E["X2"], E["u2"]
    out = {"e1": L.band95(L.err(W, X1, truth)), "e2": L.band95(L.err(W, X2, truth))}
    Xg, _, _, _ = L.fuse(X1, u1, X2, u2, 0.0, "gls")
    out["fusion_allowance"] = L.band95(L.err(W, Xg, truth))
    Xa, _, Z, _ = L.fuse(X1, u1, X2, u2, 0.0, "cauchy", k)
    ea = L.err(W, Xa, truth)
    out["asymmetric"] = L.band95(ea)
    out["full"] = L.band95(ea, Z <= ZMAX)
    Xh, _, Zh, _ = L.fuse(X1, u1, X2, u2, 0.0, "hard", 1.0)
    eh = L.err(W, Xh, truth)
    out["hard"] = L.band95(eh)
    out["hard_full"] = L.band95(eh, Zh <= ZMAX)
    out["bias_full"] = float(ea[Z <= ZMAX].mean())
    out["accept"] = float((Z <= ZMAX).mean())
    return out


def exp_robustness():
    truth = L.phi_true(W)
    res = {}
    # (a) diagnostic random uncertainty: consistent declaration vs declared at the assumed 20% / 6%
    s2s = [0.10, 0.15, 0.20, 0.30, 0.40, 0.60]
    res["s2_consistent"] = dict(x=s2s, rows=[band_pack(L.estimates(W, s2=s)) for s in s2s])
    res["s2_misdeclared"] = dict(x=s2s, rows=[band_pack(L.estimates(W, s2=s, s2_declared=0.20)) for s in s2s])
    # (b) transfer bias spread
    s2t = [0.0, 0.03, 0.06, 0.10, 0.15, 0.20]
    res["s2t_consistent"] = dict(x=s2t, rows=[band_pack(L.estimates(W, s2t=s, s2t_declared=s)) for s in s2t])
    res["s2t_misdeclared"] = dict(x=s2t, rows=[band_pack(L.estimates(W, s2t=s, s2t_declared=0.06)) for s in s2t])
    # (c) carryover prevalence, allowance matched to the truth or fixed at the assumed 25%
    ps = [0.0, 0.025, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.60]
    res["p_matched"] = dict(x=ps, rows=[band_pack(L.estimates(W, p=p)) for p in ps])
    res["p_misdeclared"] = dict(x=ps, rows=[band_pack(L.estimates(W, p=p, p_declared=0.25)) for p in ps])
    # (d) one site with a fixed diagnostic transfer bias, declared as 6% spread; no per-realization random bias
    sb = [-0.20, -0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20]
    res["site_bias"] = dict(x=sb, rows=[band_pack(L.estimates(W, s2t=0.0, s2t_declared=0.06, site_bias=b)) for b in sb])
    # (e) where does gating/fusion beat the diagnostic estimator alone? (s2 x p grid; consistent declarations)
    gp = [0.0, 0.05, 0.10, 0.20, 0.30, 0.45, 0.60]
    gs = [0.10, 0.15, 0.20, 0.30, 0.40]
    grid = [[band_pack(L.estimates(W, p=p, s2=s)) for p in gp] for s in gs]
    res["grid"] = dict(p=gp, s2=gs, rows=grid)
    # crossing point at the baseline: smallest prevalence at which the diagnostic estimator alone is no worse than
    # the asymmetric fusion and than the full method (fine grid)
    fine = np.round(np.arange(0.0, 0.401, 0.01), 3)
    fb = [band_pack(L.estimates(W, p=p)) for p in fine]
    d_asym = np.array([r["asymmetric"] - r["e2"] for r in fb])
    d_full = np.array([r["full"] - r["e2"] for r in fb])
    d_e1 = np.array([r["e1"] - r["asymmetric"] for r in fb])
    cross = lambda d: float(fine[np.argmax(d >= 0)]) if (d >= 0).any() else None
    res["crossing"] = dict(p_asym_stops_beating_e2=cross(d_asym), p_full_stops_beating_e2=cross(d_full),
                           p_e1_stops_beating_asym=cross(-d_e1),
                           fine_p=fine.tolist(), asym_minus_e2=d_asym.tolist(), full_minus_e2=d_full.tolist())
    R["robustness"] = res
    print("  crossing (fusion stops beating E2): asymmetric at p=%s, full at p=%s" %
          (res["crossing"]["p_asym_stops_beating_e2"], res["crossing"]["p_full_stops_beating_e2"]))
    return res


# =========================================================================== E3 weighting rules and threshold
def exp_weighting():
    truth = L.phi_true(W)
    rules = [("Thermodynamic estimator alone", "e1", None), ("Diagnostic estimator alone", "e2", None),
             ("Symmetric GLS (no damping)", "gls", None)]
    rules += [("One-sided Cauchy, k = %g (Eq. 12)" % k, "cauchy", k) for k in (0.5, 1.0, 1.5, 2.0, 3.0)]
    rules += [("One-sided Huber, k = 1", "huber", 1.0), ("Two-sided Cauchy, k = 1 (control)", "cauchy2", 1.0)]
    rules += [("One-sided hard switch, k = %g" % k, "hard", k) for k in (0.5, 1.0, 1.5, 2.0)]
    cols = {}
    for p in (0.10, 0.25, 0.40):
        E = L.estimates(W, p=p)
        for name, rule, k in rules:
            Xf, uf, Z, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"], 0.0, rule, 1.0 if k is None else k)
            e = L.err(W, Xf, truth)
            acc = Z <= ZMAX
            cols.setdefault(name, {})[str(p)] = dict(band95=L.band95(e), band95_accepted=L.band95(e, acc),
                                                     bias=float(e.mean()), rmse=float(np.sqrt((e ** 2).mean())),
                                                     accept=float(acc.mean()))
    R["weighting"] = cols
    for name, v in cols.items():
        print("  %-38s p=.10 %.2f  p=.25 %.2f  p=.40 %.2f" % (name, v["0.1"]["band95"], v["0.25"]["band95"], v["0.4"]["band95"]))
    # best k at the baseline among the Cauchy family
    ks = {k: cols["One-sided Cauchy, k = %g (Eq. 12)" % k]["0.25"]["band95"] for k in (0.5, 1.0, 1.5, 2.0, 3.0)}
    R["weighting_best_k_baseline"] = min(ks, key=ks.get)
    kh = {k: cols["One-sided hard switch, k = %g" % k]["0.25"]["band95"] for k in (0.5, 1.0, 1.5, 2.0)}
    R["weighting_best_hard_k_baseline"] = min(kh, key=kh.get)
    return cols


# =========================================================================== E4 detector characterization
def roc_pr(score, positive):
    """ROC and precision-recall from a score (larger = more likely positive) by sweeping the threshold."""
    order = np.argsort(-score, kind="mergesort")
    pos = positive[order].astype(float)
    tp = np.cumsum(pos)
    fp = np.cumsum(1.0 - pos)
    P, Nn = pos.sum(), (1.0 - pos).sum()
    tpr, fpr = tp / P, fp / Nn
    prec = tp / (tp + fp)
    # thin to ~600 points for storage and plotting
    idx = np.unique(np.linspace(0, len(score) - 1, 600).astype(int))
    auc = float(np.trapezoid(np.concatenate([[0], tpr]), np.concatenate([[0], fpr])))
    ap = float(np.sum(np.diff(np.concatenate([[0], tpr])) * prec))
    return dict(fpr=fpr[idx].tolist(), tpr=tpr[idx].tolist(), precision=prec[idx].tolist(), auc=auc, average_precision=ap,
                prevalence=float(P / (P + Nn)))


def exp_detector():
    out = {}
    truth = L.phi_true(W)
    E = L.estimates(W)
    Xa, ua, Z, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"])
    pos = E["carry"] > 0
    ea = L.err(W, Xa, truth)
    consequential = np.abs(ea) > 3.0
    zgrid = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
    out["confusion_carryover"] = {str(z): L.confusion(Z > z, pos) for z in zgrid}
    out["confusion_consequential_error"] = {str(z): L.confusion(Z > z, consequential) for z in zgrid}
    out["consequential_prevalence"] = float(consequential.mean())
    out["band_accepted"] = {str(z): L.band95(ea, Z <= z) for z in zgrid}
    out["roc_carryover"] = roc_pr(Z, pos)
    out["roc_consequential_error"] = roc_pr(Z, consequential)
    # detection rate against the carryover magnitude
    mags = [(0.15, 0.25), (0.25, 0.35), (0.35, 0.45), (0.45, 0.60001)]
    det = {}
    for z in (1.0, 2.0, 3.0):
        det[str(z)] = []
        for lo, hi in mags:
            m = (E["carry"] >= lo) & (E["carry"] < hi)
            det[str(z)].append(float((Z[m] > z).mean()))
    out["detection_by_magnitude"] = dict(bins=[[a, round(b, 2)] for a, b in mags], rate=det)
    # effect of correlation on the detector when the covariance is retained or ignored
    rr = {}
    for rho in (0.0, 0.3, 0.6):
        Er = L.estimates(W, rho=rho)
        for label, rho_used in (("covariance retained", rho), ("independence assumed", 0.0)):
            _, _, Zr, _ = L.fuse(Er["X1"], Er["u1"], Er["X2"], Er["u2"], rho_used)
            pr = roc_pr(Zr, Er["carry"] > 0)
            rr["%g|%s" % (rho, label)] = dict(auc=pr["auc"], at_zmax=L.confusion(Zr > ZMAX, Er["carry"] > 0))
    out["correlation"] = rr
    # a diagnostic estimator that is worse (e.g. no downstream tapping: u2 widens to 30%)
    Ew = L.estimates(W, s2=0.30)
    _, _, Zw, _ = L.fuse(Ew["X1"], Ew["u1"], Ew["X2"], Ew["u2"])
    out["wide_diagnostic_30pct"] = dict(auc=roc_pr(Zw, Ew["carry"] > 0)["auc"], at_zmax=L.confusion(Zw > ZMAX, Ew["carry"] > 0))
    R["detector"] = out
    c3 = out["confusion_carryover"]["3.0"]
    print("  Z_max=3: sens %.3f spec %.4f prec %.3f FPR %.4f rej %.4f ; AUC %.3f"
          % (c3["sensitivity"], c3["specificity"], c3["precision"], c3["fpr"], c3["rejection_rate"], out["roc_carryover"]["auc"]))
    return out


# =========================================================================== E5 declared uncertainty and Table 6
def exp_propagation():
    truth = L.phi_true(W)
    E = L.estimates(W)
    Xa, ua, Z, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"])
    ea = L.err(W, Xa, truth)
    acc = Z <= ZMAX
    u = L.declared_u_rel(W, Xa, ua)
    res = dict(coverage_2u_full=L.coverage(ea, u, acc), coverage_2u_asym=L.coverage(ea, u),
               coverage_1u_full=L.coverage(ea, u, acc, 1.0),
               median_declared_U95_pct=float(200 * np.median(u[acc])),
               empirical_band95=L.band95(ea, acc))
    # coverage by loading level
    bins = [(0.0, 0.03), (0.03, 0.06), (0.06, 0.09), (0.09, 0.2)]
    res["by_loading"] = [dict(lo=a, hi=b, n=int(((W.X >= a) & (W.X < b) & acc).sum()),
                              coverage_2u=L.coverage(ea, u, acc & (W.X >= a) & (W.X < b)),
                              median_declared_U95_pct=float(200 * np.median(u[acc & (W.X >= a) & (W.X < b)])),
                              empirical_band95=L.band95(ea, acc & (W.X >= a) & (W.X < b))) for a, b in bins]
    # Table 6 recomputed from the same fused estimate, at X_LM = 0.05 and 0.10 (realizations within +-10%)
    # The simulation lumps the transmitter, discharge-coefficient and expansion terms into one 0.7% meter term;
    # the gas-density and differential-pressure rows are an itemization of two of its components, not additional terms.
    def budget(x0):
        sel = (W.X >= 0.9 * x0) & (W.X <= 1.1 * x0)
        SX = float(np.mean(L.sens_X(W, Xa)[sel]))
        ux = float(np.median((ua / np.clip(Xa, 1e-5, None))[sel]))
        rows = {"X_LM estimate": dict(S=SX, u_rel=ux, contrib=abs(SX) * ux),
                "gas density": dict(S=0.505, u_rel=0.004, contrib=0.505 * 0.004),
                "differential pressure": dict(S=0.499, u_rel=0.005, contrib=0.499 * 0.005),
                "liquid density": dict(S=-0.0064, u_rel=0.03, contrib=0.0064 * 0.03)}
        var = {"X_LM estimate": rows["X_LM estimate"]["contrib"] ** 2, "meter and secondary (lumped, includes the two rows below)": 0.007 ** 2,
               "correlation residual": 0.006 ** 2, "liquid density": rows["liquid density"]["contrib"] ** 2}
        tot = sum(var.values())
        a, b = rows["X_LM estimate"]["contrib"], rows["gas density"]["contrib"]
        return dict(rows=rows, variance_share={k: v / tot for k, v in var.items()}, u_c_independent=float(np.sqrt(tot)),
                    u_c_if_X_and_density_fully_correlated=float(np.sqrt(tot + 2 * a * b)),
                    u_c_if_X_and_density_fully_anticorrelated=float(np.sqrt(max(tot - 2 * a * b, 0.0))),
                    n=int(sel.sum()))
    res["table6"] = {"0.05": budget(0.05), "0.10": budget(0.10)}
    t5 = res["table6"]["0.05"]
    print("  coverage of +-2u: full %.1f%% (declared U95 median %.2f%% vs empirical band %.2f%%)"
          % (100 * res["coverage_2u_full"], res["median_declared_U95_pct"], res["empirical_band95"]))
    for x0, t in res["table6"].items():
        print("  Table 6 at X=%s: S_X %.3f u_X %.1f%% -> %.2f%% ; u_c %.2f%% (correlated bounds %.2f-%.2f%%) ; X share of variance %.0f%%"
              % (x0, t["rows"]["X_LM estimate"]["S"], 100 * t["rows"]["X_LM estimate"]["u_rel"], 100 * t["rows"]["X_LM estimate"]["contrib"],
                 100 * t["u_c_independent"], 100 * t["u_c_if_X_and_density_fully_anticorrelated"],
                 100 * t["u_c_if_X_and_density_fully_correlated"], 100 * t["variance_share"]["X_LM estimate"]))
    R["propagation"] = res
    return res


# ------------------------------------------------------------------------------------------------ envelope facts
def envelope_facts():
    R["envelope"] = dict(
        pressure_kgf_cm2=[60.0, 85.0], pressure_MPa=[round(60 * 0.0980665, 2), round(85 * 0.0980665, 2)],
        temperature_C=[30.0, 60.0], line_diameter_mm=154.1,
        rho_g_range=[float(W.rho_g.min()), float(W.rho_g.max())], rho_l_range=[640.0, 720.0],
        X_LM_percentiles={str(q): float(np.percentile(W.X, q)) for q in (0, 5, 50, 95, 100)},
        Fr_percentiles={str(q): float(np.percentile(W.fr, q)) for q in (0, 5, 50, 95, 100)})


# ====================================================================================================== figures
plt.rcParams.update({"font.size": 8.5, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6})
C1, C2, C3, C4 = "#3E6B8A", "#B5544E", "#5C8A5C", "#8A7A3E"


def fig_modelform():
    mf = R["modelform"]
    names = ["matched", "Murdock (independent orifice correlation)", "over-reading -10%", "over-reading -5%",
             "over-reading +5%", "over-reading +10%", "random discrepancy 10%"]
    short = ["matched", "Murdock", "−10%", "−5%", "+5%", "+10%", "random\n10%"]
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.7))
    x = np.arange(len(names)); wd = 0.26
    ax = axes[0]
    ax.bar(x - wd, [mf[n]["oracle"]["band95"] for n in names], wd, color=C3, label="correlation, true $X_{LM}$ (oracle)")
    ax.bar(x, [mf[n]["e2"]["band95"] for n in names], wd, color=C2, label="diagnostic estimator alone")
    ax.bar(x + wd, [mf[n]["full"]["band95"] for n in names], wd, color=C1, label="full method (accepted)")
    ax.set_xticks(x); ax.set_xticklabels(short, fontsize=6.4)
    ax.set_ylabel("95% error band (±%)"); ax.set_xlabel("truth over-reading model (scaled: systematic change of the over-reading)", fontsize=7)
    ax.set_ylim(0, max(mf[n]["full"]["band95"] for n in names) * 1.45)
    ax.set_title("Error band when the truth differs from the correction", fontsize=8.6, fontweight="bold")
    ax.legend(fontsize=6.3, loc="upper left")
    ax = axes[1]
    ax.bar(x - wd / 2, [100 * mf[n]["full"]["coverage_2u"] for n in names], wd, color=C2, label="no model-form term declared")
    ax.bar(x + wd / 2, [100 * mf[n]["full"]["coverage_2u_with_form_term"] for n in names], wd, color=C1,
           label="5% model-form term declared")
    ax.axhline(95, color="k", ls="--", lw=0.9); ax.text(len(names) - 0.55, 95.6, "95%", fontsize=7, ha="right")
    ax.set_xticks(x); ax.set_xticklabels(short, fontsize=6.4)
    ax.set_ylim(60, 101); ax.set_ylabel("realized coverage of declared ±2$u$ (%)"); ax.set_xlabel("truth over-reading model", fontsize=7)
    ax.set_title("Does the declared uncertainty still cover?", fontsize=8.6, fontweight="bold")
    ax.legend(fontsize=6.3, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figI_modelform.png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_robustness():
    rb = R["robustness"]
    fig, axes = plt.subplots(2, 2, figsize=(7.8, 6.2))
    sty = [("e1", "thermodynamic alone", C3, "o"), ("e2", "diagnostic alone", C2, "s"),
           ("asymmetric", "asymmetric fusion (Eq. 12)", C1, "^"), ("hard", "one-sided hard switch, $k$ = 1", C4, "v"),
           ("full", "Eq. 12 + acceptance test", "k", "D")]

    def panel(ax, key, xs, xlabel, title, xscale=100.0, dashed=None, legend=False):
        d = rb[key]
        for m, lab, c, mk in sty:
            ax.plot(np.array(d["x"]) * xscale, [r[m] for r in d["rows"]], marker=mk, color=c, ms=3.4, lw=1.3, label=lab)
        if dashed:
            d2 = rb[dashed]
            for m, lab, c, mk in sty:
                if m in ("e2", "full"):
                    ax.plot(np.array(d2["x"]) * xscale, [r[m] for r in d2["rows"]], color=c, ls="--", lw=0.9)
        ax.set_xlabel(xlabel); ax.set_ylabel("95% error band (±%)")
        ax.set_title(title, fontsize=8.4, fontweight="bold")
        if legend:
            ax.legend(fontsize=6.0, loc="upper left")

    panel(axes[0, 0], "s2_consistent", None, "diagnostic relative uncertainty (%)", "(a) Diagnostic estimator quality",
          dashed="s2_misdeclared", legend=True)
    panel(axes[0, 1], "p_matched", None, "carryover prevalence (% of operating time)", "(b) Carryover prevalence",
          dashed="p_misdeclared")
    ax = axes[1, 0]
    d = rb["site_bias"]
    for m, lab, c, mk in sty:
        ax.plot(np.array(d["x"]) * 100, [r[m] for r in d["rows"]], marker=mk, color=c, ms=3.4, lw=1.3, label=lab)
    ax.set_xlabel("fixed site-level transfer bias of the diagnostic estimator (%)"); ax.set_ylabel("95% error band (±%)")
    ax.set_title("(c) Persistent bias at one site", fontsize=8.4, fontweight="bold")
    ax = axes[1, 1]
    g = rb["grid"]
    delta = np.array([[r["full"] - r["e2"] for r in row] for row in g["rows"]])
    lim = max(abs(delta.min()), abs(delta.max()))
    im = ax.imshow(delta, origin="lower", aspect="auto", cmap="RdBu_r", vmin=-lim, vmax=lim)
    ax.set_xticks(range(len(g["p"]))); ax.set_xticklabels([int(round(100 * p)) for p in g["p"]], fontsize=7)
    ax.set_yticks(range(len(g["s2"]))); ax.set_yticklabels([int(round(100 * s)) for s in g["s2"]], fontsize=7)
    for i in range(delta.shape[0]):
        for j in range(delta.shape[1]):
            ax.text(j, i, "%+.1f" % delta[i, j], ha="center", va="center", fontsize=6.0)
    ax.grid(False)
    ax.set_xlabel("carryover prevalence (%)"); ax.set_ylabel("diagnostic relative uncertainty (%)")
    ax.set_title("(d) Eq. 12 + acceptance minus diagnostic alone", fontsize=8.0, fontweight="bold")
    cb = fig.colorbar(im, ax=ax, pad=0.02, shrink=0.85); cb.set_label("band difference, pp (blue: fusion better)", fontsize=6.8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figJ_robustness.png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_detector():
    dt = R["detector"]
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.3))
    ax = axes[0]
    rc = dt["roc_carryover"]; rq = dt["roc_consequential_error"]
    ax.plot(rc["fpr"], rc["tpr"], color=C1, lw=1.6, label="carryover present (AUC %.2f)" % rc["auc"])
    ax.plot(rq["fpr"], rq["tpr"], color=C2, lw=1.6, label="|error| > 3%% (AUC %.2f)" % rq["auc"])
    ax.plot([0, 1], [0, 1], "k:", lw=0.8)
    for z in (1.0, 2.0, 3.0):
        c = dt["confusion_carryover"][str(z)]
        ax.plot(c["fpr"], c["sensitivity"], "o", color="k", ms=3.5)
        ax.annotate("$Z_{max}$=%g" % z, (c["fpr"], c["sensitivity"]), textcoords="offset points", xytext=(5, -3), fontsize=6.4)
    ax.set_xlabel("false-positive rate"); ax.set_ylabel("sensitivity")
    ax.set_title("ROC", fontsize=8.6, fontweight="bold"); ax.legend(fontsize=6.2, loc="center right")
    ax = axes[1]
    ax.plot(rc["tpr"], rc["precision"], color=C1, lw=1.6, label="carryover present")
    ax.plot(rq["tpr"], rq["precision"], color=C2, lw=1.6, label="|error| > 3%")
    ax.axhline(rc["prevalence"], color=C1, ls=":", lw=0.9); ax.axhline(rq["prevalence"], color=C2, ls=":", lw=0.9)
    for z in (1.0, 2.0, 3.0):
        c = dt["confusion_carryover"][str(z)]
        ax.plot(c["sensitivity"], c["precision"], "o", color="k", ms=3.5)
        ax.annotate("%g" % z, (c["sensitivity"], c["precision"]), textcoords="offset points", xytext=(4, 3), fontsize=6.4)
    ax.set_xlabel("sensitivity (recall)"); ax.set_ylabel("precision"); ax.set_ylim(0, 1.02)
    ax.set_title("Precision–recall", fontsize=8.6, fontweight="bold"); ax.legend(fontsize=6.2, loc="upper right")
    ax = axes[2]
    bins = dt["detection_by_magnitude"]["bins"]
    xl = ["%d–%d" % (round(100 * a), round(100 * b)) for a, b in bins]
    for z, c in (("1.0", C3), ("2.0", C4), ("3.0", C2)):
        ax.plot(range(len(xl)), 100 * np.array(dt["detection_by_magnitude"]["rate"][z]), "o-", color=c, ms=4, lw=1.4, label="$Z_{max}$ = %s" % z)
    ax.set_xticks(range(len(xl))); ax.set_xticklabels(xl, fontsize=7)
    ax.set_xlabel("carryover fraction of the total liquid (%)"); ax.set_ylabel("share of those cases rejected (%)")
    ax.set_title("Detection against carryover size", fontsize=8.6, fontweight="bold"); ax.legend(fontsize=6.4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figK_detector.png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    print("revision experiments  |  N = %d  seed %d" % (N, SEED))
    print("\n[0] baseline against the submitted study"); check_baseline()
    print("\n[E1] model-form discrepancy"); exp_modelform()
    print("\n[E2] fusion robustness"); exp_robustness()
    print("\n[E3] weighting rules"); exp_weighting()
    print("\n[E4] detector"); exp_detector()
    print("\n[E5] declared uncertainty"); exp_propagation()
    envelope_facts()
    json.dump(R, open(os.path.join(OUT, "fmi_revision_results.json"), "w"), indent=1)
    fig_modelform(); fig_robustness(); fig_detector()
    print("\nresults -> fmi_revision_results.json ; figures I, J, K written")
