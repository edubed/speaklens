"""
DEC-011 spike: does Whisper silently fix your grammar while transcribing?

Whisper is trained to produce fluent, well-formed text, so it may "helpfully" correct
the very mistakes SpeakLens needs to detect. If it does, the grammar diagnostic cannot
work and the project pivots to fluency metrics (DEC-010).

This script transcribes one recording under three conditions and reports, for each
deliberate mistake, whether it survived transcription.

Usage:  python spike/analyze.py [path/to/audio.wav]
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

# An initial_prompt full of disfluent, ungrammatical text biases Whisper toward
# transcribing literally. This is mitigation #1 in DEC-011, tested here for free.
VERBATIM_PROMPT = (
    "um so yeah i think he don't know, uh, she go there yesterday and, "
    "like, we was talking about it, you know"
)

CONDITIONS = [
    ("small.en", None),
    ("small.en", VERBATIM_PROMPT),
    ("medium.en", None),
]


@dataclass(frozen=True)
class Case:
    n: int
    label: str
    spoken: str
    error: str       # regex matching the mistake as spoken
    corrected: str   # regex matching Whisper having fixed it


CASES = [
    Case(1, "past simple", "Yesterday I go to the meeting",
         r"\bi go to the meeting\b", r"\bi went to the meeting\b"),
    Case(2, "calque (age)", "I have thirty two years old",
         r"\bi have (?:\w+[\s-]){0,3}years\b", r"\bi(?:'m| am) (?:\w+[\s-]){0,3}years\b"),
    Case(3, "agreement", "She don't like the project",
         r"\bshe don'?t like\b", r"\bshe doesn'?t like\b"),
    Case(4, "calque (agree)", "I am agree with you",
         r"\bi(?:'m| am) agree\b", r"\bi agree with you\b"),
    Case(5, "missing preposition", "Explain me the problem",
         r"\bexplain me\b", r"\bexplain to me\b"),
]

PRESERVED, CORRECTED, MISSING = "PRESERVED", "CORRECTED", "NOT FOUND"


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


def transcribe(model_name: str, prompt: str | None, audio: Path) -> tuple[str, float]:
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    started = time.perf_counter()
    segments, _ = model.transcribe(str(audio), beam_size=5, initial_prompt=prompt)
    text = " ".join(segment.text for segment in segments)
    return text, time.perf_counter() - started


def main() -> int:
    audio = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "audio" / "attempt.wav"
    if not audio.exists():
        print(f"No recording at {audio}\nRun spike/record.sh first.")
        return 1

    results: dict[str, list[str]] = {}

    for model_name, prompt in CONDITIONS:
        condition = f"{model_name}{' + verbatim prompt' if prompt else ''}"
        print(f"\n{'=' * 72}\n{condition}\n{'=' * 72}")
        print("loading model (first run downloads it)...", flush=True)

        text, elapsed = transcribe(model_name, prompt, audio)
        transcript = normalize(text)

        print(f"transcribed in {elapsed:.1f}s\n")
        print(f"  {text.strip()}\n")

        verdicts = [classify(case, transcript) for case in CASES]
        results[condition] = verdicts

        for case, verdict in zip(CASES, verdicts):
            mark = {PRESERVED: "OK ", CORRECTED: "FIX", MISSING: " ? "}[verdict]
            print(f"  [{mark}] {case.n}. {case.label:<22} {verdict}")

    print(f"\n{'=' * 72}\nSUMMARY\n{'=' * 72}\n")
    header = f"{'condition':<32}" + "".join(f"{c.n:^5}" for c in CASES) + f"{'kept':>7}"
    print(header)
    print("-" * len(header))

    best = 0
    for condition, verdicts in results.items():
        kept = verdicts.count(PRESERVED)
        best = max(best, kept)
        marks = "".join(
            f"{ {PRESERVED: 'OK', CORRECTED: 'fix', MISSING: '?'}[v] :^5}" for v in verdicts
        )
        print(f"{condition:<32}{marks}{kept:>5}/5")

    print(f"\n{'-' * len(header)}")
    if best >= 3:
        print(f"VERDICT: GO. {best}/5 mistakes survived — the grammar diagnostic is viable.")
        print("Use the best-scoring condition as the default transcription setting.")
    else:
        print(f"VERDICT: STOP. Only {best}/5 mistakes survived. Whisper is normalizing your speech.")
        print("Next mitigations, in order (DEC-011):")
        print("  2. Try a smaller model (base.en/tiny.en) — less language modeling, less 'help'.")
        print("  3. Pivot ASR to wav2vec2 with CTC greedy decoding, which transcribes literally.")
        print("  4. Pivot the product to fluency metrics only (DEC-010) — already designed.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
