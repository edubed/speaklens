# SpeakLens — Handoff

**Última actualización:** 2026-09-02 · **Autor:** Edu Bedini (+ Claude)
**Fase:** Ejecución · **Estado:** ▶ activo, días 0–9 de 10 completos + UI guiada (DEC-026)
**Retomá acá →** §7: queda el **día 10** — README final, video de 2 minutos y hacer el repo público. Todo lo técnico está construido y hay dos preguntas abiertas de medición en §8 que valen más que cualquier feature nueva.

---

## 1. TL;DR

SpeakLens es un **diagnóstico de inglés hablado que corre 100% offline** en una MacBook Air
M1 de 8 GB. Grabás respuestas a cinco consignas y devuelve tus errores agrupados por tema
con explicación en español, métricas de fluidez, un nivel estimado y por dónde empezar a
estudiar. El objetivo real **no es aprender inglés sino portfolio** (DEC-001): ataca dos de
los tres bloqueantes de la búsqueda laboral en España — GitHub vacío e inglés B1.

El camino corre punta a punta hoy: `python -m speaklens.cli <audio>` normaliza, transcribe,
mide fluidez, estima nivel, detecta errores, los explica, guarda la sesión y escribe
`report.html` — un archivo estático, sin servidor y sin una sola llamada de red. Cualquiera
que clone el repo lo pone a andar con `./setup.sh`. Falta sólo el día 10: el video de 2
minutos, que es el entregable final.

---

## 2. Qué es esto

- **Repo**: `~/dev/personal/speaklens` — GitHub `edubed/speaklens`, remote `github-personal`.
  El host `github-personal` de `~/.ssh/config` apunta a la clave de la cuenta personal; la
  máquina tiene más de una cuenta de GitHub configurada, así que el remote no es `github.com`.
- **Máquina**: MacBook Air M1, **8 GB**. La restricción de RAM define casi todo el diseño.
- **Para quién**: Edu, hispanohablante en B1 que apunta a AI/Automation Engineer remoto.
- **Por qué offline**: es el argumento del portfolio. Correr entero sin red en 8 GB es lo
  diferenciado; con una API sería un chatbot más (DEC-001).

La arquitectura clave, en una línea: **el LLM nunca decide qué está mal.** LanguageTool
detecta (determinístico), el código calcula, y los textos en español están escritos y
congelados en el repo. Un modelo de 4B juzgando gramática alucina, y el usuario está en B1
y no podría detectarlo (DEC-004).

---

## 3. Qué se hizo

| Día | Entregable | Archivos |
|---|---|---|
| 0 | Instalaciones + spike de riesgo | `spike/analyze.py`, `spike/record.sh` |
| 1 | Reglas propias de hispanohablante para LanguageTool | `rules/grammar-l2-es.xml`, `scripts/install_rules.py` |
| 2 | Esqueleto caminante punta a punta | `speaklens/cli.py`, `transcribe.py`, `detect.py`, `themes.py` |
| 3 | Métricas de fluidez | `speaklens/fluency.py` |
| 4 | Estimación de nivel CEFR | `speaklens/level.py`, `data/cefrj-vocabulary-profile-1.5.csv` |
| 5 | Persistencia en SQLite | `speaklens/storage.py` |
| 6 | Plan de estudio de 9 unidades | `data/curriculum.yaml`, `speaklens/curriculum.py` |
| 7 | Explicaciones en español por regla | `data/explanations.yaml`, `speaklens/explain.py` |
| 8 | Pantalla del informe | `speaklens/report.py` (+ `--open` en `cli.py`) |
| 9 | Instalación reproducible | `setup.sh` |
| — | UI guiada de grabación (fuera del plan de 10 días) | `speaklens/web.py`, `speaklens/recorder.html`, `speaklens/session.py` |

**Números actuales, todos reproducibles:**

- Detector: **88% recall, 97% precisión**, 0 falsos positivos sobre inglés correcto
  (`.venv/bin/python tests/recall.py`)
- 28 reglas propias de errores de hispanohablante (LanguageTool no trae archivo para español)
- 14/15 en las frases del spike original
- 40 explicaciones en español cubriendo las 35 reglas que disparan en la práctica
- El informe pesa ~13 KB, no pide nada por red y se abre con doble clic
- `./setup.sh` corre limpio y es idempotente: sobre una instalación ya hecha no
  reinstala nada y termina verificando

---

## 4. Decisiones clave

Las 24 están en [`decision_log.md`](decision_log.md). Las que más condicionan lo que sigue:

- **DEC-001** — el objetivo es portfolio, no aprender inglés. Se optimiza para demostrable y terminable.
- **DEC-002** — el video de 2 minutos es el contrato de alcance: lo que no aparece en pantalla, no se construye.
- **DEC-004** — el LLM no es el profesor. LanguageTool detecta, el resto es código.
- **DEC-012** — esqueleto caminante primero (ya cumplido).
- **DEC-017** — **normalizar el loudness es obligatorio**, no cosmética: sin eso Whisper "arregla" la gramática del hablante y el diagnóstico se vacía en silencio.
- **DEC-018** — `medium.en` por defecto; la métrica que gobierna la elección de modelo es la tasa de falsos positivos, no la velocidad.
- **DEC-021** — el LLM **no corre en tiempo de ejecución**; las explicaciones se precomputan. Ollama no hace falta corriendo (y en 8 GB conviene matarlo).
- **DEC-023** — toda métrica declara su condición de validez y **se abstiene** si no se cumple.
- **DEC-024** — los errores se **listan agrupados, nunca se rankean**: con recall parcial un ranking ordena la ceguera del detector.
- **DEC-015** — el repo tiene que poder correrlo un tercero: `setup.sh`. En la revisión del día 9 quedó que **no instala Ollama** (DEC-021 lo sacó del tiempo de ejecución) y que termina **verificando**, no informando.
- **DEC-025** — el informe es un **archivo HTML que se escribe**, no una página que se sirve. Cae la parte de FastAPI de DEC-007: un servidor agregaría un proceso y una explicación de más en el video, y el requisito real es más fuerte que "sin framework" — el archivo no puede pedir nada por red.

---

## 5. Estado del código

- **Rama**: `main`, sincronizada con `origin/main`. **34 commits.**
- **Cambios sin commitear**: **ninguno**. `git status` limpio.
- **Tests**:
  - `.venv/bin/python tests/check.py` → *all checks passed* (umbrales fijados contra muestras reales)
  - `.venv/bin/python tests/recall.py` → *recall 28/32 = 88%, precision 97%*
- **`sessions.db`** y **`report.html`**: existen localmente y están **gitignoreados** (los dos contienen transcripciones de la voz del usuario). Se pueden borrar sin consecuencias: el informe se reescribe en cada corrida.
- **Audio**: `spike/audio/` también gitignoreado. Hay dos grabaciones locales: `attempt.wav` (las 15 frases leídas) y `answer.wav` (39 s de habla espontánea).

**Dependencia frágil que hay que conocer:** `scripts/install_rules.py` inyecta las reglas
propias dentro del `grammar.xml` **de LanguageTool**, que vive en
`~/.cache/language_tool_python/LanguageTool-6.8/`. Es idempotente, hace backup y tiene
`--remove`, pero **si se reinstala LanguageTool hay que volver a correrlo** o el detector
cae de 88% a 27% sin avisar. Desde el día 9 eso se detecta con **`./setup.sh --check`**,
que no pregunta si las reglas están escritas sino si el detector encuentra un error que
sólo ellas ven; `./setup.sh` lo arregla.

---

## 6. Bloqueado / esperando

Nada bloqueado técnicamente. Lo único que espera **a una persona**:

- **Nada bloqueado.** Hay tres sesiones espontáneas de cinco consignas (una del autor, dos de compañeros).
- ~~Una sesión hablada de las cinco consignas~~ (histórico). La sesión 4 llegó a 85 palabras de contenido
  y dio A2, pero eran respuestas **escritas y leídas** (DEC-027), así que está marcada como
  lectura y no cuenta como diagnóstico. Sigue sin existir una muestra espontánea que pase el
  umbral de 40 palabras. Se graba con `python -m speaklens.web`.

---

## 7. Próximos pasos (ordenados, ejecutables)

```bash
cd ~/dev/personal/speaklens
```

1. **Grabar con la UI guiada**, que es lo que el video debería mostrar:
   ```bash
   .venv/bin/python -m speaklens.web     # abre http://127.0.0.1:8000
   ```
   Lleva consigna por consigna, cronometra contra los 25 s objetivo y avisa si el micrófono
   está bajo. `record.sh` sigue existiendo para tomas sueltas por terminal.
   Hablar, **no leer** — pero ojo con el punto de §8: hoy el detector de lectura no atrapa
   una lectura fluida.

2. **Día 10 — README final + grabar el video de 2 minutos.** Para el README hace falta una
   captura del informe: usar una grabación de prueba, no una con datos propios de más.

> **Puerta de verificación:** el video existe y dura ~2 minutos. Todo lo demás es medio.
> El repo, además, se hace público ese mismo día (DEC-014): es el bloqueante que este
> proyecto existe para resolver.
> **Restricción de método:** lo que no aparece en el video, no se construye (DEC-002).
> Antes de cualquier commit: `tests/check.py` y `tests/recall.py` en verde.

---

## 8. Preguntas abiertas y riesgos

| Tema | Estado / default actual |
|---|---|
| El repo sigue **privado** | DEC-014 lo revisó: se hace público como parte del día 10. **Riesgo asumido**: si no se publica, el bloqueante "GitHub vacío" sigue sin resolverse |
| 4 puntos ciegos del detector | Documentados como **fuera de alcance** en `languagetool-coverage.md`. Dos exigen saber que la oración anterior estaba en pasado: es el techo de un sistema de reglas |
| Cronograma | DEC-020: una hora por día, sin fecha de entrega. **Tres días sin avance = señal de replanificar.** Entre el 9 y el 30 de agosto pasaron 21 |
| ~~`looks_read_aloud` no separa lectura de habla~~ | **Resuelto por otra vía — DEC-030.** Con seis muestras etiquetadas quedó demostrado que **no hay umbral posible**: ordenadas por pausa máxima, lectura y habla se intercalan, porque un hablante fluido no frena a buscar la palabra. La app ahora **pregunta** y la heurística es una nota al pie. Márgenes finos documentados en `tests/check.py` |
| **El nivel parece medir registro, no dominio** | Ale y Joan dieron **A2** (21% y 16% de vocabulario sobre A2) y el texto **escrito** del autor dio **B2+** (45%) — pero los dos hablan mejor inglés que él. La prosa escrita es léxicamente más densa que el habla, y el habla de cualquiera se apoya en palabras comunes. Tres muestras no alcanzan para concluir; **es la hipótesis más probable** y explica por qué el techo de B2 nunca se toca con habla real |
| **Los umbrales de `summary_es` nunca se calibraron** | Dice "ahí se nota que te trabás" bajo 6 palabras encadenadas, y sobre seis muestras reales el máximo es 4,84. O sea que la rama optimista no se dispara nunca. Hace falta más gente antes de mover el número |
| ~~El nivel se apoya en la mediana~~ | **Arreglado — DEC-028.** Ahora sale de la proporción de vocabulario por encima de A2, y las palabras desconocidas se descartan en vez de contar como B2. Los umbrales separan seis textos y nada más: **no hay calibración contra corpus etiquetado**, y por eso el informe dice que es aproximado |
| **Arriba de B2 sigue sin verse nada** | CEFR-J termina en B2. La etiqueta ahora dice "B2 o más" en vez de mentir, pero distinguir C1 de B2 necesita otro eje: complejidad sintáctica con spaCy (`en_core_web_sm`, 12 MB) — que además resolvería el margen fino de DEC-027, porque densidad léxica y largo de cláusula separan registro escrito de hablado sin depender del reloj. **Una sola incorporación cubre las dos cosas** |
| Nombre `speaklens` | Provisional desde el día 1; nadie lo confirmó |
| Sin captura del informe en el README | El `report.html` real contiene la voz del usuario y está gitignoreado. La captura del día 10 hay que sacarla de una muestra pensada para mostrarse |
| Loop conversacional con TTS | Fuera de v1 desde el principio. `say` de macOS costaría 0 GB de RAM si alguna vez se retoma |
| Evaluación de pronunciación | Descartada (DEC-003). Las confusiones acústicas recurrentes quedaron anotadas como candidato de v2 (DEC-019) |

---

## 9. Punteros

- **Superficie de conocimiento**: este repo usa **andamiaje mínimo a propósito** (DEC-014).
  No hay `/wiki` ni `docs/structure/`. La superficie es `docs/decision_log.md` +
  `docs/languagetool-coverage.md` (todas las mediciones, incluidas las rondas que dieron mal
  y por qué se descartaron).
- **Tracker**: no hay tracker separado; el plan y el avance viven en
  [`daily-plan.md`](daily-plan.md).
- **Memoria**: `speaklens-diagnostico-ingles.md` en la memoria personal, con línea en
  `MEMORY.md`.
- **Glosario didáctico**: [`aprendizaje/glosario.md`](aprendizaje/glosario.md) — conceptos ya
  explicados y marcados como entendidos; no repetirlos.
- **Relacionados**: `plata-juntos-roadmap.md` (el otro proyecto personal, con su QA pendiente),
  `busqueda-laboral-espana.md` (por qué existe este proyecto).
