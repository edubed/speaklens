"""Pin the estimators to real measurements.

DEC-023: heuristics answer to samples, not to intuition. Both thresholds here were
originally set by intuition and both were wrong — the read-aloud test called
spontaneous speech a recital, and the level estimator demanded more words than a
whole session produces. Pinning the samples means the next person to adjust a
threshold has to explain what it does to these.

Deliberately dependency-free, so it runs with no test framework installed:

    .venv/bin/python tests/check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speaklens.fluency import Fluency          # noqa: E402
from speaklens.level import estimate, score_from_counts   # noqa: E402

failures: list[str] = []


def check(name: str, got: object, want: object) -> None:
    if got != want:
        failures.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if got == want else 'FAIL'} {name}: {got!r}")


# Six takes whose kind is known, four of them because someone watched them being
# recorded. Every threshold in looks_read_aloud answers to these six and nothing else.
#
# Fields: words, speaking_seconds, wpm, pauses, pauses/min, longest_pause,
#         silence_ratio, fillers, crutches, mean_run_length, runs, repeats

# 2026-08-09. Fifteen unrelated sentences read aloud with deliberate pauses.
READ_SLOWLY = Fluency(71, 0, 158.8, 28, 27.6, 2.66, 0.54, 0, 1, 2.54, 28, 0)

# 2026-09-01. Answers written out first and then read at pace — the opposite
# profile to a recital, and the take that killed the second version of the test.
READ_AS_PROSE = Fluency(141, 0, 116.3, 43, 23.1, 3.27, 0.30, 0, 2, 3.44, 41, 0)

# 2026-08-09. Thirty-nine seconds unscripted, with one 12.3s stop while searching
# for a word. No fillers: this speaker hesitates silently, which broke version one.
SPONTANEOUS_SHORT = Fluency(26, 0, 142.8, 12, 19.8, 12.28, 0.67, 0, 0, 2.17, 12, 0)

# 2026-09-01. Ninety seconds unscripted. Only its 4.10s pause keeps it off the
# reading side — its disfluency rate, 1.43, is lower than both readings above.
SPONTANEOUS_LONG = Fluency(70, 0, 127.1, 27, 22.9, 4.10, 0.59, 0, 1, 2.19, 32, 0)

# 2026-09-02. Two colleagues, both speaking better English than the author, both
# recorded with him in the room, so their kind is not inferred but witnessed.
# They are why the test stopped being a gate: neither ever pauses long enough to
# look like speech, because neither has to search for the word.
FLUENT_ALE = Fluency(353, 0, 158.3, 73, 22.3, 2.99, 0.31, 0, 12, 4.84, 73, 3)
FLUENT_JOAN = Fluency(314, 0, 147.4, 81, 25.3, 2.17, 0.33, 0, 5, 3.88, 81, 0)

check("a slow recital hints at reading", READ_SLOWLY.looks_read_aloud, True)
check("written answers read at pace hint at reading", READ_AS_PROSE.looks_read_aloud, True)
check("a searching pause rules reading out", SPONTANEOUS_SHORT.looks_read_aloud, False)
check("so does a 4.1s one", SPONTANEOUS_LONG.looks_read_aloud, False)
check("a fluent speaker is not called a reader", FLUENT_ALE.looks_read_aloud, False)
check("nor a fluent speaker with few markers", FLUENT_JOAN.looks_read_aloud, False)

# The two margins holding those six apart, written down because they are thin
# enough that anyone touching a threshold has to see them first. Sorted by longest
# pause, read and spoken interleave — 2.17 spoken, 2.66 read, 2.99 spoken, 3.27
# read — so the pause alone cannot separate them, and each spontaneous take is
# rescued by a different clause. This is a hint, never a verdict.
check("Joan clears the disfluency floor by a tenth of a point",
      round(FLUENT_JOAN.disfluency_rate, 2), 1.59)
check("both readings sit just under it", 
      [round(READ_SLOWLY.disfluency_rate, 2), round(READ_AS_PROSE.disfluency_rate, 2)],
      [1.41, 1.42])

A2_TEXT = """
I like my job. I work in an office with my friends. Every day I go to work by bus
and I arrive at nine. I eat lunch at one with my brother. In the evening I watch
television with my family and then I go to sleep. On Saturday I play football and
we have dinner together at home. I like music and I listen to songs on my phone.
My mother cooks very good food. I want to buy a new car next year because my old
car is broken. My sister lives in another city and I visit her sometimes.
"""

B2_TEXT = """
The most challenging aspect of the migration was coordinating deployment across
several independent teams whose priorities frequently conflicted. We eventually
established a shared release calendar, which reduced friction considerably,
although negotiating the initial agreement required substantial patience and a
willingness to compromise on scheduling decisions. Retrospectively, the technical
difficulties proved far less demanding than the organisational ones, and I suspect
that is generally true of infrastructure projects undertaken by distributed
organisations facing competing commercial deadlines.
"""

a2, b2 = estimate(A2_TEXT), estimate(B2_TEXT)
check("simple text does not read as B2", a2.level in {"A1", "A2"}, True)
check("dense text reads as B2", b2.level, "B2")
check("the two are separated", a2.above_a2_ratio < 0.2 < b2.above_a2_ratio, True)

# The first real answer produced twelve content words. Estimating a level from that
# would be exactly the failure DEC-023 exists to prevent.
short = estimate("Okay, I work in the project Plata Juntos. This project is designed for me")
check("a short sample yields no level", short.level, None)

# B2 is the top of the list, not a reading: CEFR-J has nothing above it, so the
# label has to say the scale ran out instead of implying a measurement.
check("the top of the scale says it is a ceiling", b2.label_es, "B2 o más")

# Session 4, written out and read aloud on 2026-09-01. Under the median rule this
# text came back A2 while containing architectures, relocation and stabilize — the
# common-word mass outvoted the tail. It must land above A2 now.
SESSION_4 = """
Looking back, the last project I finished was an automated internal processing
pipeline. We built custom workflows, architectures and deployed them directly to
production. The hardest part was handling unexpected file formats, so we decided to
implement strict validation rules first. Overall, it took me about three weeks to
stabilize the system and deliver it with full operation visibility. If a company in
Madrid offered me a job tomorrow, I would move after the initial losses.
"""
prose = estimate(SESSION_4)
check("dense prose is no longer read as A2", prose.level in {"B1", "B2"}, True)

# Words neither source has ever seen are transcription artefacts or proper nouns,
# not advanced vocabulary. Counting them as B2 inflated the ratio that decides the
# level — two invented words were 6% of a real session's distinct vocabulary.
noise = estimate(A2_TEXT + " canility milanesas zzzqx")
check("unknown words are dropped, not banded as B2", noise.unknown_words, 3)
check("dropping them does not move the level", noise.level, a2.level)

# Vocabulary profiles of two of the four colleagues recorded on 2026-09-02, kept as
# counts rather than text: the finding is the distribution, and the words were
# theirs. Their listener, who was in the room, ranked the first of these speakers
# best of the four and the second worst.
#
# The previous rule counted only vocabulary above A2 and put them at 14.9% and
# 15.2% — a tie, in the wrong order, with all four colleagues inside one band. The
# difference between these two speakers is 30 A2 words against 13, exactly what a
# cut above A2 throws away, and it is where spoken English varies at all.
RANKED_FIRST = {"A1": 50, "A2": 30, "B1": 7, "B2": 7}
RANKED_LAST = {"A1": 65, "A2": 13, "B1": 9, "B2": 5}

check("the old cut ranked them backwards",
      round((7 + 7) / 94, 3) < round((9 + 5) / 92, 3), True)
check("the score puts them in the order the listener heard",
      score_from_counts(RANKED_FIRST) > score_from_counts(RANKED_LAST), True)
check("and separates them by more than a rounding error",
      round(score_from_counts(RANKED_FIRST) - score_from_counts(RANKED_LAST), 2), 0.06)

print()
if failures:
    print(f"{len(failures)} failed")
    for line in failures:
        print(f"  {line}")
    raise SystemExit(1)
print("all checks passed")
