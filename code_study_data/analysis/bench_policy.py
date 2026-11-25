"""Bayesian benchmark summaries (plan Section 3) and the deployment-policy simulation (Section 3b)."""
import json, itertools
import numpy as np, pandas as pd
d = pd.read_csv("analysis/d.csv", keep_default_na=False, dtype={"item": str}).replace("", np.nan)
dm = pd.read_csv("analysis/dm.csv", dtype={"item": str})
par = json.load(open("analysis/params.json")); out = {}
for c in ["switched", "opt_switch", "excess", "excess_rho0", "excess_rho05", "excess_qlo", "excess_qhi"]: d[c] = pd.to_numeric(d[c])
# --- benchmark: excess reliance ---------------------------------------------------------------------------------
pl = d.groupby(["pid", "n_llm"])[["switched", "opt_switch", "excess", "excess_rho0", "excess_rho05", "excess_qlo", "excess_qhi"]].mean().reset_index()
t_ = pl.drop(columns="pid").groupby("n_llm").agg(["mean", "sem"]).round(3); t_.columns = [" ".join(c) for c in t_.columns]; out["excess_switch_by_n_llm"] = t_.to_dict(orient="index")
ex = dm.groupby("others").agg(adopt=("adopt_m", "mean"), optimal=("opt_adopt", "mean"), n=("adopt_m", "size"))
ex["excess"] = ex.adopt - ex.optimal; out["excess_adopt_by_others"] = ex.round(3).to_dict(orient="index")
# participant-clustered CI for excess adoption by 'others'
rng = np.random.default_rng(1); pids = dm.pid.unique()
grp = {p: g for p, g in dm.groupby("pid")}
B = []
for _ in range(1000):
    s = pd.concat([grp[p] for p in rng.choice(pids, len(pids))]); B.append(s.groupby("others").apply(lambda g: (g.adopt_m - g.opt_adopt).mean()))
B = pd.DataFrame(B); out["excess_adopt_CI"] = B.quantile([.025, .975]).round(3).to_dict()
# sensitivity: optimal adoption under alternative rho / q
# (opt_final variants exist in d; recompute adoption-optimality per variant)
look = d.set_index(["pid", "item"])
for tag in ["", "_rho0", "_rho05", "_qlo", "_qhi"]:
    of = look["opt_final" + tag]
    dm["opt" + tag] = [int(of.loc[(p, i)] == a) for p, i, a in zip(dm.pid, dm["item"], dm.ans_m)]
out["optimal_adopt_sensitivity"] = dm.groupby("others")[["adopt_m", "opt", "opt_rho0", "opt_rho05", "opt_qlo", "opt_qhi"]].mean().round(3).to_dict(orient="index")
# --- deployment-policy simulation -----------------------------------------------------------------------------------
M = ["ChatGPT", "Claude", "Llama"]; CF = ["3C", "2C1W", "1C2W-agree", "1C2W-split", "0C3W-agree", "0C3W-2+1", "0C3W-split"]
def config_dist(rho, n=200000, seed=7):
    """Configuration frequencies under the common-signal model, per subject, averaged over the four subjects."""
    r = np.random.default_rng(seed); tot = np.zeros(len(CF))
    for sub, ps in par["p"].items():
        p = np.array([ps[m] for m in M]); pc = p.mean()
        common = np.where(r.random(n) < pc, 0, r.integers(1, 10, n))            # 0 = correct option, 1-9 wrong options
        own = np.where(r.random((n, 3)) < p, 0, r.integers(1, 10, (n, 3)))
        use = r.random((n, 3)) < rho; ans = np.where(use, common[:, None], own)
        w = ans != 0; nw = w.sum(1)
        c = np.empty(n, dtype=object); c[nw == 0] = "3C"; c[nw == 1] = "2C1W"
        two = nw == 2; a2 = np.where(w, ans, -1); s2 = np.sort(a2, 1)
        c[two & (s2[:, 1] == s2[:, 2])] = "1C2W-agree"; c[two & (s2[:, 1] != s2[:, 2])] = "1C2W-split"
        three = nw == 3; nu = np.array([len(set(x)) for x in ans])
        c[three & (nu == 1)] = "0C3W-agree"; c[three & (nu == 2)] = "0C3W-2+1"; c[three & (nu == 3)] = "0C3W-split"
        tot += np.array([(c == k).mean() for k in CF])
    return dict(zip(CF, tot / 4))
out["natural_freq_observed"] = {k: round(np.mean([v.get(k, 0) for v in par["config_freq"].values()]), 3) for k in CF}
rho_hat = par["rho"]
dist = {f"rho={rho_hat:.2f} (estimated)": config_dist(rho_hat), "rho=0 (independent vendors)": config_dist(0.0), "rho=0.5 (heavily shared errors)": config_dist(0.5)}
out["simulated_freq"] = {k: {c: round(v, 3) for c, v in x.items()} for k, x in dist.items()}
T = d[d.n_llm == 3]; C = d[d.n_llm == 1]
d["harm_ev"] = ((d.init_correct == 1) & (d.final_correct == 0)).astype(int)
T = d[d.n_llm == 3]; C = d[d.n_llm == 1]
C_adv_ok = C.single_adv == C.key
a_c, a_w = C[C_adv_ok].final_correct.mean(), C[~C_adv_ok].final_correct.mean()
h_c, h_w = C[C_adv_ok].harm_ev.mean(), C[~C_adv_ok].harm_ev.mean()
acc_T = T.groupby("config").final_correct.mean().to_dict(); harm_T = T.groupby("config").harm_ev.mean().to_dict()
d["opt_correct"] = (d.opt_final == d.key).astype(int); d["opt_harm"] = ((d.init_correct == 1) & (d.opt_correct == 0)).astype(int)
T = d[d.n_llm == 3]; acc_O = T.groupby("config").opt_correct.mean().to_dict(); harm_O = T.groupby("config").opt_harm.mean().to_dict()
for dct in (acc_T, harm_T, acc_O, harm_O): dct.setdefault("0C3W-agree", dct["0C3W-2+1"])    # not in the design: proxy
maj_correct = {"3C": 1, "2C1W": 1, "1C2W-agree": 0, "1C2W-split": 1 / 3, "0C3W-agree": 0, "0C3W-2+1": 0, "0C3W-split": 0}
n_correct = {"3C": 3, "2C1W": 2, "1C2W-agree": 1, "1C2W-split": 1, "0C3W-agree": 0, "0C3W-2+1": 0, "0C3W-split": 0}
pol = {}
for lab, f in dist.items():
    pa = sum(f[c] * n_correct[c] / 3 for c in CF)                 # single vendor = one of the three at random
    A = {"(a) single vendor": (pa * a_c + (1 - pa) * a_w, pa * h_c + (1 - pa) * h_w),
         "(b) show all three": (sum(f[c] * acc_T[c] for c in CF), sum(f[c] * harm_T[c] for c in CF)),
         "(c) majority only": (sum(f[c] * (maj_correct[c] * a_c + (1 - maj_correct[c]) * a_w) for c in CF), sum(f[c] * (maj_correct[c] * h_c + (1 - maj_correct[c]) * h_w) for c in CF)),
         "(e) Bayes-optimal": (sum(f[c] * acc_O[c] for c in CF), sum(f[c] * harm_O[c] for c in CF))}
    b, cc = A["(b) show all three"], A["(c) majority only"]
    A["(d) majority + disagreement flag (range)"] = (sorted([b[0], cc[0]]), sorted([b[1], cc[1]]))
    pol[lab] = {k: {"accuracy_per_100": np.round(np.array(v[0]) * 100, 1).tolist(), "AI_induced_errors_per_100": np.round(np.array(v[1]) * 100, 1).tolist()} for k, v in A.items()}
out["policy_inputs"] = {"control_acc_when_advice_correct": round(a_c, 3), "control_acc_when_advice_wrong": round(a_w, 3),
                        "treatment_acc_by_config": {k: round(v, 3) for k, v in acc_T.items()}, "optimal_acc_by_config": {k: round(v, 3) for k, v in acc_O.items()}}
out["policies"] = pol
json.dump(out, open("analysis/bench_policy.json", "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in ("excess_switch_by_n_llm", "excess_adopt_by_others", "excess_adopt_CI", "optimal_adopt_sensitivity", "natural_freq_observed", "simulated_freq", "policy_inputs", "policies")}, indent=1, default=float)[:9000])
