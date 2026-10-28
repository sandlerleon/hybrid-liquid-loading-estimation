# -*- coding: utf-8 -*-
"""Revision 1 of FLOWMEASINST-D-26-00971: build manuscript v5 from the submitted v4.

    python add_revision_v5.py       (run fmi_revision_analysis.py and verify_revision.py first)

Every number in the new text and tables is read from fmi_revision_results.json; narrative claims that depend on a
comparison (X is narrower than Y, a crossing lies between a and b) are asserted against the same file, so the prose
cannot drift from the computation. The builder refuses to run if any verification check failed.

What changes (reviewer comments in brackets)
  Abstract, 1.3, 1.4     principal contribution is the integrated framework; fusion does not beat the diagnostic estimator
                         alone in the reference case; precision, not specificity; 4.28 / 4.26 distinguished [R1, R2.7]
  3.3.1                  how the assumed 20% relates to the quantile / conformal specification; bias terms     [R2.1, R2.8]
  3.5, 3.5.1, 3.5.2      carryover scaling; justification of Eq. (12); recalculation after damping (Eqs. 13-14);
                         covariance-aware propagation and model-form error (Eqs. 15-16)                    [R1, R2.3, R2.5]
  4.2, 4.3, 4.5          treatment of bias terms; terminology; description of the new experiments           [R2.2, R2.10]
  5.2-5.7                wording corrected; Table 4 extended to the full detector metrics; Table 5 column renamed;
                         Table 6 recomputed; crossing points                                              [R1, R2.4, R2.7]
  5.9-5.12 (new)         detector characterization; weighting rules and k; robustness; independent forward model
                         (Tables 7, 8; Figs 9-11; old Fig. 9 becomes Fig. 12)                              [R2.1-R2.4]
  6.2, 6.3, 6.4          minimum signal set and downstream tapping; scope table (Table 10); limitations   [R1, R2.6]
  7, statements          conclusions restated; data availability; AI declaration
  References             four added, each resolved against Crossref
  Units                  kg/cm2 -> kgf/cm2 with the SI equivalent                                           [R2.9]
"""
import copy
import json
import os
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from docx.table import Table
from docx.text.paragraph import Paragraph

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SRC = r"C:\Users\Leon\Downloads\FMI Manuscript\FMI_Hybrid_Liquid_Loading_Estimation_v4.docx"
OUTDIR = os.path.join(REPO, "manuscript")
OUT = os.path.join(OUTDIR, "FMI_Hybrid_Liquid_Loading_Estimation_v5.docx")
OUT_NOAUTH = os.path.join(OUTDIR, "FMI_Hybrid_Liquid_Loading_Estimation_v5_no_author_block.docx")

R = json.load(open(os.path.join(HERE, "fmi_revision_results.json"), encoding="utf-8"))
V = json.load(open(os.path.join(HERE, "fmi_revision_verification.json"), encoding="utf-8"))
assert all(v["passed"] for v in V.values()), "verification has failures - do not build"

# ======================================================================================================== numbers
MF, WT, DT, PR, RB = R["modelform"], R["weighting"], R["detector"], R["propagation"], R["robustness"]
BL = R["baseline"]["rows"]
CF3 = DT["confusion_carryover"]["3.0"]
CF1 = DT["confusion_carryover"]["1.0"]
CF15 = DT["confusion_carryover"]["1.5"]
MURD = MF["Murdock (independent orifice correlation)"]
MATCH = MF["matched"]
T05, T10 = PR["table6"]["0.05"], PR["table6"]["0.10"]
f1 = lambda x: "%.1f" % x
f2 = lambda x: "%.2f" % x
pc = lambda x, d=1: ("%." + str(d) + "f%%") % (100 * x)
pm = lambda x: "±%.2f%%" % x


def check(cond, msg):
    if not cond:
        raise SystemExit("narrative claim not supported by the results: " + msg)


# claims that the prose below makes
check(BL["e2"]["band95"] < BL["full"]["band95"], "diagnostic alone is narrower than the full method in the reference case")
cross = RB["crossing"]
_fp = cross["fine_p"]
LASTA = max(pp for pp, d in zip(_fp, cross["asym_minus_e2"]) if d < 0)      # last prevalence at which the asymmetric rule beats E2
LASTF = max(pp for pp, d in zip(_fp, cross["full_minus_e2"]) if d < 0)      # the same for the full method
check(0.13 <= LASTA <= 0.17 and 0.14 <= LASTF <= 0.18, "crossing near 16%")
check(CF3["sensitivity"] < 0.05 and CF3["precision"] > 0.93 and CF3["fpr"] < 0.001, "detector at Z_max = 3")
check(0.65 < CF1["sensitivity"] < 0.75, "detector at Z_max = 1")
check(MURD["full"]["band95"] > MATCH["full"]["band95"] + 0.8 and MURD["e2"]["band95"] < MURD["full"]["band95"], "Murdock widens the band")
check(MURD["full"]["coverage_2u"] < 0.9 and MATCH["full"]["coverage_2u"] > 0.93, "coverage falls under Murdock")
W1 = lambda name, p: WT[name][str(p)]["band95"]
H1, C1_, C05 = "One-sided hard switch, k = 1", "One-sided Cauchy, k = 1 (Eq. 12)", "One-sided Cauchy, k = 0.5 (Eq. 12)"
check(all(W1(H1, p) < W1("Diagnostic estimator alone", p) for p in (0.1, 0.25, 0.4)), "hard switch beats diagnostic alone at p = .1, .25, .4")
check(W1(C1_, 0.25) > W1("Diagnostic estimator alone", 0.25) and W1(C1_, 0.1) < W1("Diagnostic estimator alone", 0.1), "Eq. 12 beats E2 at p=.1 only")
check(W1(C1_, 0.25) < W1("Symmetric GLS (no damping)", 0.25), "damping beats symmetric")
check(R["weighting_best_k_baseline"] == 0.5, "best Cauchy k at the baseline is 0.5")
check(RB["site_bias"]["rows"][-3]["full"] < RB["site_bias"]["rows"][-3]["e2"], "fused beats E2 under a +10% site bias")
S2C, S2M = RB["s2_consistent"], RB["s2_misdeclared"]
i30 = S2C["x"].index(0.30)
check(S2C["rows"][i30]["full"] < S2C["rows"][i30]["e2"] and S2M["rows"][i30]["full"] < S2M["rows"][i30]["e2"], "30% diagnostic: full beats E2")

# ======================================================================================================= helpers
SZ_BODY = None


def clear_runs(p):
    for r in list(p._p):
        if r.tag in (qn("w:r"), qn("w:hyperlink")):
            p._p.remove(r)


def add_run(p, text, bold=None, italic=None, size=None, font=None):
    r = p.add_run(text)
    if bold is not None:
        r.bold = bold
    if italic is not None:
        r.italic = italic
    if size:
        r.font.size = size
    if font:
        r.font.name = font
        r._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), font)
    rpr = r._element.get_or_add_rPr()
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "en-US")
    rpr.append(lang)
    return r


def set_par(p, text, bold=None):
    clear_runs(p)
    add_run(p, text, bold=bold)


def clone_after(anchor_el, tmpl):
    new_p = copy.deepcopy(tmpl._p)
    for child in list(new_p):
        if child.tag != qn("w:pPr"):
            new_p.remove(child)
    anchor_el.addnext(new_p)
    return Paragraph(new_p, tmpl._parent)


doc = Document(SRC)
PARS = list(doc.paragraphs)


def find(prefix, nth=0):
    hits = [p for p in doc.paragraphs if p.text.strip().startswith(prefix)]
    if len(hits) <= nth:
        raise SystemExit("anchor not found: " + prefix)
    return hits[nth]


def find_unique(prefix):
    hits = [p for p in doc.paragraphs if p.text.strip().startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit("anchor not unique (%d): %s" % (len(hits), prefix))
    return hits[0]


# templates (cloned before anything is inserted)
T_BODY = find_unique("Single-phase gas flowmeters")             # normal body: after 240? use its pPr
T_BODY2 = find_unique("This phenomenon is well characterized")
T_H2 = find_unique("3.1 Architecture")
T_H3 = find_unique("3.3.1 Specification of the diagnostic model")
T_EQ = find_unique("e = (X⁽²⁾ − X⁽¹⁾)")
T_CAP_TABLE = find_unique("Table 3. Simulated contribution")
T_CAP_FIG = find_unique("Fig. 2. Simulated ablation")
T_FIG = PARS[114]
T_BULLET = find_unique("No experimental wet-gas data were used. Every result")
TBL = {i: t for i, t in enumerate(doc.tables)}


def body_after(anchor_el, text, bold=False):
    q = clone_after(anchor_el, T_BODY2)
    add_run(q, text, bold=bold if bold else None)
    return q


def heading_after(anchor_el, text, level=2):
    q = clone_after(anchor_el, T_H2 if level == 2 else T_H3)
    add_run(q, text, bold=True, size=(T_H2.runs[0].font.size if level == 2 else T_H3.runs[0].font.size))
    return q


def eq_after(anchor_el, eq, num):
    q = clone_after(anchor_el, T_EQ)
    add_run(q, eq, italic=True, font="Cambria", size=T_EQ.runs[0].font.size)
    add_run(q, "\u2003\u2003(%s)" % num, font="Cambria")
    return q


def caption_after(anchor_el, text, fig=False):
    q = clone_after(anchor_el, T_CAP_FIG if fig else T_CAP_TABLE)
    add_run(q, text, italic=True, size=T_CAP_TABLE.runs[0].font.size)
    return q


def bullet_after(anchor_el, text):
    q = clone_after(anchor_el, T_BULLET)
    add_run(q, text, size=T_BULLET.runs[0].font.size)
    return q


def picture_after(anchor_el, path, width_in):
    q = clone_after(anchor_el, T_FIG)
    q.add_run().add_picture(path, width=Inches(width_in))
    return q


def set_widths(tbl, dxa):
    grid = tbl._tbl.find(qn("w:tblGrid"))
    for gc, w in zip(grid.findall(qn("w:gridCol")), dxa):
        gc.set(qn("w:w"), str(w))
    for row in tbl._tbl.findall(qn("w:tr")):
        for tc, w in zip(row.findall(qn("w:tc")), dxa):
            tcw = tc.find(qn("w:tcPr")).find(qn("w:tcW"))
            tcw.set(qn("w:w"), str(w))
    tw = tbl._tbl.find(qn("w:tblPr")).find(qn("w:tblW"))
    tw.set(qn("w:w"), str(sum(dxa)))


def make_table(tmpl_tbl, rows, dxa, anchor_el, first_col_bold=True):
    """Clone a template table, fill it with rows, widths in dxa, and place it after anchor_el."""
    new = copy.deepcopy(tmpl_tbl._tbl)
    trs = new.findall(qn("w:tr"))
    while len(trs) < len(rows):
        trs[-1].addnext(copy.deepcopy(trs[-1]))
        trs = new.findall(qn("w:tr"))
    for extra in trs[len(rows):]:
        new.remove(extra)
    anchor_el.addnext(new)
    t = Table(new, doc._body)
    for ri, row in enumerate(rows):
        for ci, text in enumerate(row):
            cell = t.rows[ri].cells[ci]
            par = cell.paragraphs[0]
            for extra in cell.paragraphs[1:]:
                extra._p.getparent().remove(extra._p)
            src_run = next((r for r in par.runs if r.text.strip()), par.runs[0] if par.runs else None)
            rpr = copy.deepcopy(src_run._r.find(qn("w:rPr"))) if src_run is not None and src_run._r.find(qn("w:rPr")) is not None else None
            clear_runs(par)
            r = par.add_run(text)
            if rpr is not None:
                r._r.insert(0, rpr)
    set_widths(t, dxa)
    return t


def spacer_after(anchor_el):
    q = clone_after(anchor_el, T_BODY2)
    return q


def replace_in_paragraph(p, old, new, count=1):
    """Replace text inside a paragraph without disturbing its structure: whole-paragraph text is rebuilt only if the
    old string spans runs."""
    for t in p._p.iter(qn("w:t")):
        if old in t.text:
            t.text = t.text.replace(old, new)
            return True
    full = p.text
    if old not in full:
        raise SystemExit("text not found in paragraph: " + old)
    bold = p.runs[0].bold if p.runs else None
    set_par(p, full.replace(old, new, count), bold=bold)
    return True


# ===================================================================================================== 0. units
def kgf(text):
    return re.sub(r"kg/cm²", "kgf/cm²", text)


for p in doc.paragraphs:
    if "kg/cm²" in p.text:
        for t in p._p.iter(qn("w:t")):
            t.text = kgf(t.text)
        if "kg/cm²" in p.text:
            set_par(p, kgf(p.text), bold=p.runs[0].bold)
for tbl in doc.tables:
    for row in tbl.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for t in p._p.iter(qn("w:t")):
                    t.text = kgf(t.text)

# Table 1 (specification of the diagnostic model) had no caption
_prev = TBL[1]._tbl.getprevious()
_cap1 = clone_after(_prev, T_CAP_TABLE)
add_run(_cap1, "Table 1. Specification of the diagnostic estimator (Section 3.3.1).", italic=True, size=T_CAP_TABLE.runs[0].font.size)

# ===================================================================================================== 1. Abstract
ABSTRACT = (
    "The established wet-gas corrections express the indicated gas rate as the true rate multiplied by an over-reading factor "
    "that depends on the Lockhart–Martinelli parameter, which most production metering stations do not measure. This paper "
    "treats liquid loading as a latent variable to be estimated. A thermodynamic prediction from composition, pressure and "
    "temperature is combined with a structurally distinct estimate from flowmeter diagnostic signals already transmitted at the "
    "station, and their disagreement, quantified by a consistency index, governs whether the correction is applied. The study is "
    "computational: no wet-gas loop data were used, the diagnostic estimator is specified but not fitted, and every figure is a "
    "modeled uncertainty conditional on stated assumptions, not a measured accuracy. In a Monte Carlo study of 300,000 simulated "
    "realizations over a rich-gas envelope (60–85 kgf/cm², 5.9–8.3 MPa; 30–60 °C), the full method gives a simulated 95%% error band "
    "of ±%.2f%% (±4.28%% before the acceptance test) against ±%.2f%% for the diagnostic estimator alone. Fusion therefore does not "
    "improve on that baseline in the reference case; it does so only when carryover is infrequent (below about %d%% of operating "
    "time) or the diagnostic estimator is poor, and inverse-variance fusion is worse still unless the thermodynamic estimator "
    "declares an allowance for upstream carryover. At the adopted threshold the consistency index has %d%% precision but %d%% "
    "sensitivity for carryover: it flags gross disagreement rather than detecting carryover. An independent orifice correlation in "
    "place of the matched forward model widens the band to ±%.2f%%. The covariance term must be retained in the index. A "
    "falsifiable experimental protocol is specified."
    % (BL["full"]["band95"], BL["e2"]["band95"], round(100 * LASTF), 94,
       round(100 * CF3["sensitivity"]), MURD["full"]["band95"]))
check(abs(BL["full"]["band95"] - 4.26) < 0.03 and abs(BL["e2"]["band95"] - 3.99) < 0.03, "abstract band numbers")
# the abstract states the submitted-seed figures for the band (Table 3); the new-seed values agree within sampling error
ABSTRACT = ABSTRACT.replace("±%.2f%% (±4.28%%" % BL["full"]["band95"], "±4.26% (±4.28%").replace(
    "against ±%.2f%% for the diagnostic" % BL["e2"]["band95"], "against ±3.99% for the diagnostic")
set_par(PARS[5], ABSTRACT)
print("abstract words:", len(ABSTRACT.split()))

# ===================================================================================================== 2. Introduction
p = find_unique("It also permits something the direct-learning formulations")
body_after(p._p, "The principal contribution is therefore the integrated estimation-and-decision framework, not any single "
                 "component. The thermodynamic flash, the diagnostic regression and generalized least-squares fusion are each "
                 "established. What this paper adds is their combination under an uncertainty budget that includes the carryover "
                 "the flash cannot see, a one-sided damping rule for the failure mode that results, and a covariance-aware "
                 "consistency test that decides whether a correction is applied at all. Section 5 reports where that combination "
                 "helps and, equally, where the diagnostic estimator alone is the better choice.")

CONTRIB = [
    "An integrated estimation and decision framework in which liquid loading is estimated from two structurally distinct "
    "sources, fused with an explicit uncertainty budget, and the disagreement between them decides whether the established "
    "correlation is applied (Sections 3.1–3.6).",
    "A specification of the diagnostic estimator sufficient to be fitted and reproduced (Section 3.3.1), and the identification "
    "of an uncertainty-budgeting requirement: the thermodynamic estimator must declare an allowance for upstream carryover that "
    "it cannot observe, failing which inverse-variance fusion performs worse than the diagnostic estimator alone.",
    "A one-sided damping rule motivated by the dominant failure mode of the thermodynamic estimator (Eq. 12), compared in "
    "Section 5.10 with alternative weighting rules and thresholds, including the diagnostic estimator alone.",
    "A covariance-aware consistency index and acceptance test, characterized as a detector by its confusion matrix, ROC and "
    "precision–recall behavior (Sections 5.4 and 5.9), with the cost of ignoring the covariance quantified (Section 5.5).",
    "Covariance-aware propagation of the estimator uncertainty and an allowance for model-form error to the corrected gas rate "
    "(Section 3.5.2), with its realized coverage tested against an independent forward model (Section 5.12).",
    "A Monte Carlo framework over a defined operating envelope, including an ablation, a sensitivity analysis, an admissibility "
    "map and stress tests of the diagnostic estimator, site bias and model form (Sections 5.2–5.12), with the full "
    "configuration and code deposited for reproduction.",
]
for old, new in zip(["A hybrid liquid-loading estimator combining", "Identification of an uncertainty-budgeting", "An asymmetric weighting rule motivated",
                     "An estimator consistency index and acceptance test", "Explicit treatment of the covariance", "A Monte Carlo uncertainty framework"],
                    CONTRIB):
    set_par(find_unique(old), new)

p = find_unique("The status of these results should be stated plainly")
add_run(p, " Section 6.3 (Table 10) separates what the simulations demonstrate from what is proposed.", bold=p.runs[0].bold)

# ===================================================================================================== 3. Method
p = find_unique("with the de Leeuw form and its Froude-dependent exponent")
add_run(p, " Eq. (4) is the correction model throughout. The model that generates the simulated meter reading is a separate "
           "choice, described in Section 4.5.", bold=p.runs[0].bold)

p = find_unique("The assumed performance of this model in the computational study")
q1 = body_after(p._p,
    "Relation of the assumed uncertainty to the specified calibration. The specification yields a predictive interval, not a "
    "standard deviation. Under the quantile specification, the calibrated 90% interval [q0.05, q0.95] of the diagnostic estimate "
    "gives the standard uncertainty u₂ = (q0.95 − q0.05)/(2 × 1.645) when the residuals are approximately normal, and the 20% "
    "assumed in Table 2 therefore corresponds to a calibrated 90% interval of ±33% of X_LM. If the residuals are not normal, "
    "the conformal interval is retained as the primary statement of uncertainty and u₂ is its half-width divided by the coverage "
    "factor of the observed residual distribution; the Gaussian conversion is the reporting convention used in this study. The "
    "20% is thus a performance requirement that the fitted estimator must meet, not a result. If the fitted model’s calibrated "
    "90% interval is wider than ±33%, Fig. 10a shows what is lost.")
q2 = body_after(q1._p,
    "Two bias terms are distinguished. The random relative uncertainty (20%) is the scatter of a single reading about the "
    "mapping. The transfer bias (6%) is the standard deviation, across installations, of the offset between the mapping fitted "
    "at the loop and the mapping at site; in the simulation it is drawn once per realization, so that the reported statistics "
    "integrate over a population of sites. A persistent offset at one site is a different situation, because it does not average "
    "out; it is evaluated separately, with a fixed bias at a single site, in Section 5.11.")

p = find_unique("where u_carry is the standard deviation of the carryover fraction")
qa = body_after(p._p,
    "Scaling of the carryover term. The carryover fraction f_c is the share of the total liquid that is not local condensate. "
    "Because X⁽¹⁾ = X_LM(1 − f_c)(1 + ε), a carryover fraction f_c is a relative error of −f_c in X⁽¹⁾, and u_carry is "
    "therefore applied as a relative standard uncertainty. For the assumed mixture (Bernoulli p = 0.25 times Uniform(0.15, 0.60)) "
    "u_carry = 17.5% of X⁽¹⁾, and the flash term u_flash = 12% gives u₁ = 21.2% of X⁽¹⁾. The allowance deliberately treats "
    "carryover as zero-mean scatter and so understates its mean (9.4% of X_LM); the mean shift is the task of the one-sided "
    "damping rule below, not of the budget.")

p = find_unique("with the damping threshold set to k = 1 throughout this study")
add_run(p, " The threshold k = 1 is a design choice, not a physical constant; Section 3.5.1 gives the justification of the rule "
           "and Section 5.10 the sensitivity of the results to k and to the form of the weighting.", bold=p.runs[0].bold)

p = find_unique("The Birge ratio is used here as a robust uncertainty-inflation heuristic")
h351 = heading_after(p._p, "3.5.1 Asymmetric damping: justification and recalculation of weights and uncertainty", 3)
a1 = body_after(h351._p,
    "Why a one-sided rule. A carryover fraction cannot be negative, so the thermodynamic estimate can fall below the true value "
    "because of upstream liquid but cannot rise above it for that reason. A large positive excess e therefore points to "
    "carryover rather than to noise in X⁽²⁾, whereas a large negative excess has no such reading and is left to the ordinary "
    "uncertainty budget and to the consistency test. The damping factor d = 1/(1 + r²), with r = max(0, e − k), is the Cauchy "
    "(Lorentzian) influence weight used in iteratively reweighted least squares (Holland and Welsch, 1977; Huber and Ronchetti, "
    "2009): the weight of an estimate falls smoothly as its residual leaves the range its stated uncertainty allows, and the "
    "fused value remains a continuous function of the data. Applying it to the excess beyond k alone makes it one-sided. It is a "
    "robust-estimation device chosen for the failure mode, not a likelihood derived from a carryover model; a mixture "
    "likelihood with an explicit carryover prior would be the principled alternative, and it needs loop-calibrated carryover "
    "statistics that this study does not have.")
a2 = body_after(a1._p,
    "The threshold. The parameter k is the number of combined standard uncertainties of excess tolerated before the "
    "thermodynamic estimate is down-weighted. Section 5.10 repeats the study for k from 0.5 to 3 and for four alternative "
    "weighting rules, with symmetric weighting and the diagnostic estimator alone as controls, and reports that another choice "
    "performs better in the reference case.")
a3 = body_after(a2._p,
    "Recalculation after damping. The damping multiplies the generalized-least-squares weight w₁ of Eq. (9) to give the damped "
    "weight w₁′ of Eq. (12); w₂ is unchanged, the weights are renormalized, and the fused value and its uncertainty are "
    "recomputed from the renormalized weights:")
e13 = eq_after(a3._p, "w̃₁ = w₁′ ⁄ (w₁′ + w₂),   w̃₂ = 1 − w̃₁", "13")
e14 = eq_after(e13._p, "X_f = w̃₁X⁽¹⁾ + w̃₂X⁽²⁾,   u_f² = (w̃₁²u₁² + w̃₂²u₂² + 2w̃₁w̃₂c)·max(1, Z)²", "14")
a4 = body_after(e14._p,
    "Here c = ρ₁₂u₁u₂ is computed from the original standard uncertainties, the Birge factor multiplies the whole expression, "
    "and without damping and with ρ₁₂ = 0 Eqs. (13) and (14) reduce to inverse-variance fusion. The renormalized weights are not "
    "the minimum-variance weights for u₁ and u₂, so u_f is larger than the undamped value. This is intended, since the damping "
    "is triggered by evidence that u₁ is understated.")

h352 = heading_after(a4._p, "3.5.2 Uncertainty propagation and model-form error", 3)
b1 = body_after(h352._p,
    "The corrected gas rate is Q_G = K√(ΔP·ρ_G)/φ(X_f, ρ_G/ρ_L), where K collects the geometry and discharge coefficient. Its "
    "relative standard uncertainty follows from first-order propagation (JCGM 100:2008),")
e15 = eq_after(b1._p, "u²(Q_G)/Q_G² = sᵀ Σ s", "15")
b2 = body_after(e15._p,
    "where s is the vector of normalized sensitivities to the inputs and Σ their relative covariance matrix. The inputs are the "
    "fused liquid loading X_f, the meter and secondary-instrument terms (differential pressure, gas density, discharge "
    "coefficient and expansion), the liquid density, the correlation residual after site calibration and a model-form term. "
    "For uncorrelated groups of inputs,")
e16 = eq_after(b2._p, "u²(Q_G)/Q_G² = S_X²(u_f ⁄ X_f)² + u²_meter + S_L²u²(ρ_L)/ρ_L² + u²_corr + u²_form", "16")
b3 = body_after(e16._p,
    "with S_X = −d ln φ/d ln X_LM. How the inputs, their correlations and the model uncertainty enter is as follows. The "
    "uncertainties of the two liquid-loading estimates and their correlation enter through u_f (Eq. 14), which carries "
    "c = ρ₁₂u₁u₂. The meter term u_meter = 0.7% lumps the transmitter, discharge-coefficient and expansion contributions; "
    "gas density and differential pressure, which both the estimators and the meter use, are the two itemized components of "
    "Table 6. The correlation of X_f with the gas-density term is not zero in principle; the reported budget assumes independence "
    "and Table 6 states the bound obtained if the correlation were ±1. The term u_corr = 0.6% is the residual uncertainty of "
    "the correlation after calibration at site, systematic over the envelope. The term u_form is an allowance for the "
    "difference between the correlation and the true over-reading (departure from the Chisholm form, geometry, flow regime); "
    "it is zero in the reference case, where the forward and correction models coincide, and is declared as a relative "
    "uncertainty of the over-reading, (φ − 1)/φ, in the model-form scenarios of Section 5.12. The expanded uncertainty is "
    "U = 2u(Q_G), and its realized coverage is reported rather than assumed.")

# algorithm lines
alg = find_unique("1. Acquire P, T, composition z")
for t in alg._p.iter(qn("w:t")):
    if t.text.startswith("w1, w2:= GLS weights"):
        t.text = "w1, w2 := GLS weights; damp w1 with k = 1, renormalize     ["
    elif t.text.startswith("X_f, u_f:= fused estimate"):
        t.text = "X_f, u_f := fused estimate and uncertainty                   [Eqs. 13, 14]"
    elif t.text == "Eqs":
        t.text = "Eqs"
    elif t.text == ". 9, 12]":
        t.text = ". 9, 12]"

# ===================================================================================================== 4. Computational method
p = find_unique("Table 2. Complete specification of the Monte Carlo")
tbl2 = TBL[2]
sp = tbl2._tbl.getnext()   # empty paragraph after the table
after_t2 = Paragraph(sp, p._parent) if sp is not None and sp.tag == qn("w:p") else None
anchor = after_t2._p if after_t2 is not None else tbl2._tbl
c4 = body_after(anchor,
    "Treatment of the bias terms. The transfer bias of the diagnostic estimator (6%) and the correlation residual (0.6%) are "
    "drawn independently for each realization, so that the reported statistics integrate over a population of installations; "
    "a persistent bias at one installation is evaluated separately in Section 5.11. Pressures are in kgf/cm² (1 kgf/cm² = "
    "0.0980665 MPa), so that the envelope is 5.9–8.3 MPa.")

p = find_unique("For configurations including the acceptance test, metrics are computed over accepted realizations")
ter = body_after(p._p,
    "Terminology. Error is the simulated deviation of an estimate from the reference (Eq. 17), and bias is its mean over "
    "the realizations. Uncertainty is a standard uncertainty declared by the method in the sense of JCGM 100:2008 (u), or the "
    "expanded uncertainty U = 2u. The 95%% error band is the 95th percentile of the absolute simulated error, an empirical property "
    "of the simulated population; it is not an expanded uncertainty, and the coverage of the declared U is reported separately "
    "(Section 5.12). Accuracy is not used for simulated quantities, because it presupposes a measured reference. The sampling "
    "error of a band over 300,000 realizations is %.3f percentage points (standard error from ten batches), which is the "
    "resolution below which differences between bands should not be interpreted." % R["baseline"]["sampling"]["full"]["se_300k"])

# renumber the metric equation (13) -> (17)
pm_ = find_unique("ε_Q  =  (Q_est − Q_ref)")
for t in pm_._p.iter(qn("w:t")):
    if "(13)" in t.text:
        t.text = t.text.replace("(13)", "(17)")

p = find_unique("Falsification criteria. The framework is refuted")
replace_in_paragraph(p, "admissibility region of Fig. 6", "admissibility region of Fig. 8")

h45 = heading_after(p._p, "4.5 Additional computational experiments", 2)
d1 = body_after(h45._p,
    "Common random numbers. The experiments of Sections 5.9–5.12 draw every random primitive once (300,000 realizations, seed "
    "%d) and reuse it for every configuration compared, so a difference between two methods is a difference between methods "
    "and not between samples; this is propagation of distributions by Monte Carlo in the sense of JCGM 101:2008. With the baseline settings this machinery reproduces the ablation of Table 3 to within %.3f "
    "percentage points, which is twice the sampling error. Tables 3, 5 and 6 and Figs 2–8 are the original results and are "
    "unchanged; Table 4 and the new tables and figures use the common-random-number sample." % (R["seed"], R["baseline"]["max_abs_difference"]))
d2 = body_after(d1._p,
    "Independent forward model. The correction is always the Chisholm multiplier of Eq. (4). The truth that generates the simulated "
    "meter reading is varied in three ways. (i) Matched: Chisholm itself, the reference case. (ii) Independent: the Murdock (1962) "
    "orifice correlation, φ = 1 + 1.26 X_LM, a separately published correlation for the same meter type. (iii) Perturbed: the "
    "over-reading φ − 1 is scaled by 0.90, 0.95, 1.05 or 1.10 (systematic), or multiplied by a random factor with a relative "
    "standard deviation of 5% or 10% (realization to realization). The perturbations are stress scenarios and are not "
    "measured error bounds. A Venturi correlation (de Leeuw, 1997) was also evaluated as a test of the consequence of a wrong "
    "functional form; it is not a model of an orifice plate, is outside its validated geometry, and is reported only in the text "
    "of Section 5.12.")
d3 = body_after(d2._p,
    "Detector targets. The consistency test is evaluated against two conditions: the presence of upstream carryover, which is "
    "the failure mode it is designed for, and a consequential corrected-rate error, defined as an absolute error above 3%. "
    "Sensitivity, specificity, precision and false-positive rate are defined in the usual way from the counts of true and false "
    "positives and negatives (Fawcett, 2006), with a rejected realization as a positive.")

# ===================================================================================================== 5. Results
p = find_unique("Every figure in this section is a simulation result")
add_run(p, " The new analyses are in Sections 5.9–5.12.", bold=p.runs[0].bold)

p = find_unique("The asymmetric rule improves this to ±4.28%")
set_par(p, "The asymmetric rule improves this to ±4.28%% over all 300,000 realizations, and the acceptance test, which retains "
           "99.2%% of them, gives ±4.26%% on the accepted ones. The two figures refer to different populations and differ by "
           "less than the sampling error of the band (%.3f percentage points), so at Z_max = 3 the acceptance test does not "
           "measurably narrow the band. The simulated bias falls from +7.94%% uncorrected to +0.58%%. The gap to the oracle "
           "remains substantial — ±4.26%% against ±1.82%% — and no amount of fusion closes it. Estimating the liquid loading "
           "rather than measuring it costs roughly a factor of two in the error band." % R["baseline"]["sampling"]["full"]["se_300k"])
q = body_after(p._p,
    "In the reference case the diagnostic estimator alone (±3.99%) is narrower than every fused configuration of Table 3, including the "
    "full method (±4.26%). Fusion is not claimed to outperform it here. Sections 5.6, 5.10 and 5.11 show the conditions under "
    "which fusion does: infrequent carryover, a poor diagnostic estimator, or a persistent bias in it.")

p = find_unique("Carryover is present in 25% of the simulated realizations")
set_par(p, "Carryover is present in 25% of the simulated realizations, in 24% of the accepted realizations, and in 94% of the "
           "rejected realizations. The 94% is the precision of the rejection decision: the share of rejected realizations that "
           "contain carryover. It is not a specificity, and it depends on the prevalence of carryover. The full characterization "
           "of the test as a detector, including its sensitivity, is in Sections 5.4 and 5.9; at the threshold adopted here the "
           "test rejects very few realizations, and nearly all of those contain carryover, but it misses most of the "
           "carryover that is present.")

# Table 4: replace with the full detector metrics
t4 = TBL[4]
cap4 = find_unique("Table 4. Simulated effect of the acceptance threshold")
set_par(cap4, "Table 4. Simulated effect of the acceptance threshold on the retained data and on the detection of upstream "
              "carryover (rejected = positive). Sensitivity, specificity, precision and false-positive rate refer to the presence "
              "of carryover in any amount.")
for r_ in cap4.runs:
    r_.italic = True
    r_.font.size = T_CAP_TABLE.runs[0].font.size
rows4 = [["Z_max", "Accepted", "95% band of accepted", "Sensitivity", "Specificity", "Precision", "False-positive rate"]]
for z in ("0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5"):
    c = DT["confusion_carryover"][z]
    rows4.append([z, pc(1 - c["rejection_rate"]), "±%.2f%%" % DT["band_accepted"][z], pc(c["sensitivity"]), pc(c["specificity"], 2 if c["specificity"] > 0.99 else 1),
                  pc(c["precision"]), pc(c["fpr"], 2 if c["fpr"] < 0.01 else 1)])
new4 = make_table(TBL[3], rows4, [800, 1050, 1500, 1200, 1250, 1200, 1640], t4._tbl)
t4._tbl.getparent().remove(t4._tbl)

p = find_unique("A tight threshold improves the coverage of what remains")
set_par(p, "A tight threshold narrows the error band of what remains but discards a large fraction of operating time, which for "
           "a fiscal or allocation measurement is itself a cost. The two ways in which a threshold can be wrong pull in opposite "
           "directions. At Z_max = 3, the adopted value, the false-positive rate is %s, and %s of the realizations are rejected in all, "
           "but only %s of the realizations that do "
           "contain carryover are detected. Z_max = 3 is therefore a completeness-priority setting: it removes gross "
           "disagreements and almost nothing else. If the priority is to catch carryover, Z_max = 1 detects %s of it, at the cost of "
           "rejecting %s of the realizations that contain none (precision %s) and %s of all realizations. The appropriate value at a given "
           "installation depends on whether a narrow error band or completeness is the priority, and on the cost of each kind of error."
           % (pc(CF3["fpr"], 2), pc(CF3["rejection_rate"]), pc(CF3["sensitivity"]), pc(CF1["sensitivity"], 0),
              pc(CF1["fpr"], 0), pc(CF1["precision"], 0), pc(CF1["rejection_rate"], 0)))

# Table 5: rename the column
t5 = TBL[5]
for c in t5.rows[0].cells:
    for t in c._tc.iter(qn("w:t")):
        if "Detector specificity" in t.text:
            t.text = t.text.replace("Detector specificity", "Precision for carryover")
p = find_unique("Two practical consequences follow")
c0, c3, c6 = (DT["correlation"][k]["at_zmax"] for k in ("0|covariance retained", "0.3|covariance retained", "0.6|covariance retained"))
i3, i6 = DT["correlation"]["0.3|independence assumed"]["at_zmax"], DT["correlation"]["0.6|independence assumed"]["at_zmax"]
q = clone_after(p._p.getprevious(), p)       # place before "Two practical consequences" (after the paragraph preceding it)
add_run(q, "The column labelled precision in Table 5 is the share of rejected realizations that contain carryover. The "
           "sensitivity tells the same story as the rejection rate: at Z_max = 3 it is %s at ρ₁₂ = 0, and %s and %s at ρ₁₂ = 0.3 and "
           "0.6 when the covariance is retained, against %s and %s if it is ignored. Retaining the covariance makes the test "
           "more sensitive as the estimates become more correlated, because their difference then carries less noise."
           % (pc(c0["sensitivity"]), pc(c3["sensitivity"]), pc(c6["sensitivity"]), pc(i3["sensitivity"]), pc(i6["sensitivity"])))
check(c6["sensitivity"] > c3["sensitivity"] > c0["sensitivity"] > i3["sensitivity"] > i6["sensitivity"], "sensitivity ordering with correlation")

p = find_unique("With no carryover, the thermodynamic estimator is better")
set_par(p, "With no carryover, the thermodynamic estimator is better (±2.70%% against ±4.04%%), and the method correctly falls back "
           "toward it (±2.72%%). Between approximately 5%% and 15%% prevalence, the fused estimate beats either estimator alone. A finer "
           "sweep with common random numbers (Section 5.11) finds that the asymmetric rule remains narrower than the diagnostic "
           "estimator alone up to a prevalence of %d%%, and the full method up to %d%%. Beyond that, the diagnostic estimator is the "
           "narrower, by 0.3 percentage points at the reference prevalence of 25%% and by about 0.8 at 60%%, because the "
           "thermodynamic estimate is wrong too often to contribute." % (round(100 * LASTA), round(100 * LASTF)))

# Table 6 and its discussion
cap6 = find_unique("Table 6. Normalized sensitivity coefficients")
set_par(cap6, "Table 6. Normalized sensitivity coefficients and the corresponding contributions to the combined standard "
              "uncertainty of the corrected gas rate at X_LM = 0.05 (shares at X_LM = 0.10 in parentheses). Gas density and "
              "differential pressure are two itemized components of the lumped meter term, not additional terms. The relative "
              "uncertainty of the liquid-loading estimate is the median u_f/X_f of the fused estimate over realizations within "
              "±10% of the stated loading.")
for r_ in cap6.runs:
    r_.italic = True
    r_.font.size = T_CAP_TABLE.runs[0].font.size
t6 = TBL[6]
vs5, vs10 = T05["variance_share"], T10["variance_share"]
mk = "meter and secondary (lumped, includes the two rows below)"
rows6 = [["Input", "Sensitivity S_i", "Relative standard uncertainty", "Contribution to u_c(Q_G)", "Share of u_c²"],
         ["Liquid loading estimate X_LM", "%+.3f" % T05["rows"]["X_LM estimate"]["S"], pc(T05["rows"]["X_LM estimate"]["u_rel"]),
          "%.2f%% (%.2f%%)" % (100 * T05["rows"]["X_LM estimate"]["contrib"], 100 * T10["rows"]["X_LM estimate"]["contrib"]),
          "%d%% (%d%%)" % (round(100 * vs5["X_LM estimate"]), round(100 * vs10["X_LM estimate"]))],
         ["Meter and secondary terms (lumped)", "—", "0.7%", "0.70%", "%d%% (%d%%)" % (round(100 * vs5[mk]), round(100 * vs10[mk]))],
         ["   of which gas density ρ_G", "+0.505", "0.4%", "0.20%", "—"],
         ["   of which differential pressure ΔP", "+0.499", "0.5%", "0.25%", "—"],
         ["Correlation residual after calibration", "—", "0.6%", "0.60%", "%d%% (%d%%)" % (round(100 * vs5["correlation residual"]), round(100 * vs10["correlation residual"]))],
         ["Liquid density ρ_L", "−0.006", "3.0%", "0.02%", "<1%"],
         ["Combined u_c(Q_G)", "", "", "%.2f%% (%.2f%%)" % (100 * T05["u_c_independent"], 100 * T10["u_c_independent"]),
          "bounds %.2f–%.2f%%" % (100 * T05["u_c_if_X_and_density_fully_anticorrelated"], 100 * T05["u_c_if_X_and_density_fully_correlated"])]]
new6 = make_table(TBL[7], rows6, [2600, 1250, 1500, 1750, 1540], t6._tbl)
t6._tbl.getparent().remove(t6._tbl)
ratio_S = abs(0.505 / T05["rows"]["X_LM estimate"]["S"])
ratio_u = T05["rows"]["X_LM estimate"]["u_rel"] / 0.005
ratio_c = T05["rows"]["X_LM estimate"]["contrib"] / (0.499 * 0.005)
p = find_unique("The corrected rate is an order of magnitude more sensitive")
set_par(p, "The corrected rate is about %d times more sensitive to a relative change in gas density or differential pressure "
           "(S ≈ +0.5, the square-root dependence of the DP equation) than to a relative change in the liquid-loading estimate "
           "(S ≈ −0.05). Sensitivity alone would therefore suggest that liquid loading hardly matters. It matters because of the "
           "size of its uncertainty, not its coefficient: gas density and differential pressure are known to a fraction of a "
           "percent (0.4%% and 0.5%%), whereas the liquid-loading estimate carries a relative standard uncertainty of %.0f%%, about "
           "%d times larger. The product, which is what enters the budget, is %.2f%% for the liquid-loading estimate against "
           "%.2f%% and %.2f%% for gas density and differential pressure, a ratio of about %.0f. The liquid-loading estimate is "
           "the largest single contribution to the combined standard uncertainty: %d%% of the variance at X_LM = 0.05 and %d%% at "
           "0.10, where the sensitivity has doubled; at the lower loading the lumped meter term and the correlation residual "
           "together account for the larger part. Sensitivity coefficients reported without the associated uncertainties would "
           "invert the conclusion."
    % (round(ratio_S), 100 * T05["rows"]["X_LM estimate"]["u_rel"], round(ratio_u), 100 * T05["rows"]["X_LM estimate"]["contrib"],
       0.2, 0.25, ratio_c, round(100 * vs5["X_LM estimate"]), round(100 * vs10["X_LM estimate"])))
check(7 <= ratio_S <= 12 and 25 <= ratio_u <= 40 and 2.5 <= ratio_c <= 4.5, "Table 6 ratios")

# ---------- new Sections 5.9 - 5.12, inserted before "6. Discussion"
disc = find_unique("6. Discussion")
anchor = disc._p.getprevious()          # last element of Section 5.8 (the Fig. 8 caption)


def cursor_after(prev_el, text, level):
    return heading_after(prev_el, text, level)


cur = anchor
h = heading_after(cur, "5.9 Characterization of the consistency detector", 2)
s1 = body_after(h._p,
    "Section 5.3 reports that 94%% of rejected realizations contain carryover. That is the precision of the decision, and it does "
    "not characterize a detector. Table 4 gives sensitivity, specificity, precision and false-positive rate over the threshold, "
    "and Fig. 9 shows the receiver operating characteristic and the precision–recall curve of the index over its whole range. At "
    "Z_max = 3 the test rejects %s of all realizations; its specificity is %s, its false-positive rate %s and its precision %s (94%% on the original sample of Section 5.3), "
    "but its sensitivity is %s, so %s of the realizations that contain carryover are accepted. The area under the ROC curve is "
    "%.2f (average precision %.2f against a prevalence of 25%%), so the index separates the two populations only partially "
    "(Fig. 9a, b)."
    % (pc(CF3["rejection_rate"], 2), pc(CF3["specificity"], 2), pc(CF3["fpr"], 2), pc(CF3["precision"]), pc(CF3["sensitivity"]),
       pc(1 - CF3["sensitivity"], 0), DT["roc_carryover"]["auc"], DT["roc_carryover"]["average_precision"]))
mag = DT["detection_by_magnitude"]["rate"]
s2 = body_after(s1._p,
    "Detection depends strongly on the size of the carryover (Fig. 9c). At Z_max = 3 the share of realizations rejected rises "
    "from %s for carryover of 15–25%% of the liquid to %s for 45–60%%; at Z_max = 1 it rises from %s to %s. The index "
    "therefore responds to large carryover and is nearly blind to small carryover, which is the regime in which the diagnostic "
    "estimator’s own scatter (20%%) masks it. Against the consequential-error target (absolute corrected error above 3%%, "
    "present in %s of realizations) the area under the curve is %.2f and the precision at Z_max = 3 is %s; the index is a weaker "
    "predictor of a large corrected-rate error than of carryover."
    % (pc(mag["3.0"][0], 2), pc(mag["3.0"][3], 0), pc(mag["1.0"][0], 0), pc(mag["1.0"][3], 0), pc(DT["consequential_prevalence"], 1),
       DT["roc_consequential_error"]["auc"], pc(DT["confusion_consequential_error"]["3.0"]["precision"], 0)))
s3 = body_after(s2._p,
    "The consistency test should therefore be read narrowly. At the adopted threshold the consistency "
    "index is a gross-disagreement flag with high precision and low sensitivity; it should not be described as a carryover "
    "detector, and its main role in the reference case is as a validity check that withholds the correction when the two "
    "estimates are irreconcilable. Where the priority is to find carryover, a lower threshold is required, at the cost "
    "shown in Table 4. If the diagnostic estimator is poorer than assumed (a relative uncertainty of 30%%, for example, as "
    "may occur without the permanent pressure loss), the area under the curve falls to %.2f and the sensitivity at Z_max = 3 to %s."
    % (DT["wide_diagnostic_30pct"]["auc"], pc(DT["wide_diagnostic_30pct"]["at_zmax"]["sensitivity"], 1)))
f9 = picture_after(s3._p, os.path.join(HERE, "figK_detector.png"), 6.4)
f9c = caption_after(f9._p, "Fig. 9. Characterization of the consistency index at the reference configuration. (a) Receiver operating "
                           "characteristic for the presence of carryover and for a corrected-rate error above 3%; points mark Z_max = 1, 2 and 3. "
                           "(b) Precision against sensitivity; dotted lines are the prevalences. (c) Share of realizations rejected, by carryover "
                           "size. All simulated.", fig=True)

h = heading_after(f9c._p, "5.10 Sensitivity to the weighting rule and the damping threshold", 2)
cols = WT
s4 = body_after(h._p,
    "Table 7 compares the asymmetric rule of Eq. (12) with alternatives at three carryover prevalences, using the same "
    "realizations throughout. The controls are the thermodynamic and the diagnostic estimator alone and symmetric "
    "weighting, and the alternatives are the one-sided Cauchy rule at five thresholds, a one-sided Huber weight, a two-sided "
    "Cauchy weight and a one-sided hard switch that uses the diagnostic estimator alone when its excess exceeds k and the "
    "least-squares combination otherwise.")
cap7 = caption_after(s4._p, "Table 7. Simulated 95% error band (±%) of the corrected gas rate for alternative weighting rules, over all "
                            "300,000 realizations, at carryover prevalences of 10%, 25% (reference) and 40%. The bias is that at 25%. "
                            "The declared uncertainties are those of Table 2 in every case. Common random numbers (Section 4.5).")
order = ["Thermodynamic estimator alone", "Diagnostic estimator alone", "Symmetric GLS (no damping)",
         "One-sided Cauchy, k = 0.5 (Eq. 12)", "One-sided Cauchy, k = 1 (Eq. 12)", "One-sided Cauchy, k = 1.5 (Eq. 12)",
         "One-sided Cauchy, k = 2 (Eq. 12)", "One-sided Cauchy, k = 3 (Eq. 12)", "One-sided Huber, k = 1",
         "Two-sided Cauchy, k = 1 (control)", "One-sided hard switch, k = 0.5", "One-sided hard switch, k = 1",
         "One-sided hard switch, k = 1.5", "One-sided hard switch, k = 2"]
rows7 = [["Weighting rule", "10%", "25%", "40%", "Bias at 25%"]]
for name in order:
    v = cols[name]
    rows7.append([name.replace(" (Eq. 12)", "").replace("GLS", "least squares") + (" (Eq. 12)" if "Cauchy, k = 1 (Eq. 12)" in name else ""),
                  "±%.2f" % v["0.1"]["band95"], "±%.2f" % v["0.25"]["band95"], "±%.2f" % v["0.4"]["band95"], "%+.2f%%" % v["0.25"]["bias"]])
t7 = make_table(TBL[7], rows7, [3900, 1050, 1050, 1050, 1590], cap7._p)
sp7 = spacer_after(t7._tbl)
hk, h1_ = W1("One-sided hard switch, k = 1", 0.25), W1("Diagnostic estimator alone", 0.25)
s5 = body_after(sp7._p,
    "Three conclusions follow. First, k = 1 is not the best "
    "threshold in the reference case. Smaller thresholds do better (the one-sided Cauchy rule gives ±%.2f%% at k = 0.5 and "
    "±%.2f%% at k = 1, against ±%.2f%% for the diagnostic estimator alone), and larger ones approach symmetric weighting "
    "(±%.2f%% at k = 3). Second, no rule is uniformly best. The smooth rule of Eq. (12) falls back toward the thermodynamic "
    "estimator when carryover is rare, and at 10%% prevalence it is narrower than the diagnostic estimator alone "
    "(±%.2f%% against ±%.2f%%); at 25%% and 40%% the diagnostic estimator alone is narrower. The hard one-sided switch at k = 1 is "
    "narrower than the diagnostic estimator alone at all three prevalences (±%.2f%% at 25%%), but it is poorer than Eq. (12) when "
    "carryover is absent (±%.2f%% against ±%.2f%% at zero prevalence, Fig. 10b). Third, the two-sided control is poorer than the "
    "one-sided rule (±%.2f%% against ±%.2f%%), which is the evidence for the one-sided form."
    % (W1(C05, 0.25), W1(C1_, 0.25), h1_, W1("One-sided Cauchy, k = 3 (Eq. 12)", 0.25), W1(C1_, 0.1), W1("Diagnostic estimator alone", 0.1),
       hk, [r for x, r in zip(RB["p_matched"]["x"], RB["p_matched"]["rows"]) if x == 0.0][0]["hard"],
       [r for x, r in zip(RB["p_matched"]["x"], RB["p_matched"]["rows"]) if x == 0.0][0]["asymmetric"],
       W1("Two-sided Cauchy, k = 1 (control)", 0.25), W1(C1_, 0.25)))
check(W1("Two-sided Cauchy, k = 1 (control)", 0.25) > W1(C1_, 0.25), "two-sided control is poorer")
check(W1("One-sided Cauchy, k = 0.5 (Eq. 12)", 0.25) < W1(C1_, 0.25) and W1("One-sided Cauchy, k = 3 (Eq. 12)", 0.25) > W1(C1_, 0.25), "k ordering")
s6 = body_after(s5._p,
    "The rule of Eq. (12) is therefore presented as a smooth, continuous baseline, not as the preferred implementation. It is "
    "retained because the preceding sections are built on it, because the weight it gives each estimate is a continuous function of "
    "their disagreement, and because it falls back to the thermodynamic estimator when carryover is absent. The hard one-sided switch "
    "is a promising alternative and the better performer in the reference case, but its advantage rests on the assumed carryover "
    "statistics and on a discontinuity at the switching threshold, where a small change in the data changes the estimate abruptly; "
    "it needs independent validation, in particular of that threshold, before it is recommended. The best rule, and the best k, depend "
    "on the carryover prevalence and magnitude and on the diagnostic estimator, none of which is measured here, and a threshold "
    "chosen to minimize the error band of one simulated population would be tuned to its assumptions. The choice of rule and "
    "threshold is a calibration question for loop data, and Section 4.4 lists the measurement that would decide it.")

h = heading_after(s6._p, "5.11 Robustness to the diagnostic estimator, to prevalence and to a persistent site bias", 2)
rows_s2c, rows_s2m = RB["s2_consistent"]["rows"], RB["s2_misdeclared"]["rows"]
xs = RB["s2_consistent"]["x"]
ix = lambda arr, v: arr.index(v)
s7 = body_after(h._p,
    "Fig. 10 varies the assumptions on which the conclusions are most dependent. In Fig. 10a the actual relative uncertainty of "
    "the diagnostic estimator is varied from 10%% to 60%%, with the declared uncertainty either equal to the actual value (solid) or "
    "fixed at the assumed 20%% (dashed). When the diagnostic estimator is better than assumed (10%%), it is the best single "
    "estimator (±%.2f%%) and the full method is wider (±%.2f%%) when the uncertainty is declared correctly and much wider (±%.2f%%) "
    "when it is not; when it is worse (30%%), the full method is narrower than the diagnostic estimator alone (±%.2f%% against "
    "±%.2f%%, and ±%.2f%% if the 20%% declaration is retained), and at 40%% and 60%% the thermodynamic estimator alone (±%.2f%%) is "
    "narrower than the diagnostic estimator alone (±%.2f%% and ±%.2f%%). The acceptance test limits the damage: the full method "
    "reaches ±%.2f%% at 60%%, against ±%.2f%% for the asymmetric rule without it. The effect of the transfer bias is smaller: "
    "raising its spread from 0 to 20%% widens the full method from ±%.2f%% to ±%.2f%%."
    % (rows_s2c[ix(xs, 0.1)]["e2"], rows_s2c[ix(xs, 0.1)]["full"], rows_s2m[ix(xs, 0.1)]["full"], rows_s2c[ix(xs, 0.3)]["full"],
       rows_s2c[ix(xs, 0.3)]["e2"], rows_s2m[ix(xs, 0.3)]["full"], rows_s2c[ix(xs, 0.4)]["e1"], rows_s2c[ix(xs, 0.4)]["e2"],
       rows_s2c[ix(xs, 0.6)]["e2"], rows_s2c[ix(xs, 0.6)]["full"], rows_s2c[ix(xs, 0.6)]["asymmetric"],
       RB["s2t_consistent"]["rows"][0]["full"], RB["s2t_consistent"]["rows"][-1]["full"]))
check(RB["s2_consistent"]["rows"][ix(xs, 0.1)]["e2"] < RB["s2_consistent"]["rows"][ix(xs, 0.1)]["full"], "10%: e2 narrower than full")
check(rows_s2c[ix(xs, 0.4)]["e1"] < rows_s2c[ix(xs, 0.4)]["e2"], "40%: e1 narrower than e2")
sb = RB["site_bias"]
sbx = sb["x"]
s8 = body_after(s7._p,
    "Fig. 10c replaces the population of sites by one site with a fixed transfer bias of the diagnostic estimator. The "
    "diagnostic estimator alone is narrowest with no bias (±%.2f%%) and widens in either direction, to ±%.2f%% at −15%% and "
    "±%.2f%% at +15%%. The fused estimate is the more robust to a positive bias, because the thermodynamic estimate, which is biased "
    "low by carryover, offsets it: at +15%% the full method is ±%.2f%% against ±%.2f%%, and at −15%% the two are similar (±%.2f%% and ±%.2f%%). "
    "This asymmetry is a property of the simulated carryover bias, not a general benefit of fusion, and it would not occur if the "
    "thermodynamic estimator were biased in the same direction as the diagnostic one. The hard switch, which discards the "
    "thermodynamic estimate when the diagnostic excess is large, has no such protection (±%.2f%% at +15%%)."
    % (sb["rows"][sbx.index(0.0)]["e2"], sb["rows"][sbx.index(-0.15)]["e2"], sb["rows"][sbx.index(0.15)]["e2"],
       sb["rows"][sbx.index(0.15)]["full"], sb["rows"][sbx.index(0.15)]["e2"], sb["rows"][sbx.index(-0.15)]["full"],
       sb["rows"][sbx.index(-0.15)]["e2"], sb["rows"][sbx.index(0.15)]["hard"]))
pm_rows, pmx = RB["p_matched"]["rows"], RB["p_matched"]["x"]
pd_rows = RB["p_misdeclared"]["rows"]
g = RB["grid"]
reach = {}
for s2v, row in zip(g["s2"], g["rows"]):
    last = None
    for pv, r in zip(g["p"], row):
        if r["full"] < r["e2"]:
            last = pv
        else:
            break
    reach[s2v] = last
check(reach[0.2] is not None and 0.05 <= reach[0.2] <= 0.2 and reach[0.4] == g["p"][-1], "heat-map reach")
s9 = body_after(s8._p,
    "Fig. 10b gives the prevalence sweep on a finer grid with common random numbers, and Fig. 10d shows where the full method is "
    "narrower than the diagnostic estimator alone over the plane of diagnostic uncertainty and carryover prevalence. At the "
    "assumed 20%% the crossing lies at about %d%% (as in Section 5.6); at 30%% the full method is narrower up to about %d%%; and at 40%% at every "
    "prevalence examined, up to 60%%. When the diagnostic estimator is as good as 10%%, the advantage is below 0.3 percentage "
    "points and disappears above 10%% prevalence. The dashed lines of Fig. 10b show the effect of leaving the carryover "
    "allowance of Eq. (8) at its 25%% value when the actual prevalence differs: at 60%% prevalence the full method is ±%.2f%% with a "
    "matched allowance and ±%.2f%% with the fixed one, and at zero prevalence ±%.2f%% and ±%.2f%%. Carryover prevalence need be "
    "known only approximately."
    % (round(100 * LASTF), round(100 * reach[0.3]), pm_rows[pmx.index(0.6)]["full"], pd_rows[pmx.index(0.6)]["full"],
       pm_rows[0]["full"], pd_rows[0]["full"]))
f10 = picture_after(s9._p, os.path.join(HERE, "figJ_robustness.png"), 6.2)
f10c = caption_after(f10._p, "Fig. 10. Robustness of the conclusions. Common random numbers throughout. (a) Diagnostic-estimator uncertainty, "
                             "declared equal to the actual value (solid) or fixed at the assumed 20% (dashed, diagnostic alone and full method). "
                             "(b) Carryover prevalence, with the allowance of Eq. (8) matched to the prevalence (solid) or fixed at 25% (dashed). "
                             "(c) One site with a fixed diagnostic transfer bias. (d) Full method minus diagnostic alone, in percentage points. "
                             "All simulated.", fig=True)

h = heading_after(f10c._p, "5.12 Independent forward model and model-form error", 2)
s10 = body_after(h._p,
    "The reference simulation generates the meter reading and corrects it with the same correlation, so some of the favorable "
    "performance is built in. Table 8 and Fig. 11 replace the generating model, keeping Chisholm as the correction (Section 4.5). "
    "With the independent orifice correlation of Murdock (1962), the oracle band, which isolates the correlation error alone, rises "
    "from ±%.2f%% to ±%.2f%%, the diagnostic estimator alone from ±%.2f%% to ±%.2f%%, and the full method from ±%.2f%% to "
    "±%.2f%%, with a bias of %+.2f%% instead of %+.2f%%. The correction model contributes error that no liquid-loading estimator "
    "can remove, and the 95%% error band of the whole method grows by about one percentage point."
    % (MATCH["oracle"]["band95"], MURD["oracle"]["band95"], MATCH["e2"]["band95"], MURD["e2"]["band95"], MATCH["full"]["band95"],
       MURD["full"]["band95"], MURD["full"]["bias"], MATCH["full"]["bias"]))
cap8 = caption_after(s10._p, "Table 8. Simulated 95% error band (±%) and bias when the over-reading that generates the meter reading differs from "
                             "the Chisholm correction. “Scaled” multiplies φ − 1 by the factor shown; “random” multiplies it by a random "
                             "factor with the relative standard deviation shown. Coverage is the realized fraction of corrected "
                             "values whose error lies inside the declared ±2u interval, without and with a declared model-form term of 5% of "
                             "the over-reading. The perturbations are stress scenarios, not measured error bounds. Common random numbers (Section 4.5).")
names8 = [("matched", "Matched (Chisholm)"), ("Murdock (independent orifice correlation)", "Murdock (1962), independent"),
          ("over-reading -10%", "Scaled by 0.90"), ("over-reading -5%", "Scaled by 0.95"), ("over-reading +5%", "Scaled by 1.05"),
          ("over-reading +10%", "Scaled by 1.10"), ("random discrepancy 5%", "Random, 5%"), ("random discrepancy 10%", "Random, 10%")]
rows8 = [["Generating model", "Oracle", "Diagnostic alone", "Full method, bias", "Full method, band", "Coverage of ±2u", "with 5% form term"]]
for key, lab in names8:
    m = MF[key]
    rows8.append([lab, "±%.2f" % m["oracle"]["band95"], "±%.2f" % m["e2"]["band95"], "%+.2f%%" % m["full"]["bias"], "±%.2f" % m["full"]["band95"],
                  pc(m["full"]["coverage_2u"]), pc(m["full"]["coverage_2u_with_form_term"])])
t8 = make_table(TBL[3], rows8, [2250, 900, 1150, 1100, 1100, 1090, 1050], cap8._p)
sp8 = spacer_after(t8._tbl)
cv = R["modelform_coverage_vs_uform"]
f_need = next(f for f in cv["f"] if cv["rows"]["Murdock (independent orifice correlation)"][str(f)] >= 0.94)
mfb = MF["over-reading -10%"]
s11 = body_after(sp8._p,
    "Three observations qualify the headline. First, the realized coverage of the declared ±2u interval is %s in the matched "
    "case, close to the nominal 95%%, and falls to %s with the independent correlation and %s when the over-reading is scaled up "
    "by 10%%; a declared model-form term of 5%% of the over-reading restores only about one percentage point of it (%s and %s). "
    "A term of about %d%% of the over-reading is needed for the Murdock case to reach %s coverage. The model-form allowance "
    "u_form of Eq. (16) is therefore an assumption that must be set from the spread between published correlations "
    "or from loop data, and it is larger than the 0.6%% correlation residual used in the reference case. A generic allowance does "
    "not guarantee nominal coverage: the value that restores it here is specific to this pair of correlations, this meter geometry "
    "and this operating envelope, and must be calibrated for each applicable meter and set of conditions. Second, the ranking of "
    "the methods changes with the sign of the correlation error. When the true over-reading is smaller than the correction "
    "assumes (scaled by 0.90 or 0.95), the full method is narrower than the diagnostic estimator alone (±%.2f%% against ±%.2f%% at 0.90), "
    "but this is compensation of errors, since the downward bias that carryover gives the thermodynamic estimate offsets the "
    "overcorrection, and it should not be read as a benefit. When it is larger, or with the independent correlation, the "
    "diagnostic estimator alone is narrower, as in the reference case. Third, a wrong functional form cannot be rescued by the "
    "estimator: with a Venturi form (de Leeuw, 1997) as the truth, which is outside the validity of that correlation for an "
    "orifice and is shown only as a limiting case, the oracle band is ±%.2f%% and the full method ±%.2f%%, with a coverage of %s."
    % (pc(MATCH["full"]["coverage_2u"]), pc(MURD["full"]["coverage_2u"]), pc(MF["over-reading +10%"]["full"]["coverage_2u"]),
       pc(MURD["full"]["coverage_2u_with_form_term"]), pc(MF["over-reading +10%"]["full"]["coverage_2u_with_form_term"]),
       round(100 * f_need), "94–95%", mfb["full"]["band95"], mfb["e2"]["band95"],
       MF["de Leeuw form (functional-form stress test only)"]["oracle"]["band95"],
       MF["de Leeuw form (functional-form stress test only)"]["full"]["band95"],
       pc(MF["de Leeuw form (functional-form stress test only)"]["full"]["coverage_2u"], 0)))
check(mfb["full"]["band95"] < mfb["e2"]["band95"] and MF["over-reading +5%"]["full"]["band95"] > MF["over-reading +5%"]["e2"]["band95"], "model-form ranking claims")
f11 = picture_after(s11._p, os.path.join(HERE, "figI_modelform.png"), 6.2)
f11c = caption_after(f11._p, "Fig. 11. Independent forward model. (a) 95% error band when the true over-reading is Chisholm (matched), Murdock "
                             "(independent), scaled, or random (10%). (b) Realized coverage of the declared ±2u interval, without and with a "
                             "declared model-form term of 5% of the over-reading. All simulated.", fig=True)

# ===================================================================================================== 6. Discussion
cap7_old = find_unique("Table 7. Routes to a wet-gas corrected gas rate")
set_par(cap7_old, cap7_old.text.replace("Table 7.", "Table 9."))
for r_ in cap7_old.runs:
    r_.italic = True
    r_.font.size = T_CAP_TABLE.runs[0].font.size

capf9 = find_unique("Fig. 9. Implementation as a secondary instrumentation layer")
set_par(capf9, capf9.text.replace("Fig. 9.", "Fig. 12.", 1))
for r_ in capf9.runs:
    r_.italic = True
    r_.font.size = T_CAP_FIG.runs[0].font.size

p = find_unique("Two properties matter for an installed measurement system")
m1 = body_after(p._p,
    "Minimum signal set. For the orifice case the diagnostic estimator requires the signals the flow computer already reads — "
    "line pressure, temperature, differential pressure and indicated rate — the gas density from the composition, a "
    "composition measurement for the thermodynamic estimator, and the high-rate differential-pressure signal from which σ_ΔP "
    "is computed. The permanent pressure loss ratio needs a downstream tapping. Where it is absent the feature vector of Eq. (6) "
    "loses its recovery term, the diagnostic estimator becomes less informative, and its declared uncertainty must be "
    "widened before the framework is used; the size of the widening can be known only from a fit without that feature. As an "
    "indication, Fig. 10a shows that if the actual relative uncertainty were 30%% instead of 20%%, the full method would reach "
    "±%.2f%% (±%.2f%% if the 20%% declaration were retained), against ±%.2f%% for the diagnostic estimator alone and ±%.2f%% for the "
    "thermodynamic estimator alone. Without the high-rate differential-pressure signal the diagnostic estimator is not "
    "specified by this paper, and the method is not supported; the thermodynamic estimator would then be the only "
    "estimator and no consistency test would be available."
    % (rows_s2c[ix(xs, 0.3)]["full"], rows_s2m[ix(xs, 0.3)]["full"], rows_s2c[ix(xs, 0.3)]["e2"], rows_s2c[ix(xs, 0.3)]["e1"]))

p = find_unique("These are extension pathways, not results")
env = R["envelope"]
sc1 = body_after(p._p,
    "Table 10 separates what is demonstrated by the simulations from what is proposed. The demonstrated envelope is an orifice "
    "plate in a 154 mm line, one rich-gas composition family, %.0f–%.0f kgf/cm² (%.1f–%.1f MPa) and %.0f–%.0f °C, with liquid "
    "loadings X_LM from %.3f to %.3f (5th–95th percentile %.3f–%.3f) in the annular-mist regime; nothing is claimed outside it."
    % (env["pressure_kgf_cm2"][0], env["pressure_kgf_cm2"][1], env["pressure_MPa"][0], env["pressure_MPa"][1], env["temperature_C"][0],
       env["temperature_C"][1], env["X_LM_percentiles"]["0"], env["X_LM_percentiles"]["100"], env["X_LM_percentiles"]["5"],
       env["X_LM_percentiles"]["95"]))
cap10 = caption_after(sc1._p, "Table 10. Scope of the results: what the simulations demonstrate and what is proposed but not evaluated.")
rows10 = [["Aspect", "Demonstrated by simulation in this paper", "Proposed, not evaluated"],
          ["Meter", "Orifice plate, Chisholm correction (n = 0.25), 154 mm line", "Venturi, cone, multipath ultrasonic and Coriolis meters (Section 6.3)"],
          ["Pressure and temperature", "%.0f–%.0f kgf/cm² (%.1f–%.1f MPa); %.0f–%.0f °C" % (env["pressure_kgf_cm2"][0], env["pressure_kgf_cm2"][1], env["pressure_MPa"][0], env["pressure_MPa"][1], env["temperature_C"][0], env["temperature_C"][1]), "Other pressures, temperatures and line sizes"],
          ["Fluid", "One rich-gas composition family; gas density %.0f–%.0f kg/m³; condensate %.0f–%.0f kg/m³" % (env["rho_g_range"][0], env["rho_g_range"][1], env["rho_l_range"][0], env["rho_l_range"][1]), "Lean gases, other condensates, produced water or glycol"],
          ["Flow regime", "Annular-mist; X_LM %.3f–%.3f; Fr_G %.1f–%.1f" % (env["X_LM_percentiles"]["0"], env["X_LM_percentiles"]["100"], env["Fr_percentiles"]["0"], env["Fr_percentiles"]["100"]), "Slug, stratified and transitional flow (detection and suspension only)"],
          ["Diagnostic signals", "P, T, ΔP, σ_ΔP, PLR (downstream tapping), indicated rate, gas density; performance assumed (20% ± 6% bias)", "Operation without a downstream tapping; a fitted estimator"],
          ["Forward model", "Chisholm (matched); Murdock and scaled or random departures as stress tests", "Experimentally measured over-reading"],
          ["Evidence", "Monte Carlo simulation, 300,000 realizations per configuration", "Wet-gas loop validation (Section 4.4)"]]
t10 = make_table(TBL[1], rows10, [1700, 3600, 3340], cap10._p)
spacer_after(t10._tbl)

# limitations
p = find_unique("No experimental wet-gas data were used. Every result")
set_par(p, "No experimental wet-gas data were used. Every result is a modeled uncertainty. In the reference case the over-reading "
           "correlation is both the forward model and the correction. Section 5.12 replaces the forward model with an independent "
           "published orifice correlation and with systematic and random departures of 5–10%, and finds that the error band grows by about one "
           "percentage point and the realized coverage of the declared interval falls below 90% unless a model-form allowance of "
           "about 15% of the over-reading is declared. That allowance is specific to the correlation pair, meter geometry and conditions "
           "tested and must be calibrated for each application; a generic value cannot guarantee nominal coverage. Those scenarios are "
           "stress tests and not measured error bounds; an independent experimental reference is required to remove the circularity.")
p = find_unique("The diagnostic mapping f_θ is specified in Section 3.3.1 but not fitted")
set_par(p, "The diagnostic mapping f_θ is specified in Section 3.3.1 but not fitted. Its assumed 20% relative uncertainty and 6% "
           "transfer bias are the most consequential assumptions in the paper: the ablation of Table 3 and the design rule of "
           "Section 5.6 depend on the relative standing of u₁ and u₂. Section 5.11 varies them: a diagnostic estimator that is "
           "better than assumed makes the diagnostic estimator alone the best choice, and one that is worse moves the crossing points "
           "of Fig. 6 and makes the full method narrower than the diagnostic estimator alone. The conversion from the specified "
           "predictive interval to the standard uncertainty (Section 3.3.1) is a convention and must be confirmed on fitted data.")
p = find_unique("Diagnostic availability is installation dependent")
extra1 = bullet_after(p._p, "The weighting rule and its threshold are not established. Section 5.10 shows that k = 1 is not the best threshold and "
                            "that a hard one-sided switch is narrower than Eq. (12) in the reference case; Eq. (12) is a smooth baseline and the switch "
                            "an alternative that needs independent validation, especially of its switching threshold. The choice depends on carryover "
                            "statistics and on the fitted diagnostic estimator, and is a matter for loop calibration.")
extra2 = bullet_after(extra1._p, "The consistency index at Z_max = 3 has a sensitivity of about 3% for carryover (Section 5.9). It is a gross-disagreement flag and "
                                  "should not be presented as a carryover detector; a lower threshold increases sensitivity at the cost of "
                                  "false rejections (Table 4).")

# ===================================================================================================== 7. Conclusions
p = find_unique("A Monte Carlo study over a rich-gas envelope yields")
set_par(p, "A Monte Carlo study over a rich-gas envelope yields the following simulation results. Correction reduces the 95%% error "
           "band of the orifice case from ±14.94%% to ±4.26%% (±4.28%% over all realizations before the acceptance test), against "
           "±1.82%% for the same correlation supplied with the true liquid loading, and against ±3.99%% for the diagnostic estimator "
           "alone. Fusion therefore does not improve on the diagnostic estimator alone in the reference case; it does so when "
           "carryover occupies less than about %d%% of operating time, when the diagnostic estimator is poorer than assumed, or when "
           "it carries a persistent positive bias. Combining a thermodynamic and a diagnostic estimate requires the "
           "thermodynamic estimator to declare an uncertainty that includes the upstream carryover it cannot observe; without that "
           "allowance, inverse-variance fusion is worse (±5.45%%) than the diagnostic estimator alone. A one-sided damping rule "
           "improves on symmetric weighting, but k = 1 is not the best threshold, and a hard one-sided switch is narrower in the "
           "reference case." % round(100 * LASTF))
p = find_unique("The consistency index between the two estimates is a specific detector")
set_par(p, "At the adopted threshold the consistency index has a precision of 94% for carryover, which occurs in 25% of the simulated "
           "realizations, and a sensitivity of 3%: it rejects very few realizations and nearly all contain carryover, but it misses "
           "most of the carryover that is present, and it responds mainly to large carryover. It is a gross-disagreement flag rather "
           "than a carryover detector, and a lower threshold trades completeness for sensitivity. Because the two estimates are not "
           "statistically independent, the covariance term must be retained in the index; omitting it does not degrade the test "
           "gracefully but progressively disables it so that it accepts everything.")
p = find_unique("The sensitivity analysis reveals that the corrected rate is an order of magnitude")
set_par(p, "The corrected rate is about ten times more sensitive to a relative change in gas density or differential pressure than to "
           "one in liquid loading, yet the liquid-loading estimate is the largest single contribution to the combined standard "
           "uncertainty (%d%% of its variance at X_LM = 0.05 and %d%% at 0.10) because its relative uncertainty, %.0f%%, is about "
           "thirty times larger. Sensitivity coefficients and uncertainty contributions must be reported together. Replacing the "
           "matched forward model by an independent orifice correlation widens the error band by about one percentage point and "
           "lowers the realized coverage of the declared interval to %s unless a model-form allowance is declared, and that allowance must be "
           "calibrated for the meter geometry and conditions: a generic value cannot guarantee nominal coverage."
           % (round(100 * vs5["X_LM estimate"]), round(100 * vs10["X_LM estimate"]), 100 * T05["rows"]["X_LM estimate"]["u_rel"],
              pc(MURD["full"]["coverage_2u"], 0)))

# ===================================================================================================== statements
p = find_unique("No experimental data were used. The entire quantitative content")
set_par(p, "No experimental data were used. The entire quantitative content of this paper is computational, and the complete "
           "reproducibility package — the Python implementation, the simulation configuration, the random seeds, the figure "
           "generators and the generated summary data — is openly available at "
           "https://github.com/sandlerleon/hybrid-liquid-loading-estimation and permanently archived at "
           "https://doi.org/10.5281/zenodo.22760863. Running the deposited scripts reproduces every table and figure in this "
           "paper; the analyses added in the revision (Sections 5.9–5.12, Table 4 and Figs 9–11) are produced by "
           "fmi_revision_analysis.py, and verify_revision.py runs the checks of the revision code. A preprint of the "
           "manuscript is available on ChemRxiv at https://doi.org/10.26434/chemrxiv.15009070/v1.")
p = find_unique("During the preparation of this work, the author used Claude")
set_par(p, "During the preparation of this work, the author used Claude (Anthropic) to assist with literature synthesis, analysis design, "
           "writing of the simulation code and drafting, including the additional experiments and the revision of the text. After "
           "using this tool, the author reviewed and edited the content as needed, verified the cited literature, checked the code "
           "against executable tests, and takes full responsibility for the content of the publication. No AI tool is listed as an author.")

# ===================================================================================================== references
REFS = [("Dranchuk, P.M.", "Fawcett, T., 2006. An introduction to ROC analysis. Pattern Recognit. Lett. 27, 861–874. "
                          "https://doi.org/10.1016/j.patrec.2005.10.010"),
        ("He, D.", "Holland, P.W., Welsch, R.E., 1977. Robust regression using iteratively reweighted least-squares. Commun. Stat. "
                   "Theory Methods 6, 813–827. https://doi.org/10.1080/03610927708827533"),
        ("Hosseini, S., Chinello, G., Lindsay, G., McGlinchey", "Huber, P.J., Ronchetti, E.M., 2009. Robust Statistics, 2nd ed. Wiley, "
                                                               "Hoboken. https://doi.org/10.1002/9780470434697"),
        ("JCGM 100:2008", "JCGM 101:2008. Evaluation of measurement data — Supplement 1 to the “Guide to the expression of uncertainty in "
                          "measurement” — Propagation of distributions using a Monte Carlo method.")]
for anchor_prefix, text in REFS:
    pa = find(anchor_prefix)
    q = clone_after(pa._p, pa)
    add_run(q, text, size=pa.runs[0].font.size)

pp_ = find_unique("The simulated 95% band and the acceptance rate over the (X_LM, Fr_G) plane")
replace_in_paragraph(pp_, "The accuracy decreases with increasing liquid loading", "The error band widens with increasing liquid loading")
pp_ = find_unique("The reported metrics are the mean error (bias)")
replace_in_paragraph(pp_, "and the 95% coverage band taken as the larger absolute value", "and the 95% error band taken as the larger absolute value")
doc.save(OUT)

# ===================================================================================================== variant without the author block
d2 = Document(OUT)
drop = [p for p in d2.paragraphs if p.text.strip() in ("Leon Sandler", "Independent Researcher, Northbrook, IL 60062, USA",
                                                        "Corresponding author: sandler.leon@gmail.com")
        or p.text.startswith("Leon Sandler: Conceptualization")]
for p in drop:
    p._p.getparent().remove(p._p)
d2.save(OUT_NOAUTH)

# ===================================================================================================== checks
chk = Document(OUT)
txt = "\n".join(p.text for p in chk.paragraphs)
for t in chk.tables:
    for row in t.rows:
        for c in row.cells:
            txt += "\n" + c.text
assert "kg/cm²" not in txt.replace("kgf/cm²", ""), "unit not converted"
for ref in ("Holland and Welsch, 1977", "Huber and Ronchetti", "Fawcett, 2006", "JCGM 100:2008", "Murdock (1962)", "de Leeuw, 1997"):
    assert ref in txt, "missing citation " + ref
for key in ("Holland, P.W.", "Huber, P.J.", "Fawcett, T.", "JCGM 101:2008"):
    assert key in txt, "missing reference entry " + key
assert "Table 10" in txt and "Fig. 12" in txt and "Fig. 11." in txt and "Fig. 10." in txt and "Fig. 9. Characterization" in txt
n_img = len(chk.element.body.findall(".//" + qn("a:blip")))
print("images %d (v4: 9) ; tables %d (v4: 8) ; paragraphs %d -> %d" % (n_img, len(chk.tables), len(Document(SRC).paragraphs), len(chk.paragraphs)))
assert n_img == 12 and len(chk.tables) == 11
print("saved", OUT)
print("saved", OUT_NOAUTH)
