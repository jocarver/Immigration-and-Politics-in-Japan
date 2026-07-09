#!/usr/bin/env python3
"""LLM stance classifier — Gemma 4 (26B / 31B) via Google AI Studio.

Classifies each window in `kokkai_windows.json` as pro / neutral / anti
on immigration reform. Output is written per-window with the stance
label; per-speech aggregation (modal vote) is computed at the end.

Key design:
- Multi-key rotation: round-robin over (api_key, model) combinations.
  With K keys and 2 models, we get 2K effective rate (the per-model
  quotas are independent — see NDL AI Studio rate table).
- Shardable: --shard-id N --num-shards M filters the todo list to
  every Nth window, writing to a per-shard output file. Combined with
  --key-idx / --model pinning, this lets N parallel processes each
  own a unique (key, model) pair and a unique window slice — no rate
  limit contention, no duplicate work.
- Resumable: re-running skips windows already classified.
- Atomic save every CHECKPOINT_EVERY windows.
- The window dicts deliberately have no party info (avoid biasing the
  LLM — see feedback memory on LLM input hygiene).

Usage:
    # Single-process round-robin
    uv run python src/classify_stance_gemma.py --limit 5       # test
    uv run python src/classify_stance_gemma.py                # full run

    # Parallel run: 20 processes, each pinned to one (key, model)
    for i in $(seq 0 19); do
        ki=$((i % 10))
        mi=$((i / 10))
        uv run python src/classify_stance_gemma.py \
            --shard-id $i --num-shards 20 \
            --key-idx $ki --model "${MODELS[$mi]}" \
            --sleep 2 &
    done
    wait

Output:
    data/processed/kokkai_stances.json             # single-process run
    data/processed/kokkai_stances_shard_NN_of_MM.json   # sharded run
        {"metadata": {...}, "window_stances": {sid: [{stance, model, ...}, ...]},
         "speech_stances": {sid: {score, label, counts, ...}, ...}}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
WINDOWS_FILE = SOUV / "data" / "processed" / "kokkai_windows.json"
OUTPUT_FILE = SOUV / "data" / "processed" / "kokkai_stances.json"
CLEAN_FILE = SOUV / "data" / "processed" / "kokkai_stances_clean.json"
ENV_FILE = SOUV / ".env"

# Both Gemma 4 variants. Their rate-limit pools are independent, so
# rotating through both effectively doubles throughput. The 26B is
# actually a sparse MoE "a4b" variant per AI Studio's listing.
MODELS: list[str] = ["gemma-4-26b-a4b-it", "gemma-4-31b-it", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]

# Google AI Studio native endpoint (per-model).
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
SLEEP_SECONDS = 2
CHECKPOINT_EVERY = 100
REQUEST_TIMEOUT = 120
# Per-key rate cap. The AI Studio cap is 15 RPM per key. We aim for
# ~10 RPM (6s/call) to stay well under the cap — a previous run that
# hammered the 15 RPM limit got stuck in 429 loops. With 6 shards each
# pinned to 1 key, that's 10 RPM per key = 40% of cap. notify_429()
# bumps the timestamp on 429 so the next call sleeps a full interval
# (slows down automatically).
RATE_LIMIT_INTERVAL = 6.0
# 429 retry policy: exponential backoff capped at 5 min, up to 6 attempts.
# Total worst-case wait per window: 65+130+260+300+300+300 = 1355s (~23 min).
MAX_429_RETRIES = 6
MAX_429_BACKOFF = 300
# Transient-error retry policy (HTTP 5xx, network timeout, parse failures,
# "no final (non-thought) part"). 3 retries × (4s sleep + 6s rate limit)
# ≈ 30s worst case. Same shape as 429 but shorter — these are typically
# resolved in 1-2 retries.
MAX_TRANSIENT_RETRIES = 3
TRANSIENT_SLEEP = 4.0
# Gemma 4 "thinks" by default (parts with "thought": true). We need
# enough tokens for thinking + the final short JSON answer.
MAX_OUTPUT_TOKENS = 1500

PROMPT_TEMPLATE = """\
You are a deterministic, single-word classification API. Do not deliberate. Do not analyze historical context. Instantly output JSON based on immediate keyword matching. Think in less than 50 words.

Task: Classify this Japanese Diet speech on immigration policy into pro / neutral / anti.

- pro: supports expansion / positive evaluation
- neutral: factual report, procedural remark, or unclear stance
- anti: supports reduction / strictness / criticism / concerns

Output ONLY one line (no explanation, no reasoning, no markdown):
{{"stance": "pro"}} OR {{"stance": "neutral"}} OR {{"stance": "anti"}}

Passage:
{text}
"""


# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------
def load_env_file(path: Path) -> dict[str, str]:
    """Minimal .env parser. No variable expansion, no quoting tricks."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def load_api_keys(env: dict[str, str]) -> list[str]:
    """Collect GOOGLE_API_KEY_1, _2, ... from the env dict."""
    keys: list[str] = []
    i = 1
    while True:
        k = env.get(f"GOOGLE_API_KEY_{i}")
        if not k:
            break
        keys.append(k)
        i += 1
    return keys


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
class RateLimiter:
    """Per-key rate limiter. Ensures ≥ RATE_LIMIT_INTERVAL between calls
    on the same key. AI Studio's per-key cap is 15 RPM, so 4s/call keeps
    us under it (and below the throttle threshold).
    """

    def __init__(self, interval: float = RATE_LIMIT_INTERVAL):
        self.interval = interval
        self._last: dict[str, float] = {}

    def wait(self, api_key: str) -> None:
        last = self._last.get(api_key, 0.0)
        elapsed = time.time() - last
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last[api_key] = time.time()

    def notify_429(self, api_key: str) -> None:
        """Reset the key's slot so the retry doesn't immediately re-throttle."""
        self._last[api_key] = time.time()


def classify_window(text: str, api_key: str, model: str) -> tuple[str | None, str | None]:
    """Call Gemma 4 to classify a window's stance. Returns (stance, error).

    stance is one of "pro", "neutral", "anti" on success, None on parse
    failure. error is a short string on HTTP error, None on success.
    """
    prompt = PROMPT_TEMPLATE.format(text=text)
    url = f"{API_BASE}/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), headers=headers
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, f"network: {e}"

    # Gemma 4 returns multiple "parts": some with "thought": true (internal
    # reasoning) and one final "text" part. We only want the final answer.
    try:
        parts = resp["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return None, "no content in response"

    # Take the last part that isn't marked as a thought.
    final_text = ""
    for p in parts:
        if not p.get("thought", False):
            final_text = p.get("text", "")
    if not final_text:
        # Fallback: model hit MAX_TOKENS before emitting the final answer
        # part. The conclusion usually lives inside the last thought, so
        # scan ALL parts and take the LAST stance value (avoid matching
        # earlier counterfactual mentions like "if it were pro: ...").
        all_text = "\n".join(p.get("text", "") for p in parts)
        matches = re.findall(r'"stance"\s*:\s*"?(pro|anti|neutral)"?', all_text, re.I)
        if matches:
            return matches[-1].lower(), None
        return None, "no final (non-thought) part in response"

    # The model sometimes wraps the JSON in markdown code fences; strip them.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", final_text, re.DOTALL)
    if fenced:
        json_str = fenced.group(1)
    else:
        match = re.search(r"\{[^{}]*\"stance\"[^{}]*\}", final_text)
        if not match:
            return None, f"no JSON found in: {final_text[:120]!r}"
        json_str = match.group(0)

    try:
        parsed = json.loads(json_str)
        stance = parsed.get("stance", "").lower().strip()
    except json.JSONDecodeError as e:
        return None, f"JSON parse: {e} ({json_str[:80]!r})"

    if stance not in {"pro", "neutral", "anti"}:
        return None, f"invalid stance: {stance!r}"
    return stance, None


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def load_existing(path: Path) -> tuple[dict, dict]:
    """Load existing stance output. Returns (window_stances, speech_stances)."""
    if not path.exists():
        return {}, {}
    with open(path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    return existing.get("window_stances", {}), existing.get("speech_stances", {})


def shard_output_path(base: Path, shard_id: int, num_shards: int) -> Path:
    """Per-shard output path. e.g. kokkai_stances_shard_03_of_20.json"""
    return base.with_name(f"{base.stem}_shard_{shard_id:02d}_of_{num_shards:02d}{base.suffix}")


def stable_shard_for_sid(sid: str, num_shards: int) -> int:
    """Deterministic speechID -> shard assignment. Uses md5 (NOT Python's
    built-in hash(), which is randomized across runs for strings).

    Stable across processes, machines, and Python versions.
    """
    digest = hashlib.md5(sid.encode("utf-8")).hexdigest()
    return int(digest, 16) % num_shards


def load_clean_for_shard(
    clean_file: Path, all_windows: dict, shard_id: int, num_shards: int
) -> dict:
    """Load the clean baseline (12,606 done windows) for THIS SHARD's slice.

    The previous design sharded by flat todo-index, which split a single
    speech's windows across multiple shards. This function uses a stable
    speechID-hash partition so each shard owns a DISJOINT set of speeches.

    Returns {sid: [stance, None, stance, ...]} where the list is the same
    length as all_windows[sid] and entries are stance strings (or None
    for windows the baseline hasn't classified).
    """
    if not clean_file.exists():
        return {}
    with open(clean_file) as f:
        clean = json.load(f)
    clean_ws = clean.get("window_stances", {})
    out: dict = {}
    for sid, ws in all_windows.items():
        if stable_shard_for_sid(sid, num_shards) != shard_id:
            continue
        if sid in clean_ws:
            # Normalize entries to dict format: stance string -> {"stance": str, "model": "clean_baseline"};
            # None -> {} placeholder (matches the original 6-shard file shape).
            converted = []
            for w in clean_ws[sid]:
                if isinstance(w, str):
                    converted.append({"stance": w, "model": "clean_baseline"})
                elif w is None:
                    converted.append({})
                else:
                    converted.append(w)
            out[sid] = converted
    return out


def save_checkpoint(
    window_stances: dict,
    speech_stances: dict,
    keys: list[str],
    models: list[str],
    output_file: Path = OUTPUT_FILE,
) -> None:
    """Atomic save with a fresh speech_stances recompute."""
    # Recompute speech_stances from window_stances (modal vote, ties → neutral).
    speech_stances = aggregate_per_speech(window_stances)
    n_windows = sum(len(v) for v in window_stances.values())
    meta = {
        "classified_at": datetime.now().isoformat(),
        "n_keys": len(keys),
        "models": models,
        "n_window_stances": n_windows,
        "n_speech_stances": len(speech_stances),
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(output_file.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": meta,
                    "window_stances": window_stances,
                    "speech_stances": speech_stances,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        shutil.move(tmp_path, str(output_file))
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def aggregate_per_speech(window_stances: dict) -> dict:
    """For each speechID, modal vote of its window stances. Ties → neutral."""
    SCORE = {"anti": -1, "neutral": 0, "pro": 1}
    out: dict = {}
    for sid, ws in window_stances.items():
        if not ws:
            continue
        # Filter placeholder empty dicts (set when a partial speech was resumed)
        # AND FAILED_429 markers (not real classifications — should not count
        # in modal vote, and SCORE dict doesn't have them → KeyError).
        counts = Counter(
            w["stance"] for w in ws
            if "stance" in w and w["stance"] != "FAILED_429"
        )
        if not counts:
            continue
        # Modal vote. Ties: pick neutral (the "uncertain" default).
        max_count = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_count]
        if len(winners) > 1:
            label = "neutral"
        else:
            label = winners[0]
        out[sid] = {
            "label": label,
            "score": SCORE[label],
            "n_windows": len(ws),
            "counts": dict(counts),
        }
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--limit", type=int, default=None,
                   help="Process at most N new windows (for testing).")
    p.add_argument("--sleep", type=float, default=SLEEP_SECONDS,
                   help=f"Sleep between calls in seconds (default: {SLEEP_SECONDS}).")
    p.add_argument("--shard-id", type=int, default=None,
                   help="Process only the Nth shard (0-indexed). Requires --num-shards.")
    p.add_argument("--num-shards", type=int, default=None,
                   help="Total number of shards. Requires --shard-id.")
    p.add_argument("--key-idx", type=int, default=None,
                   help="Pin to the Nth API key (0-indexed). Skips round-robin.")
    p.add_argument("--model", choices=MODELS, default=None,
                   help="Pin to a single model. Skips round-robin.")
    p.add_argument("--skip-probe", action="store_true",
                   help="Skip the startup key probe. Use when you know the keys are live "
                        "and the API is having transient issues.")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()
    # Shard config
    if (args.shard_id is None) != (args.num_shards is None):
        raise SystemExit("--shard-id and --num-shards must be given together")
    if args.shard_id is not None:
        if args.shard_id < 0 or args.shard_id >= args.num_shards:
            raise SystemExit(f"--shard-id {args.shard_id} out of range [0, {args.num_shards})")
    output_file = (
        shard_output_path(OUTPUT_FILE, args.shard_id, args.num_shards)
        if args.shard_id is not None
        else OUTPUT_FILE
    )

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Phase 3: LLM stance classification")
    if args.shard_id is not None:
        print(f"  Shard {args.shard_id} / {args.num_shards} → {output_file.name}")
    print("=" * 60)

    env = load_env_file(ENV_FILE)
    keys = load_api_keys(env)
    if not keys:
        raise SystemExit(
            f"No GOOGLE_API_KEY_* found in {ENV_FILE}. "
            "Create sou/.env with one key per AI Studio project."
        )
    # Apply --key-idx / --model pinning (used for parallel runs to give
    # each process its own (key, model) pair and avoid rate-limit bursts).
    if args.key_idx is not None:
        if args.key_idx < 0 or args.key_idx >= len(keys):
            raise SystemExit(f"--key-idx {args.key_idx} out of range [0, {len(keys)})")
        keys = [keys[args.key_idx]]
    if args.model is not None:
        models = [args.model]
    else:
        models = MODELS
    # Probe each (key, model) before starting. 401 = key is genuinely dead
    # (quota cap or invalid) — no retry. 5xx / network / parse errors are
    # transient — retry up to 3 times before declaring dead. --skip-probe
    # bypasses this entirely (use when you trust the keys).
    probe_model = models[0]
    live_keys: list[str] = []
    if args.skip_probe:
        live_keys = list(keys)
        print(f"  --skip-probe: trusting all {len(keys)} key(s)")
    else:
        for ki, k in enumerate(keys):
            success = False
            last_err: str | None = None
            for attempt in range(3):
                probe_stance, probe_err = classify_window("ping", k, probe_model)
                last_err = probe_err
                if probe_err is None and probe_stance in ("pro", "neutral", "anti"):
                    live_keys.append(k)
                    success = True
                    suffix = f" (after {attempt + 1} tries)" if attempt else ""
                    print(f"  key {ki}: ok{suffix}")
                    break
                if probe_err and "HTTP 401" in probe_err:
                    break
                if attempt < 2:
                    time.sleep(2)
            if not success:
                print(f"  key {ki}: DEAD ({last_err or 'parse-fail'})")
    if not live_keys:
        raise SystemExit("All API keys are dead. Check AI Studio quota / key validity.")
    keys = live_keys
    combinations = [(k, m) for k in keys for m in models]
    print(f"Loaded {len(keys)} live API key(s), {len(models)} model(s)")
    print(f"Effective combinations: {len(combinations)} ({len(models) * len(keys)} rate slots)")
    if args.key_idx is not None or args.model is not None:
        print(f"  pinned to: keys={args.key_idx!r}, model={args.model!r}")

    if not WINDOWS_FILE.exists():
        raise SystemExit(f"windows file not found: {WINDOWS_FILE}. Run clean_kokkai_text.py first.")

    with open(WINDOWS_FILE, "r", encoding="utf-8") as f:
        all_windows = json.load(f)["windows"]
    print(f"Loaded {len(all_windows):,} speeches, {sum(len(v) for v in all_windows.values()):,} windows")

    # When sharding: load the clean baseline (12,606 done) filtered to THIS
    # shard's speechID-hash slice. Each shard's window_stances only contains
    # speeches it OWNS — no overlap with peer shards.
    if args.shard_id is not None:
        window_stances = load_clean_for_shard(
            CLEAN_FILE, all_windows, args.shard_id, args.num_shards
        )
        n_done = sum(1 for ws in window_stances.values() for w in ws if w is not None)
        n_speeches = len(window_stances)
        print(f"  sharded mode: this shard owns {n_speeches:,} speeches, "
              f"{n_done:,} windows already done (from baseline)")
    else:
        window_stances, _ = load_existing(output_file)
        print(f"Resuming: {sum(len(v) for v in window_stances.values()):,} window stances already done")

    # Build the todo list: (speechID, window_idx, window_dict) pairs that
    # still need classification.
    todo: list[tuple[str, int, dict]] = []
    for sid, ws in all_windows.items():
        # SpeechID-hash partition: only this shard's speeches (avoids the
        # flat-index bug that split a speech's windows across shards).
        if args.shard_id is not None and stable_shard_for_sid(sid, args.num_shards) != args.shard_id:
            continue
        existing = window_stances.get(sid, [])
        for idx, w in enumerate(ws):
            if idx < len(existing) and existing[idx] is not None and "stance" in existing[idx]:
                continue  # already done
            todo.append((sid, idx, w))

    print(f"Remaining: {len(todo):,} windows" + (f" (shard {args.shard_id}/{args.num_shards})" if args.shard_id is not None else ""))

    if not todo:
        print("Nothing to do. Exiting.")
        return

    # Process loop with round-robin
    combo_idx = 0
    n_ok = n_err = 0
    n_failed_429 = 0
    label_counter: Counter = Counter()
    start = time.time()
    # Per-key rate limiter. Enforces ≥ RATE_LIMIT_INTERVAL between calls
    # on the same key, so the per-key 15 RPM cap is never exceeded.
    rate_limiter = RateLimiter(interval=RATE_LIMIT_INTERVAL)
    for i, (sid, idx, w) in enumerate(todo, 1):
        text = w["text"]
        api_key, model = combinations[combo_idx % len(combinations)]
        combo_idx += 1
        rate_limiter.wait(api_key)
        stance, err = classify_window(text, api_key, model)

        if err is not None:
            n_err += 1
            # 429s need a LONG cooldown with exponential backoff. The
            # original 1-shot 65s retry lost data when the cooldown
            # wasn't enough (e.g., during a 20h hammer the keys went
            # into deep cooldown). Now we retry up to MAX_429_RETRIES
            # times with 65s, 130s, 260s, ... up to MAX_429_BACKOFF.
            # If still failing, mark the window as FAILED_429 (so it's
            # NOT lost — it's saved in window_stances for later retry).
            if "HTTP 429" in err:
                rate_limiter.notify_429(api_key)
                recovered = False
                for retry in range(MAX_429_RETRIES):
                    wait = min(65 * (2 ** retry), MAX_429_BACKOFF)
                    print(f"  [{i}/{len(todo)}] 429 from {model}, "
                          f"retry {retry+1}/{MAX_429_RETRIES}, sleeping {wait}s")
                    time.sleep(wait)
                    rate_limiter.wait(api_key)
                    stance, err = classify_window(text, api_key, model)
                    if err is None:
                        print(f"  [{i}/{len(todo)}] recovered after retry {retry+1}")
                        recovered = True
                        break
                    if err and "HTTP 429" in err:
                        rate_limiter.notify_429(api_key)
                        continue
                    # non-429 error after 429 — bail out of retry loop
                    break
                if not recovered and err is not None:
                    # Don't lose the window — mark as FAILED_429 so the
                    # v2 merge can filter it out and we can retry later.
                    print(f"  [{i}/{len(todo)}] FAILED_429 after {MAX_429_RETRIES} retries, marking")
                    n_failed_429 += 1
                    window_stances.setdefault(sid, [])
                    while len(window_stances[sid]) <= idx:
                        window_stances[sid].append({})
                    window_stances[sid][idx] = {
                        **w, "stance": "FAILED_429", "model": model, "error": err
                    }
                    continue
            elif "HTTP 401" in err:
                # Quota cap or dead key. Skip — resumable on next run.
                print(f"  [{i}/{len(todo)}] 401 from {model} (quota/dead), skipping")
                if err is not None:
                    continue
            elif (
                "HTTP 5" in err
                or "no final" in err
                or "network" in err
            ):
                # Quick retry on the next combination.
                time.sleep(args.sleep * 2)
                api_key, model = combinations[combo_idx % len(combinations)]
                combo_idx += 1
                rate_limiter.wait(api_key)
                stance, err = classify_window(text, api_key, model)
            if err is not None:
                print(f"  [{i}/{len(todo)}] ERROR ({model}): {err}")
                continue

        # Save the stance
        window_stances.setdefault(sid, [])
        while len(window_stances[sid]) <= idx:
            window_stances[sid].append({})
        window_stances[sid][idx] = {**w, "stance": stance, "model": model}
        label_counter[stance] += 1
        n_ok += 1

        if i % 10 == 0 or i == len(todo):
            elapsed = time.time() - start
            rate = i / elapsed if elapsed else 0
            eta = (len(todo) - i) / rate if rate else 0
            dist = ", ".join(f"{k}={v}" for k, v in sorted(label_counter.items()))
            print(
                f"  [{i}/{len(todo)}] {n_ok} ok, {n_err} err | "
                f"distribution: {dist} | {elapsed:.0f}s elapsed, ~{eta:.0f}s ETA"
            )

        if i % CHECKPOINT_EVERY == 0 or i == len(todo):
            save_checkpoint(window_stances, {}, keys, models, output_file)
            print(f"  [CHECKPOINT: {n_ok} ok, {n_err} err]")

        time.sleep(args.sleep)

    # Final save
    save_checkpoint(window_stances, {}, keys, models, output_file)
    elapsed = time.time() - start
    dist = ", ".join(f"{k}={v}" for k, v in sorted(label_counter.items()))
    print(f"\n{'=' * 60}")
    print(f"Phase 3 test/run done in {elapsed:.0f}s")
    print(f"  {n_ok} ok, {n_err} err, {n_failed_429} FAILED_429")
    print(f"  distribution: {dist}")
    print(f"  saved to: {output_file}")


if __name__ == "__main__":
    main()
