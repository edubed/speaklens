"""The study plan, and which of its units this session touched (DEC-009).

The order of the units is fixed and pedagogical — from what breaks comprehension
to what merely sounds foreign. It is deliberately not sorted by how often the
speaker made each mistake: with partial recall, that order would describe the
detector's coverage rather than the learner (DEC-024).

What is personalised is the highlighting. The report marks the units that cover
mistakes found in this session, without claiming they are the most frequent ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent.parent / "data" / "curriculum.yaml"


@dataclass(frozen=True)
class Unit:
    order: int
    theme_id: str
    title_es: str
    goal_es: str
    rule_es: str
    pairs: list[tuple[str, str]]
    drill_es: str


@lru_cache(maxsize=1)
def load(path: Path = DATA) -> list[Unit]:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        Unit(
            order=u["order"],
            theme_id=u["theme_id"],
            title_es=u["title_es"],
            goal_es=" ".join(u["goal_es"].split()),
            rule_es=" ".join(u["rule_es"].split()),
            pairs=[(a, b) for a, b in u["pairs"]],
            drill_es=" ".join(u["drill_es"].split()),
        )
        for u in sorted(spec["units"], key=lambda u: u["order"])
    ]


def relevant(theme_ids: set[str]) -> list[Unit]:
    """Units covering the themes seen, in curriculum order — never in error order."""
    return [u for u in load() if u.theme_id in theme_ids]


def next_unit(theme_ids: set[str]) -> Unit | None:
    """Where to start: the earliest unit in the plan that this session touched.

    Earliest rather than most-hit, because the plan is built so that later units
    assume the earlier ones. Fixing comparatives before subject-verb agreement
    would be studying out of order.
    """
    hits = relevant(theme_ids)
    return hits[0] if hits else None
