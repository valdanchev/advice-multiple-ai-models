# Robustness checks (plan Section 4), M8 decision value and time, M9 moderators, M1 with proportional weights.
suppressPackageStartupMessages({library(lme4); library(emmeans); library(sandwich); library(lmtest); library(jsonlite)})
emm_options(lmer.df = "asymptotic")
d  <- read.csv("intermediate/d.csv",  stringsAsFactors = FALSE, colClasses = c(item = "character"))
dm <- read.csv("intermediate/dm.csv", stringsAsFactors = FALSE, colClasses = c(item = "character"))
P  <- read.csv("data_simulated/participants.csv", stringsAsFactors = FALSE)
par <- fromJSON("outputs/params.json")
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
prep <- function(x) { x$n_llm_c <- ifelse(x$n_llm == 3, .5, -.5); x$nl <- factor(ifelse(x$n_llm == 3, "three", "one"), c("one", "three")); x$ex <- factor(paste0("exp", x$exp)); x }
d <- prep(d); dm <- prep(dm)
fit <- function(f, data) { m <- try(glmer(f, data = data, family = binomial, control = ctl), silent = TRUE)
  if (inherits(m, "try-error") || isSingular(m)) m <- glmer(update(f, . ~ . - (1 + n_llm_c | item) + (1 | item)), data = data, family = binomial, control = ctl); m }
pp <- function(m, data, var = "nl") {  # average marginal effect (three - one) by g-computation over the observed rows; SE by delta via emmeans on a factorised covariate
  a <- data; a[[var]] <- factor("one", levels(data[[var]])); b <- data; b[[var]] <- factor("three", levels(data[[var]]))
  p1 <- mean(predict(m, a, type = "response", re.form = NA)); p3 <- mean(predict(m, b, type = "response", re.form = NA))
  e <- summary(contrast(emmeans(m, ~ nl, regrid = "response"), "revpairwise"), infer = TRUE)
  c(one = p1, three = p3, ame = p3 - p1, emm_est = e$estimate, emm_lcl = e$asymp.LCL, emm_ucl = e$asymp.UCL, p = e$p.value) }
R <- list()
m1f <- function(data) fit(final_correct ~ nl * ex + init_correct + (1 | pid) + (1 + n_llm_c | item), data)
m3f <- function(data) fit(adopt_m ~ nl * ex + model_m + (1 | pid) + (1 | item:model_m), data)
R$main_M1 <- pp(m1 <- m1f(d), d); R$main_M3 <- pp(m3 <- m3f(dm), dm)
# 1 natural base rates: reweight configurations to the frequencies the three models produce on the four subjects
nat <- Reduce(`+`, lapply(par$config_freq, function(x) unlist(x)[c("3C","2C1W","1C2W-agree","1C2W-split","0C3W-agree","0C3W-2+1","0C3W-split")]), accumulate = FALSE) / 4
nat[is.na(nat)] <- 0; nat <- nat / sum(nat)
m1c <- fit(final_correct ~ nl * config + init_correct + ex + (1 | pid) + (1 | item), d)
cells <- as.data.frame(emmeans(m1c, ~ nl | config, regrid = "response", at = list(init_correct = mean(d$init_correct))))
w <- nat[cells$config]; w[is.na(w)] <- 0
R$base_rates <- list(natural_freq = nat, design_freq = table(d$config[!duplicated(d$item)]) / 32,
  M1_one = sum(cells$prob[cells$nl == "one"] * w[cells$nl == "one"]) / sum(w[cells$nl == "one"]),
  M1_three = sum(cells$prob[cells$nl == "three"] * w[cells$nl == "three"]) / sum(w[cells$nl == "three"]))
m3c <- fit(adopt_m ~ nl * config + ex + model_m + (1 | pid) + (1 | item:model_m), dm)
c3 <- as.data.frame(emmeans(m3c, ~ nl | config, regrid = "response")); w3 <- nat[c3$config]; w3[is.na(w3)] <- 0
R$base_rates$M3_one <- sum(c3$prob[c3$nl == "one"] * w3[c3$nl == "one"]) / sum(w3[c3$nl == "one"])
R$base_rates$M3_three <- sum(c3$prob[c3$nl == "three"] * w3[c3$nl == "three"]) / sum(w3[c3$nl == "three"])
# 2 subject
R$subject_fe_M1 <- pp(fit(final_correct ~ nl * ex + init_correct + subject + (1 | pid) + (1 + n_llm_c | item), d), d)
R$no_math_M1 <- pp(m1f(subset(d, subject != "college_mathematics")), subset(d, subject != "college_mathematics"))
R$no_math_M3 <- pp(m3f(subset(dm, subject != "college_mathematics")), subset(dm, subject != "college_mathematics"))
# 3 single-model identity: M3 effect per model
for (mm in unique(dm$model_m)) { s <- subset(dm, model_m == mm); R[[paste0("M3_model_", mm)]] <- pp(fit(adopt_m ~ nl * ex + (1 | pid) + (1 | item), s), s) }
# 4 participant-level OLS with HC3 + Mann-Whitney (preregistered)
pl <- aggregate(cbind(final_correct, follow_wrong) ~ pid + n_llm + exp, d, mean)
pl$nl <- factor(pl$n_llm); pl$ex <- factor(pl$exp)
for (y in c("final_correct", "follow_wrong")) { o <- lm(as.formula(paste(y, "~ nl * ex")), pl)
  R[[paste0("OLS_HC3_", y)]] <- coeftest(o, vcov = vcovHC(o, "HC3"))
  R[[paste0("MW_", y)]] <- sapply(1:2, function(e) wilcox.test(pl[[y]][pl$exp == e & pl$n_llm == 3], pl[[y]][pl$exp == e & pl$n_llm == 1])$p.value) }
# 5 exclusions: fastest 5% of participants (no attention checks were included in the survey)
fast <- P$pid[P$duration_s <= quantile(P$duration_s, .05)]
R$excl_fast_M1 <- pp(m1f(subset(d, !pid %in% fast)), subset(d, !pid %in% fast)); R$excl_fast_M3 <- pp(m3f(subset(dm, !pid %in% fast)), subset(dm, !pid %in% fast))
# 6 initial answer wrong only
R$init_wrong_M1 <- pp(fit(final_correct ~ nl * ex + (1 | pid) + (1 + n_llm_c | item), subset(d, init_correct == 0)), subset(d, init_correct == 0))
# 7 answer-key check: drop the 5 ambiguous items
R$no_ambig_M1 <- pp(m1f(subset(d, ambiguous_key == 0)), subset(d, ambiguous_key == 0))
R$no_ambig_M3 <- pp(m3f(subset(dm, ambiguous_key == 0)), subset(dm, ambiguous_key == 0))
dm$others_f <- factor(dm$others, c("alone", "both correct", "one correct, one different", "one correct, one agrees", "both wrong, none agree", "both wrong, one agrees"))
m4n <- fit(adopt_m ~ others_f + ex + model_m + (1 | pid) + (1 | item:model_m), subset(dm, ambiguous_key == 0))
R$no_ambig_M4 <- as.data.frame(emmeans(m4n, ~ others_f, regrid = "response"))
m2hn <- fit(harm ~ nl * ex + (1 | pid) + (1 | item), subset(d, init_correct == 1 & ambiguous_key == 0))
R$no_ambig_M2harm <- summary(contrast(emmeans(m2hn, ~ nl, regrid = "response"), "revpairwise"), infer = TRUE)
# M8 decision value and time cost
P$n_llm <- ifelse(grepl("^T", P$cond), 3, 1); P$exp <- ifelse(P$cond %in% c("C2", "T2"), 2, 1); P$min <- P$duration_s / 60
ot <- lm(duration_s ~ factor(n_llm) * factor(exp), P); R$time_OLS <- coeftest(ot, vcov = vcovHC(ot, "HC3"))
R$time_medians <- aggregate(min ~ cond, P, median)
set.seed(20261112); B <- 2000; acc <- aggregate(final_correct ~ pid + n_llm, d, mean); tt <- P[, c("pid", "n_llm", "duration_s")]
boot <- replicate(B, { i1 <- sample(which(acc$n_llm == 1), replace = TRUE); i3 <- sample(which(acc$n_llm == 3), replace = TRUE)
  j1 <- sample(which(tt$n_llm == 1), replace = TRUE); j3 <- sample(which(tt$n_llm == 3), replace = TRUE)
  da <- mean(acc$final_correct[i3]) - mean(acc$final_correct[i1]); dt <- (mean(tt$duration_s[j3]) - mean(tt$duration_s[j1])) / 32
  c(err_per100 = 100 * da, sec_per_dec = dt, err_per_hour = da / (dt / 3600)) })
R$M8 <- rbind(estimate = c(err_per100 = 100 * (mean(acc$final_correct[acc$n_llm == 3]) - mean(acc$final_correct[acc$n_llm == 1])),
                           sec_per_dec = (mean(tt$duration_s[tt$n_llm == 3]) - mean(tt$duration_s[tt$n_llm == 1])) / 32,
                           err_per_hour = NA), apply(boot, 1, quantile, c(.025, .5, .975)))
R$M8["estimate", "err_per_hour"] <- R$M8["estimate", "err_per100"] / 100 / (R$M8["estimate", "sec_per_dec"] / 3600)
harm_rate <- aggregate(I(init_correct == 1 & final_correct == 0) ~ n_llm, d, mean); R$M8_AI_errors_per100 <- 100 * harm_rate
saveRDS(R, "intermediate/results_robust.rds")
sink("outputs/robust_out.txt"); print(R); sink()
