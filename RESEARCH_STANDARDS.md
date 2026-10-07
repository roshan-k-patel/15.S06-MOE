# Research Standards: Expert Models (15.S06 "Which Expert, When?")

**Read this before building, training, or evaluating any expert model.** Every teammate (and every
coding assistant working for a teammate) must follow this spec exactly, so that expert results are
directly comparable. If something here is ambiguous, ask the group and update this file. Do not
improvise a local variant.

Version: 1.2 (output paths aligned with the repo structure in README.md). Changes to this file require group agreement and a version bump.

---

## 1. Data

| Item | Standard |
|---|---|
| Source | JKP global factor panel, `contrib.global_factor` on WRDS, downloaded with `scripts/get_jkp_us.py` |
| Country / screens | `excntry = 'USA'`, `common = 1`, `exch_main = 1`, `primary_sec = 1`, `obs_main = 1` |
| Sample start | Formation month 1990-01 |
| Universe | Each formation month *t*: the 2,000 largest stocks by `me` (market cap at *t*), among stocks with non-missing `me` |
| Characteristics | The 153 JKP characteristics in `data/raw/theme_map.csv` |
| Themes | The 13 JKP clusters in `theme_map.csv` (column `cluster`) |
| Target | `ret_exc_lead1m`: excess return from end of month *t* to end of month *t*+1 |
| Dtypes | Cast `me` and `ret_exc_lead1m` to `float64` and characteristics to `float32` immediately after loading (WRDS returns nullable dtypes that break arithmetic) |

Record the last formation month in your data (`max(eom)`) in every results file.

## 2. Timing convention

- All inputs for a prediction at formation month *t* must be known at the end of month *t*.
  JKP characteristics satisfy this (accounting data is lagged by JKP).
- A prediction made at *t* is evaluated against `ret_exc_lead1m` at *t*, i.e. the return earned during *t*+1.
- When plotting returns over time, label them with the month they are earned (*t*+1).

## 3. Timeline (fixed for the whole project)

| Period (formation months) | Role | Who may look at results |
|---|---|---|
| 1990-01 to 2000-12 | Initial training data only | — |
| 2001-01 to 2005-12 | Initial validation block | — |
| **2006-01 to 2015-12** | **Expert development / evaluation window.** Expert OOS predictions; gate training (2006–2012) and gate validation (2013–2015) | Everyone |
| 2016-01 to 2020-12 | Gate test. Expert OOS predictions are produced but **not evaluated during expert development** | Only when testing the gate |
| 2021-01 to latest | **Final holdout.** Touched once, at the end, with every design choice frozen | Nobody until the final run |

Rules:
- Expert design decisions (features, model class, grid) may only use results from 2006–2015.
- Experts **still produce predictions for every year 2006 → latest**; the cutoffs restrict what
  humans look at, not what models are trained on.
- Evaluation code must refuse to report metrics on formation months ≥ 2016-01 unless called with an
  explicit `gate_test=True`, and on months ≥ 2021-01 unless `final=True`.

## 4. Training procedure: annual expanding-window refits

For each **prediction year Y** from 2006 to the last year in the data:

1. **Label cutoff.** Use only formation months ≤ **November of Y−1**. (The November Y−1 label is the
   December return, known at the end of Y−1. December Y−1's label is the January Y return, not yet known.)
2. **Train block:** formation months 1990-01 to December of Y−6.
3. **Validation block:** formation months January of Y−5 to November of Y−1 (five years).
4. **Tune:** fit every grid configuration on the train block and score it on the validation block
   (see §6). Pick the best.
5. **Refit** the chosen configuration on train + validation (1990-01 to November Y−1). If the model
   uses early stopping, use the number of iterations chosen on validation; do not early-stop on data
   you are training on.
6. **Predict** formation months January to December of Y. Save the predictions (§8).

Example: prediction year 2006 trains on 1990-01 to 2000-12, validates on 2001-01 to 2005-11,
refits on 1990-01 to 2005-11, and predicts 2006-01 to 2006-12.

This produces genuinely out-of-sample predictions for every month from 2006 onward. Never train,
tune, or normalize using any data from the prediction year or later.

## 5. Features and training target

**Features (identical preprocessing for everyone):**
- Each formation month *t*, within the universe: rank each characteristic cross-sectionally
  (`rank(pct=True)`), subtract 0.5 to centre it in [−0.5, 0.5], multiply by the characteristic's JKP
  `direction` (so higher = higher expected return), and set missing values to 0.
- **An expert may use only its own theme's characteristics.** Transformations and interactions
  *within* the theme are allowed. Characteristics from other themes, gate state variables (unless they
  belong to the theme), and external data are not allowed.
- Optional: one extra feature per theme, the share of that theme's characteristics missing for the
  stock at *t*.

**Training target:** `ret_exc_lead1m`, winsorized within each formation month at the 1st and 99th
percentiles. Winsorize for training only; all evaluation uses the raw, unwinsorized return.

**Training weights:** every stock-month counts equally.

## 6. Shared hyperparameter tuning procedure

- **Selection metric:** mean monthly Spearman rank IC on the validation block (§7.1).
- **Grid:** at most 20 configurations per model class, written down in the run's config file
  *before* running. The same grid is used for every prediction year and every theme.
- **Re-tune every prediction year** using that year's validation block.
- Fix all random seeds (`seed = 42`). Results must be reproducible.
- Save the chosen configuration for every prediction year.

**Ridge grid (required baseline):** alpha ∈ {0.1, 1, 10, 100, 1,000, 10,000}.

## 7. Evaluation metrics

Unless stated otherwise, compute everything on the 2006-01 to 2015-12 development window, and also
separately for 2006–2010 and 2011–2015.

### 7.1 Out-of-sample rank IC
- Each formation month *t*: IC_t = Spearman correlation between the prediction and `ret_exc_lead1m`
  across universe stocks with a non-missing return.
- Report: mean IC; IC t-stat = mean / std × √(number of months); annualized IC information ratio =
  mean / std × √12; and % of months with IC > 0.

### 7.2 Long-short portfolios (evaluation only)
These portfolios exist only to evaluate and visualize a set of predictions. They are **not** inputs
to the gate: the gate uses every stock's `pred_z` (§8), not portfolio membership.

Built each formation month *t*, held for month *t*+1, rebalanced monthly.

1. Rank stocks in the universe by prediction: `pct = rank(pct=True, method="first")`.
2. Report **both** portfolio types for every model:
   - **Decile:** long leg = stocks with pct > 0.9 (top 10%, ~200 stocks); short leg = stocks with
     pct ≤ 0.1 (bottom 10%). Tests how well the model identifies the extremes.
   - **Tercile:** long leg = pct > 2/3 (top third, ~667 stocks); short leg = pct ≤ 1/3 (bottom third).
     Matches the JKP factor construction and is more diversified, with lower turnover.
3. Weights within each leg, two versions (report both, for both portfolio types):
   - **Capped value-weighted:** cap_i = min(me_i, q80_t), where q80_t is the 80th percentile
     of `me` across the universe at *t*; w_i = cap_i / Σ cap within the leg.
   - **Equal-weighted:** w_i = 1 / (number of stocks in the leg).
4. Stocks with a missing `ret_exc_lead1m` are dropped from the leg and the remaining weights renormalized.
5. Long-short return: r_LS = Σ_long w_i r_i − Σ_short w_i r_i.
6. Report: annualized mean (×12), annualized volatility (×√12), Sharpe = mean / std × √12,
   t-stat = mean / std × √(months), and maximum drawdown of the cumulative (summed) return.
   That is four portfolios per model: {decile, tercile} × {capped value-weighted, equal-weighted}.

### 7.3 Turnover and costs
Compute separately for each of the four portfolios in §7.2.
- Drifted weights before rebalancing: w̃_i = w_i,t−1 × (1 + r_i) / Σ_j w_j,t−1 × (1 + r_j), within each leg.
- Traded amount at *t*: T_t = Σ_long |w_i,t − w̃_i| + Σ_short |w_i,t − w̃_i| (ranges 0 to 4).
- Report mean monthly turnover = mean(T_t) / 2.
- **Net return:** r_net,t = r_LS,t − c × T_t, with **c = 10 bps (0.0010) per dollar traded**.
  Report the net Sharpe ratio.
- Report the break-even cost: c* = mean(r_LS) / mean(T).

### 7.4 Out-of-sample R² (Gu, Kelly & Xiu 2020)
- R²_oos = 1 − Σ (r_i,t − r̂_i,t)² / Σ r_i,t², summed over all stock-months in the window, using raw
  `ret_exc_lead1m` and raw (un-standardized) predictions. The benchmark is a forecast of zero, not
  the historical mean.
- Expect values near zero or negative for large-cap stocks; report them anyway.

## 8. Saving predictions and results

Every model run writes to its own folder, `outputs/runs/<YYYY-MM-DD>_<theme_slug>_<model_name>_v<N>/`
(matching the `outputs/runs/<date>_<name>/` convention in `README.md`):

| File | Contents |
|---|---|
| `predictions.parquet` | Columns: `id`, `eom`, `theme`, `model`, `pred_raw`, `pred_z`, `pred_year` |
| `metrics.csv` | Every metric in §7, one row per window (2006–2010, 2011–2015, 2006–2015) |
| `hparams.csv` | Chosen configuration for each prediction year |
| `config.yaml` | Features used, model class, grid, seed, data `max(eom)`, standards version |
| `README.md` | One paragraph describing the expert and any deviations (there should be none) |

- `pred_z` = prediction standardized within each formation month: (pred − mean_t) / std_t, clipped
  to [−3, 3] (set to 0 if std_t = 0). **The gate always uses `pred_z`**, so no expert dominates
  because of output scale.
- **The gate's input is the full cross-section:** `pred_z` for every universe stock in every month,
  from all 13 experts. Portfolio membership (deciles, terciles) is never passed to the gate.
- Predictions cover every universe stock-month from 2006-01 to the latest month.
- `theme_slug` is the lower-case theme name with underscores, e.g. `short_term_reversal`.
- Shared code lives in `src/moe/` and scripts in `scripts/` (see `README.md`). Use the environment
  from `uv sync`; add new dependencies with `uv add <package>` so everyone stays on the same versions.
- `predictions.parquet` files are not committed to git; share them via the group drive. Commit
  `metrics.csv`, `hparams.csv`, `config.yaml`, and `README.md` for every run.

## 9. Required baselines for every theme

Each expert submission reports three rows side by side, all evaluated identically:

1. **Naive:** equal-weighted average of the theme's signed ranks (no fitting).
2. **Ridge:** linear ridge regression on the theme's features, tuned per §6.
3. **Candidate model(s):** your expert (e.g. LightGBM, small neural net).

A candidate counts as an improvement only if it beats both baselines on mean rank IC over 2006–2015.

## 10. Do not

- Look at any metric for 2016-01 or later during expert development.
- Tune on test years, or choose features based on their test performance.
- Use characteristics from other themes inside an expert.
- Normalize, winsorize, or rank using data from future months, or across months.
- Change the universe, timeline, portfolio construction, cost assumption, or metric definitions
  without updating this file for everyone.
