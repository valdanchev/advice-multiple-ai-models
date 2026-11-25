# Full pipeline on simulated data

**"Advice from multiple AI models reduces overreliance only when their errors diverge"** (Studies 1–2)

This package runs every analysis in the paper end to end on a **simulated dataset**. It contains no individual-level
data from the study's participants. Aggregate study data are in `../aggregate_data/`.
Use it to check that the code runs and to see what each step produces. The numbers from the simulated data are
**not** the paper's results and are **not** independent evidence for them (see *How the data are simulated*).

Under the consent participants gave (participant information sheet approved by the Queen Mary Ethics of Research
Committee, DSREC107), individual-level data cannot be shared publicly but may be shared with qualified researchers.
See the top-level README for access.

## Contents

| Folder or file | What it holds |
|---|---|
| `simulate/simulate_data.py` | Generates the simulated dataset. Its parameters are listed at the top of the script. |
| `data_simulated/` | Output of the simulator: `trials_raw.csv` and `participants.csv`, the format read by `derive.py`, plus `replication_format/trials.csv` and `replication_format/participants.csv`, the format read by `prereg_tests.py` and `e2_trial_cluster.R` |
| `materials/design_items.csv` | The design: the 32 questions with key, subject, number of options, the answer each model gave, the answer shown in the one-model conditions and its label, and question order |
| `materials/hits.json` | The 32 MMLU-Pro questions and options (public; Wang et al. 2024) |
| `materials/advice_final.json` | The answers each model gave, as shown to participants |
| `materials/mmlu_pro_model_outputs_4subjects.csv` | Public MMLU-Pro outputs of GPT-4o, Claude 3.5 Sonnet and Llama 3.1 70B on the 1,126 questions in the four subjects (TIGER-Lab release). Used for model accuracies, error correlation and ρ, so these parts reproduce the paper's values exactly. |
| `analysis/` | The analysis scripts |
| `intermediate/` | Derived files written by the scripts (`d.csv`, `dm.csv`, `.rds`) |
| `outputs/` | Console outputs, `params.json`, `bench_policy.json` and Figs 1–5 (`outputs/figs/`) |
| `run_all.sh` | Runs everything in order |

## How the data are simulated

The simulated design matches the study:

- **Conditions:** 110, 111, 110 and 110 participants in conditions C1, T1, T2 and C2.
- **Questions:** each participant answers the same 32 questions.
- **Advice:** each condition shows the same answers as the study.

For each simulated participant and question:

1. **Initial answer.** It is correct with a probability set by the subject's base rate, the participant's ability and the question's difficulty (random effects on the logit scale). A wrong initial answer is chosen at random among the wrong options.
2. **Final answer.** It is chosen by a softmax among the initial answer and the advised answers:
   - An advised answer is more attractive the more models give it.
   - It is also more attractive with a participant-specific tendency to defer, and when reasoning is shown.
   - A correct initial answer has extra pull, standing in for private knowledge.
   - A small share of choices switch to an unadvised answer.
3. **Demographics, confidence ratings and session durations.** These are drawn from hand-set distributions.

No individual records were used, but the parameters were **set by hand to roughly match the summary rates reported
in the paper** (for example, how often a lone wrong answer is adopted). Agreement between the simulated results and
the paper's therefore reflects this calibration, not a test of the findings. Change the seed with
`bash run_all.sh <seed>`.

## Run order

Run `bash run_all.sh` from this folder; it runs every step below in order.

| Step | Script | Does | Writes to `outputs/` |
|---|---|---|---|
| 1 | `simulate/simulate_data.py` | Simulated trials and participants | `simulate_log.txt` |
| 2 | `analysis/derive.py` | Derived variables; ρ and model accuracies from the public MMLU-Pro outputs; Bayesian benchmark | `derive_log.txt`, `params.json` |
| 3 | `analysis/models.R` | Logistic mixed models: final accuracy, harmful and beneficial switches, matched adoption, adoption by what the other models said, reasoning, model identity | `models_out.txt` |
| 4 | `analysis/robust.R` | Robustness checks, time per decision, moderators | `robust_out.txt` |
| 5 | `analysis/m9.R` | Moderator models | `m9_out.txt` |
| 6 | `analysis/baserates.R` | Results reweighted to the models' natural agreement patterns | `baserates_out.txt` |
| 7 | `analysis/additional_analyses.R` | Net gain in accuracy, decision-level overreliance, demographic moderators, stimulus correlations, private knowledge and confidence | `additional_analyses_out.txt` |
| 8 | `analysis/benchmark_confidence.py` | Benchmark with confidence-specific priors | `benchmark_confidence_out.txt` |
| 9 | `analysis/error_correlation.py` | Error correlation on the full question bank: co-failure by model pair, shared wrong answers and ρ | `error_correlation_out.txt` |
| 10 | `analysis/bench_policy.py` | Benchmark summaries and the deployment simulation (ρ = 0.35, 0, 0.5) | `bench_policy.json` |
| 11 | `analysis/figures.py`, `analysis/fig1.py` | Figs 1–5 | `figs/*.png` |
| 12 | `analysis/prereg_tests.py` | Preregistered tests: H1 (C1 vs T1) and H2 (T1 vs T2) on overreliance and final accuracy. Also the added Study 2 comparison (C2 vs T2), net gain, an equal-weight sensitivity check, condition balance and a participant-cluster bootstrap of matched adoption | `prereg_tests_out.txt` |
| 13 | `analysis/e2_trial_cluster.R` | Matched adoption model with a random intercept for each decision | `e2_trial_cluster_out.txt` |
| 14 | `analysis/fit_diagnostics.R` | Singularity and convergence of every mixed model | `fit_diagnostics_out.txt` |
| 15 | `analysis/si_tables.R` | Full fixed- and random-effects tables (SI Appendix, S5) | `si_tables_out.txt`, `si_tables.json` |
| 16 | `analysis/si_logodds.R` | Condition effects as odds ratios (SI Appendix, S5) | `si_logodds_out.txt` |

The study preregistration is at https://osf.io/nrmke. Its condition labels map to the paper's as follows: prereg C2 is C1, T2 is T1, and T4 is T2. The paper's C2 (one model with reasoning) was added after the preregistration.

## Running on the study data

The analysis scripts read the two files in `data_simulated/` and the two in `data_simulated/replication_format/`. To reproduce the paper's numbers:

1. Replace these four files with the anonymised study data, in the same formats and with the same column names. See the paper's data availability statement for how to obtain them.
2. Skip step 1 of `run_all.sh`, the simulation.

## Requirements

- **Python 3.10+** with pandas, numpy, scipy and matplotlib.
- **R 4.3+** with lme4 (1.1-35), emmeans (1.10) and jsonlite.
- **Run time:** a full run takes about 10–30 minutes, mostly for the mixed models.
