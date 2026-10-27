# Model results (Phase 5 draft)

All figures are from `notebooks/05_modelling.ipynb` (random seed 42). The task is to predict whether a company will be distressed next year (Altman Z' < 1.23 in year t+1) from its ratios in year t. Companies with revenue below USD 10 million are excluded. The split is by feature year: train 2015 to 2020 (397 rows, 38% distressed), validation 2021 to 2022 (139 rows, 31%) and test 2023 to 2024 (134 rows, 40%).

## Model comparison (test years 2023 to 2024)

| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- |
| Random forest (best on validation) | 0.746 | 0.815 | 0.779 | 0.895 | 0.883 |
| XGBoost | 0.812 | 0.722 | 0.765 | 0.894 | 0.878 |
| Logistic regression | 0.826 | 0.704 | 0.760 | 0.885 | 0.844 |
| Decision tree | 0.796 | 0.722 | 0.757 | 0.852 | 0.756 |
| Baseline: current ratio < 1 | 1.000 | 0.074 | 0.138 | 0.756 | 0.715 |
| Baseline: persistence (Z' < 1.23 this year) | 0.880 | 0.815 | 0.846 | 0.953 | 0.939 |

## Why the random forest won

The random forest had the highest validation PR-AUC (0.917, against 0.902 for XGBoost, 0.860 for the decision tree and 0.849 for logistic regression). On test it also had the highest recall (44 of 54 distressed companies) and PR-AUC. A plausible reason is that distress depends on combinations of ratios: for example, a weak margin matters more when leverage is already high. Tree ensembles capture these interactions without them being specified, and averaging many trees makes the forest more stable than a single tree. On ROC-AUC, the forest and XGBoost are almost equal (0.895 and 0.894), so the advantage is small.

## Where all models fail

1. **None beats persistence.** Predicting that a company distressed today stays distressed next year gives a higher F1 (0.846) and ROC-AUC (0.953) than every model. Distress by Z' is highly persistent: 269 of 305 distressed company-years stayed distressed. The models see only ratios, and none of the 18 features carries retained earnings, which is a large part of Z'. So the ratios cannot fully rebuild today's score.
2. **Early warnings are rare.** Ten test companies were healthy at t and distressed at t+1. The random forest and XGBoost flagged 3 of them, logistic regression 2 and the decision tree 1. Persistence and the current-ratio rule, by construction, flagged none. This is where the ratios add something over the score itself, but recall on these cases is low.
3. **The current-ratio rule is not a useful warning sign on its own.** It flagged only 4 of 54 distressed companies. Most distressed semiconductor companies keep a current ratio above 1 because they hold cash from equity raises.
4. **The decision tree generalised worst.** Its PR-AUC fell from 0.860 on validation to 0.756 on test.

## Leakage checks

- Test scores are not above validation scores for any model (random forest PR-AUC 0.917 on validation, 0.883 on test).
- No single feature dominates the forest. The largest share of mean |SHAP| is 13.5% (interest coverage), and the top three together account for 38.8%. By permutation importance the leading features are operating margin, debt-to-equity, debt ratio, size (log total assets), net margin and ROA.
- Z' and its components are not model inputs.

## Logistic regression coefficients

On standardised features, the strongest risk-reducing signs are ROA (−1.57), operating margin (−1.51), current ratio (−1.27) and size (−0.93). The strongest risk-raising sign is debt ratio (+1.41). Net margin (+1.06) and gross margin (+0.45) have counter-intuitive positive signs. This is most likely multicollinearity with operating margin and ROA, which carry the same information, so those individual coefficients should not be read on their own.

## Case companies (walk-forward, out of sample)

For each feature year from 2018 to 2025, the forest is trained only on earlier years and then predicts the following year. Across all companies, these out-of-sample predictions reach ROC-AUC 0.922 and F1 0.800.

| Feature year t | AMD | Intel | Nvidia | Wolfspeed |
| --- | --- | --- | --- | --- |
| 2018 | 0.35 (actual 1) | 0.14 | 0.15 | 0.78 (actual 0) |
| 2019 | 0.32 | 0.17 | 0.10 | 0.76 (actual 1) |
| 2020 | 0.11 | 0.18 | 0.07 | 0.73 (1) |
| 2021 | 0.07 | 0.13 | 0.12 | 0.94 (1) |
| 2022 | 0.11 | 0.28 (actual 1) | 0.17 | 0.83 (1) |
| 2023 | 0.14 | 0.67 (1) | 0.11 | 0.88 (1) |
| 2024 | 0.10 | 0.85 (1) | 0.09 | 0.84 (1) |
| 2025 (forecast for 2026) | 0.06 | 0.73 | 0.09 | 0.89 |

The decision threshold is 0.494. Probabilities are shown, with the actual t+1 label where the case is notable.

- **Nvidia:** low risk in every year, consistent with its labels.
- **Wolfspeed:** flagged from 2018, one year before Z' first fell below 1.23. That 2018 flag was a false positive against the 2019 label (its Z' was 1.50, in the grey zone).
- **Intel:** its probability rose from 0.28 (2022) to 0.67 (2023) and 0.85 (2024). The model missed Intel's first distressed year: 0.28 for 2022 was below the threshold. It caught 2023 and 2024.
- **AMD:** its last distressed year (label 2019, from feature year 2018) was missed, at a probability of 0.35.

## Robustness checks

- **Robustness label** (net loss, coverage < 1.5 and current ratio < 1): only 5 positives in train, 4 in validation and 2 in test. The test F1 of 0.15 is not meaningful. This label is too rare in the sample to model, which is itself a finding: only a handful of semiconductor companies meet all three conditions at once.
- **Low-revenue companies included:** on the same operating companies in test, F1 is 0.778 against 0.779 without them, so the conclusion does not change. Scored on all test rows including the very small companies, F1 rises to 0.820 because those companies are easy to classify. This is why they were excluded from the main results.
