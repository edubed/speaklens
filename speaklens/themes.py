"""Load the theme taxonomy and classify LanguageTool matches into it.

The taxonomy (data/themes.yaml) is the single list behind three things: the Spanish
explanations, the curriculum units, and the error ranking. Classifying here keeps
every consumer reading from the same source.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DATA = Path(__file__).resolve().parent.parent / "data" / "themes.yaml"


@dataclass(frozen=True)
class Theme:
    id: str
    name_es: str
    priority: int
    why_es: str
    noise: bool
    inbox: bool


class Taxonomy:
    def __init__(self, spec: dict[str, Any]) -> None:
        self._themes: dict[str, Theme] = {}
        self._by_rule: dict[str, str] = {}
        self._by_category: dict[str, str] = {}
        self._inbox_id = "otros"

        for entry in spec["themes"]:
            theme = Theme(
                id=entry["id"],
                name_es=entry["name_es"],
                priority=entry["priority"],
                why_es=" ".join(entry.get("why_es", "").split()),
                noise=bool(entry.get("noise")),
                inbox=bool(entry.get("inbox")),
            )
            self._themes[theme.id] = theme
            if theme.inbox:
                self._inbox_id = theme.id
            for rule in entry.get("rules") or []:
                self._by_rule[rule] = theme.id
            for category in entry.get("categories") or []:
                self._by_category[category] = theme.id

    def classify(self, rule_id: str, category: str) -> Theme:
        """Rule id wins over category: it is the more specific signal."""
        theme_id = self._by_rule.get(rule_id) or self._by_category.get(category)
        return self._themes[theme_id or self._inbox_id]

    def __getitem__(self, theme_id: str) -> Theme:
        return self._themes[theme_id]

    @property
    def themes(self) -> list[Theme]:
        return sorted(self._themes.values(), key=lambda t: t.priority)


@lru_cache(maxsize=1)
def load(path: Path = DATA) -> Taxonomy:
    return Taxonomy(yaml.safe_load(path.read_text(encoding="utf-8")))
