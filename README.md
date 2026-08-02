# SpeakLens

A spoken-English diagnostic that runs **fully offline** on an 8 GB MacBook Air (M1).

Speak for two minutes and get back an estimated CEFR level, your recurring mistakes ranked by
frequency, and a study plan — with no audio ever leaving the machine.

> **Status:** pre-alpha. Validating the core technical risk before building. See
> [`docs/prep-week.md`](docs/prep-week.md).

## Why this exists

Small local models are unreliable grammar judges: a 4B model will confidently "correct" sentences
that were already right. For a B1 learner — who cannot tell the difference — that is worse than no
feedback at all. So SpeakLens never asks the model to be the teacher. Each layer does only what it
is actually good at:

```
  microphone
      │
      ▼
  Whisper (local)          transcription + word-level timestamps
      │
      ├──────────────▶  fluency metrics        pauses, fillers, WPM  (deterministic)
      │
      ├──────────────▶  LanguageTool           error detection       (rule-based, no hallucination)
      │                        │
      │                        ▼
      │                   local LLM            explains a known error in Spanish
      │
      └──────────────▶  lexical/syntactic      CEFR level estimate   (frequency bands, TTR, MLU)
                        features
                             │
                             ▼
                          SQLite  ── n=1 → diagnostic report
                                  └─ n=N → error map over time
```

The level estimate is **computed**, not guessed by the model.

## Design decisions

Every non-obvious choice, and the reasoning behind it, is recorded in
[`docs/decision_log.md`](docs/decision_log.md).

## Stack

Python · FastAPI · faster-whisper · LanguageTool · Ollama · SQLite
