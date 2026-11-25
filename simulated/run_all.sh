#!/usr/bin/env bash
# Runs the full analysis on simulated data. Run from this folder: bash run_all.sh [seed]
set -euo pipefail
SEED="${1:-20251017}"
mkdir -p data_simulated/replication_format intermediate outputs/figs
python3 -I simulate/simulate_data.py "$SEED"                         > outputs/simulate_log.txt
python3 -I analysis/derive.py                                       > outputs/derive_log.txt
Rscript analysis/models.R                                           > outputs/models_out.txt 2>&1
Rscript analysis/robust.R                                           > outputs/robust_console.txt 2>&1
Rscript analysis/m9.R                                               > outputs/m9_console.txt 2>&1
Rscript analysis/baserates.R                                        > outputs/baserates_out.txt 2>&1
Rscript analysis/additional_analyses.R                              > outputs/additional_analyses_out.txt 2>&1
python3 -I analysis/benchmark_confidence.py                         > outputs/benchmark_confidence_out.txt
python3 -I analysis/error_correlation.py                            > outputs/error_correlation_out.txt
python3 -I analysis/bench_policy.py                                 > outputs/bench_policy_log.txt
python3 -I analysis/figures.py                                      > outputs/figures_log.txt
python3 -I analysis/fig1.py                                         > outputs/fig1_log.txt
python3 -I analysis/prereg_tests.py data_simulated/replication_format > outputs/prereg_tests_out.txt
Rscript analysis/e2_trial_cluster.R data_simulated/replication_format > outputs/e2_trial_cluster_out.txt 2>&1
Rscript analysis/fit_diagnostics.R                                  > outputs/fit_diagnostics_out.txt 2>&1
Rscript analysis/si_tables.R                                       > outputs/si_tables_out.txt 2>&1
Rscript analysis/si_logodds.R                                      > outputs/si_logodds_out.txt 2>&1
echo "done: outputs/ (seed $SEED)"
