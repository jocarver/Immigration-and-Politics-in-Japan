#!/usr/bin/env python3
r"""Re-query Wikipedia for ok-status speakers to count 選挙区 entries.

A "switcher" is a Diet member whose Wikipedia infobox has multiple
`| 選挙区N = ...` entries — meaning they served from 2+ different
electoral districts across their career. The original
`lookup_speaker_district.py` only stored the FIRST (current) district
in the cache; here we go back, fetch the wikitext, and count entries.

Output: `sou/data/processed/speaker_district_switcher.csv` — same schema
as `speaker_district.csv` plus two new columns:
  - `n_districts_on_wiki`: int, count of 選挙区\d* matches
  - `is_switcher`: "True" if n_districts_on_wiki > 1, else "False"

Why this exists:
  We use the current district for every speech (per Option A in the
  plan) — but politicians who switched districts across terms have
  some speeches misattributed. We flag the misattribution rate per
  (year, prefecture, house) cell downstream via `pct_switcher_speeches`.

Runtime: ~16 min for 628 ok speakers at 1.5s polite delay.
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
INPUT = SOUV / "data" / "processed" / "speaker_district.csv"
OUTPUT = SOUV / "data" / "processed" / "speaker_district_switcher.csv"

# Count both numbered (`| 選挙区2 =`) and unnumbered (`| 選挙区 =`) entries.
# The unnumbered form is the current/primary role; numbered are older roles.
# Anything ≥ 2 entries means the politician served from 2+ districts.
ELEKIKU_COUNT_RE = re.compile(r"\|\s*選挙区\d*\s*=")

UA = "sou-kokkai-lookup/1.0 (https://github.com/uooooo/skill-migration; contact: research)"


def query_wikipedia(title: str) -> dict | None:
    encoded = urllib.parse.quote(title)
    url = (
        f"https://ja.wikipedia.org/w/api.php?action=query"
        f"&titles={encoded}&prop=revisions&rvprop=content"
        f"&format=json&rvslots=main&redirects=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(2 * (4 ** attempt))
                continue
            return {"_error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"_error": str(e)}
    return {"_error": "max retries"}


def count_district_entries(wikitext: str) -> int:
    if not wikitext:
        return 0
    return len(ELEKIKU_COUNT_RE.findall(wikitext))


def main() -> None:
    rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
    print(f"Loaded {len(rows)} speakers from {INPUT.relative_to(REPO_ROOT)}")

    ok_rows = [r for r in rows if r["status"] == "ok"]
    other_rows = [r for r in rows if r["status"] != "ok"]
    print(f"  ok: {len(ok_rows)}, other (no_district/not_found/error): {len(other_rows)}")

    print(f"\nRe-querying {len(ok_rows)} ok speakers (1.5s delay, expect ~{int(len(ok_rows) * 1.5 / 60)} min)")
    t0 = time.time()
    n_switcher = 0
    n_error = 0
    n_multi_district = 0
    for i, row in enumerate(ok_rows, 1):
        sp = row["speaker"]
        data = query_wikipedia(sp)
        if data is None or "_error" in data:
            row["n_districts_on_wiki"] = ""
            row["is_switcher"] = ""
            n_error += 1
        else:
            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values())) if pages else {}
            if page.get("missing") or "-1" in str(page.get("pageid", "")):
                row["n_districts_on_wiki"] = ""
                row["is_switcher"] = ""
            else:
                rev = page.get("revisions", [{}])[0]
                wikitext = rev.get("slots", {}).get("main", {}).get("*", "")
                n = count_district_entries(wikitext)
                row["n_districts_on_wiki"] = n
                row["is_switcher"] = "True" if n > 1 else "False"
                if n > 1:
                    n_switcher += 1
                if n >= 2:
                    n_multi_district += 1
        time.sleep(1.5)

        if i % 25 == 0 or i == len(ok_rows):
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(ok_rows) - i) / rate if rate else 0
            print(f"  [{i}/{len(ok_rows)}] switchers={n_switcher} (>=2 districts on wiki) "
                  f"errors={n_error} | {elapsed:.0f}s elapsed, ~{eta:.0f}s ETA")

    # Non-ok rows: by definition no district info. is_switcher stays False.
    for row in other_rows:
        row["n_districts_on_wiki"] = 0
        row["is_switcher"] = "False"

    # Reassemble: ok_rows first (with new fields), then other_rows
    all_rows = ok_rows + other_rows

    print(f"\nWriting {OUTPUT.relative_to(REPO_ROOT)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(all_rows[0].keys())
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)
    print(f"  {len(all_rows):,} rows")

    print(f"\nSummary:")
    print(f"  Speakers with >=2 選挙区 entries (switchers): {n_switcher}/{len(ok_rows)} "
          f"({n_switcher / len(ok_rows) * 100:.1f}%)")
    print(f"  Re-query errors: {n_error}")


if __name__ == "__main__":
    main()
