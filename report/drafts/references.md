# References (running list)

Every source used in the project, added in the phase where it was used. Before the final report, format these in one citation style and check each entry marked **verify** against the primary source. Access dates are when the source was used.

## Data sources

1. U.S. Securities and Exchange Commission. *Financial Statement Data Sets* (quarterly files 2014 Q3 to 2026 Q3). https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets (accessed 27 Oct 2026). Used in Phase 1 for all company filings and reported values.
2. U.S. Securities and Exchange Commission. *Financial Statement Data Sets: readme* (`readme.htm` inside each quarterly zip). Used in Phases 1 and 2 to confirm the field definitions of `sub` and `num` (rounding of `period`/`ddate` to month-end, `segments`, `coreg`, unscaled `value`, and the fact that `num` covers primary-statement facts only).
3. U.S. Securities and Exchange Commission. *XBRL company facts API* (`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`), for CIKs 1045810, 2488, 50863 and 895419. https://data.sec.gov/api/xbrl/companyfacts/ (accessed 27 Oct 2026). Used in Phase 2 to fill interest expense disclosed only in the notes (Intel 2014 to 2025, Wolfspeed 2020 to 2024).
4. U.S. Securities and Exchange Commission. *EDGAR filing archives*, rendered financial statements of the case-company 10-K filings (accessed 27 Oct 2026). Used in Phase 3 to check computed values:
   - NVIDIA Corp., 10-K for fiscal year ended Jan 2018 (label year 2017): https://www.sec.gov/Archives/edgar/data/1045810/000104581018000010/
   - NVIDIA Corp., 10-K for fiscal year ended Jan 2025 (label year 2024): https://www.sec.gov/Archives/edgar/data/1045810/000104581025000023/
   - Advanced Micro Devices, Inc., 10-K for 2017: https://www.sec.gov/Archives/edgar/data/2488/000000248818000042/
   - Advanced Micro Devices, Inc., 10-K for 2024: https://www.sec.gov/Archives/edgar/data/2488/000000248825000012/
   - Intel Corp., 10-K for 2017: https://www.sec.gov/Archives/edgar/data/50863/000005086318000007/
   - Intel Corp., 10-K for 2024: https://www.sec.gov/Archives/edgar/data/50863/000005086325000009/
   - Cree, Inc. (now Wolfspeed, Inc.), 10-K for fiscal year ended Jun 2017: https://www.sec.gov/Archives/edgar/data/895419/000089541917000055/
   - Wolfspeed, Inc., 10-K for fiscal year ended Jun 2024: https://www.sec.gov/Archives/edgar/data/895419/000089541924000062/
   - Wolfspeed, Inc., 10-K for fiscal year ended Jun 2025: https://www.sec.gov/Archives/edgar/data/895419/000089541925000110/

## Methods and definitions

5. Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. *Journal of Finance*. **Verify** volume, issue and pages. Original Z-score model.
6. Altman, E. I. (1983). *Corporate Financial Distress*. Wiley. **Verify**. Cited in the project guide as the source of the Z' model for firms without market prices. Use it to confirm the coefficients and the 1.23 / 2.90 cutoffs, because web sources differ on the upper cutoff (2.90 or 2.99).
7. Beaver, W. H. (1966). Financial ratios as predictors of failure. *Journal of Accounting Research*. **Verify**. Literature review.
8. Ohlson, J. A. (1980). Financial ratios and the probabilistic prediction of bankruptcy. *Journal of Accounting Research*. **Verify**. Literature review.
9. Compustat fiscal-year convention (fiscal years ending January to May assigned to the previous calendar year). Stated in the project guide as the basis of the `label_year` rule. **Verify** and cite S&P Global Market Intelligence Compustat documentation.
10. FASB Accounting Standards Codification Topic 606, *Revenue from Contracts with Customers* (effective 2018 for most public companies). **Verify**. Explains the switch from `SalesRevenueNet` to `RevenueFromContractWithCustomerExcludingAssessedTax` seen in 2018 (Phase 2).

## Web sources consulted

11. Calculate.co.nz. *Altman Z-Score Calculator*. https://www.calculate.co.nz/altman-z-score-calculator.php (accessed 27 Oct 2026). Used in Phase 4 to cross-check the Z' coefficients and cutoffs.
12. Strategic CFO. *Z Score Model*. https://strategiccfo.com/z-score-model/ (accessed 27 Oct 2026). Used in Phase 4: describes the private-firm model (book equity in X4) and gives an upper cutoff of 2.99.
13. MetricGate. *Altman Z-Score*. https://metricgate.com/docs/altman-z-score/ (accessed 27 Oct 2026). Used in Phase 4 to cross-check the Z' formula.
14. TrueData. *Altman Z-Score formula, calculation and meaning*. https://www.truedata.in/blog/altman-z-score-formula-calculation-meaning (accessed 27 Oct 2026). Used in Phase 4 to cross-check the zones.

## Software

15. Python 3.12; pandas, NumPy, scikit-learn, matplotlib, seaborn, XGBoost, imbalanced-learn, SHAP, Jupyter, pyarrow, Beautiful Soup. Exact versions are in the Phase 0 environment check and `requirements.txt`.

## Course resources (from the project guide)

16. 365 Financial Analyst learning path. https://learn.365financialanalyst.com/my-learning-path/. Used for ratio formulas and their interpretation.
17. Kbod999. *fintech-fraud-analytics* notebooks (GitHub). https://github.com/Kbod999/fintech-fraud-analytics/tree/main/notebooks. Used as a model for the notebook structure.

## Phase 4 additions

No new external sources; Phase 4 uses references 6 and 11 to 14 for the Z' model and cutoffs.
