#!/usr/bin/env python3
"""Merge per-shard stance outputs into the final kokkai_stances.json.

Each shard file (`kokkai_stances_shard_NN_of_MM.json`) contains a complete
window_stances + speech_stances dict for its slice of the corpus. We
concatenate the window_stances dicts and recompute speech_stances
freshly (modal vote, ties → neutral) so there's a single source of
truth for per-speech aggregation.

Usage:
    uv run python src/merge_stance_shards.py            # auto-detect shards
    uv run python src/merge_stance_shards.py --shards 20

Output:
    data/processed/kokkai_stances.json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
SHARDS_DIR = SOUV / "data" / "processed"
SHARD_PATTERN = "kokkai_stances_shard_{:02d}_of_{:02d}.json"
FINAL_OUTPUT = SHARDS_DIR / "kokkai_stances.json"

SCORE = {"anti": -1, "neutral": 0, "pro": 1}


def aggregate_per_speech(window_stances: dict) -> dict:
    """For each speechID, modal vote of its window stances. Ties → neutral."""
    out: dict = {}
    for sid, ws in window_stances.items():
        if not ws:
            continue
        counts = Counter(w["stance"] for w in ws)
        max_count = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_count]
        label = "neutral" if len(winners) > 1 else winners[0]
        out[sid] = {
            "label": label,
            "score": SCORE[label],
            "n_windows": len(ws),
            "counts": dict(counts),
        }
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--shards", type=int, default=None,
                   help="Total number of shards (default: auto-detect from filenames).")
    p.add_argument("--out", type=Path, default=FINAL_OUTPUT,
                   help=f"Final output path (default: {FINAL_OUTPUT})")
    return p.parse_args()


def find_shards(num_shards: int | None) -> list[Path]:
    """Return all shard files, sorted by id. Validate completeness."""
    if num_shards is None:
        # Auto-detect: find any shard file and infer total.
        candidates = sorted(SHARDS_DIR.glob("kokkai_stances_shard_*_of_*.json"))
        if not candidates:
            raise SystemExit(f"No shard files found in {SHARDS_DIR} matching kokkai_stances_shard_*_of_*.json")
        # Each filename has the form: ..._NN_of_MM.json
        nums = []
        totals = set()
        for c in candidates:
            stem = c.stem  # kokkai_stances_shard_03_of_20
            parts = stem.split("_of_")
            nums.append(int(parts[0].rsplit("_", 1)[1]))
            totals.add(int(parts[1]))
        if len(totals) > 1:
            raise SystemExit(f"Inconsistent num_shards across files: {totals}")
        num_shards = totals.pop()
        print(f"Auto-detected num_shards={num_shards} from filenames")
    paths = [SHARDS_DIR / SHARD_PATTERN.format(i, num_shards) for i in range(num_shards)]
    missing = [p for p in paths if not p.exists()]
    if missing:
        names = ", ".join(p.name for p in missing)
        raise SystemExit(f"Missing {len(missing)}/{num_shards} shard files: {names}")
    return paths


def main() -> None:
    args = parse_args()
    paths = find_shards(args.shards)

    # Load and concat window_stances from all shards.
    merged_windows: dict = {}
    shard_metas: list[dict] = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            shard = json.load(f)
        for sid, ws in shard.get("window_stances", {}).items():
            # Last-writer-wins is fine because shards partition the todo list
            # by index (no speechID appears in more than one shard).
            merged_windows[sid] = ws
        shard_metas.append({"file": p.name, "meta": shard.get("metadata", {})})
    print(f"Merged {sum(len(v) for v in merged_windows.values()):,} window stances from {len(paths)} shards")
    print(f"  covering {len(merged_windows):,} unique speeches")

    # Fresh per-speech aggregation.
    speech_stances = aggregate_per_speech(merged_windows)
    print(f"Aggregated to {len(speech_stances):,} speech stances")

    n_windows = sum(len(v) for v in merged_windows.values())
    label_dist = Counter()
    for sid in speech_stances:
        label_dist[speech_stances[sid]["label"]] += 1
    dist_str = ", ".join(f"{k}={v}" for k, v in sorted(label_dist.items()))

    final_meta = {
        "merged_at": datetime.now().isoformat(),
        "num_shards": len(paths),
        "shard_files": [p.name for p in paths],
        "n_window_stances": n_windows,
        "n_speech_stances": len(speech_stances),
        "speech_label_distribution": dict(label_dist),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(args.out.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": final_meta,
                    "window_stances": merged_windows,
                    "speech_stances": speech_stances,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        shutil.move(tmp_path, str(args.out))
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    print(f"\n{'=' * 60}")
    print(f"Final output: {args.out}")
    print(f"  Windows:  {n_windows:,}")
    print(f"  Speeches: {len(speech_stances):,}")
    print(f"  Per-speech label distribution: {dist_str}")


if __name__ == "__main__":
    main()
