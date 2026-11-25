# Data and code for "Advice from multiple AI models reduces overreliance only when their errors diverge"

Valentin Danchev, Queen Mary University of London (v.danchev@qmul.ac.uk; ORCID 0000-0002-7563-0168)

This repository holds the analysis code, study materials, aggregate data and a simulated dataset for Studies 1–2
(N = 441) of the paper. In two online experiments, participants answered 32 multiple-choice questions from MMLU-Pro,
saw the answers of one or three large language models (GPT-4o, Claude 3.5 Sonnet, Llama 3.1 70B), with or without
the models' reasoning, and could revise their answer.

The paper studies overreliance on AI. It asks whether advice from three AI models built by different developers, rather
than one, reduces how often people adopt a wrong AI answer, and whether this depends on the models making the same
errors. Seeing three models reduced the adoption of wrong answers, but only when the models' errors diverged. A wrong
answer repeated by a second model was adopted as often as a single model's wrong answer.

- Paper: [preprint link, once posted]
- Preregistration: https://osf.io/nrmke (doi:10.17605/OSF.IO/NRMKE)
- Archived release: [Zenodo DOI, once minted]

## What is included in the repository

| Folder | What it holds |
|---|---|
| `code_study_data/` | The analysis code exactly as run on the study data, with its outputs (`outputs_study_data/`): every number, table and figure in the paper and its Supplementary Information. The study data themselves are not included (see *Data access*). |
| `simulated/` | The full pipeline on a **simulated dataset** with the study's structure. `bash run_all.sh` regenerates every output from scratch. The simulated numbers are not the paper's results. |
| `aggregate_data/` | Aggregate study data (counts and rates by condition, question, model and advice pattern; demographics by condition with small cells suppressed), and the script that produced them. The paper's raw rates can be recomputed from these. |
| `materials/` | The survey print-outs for all four conditions and the post-study check of the 32 answer keys. The design files and public MMLU-Pro model outputs are in `simulated/materials/`. |

Condition labels: C1, one model (answers only); T1, three models (answers only); T2, three models with reasoning;
C2, one model with reasoning. In the preregistration, C1, T1 and T2 are labelled C2, T2 and T4; C2 was added after the
preregistration.

## Data access

Under the consent participants gave (participant information sheet approved by the Queen Mary Ethics of Research
Committee, DSREC107), individual-level data cannot be shared publicly but may be shared with qualified researchers.
The anonymised trial-level data are therefore not posted here. Qualified researchers can request them from the
author with a research plan and a data management plan; from October 2027 they will be held under controlled access
at the UK Data Service. To reproduce the paper's numbers with them, place the files in `simulated/data_simulated/`
in the same format and skip the simulation step (see `simulated/README.md`).

## Requirements

- Python 3.10+ with pandas, numpy, scipy and matplotlib.
- R 4.3+ with lme4 (1.1-35), emmeans (1.10), sandwich, lmtest and jsonlite.

## Licence and citation

Code: MIT (`LICENSE`). Data, materials and documentation: CC BY 4.0, except content from MMLU-Pro, which remains
under Apache 2.0 (`LICENSE-DATA.md`). If you use these materials, please cite the paper and this archive
(`CITATION.cff`).
