# SpeakLens

A spoken-English diagnostic that runs **fully offline** on an 8 GB MacBook Air (M1).

Answer five spoken prompts and get back your recurring mistakes grouped by grammatical
theme, an estimated level, and a study plan — with no audio ever leaving the machine and
no API key anywhere.

> **Status:** the end-to-end path works. `python -m speaklens.cli <audio>` records nothing
> yet, but takes a recording and prints classified mistakes. Level estimation, fluency
> metrics and the report UI are not built. See [`docs/daily-plan.md`](docs/daily-plan.md).

```
$ python -m speaklens.cli spike/audio/attempt.wav
transcribing attempt.wav with medium.en ...
  62s of audio in 18s, 71 words

11 mistakes

  [Artículos] 'am engineer' -> am an engineer
      Spanish drops the article before a profession, but English requires one.
      (ES_ARTICLE_JOB_AN)
  [Orden de las palabras] 'where you are' -> where are you
      English questions need the auxiliary before the subject.
      (ES_QUESTION_WORD_ORDER_BE)
  ...

by theme:
   4x  Concordancia sujeto-verbo
   2x  Preposiciones
   2x  Artículos
```

## The idea

Small local models are unreliable grammar judges: a 4B model will confidently "correct"
sentences that were already right. For a B1 learner — who cannot tell the difference —
that is worse than no feedback at all. So the model is never the teacher here. Each layer
does only what it is actually good at.

```
  microphone
      │
      ▼
  loudness normalisation      mandatory, not cosmetic — see below
      │
      ▼
  Whisper medium.en           transcript + per-word timings
      │
      ├─────────────▶  fluency metrics       pauses, fillers, WPM      (planned)
      │
      ├─────────────▶  LanguageTool          rule-based detection
      │                + Spanish L1 rules    no hallucination, ever
      │                       │
      │                       ▼
      │                  theme taxonomy      11 themes, one list feeding
      │                                      explanations, curriculum and ranking
      │
      └─────────────▶  lexical features      CEFR estimate             (planned)
                             │
                             ▼
                          SQLite  ── n=1 → diagnostic
                                  └─ n=N → error map over time
```

The local LLM does not run at request time. Explanations are generated once per rule,
reviewed by hand and frozen into the repo, so nothing is invented while you are using it.

## Three things worth knowing

**Whisper corrects your grammar when it cannot hear you.** The first version of the risk
spike concluded that Whisper silently repairs a learner's mistakes, which would have
hollowed out the whole project. It was an artifact of a quiet recording: with weak
acoustic evidence the decoder leans on its internal language model. On the same speech
normalised to −16 LUFS, 13 of 15 deliberate mistakes survive. Normalisation is therefore
a correctness requirement, not audio polish.

**LanguageTool has no Spanish speakers file, so we wrote one.** It ships
`grammar-l2-de.xml` and `grammar-l2-fr.xml` — rule files for German and French speakers
learning English — and nothing for Spanish, which is why `mother_tongue='es'` does
nothing. Out of the box it caught 9 of 15 typical Spanish-speaker mistakes and was blind
to articles and question word order, the two most characteristic of all.
[`rules/grammar-l2-es.xml`](rules/grammar-l2-es.xml) is the missing file, and coverage on
those sentences is now 11 of 15.

**That 11 of 15 does not survive contact with real speech.** On the first spontaneous
sample — visibly non-native, with a wrong preposition and an abandoned clause — the
detector found nothing at all. Curated test sentences carry one clean, well-delimited
mistake each; real speech produces overlapping errors, half-finished structures and
approximate word choices, which is exactly where a rule-based checker is blind. So
fluency, originally the fallback, is the load-bearing half of the diagnostic, and the
grammar side is reported for what it can actually see.
[The measurements are written up](docs/languagetool-coverage.md), optimistic round
included.

**The pause is not where you would look for it.** Whisper returns speech as one
unpunctuated run, and sentence-anchored rules need sentence starts. Its timeline is
contiguous — each word ends where the next begins — so silence never appears as a gap. It
is absorbed into the leading edge of the following word, which is why the longest words in
a recording are sentence openers, not closers.

## Design decisions

Every non-obvious choice and the reasoning behind it is in
[`docs/decision_log.md`](docs/decision_log.md). The measurements behind them are in
[`docs/languagetool-coverage.md`](docs/languagetool-coverage.md) and
[`docs/prep-week.md`](docs/prep-week.md), including the round of the spike that reached
the wrong conclusion and why it was discarded.

## Running it

Needs Homebrew and Python 3.12.

```bash
brew install ffmpeg openjdk ollama
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/install_rules.py     # add the Spanish L1 rules to LanguageTool
.venv/bin/python -m speaklens.cli path/to/recording.wav
```

`scripts/install_rules.py` edits a file that belongs to LanguageTool, so it keeps a
pristine backup, fences its changes with marker comments, is idempotent, and has
`--remove`. Re-run it after reinstalling LanguageTool.

Recording a sample of your own:

```bash
./spike/record.sh          # prints prompts, records, checks level, normalises
```

## Stack

Python · faster-whisper · LanguageTool · Ollama (build time only) · SQLite
