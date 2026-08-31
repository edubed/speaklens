"""Spanish explanations for detected mistakes, looked up rather than generated.

DEC-021: qwen3:4b took 48 seconds to explain one mistake and said the same thing
every time, because the explanation of a rule does not depend on who was speaking.
So the texts are written once, reviewed, frozen into data/explanations.yaml, and
read from a dictionary at runtime. Nothing is invented while the app is in use.

Three levels of fallback, from most to least specific:

  1. the rule's own Spanish explanation
  2. the theme's why_es — still Spanish, still reviewed, just more general
  3. LanguageTool's English message, which is accurate but not in the learner's
     first language

Level 3 exists because LanguageTool has hundreds of rules and new ones surface as
the app is used. Showing English is worse than showing Spanish, and far better
than showing nothing.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from . import themes as taxonomy

DATA = Path(__file__).resolve().parent.parent / "data" / "explanations.yaml"


@lru_cache(maxsize=1)
def _table(path: Path = DATA) -> dict[str, str]:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {rule: " ".join(text.split()) for rule, text in spec["rules"].items()}


def explain(rule_id: str, theme_id: str, fallback: str = "") -> tuple[str, str]:
    """Return (explanation, source) where source is 'rule', 'theme' or 'languagetool'."""
    specific = _table().get(rule_id)
    if specific:
        return specific, "rule"

    theme = taxonomy.load()[theme_id]
    if theme.why_es and not theme.inbox:
        return theme.why_es, "theme"

    return fallback, "languagetool"


def coverage(rule_ids: set[str]) -> float:
    """Share of the given rules that have a Spanish explanation of their own.

    Worth watching: as unfamiliar rules appear, this drops, and that is the signal
    to write more rather than a reason to let English leak into the report.
    """
    if not rule_ids:
        return 1.0
    return sum(1 for r in rule_ids if r in _table()) / len(rule_ids)
