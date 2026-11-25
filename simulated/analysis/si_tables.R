# Full fixed- and random-effects tables for the mixed models reported in the main text (SI Appendix, S15).
suppressPackageStartupMessages({library(lme4); library(jsonlite)})
d  <- read.csv("intermediate/d.csv",  stringsAsFactors = FALSE, colClasses = c(item = "character"))
dm <- read.csv("intermediate/dm.csv", stringsAsFactors = FALSE, colClasses = c(item = "character"))
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
code <- function(x) { x$n_llm_c <- ifelse(x$n_llm == 3, .5, -.5)
  x$nl <- factor(ifelse(x$n_llm == 3, "three", "one"), c("one", "three")); x$ex <- factor(paste0("exp", x$exp)); x }
d <- code(d); dm <- code(dm)
dm$others_f <- factor(dm$others, c("alone", "both correct", "one correct, one different", "one correct, one agrees", "both wrong, none agree", "both wrong, one agrees"))
dm$gpt <- factor(ifelse(dm$model_m == "GPT-4o", "GPT-4o", "other"))
M <- list(
  M1 = list(final_correct ~ nl * ex + init_correct + (1 | pid) + (1 + n_llm_c | item), d),
  M2h = list(harm ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 1)),
  M2b = list(benefit ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 0)),
  M3 = list(adopt_m ~ nl * ex + model_m + (1 | pid) + (1 | item:model_m), dm),
  M4 = list(adopt_m ~ others_f + ex + model_m + (1 | pid) + (1 | item:model_m), dm),
  M5 = list(follow_wrong ~ nl * ex + (1 | pid) + (1 | item), subset(d, opp_wrong == 1)),
  M7 = list(adopt_m ~ gpt * nl + ex + (1 | pid) + (1 | item:model_m), dm))
out <- list()
for (k in names(M)) {
  m <- glmer(M[[k]][[1]], data = M[[k]][[2]], family = binomial, control = ctl)
  co <- summary(m)$coefficients; vc <- as.data.frame(VarCorr(m))
  out[[k]] <- list(formula = deparse1(M[[k]][[1]]), nobs = nobs(m), ngrps = as.list(ngrps(m)), singular = isSingular(m),
    fixed = data.frame(term = rownames(co), est = co[, 1], se = co[, 2], z = co[, 3], p = co[, 4], row.names = NULL),
    random = vc[, c("grp", "var1", "var2", "sdcor")], aic = AIC(m))
  cat("\n=====", k, deparse1(M[[k]][[1]]), " n =", nobs(m), "\n"); print(round(co, 4)); print(vc[, c("grp", "var1", "var2", "sdcor")]); print(ngrps(m))
}
write_json(out, "outputs/si_tables.json", digits = 8, auto_unbox = TRUE, pretty = TRUE)
