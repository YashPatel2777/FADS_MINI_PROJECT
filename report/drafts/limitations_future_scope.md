# Limitations and future scope (Phase 9 draft)

Numbers are from `notebooks/08_conclusion.ipynb` and the data log (`docs/data_log.md`).

## Limitations

1. **Fiscal year alignment is approximate.** Of the 925 company-years, 563 end in December. The rest, including Nvidia (January) and Wolfspeed (June), were mapped to the nearest calendar year by the Compustat convention, so their "year" can be up to about six months out of step with December filers. The optional check that reruns the comparison with the SEC's own fiscal-year field was not done, so the effect of this choice is stated, not measured.
2. **Small evaluation sets make the metrics unstable.** The test years contain 134 company-years, 54 of them distressed next year, and only 10 healthy-to-distressed transitions. Each transition is worth 10 percentage points of early-warning recall, so the gaps between models (test F1 0.757 to 0.779) are within what one or two cases could change. The case-company check rests on 28 company-years.
3. **XBRL tags are inconsistent.**
   - **Fallback tags.** 15.1% of statement values came from a fallback tag rather than the first-choice one. For revenue this is mostly the post-2018 standard tag under ASC 606 (405 of 639 cases).
   - **Derived values.** Total liabilities were derived for 165 company-years, including AMD, Intel and Wolfspeed, which never report a total.
   - **Interest proxy.** Interest coverage uses cash interest paid as a substitute for interest expense in 165 company-years.
   - **Custom tags.** Nvidia's capex used a company-specific tag before 2023.
4. **The label is a score, not an event.** The models learn to predict Z' < 1.23, not bankruptcy. This has three consequences:
   - **Persistence is hard to beat.** Z' is persistent, which is why the persistence baseline beat every model.
   - **Accounting effects.** Z' also moves for accounting reasons: Nvidia's retired treasury stock lowered its retained earnings, and AMD's Xilinx acquisition lowered its asset turnover.
   - **Grey-zone choice.** Treating the grey zone as healthy was a choice; counting it as distressed would add 266 positive cases.
   - **Coefficients and cutoff.** The coefficients were estimated by Altman on manufacturing firms, not semiconductor firms, and the upper cutoff appears as 2.90 or 2.99 in different sources.
5. **Book values ignore the market.** The data has no share prices, so market value, volatility and investors' expectations are missing. This is also why the book-equity version of the score (Z') was used instead of Altman's original market-value Z.
6. **Restructured companies break the series.** Wolfspeed's fiscal 2026 accounts use fresh-start accounting as a new reporting entity, so its series ends at 2025. Its last year is the Chapter 11 year itself, when borrowings were presented as current.
7. **The sample is narrow.**
   - **Sector and filers.** Results apply to U.S. 10-K filers in SIC 3674 only. Foreign issuers filing 20-F (266 filings) were excluded.
   - **Small companies.** Companies with revenue below USD 10 million (79 labelled rows) were left out of modelling.
   - **Alternative label.** The stricter robustness label (net loss, weak coverage and a current ratio below 1 together) had only 29 positives and could not be modelled.

   The findings should not be generalised to other sectors.

## Future scope

1. **Market-based features:** stock returns, volatility and market capitalisation, which would also allow the original market-value Z-score.
2. **Event-based labels:** use actual bankruptcy, delisting or debt-default events (for example, Wolfspeed's Chapter 11 filing) instead of a score, so the models predict failure rather than Z'.
3. **Quarterly data:** quarterly 10-Q statements could give earlier warnings, since Intel's coverage and margins fell within a year. Other sub-sectors or foreign filers could be added for a larger sample.
4. **Trend features:** two- or three-year changes in operating margin and interest coverage, since the case studies show the direction of these ratios warned earlier than their level.
5. **Text features:** management's discussion and risk-factor sections of the 10-K, where going-concern doubts and refinancing risks are stated in words before they show in the ratios.
6. **Explainability and fairness:** SHAP is already used for the random forest. It could be extended to per-company explanations, together with a fairness check across company size, so small firms are not flagged mainly for being small (log total assets is among the top features by permutation). This connects to the Data Ethics course.
7. **The untested alignment check:** rerun the headline comparison with the SEC fiscal-year field to measure the effect of the year-alignment rule.
