# Step 13. Matched adoption with a random intercept for each decision (rows from one decision are correlated). Usage: Rscript e2_trial_cluster.R <replication data folder>
suppressMessages({library(lme4); library(emmeans)})
args <- commandArgs(TRUE); D <- if (length(args)) args[1] else "data"
t <- read.csv(file.path(D, "trials.csv"), colClasses = "character")
M <- c(gpt4o="ans_gpt4o", claude="ans_claude", llama="ans_llama")
rows <- list()
for (m in names(M)) {
  a <- t[[M[m]]]
  on <- ifelse(t$n_models_shown=="3", TRUE, a==t$single_model_answer)
  k <- a!=t$key & a!="X" & t$initial_answer!=a & on
  rows[[m]] <- data.frame(participant=t$participant[k], item=t$item[k], model=m, study=t$study[k],
                          n_models=t$n_models_shown[k], adopt=as.integer(t$final_answer[k]==a[k]))
}
e <- do.call(rbind, rows); e$trial <- paste(e$participant, e$item); e$im <- paste(e$item, e$model)
cat("rows", nrow(e), " trials", length(unique(e$trial)), "\n")
f0 <- glmer(adopt ~ n_models*study + model + (1|participant) + (1|im), e, binomial, control=glmerControl(optimizer="bobyqa"))
f1 <- glmer(adopt ~ n_models*study + model + (1|participant) + (1|im) + (1|trial), e, binomial, control=glmerControl(optimizer="bobyqa"))
for (f in list(original=f0, trial_cluster=f1)) {
  em <- emmeans(f, ~ n_models, regrid="response"); print(confint(pairs(em, reverse=TRUE))); print(test(pairs(em, reverse=TRUE)))
}
print(VarCorr(f1)); print(anova(f0, f1))
