"""
PLACEHOLDER: Phase 2 (preprocessing). Not implemented yet.

Will contain functions to:
- join filtered sub to num on adsh and keep only values whose ddate equals the
  filing's period, uom = USD, no coreg, qtrs = 0 (balance sheet) or 4 (income);
- select statement items using a priority list of XBRL tags per item;
- pivot to one row per filing and deduplicate 10-K/A amendments (latest wins);
- create label_year from the fiscal year-end (Jan-May -> year - 1);
- drop or flag rows missing core items (no mean filling), convert to USD
  millions, and run the sanity checks (assets ~ liabilities + equity, etc.).
"""
