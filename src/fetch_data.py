"""
Pull municipal financial data from the National Treasury Municipal Money API.

Public API, no key required: https://municipaldata.treasury.gov.za/api

The API is an OLAP "cubes" service. Each cube is queried with:
    /api/cubes/<cube>/aggregate?aggregates=<measure>.sum&cut=<filters>&drilldown=<dims>

Output CSVs land in data/ and are small enough to commit, so the repo stays
self-contained and the notebook runs without a network call.

Usage:
    python src/fetch_data.py
"""

from pathlib import Path
from urllib.parse import urlencode
import csv
import json
import sys
import time
import urllib.error
import urllib.request

BASE = "https://municipaldata.treasury.gov.za/api"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

YEARS = [2020, 2021, 2022, 2023, 2024]
AUDIT_YEARS = list(range(2015, 2025))
UIFW_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

PAGESIZE = 5000
PAUSE = 0.4          # be a polite client


def request(url: str, tries: int = 3) -> dict:
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == tries - 1:
                raise
            print(f"    retry {attempt + 1} after {exc}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def aggregate(cube: str, aggregates: str, cut: str, drilldown: str) -> list[dict]:
    """Page through an aggregate query and return every cell."""
    cells, page = [], 0
    while True:
        params = {
            "aggregates": aggregates,
            "cut": cut,
            "drilldown": drilldown,
            "page": page,
            "pagesize": PAGESIZE,
        }
        payload = request(f"{BASE}/cubes/{cube}/aggregate?{urlencode(params)}")
        batch = payload.get("cells", [])
        cells.extend(batch)
        if len(batch) < PAGESIZE:
            return cells
        page += 1
        time.sleep(PAUSE)


def facts(cube: str, fields: str, cut: str = "") -> list[dict]:
    rows, page = [], 0
    while True:
        params = {"fields": fields, "page": page, "pagesize": PAGESIZE}
        if cut:
            params["cut"] = cut
        payload = request(f"{BASE}/cubes/{cube}/facts?{urlencode(params)}")
        batch = payload.get("data", [])
        rows.extend(batch)
        if len(batch) < PAGESIZE:
            return rows
        page += 1
        time.sleep(PAUSE)


def write_csv(rows: list[dict], name: str) -> None:
    path = DATA / name
    if not rows:
        print(f"  !! {name}: no rows returned")
        return
    keys = sorted({k for r in rows for k in r})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {name:<32} {len(rows):>6,} rows")


def year_cut(years: list[int]) -> str:
    return "financial_year_end.year:" + ";".join(str(y) for y in years)


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    print(f"Fetching from {BASE}\n")

    try:
        # 1. Municipality reference data — province, category (A metro / B local / C district)
        print("municipalities")
        write_csv(
            facts("municipalities",
                  "municipality.demarcation_code,municipality.name,municipality.long_name,"
                  "municipality.province_name,municipality.category,municipality.miif_category"),
            "municipalities.csv",
        )

        # 2. Statement of Financial Performance: revenue, expenditure, surplus
        print("\nincome & expenditure  (items 2900 revenue, 4400 expenditure, 4500 surplus)")
        write_csv(
            aggregate(
                "incexp_v2", "amount.sum",
                f'{year_cut(YEARS)}|amount_type.code:"AUDA"|period_length.length:"year"'
                '|item.code:"2900";"4400";"4500"',
                "demarcation.code|financial_year_end.year|item.code|item.label",
            ),
            "income_expenditure.csv",
        )

        # 3. Cash held at year end (item 0430) — the numerator for cash coverage
        print("\ncash flow  (item 0430 cash at year end)")
        write_csv(
            aggregate(
                "cflow_v2", "amount.sum",
                f'{year_cut(YEARS)}|amount_type.code:"AUDA"|period_length.length:"year"'
                '|item.code:"0430"',
                "demarcation.code|financial_year_end.year",
            ),
            "cash.csv",
        )

        # 4. Debtor ageing (item 2000, total by income source)
        print("\naged debtors  (item 2000 total by income source)")
        write_csv(
            aggregate(
                "aged_debtor_v2",
                # NOTE: multiple aggregates are separated by "|", not ",". A comma-separated
                # list is silently accepted and all but the first measure is dropped.
                "total_amount.sum|l30_amount.sum|l60_amount.sum|l90_amount.sum"
                "|l120_amount.sum|l150_amount.sum|l180_amount.sum|g1_amount.sum|bad_amount.sum",
                f'{year_cut(YEARS)}|amount_type.code:"AUDA"|period_length.length:"year"'
                '|item.code:"2000"',
                "demarcation.code|financial_year_end.year",
            ),
            "aged_debtors.csv",
        )

        # 5. Unauthorised, irregular, fruitless and wasteful expenditure
        print("\nUIFW expenditure")
        write_csv(
            aggregate("uifwexp", "amount.sum", year_cut(UIFW_YEARS),
                      "demarcation.code|financial_year_end.year|item.code|item.label"),
            "uifw.csv",
        )

        # 6. Audit outcomes from the Auditor-General
        print("\naudit opinions")
        write_csv(
            aggregate("audit_opinions", "_count",
                      year_cut(AUDIT_YEARS),
                      "demarcation.code|financial_year_end.year|opinion.code|opinion.label"),
            "audit_opinions.csv",
        )

        # 7. Capital expenditure: audited actual vs adjusted budget, summed over all asset
        #    classes (the cube has 124 item-level codes and no roll-up row)
        print("\ncapital expenditure  (actual vs adjusted budget)")
        write_csv(
            aggregate(
                "capital_v2", "amount.sum",
                f'{year_cut(YEARS)}|amount_type.code:"AUDA";"ADJB"|period_length.length:"year"',
                "demarcation.code|financial_year_end.year|amount_type.code",
            ),
            "capital.csv",
        )

    except Exception as exc:
        print(f"\nFailed: {exc}")
        return 1

    print(f"\nAll files written to {DATA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
