"""Aggregate e-Stat 在留外国人統計 t1 Excel files into a long panel.

Input:
    data/raw/foreign_residents/<year>_<half>/<file>-t1*.xlsx
    (14 files, half-yearly 2016-12 ~ 2025-06; older periods use a different
    format with country/status splits and are skipped here.)

Output:
    aoto/data/clean/foreign_residents_panel.parquet
        Long format: (period, period_date, prefecture, residence_status, n_residents)
        - period: e.g., "2024-12"
        - period_date: end-of-period date (date)
        - prefecture: 47 都道府県 (excluding "00：全国")
        - residence_status: e.g., "01：外交"〜"36：特別永住者"
        - n_residents: sum across nationality / age / sex

    aoto/data/clean/foreign_residents_panel_total.parquet
        Same but residence_status removed (prefecture × period total only)

The second sheet of each xlsx ('令和X年Y月末') is row-level data with columns:
    国籍・地域 / 在留資格 / 性別 / 年齢（５歳階級）/ 年齢 / 都道府県 / 在留外国人数
"""
from __future__ import annotations
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "foreign_residents"
OUT = ROOT / "aoto" / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)


def find_t1_files() -> list[Path]:
    return sorted(RAW.rglob("*-t1*.xlsx"))


def parse_period_from_path(p: Path) -> tuple[str, pd.Timestamp]:
    """e.g. 'data/raw/foreign_residents/2024_12/24-12-t1.xlsx' -> ('2024-12', 2024-12-31)."""
    m = re.match(r"(\d{4})_(\d{2})", p.parent.name)
    assert m, f"could not parse year/half from {p.parent.name}"
    y, h = m.group(1), m.group(2)
    period = f"{y}-{h}"
    if h == "06":
        end = pd.Timestamp(f"{y}-06-30")
    elif h == "12":
        end = pd.Timestamp(f"{y}-12-31")
    else:
        raise ValueError(f"unexpected half {h}")
    return period, end


def load_t1(path: Path) -> pd.DataFrame:
    """Read the row-level data sheet.

    The data sheet has columns 在留資格 / 都道府県 / 在留外国人数 (plus
    国籍・地域 / 性別 / 年齢 etc.). The pivot sheet has only 2 columns.
    Pivot may appear at index 0 OR 1 depending on the year, so we
    detect by column-name fingerprint.
    """
    xl = pd.ExcelFile(path)
    needed = {"在留資格", "都道府県", "在留外国人数"}
    for sh in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sh)
        cols = {str(c).strip() for c in df.columns}
        if needed.issubset(cols):
            df = df.rename(columns={c: str(c).strip() for c in df.columns})
            return df
    raise AssertionError(
        f"no sheet with {needed} found in {path}; sheets={xl.sheet_names}"
    )


def main():
    files = find_t1_files()
    print(f"found {len(files)} t1 files")
    rows = []
    for p in files:
        period, end = parse_period_from_path(p)
        print(f"  {period}: {p.name}")
        df = load_t1(p)
        # drop the 全国 aggregate row
        df = df[~df["都道府県"].astype(str).str.startswith("00：")].copy()
        # aggregate (都道府県, 在留資格) -> sum
        agg = (
            df.groupby(["都道府県", "在留資格"], dropna=False)["在留外国人数"]
            .sum()
            .reset_index()
            .rename(columns={"在留外国人数": "n_residents"})
        )
        agg["period"] = period
        agg["period_date"] = end
        rows.append(agg)
    panel = pd.concat(rows, ignore_index=True)
    panel = panel[["period", "period_date", "都道府県", "在留資格", "n_residents"]]
    panel = panel.rename(columns={"都道府県": "prefecture_raw", "在留資格": "residence_status_raw"})
    # Normalize: "01：北海道" -> pref_code="01", prefecture="北海道"
    panel["pref_code"] = panel["prefecture_raw"].str.split("：").str[0]
    panel["prefecture"] = panel["prefecture_raw"].str.split("：").str[1]
    panel["status_code"] = panel["residence_status_raw"].str.split("：").str[0]
    panel["residence_status"] = panel["residence_status_raw"].str.split("：").str[1]
    panel = panel[[
        "period", "period_date", "pref_code", "prefecture",
        "status_code", "residence_status", "n_residents",
    ]]
    # Flag (but keep) "48：未定・不詳"
    panel["is_unknown_pref"] = panel["pref_code"] == "48"
    out_a = OUT / "foreign_residents_panel.parquet"
    panel.to_parquet(out_a, index=False)
    panel.to_csv(OUT / "foreign_residents_panel.csv", index=False)
    print(f"\nfull panel: {len(panel):,} rows -> {out_a}")
    print(panel.head())
    print()

    # Pref × period totals (sum across residence statuses, excluding 不詳)
    totals = (
        panel[~panel["is_unknown_pref"]]
        .groupby(["period", "period_date", "pref_code", "prefecture"], as_index=False)["n_residents"]
        .sum()
    )
    out_b = OUT / "foreign_residents_panel_total.parquet"
    totals.to_parquet(out_b, index=False)
    totals.to_csv(OUT / "foreign_residents_panel_total.csv", index=False)
    print(f"prefecture × period totals: {len(totals):,} rows -> {out_b}")
    print(totals.groupby("period")["n_residents"].sum().sort_index())


if __name__ == "__main__":
    main()
