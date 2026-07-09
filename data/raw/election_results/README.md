# data/raw/election_results — 選挙結果データ

総務省「選挙関連資料」から取得した Excel ファイル。いずれも **比例代表・都道府県別党派別得票数** の表。

## ファイル一覧

| ファイル名 | 選挙 | 表の粒度 | 取得元 URL |
|---|---|---|---|
| `July 21 2013 House of Councillors election.xls` | 第23回参院選 2013/07/21 | （５）都道府県別党派別得票数（比例代表） | https://www.soumu.go.jp/main_content/000244369.xls |
| `July 10 2016 House of Councillors election.xls` | 第24回参院選 2016/07/10 | （５）都道府県別党派別得票数（比例代表） | https://www.soumu.go.jp/main_content/000430610.xls |
| `July 21 2019 House of Councillors election.xls` | 第25回参院選 2019/07/21 | （５）都道府県別党派別得票数（比例代表） | https://www.soumu.go.jp/main_content/000636675.xls |
| `July 10 2022 House of Councillors election.xls` | 第26回参院選 2022/07/10 | 都道府県別党派別得票数（比例代表）全国比例 | 総務省 sangiin26 index |
| `July 20 2025 House of Councillors election results.xlsx` | 第27回参院選 2025/07/20 | 都道府県別党派別得票数（比例代表）全国比例 | 総務省 sangiin27 index |
| `December 14 2014 House of Representatives election.xls` | 第47回衆院選 2014/12/14 | 比例代表選挙区別都道府県別党派別得票数（ブロック別） | https://www.soumu.go.jp/main_content/000328949.xls |
| `October 22 2017 House of Representatives election.xls` | 第48回衆院選 2017/10/22 | 比例代表選挙区別都道府県別党派別得票数（ブロック別）項目(7) | https://www.soumu.go.jp/main_content/000516725.xls |
| `October 27 2024 House of Representatives election.xls` | 第50回衆院選 2024/10/27 | 比例代表選挙区別都道府県別党派別得票数（ブロック別） | 総務省 shugiin50 index |
| `October 31 2021 House of Representatives election.xlsx` | 第49回衆院選 2021/10/31 | 比例代表選挙区別都道府県別党派別得票数（ブロック別）項目(7) | https://www.soumu.go.jp/main_content/000776973.xlsx |
| `February 8 2026 House of Representatives election.xlsx` | 第51回衆院選 2026/02/08 | 比例代表選挙区別都道府県別党派別得票数（ブロック別） | 総務省 shugiin51 index |

## 取得方法

`aoto/src/fetch_soumu_elections.py` を参照。

```bash
uv run --with requests python aoto/src/fetch_soumu_elections.py
```

## データ構造上の注意

### 参院選 (sangiin)

- 全国単一の比例代表ブロック → 都道府県 × 党派 の 2 次元表
- 列: 党派名（自民、立憲、公明、…）
- 行: 都道府県（北海道〜沖縄 + 全国計）
- 識別列 (A 列) に都道府県コード or 名称

### 衆院選 (shugiin)

- 比例代表は 11 ブロック制 → ブロック × 都道府県 × 党派 の 3 次元表
- Excel 内でブロックごとにグループ行が存在する
- 参院選データと結合するには都道府県集計列を抽出して整形が必要

### 衆院選 ファイル選択の注意

各衆院選 index.html には複数の比例関連ファイルがある:

- `(5)` 党派別得票数（比例代表）→ **全国集計のみ、都道府県なし**
- `(7)` 比例代表選挙区別都道府県別党派別得票数 → **これが目的のファイル**

`fetch_soumu_elections.py` は (7) のファイルのみを DL している。

## インデックスページ（参照先）

| 選挙 | index.html |
|---|---|
| 第23回参院選 2013 | https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin23/index.html |
| 第24回参院選 2016 | https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin24/index.html |
| 第25回参院選 2019 | https://www.soumu.go.jp/senkyo/senkyo_s/data/sangiin25/index.html |
| 第47回衆院選 2014 | https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin47/index.html |
| 第48回衆院選 2017 | https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin48/index.html |
| 第49回衆院選 2021 | https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin49/index.html |
