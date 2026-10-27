# References (running list)

Every source used in the project, with the phase where it was used. Journal entries were checked against Crossref (DOI metadata) or the publisher's page on 28 Oct 2026; books against library catalogue records. Access dates are when the source was used. The numbered list in the final report (`report/final/SemiFin_report.md`) is built from this file.

## Data sources

1. U.S. Securities and Exchange Commission. *Financial Statement Data Sets* (quarterly files 2014 Q3 to 2026 Q3). https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets (accessed 27 Oct 2026). Phase 1: all company filings and reported values.
2. U.S. Securities and Exchange Commission. *Financial Statement Data Sets: readme* (`readme.htm` inside each quarterly zip). Phases 1 and 2: field definitions of `sub` and `num` (`period`/`ddate` rounding, `segments`, `coreg`, unscaled `value`, primary-statement facts only).
3. U.S. Securities and Exchange Commission. *XBRL company facts API* (`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`), CIKs 1045810, 2488, 50863 and 895419. https://data.sec.gov/api/xbrl/companyfacts/ (accessed 27 Oct 2026). Phase 2: interest expense disclosed only in the notes (Intel 2014–2025, Wolfspeed 2020–2024).
4. U.S. Securities and Exchange Commission. *EDGAR filing archives*, rendered financial statements of the case-company 10-K filings (accessed 27 Oct 2026). Phase 3 verification:
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

5. Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. *The Journal of Finance*, 23(4), 589–609. https://doi.org/10.1111/j.1540-6261.1968.tb00843.x. Original Z-score model.
6. Altman, E. I. (1983). *Corporate Financial Distress: A Complete Guide to Predicting, Avoiding, and Dealing with Bankruptcy*. New York: Wiley. ISBN 0471087076. Source of the Z' model for firms without market prices. The book's text was not available; the Z' coefficients and cutoffs used were taken from secondary sources 11–14, which agree on the coefficients and the 1.23 cutoff and differ on the upper cutoff (2.90 or 2.99; 2.90 used, as in the project guide).
7. Beaver, W. H. (1966). Financial ratios as predictors of failure. *Journal of Accounting Research*, 4 (Empirical Research in Accounting: Selected Studies 1966), 71–111. https://doi.org/10.2307/2490171. Literature review.
8. Ohlson, J. A. (1980). Financial ratios and the probabilistic prediction of bankruptcy. *Journal of Accounting Research*, 18(1), 109–131. https://doi.org/10.2307/2490395. Literature review.
9. Standard & Poor's (2003). *Compustat North America User's Guide*, Chapter 5 "Data Definitions", "Fiscal Year-end Month of Data", pp. 118–119 (August 2003). Copy hosted by the University of Michigan: https://leiq.bus.umich.edu/docs/Fiscal%20Year-end%20Month%20of%20Data.pdf (accessed 28 Oct 2026). States that fiscal years ending 1 January to 31 May are treated as ending in the prior calendar year; basis of the `label_year` rule.
10. Financial Accounting Standards Board (2014). *Accounting Standards Update 2014-09, Revenue from Contracts with Customers (Topic 606)*; effective date deferred by *ASU 2015-14* (2015) to annual periods beginning after 15 December 2017 for public business entities. Summary used: Deloitte IAS Plus, "FASB issues ASU to defer the effective date of the new revenue standard", https://www.iasplus.com/en/publications/us/aje/2015/0813 (accessed 28 Oct 2026). Explains the 2018 switch to the `RevenueFromContractWithCustomer…` revenue tags (Phase 2).

## Web sources consulted

11. Calculate.co.nz. *Altman Z-Score Calculator*. https://www.calculate.co.nz/altman-z-score-calculator.php (accessed 27 Oct 2026). Phase 4: cross-check of Z' coefficients and cutoffs.
12. Strategic CFO. *Z Score Model*. https://strategiccfo.com/z-score-model/ (accessed 27 Oct 2026). Phase 4: private-firm model (book equity in X4); gives an upper cutoff of 2.99.
13. MetricGate. *Altman Z-Score*. https://metricgate.com/docs/altman-z-score/ (accessed 27 Oct 2026). Phase 4: cross-check of the Z' formula.
14. TrueData. *Altman Z-Score formula, calculation and meaning*. https://www.truedata.in/blog/altman-z-score-formula-calculation-meaning (accessed 27 Oct 2026). Phase 4: cross-check of the zones.

## Software

15. Python 3.12; pandas, NumPy, scikit-learn, matplotlib, seaborn, XGBoost, imbalanced-learn, SHAP, Jupyter, pyarrow, Beautiful Soup. Exact versions are in `requirements.txt`.

## Course resources (from the project guide)

16. 365 Financial Analyst learning path. https://learn.365financialanalyst.com/my-learning-path/. Ratio formulas and their interpretation.
17. Kbod999. *fintech-fraud-analytics* notebooks (GitHub). https://github.com/Kbod999/fintech-fraud-analytics/tree/main/notebooks. Model for the notebook structure.

## Modelling methods and software (Phase 5)

18. Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html. Logistic regression, decision tree, random forest, imputation, scaling, metrics, permutation importance.
19. Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794). https://doi.org/10.1145/2939672.2939785. Gradient boosting model.
20. Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324. Best-performing model.
21. Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In *Advances in Neural Information Processing Systems 30 (NIPS 2017)*. https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html. SHAP values.
22. scikit-learn developers. *Permutation feature importance* (user guide). https://scikit-learn.org/stable/modules/permutation_importance.html (accessed 27 Oct 2026). Permutation importance method.

## Figures (Phase 6)

23. Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90–95. https://doi.org/10.1109/MCSE.2007.55. All 13 report figures.
24. Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology*, 15(1), 72–101. https://doi.org/10.2307/1412159. Rank correlation (Figure 9).

Note: company colours were checked for colour-blind readability with a palette validator used during the work; it is a tool, not a published source.

## Dashboard (Phase 7)

25. Microsoft. *Power BI Desktop* (software). https://www.microsoft.com/power-platform/products/power-bi/desktop (accessed 28 Oct 2026). Four-page dashboard (`dashboard/SemiFin.pbix`).

## Case studies (Phase 8)

26. Wolfspeed, Inc. (2025). *Form 10-K for the fiscal year ended June 29, 2025*, Note 2 "Basis of Presentation and Summary of Significant Accounting Policies" and "Subsequent Events". SEC EDGAR, accession 0000895419-25-000110. https://www.sec.gov/Archives/edgar/data/895419/000089541925000110/R10.htm (accessed 28 Oct 2026). Chapter 11 petition date and borrowings presented as current.
27. Wolfspeed, Inc. (2026). *Form 10-K for the fiscal year ended June 28, 2026*, basis of presentation, "Emergence from Voluntary Reorganization under Chapter 11" and "Fresh Start Accounting". SEC EDGAR, accession 0000895419-26-000054. https://www.sec.gov/Archives/edgar/data/895419/000089541926000054/R11.htm (accessed 28 Oct 2026). Emergence date and fresh-start accounting.
28. Cash flow statements and balance sheets of the Nvidia, AMD, Intel and Wolfspeed 10-K filings for label years 2017, 2022 and 2024 (EDGAR rendered statements); links in `data/processed/case_extra_verification.csv` (accessed 28 Oct 2026). Verification of capex, buybacks and goodwill.
29. Soliman, M. T. (2008). The use of DuPont analysis by market participants. *The Accounting Review*, 83(3), 823–853. https://doi.org/10.2308/accr.2008.83.3.823. DuPont analysis (profit margin × asset turnover). The three-factor ROE identity used here (net margin × asset turnover × equity multiplier) is an algebraic identity.

## Literature review (final report)

30. Zmijewski, M. E. (1984). Methodological issues related to the estimation of financial distress prediction models. *Journal of Accounting Research*, 22 (Supplement), 59–82. https://doi.org/10.2307/2490859.
31. Shumway, T. (2001). Forecasting bankruptcy more accurately: A simple hazard model. *The Journal of Business*, 74(1), 101–124. https://doi.org/10.1086/209665.
32. Barboza, F., Kimura, H., & Altman, E. (2017). Machine learning models and bankruptcy prediction. *Expert Systems with Applications*, 83, 405–417. https://doi.org/10.1016/j.eswa.2017.04.006.
