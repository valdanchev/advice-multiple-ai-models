"""Parse the advice shown in Studies 1-2 from the Qualtrics print-out (blocks C1, T1, T2).
Output: stimuli/advice.json  {block: {question_id: {model: option_letter}}} plus the survey order of items."""
import json, re
t = open("in_survey/raw_clean.txt").read()
h = {str(r["question_id"]): r for r in json.load(open("stimuli/hits.json"))}
IDS = "5529 5226 5750 5533 5678 5312 5311 5883 8705 8703 8152 8153 8041 7730 8574 7832 646 477 671 638 799 599 612 600 6191 6630 6061 6384 6064 6634 6274 6057".split()
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower().replace("ß", "beta").replace("β", "beta"))
segs = [m.start() for m in re.finditer(r"On the previous question", t)]
def which_item(seg):
    head = norm(seg[:400])
    best = [q for q in IDS if norm(h[q]["question"])[:50] in head]
    if len(best) != 1:
        best = [q for q in IDS if norm(h[q]["question"])[:30] in head]
    return best
def match_option(q, text):
    """letter of the option whose normalised text the given text starts with (longest match)."""
    nt = norm(text); cands = []
    exact = [i for i, o in enumerate(h[q]["opts"]) if norm(o) == nt]
    if len(exact) == 1: return "ABCDEFGHIJ"[exact[0]]
    for i, o in enumerate(h[q]["opts"]):
        no = norm(o)
        if no and (nt.startswith(no) or no.startswith(nt) and len(nt) >= 3): cands.append((len(no), "ABCDEFGHIJ"[i]))
    return max(cands)[1] if cands else None
out, order, problems = {}, [], []
for k, s in enumerate(segs):
    seg = t[s: segs[k + 1] if k + 1 < len(segs) else len(t)]
    block = "C1" if k < 32 else ("T1" if k < 64 else "T2")
    if block != "T2": seg = seg.split("You have now an opportunity")[0] if block == "T1" else seg
    qs = which_item(seg)
    if len(qs) != 1: problems.append((k, block, qs, seg[:120])); continue
    q = qs[0]; adv = {}
    if block == "C1":
        m = re.search(r"chatbot\s+(ChatGPT|Claude|Llama)\s+predicts\s+(?:the\s+answer:\s+)?([^\n]+)\n(?:([^\n]+)\n)?", seg)
        if not m: problems.append((k, block, q, seg[:300])); continue
        model, l1, l2 = m.group(1), m.group(2), m.group(3) or ""
        adv[model] = match_option(q, l1 + " " + l2) or match_option(q, l1)
    elif block == "T1":
        body = seg.split("chatbots:")[-1]
        for m in re.finditer(r"(.+?)\s*by\s*(ChatGPT|Claude|Llama)", body, re.S):
            adv[m.group(2)] = match_option(q, m.group(1).strip().split("\n")[-1]) or match_option(q, " ".join(m.group(1).split("\n")))
    else:
        cur = None
        for line in seg.split("\n"):
            ls = line.strip()
            if ls in ("ChatGPT", "Claude", "Llama"): cur = ls; continue
            for a in re.findall(r"answer is:? \(?([A-J])\)", ls):
                if cur and cur not in adv: adv[cur] = a
        for mname in ("ChatGPT", "Claude", "Llama"): adv.setdefault(mname, None)
    out.setdefault(block, {})[q] = adv
    if block == "C1": order.append(q)
json.dump({"advice": out, "order": order}, open("stimuli/advice.json", "w"), indent=1)
for b in out: print(b, len(out[b]), sum(1 for v in out[b].values() for x in v.values() if x is None), "unmatched")
print("problems", problems[:5]); print("order", order)
