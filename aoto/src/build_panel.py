"""Join elections and foreign-residents panels into one analysis-ready frame.

For each (election_id, prefecture), attach the most recent foreign-residents
period that is *strictly before* the election date — this is the pre-election
treatment state.

Outputs:
    aoto/data/clean/joined_panel.parquet
        One row per (election_id, prefecture, party):
        - election_id, election_type, election_date, election_year
        - pref_code, prefecture
        - party, votes, vote_share_pct
        - treat_period: which foreign-residents period was matched
        - foreign_total: total foreign residents in that period
        - foreign_total_year_ago: same one year earlier (for growth rate)
        - foreign_growth_yoy: year-over-year growth in foreign-residents
        - by_status_*: counts in selected residence-status categories
        - restrictive_index: 1 if party in {自由民主党, 日本維新の会,
          参政党}; -1 if {立憲, 共産, 社民, れいわ}; 0 otherwise

    aoto/data/clean/joined_panel_pref_election.parquet
        One row per (election_id, prefecture) — wide on party.
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "aoto" / "data" / "clean"


# Aggregate the 36 raw 在留資格 codes into 9 analytical categories.
# Key = status_code (2-digit string), value = category name.
STATUS_CODE_TO_CAT = {
    # permanent / settled
    "27": "permanent",
    "36": "permanent",  # 特別永住者
    "31": "spouse_japanese",
    "32": "spouse_japanese",
    "33": "long_term",
    # skilled professionals
    "07": "skilled_specialist", "08": "skilled_specialist",
    "09": "skilled_specialist", "10": "skilled_specialist",
    "11": "skilled_specialist", "12": "skilled_specialist",
    "13": "skilled_specialist", "14": "skilled_specialist",
    "15": "skilled_specialist", "16": "skilled_specialist",
    "23": "skilled_specialist",
    # low-skill labor pipeline
    "28": "intern_low_skill",
    "42": "intern_low_skill",  # 育成就労 (post-2023 successor)
    "29": "specified_skilled",
    "30": "specified_skilled",
    # student
    "20": "student",
    # other work
    "17": "other_work", "18": "other_work",
    "21": "other_work", "22": "other_work",
    # diplomatic / official
    "01": "diplomatic_official", "02": "diplomatic_official",
}


def _classify_code(code: str) -> str:
    return STATUS_CODE_TO_CAT.get(code, "other")


# Party → restrictive-index score (draft, see aoto/docs/party_positions_2025.md)
RESTRICTIVE_SCORE = {
    "自由民主党": +1,
    "日本維新の会": +1,
    "参政党": +2,
    "立憲民主党": -1,
    "民主党": -1,
    "民進党": -1,
    "日本共産党": -2,
    "社会民主党": -2,
    "れいわ新選組": -2,
    "公明党": 0,
    "国民民主党": 0,
}


def main():
    elections = pd.read_parquet(CLEAN / "elections_panel.parquet")
    fr = pd.read_parquet(CLEAN / "foreign_residents_panel.parquet")
    fr_total = pd.read_parquet(CLEAN / "foreign_residents_panel_total.parquet")

    elections["election_date"] = pd.to_datetime(elections["election_date"])
    fr["period_date"] = pd.to_datetime(fr["period_date"])
    fr_total["period_date"] = pd.to_datetime(fr_total["period_date"])

    # Aggregate fr into categories per (period, pref_code)
    fr = fr.copy()
    fr["status_cat"] = fr["status_code"].astype(str).apply(_classify_code)
    fr_cat = (
        fr.groupby(["period", "period_date", "pref_code", "status_cat"], as_index=False)[
            "n_residents"
        ]
        .sum()
    )
    fr_wide = fr_cat.pivot_table(
        index=["period", "period_date", "pref_code"],
        columns="status_cat",
        values="n_residents",
        fill_value=0,
    ).reset_index()
    fr_wide.columns.name = None
    fr_wide = fr_wide.rename(columns={c: f"by_status_{c}" for c in fr_wide.columns if c not in {"period", "period_date", "pref_code"}})

    # Join with the totals
    fr_full = fr_total.merge(fr_wide, on=["period", "period_date", "pref_code"], how="left")
    fr_full = fr_full.rename(columns={"n_residents": "foreign_total"})

    # For each (election, prefecture), find the most recent period strictly before
    # the election date.
    elec_w_treat = []
    for (eid, pref), grp in elections.groupby(["election_id", "pref_code"], sort=False):
        edate = grp["election_date"].iloc[0]
        avail = fr_full[(fr_full["pref_code"] == pref) & (fr_full["period_date"] < edate)]
        if avail.empty:
            treat_row = None
            yoy_row = None
        else:
            treat_row = avail.loc[avail["period_date"].idxmax()].to_dict()
            # year-ago: closest period roughly 1 year before treat_period_date
            target = treat_row["period_date"] - pd.Timedelta(days=365)
            yoy = fr_full[
                (fr_full["pref_code"] == pref) & (fr_full["period_date"] < treat_row["period_date"])
            ]
            yoy = yoy.iloc[(yoy["period_date"] - target).abs().argsort()]
            yoy_row = yoy.iloc[0].to_dict() if not yoy.empty else None
        out = grp.copy()
        if treat_row is None:
            out["treat_period"] = None
            out["foreign_total"] = pd.NA
        else:
            out["treat_period"] = treat_row["period"]
            for k, v in treat_row.items():
                if k.startswith("by_status_") or k == "foreign_total":
                    out[k] = v
        if yoy_row is not None and treat_row is not None and yoy_row["period"] != treat_row["period"]:
            out["foreign_total_year_ago"] = yoy_row["foreign_total"]
            out["foreign_growth_yoy"] = (
                (treat_row["foreign_total"] - yoy_row["foreign_total"]) / yoy_row["foreign_total"]
            )
        else:
            out["foreign_total_year_ago"] = pd.NA
            out["foreign_growth_yoy"] = pd.NA
        elec_w_treat.append(out)

    joined = pd.concat(elec_w_treat, ignore_index=True)
    joined["restrictive_score"] = joined["party"].map(RESTRICTIVE_SCORE).fillna(0)

    out_a = CLEAN / "joined_panel.parquet"
    joined.to_parquet(out_a, index=False)
    joined.to_csv(CLEAN / "joined_panel.csv", index=False)
    print(f"joined panel: {len(joined):,} rows -> {out_a}")
    print(joined.head().to_string())

    # Coverage summary
    print("\n=== treatment coverage per election ===")
    cov = (
        joined.groupby("election_id")
        .agg(
            n_rows=("party", "count"),
            n_with_treat=("foreign_total", lambda s: s.notna().sum()),
            n_with_yoy=("foreign_growth_yoy", lambda s: s.notna().sum()),
        )
    )
    print(cov.to_string())

    # Pref-election wide view (one row per pref × election)
    party_wide = joined.pivot_table(
        index=["election_id", "election_year", "election_date", "election_type", "pref_code", "prefecture"],
        columns="party",
        values="vote_share_pct",
    ).reset_index()
    party_wide.columns.name = None
    party_cols = [c for c in party_wide.columns if c not in {
        "election_id", "election_year", "election_date", "election_type",
        "pref_code", "prefecture",
    }]
    party_wide = party_wide.rename(columns={c: f"share_{c}" for c in party_cols})
    # add the foreign-resident covariates (one set per pref × election)
    cov_cols = ["election_id", "pref_code", "treat_period", "foreign_total",
                "foreign_growth_yoy"] + [c for c in joined.columns if c.startswith("by_status_")]
    elec_covar = joined[cov_cols].drop_duplicates(subset=["election_id", "pref_code"])
    pref_elec = party_wide.merge(elec_covar, on=["election_id", "pref_code"], how="left")
    out_b = CLEAN / "joined_panel_pref_election.parquet"
    pref_elec.to_parquet(out_b, index=False)
    pref_elec.to_csv(CLEAN / "joined_panel_pref_election.csv", index=False)
    print(f"\npref × election wide panel: {len(pref_elec):,} rows -> {out_b}")


if __name__ == "__main__":
    main()
