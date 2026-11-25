# Aggregate study data

These tables come from the study data (N = 441; 14,106 trials) and contain counts and rates only, never individual
records. The participant information sheet (DSREC107) allows data to be presented in aggregate form. In
`agg_demographics.csv`, cells with fewer than 5 participants are shown as "<5". Where a condition has only one such cell for a variable, the next smallest cell is shown as "suppressed", so that the "<5" cell cannot be recovered from the condition total. The tables reproduce the paper's raw
rates, for example final accuracy by condition (`agg_condition_question.csv`, summing `n_final_correct` / `n_trials`)
and Table 1 (`agg_table1_adoption_by_pattern.csv`).

Column `config` gives the advice pattern for the question (for example, 2C1W = two models correct, one wrong).
Column `other_models` gives, for a model's wrong answer, what the other two models said; "alone" means the
one-model conditions.
