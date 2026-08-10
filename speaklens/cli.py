"""The walking skeleton (DEC-012): audio in, mistakes out, one command.

Deliberately ugly and terminal-only. Nothing here is meant to be the final report;
the point is that the whole path exists and runs end to end before anything on top
of it gets built.

    python -m speaklens.cli spike/audio/attempt.wav
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from . import detect as detector
from . import themes as taxonomy
from . import transcribe as transcriber


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    audio = Path(args[0])
    if not audio.exists():
        print(f"no such recording: {audio}")
        return 1

    print(f"transcribing {audio.name} with {transcriber.MODEL} ...", flush=True)
    started = time.perf_counter()
    transcript = transcriber.transcribe(audio)
    elapsed = time.perf_counter() - started

    print(f"  {transcript.duration:.0f}s of audio in {elapsed:.0f}s, "
          f"{len(transcript.words)} words\n")
    print(f"  {transcript.text}\n")

    print("detecting ...", flush=True)
    mistakes = detector.detect(transcript.sentences)
    tax = taxonomy.load()

    if not mistakes:
        print("  no mistakes found")
        return 0

    print(f"\n{len(mistakes)} mistakes\n")
    for m in mistakes:
        arrow = f" -> {m.suggestion}" if m.suggestion else ""
        print(f"  [{m.theme_name}] {m.text!r}{arrow}")
        print(f"      {m.message}")
        print(f"      ({m.rule_id})")

    print("\nby theme:")
    for theme_id, count in detector.rank_themes(mistakes):
        theme = tax[theme_id]
        print(f"  {count:>2}x  {theme.name_es}")
        print(f"        {theme.why_es[:100]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
