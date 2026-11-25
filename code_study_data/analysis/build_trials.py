"""Build the trial-level dataset for Studies 1-2 from the two Qualtrics exports.
Usage: python3 -I build_trials.py  (paths fixed below). Output: analysis/trials.csv, analysis/participants.csv, build_log.txt"""
import json, re, collections
import pandas as pd
H = {str(r["question_id"]): r for r in json.load(open("stimuli/hits.json"))}
ADV = json.load(open("stimuli/advice_final.json"))
ORDER, A = ADV["order"], ADV["advice"]
SUBJ = {"ori_mmlu-global_facts": "global_facts", "ori_mmlu-college_mathematics": "college_mathematics", "ori_mmlu-nutrition": "health_nutrition"}
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower().replace("ß", "beta").replace("β", "beta").replace("-", "").replace("fibre", "fiber"))
log = []
def item_of(text):
    t = norm(text)
    c = [q for q in ORDER if norm(H[q]["question"])[:60] in t] or [q for q in ORDER if norm(H[q]["question"])[:35] in t]
    return c[0] if len(c) == 1 else None
def letter(q, val):
    if pd.isna(val): return None
    v = norm(val)
    if v.startswith("idonotwishtoupdate"): return "KEEP"
    opts = [norm(o) for o in H[q]["opts"]]
    ex = [i for i, o in enumerate(opts) if o == v]
    if len(ex) == 1: return "ABCDEFGHIJ"[ex[0]]
    pre = [i for i, o in enumerate(opts) if o and (v.startswith(o) or o.startswith(v))]
    if len(pre) == 1: return "ABCDEFGHIJ"[pre[0]]
    log.append(f"unmatched option: {q} {val!r}"); return "?"
rows, people = [], []
def take(df, prefix, cond, file):
    head, data = df.iloc[0], df.iloc[2:]
    cols = [c for c in df.columns if c.startswith(prefix)]
    pairs = {}
    for j, c in enumerate(cols):
        txt = str(head[c])
        if "UPDATE" in txt: continue
        q = item_of(txt)
        if not q: continue
        nxt = cols[j + 1]; assert "UPDATE" in str(head[nxt]), (cond, c, nxt)
        pairs[q] = {"initial": c, "final": nxt}
    assert len(pairs) == 32 and all(len(v) == 2 for v in pairs.values()), (cond, len(pairs))
    used = data[data[[pairs[q]["initial"] for q in pairs]].notna().any(axis=1)]
    for _, r in used.iterrows():
        pid = r["ResponseId"]  # anonymised participant code (P001-P441); identifiers removed from the exports
        people.append({"pid": pid, "cond": cond, "file": file, "duration_s": float(r["Duration (in seconds)"]),
                       "finished": r["Finished"], "education": r["Q3.1"], "gender": r["Q3.2"], "age": r["Q3.3"], "used_ai": r["Q3.4"], **extra(df, r)})
        for q in ORDER:
            i = letter(q, r[pairs[q]["initial"]]); f = letter(q, r[pairs[q]["final"]])
            if f == "KEEP": f = i
            rows.append({"pid": pid, "cond": cond, "item": q, "init": i, "final": f, "kept_button": int(norm(r[pairs[q]["final"]]).startswith("idonotwish"))})
def extra(df, r):
    head = df.iloc[0]; out = {}
    for c in df.columns:
        t = str(head[c])
        if t.startswith("Overall, how confident are you about the initial"): out["conf_initial"] = r[c]
        elif t.startswith("Overall, how reliable"): out["ai_reliable"] = r[c]
        elif t.startswith("Overall, how confident are you about your updated"): out["conf_updated"] = r[c]
    return out
a = pd.read_csv("in_raw/a.csv", low_memory=False, keep_default_na=False).replace("", float("nan")); b = pd.read_csv("in_raw/b.csv", low_memory=False, keep_default_na=False).replace("", float("nan"))
take(a, "Q4.", "C1", "a"); take(a, "Q5.", "T1", "a"); take(a, "Q6.", "T2", "a"); take(b, "Q7.", "C2", "b")
d = pd.DataFrame(rows); P = pd.DataFrame(people)
M = ("ChatGPT", "Claude", "Llama")
def cfg(q):
    k = H[q]["answer"]; adv = [A[q]["three"][m] for m in M]; w = [x for x in adv if x != k]
    if len(w) == 0: return "3C"
    if len(w) == 1: return "2C1W"
    if len(w) == 2: return "1C2W-agree" if w[0] == w[1] else "1C2W-split"
    return "0C3W-agree" if len(set(w)) == 1 else ("0C3W-split" if len(set(w)) == 3 else "0C3W-2+1")
d["key"] = d.item.map(lambda q: H[q]["answer"]); d["subject"] = d.item.map(lambda q: SUBJ.get(H[q]["src"], "business"))
d["n_opts"] = d.item.map(lambda q: len(H[q]["opts"])); d["config"] = d.item.map(cfg)
d["n_llm"] = d.cond.map({"C1": 1, "C2": 1, "T1": 3, "T2": 3}); d["exp"] = d.cond.map({"C1": 1, "T1": 1, "C2": 2, "T2": 2})
for m in M: d["adv_" + m] = d.item.map(lambda q, m=m: A[q]["three"][m])
d["single_adv"] = d.item.map(lambda q: A[q]["single_answer"]); d["single_label"] = d.item.map(lambda q: A[q]["single_label"])
d["init_correct"] = (d.init == d.key).astype(int); d["final_correct"] = (d.final == d.key).astype(int)
d["switched"] = (d.init != d.final).astype(int)
d.to_csv("analysis/trials_raw.csv", index=False); P.to_csv("analysis/participants.csv", index=False)
log += [f"trials {len(d)}; participants {P.pid.nunique()} by condition {P.cond.value_counts().to_dict()}",
        f"unmatched option values: {(d[['init','final']] == '?').sum().to_dict()}; missing: {d[['init','final']].isna().sum().to_dict()}",
        "configurations by item: " + str(d.drop_duplicates('item').config.value_counts().to_dict())]
open("analysis/build_log.txt", "w").write("\n".join(log) + "\n"); print("\n".join(log[-3:])); print("\n".join(log[:10]))
