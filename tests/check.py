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
from speaklens.level import estimate           # noqa: E402

failures: list[str] = []


def check(name: str, got: object, want: object) -> None:
    if got != want:
        failures.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if got == want else 'FAIL'} {name}: {got!r}")


# Measured 2026-08-09. Fifteen unrelated sentences read aloud with deliberate
# pauses; worst gap 2.7s. The metrics must refuse to interpret this.
READ_ALOUD = Fluency(71, 0, 159, 28, 27.6, 2.7, 0.54, 0, 1, 2.5, 28)

# Measured 2026-08-09. Thirty-nine seconds answering prompt 1 unscripted, with one
# 12.3s stop while searching for a word. No fillers at all — this speaker pauses
# silently, which is what broke the first version of the test.
SPONTANEOUS = Fluency(26, 0, 143, 12, 19.8, 12.3, 0.67, 0, 0, 2.2, 12)

check("read-aloud take is detected as reading", READ_ALOUD.looks_read_aloud, True)
check("spontaneous take is not called reading", SPONTANEOUS.looks_read_aloud, False)

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

print()
if failures:
    print(f"{len(failures)} failed")
    for line in failures:
        print(f"  {line}")
    raise SystemExit(1)
print("all checks passed")
