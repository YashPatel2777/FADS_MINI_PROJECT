# SemiFin: Semiconductor Financial Health Analyzer

Financial ratio analysis and distress prediction for U.S. semiconductor companies using SEC filing data, with Nvidia, AMD, Intel and Wolfspeed as case studies.

> Work in progress.

## What this project does

- Collects annual financial statements of semiconductor companies (SIC code 3674) from the SEC Financial Statement Data Sets
- Cleans the data and computes financial ratios (liquidity, leverage, profitability, efficiency, growth)
- Compares the financial trends of Nvidia, AMD, Intel and Wolfspeed
- Trains machine learning models to predict financial distress one year ahead
- Presents the results in a dashboard and a report

## Tech stack

Python (pandas, scikit-learn, matplotlib), Power BI or Tableau, Git

Full plan: [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md). Every data decision is recorded in [docs/data_log.md](docs/data_log.md).

## Setup

```bash
python -m venv .venv
# Windows:   .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Getting the data (manual download)

The raw data is not stored in this repository.

1. Go to the SEC website and search for **"SEC Financial Statement Data Sets"** (sec.gov, under Data & Research / DERA).
2. Download the quarterly zip files (for example `2024q1.zip`) covering the label-year range set in `src/config.py` (`LABEL_YEAR_START` to `LABEL_YEAR_END`). Include a few quarters after the last year so January year-end filers such as Nvidia are captured.
3. Put the zip files **as downloaded** into `data/raw/`. Do not rename, unzip into, or edit anything in that folder; the code reads from it and never writes to it.
4. Each zip contains a readme describing the `sub`, `num`, `tag` and `pre` files. Field names used in the code are checked against it.

## Running the analysis

Run the notebooks in order; each one reads the outputs of the previous one.

| Notebook | Phase |
| --- | --- |
| `notebooks/01_data_collection.ipynb` | 1: Data collection |
| `notebooks/02_preprocessing.ipynb` | 2: Preprocessing |
| `notebooks/03_ratios_and_pnl.ipynb` | 3: Ratios and profit/loss |
| `notebooks/04_distress_label.ipynb` | 4: Distress label (Altman Z') |
| `notebooks/05_modelling.ipynb` | 5: Machine learning |
| `notebooks/06_figures_and_exports.ipynb` | 6 and 7: Report figures and dashboard CSVs |
| `notebooks/07_case_studies.ipynb` | 8: Case study observations |

## Folder layout

```
data/raw         untouched SEC zips (not committed)
data/interim     intermediate tables (not committed)
data/processed   clean, ratio and labelled tables
notebooks/       one notebook per phase
src/             shared code (config, loading, preprocessing, ratios, labels, models)
figures/         numbered report figures
dashboard/       CSV exports and dashboard screenshots
report/          drafts and final report
docs/            project guide and data log
```
