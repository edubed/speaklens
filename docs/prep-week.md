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

Anotá el resultado acá abajo — es contenido del README:

```
Resultado del spike (completar):
small.en   → __/5 errores preservados
medium.en  → __/5 errores preservados
Decisión:
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
