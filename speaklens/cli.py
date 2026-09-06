"""The walking skeleton (DEC-012): audio in, mistakes out, one command.

The terminal output stays as it was built — deliberately ugly, and the thing that
proves the path exists end to end. Since day 8 the same run also writes report.html,
which is the version a person reads (and the one the video shows).

The order of the steps lives in speaklens.session, not here: the browser UI runs
the same sequence, and a duplicated sequence is how two front ends start disagreeing
about what a session is.

    python -m speaklens.cli spike/audio/attempt.wav
    python -m speaklens.cli spike/audio/attempt.wav --open
    python -m speaklens.cli otra.wav --speaker=juan     # otra persona, otro histórico
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from . import curriculum as plan
from . import explain as explainer
from . import report as reporter
from . import session as pipeline
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

    speaker = next((f.split("=", 1)[1] for f in flags if f.startswith("--speaker=")), "")
    # The web UI asks; on the command line you say it yourself, or say nothing.
    declared = "read" if "--read" in flags else "improvised" if "--improvised" in flags else ""
    analysis = pipeline.analyze(audio, speaker=speaker, declared=declared,
                                on_step=_printer(declared))
    mistakes = analysis.mistakes
    tax = taxonomy.load()

    if not mistakes:
        print("  no mistakes found")
        _write_report(analysis, flags)
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

    # Agrupado, nunca ordenado por frecuencia: con recall parcial un ranking
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

    if len(analysis.trend) > 1:
        print("\npalabras seguidas antes de frenar, por sesión:")
        for date, value in analysis.trend:
            print(f"  {date}  {value:.1f}  {'#' * int(value * 3)}")

    _write_report(analysis, flags)
    return 0


def _printer(declared: str = ""):
    """Print each result the moment it exists, rather than all of them at the end.

    Whisper takes about a third of the recording's length, so a run that printed
    nothing until it was done would look hung for half a minute.

    The declaration is honoured here too. It used to be read only by the report,
    so a run marked --read printed "this is where you get stuck" in the terminal
    and "these numbers describe the text" in the browser, from the same numbers.
    """
    started = time.perf_counter()

    def on_step(step: str, data=None) -> None:
        nonlocal started
        if step == "transcribe":
            started = time.perf_counter()
            print(f"transcribing with {transcriber.MODEL} ...", flush=True)
        elif step == "transcribed":
            elapsed = time.perf_counter() - started
            print(f"  {data.duration:.0f}s of audio in {elapsed:.0f}s, "
                  f"{len(data.words)} words\n")
            print(f"  {data.text}\n")
        elif step == "measured":
            f, level = data
            print("fluidez:")
            print(f"  {f.words_per_minute:5.0f}  palabras por minuto")
            print(f"  {f.mean_run_length:5.1f}  palabras seguidas antes de frenar ({f.runs} tramos)")
            print(f"  {f.pauses_per_minute:5.1f}  pausas por minuto (la mayor, {f.longest_pause:.1f}s)")
            print(f"  {f.silence_ratio:5.0%}  del tiempo en silencio")
            print(f"  {f.fillers:5d}  muletillas de duda, {f.crutches} de relleno")
            if declared == "read":
                print("    - Dijiste que leíste: estos números describen el texto, no a")
                print("      quien habla. No se interpretan.")
            else:
                for line in f.summary_es():
                    print(f"    - {line}")
            print("\nnivel:")
            for line in level.summary_es():
                print(f"    - {line}")
            print()
        elif step == "detect":
            print("detecting ...", flush=True)

    return on_step


def _write_report(analysis, flags) -> None:
    """The report screen (day 8). The pipeline stays the source of truth for the
    numbers; report.py only lays them out."""
    path = reporter.write(
        open_browser="--open" in flags,
        archive_as=reporter.archive_path(analysis.session_id, analysis.speaker),
        session_id=analysis.session_id,
        speaker=analysis.speaker,
        declared=analysis.declared,
        source=analysis.source,
        transcript=analysis.transcript,
        fluency=analysis.fluency,
        level=analysis.level,
        mistakes=analysis.mistakes,
        trend=analysis.trend,
    )
    print(f"\ninforme: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
