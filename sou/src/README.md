# sou/src/ — Pipeline Scripts

12 Python scripts, 3,363 lines. Organized into 4 phases of the Kokkai speech data pipeline.

---

## Quickstart

Run phases 1 → 4 in order to reproduce the dataset:

```bash
# Phase 1: collect speech metadata (~30 min for 10,961 speeches)
python3 src/fetch_kokkai_metadata.py

# Phase 2: fetch full meeting text (~8 hours, can be skipped for metadata-only analysis)
python3 src/fetch_kokkai_text.py

# Phase 3: classify stances via LLM (~6 hours with 6 shards, requires API keys)
python3 src/classify_stance_gemma.py --num-shards 6 --shard-id 0 --key-idx 1 --model gemini-3.1-flash-lite
# repeat for shards 1..5 with different --shard-id and --key-idx
python3 src/merge_stance_shards_v2.py

# Phase 4: enrich speakers with district info and aggregate to prefecture × year
python3 src/lookup_speaker_district.py --delay 1.5
python3 src/detect_switchers.py
python3 src/aggregate_stance_by_prefecture_year.py
```

---

## Phase 1 — Data collection

| Script | Input | Output | Runtime |
|---|---|---|---|
| `fetch_kokkai_metadata.py` | Kokkai NDL search API | `data/raw/kokkai/metadata.json` (10,961 speeches) | ~30 min |
| `fetch_kokkai_text.py` | `/meeting` endpoint, 1 call per meetingID | `data/raw/kokkai/meetings/*.json` | ~8 hours |

`fetch_kokkai_metadata.py` queries 9 immigration-related keywords (技能実習, 外国人労働者, etc.) and deduplicates by `speechID`. The full text fetch in `fetch_kokkai_text.py` is needed for the per-window stance classification (windows are text-derived) but is still in progress as of 2026-06-14.

---

## Phase 2 — Preprocessing

| Script | Input | Output | Runtime |
|---|---|---|---|
| `preprocess_kokkai.py` | `meetings/*.json` | `data/processed/kokkai_windows.json` (text-split windows) | ~10 min |
| `clean_kokkai_text.py` | raw meeting text | normalized text (regex, 全角/半角) | helper module |
| `party_utils.py` | raw `speakerGroup` strings | canonical party lists | imported as a library |

`preprocess_kokkai.py` splits each speech's text into ~500-character windows (LLM context size constraint) and attaches metadata. `party_utils.py` normalizes parliamentary caucus names — handles compound caucuses (e.g., `自由民主党・無所属の会` → `["自由民主党", "無所属の会"]`), applies a tiny-party filter (< 3 speeches dropped), and preserves no-party speeches (committee chairs, expert witnesses).

---

## Phase 3 — Stance classification (the heavyweight)

| Script | Input | Output | Runtime |
|---|---|---|---|
| `probe_gemma_ratelimit.py` | live API | rate-limit report (per key × model) | ~5 min |
| `classify_stance_gemma.py` | `kokkai_windows.json` | `data/processed/kokkai_stances_shard_*_of_06.json` (6 shards) | ~6 hours total |
| `merge_stance_shards.py` | (deprecated v1) | — | don't use |
| `merge_stance_shards_v2.py` | 6 shard files | `data/processed/kokkai_stances_clean.json` (modal-vote dedup) | ~30 s |

**`classify_stance_gemma.py`** is the main entry point:
- Splits windows across `--num-shards` shards using a **speechID-hash partition** (so each shard owns disjoint SPEECHES, not windows — no overlap)
- Pinned to one API key per shard via `--key-idx`
- Supports multiple models: `gemma-4-26b-a4b-it`, `gemma-4-31b-it`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`
- 429 retry policy: 6 attempts with exponential backoff (65s → 130s → 260s → 300s capped)
- FAILED_429 markers are filtered from modal vote (don't count as a real classification)
- Auto-resumes from existing shard file (no `--resume` flag needed)

**`merge_stance_shards_v2.py`** is the only correct merger. v1 had a last-writer-wins bug that lost data when the same `(speechID, window_idx)` appeared in multiple shard files. v2 dedups via modal vote across overlapping classifications.

For 10,961 speeches × ~2 windows each = 20,741 windows. With 6 shards running in parallel at ~10 RPM per key, full coverage takes ~6 hours.

---

## Phase 4 — Aggregation

| Script | Input | Output | Runtime |
|---|---|---|---|
| `lookup_speaker_district.py` | `metadata.json` + ja.wikipedia.org | `data/processed/speaker_district.csv` (803 rows) | ~28 min |
| `detect_switchers.py` | `speaker_district.csv` + ja.wikipedia.org | `data/processed/speaker_district_switcher.csv` | ~16 min |
| `aggregate_stance_by_prefecture_year.py` | stances + metadata + district | `data/processed/sou_kokkai_aggregates_2014_2024.csv` | ~5 s |

`lookup_speaker_district.py` queries the Japanese Wikipedia API for each unique speaker and extracts their 選挙区 (electoral district) from the infobox. Handles:
- `| 選挙区 =` (current role) and `| 選挙区N =` (numbered older roles)
- HOC proportional representation → `prefecture=全国, block=比例区`
- HOC prefectural → `prefecture=<県>, block=""`

Cache stored at `data/processed/.speaker_district_cache.json` — re-runs reuse successful lookups. Supports `--retry-errors` (re-query only the 429'd entries, preserve successful ones) and `--delay` (polite throttling).

`detect_switchers.py` re-queries Wikipedia for the 628 ok-status speakers to count `| 選挙区N =` entries in their infobox. Politicians with ≥2 entries are flagged `is_switcher=True` — they switched districts across their career, so the "current district" used in lookup_speaker_district may misattribute some of their earlier speeches.

`aggregate_stance_by_prefecture_year.py` produces the final aggregation table:

| year | prefecture | house | n_speeches | pct_pro | pct_anti | pct_neutral | stance_score_mean | pct_switcher_speeches |
|---|---|---|---|---|---|---|---|---|
| 2014 | 北海道 | 衆議院 | 8 | 12.5 | 62.5 | 25.0 | -0.500 | 12.5 |
| 2014 | 北海道 | 参議院 | 4 | 0.0 | 50.0 | 50.0 | -0.500 | 0.0 |
| ... | | | | | | | | |

One row per (year, prefecture, house) cell, filtered to 2014-2024. `全国` (HOC PR) speakers are kept as their own row. `pct_switcher_speeches` flags the data-quality concern for cells with many district-switching politicians.

---

## Configuration

**API keys** — stored in `sou/.env` as `GOOGLE_API_KEY_1` through `GOOGLE_API_KEY_10`. Loaded at runtime by `classify_stance_gemma.py`. Never commit `.env`.

**Rate limit budgets** (Google AI Studio free tier):
- `gemini-2.5-flash`: 15 RPM per key, 250K TPM, 50 RPD
- `gemini-2.5-flash-lite`: 10 RPM per key, 250K TPM, 20 RPD
- `gemini-3.1-flash-lite`: 15 RPM per key, 250K TPM, 500 RPD (best for retry pass)

**Checkpointing**:
- `classify_stance_gemma.py` saves every 100 windows; safe to kill + restart
- `lookup_speaker_district.py` writes cache on every speaker; --retry-errors preserves successful lookups

---

## Common gotchas

1. **Don't run `merge_stance_shards.py` (v1)** — it loses data via last-writer-wins. Always use v2.
2. **`--overwrite` on lookup_speaker_district.py re-queries successful entries too** — use `--retry-errors` to only re-query the 429'd ones.
3. **Sharding is by speechID hash, not by flat index** — changing `--num-shards` invalidates all shard files. If you re-shard, delete the old `kokkai_stances_shard_*_of_NN.json` files first.
4. **API key exhaustion is silent** — the script retries with backoff but won't tell you which key is dead. Watch the log for repeated `429` from the same key index.
5. **`preprocess_kokkai.py` requires the full text** — if Phase 2 isn't done, you can't run Phase 3. Use `metadata.json` directly for metadata-only analysis.
