"""Rebuild every stored session's report with the current renderer.

The audio is deleted after each run and the transcript is not, which turns out to
be the useful half: everything the report shows was already computed and stored, so
a change to the report — or to the level estimate that reads the transcript — can
be applied backwards without asking anyone to record again.

That matters more than it sounds. The four sessions recorded on 2026-09-02 were the
evidence that the level estimate was reading one dimension of a two-dimensional
judgement; without this, the reports those four people were shown would stay wrong
while the fix only reached whoever recorded next.

    .venv/bin/python scripts/rerender.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speaklens import report as reporter          # noqa: E402
from speaklens import storage, themes as taxonomy  # noqa: E402
from speaklens.detect import Mistake              # noqa: E402
from speaklens.fluency import Fluency             # noqa: E402
from speaklens.level import estimate              # noqa: E402
from speaklens.transcribe import Transcript, Word  # noqa: E402


def rebuild(row: sqlite3.Row, mistakes: list[sqlite3.Row], trend) -> Path:
    metrics = json.loads(row["fluency"])
    tax = taxonomy.load()

    # Word timings are gone with the audio, so the transcript carries only what the
    # report actually prints: the text and how many words there were.
    fluency = Fluency(
        words=metrics["words"], speaking_seconds=0.0,
        words_per_minute=metrics["words_per_minute"], pauses=0,
        pauses_per_minute=metrics["pauses_per_minute"],
        longest_pause=metrics["longest_pause"], silence_ratio=metrics["silence_ratio"],
        fillers=metrics["fillers"], crutches=metrics.get("crutches", 0),
        mean_run_length=metrics["mean_run_length"], runs=0,
        repeats=metrics.get("repeats", 0),
    )
    transcript = Transcript(
        text=row["transcript"], words=[Word("", 0.0, 0.0)] * metrics["words"],
        duration=row["duration"], sentences=[],
    )
    rebuilt = [
        Mistake(rule_id=m["rule_id"], theme_id=m["theme_id"],
                theme_name=tax[m["theme_id"]].name_es, text=m["text"],
                suggestion=m["suggestion"], message="",
                offset=max(m["sentence"].find(m["text"]), 0), sentence=m["sentence"])
        for m in mistakes
    ]

    path = reporter.archive_path(row["id"], row["speaker"])
    reporter.write(
        path, session_id=row["id"], speaker=row["speaker"], declared=row["declared"],
        recorded_at=row["created_at"],
        source=row["source"], transcript=transcript, fluency=fluency,
        level=estimate(row["transcript"]), mistakes=rebuilt, trend=trend,
    )
    return path


def main() -> int:
    connection = storage.connect()
    try:
        rows = list(connection.execute("SELECT * FROM sessions ORDER BY id"))
        for row in rows:
            mistakes = list(connection.execute(
                "SELECT * FROM mistakes WHERE session_id = ? ORDER BY id", (row["id"],)))
            trend = storage.fluency_trend(connection, "mean_run_length", speaker=row["speaker"])
            path = rebuild(row, mistakes, trend)
            level = estimate(row["transcript"])
            print(f"  {path.name:<22} {row['speaker'] or 'el dueño':<8} "
                  f"vocabulario={level.label_es:<9} fluidez={json.loads(row['fluency'])['mean_run_length']:.1f}")
    finally:
        connection.close()
    print(f"\n{len(rows)} informes reescritos en {reporter.ARCHIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
