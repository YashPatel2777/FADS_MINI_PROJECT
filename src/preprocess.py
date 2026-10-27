"""
Phase 2 (preprocessing): turn the Phase 1 filings and num rows into one tidy
statements table with one row per company per label year.

Pipeline (each step is a function, called in order from notebook 02):
1. select_filings        keep label years 2014-2025, one filing per company-period
2. consolidated_values   keep only the company's own consolidated full-year values
3. pick_items            choose one value per statement item using tag priority lists
4. fill_case_interest    fill case-company interest expense from SEC company facts
5. derive_and_flag       derived items, missing-value rules, USD millions, flags
6. sanity_checks         accounting and plausibility checks

Money values stay in raw USD until step 5, which converts them to USD millions.
"""

import numpy as np
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


# ---------------------------------------------------------------------------
# Statement items and their XBRL tags, in priority order
# ---------------------------------------------------------------------------
# qtrs = 0: balance sheet (point-in-time) item; qtrs = 4: full-year flow item.
# The first tag a filing reports wins, and the tag used is recorded, because
# companies switch tags between years (e.g. SalesRevenueNet was replaced by
# RevenueFromContractWithCustomer... under the ASC 606 revenue standard).
ITEMS = {
    # Balance sheet
    "total_assets": (0, ["Assets"]),
    "current_assets": (0, ["AssetsCurrent"]),
    "current_liabilities": (0, ["LiabilitiesCurrent"]),
    "inventory": (0, ["InventoryNet"]),
    # Cash: plain cash and equivalents first; the last fallback also includes
    # restricted cash, so rows using it are flagged.
    "cash": (0, ["CashAndCashEquivalentsAtCarryingValue", "Cash",
                 "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
    "total_liabilities": (0, ["Liabilities"]),
    "liabilities_and_equity": (0, ["LiabilitiesAndStockholdersEquity"]),
    # Equity attributable to the parent's shareholders (used for D/E, ROE, Z').
    "equity": (0, ["StockholdersEquity"]),
    # Total equity including non-controlling interests (only used to derive
    # total liabilities when the Liabilities tag is missing).
    "equity_incl_nci": (0, ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
    "noncontrolling_interest": (0, ["MinorityInterest"]),
    # Temporary (mezzanine) equity: shown between liabilities and equity, e.g.
    # redeemable preferred stock, redeemable non-controlling interests or the
    # conversion obligation of convertible notes. Part of neither.
    "temporary_equity": (0, ["TemporaryEquityCarryingAmountIncludingPortionAttributableToNoncontrollingInterests",
                             "TemporaryEquityCarryingAmountAttributableToParent",
                             "RedeemableNoncontrollingInterestEquityCarryingAmount"]),
    "retained_earnings": (0, ["RetainedEarningsAccumulatedDeficit"]),
    # Income statement
    "revenue": (4, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                    "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueGoodsNet",
                    "SalesRevenueServicesNet"]),
    "cost_of_revenue": (4, ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"]),
    "gross_profit": (4, ["GrossProfit"]),
    "operating_income": (4, ["OperatingIncomeLoss"]),
    # True interest expense tags. InterestIncomeExpenseNonoperatingNet is left
    # out on purpose: it is interest expense net of interest income.
    "interest_expense": (4, ["InterestExpense", "InterestExpenseNonoperating",
                             "InterestExpenseDebt", "InterestAndDebtExpense"]),
    # Cash interest paid (cash flow statement): a substitute used only when no
    # interest expense is available; rows using it are flagged.
    "interest_paid": (4, ["InterestPaidNet", "InterestPaid"]),
    "pretax_income": (4, ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                          "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]),
    "income_tax": (4, ["IncomeTaxExpenseBenefit"]),
    # Net income attributable to the parent (the bottom line, including any
    # discontinued operations); ProfitLoss includes non-controlling interests
    # and is only a fallback (flagged).
    "net_income": (4, ["NetIncomeLoss", "ProfitLoss"]),
}

# Balance sheet debt tags. A filing reporting none of these with a value
# above zero is treated as having no debt (used for the interest rule).
DEBT_TAGS = [
    "LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtCurrent", "DebtCurrent",
    "LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligationsCurrent",
    "ConvertibleNotesPayable", "ConvertibleDebtNoncurrent", "ConvertibleNotesPayableCurrent",
    "LinesOfCreditCurrent", "LongTermLineOfCredit", "ShortTermBorrowings", "NotesPayable",
    "NotesPayableCurrent", "LongTermNotesPayable", "SeniorNotes", "SeniorLongTermNotes",
    "SecuredDebt", "UnsecuredDebt", "OtherLongTermDebtNoncurrent", "DebtInstrumentCarryingAmount",
]

# Core items: a row missing any of these cannot give the main ratios or the
# Z' score and is dropped (hard rule 5: never invent statement values).
CORE_ITEMS = ["total_assets", "equity", "total_liabilities", "revenue", "net_income"]


# ---------------------------------------------------------------------------
# 1. Filings
# ---------------------------------------------------------------------------
def select_filings(filings, first_year, last_year):
    """Keep label years first_year..last_year and one filing per company-period.

    When a company has several annual filings for the same fiscal year-end
    (an original 10-K and one or more 10-K/A, or a re-filed 10-K), the most
    recently filed one is kept because it carries the corrected figures.
    Returns (kept filings, dropped duplicates).
    """
    f = filings[filings["label_year"].between(first_year, last_year)].copy()
    # Sort so the latest filing (by filing date, then acceptance time) comes last.
    f = f.sort_values(["cik", "period", "filed", "accepted"])
    latest = f.duplicated(["cik", "period"], keep="last")
    return f[~latest].reset_index(drop=True), f[latest].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Values
# ---------------------------------------------------------------------------
def consolidated_values(num, filings):
    """Keep only the filing's own consolidated, full-year USD values (hard rule 3).

    - ddate == period: the value is for this filing's fiscal year, not one of
      the prior-year comparatives every 10-K repeats;
    - uom == USD;
    - coreg empty: the consolidated company, not a co-registrant or guarantor;
    - segments empty: the company total, not a segment/product breakdown;
    - qtrs 0 (balance sheet date) or 4 (full year).

    Rows whose value is empty are also removed (the readme allows a NULL
    value); otherwise an empty top-priority tag would hide a usable fallback.
    """
    v = num.merge(filings[["adsh", "period"]], on="adsh")
    keep = ((v["ddate"] == v["period"]) & (v["uom"] == "USD") & v["coreg"].isna()
            & v["segments"].isna() & v["qtrs"].isin([0, 4]) & v["value"].notna())
    return v.loc[keep, ["adsh", "tag", "qtrs", "value"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. Items
# ---------------------------------------------------------------------------
def pick_items(values, items=ITEMS):
    """Choose one value per filing and item, following each item's tag priority.

    Returns (wide, sources): `wide` has one row per adsh and one column per
    item (raw USD); `sources` has the tag that supplied each value.
    """
    wide, sources = [], []
    for item, (qtrs, tags) in items.items():
        cand = values[(values["qtrs"] == qtrs) & values["tag"].isin(tags)].copy()
        cand["rank"] = cand["tag"].map({t: i for i, t in enumerate(tags)})
        best = cand.sort_values("rank").drop_duplicates("adsh").set_index("adsh")
        wide.append(best["value"].rename(item))
        sources.append(best["tag"].rename(item))
    return pd.concat(wide, axis=1), pd.concat(sources, axis=1)


def has_debt(values):
    """True for filings that report any debt tag (DEBT_TAGS) above zero."""
    debt = values[values["tag"].isin(DEBT_TAGS) & (values["qtrs"] == 0) & (values["value"] > 0)]
    return pd.Series(True, index=pd.Index(debt["adsh"].unique(), name="adsh"))


# ---------------------------------------------------------------------------
# 4. Case-company interest from company facts
# ---------------------------------------------------------------------------
def fill_case_interest(wide, sources, case_facts):
    """Fill missing interest_expense of case-company filings from company facts.

    `case_facts` is the output of load_sec.annual_facts_for_filings for the
    interest expense tags. The same tag priority as ITEMS is applied. Only
    gaps are filled; values already found in num are never overwritten.
    Returns the number of values filled.
    """
    tags = ITEMS["interest_expense"][1]
    cf = case_facts[case_facts["tag"].isin(tags)].copy()
    cf["rank"] = cf["tag"].map({t: i for i, t in enumerate(tags)})
    best = cf.sort_values("rank").drop_duplicates("adsh").set_index("adsh")
    gaps = wide.index[wide["interest_expense"].isna()].intersection(best.index)
    wide.loc[gaps, "interest_expense"] = best.loc[gaps, "value"]
    sources.loc[gaps, "interest_expense"] = "companyfacts:" + best.loc[gaps, "tag"]
    return len(gaps)


# ---------------------------------------------------------------------------
# 5. Derived items, missing values, units, flags
# ---------------------------------------------------------------------------
def derive_and_flag(wide, sources, filings, debt, low_revenue_musd=10.0):
    """Build the statements table from the picked items.

    Steps, in order (each recorded in a flag or source column):
    a. total_liabilities missing -> liabilities_and_equity minus total equity
       (equity incl. non-controlling interests if reported, else parent
       equity plus MinorityInterest if reported, else parent equity).
    b. gross_profit missing -> revenue minus cost_of_revenue.
    c. interest_expense missing -> cash interest paid (flagged as a substitute);
       still missing and the filing reports no debt -> 0 (flagged);
       otherwise left missing (interest coverage will be "not available").
    d. inventory missing -> 0 only for companies that never report inventory
       in any year; otherwise left missing.
    e. Convert money to USD millions.
    f. Flags: low revenue, restricted cash in cash, net income from ProfitLoss.
    """
    df = wide.copy()
    src = sources.copy()

    # a. Total liabilities. The balance sheet identity is
    #    total liabilities and equity = liabilities + temporary equity
    #                                   + total equity (parent + NCI),
    #    so liabilities = L&E - temporary equity - total equity.
    total_equity = df["equity_incl_nci"].fillna(df["equity"] + df["noncontrolling_interest"].fillna(0))
    temp_eq = df["temporary_equity"].fillna(0)
    derive_tl = df["total_liabilities"].isna() & df["liabilities_and_equity"].notna() & total_equity.notna()
    df.loc[derive_tl, "total_liabilities"] = (df.loc[derive_tl, "liabilities_and_equity"]
                                              - temp_eq[derive_tl] - total_equity[derive_tl])
    src.loc[derive_tl, "total_liabilities"] = "derived: LiabilitiesAndStockholdersEquity - temporary equity - total equity"

    # a2. Parent equity missing but total equity (incl. NCI) reported: use the
    #     total (flagged). Without non-controlling interests the two are equal.
    eq_fb = df["equity"].isna() & df["equity_incl_nci"].notna()
    df.loc[eq_fb, "equity"] = df.loc[eq_fb, "equity_incl_nci"]
    src.loc[eq_fb, "equity"] = "fallback: StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"

    # b. Gross profit (project rule: use reported gross profit; compute only if missing).
    derive_gp = df["gross_profit"].isna() & df["revenue"].notna() & df["cost_of_revenue"].notna()
    df.loc[derive_gp, "gross_profit"] = df.loc[derive_gp, "revenue"] - df.loc[derive_gp, "cost_of_revenue"]
    src.loc[derive_gp, "gross_profit"] = "derived: revenue - cost_of_revenue"

    # c. Interest expense.
    # interest_source: "reported" (num), "companyfacts" (case companies, from
    # the notes), "cash_paid_proxy", "zero_no_debt" or "not_available".
    from_cf = src["interest_expense"].fillna("").str.startswith("companyfacts:")
    df["interest_source"] = np.where(from_cf, "companyfacts",
                                     np.where(df["interest_expense"].notna(), "reported", None))
    use_paid = df["interest_expense"].isna() & df["interest_paid"].notna()
    df.loc[use_paid, "interest_expense"] = df.loc[use_paid, "interest_paid"]
    src.loc[use_paid, "interest_expense"] = "proxy: " + src.loc[use_paid, "interest_paid"]
    df.loc[use_paid, "interest_source"] = "cash_paid_proxy"
    no_debt = ~df.index.isin(debt.index)
    zero_int = df["interest_expense"].isna() & no_debt
    df.loc[zero_int, "interest_expense"] = 0.0
    src.loc[zero_int, "interest_expense"] = "zero: no debt reported"
    df.loc[zero_int, "interest_source"] = "zero_no_debt"
    df["interest_source"] = df["interest_source"].fillna("not_available")
    df["has_debt"] = ~no_debt

    # Attach company and year identifiers.
    ids = filings.set_index("adsh")[["cik", "name", "label_year", "period", "form", "filed", "source_quarter"]]
    df = ids.join(df, how="inner")

    # d. Inventory: zero only for companies that never report it in any year.
    never_inv = df.groupby("cik")["inventory"].transform(lambda s: s.isna().all())
    df["inventory_assumed_zero"] = never_inv
    df.loc[never_inv, "inventory"] = 0.0
    src.loc[df.index[never_inv], "inventory"] = "zero: company never reports inventory"

    # e. USD millions (hard rule 6).
    money = list(ITEMS)
    df[money] = df[money] / 1e6

    # f. Flags.
    df["low_revenue"] = df["revenue"] < low_revenue_musd
    df["cash_includes_restricted"] = src.reindex(df.index)["cash"].eq(
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents")
    df["net_income_from_profitloss"] = src.reindex(df.index)["net_income"].eq("ProfitLoss")
    df["equity_includes_nci"] = eq_fb.reindex(df.index, fill_value=False)
    df["total_liabilities_derived"] = derive_tl.reindex(df.index, fill_value=False)
    df["gross_profit_derived"] = derive_gp.reindex(df.index, fill_value=False)
    return df, src


def drop_missing_core(df, core=CORE_ITEMS):
    """Drop rows missing any core item. Returns (kept, dropped)."""
    missing = df[core].isna().any(axis=1)
    return df[~missing].copy(), df[missing].copy()


# ---------------------------------------------------------------------------
# 6. Sanity checks
# ---------------------------------------------------------------------------
def sanity_checks(df, balance_tol=0.01, jump_factor=10):
    """Add check columns; nothing is dropped here.

    - balance_ok: |assets - (liabilities + temporary equity + total equity)|
      <= 1% of assets. Only informative where total liabilities were
      reported, since the derived value satisfies the identity by construction.
    - assets_positive, current_liabilities_positive, revenue_positive.
    - yoy_jump: total assets or revenue changed by more than `jump_factor`
      times (up or down) versus the company's previous label year, which
      usually signals a unit/scale error rather than a real business change.
    """
    out = df.sort_values(["cik", "label_year"]).copy()
    total_equity = out["equity_incl_nci"].fillna(out["equity"] + out["noncontrolling_interest"].fillna(0))
    gap = (out["total_assets"] - (out["total_liabilities"] + out["temporary_equity"].fillna(0) + total_equity)).abs()
    out["balance_ok"] = gap <= balance_tol * out["total_assets"]
    out["assets_positive"] = out["total_assets"] > 0
    out["current_liabilities_positive"] = out["current_liabilities"] > 0
    out["revenue_positive"] = out["revenue"] > 0
    jumps = []
    for col in ["total_assets", "revenue"]:
        prev = out.groupby("cik")[col].shift(1)
        consecutive = out.groupby("cik")["label_year"].diff().eq(1)
        ratio = out[col] / prev
        jumps.append(consecutive & ((ratio > jump_factor) | (ratio < 1 / jump_factor)))
    out["yoy_jump"] = jumps[0] | jumps[1]
    return out
