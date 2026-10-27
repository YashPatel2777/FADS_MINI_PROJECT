# SemiFin: Semiconductor Financial Health Analyzer — Complete Mini Project Guide

Oct 27, 2026 · @Orcus

## Project at a glance

SemiFin measures the financial health of U.S. semiconductor companies from SEC filings, tracks their ratios over time, and trains models that flag distress, with Nvidia, AMD, Intel and Wolfspeed as the four case studies.

**Full title:** Financial Ratio Analysis and Distress Prediction of Semiconductor Companies: A Comparative Study of Nvidia, AMD, Intel and Wolfspeed Using SEC XBRL Data

**Short name for the cover page:** SemiFin: Semiconductor Financial Health Analyzer

| Item | Choice |
| --- | --- |
| Sector | Technology |
| Sub-sector | Semiconductors (SIC code 3674) |
| Main case | Nvidia: rapid growth |
| Sub cases | AMD: turnaround then growth; Intel: decline and heavy investment |
| Distress case | Wolfspeed: losses, high debt, restructuring |
| Data source | SEC Financial Statement Data Sets (XBRL), annual 10-K filings |
| Time span | About 10 fiscal years, up to the latest filings available |
| ML dataset | All SIC 3674 filers with usable data; the four cases are highlighted, not the only data |
| Tools | Python (pandas, scikit-learn, matplotlib), Power BI or Tableau, Excel for checks |

### How the project covers your teacher's 7 points

| Teacher's point | Where it is covered |
| --- | --- |
| 1. Finance company dataset | Phase 1: SEC Financial Statement Data Sets |
| 2. Check preprocessing | Phase 2: cleaning, deduplication, fiscal year alignment |
| 3. Apply ratio formulas, profit/loss calculation | Phase 3: liquidity, leverage, profitability, efficiency ratios and a profit/loss summary |
| 4. ML algorithm / Tableau / Power BI | Phase 5 (models) and Phase 7 (dashboard); both are done |
| 5. Observations: growth, loss, prediction | Phase 8: case study observations and model predictions |
| 6. Graphs for historical comparison | Phase 6: multi-year trend charts |
| 7. Conclusion and algorithm comparison | Phase 9 and the model comparison in Phase 5 |

> Check before you start: the Semester VII syllabus PDF you attached does not contain a Financial Analysis and Decision Science (FADS) course, so this plan follows your teacher's 7-point list and the lab manual they will post on Teams. If the manual prescribes a report format or marking scheme, it overrides the structure in this document.

## Problem statement and objectives

Semiconductor companies share one industry but follow very different financial paths, and a single ratio rarely tells you which firms are healthy. This project computes standard ratios from SEC filings, compares four contrasting companies over time, and tests whether machine learning can flag distress one year ahead.

**Problem statement (use this wording in the report):** To analyse the financial performance of U.S. semiconductor companies using ratio analysis on SEC XBRL data, and to build and compare machine learning models that classify companies as financially healthy or distressed, using Nvidia, AMD, Intel and Wolfspeed as comparative case studies.

### Objectives

1. Build a clean, documented dataset of annual financial statements for SIC 3674 filers.
2. Compute liquidity, leverage, profitability, efficiency and growth ratios, plus a profit/loss summary for each case company.
3. Analyse and visualise the historical trends of the four case companies.
4. Define distress with a clear, defensible rule and build at least three models to predict it one year ahead.
5. Compare the models on suitable metrics and interpret which ratios drive the predictions.
6. Present results in a dashboard and a written conclusion.

### Research questions

- Which ratios best separate healthy from distressed semiconductor companies?
- How do the financial trajectories of Nvidia, AMD, Intel and Wolfspeed differ, and do the ratios show the trouble early?
- Which model predicts next-year distress best, and is the gain over a simple baseline worth the added complexity?

## Fiscal year alignment rule

The chosen rule: **label each annual filing by the calendar year in which most of its fiscal year falls. A fiscal year ending in January to May gets the previous calendar year; one ending in June to December gets the same year.** This is the convention used by Compustat, the standard commercial financial database, so you can cite it as an established practice.

### Why this rule

- It keeps Nvidia comparable with Intel and AMD. Nvidia's fiscal year ends in late January, so a filing for the year ended January 2024 covers mostly calendar 2023.
- It needs only one field, the fiscal year-end date, which the SEC data already provides.
- It handles 52/53-week calendars: a company whose year ends on January 1 or 2 is mapped back to the year it mostly covers.
- It is a single rule applied to every company, so no one is treated as a special case.

### How it maps your four companies

| Company | Fiscal year ends | Example year-end | Label year |
| --- | --- | --- | --- |
| Nvidia | Late January | Jan 28, 2024 | 2023 |
| AMD | Late December | Dec 30, 2023 | 2023 |
| Intel | Late December | Dec 30, 2023 | 2023 |
| Wolfspeed | Late June | Jun 30, 2024 | 2024 |

Wolfspeed stays six months out of step with the other three, because a June year-end splits evenly across two calendar years and no label fixes that. Treat it as a known limitation, not an error.

### How to apply it

1. Take the period (balance sheet) date of each 10-K from the submission file.
2. Read the month: January to May gives year minus 1; June to December keeps the year.
3. Store the result as a new column, `label_year`, and use it for every join, chart and model split.
4. Keep the original fiscal year-end date in the dataset so any figure can be traced back.
5. Check that each company has exactly one row per label year; a duplicate means a mapping or amendment problem.

### Wording for your report

> Annual filings were assigned to a calendar-year label using the Compustat convention: fiscal years ending between January and May were labelled with the preceding calendar year, and those ending between June and December with the year of the fiscal year-end. Companies with non-December year-ends, such as Nvidia (January) and Wolfspeed (June), were therefore aligned to the nearest calendar year.

### Optional robustness check

Re-run your headline comparison once with the SEC's own fiscal year field instead of this rule. If the conclusions do not change, say so in the limitations section; it shows the result does not depend on the alignment choice.

## Data source: SEC Financial Statement Data Sets

The SEC publishes one zip file per quarter, each holding tab-separated text files extracted from XBRL filings. Field and file names below are from memory of the SEC's layout, so confirm them against the readme file inside each zip before you code anything.

| File | What it holds | Fields you will use |
| --- | --- | --- |
| sub | One row per filing (the submission list) | adsh (filing id), cik (company id), name, sic (industry code), fye (fiscal year-end), form, period, fy, fp, filed |
| num | One row per reported number | adsh, tag, ddate (date the value applies to), qtrs (length of period in quarters), uom (unit), coreg, value |
| tag | Definition of each tag | tag, version, custom flag, label |
| pre | How numbers were presented in the statements | Rarely needed; useful to confirm a value came from the balance sheet or income statement |

### Selecting your companies

- Filter sub to sic = 3674 and annual forms (10-K, plus 10-K/A amendments to deduplicate).
- Identify the case companies by **cik, not by name**. Wolfspeed was named Cree before late 2021, so a name match will lose its early years. Commonly cited CIKs are Nvidia 1045810, AMD 2488, Intel 50863 and Cree/Wolfspeed 895419; verify each in the sub file.
- Count how many companies and filings you have per year before going further. If the set is too small for modelling, widen the years or add neighbouring semiconductor SIC codes (for example 3672 or 3559), and say so in the report.

### How to read the num file correctly

- A number appears more than once, because each filing also repeats prior-year comparatives. Keep only values whose ddate matches the filing's own period.
- Balance sheet items are point-in-time (qtrs = 0). Income statement items cover a period (qtrs = 4 for a full year).
- Keep only rows in US dollars (uom = USD) and with no coreg value, which excludes segment and subsidiary figures.

### Tags you need

| Item | Typical XBRL tag (fallbacks may be needed) |
| --- | --- |
| Current assets | AssetsCurrent |
| Current liabilities | LiabilitiesCurrent |
| Inventory | InventoryNet |
| Cash | CashAndCashEquivalentsAtCarryingValue |
| Total assets | Assets |
| Total liabilities | Liabilities (if missing: total liabilities and equity minus equity) |
| Equity | StockholdersEquity |
| Retained earnings | RetainedEarningsAccumulatedDeficit |
| Revenue | Revenues, or RevenueFromContractWithCustomerExcludingAssessedTax, or SalesRevenueNet |
| Cost of revenue | CostOfRevenue or CostOfGoodsAndServicesSold |
| Gross profit | GrossProfit |
| Operating income | OperatingIncomeLoss |
| Interest expense | InterestExpense |
| Net income | NetIncomeLoss |

Companies and years differ in which tag they use, so build a priority list per item and record which tag each company used. Expect gaps; handling them is covered in Phase 2.

## Phase 0 and 1: Setup and data collection

By the end of this phase you have the raw SEC files on disk, a project folder you can rerun from scratch, and a first count of how much usable data exists.

### Phase 0: Setup (half a day)

1. Create a project folder with sub-folders for raw data, interim data, processed data, notebooks, figures and the report.
2. Set up a Python environment with pandas, numpy, scikit-learn, matplotlib, seaborn and a notebook editor. Add imbalanced-learn and shap if you plan to use them.
3. Create a GitHub repository for the project and commit as you go; the shared fintech-fraud example shows a notebook-per-stage layout you can copy.
4. Write a short data log file now. Every decision you make later (dropped rows, chosen tags, thresholds) goes in it, because it becomes your preprocessing section.

### Phase 1: Data collection (2 to 3 days)

1. Decide the year range: about 10 fiscal years ending with the latest 10-K filings available. Nvidia's fiscal year ends in January, so include enough early-next-year quarterly files to catch its filings.
2. Download the quarterly zip files covering that range from the SEC site. Search for "SEC Financial Statement Data Sets" on sec.gov.
3. Unzip each quarter and load sub and num (and tag if you need labels).
4. Stack the quarters into one sub table and one num table, adding a column that records the source quarter.
5. Filter the sub table to annual forms and sic = 3674.
6. Pull the cik for Nvidia, AMD, Intel and Wolfspeed/Cree and confirm all four have filings in every year you plan to use.
7. Keep only the num rows that belong to your selected filings, to shrink the data before the heavy work.

### Deliverables

- Raw files stored untouched.
- A filings table (one row per 10-K) for SIC 3674.
- A count table: number of SIC 3674 companies per year.

### Checks before moving on

- Does each of the four case companies appear in every year? If not, note which years are missing and why.
- Roughly how many companies per year do you have? A few dozen per year is workable; fewer than about 30 means you should widen the SIC codes or years.
- Are the quarterly files consistent (same columns in every quarter)? If not, standardise column names before stacking.

## Phase 2: Preprocessing

The goal is one tidy table with one row per company per label year and one column per financial statement item. This is the phase your teacher's point 2 ("check preprocessing") examines, so document every decision.

### Steps

1. **Join** the filtered sub table to num on the filing id (adsh).
2. **Keep the right values.** Retain rows where the value's date equals the filing's period date, the unit is USD and there is no coreg value. Use qtrs = 0 for balance sheet items and qtrs = 4 for income statement items.
3. **Select the tags** from the table in the data source section, using your priority list when a company uses a different tag for the same item.
4. **Pivot** so each tag becomes a column, giving one row per filing.
5. **Deduplicate.** If a company has several filings for the same period (an original 10-K and a 10-K/A), keep the most recently filed one and record that you did.
6. **Apply the fiscal year alignment rule** and create `label_year`.
7. **Handle missing values:**
   - Drop rows missing a core item: total assets, equity or total liabilities, revenue, net income.
   - If inventory is missing for a company that clearly sells chips, investigate before assuming zero; assume zero only for companies that report no inventory, and log it.
   - If interest expense is missing, treat it as zero only when the company reports no debt; otherwise mark interest coverage as not available.
   - Do not fill statement items with the mean; invented financials make the analysis meaningless.
8. **Standardise units.** Convert all values to USD millions so tables and charts are readable.
9. **Run sanity checks:**
   - Total assets approximately equal total liabilities plus equity.
   - Current liabilities and total assets are positive.
   - Revenue is positive for companies you treat as operating businesses.
   - Year-on-year values do not jump by factors that only a data error would explain.
10. **Treat ratio outliers.** After computing ratios in Phase 3, cap them at the 1st and 99th percentiles (winsorise), with the cutoffs calculated on training years only to avoid leaking test information.
11. **Handle zero denominators.** Pre-revenue or tiny companies produce undefined margins; either exclude companies with revenue below a minimum you choose or keep them with an explicit flag, and state which.

### Deliverables

- A clean statements table: `cik, name, label_year, fiscal_year_end` and the statement items.
- A data quality log listing rows removed, tags substituted and assumptions made.
- A short before-and-after summary: filings at the start, filings after each cleaning step.

### Checks before moving on

- Exactly one row per company per label year.
- No negative current liabilities or total assets.
- Your four case companies have complete core items for every year; fix these by hand if tags differ, because they carry the report.
- You can explain every dropped row.

## Phase 3: Ratio calculation and profit/loss

Compute the same ratio set for every company and year, then build a profit/loss summary for the four case companies. This is your teacher's point 3.

### Ratio formulas

| Category | Ratio | Formula | What it tells you |
| --- | --- | --- | --- |
| Liquidity | Current ratio | Current assets ÷ Current liabilities | Ability to pay short-term debts; below 1 is a warning sign |
| Liquidity | Quick ratio | (Current assets − Inventory) ÷ Current liabilities | Same test without relying on selling inventory |
| Liquidity | Cash ratio | Cash ÷ Current liabilities | Strictest liquidity test |
| Leverage | Debt-to-equity | Total liabilities ÷ Total equity | How much of the business is funded by creditors; define it this way and say so |
| Leverage | Debt ratio | Total liabilities ÷ Total assets | Share of assets financed by liabilities |
| Leverage | Interest coverage | Operating income ÷ Interest expense | How many times profit covers interest; below 1.5 is weak |
| Profitability | Gross margin | Gross profit ÷ Revenue | Pricing power and production cost control |
| Profitability | Operating margin | Operating income ÷ Revenue | Profit from core operations |
| Profitability | Net profit margin | Net income ÷ Revenue | Final profit per dollar of sales |
| Profitability | Return on assets (ROA) | Net income ÷ Total assets | How well assets generate profit |
| Profitability | Return on equity (ROE) | Net income ÷ Total equity | Return to shareholders; misleading when equity is near zero or negative |
| Efficiency | Asset turnover | Revenue ÷ Total assets | Sales generated per dollar of assets |
| Growth | Revenue growth | (Revenue this year ÷ Revenue last year) − 1 | Year-on-year sales change |
| Growth | Net income growth | (Net income this year − last year) ÷ absolute value of last year's net income | Year-on-year profit change; use the absolute value because last year can be negative |

### Profit and loss summary

For each case company and each label year, produce a small income statement so your teacher sees the profit or loss calculation directly:

1. Revenue.
2. Less cost of revenue, giving gross profit.
3. Less operating expenses, giving operating income.
4. Less interest and taxes (and other items), giving net income.
5. Label each year as profit or loss, and add the year-on-year change.

If cost of revenue or operating expenses are missing, use the reported gross profit and operating income instead of reconstructing them.

### Steps

1. Compute all ratios in one place, with one function or block per category, so formulas are written once.
2. Compute growth ratios after sorting by company and label year, so "last year" is correct.
3. Check the four case companies by hand against their published annual reports for at least two years each. This confirms your tag choices.
4. Save the ratios table as the main dataset for modelling and the dashboard.

### Deliverables

- A ratios table: one row per company and label year.
- A profit and loss summary table for the four case companies.
- A short note stating each formula exactly as you defined it (copy it into the report).

## Phase 4: Define the distress label

The label is what the models learn to predict, so it must be fixed before modelling and must not be built from the same numbers the models use at prediction time. The recommended design is to label a company as distressed in year t+1 and predict it from ratios in year t.

### Primary label: Altman Z'-score

Use the Z'-score (the version for companies without market prices), because the original Z-score needs stock market value, which the SEC statement data does not contain. Use it for the label and not as a model input.

```latex
Z' = 0.717\,X_1 + 0.847\,X_2 + 3.107\,X_3 + 0.420\,X_4 + 0.998\,X_5
```

| Term | Meaning |
| --- | --- |
| X1 | (Current assets − Current liabilities) ÷ Total assets |
| X2 | Retained earnings ÷ Total assets |
| X3 | Operating income ÷ Total assets |
| X4 | Book value of equity ÷ Total liabilities |
| X5 | Revenue ÷ Total assets |

| Z' range | Class |
| --- | --- |
| Below 1.23 | Distressed (label 1) |
| 1.23 to 2.90 | Grey zone |
| Above 2.90 | Healthy (label 0) |

Decide upfront how to treat the grey zone. The simplest choice is to treat only below 1.23 as distressed and everything else as healthy, and say so in the report. Check these cutoffs against Altman's published paper before citing them.

### Alternative label for a robustness check

Distressed if the company has a net loss, interest coverage below 1.5 and a current ratio below 1 in the same year. Run your best model on this second label too; if both labels give similar conclusions, your result is more convincing.

### Avoiding leakage

- **Time shift:** features come from year t, the label from year t+1. This turns the task into genuine early warning.
- **No label components as same-year features:** if you predict same-year distress, remove the ratios used to define it. With the time shift this is less severe, but still check feature importance for suspicious dominance by one variable.
- **Fit on training years only:** scaling parameters, winsorising cutoffs and any resampling use only the training years.

### Steps

1. Compute the Z' components and score for every company-year.
2. Create the label for year t+1 and attach it to year t's features.
3. Count the classes. If distressed companies are under about 10 percent of rows, you have an imbalance problem to handle in Phase 5; if they are very common (as can happen with small loss-making chip firms), report that too.
4. Look at the four case companies' scores over time; this becomes part of your observations.

### Deliverables

- A labelled modelling table: features at year t, label for year t+1.
- A class balance table by year.
- A written definition of distress, ready to paste into the methodology.

## Phase 5: Machine learning

Train at least three models on the labelled table, split by time, and compare them on the same test years. This covers the ML half of your teacher's point 4 and the algorithm comparison in point 7.

### Models to compare

| Model | Role | Notes |
| --- | --- | --- |
| Logistic regression | Baseline and most explainable | Scale the features; coefficients show which ratios raise risk |
| Random forest | Non-linear, robust | Gives feature importance; less sensitive to outliers |
| Gradient boosting (for example XGBoost or LightGBM) | Usually strongest on tabular data | Tune carefully to avoid overfitting small data |
| Optional: SVM or decision tree | Extra comparison | Decision tree is easy to explain in the viva |

### Time-based split (example for data through label year 2025)

| Set | Feature years | Purpose |
| --- | --- | --- |
| Train | 2016 to 2021 | Fit the models |
| Validation | 2022 to 2023 | Tune settings |
| Test | 2024 (features) predicting 2025 | Final, untouched evaluation |

Adjust the years to the data you actually have. Never split randomly; a random split lets the model see the future and inflates the scores.

### Steps

1. Choose the feature set: the ratios from Phase 3 plus growth ratios and a size measure (log of total assets). Exclude identifiers and the target.
2. Apply the winsorising cutoffs and scaling using training data only.
3. Handle class imbalance: start with class weights; use resampling (for example SMOTE) only inside the training set, never on validation or test.
4. Train each model with a small, documented grid of settings, tuned on the validation set.
5. Evaluate on the test set only once per final model.
6. Add a naive baseline for context, such as "predict distressed if the current ratio is below 1", so you can show what the ML adds.
7. Examine feature importance (and optionally SHAP values) to explain which ratios drive predictions.
8. Score the four case companies, producing a predicted distress probability for each year.

### Metrics to report

- Precision, recall and F1 for the distressed class.
- ROC-AUC and precision-recall AUC.
- Confusion matrix for each model.
- Do not rely on accuracy alone; with few distressed companies, a model that always says "healthy" scores high accuracy and is useless.

### Deliverables

- A model comparison table with the same metrics for every model.
- A feature importance chart for the best model.
- A table of predicted distress probabilities for Nvidia, AMD, Intel and Wolfspeed by year.
- A short paragraph on why the best model won and where all models fail.

### Checks

- Test scores are not dramatically better than validation scores; a big jump usually means leakage.
- No single feature explains almost everything; if it does, re-check the label and features for overlap.
- Results are reproducible: fix random seeds and record them.

## Phase 6 and 7: Historical graphs and dashboard

Phase 6 produces the static figures for the report (teacher's point 6); Phase 7 turns the same data into an interactive Power BI or Tableau dashboard (point 4). Make the figures first, because they tell you what the dashboard should show.

### Phase 6: Figures for the report

Use one consistent colour per company in every chart (for example Nvidia green, AMD red, Intel blue, Wolfspeed grey), label axes with units, and show the label year on the x-axis.

| Figure | Chart type | What it shows |
| --- | --- | --- |
| 1 | Bar chart | Number of SIC 3674 companies per year in your dataset |
| 2 | Line chart | Revenue of the four case companies over time |
| 3 | Line chart | Net income of the four case companies (shows profit and loss years) |
| 4 | Line chart | Current ratio and quick ratio, with a reference line at 1 |
| 5 | Line chart | Debt-to-equity and interest coverage |
| 6 | Line chart | Gross, operating and net margin |
| 7 | Line chart | ROA and ROE |
| 8 | Line chart | Altman Z' score with the 1.23 and 2.90 cutoffs marked |
| 9 | Heatmap | Ratio correlation across all companies, to justify feature choices |
| 10 | Grouped bars | Model comparison on F1, ROC-AUC and recall |
| 11 | ROC curves | All models on one plot |
| 12 | Bar chart | Feature importance of the best model |
| 13 | Line chart | Predicted distress probability for the four cases |

If Wolfspeed or Intel make a chart unreadable because of scale, use a log scale or plot indexed values (year one = 100) and say so in the caption.

### Phase 7: Dashboard

**Data you export from Python for the dashboard:** the ratios table, the profit and loss summary, the Z' scores and the model predictions, each as a CSV with consistent company and label year columns.

| Dashboard page | Contents |
| --- | --- |
| 1. Sector overview | Number of companies, percent flagged distressed by year, median current ratio, median net margin, ROA distribution |
| 2. Company drill-down | Company selector; revenue, net income and ratio trends; latest predicted risk |
| 3. Four-case comparison | Side-by-side trend lines of the key ratios for Nvidia, AMD, Intel and Wolfspeed |
| 4. Model results | Model comparison metrics and the distress probability for each case company |

### Dashboard steps

1. Import the CSVs and set the company and label year fields as the shared keys.
2. Build a year slicer and a company selector that filter every chart on the page.
3. Add summary cards at the top of each page (for example median current ratio, percent distressed).
4. Colour risk levels consistently (for example green, amber, red by predicted probability bands) and state the bands on the page.
5. Take screenshots of each page for the report, and keep the file for the demo.

### Deliverables

- A folder of numbered figures with captions.
- A dashboard file plus screenshots of all pages.

### Checks

- Every figure has a title, axis labels with units, a legend and a one-sentence takeaway in the report.
- Numbers in the dashboard match the tables in the report.

## Phase 8: Case study observations

These are hypotheses from general knowledge of each company, not results. Write your observations only after checking them against your computed numbers, and say plainly where the data disagrees.

| Company | Role | Expected pattern to test | Things to watch in the data |
| --- | --- | --- | --- |
| Nvidia | Main case: growth | Revenue, margins, ROA and ROE rise sharply over the period; liquidity stays strong; Z' stays far above 2.90 | Fiscal year ends in January (handled by the alignment rule); very high ROE can reflect buybacks as well as profit |
| AMD | Sub case: turnaround | Weak profitability and thin equity in the early years, then recovery and growth | The 2022 acquisition of Xilinx raises total assets and goodwill sharply, which lowers asset-based ratios such as ROA and asset turnover in that year |
| Intel | Sub case: decline | Falling margins, heavy capital spending, rising liabilities, and a net loss around 2024 | Check whether leverage and interest coverage worsen before profit collapses, which would show ratios give early warning |
| Wolfspeed | Distress case | Persistent losses, high debt, weak interest coverage and liquidity, then restructuring | Chapter 11 restructuring in 2025 (verify the dates in its filings); filings around and after that period may have gaps or break comparability, so end its series at the last reliable year |

### What to write for each company

For every case company, write one short paragraph covering:

1. The overall direction: growth, stability, decline or distress.
2. The one or two ratios that show it most clearly, with the actual numbers and years.
3. The year the picture changed, if it did.
4. What the model predicted and whether it matched what happened.

### Cross-company observations to look for

- Which ratio moved first before a company's decline: liquidity, leverage, margin or coverage.
- Whether high growth (Nvidia) and high profitability always go together with low risk.
- Whether a single ratio, such as the current ratio, would have given false alarms that the model avoids. Apple-style cases are the classic example: a current ratio near or below 1 does not always mean danger.
- How the sector as a whole changed: the share of companies flagged as distressed by year.

### Deliverable

An observations section of about two pages, with one figure or table cited per claim.

## Phase 9: Conclusion, limitations and future scope

The conclusion is your teacher's point 7: interpret what the data says and compare the algorithms. Write it last, using only results you have already shown.

### What the conclusion must contain

1. **Sector interpretation:** one paragraph on the financial health of semiconductor companies over the period, using the share flagged as distressed and the median ratios.
2. **Case summary:** two or three sentences per company: Nvidia grew, AMD recovered, Intel declined, Wolfspeed became distressed, each backed by one number. Replace these with what your data actually shows.
3. **Algorithm comparison:** state which model performed best on which metric, by how much over the baseline, and why that is plausible (for example, boosted trees capturing non-linear ratio interactions).
4. **Answers to your research questions,** one sentence each.
5. **Practical meaning:** what an analyst or investor could use from this, for example the ratios that warned earliest.

### Limitations (write these honestly)

- Fiscal year alignment is approximate, especially for Wolfspeed, whose June year-end is six months out of step with the other three.
- Few genuinely distressed companies means small test sets and unstable metrics; report this rather than hiding it.
- XBRL tags are inconsistent across companies and years, so some values come from fallback tags.
- Z' is itself a model with fixed cutoffs; labelling by it means the models learn to predict Z', not bankruptcy directly.
- Book values ignore market information such as share price.
- Restructured companies have filings that are hard to compare across the event.
- Results apply to semiconductors only and should not be generalised to other sectors.

### Future scope

- Add market-based features such as stock returns and volatility.
- Use actual bankruptcy or delisting events as the label instead of a score.
- Extend to other sub-sectors, or to quarterly data for earlier warnings.
- Add text features from the management discussion sections of filings.
- Add explainability (SHAP) and fairness checks on size, which connects to the Data Ethics course in your semester.

### Deliverable

A conclusion of about one and a half pages, plus a limitations and future scope section of about one page.

## Final report structure

The report has front matter, nine chapters and back matter, about 30 to 40 pages in total. If the lab manual prescribes a different format, use the manual's headings and map this content into them.

### Front matter

| Item | Contents |
| --- | --- |
| Cover page | Project title, short name SemiFin, your name and roll number, guide or subject teacher, department, college, academic year |
| Certificate and declaration | As per the college template |
| Acknowledgement | Short thanks to teacher and team |
| Abstract | 150 to 250 words: problem, data, method, key results, conclusion |
| Table of contents, list of figures, list of tables | Generated from headings and captions |

### Chapters

| Chapter | Contents | Approx. pages |
| --- | --- | --- |
| 1. Introduction | Background on financial ratio analysis and the semiconductor industry; motivation; problem statement; objectives; scope | 2 to 3 |
| 2. Literature review | Ratio analysis and bankruptcy prediction work (for example Beaver 1966, Altman 1968 and 1983, Ohlson 1980); machine learning for distress prediction; the gap your project fills | 3 to 4 |
| 3. Dataset description | SEC Financial Statement Data Sets, file structure, selection criteria (SIC 3674, 10-K), years covered, size of the final dataset | 2 to 3 |
| 4. Methodology | Fiscal year alignment rule, preprocessing steps, ratio definitions, distress label, models, evaluation metrics, tools; an overall workflow diagram | 5 to 6 |
| 5. Exploratory and ratio analysis | Sector-level trends, correlation heatmap, ratio distributions, profit and loss summary | 3 to 4 |
| 6. Case studies | One subsection each for Nvidia, AMD, Intel and Wolfspeed with figures and numbers | 4 to 5 |
| 7. Machine learning results | Class balance, model comparison table, ROC curves, feature importance, case company predictions | 4 to 5 |
| 8. Dashboard | Screenshots and explanation of each dashboard page and how to use it | 2 to 3 |
| 9. Conclusion, limitations and future scope | As described in Phase 9 | 2 to 3 |

### Back matter

| Item | Contents |
| --- | --- |
| References | Cited papers, books, SEC documentation and websites in a consistent style |
| Appendix A | Data dictionary: every column, its source tag and formula |
| Appendix B | Preprocessing log: dropped rows and assumptions |
| Appendix C | Code listing or link to your GitHub repository |
| Appendix D | Extra figures and full results tables |

### Report-writing rules

- Every figure and table has a number, a caption and a sentence in the text that refers to it.
- Define each ratio the first time it appears.
- Report numbers with units (USD millions, percent, times) and the label year.
- Cite every source, including the SEC data and the Altman formula; this matters for the plagiarism check.
- Write results in the past tense and keep them separate from interpretation.

### Presentation outline (8 to 10 slides)

1. Title and team.
2. Problem and objectives.
3. Data and scope.
4. Preprocessing and fiscal year alignment.
5. Ratios and distress label.
6. Case study findings.
7. Model comparison.
8. Dashboard demo.
9. Conclusion and limitations.
10. Questions.

## Week-by-week timeline

Five weeks, with the dashboard and report writing overlapping so nothing is left to the last day. Compress or stretch it to match your submission date, which the lab manual should give.

| Week | Phases | Work to finish | Milestone at the end of the week |
| --- | --- | --- | --- |
| 1 | 0, 1, 2 | Setup, download data, filter SIC 3674, preprocessing, fiscal year alignment | Clean statements table and data quality log; four case companies verified |
| 2 | 3, 4 | All ratios, profit and loss summary, Z' score, labelled modelling table | Ratios table checked against annual reports for at least two years per case company |
| 3 | 5, 6 | Train and compare models, first version of all report figures | Model comparison table and case company predictions |
| 4 | 7, 8 | Dashboard, observations, remaining figures | Four-page dashboard and observations drafted |
| 5 | 9 and report | Conclusion, limitations, full report, slides, rehearsal | Report and presentation ready; demo tested |

### Weekly habits

- Commit your work to GitHub at the end of each work session.
- Add every cleaning decision to the data log the same day, so the preprocessing chapter is almost already written.
- Show your teacher a short progress update after weeks 2 and 4, so any change in direction happens early.

### If you run short of time

Cut in this order: optional models and the robustness-check label first, then extra figures, then dashboard pages 1 and 4. Do not cut preprocessing, the ratio calculations, the case studies or the model comparison; they carry the teacher's checklist.

## Risks and viva preparation

### Risks and how to handle them

| Risk | Why it matters | What to do |
| --- | --- | --- |
| Wolfspeed filings have gaps or break comparability around its 2025 restructuring | Your distress case could have missing or inconsistent years | Check its filings early; end its series at the last reliable year and say so |
| Fiscal year mismatch | Companies could be compared across different periods | Apply the single alignment rule consistently and add the robustness check |
| Too few companies per year | Models cannot learn reliably | Widen years or add neighbouring SIC codes; report the final size |
| Very few or very many distressed rows | Metrics become unstable or the problem becomes trivial | Check class balance early, use class weights, report precision-recall metrics |
| Label leakage | Scores look excellent but mean nothing | Time-shift the label, fit preprocessing on training years only, inspect feature importance |
| Inconsistent XBRL tags | Silent missing values and wrong ratios | Priority tag lists, hand-check the four case companies against annual reports |
| Mixing amended and original filings | Double counting or old figures | Deduplicate by period, keeping the latest filing |
| Dashboard disagrees with the report | Loses marks at the demo | Export both from the same final CSV files |
| Running out of time | Incomplete mini project | Follow the cut order in the timeline section |

### Questions to prepare for the viva

1. Why did you choose semiconductors, and why these four companies?
2. What is SIC code 3674, and why did you identify companies by CIK instead of name?
3. How did you align fiscal years, and what are the weaknesses of that choice?
4. How did you define distress, and why Altman Z' instead of Z?
5. How did you avoid data leakage?
6. Why a time-based split instead of a random split?
7. Why is accuracy a poor metric here, and which metrics did you use?
8. Which model was best, and why do you think so?
9. What does a current ratio below 1 mean, and why can it mislead?
10. Why is ROE misleading when equity is very small or negative?
11. What would you do differently with more time or data?
12. What are the ethical or practical limits of using such a model to judge a company?

## Tools, references and resources

### Tools

| Purpose | Tool |
| --- | --- |
| Data handling and ratios | Python with pandas and numpy (R is also allowed by your teacher) |
| Machine learning | scikit-learn, plus XGBoost or LightGBM; imbalanced-learn for resampling |
| Charts | matplotlib and seaborn |
| Explainability (optional) | SHAP |
| Dashboard | Power BI or Tableau (one is enough) |
| Quick checks | Excel or Google Sheets for hand-verifying ratios |
| Version control | Git and GitHub |

### Resources your teacher shared

- [365 Financial Analyst learning path](https://learn.365financialanalyst.com/my-learning-path/): use it to revise the ratio formulas and their interpretation.
- [Fintech fraud analytics notebooks (GitHub)](https://github.com/Kbod999/fintech-fraud-analytics/tree/main/notebooks): a model for how to structure notebooks and write up a problem statement.
- SEC Financial Statement Data Sets: on the SEC website, with a readme inside each downloaded zip describing every field.

### Academic references to cite

These are from memory; confirm titles, years and details before you put them in your reference list.

- Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. Journal of Finance.
- Altman, E. I. (1983). Corporate Financial Distress. Wiley. (Source of the Z' variant for non-market-priced firms.)
- Beaver, W. H. (1966). Financial ratios as predictors of failure. Journal of Accounting Research.
- Ohlson, J. A. (1980). Financial ratios and the probabilistic prediction of bankruptcy. Journal of Accounting Research.
- Each company's annual report (Form 10-K) for the four case companies, to verify your numbers.

### Final checklist before submission

- [ ] Fiscal year alignment rule applied and stated in the report
- [ ] Data quality log complete
- [ ] Ratios for all four case companies hand-checked against annual reports
- [ ] Distress label defined, with class balance reported
- [ ] At least three models compared on the same test set with the same metrics
- [ ] Baseline comparison included
- [ ] All 13 figures captioned and referenced in the text
- [ ] Dashboard built and screenshots in the report
- [ ] Observations match the actual numbers, not the hypotheses
- [ ] Conclusion includes algorithm comparison, limitations and future scope
- [ ] References complete and the plagiarism check passed
- [ ] Slides and demo rehearsed
