"""
Phase 7: CSV exports for the Power BI dashboard.

No new numbers are calculated here: every value is copied from the Phase 2-5
tables in data/processed, only reshaped for Power BI. The layout is a small
star schema:

- dim_company (one row per CIK) and dim_year (one row per label year) are the
  shared filters (company selector, year slicer);
- every fact table carries cik, label_year and a single-column key cik_year,
  because a Power BI relationship can only join on one column.

Conventions in every file: money in USD millions, ratios and margins as
decimals (0.25 = 25%, formatted as % in Power BI), flags as 0/1, blanks left
empty (never 0 or "NaN"), so Power BI treats them as missing and medians are
not distorted.
"""

import numpy as np
import pandas as pd

from src import config

# Years shown on the dashboard: the analysis years (2014 is only the growth base).
YEARS = list(range(config.LABEL_YEAR_START, config.LABEL_YEAR_END + 1))

# Phase 6 colours, so the dashboard matches the report figures.
CASE_COLOURS = {"Nvidia": "#008300", "AMD": "#e34948", "Intel": "#2a78d6", "Wolfspeed": "#eda100"}
OTHER_COLOUR = "#898781"

# Ratio columns and the names shown on the dashboard (same order as Phase 3).
RATIOS = {
    "current_ratio": "Current ratio", "quick_ratio": "Quick ratio", "cash_ratio": "Cash ratio",
    "debt_to_equity": "Debt-to-equity", "debt_ratio": "Debt ratio", "interest_coverage": "Interest coverage",
    "gross_margin": "Gross margin", "operating_margin": "Operating margin", "net_margin": "Net margin",
    "roa": "ROA", "roe": "ROE", "asset_turnover": "Asset turnover",
    "revenue_growth": "Revenue growth", "net_income_growth": "Net income growth",
}
# Ratios that are percentages (formatted as % in Power BI); the rest are "x" multiples.
PERCENT_RATIOS = {"debt_ratio", "gross_margin", "operating_margin", "net_margin", "roa", "roe",
                  "revenue_growth", "net_income_growth"}

# Display-only ROA bins for the sector histogram. ROA has extreme tails
# (-1,581 to 17,618 for near-zero-asset shells), so a plain histogram would be
# one bar. Bins only group values for the chart; no value is changed or capped.
ROA_BINS = [-np.inf, -0.5, -0.2, -0.1, 0.0, 0.05, 0.1, 0.2, np.inf]
ROA_BIN_LABELS = ["1: below -50%", "2: -50% to -20%", "3: -20% to -10%", "4: -10% to 0%",
                  "5: 0% to 5%", "6: 5% to 10%", "7: 10% to 20%", "8: 20% and above"]


def add_key(df):
    """Add the single-column relationship key, e.g. 1045810_2024."""
    df = df.copy()
    df.insert(0, "cik_year", df["cik"].astype(str) + "_" + df["label_year"].astype(str))
    return df


def risk_band(prob, threshold, low_cut=0.25):
    """Green / amber / red band for a predicted probability.

    Red starts at the random forest's decision threshold (chosen on validation
    in Phase 5), so 'High' means exactly 'predicted distressed'. Amber is the
    watch zone between 0.25 and the threshold.
    """
    return np.select([prob.isna(), prob >= threshold, prob >= low_cut],
                     ["No prediction", "High", "Medium"], default="Low")


def dim_company(ratios):
    """One row per CIK: latest filed name, case-company flag and colour."""
    r = ratios[ratios["analysis_year"]].sort_values("label_year")
    g = r.groupby("cik")
    d = pd.DataFrame({
        "name": g["name"].last(),                      # latest name (e.g. WOLFSPEED, not CREE)
        "first_year": g["label_year"].min(),
        "last_year": g["label_year"].max(),
        "years_in_data": g["label_year"].count(),
        # Low-revenue status can change over time; this marks companies that
        # were below USD 10m in their latest year (the per-year flag is in fact_ratios).
        "low_revenue_latest": g["low_revenue"].last().astype(int),
    }).reset_index()
    d["company"] = d["cik"].map(config.CASE_COMPANIES).fillna(d["name"])
    d["is_case_company"] = d["cik"].isin(config.CASE_COMPANIES).astype(int)
    d["colour"] = d["company"].map(CASE_COLOURS).fillna(OTHER_COLOUR)
    # Case companies first in their report order, then the rest alphabetically.
    order = {c: i for i, c in enumerate(CASE_COLOURS)}
    d["sort_order"] = d["company"].map(order).fillna(len(order)).astype(int)
    d = d.sort_values(["sort_order", "company"]).reset_index(drop=True)
    return d[["cik", "company", "name", "is_case_company", "colour", "sort_order",
              "first_year", "last_year", "years_in_data", "low_revenue_latest"]]


def dim_year():
    return pd.DataFrame({"label_year": YEARS})


def dim_company_year(ratios):
    """One row per company-year with its revenue group (the low-revenue toggle).

    Low-revenue status is per year, and a slicer on one fact table does not
    filter the others; as a dimension joined on cik_year it filters ratios,
    Z' scores and predictions together.
    """
    r = ratios[ratios["analysis_year"]][["cik", "label_year", "low_revenue"]].copy()
    r["low_revenue"] = r["low_revenue"].astype(int)
    r["revenue_group"] = np.where(r["low_revenue"] == 1, "Low revenue (< USD 10m)",
                                  "Operating (revenue >= USD 10m)")
    return add_key(r).sort_values(["cik", "label_year"]).reset_index(drop=True)


def fact_ratios(ratios):
    """Wide ratio table: one row per company-year, 2015-2025."""
    r = ratios[ratios["analysis_year"]].copy()
    money = ["revenue", "gross_profit", "operating_income", "net_income", "total_assets",
             "total_liabilities", "equity", "cash", "current_assets", "current_liabilities"]
    flags = ["low_revenue", "negative_equity", "no_interest_expense", "coverage_uses_proxy"]
    out = r[["cik", "label_year", "fiscal_year_end"] + money + list(RATIOS) + flags].copy()
    out[flags] = out[flags].astype(int)
    out["profit_or_loss"] = np.where(out["net_income"] >= 0, "Profit", "Loss")
    out["roa_bin"] = pd.cut(out["roa"], ROA_BINS, labels=ROA_BIN_LABELS, right=False).astype(str)
    out.loc[out["roa"].isna(), "roa_bin"] = ""
    return add_key(out).sort_values(["cik", "label_year"]).reset_index(drop=True)


def fact_ratios_long(fr):
    """Long ratio table (cik, year, ratio, value) for one line chart with a ratio slicer."""
    long = fr.melt(id_vars=["cik_year", "cik", "label_year"], value_vars=list(RATIOS),
                   var_name="ratio_code", value_name="value")
    long["ratio"] = long["ratio_code"].map(RATIOS)
    long["ratio_order"] = long["ratio_code"].map({k: i + 1 for i, k in enumerate(RATIOS)})
    long["unit"] = np.where(long["ratio_code"].isin(PERCENT_RATIOS), "%", "x")
    # Blank ratios are dropped (they carry no value; the reason is in fact_ratios flags).
    return long.dropna(subset=["value"]).reset_index(drop=True)


def fact_pnl(pnl):
    """P&L summary for the four case companies, 2015-2025."""
    p = pnl[pnl["label_year"].isin(YEARS)].drop(columns=["company", "name"])
    return add_key(p).sort_values(["cik", "label_year"]).reset_index(drop=True)


def fact_zscore(zs):
    """Altman Z' components, score, zone and same-year label, 2015-2025."""
    z = zs[zs["label_year"].isin(YEARS)].drop(columns=["name"]).copy()
    z["zone"] = z["zone"].fillna("not available")
    for c in ["low_revenue"]:
        z[c] = z[c].astype(int)
    # distressed / robust_label stay blank where Z' (or a component) is missing.
    return add_key(z).sort_values(["cik", "label_year"]).reset_index(drop=True)


def fact_predictions(wf, threshold):
    """Walk-forward random-forest probabilities (out of sample).

    A row for label_year t uses year-t ratios to predict distress in t+1, so
    feature_year and target_year are both shown to avoid reading a 2024 score
    as 2024 distress. The key cik_year joins on the feature year.
    """
    p = wf.rename(columns={"prob_distressed_t1": "prob_distress_next_year",
                           "pred_distressed_t1": "predicted_distressed",
                           "distressed_t1": "actual_distressed_next_year"}).copy()
    p["feature_year"] = p["label_year"]
    p["target_year"] = p["label_year"] + 1
    p["risk_band"] = risk_band(p["prob_distress_next_year"], threshold)
    p["risk_band_order"] = p["risk_band"].map({"Low": 1, "Medium": 2, "High": 3})
    p["outcome_known"] = p["actual_distressed_next_year"].notna().astype(int)
    p["threshold"] = threshold
    cols = ["cik", "label_year", "feature_year", "target_year", "prob_distress_next_year",
            "predicted_distressed", "risk_band", "risk_band_order", "threshold",
            "actual_distressed_next_year", "outcome_known", "train_rows", "train_years"]
    return add_key(p[cols]).sort_values(["cik", "label_year"]).reset_index(drop=True)


def model_metrics(comparison):
    """Model comparison, wide (one row per model and set) and long (one row per metric)."""
    m = comparison.rename(columns={"set": "dataset"}).copy()
    m["is_baseline"] = m["model"].str.startswith("Baseline").astype(int)
    m["is_best_model"] = (m["model"] == "Random forest").astype(int)
    m["model_order"] = m["model"].map({k: i + 1 for i, k in enumerate(m["model"].unique())})
    names = {"precision": "Precision", "recall": "Recall", "f1": "F1",
             "roc_auc": "ROC-AUC", "pr_auc": "PR-AUC"}
    long = m.melt(id_vars=["model", "dataset", "model_order", "is_baseline", "is_best_model"],
                  value_vars=list(names), var_name="metric_code", value_name="value")
    long["metric"] = long["metric_code"].map(names)
    return m, long


def feature_importance(fi):
    f = fi.copy()
    f["feature_label"] = f["feature"].map(RATIOS).fillna(
        f["feature"].str.replace("_", " ").str.capitalize())
    f["rank"] = f["shap_share"].rank(ascending=False, method="first").astype(int)
    return f.sort_values("rank").reset_index(drop=True)


def sector_by_year(fr, fz):
    """Reference values for the sector-overview cards (all companies and operating only).

    These are what the Power BI measures should show; they are used to check
    the dashboard against the report, not imported as a chart source.
    """
    rows = []
    for scope, keep in [("All companies", lambda d: d),
                        ("Operating companies (revenue >= USD 10m)", lambda d: d[d["low_revenue"] == 0])]:
        r, z = keep(fr), keep(fz)
        for y in YEARS:
            ry, zy = r[r["label_year"] == y], z[(z["label_year"] == y) & z["distressed"].notna()]
            rows.append({"scope": scope, "label_year": y, "companies": ry["cik"].nunique(),
                         "z_labelled": len(zy), "distressed": int(zy["distressed"].sum()),
                         "pct_distressed": zy["distressed"].mean(),
                         "median_current_ratio": ry["current_ratio"].median(),
                         "median_net_margin": ry["net_margin"].median(),
                         "median_roa": ry["roa"].median(),
                         "loss_making": int((ry["net_income"] < 0).sum())})
    return pd.DataFrame(rows)


def build_all(processed_dir=config.PROCESSED_DIR):
    """Read the Phase 2-5 outputs and return {file name: table}."""
    ratios = pd.read_csv(processed_dir / "ratios.csv")
    pnl = pd.read_csv(processed_dir / "pnl_case_companies.csv")
    zs = pd.read_csv(processed_dir / "zscores.csv")
    wf = pd.read_csv(processed_dir / "walk_forward_predictions.csv")
    comparison = pd.read_csv(processed_dir / "model_comparison.csv")
    fi = pd.read_csv(processed_dir / "feature_importance.csv")

    threshold = float(comparison.loc[(comparison["model"] == "Random forest")
                                     & (comparison["set"] == "test"), "threshold"].iloc[0])
    fr = fact_ratios(ratios)
    fz = fact_zscore(zs)
    mw, ml = model_metrics(comparison)
    return {
        "dim_company": dim_company(ratios),
        "dim_year": dim_year(),
        "dim_company_year": dim_company_year(ratios),
        "fact_ratios": fr,
        "fact_ratios_long": fact_ratios_long(fr),
        "fact_pnl": fact_pnl(pnl),
        "fact_zscore": fz,
        "fact_predictions": fact_predictions(wf, threshold),
        "model_metrics": mw,
        "model_metrics_long": ml,
        "feature_importance": feature_importance(fi),
        "sector_by_year": sector_by_year(fr, fz),
    }


def save_all(tables, out_dir=config.DASHBOARD_EXPORTS_DIR):
    """Write UTF-8 CSVs; blanks are written as empty fields."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8")


def check_exports(tables, processed_dir=config.PROCESSED_DIR):
    """Consistency checks; returns a table of check, result, detail."""
    res = []

    def add(check, ok, detail):
        res.append({"check": check, "ok": bool(ok), "detail": detail})

    dc, dy = tables["dim_company"], tables["dim_year"]
    add("dim_company: one row per CIK", dc["cik"].is_unique, f"{len(dc)} companies")
    add("dim_year: 2015-2025", dy["label_year"].tolist() == YEARS, f"{len(dy)} years")
    dcy = tables["dim_company_year"]
    add("dim_company_year: cik_year unique", dcy["cik_year"].is_unique, f"{len(dcy)} rows")
    for name in ["fact_ratios", "fact_pnl", "fact_zscore", "fact_predictions", "fact_ratios_long"]:
        f = tables[name]
        if name != "fact_ratios_long":  # long table has one row per ratio, so the key repeats
            add(f"{name}: cik_year unique", f["cik_year"].is_unique, f"{len(f)} rows")
        add(f"{name}: every cik_year in dim_company_year", f["cik_year"].isin(dcy["cik_year"]).all(),
            f"{(~f['cik_year'].isin(dcy['cik_year'])).sum()} orphan rows")
        add(f"{name}: every CIK in dim_company", f["cik"].isin(dc["cik"]).all(),
            f"{(~f['cik'].isin(dc['cik'])).sum()} orphan rows")
        add(f"{name}: every year in dim_year", f["label_year"].isin(dy["label_year"]).all(),
            f"years {f['label_year'].min()}-{f['label_year'].max()}")

    # Row counts against the data log / earlier phases.
    add("fact_ratios = 925 analysis company-years", len(tables["fact_ratios"]) == 925, len(tables["fact_ratios"]))
    add("fact_pnl = 4 companies x 11 years", len(tables["fact_pnl"]) == 44, len(tables["fact_pnl"]))
    add("fact_predictions = 583 walk-forward rows", len(tables["fact_predictions"]) == 583,
        len(tables["fact_predictions"]))
    add("model_metrics = 12 rows (6 models x 2 sets)", len(tables["model_metrics"]) == 12, len(tables["model_metrics"]))

    # Values unchanged: every exported number equals the Phase 3 source.
    src = pd.read_csv(processed_dir / "ratios.csv").set_index(["cik", "label_year"])
    fr = tables["fact_ratios"].set_index(["cik", "label_year"])
    cols = list(RATIOS) + ["revenue", "net_income", "total_assets"]
    diff = (fr[cols] - src.loc[fr.index, cols]).abs().max().max()
    add("fact_ratios values equal ratios.csv", diff == 0 or np.isnan(diff), f"max abs difference {diff}")

    # Case-company spot checks against the 10-K verification table (Phase 3).
    # The verification table names companies, so map back to CIK; compare every
    # verified item that is also exported.
    tv = pd.read_csv(processed_dir / "tenk_verification.csv")
    tv["cik"] = tv["company"].map({v: k for k, v in config.CASE_COMPANIES.items()})
    tv = tv[tv["item"].isin(fr.columns)]
    exported = [fr.loc[(c, y), i] for c, y, i in zip(tv["cik"], tv["label_year"], tv["item"])]
    n_bad = int((~np.isclose(exported, tv["tenk_value_musd"])).sum())
    add("case-company values equal 10-K values", n_bad == 0 and len(tv) > 0,
        f"{len(tv)} values ({', '.join(sorted(tv['item'].unique()))}) compared, {n_bad} mismatches")

    # Predictions: same probabilities as Phase 5, bands consistent with the threshold.
    p = tables["fact_predictions"]
    thr = p["threshold"].iloc[0]
    add("High band <=> predicted distressed",
        ((p["risk_band"] == "High") == (p["predicted_distressed"] == 1)).all(), f"threshold {thr:.3f}")
    return pd.DataFrame(res)
