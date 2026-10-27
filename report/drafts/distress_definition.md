# Definition of financial distress

## Primary label: Altman Z' score

Financial distress is defined with the Altman Z' score, the version of the Z-score for companies without market prices (Altman, 1983; see references 6 and 11 to 14). The original Z-score needs the market value of equity, which the SEC statement data does not contain. Z' uses the book value of equity instead.

Z' = 0.717 X1 + 0.847 X2 + 3.107 X3 + 0.420 X4 + 0.998 X5

| Term | Formula | Meaning |
| --- | --- | --- |
| X1 | (Current assets − Current liabilities) ÷ Total assets | Working capital relative to size |
| X2 | Retained earnings ÷ Total assets | Accumulated profitability (also reflects company age) |
| X3 | Operating income ÷ Total assets | Operating return on assets |
| X4 | Book value of equity ÷ Total liabilities | Solvency cushion |
| X5 | Revenue ÷ Total assets | Asset turnover |

| Z' range | Zone | Label |
| --- | --- | --- |
| Below 1.23 | Distress | 1 (distressed) |
| 1.23 to 2.90 | Grey | 0 (healthy) |
| 2.90 and above | Safe | 0 (healthy) |

Only scores below 1.23 count as distressed; the grey zone is treated as healthy. Z' is blank when any of its five inputs is missing, so those company-years receive no label (45 of 1,028). Some secondary sources give the safe-zone cutoff as 2.99 rather than 2.90; this affects only the grey/safe split shown in figures, not the label. The cutoffs and coefficients should be cited from the primary source.

## Prediction horizon

Features are the financial ratios of year t; the label is the company's Z' label in year t+1. The label is attached only when the following year is the next consecutive label year for that company. This makes the task a one-year-ahead early warning, not a description of the present.

Z' and its components X1 to X5 are used only to build the label and are never model inputs. Several input ratios are related to the components (operating income, revenue, liabilities and equity over assets), and distress persists from year to year: 269 of 305 distressed company-years remain distressed the next year. Feature importance is therefore checked for dominance by any single variable in the modelling phase. The 46 cases where a healthy company became distressed the next year are the true early-warning cases and are reported separately.

## Robustness label

As a second definition, a company-year is distressed if, in the same year, it has a net loss, interest coverage below 1.5 and a current ratio below 1. Missing inputs are handled with three-valued logic: a company with no interest expense (no debt) does not have weak coverage; the label is 1 only when all three conditions are known to hold, 0 when any known condition fails, and blank otherwise. This label is far rarer (36 of 925 company-years in 2015 to 2025, 29 of 749 one-year-ahead labels), and every company it flags is also distressed by Z'.

## Class balance (one-year-ahead primary label, feature years 2015 to 2024)

749 feature-years have a next-year label; 319 (43%) are distressed. The share ranges from 38% to 50% by year. Distress is concentrated among very small companies: excluding those with revenue below USD 10 million leaves 670 rows, of which 249 (37%) are distressed. Distress is therefore common in this sector sample rather than rare, and the class imbalance is mild. If the grey zone were counted as distressed, 266 further labels would change from 0 to 1.
