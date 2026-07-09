"""Party canonicalization utilities for Kokkai NDL speakerGroup values.

The Kokkai API returns a single ``speakerGroup`` string per speech, but in
practice these values are parliamentary caucuses (会派) that bundle multiple
parties with separators like ``・`` (most common), ``．`` (rare variant) and
``/`` (rare). For analysis, we want to attribute each speech to one or more
canonical parties.

This module is pure (no I/O). It exposes three functions:
  * ``parse_speaker_group`` — split + normalize a single raw string
  * ``compute_canonical_counts`` — count how many speeches carry each canonical party
  * ``filter_speeches_by_party_size`` — drop tiny parties (and any speech whose
    canonical list becomes empty as a result)
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

# Separators used in caucus names. Order is not significant; ``re.split``
# accepts a pattern built from this tuple.
SEPARATORS: tuple[str, ...] = ("・", "．", "/")

# Common abbreviations and variants found in the corpus. Add new entries
# here as new variants surface; the canonical key on the right is the form
# that will be stored in ``parties_canonical``.
NORMALIZATIONS: dict[str, str] = {
    "社民": "社会民主党",
    "立憲民主": "立憲民主党",
    "無所属会": "無所属の会",
    "国民": "国民民主党",
    "民主": "民主党",
    "維新": "日本維新の会",
}


def parse_speaker_group(raw, normalizations: dict | None = None) -> list[str]:
    """Lenient split on caucus separators, then normalize each component.

    Returns an empty list for None / NaN / empty input.
    """
    if normalizations is None:
        normalizations = NORMALIZATIONS
    if raw is None:
        return []
    if not isinstance(raw, str):
        # Catches pandas NaN, float, etc.
        return []
    if not raw.strip():
        return []
    pattern = "|".join(re.escape(sep) for sep in SEPARATORS)
    parts = re.split(pattern, raw)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(normalizations.get(p, p))
    return out


def compute_canonical_counts(speeches: dict) -> dict[str, int]:
    """For each canonical party, count how many speeches have it in
    ``parties_canonical``. A speech with multiple parties contributes +1
    to each party's count.
    """
    counts: Counter[str] = Counter()
    for s in speeches.values():
        for p in s.get("parties_canonical", []):
            counts[p] += 1
    return dict(counts)


def filter_speeches_by_party_size(
    speeches: dict,
    min_count: int = 3,
    keep_parties: set[str] | None = None,
) -> tuple[dict, set[str]]:
    """Drop canonical parties with fewer than ``min_count`` speeches.

    A speech is removed entirely if, after dropping tiny parties, all of
    its canonical parties were tiny. Speeches with an empty
    ``parties_canonical`` list (no party affiliation, e.g. committee
    chairs, expert witnesses) are KEPT — they are not "tiny party"
    speeches, they are "no party" speeches and have analytical value.

    ``keep_parties`` is an optional whitelist of canonical parties that
    should be kept regardless of their speech count. Useful for
    cross-team joins: if Joe's election-data analysis treats a party
    as important, we keep its few speeches in our analysis rather
    than dropping them as "tiny". Pass ``set(load_joe_party_dicts()[0])``
    to use Joe's full list as the whitelist.

    Returns the filtered speeches dict and the set of kept canonical
    party names.
    """
    counts = compute_canonical_counts(speeches)
    kept_by_count = {p for p, c in counts.items() if c >= min_count}
    keep_parties = keep_parties or set()
    kept = kept_by_count | keep_parties
    filtered: dict = {}
    for sid, s in speeches.items():
        cps = s.get("parties_canonical", [])
        if not cps:
            # No party affiliation — keep the speech (separate from party-attributed).
            filtered[sid] = s
        elif any(p in kept for p in cps):
            # At least one canonical party is large or whitelisted — keep.
            filtered[sid] = s
        # else: all canonical parties are tiny — drop.
    return filtered, kept


def all_unique_raw_groups(speeches: dict) -> list[str]:
    """Return the sorted list of unique non-null raw ``speakerGroup`` values."""
    seen: set[str] = set()
    for s in speeches.values():
        g = s.get("speakerGroup")
        if isinstance(g, str) and g.strip():
            seen.add(g)
    return sorted(seen)


def attach_parties_canonical(speeches: dict, normalizations: dict | None = None) -> None:
    """In-place: ensure every speech has a ``parties_canonical`` list. Idempotent."""
    for s in speeches.values():
        if "parties_canonical" not in s or s["parties_canonical"] is None:
            s["parties_canonical"] = parse_speaker_group(
                s.get("speakerGroup"), normalizations
            )


def attach_text_slot(speeches: dict) -> None:
    """In-place: ensure every speech has a ``text`` key (None for now). The
    Phase 2 text fetcher will fill this in without overwriting other fields.
    """
    for s in speeches.values():
        if "text" not in s:
            s["text"] = None


# ---------------------------------------------------------------------------
# Cross-team: Joe's election-data party list
# ---------------------------------------------------------------------------
# Joe maintains a canonical list of active political parties with EN names
# and abbreviations, used in their election-data analysis. The
# ``jp_party_to_eng`` and ``jp_party_to_abbrv`` dicts in
# ``Joe/src/election_data_cleaning/jp_eng_dicts.py`` are the source of
# truth. We load them here so speech-data analysis can be joined against
# election-data analysis on the canonical JP party name.

def load_joe_party_dicts() -> tuple[dict, dict]:
    """Load Joe's party translation dicts.

    Returns ``(jp_party_to_eng, jp_party_to_abbrv)``. The dicts are loaded
    from ``Joe/src/election_data_cleaning/jp_eng_dicts.py`` via importlib
    so we don't duplicate the data or hard-code Joe's party list in our
    own files.
    """
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    dict_path = (
        repo_root
        / "Joe"
        / "src"
        / "election_data_cleaning"
        / "jp_eng_dicts.py"
    )
    if not dict_path.exists():
        # Joe's file is not present (e.g. running in isolation). Return
        # empty dicts so the rest of the pipeline still works.
        return {}, {}
    spec = importlib.util.spec_from_file_location("joe_jp_eng_dicts", dict_path)
    if spec is None or spec.loader is None:
        return {}, {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return dict(mod.jp_party_to_eng), dict(mod.jp_party_to_abbrv)


def joe_crossref_for_party(party: str) -> dict:
    """Return a dict with Joe's EN name and abbreviation for ``party``.

    The dict has keys ``in_joe_list`` (bool), ``joe_en_name`` (str, may be
    empty), ``joe_abbrv`` (str, may be empty). Parties not in Joe's list
    get ``in_joe_list=False`` and empty strings.
    """
    jp_to_en, jp_to_abbrv = load_joe_party_dicts()
    in_list = party in jp_to_en
    return {
        "in_joe_list": in_list,
        "joe_en_name": jp_to_en.get(party, "") if in_list else "",
        "joe_abbrv": jp_to_abbrv.get(party, "") if in_list else "",
    }


def attach_has_joe_party(speeches: dict) -> None:
    """In-place: ensure every speech has a ``has_joe_party`` boolean.

    True if at least one of the speech's canonical parties is in Joe's
    party list. Useful for filtering at merge time — parties not in
    Joe's list are dropped during the merge, so this flag lets us
    pre-compute which speeches will survive the join without re-running
    the canonicalization.
    """
    jp_to_en, _ = load_joe_party_dicts()
    for s in speeches.values():
        cps = s.get("parties_canonical", [])
        s["has_joe_party"] = any(p in jp_to_en for p in cps)
