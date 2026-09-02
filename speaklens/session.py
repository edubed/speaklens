"""One recording in, one analysed session out — the pipeline both front ends run.

Extracted when the browser UI arrived. Until then the order of the steps lived
inside cli.py, and a second caller would have had to repeat it: transcribe, then
measure, then estimate, then detect, then store. Repeating an order is how two
front ends start disagreeing about what a session is — one forgets to persist, the
other forgets that the level estimate reads the transcript and not the audio.

The steps themselves stay where they were. This only owns the sequence, and the
fact that a session is those five things together.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import detect as detector
from . import fluency as fluency_meter
from . import level as level_estimator
from . import storage
from . import transcribe as transcriber
from .detect import Mistake
from .fluency import Fluency
from .level import LevelEstimate
from .transcribe import Transcript

# Trim silence off both ends of a clip before it is joined to the next one.
# Without this, the gap between "I stopped talking" and "I pressed stop" becomes a
# pause inside the recording, and the fluency metrics would be measuring reaction
# time to a button. start_periods=1 only ever removes the leading run, so silence
# *inside* the answer — which is the actual signal (DEC-010) — is left alone; the
# reverse-trim-reverse is how the same filter reaches the tail.
TRIM_EDGES = (
    "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB,areverse,"
    "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB,areverse"
)


@dataclass(frozen=True)
class Analysis:
    session_id: int | None
    speaker: str
    source: str
    transcript: Transcript
    fluency: Fluency
    level: LevelEstimate
    mistakes: list[Mistake]
    trend: list[tuple[str, float]]


def analyze(audio: Path, *, speaker: str = "", persist: bool = True,
            on_step: Callable[[str, Any], None] = lambda step, data=None: None) -> Analysis:
    """Run the whole diagnostic over one recording.

    `on_step` reports progress with whatever is ready at that point — "transcribe"
    and "detect" before the two slow steps, "transcribed" and "measured" with their
    results. It exists so a caller can narrate the wait without this module knowing
    whether it is talking to a terminal or to a browser, and so the terminal can
    keep printing each result the moment it exists rather than all at the end.
    """
    on_step("transcribe", None)
    transcript = transcriber.transcribe(audio)
    on_step("transcribed", transcript)

    fluency = fluency_meter.measure(transcript.words)
    level = level_estimator.estimate(transcript.text)
    on_step("measured", (fluency, level))

    on_step("detect", None)
    mistakes = detector.detect(transcript.sentences)

    session_id: int | None = None
    trend: list[tuple[str, float]] = []
    if persist:
        connection = storage.connect()
        try:
            session_id = storage.save(
                connection,
                source=audio.name,
                duration=transcript.duration,
                transcript=transcript.text,
                fluency=fluency,
                level=level,
                mistakes=mistakes,
                speaker=speaker,
            )
            # Scoped to this speaker: a line that walks across several people
            # answers nobody's question about whether they are improving.
            trend = storage.fluency_trend(connection, "mean_run_length", speaker=speaker)
        finally:
            connection.close()

    return Analysis(
        session_id=session_id,
        speaker=speaker,
        source=audio.name,
        transcript=transcript,
        fluency=fluency,
        level=level,
        mistakes=mistakes,
        trend=trend,
    )


def join(clips: list[Path], destination: Path) -> Path:
    """Concatenate answers into the single recording the diagnostic reads.

    The five prompts are five takes but one measurement: the level estimate needs
    forty content words and no single answer reaches that (DEC-008, DEC-023). They
    are joined rather than analysed one by one for the same reason a test is scored
    whole and not question by question.

    Each clip is decoded to the mono 16 kHz Whisper wants and edge-trimmed first,
    so the joins add no silence the speaker did not produce.
    """
    if not clips:
        raise ValueError("no clips to join")

    staged: list[Path] = []
    for index, clip in enumerate(clips):
        out = destination.parent / f"{destination.stem}-{index}.wav"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(clip),
             "-af", TRIM_EDGES, "-ar", "16000", "-ac", "1", "-y", str(out)],
            check=True,
        )
        staged.append(out)

    listing = Path(tempfile.mkstemp(suffix=".txt", prefix="speaklens-concat-")[1])
    listing.write_text("".join(f"file '{p}'\n" for p in staged), encoding="utf-8")
    try:
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "concat",
             "-safe", "0", "-i", str(listing), "-c", "copy", "-y", str(destination)],
            check=True,
        )
    finally:
        listing.unlink(missing_ok=True)
        for path in staged:
            path.unlink(missing_ok=True)
    return destination
