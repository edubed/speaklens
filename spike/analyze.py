"""
DEC-011 spike: does Whisper silently fix your grammar while transcribing?

Whisper is trained to produce fluent, well-formed text, so it may "helpfully" correct
the very mistakes SpeakLens needs to detect. If it corrects too many, the grammar
diagnostic cannot work and the project pivots to fluency metrics (DEC-010).

The first run of this spike (5 sentences) confirmed the risk is real but could not size
it: all models corrected "she don't like" and "I am agree", while preserving "I go to
meeting" and "I have 32 years old". That suggested a hypothesis worth testing properly:

    Whisper corrects mistakes whose correction is a high-frequency collocation,
    and preserves mistakes whose correction is not.

This version tests 15 sentences across 6 error categories to characterise WHICH classes
of mistake survive, rather than producing a single pass/fail number.

PRE-REGISTERED CRITERIA (fixed before running; do not renegotiate after seeing results):

    GO       >= 8/15 survive     build the diagnostic, scoped to surviving categories
    PARTIAL   5-7/15 survive     build, but the README states which classes are detected
    STOP     <= 4/15 survive     pivot to fluency metrics only (DEC-010)

Regexes deliberately tolerate dropped articles and other unstressed function words,
which the transcriber omits often enough to cause false negatives. They do NOT tolerate
substitutions that change the error being tested — a misheard word counts as NOT FOUND,
never as a surviving mistake.

Usage:
    python spike/analyze.py --print-script    show the sentences to read aloud
    python spike/analyze.py [audio.wav]       transcribe and score
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# An initial_prompt full of disfluent, ungrammatical text biases Whisper toward
# transcribing literally (mitigation #1 in DEC-011). base.en tests mitigation #2:
# a smaller model does less language modelling, so it may "help" less.
VERBATIM_PROMPT = (
    "um so yeah i think he don't know, uh, she go there yesterday and, "
    "like, we was talking about it, you know"
)

CONDITIONS = [
    ("base.en", None),
    ("small.en", None),
    ("small.en", VERBATIM_PROMPT),
    ("medium.en", None),
]


@dataclass(frozen=True)
class Case:
    n: int
    category: str
    spoken: str
    error: str       # regex matching the mistake as spoken
    corrected: str   # regex matching Whisper having fixed it


CASES = [
    # Main-verb tense. The correct forms are common but the wrong ones are not
    # obviously "repairable" without changing meaning, so these should survive.
    Case(1, "verb tense", "Yesterday I go to the meeting",
         r"\bi go to (?:the )?meeting\b", r"\bi went to (?:the )?meeting\b"),
    Case(2, "verb tense", "Last week she buy a new laptop",
         r"\bshe buy\b", r"\bshe bought\b"),
    Case(3, "verb tense", "I didn't went to the party",
         r"\bdidn'?t went\b", r"\bdidn'?t go\b"),

    # Subject-verb agreement. Corrections here are extremely frequent n-grams,
    # so the hypothesis predicts Whisper will fix these.
    Case(4, "agreement", "She don't like the project",
         r"\bshe don'?t like\b", r"\bshe doesn'?t like\b"),
    Case(5, "agreement", "He have two brothers",
         r"\bhe have\b", r"\bhe has\b"),
    Case(6, "agreement", "My friends is coming tomorrow",
         r"\bfriends is\b", r"\bfriends are\b"),

    # Calques from Spanish. Lexically odd in English, so no strong pull toward a fix.
    Case(7, "calque", "I have thirty two years old",
         r"\bi have (?:\w+[\s-]){0,3}years\b", r"\bi(?:'m| am) (?:\w+[\s-]){0,3}years\b"),
    Case(8, "calque", "I am agree with you",
         r"\bi(?:'m| am) agree\b", r"\bi agree\b"),
    Case(9, "calque", "I have hungry",
         r"\bi have hungry\b", r"\bi(?:'m| am) hungry\b"),

    # Prepositions. Short unstressed words, so watch for NOT FOUND from audio issues.
    Case(10, "preposition", "Explain me the problem",
         r"\bexplain me\b", r"\bexplain to me\b"),
    Case(11, "preposition", "I depend of my parents",
         r"\bdepend of\b", r"\bdepend on\b"),
    Case(12, "preposition", "She arrived to the airport",
         r"\barrived to\b", r"\barrived (?:at|in)\b"),

    # Articles. Whisper inserting a missing article would be a clear normalisation.
    Case(13, "article", "I am engineer",
         r"\bi(?:'m| am) engineer\b", r"\bi(?:'m| am) an engineer\b"),
    Case(14, "article", "The life is difficult",
         r"\bthe life is\b", r"\blife is\b"),

    # Word order in questions.
    Case(15, "word order", "Where you are going?",
         r"\bwhere you are going\b", r"\bwhere are you going\b"),
]

PRESERVED, CORRECTED, MISSING = "PRESERVED", "CORRECTED", "NOT FOUND"
MARK = {PRESERVED: "OK", CORRECTED: "fix", MISSING: "?"}


def normalize(text: str) -> str:
    """Lowercase, straighten apostrophes, drop other punctuation, collapse spaces."""
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9'\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify(case: Case, transcript: str) -> str:
    if re.search(case.error, transcript):
        return PRESERVED
    if re.search(case.corrected, transcript):
        return CORRECTED
    return MISSING


def print_script() -> None:
    print("\n  Read these aloud WITH the mistakes, exactly as written.")
    print("  Pause about a second between sentences. Normal voice, normal speed.\n")
    for case in CASES:
        print(f"   {case.n:>2}. {case.spoken}")
    print()


def transcribe(model_name: str, prompt: str | None, audio: Path) -> tuple[str, float]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    started = time.perf_counter()
    segments, _ = model.transcribe(str(audio), beam_size=5, initial_prompt=prompt)
    text = " ".join(segment.text for segment in segments)
    return text, time.perf_counter() - started


def report_by_category(verdicts: list[str]) -> None:
    print(f"\n{'BY CATEGORY (best condition)':<28}{'kept':>12}")
    print("-" * 40)
    seen: dict[str, list[str]] = {}
    for case, verdict in zip(CASES, verdicts):
        seen.setdefault(case.category, []).append(verdict)
    for category, results in seen.items():
        kept = results.count(PRESERVED)
        bar = "".join(MARK[r].ljust(4) for r in results)
        print(f"{category:<20}{bar:<12}{kept}/{len(results)}")


def main() -> int:
    if "--print-script" in sys.argv:
        print_script()
        return 0

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    audio = Path(args[0]) if args else Path(__file__).parent / "audio" / "attempt.wav"
    if not audio.exists():
        print(f"No recording at {audio}\nRun spike/record.sh first.")
        return 1

    results: dict[str, list[str]] = {}

    for model_name, prompt in CONDITIONS:
        condition = f"{model_name}{' + verbatim prompt' if prompt else ''}"
        print(f"\n{'=' * 78}\n{condition}\n{'=' * 78}")
        print("loading model (first run downloads it)...", flush=True)

        text, elapsed = transcribe(model_name, prompt, audio)
        transcript = normalize(text)
        print(f"transcribed in {elapsed:.1f}s\n\n  {text.strip()}\n")

        verdicts = [classify(case, transcript) for case in CASES]
        results[condition] = verdicts

        for case, verdict in zip(CASES, verdicts):
            print(f"  [{MARK[verdict]:^3}] {case.n:>2}. {case.category:<14} {verdict}")

    print(f"\n{'=' * 78}\nSUMMARY\n{'=' * 78}\n")
    header = f"{'condition':<30}" + "".join(f"{c.n:^4}" for c in CASES) + f"{'kept':>8}"
    print(header)
    print("-" * len(header))

    best_condition, best_kept = "", -1
    for condition, verdicts in results.items():
        kept = verdicts.count(PRESERVED)
        if kept > best_kept:
            best_condition, best_kept = condition, kept
        marks = "".join(f"{MARK[v]:^4}" for v in verdicts)
        print(f"{condition:<30}{marks}{kept:>6}/{len(CASES)}")

    report_by_category(results[best_condition])

    print(f"\n{'-' * len(header)}")
    print(f"Best condition: {best_condition} with {best_kept}/{len(CASES)} mistakes preserved.\n")

    if best_kept >= 8:
        print("VERDICT: GO. The grammar diagnostic is viable.")
        print("Scope it to the categories that survive; state the blind spots in the README.")
    elif best_kept >= 5:
        print("VERDICT: PARTIAL. Build it, but only for the categories that survive.")
        print("The README must say plainly which error classes SpeakLens cannot see.")
    else:
        print("VERDICT: STOP. Whisper normalizes too much for a grammar diagnostic.")
        print("Pivot to fluency metrics only (DEC-010) — already designed, and immune to this.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
