# Project 5 concepts glossary

Plain-language definitions for "Which Expert, When? Alpha Models Across Market Regimes".
Starred items (★) are the core minimum.

## Finance

- ★ **Excess return**: the return minus the risk-free (T-bill) rate. JKP returns are already excess returns.
- ★ **Factor (long-short portfolio)**: buy stocks that score high on a signal and short stocks that score low. The return measures the signal itself, separate from the market's moves.
- ★ **Anomaly**: a signal that past research found predicts returns (value, momentum, accruals, ...). Each of the 153 JKP factors comes from one published paper.
- ★ **Sharpe ratio**: average return divided by volatility, usually annualised. The main scorecard.
- **Alpha**: return left over after accounting for exposure to the market or other factors.
- **Theme (JKP)**: one of 13 groups of related factors. The theme return is the equal-weighted average of its factors. Nothing in it is estimated.
- **Factor timing**: changing factor weights over time rather than holding them fixed. This project is a form of factor timing.
- **Regime**: a persistent market environment, such as calm vs stressed, or expansion vs recession.
- **State variables**: numbers describing today's environment, known at the time: VIX, realised market volatility, credit spread, term spread, T-bill rate, aggregate valuation.
- **Turnover and trading costs**: how much the portfolio changes each month, and what that change costs.

## Machine learning

- ★ **Mixture of experts (MoE)**: several specialist models (experts) plus a gate that decides how much to trust each one.
- ★ **Expert**: in this project, one JKP theme. In the basic version an expert is just the theme's return series. In richer versions it is a model trained on that theme's signals.
- ★ **Gate**: a small model that takes the state variables and outputs one weight per expert.
- ★ **Softmax**: the function that turns the gate's scores into weights that are positive and sum to 1.
- ★ **Overfitting**: fitting noise in past data. The model looks good in-sample and fails out-of-sample. The biggest risk in this project, because there are only a few hundred months of data.
- **Regularisation (ridge, shrinkage)**: penalising large coefficients to reduce overfitting.
- **Loss function**: what training minimises, for example forecast error or negative Sharpe ratio.
- **Soft vs hard routing**: soft routing blends all experts; hard routing picks one (or a few).
- **Expert collapse**: the gate puts nearly all weight on one expert. This can be a real result or a training failure.

## Evaluation

- ★ **Out-of-sample testing**: judging the model only on data it never saw during training.
- ★ **Look-ahead bias**: using information that was not available at the time, such as revised macro data, NBER recession dates, or full-sample statistics.
- ★ **Walk-forward (rolling) validation**: train on the past, test on the next period, roll forward and repeat. Never shuffle months.
- **Benchmarks**: equal weighting of the 13 themes (hard to beat), factor momentum (weight recent winners), buy-and-hold.
- **Multiple testing**: if you try enough variations, one will look good by chance. Decide the main test before running it.

## Statistics for the benchmarks

- **Predictive regression**: regress next month's return on variables known today. The building block for experts and gates.
- **Bayesian model averaging (BMA)**: weight each model by how strongly the data supports it (Avramov 2002).
- **Hidden Markov / regime-switching model**: infers unobserved regimes from the data and gives the probability of being in each one (Ang & Timmermann 2012). Use filtered probabilities only, never smoothed ones, to avoid look-ahead.

## Reading order (about 4 hours)

1. Jacobs, Jordan, Nowlan & Hinton (1991), "Adaptive Mixtures of Local Experts": what experts and gates are.
2. Ang & Timmermann (2012), "Regime Changes and Financial Markets": why one fixed model is fragile.
3. Avramov (2002), "Stock Return Predictability and Model Uncertainty": why averaging models helps.
4. Jensen, Kelly & Pedersen (2023), "Is There a Replication Crisis in Finance?", introduction only: what factors and themes are.
5. Daniel & Moskowitz (2016), "Momentum Crashes", introduction only: a clear example of a factor failing in one regime.
