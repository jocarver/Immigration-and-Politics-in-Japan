"""Quick descriptive stats on the joined panel.

Output: aoto/data/clean/quick_describe.md (and printed to stdout).
This is exploratory — DOES NOT establish causality, only correlations.
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "aoto" / "data" / "clean"
OUT_MD = CLEAN / "quick_describe.md"


def main():
    pe = pd.read_parquet(CLEAN / "joined_panel_pref_election.parquet")
    lines = []
    lines.append("# Quick descriptive stats — joined panel\n")
    lines.append("> One row per (election × prefecture). 470 rows total. **NOT causal**, just first-look correlations.\n")

    lines.append("## 1. Coverage\n")
    cov = (
        pe.groupby(["election_id", "election_date"])
        .agg(
            n_prefs=("pref_code", "nunique"),
            has_treat=("foreign_total", lambda s: s.notna().sum()),
        )
    )
    lines.append("```\n" + cov.to_string() + "\n```\n")

    lines.append("## 2. Foreign-resident totals (national sum, latest pre-election period)\n")
    nat = pe.dropna(subset=["foreign_total"]).groupby("election_id")["foreign_total"].sum().astype(int)
    lines.append("```\n" + nat.to_string() + "\n```\n")

    lines.append("## 3. Top-10 prefectures by foreign share (latest = 2025 sangiin period)\n")
    # foreign_total per prefecture / sum -> share. Use 2025 sangiin pre-treatment.
    s25 = pe[pe["election_id"] == "2025_sangiin"][["prefecture", "foreign_total"]].dropna()
    s25 = s25.sort_values("foreign_total", ascending=False).head(10)
    lines.append("```\n" + s25.to_string(index=False) + "\n```\n")

    lines.append("## 4. Correlation: foreign-residents level vs party vote share (latest sangiin = 2025)\n")
    party_cols = [c for c in pe.columns if c.startswith("share_")]
    s25_full = pe[pe["election_id"] == "2025_sangiin"].dropna(subset=["foreign_total"]).copy()
    corr_rows = []
    for c in party_cols:
        if s25_full[c].notna().sum() < 10:
            continue
        r = s25_full[["foreign_total", c]].corr().iloc[0, 1]
        r_log = s25_full[[c]].assign(lf=s25_full["foreign_total"].apply(lambda x: pd.NA if pd.isna(x) else float(x))).corr().iloc[0, 1]
        corr_rows.append((c, r))
    corr_df = pd.DataFrame(corr_rows, columns=["party", "corr_with_foreign_total"]).sort_values(
        "corr_with_foreign_total", ascending=False
    )
    lines.append("```\n" + corr_df.to_string(index=False) + "\n```\n")
    lines.append("Interpretation: positive corr → party does *better* in prefectures with more foreign residents (which are also the urban / Tokyo / Osaka / Aichi triad). NOT a causal statement — confounded by population, urbanization, etc.\n")

    lines.append("## 5. Correlation: foreign-residents YoY growth vs party vote share (2025 sangiin)\n")
    g25 = s25_full.dropna(subset=["foreign_growth_yoy"]).copy()
    corr_rows_g = []
    for c in party_cols:
        if g25[c].notna().sum() < 10:
            continue
        r = g25[["foreign_growth_yoy", c]].corr().iloc[0, 1]
        corr_rows_g.append((c, r))
    corr_df_g = pd.DataFrame(corr_rows_g, columns=["party", "corr_with_foreign_growth_yoy"]).sort_values(
        "corr_with_foreign_growth_yoy", ascending=False
    )
    lines.append("```\n" + corr_df_g.to_string(index=False) + "\n```\n")

    lines.append("## 6. Sanseitō (2026 shugiin) vs foreign-residents — the key relationship\n")
    s26 = pe[pe["election_id"] == "2026_shugiin"].dropna(subset=["foreign_total"]).copy()
    sanseito_col = next((c for c in s26.columns if "参政" in c), None)
    if sanseito_col:
        s26_clean = s26.dropna(subset=[sanseito_col, "foreign_total"])
        r_level = s26_clean[[sanseito_col, "foreign_total"]].corr().iloc[0, 1]
        # Try log
        import numpy as np
        s26_clean["log_foreign_total"] = np.log(s26_clean["foreign_total"])
        r_log = s26_clean[[sanseito_col, "log_foreign_total"]].corr().iloc[0, 1]
        r_growth = s26_clean.dropna(subset=["foreign_growth_yoy"])[[sanseito_col, "foreign_growth_yoy"]].corr().iloc[0, 1]
        lines.append(f"- Sanseitō vote share vs foreign-residents level: r = **{r_level:.3f}**\n")
        lines.append(f"- Sanseitō vote share vs log(foreign-residents): r = **{r_log:.3f}**\n")
        lines.append(f"- Sanseitō vote share vs YoY growth in foreign-residents: r = **{r_growth:.3f}**\n")
        top = s26_clean.sort_values(sanseito_col, ascending=False).head(10)[
            ["prefecture", sanseito_col, "foreign_total", "foreign_growth_yoy"]
        ]
        lines.append("\nTop-10 Sanseitō-share prefectures (2026 shugiin):\n")
        lines.append("```\n" + top.to_string(index=False) + "\n```\n")
    else:
        lines.append("No 参政党 column found in 2026 panel — check parser output.\n")

    text = "".join(lines) if isinstance(lines, str) else "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
