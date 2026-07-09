# 国会会議録 API 取得データ

## 取得概要

| 項目 | 内容 |
|---|---|
| 取得日 | 2026-05-13 |
| API | [国会会議録検索システム API](https://kokkai.ndl.go.jp/api.html) — `/api/speech` エンドポイント |
| 期間 | 2015-01-01 ~ 2026-04-30 (約 11 年) |
| 取得単位 | 発言 (speech) 単位 |
| 重複除去後総件数 | 13,563 件 |

## 検索キーワード一覧と件数

API の `any` パラメータで各キーワードを個別に検索し、OR ではなくキーワード別にファイルを分けた。

| キーワード | API ヒット総数 | 取得件数 | 備考 |
|---|---|---|---|
| 移民 | 955 | 955 | 全件取得 |
| 外国人 | 19,251 | 5,000 | 5,000 件でキャップ |
| 在留外国人 | 505 | 505 | 全件取得 |
| 特定技能 | 2,307 | 2,307 | 全件取得 |
| 技能実習 | 5,931 | 5,000 | 5,000 件でキャップ |
| 外国人労働者 | 1,779 | 1,779 | 全件取得 |
| 永住者 | 565 | 565 | 全件取得 |
| 在留資格 | 2,938 | 2,938 | 全件取得 |

## ファイル構成

```
data/raw/kokkai/
├── README.md                                    (このファイル)
├── speeches_移民_2015-01-01_2026-04-30.json
├── speeches_外国人_2015-01-01_2026-04-30.json
├── speeches_在留外国人_2015-01-01_2026-04-30.json
├── speeches_特定技能_2015-01-01_2026-04-30.json
├── speeches_技能実習_2015-01-01_2026-04-30.json
├── speeches_外国人労働者_2015-01-01_2026-04-30.json
├── speeches_永住者_2015-01-01_2026-04-30.json
└── speeches_在留資格_2015-01-01_2026-04-30.json
```

各 JSON は `list[dict]` 形式。フィールドは以下の通り:
`speechID`, `issueID`, `imageKind`, `searchObject`, `session`, `nameOfHouse`, `nameOfMeeting`, `issue`, `date`, `closing`, `speechOrder`, `speaker`, `speakerYomi`, `speakerGroup`, `speakerPosition`, `speakerRole`, `speech` (本文), `startPage`, `speechURL`, `meetingURL`

## クリーンデータ (aoto/data/clean/)

| ファイル | 内容 |
|---|---|
| `kokkai_speeches_all.csv` | 全 13,563 発言を `speechID` で重複除去したフラット CSV |
| `kokkai_count_by_year_party.csv` | 年 × 政党の発言件数クロス集計 (long format) |
| `kokkai_top_speakers.csv` | 議員別発言件数 Top 30 |

## 注意点・落とし穴

1. **キャップあり**: 「外国人」(19,251 件) と「技能実習」(5,931 件) は 5,000 件でキャップ。API は日付昇順で返すため、古い発言が優先的に収録される。最新発言が不足している可能性に注意。
2. **重複**: 複数キーワードにヒットする発言が多数 (19,049 件 → 13,563 件、約 29% が重複)。`kokkai_speeches_all.csv` では `speechID` で除去済み。
3. **speakerGroup 欠損**: 「不明」が 3,738 件 (27.6%)。委員長発言・政府参考人・大臣官僚の発言は所属政党が記録されない場合が多い。政党分析には要注意。
4. **speaker 欠損**: 議員名が空欄のレコードは `"不明"` に統一してある。
5. **「外国人」の広義性**: このキーワードは移民文脈以外 (外国人観光客、外国人研究者など) も含む可能性がある。text analysis 時にフィルタリングを検討すること。
6. **期間外の可能性**: API 側の更新タイミングにより 2026-04 の最新会議録が未収録のケースがある。

## 再取得方法

```bash
cd /Users/uooooo/Documents/ut/2026S/wed2_ds/Skilled-Immigration
uv run --project aoto python aoto/src/fetch_kokkai.py
```
