"""Error correlation: how correlated the three models' errors are on the full MMLU-Pro question bank
of the four subjects (the 32 stimuli were selected to make correctness uncorrelated, so they cannot show this).
(1) co-failure: how often two models are wrong on the same question, against independence; phi correlation of correctness.
(2) shared wrong answers: how often two models that are both wrong choose the same wrong option, against chance (gives rho).
Run from the package root: python3 -I analysis/error_correlation.py"""
import itertools
import numpy as np
src = open("analysis/derive.py").read().split("ch = chance / both")[0]
exec(src)  # loads the published model outputs, the four subject strata, and counts both-wrong pairs
allq = [q for v in strata.values() for q in v]
print(f"questions in the four subjects: {len(allq)} ({', '.join(f'{SUB[s]} {len(v)}' for s, v in strata.items())})")
ch = chance / both
print(f"(2) both-wrong pairs: {both}; same wrong option: {same} ({same / both:.1%}); chance {ch:.1%}; rho = {((same / both) - ch) / (1 - ch):.3f}")
C = {m: np.array([recs[m][q]["pred"] == recs[m][q]["answer"] for q in allq], float) for m in M}
print("(1) co-failure by pair of models:")
for a, b in itertools.combinations(M, 2):
    wa, wb = 1 - C[a].mean(), 1 - C[b].mean(); bw = ((1 - C[a]) * (1 - C[b])).mean()
    print(f"  {MODEL_NAME[a]} / {MODEL_NAME[b]}: wrong {wa:.3f} and {wb:.3f}; both wrong {bw:.3f} vs {wa * wb:.3f} if independent "
          f"(ratio {bw / (wa * wb):.2f}); phi {np.corrcoef(C[a], C[b])[0, 1]:.2f}")
print("Answer keys are used as published (not corrected for key errors).")
