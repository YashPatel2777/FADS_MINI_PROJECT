"""
Teacher's mini project format (FADS, 10 marks): Nvidia financial statements,
ratio analysis, capital budgeting under risk, cost of capital, leverage.

Real data: Nvidia's two latest 10-K filings (fiscal years ended January 2025
and January 2026), read from the SEC Financial Statement Data Sets with the
same value filter as Phase 2 (consolidated, USD, the filing's own period).
Assumed data: the 5-year expansion project and the new-debt spread, stated
in ASSUMPTIONS below. Market inputs (risk-free rate, beta, equity risk
premium) were looked up on 28 Oct 2026; sources in report/drafts/references.md.

Run from the project root:  python -m src.finance_report
Outputs: data/processed/nvidia_statements_2y.csv, report/final/finance_numbers.json,
figures/fig15-fig17.
"""

import json
import zipfile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import config
from src import plots as P

NVIDIA_CIK = 1045810
# The two filings (accession number, quarterly zip, fiscal year-end as ddate)
FILINGS = {
    "FY2025": ("0001045810-25-000023", "2025q1", 20250131),
    "FY2026": ("0001045810-26-000021", "2026q1", 20260131),
}

# XBRL tag -> line item. Balance sheet items are point-in-time (qtrs 0),
# income and cash flow items cover the full year (qtrs 4).
TAGS = {
    # Balance sheet: current assets
    "CashAndCashEquivalentsAtCarryingValue": "cash",
    "MarketableSecuritiesCurrent": "securities",
    "MarketableSecuritiesAndEquitySecuritiesFVNI": "securities",  # tag used in FY2026
    "AccountsReceivableNetCurrent": "receivables",
    "InventoryNet": "inventory",
    "PrepaidExpenseAndOtherAssetsCurrent": "prepaid_other_current",
    "AssetsCurrent": "current_assets",
    # Balance sheet: non-current assets
    "PropertyPlantAndEquipmentNet": "ppe",
    "OperatingLeaseRightOfUseAsset": "lease_assets",
    "Goodwill": "goodwill",
    "IntangibleAssetsNetExcludingGoodwill": "intangibles",
    "DeferredIncomeTaxAssetsNet": "deferred_tax_assets",
    "EquitySecuritiesFVNINoncurrent": "noncurrent_investments",
    "OtherAssetsNoncurrent": "other_noncurrent_assets",
    "Assets": "total_assets",
    # Liabilities
    "AccountsPayableCurrent": "payables",
    "AccruedLiabilitiesCurrent": "accrued_current",
    "DebtCurrent": "short_term_debt",
    "LiabilitiesCurrent": "current_liabilities",
    "LongTermDebtNoncurrent": "long_term_debt",
    "OperatingLeaseLiabilityNoncurrent": "lease_liabilities",
    "OtherLiabilitiesNoncurrent": "other_noncurrent_liabilities",
    "Liabilities": "total_liabilities",
    # Equity
    "CommonStockValue": "common_stock",
    "AdditionalPaidInCapital": "apic",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax": "aoci",
    "RetainedEarningsAccumulatedDeficit": "retained_earnings",
    "StockholdersEquity": "equity",
    # Income statement
    "Revenues": "revenue",
    "CostOfRevenue": "cost_of_revenue",
    "GrossProfit": "gross_profit",
    "ResearchAndDevelopmentExpense": "rd",
    "SellingGeneralAndAdministrativeExpense": "sga",
    "OperatingExpenses": "operating_expenses",
    "OperatingIncomeLoss": "operating_income",
    "InvestmentIncomeInterest": "interest_income",
    "InterestExpenseNonoperating": "interest_expense",
    "OtherNonoperatingIncomeExpense": "other_income",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "pretax_income",
    "IncomeTaxExpenseBenefit": "income_tax",
    "NetIncomeLoss": "net_income",
    # Cash flow statement
    "DepreciationDepletionAndAmortization": "depreciation",
    "NetCashProvidedByUsedInOperatingActivities": "cfo",
    "PaymentsToAcquireProductiveAssets": "capex",
    "NetCashProvidedByUsedInInvestingActivities": "cfi",
    "PaymentsForRepurchaseOfCommonStock": "buybacks",
    "PaymentsOfDividends": "dividends",
    "PaymentsRelatedToTaxWithholdingForShareBasedCompensation": "tax_withholding_rsu",
    "RepaymentsOfDebt": "debt_repaid",
    "NetCashProvidedByUsedInFinancingActivities": "cff",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect": "net_change_cash",
}

# ---------------------------------------------------------------------------
# Assumptions (everything not taken from a filing or a market source)
# ---------------------------------------------------------------------------
MARKET = {
    "risk_free": 0.0500,   # 10-year U.S. Treasury, FRED DGS10, 26 Oct 2026
    "beta": 2.22,          # Nvidia 5-year monthly beta, Yahoo Finance, 28 Oct 2026
    "erp": 0.0420,         # Damodaran implied equity risk premium, 1 Oct 2026
    "market_cap": 5_220_000.0,  # USD m, Yahoo Finance valuation measures, 26 Oct 2026
}
ASSUMPTIONS = {
    "new_debt_spread": 0.0075,  # new senior notes priced at Treasury + 0.75%
    "capex": 5000.0,            # USD m: GPU servers, networking, data-hall fit-out
    "working_capital": 300.0,   # USD m, released at the end of year 5
    "life": 5,                  # years, the useful life of a GPU server generation
    "revenue": [2500.0, 4000.0, 4500.0, 3800.0, 2800.0],  # USD m, compute rental
    "variable_cost": 0.35,      # power, bandwidth, support: share of revenue
    "fixed_cost": 400.0,        # USD m a year: staff, site lease, maintenance
    "risk_premium": 0.04,       # added to WACC for a new line of business
    "debt_share": 0.30,         # proposed mix: 70% internal equity, 30% new debt
}
# Scenario changes to the base case (applied to revenue and variable cost ratio)
SCENARIOS = {
    "Best case": {"revenue_mult": 1.20, "variable_cost": 0.32, "prob": 0.25},
    "Most likely case": {"revenue_mult": 1.00, "variable_cost": 0.35, "prob": 0.50},
    "Worst case": {"revenue_mult": 0.75, "variable_cost": 0.38, "prob": 0.25},
}


def extract_statements(path=config.PROCESSED_DIR / "nvidia_statements_2y.csv"):
    """Read Nvidia's two 10-K filings from the raw SEC zips (cached as a CSV)."""
    if path.exists():
        return pd.read_csv(path, index_col=0)
    cols = {}
    for fy, (adsh, quarter, ddate) in FILINGS.items():
        rows = []
        with zipfile.ZipFile(config.RAW_DIR / f"{quarter}.zip") as z:
            for chunk in pd.read_csv(z.open("num.txt"), sep="\t", dtype=str, chunksize=2_000_000):
                rows.append(chunk[chunk.adsh == adsh])
        num = pd.concat(rows)
        # Same filter as Phase 2: own period, USD, consolidated, full year or point in time
        num = num[(num.segments.isna()) & (num.coreg.isna()) & (num.uom == "USD")
                  & (num.ddate.astype(int) == ddate) & (num.qtrs.isin(["0", "4"]))]
        values = {}
        for tag, item in TAGS.items():
            hit = num.loc[num.tag == tag, "value"]
            if len(hit):
                values[item] = float(hit.iloc[0]) / 1e6   # dollars -> USD millions
        cols[fy] = values
    df = pd.DataFrame(cols).fillna(0.0)   # an item a filing does not report is zero on its face
    df.to_csv(path)
    return df


def check_statements(s):
    """The statements must add up exactly as filed."""
    for fy in s.columns:
        c = s[fy]
        ca = c.cash + c.securities + c.receivables + c.inventory + c.prepaid_other_current
        nca = (c.ppe + c.lease_assets + c.goodwill + c.intangibles + c.deferred_tax_assets
               + c.noncurrent_investments + c.other_noncurrent_assets)
        cl = c.payables + c.accrued_current + c.short_term_debt
        ncl = c.long_term_debt + c.lease_liabilities + c.other_noncurrent_liabilities
        eq = c.common_stock + c.apic + c.aoci + c.retained_earnings
        checks = {
            "current assets": (ca, c.current_assets),
            "total assets": (ca + nca, c.total_assets),
            "current liabilities": (cl, c.current_liabilities),
            "total liabilities": (cl + ncl, c.total_liabilities),
            "equity": (eq, c.equity),
            "balance": (c.total_liabilities + c.equity, c.total_assets),
            "pretax": (c.operating_income + c.interest_income - c.interest_expense + c.other_income, c.pretax_income),
            "net income": (c.pretax_income - c.income_tax, c.net_income),
            "cash flow": (c.cfo + c.cfi + c.cff, c.net_change_cash),
        }
        for name, (got, want) in checks.items():
            assert abs(got - want) < 0.5, f"{fy} {name}: {got} vs {want}"
    print("statement checks passed:", list(s.columns))


def ratios(s):
    """The six ratios the brief asks for, with the project's definitions."""
    out = {}
    for fy in s.columns:
        c = s[fy]
        debt = c.short_term_debt + c.long_term_debt
        out[fy] = {
            "net_profit_margin": c.net_income / c.revenue,
            "roa": c.net_income / c.total_assets,
            "current_ratio": c.current_assets / c.current_liabilities,
            "quick_ratio": (c.current_assets - c.inventory) / c.current_liabilities,
            "debt_to_equity": c.total_liabilities / c.equity,   # project definition (total liabilities)
            "borrowings_to_equity": debt / c.equity,            # interest-bearing debt only
            "interest_coverage": c.operating_income / c.interest_expense,
            "total_debt": debt,
            "tax_rate": c.income_tax / c.pretax_income,
        }
    return out


def sector_medians(year=2025):
    """Median ratios of SIC 3674 operating companies (revenue >= USD 10m) for comparison."""
    r = pd.read_csv(config.PROCESSED_DIR / "ratios.csv")
    o = r[(r.label_year == year) & (r.revenue >= 10)]
    cols = ["net_margin", "roa", "current_ratio", "quick_ratio", "debt_to_equity", "interest_coverage"]
    return {"companies": int(len(o)), **{c: float(o[c].median()) for c in cols}}


def cost_of_capital(s, r):
    """CAPM cost of equity, cost of debt and WACC (book, market and proposed mix)."""
    c = s["FY2026"]
    tax = r["FY2026"]["tax_rate"]
    ke = MARKET["risk_free"] + MARKET["beta"] * MARKET["erp"]
    # Existing debt: interest expense over the average borrowings of the two year-ends
    avg_debt = (r["FY2025"]["total_debt"] + r["FY2026"]["total_debt"]) / 2
    kd_pre = c.interest_expense / avg_debt
    kd = kd_pre * (1 - tax)
    debt = r["FY2026"]["total_debt"]
    w_book = debt / (debt + c.equity)
    w_mkt = debt / (debt + MARKET["market_cap"])
    # New debt for the project: Treasury + spread
    kd_new_pre = MARKET["risk_free"] + ASSUMPTIONS["new_debt_spread"]
    kd_new = kd_new_pre * (1 - tax)

    # Financing plans for the project. Cost of equity rises with leverage (Hamada:
    # beta_L = beta_U x (1 + (1 - t) D/E)), as MM Proposition II predicts.
    beta_u = MARKET["beta"] / (1 + (1 - tax) * debt / MARKET["market_cap"])
    plans = {}
    for name, d in [("Plan A: 100% equity", 0.0), ("Plan B: 70% equity, 30% debt", 0.30),
                    ("Plan C: 50% equity, 50% debt", 0.50)]:
        de = d / (1 - d)
        beta_l = beta_u * (1 + (1 - tax) * de)
        ke_l = MARKET["risk_free"] + beta_l * MARKET["erp"]
        # NI approach: Ke stays at today's level whatever the mix
        plans[name] = {
            "debt_share": d, "beta": beta_l, "ke": ke_l,
            "wacc_mm": (1 - d) * ke_l + d * kd_new,
            "wacc_ni": (1 - d) * ke + d * kd_new,
        }
    return {
        "tax_rate": tax, "ke": ke, "kd_pre": kd_pre, "kd": kd, "avg_debt": avg_debt,
        "w_debt_book": w_book, "w_debt_market": w_mkt,
        "wacc_book": (1 - w_book) * ke + w_book * kd,
        "wacc_market": (1 - w_mkt) * ke + w_mkt * kd,
        "kd_new_pre": kd_new_pre, "kd_new": kd_new, "beta_unlevered": beta_u,
        "plans": plans,
    }


def project_cash_flows(tax, revenue_mult=1.0, variable_cost=None, fixed_mult=1.0, var_mult=1.0):
    """Yearly after-tax cash flows of the expansion project (USD m)."""
    a = ASSUMPTIONS
    vc = a["variable_cost"] if variable_cost is None else variable_cost
    dep = a["capex"] / a["life"]                    # straight line, no salvage value
    rows = []
    for year, rev in enumerate(a["revenue"], start=1):
        rev = rev * revenue_mult
        cash_cost = rev * vc * var_mult + a["fixed_cost"] * fixed_mult
        ebit = rev - cash_cost - dep
        nopat = ebit * (1 - tax)                    # a loss saves tax against Nvidia's other profits
        cf = nopat + dep + (a["working_capital"] if year == a["life"] else 0.0)
        rows.append({"year": year, "revenue": rev, "cash_cost": cash_cost, "depreciation": dep,
                     "ebit": ebit, "tax": ebit * tax, "nopat": nopat, "cash_flow": cf})
    return pd.DataFrame(rows)


def npv(rate, outlay, flows):
    return -outlay + sum(cf / (1 + rate) ** t for t, cf in enumerate(flows, start=1))


def irr(outlay, flows, lo=-0.9, hi=1.0):
    """Discount rate at which NPV = 0, by bisection (NPV falls as the rate rises)."""
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid, outlay, flows) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def payback(outlay, flows, rate=None):
    """Years until cumulative (optionally discounted) cash flow repays the outlay."""
    cum = 0.0
    for t, cf in enumerate(flows, start=1):
        v = cf / (1 + rate) ** t if rate else cf
        if cum + v >= outlay:
            return t - 1 + (outlay - cum) / v
        cum += v
    return None


def evaluate(cf, rate, tax):
    a = ASSUMPTIONS
    outlay = a["capex"] + a["working_capital"]
    flows = cf.cash_flow.tolist()
    pv = [f / (1 + rate) ** t for t, f in enumerate(flows, start=1)]
    avg_investment = (a["capex"] + 0.0) / 2 + a["working_capital"]
    return {
        "outlay": outlay, "pv_factors": [1 / (1 + rate) ** t for t in range(1, 6)], "pv": pv,
        "pv_total": sum(pv), "npv": sum(pv) - outlay, "irr": irr(outlay, flows),
        "pi": sum(pv) / outlay, "payback": payback(outlay, flows),
        "discounted_payback": payback(outlay, flows, rate),
        "avg_profit": cf.nopat.mean(), "avg_investment": avg_investment,
        "arr": cf.nopat.mean() / avg_investment,
    }


def leverage(s, coc, cf):
    """Degree of financial leverage for Nvidia and for the project's financing plans."""
    out = {"company": {}}
    for fy in s.columns:
        c = s[fy]
        out["company"][fy] = c.operating_income / (c.operating_income - c.interest_expense)
    a = ASSUMPTIONS
    outlay = a["capex"] + a["working_capital"]
    tax = coc["tax_rate"]
    ebit_base = cf["base"].ebit.iloc[2]     # year 3 of the base case, the peak year
    ebit_worst = cf["worst"].ebit.iloc[0]   # year 1 of the worst case, the weakest year
    out["plans"] = {}
    for name, p in coc["plans"].items():
        debt = outlay * p["debt_share"]
        equity = outlay - debt
        interest = debt * coc["kd_new_pre"]
        row = {"debt": debt, "equity": equity, "interest": interest}
        for label, ebit in [("base", ebit_base), ("worst", ebit_worst)]:
            row[f"ebit_{label}"] = ebit
            row[f"dfl_{label}"] = ebit / (ebit - interest)
            row[f"roe_{label}"] = (ebit - interest) * (1 - tax) / equity
        out["plans"][name] = row
    return out


def figures(cf, ev, coc, sens, scen, rate, radr):
    P.apply_style()
    outlay = ev["outlay"]
    # Figure 15: yearly cash flows and cumulative cash position (payback)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    years = [0] + cf.year.tolist()
    flows = [-outlay] + cf.cash_flow.tolist()
    ax.bar(years, flows, color=["#e34948"] + ["#2a78d6"] * 5, width=0.6)
    ax.plot(years, np.cumsum(flows), color=P.INK, marker="o", lw=P.LINE_W, ms=P.MARKER_SIZE,
            label="Cumulative cash flow")
    ax.axhline(0, color=P.AXIS, lw=1)
    # Value labels inside the bars, so they never collide with the cumulative line
    for x, y in zip(years, flows):
        ax.text(x, y / 2, f"{y:,.0f}", ha="center", va="center", fontsize=8, color="white",
                fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("USD millions")
    ax.set_title(f"Project cash flows (simple payback {ev['payback']:.2f} years)")
    ax.legend(frameon=False, loc="upper left")
    P.save(fig, config.FIGURES_DIR / "fig15_project_cash_flows.png")

    # Figure 16: NPV profile with the two discount rates and the IRR
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    rates = np.linspace(0, 0.30, 121)
    ax.plot(rates * 100, [npv(x, outlay, cf.cash_flow) for x in rates], color="#2a78d6", lw=P.LINE_W)
    ax.axhline(0, color=P.AXIS, lw=1)
    # Each label gets its own offset so the three close points stay readable
    for x, label, off in [(rate, "WACC", (10, 10)), (radr, "Risk-adjusted", (10, 14)),
                          (ev["irr"], "IRR", (-10, -30))]:
        y = npv(x, outlay, cf.cash_flow)
        ax.plot(x * 100, y, "o", color=P.INK, ms=P.MARKER_SIZE)
        ax.annotate(f"{label} {x:.1%}\nNPV {y:,.0f}", (x * 100, y), textcoords="offset points",
                    xytext=off, ha="left" if off[0] > 0 else "right", fontsize=8, color=P.INK_2)
    ax.set_xlabel("Discount rate (%)")
    ax.set_ylabel("NPV, USD millions")
    ax.set_title("NPV profile of the expansion project")
    P.save(fig, config.FIGURES_DIR / "fig16_npv_profile.png")

    # Figure 17: NPV under sensitivity and scenario cases (at WACC)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    labels = ["Base case"] + list(sens) + list(scen)
    vals = [ev["npv"]] + [v["npv"] for v in sens.values()] + [v["npv"] for v in scen.values()]
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in vals]
    ax.barh(labels[::-1], vals[::-1], color=colors[::-1], height=0.6)
    ax.axvline(0, color=P.AXIS, lw=1)
    for i, v in enumerate(vals[::-1]):
        ax.text(v + (40 if v >= 0 else -40), i, f"{v:,.0f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=8, color=P.INK_2)
    ax.set_xlabel(f"NPV at WACC {rate:.2%}, USD millions")
    ax.set_title("Sensitivity and scenario analysis")
    lo = min(vals) - 600
    ax.set_xlim(lo, max(vals) + 600)
    P.save(fig, config.FIGURES_DIR / "fig17_npv_scenarios.png")


def main():
    s = extract_statements()
    check_statements(s)
    r = ratios(s)
    coc = cost_of_capital(s, r)
    tax = coc["tax_rate"]

    # Discount rate: WACC of the proposed financing mix (Plan B, MM with taxes)
    rate = coc["plans"]["Plan B: 70% equity, 30% debt"]["wacc_mm"]
    radr = rate + ASSUMPTIONS["risk_premium"]

    base = project_cash_flows(tax)
    ev = evaluate(base, rate, tax)
    ev_radr = evaluate(base, radr, tax)

    sens = {
        "Sales -10%": evaluate(project_cash_flows(tax, revenue_mult=0.9), rate, tax),
        "Costs +10%": evaluate(project_cash_flows(tax, fixed_mult=1.1, var_mult=1.1), rate, tax),
    }
    scen_cf = {k: project_cash_flows(tax, revenue_mult=v["revenue_mult"], variable_cost=v["variable_cost"])
               for k, v in SCENARIOS.items()}
    scen = {k: {**evaluate(cf, rate, tax), "prob": SCENARIOS[k]["prob"]} for k, cf in scen_cf.items()}
    expected_npv = sum(v["npv"] * v["prob"] for v in scen.values())
    sd_npv = np.sqrt(sum(v["prob"] * (v["npv"] - expected_npv) ** 2 for v in scen.values()))

    lev = leverage(s, coc, {"base": base, "worst": scen_cf["Worst case"]})
    figures(base, ev, coc, sens, {k: v for k, v in scen.items() if k != "Most likely case"}, rate, radr)

    numbers = {
        "statements": s.to_dict(), "ratios": r, "sector_2025": sector_medians(), "market": MARKET, "assumptions": ASSUMPTIONS,
        "scenario_settings": SCENARIOS, "coc": coc, "rate": rate, "radr": radr,
        "cash_flows": base.to_dict(orient="list"), "eval": ev, "eval_radr": ev_radr,
        "sensitivity": sens, "scenarios": scen,
        "scenario_cash_flows": {k: v.to_dict(orient="list") for k, v in scen_cf.items()},
        "expected_npv": expected_npv, "sd_npv": sd_npv, "leverage": lev,
    }
    out = config.PROJECT_ROOT / "report" / "final" / "finance_numbers.json"
    out.write_text(json.dumps(numbers, indent=1, default=float))

    # Show the headline numbers
    print(pd.DataFrame(r).round(4).to_string())
    print(f"\nKe {coc['ke']:.4f}  Kd pre {coc['kd_pre']:.4f}  Kd after tax {coc['kd']:.4f}  tax {tax:.4f}")
    print(f"WACC book {coc['wacc_book']:.4f}  market {coc['wacc_market']:.4f}  new Kd {coc['kd_new']:.4f}")
    for k, p in coc["plans"].items():
        print(f"  {k}: beta {p['beta']:.3f} Ke {p['ke']:.4f} WACC(MM) {p['wacc_mm']:.4f} WACC(NI) {p['wacc_ni']:.4f}")
    print("\n", base.round(1).to_string())
    print(f"\nrate {rate:.4f}  RADR {radr:.4f}")
    for name, e in [("WACC", ev), ("RADR", ev_radr)]:
        print(f"{name}: PV {e['pv_total']:.1f} NPV {e['npv']:.1f} IRR {e['irr']:.4f} PI {e['pi']:.3f} "
              f"payback {e['payback']:.2f} disc payback {e['discounted_payback']} ARR {e['arr']:.4f}")
    for k, e in {**sens, **scen}.items():
        print(f"  {k}: NPV {e['npv']:.1f} IRR {e['irr']:.4f} PI {e['pi']:.3f} payback {e['payback']}")
    print(f"expected NPV {expected_npv:.1f}  SD {sd_npv:.1f}")
    print("DFL company", lev["company"])
    for k, p in lev["plans"].items():
        print(" ", k, {x: round(y, 4) for x, y in p.items()})
    print("saved", out)


if __name__ == "__main__":
    main()
