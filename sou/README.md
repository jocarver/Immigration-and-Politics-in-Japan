# sou/ — Kokkai NDL Speech Data Pipeline

sou's fork for the cross-team research project on Japanese immigration politics. Collects, classifies, and aggregates National Diet (国会会議録) speeches on immigration/foreign workers.

## Pipeline status — all phases complete

| Phase | Output | Status |
|---|---|---|
| 1. Metadata fetch | 10,961 speeches | ✓ |
| 2. Full-text fetch | 351 MB corpus | ✓ |
| 2.5. Window extraction (±1 sentence) | 20,741 windows | ✓ |
| 3. LLM stance classification | pro/anti/neutral per window | ✓ |
| 4. Speaker → prefecture + aggregate | 525 (year, prefecture, house) cells | ✓ |

For per-script reference: see [`src/README.md`](src/README.md).

## Data summary

- **Period**: 2012-01-30 → 2024-12-19
- **Keywords**: 9 (技能実習, 外国人労働者, 出入国管理, 特定技能, 外国人材, 不法滞在, 多文化共生, 移民政策, 外国人犯罪)
- **Speeches**: 10,961 → 7,796 party-attributed + 3,158 no-party (3,158 committee chairs / expert witnesses kept as "no-party" — they have analytical value)
- **Stance labels (1,894 anti / 1,497 pro / 6,905 neutral)**: 1,901 → 1,894 after normalize_prefecture (anti); distribution: 65% neutral / 21% anti / 14% pro
- **Speaker districts**: 803 unique speakers → 628 with Wikipedia prefecture → 568 after junk-string normalization (5 unparseable dropped)
- **Aggregate**: 7,126 speeches joined, 525 (year × prefecture × house) cells, 2014-2024

### Yearly distribution

| 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|  52 | 112 | 589 | 347 |1470 | 485 |2573 |1699 | 494 | 396 | 470 | 707 |1560 |

## LLM classification prompt

`src/classify_stance_gemma.py` sends each ~500-char window through this prompt (Gemini 3.1 Flash Lite via Google AI Studio, deterministic JSON, no markdown):

```
You are a deterministic, single-word classification API. Do not deliberate. Do not analyze historical context. Instantly output JSON based on immediate keyword matching. Think in less than 50 words.

Task: Classify this Japanese Diet speech on immigration policy into pro / neutral / anti.

- pro: supports expansion / positive evaluation
- neutral: factual report, procedural remark, or unclear stance
- anti: supports reduction / strictness / criticism / concerns

Output ONLY one line (no explanation, no reasoning, no markdown):
{"stance": "pro"} OR {"stance": "neutral"} OR {"stance": "anti"}

Passage:
{text}
```

Final label is the **modal vote** across N classifications per window (see `src/merge_stance_shards_v2.py` — the v1 merger has a last-writer-wins bug; don't use it).

## Project structure

```
sou/
├── README.md              # this file
├── CLAUDE.md              # project memory: data pipeline principle, Joe's schema (read-only)
├── pyproject.toml
├── src/                   # 11 active scripts (1 archived in src/archive/) — see src/README.md
├── data/
│   ├── raw/kokkai/
│   │   ├── metadata.json           # 7 MB, committed
│   │   └── speech_texts.json       # 351 MB, gitignored
│   ├── clean/                      # analysis CSVs (kokkai_party_counts, kokkai_year_party, etc.)
│   ├── logs/                       # pipeline run logs (gitignored)
│   └── processed/
│       ├── kokkai_windows.json
│       ├── kokkai_stances_clean.json
│       ├── speaker_district_switcher.csv
│       └── sou_kokkai_aggregates_2014_2024.csv   # ← Joe's input
├── notebooks/
│   ├── 01_metadata_analysis.ipynb
│   ├── 02_stance_analysis.ipynb
│   ├── 03_speaker_concentration.ipynb
│   └── figures/                    # analysis output PNGs (all figures live here, not in data/raw/)
└── slides/                         # deliverable deck (gitignored) — see slides/gen.js
```

## Setup

```bash
cd sou
uv sync
# see src/README.md for the full pipeline commands
```

## Cross-team deliverables

- `sou/data/processed/sou_kokkai_aggregates_2014_2024.csv` — ready to join on `prefecture` against Joe's election/immigration data
- Joe's data schema documented in `CLAUDE.md` (read-only reference for the merge design)
- Per-prefecture stance is uniform (Pearson r = -0.05 vs foreign resident ratio, n.s.) — not a strong signal, but per-prefecture anti-immigration speech is heavily concentrated in 1-2 local Diet members (notebook 03)

## Caveats

Junk strings from the Wikipedia infobox parser (e.g. `| 当選回数 =`, `千葉1区`) are normalized in `aggregate_stance_by_prefecture_year.py`; 8 unparseable are dropped. 216 of 628 (34.4%) politicians are "switchers" (≥2 districts in career) — the `pct_switcher_speeches` column flags high-risk cells. `全国` (HoC PR) is kept in the aggregate but typically excluded from per-prefecture analysis.
