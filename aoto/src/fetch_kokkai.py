"""
fetch_kokkai.py
国会会議録 API から移民・外国人関連の発言データを収集し、CSV に集計する。

Usage:
    uv run python aoto/src/fetch_kokkai.py

Output:
    data/raw/kokkai/speeches_<query>_<from>_<until>.json  (生 JSON)
    aoto/data/clean/kokkai_speeches_all.csv               (全発言、重複除去)
    aoto/data/clean/kokkai_count_by_year_party.csv        (年 × 政党クロス集計)
    aoto/data/clean/kokkai_top_speakers.csv               (議員別件数 Top30)
"""

import json
import time
import sys
import pathlib
import requests
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://kokkai.ndl.go.jp/api/speech"
FROM_DATE = "2015-01-01"
UNTIL_DATE = "2026-04-30"
MAX_RECORDS_PER_REQUEST = 100
MAX_RECORDS_PER_KEYWORD = 5000   # 50 ページで打ち切り
SLEEP_SEC = 1.5                  # リクエスト間隔

KEYWORDS = [
    "移民",
    "外国人",
    "在留外国人",
    "特定技能",
    "技能実習",
    "外国人労働者",
    "永住者",
    "在留資格",
]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]  # Skilled-Immigration/
RAW_DIR   = REPO_ROOT / "data" / "raw" / "kokkai"
CLEAN_DIR = REPO_ROOT / "aoto" / "data" / "clean"
RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Fetch functions
# ---------------------------------------------------------------------------

def fetch_speeches_for_keyword(keyword: str) -> list[dict]:
    """1 キーワードについて全件取得 (最大 MAX_RECORDS_PER_KEYWORD 件)"""
    all_records: list[dict] = []
    start = 1

    params_base = {
        "any": keyword,
        "from": FROM_DATE,
        "until": UNTIL_DATE,
        "maximumRecords": MAX_RECORDS_PER_REQUEST,
        "recordPacking": "json",
    }

    print(f"\n[fetch] keyword='{keyword}'", flush=True)

    while True:
        params = {**params_base, "startRecord": start}
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
        except requests.HTTPError as e:
            print(f"  [ERROR] HTTP error: {e}", file=sys.stderr)
            break
        except requests.RequestException as e:
            print(f"  [ERROR] Request failed: {e}", file=sys.stderr)
            break

        try:
            data = resp.json()
        except ValueError as e:
            print(f"  [ERROR] JSON decode error: {e}", file=sys.stderr)
            break

        total = data.get("numberOfRecords", 0)
        records = data.get("speechRecord", [])

        if start == 1:
            print(f"  total hits: {total}", flush=True)
            if total > MAX_RECORDS_PER_KEYWORD:
                print(f"  [WARN] {total} > {MAX_RECORDS_PER_KEYWORD}. "
                      f"Will cap at {MAX_RECORDS_PER_KEYWORD} records.", flush=True)

        if not records:
            break

        all_records.extend(records)
        print(f"  fetched {len(all_records)}/{min(total, MAX_RECORDS_PER_KEYWORD)} ...",
              flush=True)

        # 次ページ判定
        next_pos = data.get("nextRecordPosition")
        if not next_pos or len(all_records) >= MAX_RECORDS_PER_KEYWORD:
            break

        start = next_pos
        time.sleep(SLEEP_SEC)

    print(f"  -> collected {len(all_records)} records for '{keyword}'", flush=True)
    return all_records


def save_raw_json(keyword: str, records: list[dict]) -> pathlib.Path:
    safe_kw = keyword.replace("/", "_")
    fname = f"speeches_{safe_kw}_{FROM_DATE}_{UNTIL_DATE}.json"
    path = RAW_DIR / fname
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"  saved -> {path}", flush=True)
    return path


# ---------------------------------------------------------------------------
# Build CSVs
# ---------------------------------------------------------------------------

def build_csvs(raw_dir: pathlib.Path, clean_dir: pathlib.Path) -> pd.DataFrame:
    """JSON を読み込んで CSV を生成し、全発言 DataFrame を返す"""
    frames = []
    for jfile in sorted(raw_dir.glob("speeches_*.json")):
        with open(jfile, encoding="utf-8") as f:
            records = json.load(f)
        if records:
            frames.append(pd.DataFrame(records))

    if not frames:
        print("[WARN] No JSON files found. Skipping CSV build.", file=sys.stderr)
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # 重複除去 (speechID)
    before = len(df)
    df = df.drop_duplicates(subset=["speechID"])
    after = len(df)
    print(f"\n[build_csvs] Total records: {before} -> {after} after dedup on speechID")

    # 型整備
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["speakerGroup"] = df["speakerGroup"].fillna("不明")
    df["speaker"] = df["speaker"].fillna("不明")

    # --- 1. 全発言 CSV ---
    all_csv = clean_dir / "kokkai_speeches_all.csv"
    df.to_csv(all_csv, index=False, encoding="utf-8-sig")
    print(f"  saved -> {all_csv}  ({len(df)} rows)")

    # --- 2. 年 × 政党クロス集計 (long format) ---
    year_party = (
        df.groupby(["year", "speakerGroup"])
          .size()
          .reset_index(name="count")
          .sort_values(["year", "count"], ascending=[True, False])
    )
    yp_csv = clean_dir / "kokkai_count_by_year_party.csv"
    year_party.to_csv(yp_csv, index=False, encoding="utf-8-sig")
    print(f"  saved -> {yp_csv}  ({len(year_party)} rows)")

    # --- 3. 議員別件数 Top30 ---
    top_speakers = (
        df.groupby(["speaker", "speakerGroup"])
          .size()
          .reset_index(name="count")
          .sort_values("count", ascending=False)
          .head(30)
    )
    ts_csv = clean_dir / "kokkai_top_speakers.csv"
    top_speakers.to_csv(ts_csv, index=False, encoding="utf-8-sig")
    print(f"  saved -> {ts_csv}  ({len(top_speakers)} rows)")

    return df


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(df: pd.DataFrame, keyword_counts: dict[str, int]) -> None:
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total speeches (dedup): {len(df)}")
    print(f"Date range: {FROM_DATE} ~ {UNTIL_DATE}")

    print("\n-- Keyword breakdown --")
    for kw, cnt in keyword_counts.items():
        print(f"  {kw}: {cnt}")

    if df.empty:
        return

    print("\n-- Top 3 years by speech count --")
    year_counts = df["year"].value_counts().sort_values(ascending=False).head(3)
    for yr, cnt in year_counts.items():
        print(f"  {int(yr)}: {cnt}")

    print("\n-- Top 5 parties by speech count --")
    party_counts = df["speakerGroup"].value_counts().head(5)
    for party, cnt in party_counts.items():
        print(f"  {party}: {cnt}")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Kokkai API fetch started at {datetime.now().isoformat()}")
    print(f"Period: {FROM_DATE} ~ {UNTIL_DATE}")
    print(f"Keywords: {KEYWORDS}")
    print(f"Max per keyword: {MAX_RECORDS_PER_KEYWORD}")

    keyword_counts: dict[str, int] = {}

    for kw in KEYWORDS:
        records = fetch_speeches_for_keyword(kw)
        keyword_counts[kw] = len(records)
        if records:
            save_raw_json(kw, records)
        time.sleep(SLEEP_SEC)

    df = build_csvs(RAW_DIR, CLEAN_DIR)
    print_summary(df, keyword_counts)


if __name__ == "__main__":
    main()
