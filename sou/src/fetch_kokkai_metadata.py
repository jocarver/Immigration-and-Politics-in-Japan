#!/usr/bin/env python3
"""Kokkai NDL API - Phase 1: metadata fetch.

9 keywords x 2012-2024, with speechID deduplication.
Atomic checkpoint saves after every keyword.

Usage:
    uv run python sou/src/fetch_kokkai_metadata.py

Output:
    data/raw/kokkai/metadata.json   # deduplicated speech metadata
"""
import urllib.request
import urllib.parse
import json
import time
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# Search keywords. These are JP data values sent verbatim to the NDL API,
# not prose — they stay in JP.
KEYWORDS = [
    "技能実習", "外国人労働者", "出入国管理", "特定技能", "外国人材",
    "不法滞在", "多文化共生", "移民政策", "外国人犯罪",
]

# Resolve paths relative to project root (Skilled-Immigration/).
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "sou" / "data" / "raw" / "kokkai"
OUTPUT_FILE = OUTPUT_DIR / "metadata.json"
BASE_URL = "https://kokkai.ndl.go.jp/api/speech"
FROM_DATE = "2012-01-01"
UNTIL_DATE = "2024-12-31"
MAX_PER_REQUEST = 100
SLEEP_SECONDS = 2

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def fetch_keyword(keyword: str) -> list[dict]:
    """Fetch all speeches for one keyword (paginated)."""
    all_records = []
    start_record = 1

    while True:
        params = {
            "any": keyword,
            "from": FROM_DATE,
            "until": UNTIL_DATE,
            "startRecord": start_record,
            "maximumRecords": MAX_PER_REQUEST,
            "recordPacking": "json",
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"  [ERROR] {keyword}: {e}")
            break

        records = data.get("speechRecord", [])
        if not records:
            break

        all_records.extend(records)
        total = data.get("numberOfRecords", 0)
        returned = data.get("numberOfReturn", 0)
        next_pos = data.get("nextRecordPosition")

        print(f"  [{start_record}-{start_record + returned - 1}] of {total} total, {len(all_records)} fetched")
        if not next_pos or len(records) < MAX_PER_REQUEST:
            break

        start_record = next_pos
        time.sleep(SLEEP_SECONDS)

    return all_records


def save_checkpoint(all_speeches: dict, completed_keywords: list, stats: dict) -> None:
    """Atomic checkpoint save (write to temp, then rename)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(OUTPUT_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "fetched_at": datetime.now().isoformat(),
                    "keywords": KEYWORDS,
                    "date_range": {"from": FROM_DATE, "until": UNTIL_DATE},
                    "completed_keywords": completed_keywords,
                    "stats": stats,
                },
                "speeches": all_speeches,
            }, f, ensure_ascii=False, indent=2)
        shutil.move(tmp_path, str(OUTPUT_FILE))
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    print(f"  [CHECKPOINT: {len(all_speeches)} speeches saved]")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Phase 1: metadata fetch")
    print(f"Date range: {FROM_DATE} ~ {UNTIL_DATE}")
    print(f"Keyword count: {len(KEYWORDS)}")
    print("=" * 60)

    all_speeches = {}
    completed_keywords = []
    stats = {}

    # Load checkpoint if it exists.
    if OUTPUT_FILE.exists():
        print("Loading checkpoint...")
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            all_speeches = d.get("speeches", {})
            completed_keywords = d.get("metadata", {}).get("completed_keywords", [])
            stats = d.get("metadata", {}).get("stats", {})
            print(f"  Loaded {len(all_speeches)} speeches, {len(completed_keywords)} keywords done")
        except json.JSONDecodeError:
            print("  Warning: checkpoint corrupted, starting fresh")

    for kw in KEYWORDS:
        if kw in completed_keywords:
            idx = KEYWORDS.index(kw) + 1
            print(f"\n▶ [{idx}/{len(KEYWORDS)}] {kw} - skip (done)")
            continue

        print(f"\n▶ [{KEYWORDS.index(kw) + 1}/{len(KEYWORDS)}] {kw}")
        records = fetch_keyword(kw)

        new_count = 0
        for rec in records:
            sid = rec.get("speechID")
            if sid and sid not in all_speeches:
                all_speeches[sid] = rec
                all_speeches[sid]["keywords_matched"] = [kw]
                new_count += 1
            elif sid in all_speeches:
                all_speeches[sid]["keywords_matched"].append(kw)

        completed_keywords.append(kw)
        stats[kw] = len(records)
        print(f"  -> new: {new_count} / cumulative: {len(all_speeches)}")

        save_checkpoint(all_speeches, completed_keywords, stats)
        time.sleep(SLEEP_SECONDS)

    print(f"\n{'=' * 60}")
    print(f"✅ Phase 1 done")
    print(f"   after dedup: {len(all_speeches)} speeches")
    print(f"   saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
