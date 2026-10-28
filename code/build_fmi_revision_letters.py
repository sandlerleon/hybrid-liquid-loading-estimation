# -*- coding: utf-8 -*-
"""Cover letter, point-by-point response, pasteable replies for the Elsevier review platform, Highlights and Title Page for
revision 1 of FLOWMEASINST-D-26-00971. Numbers are read from fmi_revision_results.json.

    python build_fmi_revision_letters.py
"""
import copy
import json
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor
from docx.text.paragraph import Paragraph

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SRCD = r"C:\Users\Leon\Downloads\FMI Manuscript"
OUTD = os.path.join(SRCD, "revision1")
os.makedirs(OUTD, exist_ok=True)
R = json.load(open(os.path.join(HERE, "fmi_revision_results.json"), encoding="utf-8"))
V = json.load(open(os.path.join(HERE, "fmi_revision_verification.json"), encoding="utf-8"))
assert all(v["passed"] for v in V.values())

DATE = "27 October 2026"
MS = "FLOWMEASINST-D-26-00971"
TITLE = "Hybrid Physics–Diagnostic Estimation of Liquid Loading for Wet-Gas Flowmeter Correction: A Model-Based Uncertainty Framework"
DT, MF, WT, RB, PR = R["detector"], R["modelform"], R["weighting"], R["robustness"], R["propagation"]
CF3, CF1 = DT["confusion_carryover"]["3.0"], DT["confusion_carryover"]["1.0"]
MURD, MATCH = MF["Murdock (independent orifice correlation)"], MF["matched"]
_fp = RB["crossing"]["fine_p"]
LASTF = max(p for p, d in zip(_fp, RB["crossing"]["full_minus_e2"]) if d < 0)
LASTA = max(p for p, d in zip(_fp, RB["crossing"]["asym_minus_e2"]) if d < 0)
pct = lambda x, d=0: ("%." + str(d) + "f%%") % (100 * x)

# ============================================================================================ content
R1 = [
    ("Novelty: emphasize the integrated estimation and decision framework as the principal contribution.",
     "Accepted. Section 1.3 now states that the principal contribution is the integrated estimation-and-decision framework and not any "
     "single component: the thermodynamic flash, the diagnostic regression and least-squares fusion are established, and what is added is "
     "their combination under an uncertainty budget that includes carryover, a one-sided damping rule, and a covariance-aware "
     "consistency test that decides whether a correction is applied. The list of contributions in Section 1.4 now begins with the "
     "framework, and the Abstract is reorganized around it.",
     "Abstract; Section 1.3 (new paragraph); Section 1.4 (contributions 1–6 rewritten)."),
    ("Fusion benefits: clarify when fusion outperforms individual estimators; the diagnostic-only case has a narrower baseline 95% error band.",
     "You are right, and the manuscript now says so directly. In the reference case the diagnostic estimator alone (±3.99%%) is narrower than "
     "every fused configuration of Table 3, including the full method (±4.26%%); the Abstract, Section 5.2 and the Conclusions state this. "
     "The conditions under which fusion does outperform it are now mapped with common random numbers: when carryover occupies less than "
     "about %d%% of operating time (Fig. 10b); when the diagnostic estimator is poorer than assumed, for example 30%% or more instead of "
     "20%% (Fig. 10a, d); and when the diagnostic estimator carries a persistent positive bias at one site (Fig. 10c). Section 5.10 "
     "adds a comparison with alternative weighting rules, and shows that a one-sided hard switch is narrower than the diagnostic estimator "
     "alone at all prevalences examined, while the rule of Eq. (12) is better only when carryover is rare." % round(100 * LASTF),
     "Abstract; Sections 5.2, 5.6, 5.10, 5.11 (new), Fig. 10, Table 7 (new); Section 7."),
    ("Detection terminology: describe the 94% carryover finding as precision rather than specificity.",
     "Accepted, throughout: Abstract, Section 1.4, Section 5.3, Table 5 (column renamed) and the Conclusions. In response to the same "
     "concern from Reviewer 2 (comment 4) the detector is now fully characterized (Table 4, Section 5.9, Fig. 9), and the characterization "
     "changes the reading of the result. At Z_max = 3 the precision is %s, the specificity %s, the false-positive rate %s, but the "
     "sensitivity for carryover is only %s. The index flags gross disagreement; it is not a general carryover detector, and the "
     "manuscript no longer describes it as one." % (pct(CF3["precision"]), pct(CF3["specificity"], 2), pct(CF3["fpr"], 2), pct(CF3["sensitivity"], 1)),
     "Abstract; Sections 1.4, 5.3, 5.4, 5.9; Tables 4, 5; Fig. 9; Section 7."),
    ("Algorithm: specify how weights and uncertainty are recalculated after asymmetric damping.",
     "Section 3.5.1 (new) gives the procedure. The damping factor multiplies the generalized-least-squares weight of the thermodynamic "
     "estimate (Eq. 12), the weights are renormalized (Eq. 13), and the fused value and its uncertainty are recomputed from the "
     "renormalized weights, with the covariance term and the Birge factor (Eq. 14). Steps 6 and 7 of Algorithm 1 are updated to match. "
     "Section 3.5.1 also gives the justification of the one-sided form and identifies the damping factor as the Cauchy influence weight of "
     "iteratively reweighted least squares.",
     "Section 3.5.1 (new), Eqs. (13)–(14); Algorithm 1, steps 6–7."),
    ("Uncertainty: clarify carryover scaling, bias treatment, and conversion of diagnostic intervals to standard uncertainty.",
     "Three paragraphs address these in turn. Carryover scaling (Section 3.5): the carryover fraction is a relative error of the "
     "thermodynamic estimate, so u_carry = 17.5% is applied as a relative standard uncertainty, and the allowance treats carryover as "
     "zero-mean scatter although its mean is 9.4%; the mean shift is handled by the damping rule. Bias treatment (Sections 3.3.1 and 4.2): "
     "the transfer bias is a spread across installations, drawn once per realization, and a persistent bias at one site is evaluated "
     "separately (Fig. 10c). Conversion of intervals (Section 3.3.1): u₂ = (q0.95 − q0.05)/(2 × 1.645) for approximately normal "
     "residuals, so the assumed 20% corresponds to a calibrated 90% interval of ±33%; non-normal residuals are treated with the coverage "
     "factor of the observed distribution.",
     "Sections 3.3.1, 3.5, 4.2, 5.11."),
    ("Implementation: state the minimum diagnostic signals and requirements when downstream tapping is unavailable.",
     "Section 6.2 now has a paragraph on the minimum signal set. For the orifice case: line pressure, temperature, differential pressure and "
     "indicated rate, the composition, and the high-rate differential-pressure signal; the permanent pressure loss ratio needs a downstream "
     "tapping. Without it the feature vector loses its recovery term and the declared uncertainty of the diagnostic estimator must be widened; "
     "the size of the widening can be known only from a fit. As an indication, if the actual relative uncertainty were 30%% instead of 20%% "
     "the full method would reach ±%.2f%% against ±%.2f%% for the diagnostic estimator alone (Fig. 10a). Without the high-rate "
     "differential-pressure signal the method is not supported." % (RB["s2_consistent"]["rows"][3]["full"], RB["s2_consistent"]["rows"][3]["e2"]),
     "Section 6.2 (new paragraph); Table 10."),
    ("Presentation: standardize pressure units, correct the admissibility figure reference, and moderate the “order of magnitude” statement for Table 6.",
     "Units: pressures are now kgf/cm² throughout, with the SI equivalent at first use (1 kgf/cm² = 0.0980665 MPa; 60–85 kgf/cm² is "
     "5.9–8.3 MPa). Figure reference: the falsification criterion in Section 4.4 pointed to Fig. 6 for the admissibility region; it is Fig. 8, "
     "and is corrected. Table 6: recomputed, with the actual ratios. The corrected rate is about 10 times more sensitive to gas density or "
     "differential pressure than to the liquid-loading estimate; the liquid-loading estimate has an uncertainty about 30 times larger; their "
     "product, the contribution to the combined standard uncertainty, is about 3 times larger (0.76%% against 0.20%% and 0.25%%), and the "
     "estimate accounts for %d%% of the variance at X_LM = 0.05 and %d%% at 0.10. “Order of magnitude” is removed in Sections 5.7 and 7."
     % (round(100 * PR["table6"]["0.05"]["variance_share"]["X_LM estimate"]), round(100 * PR["table6"]["0.10"]["variance_share"]["X_LM estimate"])),
     "Sections 4.4, 5.7, 7; Table 2, Table 6; Abstract."),
]

R2 = [
    ("Lack of experimental validation. The diagnostic estimator has not been trained or experimentally validated, while its uncertainty and bias are assumed. The authors should justify these assumptions and clarify the limitations of the simulation results.",
     "Experimental validation is not available to me: I am an independent researcher without a wet-gas flow loop, and the manuscript says "
     "throughout that no loop data were used. What the revision can do, and does, is to justify the assumed values, to show how far the "
     "conclusions depend on them, and to state the limits plainly. The 20% is related to the specified calibration (Section 3.3.1): it "
     "is a performance requirement, equivalent to a calibrated 90% interval of ±33%, that a fitted estimator must meet. Section 5.11 varies "
     "the assumption from 10% to 60%, the transfer bias from 0 to 20%, a persistent bias at one site from −20% to +20%, and the carryover "
     "prevalence from 0 to 60%, each with the declared uncertainty either matched or left at the assumed value. Table 10 separates what "
     "the simulations demonstrate from what is proposed, and the Limitations (Section 6.4) are extended. The conclusions that depend on the "
     "assumptions are stated as conditional: the diagnostic estimator alone is the best choice when it is better than assumed, and fusion "
     "helps when it is worse.",
     "Sections 3.3.1, 5.11 (new), 6.3, 6.4; Table 10 (new); Fig. 10."),
    ("Potential circularity of the uncertainty assessment. The same wet-gas correlation is used in the forward model and in the correction procedure. The authors should assess the impact of model-form errors and possible bias in the correlation.",
     "Accepted. Section 4.5 (new) separates the correction model (always Chisholm) from the model that generates the simulated reading, and "
     "Section 5.12 (new) evaluates three situations: matched, an independent published orifice correlation (Murdock, 1962), and "
     "systematic (±5–10%%) and random (5–10%%) departures of the over-reading, the latter as stress scenarios and not as error bounds. With the "
     "independent correlation the oracle band rises from ±%.2f%% to ±%.2f%% and the full method from ±%.2f%% to ±%.2f%% (bias %+.2f%%); the "
     "realized coverage of the declared ±2u interval falls from %s to %s, and a declared model-form allowance of about 15%% of the "
     "over-reading is needed to restore 95%%. The ranking of methods also changes with the sign of the correlation error, and the "
     "apparent advantage of the full method when the over-reading is overstated is identified as compensation of errors. The model-form term "
     "u_form is now part of the uncertainty budget (Eq. 16), and the text states that the allowance restoring coverage is specific to the "
     "correlations, geometry and conditions tested and must be calibrated for each application. The Limitations are rewritten accordingly."
     % (MATCH["oracle"]["band95"], MURD["oracle"]["band95"], MATCH["full"]["band95"], MURD["full"]["band95"], MURD["full"]["bias"],
        pct(MATCH["full"]["coverage_2u"], 1), pct(MURD["full"]["coverage_2u"], 1)),
     "Sections 3.5.2, 4.5, 5.12 (new), 6.4; Table 8; Fig. 11; Eq. (16)."),
    ("Justification of the asymmetric weighting rule. The physical and statistical justification of Eq. (12) and the choice of k=1 are insufficient. The authors should examine the sensitivity of the results to alternative weighting rules and threshold values.",
     "Section 3.5.1 gives the physical justification (a carryover fraction cannot be negative, so only an upward excess of the diagnostic "
     "estimate is evidence of carryover) and the statistical one (the damping factor is the Cauchy influence weight of iteratively "
     "reweighted least squares, applied to the excess beyond k). Section 5.10 and Table 7 compare Eq. (12) at k = 0.5, 1, 1.5, 2 and 3 with "
     "symmetric weighting, a Huber weight, a two-sided Cauchy weight, a one-sided hard switch at four thresholds, and the thermodynamic and "
     "diagnostic estimators alone, at carryover prevalences of 10%%, 25%% and 40%%. The results qualify the choice of the first version: k = 1 "
     "is not the best threshold in the reference case (±%.2f%% against ±%.2f%% at k = 0.5), the hard one-sided switch is narrower than "
     "Eq. (12) at all three prevalences (±%.2f%% against ±%.2f%% at 25%%) but poorer when carryover is absent, and the two-sided control is poorer "
     "than the one-sided rule. No rule is uniformly best. Eq. (12) is presented as a smooth, continuous baseline and not as the preferred implementation; the hard "
     "switch is described as a promising alternative that needs independent validation, especially of its switching threshold, and the "
     "choice is a calibration question for loop data."
     % (WT["One-sided Cauchy, k = 1 (Eq. 12)"]["0.25"]["band95"], WT["One-sided Cauchy, k = 0.5 (Eq. 12)"]["0.25"]["band95"],
        WT["One-sided hard switch, k = 1"]["0.25"]["band95"], WT["One-sided Cauchy, k = 1 (Eq. 12)"]["0.25"]["band95"]),
     "Sections 3.5, 3.5.1 (new), 5.10 (new), 6.4; Table 7 (new)."),
    ("Validation of the consistency index. The reported proportion of carryover cases among rejected realizations is insufficient to characterize the detector. The authors should report its sensitivity, specificity, and false-positive rate and justify the selection of Z_max.",
     "Table 4 now reports, for every threshold, the accepted fraction, the 95%% error band of the accepted realizations, sensitivity, "
     "specificity, precision and false-positive rate, and Section 5.9 (new) adds the ROC and precision–recall curves (Fig. 9, AUC %.2f), the "
     "detection rate against the size of the carryover, and a second target, a corrected-rate error above 3%%. At Z_max = 3 the "
     "specificity is %s and the false-positive rate %s, but the sensitivity is %s; at Z_max = 1 the sensitivity is %s with a false-positive "
     "rate of %s. Z_max = 3 is justified only as a completeness-priority setting that removes gross disagreement, and Section 5.4 now states "
     "what a lower threshold costs. The result is less favorable than the first version suggested, and the text is changed: the index is "
     "described as a gross-disagreement flag with high precision and low sensitivity, not as a carryover detector."
     % (DT["roc_carryover"]["auc"], pct(CF3["specificity"], 2), pct(CF3["fpr"], 2), pct(CF3["sensitivity"], 1), pct(CF1["sensitivity"], 0), pct(CF1["fpr"], 0)),
     "Sections 5.3, 5.4, 5.9 (new); Table 4; Fig. 9."),
    ("Uncertainty propagation. The procedure for propagating uncertainties through the wet-gas correction equation is not described in sufficient detail. The authors should clarify how input uncertainties, correlations, and uncertainty in the correction model are incorporated.",
     "Section 3.5.2 (new) gives the propagation: first-order, in the form u²(Q_G)/Q_G² = sᵀΣs (Eq. 15), which for the uncorrelated groups "
     "of inputs becomes Eq. (16). The estimator uncertainties and their correlation enter through u_f, which carries c = ρ₁₂u₁u₂; the meter "
     "terms are lumped (0.7%%) and itemized in Table 6; the correlation residual (0.6%%) and a model-form term u_form complete the budget. "
     "The one correlation not treated, between the liquid-loading estimate and the gas-density term, is bounded: with a correlation of ±1 "
     "the combined uncertainty at X_LM = 0.05 would lie between %.2f%% and %.2f%% instead of %.2f%% (Table 6). The realized coverage of the "
     "declared ±2u interval is %s in the reference case (Section 5.12), and the propagation of the liquid-loading term was checked against "
     "Monte Carlo propagation (verify_revision.py, check V8)."
     % (100 * PR["table6"]["0.05"]["u_c_if_X_and_density_fully_anticorrelated"], 100 * PR["table6"]["0.05"]["u_c_if_X_and_density_fully_correlated"],
        100 * PR["table6"]["0.05"]["u_c_independent"], pct(PR["coverage_2u_full"], 1)),
     "Sections 3.5, 3.5.1, 3.5.2 (new); Eqs. (13)–(16); Table 6; Section 5.12."),
    ("Applicability of the proposed method. The results are limited to an orifice meter and a specific operating envelope. The authors should clearly define the applicability limits and distinguish the demonstrated results from proposed extensions to other flowmeter types.",
     "Table 10 (new) lists, aspect by aspect, what the simulations demonstrate and what is proposed but not evaluated: meter type, "
     "pressure and temperature, fluid, flow regime, diagnostic signals, forward model and evidence. The demonstrated envelope is an orifice "
     "plate in a 154 mm line, one rich-gas composition family, 60–85 kgf/cm² (5.9–8.3 MPa), 30–60 °C, X_LM 0.006–0.152 in the annular-mist "
     "regime. Section 6.3 states that the Venturi, ultrasonic and Coriolis cases are extension pathways with no computational "
     "assessment, and the Limitations repeat the restriction.",
     "Sections 6.3, 6.4; Table 10 (new)."),
    ("Numerical consistency. The Abstract reports a 95% uncertainty band of ±4.28%, whereas Table 3 gives ±4.26% for the full method. Please clarify this discrepancy.",
     "The two figures are both correct and refer to different populations: ±4.28% is the asymmetric weighting over all 300,000 realizations, "
     "and ±4.26% is the full method over the 99.2% of realizations that the acceptance test retains. The Abstract and Section 5.2 now "
     "state both and explain that they differ by less than the sampling error of the band (0.015 percentage points), so the acceptance "
     "test does not measurably narrow the band at Z_max = 3. The phrase “95% uncertainty band” is replaced by “95% error band” "
     "(see comment 10).",
     "Abstract; Section 5.2."),
    ("Diagnostic uncertainty. Please explain how the assumed 20% relative uncertainty relates to the quantile regression and conformal calibration described in Section 3.3.1.",
     "A new paragraph in Section 3.3.1 gives the relation. The specification yields a calibrated predictive interval; for approximately normal "
     "residuals the standard uncertainty is u₂ = (q0.95 − q0.05)/(2 × 1.645), so the assumed 20% corresponds to a calibrated 90% interval of "
     "±33% of X_LM. For non-normal residuals the conformal interval is retained and u₂ is its half-width divided by the coverage factor of "
     "the observed distribution. The 20% is therefore a requirement on the fitted estimator and not a result, and Fig. 10a shows what is "
     "lost if the fitted estimator falls short of it.",
     "Section 3.3.1 (new paragraphs); Fig. 10a."),
    ("Units. Please clarify whether the pressure unit kg/cm² denotes kgf/cm² and ensure consistent use of units throughout the manuscript.",
     "Yes, it denotes kgf/cm². The unit is now written kgf/cm² everywhere (Abstract, Table 2, Table 10, text), with the SI equivalent "
     "given where it is introduced: 1 kgf/cm² = 0.0980665 MPa, so the envelope is 5.9–8.3 MPa.",
     "Abstract; Section 4.2; Table 2; Section 6.3; Table 10."),
    ("Terminology. Please use the terms uncertainty, error, bias, and accuracy consistently and distinguish modeled uncertainty from experimentally demonstrated measurement performance.",
     "Section 4.3 now defines the terms. Error is the simulated deviation from the reference (Eq. 17); bias is its mean; uncertainty is a "
     "standard uncertainty declared by the method (u), or the expanded uncertainty U = 2u; the “95% error band” is the 95th percentile of the "
     "absolute simulated error, an empirical property of the simulation and not an expanded uncertainty; accuracy is not used for simulated "
     "quantities. The text is changed accordingly (“95% uncertainty band” and “coverage band” become “95% error band”; “the accuracy decreases” "
     "becomes “the error band widens”), and the distinction between modeled uncertainty and demonstrated performance is made in the "
     "Abstract, Section 1.4, Section 6.3 (Table 10) and the Conclusions.",
     "Section 4.3; Abstract; Sections 5.4, 5.8, 6.3, 7."),
]

EXTRA = [
    "The prevalence range over which fusion beats both estimators was stated as 5–20% in Section 5.6. The finer sweep with common random numbers "
    "places the upper end at about 15–16%, and the text is corrected.",
    "Section 5.7 and the Conclusions said that the liquid-loading estimate “dominates the uncertainty budget by roughly an order of magnitude”. "
    "That overstated it: its contribution is about 3 times that of gas density or differential pressure, and 40% of the variance at X_LM = 0.05 "
    "(70% at 0.10). Table 6 is recomputed and corrected, including the relative uncertainty of the liquid-loading estimate (15.0%, from the "
    "fused uncertainty with the damping and Birge factors of Eq. 14).",
    "The column of Table 5 headed “Detector specificity” held the precision (the share of rejected realizations that contain carryover); it is renamed.",
    "The Declaration of generative AI is expanded to cover the writing of the simulation code and the additional experiments, and the checks of "
    "the revision code (verify_revision.py) are named in the Data availability statement.",
    "Tables and figures are renumbered: the new Tables are 7, 8 and 10, the former Table 7 becomes Table 9, the metric equation (13) becomes (17), "
    "and the former Fig. 9 becomes Fig. 12.",
]

# ============================================================================================ response document
d = Document()
st = d.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10.5)
st.paragraph_format.space_after = Pt(6)
for s_ in d.sections:
    s_.left_margin = s_.right_margin = Inches(1.1)
    s_.top_margin = s_.bottom_margin = Inches(1.0)


def para(text="", bold=False, italic=False, size=None, indent=None, after=None, before=None, color=None):
    p = d.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor(*color)
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    if before is not None:
        p.paragraph_format.space_before = Pt(before)
    return p


def labelled(label, text, indent=None):
    p = d.add_paragraph()
    r = p.add_run(label + " ")
    r.bold = True
    p.add_run(text)
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    return p


para("Response to Reviewers — Revision 1", bold=True, size=15, after=2)
para("Manuscript " + MS, bold=True, after=2)
para(TITLE, italic=True, after=2)
para("Leon Sandler, Independent Researcher, Northbrook, Illinois, USA", after=2)
para(DATE, after=10)
para("Dear Dr Kutin and Reviewers,")
para("Thank you for the careful reviews. Reviewer 1 recommended minor revisions and Reviewer 2 raised ten specific points about the "
     "assumptions and the statistical treatment of the simulation. Each comment is quoted below and answered, with the place in the "
     "manuscript where the change can be found. Section numbers refer to the clean manuscript, "
     "FMI_Hybrid_Liquid_Loading_Estimation_v5.docx.")
para("Two points should be stated at the outset. First, I cannot supply wet-gas loop data: this is a computational study by an "
     "independent researcher, and it remains one. The revision responds by testing the assumptions that the conclusions depend on, "
     "and by narrowing the claims where the new tests warrant it. Second, the new analyses changed some conclusions. In the reference case "
     "the diagnostic estimator alone is narrower than the full method; the consistency index has a precision of 94% but a sensitivity of "
     "3% at the adopted threshold; and the damping threshold k = 1 is not the best choice. These are reported plainly in the Abstract, "
     "Sections 5.9–5.12 and the Conclusions, and I thank the reviewers for the questions that led to them.")
para("What changed", bold=True, size=12, before=8)
for t in [
    "New Sections 3.5.1 (justification and recalculation of the damping rule) and 3.5.2 (uncertainty propagation and model-form error), "
    "Eqs. (13)–(16), and Section 4.5 (the new experiments).",
    "New Sections 5.9 (detector characterization), 5.10 (weighting rules and threshold), 5.11 (robustness to the diagnostic estimator, "
    "prevalence and site bias) and 5.12 (independent forward model); new Tables 7, 8 and 10; new Figs 9, 10 and 11.",
    "Table 4 (full detector metrics) and Table 6 (recomputed) replaced; Abstract, Sections 1.3, 1.4, 5.2–5.7, 6.2–6.4 and 7 revised; "
    "units standardized to kgf/cm²; four references added (Fawcett, 2006; Holland and Welsch, 1977; Huber and Ronchetti, 2009; JCGM 101:2008).",
    "New analysis code (fmi_revision_lib.py, fmi_revision_analysis.py), executable checks (verify_revision.py, ten checks, all passing) and "
    "the manuscript builder are added to the public repository; the original analysis code and Tables 3, 5 and 6 and Figs 2–8 are unchanged.",
]:
    p = d.add_paragraph(style="List Bullet")
    p.add_run(t)
para("Files in this submission", bold=True, size=12, before=8)
for t in ["FMI_Hybrid_Liquid_Loading_Estimation_v5.docx — the revised manuscript; v5_marked — every changed paragraph and table highlighted.",
          "FMI_Revision1_Cover_Letter.docx, FMI_Response_to_Reviewers_R1.docx (this document), FMI_Highlights.docx, FMI_Title_Page.docx.",
          "Fig1–Fig12 (TIFF): Figs 1–8 unchanged; Figs 9–11 new; Fig. 12 is the former Fig. 9."]:
    p = d.add_paragraph(style="List Bullet")
    p.add_run(t)

para("Reviewer 1", bold=True, size=13, before=12)
para("The reviewer’s comments were given as a summary and a list of six points plus one on presentation; each is answered in turn.", italic=True)
for i, (c, r_, ch) in enumerate(R1, 1):
    para("Comment 1.%d" % i, bold=True, before=6, after=2)
    labelled("Comment.", c, 0.25)
    labelled("Response.", r_, 0.25)
    labelled("Change in the manuscript.", ch, 0.25)

para("Reviewer 2", bold=True, size=13, before=12)
for i, (c, r_, ch) in enumerate(R2, 1):
    para("Comment 2.%d" % i, bold=True, before=6, after=2)
    labelled("Comment.", c, 0.25)
    labelled("Response.", r_, 0.25)
    labelled("Change in the manuscript.", ch, 0.25)

para("Corrections not requested by a reviewer", bold=True, size=13, before=12)
para("These were found while preparing the revision. None was raised in review, and each is stated here so that the reviewers and the editor "
     "can see what else changed.")
for t in EXTRA:
    p = d.add_paragraph(style="List Bullet")
    p.add_run(t)
para("Closing", bold=True, size=13, before=10)
para("The two reviews identified the weak points of the first version precisely: an assumed diagnostic estimator, a circular forward model, "
     "an unexamined weighting rule and a detector characterized by one number. All four are now tested, and the paper’s claims are "
     "narrower for it. The experimental validation that would settle the remaining questions is specified in Section 4.4. I would be "
     "glad to clarify anything further.")
para("Leon Sandler")
d.save(os.path.join(OUTD, "FMI_Response_to_Reviewers_R1.docx"))

# ============================================================================================ pasteable replies (platform text boxes)
def plain(tag, items, intro):
    out = [intro, ""]
    for i, (c, r_, ch) in enumerate(items, 1):
        out += ["%s%d. %s" % (tag, i, c.split(".")[0] if len(c) > 90 else c), "Response: " + r_, "Change: " + ch, ""]
    return "\n".join(out)


intro1 = ("Thank you for the constructive review. Each point is answered below and the changes are in the revised manuscript (v5; "
          "section numbers refer to it). The full point-by-point response is in the uploaded file FMI_Response_to_Reviewers_R1.docx.")
intro2 = ("Thank you for the detailed review, which led to substantial new analyses. I cannot supply loop data, so the revision tests the "
          "assumptions the conclusions depend on and narrows the claims where the tests warrant it; the answers are numbered as in the "
          "review. The full response is in the uploaded file FMI_Response_to_Reviewers_R1.docx.")
open(os.path.join(OUTD, "reply_reviewer1.txt"), "w", encoding="utf-8").write(plain("R1.", R1, intro1))
open(os.path.join(OUTD, "reply_reviewer2.txt"), "w", encoding="utf-8").write(plain("R2.", R2, intro2))

# ============================================================================================ cover letter
cl = Document(os.path.join(SRCD, "FMI_Cover_Letter_Sandler.docx"))
cp = cl.paragraphs
tm = dict(name=cp[0], line=cp[1], date=cp[4], to=cp[5], body=cp[9], sign=cp[20])
holders = {k: Paragraph(copy.deepcopy(v._p), cl._body) for k, v in tm.items()}
body = cl.element.body
for el in list(body):
    if not el.tag.endswith("}sectPr"):
        body.remove(el)


def cmake(kind, text, bold=None):
    tmpl = holders[kind]
    p = copy.deepcopy(tmpl._p)
    for r in list(p):
        if r.tag == qn("w:r"):
            p.remove(r)
    body.find(qn("w:sectPr")).addprevious(p)
    par = Paragraph(p, cl._body)
    src = tmpl.runs[0]._r
    r = copy.deepcopy(src)
    for t in list(r):
        if t.tag in (qn("w:t"), qn("w:br"), qn("w:tab")):
            r.remove(t)
    p.append(r)
    from docx.text.run import Run
    rr = Run(r, par)
    rr.text = text
    if bold is not None:
        rr.bold = bold
    return par


cmake("name", "Leon Sandler", True)
for t in ("Independent Researcher", "Northbrook, IL 60062, USA", "sandler.leon@gmail.com"):
    cmake("line", t)
cmake("date", DATE)
cmake("to", "Dr Joze Kutin")
cmake("to", "Senior Associate Editor, Flow Measurement and Instrumentation")
cmake("to", "Elsevier")
cmake("body", "Re: Revision of manuscript %s — “%s”" % (MS, TITLE), True)
cmake("body", "Dear Dr Kutin,")
cmake("body", "Thank you for the decision of 21 October 2026 and for the two reviews. Reviewer 1 recommended minor revisions; Reviewer 2 "
              "asked for stronger justification of the assumed diagnostic estimator, a test of the circularity of the forward model, a "
              "justification of the weighting rule, a proper characterization of the consistency index, a fuller account of the uncertainty "
              "propagation, and a clearer separation of simulated performance from demonstrated accuracy. All of the points are "
              "addressed, and a point-by-point response is provided as a separate file.")
cmake("body", "I should say at the outset what the revision can and cannot do. I cannot add experimental wet-gas data: this is a "
              "computational study by an independent researcher without a flow loop, and the revised manuscript says so more prominently, "
              "with a new table (Table 10) that separates what the simulations demonstrate from what is proposed. What the revision "
              "does is test the assumptions on which the conclusions depend, and it narrows the claims where those tests warrant it.")
cmake("body", "The principal changes are these.", True)
for t in [
    "An independent forward model (new Sections 4.5 and 5.12). The correction remains the Chisholm multiplier, but the simulated meter "
    "reading is now also generated with an independent published orifice correlation and with systematic and random departures of "
    "5–10%% of the over-reading. The error band of the full method grows from ±4.26%% to ±%.2f%%, and the realized coverage of the declared "
    "interval falls from %s to %s unless a model-form allowance of about 15%% of the over-reading is declared." % (MURD["full"]["band95"], pct(MATCH["full"]["coverage_2u"], 0), pct(MURD["full"]["coverage_2u"], 0)),
    "The diagnostic estimator and the weighting rule (new Sections 3.5.1, 5.10 and 5.11). The assumed 20%% uncertainty is related to the "
    "quantile and conformal specification and varied from 10%% to 60%%, with a persistent site bias tested separately; the damping rule is "
    "justified and compared with alternative rules and thresholds. In the reference case the diagnostic estimator alone (±3.99%%) is "
    "narrower than the full method (±4.26%%); fusion is narrower only when carryover is infrequent (below about %d%% of operating time), "
    "when the diagnostic estimator is poorer than assumed, or when it carries a persistent positive bias. The threshold k = 1 is not "
    "the best choice in the reference case, and the manuscript says so." % round(100 * LASTF),
    "The consistency index (Table 4, new Section 5.9 and Fig. 9). Sensitivity, specificity, precision, false-positive rate, ROC and "
    "precision–recall curves are reported. At the adopted threshold the index has a precision of 94%% but a sensitivity of %s for carryover, "
    "so it is described as a gross-disagreement flag and not a carryover detector; the 94%% is now called precision, as Reviewer 1 asked." % pct(CF3["sensitivity"], 0),
    "Uncertainty propagation (new Section 3.5.2, Eqs. 13–16). The damped weights and the fused uncertainty are specified; the first-order "
    "propagation, the treatment of correlations and the model-form term are written out; and Table 6 is recomputed, with the "
    "“order of magnitude” statement replaced by the ratios.",
    "Presentation. Units are standardized to kgf/cm² with the SI equivalent; the Abstract states ±4.26% and ±4.28% and what each refers to; "
    "terms are defined in Section 4.3; the minimum signal set and the case without downstream tapping are described in Section 6.2.",
]:
    p = cmake("body", t)
    p._p.get_or_add_pPr()
    ind = p._p.pPr.find(qn("w:ind"))
cmake("body", "Five corrections that no reviewer raised are listed in the response, among them a statement of the prevalence range over "
              "which fusion beats both estimators (5–20% in the first version, about 15–16% after a finer sweep) and a correction of the "
              "claim that the liquid-loading estimate dominates the uncertainty budget by an order of magnitude (about 3 times, and 40% of "
              "the variance at X_LM = 0.05).")
cmake("body", "The new analyses are deposited with the earlier code at https://github.com/sandlerleon/hybrid-liquid-loading-estimation "
              "(archived at https://doi.org/10.5281/zenodo.22760863). They include executable checks of the revision code, all of which "
              "pass; the original analysis, and Tables 3, 5 and 6 and Figs 2–8, are unchanged. A preprint of the first version is "
              "available on ChemRxiv at https://doi.org/10.26434/chemrxiv.15009070/v1.")
cmake("body", "The manuscript is original, is not under consideration elsewhere, and has not been published previously except as the "
              "preprint noted above. I am the sole author, I have no competing interests, and the work received no external funding. "
              "The use of a generative AI tool for drafting, literature synthesis, analysis design and code writing is disclosed in the "
              "manuscript.")
cmake("body", "Thank you for your consideration.")
cmake("sign", "Sincerely,")
cmake("sign", "Leon Sandler", True)
cmake("sign", "Independent Researcher, Northbrook, IL, USA")
cmake("sign", "sandler.leon@gmail.com")
cl.save(os.path.join(OUTD, "FMI_Revision1_Cover_Letter.docx"))

# ============================================================================================ highlights
hl = Document(os.path.join(SRCD, "FMI_Highlights.docx"))
BUL = ["Liquid loading is estimated as a latent variable; the correlation is unchanged",
       "Fusion beats the diagnostic estimator alone only when carryover is infrequent",
       "The consistency index has 94% precision but only 3% sensitivity for carryover",
       "Omitting the estimator covariance silently disables the acceptance test",
       "Modeled uncertainties only; an independent correlation widens the band by 1 point"]
assert all(len(b) <= 85 for b in BUL), [len(b) for b in BUL]
bl = [p for p in hl.paragraphs if p.style.name == "List Bullet"]
assert len(bl) == 5
for p, t in zip(bl, BUL):
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    p.runs[0].text = t
hl.save(os.path.join(OUTD, "FMI_Highlights.docx"))

# ============================================================================================ title page
tp = Document(os.path.join(SRCD, "FMI_Title_Page.docx"))
man = Document(os.path.join(REPO, "manuscript", "FMI_Hybrid_Liquid_Loading_Estimation_v5.docx"))
ps = [p.text for p in man.paragraphs]
i0 = next(k for k, t in enumerate(ps) if t.strip() == "1. Introduction")
i1 = next(k for k, t in enumerate(ps) if t.strip().startswith("CRediT authorship"))
words = sum(len(t.split()) for t in ps[i0:i1])
abs_words = len(ps[5].split())
nref = sum(1 for t in ps[next(k for k, t in enumerate(ps) if t.strip() == "References") + 1:] if t.strip())
import re as _re
nfig = len([1 for t in ps if _re.match(r"^Fig\. \d+\. ", t.strip())])
ntab = len([1 for t in ps if _re.match(r"^Table \d+\. ", t.strip())])
print("title page metrics: abstract %d, main text %d, figures %d, tables %d, references %d" % (abs_words, words, nfig, ntab, nref))
for p in tp.paragraphs:
    t = p.text
    new = None
    if t.startswith("Abstract: "):
        new = "Abstract: %d words (unstructured, single paragraph)" % abs_words
    elif t.startswith("Main text: "):
        new = "Main text: approximately %s words, excluding references" % format(int(round(words, -1)), ",")
    elif t.startswith("Figures: "):
        new = "Figures: %d (all original; generated by the deposited code)" % nfig
    elif t.startswith("Tables: "):
        new = "Tables: %d" % ntab
    elif t.startswith("References: "):
        new = "References: %d" % nref
    elif t.startswith("The author acknowledges the use of generative AI"):
        new = ("The author acknowledges the use of generative AI (Claude, Anthropic) as a drafting, literature-synthesis, analysis-design and "
               "code-writing aid during the preparation of this manuscript, as set out in the Declaration of generative AI in the writing "
               "process. All modelling, analysis and conclusions are the author’s own, and the author takes full responsibility for the "
               "content of this publication. No other assistance was received.")
    if new:
        for r in p.runs[1:]:
            r._r.getparent().remove(r._r)
        p.runs[0].text = new
tp.save(os.path.join(OUTD, "FMI_Title_Page.docx"))
print("saved to", OUTD)
