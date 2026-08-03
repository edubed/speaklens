# Semana de preparación — 3 al 7 de agosto 2026

Objetivo: llegar al sábado 8 con **cero riesgo técnico desconocido** y todo descargado,
para que el fin de semana sea puro construir. Total estimado: ~3 horas repartidas.

---

## 1. El spike que puede matar el proyecto (30 min) — hacelo primero

Valida DEC-011: ¿Whisper te corrige la gramática al transcribir?

```bash
brew install ffmpeg
pip install faster-whisper
```

Grabá estas 5 frases en un `.wav`, diciéndolas **con el error**:

| # | Decir literalmente | Error esperado |
|---|---|---|
| 1 | "Yesterday I go to the meeting" | pasado simple |
| 2 | "I have 32 years old" | calco del español |
| 3 | "She don't like the project" | concordancia |
| 4 | "I am agree with you" | calco del español |
| 5 | "Explain me the problem" | orden / preposición |

Pasalas por `small.en` y por `medium.en` y compará contra lo que dijiste.

**Criterio de decisión:**
- **3 o más errores sobreviven** → el enfoque gramatical va. Seguí con el plan.
- **Menos de 3 sobreviven** → aplicá las mitigaciones de DEC-011 en orden. Si ninguna
  funciona, el proyecto pivotea a fluidez pura (DEC-010), que ya está diseñada.

### Ronda 1 — 2026-08-02 · resultado: **inconcluyente, riesgo confirmado**

5 frases, 3 condiciones. Grabación a −39,5 dB de media (demasiado baja).

| # | Categoría | Resultado |
|---|---|---|
| 1 | pasado simple | preservado — *"I go to meeting"* |
| 2 | calco (edad) | preservado — *"I have 32 years old"* |
| 3 | concordancia | **corregido** — *don't* → *doesn't*, en los 3 modelos |
| 4 | calco (agree) | **corregido** — *I am agree* → *I agree*, en los 3 modelos |
| 5 | preposición | no encontrado — Whisper se comió *"me"* (audio flojo) |

**Conclusiones:**

1. **El riesgo de DEC-011 es real y está confirmado.** Whisper corrige gramática: los casos 3 y 4 fueron normalizados por las tres condiciones sin excepción.
2. **La magnitud no se pudo medir.** Muestra de 5, grabación baja, y dos pérdidas de palabras cortas atribuibles al volumen y no a normalización.
3. **Advertencia metodológica:** el conteo pasó de 1/5 a 3/5 tras corregir dos regex *después* de ver los datos. El arreglo del caso 1 era legítimo (la regex exigía un `"the"` que Whisper omitió). El del caso 5 fue discutible: aceptaba *"explain my"* como error sobreviviente cuando en realidad era una mala escucha. Ese cambio post-hoc fue justo el que cruzó el umbral, así que **el GO de la ronda 1 no es válido** y se descarta.
4. **Hipótesis emergente:** Whisper corrige los errores cuya forma correcta es una colocación de alta frecuencia (*"she doesn't like"*, *"I agree with you"*) y preserva aquellos cuya corrección no lo es (*"I go to meeting"*, *"I have 32 years old"*).

### Ronda 2 — pendiente de grabar

15 frases sobre 6 categorías, diseñadas para poner a prueba la hipótesis anterior. 4 condiciones (`base.en`, `small.en`, `small.en` + prompt de literalidad, `medium.en`), que cubren de paso las mitigaciones 1 y 2 de DEC-011.

**Criterio pre-registrado en el código, cerrado antes de correr:**

| Sobreviven | Veredicto |
|---|---|
| ≥ 8/15 | **GO** — se construye el diagnóstico, acotado a las categorías que sobreviven |
| 5–7/15 | **PARCIAL** — se construye, y el README declara qué clases de error no se detectan |
| ≤ 4/15 | **STOP** — pivot a métricas de fluidez (DEC-010) |

Las regex ya nacen tolerantes a artículos y palabras átonas omitidas, y `record.sh` aborta si la grabación queda por debajo de −32 dB. Los 15 casos pasan test de regresión en ambas direcciones.

### Ronda 2 — 2026-08-02 · resultado: **GO (13/15)**

Grabación de 62 s, normalizada a −16 LUFS antes de transcribir.

| Condición | Preservados |
|---|---|
| `base.en` | 13/15 |
| `small.en` | 12/15 |
| `small.en` + prompt de literalidad | 12/15 |
| `medium.en` | 13/15 |

Por categoría (mejor condición): tiempo verbal 3/3 · concordancia 3/3 · calcos 2/3 · preposiciones 2/3 · artículos 2/2 · orden de palabras 1/1.

**Hallazgo principal — la conclusión de la ronda 1 era un artefacto del audio.** En la ronda 1, *"She don't like the project"* fue corregida por los tres modelos sin excepción. Con el mismo tipo de habla pero audio normalizado, la preservan las cuatro condiciones. La explicación es conocida en ASR: cuando la evidencia acústica es débil, el decodificador se apoya más en su modelo de lenguaje interno y "repara" el texto. **Con audio limpio, Whisper transcribe literal.**

Sobre 60 observaciones (4 condiciones × 15 casos) hubo **una sola corrección genuina**: `small.en` + prompt de literalidad convirtió *"depend of"* en *"depend on"*. Irónicamente fue la condición diseñada para aumentar la literalidad — el prompt se descarta.

**Los dos casos que no cerraron no son normalización:**

- **Caso 8** (*"I am agree"*): las cuatro condiciones escucharon *"I am **angry** with you"*. Es una confusión acústica, no una corrección.
- **Caso 12** (*"She arrived to the airport"*): se transcribió *"she arrive to"*. El rasgo evaluado — la preposición equivocada — **sí sobrevivió**; la regex exigía *"arrived"* y falló por la `-d` final no pronunciada. No se tocó la regex ni el umbral: el veredicto pasa cómodo de cualquier manera.

Ambos son, de hecho, **señal real sobre la pronunciación del usuario** y no ruido del experimento.

**Hallazgo secundario, y es el que más importa para el diseño:** `base.en` empata en preservación (13/15) pero transcribe peor el léxico — escribió *"a new letter"* por *"a new laptop"* y *"Just like"* por *"Yesterday"*. Para un diagnóstico eso es peligroso: **LanguageTool le atribuiría al usuario errores que en realidad cometió el transcriptor** (falsos positivos). Preservar errores es necesario pero no suficiente; también hace falta fidelidad léxica. Por eso el modelo por defecto no es el que puntúa igual siendo más chico.

```
mejor condición → medium.en (13/15, mejor fidelidad léxica)
sobreviven      → 13/15
decisión        → GO. Ver DEC-017 y DEC-018.
```

---

## 2. Descargas y verificación (45 min)

```bash
brew install ollama && ollama serve
ollama pull qwen3:4b          # ~2.5 GB — el que explica en español
pip install language-tool-python fastapi uvicorn
```

- [ ] Verificar que LanguageTool arranca **sin internet** (baja un jar de ~200 MB la primera vez; requiere Java). Apagá el WiFi y probá que sigue detectando errores.
- [ ] Medir cuánta RAM quedan usando Whisper + Ollama simultáneamente. Presupuesto: no pasar de ~4 GB entre los dos.
- [ ] Probar que `qwen3:4b` explica bien un error en español. Si las explicaciones son flojas, probar `llama3.2:3b` o subir a `qwen3:8b` sabiendo que va a hacer swap.

---

## 3. Contenido a redactar (1 h)

- [ ] **Las 4–5 consignas de elicitación** (DEC-008). Cada una debe forzar una estructura:
  - pasado simple — "Contame qué hiciste el fin de semana pasado"
  - condicional — "¿Qué harías si te ofrecieran un trabajo en Madrid?"
  - presente perfecto — "¿Qué proyectos hiciste que te enorgullezcan?"
  - comparativos — "Compará tu trabajo actual con uno anterior"
  - futuro — "¿Dónde te ves en dos años?"
- [ ] **Listas de frecuencia CEFR** para DEC-005. Buscar wordlists públicas (CEFR-J, English Vocabulary Profile) y dejarlas en `data/`.
- [ ] **El YAML del currículum** (DEC-009): correr el LLM una vez sobre las ~10 categorías más comunes de LanguageTool, revisar a mano, versionar.

---

## 4. Decisiones a cerrar antes del commit 1

- [ ] Nombre definitivo del repo (`speaklens` es provisional)
- [ ] Confirmar que el audio **no se persiste** — sólo el transcript

---

## Orden del fin de semana (DEC-012)

**Sábado — horas 1 a 6: esqueleto caminante.** Nada de UI linda.
`grabar → whisper → languagetool → imprimir errores por terminal`. Si a la hora 6 no
existe ese camino completo, se cortan features hasta que exista.

**Sábado tarde / domingo — lo que se agrega encima, en este orden:**
1. Métricas de fluidez (DEC-010) — 50 líneas, alto retorno
2. Estimación de nivel CEFR (DEC-005) — la pieza más impresionante
3. Lookup del currículum (DEC-009)
4. UI web del informe
5. `setup.sh` (DEC-015)
6. README en inglés con diagrama del pipeline (DEC-013)

**Domingo, última hora: grabar el video de 2 minutos.** No es opcional y no es "después".
