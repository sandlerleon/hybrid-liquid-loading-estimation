# -*- coding: utf-8 -*-
"""Revised Flow Measurement and Instrumentation manuscript.

Changes from the first draft: GUM notation throughout, the covariance between the
two estimators treated explicitly, the diagnostic estimator specified as a
fittable model, the modelled nature of every result made explicit, and the
validation design moved into the Methods.
"""
import os, json
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "fmi_results.json")))
CV = json.load(open(os.path.join(HERE, "covariance_results.json")))["correlation_sweep"]
AB, SEL, SENS, DS, ZS = (R["ablation"], R["rejection_selectivity"],
                         R["sensitivity"], R["design_sweep"], R["z_sweep"])
UNC = AB["Uncorrected meter"]; ORC = AB["Correlation with known X_LM (oracle)"]
E1 = AB["E1 only (thermodynamic)"]; E2 = AB["E2 only (diagnostic)"]
FN = AB["Fusion, carryover omitted from E1 budget"]
FH = AB["Fusion, honest E1 uncertainty budget"]
FR = AB["Robust asymmetric fusion"]
SW = AB["SWCL: robust fusion + consistency rejection"]

DOI_PAPER = "10.5281/zenodo.22760861"
DOI_CODE = "10.5281/zenodo.22760863"
GITHUB = "https://github.com/sandlerleon/hybrid-liquid-loading-estimation"

doc = Document()
doc.styles['Normal'].font.name = 'Calibri'
doc.styles['Normal'].font.size = Pt(10.5)


def para(t=None, bold=False, italic=False, size=10.5, after=9):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after)
    if t:
        r = p.add_run(t); r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    return p


def h(t, lvl=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(t); r.bold = True
    r.font.size = Pt(13 if lvl == 1 else 11)
    return p


def bullet(t, size=10):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    p.add_run(t).font.size = Pt(size)
    return p


def numbered(t, size=10):
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.space_after = Pt(3)
    p.add_run(t).font.size = Pt(size)
    return p


def table(rows, fs=8.5):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = 'Light Grid Accent 1'
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            c = t.rows[i].cells[j]; c.text = ''
            pp = c.paragraphs[0]; pp.paragraph_format.space_after = Pt(2)
            rr = pp.add_run(cell); rr.font.size = Pt(fs)
            if i == 0: rr.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def cap(t):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(11)
    r = p.add_run(t); r.font.size = Pt(8.5); r.italic = True


def figure(fn, caption, width=6.0):
    doc.add_picture(os.path.join(HERE, fn), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap(caption)


def eq(body, num=None):
    """Display equation: serif, centred, numbered at the right."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7); p.paragraph_format.space_after = Pt(9)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(body); r.font.size = Pt(11); r.font.name = 'Cambria'; r.italic = True
    if num:
        r2 = p.add_run("  (%s)" % num)
        r2.font.size = Pt(10.5); r2.font.name = 'Cambria'
    return p


def code_block(t, size=9):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.left_indent = Inches(0.22)
    r = p.add_run(t); r.font.size = Pt(size); r.font.name = 'Consolas'
    return p


# ==================================================================== TITLE
para("Hybrid Physics–Diagnostic Estimation of Liquid Loading for Wet-Gas "
     "Flowmeter Correction: A Model-Based Uncertainty Framework",
     bold=True, size=15.5, after=10)
para("Leon Sandler", size=11, after=2)
para("Independent Researcher, Northbrook, IL 60062, USA", size=10, after=2)
para("Corresponding author: sandler.leon@gmail.com", size=10, after=16)

# ==================================================================== ABSTRACT
h("Abstract")
ABSTRACT = (
    "Established wet-gas corrections express the indicated gas rate as the true rate multiplied "
    "by an over-reading factor that depends on the Lockhart–Martinelli parameter. At most "
    "production metering stations that parameter is not measured, so the correction cannot be "
    "closed from the meter signal alone. This paper treats liquid loading as a latent variable to "
    "be estimated rather than treating the over-reading as a quantity to be learned. A "
    "thermodynamic prediction from composition, pressure and temperature is combined with a "
    "structurally distinct estimate from flowmeter diagnostic signals already transmitted at the "
    "station, and their disagreement is quantified by an estimator consistency index governing "
    "whether the correction is applied. The study is computational: no wet-gas loop data were "
    "used, the diagnostic estimator is specified but not fitted, and every figure below is a "
    "modelled uncertainty rather than a measured accuracy. In a Monte Carlo study of 300,000 "
    "simulated realisations over a rich-gas envelope (60–85 kg/cm², 30–60 °C), three results "
    "follow. Inverse-variance fusion degrades the estimate unless the thermodynamic estimator "
    "declares an allowance for upstream carryover it cannot observe; with that allowance and an "
    f"asymmetric weighting, the simulated 95% band falls from ±{FN['band95']:.2f}% to "
    f"±{FR['band95']:.2f}%. The consistency index is a specific detector of that failure mode: "
    f"carryover occurs in {100*SEL['all']:.0f}% of realisations but in "
    f"{100*SEL['rejected']:.0f}% of those rejected. Because the two estimates are not "
    "statistically independent, the covariance term must be retained in the index; omitting it "
    "progressively disables the acceptance test. A falsifiable experimental protocol is specified."
)
para(ABSTRACT, after=10)

h("Keywords")
para("Wet gas metering; Liquid loading estimation; Lockhart–Martinelli parameter; "
     "Differential pressure flowmeter; Uncertainty quantification; Estimator fusion",
     italic=True, size=10)

h("Nomenclature", 2)
table([
    ["Symbol", "Meaning", "Symbol", "Meaning"],
    ["Q_ind", "indicated gas flow rate", "u₁, u₂", "standard uncertainties of X⁽¹⁾, X⁽²⁾"],
    ["Q_G", "true gas flow rate", "u_f", "standard uncertainty of the fused estimate"],
    ["φ", "wet-gas over-reading factor", "ρ₁₂", "correlation between the estimator errors"],
    ["X_LM", "Lockhart–Martinelli parameter", "c", "covariance, c = ρ₁₂ u₁ u₂"],
    ["X⁽¹⁾", "thermodynamic estimate of X_LM", "Z", "estimator consistency index"],
    ["X⁽²⁾", "diagnostic estimate of X_LM", "k", "damping threshold in the asymmetric rule"],
    ["X_f", "fused estimate of X_LM", "Fr_G", "gas densiometric Froude number"],
    ["ṁ_L, ṁ_G", "liquid and gas mass flow rates", "ρ_G, ρ_L", "gas and liquid densities"],
], fs=8.5)

# ==================================================================== 1
h("1. Introduction")

h("1.1 The wet-gas measurement problem", 2)
para("Single-phase gas flowmeters are widely used on streams that carry entrained liquid. In a "
     "differential-pressure meter the liquid raises the measured differential pressure above its "
     "dry-gas value, so a flow computer correctly applying ISO 5167 or AGA Report No. 3 reports a "
     "gas rate that is too high. The magnitude is not marginal: for a rich gas at typical "
     "production pressures, condensate–gas ratios of 50 and 100 bbl/MMscf produce over-readings "
     "of approximately 8% and 16% on the Chisholm multiplier.")
para("The phenomenon is well characterised. Murdock (1962) and Chisholm (1977) established the "
     "form of the two-phase multiplier for orifice plates; de Leeuw (1997) and Steven (2002) "
     "extended it to Venturi meters with an explicit Froude-number dependence; ISO/TR 11583:2012 "
     "codifies the approach; and Alkhurayef et al. (2026b) review the correlation literature for "
     "Venturi meters. All share one structural feature: the over-reading is expressed as a "
     "function of the Lockhart–Martinelli parameter, which is a property of the flow rather than "
     "of the meter, and which the meter does not measure.")

h("1.2 Existing approaches", 2)
para("Empirical correlations. Murdock (1962), Chisholm (1977), de Leeuw (1997), Steven (2002), "
     "He et al. (2019) and Pan et al. (2019) fit over-reading to liquid loading and density "
     "ratio, with progressively better treatment of Froude number and geometry. Gajan et al. "
     "(2015) examined high-pressure behaviour and Zheng et al. (2019) ultra-low liquid loading. "
     "These are accurate when liquid loading is known and undefined when it is not.")
para("Additional pressure or diagnostic measurements. Nasr et al. (2026) instrument an orifice "
     "plate with a third pressure tap and use the additional pressure information to detect and "
     "quantify liquid, reporting gas-rate prediction within approximately 3% over the range "
     "tested. This is the closest existing approach to the present one; the distinction is "
     "discussed in Section 6.1.")
para("Dedicated multiphase metering. Where budget and space allow, a multiphase or wet-gas meter "
     "measures the phases directly. This is a reference case rather than a competitor: it "
     "resolves the ambiguity by instrumentation, at a cost and footprint that a large installed "
     "base of single-phase meters cannot absorb.")
para("Data-driven correction. Pereira et al. (2026) predict gas and liquid rates from cone-meter "
     "pressure information using machine learning; Hosseini et al. (2026a) address generalisation "
     "with transfer learning; Hosseini et al. (2026b) develop an uncertainty quantification "
     "framework for machine-learning wet-gas metering.")
para("Hybrid physics–machine-learning correction. Alkhurayef and Alsarkhi (2026a) combine a "
     "physical over-reading model with a learned residual trained on 1,868 experimental points. "
     "This is the most direct recent precedent for coupling a correlation with a data-driven term.")

h("1.3 Research gap", 2)
para("The mature correlation literature solves the problem of computing the correction once "
     "liquid loading is known, while the practical difficulty at an installed station is the "
     "preceding step: liquid loading is not measured. The recent data-driven and hybrid work "
     "addresses this by learning the over-reading, or the flow rates, directly from experimental "
     "datasets, which requires those datasets to cover the installation's geometry, fluid and "
     "operating range.")
para("The approach taken here differs in what is treated as the learned quantity. Liquid loading "
     "is treated as a latent variable to be estimated from information already available at the "
     "station, and the established correlation is retained unchanged to convert that estimate "
     "into a correction. This preserves the correlation's physical form and its extrapolation "
     "behaviour, and confines the data-driven element to a single scalar whose uncertainty can be "
     "stated and propagated.", bold=True)
para("It also permits something the direct-learning formulations do not naturally provide: "
     "because two structurally distinct estimates of the same latent variable are available, "
     "their disagreement is measurable and can be used to decide whether the correction should be "
     "applied at all.")

h("1.4 Contributions and status of the results", 2)
para("The contributions are:")
numbered("A hybrid liquid-loading estimator combining a thermodynamic prediction from gas "
         "composition, pressure and temperature with an estimate derived from flowmeter "
         "diagnostic signals, with a specification of the diagnostic model sufficient to be "
         "fitted and reproduced (Section 3.3.1).")
numbered("Identification of an uncertainty-budgeting requirement: the thermodynamic estimator "
         "must declare an allowance for upstream carryover that it cannot observe, failing which "
         "inverse-variance fusion performs worse than the diagnostic estimator alone.")
numbered("An asymmetric weighting rule motivated by the dominant failure mode of the "
         "thermodynamic estimator, with the damping threshold specified.")
numbered("An estimator consistency index and acceptance test that withholds the correction when "
         "the two estimates are irreconcilable, with its specificity as a carryover detector "
         "quantified.")
numbered("Explicit treatment of the covariance between the two estimates, which are not "
         "statistically independent, and quantification of the cost of ignoring it.")
numbered("A Monte Carlo uncertainty framework over a defined operating envelope, including an "
         "ablation, a sensitivity analysis and an admissibility map, with the full configuration "
         "and code deposited for reproduction.")
para("The status of these results should be stated plainly at the outset. This is a model-based "
     "study. No experimental wet-gas data were used, the diagnostic estimator is specified but "
     "not fitted, and every performance figure reported is a modelled uncertainty conditional on "
     "the assumptions in Table 2, not a demonstrated measurement accuracy.", bold=True)
para("The central hypothesis is nevertheless falsifiable, and the test is specified in Section "
     "4.4 rather than deferred to the discussion. It has two parts: an independently trained "
     "diagnostic estimator should recover X_LM within the uncertainty assumed here, and "
     "disagreement between the thermodynamic and diagnostic estimates should preferentially "
     "identify realisations in which liquid arrived from upstream rather than condensing locally. "
     "If either fails on loop data, the framework is refuted in the specific way named in Section "
     "4.4.")

# ==================================================================== 2
h("2. Problem Formulation")
para("For a differential-pressure meter in wet gas the indicated gas rate is related to the true "
     "gas rate by an over-reading factor:")
eq("Q_ind  =  Q_G · φ(X_LM , ρ_G/ρ_L , Fr_G)", "1")
para("so that the correction is")
eq("Q_G  =  Q_ind ⁄ φ(X_LM , ρ_G/ρ_L , Fr_G)", "2")
para("where the Lockhart–Martinelli parameter is")
eq("X_LM  =  (ṁ_L ⁄ ṁ_G) · √(ρ_G ⁄ ρ_L)", "3")
para("with ṁ_L and ṁ_G the liquid and gas mass flow rates and Fr_G the gas densiometric Froude "
     "number. Equations (1)–(3) contain two unknowns, Q_G and ṁ_L, and a single-phase meter "
     "supplies one measurement. The system is underdetermined, and no processing of that single "
     "measurement resolves it.")
para("The problem addressed is therefore:")
para("Estimate X_LM from process and meter information already available at the station, quantify "
     "the uncertainty of that estimate, and propagate it through Eq. (2) to a defensible "
     "uncertainty on the corrected gas rate.", bold=True)
para("Throughout, the Chisholm multiplier is used for the orifice case,")
eq("φ  =  √(1 + C·X_LM + X_LM²) ,   C = (ρ_L/ρ_G)ⁿ + (ρ_G/ρ_L)ⁿ ,   n = 0.25", "4")
para("with the de Leeuw form and its Froude-dependent exponent available for Venturi and cone "
     "geometries. The choice of correlation is not the subject of this study; the estimator "
     "developed below supplies the input that any of them requires.")

# ==================================================================== 3
h("3. Method")

h("3.1 Architecture", 2)
para("Fig. 1 shows the estimation and decision flow. Two estimators of X_LM operate on different "
     "information, a fusion step combines them and quantifies their disagreement, and an "
     "acceptance test determines whether the correction is applied.", after=12)
figure("figG_method.png",
       "Fig. 1. Estimation and decision flow. The two estimators draw on structurally distinct "
       "information, so their disagreement is informative. Reference data act on the estimators "
       "through periodic calibration rather than on the real-time correction path.", width=5.5)

h("3.2 Thermodynamic estimator", 2)
para("The first estimator predicts the liquid that condenses from the gas at the meter's own "
     "conditions:")
eq("X⁽¹⁾  =  f_EOS(P , T , z)", "5")
para("where z is the molar composition vector. The calculation is a standard isothermal flash: "
     "obtain composition from the station chromatograph, obtain local pressure and temperature, "
     "perform a phase-equilibrium calculation with a cubic or reference equation of state (Peng "
     "and Robinson, 1976; Kunz and Wagner, 2012), extract the condensed mass fraction and both "
     "phase densities, and evaluate Eq. (3).")
para("This estimator is predictive rather than observational, and it has several error sources: "
     "composition uncertainty and C6+ characterisation, the limitations of the equation of state, "
     "departure from phase equilibrium at the meter, sampling representativeness, and errors in "
     "the local pressure and temperature. Any of these can bias the result in either direction.")
para("One failure mode is treated separately because it is systematic and one-directional at the "
     "population level. A flash calculation represents the liquid that the local stream should "
     "drop at the stated conditions; it does not represent liquid introduced from upstream — "
     "carryover past a separator, or re-entrainment from a low point — because that liquid is not "
     "a thermodynamic property of the local stream. The dominant unmodelled failure mode "
     "considered here is therefore under-estimation caused by externally introduced liquid. This "
     "is a statement about one specific mechanism, not a claim that the thermodynamic calculation "
     "cannot err in the other direction for the other reasons listed above.", bold=True)

h("3.3 Diagnostic estimator", 2)
para("The second estimator infers liquid loading from the meter's own behaviour. For the orifice "
     "case the feature vector is")
eq("x  =  [ P , T , ΔP , σ_ΔP , PLR , Q_ind , ρ_G ]", "6")
eq("X⁽²⁾  =  f_θ(x)", "7")
para("where σ_ΔP is the standard deviation of the high-rate differential-pressure signal over the "
     "averaging window and PLR is the permanent pressure loss ratio, available where a downstream "
     "tapping exists. The fluctuation statistics carry information because differential-pressure "
     "variance responds to liquid film formation before the mean value shifts appreciably; the "
     "permanent pressure loss responds because the film alters the recovery downstream of the "
     "plate (Zheng et al., 2019; Liu et al., 2020).")
para("The thermodynamic estimate X⁽¹⁾ is deliberately excluded from Eq. (6). Including it as a "
     "contextual feature would let the mapping learn where the thermodynamic prediction is "
     "reliable, but it would also correlate the two estimates, and Section 5.5 shows that "
     "correlation degrades the acceptance test that the architecture depends on. The two "
     "estimators are therefore structurally distinct by construction. They are not guaranteed "
     "statistically independent even so — both respond to pressure, temperature and gas density — "
     "so the covariance is retained explicitly in Section 3.5 rather than assumed away.", bold=True)

h("3.3.1 Specification of the diagnostic model", 2)
para("The diagnostic model is specified here in enough detail to be fitted and reproduced, "
     "although it is not fitted in this study. The specification is part of the contribution: an "
     "estimator that cannot be reproduced cannot be falsified.")
table([
    ["Element", "Specification", "Reason"],
    ["Model class", "Gradient-boosted regression trees with monotonic constraints, or a "
     "constrained generalised additive model",
     "Both admit hard monotonicity constraints and handle the modest feature count without "
     "requiring the data volume a neural network would"],
    ["Target", "X_LM from the reference metering of the calibration facility",
     "The latent variable itself, not the over-reading"],
    ["Output transform", "softplus, guaranteeing X⁽²⁾ > 0",
     "A negative liquid loading is unphysical and must be impossible by construction, not merely "
     "unlikely"],
    ["Monotonic constraints", "non-decreasing in σ_ΔP and in PLR at fixed P, T, ρ_G",
     "Imposes the physical direction of the diagnostic response and disciplines extrapolation"],
    ["Loss", "Pinball (quantile) loss at the 0.05, 0.50 and 0.95 quantiles",
     "Yields a predictive interval directly, rather than a point estimate to which an uncertainty "
     "must afterwards be attached"],
    ["Uncertainty", "u₂ from the fitted quantile spread, calibrated by split conformal prediction "
     "on a held-out fold",
     "Conformal calibration gives finite-sample coverage without assuming the residual "
     "distribution"],
    ["Data split", "grouped by operating condition (X_LM and Fr_G combination), not by random "
     "point",
     "Random splitting of loop data leaks information between folds because repeat points at one "
     "condition are near-duplicates, and inflates apparent accuracy"],
    ["Out-of-domain", "convex-hull or Mahalanobis distance test on x against the training set; "
     "outside it the estimator returns a flag rather than a value",
     "Prevents a regressor from silently extrapolating outside the conditions it was fitted on"],
    ["Regularisation", "depth and leaf-count limits selected by grouped cross-validation",
     "Wet-gas loop matrices are small; the dominant risk is overfitting the condition grid"],
])
para("The assumed performance of this model in the computational study — a relative standard "
     "uncertainty of 20% with a 6% transfer bias — is an assumption, and Section 6.4 identifies "
     "it as the most consequential one in the paper.", bold=True)

h("3.4 Reference-based calibration and drift control", 2)
para("Periodic reference data — test-separator runs, allocation balances, or proving data — "
     "calibrate and validate the two estimators and correct slow drift. They are not a real-time "
     "input to the correction, because test separators carry uncertainties of several per cent; "
     "admitting them per cycle would inject that uncertainty into every reading, whereas averaged "
     "over many runs they constrain a slowly varying offset effectively.")

h("3.5 Fusion with correlated estimators and the consistency index", 2)
para("Let u₁ and u₂ be the standard uncertainties of X⁽¹⁾ and X⁽²⁾, ρ₁₂ the correlation between "
     "their errors, and c = ρ₁₂u₁u₂ the covariance. The thermodynamic uncertainty is declared as")
eq("u₁²  =  u²_flash  +  u²_carry", "8")
para("where u_carry is the standard deviation of the carryover fraction over the site's operating "
     "conditions. The second term is not optional: Section 5.2 shows that omitting it makes the "
     "fused estimate worse than the diagnostic estimate alone, because the weighting below then "
     "over-trusts the thermodynamic estimator.")
para("The minimum-variance linear combination of two correlated estimates is")
eq("w₁ = (u₂² − c) ⁄ (u₁² + u₂² − 2c) ,   w₂ = 1 − w₁", "9")
eq("X_f = w₁X⁽¹⁾ + w₂X⁽²⁾ ,   u_f² = w₁²u₁² + w₂²u₂² + 2w₁w₂c", "10")
para("which reduces to inverse-variance weighting when ρ₁₂ = 0. The disagreement between the two "
     "estimates is quantified by the consistency index")
eq("Z  =  |X⁽¹⁾ − X⁽²⁾| ⁄ √(u₁² + u₂² − 2c)", "11")
para("The covariance term in the denominator of Eq. (11) matters and is easy to omit. "
     "var(X⁽¹⁾ − X⁽²⁾) = u₁² + u₂² − 2c, so assuming independence when ρ₁₂ > 0 makes the "
     "denominator too large, Z too small, and the acceptance test progressively less sensitive. "
     "Section 5.5 quantifies this: at ρ₁₂ = 0.3 the rejection rate falls from "
     f"{100*CV['reject_true_Z'][3]:.1f}% to {100*CV['reject_naive_Z'][3]:.1f}% if the covariance "
     f"is ignored, and at ρ₁₂ = 0.7 from {100*CV['reject_true_Z'][7]:.1f}% to "
     f"{100*CV['reject_naive_Z'][7]:.1f}%. In practice ρ₁₂ is estimated during the calibration of "
     "Section 3.4, from the joint residuals of the two estimators against the reference.",
     bold=True)
para("Because the thermodynamic estimator's dominant unmodelled failure is one-directional, a "
     "significant excess of X⁽²⁾ over X⁽¹⁾ is evidence of carryover rather than of noise in "
     "X⁽²⁾, and the weighting moves toward X⁽²⁾ rather than averaging. Disagreement in the "
     "opposite direction carries no such interpretation and is treated as ordinary scatter:")
eq("e = (X⁽²⁾ − X⁽¹⁾) ⁄ √(u₁² + u₂² − 2c) ,   w₁′ = w₁ ⁄ (1 + max(0, e − k)²)", "12")
para("with the damping threshold set to k = 1 throughout this study, so that damping begins only "
     "once the excess exceeds one combined standard uncertainty. The fused uncertainty is "
     "inflated by the Birge ratio max(1, Z) when the two estimates disagree by more than their "
     "stated uncertainties allow.")
para("The Birge ratio is used here as a robust uncertainty-inflation heuristic, not as a "
     "statistically optimal estimator. Its justification is pragmatic: when two estimates of the "
     "same quantity disagree by more than their stated uncertainties admit, at least one of those "
     "uncertainties is understated, and reporting the unadjusted u_f would be indefensible. It is "
     "not claimed to be the minimum-variance response to that situation, and the sensitivity of "
     "the results to this choice is small because the acceptance test of Eq. (11) removes the "
     "cases where inflation would be largest.", bold=True)

h("3.6 Correction and acceptance algorithm", 2)
para("Algorithm 1 — correction decision", bold=True)
code_block(
    "1.  Acquire P, T, composition z and meter diagnostics.\n"
    "2.  X1 := f_EOS(P, T, z);  u1 := sqrt(u_flash^2 + u_carry^2)      [Eq. 5, 8]\n"
    "3.  X2 := f_theta(x);      u2 from the calibrated quantile spread  [Eq. 6, 7]\n"
    "4.  c  := rho_12 * u1 * u2        rho_12 from calibration (Sec 3.4)\n"
    "5.  Z  := |X1 - X2| / sqrt(u1^2 + u2^2 - 2c)                       [Eq. 11]\n"
    "6.  w1, w2 := GLS weights; apply asymmetric damping with k = 1     [Eq. 9, 12]\n"
    "7.  X_f, u_f := fused estimate; inflate u_f by max(1, Z)           [Eq. 10]\n"
    "8.  if Z <= Z_max:\n"
    "        Q_G := Q_ind / phi(X_f, rho_G/rho_L, Fr_G)                 [Eq. 2]\n"
    "        propagate u_f, correlation and meter uncertainties to U(Q_G)\n"
    "        status := CORRECTION APPLIED\n"
    "9.  else:\n"
    "        Q_G := Q_ind          (unchanged)\n"
    "        status := UNCORRECTED, LOW CONFIDENCE\n"
    "10. Publish Q_G, U(Q_G), X_f, Z and status.")

# ==================================================================== 4
h("4. Computational Method")

h("4.1 Forward model and operating envelope", 2)
para("The forward model is Eq. (4) evaluated at sampled operating conditions. Gas density is "
     "computed from Standing pseudo-critical properties with the Dranchuk and Abou-Kassem (1975) "
     "Z-factor correlation, which over the sampled envelope returns 48.5–85.5 kg/m³ and Z of "
     "0.785–0.889.")

h("4.2 Sampling distributions and assumed uncertainties", 2)
para("Table 2 gives every distribution used, so that the study can be reproduced and so that a "
     "reader can see exactly which quantities are assumed rather than measured.", after=6)
para("Table 2. Complete specification of the Monte Carlo. Every entry in the final column marked "
     "'assumed' is a modelling choice, not a measurement; Section 6.4 discusses their standing "
     "and Section 5.6 tests the sensitivity of the conclusions to the most consequential one.",
     italic=True, size=8.5, after=4)
table([
    ["Quantity", "Distribution", "Range / value", "Basis"],
    ["Line pressure P", "Uniform", "60–85 kg/cm²", "Assumed operating envelope"],
    ["Temperature T", "Uniform", "30–60 °C", "Assumed operating envelope"],
    ["Condensate–gas ratio", "Uniform", "5–100 bbl/MMscf", "Assumed; converted to X_LM by Eq. (3)"],
    ["Condensate density ρ_L", "Uniform", "640–720 kg/m³", "Typical gas-condensate range"],
    ["Superficial gas velocity", "Uniform", "8–18 m/s in a 154 mm line", "Assumed; sets Fr_G"],
    ["Gas density ρ_G", "Derived", "48.5–85.5 kg/m³", "Standing pseudo-criticals with DAK Z-factor"],
    ["u_flash, relative", "Gaussian", "12%", "Assumed: flash calculation with composition uncertainty"],
    ["Carryover occurrence", "Bernoulli", "p = 0.25", "Assumed prevalence; swept 0–60% in Section 5.6"],
    ["Carryover magnitude", "Uniform", "U(0.15, 0.60) of total liquid",
     "Assumed; the fraction invisible to the flash calculation"],
    ["u_carry, relative", "Derived", "17.5%",
     "Standard deviation of the Bernoulli × Uniform mixture above, entering Eq. (8)"],
    ["u₂ random, relative", "Gaussian", "20%", "Assumed performance of the fitted diagnostic model"],
    ["u₂ transfer bias, relative", "Gaussian", "6%, systematic",
     "Assumed loop-to-site transfer error of the fitted mapping"],
    ["ρ₁₂", "Parameter", "0 baseline; swept 0–0.7", "Correlation between estimator errors, Section 5.5"],
    ["Correlation residual", "Gaussian", "0.6%, systematic", "Assumed, after site calibration"],
    ["Meter and secondary instrumentation", "Gaussian", "0.7%", "Dry-gas meter and transmitter performance"],
    ["Realisations", "—", "300,000 per configuration; 4,000 per envelope cell",
     "Fixed seed; see Data availability"],
])

h("4.3 Metrics", 2)
para("Reported metrics are mean error (bias), mean absolute error, root-mean-square error, "
     "maximum absolute error, and the 95% coverage band taken as the larger absolute value of the "
     "2.5th and 97.5th percentiles of the simulated error distribution. Errors are relative:")
eq("ε_Q  =  (Q_est − Q_ref) ⁄ Q_ref × 100 %", "13")
para("For configurations including the acceptance test, metrics are computed over accepted "
     "realisations and the acceptance rate is reported alongside, since the method's output on "
     "rejected realisations is the uncorrected value with a flag rather than a corrected value.")

h("4.4 Validation design and falsification criteria", 2)
para("Because the study is computational, the experiment that would test it is specified here in "
     "the Methods rather than deferred, so that the claims can be read against the test that "
     "would refute them.")
para("Facility and configuration. A wet-gas flow loop with independent gas and liquid reference "
     "metering, controlled liquid injection, an orifice meter of known geometry with upstream and "
     "downstream tappings, pressure and temperature instrumentation, and either a chromatograph "
     "or a gas of known composition. The full high-rate differential-pressure signal must be "
     "recorded so that σ_ΔP and the spectral features of Eq. (6) can be computed rather than "
     "assumed.")
para("Test matrix. X_LM at 0, 0.01, 0.02, 0.04, 0.06, 0.08 and 0.10, each at a minimum of four "
     "gas densiometric Froude numbers spanning the operating range. Deliberate liquid injection "
     "upstream of the flash-equilibrium point, in a subset of runs, to create the carryover "
     "condition that the consistency index is claimed to detect.")
para("Comparisons. Four cases reported against the reference: (A) the uncorrected meter; (B) the "
     "standard correlation supplied with the reference liquid loading, which bounds achievable "
     "performance; (C) the estimated liquid loading against the reference liquid loading, which "
     "tests the estimator directly and independently of the correction; and (D) the fully "
     "corrected gas rate. Reporting (C) separately matters: it is the only comparison that "
     "isolates this paper's contribution from the correlation's.")
para("Falsification criteria. The framework is refuted if any of the following holds on loop "
     "data: the fitted diagnostic estimator does not recover X_LM within the 20% relative "
     "uncertainty assumed in Table 2; the consistency index does not preferentially flag the runs "
     "with deliberate upstream injection; the measured correlation ρ₁₂ between the estimator "
     "residuals is large enough that the acceptance test loses the sensitivity reported in "
     "Section 5.5; or the corrected gas rate fails to improve on the uncorrected meter within the "
     "admissibility region of Fig. 6.", bold=True)

# ==================================================================== 5
h("5. Results")
para("Every figure in this section is a simulation result. The quantities reported are modelled "
     "uncertainties conditional on Table 2, and the word 'accuracy' is deliberately avoided.",
     italic=True)

h("5.1 Forward-model check", 2)
para("At representative envelope conditions, condensate–gas ratios of 50 and 100 bbl/MMscf give "
     f"over-readings of 7.9% and 15.7%, and the simulated population mean over-reading across the "
     f"envelope is {UNC['bias']:+.2f}% with a 95% band of ±{UNC['band95']:.2f}%. These magnitudes "
     "are consistent with uncorrected errors reported for DP meters in wet gas, which is a "
     "necessary check on everything downstream.")

h("5.2 Ablation study", 2)
para("Table 3 decomposes the method. The oracle row applies the same correlation supplied with "
     "the true liquid loading and bounds what any estimator can achieve; the residual "
     f"±{ORC['band95']:.2f}% is the correlation and meter uncertainty alone.", after=6)
para("Table 3. Simulated contribution of each element of the estimator, at ρ₁₂ = 0. Metrics in "
     "per cent of gas rate over 300,000 realisations.", italic=True, size=8.5, after=4)
rows = [["Configuration", "Bias", "MAE", "RMSE", "Max |ε|", "95% band", "Accepted"]]
for label, m in [("Uncorrected meter", UNC),
                 ("Correlation with known X_LM (oracle)", ORC),
                 ("Thermodynamic estimator alone", E1),
                 ("Diagnostic estimator alone", E2),
                 ("Fusion, carryover omitted from budget", FN),
                 ("Fusion, carryover allowance declared", FH),
                 ("Asymmetric weighting, Eq. (12)", FR),
                 ("Full method, with acceptance test", SW)]:
    rows.append([label, f"{m['bias']:+.2f}", f"{m['mae']:.2f}", f"{m['rmse']:.2f}",
                 f"{m['maxabs']:.2f}", f"±{m['band95']:.2f}",
                 f"{100*m['accept_rate']:.0f}%"])
table(rows)
para(f"The uncertainty budget is not cosmetic. Fusing while the thermodynamic estimator declares "
     f"only its flash uncertainty gives ±{FN['band95']:.2f}%, worse than the diagnostic estimator "
     f"alone (±{E2['band95']:.2f}%). Declaring the carryover allowance of Eq. (8) recovers "
     f"±{FH['band95']:.2f}%. This is a general point about fusing estimators with different "
     "failure modes: inverse-variance weighting is only as good as the declared variances.")
para(f"The asymmetric rule improves this to ±{FR['band95']:.2f}% and the acceptance test to "
     f"±{SW['band95']:.2f}%, reducing simulated bias from {UNC['bias']:+.2f}% uncorrected to "
     f"{SW['bias']:+.2f}%. The gap to the oracle remains substantial — ±{SW['band95']:.2f}% "
     f"against ±{ORC['band95']:.2f}% — and no amount of fusion closes it. Estimating liquid "
     "loading rather than measuring it costs roughly a factor of two in coverage band.",
     bold=True)
figure("figB_ablation.png",
       "Fig. 2. Simulated ablation of the estimator. The naive-budget configuration is worse than "
       "the diagnostic estimator alone.", width=5.9)
figure("figE_distribution.png",
       "Fig. 3. Simulated error distribution before and after correction. The uncorrected "
       "distribution is strictly positive because wet-gas over-reading has a sign.", width=5.6)

h("5.3 Behaviour of the consistency index", 2)
para(f"Carryover is present in {100*SEL['all']:.0f}% of simulated realisations, in "
     f"{100*SEL['accepted']:.0f}% of accepted realisations, and in {100*SEL['rejected']:.0f}% of "
     "rejected realisations. The test is therefore a specific detector of the thermodynamic "
     "estimator's dominant failure mode rather than an indiscriminate filter.", bold=True)
figure("figA_estimator_agreement.png",
       "Fig. 4. Left: simulated agreement between the two estimators, separated by whether "
       "upstream carryover is present. Right: distribution of the consistency index for the two "
       "populations, with the acceptance threshold marked.", width=6.2)

h("5.4 Threshold selection", 2)
para("Table 4. Simulated effect of the acceptance threshold on retained data and coverage.",
     italic=True, size=8.5, after=4)
zr = [["Z_max", "Accepted", "95% band of accepted"]]
for zt, ar, bb in zip(ZS["Z"], ZS["accept"], ZS["band95"]):
    if zt in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
        zr.append([f"{zt:.1f}", f"{100*ar:.1f}%", f"±{bb:.2f}%"])
table(zr, fs=9)
para("A tight threshold improves the coverage of what remains but discards a large fraction of "
     "operating time, which for a fiscal or allocation measurement is itself a cost. Z_max = 3 "
     "retains almost all data while removing the cases the estimator cannot handle. The "
     "appropriate value at a given installation depends on whether coverage or completeness is "
     "the priority.")

h("5.5 Effect of correlation between the estimators", 2)
para("The two estimates are structurally distinct but not guaranteed statistically independent: "
     "both respond to pressure, temperature and gas density, and any implementation that admitted "
     "X⁽¹⁾ into the diagnostic feature vector would correlate them further. Fig. 5 varies ρ₁₂ "
     "from 0 to 0.7 and compares treating the estimates as independent against retaining the "
     "covariance term.")
para("Table 5. Simulated cost of assuming independence. Rejection rate is the fraction of "
     "realisations on which the correction is withheld.", italic=True, size=8.5, after=4)
cr = [["ρ₁₂", "Rejection rate, Z assumes independence", "Rejection rate, Z retains covariance",
       "Detector specificity, covariance retained"]]
for i, rho in enumerate(CV["rho"]):
    if rho in (0.0, 0.2, 0.3, 0.5, 0.7):
        cr.append([f"{rho:.1f}", f"{100*CV['reject_naive_Z'][i]:.1f}%",
                   f"{100*CV['reject_true_Z'][i]:.1f}%", f"{100*CV['spec_true_Z'][i]:.1f}%"])
table(cr, fs=9)
para("The consequence is one-directional and severe. As ρ₁₂ grows, a consistency index that "
     "assumes independence has a denominator that is too large, so Z shrinks, and the acceptance "
     f"test progressively stops firing: the rejection rate falls from "
     f"{100*CV['reject_true_Z'][7]:.1f}% to {100*CV['reject_naive_Z'][7]:.1f}% at ρ₁₂ = 0.7. The "
     "test does not fail loudly; it quietly accepts everything, which is the worst failure mode "
     "available to a mechanism whose purpose is to withhold a correction.", bold=True)
para("For the point estimate the effect is different and smaller. Generalised least-squares "
     "weights are minimum-variance but not minimum-error when one estimator carries an unmodelled "
     "bias, and in this regime the error is bias-dominated, so the covariance-aware weights give "
     f"a slightly wider band at high ρ₁₂ (±{CV['band_gls_w'][6]:.2f}% against "
     f"±{CV['band_naive_w'][6]:.2f}% at ρ₁₂ = 0.6) rather than a narrower one. The operative "
     "mechanism against bias remains the asymmetric damping of Eq. (12), not the weighting.")
para("Two practical consequences follow. First, X⁽¹⁾ should be excluded from the diagnostic "
     "feature vector, as in Eq. (6), so that ρ₁₂ is kept small by construction. Second, ρ₁₂ "
     "should be measured during calibration from the joint residuals of the two estimators and "
     "retained in Eqs. (9)–(12), rather than assumed to be zero.", bold=True)
figure("figH_covariance.png",
       "Fig. 5. Simulated cost of treating structurally distinct estimates as independent. Left: "
       "effect on the fused estimate. Right: effect on the acceptance test, which loses "
       "sensitivity as the correlation grows.", width=6.2)

h("5.6 When does hybrid fusion outperform either estimator alone?", 2)
para("The value of combining the two estimators depends on how often the thermodynamic one is "
     "blind. Fig. 6 varies carryover prevalence from 0 to 60% of operating time.")
para(f"With no carryover the thermodynamic estimator is the better of the two "
     f"(±{DS['E1'][0]:.2f}% against ±{DS['E2'][0]:.2f}%) and the method correctly falls back "
     f"toward it (±{DS['robust'][0]:.2f}%). Between roughly 5% and 20% prevalence the fused "
     f"estimate beats either estimator alone. Beyond that the diagnostic estimator becomes "
     f"competitive again, because the thermodynamic estimate is wrong too often to contribute.")
para("The practical reading is a deployment rule: the hybrid architecture is most beneficial in "
     "installations where upstream separation is effective but imperfect, which is the condition "
     "an inlet separator and dehydration train produce. Where carryover is frequent the sensible "
     "configuration is the diagnostic estimator alone, with the consistency index retained purely "
     "as a validity check. Carryover prevalence is therefore the first quantity to establish at a "
     "candidate installation, and it can be established from historical separator and meter data "
     "without any new instrumentation.", bold=True)
figure("figF_designspace.png",
       "Fig. 6. Simulated effect of upstream carryover prevalence on the 95% error band of each "
       "configuration. The crossing points define the regime in which fusion is worthwhile.",
       width=5.6)

h("5.7 Sensitivity analysis", 2)
para("Table 6. Normalised sensitivity coefficients and the corresponding contributions to the "
     "combined standard uncertainty of the corrected gas rate, at X_LM = 0.05.",
     italic=True, size=8.5, after=4)
sr = [["Input", "Sensitivity S_i", "Relative uncertainty", "Contribution to u_c(Q_G)"]]
for lab, S, u in [("Liquid loading estimate X_LM", SENS["Liquid loading estimate X_LM"], 0.145),
                  ("Gas density ρ_G", SENS["Gas density rho_g"], 0.004),
                  ("Differential pressure ΔP", SENS["Differential pressure dP"], 0.005),
                  ("Liquid density ρ_L", SENS["Liquid density rho_l"], 0.03)]:
    sr.append([lab, f"{S:+.3f}", f"{100*u:.1f}%", f"{abs(S)*u*100:.2f}%"])
table(sr)
para("The corrected rate is an order of magnitude more sensitive to a relative change in gas "
     "density or differential pressure (S ≈ +0.5, the square-root dependence of the DP equation) "
     "than to a relative change in the liquid-loading estimate (S ≈ −0.05). Sensitivity alone "
     "would therefore suggest liquid loading hardly matters. It matters because of the size of "
     "its uncertainty, not its coefficient: gas density and differential pressure are known to a "
     "fraction of a per cent, whereas the liquid-loading estimate carries an uncertainty of order "
     "15%. The product — the final column — is what enters the budget, and on that basis the "
     "liquid-loading estimate dominates by roughly an order of magnitude. Sensitivity "
     "coefficients reported without the associated uncertainties would invert the conclusion.",
     bold=True)
figure("figC_sensitivity.png",
       "Fig. 7. Normalised sensitivity coefficients. The liquid-loading estimate has the smallest "
       "coefficient and the largest uncertainty contribution; see Table 6.", width=5.3)

h("5.8 Admissibility envelope", 2)
para("Fig. 8 maps the simulated 95% band and the acceptance rate over the (X_LM, Fr_G) plane, "
     "classifying each cell by whether the ±2% and ±3% levels are met. This defines a validity "
     "domain rather than a single headline figure. Accuracy degrades with liquid loading as the "
     "correlation's sensitivity to X_LM grows; the Froude dependence is weak over the range "
     "examined because the Chisholm form carries no explicit Froude term.")
figure("figD_envelope.png",
       "Fig. 8. Left: simulated admissibility of the correction over the (X_LM, Fr_G) plane. "
       "Right: acceptance rate of the consistency test. The upper part of the X_LM range lies "
       "beyond the loading expected for the sampled duty and is included to show where the method "
       "fails.", width=6.2)

# ==================================================================== 6
h("6. Discussion")

h("6.1 Comparison with existing approaches", 2)
para("Table 7. Routes to a wet-gas corrected gas rate, compared by what supplies the liquid "
     "information and by what each requires.", italic=True, size=8.5, after=4)
table([
    ["Approach", "Liquid information", "Additional hardware", "Experimental data required",
     "Relation to this work"],
    ["Empirical correlations", "Assumed known", "None", "None beyond the original fit",
     "Retained unchanged as the correction stage"],
    ["Third pressure tap (Nasr et al., 2026)", "Measured", "Additional tapping and transmitter",
     "Yes, for the specific geometry", "Closest existing approach; adds instrumentation"],
    ["Dedicated multiphase metering", "Measured directly", "Dedicated meter", "Vendor calibration",
     "Reference case rather than competitor"],
    ["Data-driven rate prediction (Pereira et al., 2026; Hosseini et al., 2026a)",
     "Bypassed; rates learned directly", "None", "Yes, covering the installation",
     "Learns a different target; no explicit latent variable"],
    ["Hybrid physics–ML over-reading (Alkhurayef and Alsarkhi, 2026a)",
     "Bypassed; over-reading learned as a residual", "None", "Yes (1,868 points reported)",
     "Closest in spirit; learns the correction rather than its input"],
    ["This work", "Estimated as a latent variable", "None; uses existing diagnostics",
     "Yes, to fit the diagnostic estimator before deployment", "—"],
])
para("The distinction from Nasr et al. (2026) is the one most likely to be raised, since both "
     "target the orifice meter and both aim at quantifying liquid. They add a physical "
     "measurement point and obtain a more direct observation; the present approach attempts to "
     "extract the same information from instrumentation already present, and accepts a weaker "
     "observation in exchange. These are complementary: a third tapping, where it can be "
     "installed, would enter the framework of Section 3 as a higher-quality diagnostic estimator, "
     "and the fusion and acceptance machinery would apply unchanged.")
para("The distinction from the hybrid and data-driven work is what is learned. Those methods "
     "learn the correction; this one learns the correction's input and leaves the correlation "
     "intact. The cost is an extra inference step and a weaker result than direct learning can "
     "achieve where training data are plentiful. The benefit is that the physical form governs "
     "extrapolation, the learned component is a single scalar with a stated uncertainty, and a "
     "second estimate of that scalar exists and can be cross-checked — which is what makes the "
     "rejection mechanism possible at all. A method that learns the over-reading directly has no "
     "second opinion to consult.", bold=True)
para("The uncertainty quantification framework of Hosseini et al. (2026b) addresses a related "
     "problem for machine-learning wet-gas metering. The difference in emphasis is that their "
     "framework quantifies the uncertainty of a learned predictor, whereas the mechanism here "
     "uses the disagreement between two structurally distinct estimators to decide whether to "
     "produce an output at all.")

h("6.2 Practical implementation", 2)
para("The method is implementable as a secondary-instrumentation layer on an edge gateway "
     "adjacent to the existing flow computer, reading the transmitters, chromatograph and meter "
     "diagnostics and publishing the corrected rate, its uncertainty, the fused liquid loading "
     "and the status flag. Because it is realised in software and reads existing signals, it "
     "introduces no additional process restriction and therefore no additional pressure drop.",
     after=12)
figure("fig6_deployment_topology.png",
       "Fig. 9. Implementation as a secondary-instrumentation layer. The path to the flow "
       "computer is read-only, so a fault in the correction layer cannot alter the primary "
       "measurement.", width=6.0)
para("Two properties matter for an installed measurement system. The failure mode on loss of the "
     "layer is the present-day behaviour of the meter. And the rejection mechanism means the "
     "layer declines to answer rather than answering unreliably, which is the behaviour a "
     "measurement system should exhibit when its assumptions are not met.")

h("6.3 Generalisation to other meter types", 2)
para("The architecture is meter-agnostic but the diagnostic estimator is not. For multipath "
     "ultrasonic meters the natural features are the deviation of measured speed of sound from "
     "the value computed from composition (AGA Report No. 10), gain levels, signal-to-noise "
     "ratio, and per-path velocity ratios, since the liquid film degrades near-wall chords before "
     "mid-radius chords. For Coriolis meters they are drive gain and the deviation of indicated "
     "mixture density from the equation-of-state gas density.")
para("These are extension pathways, not results. No computational assessment of either is "
     "presented, and the Coriolis case is expected to be harder: resolving gas from total mass "
     "requires the liquid fraction to a tighter tolerance than a differential-pressure meter "
     "does.", bold=True)

h("6.4 Limitations", 2)
bullet("No experimental wet-gas data were used. Every result is a modelled uncertainty. The "
       "over-reading correlation serves as the forward model as well as sitting inside the "
       "estimator, with an added model-form term standing in for its real error; an independent "
       "experimental reference is required to break that circularity.")
bullet("The diagnostic mapping f_θ is specified in Section 3.3.1 but not fitted. Its assumed 20% "
       "relative uncertainty and 6% transfer bias are the most consequential assumptions in the "
       "paper: the ablation of Table 3 and the design rule of Section 5.6 both depend on the "
       "relative standing of u₁ and u₂, and a fitted estimator that performed materially better "
       "or worse would move the crossing points of Fig. 6.")
bullet("The carryover model is an assumption. Section 5.6 examines the sensitivity of the "
       "conclusions to its prevalence directly and the qualitative conclusions hold across the "
       "range examined, but the specific figures in Table 3 are conditional on p = 0.25.")
bullet("ρ₁₂ is treated as a parameter rather than estimated from data. Its value at a real "
       "installation is unknown until the joint residuals are measured, which is why Section 4.4 "
       "makes that measurement part of the validation protocol.")
bullet("Diagnostic availability is installation-dependent. The permanent pressure loss ratio "
       "requires a downstream tapping that not every meter run has; where absent, u₂ widens and "
       "the framework must reflect that rather than proceed unchanged.")
bullet("Slugging and flow-regime transition are not modelled. The correlations used are valid in "
       "the annular-mist region; operation outside it requires detection and suspension rather "
       "than extrapolation.")
bullet("Results are for the orifice case at one composition family and one line size. The "
       "Chisholm form carries no explicit Froude dependence, which limits what Fig. 8 can say "
       "about the Froude axis.")

# ==================================================================== 7
h("7. Conclusions")
para("Wet-gas corrections for differential-pressure meters are mature, and the obstacle to "
     "applying them at an installed metering station is not the correlation but its input. This "
     "paper treated liquid loading as a latent variable to be estimated from information already "
     "present at the station, rather than treating the over-reading as a quantity to be learned "
     "from experimental data.")
para("A Monte Carlo study over a rich-gas envelope gives the following simulated results. "
     f"Correction reduces the 95% error band of the orifice case from ±{UNC['band95']:.2f}% to "
     f"±{SW['band95']:.2f}%, against ±{ORC['band95']:.2f}% for the same correlation supplied with "
     "the true liquid loading. Combining a thermodynamic and a diagnostic estimate requires the "
     "thermodynamic estimator to declare an uncertainty that includes the upstream carryover it "
     f"cannot observe; without that allowance, inverse-variance fusion is worse "
     f"(±{FN['band95']:.2f}%) than the diagnostic estimator alone (±{E2['band95']:.2f}%). An "
     "asymmetric weighting motivated by the one-directional nature of that failure mode improves "
     f"this to ±{FR['band95']:.2f}%.")
para(f"The consistency index between the two estimates is a specific detector of that failure "
     f"mode: carryover occurs in {100*SEL['all']:.0f}% of simulated realisations and in "
     f"{100*SEL['rejected']:.0f}% of those the test rejects. Because the two estimates are not "
     "statistically independent, the covariance term must be retained in the index; omitting it "
     "does not degrade the test gracefully but progressively disables it, so that it accepts "
     "everything.", bold=True)
para("The sensitivity analysis shows that the corrected rate is an order of magnitude less "
     "sensitive to a relative change in liquid loading than to gas density or differential "
     "pressure, yet liquid loading dominates the uncertainty budget because its own uncertainty "
     "is roughly thirty times larger. Sensitivity coefficients and uncertainty contributions must "
     "be reported together.")
para("These are modelled uncertainties, not measured accuracies. Section 4.4 specifies the loop "
     "experiment that would convert them, including the comparison that isolates the estimator "
     "from the correlation and the criteria that would refute the framework.", bold=True)

# ==================================================================== DECLARATIONS
h("CRediT authorship contribution statement")
para("Leon Sandler: Conceptualization, Methodology, Software, Formal analysis, Investigation, "
     "Visualization, Writing – original draft, Writing – review & editing.")

h("Declaration of Competing Interest")
para("The author declares no known competing financial interests or personal relationships that "
     "could have appeared to influence the work reported in this paper.")

h("Funding")
para("This research received no specific grant from funding agencies in the public, commercial, "
     "or not-for-profit sectors.")

h("Data availability")
para("No experimental data were used. The entire quantitative content of this paper is "
     "computational, and the complete reproducibility package — the Python implementation, the "
     "simulation configuration, the random seed, the figure generators and the generated summary "
     f"data — is openly available at {GITHUB} and permanently archived at "
     f"https://doi.org/{DOI_CODE}. Running the deposited scripts reproduces every table and "
     f"figure in this paper. A preprint of the manuscript is archived at "
     f"https://doi.org/{DOI_PAPER}.")

h("Declaration of generative AI in the writing process")
para("During the preparation of this work the author used Claude (Anthropic) to assist with "
     "literature synthesis, analysis design and drafting. After using this tool, the author "
     "reviewed and edited the content as needed, verified the cited literature, and takes full "
     "responsibility for the content of the publication. No AI tool is listed as an author.")

h("References")
for r in [
 "Alkhurayef, A., Alsarkhi, A., 2026a. A new hybrid physics–ML model for predicting over-reading in differential pressure measurements under wet gas flow. Flow Meas. Instrum. 111, 103465. https://doi.org/10.1016/j.flowmeasinst.2026.103465",
 "Alkhurayef, A., Al-Sarkhi, A., AbdulMajeed, G., Gajbhiye, R., 2026b. A comprehensive review of wet gas flow correlations for Venturi meter. Flow Meas. Instrum. 109, 103224. https://doi.org/10.1016/j.flowmeasinst.2026.103224",
 "American Gas Association, Report No. 3 / API MPMS Chapter 14.3. Orifice Metering of Natural Gas and Other Related Hydrocarbon Fluids.",
 "American Gas Association, Report No. 8. Thermodynamic Properties of Natural Gas and Related Gases.",
 "American Gas Association, Report No. 9. Measurement of Gas by Multipath Ultrasonic Meters.",
 "American Gas Association, Report No. 10. Speed of Sound in Natural Gas and Other Related Hydrocarbon Gases.",
 "American Gas Association, Report No. 11 / API MPMS Chapter 14.9. Measurement of Natural Gas by Coriolis Meter.",
 "Birge, R.T., 1932. The calculation of errors by the method of least squares. Phys. Rev. 40, 207–227. https://doi.org/10.1103/PhysRev.40.207",
 "Chisholm, D., 1977. Research note: two-phase flow through sharp-edged orifices. J. Mech. Eng. Sci. 19, 128–130. https://doi.org/10.1243/jmes_jour_1977_019_027_02",
 "de Leeuw, R., 1997. Liquid correction of Venturi meter readings in wet gas flow. North Sea Flow Measurement Workshop, Kristiansand.",
 "Dranchuk, P.M., Abou-Kassem, J.H., 1975. Calculation of Z factors for natural gases using equations of state. J. Can. Pet. Technol. 14 (3). https://doi.org/10.2118/75-03-03",
 "Gajan, P., Decaudin, Q., Couput, J.P., 2015. Analysis of high pressure tests on wet gas flow metering with a Venturi meter. Flow Meas. Instrum. 44, 126–131. https://doi.org/10.1016/j.flowmeasinst.2014.12.004",
 "He, D., Chen, S., Bai, B., 2019. A V-Cone meter measurement correlation in low pressure wet gas based on Chisholm model. Flow Meas. Instrum. 66, 12–17. https://doi.org/10.1016/j.flowmeasinst.2019.01.019",
 "Hosseini, S., Chinello, G., Lindsay, G., Loweimi, E., Ansari, M.A., McGlinchey, D., 2026a. Transfer learning for data-driven wet gas flow metering: enhancing generalisation in digital measurement systems. Flow Meas. Instrum. 108, 103146. https://doi.org/10.1016/j.flowmeasinst.2025.103146",
 "Hosseini, S., Chinello, G., Lindsay, G., McGlinchey, D., 2026b. A robust uncertainty quantification framework for machine learning–based wet-gas flow metering. Measurement 269, 120670. https://doi.org/10.1016/j.measurement.2026.120670",
 "ISO 5167 (all parts). Measurement of fluid flow by means of pressure differential devices inserted in circular cross-section conduits running full.",
 "ISO/TR 11583:2012. Measurement of wet gas flow by means of pressure differential devices inserted in circular cross-section conduits.",
 "JCGM 100:2008. Evaluation of measurement data — Guide to the expression of uncertainty in measurement.",
 "Kunz, O., Wagner, W., 2012. The GERG-2008 wide-range equation of state for natural gases and other mixtures. J. Chem. Eng. Data 57, 3032–3091. https://doi.org/10.1021/je300655b",
 "Liu, W., Ma, Y., Lyu, J., Shao, J., Wang, S., 2020. Wet gas pressure drop across orifice plate in horizontal pipes in the region of flow pattern transition. Flow Meas. Instrum. 71, 101678. https://doi.org/10.1016/j.flowmeasinst.2019.101678",
 "Lockhart, R.W., Martinelli, R.C., 1949. Proposed correlation of data for isothermal two-phase, two-component flow in pipes. Chem. Eng. Prog. 45 (1), 39–48.",
 "Murdock, J.W., 1962. Two-phase flow measurement with orifices. J. Basic Eng. 84, 419–432. https://doi.org/10.1115/1.3658657",
 "Nasr, M., Chacon, P., Brenskelle, L., Pereyra, E., 2026. Use of third pressure tap for liquid detection and quantification in an orifice plate meter for gas-liquid systems. Flow Meas. Instrum. 110, 103354. https://doi.org/10.1016/j.flowmeasinst.2026.103354",
 "Pan, Y., Hong, Y., Sun, Q., Zheng, Z., Wang, D., Niu, P., 2019. A new correlation of wet gas flow for low pressure with a vertically mounted Venturi meter. Flow Meas. Instrum. 70, 101636. https://doi.org/10.1016/j.flowmeasinst.2019.101636",
 "Peng, D.-Y., Robinson, D.B., 1976. A new two-constant equation of state. Ind. Eng. Chem. Fundam. 15, 59–64. https://doi.org/10.1021/i160057a011",
 "Pereira, L.O.V., Farias, M.H., Rocha, W.F.d.C., Franco, L.G., Ramos, R., 2026. Machine learning-based prediction of gas and liquid flow rates in wet gas using single and dual cone meter configurations. Flow Meas. Instrum. 111, 103453. https://doi.org/10.1016/j.flowmeasinst.2026.103453",
 "Steven, R.N., 2002. Wet gas metering with a horizontally mounted Venturi meter. Flow Meas. Instrum. 12, 361–372. https://doi.org/10.1016/S0955-5986(02)00003-1",
 "Vovk, V., Gammerman, A., Shafer, G., 2005. Algorithmic Learning in a Random World. Springer, New York.",
 "Zheng, X., He, D., Bai, B., 2019. Pressure drop of wet gas flow with ultra-low liquid loading through DP meters. Flow Meas. Instrum. 70, 101664. https://doi.org/10.1016/j.flowmeasinst.2019.101664",
]:
    para(r, size=9, after=4)

out = os.path.join(HERE, "FMI_Hybrid_Liquid_Loading_Estimation_v2.docx")
doc.save(out)
print("saved", out)
print("abstract words:", len(ABSTRACT.split()))
