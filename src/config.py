"""
Project-wide settings for SemiFin (Phase 0: setup).

Every notebook and module imports paths, company identifiers, the year range
and the random seed from here, so each value is defined in exactly one place.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# PROJECT_ROOT is the folder that contains src/. Building every path from it
# means the code works no matter which folder a notebook is launched from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"              # untouched SEC quarterly zips; never modified
INTERIM_DIR = DATA_DIR / "interim"      # intermediate tables (stacked sub/num, filtered rows)
PROCESSED_DIR = DATA_DIR / "processed"  # final clean, ratio and labelled tables

DOCS_DIR = PROJECT_ROOT / "docs"
DATA_LOG = DOCS_DIR / "data_log.md"     # every cleaning decision is recorded here

NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
FIGURES_DIR = PROJECT_ROOT / "figures"  # numbered report figures (Figures 1 to 13)

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_EXPORTS_DIR = DASHBOARD_DIR / "exports"          # CSVs for Power BI / Tableau
DASHBOARD_SCREENSHOTS_DIR = DASHBOARD_DIR / "screenshots"  # dashboard page images for the report

REPORT_DIR = PROJECT_ROOT / "report"

# ---------------------------------------------------------------------------
# Company selection
# ---------------------------------------------------------------------------
# Industry filter: SIC 3674 = Semiconductors and Related Devices.
SIC_CODE = 3674

# Annual report forms. 10-K/A amendments are kept only so they can be
# deduplicated against the original 10-K (latest filing per period wins).
ANNUAL_FORMS = ["10-K", "10-K/A"]

# The four case companies, keyed by CIK (companies are identified by CIK,
# never by name, because Wolfspeed was named Cree before late 2021).
# These CIKs are the commonly cited values: TO BE VERIFIED in the sub file
# during Phase 1 before they are relied on.
CASE_COMPANIES = {
    1045810: "Nvidia",     # TO BE VERIFIED in sub file
    2488: "AMD",           # TO BE VERIFIED in sub file
    50863: "Intel",        # TO BE VERIFIED in sub file
    895419: "Wolfspeed",   # formerly Cree; TO BE VERIFIED in sub file
}

# ---------------------------------------------------------------------------
# Year range (confirmed in Phase 2 from the Phase 1 coverage check)
# ---------------------------------------------------------------------------
# These are label years (Compustat convention: fiscal year-end in January to
# May -> previous calendar year; June to December -> same year). The analysis
# covers 2015 to 2025; label year 2014 (GROWTH_BASE_YEAR) is kept only as the
# "last year" for 2015 growth ratios. Years outside 2014-2025 are only
# partially covered by the downloaded quarters and are dropped.
LABEL_YEAR_START = 2015
LABEL_YEAR_END = 2025
GROWTH_BASE_YEAR = LABEL_YEAR_START - 1

# ---------------------------------------------------------------------------
# SEC company facts (case companies only, used to fill note-only items)
# ---------------------------------------------------------------------------
# One JSON file per case company from data.sec.gov/api/xbrl/companyfacts.
# The SEC asks automated requests to identify themselves; the User-Agent is
# read from the SEC_USER_AGENT environment variable ("Name email") so no
# personal email is stored in the repository.
COMPANYFACTS_DIR = RAW_DIR / "companyfacts"
SEC_USER_AGENT_ENV = "SEC_USER_AGENT"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
# One seed for every random operation (models, resampling, any sampling).
RANDOM_SEED = 42
