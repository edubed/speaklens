"""Render one session as a local HTML page — the report screen (day 8).

Presentation only. Every number on the page was computed by the modules the CLI
already calls; nothing is recalculated on the way out, and nothing is decided here.
If the page and the terminal ever disagree, this file is the one that is wrong.

Three properties are deliberate:

  * **One file, no requests.** No CDN, no web font, no server. The whole point of
    the project is that it runs with the wifi off (DEC-001), and a report that
    silently needs the network to look right would undo that in the one artifact a
    reviewer actually sees. It is also why this writes a file instead of serving
    one: a static page has no process to start and nothing to explain in the video.

  * **Abstentions are shown, not hidden.** When the sample is too short to place a
    level, or looks recited rather than spoken, the page says so in the same place
    the number would have gone (DEC-023). A blank space would read as a bug; a
    fabricated number would be worse than either.

  * **Mistakes are grouped, never ranked.** The detector finds most of what is
    there, not all of it, so a frequency order would describe its coverage rather
    than the speaker (DEC-024). The page states that ceiling next to the list.

    from speaklens import report
    report.write(Path("report.html"), source=..., transcript=..., ...)
"""

from __future__ import annotations

import html
import webbrowser
from datetime import datetime
from pathlib import Path

from . import curriculum as plan
from . import explain as explainer
from . import themes as taxonomy
from .transcribe import MODEL

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "report.html"
ARCHIVE = Path(__file__).resolve().parent.parent / "reports"


def archive_path(session_id: int | None, speaker: str = "") -> Path:
    """Where this session's report is kept, so the next one does not overwrite it.

    report.html is the latest run and the one the CLI prints; this is the copy that
    survives. It only started mattering when the app was handed to a second person:
    five people in a row used to leave one report.
    """
    who = "".join(c for c in speaker.lower().replace(" ", "-") if c.isalnum() or c == "-")
    name = f"{session_id or 0:03d}" + (f"-{who}" if who else "")
    return ARCHIVE / f"{name}.html"

STYLE = """
:root {
  --bg: #f6f6f4; --card: #ffffff; --ink: #16181d; --dim: #5f6672;
  --line: #e2e3e0; --accent: #2f5d50; --warn: #8a5a12; --warn-bg: #fdf5e6;
  --mark: #b23c2e;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14161a; --card: #1c1f25; --ink: #e8e9ea; --dim: #9aa2ad;
    --line: #2c3038; --accent: #7fc2ad; --warn: #e0b062; --warn-bg: #2a2318;
    --mark: #e08a7c;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2.5rem 1.25rem 5rem;
  background: var(--bg); color: var(--ink);
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}
main { max-width: 46rem; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; letter-spacing: -.01em; }
h2 {
  font-size: .8rem; text-transform: uppercase; letter-spacing: .09em;
  color: var(--dim); margin: 2.5rem 0 .75rem; font-weight: 600;
}
h3 { font-size: 1rem; margin: 0 0 .35rem; }
p { margin: .5rem 0; }
.meta { color: var(--dim); font-size: .85rem; margin: 0 0 .5rem; }
.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 1.1rem 1.25rem; margin-bottom: .75rem;
}
.axes { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
@media (max-width: 30rem) { .axes { grid-template-columns: 1fr; } }
.axis {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 1.1rem 1.25rem;
}
.axis .tag {
  font-size: .72rem; text-transform: uppercase; letter-spacing: .09em;
  color: var(--dim); font-weight: 600; display: block; margin-bottom: .5rem;
}
.axis b { display: block; font-size: 2.4rem; font-weight: 700; line-height: 1;
          letter-spacing: -.03em; color: var(--accent); }
.axis .unit { font-size: .8rem; color: var(--dim); display: block; margin-top: .4rem; }
.axis.quiet b { color: var(--warn); font-size: 1.6rem; }
.level { display: flex; align-items: baseline; gap: 1rem; }
.level .letter { font-size: 3rem; font-weight: 700; line-height: 1; color: var(--accent); }
.abstain {
  background: var(--warn-bg); border-color: color-mix(in srgb, var(--warn) 35%, transparent);
}
.abstain .tag {
  font-size: .72rem; text-transform: uppercase; letter-spacing: .08em;
  color: var(--warn); font-weight: 600; display: block; margin-bottom: .3rem;
}
.grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .5rem; }
@media (max-width: 34rem) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.stat { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: .8rem .9rem; }
.stat b { display: block; font-size: 1.5rem; font-weight: 650; letter-spacing: -.02em; }
.stat span { color: var(--dim); font-size: .78rem; }
ul.read { margin: .75rem 0 0; padding-left: 1.1rem; color: var(--dim); }
ul.read li { margin: .3rem 0; }
.theme + .theme { margin-top: .75rem; }
.why { color: var(--dim); font-size: .88rem; margin: 0 0 .8rem; }
.mistake { border-top: 1px solid var(--line); padding: .7rem 0 .1rem; }
.mistake:first-of-type { border-top: 0; }
.said { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .9rem; }
.said s { color: var(--mark); text-decoration-thickness: 1px; }
.said em { font-style: normal; color: var(--accent); font-weight: 600; }
.ctx {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: .82rem; color: var(--dim); margin-bottom: .2rem;
}
.ctx s { color: var(--mark); text-decoration-thickness: 1px; }
.said .arrow { color: var(--dim); padding: 0 .35rem; }
.mistake p { margin: .3rem 0 0; font-size: .9rem; color: var(--dim); }
.src { font-size: .7rem; text-transform: uppercase; letter-spacing: .06em; color: var(--dim); opacity: .7; }
.pairs { margin: .6rem 0 0; padding: 0; list-style: none; font-size: .9rem; }
.pairs li { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; padding: .12rem 0; }
.later { color: var(--dim); font-size: .85rem; margin-top: .8rem; }
.bar { display: flex; align-items: center; gap: .6rem; font-size: .85rem; margin: .3rem 0; }
.bar .date { color: var(--dim); font-variant-numeric: tabular-nums; min-width: 5.5rem; }
.bar .fill { height: .55rem; border-radius: 3px; background: var(--accent); }
.bar .val { font-variant-numeric: tabular-nums; }
details { color: var(--dim); font-size: .9rem; }
summary { cursor: pointer; color: var(--dim); }
details p { color: var(--ink); margin-top: .6rem; }
footer { margin-top: 3rem; color: var(--dim); font-size: .8rem; border-top: 1px solid var(--line); padding-top: 1rem; }
footer code { font-size: .95em; }
"""


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _card(body: str, *, abstain: bool = False, tag: str = "") -> str:
    label = f'<span class="tag">{_esc(tag)}</span>' if tag else ""
    return f'<div class="card{" abstain" if abstain else ""}">{label}{body}</div>'


def _axes_section(level, fluency, declared: str = "") -> str:
    """The two things a listener is actually adding up, side by side.

    Four colleagues recorded on 2026-09-02 came back with the same level, and the
    person who ranked them could not see why: the one he put first won on
    vocabulary, the one he put last lost on fluency, and the report was showing a
    single letter drawn from the first axis only. A headline that reports one
    dimension of a two-dimensional judgement does not read as incomplete — it
    reads as wrong.
    """
    if level.level is None:
        vocabulario = ('<div class="axis quiet"><span class="tag">Vocabulario</span>'
                       f'<b>—</b><span class="unit">{_esc(level.reason)}</span></div>')
    else:
        vocabulario = ('<div class="axis"><span class="tag">Vocabulario</span>'
                       f'<b>{_esc(level.level)}{"+" if level.saturated else ""}</b>'
                       f'<span class="unit">{level.distinct_words} palabras distintas · '
                       f'puntaje {level.score:.2f}</span></div>')

    if declared == "read":
        fluidez = ('<div class="axis quiet"><span class="tag">Fluidez</span><b>—</b>'
                   '<span class="unit">dijiste que leíste: esto mediría el texto</span></div>')
    else:
        fluidez = ('<div class="axis"><span class="tag">Fluidez</span>'
                   f'<b>{fluency.mean_run_length:.1f}</b>'
                   '<span class="unit">palabras seguidas antes de frenar · '
                   f'pausa más larga {fluency.longest_pause:.1f}s</span></div>')

    return (f'<div class="axes">{vocabulario}{fluidez}</div>'
            '<p class="why">Son dos ejes y no se promedian. Se puede tener vocabulario '
            "amplio y trabarse cada tres palabras, o encadenar largo con pocas palabras. "
            "La letra mide sólo lo primero.</p>")


def _level_section(level) -> str:
    if level.level is None:
        # DEC-023: the missing number is the finding. Say which sample would fix it.
        return _card(f"<p>{_esc(level.reason)}</p>", abstain=True,
                     tag="sin muestra suficiente")

    lines = level.summary_es()
    head, rest = lines[0], lines[1:]
    bands = " · ".join(f"{band} {count}" for band, count in level.band_counts.items() if count)
    body = (
        f"<p>{_esc(head)}</p>"
        f'<p class="meta">bandas de vocabulario: {_esc(bands)}</p>'
        + '<ul class="read">'
        + "".join(f"<li>{_esc(line)}</li>" for line in rest)
        + "</ul>"
    )
    return _card(body)


def _fluency_section(f, declared: str = "") -> str:
    """The metrics, unless the speaker said they read — then they measure the text.

    This used to be decided by a heuristic. It was wrong about two of the first
    three people who ever used the app, both of whom speak fluently enough that
    they never stop to search for a word, which is the only thing silence can see.
    So the app asks, and the heuristic is demoted to a footnote that appears only
    when it disagrees with the answer.
    """
    if declared == "read":
        return _card(
            "<p>Dijiste que leíste alguna de las respuestas, así que estas métricas "
            "describen el texto y no a quien habla: un texto ya resuelto se dice "
            "sin las pausas ni los rearranques que se están midiendo acá.</p>"
            "<p>Para medir fluidez hace falta una toma improvisada. Trabarse no "
            "arruina la medición: <b>es</b> la medición.</p>",
            abstain=True, tag="las métricas miden el texto, no a vos")

    stats = [
        (f"{f.words_per_minute:.0f}", "palabras por minuto"),
        (f"{f.mean_run_length:.1f}", "palabras seguidas antes de frenar"),
        (f"{f.pauses_per_minute:.1f}", "pausas por minuto"),
        (f"{f.longest_pause:.1f}s", "la pausa más larga"),
        (f"{f.silence_ratio:.0%}", "del tiempo en silencio"),
        (f"{f.fillers + f.crutches + f.repeats}", "marcas de duda y rearranques"),
    ]
    cells = "".join(
        f'<div class="stat"><b>{_esc(value)}</b><span>{_esc(label)}</span></div>'
        for value, label in stats
    )
    reading = "".join(f"<li>{_esc(line)}</li>" for line in f.summary_es())

    hint = ""
    if f.looks_read_aloud:
        hint = ('<p class="meta">Este patrón —ninguna pausa larga y casi ningún '
                "rearranque— también lo produce alguien leyendo un texto preparado. "
                "Si improvisaste, ignorá esta línea: es una señal débil, y sobre las "
                "muestras que tenemos se equivoca con hablantes fluidos.</p>")
    return f'<div class="grid">{cells}</div><ul class="read">{reading}</ul>{hint}'
# How much of the surrounding sentence to keep around a marked fragment before
# clipping it. Two passes run over the transcript and the second one checks the
# whole thing as a single chunk, so a mistake's "sentence" is sometimes the entire
# recording — printed whole it would bury the fragment it is meant to locate.
CONTEXT_CHARS = 45


def _context(mistake) -> str:
    """The sentence around the fragment, with the fragment struck out.

    Worth the extra lines: on its own, a match like `do -> does` is unreadable.
    In context — "she do not like it" — the learner can see what the rule saw,
    which is the difference between a correction and a lesson.
    """
    sentence, fragment = mistake.sentence, mistake.text
    start = mistake.offset
    if sentence[start:start + len(fragment)] != fragment:
        start = sentence.find(fragment)          # the offset belonged to another pass
    if start < 0 or not fragment or sentence.strip() == fragment.strip():
        return ""

    end = start + len(fragment)
    before, after = sentence[:start], sentence[end:]
    if len(before) > CONTEXT_CHARS:
        before = "… " + before[-CONTEXT_CHARS:].split(" ", 1)[-1]
    if len(after) > CONTEXT_CHARS:
        after = after[:CONTEXT_CHARS].rsplit(" ", 1)[0] + " …"
    return (f'<div class="ctx">{_esc(before)}<s>{_esc(fragment)}</s>{_esc(after)}</div>')


def _said(mistake) -> str:
    """The correction itself: the fragment, and the replacement when there is one.

    Some rules explain without proposing, because the fix depends on the rest of
    the sentence. Showing an empty arrow there would read as a broken template.
    """
    said = f"<s>{_esc(mistake.text)}</s>"
    if mistake.suggestion:
        said += f'<span class="arrow">→</span><em>{_esc(mistake.suggestion)}</em>'
    return _context(mistake) + f'<div class="said">{said}</div>'


def _mistakes_section(mistakes) -> str:
    if not mistakes:
        return _card("<p>No se encontraron errores en esta grabación. Con una muestra "
                     "corta eso dice más de la muestra que del inglés.</p>")

    tax = taxonomy.load()
    grouped: dict[str, list] = {}
    for m in mistakes:
        grouped.setdefault(m.theme_id, []).append(m)

    blocks = []
    for theme_id, items in grouped.items():
        theme = tax[theme_id]
        rows = []
        for m in items:
            texto, origen = explainer.explain(m.rule_id, m.theme_id, m.message)
            marca = "" if origen == "rule" else f' <span class="src">{_esc(origen)}</span>'
            rows.append(f'<div class="mistake">{_said(m)}'
                        f"<p>{_esc(texto)}{marca}</p></div>")
        blocks.append(_card(
            f"<h3>{_esc(theme.name_es)}</h3>"
            f'<p class="why">{_esc(theme.why_es)}</p>' + "".join(rows)
        ))

    cobertura = explainer.coverage({m.rule_id for m in mistakes})
    nota = ""
    if cobertura < 1.0:
        nota = (f'<p class="meta">{cobertura:.0%} de los errores tienen explicación propia '
                "en español; el resto cae al tema o al mensaje de LanguageTool.</p>")
    return "".join(blocks) + nota


def _plan_section(mistakes) -> str:
    seen = {m.theme_id for m in mistakes}
    unit = plan.next_unit(seen)
    if unit is None:
        return ""

    others = [u for u in plan.relevant(seen) if u is not unit]
    pairs = "".join(
        f'<li><s>{_esc(wrong)}</s><span class="arrow">→</span><em>{_esc(right)}</em></li>'
        for wrong, right in unit.pairs[:3]
    )
    later = ""
    if others:
        nombres = ", ".join(f"{u.order}. {u.title_es}" for u in others)
        later = f'<p class="later">Después, y en este orden: {_esc(nombres)}.</p>'

    return _card(
        f'<p class="meta">Unidad {unit.order} de {len(plan.load())}</p>'
        f"<h3>{_esc(unit.title_es)}</h3>"
        f"<p>{_esc(unit.goal_es)}</p>"
        f'<p class="why">{_esc(unit.rule_es)}</p>'
        f'<ul class="pairs said">{pairs}</ul>'
        f"<p><b>Práctica:</b> {_esc(unit.drill_es)}</p>"
        + later
    )


def _trend_section(trend) -> str:
    """Fluency across sessions — the only thing worth comparing over time (DEC-024)."""
    if len(trend) < 2:
        return ""
    top = max(value for _, value in trend) or 1.0
    bars = "".join(
        f'<div class="bar"><span class="date">{_esc(date)}</span>'
        f'<span class="fill" style="width:{value / top * 70:.1f}%"></span>'
        f'<span class="val">{value:.1f}</span></div>'
        for date, value in trend
    )
    return _card('<h3>Palabras seguidas antes de frenar</h3>'
                 '<p class="why">Sólo grabaciones espontáneas: una lectura en voz alta '
                 'mediría el texto, no a quien habla.</p>' + bars)


def _section(title: str, body: str) -> str:
    return f"<h2>{_esc(title)}</h2>{body}" if body else ""


def render(*, source: str, transcript, fluency, level, mistakes, trend=(),
           speaker: str = "", session_id: int | None = None, declared: str = "",
           recorded_at: str = "") -> str:
    # The date belongs to the recording, not to the render. Rebuilding an old
    # session with a newer report used to stamp it with today, which quietly
    # rewrote when someone had spoken.
    when = (datetime.fromisoformat(recorded_at).astimezone().strftime("%d/%m/%Y %H:%M")
            if recorded_at else datetime.now().strftime("%d/%m/%Y %H:%M"))
    quien = f"{_esc(speaker)} · " if speaker else ""
    header = (
        "<h1>SpeakLens — diagnóstico</h1>"
        f'<p class="meta">{quien}{_esc(source)} · {transcript.duration:.0f}s · '
        f"{len(transcript.words)} palabras · {_esc(when)}</p>"
    )
    body = "".join([
        header,
        _section("Cómo sonás", _axes_section(level, fluency, declared)),
        _section("Vocabulario, en detalle", _level_section(level)),
        _section("Fluidez, en detalle", _fluency_section(fluency, declared)),
        _section("Errores encontrados", _mistakes_section(mistakes)),
        _section("Por dónde empezar", _plan_section(mistakes)),
        _section("Entre sesiones", _trend_section(trend)),
        _section("Lo que dijiste", "<details><summary>Ver la transcripción</summary>"
                 f"<p>{_esc(transcript.text)}</p></details>"),
        "<footer>"
        f"<p>Transcripción local con Whisper <code>{_esc(MODEL)}</code>; errores detectados "
        "por LanguageTool con 28 reglas propias de hispanohablante; explicaciones escritas "
        "y revisadas de antemano. Ningún modelo de lenguaje decide qué está mal, y nada "
        "de esto sale de esta máquina.</p>"
        "<p>El detector encuentra 88 de cada 100 errores marcados a mano, y acierta en el "
        "97% de lo que marca. Esta lista es lo que se pudo detectar con seguridad, no un "
        "perfil completo de tu inglés.</p>"
        "</footer>",
    ])
    return (
        "<!doctype html>\n"
        '<html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>SpeakLens — diagnóstico</title>"
        f"<style>{STYLE}</style></head><body><main>{body}</main></body></html>\n"
    )


def write(path: Path = DEFAULT_PATH, *, open_browser: bool = False,
          archive_as: Path | None = None, **session) -> Path:
    html = render(**session)
    path.write_text(html, encoding="utf-8")
    if archive_as is not None:
        archive_as.parent.mkdir(parents=True, exist_ok=True)
        archive_as.write_text(html, encoding="utf-8")
    if open_browser:
        webbrowser.open(path.resolve().as_uri())
    return path
