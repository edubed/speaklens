# SpeakLens — Handoff

**Última actualización:** 2026-08-30 (día 8) · **Autor:** Edu Bedini (+ Claude)
**Fase:** Ejecución · **Estado:** ▶ activo, días 0–9 de 10 completos
**Retomá acá →** §7 paso 1: grabar las 5 consignas con `./spike/record.sh --prompt N` (N=1..5) para desbloquear la estimación de nivel, que hoy se abstiene por muestra corta. Es lo único que espera a una persona, y ya hay pantalla donde mirar el resultado.

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

- **Repo**: `~/dev/personal/speaklens` — GitHub **privado** `edubed/speaklens`, remote
  `github-personal` (cuenta personal, **no** la de Kenility; ambas conviven en `~/.ssh/config`).
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

- **Rama**: `main`, sincronizada con `origin/main`. **27 commits.**
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

- **Grabar las 5 consignas.** La estimación de nivel se abstiene con menos de 40 palabras de
  contenido, y la única grabación espontánea que existe dio 12. El informe ya muestra ese
  hueco de forma prolija —una tarjeta ámbar que dice qué muestra falta, DEC-023— pero en el
  video hay que poder mostrar también el caso en que sí estima.

---

## 7. Próximos pasos (ordenados, ejecutables)

```bash
cd ~/dev/personal/speaklens
```

1. **Grabar las cinco consignas, más cerca del micrófono.** Una por vez:
   ```bash
   ./spike/record.sh --prompt 1     # y luego 2, 3, 4, 5
   .venv/bin/python -m speaklens.cli spike/audio/answer.wav
   ```
   Hablar, **no leer** — leer degrada las métricas de fluidez igual que trabarse, y el
   detector de lectura lo va a rechazar. Trabarse está bien: es la medición.

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
