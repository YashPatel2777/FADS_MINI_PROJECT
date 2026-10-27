"""
Phase 2 (preprocessing). Mostly PLACEHOLDER: only label_year_from_period is
implemented, because Phase 1 already needs it to count companies per year.

Will contain functions to:
- join filtered sub to num on adsh and keep only values whose ddate equals the
  filing's period, uom = USD, no coreg, no segments, qtrs = 0 (balance sheet)
  or 4 (income);
- select statement items using a priority list of XBRL tags per item;
- pivot to one row per filing and deduplicate 10-K/A amendments (latest wins);
- drop or flag rows missing core items (no mean filling), convert to USD
  millions, and run the sanity checks (assets ~ liabilities + equity, etc.).
"""

import pandas as pd


def label_year_from_period(period):
    """Assign each filing to a calendar year (Compustat convention).

    `period` is the fiscal year-end (balance sheet) date from sub.txt, which
    the SEC rounds to the nearest month-end. A fiscal year ending January to
    May mostly covers the previous calendar year, so it gets year - 1; one
    ending June to December keeps its own year.
    Examples: Nvidia 2024-01-31 -> 2023; AMD 2023-12-31 -> 2023;
    Wolfspeed 2024-06-30 -> 2024.
    """
    period = pd.to_datetime(period)
    return period.dt.year - (period.dt.month <= 5).astype(int)
