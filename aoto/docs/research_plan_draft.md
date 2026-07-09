# Research Plan — Initial Draft

> **Initial draft by Aoto (@uooooo) — 2026-05-13.**
> This is a *proposal to discuss*, not a final plan. Please edit, push back, or rewrite freely. The goal is to converge in 1–2 group meetings.

## 1. Research Question

> **Does immigration inflow to Japanese prefectures affect electoral outcomes and voter attitudes toward immigration policy?**

Sub-questions:

1. **Q1 (descriptive)**: Are prefectures with higher foreign-resident growth correlated with higher / lower vote share for parties that take a restrictive stance on immigration?
2. **Q2 (causal)**: Is there a causal effect of foreign inflow on the vote share of "restrictive" parties (in particular Sanseitō / 参政党 in 2025/2026)? — using shift-share or refugee-dispersal style IV.
3. **Q3 (mechanism)**: Through which channel? labor-market competition / public-service congestion / cultural/identity politics? — heterogeneity by skill mix of incoming foreigners.
4. **Q4 (discourse)**: Do Diet speeches by representatives from high-foreign-share prefectures shift toward (or away from) restrictive framing? — text analysis of 国会会議録.

## 2. Hypotheses

- **H1 (baseline)**: Prefectures with higher foreign-resident share or higher inflow rate experience higher vote share for parties with restrictive immigration platforms (LDP-right faction, Sanseitō).
- **H2 (heterogeneity by labor dependence)** *(README 案)*: H1 is **weaker or reversed** in prefectures with higher dependence on foreign labor (e.g., agriculture/manufacturing heavy prefectures where the economic-necessity narrative dominates).
- **H3 (skill mix)**: H1 is driven by **low-skill** inflow (技能実習・特定技能), not by **high-skill** inflow (技術・人文知識・国際業務、高度専門職). Following Mayda, Peri & Steingress (2022).
- **H4 (urban vs rural)**: Effect is concentrated in non-metropolitan prefectures (Dustmann et al. 2019).
- **H5 (issue salience shift)**: The effect strengthens after 2025/7 参院選, when immigration became politically salient (Rehm 2026).

## 3. Empirical Design

### Unit of analysis
- **Primary**: prefecture × election year panel (47 都道府県 × 衆参両院, 2012–2026)
- **Outcome**: 比例代表の党派別得票率 (Sanseitō, LDP, 立憲, 国民, etc.)
- **Treatment**: 在留外国人比率 (foreign residents / total population), or year-over-year inflow rate
- **Skill split** (for H3): 低技能 = 技能実習 + 特定技能、高技能 = 技術・人文知識・国際業務 + 高度専門職、永住 = 永住者

### Identification strategy
1. **Phase 1 (descriptive)**: Cross-section + panel fixed effects (prefecture FE + year FE). Establish stylized facts before causal claims.
2. **Phase 2 (causal, if data allows)**: Shift-share IV à la Card (1990) / Halla et al. (2017):
   ```
   Z_{p,t} = sum over origins o of (foreign_residents_{p,o,t0} / foreign_residents_{p,t0}) * national_inflow_{o,t}
   ```
   Historical settlement pattern (t0 = e.g., 2010) times national inflow by origin — gives an exogenous shifter for prefecture-level inflow.
3. **Text analysis (Q4)**: 国会会議録 API で「移民/外国人/在留資格」関連発言を抽出 → 議員別 / 政党別 / prefecture × year で集計 → Wordfish or BERT embedding でスケーリング → 在留外国人比率との相関を見る。

### Key control variables
- Unemployment rate / 有効求人倍率 (prefecture × year)
- Aging rate (65歳以上比率)
- GDP per capita (県民経済計算)
- 外国人労働者依存度 (厚労省「外国人雇用状況」)
- Crime rate (要検証)

## 4. Data — Phase 1 (まず取るべきもの)

詳細は `data_sources.md` 参照。

| 優先 | データ | 入手先 | 担当 |
|---|---|---|---|
| 1 | 在留外国人統計 (都道府県 × 在留資格 × 国籍、半期、2012–2025) | e-Stat API `statsDataId=0003147704` + `0004019020` | TBD |
| 2 | 総務省 衆・参院選結果 (2012–2026 で過去分を補完) | soumu.go.jp 各回 | TBD (4 ファイルは既取得) |
| 3 | 有効求人倍率 (都道府県 × 月) | e-Stat `toukei=00450222` | TBD |
| 4 | 外国人雇用状況届出 (2007–) | 厚労省 報道発表 各年 | TBD |
| 5 | 国会会議録 API サンプル fetch | kokkai.ndl.go.jp/api/speech | TBD |

**重要な発見** (data/raw/ プロファイル結果): 既存の `February 2026 Foreigners Entering/Leaving Japan.xlsx` は **国籍 × 在留資格** の月次フローで **都道府県別ではない**。Phase 1 の treatment 変数は **e-Stat の在留外国人統計を別途取得** する必要がある。

## 5. Closest precedent & how we differentiate

- **Maeda & Strausz (2025)** *Journal of East Asian Studies* が最も近い。彼らは **議員のサーベイ態度** を outcome にしている。
- 本プロジェクトは **有権者の得票** を outcome にして差別化。
- 加えて 2025/7 参院選 + 2026/2 衆院選という、**移民が初めて争点化したショック** を pre/post で扱える点が新しい (Rehm 2026 は記述的)。

詳細は `literature_review.md` 参照。

## 6. Folder & Workflow (README の規約に従う)

```
data/raw/         ← 既存 + 上記 1〜2 を追加
data/clean/       ← 都道府県 × 年 panel を生成
notebooks/        ← 01_eda, 02_panel_construction, 03_baseline_regression, 04_iv, 05_text_analysis
src/              ← fetch_estat.py, fetch_kokkai.py, build_panel.py
reports/figures/  ← 図表
docs/             ← この research_plan_draft.md, literature_review.md, data_sources.md
```

## 7. Timeline (たたき台、適宜更新)

| Milestone | 想定 deadline | Deliverable |
|---|---|---|
| M1 | 2026-06-? | RQ・hypothesis 確定、Phase 1 データ取得完了、EDA notebook 1 本 |
| M2 | 2026-07-? | Baseline 回帰結果 (panel FE)、中間レポート |
| M3 | 2026-08-? | IV or text analysis、最終 presentation |

(M1–M3 の具体日付は授業スケジュール (HW / final presentation 締切) と合わせて埋める)

## 8. Open questions (グループで議論したい)

1. **Outcome の選択**: Sanseitō 単独得票率 / LDP+Sanseitō 合計 / 「restrictive index」スコア — どれを主 outcome にする?
2. **時間軸**: 2012–2026 全期間 / 2020–2026 だけ / 2025 参院選を断面で集中分析? — 因果か記述か次第
3. **IV を諦めて descriptive + DID にする**: 2025 参院選を「ショック」として、参政党台頭前後で foreign-share の高低別に DID 的に比較する手もある
4. **テキスト分析を入れるか**: 入れると一本でやる量が増える。Q4 を分離して別 deliverable にする手もある
5. **役割分担**: データパイプライン / EDA / 統計分析 / テキスト分析 / 政策メモ・スライドの 5 分担で揃えるか
6. **個人ディレクトリ**: 各メンバーが `notebooks/` 配下に個人 dir (`notebooks/aoto/`, `notebooks/christie/` 等) を切るか、共通ファイル名で番号付きにするか

## 9. 次にやること (Aoto 私案)

- [ ] e-Stat appId 取得
- [ ] 在留外国人統計を都道府県 × 在留資格 × 年で取得する fetch script (`src/fetch_estat.py`)
- [ ] 既存 4 ファイル + e-Stat 在留外国人統計を JOIN して panel.parquet を生成
- [ ] 国会会議録 API の「移民」発言 sample fetch (動作確認)
