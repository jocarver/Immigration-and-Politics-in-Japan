#!/usr/bin/env python3
"""Kokkai speech text cleaning - extract ±1 sentence windows around keywords.

For each speech with text, finds all keyword mentions and extracts a window
of three sentences (one before, the keyword-mentioning one, one after). This
is the input that will be fed to an LLM stance classifier in a later step.

Why windows:
- A full Diet speech is often 1,000+ chars. A 3-sentence window around a
  keyword is typically 100-200 chars, cutting LLM tokens by 80-90%.
- The keyword-mentioning sentence is the most stance-relevant; ±1 sentence
  provides disambiguating context (handles irony, hedging, surrounding
  argument).

Why dedupe: a long speech can mention "技能実習" 5+ times in the same
paragraph. Identical ±1 sentence contexts = identical classifications,
so we only keep one window per unique text.

Resumable: re-running the script skips speeches already in the output
file. Atomic saves every CHECKPOINT_EVERY speeches.

Usage:
    uv run python sou/src/clean_kokkai_text.py
    uv run python sou/src/clean_kokkai_text.py --limit 100

Output:
    data/processed/kokkai_windows.json
        {"metadata": {...}, "windows": {speechID: [{text, keywords, char_start}, ...]}}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# Same 9 keywords as Phase 1 (fetch_kokkai_metadata.py). These anchor the
# window extraction - a speech with no keyword mentions has no windows.
KEYWORDS: list[str] = [
    "技能実習", "外国人労働者", "出入国管理", "特定技能", "外国人材",
    "不法滞在", "多文化共生", "移民政策", "外国人犯罪",
]

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "sou" / "data" / "raw" / "kokkai"
TEXTS_FILE = RAW_DIR / "speech_texts.json"
OUTPUT_DIR = REPO_ROOT / "sou" / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "kokkai_windows.json"
CHECKPOINT_EVERY = 100

# Sentence-terminator regex. Diet minutes are well-punctuated so a simple
# character class is enough. Captures the delimiter with the sentence so
# windows rejoin cleanly.
_SENT_SPLIT = re.compile(r"([^。！？\n]*(?:[。！？\n]|$))")

# Minimum window length in characters. The keyword-mentioning sentence
# is the meaningful unit, so even short windows are kept. We just skip
# degenerate single-character matches.
MIN_WINDOW_CHARS = 5


# ---------------------------------------------------------------------------
# Core: window extraction
# ---------------------------------------------------------------------------
def _split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split text into sentences. Returns list of (start, end, sentence_text).

    Each entry includes the trailing delimiter (。/！/?/\\n) so windows
    rejoin cleanly. The final entry may have no delimiter if the text
    doesn't end with one.
    """
    sentences: list[tuple[int, int, str]] = []
    pos = 0
    for m in _SENT_SPLIT.finditer(text):
        chunk = m.group(1)
        if not chunk:
            continue
        s, e = m.start(1), m.end(1)
        # Avoid duplicating coverage if regex matches at the same pos
        if s < pos:
            continue
        sentences.append((s, e, chunk))
        pos = e
    return sentences


def extract_windows(text: str, keywords: list[str] = KEYWORDS) -> list[dict]:
    """Extract ±1 sentence windows around each keyword mention.

    Returns a list of dicts: {"text", "keywords", "char_start"}.
    Dedupes identical windows (by text content) per speech.
    """
    if not text:
        return []
    sentences = _split_sentences(text)
    if not sentences:
        return []

    windows: list[dict] = []
    seen: set[str] = set()

    for sent_idx, (s_start, s_end, s_text) in enumerate(sentences):
        kws_in_sent = [kw for kw in keywords if kw in s_text]
        if not kws_in_sent:
            continue
        win_start = sentences[max(0, sent_idx - 1)][0]
        win_end = sentences[min(len(sentences) - 1, sent_idx + 1)][1]
        window_text = text[win_start:win_end].strip()
        if not window_text or window_text in seen:
            continue
        if len(window_text) < MIN_WINDOW_CHARS:
            # Skip degenerate matches; the keyword presence is the real filter.
            continue
        seen.add(window_text)
        windows.append({
            "text": window_text,
            "keywords": kws_in_sent,
            "char_start": win_start,
        })
    return windows


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def load_texts(path: Path) -> dict[str, str]:
    """Load speech_texts.json. Returns {speechID: text}."""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d.get("texts", {})


def load_existing_windows(path: Path) -> tuple[dict, dict]:
    """Load existing windows file. Returns (windows dict, metadata dict).

    The windows dict is keyed by speechID with values being lists of
    window dicts. The metadata dict preserves the prior extracted_at and
    other fields; we update extracted_at on each run.
    """
    if not path.exists():
        return {}, {}
    with open(path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    return existing.get("windows", {}), existing.get("metadata", {})


def save_checkpoint(windows: dict, prev_meta: dict) -> None:
    """Atomic save (tempfile + rename)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    n_windows = sum(len(v) for v in windows.values())
    meta = {
        **prev_meta,
        "extracted_at": datetime.now().isoformat(),
        "n_speeches_with_windows": len(windows),
        "n_windows_total": n_windows,
        "keywords_used": KEYWORDS,
    }
    fd, tmp_path = tempfile.mkstemp(dir=str(OUTPUT_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                {"metadata": meta, "windows": windows},
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
        "--limit",
        type=int,
        default=None,
        help="Process at most N new speeches (useful for testing).",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Phase 2.5: window extraction")
    print("=" * 60)

    if not TEXTS_FILE.exists():
        raise SystemExit(f"speech_texts.json not found at {TEXTS_FILE}. Run fetch_kokkai_text.py first.")

    texts = load_texts(TEXTS_FILE)
    print(f"Loaded {len(texts)} speech texts")

    windows, prev_meta = load_existing_windows(OUTPUT_FILE)
    print(f"Resuming: {len(windows)} speeches already processed, "
          f"{sum(len(v) for v in windows.values())} windows total")

    # Skip already-processed speeches
    new_sids = [sid for sid in texts if sid not in windows]
    print(f"New speeches to process: {len(new_sids)}")

    if args.limit:
        new_sids = new_sids[: args.limit]
        print(f"Limiting to first {len(new_sids)} speeches")

    if not new_sids:
        print("Nothing to do. Exiting.")
        return

    # Process loop
    for i, sid in enumerate(new_sids, 1):
        text = texts.get(sid) or ""
        ws = extract_windows(text, KEYWORDS)
        if ws:
            windows[sid] = ws

        if i % CHECKPOINT_EVERY == 0 or i == len(new_sids):
            save_checkpoint(windows, prev_meta)
            total_windows = sum(len(v) for v in windows.values())
            print(f"  [{i}/{len(new_sids)}] {len(windows)} speeches, {total_windows} windows")

    # Final save
    save_checkpoint(windows, prev_meta)
    total_windows = sum(len(v) for v in windows.values())
    print(f"\nDone: {len(windows)} speeches, {total_windows} windows total")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
