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
CRUTCH_WORDS = {"like", "well", "so", "actually", "basically"}

# Below this, a gap is ordinary articulation rather than hesitation.
PAUSE_FLOOR = 0.35

# Thresholds for the reading hint. Both are weak, and the code says so where it
# uses them: on the six labelled takes, a fluent speaker's spontaneous English sits
# on the reading side of the pause threshold, and one of them (Joan, 2026-09-02)
# clears the disfluency threshold by a tenth of a point. They are kept only because
# the hint no longer decides anything — the speaker is asked instead.
READING_PAUSE_CEILING = 3.5
DISFLUENCY_FLOOR = 1.5


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
    repeats: int = 0

    @property
    def disfluency_rate(self) -> float:
        """Hesitation markers per hundred words: fillers, crutches and repetitions.

        Speech leaves debris that writing does not — "people people around", "let's
        say", a clause abandoned and restarted. A text read aloud has none of it,
        because the sentence was already solved before the mouth opened.
        """
        return (self.fillers + self.crutches + self.repeats) / max(self.words, 1) * 100

    @property
    def looks_read_aloud(self) -> bool:
        """A hint that this take may have been read. It decides nothing on its own.

        Three versions of this were a gate, and the third died on contact with two
        speakers who were not its author.

        The first counted fillers, on the theory that someone assembling a sentence
        says "uh" while a reader goes quiet. It misfired at once: this speaker
        hesitates silently, an ordinary style, and was told his speech was reading.

        The second asked for lots of silence and no long stop — a slow recital of
        disconnected sentences. Someone who writes their answers and reads them at
        pace produces the opposite profile and sailed straight through.

        The third kept the trait both readings shared: never stopping four seconds
        to find a word. Then the app was handed to two colleagues who speak better
        English than its author, and their spontaneous takes paused for 2.99s and
        2.17s — inside the reading range, between the two real readings at 2.66s
        and 3.27s. Sorted by longest pause, read and spoken interleave. There is no
        threshold, because there is no separation: a fluent speaker does not stop
        to search, so silence cannot tell the two apart.

        Adding disfluency markers narrows it but does not save it. On these six
        takes the readings sit at 1.4 per hundred words and Joan at 1.6 — a
        difference of less than one word in her whole answer.

        So the app now asks the speaker, and this is reduced to a hint that only
        ever appears alongside a declaration it disagrees with. That is why the
        thresholds above are allowed to be weak: a wrong hint costs a sentence in a
        report, where a wrong gate used to cost someone their entire measurement.
        """
        return (
            self.words > 20
            and self.longest_pause < READING_PAUSE_CEILING
            and self.disfluency_rate < DISFLUENCY_FLOOR
        )

    def summary_es(self) -> list[str]:
        """Plain-language readings. Thresholds are rough B1/B2 speaking norms."""
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
        return Fluency(0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0, 0.0, 0, 0)

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
    # A word said twice in a row is a restart, not vocabulary. Whisper keeps them:
    # "people people around", "it was it's going to be".
    repeats = sum(1 for a, b in zip(tokens, tokens[1:]) if a == b and len(a) > 1)

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
        repeats=repeats,
    )
