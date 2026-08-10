"""Estimate a CEFR level from measurable properties of the text (DEC-005).

Asking a 4B model "what level is this?" returns a plausible letter and no way to
defend it. What can be defended is vocabulary: which frequency bands a speaker
actually reaches. Someone at A2 builds sentences almost entirely from the thousand
commonest words; reaching for less common ones is what moving up looks like.

Two sources, cross-checked when the data was added: the CEFR-J profile maps 7,798
headwords to a level, and wordfreq supplies Zipf frequencies for everything else.
Median Zipf falls monotonically across A1→B2 in the profile, so the two agree.

Known ceilings, both stated in the report rather than hidden:

  * CEFR-J stops at B2, so C1 and C2 are indistinguishable here.
  * Vocabulary is one dimension of a level, not the whole of it. Someone can know
    B2 words and assemble them badly, which is why this runs beside the fluency
    metrics rather than instead of them.
"""

from __future__ import annotations

import csv
import re
import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROFILE = Path(__file__).resolve().parent.parent / "data" / "cefrj-vocabulary-profile-1.5.csv"

LEVELS = ["A1", "A2", "B1", "B2"]
RANK = {level: i for i, level in enumerate(LEVELS)}

# Zipf bands for words the profile does not list. A Zipf of 5 appears about once
# per ten thousand words; 3 is roughly once per million.
ZIPF_BANDS = [(5.0, "A1"), (4.4, "A2"), (3.8, "B1")]

# Below this the estimate is noise: a handful of words cannot locate anyone on a
# scale. DEC-023 — say nothing rather than say something unsupportable.
#
# Chosen by checking where the estimate separates: an A2-style paragraph of ~50
# distinct words lands 45 of them in the A1 band with 4% above A2, while a B2-style
# one of similar length spreads across all four bands with 59% above A2. Below
# roughly forty the median swings on a couple of words. This is a judgement made
# against two samples, not a power analysis, and should be revisited once real
# five-prompt sessions exist to check it against.
MIN_CONTENT_WORDS = 40

# Function words carry no level signal. Everyone says "the" at every level, so
# including them would drag every estimate toward A1 in proportion to how much the
# speaker hesitated rather than to what they know.
FUNCTION_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "at", "for",
    "with", "from", "by", "as", "is", "am", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "not", "no", "so", "very", "then", "there", "here",
    "what", "when", "where", "who", "how", "why", "will", "would", "can", "could",
    "should", "may", "might", "must", "about", "okay", "ok", "yes",
}


@dataclass(frozen=True)
class LevelEstimate:
    level: str | None
    content_words: int
    distinct_words: int
    type_token_ratio: float
    band_counts: dict[str, int]
    above_a2_ratio: float
    reason: str

    def summary_es(self) -> list[str]:
        if self.level is None:
            return [self.reason]
        lines = [
            f"Nivel estimado por vocabulario: {self.level}.",
            f"{self.content_words} palabras de contenido, {self.distinct_words} distintas "
            f"(riqueza léxica {self.type_token_ratio:.2f}).",
            f"El {self.above_a2_ratio:.0%} de lo que decís está por encima de A2.",
        ]
        if self.band_counts.get("B2"):
            lines.append(f"Usaste {self.band_counts['B2']} palabras de banda B2.")
        lines.append("Mide vocabulario, no gramática: se lee junto a la fluidez, no en su lugar.")
        return lines


@lru_cache(maxsize=1)
def _profile(path: Path = PROFILE) -> dict[str, str]:
    levels: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            level = row["CEFR"].strip()
            if level not in RANK:
                continue
            for form in row["headword"].strip().lower().split("/"):
                form = form.strip()
                # Keep the easiest listing: a word a learner meets at A1 is an A1
                # word even if a rarer sense of it is catalogued higher.
                if form and (form not in levels or RANK[level] < RANK[levels[form]]):
                    levels[form] = level
    return levels


def _band(word: str) -> str:
    listed = _profile().get(word)
    if listed:
        return listed

    from wordfreq import zipf_frequency

    zipf = zipf_frequency(word, "en")
    if zipf == 0.0:
        return "B2"          # unknown to both sources: treat as rare, not as missing
    for floor, level in ZIPF_BANDS:
        if zipf >= floor:
            return level
    return "B2"


def _content_words(text: str) -> list[str]:
    tokens = re.findall(r"[a-z']+", text.lower())
    return [t for t in tokens if len(t) > 1 and t not in FUNCTION_WORDS]


def estimate(text: str) -> LevelEstimate:
    words = _content_words(text)
    distinct = sorted(set(words))

    if len(words) < MIN_CONTENT_WORDS:
        return LevelEstimate(
            level=None,
            content_words=len(words),
            distinct_words=len(distinct),
            type_token_ratio=0.0,
            band_counts={},
            above_a2_ratio=0.0,
            reason=(
                f"Muestra insuficiente para estimar nivel: {len(words)} palabras de "
                f"contenido, hacen falta {MIN_CONTENT_WORDS}. Respondé más consignas."
            ),
        )

    bands = [_band(w) for w in distinct]
    counts = {level: bands.count(level) for level in LEVELS}
    above_a2 = sum(counts[l] for l in ("B1", "B2")) / len(bands)

    # The median band of the distinct vocabulary, nudged up when a substantial part
    # of it sits above A2 — reaching for less common words is the thing that
    # distinguishes the level, and a median alone would hide it.
    median_rank = statistics.median(RANK[b] for b in bands)
    rank = int(median_rank) + (1 if above_a2 >= 0.5 else 0)

    return LevelEstimate(
        level=LEVELS[min(rank, len(LEVELS) - 1)],
        content_words=len(words),
        distinct_words=len(distinct),
        type_token_ratio=len(distinct) / len(words),
        band_counts=counts,
        above_a2_ratio=above_a2,
        reason="",
    )
