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
# M9 moderators
lev <- c("Very unconfident" = 1, "Unconfident" = 2, "Neither confident nor unconfident" = 3, "Confident" = 4, "Very confident" = 5)
rel <- c("Very unreliable" = 1, "Unreliable" = 2, "Neither reliable nor unreliable" = 3, "Reliable" = 4, "Very reliable" = 5)
d$Z_conf <- as.numeric(scale(lev[d$conf_initial])); d$Z_ai <- as.numeric(scale(rel[d$ai_reliable]))  # perceived AI reliability: AI-knowledge item absent; 439 of 441 had used AI chatbots
loo <- ave(d$init_correct, d$pid, FUN = function(x) (sum(x) - x) / (length(x) - 1)); d$Z_skill <- as.numeric(scale(loo))
d$Z_bus <- ifelse(d$subject == "business", .5, -.5)
R$M9_levels_conf_initial <- table(d$conf_initial[!duplicated(d$pid)], useNA = "ifany"); R$M9_used_ai <- table(d$used_ai[!duplicated(d$pid)], useNA = "ifany")
pv <- c()
for (z in c("Z_conf", "Z_ai", "Z_skill", "Z_bus")) { s <- d[!is.na(d[[z]]), ]
  m <- fit(as.formula(paste("final_correct ~ nl * ex + nl *", z, "+ init_correct + (1 | pid) + (1 + n_llm_c | item)")), s)
  co <- summary(m)$coefficients; r <- co[grep(paste0("nlthree:", z, "|", z, ":nlthree"), rownames(co)), ]; R[[paste0("M9_", z)]] <- r; pv[z] <- r[4] }
R$M9_holm <- p.adjust(pv, "holm")
saveRDS(R, "intermediate/results_m9.rds"); sink("outputs/m9_out.txt"); print(R); sink()
