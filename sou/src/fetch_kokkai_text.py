#!/usr/bin/env python3
"""Kokkai NDL API - Phase 2: speech text fetch.

Fetches the full text of every speech in meetings (issueIDs) that contain
at least one party-attributed speech. The text is written to a separate
file keyed by speechID, NOT into metadata.json, so the metadata file
stays compact for analysis.

The /meeting API does not take a speechID parameter. It returns the full
meeting record (all speeches in that meeting) when given an issueID. Our
speechIDs have the form "{issueID}_{speechOrder}", so we derive the
issueID and dedupe — 10,961 speeches collapse to 1,770 unique issueIDs
(a 6.2x reduction in API calls).

The run is resumable: re-running the script skips already-completed
issueIDs. Output is written atomically (tempfile + rename) every
CHECKPOINT_EVERY issueIDs to avoid losing progress on interruption.

Usage:
    uv run python sou/src/fetch_kokkai_text.py --mode party_first
    uv run python sou/src/fetch_kokkai_text.py --mode party_first --limit 5
    uv run python sou/src/fetch_kokkai_text.py --issue 121115261X01720230526

Output:
    data/raw/kokkai/speech_texts.json   # {"metadata": {...}, "texts": {sid: text, ...}}
"""
import argparse
import json
import os
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "sou" / "data" / "raw" / "kokkai"
METADATA_FILE = OUTPUT_DIR / "metadata.json"
OUTPUT_FILE = OUTPUT_DIR / "speech_texts.json"
BASE_URL = "https://kokkai.ndl.go.jp/api/meeting"
SLEEP_SECONDS = 2
CHECKPOINT_EVERY = 10

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def derive_issue_id(speech_id: str) -> str | None:
    """Strip the trailing _{speechOrder} suffix from a speechID.

    speechID format: "{issueID}_{speechOrder}", e.g.
        121115261X01720230526_199
    The issueID encodes: Diet session, meeting number, date.
    """
    return speech_id.rsplit("_", 1)[0] if "_" in speech_id else None


def target_issue_ids(speeches: dict, mode: str) -> set[str]:
    """Return the set of issueIDs to fetch for the given mode.

    ``party_first``: every issueID that contains at least one speech with
        a non-empty parties_canonical list. (Phase 2 first run.)
    ``all``: every issueID that does NOT contain any party-attributed
        speech. (Phase 2 second run — fills in no-party-only meetings.)
    """
    party_ids: set[str] = set()
    all_ids: set[str] = set()
    for sid, s in speeches.items():
        iid = derive_issue_id(sid)
        if iid is None:
            continue
        all_ids.add(iid)
        if s.get("parties_canonical"):
            party_ids.add(iid)
    if mode == "party_first":
        return party_ids
    if mode == "all":
        return all_ids - party_ids
    raise ValueError(f"Unknown mode: {mode!r}. Use 'party_first' or 'all'.")


def fetch_meeting(issue_id: str) -> list[tuple[str, str]]:
    """Fetch /meeting?issueID={issue_id} and return list of (speechID, text).

    Raises on network/HTTP error — caller decides whether to retry/skip.
    """
    params = {"recordPacking": "json", "issueID": issue_id}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    records = data.get("meetingRecord", [])
    if not records:
        return []
    speech_record = records[0].get("speechRecord", [])
    return [
        (sr["speechID"], sr["speech"])
        for sr in speech_record
        if sr.get("speechID") and sr.get("speech") is not None
    ]


def load_existing(path: Path) -> tuple[dict, set[str]]:
    """Load existing checkpoint. Returns (texts dict, completed issueIDs set)."""
    with open(path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    texts = existing.get("texts", {})
    completed = set(existing.get("metadata", {}).get("completed_issue_ids", []))
    return texts, completed


def save_checkpoint(
    texts: dict,
    completed: set[str],
    mode: str,
    total: int,
) -> None:
    """Atomic save (write to temp, then rename)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(OUTPUT_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "fetched_at": datetime.now().isoformat(),
                        "mode": mode,
                        "total_issue_ids": total,
                        "completed_issue_ids": sorted(completed),
                        "speech_count": len(texts),
                    },
                    "texts": texts,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        shutil.move(tmp_path, str(OUTPUT_FILE))
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--mode",
        choices=["party_first", "all"],
        default="party_first",
        help="party_first: only issueIDs with party-attributed speeches (default). "
             "all: only issueIDs WITHOUT party-attributed speeches (second run).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N issueIDs (useful for testing).",
    )
    p.add_argument(
        "--issue",
        type=str,
        default=None,
        help="Process a single specific issueID (debug/sanity check). "
             "Overrides --mode and --limit.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Phase 2: speech text fetch")
    print(f"Mode: {args.mode}")
    print("=" * 60)

    if not METADATA_FILE.exists():
        raise SystemExit(f"metadata.json not found at {METADATA_FILE}. Run fetch_kokkai_metadata.py first.")

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        speeches = json.load(f)["speeches"]
    print(f"Loaded {len(speeches)} speeches from metadata.json")

    # Resolve target issueIDs
    if args.issue:
        target = {args.issue}
        mode_label = f"single-issue:{args.issue}"
    else:
        target = target_issue_ids(speeches, args.mode)
        mode_label = args.mode
    print(f"Target issueIDs ({mode_label}): {len(target)}")

    # Load existing checkpoint for resume
    texts: dict = {}
    completed: set[str] = set()
    if OUTPUT_FILE.exists() and not args.issue:
        try:
            texts, completed = load_existing(OUTPUT_FILE)
            print(f"Resuming: {len(texts)} texts, {len(completed)} issueIDs done")
        except json.JSONDecodeError:
            print("Warning: existing checkpoint corrupted, starting fresh")

    remaining = sorted(target - completed)
    print(f"Remaining: {len(remaining)} issueIDs")

    if args.limit:
        remaining = remaining[: args.limit]
        print(f"Limiting to first {len(remaining)} issueIDs")

    if not remaining:
        print("Nothing to do. Exiting.")
        return

    # Fetch loop
    start = time.time()
    for i, iid in enumerate(remaining, 1):
        print(f"\n▶ [{i}/{len(remaining)}] {iid}")
        try:
            pairs = fetch_meeting(iid)
        except Exception as e:
            print(f"  [ERROR] {iid}: {e}")
            print(f"  Skipping; will retry on next run if needed")
            time.sleep(SLEEP_SECONDS)
            continue

        for sid, text in pairs:
            texts[sid] = text
        completed.add(iid)
        print(f"  -> {len(pairs)} speeches | cumulative: {len(texts)}")

        if i % CHECKPOINT_EVERY == 0 or i == len(remaining):
            save_checkpoint(texts, completed, args.mode if not args.issue else "single", len(target))
            elapsed = time.time() - start
            eta = elapsed / i * (len(remaining) - i)
            print(f"  [CHECKPOINT: {len(texts)} texts | {elapsed:.0f}s elapsed, ~{eta:.0f}s ETA]")

        time.sleep(SLEEP_SECONDS)

    # Final save
    save_checkpoint(texts, completed, args.mode if not args.issue else "single", len(target))

    print(f"\n{'=' * 60}")
    print(f"Phase 2 run done")
    print(f"   texts saved: {len(texts)}")
    print(f"   issueIDs done: {len(completed)}")
    print(f"   saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
