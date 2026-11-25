"""Benchmark with confidence-specific priors: does a benchmark that uses participants' self-rated confidence
still follow two agreeing models? q is set to the observed initial accuracy for the participant's subject and
confidence level, instead of the subject mean. Run from the package root: python3 -I analysis/benchmark_confidence.py"""
src = open("analysis/derive.py").read().split("for tag, rho, qs in")[0]
exec(src)
import pandas as pd
d = d.merge(P[["pid", "conf_initial"]], on="pid", how="left")
QC = d.groupby(["subject", "conf_initial"]).init_correct.mean().to_dict()
def bench_conf(r):
    global Q
    keep = Q[r.subject]; Q[r.subject] = QC[(r.subject, r.conf_initial)]
    try: return bench(r, RHO)[1]
    finally: Q[r.subject] = keep
k3 = d[(d.n_llm == 3) & (d.config == "1C2W-agree")].copy()
wrong_agreed = k3.apply(lambda r: [a for a in (r.adv_ChatGPT, r.adv_Claude, r.adv_Llama) if a != r.key][0], axis=1)
k3 = k3[k3.init != wrong_agreed]
k3["opt_final_conf"] = k3.apply(bench_conf, axis=1)
adopt_conf = (k3.opt_final_conf == wrong_agreed[k3.index]).mean()
print(f"Trials with two models agreeing on a wrong answer and a correct third model (initial answer not the shared error): {len(k3)}")
print(f"Benchmark adopting the shared wrong answer, q from subject x confidence level: {adopt_conf:.3f}")
print("q by confidence level (pooled over subjects):"); print(d.groupby("conf_initial").init_correct.mean().round(3).to_string())
print("max q used:", round(max(QC.values()), 3))
