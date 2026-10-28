// Builds "SemiFin - A Semiconductor Financial Analysis Report.docx" in the
// teacher's mini project format. Every number comes from
// report/final/finance_numbers.json, written by `python -m src.finance_report`.
// Run from the project root:  node src/build_finance_docx.js   (needs the npm package docx)

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel,
  AlignmentType, WidthType, ShadingType, BorderStyle, PageBreak, Footer, Header, PageNumber,
  TableOfContents, LevelFormat,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const N = JSON.parse(fs.readFileSync(path.join(ROOT, "report/final/finance_numbers.json"), "utf8"));
const OUT = path.join(ROOT, "report/final/SemiFin - A Semiconductor Financial Analysis Report.docx");

const S25 = N.statements.FY2025, S26 = N.statements.FY2026;
const R25 = N.ratios.FY2025, R26 = N.ratios.FY2026;
const SEC = N.sector_2025, C = N.coc, A = N.assumptions, E = N.eval, ER = N.eval_radr;
const PLAN_A = "Plan A: 100% equity", PLAN_B = "Plan B: 70% equity, 30% debt", PLAN_C = "Plan C: 50% equity, 50% debt";

// ---------- number formatting ----------
const MINUS = "−";
function num(x, d = 0) {
  const s = Math.abs(x).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  return (x < 0 && Number(s.replace(/,/g, "")) !== 0 ? MINUS : "") + s;
}
const pct = (x, d = 1) => num(x * 100, d) + "%";
const times = (x, d = 2) => num(x, d) + "x";

// ---------- layout constants (A4, 1 inch margins) ----------
const PAGE_W = 11906, MARGIN = 1440, CONTENT_W = PAGE_W - 2 * MARGIN; // 9026 DXA
const FONT = "Times New Roman";
const ACCENT = "1F4E79";
const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
const borders = { top: border, bottom: border, left: border, right: border };

// Inline **bold** markup -> runs
function runs(text, opts = {}) {
  return text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((part) =>
    part.startsWith("**")
      ? new TextRun({ text: part.slice(2, -2), bold: true, ...opts })
      : new TextRun({ text: part, ...opts }));
}
const P = (text, opts = {}) => new Paragraph({
  children: runs(text, opts.run || {}), alignment: opts.align || AlignmentType.JUSTIFIED,
  spacing: { after: 100, line: 264 }, ...(opts.para || {}),
});
const H1 = (text, newPage = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)], pageBreakBefore: newPage });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
const bullet = (text, level = 0) => new Paragraph({
  numbering: { reference: "bullets", level }, children: runs(text), spacing: { after: 40, line: 264 },
  alignment: AlignmentType.LEFT,
});
const numbered = (text, ref = "numbers") => new Paragraph({
  numbering: { reference: ref, level: 0 }, children: runs(text), spacing: { after: 60, line: 288 },
});
const formula = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 120 },
  children: [new TextRun({ text, italics: true, font: "Cambria Math" })],
});
const caption = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 40, after: 160 },
  children: runs(text, { size: 18, italics: true }),
});
const tableTitle = (text) => new Paragraph({
  keepNext: true, spacing: { before: 160, after: 60 }, children: runs(text, { bold: true, size: 20 }),
});
const note = (text) => new Paragraph({ spacing: { before: 40, after: 160 }, children: runs(text, { size: 18, italics: true, color: "404040" }) });

// Table: header row shaded; numeric columns right-aligned; rows listed in `boldRows` are bold.
function table(headers, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const scale = CONTENT_W / total;
  const w = widths.map((x) => Math.round(x * scale));
  w[w.length - 1] += CONTENT_W - w.reduce((a, b) => a + b, 0);
  const align = (i, isHeader) => (i === 0 || (opts.leftCols || []).includes(i)) ? AlignmentType.LEFT
    : (isHeader ? AlignmentType.CENTER : AlignmentType.RIGHT);
  const cell = (text, i, isHeader, bold, shade) => new TableCell({
    borders, width: { size: w[i], type: WidthType.DXA },
    shading: shade ? { fill: shade, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    children: [new Paragraph({
      alignment: align(i, isHeader),
      children: runs(String(text), { bold: isHeader || bold, size: 18, color: isHeader ? "FFFFFF" : undefined }),
    })],
  });
  const header = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true, true, ACCENT)) });
  const body = rows.map((r, ri) => {
    const bold = (opts.boldRows || []).includes(ri);
    const shade = (opts.shadeRows || []).includes(ri) ? "E7EEF6" : (bold ? "F2F2F2" : undefined);
    return new TableRow({ children: r.map((t, i) => cell(t, i, false, bold, shade)) });
  });
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w, rows: [header, ...body] });
}

// Image scaled to a width in inches, keeping its aspect ratio (PNG size from the IHDR chunk)
function image(rel, widthIn = 6.2) {
  const buf = fs.readFileSync(path.join(ROOT, rel));
  const pw = buf.readUInt32BE(16), ph = buf.readUInt32BE(20);
  const wpx = Math.round(widthIn * 96), hpx = Math.round(wpx * ph / pw);
  return new Paragraph({
    alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: wpx, height: hpx },
      altText: { title: path.basename(rel), description: path.basename(rel), name: path.basename(rel) } })],
  });
}
const spacer = () => new Paragraph({ children: [] });

// ---------- derived values used in the text ----------
const fcf25 = S25.cfo - S25.capex, fcf26 = S26.cfo - S26.capex;
const liquid26 = S26.cash + S26.securities;
const nca = (s) => s.total_assets - s.current_assets;
const ncl = (s) => s.total_liabilities - s.current_liabilities;
const cf = N.cash_flows;
const yrs = [1, 2, 3, 4, 5];
const plans = C.plans, lev = N.leverage.plans;
const scen = N.scenarios, sens = N.sensitivity;
const cv = N.sd_npv / N.expected_npv;
const pctChange = (a, b) => (b - a) / Math.abs(a);

// =====================================================================
// Cover page
// =====================================================================
// Page 1 is left blank for the student's own cover page
const cover = [new Paragraph({ children: [] })];

const index = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Index")] }),
  new TableOfContents("Index", { hyperlink: true, headingStyleRange: "1-2" }),
  note("If the page numbers are blank, right-click the index and choose Update Field."),
];

// =====================================================================
// Introduction
// =====================================================================
const intro = [
  H1("1. Introduction", true),
  P("This report applies the financial decision framework of the FADS mini project to a real semiconductor company, **NVIDIA Corporation (Nvidia)**. It prepares and analyses Nvidia’s financial statements for its last two fiscal years, evaluates a proposed five-year expansion project under risk, recommends how to finance it, and identifies the insurance cover that protects it."),
  P("Nvidia was chosen because it is the main case company of the wider **SemiFin** project (Chapter 2), which studied the financial health of all U.S. semiconductor companies from SEC filings. Using a real company means that the statements, ratios and cost of capital come from actual filings and market data; only the expansion project itself is assumed."),
  H2("1.1 Data and units"),
  bullet("**Financial statements:** Nvidia’s Form 10-K filings for fiscal years ended late January 2025 (**FY2025**) and late January 2026 (**FY2026**), taken from the SEC Financial Statement Data Sets [1, 2]. Every subtotal was checked: current and total assets, liabilities, equity, profit before tax, net income and the cash flow total all add up exactly as filed."),
  bullet("**Market data:** 10-year U.S. Treasury yield [3], Nvidia’s beta and market value [4] and the implied equity risk premium [5], all as of October 2026."),
  bullet("**Units:** all amounts are in **USD millions** (Nvidia reports in U.S. dollars) unless stated otherwise."),
  tableTitle("Table 1.1. What is real and what is assumed"),
  table(["Item", "Source", "Status"], [
    ["Balance sheet, income statement, cash flow statement", "Nvidia 10-K filings via SEC data [1, 2]", "Real"],
    ["Ratios", "Computed from the statements", "Real"],
    ["Risk-free rate, beta, market value, equity risk premium", "FRED, Yahoo Finance, Damodaran [3–5]", "Real (Oct 2026)"],
    ["Cost of existing debt, tax rate", "Interest expense, debt and tax in the 10-K", "Real"],
    ["Expansion project: investment, revenue, costs, life", "Stated assumptions (Section 5.1)", "Assumed"],
    ["New-debt spread, project risk premium, scenario probabilities", "Stated assumptions", "Assumed"],
  ], [5, 4, 2], { leftCols: [1, 2] }),
  H2("1.2 Structure of the report"),
  P("Chapter 2 summarises the wider SemiFin study. Chapters 3 to 7 follow the five steps of the project brief: company profile, financial statements and ratios, capital budgeting under risk, financing and capital structure, and insurance. Chapter 8 gives the final recommendation."),
];

// =====================================================================
// Chapter 2: background SemiFin study
// =====================================================================
const background = [
  H1("2. Background: the SemiFin study"),
  P("SemiFin (Semiconductor Financial Health Analyzer) is the larger project behind this report. It built a cleaned dataset of **1,028 company-years from 161 U.S. semiconductor companies** (SIC code 3674, fiscal years 2014 to 2025) from the SEC Financial Statement Data Sets, computed 14 financial ratios, and compared four case companies: Nvidia (growth), AMD (turnaround), Intel (decline) and Wolfspeed (distress). Financial distress was defined with the Altman Z′ score, and four machine learning models were trained to predict it one year ahead. The results are presented in a Power BI dashboard."),
  image("figures/fig14_workflow.png", 3.0),
  caption("**Figure 2.1. Workflow of the SemiFin study.** From SEC filings to ratios, the Altman Z′ distress label, machine learning and the dashboard."),
  tableTitle("Table 2.1. Key findings of the SemiFin study"),
  table(["Area", "Finding"], [
    ["Sector health", "Each year 28% to 47% of operating companies had Z′ below 1.23 (distressed); the median net margin was only 1.2% in 2025."],
    ["Nvidia", "Revenue rose from USD 5,010m (2015) to 215,938m (2025); profitable every year; current ratio never below 2.57."],
    ["AMD", "Recovered from negative equity in 2015 to a Z′ above 1.23 from 2020."],
    ["Intel", "Gross margin fell from 63% to 33%; net loss of USD 18,756m in 2024."],
    ["Wolfspeed", "Losses every year; filed for Chapter 11 in June 2025 while its current ratio stayed above 3 until 2024."],
    ["Best model", "Random forest: test F1 0.779, ROC-AUC 0.895; far better than a current-ratio rule (F1 0.138)."],
    ["Warning signs", "Profitability and interest coverage warned of distress earlier than liquidity."],
  ], [2, 7], { leftCols: [1] }),
  P("This report takes the main case company, Nvidia, and applies the full financial decision framework of the project brief to it."),
];

// =====================================================================
// Step 1: Company profile
// =====================================================================
const profile = [
  H1("3. Step 1: Company profile"),
  tableTitle("Table 3.1. Company profile of NVIDIA Corporation"),
  table(["Attribute", "Details"], [
    ["Name of the company", "NVIDIA Corporation (SEC CIK 1045810), listed on Nasdaq as NVDA"],
    ["Headquarters", "Santa Clara, California, United States"],
    ["Industry", "Semiconductors and related devices (SIC code 3674)"],
    ["Nature of business", "Designs graphics processing units (GPUs), data-centre accelerators for artificial intelligence, networking products and the software that runs on them (such as the CUDA platform). Its markets are data centres, gaming, professional visualisation and automotive. Nvidia is fabless: it designs chips and outsources manufacturing to foundry partners."],
    ["Fiscal year", "Ends in late January (FY2026 ended January 2026)"],
    ["Revenue (FY2026)", `USD ${num(S26.revenue)}m, up ${pct(S26.revenue / S25.revenue - 1)} from USD ${num(S25.revenue)}m`],
    ["Net profit (FY2026)", `USD ${num(S26.net_income)}m (net margin ${pct(R26.net_profit_margin)})`],
    ["Total assets (FY2026)", `USD ${num(S26.total_assets)}m`],
    ["Research and development (FY2026)", `USD ${num(S26.rd)}m (${pct(S26.rd / S26.revenue)} of revenue)`],
    ["Market value", `About USD ${num(N.market.market_cap / 1e6, 2)} trillion (26 October 2026) [4]`],
    ["Size of operations", "Large-cap, global: among the largest semiconductor companies in the world by revenue and market value"],
    ["Expansion objective", `Build an AI compute cloud: GPU server capacity rented to enterprise and government customers, with an initial investment of USD ${num(A.capex + A.working_capital)}m over a five-year life (Chapter 5)`],
  ], [2.2, 6.8], { leftCols: [1] }),
  H2("3.1 Rationale for the expansion"),
  P(`Demand for AI computing has driven Nvidia’s revenue up ${pct(S26.revenue / S25.revenue - 1, 0)} in FY2026 alone. Today Nvidia mainly sells hardware; renting computing capacity directly would add a recurring revenue stream and bring Nvidia closer to end customers. The project is new for the company, so it carries more risk than its existing chip business, which is why Chapter 5 evaluates it with a risk-adjusted discount rate, sensitivity analysis and scenarios.`),
  P(`Nvidia can afford the project easily: it held USD ${num(liquid26)}m of cash and marketable securities at the end of FY2026 and generated USD ${num(S26.cfo)}m of operating cash flow in that year. The question is therefore not whether Nvidia can pay for the project, but whether the project earns more than its cost of capital and how it should be financed.`),
];

// =====================================================================
// Step 2: financial statements and ratios
// =====================================================================
const bsRows = [
  ["**Current assets**", "", ""],
  ["Cash and cash equivalents", num(S25.cash), num(S26.cash)],
  ["Marketable securities", num(S25.securities), num(S26.securities)],
  ["Accounts receivable", num(S25.receivables), num(S26.receivables)],
  ["Inventories", num(S25.inventory), num(S26.inventory)],
  ["Prepaid expenses and other", num(S25.prepaid_other_current), num(S26.prepaid_other_current)],
  ["Total current assets", num(S25.current_assets), num(S26.current_assets)],
  ["**Non-current assets**", "", ""],
  ["Property, plant and equipment (net)", num(S25.ppe), num(S26.ppe)],
  ["Operating lease assets", num(S25.lease_assets), num(S26.lease_assets)],
  ["Goodwill", num(S25.goodwill), num(S26.goodwill)],
  ["Intangible assets", num(S25.intangibles), num(S26.intangibles)],
  ["Deferred tax assets", num(S25.deferred_tax_assets), num(S26.deferred_tax_assets)],
  ["Non-current equity investments", S25.noncurrent_investments ? num(S25.noncurrent_investments) : "–", num(S26.noncurrent_investments)],
  ["Other assets", num(S25.other_noncurrent_assets), num(S26.other_noncurrent_assets)],
  ["Total non-current assets", num(nca(S25)), num(nca(S26))],
  ["TOTAL ASSETS", num(S25.total_assets), num(S26.total_assets)],
  ["**Current liabilities**", "", ""],
  ["Accounts payable", num(S25.payables), num(S26.payables)],
  ["Accrued and other current liabilities", num(S25.accrued_current), num(S26.accrued_current)],
  ["Short-term debt", num(S25.short_term_debt), num(S26.short_term_debt)],
  ["Total current liabilities", num(S25.current_liabilities), num(S26.current_liabilities)],
  ["**Long-term liabilities**", "", ""],
  ["Long-term debt", num(S25.long_term_debt), num(S26.long_term_debt)],
  ["Long-term operating lease liabilities", num(S25.lease_liabilities), num(S26.lease_liabilities)],
  ["Other long-term liabilities", num(S25.other_noncurrent_liabilities), num(S26.other_noncurrent_liabilities)],
  ["Total long-term liabilities", num(ncl(S25)), num(ncl(S26))],
  ["TOTAL LIABILITIES", num(S25.total_liabilities), num(S26.total_liabilities)],
  ["**Shareholders’ equity**", "", ""],
  ["Common stock and additional paid-in capital", num(S25.common_stock + S25.apic), num(S26.common_stock + S26.apic)],
  ["Accumulated other comprehensive income", num(S25.aoci), num(S26.aoci)],
  ["Retained earnings", num(S25.retained_earnings), num(S26.retained_earnings)],
  ["TOTAL EQUITY", num(S25.equity), num(S26.equity)],
  ["TOTAL LIABILITIES AND EQUITY", num(S25.total_liabilities + S25.equity), num(S26.total_liabilities + S26.equity)],
];
const bsBold = [6, 15, 16, 21, 26, 27, 32, 33];

const isRows = [
  ["Revenue", num(S25.revenue), num(S26.revenue)],
  ["Less: Cost of revenue", num(-S25.cost_of_revenue), num(-S26.cost_of_revenue)],
  ["Gross profit", num(S25.gross_profit), num(S26.gross_profit)],
  ["Less: Research and development", num(-S25.rd), num(-S26.rd)],
  ["Less: Sales, general and administrative", num(-S25.sga), num(-S26.sga)],
  ["Total operating expenses", num(-S25.operating_expenses), num(-S26.operating_expenses)],
  ["Operating income (EBIT)", num(S25.operating_income), num(S26.operating_income)],
  ["Add: Interest income", num(S25.interest_income), num(S26.interest_income)],
  ["Less: Interest expense", num(-S25.interest_expense), num(-S26.interest_expense)],
  ["Add: Other income (net)", num(S25.other_income), num(S26.other_income)],
  ["Profit before tax", num(S25.pretax_income), num(S26.pretax_income)],
  ["Less: Income tax", num(-S25.income_tax), num(-S26.income_tax)],
  ["NET PROFIT", num(S25.net_income), num(S26.net_income)],
  ["Total expenses (revenue − net profit)", num(S25.revenue - S25.net_income), num(S26.revenue - S26.net_income)],
];

const cfoOther = (s) => s.cfo - s.net_income - s.depreciation;
const cfiOther = (s) => s.cfi + s.capex;
const cffOther = (s) => s.cff + s.buybacks + s.dividends + s.tax_withholding_rsu + s.debt_repaid;
const opening = (s) => s.cash - s.net_change_cash;
const cfRows = [
  ["**A. Operating activities**", "", ""],
  ["Net profit", num(S25.net_income), num(S26.net_income)],
  ["Add: Depreciation and amortisation", num(S25.depreciation), num(S26.depreciation)],
  ["Other adjustments and working capital changes", num(cfoOther(S25)), num(cfoOther(S26))],
  ["Net cash from operating activities", num(S25.cfo), num(S26.cfo)],
  ["**B. Investing activities**", "", ""],
  ["Purchase of property, equipment and intangibles", num(-S25.capex), num(-S26.capex)],
  ["Securities, investments and acquisitions (net)", num(cfiOther(S25)), num(cfiOther(S26))],
  ["Net cash used in investing activities", num(S25.cfi), num(S26.cfi)],
  ["**C. Financing activities**", "", ""],
  ["Share buybacks", num(-S25.buybacks), num(-S26.buybacks)],
  ["Dividends paid", num(-S25.dividends), num(-S26.dividends)],
  ["Tax paid on employee share awards", num(-S25.tax_withholding_rsu), num(-S26.tax_withholding_rsu)],
  ["Repayment of debt", num(-S25.debt_repaid), num(-S26.debt_repaid)],
  ["Other financing (net)", num(cffOther(S25)), num(cffOther(S26))],
  ["Net cash used in financing activities", num(S25.cff), num(S26.cff)],
  ["Net change in cash (A + B + C)", num(S25.net_change_cash), num(S26.net_change_cash)],
  ["Cash at the beginning of the year", num(opening(S25)), num(opening(S26))],
  ["Cash at the end of the year", num(S25.cash), num(S26.cash)],
  ["Free cash flow (operating cash flow − capital expenditure)", num(fcf25), num(fcf26)],
];

const ratioRows = [
  ["Net profit margin", "Net profit ÷ Revenue", `${num(S26.net_income)} ÷ ${num(S26.revenue)}`, pct(R25.net_profit_margin), pct(R26.net_profit_margin), pct(SEC.net_margin)],
  ["Return on assets (ROA)", "Net profit ÷ Total assets", `${num(S26.net_income)} ÷ ${num(S26.total_assets)}`, pct(R25.roa), pct(R26.roa), pct(SEC.roa)],
  ["Current ratio", "Current assets ÷ Current liabilities", `${num(S26.current_assets)} ÷ ${num(S26.current_liabilities)}`, times(R25.current_ratio), times(R26.current_ratio), times(SEC.current_ratio)],
  ["Quick ratio", "(Current assets − Inventory) ÷ Current liabilities", `${num(S26.current_assets - S26.inventory)} ÷ ${num(S26.current_liabilities)}`, times(R25.quick_ratio), times(R26.quick_ratio), times(SEC.quick_ratio)],
  ["Debt–equity ratio", "Total liabilities ÷ Total equity", `${num(S26.total_liabilities)} ÷ ${num(S26.equity)}`, times(R25.debt_to_equity), times(R26.debt_to_equity), times(SEC.debt_to_equity)],
  ["Borrowings to equity", "(Short + long-term debt) ÷ Total equity", `${num(R26.total_debt)} ÷ ${num(S26.equity)}`, times(R25.borrowings_to_equity), times(R26.borrowings_to_equity), "–"],
  ["Interest coverage ratio", "EBIT ÷ Interest expense", `${num(S26.operating_income)} ÷ ${num(S26.interest_expense)}`, times(R25.interest_coverage, 1), times(R26.interest_coverage, 1), times(SEC.interest_coverage)],
];

const statements = [
  H1("4. Step 2: Financial statement preparation and analysis", true),
  P("The statements below are simplified from Nvidia’s 10-K filings: related lines are grouped, but every total is exactly as filed. FY2025 is the year ended late January 2025 and FY2026 the year ended late January 2026."),
  H2("4.1 Balance sheet"),
  tableTitle("Table 4.1. Balance sheet of NVIDIA Corporation (USD millions)"),
  table(["Particulars", "FY2025", "FY2026"], bsRows, [6, 2, 2], { boldRows: bsBold }),
  note("FY2025 reports non-current equity investments within other assets. Source: Nvidia 10-K filings, accession numbers 0001045810-25-000023 and 0001045810-26-000021 [1, 2]."),
  P(`**Observations.** Total assets almost doubled, from USD ${num(S25.total_assets)}m to ${num(S26.total_assets)}m, funded mainly by retained profits: equity rose from USD ${num(S25.equity)}m to ${num(S26.equity)}m. Cash and marketable securities reached USD ${num(liquid26)}m. Goodwill rose from USD ${num(S25.goodwill)}m to ${num(S26.goodwill)}m, showing acquisitions during the year, and inventories more than doubled to USD ${num(S26.inventory)}m. Borrowings were almost unchanged at about USD ${num(R26.total_debt)}m.`),
  H2("4.2 Income statement"),
  tableTitle("Table 4.2. Income statement of NVIDIA Corporation (USD millions)"),
  table(["Particulars", "FY2025", "FY2026"], isRows, [6, 2, 2], { boldRows: [2, 6, 10, 12] }),
  P(`**Observations.** Revenue grew ${pct(S26.revenue / S25.revenue - 1)} to USD ${num(S26.revenue)}m and net profit ${pct(S26.net_income / S25.net_income - 1)} to USD ${num(S26.net_income)}m. The gross margin eased from ${pct(S25.gross_profit / S25.revenue)} to ${pct(S26.gross_profit / S26.revenue)}, but operating expenses grew more slowly than revenue, so the operating margin stayed above 60%. Interest expense (USD ${num(S26.interest_expense)}m) was tiny next to operating income. Other income rose to USD ${num(S26.other_income)}m, mostly gains on investments.`),
  H2("4.3 Cash flow statement (summary)"),
  tableTitle("Table 4.3. Cash flow statement of NVIDIA Corporation, summary (USD millions)"),
  table(["Particulars", "FY2025", "FY2026"], cfRows, [6, 2, 2], { boldRows: [4, 8, 15, 16, 18, 19] }),
  P(`**Observations.** Operating activities generated USD ${num(S26.cfo)}m in FY2026, close to net profit, so profits were backed by cash. Capital expenditure was small (USD ${num(S26.capex)}m) because Nvidia is fabless, leaving free cash flow of USD ${num(fcf26)}m. Investing outflows of USD ${num(-S26.cfi)}m went mostly into marketable securities, equity investments and acquisitions. Financing outflows of USD ${num(-S26.cff)}m were mainly share buybacks (USD ${num(S26.buybacks)}m), so most surplus cash was returned to shareholders.`),
  H2("4.4 Ratio analysis"),
  tableTitle("Table 4.4. Ratio analysis of NVIDIA Corporation"),
  table(["Ratio", "Formula", "FY2026 calculation", "FY2025", "FY2026", "Sector median 2025"], ratioRows, [2.2, 2.8, 2.4, 1.2, 1.2, 1.4], { leftCols: [1, 2] }),
  note(`Sector median: ${SEC.companies} U.S. semiconductor companies (SIC 3674) with revenue of at least USD 10 million, label year 2025, from the SemiFin dataset. The SemiFin project defines debt–equity as total liabilities ÷ equity; borrowings to equity counts interest-bearing debt only.`),
  H3("Interpretation"),
  bullet(`**Profitability.** A net profit margin of ${pct(R26.net_profit_margin)} means Nvidia kept about 56 cents of every dollar of sales as profit, against a sector median of ${pct(SEC.net_margin)}. ROA fell from ${pct(R25.roa)} to ${pct(R26.roa)}, not because profits weakened but because total assets grew faster than profit (cash, investments and goodwill from acquisitions). Both figures are exceptional for any industry.`),
  bullet(`**Liquidity.** A current ratio of ${times(R26.current_ratio)} and a quick ratio of ${times(R26.quick_ratio)} mean current assets cover short-term obligations almost four times, even without inventory. Both ratios fell slightly as payables and accrued liabilities grew with the business, but they remain well above the sector medians (${times(SEC.current_ratio)} and ${times(SEC.quick_ratio)}).`),
  bullet(`**Solvency.** Total liabilities were only ${times(R26.debt_to_equity)} of equity, and interest-bearing borrowings only ${times(R26.borrowings_to_equity)}. Operating income covered interest ${num(R26.interest_coverage, 0)} times, while the median semiconductor company did not cover its interest even once (${times(SEC.interest_coverage)}). Nvidia has almost no financial risk.`),
  P("**Overall.** Nvidia is highly profitable, highly liquid and very lightly geared. Its financial position can comfortably absorb a new investment of the size proposed in Chapter 5."),
];

// =====================================================================
// Step 3: capital budgeting under risk
// =====================================================================
const cfTableRows = [
  ["Revenue", "", ...yrs.map((y) => num(cf.revenue[y - 1]))],
  ["Less: Cash operating costs", "", ...yrs.map((y) => num(-cf.cash_cost[y - 1]))],
  ["Less: Depreciation", "", ...yrs.map((y) => num(-cf.depreciation[y - 1]))],
  ["EBIT", "", ...yrs.map((y) => num(cf.ebit[y - 1]))],
  [`Less: Tax at ${pct(C.tax_rate)}`, "", ...yrs.map((y) => num(-cf.tax[y - 1]))],
  ["Net operating profit after tax", "", ...yrs.map((y) => num(cf.nopat[y - 1]))],
  ["Add: Depreciation", "", ...yrs.map((y) => num(cf.depreciation[y - 1]))],
  ["Initial investment and working capital", num(-(A.capex + A.working_capital)), "", "", "", "", num(A.working_capital)],
  ["Net cash flow", num(-(A.capex + A.working_capital)), ...yrs.map((y) => num(cf.cash_flow[y - 1]))],
];
const pvRows = [
  ["Net cash flow", num(-E.outlay), ...yrs.map((y) => num(cf.cash_flow[y - 1]))],
  [`PV factor at ${pct(N.rate, 2)}`, "1.0000", ...E.pv_factors.map((f) => num(f, 4))],
  ["Present value", num(-E.outlay), ...E.pv.map((v) => num(v))],
  [`PV factor at ${pct(N.radr, 2)} (risk-adjusted)`, "1.0000", ...ER.pv_factors.map((f) => num(f, 4))],
  ["Present value (risk-adjusted)", num(-E.outlay), ...ER.pv.map((v) => num(v))],
];
const cumAt = (flows, outlay) => { let c = -outlay; return flows.map((f) => (c += f)); };
const cum = cumAt(cf.cash_flow, E.outlay);

const capbud = [
  H1("5. Step 3: Investment decision – capital budgeting under risk", true),
  H2("5.1 The proposed project"),
  P(`The project builds an AI compute cloud: GPU servers, networking and data-hall fit-out whose computing capacity is rented to enterprise and government customers. The figures below are **assumptions** made for this exercise, sized to Nvidia’s scale (the investment is about ${pct(A.capex / S26.capex, 0)} of Nvidia’s FY2026 capital expenditure).`),
  tableTitle("Table 5.1. Project assumptions"),
  table(["Item", "Assumption", "Reasoning"], [
    ["Initial investment", `USD ${num(A.capex)}m`, "GPU servers, networking, data-hall fit-out"],
    ["Working capital", `USD ${num(A.working_capital)}m, recovered in year 5`, "Receivables and spare parts"],
    ["Life", `${A.life} years, no salvage value`, "Useful life of one GPU server generation"],
    ["Depreciation", `Straight line, USD ${num(A.capex / A.life)}m a year`, "Capex ÷ life"],
    ["Revenue", A.revenue.map((x) => num(x)).join(", "), "Ramp-up, then lower prices as newer GPUs arrive"],
    ["Variable costs", `${pct(A.variable_cost, 0)} of revenue`, "Power, bandwidth, support"],
    ["Fixed cash costs", `USD ${num(A.fixed_cost)}m a year`, "Staff, site lease, maintenance"],
    ["Tax rate", pct(C.tax_rate), "Nvidia’s FY2026 effective tax rate (tax ÷ profit before tax)"],
    ["Discount rate (WACC)", pct(N.rate, 2), "Proposed financing mix, Chapter 6"],
    ["Risk-adjusted discount rate", pct(N.radr, 2), `WACC + ${pct(A.risk_premium, 0)} premium for a new line of business`],
  ], [2.2, 3, 4], { leftCols: [1, 2] }),
  tableTitle("Table 5.2. Project cash flows (USD millions)"),
  table(["Particulars", "Year 0", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"], cfTableRows, [3.6, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1], { boldRows: [3, 5, 8] }),
  note("Cash flow = EBIT × (1 − tax) + depreciation. A loss year would still save tax against Nvidia’s other profits, so tax is applied to negative EBIT too."),
  image("figures/fig15_project_cash_flows.png", 4.6),
  caption(`**Figure 5.1. Project cash flows and cumulative cash position.** The cumulative line crosses zero after ${num(E.payback, 2)} years (simple payback).`),

  H2("5.2 (a) Time value of money: present value of cash flows"),
  P("A dollar received today is worth more than a dollar received later, because it can be invested to earn a return and because later cash is less certain. Future cash flows are therefore discounted to their present value (PV):"),
  formula("PV = CFₜ ÷ (1 + r)ᵗ"),
  tableTitle("Table 5.3. Present value of the project cash flows (USD millions)"),
  table(["Particulars", "Year 0", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"], pvRows, [3.6, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1], { boldRows: [2, 4] }),
  P(`The present value of the inflows is **USD ${num(E.pv_total)}m** at WACC and USD ${num(ER.pv_total)}m at the risk-adjusted rate, against an outlay of USD ${num(E.outlay)}m.`),

  H2("5.3 (b) Investment evaluation techniques"),
  tableTitle("Table 5.4. Evaluation of the project at WACC"),
  table(["Technique", "Formula", "Calculation", "Result", "Decision rule", "Verdict"], [
    ["Net present value (NPV)", "PV of inflows − outlay", `${num(E.pv_total)} − ${num(E.outlay)}`, `USD ${num(E.npv)}m`, "Accept if NPV > 0", "Accept"],
    ["Internal rate of return (IRR)", "Rate at which NPV = 0", "Solved by trial (bisection)", pct(E.irr, 2), `Accept if IRR > ${pct(N.rate, 2)}`, "Accept"],
    ["Profitability index (PI)", "PV of inflows ÷ outlay", `${num(E.pv_total)} ÷ ${num(E.outlay)}`, num(E.pi, 3), "Accept if PI > 1", "Accept"],
    ["Payback period", "Years until cumulative cash flow ≥ 0", `2 + ${num(-cum[1])} ÷ ${num(cf.cash_flow[2])}`, `${num(E.payback, 2)} years`, `Accept if < ${A.life} years`, "Accept"],
    ["Discounted payback", "As payback, on present values", "From Table 5.3", `${num(E.discounted_payback, 2)} years`, `Accept if < ${A.life} years`, "Accept"],
    ["Accounting rate of return (ARR)", "Average profit after tax ÷ average investment", `${num(E.avg_profit)} ÷ ${num(E.avg_investment)}`, pct(E.arr), `Accept if > ${pct(N.rate, 2)}`, "Accept"],
  ], [2.2, 2.4, 2.2, 1.4, 1.8, 1.1], { leftCols: [1, 2, 4, 5] }),
  note(`Average investment = (initial investment + salvage value) ÷ 2 + working capital = (${num(A.capex)} + 0) ÷ 2 + ${num(A.working_capital)} = ${num(E.avg_investment)}.`),
  P(`All six techniques favour the project. The NPV of USD ${num(E.npv)}m is the amount by which the project would increase Nvidia’s value. The IRR of ${pct(E.irr, 1)} exceeds the WACC by ${num((E.irr - N.rate) * 100, 1)} percentage points, and each dollar invested returns USD ${num(E.pi, 2)} in present value. The simple payback of ${num(E.payback, 2)} years is well inside the five-year life, but the discounted payback of ${num(E.discounted_payback, 2)} years shows that, after allowing for the time value of money, the investment is recovered only in the fifth year. The ARR is an accounting measure that ignores timing, so it is shown for completeness; NPV is the deciding criterion.`),
  image("figures/fig16_npv_profile.png", 4.6),
  caption(`**Figure 5.2. NPV profile.** NPV falls as the discount rate rises and reaches zero at the IRR of ${pct(E.irr, 1)}.`),

  H2("5.4 (c) Risk consideration: risk-adjusted discount rate"),
  P(`The WACC reflects the risk of Nvidia’s existing business. Renting out computing capacity is a new business with new competitors (large cloud providers) and uncertain pricing, so a premium of ${pct(A.risk_premium, 0)} is added to the discount rate: **${pct(N.rate, 2)} + ${pct(A.risk_premium, 0)} = ${pct(N.radr, 2)}**.`),
  tableTitle("Table 5.5. Normal and risk-adjusted evaluation"),
  table(["Measure", `Normal (WACC ${pct(N.rate, 2)})`, `Risk-adjusted (${pct(N.radr, 2)})`], [
    ["PV of inflows (USD m)", num(E.pv_total), num(ER.pv_total)],
    ["NPV (USD m)", num(E.npv), num(ER.npv)],
    ["Profitability index", num(E.pi, 3), num(ER.pi, 3)],
    ["Discounted payback (years)", num(E.discounted_payback, 2), num(ER.discounted_payback, 2)],
    ["IRR compared with the rate", `${pct(E.irr, 2)} > ${pct(N.rate, 2)}`, `${pct(E.irr, 2)} > ${pct(N.radr, 2)}`],
  ], [4, 3, 3]),
  P(`The risk adjustment cuts the NPV by ${pct(1 - ER.npv / E.npv, 0)}, from USD ${num(E.npv)}m to USD ${num(ER.npv)}m, but it stays positive: the project is acceptable even after charging for its extra risk. The margin is thinner, however, which is why the sensitivity and scenario analysis below matter.`),

  H2("5.5 (d) Sensitivity analysis"),
  P("Each input is changed by 10% while everything else stays at the base case (discounted at WACC). When sales fall, variable costs fall with them; when costs rise, both variable and fixed cash costs rise by 10%."),
  tableTitle("Table 5.6. Sensitivity analysis (USD millions)"),
  table(["Case", "NPV", "Change in NPV", "IRR", "PI", "Payback (years)"], [
    ["Base case", num(E.npv), "–", pct(E.irr), num(E.pi, 3), num(E.payback, 2)],
    ["Sales decrease by 10%", num(sens["Sales -10%"].npv), pct(pctChange(E.npv, sens["Sales -10%"].npv), 0), pct(sens["Sales -10%"].irr), num(sens["Sales -10%"].pi, 3), num(sens["Sales -10%"].payback, 2)],
    ["Costs increase by 10%", num(sens["Costs +10%"].npv), pct(pctChange(E.npv, sens["Costs +10%"].npv), 0), pct(sens["Costs +10%"].irr), num(sens["Costs +10%"].pi, 3), num(sens["Costs +10%"].payback, 2)],
  ], [3, 1.5, 1.8, 1.3, 1.3, 1.8]),
  P(`A 10% fall in sales cuts the NPV by ${pct(-pctChange(E.npv, sens["Sales -10%"].npv), 0)}, while a 10% rise in costs cuts it by ${pct(-pctChange(E.npv, sens["Costs +10%"].npv), 0)}. The project is therefore **most sensitive to sales**: revenue is the larger number, and fixed costs and depreciation do not shrink when sales fall. In both cases the NPV stays positive, so the project survives a moderate shock to either variable on its own. Management should focus on securing demand, for example with multi-year capacity contracts.`),

  H2("5.6 (e) Scenario analysis"),
  P("Scenarios change several inputs together. Probabilities are assumed to weight the outcomes."),
  tableTitle("Table 5.7. Scenario analysis (USD millions, at WACC)"),
  table(["Scenario", "Assumptions", "Probability", "NPV", "IRR", "PI", "Payback (years)"], [
    ["Best case", "Revenue +20%, variable cost 32%", pct(scen["Best case"].prob, 0), num(scen["Best case"].npv), pct(scen["Best case"].irr), num(scen["Best case"].pi, 3), num(scen["Best case"].payback, 2)],
    ["Most likely case", "Base case", pct(scen["Most likely case"].prob, 0), num(scen["Most likely case"].npv), pct(scen["Most likely case"].irr), num(scen["Most likely case"].pi, 3), num(scen["Most likely case"].payback, 2)],
    ["Worst case", "Revenue −25%, variable cost 38%", pct(scen["Worst case"].prob, 0), num(scen["Worst case"].npv), pct(scen["Worst case"].irr), num(scen["Worst case"].pi, 3), num(scen["Worst case"].payback, 2)],
    ["Expected value", "Probability-weighted", "100%", num(N.expected_npv), "", "", ""],
  ], [1.8, 3, 1.3, 1.2, 1.1, 1, 1.4], { leftCols: [1], boldRows: [3] }),
  image("figures/fig17_npv_scenarios.png", 4.6),
  caption("**Figure 5.3. NPV under the sensitivity and scenario cases.** Only the worst case gives a negative NPV."),
  P(`The expected NPV is **USD ${num(N.expected_npv)}m**, positive. The standard deviation of NPV across the scenarios is USD ${num(N.sd_npv)}m, a coefficient of variation of ${num(cv, 2)}, so the outcome is uncertain. In the worst case, with demand 25% below plan, the project loses USD ${num(-scen["Worst case"].npv)}m in present value and its IRR (${pct(scen["Worst case"].irr)}) falls below the cost of capital. The upside (USD ${num(scen["Best case"].npv)}m) is larger than the downside, which supports going ahead, but with safeguards: building capacity in stages and signing customer contracts before each stage.`),
];

// =====================================================================
// Step 4: financing and capital structure
// =====================================================================
const planRows = [PLAN_A, PLAN_B, PLAN_C].map((k) => [
  k.replace(/^Plan (\w): /, "Plan $1 ("), // e.g. "Plan B (70% equity, 30% debt"
  num(plans[k].beta, 2), pct(plans[k].ke, 2), pct(plans[k].wacc_ni, 2), pct(plans[k].wacc_mm, 2),
]).map((r) => [r[0] + ")", ...r.slice(1)]);
const levRows = [PLAN_A, PLAN_B, PLAN_C].map((k) => [
  k.replace(/^Plan (\w): .*/, "Plan $1"), num(lev[k].debt), num(lev[k].equity), num(lev[k].interest, 1),
  num(lev[k].dfl_base, 3), pct(lev[k].roe_base), pct(lev[k].roe_worst),
]);

const financing = [
  H1("6. Step 4: Financing and capital structure decision", true),
  H2("6.1 (a) Sources of finance: proposed financing mix"),
  P(`The project needs USD ${num(E.outlay)}m (investment plus working capital). Three financing plans were compared:`),
  tableTitle("Table 6.1. Financing plans for the project (USD millions)"),
  table(["Plan", "Equity (retained earnings)", "Debt (new senior notes)", "Debt share"], [
    ["Plan A: all equity", num(lev[PLAN_A].equity), num(lev[PLAN_A].debt), "0%"],
    ["Plan B: proposed mix", num(lev[PLAN_B].equity), num(lev[PLAN_B].debt), "30%"],
    ["Plan C: equal mix", num(lev[PLAN_C].equity), num(lev[PLAN_C].debt), "50%"],
  ], [3, 2.5, 2.5, 1.5], { shadeRows: [1] }),
  bullet(`**Equity:** internal funds (retained earnings). Nvidia’s retained earnings were USD ${num(S26.retained_earnings)}m at the end of FY2026, and it held USD ${num(liquid26)}m in cash and securities, so no new shares need to be issued (which would avoid issue costs and dilution).`),
  bullet(`**Debt:** new five-year senior unsecured notes, assumed to be priced at the Treasury yield plus ${pct(A.new_debt_spread, 2)}, i.e. ${pct(C.kd_new_pre, 2)} before tax. The five-year term matches the project life.`),
  bullet("**Hybrid instruments (optional):** convertible notes could lower the coupon, but they would dilute shareholders if converted. Nvidia has no need for them, so they are not proposed."),

  H2("6.2 (b) Cost of capital"),
  H3("Cost of equity (Ke): capital asset pricing model"),
  P("The capital asset pricing model (CAPM) [9] prices equity by its market risk (beta):"),
  formula("Ke = Rf + β × (Rm − Rf)"),
  P(`With a risk-free rate of ${pct(N.market.risk_free, 2)} (10-year U.S. Treasury, 26 Oct 2026) [3], a beta of ${num(N.market.beta, 2)} (5-year monthly) [4] and an equity risk premium of ${pct(N.market.erp, 2)} (October 2026) [5]: **Ke = ${pct(N.market.risk_free, 2)} + ${num(N.market.beta, 2)} × ${pct(N.market.erp, 2)} = ${pct(C.ke, 2)}**. The high beta reflects how strongly Nvidia’s share price moves with the market.`),
  H3("Cost of debt (Kd)"),
  formula("Kd (after tax) = Interest ÷ Average debt × (1 − t)"),
  P(`Existing debt: interest expense of USD ${num(S26.interest_expense)}m on average borrowings of USD ${num(C.avg_debt)}m gives a pre-tax cost of ${pct(C.kd_pre, 2)}; after tax at ${pct(C.tax_rate)}, **Kd = ${pct(C.kd, 2)}**. This is well below today’s market rates, because existing notes keep the fixed coupons set when they were issued. New debt would cost ${pct(C.kd_new_pre, 2)} before tax, or **${pct(C.kd_new, 2)}** after tax, and this marginal cost is used for the project.`),
  H3("Weighted average cost of capital (WACC)"),
  formula("WACC = We × Ke + Wd × Kd"),
  tableTitle("Table 6.2. WACC of Nvidia today"),
  table(["Basis", "Weight of equity", "Weight of debt", "Ke", "Kd (after tax)", "WACC"], [
    ["Book values (FY2026)", pct(1 - C.w_debt_book, 2), pct(C.w_debt_book, 2), pct(C.ke, 2), pct(C.kd, 2), pct(C.wacc_book, 2)],
    ["Market values (26 Oct 2026)", pct(1 - C.w_debt_market, 2), pct(C.w_debt_market, 2), pct(C.ke, 2), pct(C.kd, 2), pct(C.wacc_market, 2)],
  ], [3, 1.6, 1.6, 1.2, 1.4, 1.2]),
  P(`At market values, debt is less than 0.2% of Nvidia’s capital, so its WACC (${pct(C.wacc_market, 2)}) is almost the same as its cost of equity. For the project, the WACC of the proposed financing mix (Plan B) is used: **${pct(N.rate, 2)}** (Table 6.3).`),

  H2("6.3 (c) Capital structure theories"),
  P("The theories differ on whether borrowing changes the cost of capital. Table 6.3 applies two of them to the three plans. Under the NI approach Ke stays fixed. Under MM with taxes, Ke rises with debt because shareholders bear more financial risk (Plan A uses the unlevered beta of ${num(C.beta_unlevered, 3)}, so its Ke is ${pct(plans[PLAN_A].ke, 2)}); the levered beta is found with Hamada’s formula [8]: βL = βU × (1 + (1 − t) × D/E)."),
  tableTitle("Table 6.3. Cost of capital of the project under each financing plan"),
  table(["Plan", "Levered beta", "Ke (MM, rises with debt)", "WACC: NI approach", "WACC: MM with taxes"], planRows, [3.6, 1.4, 1.8, 1.6, 1.6], { shadeRows: [1] }),
  bullet(`**Net income (NI) approach** [6]: the costs of debt and equity stay constant whatever the mix, so replacing expensive equity with cheap debt always lowers WACC (from ${pct(plans[PLAN_A].wacc_ni, 2)} to ${pct(plans[PLAN_C].wacc_ni, 2)}) and raises firm value. Taken literally, the firm should be financed almost entirely by debt, which ignores the extra risk debt places on shareholders.`),
  bullet("**Net operating income (NOI) approach** [6]: the overall cost of capital is constant. Any saving from cheaper debt is cancelled by a higher cost of equity, so the financing mix does not change firm value. Applied here, Nvidia’s value depends on the project’s cash flows, not on how it is financed."),
  bullet("**Traditional theory:** moderate borrowing lowers WACC because debt is cheaper, but beyond some point both lenders and shareholders demand higher returns, and WACC rises again. There is therefore an optimal, moderate level of debt."),
  bullet(`**Modigliani–Miller (MM)** [7, 10]: without taxes, firm value is independent of capital structure (Proposition I), and the cost of equity rises linearly with leverage (Proposition II), exactly offsetting the cheaper debt. With corporate taxes, interest is tax-deductible, so debt adds a tax shield. Table 6.3 shows this: Ke rises from ${pct(plans[PLAN_A].ke, 2)} to ${pct(plans[PLAN_C].ke, 2)}, but WACC still falls slightly, from ${pct(plans[PLAN_A].wacc_mm, 2)} to ${pct(plans[PLAN_C].wacc_mm, 2)}.`),
  P(`**Application.** The realistic view (MM with taxes, limited by the traditional theory’s rising costs of financial distress) gives a small gain from debt: Plan B lowers WACC by ${num((plans[PLAN_A].wacc_mm - plans[PLAN_B].wacc_mm) * 100, 2)} percentage points compared with all equity. The gain is small because Nvidia’s tax rate is only ${pct(C.tax_rate, 0)}, which limits the tax shield. Plan C saves a further ${num((plans[PLAN_B].wacc_mm - plans[PLAN_C].wacc_mm) * 100, 2)} points but makes the worst-case loss to shareholders much larger (Section 6.4).`),

  H2("6.4 (d) Leverage analysis"),
  formula("Degree of financial leverage (DFL) = EBIT ÷ (EBIT − Interest)"),
  P(`For Nvidia as a whole, DFL was ${num(N.leverage.company.FY2025, 4)} in FY2025 and ${num(N.leverage.company.FY2026, 4)} in FY2026: a 1% change in operating income changes profit before tax by almost exactly 1%. Nvidia’s interest is so small that it has essentially no financial leverage.`),
  P(`For the project, Table 6.4 compares the return to equity holders (profit after interest and tax ÷ equity invested) in the base case at its peak (year 3, EBIT USD ${num(lev[PLAN_A].ebit_base)}m) and in the weakest year of the worst case (year 1, EBIT USD ${num(lev[PLAN_A].ebit_worst)}m).`),
  tableTitle("Table 6.4. Effect of leverage on the project’s return and risk (USD millions)"),
  table(["Plan", "Debt", "Equity", "Interest", "DFL (base)", "Return on equity: base", "Return on equity: worst"], levRows, [1.4, 1.2, 1.2, 1.2, 1.3, 1.9, 1.9], { shadeRows: [1] }),
  P(`Debt magnifies both outcomes. In the base case the return on equity rises from ${pct(lev[PLAN_A].roe_base)} (all equity) to ${pct(lev[PLAN_B].roe_base)} (Plan B) and ${pct(lev[PLAN_C].roe_base)} (Plan C). In the worst case the loss to equity grows from ${pct(lev[PLAN_A].roe_worst)} to ${pct(lev[PLAN_B].roe_worst)} and ${pct(lev[PLAN_C].roe_worst)}. This is financial risk: higher expected return for shareholders comes with a wider spread of outcomes.`),
  P(`**Justification of Plan B.** A 30% debt share captures most of the available tax benefit and raises the expected return on equity, while keeping DFL close to 1 (${num(lev[PLAN_B].dfl_base, 3)}). Even after borrowing USD ${num(lev[PLAN_B].debt)}m, Nvidia’s borrowings would be about USD ${num(R26.total_debt + lev[PLAN_B].debt)}m against equity of USD ${num(S26.equity)}m, a ratio of ${num((R26.total_debt + lev[PLAN_B].debt) / S26.equity, 2)}, so its borrowing remains very low. Plan C adds little extra value but deepens the worst-case loss to equity from ${pct(lev[PLAN_B].roe_worst)} to ${pct(lev[PLAN_C].roe_worst)}.`),
];

// =====================================================================
// Step 5: insurance and risk mitigation
// =====================================================================
const insurance = [
  H1("7. Step 5: Role of insurance and risk mitigation"),
  P("Insurance transfers the financial cost of a risk to an insurer in return for a premium. It cannot remove business risks such as weak demand, but it protects the company against sudden, large losses that would otherwise disrupt its cash flows and financing."),
  tableTitle("Table 7.1. Key risks and suitable insurance products"),
  table(["Risk type", "Specific risk", "Suitable insurance or mitigation", "How it helps"], [
    ["Operational", "Fire, flood or earthquake damaging the data halls and GPU servers", "Property (all-risk) insurance including earthquake cover", "Pays to repair or replace the USD 5,000m of equipment"],
    ["Operational", "Shutdown of the data centre after damage", "Business interruption insurance", "Replaces lost profit and covers fixed costs during repairs"],
    ["Operational", "Disruption at a foundry or supplier (Nvidia is fabless)", "Contingent business interruption insurance", "Covers profit lost when a key supplier’s site is damaged"],
    ["Operational", "Breakdown of cooling, power or servers", "Machinery breakdown (equipment) insurance; maintenance contracts", "Funds repairs and limits downtime"],
    ["Operational", "Damage to GPUs in transit", "Marine cargo (transit) insurance", "Covers loss or damage between factory and site"],
    ["Operational", "Cyber attack or data breach on a cloud that holds customer data", "Cyber liability insurance", "Covers breach response, customer claims and lost income"],
    ["Project", "Service failures causing losses to cloud customers", "Professional indemnity (errors and omissions) insurance", "Pays customer claims for service failures"],
    ["Project", "Demand below plan (worst case)", "Not insurable: multi-year customer contracts and staged investment", "Locks in revenue before capacity is built"],
    ["Financial", "Customer fails to pay for capacity used", "Trade credit insurance", "Protects receivables and cash flow"],
    ["Financial", "Claims against directors over investment decisions", "Directors and officers (D&O) liability insurance", "Protects management and the company’s balance sheet"],
    ["Financial", "Rising interest rates on the new debt", "Not insurable: fixed-rate notes or an interest rate swap", "Keeps the cost of debt at the planned rate"],
  ], [1.3, 2.6, 2.6, 2.5], { leftCols: [1, 2, 3] }),
  H2("7.1 How insurance supports financial stability"),
  bullet("**Protects cash flows.** A large uninsured loss, such as the loss of a data hall, would wipe out several years of the project’s expected cash flows. Insurance turns that uncertain large loss into a small, predictable premium."),
  bullet("**Protects the investment decision.** The NPV in Chapter 5 assumes the equipment runs for five years. Property and business interruption cover make that assumption safer, so the risk premium in the discount rate does not have to cover these insurable events."),
  bullet("**Supports financing.** Lenders usually require insured assets as a condition of lending, so insurance makes the debt in Plan B easier and cheaper to raise."),
  bullet("**Complements other risk management.** Risks that cannot be insured, such as demand and interest rates, are reduced by contracts, staged investment and fixed-rate borrowing."),
];

// =====================================================================
// Final recommendation and conclusion
// =====================================================================
const conclusion = [
  H1("8. Final recommendation and conclusion"),
  H2("8.1 Investment decision: accept"),
  P(`**Accept the AI compute cloud project.** It has an NPV of USD ${num(E.npv)}m at the ${pct(N.rate, 2)} WACC and USD ${num(ER.npv)}m even at the ${pct(N.radr, 2)} risk-adjusted rate. Its IRR of ${pct(E.irr, 1)} exceeds both rates, its profitability index is ${num(E.pi, 2)}, and it pays back in ${num(E.payback, 2)} years. The probability-weighted NPV across the scenarios is USD ${num(N.expected_npv)}m.`),
  P(`The decision is not risk-free. The project is most sensitive to sales, and in the worst case (demand 25% below plan) its NPV is USD ${num(scen["Worst case"].npv)}m. It should therefore be **built in stages**, each stage approved only after customer contracts cover a large part of its capacity.`),
  H2("8.2 Optimal financing: Plan B"),
  P(`**Finance the project with 70% internal equity (USD ${num(lev[PLAN_B].equity)}m from retained earnings) and 30% new five-year fixed-rate senior notes (USD ${num(lev[PLAN_B].debt)}m).** This mix gives a WACC of ${pct(plans[PLAN_B].wacc_mm, 2)} against ${pct(plans[PLAN_A].wacc_mm, 2)} for all equity, raises the expected return on equity from ${pct(lev[PLAN_A].roe_base)} to ${pct(lev[PLAN_B].roe_base)}, and keeps financial leverage low (DFL ${num(lev[PLAN_B].dfl_base, 2)}). This follows MM with taxes and the traditional theory: a moderate amount of debt gives a tax benefit without significant financial distress risk.`),
  H2("8.3 Risk management summary"),
  bullet("**Insure** the equipment and data halls (property, earthquake, machinery breakdown, transit), the income they generate (business interruption and contingent business interruption) and the data they hold (cyber liability)."),
  bullet("**Contract** for demand before building each stage of capacity, as the project is most sensitive to sales."),
  bullet("**Fix** the interest rate on the new notes and keep total borrowings well below equity."),
  bullet("**Monitor** the warning signs found in the SemiFin study: operating margin and interest coverage weaken before liquidity does."),
  H2("8.4 Conclusion"),
  P(`Nvidia is an exceptionally strong company: in FY2026 it earned a net margin of ${pct(R26.net_profit_margin)} and an ROA of ${pct(R26.roa)}, held current assets of ${times(R26.current_ratio)} its current liabilities, and covered its interest ${num(R26.interest_coverage, 0)} times. This strength means the proposed expansion can be judged on its own merits. On the evidence of NPV, IRR and the scenario analysis, the project adds value and should be accepted, financed with a moderate share of debt and protected with insurance. The wider SemiFin study shows that such strength is rare in the semiconductor sector, where about a third of companies are in financial distress in a typical year.`),
];

// =====================================================================
// References
// =====================================================================
const refs = [
  "U.S. Securities and Exchange Commission. Financial Statement Data Sets, quarterly files 2025 Q1 and 2026 Q1. https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets (accessed 27 October 2026).",
  "NVIDIA Corporation. Form 10-K for the fiscal years ended January 2025 and January 2026. SEC EDGAR, accession numbers 0001045810-25-000023 and 0001045810-26-000021. https://www.sec.gov/Archives/edgar/data/1045810/ (accessed 28 October 2026).",
  "Board of Governors of the Federal Reserve System. Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity (DGS10), retrieved from FRED, Federal Reserve Bank of St. Louis. https://fred.stlouisfed.org/series/DGS10 (value for 26 October 2026, accessed 28 October 2026).",
  "Yahoo Finance. NVIDIA Corporation (NVDA): Beta (5Y Monthly) and Valuation Measures. https://finance.yahoo.com/quote/NVDA/ (accessed 28 October 2026).",
  "Damodaran, A. Implied equity risk premium, 1 October 2026. Damodaran Online, NYU Stern School of Business. https://pages.stern.nyu.edu/~adamodar/ (accessed 28 October 2026).",
  "Durand, D. (1952). Costs of debt and equity funds for business: Trends and problems of measurement. In Conference on Research in Business Finance (pp. 215–262). National Bureau of Economic Research. https://www.nber.org/books-and-chapters/conference-research-business-finance/costs-debt-and-equity-funds-business-trends-and-problems-measurement",
  "Modigliani, F., & Miller, M. H. (1958). The cost of capital, corporation finance and the theory of investment. American Economic Review, 48(3), 261–297. https://www.jstor.org/stable/1809766",
  "Hamada, R. S. (1972). The effect of the firm’s capital structure on the systematic risk of common stocks. The Journal of Finance, 27(2), 435–452. https://doi.org/10.1111/j.1540-6261.1972.tb00971.x",
  "Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. The Journal of Finance, 19(3), 425–442. https://doi.org/10.1111/j.1540-6261.1964.tb02865.x",
  "Modigliani, F., & Miller, M. H. (1963). Corporate income taxes and the cost of capital: A correction. American Economic Review, 53(3), 433–443.",
  "SemiFin project report: Financial Ratio Analysis and Distress Prediction of Semiconductor Companies: A Comparative Study of Nvidia, AMD, Intel and Wolfspeed Using SEC XBRL Data (2026). Source of Chapter 2 and the sector medians.",
];
const references = [
  H1("References"),
  ...refs.map((r) => new Paragraph({ numbering: { reference: "refs", level: 0 }, spacing: { after: 100, line: 276 }, children: [new TextRun({ text: r, size: 22 })] })),
];

// =====================================================================
// Document
// =====================================================================
const doc = new Document({
  creator: "SemiFin",
  title: "SemiFin - A Semiconductor Financial Analysis Report",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: ACCENT }, paragraph: { spacing: { before: 0, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: ACCENT }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, italics: true, font: FONT }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
      ] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 720 } } } }] },
    ],
  },
  sections: [
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
      children: cover },
    {
      properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "SemiFin - A Semiconductor Financial Analysis Report", size: 18, italics: true, color: "7F7F7F" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] }) },
      children: [...index, ...intro, ...background, ...profile, ...statements, ...capbud, ...financing, ...insurance, ...conclusion, ...references],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("saved", OUT, buf.length, "bytes");
});
