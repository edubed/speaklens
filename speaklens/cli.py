"""The walking skeleton (DEC-012): audio in, mistakes out, one command.

The terminal output stays as it was built — deliberately ugly, and the thing that
proves the path exists end to end. Since day 8 the same run also writes report.html,
which is the version a person reads (and the one the video shows).

    python -m speaklens.cli spike/audio/attempt.wav
    python -m speaklens.cli spike/audio/attempt.wav --open
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from . import curriculum as plan
from . import detect as detector
from . import explain as explainer
from . import fluency as fluency_meter
from . import level as level_estimator
from . import report as reporter
from . import storage
from . import themes as taxonomy
from . import transcribe as transcriber


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    flags = {a for a in args if a.startswith("-")}
    recordings = [a for a in args if not a.startswith("-")]
    if not recordings:
        print(__doc__)
        return 1

    audio = Path(recordings[0])
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

    f = fluency_meter.measure(transcript.words)
    print("fluidez:")
    print(f"  {f.words_per_minute:5.0f}  palabras por minuto")
    print(f"  {f.mean_run_length:5.1f}  palabras seguidas antes de frenar ({f.runs} tramos)")
    print(f"  {f.pauses_per_minute:5.1f}  pausas por minuto (la mayor, {f.longest_pause:.1f}s)")
    print(f"  {f.silence_ratio:5.0%}  del tiempo en silencio")
    print(f"  {f.fillers:5d}  muletillas de duda, {f.crutches} de relleno")
    for line in f.summary_es():
        print(f"    - {line}")
    print()

    level = level_estimator.estimate(transcript.text)
    print("nivel:")
    for line in level.summary_es():
        print(f"    - {line}")
    print()

    print("detecting ...", flush=True)
    mistakes = detector.detect(transcript.sentences)
    tax = taxonomy.load()

    if not mistakes:
        print("  no mistakes found")
        trend = _persist(audio, transcript, f, level, mistakes)
        _write_report(audio, transcript, f, level, mistakes, trend, flags)
        return 0

    print(f"\n{len(mistakes)} errores\n")
    for m in mistakes:
        arrow = f" -> {m.suggestion}" if m.suggestion else ""
        texto, origen = explainer.explain(m.rule_id, m.theme_id, m.message)
        marca = "" if origen == "rule" else f"  [{origen}]"
        print(f"  [{m.theme_name}] {m.text!r}{arrow}")
        print(f"      {texto}{marca}")

    cobertura = explainer.coverage({m.rule_id for m in mistakes})
    if cobertura < 1.0:
        print(f"\n  ({cobertura:.0%} de los errores tienen explicación propia en español;"
              " el resto cae al tema o al mensaje de LanguageTool)")

    # Agrupado, nunca ordenado por frecuencia: con ~27% de recall un ranking
    # ordenaría nuestros puntos ciegos, no las debilidades del hablante (DEC-024).
    print("\npor tema — esto es lo que pudimos detectar con seguridad,")
    print("no un perfil completo de tu inglés:")
    grouped: dict[str, list] = {}
    for m in mistakes:
        grouped.setdefault(m.theme_id, []).append(m)
    for theme_id, items in grouped.items():
        theme = tax[theme_id]
        print(f"\n  {theme.name_es}")
        print(f"    {theme.why_es[:110]}")
        for m in items:
            # Algunas reglas explican sin proponer un reemplazo, porque la corrección
            # depende del resto de la frase. En ese caso vale más el mensaje que un signo.
            if m.suggestion:
                print(f"      · {m.text!r} -> {m.suggestion}")
            else:
                print(f"      · {m.text!r}: {m.message}")

    seen = {m.theme_id for m in mistakes}
    unit = plan.next_unit(seen)
    if unit is not None:
        others = [u for u in plan.relevant(seen) if u is not unit]
        print(f"\npor dónde empezar — unidad {unit.order} de {len(plan.load())}:")
        print(f"  {unit.title_es}")
        print(f"    {unit.goal_es}")
        print(f"    {unit.rule_es}")
        for wrong, right in unit.pairs[:3]:
            print(f"      {wrong}  ->  {right}")
        print(f"    práctica: {unit.drill_es}")
        if others:
            nombres = ", ".join(f"{u.order}. {u.title_es}" for u in others)
            print(f"\n  después, y en este orden: {nombres}")

    trend = _persist(audio, transcript, f, level, mistakes)
    _write_report(audio, transcript, f, level, mistakes, trend, flags)
    return 0


def _write_report(audio, transcript, f, level, mistakes, trend, flags) -> None:
    """The report screen (day 8). The CLI stays the source of truth for the numbers;
    report.py only lays them out."""
    path = reporter.write(
        open_browser="--open" in flags,
        source=audio.name,
        transcript=transcript,
        fluency=f,
        level=level,
        mistakes=mistakes,
        trend=trend,
    )
    print(f"\ninforme: {path}")


def _persist(audio, transcript, f, level, mistakes) -> list[tuple[str, float]]:
    connection = storage.connect()
    try:
        storage.save(
            connection,
            source=audio.name,
            duration=transcript.duration,
            transcript=transcript.text,
            fluency=f,
            level=level,
            mistakes=mistakes,
        )
        history = storage.fluency_trend(connection, "mean_run_length")
        if len(history) > 1:
            print("\npalabras seguidas antes de frenar, por sesión:")
            for date, value in history:
                print(f"  {date}  {value:.1f}  {'#' * int(value * 3)}")
        return history
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
