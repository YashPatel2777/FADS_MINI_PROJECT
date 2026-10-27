"""
Phase 3: check computed statement values against the case companies' 10-K filings.

For each chosen filing, the SEC's rendered financial statements (the "R"
pages EDGAR builds for every 10-K, listed in the filing's FilingSummary.xml)
are downloaded once into data/raw/edgar_statements/<adsh>/. The balance sheet
and income statement are parsed into (line label, current-year value) rows,
and each computed value is looked up among them: a match within rounding
shows both that the number is right and which line of the 10-K it came from.
"""

import re
import time
import urllib.request
import warnings
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{file}"

# Items checked, the statement each appears on, and words used to show the
# statement's own line when no exact match is found.
CHECK_ITEMS = {
    "revenue": ("income", ["revenue", "net sales", "sales"]),
    "gross_profit": ("income", ["gross"]),
    "operating_income": ("income", ["operating income", "operating loss", "operating (loss)", "income from operations", "loss from operations", "operating income (loss)"]),
    "net_income": ("income", ["net income", "net loss", "net (loss)"]),
    "total_assets": ("balance", ["total assets"]),
    "current_assets": ("balance", ["total current assets"]),
    "current_liabilities": ("balance", ["total current liabilities"]),
    "liabilities_and_equity": ("balance", ["total liabilities and"]),
    "equity": ("balance", ["total stockholders", "total shareholders", "total equity"]),
    "cash": ("balance", ["cash and cash equivalents"]),
    "inventory": ("balance", ["inventor"]),
}


def filing_url(cik, adsh, file):
    return ARCHIVE.format(cik=int(cik), acc=adsh.replace("-", ""), file=file)


def _get(url, user_agent):
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    time.sleep(0.3)  # stay well under the SEC's request-rate limit
    return data


def download_statements(cik, adsh, out_dir, user_agent):
    """Download FilingSummary.xml plus the balance sheet, income statement and cash flow R pages.

    Returns {"balance": path, "income": path, "cash_flow": path}. Files already
    on disk are reused.
    """
    folder = Path(out_dir) / adsh
    folder.mkdir(parents=True, exist_ok=True)
    summary_path = folder / "FilingSummary.xml"
    if not summary_path.exists():
        summary_path.write_bytes(_get(filing_url(cik, adsh, "FilingSummary.xml"), user_agent))
    with warnings.catch_warnings():
        # FilingSummary is XML; the built-in HTML parser reads it fine here.
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(summary_path.read_bytes(), "html.parser")

    found = {}
    for report in soup.find_all("report"):
        cat = report.find("menucategory")
        name = report.find("shortname")
        html = report.find("htmlfilename")
        if not (cat and name and html) or cat.text.strip() != "Statements":
            continue
        n = name.text.lower()
        if "parenthetical" in n:
            continue
        if "balance sheet" in n or "financial position" in n:
            found.setdefault("balance", html.text.strip())
        elif "cash flow" in n:
            found.setdefault("cash_flow", html.text.strip())
        elif any(w in n for w in ["operations", "income", "earnings"]) and "comprehensive" not in n:
            found.setdefault("income", html.text.strip())

    paths = {}
    for kind, file in found.items():
        path = folder / file
        if not path.exists():
            path.write_bytes(_get(filing_url(cik, adsh, file), user_agent))
        paths[kind] = path
    return paths


def _number(text):
    """'$ (1,329.5)' -> -1329.5; returns None for blanks."""
    t = text.replace("$", "").replace(",", "").replace("\xa0", "").strip()
    if not t:
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").strip()
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _value_column(table):
    """Index of the current full-year column.

    Income statements can start with quarterly columns ("3 Months Ended"
    group) before the "12 Months Ended" group, so the first column under a
    "12 Months" header is used. Balance sheets have no period groups; their
    first column is the latest balance sheet date.
    """
    first_row = table.find("tr").find_all("th")[1:]  # skip the title cell
    groups = []
    for th in first_row:
        groups += [th.get_text(" ", strip=True)] * int(th.get("colspan", 1))
    for i, g in enumerate(groups):
        if "12 Months" in g:
            return i
    return 0


def parse_statement(path):
    """Parse an R page into rows of (label, current-year value in USD millions).

    The money scale comes from the "$ in Millions" / "$ in Thousands" part of
    the header (a "shares in Millions" note refers to share counts only);
    with neither, values are plain dollars.
    """
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")  # older R pages are Windows-encoded (curly apostrophes)
    soup = BeautifulSoup(text, "html.parser")
    table = soup.find("table", class_="report")
    header = table.find("th").get_text(" ", strip=True)
    scale = re.search(r"\$\s*in\s*(Millions|Thousands)", header)
    to_millions = {"Millions": 1.0, "Thousands": 0.001}[scale.group(1)] if scale else 1e-6
    col = _value_column(table)
    rows = []
    for tr in table.find_all("tr"):
        label = tr.find("td", class_="pl")
        cells = tr.find_all("td", class_=re.compile(r"^(nump|num|text)$"))
        if label is None or len(cells) <= col:
            continue
        value = _number(cells[col].get_text(" ", strip=True))
        if value is not None:
            rows.append({"label": label.get_text(" ", strip=True), "value_musd": value * to_millions})
    return pd.DataFrame(rows), header, to_millions


def check_filing(row, statement_paths, items=CHECK_ITEMS, absolute=False):
    """Compare one company-year's computed items with its 10-K statements.

    A value matches when a statement line is within half a reported unit
    (rounding), e.g. 0.5 for statements in millions. Returns one row per item.
    absolute=True compares sizes only: cash flow statements show payments
    such as capex in brackets (negative), while the XBRL payment tags are
    positive. Items that are blank in `row` are skipped.
    """
    parsed = {kind: parse_statement(p) for kind, p in statement_paths.items()}
    out = []
    for item, (kind, words) in items.items():
        ours = row[item]
        if pd.isna(ours):
            continue
        rec = {"item": item, "computed_musd": ours, "statement": kind}
        if kind not in parsed:
            rec.update(status="statement not found")
            out.append(rec)
            continue
        lines, _, to_millions = parsed[kind]
        if absolute:
            lines = lines.assign(value_musd=lines["value_musd"].abs())
            ours = abs(ours)
        tol = 0.5 * to_millions + 1e-9
        hit = lines[(lines["value_musd"] - ours).abs() <= tol]
        # Several lines can share a value (total assets = total liabilities
        # and equity); show the one whose label fits the item when possible.
        named = hit[hit["label"].str.lower().str.contains("|".join(map(re.escape, words)))]
        hit = named if len(named) else hit
        if len(hit):
            rec.update(status="match", tenk_line=hit["label"].iloc[0], tenk_value_musd=hit["value_musd"].iloc[0])
        else:
            near = lines[lines["label"].str.lower().str.contains("|".join(map(re.escape, words)))]
            rec.update(status="MISMATCH",
                       tenk_line=near["label"].iloc[0] if len(near) else "(no similar line)",
                       tenk_value_musd=near["value_musd"].iloc[0] if len(near) else None)
        out.append(rec)
    return pd.DataFrame(out)
