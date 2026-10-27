# Conclusion (Phase 9 draft)

Every number below was reported in an earlier chapter and is collected in `notebooks/08_conclusion.ipynb`. "Operating companies" means companies with revenue of at least USD 10 million, the sample used for modelling.

## Financial health of the sector

Distress was common among U.S. semiconductor filers throughout 2015 to 2025, not a rare event:

- **Distress.** Each year, between 28.2% (2015) and 46.6% (2016) of operating companies had a Z' score below 1.23, with an average of 36.9%. The share peaked twice, in 2016 and in 2024 (44.3%), so there was no steady improvement or decline over the period.
- **Liquidity.** It weakened slowly: the median current ratio fell from 3.57 (2015) to 2.69 (2025), its lowest value.
- **Profitability.** It was thin and cyclical. The median net margin was best in 2021 (8.5%), turned negative in 2024 (-2.5%) and recovered only to 1.2% in 2025.
- **Losses.** The share of loss-making operating companies rose from 43.9% (2015) to 54.9% (2024).

So while a few large firms grew very fast, the typical company in the sector earned little, and roughly a third were in distress in any given year.

## Case companies

- **Nvidia grew.** Revenue rose from USD 5,010m to 215,938m and operating margin from 15% to 62% (2024). Its current ratio never fell below 2.57 and the model never rated it above 18% risk (highest 17.3%). Contrary to expectation, its Z' was in the grey zone in 2015 and 2020–2022. The cause was a large asset base relative to sales and the retirement of bought-back shares against retained earnings, not weakness.
- **AMD recovered.** It moved from negative equity in 2015 (USD -412m) and a Z' of -1.03 to a Z' above 1.23 from 2020 and a debt-to-equity of 0.22 in 2025. The 2022 Xilinx acquisition cut its ROA from 25% to 2% through the larger asset base, without any distress.
- **Intel declined.** Gross margin fell from 63% to 33% (2024), capital spending rose to 47% of revenue (2023), and it made a net loss of USD -18,756m in 2024. Interest coverage collapsed in 2022–2023, before the loss, and Z' fell below 1.23 from 2023.
- **Wolfspeed became distressed.** It made a loss in all 11 years and its Z' fell below 1.23 from 2020. Its debt ratio rose to 1.07 by 2025, and it filed for Chapter 11 on 30 June 2025, one day after its last fiscal year end. Its current ratio stayed above 3 until 2024, so liquidity gave no warning.

## Comparison of the algorithms

Four models were compared on the same test years (feature years 2023–2024, 134 company-years, 54 of them distressed next year), using the same metrics (Chapter 7).

| Model (test) | F1 | Recall | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- |
| Random forest (chosen on validation) | 0.779 | 0.815 | 0.895 | 0.883 |
| XGBoost | 0.765 | 0.722 | 0.894 | 0.878 |
| Logistic regression | 0.760 | 0.704 | 0.885 | 0.844 |
| Decision tree | 0.757 | 0.722 | 0.852 | 0.756 |
| Baseline: current ratio < 1 | 0.138 | 0.074 | 0.756 | 0.715 |
| Baseline: persistence (Z' < 1.23 now) | 0.846 | 0.815 | 0.953 | 0.939 |

- **The random forest performed best.** It had the highest validation PR-AUC (0.917), which was the selection rule, and it led every test metric except precision. The margin over the other models was small: test F1 ranged only from 0.757 to 0.779, and XGBoost's ROC-AUC (0.894) was almost equal. A plausible reason for the forest's edge is that distress depends on combinations of ratios, such as a weak margin together with high leverage. Tree ensembles capture these interactions without them being specified, and averaging many trees made the forest more stable than the single decision tree, whose PR-AUC fell from 0.860 on validation to 0.756 on test.
- **Against the current-ratio rule, the gain is large:** +0.641 F1 and +0.168 PR-AUC.
- **No model beat persistence,** the rule "distressed next year if Z' < 1.23 this year" (F1 0.846 against 0.779; ROC-AUC 0.953 against 0.895). Distress by Z' is highly persistent, and the ratios cannot fully rebuild the score, since retained earnings are not a model input.
- **The models' real value is early warning, but they caught only a few.** Of the 10 test cases that moved from healthy to distressed, the random forest and XGBoost flagged 3, logistic regression 2 and the decision tree 1. Persistence flags none of these by construction.
- **Out of sample, the forest held up.** Walk-forward predictions for 2018–2024 (469 company-years) reached ROC-AUC 0.922 and F1 0.800. For the four case companies, 25 of 28 years were classified correctly. All three errors fell at turning points: AMD 2018 and Intel 2022 were missed, and Wolfspeed 2018 was a false alarm.

## Answers to the research questions

1. **Which ratios best separate healthy from distressed companies?** Profitability, interest coverage and leverage did; liquidity did not. In the random forest, the largest SHAP shares were interest coverage (13.5%), operating margin (13.3%) and net margin (12.0%). Permutation importance ranked operating margin, debt-to-equity and debt ratio highest. A current ratio below 1 occurred in only 15 of 670 operating company-years.
2. **How did the four companies differ, and did the ratios show trouble early?** Nvidia grew, AMD recovered, Intel declined and Wolfspeed became distressed. Profitability and coverage warned early: five years before Wolfspeed's Z' crossed the cutoff, and one to two years before Intel's loss. Liquidity warned last or not at all.
3. **Which model predicts best, and is the gain over a simple baseline worth it?** The random forest predicted best, but only narrowly. It is far better than the current-ratio rule, yet worse than simply carrying forward this year's Z'. The added complexity pays off only for spotting companies that are healthy now and distressed next year, and there the models caught 3 of 10 at best.

## Practical meaning

For an analyst or investor, the results suggest four things:
- **Watch trends, not liquidity.** Follow the trend in operating margin and interest coverage rather than the current ratio, which stayed comfortable at Wolfspeed until the year it filed for Chapter 11.
- **Use Z' as a quick screen, with care.** This year's Z' is a strong guide to next year's, but it understates healthy firms that buy back shares heavily (Nvidia) or have just made a large acquisition (AMD).
- **Use the model probability as a second opinion,** for companies that are not yet distressed: a rising probability, as for Intel from 28% (2022) to 67% (2023), is worth a closer look.
- **Expect missed turning points.** No ratio-based model here anticipated most turning points.
