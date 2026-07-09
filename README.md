# Skilled-Immigration

## 👥 Team Members

- Joseph Carver (@jocarver) - Role/Responsibility
- Cao Han (@kannch8765) - Role/Responsibility
- Aoto Sato (@uooooo) - Role/Responsibility

*(Add more members as needed)*

## Youtube Video Link
- Part I: https://youtu.be/W7n_9-Hr77w
- Part II: https://youtu.be/18PJf5sQ1_8

## ❓ Research Question & 🎯 Hypothesis

> State your central research question clearly and concisely

### Potential Research Questions:
- Do immigration rates in different prefectures in Japan correlate with electoral support for stricter immigration policies?
  
#### Data sources:
- https://www.soumu.go.jp/senkyo/senkyo_s/data/ (voting/election data)
- e-Stat portal for immigration statistics
- https://kokkai.ndl.go.jp/api.html (database of parliamentary records (speeches, debates, etc I think))
- Immigration Services Agency: https://www.moj.go.jp/isa/policies/statistics/?hl=en
- Speech Data:
  - 東京都議会 https://www.gikai.metro.tokyo.lg.jp/
  - 国会会議録検索システム https://kokkai.ndl.go.jp/
  - 大阪府議会　会議録検索システム https://ssp.kaigiroku.net/tenant/prefosaka/pg/index.html

#### References:
- https://academic.oup.com/ssjj/article/29/1/jyag001/8507400?login=true (text analysis to extract ideological slant from Japanese Diet speeches)
- https://www.cambridge.org/core/journals/asia-pacific-journal/article/have-japanese-voters-begun-to-care-about-migration/D694F5B18D388A600116405A65F0CE73 (opinion style article on immigration politics in Japan)
- survey data on attitudes towards immigration: https://aparc.fsi.stanford.edu/news/japanese-public-sets-high-bar-immigrants
- LDP candidate positions on immigration over time: https://www.cambridge.org/core/journals/journal-of-east-asian-studies/article/conservative-politics-and-the-dilemma-of-immigration-in-japan/B9EDC7422AF7C44B068318690A52755C

- Hypothesis 1 (possible hypo) The positive relationship between immigration and support for stricter policies is weaker (or reversed) in prefectures with higher dependence on foreign labor.
- Hypothesis 2
- Hypothesis 3

## 📁 Data Sources

| Source | Description | URL |
|--------|-------------|-----|
|  | | |
|  |  | |

### Data Sources Details

#### D.1 World Bank  
**Variables:** e.g., NY.GDP.MKTP.CD, SE.PRM.CMPT.ZS

**Granularity:** e.g., Annual data by Country

#### D.2 IMF  
**Variables:** e.g., Consumer Price Index, Interest Rates

**Granularity:** e.g., Quarterly data by Region

## 📂 Folder Structure

### Folder Structure Notes
- All projects MUST follow this standardized folder structure
- `data/raw/` - **NEVER** edit manually; store original data here
- `data/clean/` - Cleaned datasets ready for analysis
- `data/temp/` - Temporary files (can be deleted)
- `notebooks/` - Jupyter notebooks for analysis
- `src/` - Python code
- `reports/` - Final outputs: plots, summaries, model files
- `docs/` - Project documentation, README, presentations

### Folder Structure Tree

```tree
project/
├── data/
│   ├── raw/                   # Original, immutable data
│   │   ├── world_bank_raw.csv
│   │   └── imf_financials_raw.csv
│   ├── clean/                 # Cleaned, transformed data
│   │   ├── world_bank_clean.csv
│   │   └── imf_merged_clean.csv
│   └── temp/                  # Temporary working files
├── notebooks/                 # Jupyter notebooks for exploration
│   ├── 01_eda_worldbank.ipynb
│   ├── 02_regression_analysis.ipynb
│   └── 03_policy_simulations.ipynb
├── src/                       # Production-ready scripts
│   ├── download_worldbank.py  # API/Scraping script
│   ├── clean_data.py          # Merging and cleaning logic
│   └── visualize_worldbank.py # Chart generation functions
├── reports/                   # Final outputs
│   ├── figures/               # Saved .png plots for the memo
│   │   ├── gdp_trend_line.png
│   │   └── debt_distribution.png
│   ├── policy_memo_final.pdf
│   └── regression_results.txt
└── docs/                      # Documentation
    ├── data_details.md        # Data dictionary & column definitions
    ├── data_architecture.md   # Pipeline logic and join keys
    ├── policy_context.md      # Political background & stakeholders
```

## 📅 Timeline

| Milestone | Deadline | Deliverable |
|-----------|----------|-------------|
| M1        | Date     | Output      |
| M2        | Date     | Output      |
| M3        | Date     | Output      |

## 🤝 Contributions

| Member | Tasks |
|--------|-------|
| Name   | Description of contributions |
| Name   | Description of contributions |

## 🔗 References
- Link to methodology references
