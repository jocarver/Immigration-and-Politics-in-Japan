#!/usr/bin/env python3
"""Build a speaker → prefecture (electoral district) lookup CSV.

The Kokkai NDL API (https://kokkai.ndl.go.jp/api.html) does NOT return
district/prefecture info — only speaker name, yomi, party, position, role.

This script:
  1. Loads our metadata (10,961 speeches) and identifies "real" speakers
     (Diet members / ministers / committee chairs). Excludes system rows
     like 会議録情報 / 参考人 / 公述人 / unknown bureaucrats.
  2. For each real speaker, queries ja.wikipedia.org's API to find their
     page and extract 選挙区 from the infobox.
  3. Outputs a CSV with disambiguation fields (yomi, party, house) so a
     human can verify and fix ambiguous cases later.

Output: sou/data/processed/speaker_district.csv

Caveats:
  - Diet members can switch districts across terms. For now we record
    the *latest known* district (Wikipedia tends to reflect current role).
    A per-speech mapping can be built downstream by joining on (speaker,
    date) — but for the cross-team merge, an aggregate-by-speaker table
    is enough.
  - HOC (参議院) has both 選挙区 (prefectural) and 比例代表 (national PR).
    We record both forms. Most HOC members are 選挙区 in practice.
  - 大臣/局長 who are bureaucrats (not Diet members) won't have a 選挙区
    on Wikipedia. The script flags them as `no_district` for manual review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
METADATA_FILE = SOUV / "data" / "raw" / "kokkai" / "metadata.json"
OUTPUT_FILE = SOUV / "data" / "processed" / "speaker_district.csv"
CACHE_FILE = SOUV / "data" / "processed" / ".speaker_district_cache.json"

# Politicians without a real constituency: 会議録情報 (system), 参考人 (witness),
# 公述人 (public commenter), 政府参考人 (government witness). The
# speakerPosition for bureaucrats (局長 / 審議官 / 政務官) is a gray zone — some
# are Diet members serving as ministers, others are career bureaucrats. We
# keep them in the lookup but expect many to have no Wikipedia 選挙区.
NON_POLITICIAN_POSITIONS = {
    "参考人",
    "公述人",
    "政府参考人",
}

# Pre-compiled regex for 選挙区 extraction from Wikipedia infobox.
#
# Japanese Diet members' Wikipedia pages have a multi-role infobox. The
# numbering is **reversed** from what you might expect:
#   - `| 選挙区 = ...`        = OLDEST role (first cabinet/position)
#   - `| 選挙区2 = ...`       = next role
#   - `| 選挙区5 = ...`       = most recent role (highest number)
# Some politicians have only `| 選挙区 =` (one role only).
#
# We want the **most recent** district, so we take the LAST match
# (highest number, lowest in the page).
#
# Examples of value forms:
#   "[[岡山県第2区|岡山2区]]"      → prefecture="岡山県", block="第2区"
#   "東京都第5区"                  → "東京都", "第5区"
#   "[[参議院比例区]]"             → "全国", "比例区"
#   "千葉選挙区"                   → "千葉県", "" (HOC prefectural)
#   "（[[静岡県第1区]]→）<br />（[[比例東海ブロック]]→）<br />静岡県第1区"
#                                  → "静岡県", "第1区" (latest segment)
ELEKIKU_RE = re.compile(
    r"\|\s*選挙区\d*\s*=\s*([^\n]+?)(?:\n|$)",
)


def is_politician(speaker: str, position: str, party: str) -> bool:
    """Filter out non-politician rows. Real Diet members have either
    a 議員 position OR a real party affiliation (excluding system rows)."""
    if speaker in ("会議録情報", "不明", ""):
        return False
    pos = position or ""
    if pos in NON_POLITICIAN_POSITIONS:
        return False
    if "議員" in pos or "大臣" in pos or "委員長" in pos or "副大臣" in pos or "政務官" in pos:
        return True
    # No position but has a real party → likely a politician without
    # position recorded (e.g. 委員長発言 with no position set)
    if party and party not in ("(none)", "会議録情報", "各派に属しない議員"):
        return True
    return False


def collect_real_speakers(meta: dict) -> dict[str, dict]:
    """Return {speaker: {yomi, house, party, position, n_speeches, first_date, last_date}}.

    Aggregates across all speeches by the same speaker. Uses the most
    recent house/party/position for the canonical record.
    """
    agg: dict[str, dict] = {}
    for sid, e in meta.items():
        sp = e.get("speaker", "?")
        if not is_politician(sp, e.get("speakerPosition"), e.get("speakerGroup")):
            continue
        rec = agg.setdefault(sp, {
            "yomi": e.get("speakerYomi") or "",
            "n_speeches": 0,
            "first_date": e.get("date", "9999"),
            "last_date": e.get("date", "0000"),
            "house_counts": Counter(),
            "party_counts": Counter(),
            "position_counts": Counter(),
        })
        rec["n_speeches"] += 1
        d = e.get("date", "")
        if d and d < rec["first_date"]:
            rec["first_date"] = d
        if d and d > rec["last_date"]:
            rec["last_date"] = d
        h = e.get("nameOfHouse") or ""
        if h:
            rec["house_counts"][h] += 1
        p = e.get("speakerGroup") or ""
        if p:
            rec["party_counts"][p] += 1
        pos = e.get("speakerPosition") or ""
        if pos:
            rec["position_counts"][pos] += 1
    return agg


def query_wikipedia(title: str, session: str = "sou-kokkai-lookup/1.0 (https://github.com/uooooo/skill-migration; contact: research)") -> dict | None:
    """Query ja.wikipedia.org API for a page by exact title.

    Returns the parsed wikitext content (or None if not found).
    Retries on 429 with exponential backoff (max 3 retries).
    """
    import urllib.error
    encoded = urllib.parse.quote(title)
    url = (
        f"https://ja.wikipedia.org/w/api.php?action=query"
        f"&titles={encoded}&prop=revisions&rvprop=content"
        f"&format=json&rvslots=main&redirects=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": session})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                # Exponential backoff: 2s, 8s
                wait = 2 * (4 ** attempt)
                time.sleep(wait)
                continue
            return {"_error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"_error": str(e)}
    return {"_error": "max retries"}


def extract_election_district(wikitext: str) -> tuple[str, str]:
    """Extract (district_prefecture, district_block) from Wikipedia infobox.

    Returns ("", "") if not found. Picks the FIRST 選挙区 entry (the
    lowest-numbered, which is the current/primary role). For politicians
    with only `| 選挙区2 =` (no `| 選挙区 =`), the only entry IS the
    current role — same logic.

    Examples of input → output:
      "[[岡山県第2区|岡山2区]]"      → ("岡山県", "第2区")
      "東京都第5区"                  → ("東京都", "第5区")
      "[[参議院比例区]]"             → ("全国", "比例区")
      "[[沖縄県選挙区]]"             → ("沖縄県", "")  # HOC prefectural
      "（[[静岡県第1区]]→）<br>[[山口県第4区|山口4区]]"
                                     → ("山口県", "第4区")  # latest segment
    """
    if not wikitext:
        return "", ""
    matches = ELEKIKU_RE.findall(wikitext)
    if not matches:
        return "", ""
    # Take the FIRST match (lowest-numbered = primary role).
    # Per Wikipedia convention, `| 選挙区 =` (no number) is the primary
    # / current role. Numbered entries (`| 選挙区2 =`, etc.) are older
    # or secondary roles. If `| 選挙区 =` doesn't exist, the only
    # numbered entry is the current one — same logic.
    raw = matches[0].strip()
    # Split on <br /> / <br> / → FIRST. Some entries have multiple
    # districts separated by arrows (career moves) or <br> (line breaks
    # in the infobox). We want the LAST non-empty segment (most recent).
    if "<br" in raw or "→" in raw:
        parts = re.split(r"<br\s*/?>|→", raw)
        raw = next((p.strip() for p in reversed(parts) if p.strip()), raw)
    # Strip surrounding parens and whitespace
    raw = raw.strip("（）() ").strip()
    # Strip wiki link display aliases — keep only the article target
    # e.g. "[[岡山県第2区|岡山2区]]" → "岡山県第2区"
    # Apply repeatedly because some values have nested/consecutive links.
    while True:
        new = re.sub(r"\[\[([^|\]]+?)(?:\|[^\]]*)?\]\]", r"\1", raw)
        if new == raw:
            break
        raw = new
    # Handle "参議院比例区" / "衆議院比例代表" — national PR
    if "比例" in raw:
        return "全国", "比例区"
    # Handle "○○選挙区" — HOC prefectural (e.g. 千葉選挙区)
    m2 = re.match(r"(.+?)選挙区$", raw)
    if m2:
        return m2.group(1), ""
    # Handle "○○[都道府県]第N区"
    m3 = re.match(r"(.+?[都道府県])第(\d+)区", raw)
    if m3:
        return m3.group(1), f"第{m3.group(2)}区"
    return raw, ""


def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limit number of speakers to look up (for testing)")
    parser.add_argument("--delay", type=float, default=0.1, help="Seconds between Wikipedia API calls")
    parser.add_argument("--overwrite", action="store_true", help="Re-query Wikipedia even if cached")
    parser.add_argument("--speakers", type=str, default=None, help="Comma-separated list of speakers to look up (for testing)")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Re-query only cache entries with status='error' (preserves 'ok' and 'no_district' results). "
                             "Use after a throttled run to recover failed entries without re-querying successful ones.")
    args = parser.parse_args()

    print("=" * 60)
    print("Speaker → Prefecture lookup")
    print("=" * 60)

    print(f"\n[1/4] Loading metadata from {METADATA_FILE.relative_to(REPO_ROOT)}")
    with open(METADATA_FILE) as f:
        meta = json.load(f)["speeches"]
    print(f"      {len(meta):,} speeches")

    print(f"\n[2/4] Identifying real speakers")
    speakers = collect_real_speakers(meta)
    print(f"      {len(speakers):,} unique real speakers")

    # Optional: filter to specific speakers (testing)
    if args.speakers:
        keep = set(s.strip() for s in args.speakers.split(","))
        speakers = {k: v for k, v in speakers.items() if k in keep}
        print(f"      filtered to {len(speakers)} by --speakers")

    # Sort by speech count (most common first)
    speakers_sorted = sorted(
        speakers.items(),
        key=lambda kv: -kv[1]["n_speeches"],
    )
    if args.limit:
        speakers_sorted = speakers_sorted[: args.limit]
        print(f"      limited to top {args.limit} by --limit")

    print(f"\n[3/4] Querying ja.wikipedia.org for {len(speakers_sorted):,} speakers")
    cache = load_cache()
    results = []
    n_ok = 0
    n_not_found = 0
    n_error = 0
    n_no_district = 0
    t0 = time.time()
    for i, (sp, info) in enumerate(speakers_sorted, 1):
        # Cache decision:
        #   --overwrite             → always re-query
        #   --retry-errors          → re-query only status=='error' (keep ok/no_district)
        #   default                 → use whatever is cached
        if not args.overwrite and sp in cache:
            cached = cache[sp]
            if args.retry_errors and cached.get("status") != "error":
                res = cached  # preserve successful results
            elif args.retry_errors and cached.get("status") == "error":
                # Drop the error so the query block runs; we'll write a fresh result.
                # Don't increment n_error here — that counter is for the live run.
                del cache[sp]
                res = None
            else:
                res = cached
        else:
            res = None

        if res is None:
            data = query_wikipedia(sp)
            if data is None or "_error" in data:
                err_msg = data.get("_error", "no data") if data else "no data (None)"
                res = {"status": "error", "error": err_msg}
                n_error += 1
                if n_error <= 3:
                    print(f"      DEBUG error #{n_error} at [{i}/{len(speakers_sorted)}] speaker='{sp}': {err_msg[:160]}")
            else:
                pages = data.get("query", {}).get("pages", {})
                # pages is a dict; first key is the page id or -1 for missing
                page = next(iter(pages.values())) if pages else {}
                if page.get("missing") or "-1" in str(page.get("pageid", "")):
                    res = {"status": "not_found"}
                    n_not_found += 1
                else:
                    rev = page.get("revisions", [{}])[0]
                    wikitext = rev.get("slots", {}).get("main", {}).get("*", "")
                    pref, blk = extract_election_district(wikitext)
                    if pref:
                        res = {
                            "status": "ok",
                            "page_title": page.get("title", ""),
                            "prefecture": pref,
                            "block": blk,
                        }
                        n_ok += 1
                    else:
                        res = {
                            "status": "no_district",
                            "page_title": page.get("title", ""),
                        }
                        n_no_district += 1
            cache[sp] = res
            if args.delay > 0 and i < len(speakers_sorted):
                time.sleep(args.delay)

        # Build record
        house = info["house_counts"].most_common(1)[0][0] if info["house_counts"] else ""
        party = info["party_counts"].most_common(1)[0][0] if info["party_counts"] else ""
        position = info["position_counts"].most_common(1)[0][0] if info["position_counts"] else ""
        results.append({
            "speaker": sp,
            "speaker_yomi": info["yomi"],
            "canonical_house": house,
            "canonical_party": party,
            "canonical_position": position,
            "n_speeches": info["n_speeches"],
            "first_date": info["first_date"],
            "last_date": info["last_date"],
            "wikipedia_title": res.get("page_title", ""),
            "district_prefecture": res.get("prefecture", ""),
            "district_block": res.get("block", ""),
            "status": res.get("status", ""),
            "source": "wikipedia" if res.get("status") == "ok" else "",
            "notes": "",
        })

        if i % 50 == 0 or i == len(speakers_sorted):
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            print(f"      [{i}/{len(speakers_sorted)}] ok={n_ok} not_found={n_not_found} "
                  f"no_district={n_no_district} error={n_error} | {elapsed:.0f}s elapsed, ~{(len(speakers_sorted)-i)/rate:.0f}s ETA")

    save_cache(cache)
    print(f"      cache saved: {CACHE_FILE.relative_to(REPO_ROOT)}")

    print(f"\n[4/4] Writing {OUTPUT_FILE.relative_to(REPO_ROOT)}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fields = list(results[0].keys()) if results else []
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    print(f"      {len(results):,} rows")

    # Summary
    statuses = Counter(r["status"] for r in results)
    print(f"\n      status breakdown: {dict(statuses)}")
    if results:
        ok_results = [r for r in results if r["status"] == "ok"]
        if ok_results:
            from collections import Counter as C
            prefecture_dist = C(r["district_prefecture"] for r in ok_results)
            print(f"      prefecture distribution (top 10): {dict(prefecture_dist.most_common(10))}")

    print("\n" + "=" * 60)
    print("DONE.")
    print("=" * 60)


if __name__ == "__main__":
    main()
