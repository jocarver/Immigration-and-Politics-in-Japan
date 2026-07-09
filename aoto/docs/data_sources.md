# 日本の移民×選挙研究用データソース総覧

> **Initial draft by Aoto (@uooooo) — 2026-05-13.**
> Please edit, add sources, or correct URLs. All entries should be validated when actually used.

**分析単位**: 都道府県 × 選挙年 (パネル / クロスセクション)

> ⚠️ URL は Web 確認ベース。e-Stat API 利用前には appId 取得 + 最新の `statsDataId` を再確認すること。

---

## 1. 外国人・移民データ (prefecture 別、年次)

### 1-1. 在留外国人統計 (e-Stat 経由、出入国在留管理庁)

| データ名 | URL | 取得方法 | 単位 | 期間 | 注意点 |
|---|---|---|---|---|---|
| 在留外国人統計 (ファイル一覧) | https://www.e-stat.go.jp/stat-search/files?toukei=00250012&tstat=000001018034 | CSV/Excel DL or API | 都道府県 × 在留資格 × 国籍、半期 | 2012/12 〜 2025/6 (年 2 回) | appId 要登録 (無料) |
| 在留外国人 DB (2012-2017) | https://www.e-stat.go.jp/stat-search/database?toukei=00250012&layout=dataset&statdisp_id=0003147704 | e-Stat API `statsDataId=0003147704` | 都道府県 × 在留資格 × 国籍 6 区分 | 2012/12 〜 2017/6 | 国籍は総数・中国・台湾・韓国・フィリピン・ブラジルのみ |
| 在留外国人 DB (2024/12) | https://www.e-stat.go.jp/dbview?sid=0004019020 | e-Stat API `statsDataId=0004019020` | 都道府県 × 在留資格 × 国籍 × 年齢 × 性別 | 2024/12 単年 | 5 軸クロスが可能 (リッチ) |
| テーブルデータ (市区町村まで) | https://www.e-stat.go.jp/stat-search/files?stat_infid=000040186957 | Excel DL | 国籍 × 在留資格 × 市区町村 | 2023/12 末 | 市区町村コード付き |

**説明**

半期データ (6/末・12/末)。2012 以降は e-Stat 経由で都道府県 × 在留資格 × 国籍が取れる。12 月末データを「その年の代表値」とするのが標準。

**主な落とし穴**:
- 2012 以前 (旧登録外国人制度) と接合不可
- 「技能実習」は 2022 法改正で「育成就労」へ順次移行
- 「技術・人文知識・国際業務」は 2015 に旧「技術」+「人文知識・国際業務」を統合

**e-Stat API サンプル**:
```
GET https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData
  ?appId=YOUR_APP_ID
  &statsDataId=0003147704
  &cdCat01=ALL          # 在留資格
  &cdArea=ALL           # 都道府県
  &limit=100000
```

### 1-2. 国勢調査 国籍別人口 (e-Stat / 総務省)

| データ名 | URL | 単位 | 期間 |
|---|---|---|---|
| R2 国勢調査 44-1 国籍別人口 | https://www.e-stat.go.jp/stat-search/database?statdisp_id=0003445244 | 都道府県・市区町村 × 国籍 14 区分 × 男女 | 2020/10 |
| H27 国勢調査 国籍 12 区分 | https://www.e-stat.go.jp/stat-search/database?statdisp_id=0003148596 | 都道府県・市区町村 | 2015 |

5 年に 1 回のスナップショット。フローを捉えるには不向きだが、教育・就業との同時捕捉ができるので control variable として有用。

### 1-3. 外国人雇用状況届出 (厚労省)

| データ名 | URL | 単位 | 期間 |
|---|---|---|---|
| 外国人雇用状況まとめ (2024/10 末) | https://www.mhlw.go.jp/stf/newpage_50256.html | 都道府県別 | 2007 〜 毎年 10 月末 |

雇用主の届出義務に基づく全数調査。「外国人労働者依存度」(外国人労働者数 / 総雇用者数) を control 変数として作るのに最適。各年の報道発表ページからスクレイピング必要。

---

## 2. 選挙結果データ (prefecture × 党派 × 年)

### 2-1. 総務省 選挙関連資料

| 選挙 | URL | 形式 |
|---|---|---|
| 第 50 回衆院選 (2024/10) | https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin50/index.html | Excel (.xlsx) |
| 第 27 回参院選 (2025/7) | https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin27/index.html | Excel (.xlsx) |
| 第 26 回参院選 (2022/7) | https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin26/index.html | Excel (.xls) |

衆院: 小選挙区は市区町村単位、比例は 11 ブロック。prefecture-level に揃えるには小選挙区を都道府県コードで集計する必要あり。参院は選挙区が都道府県なので素直。

**注意点**:
- 2016 参院選から「合区」(鳥取+島根、徳島+高知)
- 2022 衆院選から「10 増 10 減」で小選挙区の区割り変更
- e-Stat 経由の衆院選データは **PDF のみ**。生データは総務省ページから取得すること

**既存ファイル (data/raw/election_results/)**:
- 2022/7 参院選 (.xls) — 都道府県別比例得票
- 2024/10 衆院選 (.xls) — 比例代表選挙区別都道府県別党派別得票
- 2025/7 参院選 (.xlsx) — 都道府県別比例得票
- 2026/2 衆院選 (.xlsx) — 比例代表選挙区別都道府県別党派別得票

### 2-2. 研究者公開データセット

| データ名 | URL | 期間 | 用途 |
|---|---|---|---|
| Reed-Smith JHRED | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/QFEPXD | 1947–2014 衆院選 | 長期パネル基礎 |
| 矢内浩朗 2024 衆院選 CSV | https://yukiyanai.github.io/jp/resources/data/hr2024election.html | 2024 | クリーンな CSV |
| 日本地方選挙 (JLED) | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TLC5R4 | 1985–2017 都道府県議会選 | 拡張用 |

### 2-3. 2025/7 参院選・2026/2 衆院選の特殊性

- **2025/7 参院選**: 参政党が「外国人総合政策庁の新設」「生活保護支給停止」等を公約。14 議席獲得 (比例 12.6%) で第 4 野党に。LDP も「外国人にはルールを守らせる」と同調的発言。**移民が初めて主要争点になった選挙**。
- **2026/2 衆院選**: 上記の流れを引き継ぐ。`data/raw/` に既に取得済み。

---

## 3. テキストデータ (政治家発言・政策文書)

### 3-1. 国会会議録 API (国立国会図書館)

| エンドポイント | 用途 |
|---|---|
| `GET https://kokkai.ndl.go.jp/api/speech` | 発言単位 (1 リクエスト最大 100 件) |
| `GET https://kokkai.ndl.go.jp/api/meeting` | 会議全文 (1 リクエスト最大 10 件) |

**主要パラメータ**: `any` (検索語), `nameOfHouse` (衆議院/参議院), `from`/`until` (YYYY-MM-DD), `speaker` (議員名), `sessionFrom`/`sessionTo` (国会回次), `recordPacking=json`. 認証不要、レート制限は明文化されていないが連続リクエスト時は数秒空ける。

**サンプル**:
```
GET https://kokkai.ndl.go.jp/api/speech
  ?any=移民 外国人受け入れ
  &nameOfHouse=衆議院
  &from=2020-01-01&until=2025-07-31
  &maximumRecords=100
  &recordPacking=json
```

### 3-2. 政党マニフェスト・政策文書

| データ名 | URL |
|---|---|
| 参政党 2025 参院選公約 | https://sanseito.jp/sanin_election_27_policy/ |
| 難民支援協会 各党公約比較 (2025) | https://www.refugee.or.jp/report/refugee/2025/07/manifest2507/ |
| 移住連 政党アンケート (2025) | https://migrants.jp/news/voice/2025_party_survey.html |
| 移住連 政党アンケート (2022) | https://migrants.jp/news/voice/20220710.html |

### 3-3. 都道府県議会議事録 (要検証)

東京・大阪・愛知・神奈川・埼玉・福岡・北海道 など主要都府県は独自の議事録検索を持つが API は標準化されていない。**第一フェーズでは国会会議録 API で代替推奨**。都道府県議会まで広げるのは Phase 3 以降。

---

## 4. 世論調査・態度データ

### 4-1. JGSS (日本版総合的社会調査)

| 名前 | URL | アクセス |
|---|---|---|
| JGSS-2017/2018G | https://www.icpsr.umich.edu/web/ICPSR/studies/38162 | ICPSR 申請 (無料登録) |
| JGSS 累積 2000–2003 | https://csrda.iss.u-tokyo.ac.jp/english/socialresearch/joint/ | SSJDA 申請 |

EASS (東アジア社会調査) のグローバル化モジュール: 外国人労働者受け入れ態度・外国人知人の有無等を含む。都道府県別サンプルは小さいので multilevel 分析向き。

### 4-2. World Values Survey (WVS)

| 名前 | URL |
|---|---|
| WVS Wave 7 日本 (2017–2022) | https://www.worldvaluessurvey.org/WVSDocumentationWV7.jsp |

全国 ~1000 件。都道府県別不可。記述統計・外部バリデーション用。

### 4-3. 出入国在留管理庁「外国人との共生に関する意識調査」

URL: https://www.moj.go.jp/isa/support/coexistence/survey03.html — 都道府県別集計の有無は **未確認 (要検証)**。

### 4-4. Stanford Japan Barometer

https://www.japanbarometer.org/ — 8,000 人規模の多波パネル。コンジョイント実験。外国人労働者受け入れ反対が 2022–23 の 36% → 2026 に 53% 超 (+17%pt) と急増。

---

## 5. Control Variables

| データ | URL | 単位 |
|---|---|---|
| 有効求人倍率 | https://www.e-stat.go.jp/stat-search/files?layout=dataset&toukei=00450222&tstat=000001020327 | 都道府県 × 月 |
| 県民経済計算 | https://data.e-gov.go.jp/data/dataset/cao_20210602_0017 | 都道府県 × 年度 |
| 人口推計・高齢化率 | https://www.e-stat.go.jp/ | 都道府県 × 年次 × 年齢階層 |
| 警察庁犯罪統計 | https://www.npa.go.jp/publications/statistics/crime/index.html | 都道府県 × 年 (要確認) |

---

## 推奨データ取得ロードマップ

### Phase 1 (1〜2 週間): まずこれを取れ

1. **在留外国人統計** (e-Stat API `statsDataId=0003147704` + `0004019020`, 2012–2025)
2. **総務省 衆/参院選結果 Excel** (2012–2026) — 既取得 4 ファイル + 過去回を補完
3. **有効求人倍率** (e-Stat, 都道府県別)

### Phase 2 (2〜4 週間): panel を厚くする

4. **外国人雇用状況届出** (厚労省、2007〜)
5. **国勢調査 R2 国籍別人口** (e-Stat)

### Phase 3 (任意): 拡張

6. **JGSS-2017/2018G 個票** (ICPSR 申請)
7. **国会会議録 API** で「移民」「外国人」発言のテキスト分析

---

## JOIN キー設計

```
primary key: pref_code (JIS X 0401, 2 桁) × year

# 例: 都道府県名 → コード変換テーブル
pref_map = {"北海道": "01", "青森県": "02", ..., "沖縄県": "47"}
```

- e-Stat の `cdArea` (例: `"01000"`) → 上 2 桁で結合
- 総務省選挙データは都道府県「名」のみ → 変換テーブル必要
- **合区 (鳥取+島根 / 徳島+高知)** は事前ルール決定: 別扱い扱いか欠損処理か

---

## 既存 data/raw/ のプロファイル

### `February 2026 Foreigners Entering Japan.xlsx`
- シート: `26-02-02-2` (`2-2 国籍・地域別 新規入国外国人の在留資格`)
- 形状: 約 30 × 40
- **行**: 国籍・地域 (アジア、アフガニスタン、...)
- **列**: 在留資格 (総数、外交、公用、...、永住者、日本人の配偶者等、永住者の配偶者等、定住者)
- **粒度**: **国籍 × 在留資格** (← prefecture 別ではない！フローのみ)
- **期間**: 2026 年 2 月単月

### `February 2026 Foreigners Leaving Japan.xlsx`
- 構造はほぼ同じ、出国フロー版

### `July 10 2022 House of Councillors election.xls`
- シート: `5110` (`(5) 都道府県別党派別得票数 (比例代表)`)
- **行**: 都道府県 47
- **列**: 政党名 × {得票総数, 得票率, 政党等の得票総数, 名簿登載者得票総数} の 4 値セット
- **粒度**: **都道府県 × 党派**

### `July 20 2025 House of Councillors election results.xlsx`
- シート: `都道府県別` (`(6) 都道府県別党派別得票数 (比例代表)`)
- 構造は 2022 とほぼ同じ

### `October 27 2024 House of Representatives election.xls`
- シート: `5210` (`(7) 比例代表選挙区別都道府県別党派別得票数`)
- **行**: 比例代表区 (北海道、東北、北関東、...) × 都道府県
- **列**: 党派 (自民、立憲、維新、公明、共産、国民、参政、社民、...)
- **粒度**: **比例ブロック × 都道府県 × 党派**

### `February 8 2026 House of Representatives election.xlsx`
- 構造は 2024 とほぼ同じ

### 重要な発見

**問題**: `data/raw/` の **入出国 Excel は国籍別フローのみ** で、**都道府県別ではない**。Phase 1 の outcome (都道府県別在留外国人ストック) を作るには、**e-Stat の在留外国人統計** (上記 1-1) を別途取得する必要がある。

**選挙データ**: 4 ファイルとも都道府県別の比例得票が含まれているので、treatment と outcome の片側 (outcome 側) は既に手元にある。
