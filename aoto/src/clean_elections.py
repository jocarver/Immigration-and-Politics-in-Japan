"""Clean the 4 existing election Excel files into a long-format panel.

Input:
    data/raw/election_results/*.xls{,x}
Output:
    aoto/data/clean/elections_panel.parquet
    aoto/data/clean/elections_panel.csv

Each row: (election_id, election_type, election_date, prefecture, party, votes, vote_share_pct)
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # repo root
RAW = ROOT / "data" / "raw" / "election_results"
OUT = ROOT / "aoto" / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

# 47 都道府県 (JIS X 0401 ordering — index + 1 = pref_code)
PREFS = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]
PREF_SET = set(PREFS)
PREF_CODE = {name: f"{i+1:02d}" for i, name in enumerate(PREFS)}


def _norm(s):
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize("NFKC", s)
    return s.strip().replace("　", " ").replace("\n", " ")


def _to_float(x):
    if pd.isna(x):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).replace(",", "").strip()
    if not s or s in {"-", "ー", "―"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_sangiin(path: Path, election_id: str, election_date: str):
    """参院選: (5) or (6) 都道府県別党派別得票数 (比例代表).

    The layout is:
      row 0: title
      row 3: party names sparsely (every 4 cols)
      row 6/7: header (都道府県 / 得票総数 / 得票率 / 政党等の得票総数 / 名簿登載者得票総数)
      row 8 onwards: 47 prefectures, then 合計
    Each party occupies 4 columns: 得票総数, 得票率(%), 政党等の得票総数, 名簿登載者の得票総数
    """
    raw = pd.read_excel(path, header=None, sheet_name=0)
    # Find the row that has 自由民主党 / 立憲民主党 etc.
    party_row = None
    for i in range(min(15, len(raw))):
        cells = [_norm(c) for c in raw.iloc[i].tolist()]
        if any(isinstance(c, str) and "自由民主党" in c for c in cells):
            party_row = i
            break
    assert party_row is not None, f"could not find party header in {path}"
    parties = []
    for col_idx, val in enumerate(raw.iloc[party_row]):
        v = _norm(val)
        if isinstance(v, str) and any(k in v for k in ("党", "の会", "新選組", "風", "政")):
            parties.append((col_idx, v))
    # Find pref column (the column whose first 47 non-null values include many prefs)
    pref_col = None
    for col in range(min(6, raw.shape[1])):
        vals = [_norm(v) for v in raw.iloc[:, col].dropna().tolist()]
        if sum(1 for v in vals if v in PREF_SET) >= 30:
            pref_col = col
            break
    assert pref_col is not None, f"could not find prefecture column in {path}"
    # Walk rows after party_row, dedup prefectures (some sheets repeat the prefecture column)
    rows = []
    seen_prefs = set()
    for i in range(party_row, len(raw)):
        pref = _norm(raw.iat[i, pref_col]) if pref_col < raw.shape[1] else None
        if pref not in PREF_SET or pref in seen_prefs:
            continue
        seen_prefs.add(pref)
        for col_idx, party in parties:
            votes = _to_float(raw.iat[i, col_idx])
            share = _to_float(raw.iat[i, col_idx + 1]) if col_idx + 1 < raw.shape[1] else None
            rows.append({
                "election_id": election_id,
                "election_type": "sangiin_pr",
                "election_date": election_date,
                "prefecture": pref,
                "party": party,
                "votes": votes,
                "vote_share_pct": share,
            })
    return pd.DataFrame(rows)


def parse_shugiin(path: Path, election_id: str, election_date: str):
    """衆院選: (7) 比例代表選挙区別都道府県別党派別得票数.

    Layout:
      row ~3: party headers
      The block has '比例代表区' column and '都道府県' (or 区分) column then party vote columns.
      For each prefecture in each 比例 block, votes for each party.
    """
    raw = pd.read_excel(path, header=None, sheet_name=0)
    # Find row that has 自由民主党 etc.
    party_row = None
    for i in range(min(15, len(raw))):
        cells = [_norm(c) for c in raw.iloc[i].tolist()]
        if any(isinstance(c, str) and "自由民主党" in c for c in cells):
            party_row = i
            break
    assert party_row is not None, f"could not find party header in {path}"
    parties = []
    for col_idx, val in enumerate(raw.iloc[party_row]):
        v = _norm(val)
        if isinstance(v, str) and ("党" in v or "の会" in v or "新選組" in v or "参政" in v):
            parties.append((col_idx, v))
    # Find prefecture column: look for a column where many entries are pref names
    pref_col = None
    best_count = 0
    for col in range(min(6, raw.shape[1])):
        vals = [_norm(v) for v in raw.iloc[party_row:, col].dropna().tolist()]
        c = sum(1 for v in vals if v in PREF_SET)
        if c > best_count:
            best_count = c
            pref_col = col
    assert best_count >= 30, f"could not find prefecture column in {path} (best={best_count})"
    rows = []
    seen_prefs = set()
    for i in range(party_row + 1, len(raw)):
        pref = _norm(raw.iat[i, pref_col]) if pref_col < raw.shape[1] else None
        if pref not in PREF_SET or pref in seen_prefs:
            continue
        seen_prefs.add(pref)
        for col_idx, party in parties:
            votes = _to_float(raw.iat[i, col_idx])
            if votes is None:
                continue
            rows.append({
                "election_id": election_id,
                "election_type": "shugiin_pr",
                "election_date": election_date,
                "prefecture": pref,
                "party": party,
                "votes": votes,
                "vote_share_pct": None,  # need to compute
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Compute share per (election_id, prefecture)
    totals = df.groupby(["election_id", "prefecture"])["votes"].transform("sum")
    df["vote_share_pct"] = (df["votes"] / totals) * 100.0
    return df


def main():
    files = {
        "2013_sangiin": (RAW / "July 21 2013 House of Councillors election.xls", "2013-07-21", parse_sangiin),
        "2014_shugiin": (RAW / "December 14 2014 House of Representatives election.xls", "2014-12-14", parse_shugiin),
        "2016_sangiin": (RAW / "July 10 2016 House of Councillors election.xls", "2016-07-10", parse_sangiin),
        "2017_shugiin": (RAW / "October 22 2017 House of Representatives election.xls", "2017-10-22", parse_shugiin),
        "2019_sangiin": (RAW / "July 21 2019 House of Councillors election.xls", "2019-07-21", parse_sangiin),
        "2021_shugiin": (RAW / "October 31 2021 House of Representatives election.xlsx", "2021-10-31", parse_shugiin),
        "2022_sangiin": (RAW / "July 10 2022 House of Councillors election.xls", "2022-07-10", parse_sangiin),
        "2024_shugiin": (RAW / "October 27 2024 House of Representatives election.xls", "2024-10-27", parse_shugiin),
        "2025_sangiin": (RAW / "July 20 2025 House of Councillors election results.xlsx", "2025-07-20", parse_sangiin),
        "2026_shugiin": (RAW / "February 8 2026 House of Representatives election.xlsx", "2026-02-08", parse_shugiin),
    }
    dfs = []
    for eid, (path, date, parser) in files.items():
        if not path.exists():
            print(f"  MISSING: {path}")
            continue
        print(f"Parsing {eid}: {path.name}")
        df = parser(path, eid, date)
        print(f"  -> {len(df)} rows, parties: {sorted(df['party'].unique())}")
        dfs.append(df)
    panel = pd.concat(dfs, ignore_index=True)
    panel["pref_code"] = panel["prefecture"].map(PREF_CODE)
    panel["election_year"] = pd.to_datetime(panel["election_date"]).dt.year
    panel = panel[[
        "election_id", "election_type", "election_date", "election_year",
        "pref_code", "prefecture", "party", "votes", "vote_share_pct",
    ]]
    panel.to_parquet(OUT / "elections_panel.parquet", index=False)
    panel.to_csv(OUT / "elections_panel.csv", index=False)
    print("=" * 60)
    print(f"Total rows: {len(panel)}")
    print(panel.groupby(["election_id", "election_type"]).agg(
        n_rows=("votes", "count"),
        total_votes=("votes", "sum"),
        n_prefs=("prefecture", "nunique"),
        n_parties=("party", "nunique"),
    ))


if __name__ == "__main__":
    main()
