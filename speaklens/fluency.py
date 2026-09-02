"""Measure how fluently someone speaks, from word timings alone.

This is the half of the diagnostic that grammar cannot reach (DEC-010). "Trabarse
al hablar" is not a grammatical defect: you can produce flawless sentences and
still be unusable in a meeting because each one takes eight seconds to assemble.

It is also the robust half. These numbers come from timings rather than from what
the transcriber thought it heard, so they survive the failure modes that threaten
the grammar side — a mistake silently repaired, or a word invented.

Pauses are read the way transcribe.split_on_pauses reads them: Whisper's timeline
is contiguous, so silence is absorbed into the leading edge of the word that
follows it rather than appearing as a gap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .transcribe import Word, leading_silence

# Hesitation sounds, plus the discourse crutches learners lean on while assembling
# the next clause. "like" and "so" are ordinary words too, so they are counted but
# reported separately from the unambiguous ones.
UNAMBIGUOUS_FILLERS = {"uh", "um", "erm", "eh", "mmm", "hmm", "ah", "er"}
CRUTCH_WORDS = {"like", "well", "so", "actually", "basically", "you know"}

# Below this, a gap is ordinary articulation rather than hesitation.
PAUSE_FLOOR = 0.35

# A silence longer than this is someone hunting for a word, not someone turning a
# page. Reading produces regular short gaps between sentences; nothing in reading
# produces a four-second stop.
READING_PAUSE_CEILING = 4.0

# The second reading style, and the one that got through. Prepared prose read at
# pace has almost no silence in it and long uninterrupted runs — the opposite
# profile to a slow recital, and indistinguishable from excellent spontaneous
# speech by the pause test alone.
PROSE_SILENCE_CEILING = 0.35
PROSE_RUN_FLOOR = 3.0


@dataclass(frozen=True)
class Fluency:
    words: int
    speaking_seconds: float
    words_per_minute: float
    pauses: int
    pauses_per_minute: float
    longest_pause: float
    silence_ratio: float
    fillers: int
    crutches: int
    mean_run_length: float
    runs: int

    @property
    def looks_read_aloud(self) -> bool:
        """Whether this sample is probably someone reading, not speaking freely.

        These metrics only mean something on spontaneous speech. Read your answers
        off a screen and every number describes the text instead of the speaker,
        and the report goes on to diagnose a person who was never measured.

        Three versions, and it is worth keeping why each failed.

        The first counted fillers, on the theory that someone assembling a sentence
        says "uh" while someone reading just goes quiet. It misfired immediately:
        this speaker hesitates silently, which is an ordinary style, and got told
        his spontaneous speech was reading.

        The second asked for a lot of silence and no long stop, which describes a
        slow recital of disconnected sentences. It missed the case that matters.
        Someone who writes their answers first and reads them at pace produces the
        opposite profile — 30% silence, runs of three and a half words — and sailed
        through as excellent spontaneous speech. That sample is the labelled one
        now: the speaker said afterwards that he had written the answers.

        So there are two reading styles and one shared trait: neither ever stops
        for four seconds to find a word. That is the test. The prose clause is the
        second signal, for a fluent read whose longest pause lands above the
        ceiling anyway.

        The test is deliberately eager. Flagging real spontaneous speech costs the
        speaker a re-recording and says why; missing a read take makes the whole
        report quietly wrong about a person. DEC-023 prefers the loud failure.
        """
        if self.words <= 20:
            return False
        searched_for_a_word = self.longest_pause >= READING_PAUSE_CEILING
        reads_like_prose = (
            self.silence_ratio < PROSE_SILENCE_CEILING
            and self.mean_run_length > PROSE_RUN_FLOOR
        )
        return not searched_for_a_word or reads_like_prose

    def summary_es(self) -> list[str]:
        """Plain-language readings. Thresholds are rough B1/B2 speaking norms."""
        if self.looks_read_aloud:
            porque = (
                f"encadenás {self.mean_run_length:.1f} palabras sin frenar y sólo "
                f"{self.silence_ratio:.0%} del tiempo es silencio, que es el ritmo de "
                "un texto escrito"
                if self.silence_ratio < PROSE_SILENCE_CEILING
                else f"nunca frenás más de {self.longest_pause:.1f}s, y buscar una "
                     "palabra lleva más que eso"
            )
            return [
                f"Esta grabación parece leída, no hablada: {porque}.",
                "Las métricas de fluidez no son válidas acá — medirían el texto, no a "
                "quien habla. Hacen falta respuestas improvisadas: trabarte es el dato.",
            ]

        lines = []
        if self.words_per_minute < 90:
            lines.append(f"Hablás a {self.words_per_minute:.0f} palabras por minuto. "
                         "Un hablante cómodo ronda 120-150.")
        elif self.words_per_minute > 170:
            lines.append(f"Hablás a {self.words_per_minute:.0f} palabras por minuto, muy rápido. "
                         "Puede ser nervios más que fluidez.")
        else:
            lines.append(f"Ritmo de {self.words_per_minute:.0f} palabras por minuto, dentro de lo normal.")

        if self.mean_run_length < 6:
            lines.append(f"Decís {self.mean_run_length:.1f} palabras seguidas antes de frenar. "
                         "Ahí es donde se nota que te trabás.")
        else:
            lines.append(f"Encadenás {self.mean_run_length:.1f} palabras antes de frenar.")

        if self.silence_ratio > 0.30:
            lines.append(f"El {self.silence_ratio:.0%} del tiempo es silencio. "
                         "Estás armando la frase mientras hablás.")

        if self.fillers:
            lines.append(f"{self.fillers} muletillas de duda (uh, um). "
                         "Aparecen justo donde te falta la palabra.")
        return lines


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z']", "", text.lower())


def measure(words: list[Word]) -> Fluency:
    if not words:
        return Fluency(0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0, 0.0, 0)

    total_seconds = words[-1].end - words[0].start

    silences = [leading_silence(w) for w in words[1:]]
    pauses = [s for s in silences if s >= PAUSE_FLOOR]
    silence_total = sum(pauses)

    # A run is an uninterrupted stretch of words between pauses — the closest thing
    # to "how much can you say before you have to stop and think".
    runs, current = [], 1
    for silence in silences:
        if silence >= PAUSE_FLOOR:
            runs.append(current)
            current = 0
        current += 1
    runs.append(current)

    tokens = [_normalize(w.text) for w in words]
    fillers = sum(1 for t in tokens if t in UNAMBIGUOUS_FILLERS)
    crutches = sum(1 for t in tokens if t in CRUTCH_WORDS)

    speaking = max(total_seconds - silence_total, 1e-6)
    minutes = max(total_seconds / 60, 1e-6)

    return Fluency(
        words=len(words),
        speaking_seconds=speaking,
        words_per_minute=len(words) / (speaking / 60),
        pauses=len(pauses),
        pauses_per_minute=len(pauses) / minutes,
        longest_pause=max(pauses, default=0.0),
        silence_ratio=silence_total / max(total_seconds, 1e-6),
        fillers=fillers,
        crutches=crutches,
        mean_run_length=sum(runs) / len(runs),
        runs=len(runs),
    )
