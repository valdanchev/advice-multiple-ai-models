"""Aggregate tables from the study data (Studies 1-2), for open posting.

The participant information sheet (DSREC107) allows aggregate presentation of the data, so these tables contain counts
and rates only, never individual records. Demographic counts below 5 are shown as "<5"; a second cell is shown as "suppressed" where needed to stop a "<5" cell being recovered by subtraction.
Run on the study data (not included in the public package):
    python3 -I aggregate_data/make_aggregate_tables.py <folder with d.csv, dm.csv, participants.csv> <output folder>
"""
import sys, pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]
d = pd.read_csv(f"{SRC}/d.csv", dtype={"item": str}); dm = pd.read_csv(f"{SRC}/dm.csv", dtype={"item": str})
p = pd.read_csv(f"{SRC}/participants.csv", keep_default_na=False)

# 1. Condition x question: counts of trials, correct initial and final answers, switches and harmful/beneficial switches
g = d.groupby(["cond", "item", "subject", "config"])
t1 = g.agg(n_trials=("final_correct", "size"), n_initial_correct=("init_correct", "sum"), n_final_correct=("final_correct", "sum"),
           n_switched=("switched", "sum"), n_harmful_switch=("harm", lambda s: int(s.fillna(0).sum())),
           n_beneficial_switch=("benefit", lambda s: int(s.fillna(0).sum()))).reset_index()
t1.to_csv(f"{OUT}/agg_condition_question.csv", index=False)

# 2. Adoption of a model's wrong answer (matched rows), by condition, question, model and what the other two models said
t2 = (dm.groupby(["cond", "item", "model_m", "others"]).agg(n_rows=("adopt_m", "size"), n_adopted=("adopt_m", "sum"))
      .reset_index().rename(columns={"model_m": "model", "others": "other_models"}))
t2.to_csv(f"{OUT}/agg_wrong_answer_adoption.csv", index=False)

# 3. Table 1 of the paper: adoption by what the other two models said (pooled)
t3 = dm.groupby(["n_llm", "others"]).agg(n_rows=("adopt_m", "size"), n_adopted=("adopt_m", "sum")).reset_index()
t3["adoption_rate"] = (t3.n_adopted / t3.n_rows).round(3); t3.to_csv(f"{OUT}/agg_table1_adoption_by_pattern.csv", index=False)

# 4. Condition-level summaries of participant-level measures (means, SDs, quartiles; no individual values)
part = d.groupby(["cond", "pid"]).agg(initial_accuracy=("init_correct", "mean"), final_accuracy=("final_correct", "mean"),
                                       switch_rate=("switched", "mean")).reset_index()
part["net_gain"] = part.final_accuracy - part.initial_accuracy
part = part.merge(p[["pid", "duration_s"]], on="pid"); part["duration_min"] = part.duration_s / 60
rows = []
for c, gr in part.groupby("cond"):
    for v in ["initial_accuracy", "final_accuracy", "net_gain", "switch_rate", "duration_min"]:
        x = gr[v]; rows.append({"cond": c, "measure": v, "n_participants": len(x), "mean": round(x.mean(), 4), "sd": round(x.std(), 4),
                                "q25": round(x.quantile(.25), 4), "median": round(x.median(), 4), "q75": round(x.quantile(.75), 4)})
pd.DataFrame(rows).to_csv(f"{OUT}/agg_condition_summaries.csv", index=False)

# 5. Demographics and ratings by condition (counts). Cells below 5 are suppressed. Because each condition's total is
# known, a lone suppressed cell could be recovered by subtraction, so within each variable and condition the smallest
# remaining cell is also suppressed whenever exactly one cell would otherwise be suppressed (secondary suppression).
rows = []
for v in ["age", "gender", "education", "used_ai", "conf_initial", "ai_reliable"]:
    ct = pd.crosstab(p[v], p.cond); out = ct.astype(object)
    for c in ct.columns:
        col = ct[c]; small = col[(col < 5)].index.tolist()
        if len(small) == 1:
            rest = col.drop(small).sort_values(); small.append(rest.index[0])
        for lev in small: out.loc[lev, c] = "<5" if ct.loc[lev, c] < 5 else "suppressed"
    for lev, r in out.iterrows():
        rows.append({"variable": v, "level": lev, **{c: r[c] for c in out.columns}})
pd.DataFrame(rows).to_csv(f"{OUT}/agg_demographics.csv", index=False)
print("written:", OUT)
