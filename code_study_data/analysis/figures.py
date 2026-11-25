"""Draft figures for the Studies 1-2 re-analysis (Figs 2-5). Raw rates with participant-cluster bootstrap 95% CIs."""
import os; os.makedirs("analysis/figs", exist_ok=True)
import json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8a8a85",
                     "axes.labelcolor": "#3d3d3a", "xtick.color": "#5c5c57", "ytick.color": "#5c5c57", "axes.grid": True,
                     "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "axes.axisbelow": True})
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8a85"
d = pd.read_csv("analysis/d.csv", dtype={"item": str}); dm = pd.read_csv("analysis/dm.csv", dtype={"item": str})
rng = np.random.default_rng(3)
def boot(df, col, by, B=1000):
    pm = df.groupby(["pid"] + by)[col].agg(["sum", "count"]).reset_index(); res = {}
    for k, g in pm.groupby(by):
        est = g["sum"].sum() / g["count"].sum(); idx = rng.integers(0, len(g), (B, len(g)))
        bs = g["sum"].values[idx].sum(1) / g["count"].values[idx].sum(1); res[k if isinstance(k, tuple) else (k,)] = (est, *np.quantile(bs, [.025, .975]))
    return res
# Fig 2: accuracy and AI-induced errors
d["harm_ev"] = ((d.init_correct == 1) & (d.final_correct == 0)).astype(int)
fig, ax = plt.subplots(1, 2, figsize=(8, 3.4))
for a, col, title in ((ax[0], "final_correct", "Final accuracy"), (ax[1], "harm_ev", "AI-induced errors\n(correct answer switched to wrong)")):
    r = boot(d, col, ["exp", "n_llm"])
    for j, (n, c, lab) in enumerate(((1, GRAY, "One model"), (3, BLUE, "Three models"))):
        xs = np.array([0, 1]) + (j - .5) * 0.28
        est = [r[(e, n)][0] for e in (1, 2)]; lo = [r[(e, n)][1] for e in (1, 2)]; hi = [r[(e, n)][2] for e in (1, 2)]
        a.bar(xs, est, 0.26, color=c, label=lab, zorder=2)
        a.errorbar(xs, est, yerr=[np.subtract(est, lo), np.subtract(hi, est)], fmt="none", ecolor="#3d3d3a", lw=1, capsize=3, zorder=3)
        top = a.get_ylim()[1] if False else (0.65 if col == "final_correct" else 0.065)
        for x, v, h in zip(xs, est, hi): a.text(x, h + top * 0.015, f"{v:.0%}" if col == "final_correct" else f"{v:.1%}", ha="center", va="bottom", fontsize=8, color="#3d3d3a")
    a.set_xticks([0, 1], ["Answers only\n(Study 1)", "With reasoning\n(Study 2)"]); a.set_title(title, fontsize=10, loc="left")
    a.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
fig.legend(*ax[0].get_legend_handles_labels(), frameon=False, loc="upper right", ncol=2, fontsize=8); ax[0].set_ylim(0, .65); ax[1].set_ylim(0, .065)
fig.tight_layout(rect=(0, 0, 1, .93)); fig.savefig("analysis/figs/fig2_accuracy_harm.png", dpi=200)
# Fig 3: adoption of a given wrong answer by what the other two models said
order = ["alone", "both correct", "one correct, one different", "one correct, one agrees", "both wrong, none agree", "both wrong, one agrees"]
labels = ["Shown alone\n(one model)", "Both others\ncorrect", "One correct,\none different", "One correct,\none agrees", "Both wrong,\nneither agrees", "Both wrong,\none agrees"]
r = boot(dm, "adopt_m", ["others"]); o = {k[0]: v for k, v in r.items()}
fig, a = plt.subplots(figsize=(8, 3.6)); xs = np.arange(len(order))
cols = [GRAY] + [ORANGE if "agrees" in k else BLUE for k in order[1:]]
est = [o[k][0] for k in order]
a.bar(xs, est, 0.6, color=cols, zorder=2)
a.errorbar(xs, est, yerr=[[o[k][0] - o[k][1] for k in order], [o[k][2] - o[k][0] for k in order]], fmt="none", ecolor="#3d3d3a", lw=1, capsize=3, zorder=3)
for x, v, k in zip(xs, est, order): a.text(x, o[k][2] + 0.015, f"{v:.0%}", ha="center", fontsize=8.5, color="#3d3d3a")
a.axhline(o["alone"][0], ls="--", lw=1, color=GRAY, zorder=1)
a.set_xticks(xs, labels, fontsize=8.5); a.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0)); a.set_ylim(0, 1)
a.set_title("Adoption of a model's wrong answer, by what the other two models said (three-model conditions)", fontsize=10, loc="left")
a.text(5.4, 0.97, "orange = another model gave the same wrong answer", ha="right", fontsize=8, color=ORANGE)
fig.tight_layout(); fig.savefig("analysis/figs/fig3_adoption_by_others.png", dpi=200)
# Fig 4: observed vs Bayes-optimal adoption
ex = dm.groupby("others")[["adopt_m", "opt_adopt"]].mean().loc[order]
fig, a = plt.subplots(figsize=(8, 3.4))
a.bar(xs - .17, ex.adopt_m, .32, color=BLUE, label="Observed", zorder=2); a.bar(xs + .17, ex.opt_adopt, .32, color="#b7d3f6", label="Bayes-optimal (ρ = 0.35)", zorder=2)
a.set_xticks(xs, labels, fontsize=8.5); a.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0)); a.set_ylim(0, 1.08)
a.legend(frameon=False, fontsize=8, loc="upper center", ncol=2)
a.set_title("Observed vs Bayes-optimal adoption of a model's wrong answer", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig("analysis/figs/fig4_benchmark.png", dpi=200)
# Fig 5: policies
pol = json.load(open("analysis/bench_policy.json"))["policies"]
names = ["(a) single vendor", "(b) show all three", "(c) majority only", "(e) Bayes-optimal"]; short = ["Single\nvendor", "Show all\nthree", "Majority\nonly", "Bayes-\noptimal"]
fig, ax = plt.subplots(1, 2, figsize=(8, 3.4)); keys = [list(pol)[1], list(pol)[0], list(pol)[2]]
for a, met, ttl in ((ax[0], "accuracy_per_100", "Correct decisions per 100"), (ax[1], "AI_induced_errors_per_100", "AI-induced errors per 100")):
    for j, (k, c) in enumerate(zip(keys, ("#86b6ef", "#2a78d6", "#184f95"))):
        a.bar(np.arange(4) + (j - 1) * .26, [pol[k][n][met] for n in names], .24, color=c, label=k.replace(" (estimated)", ", estimated"), zorder=2)
    a.set_xticks(np.arange(4), short, fontsize=8.5); a.set_title(ttl, fontsize=10, loc="left")
ax[0].set_ylim(0, 85); ax[0].legend(frameon=False, fontsize=7, loc="upper left")
fig.text(0.01, 0.01, "Policies (c) and the Bayes benchmark are model-based predictions; (a) and (b) use observed behaviour.", fontsize=7, color="#5c5c57")
fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig("analysis/figs/fig5_policies.png", dpi=200)
print("ok")
