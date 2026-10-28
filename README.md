# Hybrid Physics–Diagnostic Estimation of Liquid Loading for Wet-Gas Flowmeter Correction

Leon Sandler, Independent Researcher — sandler.leon@gmail.com

Reproducibility package for *"Hybrid Physics–Diagnostic Estimation of Liquid Loading
for Wet-Gas Flowmeter Correction: A Model-Based Uncertainty Framework,"* prepared for
submission to Elsevier's **Flow Measurement and Instrumentation**.

## The problem

Every established wet-gas correction — Murdock, Chisholm, de Leeuw, ISO/TR 11583 —
writes the indicated gas rate as the true rate times an over-reading factor that
depends on the Lockhart–Martinelli parameter:

```
Q_ind = Q_G · φ(X_LM, ρ_G/ρ_L, Fr_G)
X_LM  = (ṁ_L/ṁ_G)·√(ρ_G/ρ_L)
```

One measurement, two unknowns. The correlation is mature; its **input** is what a
production metering station does not have.

This work estimates `X_LM` as a latent variable from information already present at
the station, and leaves the correlation untouched.

## What is and is not claimed

**This is a computational study.** No wet-gas loop data were used. The diagnostic
estimator is specified in enough detail to be fitted and reproduced, but it is **not
fitted here**. Every performance figure is a *modelled uncertainty* conditional on the
assumptions tabulated in the paper, not a measured accuracy.

The central hypothesis is falsifiable, and the experiment that would refute it — test
matrix, comparisons and criteria — is specified in the paper's Methods rather than
deferred to the discussion.

## Results the code reproduces

| Finding | Where |
|---|---|
| Inverse-variance fusion is **worse** than the diagnostic estimator alone unless the thermodynamic estimator declares an allowance for the upstream carryover it cannot observe | `fmi_analysis.py`, ablation |
| In the reference case the diagnostic estimator alone (±3.99%) is **narrower** than every fused configuration, including the full method (±4.26%); fusion beats it only when carryover occupies less than about 16% of operating time, when the diagnostic estimator is poorer than assumed, or when it carries a persistent positive bias | `fmi_analysis.py`; `fmi_revision_analysis.py`, E2 |
| The consistency index has 94% **precision** for carryover at Z_max = 3 but about 3% **sensitivity** (AUC 0.81): it flags gross disagreement and is not a general carryover detector | `fmi_revision_analysis.py`, E4 |
| The damping threshold k = 1 is not the best choice in the reference case; a one-sided hard switch is narrower than Eq. (12) except at zero carryover; no rule is uniformly best | `fmi_revision_analysis.py`, E3 |
| An independent orifice correlation (Murdock, 1962) as the truth widens the full method's band from ±4.26% to ±5.26% and lowers the realized coverage of the declared ±2u interval from 94% to 89% | `fmi_revision_analysis.py`, E1 |
| The corrected rate is about 10 times *less* sensitive to liquid loading than to gas density or ΔP, yet the liquid-loading estimate is the largest single contribution to the combined uncertainty (40% of the variance at X_LM = 0.05, 70% at 0.10) because its uncertainty is ~30 times larger | `fmi_revision_analysis.py`, E5 |
| Treating the two structurally distinct estimates as independent does not degrade the acceptance test gracefully — it **progressively disables** it | `covariance_analysis.py` |

## Contents

```
code/       swcl_physics.py               real-gas density (Standing + Dranchuk–Abou-Kassem),
                                          Chisholm / de Leeuw / USM / Coriolis over-reading
            fmi_analysis.py               main Monte Carlo: estimator error model, ablation,
                                          threshold sweep, sensitivity, admissibility envelope,
                                          carryover design space
            covariance_analysis.py        correlated-estimator study: GLS fusion and the
                                          covariance-aware consistency index
            generate_method_figure.py     Fig. 1
            generate_deployment_figure.py Fig. 9
            build_fmi_v2.py               builds the submitted (first-version) manuscript from the JSON results
            fmi_revision_lib.py           revision 1: common-random-number machinery, separate truth and
                                          correction models, selectable fusion rule
            fmi_revision_analysis.py      revision 1: model-form discrepancy, fusion robustness, weighting
                                          rules, detector characterization, declared-uncertainty coverage
            verify_revision.py            ten executable checks of the revision code
            add_revision_v5.py            builds manuscript v5 from v4 and the revision results
            make_marked_v5.py             change-marked copy
            build_fmi_revision_letters.py cover letter, point-by-point response, Highlights, Title Page
            *.json                        generated summaries the manuscript reads from
manuscript/ the manuscript (v4 submitted, v5 revised) and cover letter (CC BY 4.0)
revision1/  the revision package: response to reviewers, cover letter, replies as entered on the review platform
figures/    all figures at 300 dpi
```

## Reproducing

```bash
pip install -r code/requirements.txt
python code/swcl_physics.py          # imported by the others; no output of its own
python code/fmi_analysis.py          # ~2 min; writes fmi_results.json and figures A–F
python code/covariance_analysis.py   # writes covariance_results.json and figure H
python code/generate_method_figure.py
python code/generate_deployment_figure.py
python code/build_fmi_v2.py          # rebuilds the first-version manuscript from those results
```

Revision 1 (all of the above is unchanged; these add to it):

```bash
python code/fmi_revision_analysis.py   # ~1 min; writes fmi_revision_results.json and figures I, J, K
python code/verify_revision.py         # ten checks; writes fmi_revision_verification.json
python code/add_revision_v5.py         # builds manuscript v5; refuses to run if a check failed
```

The revision experiments use one sampled world of 300,000 realizations (seed `20261027`) that every
configuration shares (common random numbers), so differences between methods are not sampling noise.
With the baseline settings this machinery reproduces the submitted ablation (Table 3) to within
0.03 percentage points.

Seeds are fixed (`20260914`, `20260915`, `20260916`), so the numbers reproduce exactly.
The manuscript builder reads its figures from the JSON summaries rather than from
transcribed values, so the text and the computation cannot drift apart.

Default configuration: 300,000 realisations per configuration, 4,000 per envelope grid
cell, operating envelope 60–85 kg/cm² and 30–60 °C, condensate–gas ratio 5–100
bbl/MMscf. Every distribution is tabulated in the paper's Section 4.2 and set at the
top of `fmi_analysis.py`.

## Citation

- Paper (preprint) — concept: [10.5281/zenodo.22760861](https://doi.org/10.5281/zenodo.22760861)
  · current version (v4): [10.5281/zenodo.22760981](https://doi.org/10.5281/zenodo.22760981)
- Code — concept: [10.5281/zenodo.22760863](https://doi.org/10.5281/zenodo.22760863)
  · this version: [10.5281/zenodo.22760864](https://doi.org/10.5281/zenodo.22760864)

The manuscript cites the concept DOIs, which always resolve to the latest version.

## License

- Manuscript text and figures: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — see `manuscript/LICENSE`
- Code: MIT — see `LICENSE` at repository root
