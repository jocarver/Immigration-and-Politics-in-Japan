#!/usr/bin/env python3
"""Merge 6-shard stance outputs with proper modal-vote dedup.

The original merge_stance_shards.py uses last-writer-wins on the
window_stances[sid] list, which loses data when a single speech's
windows are scattered across multiple shards (the sharding bug:
`todo[shard_id :: num_shards]` splits windows by flat-index, so a
speech with N windows at positions P..P+N-1 has its windows spread
across multiple shards).

This v2 merge:
  1. Collects ALL (sid, window_idx) -> [stance, ...] across all 6 shards
  2. For each (sid, idx), takes the modal stance. Ties → neutral.
  3. Builds window_stances[sid] = [stance0, stance1, ...] cleanly.
  4. Also extracts the REMAINING (sid, idx) pairs that are not yet
     classified (i.e., the 8,135 windows we still need to process).
  5. Writes:
       - data/processed/kokkai_stances_clean.json   (finished work)
       - data/processed/kokkai_windows_remaining.json (todo for restart)
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
SHARDS_DIR = SOUV / "data" / "processed"
WINDOWS_FILE = SHARDS_DIR / "kokkai_windows.json"
CLEAN_OUTPUT = SHARDS_DIR / "kokkai_stances_clean.json"
REMAINING_OUTPUT = SHARDS_DIR / "kokkai_windows_remaining.json"

SCORE = {"anti": -1, "neutral": 0, "pro": 1}


def collect_all_classifications(num_shards: int = 6) -> dict:
    """Return {(sid, idx): [(stance, model), ...]} across all shards."""
    pair_to_classifications: dict = {}
    for s in range(num_shards):
        path = SHARDS_DIR / f"kokkai_stances_shard_{s:02d}_of_{num_shards:02d}.json"
        with open(path) as f:
            d = json.load(f)
        for sid, ws in d.get("window_stances", {}).items():
            for idx, w in enumerate(ws):
                if "stance" in w:
                    pair_to_classifications.setdefault((sid, idx), []).append(
                        (w["stance"], w.get("model"))
                    )
    return pair_to_classifications


def modal_vote(stances: list[str]) -> str:
    """Pick the modal stance. Ties → neutral."""
    counts = Counter(stances)
    max_count = max(counts.values())
    winners = [k for k, v in counts.items() if v == max_count]
    return "neutral" if len(winners) > 1 else winners[0]


def build_window_stances(
    classifications: dict, all_windows: dict
) -> tuple[dict, dict, dict]:
    """Build clean window_stances + speech_stances + a list of conflicts.

    Returns:
        window_stances: {sid: [stance, stance, ...]} (clean)
        speech_stances: {sid: {label, score, n_windows, counts}} (modal per speech)
        conflicts: { (sid, idx): {"stances": [...], "modal": str, "all_agree": bool} }
    """
    window_stances: dict = {}
    conflicts: dict = {}
    for sid, ws in all_windows.items():
        stances_for_speech = []
        for idx in range(len(ws)):
            if (sid, idx) in classifications:
                stances = [c[0] for c in classifications[(sid, idx)]]
                modal = modal_vote(stances)
                stances_for_speech.append(modal)
                if len(set(stances)) > 1:
                    conflicts[(sid, idx)] = {
                        "stances": stances,
                        "modal": modal,
                    }
            else:
                stances_for_speech.append(None)  # placeholder
        # Only keep speeches that have at least one classification.
        if any(s is not None for s in stances_for_speech):
            window_stances[sid] = stances_for_speech

    # Per-speech aggregation (modal across windows, ties → neutral).
    speech_stances: dict = {}
    for sid, stances in window_stances.items():
        non_null = [s for s in stances if s is not None]
        if not non_null:
            continue
        counts = Counter(non_null)
        max_count = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_count]
        label = "neutral" if len(winners) > 1 else winners[0]
        speech_stances[sid] = {
            "label": label,
            "score": SCORE[label],
            "n_windows": len(non_null),
            "counts": dict(counts),
        }
    return window_stances, speech_stances, conflicts


def find_remaining(
    all_windows: dict, classifications: dict
) -> dict:
    """Find (sid, idx) pairs not yet classified. Returns {sid: [idx, ...]}."""
    remaining: dict = {}
    for sid, ws in all_windows.items():
        missing = [idx for idx in range(len(ws)) if (sid, idx) not in classifications]
        if missing:
            remaining[sid] = missing
    return remaining


def save_atomic(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(tmp, str(path))
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def main() -> None:
    print("=" * 60)
    print("Merge v2: modal-vote dedup + extract remaining")
    print("=" * 60)

    # 1. Collect all classifications from 6 shard files
    classifications = collect_all_classifications(num_shards=6)
    n_pairs = len(classifications)
    n_classifications = sum(len(v) for v in classifications.values())
    print(f"\n[1/4] Collected classifications from 6 shards")
    print(f"      unique (sid, idx) pairs: {n_pairs:,}")
    print(f"      total classifications:   {n_classifications:,}")
    print(f"      overlap factor:          {n_classifications / n_pairs:.2f}x")

    # 2. Load all windows
    with open(WINDOWS_FILE) as f:
        windows_data = json.load(f)
    all_windows = windows_data["windows"]
    n_total = sum(len(v) for v in all_windows.values())
    print(f"\n[2/4] Loaded windows file: {len(all_windows):,} speeches, {n_total:,} windows")

    # 3. Build clean window_stances + speech_stances
    window_stances, speech_stances, conflicts = build_window_stances(
        classifications, all_windows
    )
    n_windows_done = sum(
        1 for sid in window_stances for s in window_stances[sid] if s is not None
    )
    print(f"\n[3/4] After dedup:")
    print(f"      {n_windows_done:,} / {n_total:,} windows classified "
          f"({n_windows_done / n_total * 100:.1f}%)")
    print(f"      {len(speech_stances):,} speeches have at least one classified window")
    print(f"      {len(conflicts):,} (sid, idx) pairs had inconsistent classifications "
          f"(resolved via modal vote)")

    # Distribution
    label_dist = Counter(s["label"] for s in speech_stances.values())
    print(f"      per-speech distribution: {dict(label_dist)}")

    # 4. Save clean output
    final_meta = {
        "merged_at": datetime.now().isoformat(),
        "merge_method": "modal_vote_per_(sid,idx)",
        "source_shards": [
            f"kokkai_stances_shard_{s:02d}_of_06.json" for s in range(6)
        ],
        "n_window_stances": n_windows_done,
        "n_speech_stances": len(speech_stances),
        "n_conflicts_resolved_by_modal_vote": len(conflicts),
        "speech_label_distribution": dict(label_dist),
        "coverage_pct": round(n_windows_done / n_total * 100, 2),
    }
    save_atomic(
        {
            "metadata": final_meta,
            "window_stances": window_stances,
            "speech_stances": speech_stances,
        },
        CLEAN_OUTPUT,
    )
    print(f"\n[4a/4] Saved clean: {CLEAN_OUTPUT}")
    print(f"       ({(CLEAN_OUTPUT.stat().st_size / 1024):.1f} KB)")

    # 5. Save remaining windows
    remaining = find_remaining(all_windows, classifications)
    n_remaining = sum(len(v) for v in remaining.values())
    print(f"\n[4b/4] Remaining to classify: {n_remaining:,} windows "
          f"across {len(remaining):,} speeches")
    save_atomic(
        {
            "metadata": {
                "extracted_at": datetime.now().isoformat(),
                "n_remaining_windows": n_remaining,
                "n_remaining_speeches": len(remaining),
                "source": "kokkai_stances_clean.json (12,606 finished)",
            },
            "remaining": remaining,
        },
        REMAINING_OUTPUT,
    )
    print(f"       Saved: {REMAINING_OUTPUT} "
          f"({(REMAINING_OUTPUT.stat().st_size / 1024):.1f} KB)")

    print("\n" + "=" * 60)
    print("DONE. Work is saved. Safe to kill the 6 shard processes.")
    print("=" * 60)


if __name__ == "__main__":
    main()
