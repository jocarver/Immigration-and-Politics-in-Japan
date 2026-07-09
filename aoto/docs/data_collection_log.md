# Data collection log

> By Aoto (@uooooo). Updated as work progresses on branch `feat/aoto-data-collection`.

## ✅ Done so far (2026-05-13)

### Election panel — 10 elections, 2013–2026
- Source: `data/raw/election_results/` の 10 Excel ファイル
  - 衆院 5 回: 2014/2017/2021/2024/2026
  - 参院 5 回: 2013/2016/2019/2022/2025
- Output: `aoto/data/clean/elections_panel.{parquet,csv}` (**2303 rows**: prefecture × party × election)
- Script: `aoto/src/clean_elections.py`
- **Limitation**: 各 Excel が含む政党数:
  - 衆院 (2014-2024): 6 党 (LDP, 立憲/民主/民進, 公明, 維新, 共産, 国民)
  - 衆院 (2026): 5 党 (LDP, 維新, 共産, 国民, **参政**) ← 立憲・公明欠
  - 参院 (2013-2025): 4 党のみ (主要 4 党のみ、年により党名変動)
  - Sanseitō (参政党) は 2026 衆院ファイルにしか出てこない。Sangiin での参政・共産・国民・社民・れいわ など minor party の得票は別 Excel が必要 (総務省ページに「(5)」「(6)」「(7)」と分割されている)。

### Diet-speech corpus (国会会議録 API)
- Source: https://kokkai.ndl.go.jp/api/speech (認証不要)
- Keywords: 移民 / 外国人 / 在留外国人 / 在留資格 / 特定技能 / 技能実習 / 外国人労働者 / 永住者
- Period: 2015-01-01 ~ 2026-04-30 (~ 11 年)
- Output:
  - `data/raw/kokkai/speeches_*.json` × 8 (合計 ~60 MB、**gitignore 済み**、`fetch_kokkai.py` で再現可能)
  - `aoto/data/clean/kokkai_speeches_all.csv` (34 MB、**gitignore**)
  - `aoto/data/clean/kokkai_count_by_year_party.csv` (200 行、commit 済み)
  - `aoto/data/clean/kokkai_top_speakers.csv` (Top 30 議員、commit 済み)
- **取得実績**: 重複除去後 **13,563 unique speeches**
  - 年別 top 3: 2024 (3074) > 2018 (2458) > 2025 (1973)
  - キーワード別 hit 数: 外国人 19,251 (5000 でキャップ) / 技能実習 5,931 (キャップ) / 在留資格 2,938 / 特定技能 2,307 / 外国人労働者 1,779 / 移民 955 / 永住者 565 / 在留外国人 505
  - 政党別 top 5: 「不明」(政府参考人/官僚) 3,738 / 自民・無所属の会 1,706 / 自民 1,529 / 公明 797 / 共産 726
- **落とし穴**: 「不明」27.6% は官僚・委員長による発言で、政党分析からは除外する必要。「外国人」キーワードは観光・研究者文脈も拾うので、text analysis 段階で文脈フィルタが要る。
- Script: `aoto/src/fetch_kokkai.py`

### Party-position summary for 2025 参院選
- Source: 移住連 (migrants.jp) 8-question survey + 難民支援協会 (refugee.or.jp) policy comparison
- Output: `aoto/docs/party_positions_2025.md`
- 暫定 "restrictive index" 分類 (参政=+2 ... 共産/社民/れいわ=−2) を含む。**チーム議論ネタ**。

### 報道調査 — 2025 参院選 移民論点化
- Output: `aoto/docs/news_coverage_2025_immigration.md`
- 12 報道 (時事、日経、NRI、NHK 系、CSIS、Reuters、Edelman 等) + 学術 2 件 (Schäfer 2025 APJJF, Rehm 2026)
- 主因の解釈: 「参政党躍進 (YouTube 動員) + LDP スキャンダル → 政治空間の発生 → 与党は反論せず右翼言説を模倣 → 議題設定の主導権喪失」(Rehm 2026 系)
- ファクトチェック付き: 参政党の「外国人犯罪増加」「生活保護優遇」言説はいずれも事実否定 (FactCheck Navi)

### 取得 script の整備
- `aoto/src/clean_elections.py` — election Excel パーサ
- `aoto/src/fetch_kokkai.py` — 国会会議録 fetcher
- `aoto/src/fetch_soumu_elections.py` — 総務省選挙ファイル fetcher (binary scan で section 番号を当てるロジック付き)
- `aoto/src/fetch_estat_files.py` — e-Stat 直接 DL の試作 (file listing scraping 段階で停止、API 版に切替予定)
- `data/raw/election_results/README.md` — 取得元と各ファイルの解説
- `data/raw/kokkai/README.md` — 同上 (kokkai)

## 🟡 In progress / blocked

| Task | Status | Notes |
|---|---|---|
| 在留外国人統計 Excel 直接 DL | **stuck** | agent 2 が e-Stat ファイル一覧ページから直接 Excel を取れず。動的レンダリング / 構造化の問題か。**API ルート (appId 必要) に切替**予定 |
| 在留外国人統計 e-Stat API | **awaiting user** | ユーザーがアプリ ID 登録 (5–15 min) → 提供されたら `fetch_estat.py` を仕上げて実走 |
| sangiin の minor party (参政・共産・国民・社民・れいわ) 得票 | open | 総務省の同じ選挙ページ内に別 Excel (file 番号違い) があるはず。要追加 fetch |

## 🚧 Known blockers / things to escalate to user

- **e-Stat API は appId 必須**。即時発行、メアドだけ、無料、研究目的 OK ([登録 URL](https://www.e-stat.go.jp/mypage/user/preregister/))。**user 登録待ち**。
- **JGSS 個票** は ICPSR/SSJDA 申請が必要 → 人間タスク (中期に検討)
- **paywall 報道** (朝日, 日経の本文) → headline + URL のみ収集済み
- **参政党 公式 policy URL** は 2026-05-13 時点で 404 → 難民支援協会・移住連の二次資料で代替済み

## 🚧 Known blockers / things to escalate to user

- **e-Stat API (statsDataId access)** requires `appId` (free registration) → if direct Excel DL via the file-listing pages fails, the user will need to register at https://www.e-stat.go.jp/api/api-info/api-guide and provide an appId.
- **JGSS individual-record data** requires application via ICPSR or SSJDA → a human (Aoto) must submit an application, can't be automated.
- **Some media outlets are paywalled** (朝日, 日経) → only headlines + URL will be captured; full text needs human access via institutional subscription if used as evidence.
- **参政党 公式 policy page** (https://sanseito.jp/sanin_election_27_policy/) **returned 404** as of 2026-05-13. Need to find an archived snapshot or use 難民支援協会's summary as a secondary source.

## 📋 Next planned steps

1. **e-Stat appId 取得 (user)** → `fetch_estat.py` で `statsDataId=0003147704` を叩いて都道府県 × 在留資格 × 年の treatment DataFrame を作る
2. **Sangiin の minor party 補完**: 総務省 sangiin の `(6)` `(7)` 等 別 Excel を追加 fetch して、参政・共産・国民・社民の sangiin 得票を panel に統合
3. **EDA notebook 1 本**: 既存 panel (2303 行) を使って (a) 党別得票率の時系列推移、(b) 都道府県別 LDP/参政 得票率分布、(c) 参政党 (2026 衆院) の県別得票と外国人比率の散布図 — treatment 取得後
4. **データ取得 PR**: 上記まで揃ったら `feat/aoto-data-collection` → main に PR を投げてレビュー
