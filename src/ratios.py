"""
Phase 3 (ratio calculation and profit/loss).

Every ratio is written once here, one function per category, using the
project's formula definitions. Each function takes the clean statements
table (USD millions, one row per company per label year) and returns new
columns. Zero or negative denominators never produce a number: the ratio is
left blank (NaN) and, where the reason itself carries information, a flag
column records it.

Denominator rules
- current liabilities missing or <= 0      -> current, quick, cash ratio blank
- equity <= 0                              -> debt-to-equity and ROE blank,
                                              flag negative_equity
- interest expense = 0 (no debt)           -> interest coverage blank,
                                              flag no_interest_expense
- interest expense not available           -> interest coverage blank
- interest expense is cash paid (proxy)    -> coverage computed,
                                              flag coverage_uses_proxy
- revenue <= 0                             -> margins blank
- last year's revenue <= 0                 -> revenue growth blank
- last year's net income = 0               -> net income growth blank
- previous label year missing              -> both growth ratios blank
"""

import numpy as np
import pandas as pd


def safe_divide(numerator, denominator):
    """numerator / denominator, blank (NaN) wherever the denominator is <= 0 or missing.

    Used for every ratio whose denominator must be positive to be meaningful
    (liabilities, assets, equity, revenue, interest expense).
    """
    ok = denominator > 0
    return (numerator / denominator.where(ok)).where(ok)


def liquidity(df):
    """Ability to pay short-term obligations from short-term assets."""
    cl = df["current_liabilities"]
    return pd.DataFrame({
        # Current ratio = current assets / current liabilities (< 1 is a warning sign)
        "current_ratio": safe_divide(df["current_assets"], cl),
        # Quick ratio = (current assets - inventory) / current liabilities:
        # the same test without relying on selling inventory
        "quick_ratio": safe_divide(df["current_assets"] - df["inventory"], cl),
        # Cash ratio = cash / current liabilities: the strictest test
        "cash_ratio": safe_divide(df["cash"], cl),
    }, index=df.index)


def leverage(df):
    """How the company is financed and how easily it services its debt."""
    out = pd.DataFrame(index=df.index)
    # Debt-to-equity = total liabilities / total equity (all liabilities, not
    # only borrowings). Blank when equity <= 0: a negative ratio would read as
    # "less leveraged" for a company whose liabilities exceed its assets.
    out["debt_to_equity"] = safe_divide(df["total_liabilities"], df["equity"])
    out["negative_equity"] = df["equity"] <= 0
    # Debt ratio = total liabilities / total assets: share of assets financed by liabilities
    out["debt_ratio"] = safe_divide(df["total_liabilities"], df["total_assets"])
    # Interest coverage = operating income / interest expense (< 1.5 is weak).
    # Interest = 0 means no debt, so coverage is unbounded: left blank and flagged.
    out["interest_coverage"] = safe_divide(df["operating_income"], df["interest_expense"])
    out["no_interest_expense"] = df["interest_expense"] == 0
    out["coverage_uses_proxy"] = df["interest_source"].eq("cash_paid_proxy") & out["interest_coverage"].notna()
    return out


def profitability(df):
    """How much profit the company earns per dollar of sales, assets and equity."""
    rev = df["revenue"]
    return pd.DataFrame({
        # Margins over revenue; blank for zero/negative revenue (pre-revenue shells)
        "gross_margin": safe_divide(df["gross_profit"], rev),
        "operating_margin": safe_divide(df["operating_income"], rev),
        "net_margin": safe_divide(df["net_income"], rev),
        # ROA = net income / total assets
        "roa": safe_divide(df["net_income"], df["total_assets"]),
        # ROE = net income / total equity; blank when equity <= 0, where the
        # sign flips and the ratio is meaningless (see negative_equity flag)
        "roe": safe_divide(df["net_income"], df["equity"]),
    }, index=df.index)


def efficiency(df):
    """How much revenue the asset base generates."""
    return pd.DataFrame({
        # Asset turnover = revenue / total assets (computed even for revenue <= 0,
        # since assets are the denominator)
        "asset_turnover": safe_divide(df["revenue"], df["total_assets"]),
        # Size measure for modelling: natural log of total assets (USD millions)
        "log_total_assets": np.log(df["total_assets"].where(df["total_assets"] > 0)),
    }, index=df.index)


def growth(df):
    """Year-on-year growth. Requires the frame sorted by company and label year.

    "Last year" is the same company's previous row, used only when it is the
    immediately preceding label year; a gap gives a blank, so growth is never
    measured over two or more years by accident.
    """
    g = df.groupby("cik")
    consecutive = g["label_year"].diff().eq(1)
    rev_last = g["revenue"].shift(1).where(consecutive)
    ni_last = g["net_income"].shift(1).where(consecutive)
    out = pd.DataFrame(index=df.index)
    # Revenue growth = this year / last year - 1 (blank if last year <= 0)
    out["revenue_growth"] = safe_divide(df["revenue"], rev_last) - 1
    # Net income growth = (this - last) / |last|: the absolute value keeps the
    # sign meaningful when last year was a loss (blank if last year = 0)
    ni_abs = ni_last.abs()
    out["net_income_growth"] = safe_divide(df["net_income"] - ni_last, ni_abs)
    return out


RATIO_COLUMNS = [
    "current_ratio", "quick_ratio", "cash_ratio",
    "debt_to_equity", "debt_ratio", "interest_coverage",
    "gross_margin", "operating_margin", "net_margin", "roa", "roe",
    "asset_turnover", "revenue_growth", "net_income_growth", "log_total_assets",
]
FLAG_COLUMNS = ["negative_equity", "no_interest_expense", "coverage_uses_proxy"]


def compute_ratios(statements):
    """All ratios for every company and label year, in one table."""
    df = statements.sort_values(["cik", "label_year"]).reset_index(drop=True)
    parts = [liquidity(df), leverage(df), profitability(df), efficiency(df), growth(df)]
    ratios = pd.concat(parts, axis=1)
    return pd.concat([df, ratios[RATIO_COLUMNS + FLAG_COLUMNS]], axis=1)


def profit_and_loss(statements):
    """Profit and loss summary (USD millions), one row per company and label year.

    Reported gross profit and operating income are used as they are; the lines
    between them are derived so each statement adds up:
      operating expenses        = gross profit - operating income
      other non-operating items = pre-tax income - (operating income - interest expense)
      discontinued ops & other  = net income - (pre-tax income - income tax)
    The last line holds discontinued operations, equity-method results and
    non-controlling interests. Expenses are shown as positive amounts.
    """
    s = statements.sort_values(["cik", "label_year"]).reset_index(drop=True)
    pnl = pd.DataFrame({
        "cik": s["cik"], "name": s["name"], "label_year": s["label_year"],
        "fiscal_year_end": s["fiscal_year_end"],
        "revenue": s["revenue"],
        "cost_of_revenue": s["cost_of_revenue"],
        "gross_profit": s["gross_profit"],
        "operating_expenses": s["gross_profit"] - s["operating_income"],
        "operating_income": s["operating_income"],
        "interest_expense": s["interest_expense"],
        "other_nonoperating": s["pretax_income"] - (s["operating_income"] - s["interest_expense"]),
        "pretax_income": s["pretax_income"],
        "income_tax": s["income_tax"],
        "discontinued_and_other": s["net_income"] - (s["pretax_income"] - s["income_tax"]),
        "net_income": s["net_income"],
    })
    pnl["profit_or_loss"] = np.where(pnl["net_income"] >= 0, "Profit", "Loss")
    g = pnl.groupby("cik")
    consecutive = g["label_year"].diff().eq(1)
    pnl["revenue_change"] = (pnl["revenue"] - g["revenue"].shift(1)).where(consecutive)
    pnl["revenue_change_pct"] = (pnl["revenue"] / g["revenue"].shift(1) - 1).where(consecutive)
    pnl["net_income_change"] = (pnl["net_income"] - g["net_income"].shift(1)).where(consecutive)
    return pnl
