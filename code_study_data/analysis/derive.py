"""Derived variables (re-analysis plan, Section 1) and the Bayesian benchmark (Section 3).
Outputs: analysis/d.csv (trial level), analysis/dm.csv (trial x wrong model), analysis/params.json"""
import json, zipfile, itertools, collections
import numpy as np, pandas as pd
d = pd.read_csv("analysis/trials_raw.csv", keep_default_na=False).replace("", np.nan)
d["item"] = d["item"].astype(str)
P = pd.read_csv("analysis/participants.csv")
H = {str(r["question_id"]): r for r in json.load(open("stimuli/hits.json"))}
M = ("ChatGPT", "Claude", "Llama"); MODEL_NAME = {"ChatGPT": "GPT-4o", "Claude": "Claude 3.5 Sonnet", "Llama": "Llama 3.1 70B"}
AMBIG = {"8574", "6064", "6274", "5312", "5678"}
d = d[d.final.notna()].copy()                      # 6 trials with no final answer (item 638)
d["advised"] = d.apply(lambda r: [r.single_adv] if r.n_llm == 1 else [r["adv_" + m] for m in M], axis=1)
d["wrong_adv"] = d.apply(lambda r: {a for a in r.advised if a != r.key and a != "X"}, axis=1)
d["harm"] = np.where(d.init_correct == 1, 1 - d.final_correct, np.nan)
d["benefit"] = np.where(d.init_correct == 0, d.final_correct, np.nan)
d["opp_wrong"] = d.apply(lambda r: int(any(a != r.init for a in r.wrong_adv)), axis=1)
d["follow_wrong"] = d.apply(lambda r: int(r.final in r.wrong_adv and r.final != r.init), axis=1)
d["ambiguous_key"] = d["item"].isin(AMBIG).astype(int)
# ---- Bayesian benchmark parameters from the full MMLU-Pro outputs (TIGER-Lab release) ----------------------
recs = {}
for tag, f in (("ChatGPT", "model_outputs_gpt-4o-2024-08-06_5shots.zip"), ("Claude", "model_outputs_claude-3-5-sonnet-20241022_5shots.json.zip"), ("Llama", "model_outputs_Meta-Llama-3_1-70B_5shots.zip")):
    z = zipfile.ZipFile("src/MMLU-Pro/eval_results/" + f); recs[tag] = {str(r["question_id"]): r for r in json.loads(z.read(z.namelist()[0]))}
def stratum(r): return r["src"] if r["src"] in ("ori_mmlu-global_facts", "ori_mmlu-college_mathematics", "ori_mmlu-nutrition") else ("business" if r["category"] == "business" else None)
base = recs["ChatGPT"]
strata = collections.defaultdict(list)
for q, r in base.items():
    s = stratum(r)
    if s and all(q in recs[m] for m in M): strata[s].append(q)
SUB = {"ori_mmlu-global_facts": "global_facts", "ori_mmlu-college_mathematics": "college_mathematics", "ori_mmlu-nutrition": "health_nutrition", "business": "business"}
params = {"p": {}, "n_items": {}, "rho_pairs": {}, "config_freq": {}}
same = both = chance = 0
cfg_count = collections.defaultdict(collections.Counter)
for s, qs in strata.items():
    sub = SUB[s]; params["n_items"][sub] = len(qs)
    params["p"][sub] = {m: float(np.mean([recs[m][q]["pred"] == recs[m][q]["answer"] for q in qs])) for m in M}
    for q in qs:
        k = base[q]["answer"]; preds = [recs[m][q]["pred"] for m in M]; nopt = len(base[q]["options"])
        for a, b in itertools.combinations(preds, 2):
            if a != k and b != k and a and b:
                both += 1; same += a == b; chance += 1 / (nopt - 1)
        w = [x for x in preds if x != k]
        c = "3C" if not w else "2C1W" if len(w) == 1 else ("1C2W-agree" if w[0] == w[1] else "1C2W-split") if len(w) == 2 else ("0C3W-agree" if len(set(w)) == 1 else "0C3W-split" if len(set(w)) == 3 else "0C3W-2+1")
        cfg_count[sub][c] += 1
ch = chance / both; RHO = ((same / both) - ch) / (1 - ch)
params["rho"] = RHO; params["rho_note"] = f"pooled over pairs and the four subjects: {same}/{both} both-wrong pairs on the same option, chance {ch:.3f}; uncorrected for key errors"
params["config_freq"] = {s: {c: n / sum(v.values()) for c, n in v.items()} for s, v in cfg_count.items()}
Q = d.groupby("subject").init_correct.mean().to_dict(); params["q"] = Q
def posterior(nopt, init, advice, ps, q, rho):
    """advice: list of option indices (one per advisor); ps: accuracies. Common-signal model, exact enumeration."""
    prior = np.full(nopt, (1 - q) / (nopt - 1)); prior[init] = q
    pc = float(np.mean(ps)); n = len(advice); lik = np.zeros(nopt)
    for t in range(nopt):
        tot = 0.0
        for k in range(n + 1):
            for S in itertools.combinations(range(n), k):
                w = rho ** k * (1 - rho) ** (n - k)
                if k:
                    vals = {advice[i] for i in S}
                    if len(vals) > 1: continue
                    s = vals.pop(); w *= pc if s == t else (1 - pc) / (nopt - 1)
                for i in range(n):
                    if i in S: continue
                    w *= ps[i] if advice[i] == t else (1 - ps[i]) / (nopt - 1)
                tot += w
        lik[t] = tot
    post = prior * lik; return post / post.sum()
L = "ABCDEFGHIJ"
def bench(r, rho, qshift=0.0):
    nopt = len(H[r["item"]]["opts"]); q = min(max(Q[r.subject] + qshift, 0.01), 0.99)
    if r.n_llm == 1:
        src = [m for m in M if r["adv_" + m] == r.single_adv] or [r.single_label]
        adv = [L.index(r.single_adv)]; ps = [params["p"][r.subject][src[0]]]
    else:
        pairs = [(L.index(r["adv_" + m]), params["p"][r.subject][m]) for m in M if r["adv_" + m] != "X"]
        adv = [a for a, _ in pairs]; ps = [p for _, p in pairs]
    post = posterior(nopt, L.index(r.init), adv, ps, q, rho)
    best = max(set(adv), key=lambda a: post[a])
    opt_switch = int(best != L.index(r.init) and post[best] > post[L.index(r.init)])
    return opt_switch, L[best] if opt_switch else r.init, float(post[L.index(r.key)])
for tag, rho, qs in (("", RHO, 0), ("_rho0", 0.0, 0), ("_rho05", 0.5, 0), ("_qlo", RHO, -0.05), ("_qhi", RHO, 0.05)):
    out = d.apply(lambda r: bench(r, rho, qs), axis=1, result_type="expand")
    d["opt_switch" + tag], d["opt_final" + tag] = out[0], out[1]
    if tag == "": d["post_key"] = out[2]
    d["excess" + tag] = d.switched - d["opt_switch" + tag]
# ---- trial x wrong model (adopt_m) ----------------------------------------------------------------------------
rows = []
for _, r in d.iterrows():
    for m in M:
        a = r["adv_" + m]
        if a == r.key or a == "X": continue
        if r.n_llm == 1 and a != r.single_adv: continue      # control: only the wrong answer actually shown
        if r.init == a: continue                              # not at risk of adopting it
        others = [r["adv_" + o] for o in M if o != m]
        n_corr = sum(o == r.key for o in others); n_agree = sum(o == a for o in others)
        lab = {(2, 0): "both correct", (1, 1): "one correct, one agrees", (1, 0): "one correct, one different",
               (0, 2): "both wrong, both agree", (0, 1): "both wrong, one agrees", (0, 0): "both wrong, none agree"}[(n_corr, n_agree)]
        rows.append({"pid": r.pid, "cond": r.cond, "item": r["item"], "subject": r.subject, "n_llm": r.n_llm, "exp": r.exp,
                     "model_m": MODEL_NAME[m], "ans_m": a, "adopt_m": int(r.final == a), "others": lab if r.n_llm == 3 else "alone",
                     "opt_adopt": int(r.opt_final == a), "ambiguous_key": r.ambiguous_key, "config": r.config,
                     "init_correct": r.init_correct, "shown_label": r.single_label if r.n_llm == 1 else ""})
dm = pd.DataFrame(rows); dm["excess_adopt"] = dm.adopt_m - dm.opt_adopt
d = d.merge(P[["pid", "duration_s", "conf_initial", "ai_reliable", "used_ai"]], on="pid", how="left")
d.drop(columns=["advised", "wrong_adv"]).to_csv("analysis/d.csv", index=False); dm.to_csv("analysis/dm.csv", index=False)
json.dump(params, open("analysis/params.json", "w"), indent=1)
print("rho", round(RHO, 3), params["rho_note"]); print("p", json.dumps(params["p"], indent=0)); print("q", {k: round(v, 3) for k, v in Q.items()})
print("dm rows", len(dm)); print(dm.groupby(["n_llm", "others"]).adopt_m.agg(["mean", "size"]).round(3))
print(d.groupby("n_llm")[["final_correct", "harm", "benefit", "follow_wrong", "switched", "opt_switch"]].mean().round(3))
