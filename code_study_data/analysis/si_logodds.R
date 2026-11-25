# Condition contrasts on the log-odds scale (odds ratios), averaged over study, for the mixed models (SI Appendix, S5).
suppressPackageStartupMessages({library(lme4); library(emmeans)}); emm_options(lmer.df = "asymptotic")
d <- read.csv("analysis/d.csv", stringsAsFactors = FALSE, colClasses = c(item = "character")); dm <- read.csv("analysis/dm.csv", stringsAsFactors = FALSE, colClasses = c(item = "character"))
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
code <- function(x) { x$n_llm_c <- ifelse(x$n_llm == 3, .5, -.5); x$nl <- factor(ifelse(x$n_llm == 3, "three", "one"), c("one", "three")); x$ex <- factor(paste0("exp", x$exp)); x }
d <- code(d); dm <- code(dm)
L <- list(M1 = glmer(final_correct ~ nl * ex + init_correct + (1 | pid) + (1 + n_llm_c | item), d, binomial, control = ctl),
  M2h = glmer(harm ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 1), binomial, control = ctl),
  M2b = glmer(benefit ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 0), binomial, control = ctl),
  M3 = glmer(adopt_m ~ nl * ex + model_m + (1 | pid) + (1 | item:model_m), dm, binomial, control = ctl),
  M5 = glmer(follow_wrong ~ nl * ex + (1 | pid) + (1 | item), subset(d, opp_wrong == 1), binomial, control = ctl))
for (k in names(L)) { cat("\n==", k, "\n"); print(summary(contrast(emmeans(L[[k]], ~ nl), "revpairwise"), infer = TRUE, type = "response")) }
cat("\n== raw harm rates by n_llm\n"); print(aggregate(harm ~ n_llm + exp, subset(d, init_correct == 1), mean))
