#!/usr/bin/env python3
"""Aggregate per-speech stance labels into a prefecture × year × house pivot.

Output: `sou/data/processed/sou_kokkai_aggregates_2014_2024.csv`

Schema (one row per year × prefecture × house cell):
  year, prefecture, house, n_speeches,
  pct_pro, pct_anti, pct_neutral, stance_score_mean,
  pct_switcher_speeches

Method:
  1. Inner-join stance classifications × metadata on speechID
     (adds date, speaker, house)
  2. Inner-join with speaker_district_switcher.csv on speaker
     (adds prefecture + is_switcher)
  3. Drop: bureaucrats / 参考人 / 公述人 (not in speaker_district)
  4. Drop: 175 no_district speakers (no prefecture to merge on)
  5. Filter to 2014 ≤ year ≤ 2024
  6. Group by (year, prefecture, house):
       n_speeches             = count
       pct_pro / anti / neutral = 100 × (label == X) / n
       stance_score_mean      = mean(score)   # pro=+1, anti=-1, neutral=0
       pct_switcher_speeches  = 100 × mean(is_switcher)
  7. Sort by year, prefecture, house
  8. Write CSV

This is the cross-team merge input for Joe — he joins his
prefecture-level election and immigration data on (prefecture, year).
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
META = SOUV / "data" / "raw" / "kokkai" / "metadata.json"
STANCES = SOUV / "data" / "processed" / "kokkai_stances_clean.json"
DISTRICT = SOUV / "data" / "processed" / "speaker_district_switcher.csv"
OUTPUT = SOUV / "data" / "processed" / "sou_kokkai_aggregates_2014_2024.csv"

YEAR_MIN, YEAR_MAX = 2014, 2024
VALID_HOUSES = {"衆議院", "参議院"}

# 47 prefectures + 全国 (HOC PR). Anything else in district_prefecture is either
# (a) a 衆議院 single-member district name like "千葉1区" — normalize to parent prefecture
# (b) a HoC 合区 name like "徳島県・高知県" — pick first prefecture
# (c) a Wikipedia infobox parse artifact like "| 当選回数 =" — drop
VALID_PREFECTURES = {
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
    "全国",
}

# Stem → canonical prefecture, used for "{stem}{N}区" pattern.
# e.g., "千葉1区" → "千葉県", "北海道2区" → "北海道", "東京1区" → "東京都"
# Sorted longest-first so 北海道 matches before 北 if any short stem existed.
PREFECTURE_STEMS: list[tuple[str, str]] = sorted(
    [
        (p[:-1] if p.endswith(("県", "府")) else (p[:-2] if p.endswith("都") else p), p)
        for p in VALID_PREFECTURES if p != "全国"
    ],
    key=lambda kv: -len(kv[0]),
)


def normalize_prefecture(raw: str) -> str | None:
    """Map a district_prefecture string to a canonical prefecture name.
    Returns None if the value is a parser artifact and should be dropped.
    """
    if not raw:
        return None
    # Drop obvious wikitext parser artifacts
    if raw.startswith("|") or raw.startswith("{{"):
        return None
    # Already a canonical prefecture
    if raw in VALID_PREFECTURES:
        return raw
    # 衆議院 single-member district: "{stem}{N}区" (e.g., "千葉1区" → "千葉県")
    if raw.endswith("区"):
        for stem, canonical in PREFECTURE_STEMS:
            if raw.startswith(stem):
                return canonical
    # HoC 合区 or comma-joined: "徳島県・高知県" → take first prefecture
    for sep in ["・", "、", ","]:
        if sep in raw:
            first = raw.split(sep, 1)[0].strip()
            if first in VALID_PREFECTURES:
                return first
    return None


def main() -> None:
    print("=" * 60)
    print("Aggregate stance by (year, prefecture, house)")
    print("=" * 60)

    print(f"\n[1/4] Loading inputs")
    meta = json.load(open(META, encoding="utf-8"))["speeches"]
    stances = json.load(open(STANCES, encoding="utf-8"))["speech_stances"]
    speakers = list(csv.DictReader(open(DISTRICT, encoding="utf-8")))
    print(f"      metadata:    {len(meta):,} speeches")
    print(f"      stances:     {len(stances):,} speeches")
    print(f"      speakers:    {len(speakers):,} (with district info)")

    # Build speaker → (prefecture, is_switcher) lookup
    sp_info: dict[str, dict] = {}
    n_normalized = 0
    n_unparseable = 0
    for s in speakers:
        raw = s.get("district_prefecture") or ""
        norm = normalize_prefecture(raw)
        if raw and not norm:
            n_unparseable += 1
        elif raw and norm != raw:
            n_normalized += 1
        sp_info[s["speaker"]] = {
            "prefecture": norm,
            "is_switcher": s.get("is_switcher") == "True",
        }
    print(f"      speakers with prefecture: "
          f"{sum(1 for v in sp_info.values() if v['prefecture']):,}")
    print(f"      district→prefecture normalized: {n_normalized:,}")
    print(f"      dropped as unparseable: {n_unparseable:,}")
    print(f"      switchers (≥2 districts on wiki): "
          f"{sum(1 for v in sp_info.values() if v['is_switcher']):,}")

    print(f"\n[2/4] Joining stance × metadata × district")
    # Group accumulators: (year, prefecture, house) -> list of {label, score, is_switcher}
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    n_no_stance = 0
    n_no_speaker_match = 0
    n_no_prefecture = 0
    n_wrong_year = 0
    n_wrong_house = 0
    for sid, st in stances.items():
        m = meta.get(sid, {})
        sp = m.get("speaker", "")
        si = sp_info.get(sp)
        if not si:
            n_no_speaker_match += 1
            continue
        pref = si["prefecture"]
        if not pref:
            n_no_prefecture += 1
            continue
        house = m.get("nameOfHouse", "")
        if house not in VALID_HOUSES:
            n_wrong_house += 1
            continue
        date = m.get("date", "")
        if not date:
            n_wrong_year += 1
            continue
        year = date[:4]
        if not (year.isdigit() and YEAR_MIN <= int(year) <= YEAR_MAX):
            n_wrong_year += 1
            continue
        groups[(year, pref, house)].append({
            "label": st["label"],
            "score": st["score"],
            "is_switcher": si["is_switcher"],
        })
    print(f"      joined: {sum(len(v) for v in groups.values()):,} speeches")
    print(f"      cells:  {len(groups):,} unique (year, prefecture, house)")
    print(f"      dropped: no_stance={n_no_stance:,} no_speaker_match={n_no_speaker_match:,} "
          f"no_prefecture={n_no_prefecture:,} wrong_year={n_wrong_year:,} wrong_house={n_wrong_house:,}")

    print(f"\n[3/4] Aggregating")
    rows = []
    for (year, pref, house), speeches in sorted(groups.items()):
        n = len(speeches)
        n_pro = sum(1 for s in speeches if s["label"] == "pro")
        n_anti = sum(1 for s in speeches if s["label"] == "anti")
        n_neutral = sum(1 for s in speeches if s["label"] == "neutral")
        score_sum = sum(s["score"] for s in speeches)
        n_switcher = sum(1 for s in speeches if s["is_switcher"])
        rows.append({
            "year": year,
            "prefecture": pref,
            "house": house,
            "n_speeches": n,
            "pct_pro": round(100 * n_pro / n, 1),
            "pct_anti": round(100 * n_anti / n, 1),
            "pct_neutral": round(100 * n_neutral / n, 1),
            "stance_score_mean": round(score_sum / n, 3),
            "pct_switcher_speeches": round(100 * n_switcher / n, 1),
        })

    print(f"\n[4/4] Writing {OUTPUT.relative_to(REPO_ROOT)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"      {len(rows):,} rows")

    # Summary
    from collections import Counter
    n_rows = len(rows)
    n_hoc = sum(1 for r in rows if r["house"] == "参議院")
    n_hor = sum(1 for r in rows if r["house"] == "衆議院")
    pref_count = Counter(r["prefecture"] for r in rows)
    n_pr = pref_count.get("全国", 0)
    print(f"\n      breakdown by house: 参議院={n_hoc}, 衆議院={n_hor}")
    print(f"      全国 (HOC PR) rows: {n_pr}")
    print(f"      unique prefectures: {len(pref_count)} (incl. 全国)")
    print(f"      sample row: {rows[0]}")


if __name__ == "__main__":
    main()
