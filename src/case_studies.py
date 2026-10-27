"""
Phase 8: case study observations for Nvidia, AMD, Intel and Wolfspeed.

Two parts:
1. Three extra items for the case companies only, needed to test two of the
   guide's hypotheses (Intel's heavy capital spending, Nvidia's buyback-driven
   ROE) and the AMD-Xilinx goodwill effect: capital expenditure and share
   repurchases (cash flow statement) and goodwill (balance sheet). They are
   taken from the same num rows with the same filters as Phase 2 (hard rule 3).
2. Helpers that turn the existing Phase 3-5 tables into the evidence tables
   for the observations: Z' broken into its parts, DuPont ROE, the first year
   each warning sign appeared, and model predictions against outcomes.

Nothing here changes the modelling data; these tables are descriptive.
"""

import numpy as np
import pandas as pd

from src import config
from src.preprocess import consolidated_values, pick_items

# Tag priority per item (same mechanism as preprocess.ITEMS).
# Capex: PaymentsToAcquirePropertyPlantAndEquipment is the standard tag (AMD,
# Intel, Wolfspeed). Nvidia used its own custom tag
# PurchasesOfPropertyAndEquipmentAndIntangibleAssets until fiscal 2023 and the
# standard PaymentsToAcquireProductiveAssets afterwards; both include purchases
# of intangible assets, so Nvidia's capex is flagged (slightly broader).
EXTRA_ITEMS = {
    "capex": (4, ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
                  "PurchasesOfPropertyAndEquipmentAndIntangibleAssets"]),
    "buybacks": (4, ["PaymentsForRepurchaseOfCommonStock"]),
    "goodwill": (0, ["Goodwill"]),
}
# Statement and label words for the 10-K check (src/verify.check_filing).
EXTRA_CHECK_ITEMS = {
    "capex": ("cash_flow", ["property", "productive assets", "capital expenditure"]),
    "buybacks": ("cash_flow", ["repurchase"]),
    "goodwill": ("balance", ["goodwill"]),
}
CAPEX_INCLUDES_INTANGIBLES = {"PaymentsToAcquireProductiveAssets", "PurchasesOfPropertyAndEquipmentAndIntangibleAssets"}

# Altman Z' coefficients (same as src/labels.py) for the component breakdown.
Z_WEIGHTS = {"X1": 0.717, "X2": 0.847, "X3": 3.107, "X4": 0.420, "X5": 0.998}
Z_PARTS = {"X1": "Working capital / assets", "X2": "Retained earnings / assets",
           "X3": "Operating income / assets", "X4": "Book equity / liabilities", "X5": "Revenue / assets"}

# Warning levels used for the "which ratio moved first" timeline. These are
# conventional rule-of-thumb levels, fixed before looking at the case results:
# current ratio below 1 (current liabilities exceed current assets), debt ratio
# above 0.6 (liabilities more than 60% of assets), interest coverage below 1.5
# (the robustness-label level), operating margin below 0 and a net loss.
WARNINGS = {
    "Liquidity: current ratio < 1": lambda d: d["current_ratio"] < 1,
    "Leverage: debt ratio > 0.6": lambda d: d["debt_ratio"] > 0.6,
    "Coverage: interest coverage < 1.5": lambda d: d["interest_coverage"] < 1.5,
    "Margin: operating margin < 0": lambda d: d["operating_margin"] < 0,
    "Profit: net loss": lambda d: d["net_income"] < 0,
}


def case_rows(ratios):
    """Analysis-year rows of the four case companies with a short company name."""
    c = ratios[ratios["cik"].isin(config.CASE_COMPANIES) & ratios["analysis_year"]].copy()
    c["company"] = c["cik"].map(config.CASE_COMPANIES)
    return c.sort_values(["company", "label_year"]).reset_index(drop=True)


def extract_extra_items(num, ratios):
    """Capex, buybacks and goodwill (USD millions) for every case-company 10-K.

    Uses the filings already chosen in Phase 2 (one per company and label year,
    including the 2014 base year) and the Phase 2 value filter. A blank means
    the filing reports no such line; it is never filled (hard rule 5).
    """
    f = ratios[ratios["cik"].isin(config.CASE_COMPANIES)][["adsh", "cik", "label_year", "fiscal_year_end"]].copy()
    f["period"] = pd.to_datetime(f["fiscal_year_end"])
    values = consolidated_values(num[num["adsh"].isin(f["adsh"])], f)
    wide, sources = pick_items(values, EXTRA_ITEMS)
    wide = wide / 1e6  # USD millions (hard rule 6)
    out = f.drop(columns="period").merge(wide, left_on="adsh", right_index=True, how="left")
    out = out.merge(sources.add_suffix("_tag"), left_on="adsh", right_index=True, how="left")
    out["company"] = out["cik"].map(config.CASE_COMPANIES)
    out["capex_includes_intangibles"] = out["capex_tag"].isin(CAPEX_INCLUDES_INTANGIBLES)
    return out.sort_values(["company", "label_year"]).reset_index(drop=True)


def z_breakdown(zs, companies=config.CASE_COMPANIES):
    """Weighted contribution of each Z' component (coefficient x ratio); they add up to Z'."""
    z = zs[zs["cik"].isin(companies)].copy()
    z["company"] = z["cik"].map(companies)
    for x, w in Z_WEIGHTS.items():
        z[f"{x}_contrib"] = w * z[x]
    return z


def dupont(case):
    """ROE = net margin x asset turnover x equity multiplier (assets / equity).

    The product equals net income / equity exactly, so this shows whether a
    high ROE comes from profitability, efficiency or a thin equity base
    (which buybacks create by paying cash out of equity).
    """
    d = case[["company", "label_year", "net_margin", "asset_turnover", "roe", "total_assets", "equity"]].copy()
    d["equity_multiplier"] = np.where(d["equity"] > 0, d["total_assets"] / d["equity"], np.nan)
    d["roe_check"] = d["net_margin"] * d["asset_turnover"] * d["equity_multiplier"]
    return d


def warning_timeline(case, zs):
    """First analysis year each warning sign appears, next to the first Z' < 1.23 year."""
    z = zs[["cik", "label_year", "z_prime"]]
    d = case.merge(z, on=["cik", "label_year"], how="left")
    rows = []
    for company, g in d.groupby("company", sort=False):
        rec = {"company": company}
        for name, rule in WARNINGS.items():
            hit = g.loc[rule(g).fillna(False), "label_year"]
            rec[name] = int(hit.min()) if len(hit) else None
        hit = g.loc[g["z_prime"] < 1.23, "label_year"]
        rec["First Z' < 1.23"] = int(hit.min()) if len(hit) else None
        rows.append(rec)
    return pd.DataFrame(rows)


def prediction_outcomes(wf):
    """Walk-forward predictions of the case companies against what happened in t+1."""
    w = wf[wf["company"].notna()].copy()
    pred, actual = w["pred_distressed_t1"], w["distressed_t1"]
    w["outcome"] = np.select(
        [actual.isna(), (pred == 1) & (actual == 1), (pred == 1) & (actual == 0),
         (pred == 0) & (actual == 1)],
        ["forecast (t+1 not yet known)", "correct warning", "false alarm", "missed"],
        default="correct (healthy)")
    return w[["company", "label_year", "prob_distressed_t1", "pred_distressed_t1", "distressed_t1", "outcome"]]


def current_ratio_signal(mt):
    """How the 'current ratio < 1' rule relates to next-year distress (labelled rows).

    Uses operating companies (the modelling sample) and all of them, so the
    effect of tiny shell companies is visible.
    """
    rows = []
    lab = mt[mt["distressed_t1"].notna() & mt["current_ratio"].notna()]
    for scope, d in [("Operating companies", lab[~lab["low_revenue"].astype(bool)]), ("All companies", lab)]:
        low = d["current_ratio"] < 1
        dist = d["distressed_t1"] == 1
        rows.append({
            "scope": scope, "company_years": len(d),
            "current_ratio_below_1": int(low.sum()),
            "of_which_distressed_next_year": int((low & dist).sum()),
            "false_alarms": int((low & ~dist).sum()),
            "distressed_next_year": int(dist.sum()),
            "distressed_with_current_ratio_at_least_1": int((~low & dist).sum()),
        })
    return pd.DataFrame(rows)


def growth_vs_risk(mt):
    """Next-year distress share by revenue-growth quartile (operating companies)."""
    d = mt[mt["distressed_t1"].notna() & mt["revenue_growth"].notna()
           & ~mt["low_revenue"].astype(bool)].copy()
    d["growth_quartile"] = pd.qcut(d["revenue_growth"], 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
    g = d.groupby("growth_quartile", observed=True).agg(
        company_years=("distressed_t1", "size"),
        growth_min=("revenue_growth", "min"), growth_max=("revenue_growth", "max"),
        median_net_margin=("net_margin", "median"),
        share_distressed_next_year=("distressed_t1", "mean"))
    return g.reset_index()
