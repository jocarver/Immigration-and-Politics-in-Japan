"""
fetch_estat_files.py
====================
e-Stat (政府統計の総合窓口) から在留外国人統計の Excel ファイルを取得する。

対象: https://www.e-stat.go.jp/stat-search/files?toukei=00250012&tstat=000001018034
期間: 2012年12月 ~ 最新 (月次 cycle=1, 半期データ)
優先: 都道府県別 × 在留資格別 のファイル

利用方法:
    uv run --with requests --with beautifulsoup4 --with pandas --with openpyxl \
        python aoto/src/fetch_estat_files.py

出力:
    data/raw/foreign_residents/{year}_{month}/{filename}.xlsx
    data/raw/foreign_residents/README.md
    aoto/data/clean/foreign_residents_sample_preview.md
"""

import os
import re
import sys
import time
import json
import datetime
import traceback
from pathlib import Path
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://www.e-stat.go.jp"
STAT_SEARCH_BASE = f"{BASE_URL}/stat-search/files"
FILE_DOWNLOAD_BASE = f"{BASE_URL}/stat-search/file-download"

# Monthly cycle (cycle=1) for 在留外国人統計 (2012-12 onward)
MONTHLY_TCLASS1 = "000001060399"
TOUKEI = "00250012"
TSTAT = "000001018034"

# Output directories (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Skilled-Immigration/
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "foreign_residents"
CLEAN_DIR = PROJECT_ROOT / "aoto" / "data" / "clean"

# Request settings
SLEEP_BETWEEN_FILES = 2.5   # seconds between file downloads
SLEEP_RETRY = 30            # seconds to wait on 429/503
MAX_RETRIES = 3

# Keywords that identify prefecture-level data files (priority order)
PREF_KEYWORDS_HIGH = [
    "t1",               # テーブルデータ（都道府県別）— new format
    "都道府県別",
    "テーブルデータ",       # retrospective table data files (2016-2022 年末)
]
PREF_KEYWORDS_LOW = [
    "05-0",         # 都道府県別 在留資格別 総数 — old format
    "04",           # 都道府県別 国籍別
    "t2",           # 市区町村別 (secondary)
]

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def make_session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": BASE_URL,
    })
    return sess


# ---------------------------------------------------------------------------
# Period discovery
# ---------------------------------------------------------------------------

# Hard-coded period list based on e-Stat structure observed.
# Each entry: (year_code, month_code, label) where year_code and month_code
# are the URL parameters used by e-Stat.
# year_code: e.g. "20240" for 2024
# month_code: e.g. "24101212" for 2024/12 (month param value)
# label: human-readable, used for directory naming

# These were discovered by browsing the site.
# Pattern: year=YYYY0, month varies per period.
# We discover these dynamically by scraping the listing page.

def get_period_list(sess: requests.Session) -> list[dict]:
    """
    Scrape the monthly cycle listing page to get all available period URLs.
    Returns list of dicts: {label, year, half, url}
    """
    url = (
        f"{STAT_SEARCH_BASE}?toukei={TOUKEI}&tstat={TSTAT}"
        f"&cycle=1&tclass1={MONTHLY_TCLASS1}&layout=datalist&page=1&tclass2val=0"
    )
    print(f"[fetch_periods] GET {url}")
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    periods = []
    # Look for links that contain year= and month= parameters
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "year=" in href and "month=" in href and "result_back=1" in href:
            full_url = urljoin(BASE_URL, href)
            # Extract year and month from URL
            year_m = re.search(r"year=(\d{5})", href)
            month_m = re.search(r"month=(\d+)", href)
            if year_m and month_m:
                year_code = year_m.group(1)
                month_code = month_m.group(1)
                year = int(year_code[:4])
                # Determine half (6=June, 12=December) from month_code suffix
                if month_code.endswith("06"):
                    half = 6
                elif month_code.endswith("12"):
                    half = 12
                else:
                    # Try to infer from link text
                    text = a.get_text(strip=True)
                    half = 6 if "6" in text else 12

                label = f"{year}年{half}月末"
                dir_name = f"{year}_{half:02d}"

                # Filter: 2012 onward only
                if year < 2012:
                    continue

                # Deduplicate
                if not any(p["dir_name"] == dir_name for p in periods):
                    periods.append({
                        "label": label,
                        "year": year,
                        "half": half,
                        "dir_name": dir_name,
                        "url": full_url,
                        "year_code": year_code,
                        "month_code": month_code,
                    })

    # Sort chronologically
    periods.sort(key=lambda x: (x["year"], x["half"]))
    return periods


# ---------------------------------------------------------------------------
# File listing per period
# ---------------------------------------------------------------------------

def get_file_list(sess: requests.Session, period: dict) -> list[dict]:
    """
    Scrape a period's datalist page and return all Excel download links.
    Each entry: {title, stat_inf_id, download_url, file_kind}
    """
    url = period["url"]
    print(f"  [get_file_list] GET {url}")

    for attempt in range(MAX_RETRIES):
        try:
            resp = sess.get(url, timeout=30)
            if resp.status_code in (429, 503):
                print(f"    Rate limited ({resp.status_code}), waiting {SLEEP_RETRY}s...")
                time.sleep(SLEEP_RETRY)
                continue
            resp.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                print(f"    FAILED: {e}")
                return []
            time.sleep(5)
    else:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    files = []

    # Find all download links: /stat-search/file-download?statInfId=...&fileKind=0
    seen_ids = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "file-download" not in href:
            continue

        id_m = re.search(r"statInfId=(\d+)", href)
        kind_m = re.search(r"fileKind=(\d+)", href)
        if not id_m or not kind_m:
            continue

        stat_inf_id = id_m.group(1)
        file_kind = int(kind_m.group(1))

        # fileKind=0: Excel download, fileKind=2: PDF, fileKind=4: Excel viewer
        if file_kind not in (0,):
            continue
        if stat_inf_id in seen_ids:
            continue
        seen_ids.add(stat_inf_id)

        # Try to get associated title from parent elements
        title = _extract_title(a, soup, stat_inf_id)

        download_url = urljoin(BASE_URL, href)
        files.append({
            "title": title,
            "stat_inf_id": stat_inf_id,
            "download_url": download_url,
            "file_kind": file_kind,
        })

    return files


def _extract_title(a_tag, soup: BeautifulSoup, stat_inf_id: str) -> str:
    """Try to extract a meaningful title for the file."""
    # Walk up the DOM tree to find a title-like element
    parent = a_tag.parent
    for _ in range(6):
        if parent is None:
            break
        text = parent.get_text(separator=" ", strip=True)
        if len(text) > 5 and len(text) < 200:
            # Clean up the text
            text = re.sub(r"\s+", " ", text).strip()
            return text
        parent = parent.parent

    # Fallback: look for element with matching stat_inf_id nearby
    return f"statInfId={stat_inf_id}"


# ---------------------------------------------------------------------------
# Priority scoring for file selection
# ---------------------------------------------------------------------------

def score_file(f: dict) -> int:
    """Higher score = higher priority for download."""
    title = f["title"]
    score = 0

    # High priority: prefecture-level table data
    for kw in PREF_KEYWORDS_HIGH:
        if kw in title:
            score += 100

    # Medium priority: old-format prefecture files
    for kw in PREF_KEYWORDS_LOW:
        if kw in title:
            score += 50

    # Exclude pure PDF supplementary docs
    if any(x in title for x in ["用語", "注意", "ご利用方法", "解説"]):
        score -= 200

    return score


def select_priority_files(files: list[dict], period: dict) -> list[dict]:
    """
    Select the files to download for this period.
    Strategy:
    - Always include the highest-scoring prefecture-level file
    - Include t1 (都道府県別テーブルデータ) if present (new format, 2015+)
    - For older periods (2012-2014), include 都道府県別 files
    - Also include 01-1 (国籍×在留資格 全国) as secondary
    """
    if not files:
        return []

    scored = [(score_file(f), f) for f in files]
    scored.sort(key=lambda x: -x[0])

    selected = []

    # Always get the top prefecture file(s)
    for score, f in scored:
        if score >= 50:
            selected.append(f)
        elif score >= 0 and len(selected) == 0:
            # If nothing scored well, take the best we have
            selected.append(f)

    # If nothing selected, take all non-PDF files
    if not selected:
        selected = [f for f in files if f["file_kind"] == 0]

    return selected


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_file(sess: requests.Session, f: dict, dest_dir: Path) -> Path | None:
    """Download a file to dest_dir. Returns path if successful, None otherwise."""
    url = f["download_url"]
    stat_inf_id = f["stat_inf_id"]

    # Try to determine filename from Content-Disposition or URL
    dest_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(MAX_RETRIES):
        try:
            print(f"    DL {url}")
            resp = sess.get(url, timeout=60, stream=True)

            if resp.status_code in (429, 503):
                print(f"    Rate limited ({resp.status_code}), waiting {SLEEP_RETRY}s...")
                time.sleep(SLEEP_RETRY)
                continue

            if resp.status_code == 403:
                print(f"    403 Forbidden — skipping {url}")
                return None

            resp.raise_for_status()

            # Determine filename
            cd = resp.headers.get("Content-Disposition", "")
            fname_m = re.search(r'filename\*?=(?:UTF-8\'\')?([^\s;]+)', cd)
            if fname_m:
                fname = fname_m.group(1).strip('"')
                # URL-decode if needed
                from urllib.parse import unquote
                fname = unquote(fname)
            else:
                # Infer from content type
                ct = resp.headers.get("Content-Type", "")
                ext = ".xlsx" if "excel" in ct or "spreadsheet" in ct or "zip" in ct else ".bin"
                fname = f"{stat_inf_id}{ext}"

            # Sanitize filename
            fname = re.sub(r'[\\/:*?"<>|]', '_', fname)

            dest_path = dest_dir / fname

            # Skip if already downloaded
            if dest_path.exists():
                print(f"    Already exists: {dest_path.name}")
                return dest_path

            # Write file
            with open(dest_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)

            size_kb = dest_path.stat().st_size // 1024
            print(f"    Saved: {dest_path.name} ({size_kb} KB)")
            return dest_path

        except requests.RequestException as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)

    return None


# ---------------------------------------------------------------------------
# Sample parsing
# ---------------------------------------------------------------------------

def parse_sample(xlsx_path: Path) -> dict:
    """Parse a downloaded Excel file and return metadata."""
    result = {
        "path": str(xlsx_path),
        "sheets": [],
        "error": None,
    }
    try:
        xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
        result["sheets"] = xl.sheet_names

        sheet_info = []
        for sheet in xl.sheet_names[:5]:  # limit to first 5 sheets
            try:
                df = pd.read_excel(xlsx_path, sheet_name=sheet, nrows=10, engine="openpyxl")
                sheet_info.append({
                    "name": sheet,
                    "shape": df.shape,
                    "columns": list(df.columns)[:10],
                    "head": df.head(5).to_string(),
                })
            except Exception as e:
                sheet_info.append({"name": sheet, "error": str(e)})

        result["sheet_info"] = sheet_info
    except Exception as e:
        result["error"] = str(e)
        traceback.print_exc()

    return result


# ---------------------------------------------------------------------------
# README generation
# ---------------------------------------------------------------------------

def write_readme(results: list[dict], output_path: Path):
    today = datetime.date.today().isoformat()
    lines = [
        "# 在留外国人統計 — 取得ファイル一覧",
        "",
        f"**取得日**: {today}",
        f"**取得元**: https://www.e-stat.go.jp/stat-search/files?toukei=00250012&tstat=000001018034",
        "",
        "## データ説明",
        "",
        "在留外国人統計は法務省が毎年6月末・12月末時点の在留外国人数を集計したもの。",
        "2012年7月の改正入管法施行に伴い「登録外国人統計」から「在留外国人統計」に移行。",
        "",
        "### 主要ファイル種別",
        "",
        "| ファイルパターン | 内容 | 粒度 |",
        "|---|---|---|",
        "| `*-t1.*` | テーブルデータ（国籍×在留資格×都道府県×年齢×性別） | 2015年以降の統合形式 |",
        "| `*-05-0.*` | 都道府県別 在留資格別 在留外国人（総数） | 2012-2014年の旧形式 |",
        "| `*-04.*` | 都道府県別 国籍・地域別 在留外国人 | 2012-2014年の旧形式 |",
        "| `*-01-1.*` | 国籍・地域別 在留資格別 在留外国人（全国） | 全期間 |",
        "",
        "### 注意事項",
        "",
        "1. **技能実習 → 育成就労**: 2022年改正入管法で「技能実習」制度は段階的廃止され",
        "   「育成就労」に移行。統計での在留資格名称が変わる点に注意（データ連結時は要マッピング）。",
        "2. **特定技能**: 2019年4月新設の在留資格。それ以前の期間は存在しない。",
        "3. **永住者**: 2015年以前は「特別永住者」と「永住者」が別集計。",
        "4. **都道府県合区**: 2016年参院選から一部選挙区が合区（鳥取+島根、徳島+高知）。",
        "   在留外国人統計は都道府県単位なので選挙データと結合する際は合区処理が必要。",
        "5. **ファイル形式変更**: 2015年6月末データから都道府県×在留資格の統合テーブル形式に変更。",
        "   それ以前は在留資格別・国籍別に複数ファイルに分割されていた。",
        "",
        "## 取得ファイル一覧",
        "",
    ]

    success_count = 0
    fail_count = 0

    for r in results:
        period = r["period"]
        lines.append(f"### {period['label']}")
        lines.append("")

        if r.get("files_downloaded"):
            for f in r["files_downloaded"]:
                lines.append(f"- `{f['rel_path']}` — {f['title'][:80]}")
                success_count += 1

        if r.get("files_failed"):
            for f in r["files_failed"]:
                lines.append(f"- ❌ FAILED: {f['title'][:80]} ({f.get('reason', 'unknown')})")
                fail_count += 1

        if r.get("skipped"):
            lines.append(f"- (skipped: {r['skipped']})")

        lines.append("")

    lines += [
        "## 統計",
        "",
        f"- 取得成功: {success_count} ファイル",
        f"- 取得失敗: {fail_count} ファイル",
        "",
        "## e-Stat API について",
        "",
        "直接 HTML スクレイピングで取得可能なため、appId 登録は不要。",
        "ダウンロード URL パターン: `https://www.e-stat.go.jp/stat-search/file-download?statInfId=<ID>&fileKind=0`",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[README] Written to {output_path}")


# ---------------------------------------------------------------------------
# Sample preview
# ---------------------------------------------------------------------------

def write_sample_preview(sample: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 在留外国人統計 — サンプルファイル解析",
        "",
        f"**対象ファイル**: `{sample['path']}`",
        f"**解析日**: {datetime.date.today().isoformat()}",
        "",
    ]

    if sample.get("error"):
        lines.append(f"**エラー**: {sample['error']}")
    else:
        lines.append(f"**シート数**: {len(sample['sheets'])}")
        lines.append(f"**シート名一覧**: {', '.join(sample['sheets'])}")
        lines.append("")

        for si in sample.get("sheet_info", []):
            lines.append(f"### シート: `{si['name']}`")
            if "error" in si:
                lines.append(f"- エラー: {si['error']}")
            else:
                lines.append(f"- Shape: {si['shape'][0]} 行 × {si['shape'][1]} 列")
                lines.append(f"- 列名 (最初の10列): {si['columns']}")
                lines.append("")
                lines.append("**先頭5行:**")
                lines.append("```")
                lines.append(si["head"])
                lines.append("```")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[preview] Written to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    sess = make_session()

    print("=" * 60)
    print("e-Stat 在留外国人統計 ダウンローダー")
    print("=" * 60)

    # Step 1: Get period list
    print("\n[Step 1] 期間一覧を取得中...")
    periods = get_period_list(sess)

    if not periods:
        print("ERROR: 期間一覧の取得に失敗しました。手動確認が必要です。")
        sys.exit(1)

    print(f"  {len(periods)} 期間を発見:")
    for p in periods:
        print(f"    {p['label']} → {p['dir_name']}")

    # Step 2: For each period, get file list and download
    print(f"\n[Step 2] 各期間のファイルをダウンロード中...")

    all_results = []
    downloaded_paths = []

    for period in periods:
        print(f"\n{'='*50}")
        print(f"  期間: {period['label']}")

        dest_dir = RAW_DIR / period["dir_name"]

        # Get file list for this period
        files = get_file_list(sess, period)
        time.sleep(1)

        if not files:
            print(f"  警告: ファイルリスト取得失敗")
            all_results.append({"period": period, "skipped": "file list fetch failed"})
            continue

        print(f"  {len(files)} ファイル発見")
        for f in files:
            print(f"    [{f['stat_inf_id']}] {f['title'][:70]}")

        # Select priority files
        priority_files = select_priority_files(files, period)
        print(f"  優先ファイル: {len(priority_files)} 件")

        period_result = {
            "period": period,
            "files_downloaded": [],
            "files_failed": [],
        }

        for f in priority_files:
            path = download_file(sess, f, dest_dir)

            if path:
                rel_path = path.relative_to(RAW_DIR)
                period_result["files_downloaded"].append({
                    "title": f["title"],
                    "stat_inf_id": f["stat_inf_id"],
                    "rel_path": str(rel_path),
                    "abs_path": str(path),
                })
                downloaded_paths.append(path)
            else:
                period_result["files_failed"].append({
                    "title": f["title"],
                    "stat_inf_id": f["stat_inf_id"],
                    "reason": "download returned None",
                })

            time.sleep(SLEEP_BETWEEN_FILES)

        all_results.append(period_result)

    # Step 3: Write README
    print(f"\n[Step 3] README を生成中...")
    write_readme(all_results, RAW_DIR / "README.md")

    # Step 4: Sample parse of the latest downloaded file
    print(f"\n[Step 4] 最新ファイルのサンプル解析...")

    # Find latest downloaded file (prefer t1 / 都道府県 files)
    sample_path = None
    for result in reversed(all_results):
        for fd in result.get("files_downloaded", []):
            ap = fd["abs_path"]
            if "t1" in ap or "都道府県" in fd["title"]:
                sample_path = Path(ap)
                break
        if sample_path:
            break

    if not sample_path and downloaded_paths:
        sample_path = downloaded_paths[-1]

    if sample_path and sample_path.exists():
        print(f"  解析対象: {sample_path}")
        sample = parse_sample(sample_path)
        write_sample_preview(sample, CLEAN_DIR / "foreign_residents_sample_preview.md")
    else:
        print("  解析対象ファイルなし")

    # Summary
    total_ok = sum(len(r.get("files_downloaded", [])) for r in all_results)
    total_fail = sum(len(r.get("files_failed", [])) for r in all_results)
    print(f"\n{'='*60}")
    print(f"完了: {total_ok} ファイル取得成功, {total_fail} 失敗")
    print(f"出力先: {RAW_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
