# Study materials

| Folder or file | What it holds |
|---|---|
| `survey/survey_C1_T1_T2.pdf` | Qualtrics print-out of the survey for conditions C1 (one model, answers), T1 (three models, answers) and T2 (three models, answers and reasoning), recruited together on 17 October 2025. It includes the participant information sheet, consent form, background questions, instructions, all 32 questions with the advice shown, and the post-survey questions. |
| `survey/survey_C2.pdf` | The same for condition C2 (one model, answers and reasoning), recruited on 24 October 2025. |
| `answer_key_check/answer_key_check_32_items.csv` | The post-study check of the MMLU-Pro answer key for each of the 32 questions (see below). |

The design files (the 32 questions, the answer each model gave, the answer shown in the one-model conditions) and the
public MMLU-Pro model outputs are in `../simulated/materials/`.

**Survey print-outs.** These are Qualtrics print previews. Text such as `${q://QID41/ChoiceGroup/SelectedChoices}` is
a placeholder that showed the participant's initial answer in the live survey, and `${e://Field/PROLIFIC_PID}` filled
in the participant's Prolific ID, which is not part of any shared data. The survey links in the page footers have been
removed. In the print preview, some long lines of model reasoning are cut off at the right margin. Models were labelled
"ChatGPT", "Claude" and "Llama", without version numbers.

**Answer-key check.** After the studies, each answer key was checked. An item was judged sound (`ok`) only if the keyed
answer is correct and no other option is defensible; it was judged `ambiguous` if more than one option is defensible or
the key could not be confirmed from a source. Columns:

- `ai_screen` and `check_or_evidence`: a first screen by Claude (Anthropic), with a computed check for calculation items
  and sources or objections for factual ones. This screen is not independent, because Claude 3.5 Sonnet was one of the
  advisers in the study.
- `author_verdict` and `author_note`: the author's verdict, which is the one used in the analyses.

Five items were judged ambiguous: 5312, 5678, 6064, 6274 and 8574.

**MMLU-Pro.** The questions, options and answer keys, and the model outputs, come from MMLU-Pro (Y. Wang et al.,
"MMLU-Pro: A more robust and challenging multi-task language understanding benchmark", NeurIPS 2024;
https://github.com/TIGER-AI-Lab/MMLU-Pro), released under the Apache License 2.0.
