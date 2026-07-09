#!/usr/bin/env python3
"""Phase 1.5: preprocess metadata.json into clean CSVs and analysis plots.

Pipeline:
  1. Load raw metadata from ``data/raw/kokkai/metadata.json``.
  2. Attach derived fields to each speech:
       - ``parties_canonical`` — list of canonical parties parsed from
         ``speakerGroup`` (caucus names split on ``・`` / ``．`` / ``/``,
         then normalized; see ``party_utils.py``)
       - ``text`` — placeholder for Phase 2's text fetch (None for now)
       - ``has_joe_party`` — True if any canonical party is in Joe's
         election-data party list (for cross-team join)
  3. Atomically save the updated ``metadata.json`` back to disk.
  4. Compute canonical party counts and filter tiny parties (< 3
     speeches). No-party speeches (NaN ``speakerGroup``) are kept; only
     speeches whose canonical parties are ALL tiny are dropped.
  5. Emit clean CSVs and 5 figures under ``data/clean/`` and
     ``data/raw/kokkai/``.

Usage:
    uv run python sou/src/preprocess_kokkai.py

Inputs:
    sou/data/raw/kokkai/metadata.json   (produced by fetch_kokkai_metadata.py)

Outputs:
    sou/data/raw/kokkai/metadata.json                (in-place, with new fields)
    sou/data/clean/party_mapping.csv                 (raw -> canonical audit)
    sou/data/clean/party_mapping_joe.csv             (extended with Joe cross-ref)
    sou/data/clean/kokkai_party_counts.csv           (per-canonical-party counts)
    sou/data/clean/kokkai_metadata.csv               (full data, exploded canonical)
    sou/data/clean/kokkai_year_party.csv             (year x canonical_party)
    sou/data/clean/kokkai_keyword_counts.csv         (per-keyword speech counts)
    sou/data/clean/kokkai_overlap_matrix.csv         (keyword co-occurrence)
    sou/notebooks/figures/fig[1-5]_*.png             (analysis plots)
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from party_utils import (
    all_unique_raw_groups,
    attach_has_joe_party,
    attach_parties_canonical,
    attach_text_slot,
    compute_canonical_counts,
    filter_speeches_by_party_size,
    joe_crossref_for_party,
    load_joe_party_dicts,
    parse_speaker_group,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "sou" / "data" / "raw" / "kokkai"
CLEAN_DIR = REPO_ROOT / "sou" / "data" / "clean"
OUT_DIR = RAW_DIR  # Figures go alongside the raw data
META_FILE = RAW_DIR / "metadata.json"

# Tiny-party filter threshold. Parties with fewer speeches than this
# (after splitting compounds) are dropped from the working set.
MIN_PARTY_SPEECHES = 3

# ---------------------------------------------------------------------------
# Font setup for CJK in figures (system font preferred)
# ---------------------------------------------------------------------------
cjk_fonts = [f.name for f in fm.fontManager.ttflist if "Noto Serif CJK" in f.name]
plt.rcParams["font.family"] = cjk_fonts[0] if cjk_fonts else "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


# ---------------------------------------------------------------------------
# Atomic JSON writer (mirrors fetch_kokkai_metadata.py's pattern)
# ---------------------------------------------------------------------------
def save_json_atomic(path: Path, data: dict) -> None:
    """Write ``data`` to ``path`` atomically: temp file + rename.

    Avoids leaving a half-written ``metadata.json`` if the script is
    killed mid-write. Required because the raw file is the
    forward-compat backbone for Phase 2.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Load + derive
# ---------------------------------------------------------------------------
def load_metadata() -> dict:
    """Load raw metadata and attach the derived forward-compat fields.

    Returns the in-memory ``raw`` dict (with all speech records updated).
    The on-disk file is left untouched here — call ``save_metadata`` to
    persist the changes.
    """
    print(f"Loading {META_FILE} ...")
    with open(META_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    speeches = raw["speeches"]
    print(f"  speeches: {len(speeches)}, keywords: {len(raw['metadata'].get('keywords', []))}")

    # Idempotent attaches — safe to re-run.
    attach_parties_canonical(speeches)
    attach_text_slot(speeches)
    attach_has_joe_party(speeches)
    return raw


def save_metadata(raw: dict) -> None:
    """Atomically save ``raw`` back to ``metadata.json``."""
    print(f"Saving updated {META_FILE} (atomic) ...")
    save_json_atomic(META_FILE, raw)
    print(f"  -> {os.path.getsize(META_FILE) / 1024 / 1024:.1f} MB")


# ---------------------------------------------------------------------------
# CSVs
# ---------------------------------------------------------------------------
def build_dataframe(speeches: dict) -> pd.DataFrame:
    """Build a DataFrame from the in-memory speeches dict.

    Adds ``parties_canonical_str`` (semicolon-joined for CSV) so the
    analysis CSV is human-readable.
    """
    records = []
    for sid, s in speeches.items():
        records.append(
            {
                "speechID": sid,
                "session": s.get("session"),
                "nameOfHouse": s.get("nameOfHouse"),
                "nameOfMeeting": s.get("nameOfMeeting"),
                "issue": s.get("issue"),
                "date": s.get("date"),
                "year": int(s["date"][:4]) if s.get("date") else None,
                "speaker": s.get("speaker"),
                "speakerYomi": s.get("speakerYomi"),
                "speakerGroup": s.get("speakerGroup"),
                "speakerPosition": s.get("speakerPosition"),
                "speakerRole": s.get("speakerRole"),
                "speechURL": s.get("speechURL"),
                "meetingURL": s.get("meetingURL"),
                "pdfURL": s.get("pdfURL"),
                "keywords_matched": s.get("keywords_matched", []),
                "num_keywords": len(s.get("keywords_matched", [])),
                "parties_canonical": s.get("parties_canonical", []),
                "parties_canonical_str": ";".join(s.get("parties_canonical", [])),
                "has_joe_party": s.get("has_joe_party", False),
            }
        )
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    return df


def write_party_mapping_csv(speeches: dict) -> None:
    """Emit ``party_mapping.csv`` — the basic audit trail.

    One row per unique raw ``speakerGroup`` value, with the semicolon-
    joined list of canonical parties, the total speech count for that
    raw value, and a ``dropped`` flag indicating whether the raw value
    was filtered out (i.e. all of its canonical parties were tiny).

    This file is intentionally Joe-agnostic so we can backtrack to
    the cleaning step without the cross-team join dependency.
    """
    raw_groups = all_unique_raw_groups(speeches)
    counts_by_raw: Counter[str] = Counter()
    for s in speeches.values():
        g = s.get("speakerGroup")
        if isinstance(g, str) and g.strip():
            counts_by_raw[g] += 1

    rows = []
    for raw in raw_groups:
        canon = parse_speaker_group(raw)
        rows.append(
            {
                "raw_speaker_group": raw,
                "canonical_parties": ";".join(canon),
                "speech_count": counts_by_raw[raw],
                "dropped": not canon,  # NaN raw values are not "dropped", but produce empty canonical
            }
        )
    pd.DataFrame(rows).to_csv(
        CLEAN_DIR / "party_mapping.csv", index=False, encoding="utf-8-sig"
    )
    print(f"  -> party_mapping.csv: {len(rows)} rows (one per raw speakerGroup)")


def write_party_mapping_joe_csv(speeches: dict) -> None:
    """Emit ``party_mapping_joe.csv`` — extended cross-reference.

    One row per (raw, canonical) pair, with Joe's EN name and
    abbreviation for the canonical party. Useful for joining
    speech-data analysis with election-data analysis (where the
    party name in the JP column is the join key).
    """
    raw_groups = all_unique_raw_groups(speeches)
    rows = []
    for raw in raw_groups:
        for party in parse_speaker_group(raw):
            info = joe_crossref_for_party(party)
            rows.append(
                {
                    "raw_speaker_group": raw,
                    "canonical_party": party,
                    "in_joe_list": info["in_joe_list"],
                    "joe_en_name": info["joe_en_name"],
                    "joe_abbrv": info["joe_abbrv"],
                }
            )
    pd.DataFrame(rows).to_csv(
        CLEAN_DIR / "party_mapping_joe.csv", index=False, encoding="utf-8-sig"
    )
    n_joe = sum(1 for r in rows if r["in_joe_list"])
    print(
        f"  -> party_mapping_joe.csv: {len(rows)} rows "
        f"({n_joe} pairs in Joe's list, {len(rows) - n_joe} not)"
    )


def write_party_counts_csv(speeches: dict) -> None:
    """Emit ``kokkai_party_counts.csv`` — per-canonical-party counts.

    Post-tiny-filter; only canonical parties with >= MIN_PARTY_SPEECHES
    speeches are included. Each row also carries the Joe cross-ref so
    this file is joinable against Joe's election data without an extra
    lookup.
    """
    counts = compute_canonical_counts(speeches)
    rows = []
    for party, n in sorted(counts.items(), key=lambda x: -x[1]):
        if n < MIN_PARTY_SPEECHES:
            continue
        info = joe_crossref_for_party(party)
        rows.append(
            {
                "canonical_party": party,
                "unique_speeches": n,
                "in_joe_list": info["in_joe_list"],
                "joe_en_name": info["joe_en_name"],
                "joe_abbrv": info["joe_abbrv"],
            }
        )
    pd.DataFrame(rows).to_csv(
        CLEAN_DIR / "kokkai_party_counts.csv", index=False, encoding="utf-8-sig"
    )
    print(f"  -> kokkai_party_counts.csv: {len(rows)} canonical parties (>= {MIN_PARTY_SPEECHES} speeches)")


def write_full_csv(df: pd.DataFrame) -> None:
    """Emit ``kokkai_metadata.csv`` — full speech data with derived cols."""
    out = df[
        [
            "speechID",
            "session",
            "nameOfHouse",
            "nameOfMeeting",
            "issue",
            "date",
            "year",
            "speaker",
            "speakerYomi",
            "speakerGroup",
            "speakerPosition",
            "speakerRole",
            "speechURL",
            "meetingURL",
            "pdfURL",
            "keywords_matched",
            "num_keywords",
            "parties_canonical_str",
            "has_joe_party",
        ]
    ].copy()
    # Serialize list columns as semicolon-joined strings (CSV-safe).
    out["keywords_matched"] = out["keywords_matched"].apply(
        lambda v: ";".join(v) if isinstance(v, list) else ""
    )
    out.to_csv(CLEAN_DIR / "kokkai_metadata.csv", index=False, encoding="utf-8-sig")
    print(f"  -> kokkai_metadata.csv: {len(out)} rows")


def write_year_party_csv(df: pd.DataFrame, kept_parties: set[str]) -> None:
    """Emit ``kokkai_year_party.csv`` — year x canonical_party cross-tab.

    Speeches are exploded on ``parties_canonical``: a single speech in
    2 parties appears in 2 rows (one per party). Speeches with empty
    ``parties_canonical`` (NaN ``speakerGroup``) are excluded from this
    cross-tab but remain in ``kokkai_metadata.csv``.

    Rows for tiny parties (< MIN_PARTY_SPEECHES) are dropped here as
    well: a speech in (LDP, 参政党) where 参政党 is tiny will appear
    only in the LDP row, not in 参政党's row. This keeps the cross-tab
    consistent with ``kokkai_party_counts.csv`` (both report only
    non-tiny parties).

    Joe EN name and abbreviation are joined per canonical party for
    readability.
    """
    exploded = df.explode("parties_canonical")
    exploded = exploded.dropna(subset=["parties_canonical"])
    exploded = exploded[exploded["parties_canonical"].str.len() > 0]
    # Drop tiny parties from the exploded view (consistent with party_counts).
    exploded = exploded[exploded["parties_canonical"].isin(kept_parties)]
    # Join Joe info per party
    joe_info = {
        party: joe_crossref_for_party(party)
        for party in exploded["parties_canonical"].unique()
    }
    exploded["joe_en_name"] = exploded["parties_canonical"].map(
        lambda p: joe_info[p]["joe_en_name"]
    )
    exploded["joe_abbrv"] = exploded["parties_canonical"].map(
        lambda p: joe_info[p]["joe_abbrv"]
    )
    grouped = (
        exploded.groupby(
            ["year", "parties_canonical", "joe_en_name", "joe_abbrv"]
        )
        .size()
        .reset_index(name="count")
        .sort_values(["year", "count"], ascending=[True, False])
    )
    grouped.to_csv(
        CLEAN_DIR / "kokkai_year_party.csv", index=False, encoding="utf-8-sig"
    )
    print(f"  -> kokkai_year_party.csv: {len(grouped)} year x party rows")


def write_keyword_counts_csv(df: pd.DataFrame) -> None:
    """Emit ``kokkai_keyword_counts.csv`` — per-keyword speech counts."""
    kw_exp = df.explode("keywords_matched")
    kw_counts = (
        kw_exp["keywords_matched"]
        .value_counts()
        .reset_index()
    )
    kw_counts.columns = ["keyword", "unique_speeches"]
    kw_counts.to_csv(
        CLEAN_DIR / "kokkai_keyword_counts.csv", index=False, encoding="utf-8-sig"
    )
    print(f"  -> kokkai_keyword_counts.csv: {len(kw_counts)} keywords")


def write_overlap_matrix_csv(speeches: dict) -> None:
    """Emit ``kokkai_overlap_matrix.csv`` — keyword co-occurrence matrix."""
    sid_to_kws = {
        sid: set(s.get("keywords_matched", [])) for sid, s in speeches.items()
    }
    all_kws: list[str] = []
    for kws in sid_to_kws.values():
        all_kws.extend(kws)
    unique_kws = sorted(set(all_kws))
    n = len(unique_kws)
    overlap_arr = np.zeros((n, n), dtype=int)
    for i, kwi in enumerate(unique_kws):
        for j, kwj in enumerate(unique_kws):
            overlap_arr[i, j] = sum(
                1 for kws in sid_to_kws.values() if kwi in kws and kwj in kws
            )
    overlap_df = pd.DataFrame(overlap_arr, index=unique_kws, columns=unique_kws)
    overlap_df.to_csv(
        CLEAN_DIR / "kokkai_overlap_matrix.csv", encoding="utf-8-sig"
    )
    print(f"  -> kokkai_overlap_matrix.csv: {n}x{n} matrix")


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def write_figures(df: pd.DataFrame, party_counts: pd.DataFrame) -> None:
    """Generate the 5 standard analysis figures."""
    print("Generating figures ...")

    # Fig 1: keyword frequency
    kw_exp = df.explode("keywords_matched")
    kw_counts = kw_exp["keywords_matched"].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(kw_counts.index, kw_counts.values, color="steelblue")
    ax.set_xlabel("Unique Speeches")
    ax.set_title("Keyword Frequency Distribution")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig1_keyword_frequency.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Fig 2: keyword overlap heatmap
    sid_to_kws = {
        sid: set(s.get("keywords_matched", [])) for sid, s in df.set_index("speechID").iterrows()
    }
    unique_kws = sorted({k for s in sid_to_kws.values() for k in s})
    n = len(unique_kws)
    arr = np.zeros((n, n), dtype=int)
    for i, kwi in enumerate(unique_kws):
        for j, kwj in enumerate(unique_kws):
            arr[i, j] = sum(1 for s in sid_to_kws.values() if kwi in s and kwj in s)
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(arr, cmap="Blues", aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(unique_kws, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(unique_kws, fontsize=9)
    plt.colorbar(im, ax=ax, label="Shared speeches")
    ax.set_title("Keyword Overlap Matrix")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig2_overlap_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Fig 3: yearly speech count
    yearly = df.groupby("year").size().reset_index(name="count")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(yearly["year"], yearly["count"], color="steelblue", alpha=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Speech Count")
    ax.set_title("Yearly Speech Count (2012-2024)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig3_yearly_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Fig 4: top canonical parties (post-filter, post-explode, NaN excluded)
    if not party_counts.empty:
        top20 = party_counts.head(20)
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.barh(top20["canonical_party"], top20["unique_speeches"], color="coral")
        ax.set_xlabel("Speech Count")
        ax.set_title("Canonical Party Distribution (Top 20)")
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig(OUT_DIR / "fig4_party_distribution.png", dpi=150, bbox_inches="tight")
        plt.close()
    else:
        print("  (skipping fig4: no party counts)")

    # Fig 5: top committees
    comm_counts = df["nameOfMeeting"].value_counts().head(20)
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(comm_counts.index, comm_counts.values, color="seagreen")
    ax.set_xlabel("Speech Count")
    ax.set_title("Committee Distribution (Top 20)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig5_committee_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("  -> 5 figures saved")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] preprocess_kokkai.py")
    print("=" * 60)

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Load + derive
    raw = load_metadata()
    speeches = raw["speeches"]
    save_metadata(raw)

    # 2) Filter tiny parties (with Joe's party list as whitelist)
    print(f"\n[filter] dropping canonical parties with < {MIN_PARTY_SPEECHES} speeches ...")
    jp_to_eng, _ = load_joe_party_dicts()
    keep_parties = set(jp_to_eng.keys())
    n_before = len(speeches)
    filtered, kept = filter_speeches_by_party_size(
        speeches,
        min_count=MIN_PARTY_SPEECHES,
        keep_parties=keep_parties,
    )
    n_after = len(filtered)
    n_dropped = n_before - n_after
    n_nan = sum(1 for s in filtered.values() if not s.get("parties_canonical"))
    n_attributed = n_after - n_nan
    print(
        f"  -> kept {n_after}/{n_before} speeches "
        f"({n_attributed} party-attributed + {n_nan} no-party); "
        f"dropped {n_dropped} (tiny-party-only, not in Joe's list)"
    )
    print(
        f"  -> kept {len(kept)} canonical parties "
        f"({len(keep_parties)} from Joe whitelist + count >= {MIN_PARTY_SPEECHES})"
    )

    # 3) Build DataFrame from the filtered set
    df = build_dataframe(filtered)

    # 4) Audit + cross-ref CSVs
    print("\n[1/6] Writing party_mapping.csv ...")
    write_party_mapping_csv(speeches)

    print("\n[2/6] Writing party_mapping_joe.csv ...")
    write_party_mapping_joe_csv(speeches)

    print("\n[3/6] Writing kokkai_party_counts.csv ...")
    write_party_counts_csv(speeches)

    # 5) Derived CSVs
    print("\n[4/6] Writing full + per-keyword CSVs ...")
    write_full_csv(df)
    write_keyword_counts_csv(df)

    print("\n[5/6] Writing year x party + overlap CSVs ...")
    write_year_party_csv(df, kept)
    write_overlap_matrix_csv(speeches)

    # 6) Figures
    print("\n[6/6] Generating figures ...")
    party_counts_df = pd.read_csv(CLEAN_DIR / "kokkai_party_counts.csv")
    write_figures(df, party_counts_df)

    # 7) Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total speeches (after filter): {n_after}")
    print(f"  Party-attributed: {n_attributed}")
    print(f"  No-party (NaN speakerGroup): {n_nan}")
    print(f"  Dropped (tiny-party only): {n_dropped}")
    print(f"Date range: {df['date'].min().date()} ~ {df['date'].max().date()}")
    print(f"Unique speakers: {df['speaker'].nunique()}")
    print(f"Canonical parties (>= {MIN_PARTY_SPEECHES} speeches or in Joe's list): {len(kept)}")
    print(f"Speeches with has_joe_party=True: "
          f"{sum(1 for s in speeches.values() if s.get('has_joe_party'))}")
    print(f"Speeches with 2+ keywords: {(df['num_keywords'] > 1).sum()}")
    print("\nOutputs:")
    for p in [
        META_FILE,
        CLEAN_DIR / "party_mapping.csv",
        CLEAN_DIR / "party_mapping_joe.csv",
        CLEAN_DIR / "kokkai_party_counts.csv",
        CLEAN_DIR / "kokkai_metadata.csv",
        CLEAN_DIR / "kokkai_year_party.csv",
        CLEAN_DIR / "kokkai_keyword_counts.csv",
        CLEAN_DIR / "kokkai_overlap_matrix.csv",
        OUT_DIR / "fig1_keyword_frequency.png",
        OUT_DIR / "fig2_overlap_matrix.png",
        OUT_DIR / "fig3_yearly_distribution.png",
        OUT_DIR / "fig4_party_distribution.png",
        OUT_DIR / "fig5_committee_distribution.png",
    ]:
        print(f"  {p}")
    print("=" * 60)


if __name__ == "__main__":
    main()
