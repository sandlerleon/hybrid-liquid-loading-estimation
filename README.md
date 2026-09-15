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
| The estimator consistency index is a **specific** detector of that failure mode: carryover occurs in 25% of realisations but 94% of those rejected | `fmi_analysis.py` |
| Hybrid fusion is worthwhile only where upstream separation is effective but imperfect (≈5–20% carryover prevalence) | `fmi_analysis.py`, design sweep |
| The corrected rate is an order of magnitude *less* sensitive to liquid loading than to gas density or ΔP, yet liquid loading dominates the budget because its uncertainty is ~30× larger | `fmi_analysis.py`, sensitivity |
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
            build_fmi_v2.py               builds the manuscript from the JSON results
            *.json                        generated summaries the manuscript reads from
manuscript/ the manuscript and cover letter (CC BY 4.0)
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
python code/build_fmi_v2.py          # rebuilds the manuscript from those results
```

Seeds are fixed (`20260914`, `20260915`, `20260916`), so the numbers reproduce exactly.
The manuscript builder reads its figures from the JSON summaries rather than from
transcribed values, so the text and the computation cannot drift apart.

Default configuration: 300,000 realisations per configuration, 4,000 per envelope grid
cell, operating envelope 60–85 kg/cm² and 30–60 °C, condensate–gas ratio 5–100
bbl/MMscf. Every distribution is tabulated in the paper's Section 4.2 and set at the
top of `fmi_analysis.py`.

## Citation

- Paper (preprint) — concept: [10.5281/zenodo.22760861](https://doi.org/10.5281/zenodo.22760861)
  · this version: [10.5281/zenodo.22760862](https://doi.org/10.5281/zenodo.22760862)
- Code — concept: [10.5281/zenodo.22760863](https://doi.org/10.5281/zenodo.22760863)
  · this version: [10.5281/zenodo.22760864](https://doi.org/10.5281/zenodo.22760864)

The manuscript cites the concept DOIs, which always resolve to the latest version.

## License

- Manuscript text and figures: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — see `manuscript/LICENSE`
- Code: MIT — see `LICENSE` at repository root
