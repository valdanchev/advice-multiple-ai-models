suppressPackageStartupMessages({library(lme4); library(emmeans); library(jsonlite)}); emm_options(lmer.df = "asymptotic")
d <- read.csv("analysis/d.csv", stringsAsFactors = FALSE, colClasses = c(item = "character")); dm <- read.csv("analysis/dm.csv", stringsAsFactors = FALSE, colClasses = c(item = "character"))
par <- fromJSON("analysis/params.json"); ctl <- glmerControl(optimizer = "bobyqa")
d$nl <- factor(ifelse(d$n_llm == 3, "three", "one")); dm$nl <- factor(ifelse(dm$n_llm == 3, "three", "one"))
cf <- c("3C","2C1W","1C2W-agree","1C2W-split","0C3W-agree","0C3W-2+1","0C3W-split")
nat <- rowMeans(sapply(par$config_freq, function(x) { v <- unlist(x)[cf]; v[is.na(v)] <- 0; v })); names(nat) <- cf
print(round(nat, 3))
# raw cell means (participant-weighted) by configuration, then reweighted; CI by participant bootstrap
cell <- function(x, y) tapply(x[[y]], list(x$config, x$nl), mean)
rw <- function(tab) { w <- nat[rownames(tab)]; w <- w / sum(w); colSums(tab * w) }
t1 <- cell(d, "final_correct"); t3 <- cell(dm, "adopt_m"); print(round(t1, 3)); print(round(t3, 3))
est <- c(acc = rw(t1), adopt = rw(t3[rownames(t3) %in% names(nat), , drop = FALSE]))
set.seed(1); ids <- unique(d$pid)
bs <- replicate(1000, { s <- sample(ids, replace = TRUE); dd <- d[match(s, d$pid) |> (\(i) unlist(lapply(s, function(p) which(d$pid == p))))(), ]
  mm <- dm[unlist(lapply(s, function(p) which(dm$pid == p))), ]; c(rw(cell(dd, "final_correct")), rw(cell(mm, "adopt_m"))) })
print(round(rbind(estimate = est, apply(bs, 1, quantile, c(.025, .975))), 3))
