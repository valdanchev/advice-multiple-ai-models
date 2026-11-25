# Analysis code as run on the study data: "Advice from multiple AI models reduces overreliance only when their errors diverge"

Code for the analyses of Studies 1–2 (N = 441) reported in the manuscript. All scripts run from the folder that contains `stimuli/` and `analysis/`.

## Inputs not included
- `in_raw/a.csv`, `in_raw/b.csv`: Qualtrics exports (conditions C1/T1/T2 and C2). Under the consent participants gave,
  individual-level data cannot be shared publicly, so these files are not included. Anonymised copies (Prolific and
  Qualtrics identifiers, IP addresses and locations removed; participant codes P001–P441) are available to qualified
  researchers on request (see the top-level README). Steps 0–2 need them; every later step can be checked from the
  files in `outputs_study_data/`.
- `in_survey/raw_clean.txt`: text print-out of the survey, used once to recover the advice participants saw (the survey print-outs are in `../materials/survey/`).
- `src/MMLU-Pro/eval_results/`: model outputs released by TIGER-Lab (https://github.com/TIGER-AI-Lab/MMLU-Pro),
  files `model_outputs_gpt-4o-2024-08-06_5shots.zip`, `model_outputs_claude-3-5-sonnet-20241022_5shots.json.zip`,
  `model_outputs_Meta-Llama-3_1-70B_5shots.zip`.

Included stimuli: `stimuli/hits.json` (the 32 MMLU-Pro questions) and `stimuli/advice_final.json` (the answer each model
showed, after manual checks against the survey print-out).

## Run order
| Step | Script | Does | Writes |
|---|---|---|---|
| 0 | `stimuli/parse_advice.py` | parses the advice shown from the survey print-out (manually checked into `advice_final.json`) | `stimuli/advice.json` |
| 1 | `analysis/build_trials.py` | trial-level and participant-level data from the two Qualtrics exports | `trials_raw.csv`, `participants.csv` |
| 2 | `analysis/derive.py` | derived variables; ρ and model accuracies from the full MMLU-Pro outputs; Bayesian benchmark | `d.csv`, `dm.csv`, `params.json` |
| 3 | `analysis/models.R` | confirmatory and exploratory GLMMs (M1–M7) | `models_out.txt`, `results_main.rds` |
| 4 | `analysis/robust.R` | robustness checks, decision time (M8), moderators (M9) | `robust_out.txt`, `results_robust.rds` |
| 5 | `analysis/m9.R` | re-run of the M9 moderator models | `m9_out.txt` |
| 6 | `analysis/baserates.R` | results reweighted to the models' natural agreement patterns | `baserates_out.txt` |
| 7 | `analysis/bench_policy.py` | benchmark summaries and the deployment-policy simulation (ρ = 0.35, 0, 0.5) | `bench_policy.json` |
| 8 | `analysis/figures.py`, `analysis/fig1.py` | Figs 1–5 | `analysis/figs/*.png` |
| 9 | `analysis/additional_analyses.R` | additional analyses: net gain in accuracy, decision-level overreliance, demographic moderators, stimulus correlations, private knowledge and confidence | `additional_analyses_out.txt` |
| 10 | `analysis/benchmark_confidence.py` | benchmark with a confidence-informed prior | `benchmark_confidence_out.txt` |
| 11 | `analysis/error_correlation.py` | error correlation on the full question bank: co-failure by model pair, shared wrong answers and ρ | `error_correlation_out.txt` |
| 12 | `analysis/prereg_tests.py` | preregistered tests (H1: C1 vs T1; H2: T1 vs T2) and the added Study 2 comparison (C2 vs T2) on overreliance and final accuracy; net gain; equal-weight sensitivity; condition balance; participant-cluster bootstrap of matched adoption. Runs on the anonymised replication data | `prereg_tests_out.txt` |
| 13 | `analysis/e2_trial_cluster.R` | matched adoption model with a random intercept for each decision | `e2_trial_cluster_out.txt` |
| 14 | `analysis/fit_diagnostics.R` | singularity and convergence of every reported GLMM | `fit_diagnostics_out.txt` |
| 15 | `analysis/si_tables.R` | full fixed- and random-effects tables of the mixed models (SI Appendix, S5) | `si_tables_out.txt`, `si_tables.json` |
| 16 | `analysis/si_logodds.R` | condition effects as odds ratios, alongside the probability differences (SI Appendix, S5) | `si_logodds_out.txt` |

Preregistration (https://osf.io/nrmke) labels map to the manuscript as prereg C2 → C1, T2 → T1, T4 → T2; the
manuscript's C2 (one model with reasoning) was added after the preregistration.

Example: `python3 -I analysis/derive.py`, `Rscript analysis/models.R > analysis/models_out.txt`,
`python3 -I analysis/prereg_tests.py <replication_package/data>`.

## Software
R 4.3.3 with lme4 1.1-35.1 (optimizer bobyqa), emmeans 1.10.0, sandwich 3.1-0, lmtest 0.9-40, jsonlite.
Python 3 with pandas 2.x, numpy, scipy, matplotlib.

## Outputs included
`outputs_study_data/` holds the console output of each step, `params.json` (ρ, model accuracies, priors),
`bench_policy.json` (simulation results) and the figures, so results can be checked without the raw data.
These outputs come from the study data. To run the same scripts end to end without the study data, use
`../simulated/`.
