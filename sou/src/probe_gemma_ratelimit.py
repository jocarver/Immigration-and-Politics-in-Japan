#!/usr/bin/env python3
"""Probe the actual Gemma 4 rate-limit dynamics on Google AI Studio.

Sends N requests in quick succession, tracks HTTP status and any rate-limit
headers, and reports:
- success rate
- the time between the first 429 and the first subsequent 200 (cooldown)
- any rate-limit response headers (X-RateLimit-*, Retry-After, etc.)

This is a diagnostic — not part of the stance pipeline. Run before
deciding the parallel-run strategy.

Usage:
    uv run python src/probe_gemma_ratelimit.py --key-idx 0 --model gemma-4-26b-a4b-it
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOUV = REPO_ROOT / "sou"
ENV_FILE = SOUV / ".env"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MODELS = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]

PROMPT = "Reply with the single word: ok"

# A minimal body — short prompt + tight tokens + no thinking overhead.
BODY = {
    "contents": [{"parts": [{"text": PROMPT}]}],
    "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8},
}


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def load_api_keys(env: dict[str, str]) -> list[str]:
    keys: list[str] = []
    i = 1
    while True:
        k = env.get(f"GOOGLE_API_KEY_{i}")
        if not k:
            break
        keys.append(k)
        i += 1
    return keys


def call(api_key: str, model: str) -> tuple[int, dict, str, float]:
    """Make one call. Returns (http_status, headers, body, elapsed_sec)."""
    url = f"{API_BASE}/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    data = json.dumps(BODY).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.status
            headers = dict(r.getheaders())
            body = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        headers = dict(e.headers.items()) if e.headers else {}
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
    except Exception as e:
        return -1, {}, f"network: {e}", time.time() - t0
    return status, headers, body, time.time() - t0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--key-idx", type=int, default=0, help="API key index (0-based).")
    p.add_argument("--model", choices=MODELS, default=MODELS[0])
    p.add_argument("--n", type=int, default=30, help="Number of probe calls.")
    p.add_argument("--sleep", type=float, default=0.5, help="Sleep between calls in seconds.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    env = load_env_file(ENV_FILE)
    keys = load_api_keys(env)
    if not keys:
        raise SystemExit(f"No GOOGLE_API_KEY_* in {ENV_FILE}")
    api_key = keys[args.key_idx]

    print(f"Probing key #{args.key_idx} on {args.model} with {args.n} calls, sleep={args.sleep}s")
    print("=" * 60)

    calls = []  # (i, status, elapsed, headers_subset)
    cooldown_after_first_429 = None
    for i in range(1, args.n + 1):
        status, headers, body, elapsed = call(api_key, args.model)
        t = time.time()
        # Pull rate-limit-relevant headers if present.
        rl = {k: v for k, v in headers.items()
              if k.lower() in {"retry-after", "x-ratelimit-limit", "x-ratelimit-remaining",
                               "x-ratelimit-reset", "x-goog-quota-user", "x-goog-quota-reset"}}
        if rl:
            print(f"  [{i:2d}] status={status} elapsed={elapsed:.1f}s headers={rl}")
        else:
            print(f"  [{i:2d}] status={status} elapsed={elapsed:.1f}s")
        calls.append((i, t, status, elapsed, rl, body[:120]))
        # Track first 429 → first 200 after.
        if status == 429 and cooldown_after_first_429 is None:
            cooldown_after_first_429 = {"first_429_at_call": i, "first_429_at_t": t}
        elif status == 200 and cooldown_after_first_429 is not None and "recovered_at_call" not in cooldown_after_first_429:
            cooldown_after_first_429["recovered_at_call"] = i
            cooldown_after_first_429["recovered_at_t"] = t
            cooldown_after_first_429["cooldown_sec"] = t - cooldown_after_first_429["first_429_at_t"]
        if i < args.n:
            time.sleep(args.sleep)

    # Summary
    statuses = [c[2] for c in calls]
    n_200 = statuses.count(200)
    n_429 = statuses.count(429)
    n_other = len(statuses) - n_200 - n_429

    print(f"\n{'=' * 60}")
    print(f"Summary: {n_200}/200 ok, {n_429}/429 throttled, {n_other}/other")
    if n_other:
        from collections import Counter
        print(f"  other statuses: {dict(Counter(s for s in statuses if s not in (200, 429)))}")
    # Find 429 pattern
    first_429_idx = next((i for i, s in enumerate(statuses) if s == 429), None)
    if first_429_idx is not None:
        print(f"  First 429 at call #{first_429_idx + 1}")
        # Count consecutive 429s
        consec = 0
        for s in statuses[first_429_idx:]:
            if s == 429:
                consec += 1
            else:
                break
        print(f"  Consecutive 429s starting there: {consec}")
    # Wall time
    if calls:
        total = calls[-1][1] - calls[0][1]
        print(f"  Total wall time: {total:.1f}s, call rate: {args.n / total:.2f}/s = {60 * args.n / total:.1f}/min")
    if cooldown_after_first_429 and "cooldown_sec" in cooldown_after_first_429:
        print(f"  Cooldown observed: {cooldown_after_first_429['cooldown_sec']:.1f}s "
              f"(from call {cooldown_after_first_429['first_429_at_call']} to call "
              f"{cooldown_after_first_429['recovered_at_call']})")
    # Show all unique header keys we ever saw
    all_hk = set()
    for c in calls:
        all_hk.update(c[4].keys())
    if all_hk:
        print(f"  Rate-limit headers seen: {sorted(all_hk)}")
    else:
        print("  No rate-limit response headers observed.")


if __name__ == "__main__":
    main()
