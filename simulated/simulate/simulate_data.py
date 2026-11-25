"""Simulate a synthetic dataset with the same design and file formats as Studies 1-2, so that every analysis script
can be run without the original participant data.

Nothing here is drawn from, fitted to, or resampled from the original participants. The only inputs are the study
materials: the 32 questions and the advice each condition showed (materials/design_items.csv). Behaviour comes from
a simple generative model with hand-set parameters (PARAMETERS below), chosen to give plausible magnitudes. Results
from the simulated data therefore illustrate the pipeline; they are not the study's results.

Usage (from the package root):  python3 -I simulate/simulate_data.py [seed]
Writes: data_simulated/trials_raw.csv, data_simulated/participants.csv   (format used by analysis/derive.py)
        data_simulated/replication_format/{trials,participants}.csv (used by prereg_tests.py, e2_trial_cluster.R)
"""
import sys, numpy as np, pandas as pd

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20251017
rng = np.random.default_rng(SEED)
L = "ABCDEFGHIJ"
M = ("ChatGPT", "Claude", "Llama")
MODEL_NAME = {"ChatGPT": "GPT-4o", "Claude": "Claude 3.5 Sonnet", "Llama": "Llama 3.1 70B"}
AMBIG = {"8574", "6064", "6274", "5312", "5678"}

# ---- PARAMETERS (hand-set; not estimated from the study data) -------------------------------------------------
N_PER_CONDITION = {"C1": 110, "T1": 111, "T2": 110, "C2": 110}
BASE_INITIAL_ACCURACY = {"global_facts": 0.20, "business": 0.15, "college_mathematics": 0.12, "health_nutrition": 0.22}
SD_ABILITY, SD_ITEM, SD_DEFERENCE = 0.5, 0.5, 0.6     # logit-scale random effects: participant ability, item, deference
# Attractiveness (logit scale) of switching to an advised answer, by how many models gave it.
SCORE_ONE_MODEL = 1.10                                  # one model shown
SCORE_THREE = {1: -1.70, 2: 1.30, 3: 2.00}              # three models shown: answer given by 1, 2 or 3 models
REASONING_BONUS = {1: 0.45, 3: 0.05}                    # extra pull of advice when reasoning is shown (one / three models)
PRIVATE_KNOWLEDGE = 1.30                                # extra pull of the initial answer when it is correct
P_RANDOM_SWITCH = 0.02                                  # switch to an unadvised answer
P_KEEP_BUTTON = 0.90                                    # final = initial via the "keep my answer" button
MEDIAN_DURATION_S = {1: 1440, 2: 1800}; SD_LOG_DURATION = 0.40; SECONDS_PER_DECISION_THREE = 3.0
CATEGORIES = {
    "education": (["Less than high school", "High school", "Bachelors or equivalent first degree qualification",
                   "Postgraduate academic below-Masters level qualification (e.g. Certificate or Diploma)",
                   "Masters or equivalent higher degree level qualification", "Professional degree", "Doctorate", "Other"],
                  [.02, .30, .38, .04, .17, .03, .03, .03]),
    "gender": (["Female", "Male", "Prefer not to say"], [.50, .495, .005]),
    "age": (["18 to 24", "25 to 34", "35 to 44", "45 to 54", "55 to 64", "65 or over"], [.08, .22, .24, .20, .16, .10]),
    "used_ai": (["Yes", "No"], [.99, .01]),
    "ai_reliable": (["Very unreliable", "Unreliable", "Neither reliable nor unreliable", "Reliable", "Very reliable"],
                    [.02, .10, .28, .50, .10]),
}
CONF = ["Very unconfident", "Unconfident", "Neither confident nor unconfident", "Confident", "Very confident"]

# ---- design -----------------------------------------------------------------------------------------------------
items = pd.read_csv("materials/design_items.csv", dtype=str, keep_default_na=False).sort_values("order", key=lambda s: s.astype(int))
items["n_opts"] = items.n_opts.astype(int)
item_effect = dict(zip(items.item, rng.normal(0, SD_ITEM, len(items))))
logit = lambda p: np.log(p / (1 - p)); expit = lambda x: 1 / (1 + np.exp(-x))

def choose_final(init, init_correct, advice, n_models, reasoning, deference):
    """Softmax choice among the initial answer and the advised answers."""
    counts = {a: advice.count(a) for a in sorted(set(advice)) if a != "X"}   # sorted: set order varies between runs
    opts, scores = [init], [PRIVATE_KNOWLEDGE * init_correct]
    for a, k in counts.items():
        s = (SCORE_ONE_MODEL if n_models == 1 else SCORE_THREE[k]) + deference + reasoning * REASONING_BONUS[n_models]
        if a == init: scores[0] = max(scores[0], s + 1.7)   # advice agreeing with the initial answer makes staying likelier
        else: opts.append(a); scores.append(s)
    p = np.exp(np.array(scores) - max(scores)); p /= p.sum()
    return opts[rng.choice(len(opts), p=p)]

trials, people, pid_n = [], [], 0
for cond, n in N_PER_CONDITION.items():
    n_llm = 3 if cond.startswith("T") else 1; exp = 2 if cond in ("T2", "C2") else 1; reasoning = int(exp == 2)
    for _ in range(n):
        pid_n += 1; pid = f"S{pid_n:03d}"
        ability, deference = rng.normal(0, SD_ABILITY), rng.normal(0, SD_DEFERENCE)
        for it in items.itertuples():
            p0 = expit(logit(BASE_INITIAL_ACCURACY[it.subject]) + ability + item_effect[it.item])
            wrong_opts = [o for o in L[:it.n_opts] if o != it.key]
            init = it.key if rng.random() < p0 else rng.choice(wrong_opts)
            advice = [it.single_adv] if n_llm == 1 else [getattr(it, "adv_" + m) for m in M]
            final = choose_final(init, int(init == it.key), advice, n_llm, reasoning, deference)
            if rng.random() < P_RANDOM_SWITCH: final = rng.choice([o for o in L[:it.n_opts] if o != init])
            kept = int(final == init and rng.random() < P_KEEP_BUTTON)
            trials.append({"pid": pid, "cond": cond, "item": it.item, "init": init, "final": final, "kept_button": kept,
                           "key": it.key, "subject": it.subject, "n_opts": it.n_opts, "config": it.config, "n_llm": n_llm,
                           "exp": exp, "adv_ChatGPT": it.adv_ChatGPT, "adv_Claude": it.adv_Claude, "adv_Llama": it.adv_Llama,
                           "single_adv": it.single_adv, "single_label": it.single_label_C2 if cond == "C2" else it.single_label_C1,
                           "init_correct": int(init == it.key), "final_correct": int(final == it.key), "switched": int(final != init)})
        acc = np.mean([t["init_correct"] for t in trials[-len(items):]])
        conf = CONF[int(np.clip(np.round(1.2 + 4 * acc + rng.normal(0, 0.9)), 0, 4))]
        dur = MEDIAN_DURATION_S[exp] * np.exp(rng.normal(0, SD_LOG_DURATION)) + (SECONDS_PER_DECISION_THREE * len(items) if n_llm == 3 else 0)
        person = {"pid": pid, "cond": cond, "file": "b" if cond == "C2" else "a", "duration_s": round(float(dur), 1), "finished": True}
        for c, (levels, probs) in CATEGORIES.items(): person[c] = rng.choice(levels, p=probs)
        person["conf_initial"] = conf
        person["conf_updated"] = CONF[int(np.clip(CONF.index(conf) + rng.integers(0, 2), 0, 4))]
        people.append(person)

T = pd.DataFrame(trials); P = pd.DataFrame(people)
P = P[["pid", "cond", "file", "duration_s", "finished", "education", "gender", "age", "used_ai", "conf_initial", "ai_reliable", "conf_updated"]]
T.to_csv("data_simulated/trials_raw.csv", index=False); P.to_csv("data_simulated/participants.csv", index=False)

# ---- the same data in the replication-package format --------------------------------------------------------------
src = {r.item: [m for m in M if getattr(r, "adv_" + m) == r.single_adv] for r in items.itertuples()}
R = pd.DataFrame({"participant": T.pid, "condition": T.cond, "study": T.exp, "recruitment_wave": np.where(T.cond == "C2", 2, 1),
                  "n_models_shown": T.n_llm, "reasoning_shown": (T.exp == 2).astype(int), "item": T.item, "subject": T.subject,
                  "n_options": T.n_opts, "key": T.key, "ans_gpt4o": T.adv_ChatGPT, "ans_claude": T.adv_Claude, "ans_llama": T.adv_Llama,
                  "single_model": T.item.map(lambda q: MODEL_NAME[src[q][0]]), "single_model_answer": T.single_adv,
                  "initial_answer": T.init, "final_answer": T.final, "kept_initial_button": T.kept_button,
                  "ambiguous_key": T.item.isin(AMBIG).astype(int)})
R.to_csv("data_simulated/replication_format/trials.csv", index=False)
PL = pd.DataFrame({"participant": P.pid, "condition": P.cond, "study": np.where(P.cond.isin(["T2", "C2"]), 2, 1),
                   "recruitment_wave": np.where(P.cond == "C2", 2, 1), "session_duration_s": P.duration_s, "age_band": P.age,
                   "gender": P.gender, "education": P.education, "used_ai_chatbots_before": P.used_ai,
                   "confidence_initial_answers": P.conf_initial, "ai_reliability_rating": P.ai_reliable,
                   "confidence_updated_answers": P.conf_updated})
PL.to_csv("data_simulated/replication_format/participants.csv", index=False)
print(f"seed {SEED}: {len(P)} simulated participants, {len(T)} trials")
print(T.groupby("cond")[["init_correct", "final_correct", "switched"]].mean().round(3).to_string())
