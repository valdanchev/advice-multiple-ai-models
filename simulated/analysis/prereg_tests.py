"""Step 12. Preregistered tests (OSF nrmke, 17 Oct 2025), the added Study 2 comparison, condition balance and a
participant-cluster bootstrap of matched adoption. Input: the anonymised replication data.
Usage: python3 -I prereg_tests.py <path to replication_package/data>
Preregistration labels -> manuscript labels: C2 -> C1, T2 -> T1, T4 -> T2. Manuscript C2 (one model with reasoning) was
added after the preregistration."""
import sys, numpy as np, pandas as pd
from scipy.stats import mannwhitneyu, kruskal, chi2_contingency
D = sys.argv[1] if len(sys.argv) > 1 else "data"
t = pd.read_csv(f"{D}/trials.csv", dtype=str, keep_default_na=False)
p = pd.read_csv(f"{D}/participants.csv", dtype=str, keep_default_na=False)
t["init_c"] = (t.initial_answer == t.key).astype(int); t["final_c"] = (t.final_answer == t.key).astype(int)
def wrong_shown(r):
    w = [r.single_model_answer] if r.n_models_shown == "1" else [r.ans_gpt4o, r.ans_claude, r.ans_llama]
    return [a for a in w if a != r.key and a != "X"]
rows = [(r.participant, r.condition, i, int(r.final_answer == a and r.kept_initial_button == "0"))
        for i, r in enumerate(t.itertuples()) for a in wrong_shown(r)]
o = pd.DataFrame(rows, columns=["p", "c", "trial", "s"])
M = {"overreliance (each wrong answer shown counts once; preregistered)": o.groupby(["c", "p"]).s.mean(),
     "overreliance (each question weighted equally; sensitivity)": o.groupby(["c", "p", "trial"]).s.mean().groupby(["c", "p"]).mean(),
     "final accuracy (preregistered)": t.groupby(["condition", "participant"]).final_c.mean(),
     "net gain in accuracy (additional)": (t.final_c - t.init_c).groupby([t.condition, t.participant]).mean()}
def ci(x): return f"{x.mean():.3f} ({x.mean() - 1.96 * x.sem():.3f} to {x.mean() + 1.96 * x.sem():.3f}), n = {len(x)}"
tests = [("H1, preregistered (prereg C2 vs T2)", "C1", "T1"), ("H2, preregistered (prereg T2 vs T4)", "T1", "T2"),
         ("Study 2, added comparison (not preregistered)", "C2", "T2"), ("One model, reasoning vs none (not randomised)", "C1", "C2")]
print("PARTICIPANT-LEVEL MEANS (95% CI = mean +/- 1.96 SE) AND TWO-SIDED MANN-WHITNEY TESTS")
for name, s in M.items():
    print(f"\n{name}"); [print(f"  {c}: {ci(s[c])}") for c in ["C1", "T1", "T2", "C2"]]
    for lab, a, b in tests: print(f"  {lab}: {a} vs {b}, P = {mannwhitneyu(s[a], s[b]).pvalue:.2g}")
print("\nBALANCE ACROSS CONDITIONS")
ia = t.groupby(["condition", "participant"]).init_c.mean().reset_index()
print("  initial accuracy:", ia.groupby("condition").init_c.mean().round(3).to_dict(), f"Kruskal-Wallis P = {kruskal(*[g.init_c for _, g in ia.groupby('condition')]).pvalue:.2f}")
p["C2"] = p.condition == "C2"
for v in ["age_band", "gender", "education", "used_ai_chatbots_before", "confidence_initial_answers"]:
    print(f"  {v}: chi-square across 4 conditions P = {chi2_contingency(pd.crosstab(p[v], p.condition))[1]:.3f}; C2 vs the other three P = {chi2_contingency(pd.crosstab(p[v], p.C2))[1]:.3f}")
print("  'Very unconfident' share: C2 %.2f vs others %.2f (rated after the task)" % ((p[p.C2].confidence_initial_answers == "Very unconfident").mean(), (p[~p.C2].confidence_initial_answers == "Very unconfident").mean()))
print("\nMATCHED ADOPTION OF THE SAME WRONG ANSWER: RAW DIFFERENCE WITH PARTICIPANT-CLUSTER BOOTSTRAP (rows from one decision stay together)")
R = []
for c in ["ans_gpt4o", "ans_claude", "ans_llama"]:
    a = t[c]; on = (t.n_models_shown == "3") | (a == t.single_model_answer)
    k = (a != t.key) & (a != "X") & (t.initial_answer != a) & on
    R.append(pd.DataFrame({"p": t.participant[k], "n": t.n_models_shown[k], "y": (t.final_answer[k] == a[k]).astype(int)}))
g = pd.concat(R).groupby(["p", "n"]).y.agg(["sum", "count"]).reset_index(); G = {n: g[g.n == n] for n in ["1", "3"]}
rate = lambda s: s["sum"].sum() / s["count"].sum(); rng = np.random.default_rng(1)
B = [rate(G["3"].sample(frac=1, replace=True, random_state=rng.integers(1e9))) - rate(G["1"].sample(frac=1, replace=True, random_state=rng.integers(1e9))) for _ in range(2000)]
print(f"  alone {rate(G['1']):.3f}, with others {rate(G['3']):.3f}; difference {rate(G['3']) - rate(G['1']):.3f} (95% CI {np.percentile(B, 2.5):.3f} to {np.percentile(B, 97.5):.3f}); 2,000 resamples")
