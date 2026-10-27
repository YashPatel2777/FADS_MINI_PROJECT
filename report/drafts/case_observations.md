# Case study observations (Phase 8 draft)

All numbers come from `notebooks/07_case_studies.ipynb` and the earlier phase outputs. Money is in USD millions and years are label years. Tables 8.1 to 8.6 are in the notebook and saved in `data/processed/`. The guide's expected patterns were hypotheses, and this section says where the data disagrees with them.

## Nvidia: growth (main case)

Nvidia is the clear growth case. Revenue rose from 5,010 in 2015 to 215,938 in 2025 (Figure 2), operating margin from 15% to 62% in 2024 (Figure 6), and ROE from 14% to 92% in 2024 (Figure 7). The rise was not smooth: operating margin dipped to 26% in 2019 and 16% in 2022, and the step change came in 2023 (revenue 60,922, operating margin 54%). Liquidity stayed strong, with a current ratio between 2.57 and 8.03 in every year (Figure 4).

**Contradiction.** The guide expected Z' to stay far above 2.90. It did not: Nvidia was in the grey zone in 2015, 2020, 2021 and 2022, with a low of 1.96 in 2022 (Figure 8). The Z' breakdown (notebook section 3) shows two causes, neither of them financial weakness:

- Revenue / total assets (X5) stayed below 1 until 2024, because Nvidia carries a large asset base relative to sales.
- Retained earnings fell while the company was profitable. Nvidia retired 12,026 of treasury stock (shares bought back in earlier years) against retained earnings in 2021, and buybacks of 10,039 in 2022 were also charged there. So the retained-earnings term (X2) fell from 0.80 in 2018 to 0.21 in 2022.

The book-value Z' therefore understates the health of a cash-rich firm that returns capital through buybacks.

**ROE and buybacks: partly supported.** The DuPont breakdown for 2024 is net margin 0.56 × asset turnover 1.17 × equity multiplier 1.41 = ROE 0.92. The multiplier stayed between 1.31 and 1.86, so the high ROE comes from profit, not from a thin equity base. Buybacks were large (33,706 in 2024, 46% of net income), but equity still grew from 42,978 to 79,327.

**Model.** The walk-forward probability stayed between 7% and 17% and was correct (healthy) in every year from 2018 to 2024 (Figure 13, Table 8.3).

## AMD: turnaround

AMD matches the turnaround hypothesis:

- **Weak start.** It lost money in 2015 and 2016 (-660 and -497), had negative equity in 2015 (-412) and a debt-to-equity of 6.98 in 2016, and started with a Z' of -1.03 (Figures 3, 5 and 8).
- **Recovery.** Z' stayed just below the cutoff in 2019 (1.08), then rose above it in 2020 (2.21) and stayed in the grey zone or above. ROA reached 28% in 2020, and revenue grew from 4,272 (2016) to 34,639 (2025) while debt-to-equity fell to 0.22.

**Xilinx, 2022: supported.** The acquisition raised total assets from 12,419 to 67,580 and goodwill from 289 to 24,177. Asset turnover fell from 1.32 to 0.35 and ROA from 25% to 2% (Figure 7). Z' fell from 3.02 to 2.29 through the asset-turnover term alone. This is an accounting effect of the larger asset base, not distress.

**Model.** The 2018 data gave a probability of 35%, below the 0.494 threshold, but AMD's Z' in 2019 was 1.08, so this early warning was **missed**. From the 2019 data onward, the model correctly rated AMD healthy (Table 8.3).

## Intel: decline

Intel matches most of the decline hypothesis:

- **Margins.** Gross margin fell from 63% (2015) to 33% (2024). Operating margin fell from 25% (2021) to 4% (2022) and -22% (2024) (Figure 6).
- **Loss.** Net income turned to a loss of -18,756 in 2024 and -267 in 2025 (Figure 3).
- **Capital spending.** Capex rose from 7,326 (13% of revenue, 2015) to 25,750 (47% of revenue, 2023), while revenue fell from 79,024 (2021) to 54,228 (2023). Buybacks stopped (0 in 2022–2023). These capex and buyback values were checked against the 10-K cash flow statements (32 of 32 extra values match).

**Rising liabilities: partly supported.** Total liabilities rose from 41,083 to 91,453 (2024), but the debt ratio stayed between 0.40 and 0.47 because equity also grew. Leverage therefore gave **no** early warning (Table 8.2).

**Early warning from coverage: partly supported.** Interest coverage fell from 32.6 (2021) to 4.7 (2022) and 0.11 (2023), one to two years before the 2024 loss, and Z' fell below 1.23 in 2023. But coverage fell mainly because operating income collapsed (19,456 in 2021, 2,334 in 2022, 93 in 2023), while interest expense stayed between 496 and 878. So it is a profitability signal more than a debt signal.

**Model.** The 2022 data gave 28% and the 2023 distress was **missed**. The 2023 and 2024 data gave 67% and 85%, which were correct warnings. The 2025 forecast for 2026 is 73% (High).

## Wolfspeed: distress

Wolfspeed is the distress case:

- **Losses.** It lost money in all 11 years (-64 in 2015 to -1,609 in 2025). Operating margin was negative every year (-175% in 2025), and interest coverage was negative every year (Figures 3, 5 and 6).
- **Leverage arrived late.** The debt ratio rose from 0.17 (2015) to 0.75 (2023) and 1.07 (2025). Debt-to-equity reached 8.05 in 2024, and equity was negative in 2025.
- **Investment.** Capex was 2.8 times revenue in 2024 (2,274 against 807).
- **Comparability.** Discontinued operations of -317 (2019) and -183 (2021) in the P&L show that businesses were sold, so revenue in the early years is not fully comparable with later years.

**Contradiction: liquidity.** The current ratio stayed between 3.29 and 5.74 from 2015 to 2024 (still 4.51 in 2024), then dropped to 0.36 in 2025 (Figure 4). The fiscal 2025 10-K explains the drop: the missed interest payment on the 2029 notes, the restructuring support agreement (23 June 2025) and the defaults triggered by the Chapter 11 filing led the company to present its long-term borrowings as current on the 29 June 2025 balance sheet.

**Restructuring (verified in the 10-K notes).** The Chapter 11 petition was filed on 30 June 2025, one day after the fiscal year end. The company emerged on 29 September 2025 with fresh-start accounting as a new reporting entity, so its series ends at 2025.

**Model.** Wolfspeed was rated High in every year from 2018 (73% to 94%). The 2018 rating was a false alarm, because Z' in 2019 was 1.50 (grey zone). The ratings from 2019 to 2024 were correct warnings, since Z' was below 1.23 from 2020 (Table 8.3).

## Cross-company observations

1. **Profitability and coverage weaken first; liquidity weakens last (Table 8.2).**
   - Wolfspeed had operating losses and coverage below 1.5 from 2015, five years before Z' fell below 1.23 (2020). Leverage crossed 0.6 in 2023, and the current ratio fell below 1 only in 2025, at the Chapter 11 filing.
   - Intel's coverage fell below 1.5 in 2023, the same year as Z', and before its first loss in 2024. Its liquidity and leverage never crossed the warning levels.
2. **A current ratio below 1 is rarely a false alarm here, but it misses most distress (Table 8.4).** This contradicts the guide's expectation. Of 670 company-years of operating companies, only 15 had a current ratio below 1, and 13 of these were distressed the next year (2 false alarms). The real weakness is the opposite: 236 of the 249 company-years that were distressed the next year still had a current ratio of 1 or more. Wolfspeed is the example, at 4.51 one year before Chapter 11. This explains why the current-ratio baseline reached an F1 of only 0.138 (Phase 5).
3. **High growth does not mean low risk (Table 8.5).** The fastest-growing quarter of company-years had a 34.2% chance of distress the next year, about the same as the middle quarters (31.6% and 31.8%). Only the slowest-growing quarter was clearly riskier (46.8%). Nvidia combines high growth with low risk, but that is not a sector rule.
4. **The sector's distress share has no steady trend (Table 8.6).** The share of operating companies with Z' below 1.23 was 28.2% in 2015, peaked at 46.6% (2016) and 44.3% (2024), and was 35.7% in 2025. In every year, between about a quarter and a half of the sector was in distress.
5. **The model gets the four cases mostly right; its errors are at turning points (Table 8.3).** Of the 28 case-company years with a known outcome (2018–2024), 25 were classified correctly. The two misses (AMD 2018, Intel 2022) were years just before a company entered distress, and the one false alarm (Wolfspeed 2018) came one year before its Z' crossed the cutoff. This matches the Phase 5 finding that early warnings are the hardest cases (3 of 10 caught on the test years).
6. **Z' has blind spots.** Nvidia (buyback accounting) and AMD (the Xilinx asset base) show that the book-value Z' moves with capital returns and acquisitions, not only with financial health. This should be listed as a limitation of the label in Phase 9.

## Summary of hypothesis checks (Table 8.1)

| Company | Supported | Partly | Contradicted |
| --- | --- | --- | --- |
| Nvidia | Growth in revenue, margins and returns; strong liquidity | ROE driven by buybacks | Z' stays far above 2.90 |
| AMD | Weak start; recovery; Xilinx effect on ROA and turnover | | |
| Intel | Falling margins; heavy capex; net loss around 2024 | Rising liabilities; early warning (coverage yes, leverage no) | |
| Wolfspeed | Persistent losses; weak coverage; high debt (from 2023); restructuring | | Weak liquidity (until 2025) |
