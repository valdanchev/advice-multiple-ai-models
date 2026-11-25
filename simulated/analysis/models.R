# Studies 1-2 re-analysis: confirmatory and exploratory GLMMs (re-analysis plan, Section 2) and robustness (Section 4).
suppressPackageStartupMessages({library(lme4); library(emmeans); library(sandwich); library(lmtest)})
emm_options(lmer.df = "asymptotic")
d  <- read.csv("intermediate/d.csv",  stringsAsFactors = FALSE, colClasses = c(item = "character"))
dm <- read.csv("intermediate/dm.csv", stringsAsFactors = FALSE, colClasses = c(item = "character"))
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
code <- function(x) { x$n_llm_c <- ifelse(x$n_llm == 3, .5, -.5); x$exp_c <- ifelse(x$exp == 2, .5, -.5)
  x$nl <- factor(ifelse(x$n_llm == 3, "three", "one"), c("one", "three")); x$ex <- factor(paste0("exp", x$exp)); x }
d <- code(d); dm <- code(dm)
fit <- function(f, data) {
  m <- try(glmer(f, data = data, family = binomial, control = ctl), silent = TRUE)
  if (inherits(m, "try-error") || isSingular(m)) {          # plan: drop random slopes first, then the item intercept
    f2 <- update(f, . ~ . - (1 + n_llm_c | item) + (1 | item))
    m <- try(glmer(f2, data = data, family = binomial, control = ctl), silent = TRUE) }
  m }
res <- list(); out <- function(name, x) { res[[name]] <<- x; cat("\n=====", name, "\n"); print(x) }
eff <- function(m, spec = ~ nl) {   # marginal pp effect three - one with 95% CI, plus the cell means
  e <- emmeans(m, spec, regrid = "response"); list(cells = summary(e), contrast = summary(contrast(e, "revpairwise"), infer = TRUE)) }

# M1 final accuracy
m1 <- fit(final_correct ~ nl * ex + init_correct + (1 | pid) + (1 + n_llm_c | item), d)
out("M1 coefficients", summary(m1)$coefficients); out("M1 effect (pp)", eff(m1)); out("M1 by experiment", eff(m1, ~ nl | ex))
# M2 harmful and beneficial switches
m2h <- fit(harm ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 1)); out("M2 harm", eff(m2h)); out("M2 harm by exp", eff(m2h, ~ nl | ex))
m2b <- fit(benefit ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 0)); out("M2 benefit", eff(m2b)); out("M2 benefit by exp", eff(m2b, ~ nl | ex))
# M3 matched adoption of a given wrong answer
m3 <- fit(adopt_m ~ nl * ex + model_m + (1 | pid) + (1 | item:model_m), dm); out("M3 effect (pp)", eff(m3)); out("M3 by exp", eff(m3, ~ nl | ex))
# M4 what the other models said (treatment) + alone as reference, one model so the levels are comparable
dm$others_f <- factor(dm$others, c("alone", "both correct", "one correct, one different", "one correct, one agrees", "both wrong, none agree", "both wrong, one agrees"))
m4 <- fit(adopt_m ~ others_f + ex + model_m + (1 | pid) + (1 | item:model_m), dm)
e4 <- emmeans(m4, ~ others_f, regrid = "response"); out("M4 adoption by what the others said", summary(e4))
out("M4 contrasts vs alone", summary(contrast(e4, "trt.vs.ctrl", ref = 1), infer = TRUE))
out("M4 agree vs different (one correct)", summary(contrast(e4, list(agree_minus_diff = c(0, 0, -1, 1, 0, 0), bothwrong_agree_minus_none = c(0, 0, 0, 0, -1, 1))), infer = TRUE))
# M5 original overreliance metric
m5 <- fit(follow_wrong ~ nl * ex + (1 | pid) + (1 | item), subset(d, opp_wrong == 1)); out("M5 follow_wrong", eff(m5)); out("M5 by exp", eff(m5, ~ nl | ex))
# M6 reasoning: experiment effect within controls (descriptive)
out("M6 reasoning within controls (M5, M3)", list(M5 = summary(contrast(emmeans(m5, ~ ex | nl, regrid = "response"), "revpairwise"), infer = TRUE),
                                                 M3 = summary(contrast(emmeans(m3, ~ ex | nl, regrid = "response"), "revpairwise"), infer = TRUE)))
# M7 brand
dm$gpt <- factor(ifelse(dm$model_m == "GPT-4o", "GPT-4o", "other"))
m7 <- fit(adopt_m ~ gpt * nl + ex + (1 | pid) + (1 | item:model_m), dm); out("M7 brand", summary(emmeans(m7, ~ gpt | nl, regrid = "response")))
out("M7 GPT minus other", summary(contrast(emmeans(m7, ~ gpt | nl, regrid = "response"), "revpairwise"), infer = TRUE))
saveRDS(list(m1 = m1, m2h = m2h, m2b = m2b, m3 = m3, m4 = m4, m5 = m5, m7 = m7), "intermediate/models.rds")
saveRDS(res, "intermediate/results_main.rds")
