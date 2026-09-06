# SpeakLens

A spoken-English diagnostic that runs **fully offline** on an 8 GB MacBook Air (M1).

Answer five spoken prompts and get back your recurring mistakes grouped by grammatical
theme, an estimated level, and a study plan — with no audio ever leaving the machine and
no API key anywhere.

> **Status:** everything below runs. Recording is guided by a local page, transcription,
> fluency, level, detection, the Spanish explanations and the study plan are built, `setup.sh`
> takes a clone to a working install, and seven real sessions have been recorded — four of
> them by other people, which is where most of the interesting bugs came from. The two-minute
> demo video is the one thing still missing. See [`docs/daily-plan.md`](docs/daily-plan.md).

```
$ python -m speaklens.cli spike/audio/attempt.wav --read
transcribing with medium.en ...
  62s of audio in 17s, 71 words

  yesterday I go to the meeting last week she buy a new laptop I didn't went to
  the party she don't like the project he have two brothers my friends is coming
  tomorrow I have 32 years old ...

fluidez:
    159  palabras por minuto
    2.5  palabras seguidas antes de frenar (28 tramos)
    54%  del tiempo en silencio
    - Dijiste que leíste: estos números describen el texto, no a
      quien habla. No se interpretan.

nivel:
    - Muestra insuficiente para estimar nivel: 33 palabras de contenido,
      hacen falta 40. Respondé más consignas.

14 errores

  [Tiempos verbales] 'yesterday I go' -> went
      En español alcanza con decir "ayer" y dejar el verbo en presente. El inglés
      marca el pasado en el verbo igual: "yesterday I WENT".
  [Concordancia sujeto-verbo] 'do' -> does
      Con he, she o it el verbo lleva -s en presente. Y en negativo esa -s se muda
      al auxiliar: no es "she don't like" sino "she doesn't like".
```

Two refusals in one run, and both are the point: the sample was declared as read aloud, so
the fluency numbers are shown but not interpreted, and it is too short to place a level, so
no level is given. The mistakes are real either way — those come from rules, not from timing.

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
      ├─────────────▶  fluency metrics       pauses, fillers, WPM
      │
      ├─────────────▶  LanguageTool          rule-based detection
      │                + Spanish L1 rules    no hallucination, ever
      │                       │
      │                       ▼
      │                  theme taxonomy      11 themes, one list feeding
      │                                      explanations and curriculum
      │
      └─────────────▶  lexical features      CEFR estimate, or an honest
                             │                refusal below 40 content words
                             │
                             ▼
                          SQLite  ── mistakes listed, never ranked
                             │    └─ fluency compared across sessions
                             ▼
                        report.html   one static file, no CDN and no
                                      request — see DEC-025

  both front ends — the terminal and the guided browser recorder — run the same
  sequence from speaklens/session.py, so they cannot disagree about a session
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
those sentences is now 14 of 15.

**Curated sentences flattered it, so recall got measured properly.** Against 32 mistakes
annotated by hand in realistic spontaneous learner speech, the detector started at 27%
recall — real speech produces overlapping errors and half-finished clauses, not the one
clean mistake per sentence a test set contains. Twenty-four more rules took it to **88%
recall at 97% precision**, with zero false positives on correct English. The tense rules
inflect their own suggestions, so "Yesterday I go" is answered with "went".

Four blind spots remain and are [documented as out of reach](docs/languagetool-coverage.md)
rather than left pending: two of them need to know that the previous sentence was in the
past, which is the ceiling of any rule-based system.

**Two colleagues broke the read-aloud detector on the first day it left my laptop.**
Fluency metrics only mean something on spontaneous speech, so a heuristic guarded them: no
reading of any kind stops for four seconds to search for a word. It held across every
recording I made and misfired on both of the first two people who used it — both of whom
speak better English than I do, and therefore never stop to search. Sorted by longest pause,
the labelled takes interleave: 2.17s spoken, 2.66s read, 2.99s spoken, 3.27s read. There is
no threshold because there is no separation. The app asks the speaker now, and the heuristic
survives as a footnote that appears only when it disagrees with the answer.

**A listener adds up two things, so the report stopped reporting one.** Four colleagues
recorded in one afternoon came back with the same level, and the person who had listened to
all four could not see why. He was right: the one he ranked first wins on vocabulary, and the
one he ranked last loses on fluency — 2.85 words between pauses against 4.84, and a seven
second stop where nobody else exceeds three. The report was showing a single letter drawn
from the axis that varies least in speech. It leads with both now.

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

Needs Homebrew and Python 3.12. One command, about 1.9 GB of downloads the first time:

```bash
./setup.sh
```

It installs ffmpeg and a JDK, creates the virtualenv, pulls Whisper `medium.en` and
LanguageTool, injects the Spanish L1 rules into it, and then proves the detector is armed
by asking it to catch a mistake only those rules can catch. It does not install Ollama:
the explanations were generated once and frozen into the repo, so nothing needs a model
server at run time.

Then either front end. The guided one, which is the one to use for a real diagnostic:

```bash
.venv/bin/python -m speaklens.web        # opens http://127.0.0.1:8000
```

One prompt at a time, timed, with a live microphone level — it exists because the first
real session came back with three of the five prompts unanswered, which is not a cosmetic
problem: the level estimate abstained two words short of its threshold. Or the terminal,
on a recording you already have:

```bash
.venv/bin/python -m speaklens.cli path/to/recording.wav --open
```

The run prints the diagnosis to the terminal and writes `report.html` next to it — level,
fluency, every mistake shown inside the sentence you said it in with an explanation in
Spanish, and the unit of the study plan to start from. `--open` opens it in the browser.
The file is gitignored: like the database, it holds a transcript of your own voice.

`scripts/install_rules.py` edits a file that belongs to LanguageTool, so it keeps a
pristine backup, fences its changes with marker comments, is idempotent, and has
`--remove`. Upgrading LanguageTool restores its own rule files and takes ours with it,
which drops recall from 88% to 27% with no error and no clue — `./setup.sh --check`
detects exactly that, and re-running `./setup.sh` fixes it.

Recording a sample of your own:

```bash
./spike/record.sh          # prints prompts, records, checks level, normalises
```

## Stack

Python · faster-whisper · LanguageTool · Ollama (build time only) · SQLite
