"""
fetch_soumu_elections.py
総務省 選挙関連資料から「都道府県別党派別得票数（比例代表）」Excel を DL するスクリプト。

対象選挙 (比例代表、都道府県別党派別得票数):
  - 第23回参院選 2013/07/21  /main_content/000244369.xls  ← (5) 都道府県別党派別得票数（比例代表）
  - 第24回参院選 2016/07/10  /main_content/000430610.xls  ← (5) 都道府県別党派別得票数（比例代表）
  - 第25回参院選 2019/07/21  /main_content/000636675.xls  ← (5) 都道府県別党派別得票数（比例代表）
  - 第47回衆院選 2014/12/14  /main_content/000328949.xls  ← (7) 比例代表選挙区別都道府県別党派別得票数
  - 第48回衆院選 2017/10/22  /main_content/000516725.xls  ← (7) 比例代表選挙区別都道府県別党派別得票数
  - 第49回衆院選 2021/10/31  /main_content/000776973.xlsx ← (7) 比例代表選挙区別都道府県別党派別得票数

注: 参院選 index.html の WebFetch で AI が返した URL は (9)「得票順党派別得票数」と混同しやすい。
  正しい target は section (5) で、都道府県 × 党派の 2 次元表 (218 行程度)。
  衆院選は section (7) が「選挙区別都道府県別党派別得票数」(124 行程度、ブロック別)。
  section (5) の衆院は全国集計のみなので誤り注意。

調査手順 (再現用メモ):
  1. https://www.soumu.go.jp/senkyo/senkyo_s/data/ → sangiin/shugiin ichiran ページへ
  2. 各回 index.html から XLS リンクを WebFetch で列挙
  3. 参院: 「都道府県別党派別得票数（比例代表）」= 概ね 9 番目のファイル
  4. 衆院: 「比例代表選挙区別都道府県別党派別得票数」= 3(7) 相当のファイル
     ※ 3(5) は全国集計の党派別得票数なので誤り注意
  5. requests で DL (Referer ヘッダー必要)

Usage:
    uv run --with requests python aoto/src/fetch_soumu_elections.py

Output:
    data/raw/election_results/ に各 XLS/XLSX を保存
"""

import os
import requests

OUTPUT_DIR = "data/raw/election_results"
BASE_URL = "https://www.soumu.go.jp"

TARGETS = [
    # --- 参議院 (House of Councillors) ---
    # 注: 各 index.html に並ぶ XLS は同名項目が複数ある。
    #   WebFetch が返す「(9) 得票順党派別得票数」等と混同しないこと。
    #   正解は section (5)「都道府県別党派別得票数（比例代表）」のファイル。
    #   手動確認: 対象ページをスキャンして「北海道」行を含む 218 行 × 多列ファイルを選択。
    {
        "election": "第23回参院選 2013/07/21",
        "filename": "July 21 2013 House of Councillors election.xls",
        "path": "/main_content/000244369.xls",   # (5) 都道府県別党派別得票数（比例代表）
        "table": "（５）都道府県別党派別得票数（比例代表）",
        "source_page": "https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin23/index.html",
    },
    {
        "election": "第24回参院選 2016/07/10",
        "filename": "July 10 2016 House of Councillors election.xls",
        "path": "/main_content/000430610.xls",   # (5) 都道府県別党派別得票数（比例代表）
        "table": "（５）都道府県別党派別得票数（比例代表）",
        "source_page": "https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin24/index.html",
    },
    {
        "election": "第25回参院選 2019/07/21",
        "filename": "July 21 2019 House of Councillors election.xls",
        "path": "/main_content/000636675.xls",   # (5) 都道府県別党派別得票数（比例代表）
        "table": "（５）都道府県別党派別得票数（比例代表）",
        "source_page": "https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin25/index.html",
    },
    # --- 衆議院 (House of Representatives) ---
    {
        "election": "第47回衆院選 2014/12/14",
        "filename": "December 14 2014 House of Representatives election.xls",
        "path": "/main_content/000328949.xls",
        "table": "（７）比例代表選挙区別都道府県別党派別得票数",
        "source_page": "https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin47/index.html",
    },
    {
        "election": "第48回衆院選 2017/10/22",
        "filename": "October 22 2017 House of Representatives election.xls",
        "path": "/main_content/000516725.xls",
        "table": "（７）比例代表選挙区別都道府県別党派別得票数",
        "source_page": "https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin48/index.html",
    },
    {
        "election": "第49回衆院選 2021/10/31",
        "filename": "October 31 2021 House of Representatives election.xlsx",
        "path": "/main_content/000776973.xlsx",
        "table": "（７）比例代表選挙区別都道府県別党派別得票数",
        "source_page": "https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin49/index.html",
    },
]


def download_all(output_dir: str = OUTPUT_DIR, skip_existing: bool = True) -> list[dict]:
    """Download all target Excel files. Returns list of result dicts."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for t in TARGETS:
        out_path = os.path.join(output_dir, t["filename"])
        if skip_existing and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            results.append({"election": t["election"], "status": "skipped (exists)", "path": out_path})
            continue

        url = BASE_URL + t["path"]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": t["source_page"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en;q=0.9",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                results.append({
                    "election": t["election"],
                    "status": f"OK ({len(resp.content):,} bytes)",
                    "path": out_path,
                })
            else:
                results.append({
                    "election": t["election"],
                    "status": f"FAIL HTTP {resp.status_code} size={len(resp.content)}",
                    "path": None,
                })
        except Exception as e:
            results.append({"election": t["election"], "status": f"ERROR {e}", "path": None})

    return results


if __name__ == "__main__":
    print(f"Downloading to {OUTPUT_DIR}/")
    results = download_all()
    for r in results:
        print(f"  [{r['status']}] {r['election']}")
    ok = sum(1 for r in results if r["status"].startswith(("OK", "skipped")))
    print(f"\n{ok}/{len(results)} files available.")
