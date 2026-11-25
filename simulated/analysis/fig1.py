import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
fig, a = plt.subplots(figsize=(8, 3.2)); a.set_xlim(0, 10); a.set_ylim(0, 4); a.axis("off")
def box(x, y, w, h, title, body, fc):
    a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec="#8a8a85", lw=1))
    a.text(x + w / 2, y + h - 0.28, title, ha="center", va="top", fontsize=10, weight="bold", color="#1f1f1d")
    a.text(x + w / 2, y + h - 0.7, body, ha="center", va="top", fontsize=8.5, color="#3d3d3a", linespacing=1.4)
def arrow(x1, x2, y=2.0):
    a.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=14, color="#5c5c57", lw=1.2))
box(0.1, 0.9, 2.2, 2.2, "1. Initial answer", "Participant answers a\nmultiple-choice question\n(8–10 options)", "#f4f3ef")
box(3.0, 0.2, 4.0, 3.6, "2. AI advice", "", "#e8f0fb")
a.text(5.0, 3.0, "One model   vs   three models", ha="center", fontsize=9, color="#184f95", weight="bold")
a.text(5.0, 2.6, "(GPT-4o, Claude 3.5 Sonnet, Llama 3.1 70B;\nreal answers from different developers)", ha="center", va="top", fontsize=8, color="#3d3d3a")
a.text(5.0, 1.6, "Study 1: answers only\nStudy 2: answers + step-by-step reasoning", ha="center", va="top", fontsize=8.5, color="#3d3d3a", linespacing=1.5)
a.text(5.0, 0.6, "Which models are correct is balanced across\n32 questions; wrong answers are the models' own", ha="center", va="top", fontsize=7.5, color="#5c5c57", style="italic")
box(7.7, 0.9, 2.2, 2.2, "3. Final answer", "Participant keeps or\nrevises the answer", "#f4f3ef")
arrow(2.35, 2.95); arrow(7.05, 7.65)
fig.tight_layout(); fig.savefig("outputs/figs/fig1_design.png", dpi=200)
