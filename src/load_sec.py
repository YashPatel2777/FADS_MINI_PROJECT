"""
Phase 1 (data collection): read the SEC Financial Statement Data Sets.

Each quarterly zip in data/raw holds tab-separated files (field definitions
checked against readme.htm inside the zips):
- sub.txt: one row per submission (filing): adsh, cik, name, sic, form, period, ...
- num.txt: one row per reported number: adsh, tag, version, ddate, qtrs, uom,
  segments, coreg, value, footnote.

The zips are read in place and never extracted or modified, so data/raw stays
exactly as downloaded.
"""

import csv
import re
import zipfile
from pathlib import Path

import pandas as pd

# Columns the readme defines for each file. Every quarter is checked against
# these before stacking, so a layout change would stop the run instead of
# silently misaligning columns.
SUB_COLUMNS = [
    "adsh", "cik", "name", "sic", "countryba", "stprba", "cityba", "zipba",
    "bas1", "bas2", "baph", "countryma", "stprma", "cityma", "zipma", "mas1",
    "mas2", "countryinc", "stprinc", "ein", "former", "changed", "afs", "wksi",
    "fye", "form", "period", "fy", "fp", "filed", "accepted", "prevrpt",
    "detail", "instance", "nciks", "aciks",
]
NUM_COLUMNS = [
    "adsh", "tag", "version", "ddate", "qtrs", "uom", "segments", "coreg",
    "value", "footnote",
]

# The sub columns we keep for the filings table. Address and contact fields
# are not needed for the analysis.
SUB_KEEP = [
    "adsh", "cik", "name", "sic", "former", "changed", "fye", "form",
    "period", "fy", "fp", "filed", "accepted", "prevrpt", "nciks", "source_quarter",
]

# num columns kept. The footnote text is dropped because it is long and not used.
NUM_KEEP = ["adsh", "tag", "version", "ddate", "qtrs", "uom", "segments", "coreg", "value"]

# Shared read settings for every SEC text file:
# - dtype=str: read everything as text first so codes such as CIK, SIC and
#   dates are not mangled (e.g. leading zeros); convert types explicitly later.
# - keep_default_na=False + na_values=[""]: only a truly empty field is
#   missing. Without this pandas would turn the text "NA" (Namibia's country
#   code) or "NULL" into missing values.
# - quoting=QUOTE_NONE (sub only): sub.txt uses no quote characters, so a
#   stray " inside a company name must be read literally.
READ_KW = dict(
    sep="\t", dtype=str, keep_default_na=False, na_values=[""],
    quoting=csv.QUOTE_NONE, encoding="utf-8",
)

# num.txt is different: when a segments value itself contains tabs (seen in
# 2022q4 for investment-company holdings, e.g. "InvestmentIdentifier=...\t..."),
# the SEC wraps it in double quotes. QUOTE_MINIMAL reads such a field as one
# value; the rows-parsed vs lines-in-file check confirms nothing was merged.
NUM_READ_KW = {**READ_KW, "quoting": csv.QUOTE_MINIMAL, "quotechar": '"'}

QUARTER_PATTERN = re.compile(r"^(\d{4})q([1-4])\.zip$")


def list_quarter_zips(raw_dir):
    """Return the quarterly zip paths in data/raw sorted by time (e.g. 2014q3 ... 2026q3)."""
    paths = [p for p in Path(raw_dir).iterdir() if QUARTER_PATTERN.match(p.name)]
    return sorted(paths, key=lambda p: p.stem)  # "2014q3" < "2015q1" sorts correctly as text


def _header(zf, member):
    """Read only the first line (column names) of a file inside an open zip."""
    with zf.open(member) as fh:
        return fh.readline().decode("utf-8").rstrip("\r\n").split("\t")


def _count_data_lines(zf, member, block=64 * 1024 * 1024):
    """Count data rows (newlines minus the header) by streaming raw bytes.

    Used to prove that the parser read every row: if pandas returns fewer rows
    than there are lines, something (e.g. an embedded newline) broke parsing.
    """
    n = 0
    with zf.open(member) as fh:
        while chunk := fh.read(block):
            n += chunk.count(b"\n")
    return n - 1


def check_layouts(zip_paths):
    """Check every quarter has the sub and num columns the readme defines.

    Returns one row per quarter with True/False per file, so the result can be
    shown in the notebook as evidence that the quarters can be stacked.
    """
    rows = []
    for p in zip_paths:
        with zipfile.ZipFile(p) as zf:
            rows.append({
                "quarter": p.stem,
                "sub_columns_ok": _header(zf, "sub.txt") == SUB_COLUMNS,
                "num_columns_ok": _header(zf, "num.txt") == NUM_COLUMNS,
            })
    return pd.DataFrame(rows)


def read_sub(zip_path):
    """Read sub.txt from one quarter, keep the useful columns, tag the source quarter.

    Also returns the raw line count so the caller can confirm nothing was lost.
    """
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("sub.txt") as fh:
            sub = pd.read_csv(fh, **READ_KW)
        n_lines = _count_data_lines(zf, "sub.txt")
    sub["source_quarter"] = zip_path.stem
    return sub[SUB_KEEP], n_lines


def load_all_sub(zip_paths):
    """Stack sub.txt from every quarter into one table.

    Returns (sub, check) where check lists rows parsed vs lines in the file
    for each quarter; the two must match.
    """
    frames, checks = [], []
    for p in zip_paths:
        sub, n_lines = read_sub(p)
        frames.append(sub)
        checks.append({"quarter": p.stem, "rows_parsed": len(sub), "lines_in_file": n_lines})
    sub = pd.concat(frames, ignore_index=True)

    # Convert the fields we filter or sort on into proper types.
    sub["cik"] = sub["cik"].astype("int64")
    sub["sic"] = pd.to_numeric(sub["sic"]).astype("Int64")   # nullable: sic may be blank
    sub["period"] = pd.to_datetime(sub["period"], format="%Y%m%d")
    sub["filed"] = pd.to_datetime(sub["filed"], format="%Y%m%d")
    sub["fy"] = pd.to_numeric(sub["fy"]).astype("Int64")     # nullable: fy may be blank
    sub["prevrpt"] = sub["prevrpt"].astype("int64")
    return sub, pd.DataFrame(checks)


def load_num_for_filings(zip_paths, adsh_keep, chunksize=2_000_000):
    """Read num.txt from every quarter and keep only rows of the selected filings.

    num.txt is about 500 MB per quarter, so it is read in chunks of
    `chunksize` rows; each chunk is filtered to the wanted accession numbers
    (adsh) before the next one is read. Only the filtered rows stay in memory.

    Returns (num, check): the stacked rows and, per quarter, the rows parsed vs
    lines in the file plus how many rows were kept.
    """
    adsh_keep = set(adsh_keep)
    frames, checks = [], []
    for p in zip_paths:
        parsed = kept = 0
        with zipfile.ZipFile(p) as zf:
            with zf.open("num.txt") as fh:
                for chunk in pd.read_csv(fh, chunksize=chunksize, **NUM_READ_KW):
                    parsed += len(chunk)
                    chunk = chunk.loc[chunk["adsh"].isin(adsh_keep), NUM_KEEP]
                    kept += len(chunk)
                    chunk["source_quarter"] = p.stem
                    frames.append(chunk)
            n_lines = _count_data_lines(zf, "num.txt")
        checks.append({"quarter": p.stem, "rows_parsed": parsed,
                       "lines_in_file": n_lines, "rows_kept": kept})
        print(f"{p.stem}: parsed {parsed:,} rows, kept {kept:,}")
    num = pd.concat(frames, ignore_index=True)

    # Types: dates as datetime, qtrs as an integer, value as a float (still in
    # raw USD/units here; conversion to USD millions happens in Phase 2).
    num["ddate"] = pd.to_datetime(num["ddate"], format="%Y%m%d")
    num["qtrs"] = num["qtrs"].astype("int64")
    num["value"] = pd.to_numeric(num["value"])
    return num, pd.DataFrame(checks)
