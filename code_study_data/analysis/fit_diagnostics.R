# Step 14. Fit diagnostics for every reported GLMM: singularity, convergence messages, and whether the random slope was dropped.
suppressPackageStartupMessages({library(lme4)})
src <- readLines("analysis/models.R")
eval(parse(text = src[2:9]))          # data, control, coding
log_fit <- function(name, f, data) {
  m <- try(glmer(f, data = data, family = binomial, control = ctl), silent = TRUE); used <- deparse(f)
  sing <- !inherits(m, "try-error") && isSingular(m)
  if (inherits(m, "try-error") || sing) { f <- update(f, . ~ . - (1 + n_llm_c | item) + (1 | item)); m <- glmer(f, data = data, family = binomial, control = ctl); used <- paste(deparse(f), collapse = "") }
  msg <- m@optinfo$conv$lme4$messages
  cat(sprintf("%-6s initial_singular=%s final_singular=%s convergence_msgs=%s\n  formula: %s\n", name, sing, isSingular(m), ifelse(is.null(msg), "none", paste(msg, collapse = "; ")), paste(used, collapse = "")))
}
dm$others_f <- factor(dm$others, c("alone", "both correct", "one correct, one different", "one correct, one agrees", "both wrong, none agree", "both wrong, one agrees"))
log_fit("M1", final_correct ~ nl * ex + init_correct + (1 | pid) + (1 + n_llm_c | item), d)
log_fit("M2h", harm ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 1))
log_fit("M2b", benefit ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 0))
log_fit("M3", adopt_m ~ nl * ex + model_m + (1 | pid) + (1 | item:model_m), dm)
log_fit("M4", adopt_m ~ others_f + ex + model_m + (1 | pid) + (1 | item:model_m), dm)
dm$gpt <- factor(ifelse(dm$model_m == "GPT-4o", "GPT-4o", "other"))
log_fit("M7", adopt_m ~ gpt * nl + ex + (1 | pid) + (1 | item:model_m), dm)
