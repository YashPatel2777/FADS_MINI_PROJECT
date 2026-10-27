"""
Phase 4 (distress label).

Primary label: Altman Z' (the version for firms without market prices; book
equity replaces market equity in X4). A company-year is distressed when
Z' < 1.23; the grey zone (1.23 to 2.90) counts as healthy.

The label is predicted one year ahead: features come from year t, the label
from year t+1, so the models give an early warning instead of describing the
present. Z' and its components X1 to X5 are used only to build the label,
never as model inputs.

Secondary (robustness) label: a net loss, interest coverage below 1.5 and a
current ratio below 1, all in the same year.
"""

import numpy as np
import pandas as pd

from src.ratios import RATIO_COLUMNS

# Model inputs (year t): the Phase 3 ratios plus flags that carry information
# themselves. Z', X1 to X5 and any same-year label are deliberately absent.
FEATURE_COLUMNS = RATIO_COLUMNS + ["negative_equity", "no_interest_expense", "coverage_uses_proxy", "low_revenue"]
ID_COLUMNS = ["cik", "name", "label_year", "fiscal_year_end"]
TARGET_COLUMNS = ["distressed_t1", "robust_label_t1"]

# Z' =0.717 X1 + 0.847 X2 + 3.107 X3 + 0.420 X4 + 0.998 X5
Z_WEIGHTS = {"X1": 0.717, "X2": 0.847, "X3": 3.107, "X4": 0.420, "X5": 0.998}
DISTRESS_CUTOFF = 1.23   # below: distress zone (label 1)
SAFE_CUTOFF = 2.90       # at or above: safe zone; between the two: grey zone (label 0)


def altman_z(df):
    """Z' components and score for every company-year.

    X1 = (current assets - current liabilities) / total assets   working capital
    X2 = retained earnings / total assets                         accumulated profitability
    X3 = operating income / total assets                          operating return on assets
    X4 = book equity / total liabilities                          solvency cushion
    X5 = revenue / total assets                                   asset turnover
    Z' is blank when any component is blank (no value is filled in).
    """
    ta, tl = df["total_assets"], df["total_liabilities"]
    pos = lambda s: s.where(s > 0)  # denominators must be positive
    out = pd.DataFrame({
        "X1": (df["current_assets"] - df["current_liabilities"]) / pos(ta),
        "X2": df["retained_earnings"] / pos(ta),
        "X3": df["operating_income"] / pos(ta),
        "X4": df["equity"] / pos(tl),
        "X5": df["revenue"] / pos(ta),
    }, index=df.index)
    # Weighted sum, kept only where all five components exist
    out["z_prime"] = sum(Z_WEIGHTS[k] * out[k] for k in Z_WEIGHTS).where(out[list(Z_WEIGHTS)].notna().all(axis=1))
    out["zone"] = pd.cut(out["z_prime"], [-np.inf, DISTRESS_CUTOFF, SAFE_CUTOFF, np.inf],
                         right=False, labels=["distress", "grey", "safe"])
    # Primary label: 1 = distressed (Z' < 1.23), 0 = healthy (grey or safe), blank if no Z'
    out["distressed"] = (out["z_prime"] < DISTRESS_CUTOFF).astype(float).where(out["z_prime"].notna())
    return out


def robustness_label(df):
    """1 if net loss AND interest coverage < 1.5 AND current ratio < 1 in the same year.

    Three-valued logic, so a missing input never invents a label:
    - each condition is True, False or unknown;
    - interest = 0 because the company has no debt -> "weak coverage" is False;
    - label = 1 if all three are True, 0 if any is False, blank otherwise.
    """
    loss = df["net_income"] < 0
    weak_cov = pd.Series(np.where(df["interest_coverage"].notna(), df["interest_coverage"] < 1.5,
                                  np.where(df["no_interest_expense"], False, np.nan)), index=df.index)
    illiquid = pd.Series(np.where(df["current_ratio"].notna(), df["current_ratio"] < 1, np.nan), index=df.index)
    conds = pd.concat([loss.astype(float), weak_cov.astype(float), illiquid.astype(float)], axis=1)
    label = pd.Series(np.nan, index=df.index)
    label[(conds == 1).all(axis=1)] = 1.0
    label[(conds == 0).any(axis=1)] = 0.0
    return label


def shift_to_next_year(df, columns):
    """Attach each company's next-year values to the current row (suffix _t1).

    Only used when the next row of the same company is exactly one label year
    later; otherwise the t+1 value is blank, so a gap never pairs year t with
    year t+2.
    """
    df = df.sort_values(["cik", "label_year"])
    g = df.groupby("cik")
    has_next = g["label_year"].shift(-1).eq(df["label_year"] + 1)
    shifted = {f"{c}_t1": g[c].shift(-1).where(has_next) for c in columns}
    return df.assign(**shifted, has_next_year=has_next)
