"""
Rainfall data loading.

Two paths are supported:

1. load_from_csv() - reads data/rainfall_data.csv. This works right now,
   with no external dependency, and is what the API uses by default.
   Update that CSV (manually, or via the /api/upload-csv endpoint) with
   fresh numbers whenever you want the risk table to reflect new data.

2. fetch_from_imd() - a STUB for scraping mausam.imd.gov.in directly.
   That site loads its rainfall numbers via a JavaScript call after the
   page loads, not in the initial HTML, so a simple requests.get() will
   not see the data. To wire this up for real:

     a. Open the state rainfall page in Chrome/Firefox:
        https://mausam.imd.gov.in/imd_latest/contents/index_rainfall_state_new.php
     b. Open Developer Tools (F12) -> Network tab -> filter by "XHR" or "Fetch"
     c. Reload the page and look for a request that returns JSON or a data
        table (it'll usually have a name like getdata.php, ajax.php, or
        similar, and will show up right after the page loads)
     d. Right-click that request -> Copy -> Copy as cURL, and send it to me
        (or just tell me the URL + parameters) - I'll wire fetch_from_imd()
        up to call it directly and parse the response.

   Until that's done, fetch_from_imd() raises NotImplementedError so the
   API cleanly falls back to the CSV data instead of silently failing.
"""

import csv
import os
from typing import List, Dict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "rainfall_data.csv")


def load_from_csv() -> List[Dict]:
    if not os.path.exists(CSV_PATH):
        return []
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "region": row["region"].strip(),
                "state": row.get("state", row["region"]).strip(),
                "actual_mm": float(row["actual_mm"]),
                "normal_mm": float(row["normal_mm"]),
            })
    return rows


def save_to_csv(rows: List[Dict]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["region", "state", "actual_mm", "normal_mm"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fetch_from_imd() -> List[Dict]:
    """
    Placeholder for a live scrape of mausam.imd.gov.in.
    See the module docstring above for how to wire this up once the
    real data endpoint is identified via browser dev tools.
    """
    raise NotImplementedError(
        "Live IMD scraping isn't wired up yet - see the instructions in "
        "data_source.py. Falling back to CSV data for now."
    )


def get_rainfall_data() -> List[Dict]:
    """Main entry point: try live IMD data, fall back to CSV."""
    try:
        return fetch_from_imd()
    except NotImplementedError:
        return load_from_csv()
