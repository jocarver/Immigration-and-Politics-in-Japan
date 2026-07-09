# aoto/

Personal namespace for **Aoto Sato (@uooooo)**.

Everything in here is **my draft / proposal / experiment**, not group-approved output.
Feel free to read, comment in PRs, or open issues — but please don't edit my files in place without a heads-up.

Other members are welcome to mirror this pattern (e.g. `christie/`, `joseph/`, `kannch/`) for their own drafts.

Once we agree on something as a team, the final version moves out of here and into the repo-root folders (`notebooks/`, `src/`, `data/`, `reports/`, `docs/`) per the README structure.

## Structure

```
aoto/
├── README.md
├── pyproject.toml + uv.lock         ← uv project (Python deps)
├── .env                             ← e-Stat appId (gitignored)
├── docs/                            ← drafts, memos
│   ├── literature_review.md         ← initial survey (PR #3)
│   ├── data_sources.md              ← Japanese data-source inventory (PR #3)
│   ├── research_plan_draft.md       ← RQ / hypotheses / design draft (PR #3)
│   ├── party_positions_2025.md      ← 2025 参院選 各党スタンス
│   ├── news_coverage_2025_immigration.md  ← 報道調査
│   ├── ml_methods_review.md         ← Causal Forest / SDID / DML 等
│   ├── literature_non_japan.md      ← Germany / Sweden / UK / US 等
│   └── data_collection_log.md       ← running log
├── src/                             ← reusable fetch / clean scripts
│   ├── fetch_kokkai.py              ← 国会会議録 API
│   ├── fetch_estat_files.py         ← e-Stat 在留外国人統計 (HTML scraping)
│   ├── fetch_soumu_elections.py     ← 総務省選挙データ
│   ├── clean_elections.py           ← 10 election Excel → long panel
│   ├── clean_foreign_residents.py   ← 14 t1 Excel → long panel
│   ├── build_panel.py               ← joined panel (election × treatment)
│   └── quick_describe.py            ← first-look correlations
├── data/                            ← outputs of src/
│   └── clean/
│       ├── elections_panel.{parquet,csv}
│       ├── foreign_residents_panel.{parquet,csv}
│       ├── joined_panel.{parquet,csv}
│       ├── joined_panel_pref_election.{parquet,csv}
│       ├── kokkai_count_by_year_party.csv
│       ├── kokkai_top_speakers.csv
│       └── quick_describe.md
└── notebooks/                       ← personal EDA
```

Raw data fetched from external sources lives in repo-root `data/raw/` (project-wide convention from the main README). Large files (`*.json` for kokkai; `*.xlsx` for foreign_residents) are gitignored and reproducible via `aoto/src/fetch_*.py`.

## How to run

```bash
# from repo root, with uv (Python deps are pinned in aoto/uv.lock)
uv run --project aoto python aoto/src/clean_elections.py
uv run --project aoto python aoto/src/clean_foreign_residents.py
uv run --project aoto python aoto/src/build_panel.py
uv run --project aoto python aoto/src/quick_describe.py
```
