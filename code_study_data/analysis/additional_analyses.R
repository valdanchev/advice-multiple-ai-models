# Additional analyses: net gain in accuracy, decision-level overreliance (one count per decision),
# demographic moderators, stimulus correlation, private knowledge and confidence.
suppressPackageStartupMessages({library(lme4); library(emmeans)})
emm_options(lmer.df = "asymptotic")
d  <- read.csv("analysis/d.csv",  stringsAsFactors = FALSE, colClasses = c(item = "character"), na.strings = "")
dm <- read.csv("analysis/dm.csv", stringsAsFactors = FALSE, colClasses = c(item = "character"), na.strings = "")
P  <- read.csv("analysis/participants.csv", stringsAsFactors = FALSE, na.strings = "")
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
d$nl <- factor(ifelse(d$n_llm == 3, "three", "one"), c("one", "three")); dm$nl <- factor(ifelse(dm$n_llm == 3, "three", "one"), c("one", "three"))
d$ex <- factor(paste0("exp", d$exp)); dm$ex <- factor(paste0("exp", dm$exp))
ci <- function(x) { m <- mean(x); s <- sd(x) / sqrt(length(x)); sprintf("%.2f (%.2f-%.2f)", m, m - 1.96 * s, m + 1.96 * s) }
cat("== 1. Net gain in accuracy (final_correct - init_correct, mean per participant; additional measure)\n")
d$learn <- d$final_correct - d$init_correct
L <- aggregate(learn ~ pid + cond + exp + n_llm, d, mean)
for (e in 1:2) { a <- L$learn[L$exp == e & L$n_llm == 1]; b <- L$learn[L$exp == e & L$n_llm == 3]
  w <- wilcox.test(a, b); cat(sprintf("Study %d: one %s  three %s  MW P = %.2g\n", e, ci(a), ci(b), w$p.value)) }
cat("\n== 2. Decision-level overreliance: items where the one-model condition's model was wrong (same items in both arms)\n")
adv <- c("adv_ChatGPT", "adv_Claude", "adv_Llama")
d$sw <- d$single_adv != d$key
wrongset <- function(r) { a <- unlist(r[adv]); if (r[["n_llm"]] == 1) a <- r[["single_adv"]]; unique(a[a != r[["key"]] & a %in% LETTERS[1:10]]) }
ws <- apply(d, 1, wrongset)
d$init_in_wrong <- mapply(function(i, w) i %in% w, d$init, ws)
d$final_in_wrong <- mapply(function(f, w) f %in% w, d$final, ws)
s <- d[d$sw & !d$init_in_wrong & !is.na(d$final), ]
cat("decisions:", nrow(s), " items:", length(unique(s$item)), "\n")
O <- aggregate(final_in_wrong ~ pid + exp + n_llm, s, mean)
for (e in 1:2) { a <- O$final_in_wrong[O$exp == e & O$n_llm == 1]; b <- O$final_in_wrong[O$exp == e & O$n_llm == 3]
  cat(sprintf("Study %d: one %s  three %s  MW P = %.2g\n", e, ci(a), ci(b), wilcox.test(a, b)$p.value)) }
cat(sprintf("Pooled raw: one %.3f three %.3f\n", mean(s$final_in_wrong[s$n_llm == 1]), mean(s$final_in_wrong[s$n_llm == 3])))
m <- glmer(final_in_wrong ~ nl * ex + (1 | pid) + (1 | item), data = s, family = binomial, control = ctl)
print(summary(contrast(emmeans(m, ~ nl, regrid = "response"), "revpairwise"), infer = TRUE))
cat("\n== 3. Demographic moderators of the effect of three models\n")
P$age_n <- c("18 to 24" = 21, "25 to 34" = 29.5, "35 to 44" = 39.5, "45 to 54" = 49.5, "55 to 64" = 59.5, "65 or over" = 70)[P$age]
P$female <- ifelse(P$gender == "Female", .5, ifelse(P$gender == "Male", -.5, NA))
deg <- c("Bachelors or equivalent first degree qualification", "Masters or equivalent higher degree level qualification", "Doctorate",
         "Postgraduate academic below-Masters level qualification (e.g. Certificate or Diploma)", "Professional degree")
P$degree <- ifelse(P$education %in% deg, .5, ifelse(P$education %in% c("High school", "Less than high school"), -.5, NA))
P$Z_age <- as.numeric(scale(P$age_n))
cat("used AI before:", table(P$used_ai), "\n"); cat("degree:", table(P$degree, useNA = "ifany"), " female:", table(P$female, useNA = "ifany"), "\n")
d <- merge(d, P[, c("pid", "Z_age", "female", "degree")], by = "pid"); dm <- merge(dm, P[, c("pid", "Z_age", "female", "degree")], by = "pid")
dm$adopt_m <- as.numeric(dm$adopt_m); dmm <- dm[!is.na(dm$adopt_m), ]
pv <- c(); est <- list()
for (z in c("Z_age", "female", "degree")) {
  s1 <- d[!is.na(d[[z]]), ]
  m1 <- glmer(as.formula(paste("final_correct ~ nl * ex + nl *", z, "+ init_correct + (1 | pid) + (1 | item)")), data = s1, family = binomial, control = ctl)
  s2 <- dmm[!is.na(dmm[[z]]), ]
  m2 <- glmer(as.formula(paste("adopt_m ~ nl * ex + nl *", z, "+ model_m + (1 | pid) + (1 | item:model_m)")), data = s2, family = binomial, control = ctl)
  for (k in list(list("accuracy", m1), list("adoption", m2))) { co <- summary(k[[2]])$coefficients
    r <- co[grep(paste0("nlthree:", z), rownames(co)), ]; nm <- paste(k[[1]], z); pv[nm] <- r[4]
    cat(sprintf("%-18s interaction b = %.3f (SE %.3f), P = %.3f\n", nm, r[1], r[2], r[4])) } }
cat("Holm-adjusted:\n"); print(round(p.adjust(pv, "holm"), 3))
cat("\n== 4. Stimulus set: correctness correlation between models, wrong-answer agreement\n")
it <- d[!duplicated(d$item), c("item", "key", adv)]
C <- sapply(adv, function(a) as.numeric(it[[a]] == it$key)); print(round(cor(C), 3)); cat("per-model accuracy on stimuli:", colMeans(C), "\n")
both <- 0; agree <- 0
for (i in seq_len(nrow(it))) for (pr in combn(adv, 2, simplify = FALSE)) { a <- it[i, pr[1]]; b <- it[i, pr[2]]
  if (a != it$key[i] && b != it$key[i]) { both <- both + 1; agree <- agree + (a == b) } }
cat(sprintf("pairs of models both wrong: %d; same wrong answer: %d (%.0f%%; chance about 11%%)\n", both, agree, 100 * agree / both))
cat("\n== 5. Private knowledge and the benchmark\n")
# Adoption of a wrong answer shared by two models (third model correct), by whether the participant's initial answer was correct
k3 <- dm[dm$n_llm == 3 & dm$others == "one correct, one agrees", ]
cat(sprintf("shared wrong answer, third model correct: adoption %.3f overall (n = %d rows); benchmark %.3f\n",
            mean(k3$adopt_m), nrow(k3), mean(k3$opt_adopt)))
for (ic in 1:0) { s <- k3[k3$init_correct == ic, ]
  cat(sprintf("  initial answer %s: adoption %.3f (n = %d rows); benchmark %.3f\n",
              ifelse(ic == 1, "correct", "wrong"), mean(s$adopt_m), nrow(s), mean(s$opt_adopt))) }
# Self-rated confidence (one rating per participant, asked after the task: "Overall, how confident are you about the
# initial answers you have given...?") against initial accuracy
lev <- c("Very unconfident", "Unconfident", "Neither confident nor unconfident", "Confident", "Very confident")
d$conf <- factor(d$conf_initial, lev)
cal <- aggregate(init_correct ~ conf, d, function(x) c(acc = mean(x), n = length(x)))
cal <- data.frame(confidence = cal$conf, initial_accuracy = round(cal$init_correct[, "acc"], 3), trials = cal$init_correct[, "n"],
                  participants = as.vector(table(factor(P$conf_initial, lev))))
print(cal, row.names = FALSE)
cat("A benchmark using subject x confidence-level accuracy as the prior: see analysis/benchmark_confidence.py\n")
