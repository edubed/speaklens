"""Measure how much of a learner's real speech the detector actually catches.

DEC-022 was raised on a 26-word sample where LanguageTool found nothing. That was
enough to suspect, not enough to conclude. This runs the detector over annotated
learner speech — five spontaneous answers with the mistakes marked by hand — and
reports recall and precision.

A mistake counts as caught only when its character span overlaps the annotated
one. The first version of this compared substrings, which scored the single-letter
'a' from a/an as a hit inside "since March" and "I have many problems", and put
recall 18 points too high. Positions do not lie.

    .venv/bin/python tests/recall.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speaklens.detect import detect  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "learner_speech.yaml"


def overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def main() -> int:
    spec = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))

    caught = expected = spurious = 0
    for sample in spec["samples"]:
        sentences = sample["sentences"]
        found = detect(sentences)
        useful: set[int] = set()
        results = []

        for fragment in sample["expect"]:
            host = next((s for s in sentences if fragment in s), None)
            if host is None:
                results.append((fragment, "BAD-ANNOTATION"))
                continue
            start = host.find(fragment)
            target = (start, start + len(fragment))

            hit = False
            for i, m in enumerate(found):
                if m.sentence != host:
                    continue
                if overlaps(target, (m.offset, m.offset + len(m.text))):
                    hit = True
                    useful.add(i)
            results.append((fragment, hit))

        hits = sum(1 for _, r in results if r is True)
        caught += hits
        expected += len(results)
        spurious += len(found) - len(useful)

        print(f"\n--- {sample['prompt']}: {hits}/{len(results)}")
        for fragment, result in results:
            label = "ok   " if result is True else "blind" if result is False else result
            print(f"   {label} {fragment}")

    print(f"\n{'=' * 56}")
    precision = caught / max(caught + spurious, 1)
    print(f"recall:    {caught}/{expected} = {caught / expected:.0%}")
    print(f"precision: {precision:.0%} ({spurious} marks matched no annotated mistake)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
