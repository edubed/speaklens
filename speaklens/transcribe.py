"""Turn a recording into text, with per-word timings.

Two findings from the DEC-011 spike are baked in here rather than left to the
caller to remember:

  * Audio is normalised before transcription (DEC-017). With weak acoustic
    evidence the decoder leans on its language model and quietly repairs the
    learner's grammar — the failure mode that would silently hollow out the whole
    diagnostic.
  * The model is medium.en (DEC-018). base.en preserves just as many mistakes but
    invents words, and an invented word becomes a mistake wrongly attributed to
    the speaker.

Word timings are always requested: fluency metrics (DEC-010) are built on them and
asking for them later would mean transcribing twice.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

MODEL = "medium.en"
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Transcript:
    text: str
    words: list[Word]
    duration: float
    sentences: list[str]


# Whisper often returns speech as one unpunctuated run, and LanguageTool needs
# sentence boundaries: several of its rules — including ours for articles and
# question word order — only fire at the start of a sentence. Fed the whole run at
# once it silently finds a third fewer mistakes, which is the worst kind of bug
# because the output still looks plausible.
#
# Speakers mark their own boundaries by pausing, but the pause is not where you
# would look for it. Whisper hands back a contiguous timeline — each word's end is
# the next word's start — so silence never appears as a gap. It is absorbed into
# the leading edge of the word that follows it, which is why the words carrying the
# most excess duration here are sentence openers ("he", "she", "my", "where") and
# not sentence closers.
#
# So a boundary is inferred from a word lasting far longer than its own length can
# account for, and the split goes BEFORE that word.
# How long a word "should" take. Not purely proportional to length: every word
# carries a fixed onset regardless of size, so a one-letter "I" would be predicted
# at well under its real ~0.2s and the shortfall would be misread as hesitation.
WORD_ONSET = 0.09
PER_CHAR = 0.055

SILENCE_THRESHOLD = 0.8    # excess seconds that read as a deliberate pause


def expected_duration(text: str) -> float:
    return WORD_ONSET + len(text) * PER_CHAR


def leading_silence(word: Word) -> float:
    """Silence absorbed into this word's span, before it was actually spoken.

    The single definition of "there was a pause here". Sentence splitting and the
    fluency metrics both read pauses, and if they disagreed about what counts as
    one, the report would contradict itself.
    """
    return max(0.0, (word.end - word.start) - expected_duration(word.text))


def split_on_pauses(words: list[Word], threshold: float = SILENCE_THRESHOLD) -> list[str]:
    if not words:
        return []

    sentences, current = [], [words[0].text]
    for word in words[1:]:
        if leading_silence(word) >= threshold and current:
            sentences.append(" ".join(current))
            current = []
        current.append(word.text)
    if current:
        sentences.append(" ".join(current))
    return [s for s in sentences if s.strip()]


def normalize_audio(source: Path) -> Path:
    """Loudness-normalise into a temp file. See DEC-017 — this is not optional."""
    out = Path(tempfile.mkstemp(suffix=".wav", prefix="speaklens-")[1])
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(source),
         "-af", LOUDNORM, "-ar", "16000", "-ac", "1", "-y", str(out)],
        check=True,
    )
    return out


def transcribe(source: Path, model_name: str = MODEL, normalize: bool = True) -> Transcript:
    from faster_whisper import WhisperModel

    audio = normalize_audio(source) if normalize else source
    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio), beam_size=5, word_timestamps=True)

        words: list[Word] = []
        chunks: list[str] = []
        for segment in segments:
            chunks.append(segment.text)
            for w in segment.words or []:
                words.append(Word(w.word.strip(), w.start, w.end))

        return Transcript(
            text=" ".join(chunks).strip(),
            words=words,
            duration=info.duration,
            sentences=split_on_pauses(words),
        )
    finally:
        if normalize:
            audio.unlink(missing_ok=True)
