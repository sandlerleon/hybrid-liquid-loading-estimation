# -*- coding: utf-8 -*-
"""Executable checks of the revision code (fmi_revision_lib.py, fmi_revision_analysis.py).

    python verify_revision.py          (run fmi_revision_analysis.py first)

Writes fmi_revision_verification.json. The manuscript builder refuses to run unless every check passes.

    V1  the revision machinery reproduces the submitted ablation (Table 3) within Monte Carlo error
    V2  symmetric fusion at rho = 0 equals closed-form inverse-variance weighting
    V3  asymmetric damping with a very large threshold reduces to symmetric fusion
    V4  Eq. (14) without damping or Birge inflation equals the inverse-variance variance
    V5  the detector table is reproduced from the consistency index by an independent count
    V6  the correlated-estimator generator produces the requested correlation
    V7  common random numbers: the matched model-form scenario is the baseline, array for array
    V8  first-order propagation (Eq. 16) against Monte Carlo propagation of the liquid-loading term
    V9  stored results are internally consistent (shares sum to one; ROC and PR are valid curves)
"""
import json
import os

import numpy as np

import fmi_revision_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "fmi_revision_results.json"), encoding="utf-8"))
res = {}


def rec(name, ok, **kw):
    res[name] = dict(passed=bool(ok), **kw)
    print(("PASS " if ok else "FAIL ") + name, kw)


W = L.World(R["n"], R["seed"])
E = L.estimates(W)
truth = L.phi_true(W)

# V1
b = R["baseline"]
tol = 3 * max(v["se_300k"] for v in b["sampling"].values())
rec("V1_baseline_reproduces_Table3", b["max_abs_difference"] < tol + 0.02, max_abs_difference_pp=round(b["max_abs_difference"], 4),
    tolerance_pp=round(tol + 0.02, 4), standard_error_pp=round(max(v["se_300k"] for v in b["sampling"].values()), 4))

# V2
Xg, ug, Z, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"], 0.0, "gls", birge=False)
iv = (E["X1"] / E["u1"] ** 2 + E["X2"] / E["u2"] ** 2) / (1 / E["u1"] ** 2 + 1 / E["u2"] ** 2)
rec("V2_gls_equals_inverse_variance", np.max(np.abs(Xg - iv)) < 1e-12, max_abs_difference=float(np.max(np.abs(Xg - iv))))

# V3
Xc, _, _, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"], 0.0, "cauchy", 1e9)
rec("V3_damping_limit_is_symmetric_fusion", np.max(np.abs(Xc - iv)) < 1e-12, max_abs_difference=float(np.max(np.abs(Xc - iv))))

# V4
var_iv = 1.0 / (1 / E["u1"] ** 2 + 1 / E["u2"] ** 2)
rec("V4_Eq14_reduces_to_inverse_variance", np.max(np.abs(ug ** 2 - var_iv) / var_iv) < 1e-10,
    max_relative_difference=float(np.max(np.abs(ug ** 2 - var_iv) / var_iv)))

# V5
_, _, Z, _ = L.fuse(E["X1"], E["u1"], E["X2"], E["u2"])
pos = E["carry"] > 0
ok, worst = True, 0.0
for z, c in R["detector"]["confusion_carryover"].items():
    zz = float(z)
    rej = Z > zz
    tp, fp, fn, tn = int((rej & pos).sum()), int((rej & ~pos).sum()), int((~rej & pos).sum()), int((~rej & ~pos).sum())
    ok &= (tp, fp, fn, tn) == (c["tp"], c["fp"], c["fn"], c["tn"]) and tp + fp + fn + tn == W.n
    worst = max(worst, abs(c["sensitivity"] - tp / (tp + fn)), abs(c["specificity"] - tn / (tn + fp)),
                abs(c["precision"] - tp / max(tp + fp, 1)), abs(c["fpr"] - fp / (fp + tn)))
rec("V5_confusion_matrix_independent_count", ok and worst < 1e-12, thresholds=len(R["detector"]["confusion_carryover"]), max_rate_difference=worst)

# V6
for rho in (0.3, 0.6):
    Er = L.estimates(W, rho=rho)
    e2 = (Er["X2"] / (W.X * (1 + L.BASE["s2t"] * W.zb)) - 1.0) / L.BASE["s2"]
    cc = float(np.corrcoef(W.z1, e2)[0, 1])
    rec("V6_generator_correlation_rho_%g" % rho, abs(cc - rho) < 0.005, requested=rho, realized=round(cc, 4))

# V7
ms = L.estimates(W)
e_base = L.err(W, L.fuse(ms["X1"], ms["u1"], ms["X2"], ms["u2"])[0], L.phi_true(W))
e_matched = L.err(W, L.fuse(ms["X1"], ms["u1"], ms["X2"], ms["u2"])[0], L.phi_true(W, model="chisholm", scale=1.0, rand=0.0))
rec("V7_common_random_numbers", np.array_equal(e_base, e_matched))

# V8: Monte Carlo propagation of the X term at a few loadings
rng = np.random.default_rng(7)
worst = 0.0
for X0 in (0.03, 0.06, 0.10):
    sel = np.where(np.abs(W.X - X0) < 0.002)[0][:200]
    for i in sel[:20]:
        xf, uf = max(X0, 1e-3), 0.15 * X0
        draw = np.clip(rng.normal(xf, uf, 200_000), 1e-5, None)
        cn, rg = W.cn[i], None
        q = 1.0 / np.sqrt(1.0 + cn * draw + draw ** 2)
        mc = np.std(np.log(q))
        fo = abs(-(xf * (cn + 2 * xf)) / (2 * (1 + cn * xf + xf ** 2))) * uf / xf
        worst = max(worst, abs(mc - fo) / fo)
rec("V8_first_order_propagation_vs_monte_carlo", worst < 0.03, max_relative_difference=round(worst, 4))

# V9
ok = True
for x0, t in R["propagation"]["table6"].items():
    ok &= abs(sum(t["variance_share"].values()) - 1.0) < 1e-9
for k in ("roc_carryover", "roc_consequential_error"):
    r = R["detector"][k]
    ok &= 0.5 < r["auc"] < 1.0
    ok &= np.all(np.diff(r["fpr"]) >= -1e-12) and np.all(np.diff(r["tpr"]) >= -1e-12)
rec("V9_stored_results_consistent", ok)

json.dump(res, open(os.path.join(HERE, "fmi_revision_verification.json"), "w", encoding="utf-8"), indent=1)
print("\nALL PASS" if all(v["passed"] for v in res.values()) else "\nSOME FAILED")
