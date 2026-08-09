# **Registro de Decisiones — SpeakLens**

> [!NOTE]
> **Origen:** Este archivo consolida las decisiones tomadas durante la sesión de
> `/mi-interrogame` del **2026-08-02** (5 rondas). Nombre del repo **provisional**.

**Qué es:** diagnóstico de inglés hablado que corre 100% offline en una MacBook Air M1 de 8 GB.
Hablás 2 minutos siguiendo consignas, y devuelve tu nivel estimado, tus errores recurrentes
rankeados y un plan de estudio.

---

## **Decisiones de Producto**

### **DEC-001: El objetivo primario es portfolio, no aprender inglés**

- **Fecha**: 2026-08-02
- **Contexto**: El disparador fue "tengo que mejorar mi inglés", pero hoy existe ChatGPT en modo voz que cubre el ~80% del caso de uso, gratis y sin latencia. Construir un tutor para aprender inglés sería un desvío de meses frente a una alternativa superior y disponible.
- **Decisión**: El fin del proyecto es un repositorio público que demuestre ingeniería de IA para la búsqueda laboral en España. La mejora del inglés es un beneficio secundario.
- **Motivo**: De los tres bloqueantes de la búsqueda laboral (monotributo, GitHub vacío, inglés B1), este proyecto ataca dos. Como herramienta de aprendizaje sería peor que lo existente; como pieza de portfolio es diferenciado.
- **Impacto**: Se optimiza para que sea demostrable en 2 minutos y para que se termine, no para uso diario. Habilita DEC-002 y DEC-011.

### **DEC-002: El demo de 2 minutos es el contrato de alcance**

- **Fecha**: 2026-08-02
- **Contexto**: Con un timebox de un fin de semana hace falta un instrumento de recorte que no dependa de la fuerza de voluntad.
- **Decisión**: Se diseña primero el video de 2 minutos y se construye **únicamente** lo que aparece en pantalla. El demo elegido: hablar 2 minutos y recibir un informe con nivel estimado, errores recurrentes rankeados y plan de 8 semanas.
- **Motivo**: Ataca directamente el problema declarado por el usuario ("tengo el conocimiento muy desordenado"), que es un déficit de mapa más que de práctica. Además es mucho más original que otro chatbot conversacional.
- **Impacto**: El loop conversacional hablado (TTS + respuesta del coach) queda **fuera de la v1**. Lo que no está en el video, no se construye.

### **DEC-003: El déficit a atacar es fluidez y desorden, no comprensión**

- **Fecha**: 2026-08-02
- **Contexto**: "Mejorar mi inglés" es demasiado vago para diseñar. Al desagregarlo aparecieron dos déficits reales: trabarse al hablar, y conocimiento desordenado.
- **Decisión**: El producto apunta a esos dos y explícitamente **no** a comprensión auditiva (que se resuelve con input masivo, no con un tutor) ni a pronunciación fina.
- **Motivo**: Evaluar pronunciación de verdad exige scoring a nivel fonema (forced alignment, wav2vec2 fonético): es un proyecto aparte y bastante más difícil.
- **Impacto**: Ninguna promesa de evaluación de pronunciación en el README. Habilita DEC-010.

---

## **Decisiones de Arquitectura**

### **DEC-004: Arquitectura híbrida por capas — el LLM no es el profesor**

- **Fecha**: 2026-08-02
- **Contexto**: El diseño intuitivo es "el LLM es el profesor". Con un modelo de 3–4B eso falla del peor modo posible: corrige cosas correctas e inventa reglas con total seguridad. Para alguien en B1, que no puede detectar el error, es peor que no tener nada.
- **Decisión**: Cada capa hace sólo lo que sabe hacer:
  - **Whisper** (local) transcribe.
  - **LanguageTool** (offline, basado en reglas) **detecta** los errores. Determinístico, no alucina.
  - **El LLM local** únicamente **explica** en español un error ya detectado, con un ejemplo.
  - **Código determinístico** calcula métricas, rankea y arma el informe.
- **Motivo**: Usa al modelo chico en la tarea donde es bueno (redactar una explicación de algo ya identificado) y lo mantiene lejos de la tarea donde es malo (juzgar corrección gramatical).
- **Impacto**: Se mantiene la historia de portfolio "LLM local corriendo en 8 GB" con ~1/4 del trabajo. Al no ser tiempo real, la latencia de ~6s del LLM es irrelevante.

### **DEC-005: El nivel CEFR sale de métricas objetivas, no del LLM**

- **Fecha**: 2026-08-02
- **Contexto**: El número "B1" es lo más vistoso del informe y también lo más fácil de inventar.
- **Decisión**: Se estima con métricas computables del texto: riqueza léxica (type-token ratio), largo medio de oración, complejidad sintáctica, y bandas de frecuencia de vocabulario contra listas CEFR públicas.
- **Motivo**: Es NLP aplicado real, reproducible y defendible en una entrevista técnica. Preguntarle el nivel a un 4B es ruido con formato lindo, y deja sin respuesta la pregunta "¿cómo lo calculás?".
- **Impacto**: Es la pieza técnicamente más impresionante del proyecto. Requiere conseguir listas de frecuencia CEFR durante la semana de prep.

### **DEC-006: Diagnóstico y mapa son el mismo código sobre distinta ventana**

- **Fecha**: 2026-08-02
- **Contexto**: Contradicción detectada en la Ronda 3: el demo pide un informe de una sola muestra, pero el mapa de errores se había definido como acumulación a lo largo de N sesiones.
- **Decisión**: Una única función de análisis que corre sobre una ventana de sesiones. Con `n=1` es el diagnóstico inicial; con `n=30` es el mapa que evoluciona. Los errores se persisten en SQLite local.
- **Motivo**: 2 minutos de habla producen 10–20 errores, suficiente para rankear las 5 categorías principales. Cero código extra y el demo puede mostrar ambas lecturas.
- **Impacto**: El "mapa" sale casi gratis y habilita un segundo demo (progreso en el tiempo) sin desarrollo adicional.

### **DEC-007: Stack Python, sin framework de frontend**

- **Fecha**: 2026-08-02
- **Contexto**: El usuario domina TypeScript/React por Plata Juntos, pero apunta a puestos de AI/Automation Engineer.
- **Decisión**: FastAPI + faster-whisper + Ollama, con una página HTML/JS sin framework.
- **Motivo**: Python es el idioma del rol buscado; un repo de IA en TypeScript lee raro. La UI es un botón y un panel de texto: React sería ceremonia pura y no hay equivalente cómodo de faster-whisper en Node.
- **Impacto**: Riesgo de stack nuevo, mitigado porque la superficie es chica.

---

## **Decisiones de Contenido**

### **DEC-008: Elicitación por consignas fijas, no habla libre**

- **Fecha**: 2026-08-02
- **Contexto**: Qué se le pide decir al usuario define la calidad de todo el diagnóstico.
- **Decisión**: 4–5 consignas que fuerzan estructuras concretas (pasado simple, condicional, comparativos, futuro, presente perfecto).
- **Motivo**: En adquisición de lenguas existe el fenómeno de **evitación**: uno esquiva inconscientemente las estructuras que no domina, así que el habla libre da un diagnóstico inflado. Además, consignas fijas hacen el demo **reproducible** por cualquiera que clone el repo.
- **Impacto**: Hay que redactar las consignas en la semana de prep.

### **DEC-009: El currículum se genera una vez y se congela como data**

- **Fecha**: 2026-08-02
- **Contexto**: El informe promete un plan de 8 semanas, pero escribir un currículum a mano consumiría medio timebox.
- **Decisión**: Se corre el LLM **una sola vez, offline**, sobre las ~10 categorías de reglas más comunes de LanguageTool para redactar el blurb de cada unidad. Se revisa a mano y queda versionado como YAML en el repo.
- **Motivo**: Cero alucinación en runtime, ~1h de trabajo, plan auditable y demo reproducible.
- **Impacto**: El plan de 8 semanas es un lookup por categoría de error, no una generación por request.

### **DEC-010: Se miden métricas de fluidez, y son el plan B**

- **Fecha**: 2026-08-02
- **Contexto**: El déficit declarado ("trabarme al hablar") es fluidez, no gramática. Además existe un riesgo que puede matar el enfoque gramatical entero (ver DEC-011).
- **Decisión**: Se calculan pausas por minuto, muletillas (uh/um/like), palabras por minuto y largo medio de tramo sin pausa, todo desde los timestamps por palabra de Whisper.
- **Motivo**: Son ~50 líneas de código, le pegan justo al déficit real, no aparecen en portfolios ajenos, y **son inmunes al riesgo de DEC-011**: si Whisper normaliza la gramática, estas métricas siguen siendo válidas y salvan el proyecto.
- **Impacto**: Es simultáneamente una feature y la red de seguridad del fin de semana.

---

## **Decisiones de Proceso**

### **DEC-011: Spike de literalidad de Whisper antes de construir nada** ✅ RESUELTA

> Resuelta el 2026-08-02 tras dos rondas. **Veredicto: GO, 13/15.** El riesgo no se materializó:
> con audio normalizado Whisper transcribe literal. Ver `prep-week.md` para los datos y
> DEC-017/DEC-018 para las consecuencias de diseño.


- **Fecha**: 2026-08-02
- **Contexto**: **Riesgo #1 del proyecto.** Whisper no transcribe literal: está entrenado para producir texto fluido y bien formado, así que tiende a corregir la gramática al transcribir. Si al decir *"yesterday I go to the meeting"* escribe *"yesterday I went to the meeting"*, LanguageTool no encuentra nada y el diagnóstico gramatical se cae entero.
- **Decisión**: Primera actividad, 30 minutos: grabar 5 frases con errores deliberados, pasarlas por `small.en` y `medium.en`, y comparar contra lo dicho.
- **Motivo**: 30 minutos que pueden salvar el fin de semana completo. Enterarse el domingo a la tarde sería fatal.
- **Impacto**: Si el spike falla, las mitigaciones en orden son: (1) `initial_prompt` con texto agramatical para sesgar hacia literalidad, (2) modelo más chico, que normaliza menos, (3) pivot a wav2vec2 con decodificación CTC sin modelo de lenguaje, que transcribe fonéticamente, (4) pivot del producto a fluidez pura, ya cubierto por DEC-010.

### **DEC-012: Esqueleto caminante a la hora 6**

- **Fecha**: 2026-08-02
- **Contexto**: Un timebox sin criterio de corte es un deseo.
- **Decisión**: Checkpoint duro a la hora 6: tiene que existir el camino completo grabar → transcribir → detectar → mostrar, aunque sea feo y por terminal. Todo lo lindo (currículum, plan, UI, fluidez) se agrega **después** de que el camino exista. Si a la hora 6 no está, se cortan features hasta que esté.
- **Motivo**: Garantiza que exista algo grabable el domingo, que es el criterio de éxito de DEC-001.
- **Impacto**: Orden de construcción no negociable.

### **DEC-013: README y código en inglés, explicaciones de la app en español**

- **Fecha**: 2026-08-02
- **Contexto**: El repo lo va a leer alguien que decide si te entrevista.
- **Decisión**: README, comentarios y nombres en inglés. Las explicaciones gramaticales dentro de la app, en español.
- **Motivo**: El README en inglés abre el mercado internacional y demuestra escritura técnica en inglés, justo lo que un empleador español quiere ver. Las explicaciones van en la lengua materna porque explicar un error en el idioma que se está aprendiendo es peor pedagogía. Bonus: escribir el README es práctica real.
- **Impacto**: Escribir el README cuenta como estudio de inglés.

### **DEC-014: Andamiaje mínimo; repo privado hasta que esté presentable**

- **Fecha**: 2026-08-02 · **Revisada**: 2026-08-02 (misma sesión)
- **Contexto**: La metodología personal (docs/prds, sprint_log, structure) es desproporcionada para 8–12 horas de trabajo, pero el repo **es** el entregable de portfolio.
- **Decisión**: Sólo README fuerte (qué hace, GIF del demo, diagrama del pipeline, y por qué cada capa usa la herramienta que usa) + este `decision_log.md`. Sin PRDs ni sprints. El repo arranca **privado** y se hace público cuando esté presentable.
- **Motivo**: El decision log muestra criterio, no sólo código, y es lo que diferencia un repo de portfolio de un tutorial copiado. Sobre la visibilidad: la versión original de esta decisión era público desde el commit 1, para evitar el "cuando esté lindo" que nunca llega. El usuario optó por privado al inicio y lo reafirmó; queda registrado el riesgo.
- **Impacto**: Este archivo es parte del entregable, no documentación interna. **Riesgo asumido**: el repo puede quedar privado indefinidamente y el bloqueante de "GitHub vacío" seguir sin resolverse. Mitigación: hacerlo público es parte del entregable del domingo 9, junto con el video.

### **DEC-015: Reproducible por terceros vía setup.sh**

- **Fecha**: 2026-08-02
- **Contexto**: Un repo de portfolio que nadie puede correr vale la mitad.
- **Decisión**: Un `setup.sh` que instale dependencias, baje el modelo de Whisper y haga `ollama pull`, más el video para quien no quiera instalar nada.
- **Motivo**: ~1h de trabajo con retorno alto en credibilidad. Un evaluador escéptico asume que un demo no reproducible está maquillado.
- **Impacto**: Entra en el domingo, después del esqueleto caminante.

### **DEC-016: Cronograma — prep 3–7/8, construcción 8–9/8, video el domingo 9**

- **Fecha**: 2026-08-02
- **Contexto**: Plata Juntos tiene pendiente el QA con dos celulares, que es su gate.
- **Decisión**: Semana del 3 al 7 de agosto para instalar y hacer el spike sin apuro. Sábado 8 y domingo 9 para construir. **El video se graba el domingo 9**, no "después".
- **Motivo**: Llegar al fin de semana con el riesgo técnico ya resuelto. Los proyectos mueren porque el demo nunca se graba, así que el video es entregable del fin de semana.
- **Impacto**: El gate de Plata Juntos se corre una semana; sigue siendo el gate.
- **Reemplazada el 2026-08-09 por DEC-020** (una hora por día). El seguimiento de abajo se conserva como registro del deslizamiento.
- **Seguimiento 2026-08-09**: **El cronograma no se cumplió.** La semana de prep (3–7/8) no se hizo y el sábado 8 tampoco. El domingo 9 se usó para cerrar la autoría pendiente — consignas y listas CEFR, ambas ya versionadas — pero no se escribió código de producto. Lo único que sigue bloqueado de la prep es el YAML del currículum, que necesita LanguageTool y Ollama instalados. **Falta fijar fecha nueva de construcción**; el candidato natural es el fin de semana del 15–16/8. Se deja registrado en vez de reescribir la fecha original, porque el patrón de deslizamiento es información y el timebox sólo sirve si se anota cuando falla.

### **DEC-017: Normalización de loudness obligatoria antes de transcribir**

- **Fecha**: 2026-08-02
- **Contexto**: La ronda 1 del spike concluyó que Whisper corregía la gramática. La ronda 2, sobre habla equivalente pero con el audio normalizado a −16 LUFS, mostró lo contrario: los mismos errores se preservaron en las cuatro condiciones. La causa es conocida en ASR: con evidencia acústica débil el decodificador se apoya en su modelo de lenguaje interno y "repara" el texto.
- **Decisión**: Todo audio pasa por `loudnorm=I=-16:TP=-1.5:LRA=11` antes de llegar a Whisper. No es un paso opcional de calidad: es lo que hace válido el diagnóstico.
- **Motivo**: Sin normalizar, el sistema silenciosamente esconde los errores que existe para detectar — el peor modo de falla posible, porque no se nota.
- **Impacto**: Se descarta juzgar tomas por `mean_volume`, que promedia los silencios entre frases y rechaza grabaciones perfectamente audibles. El corte se hace por pico, y la normalización se encarga del resto.

### **DEC-018: `medium.en` por defecto; sin `initial_prompt`**

- **Fecha**: 2026-08-02
- **Contexto**: `base.en` y `medium.en` empataron en preservación de errores (13/15), y `base.en` es ~10× más chico y más rápido.
- **Decisión**: El modelo por defecto es `medium.en`. Se descarta el `initial_prompt` de literalidad. `small.en` queda como alternativa si la RAM aprieta.
- **Motivo**: Empatan en preservar errores pero no en fidelidad léxica: `base.en` transcribió *"a new letter"* por *"a new laptop"* y *"Just like"* por *"Yesterday"*. En un diagnóstico eso es peor que perder un error, porque **LanguageTool le atribuiría al usuario errores cometidos por el transcriptor**. Un falso positivo le enseña algo falso a alguien que no puede detectarlo — exactamente lo que DEC-004 busca evitar. Sobre el prompt: no aumentó la literalidad y produjo la única corrección genuina de las 60 observaciones.
- **Impacto**: ~10,6 s para transcribir 62 s de audio (≈6× tiempo real), aceptable para un diagnóstico que no es conversacional. La métrica que gobierna la elección de modelo es la tasa de falsos positivos, no la velocidad.

### **DEC-019: Las confusiones acústicas recurrentes son señal, no ruido**

- **Fecha**: 2026-08-02
- **Contexto**: Dos casos no cerraron por transcripción divergente: *"agree"* se escuchó como *"angry"* en las cuatro condiciones, y *"arrived"* perdió la `-d` final.
- **Decisión**: Registrar estos desacuerdos en lugar de descartarlos. Cuando varios modelos coinciden en escuchar otra palabra, es información sobre la pronunciación del hablante.
- **Motivo**: Es la aproximación más barata a evaluar pronunciación que existe en el sistema, y DEC-003 había descartado el scoring fonémico por costo. No reemplaza un forced aligner, pero no cuesta nada.
- **Impacto**: Candidato a feature de v2. No entra en el fin de semana.

### **DEC-020: Una hora por día en lugar de un fin de semana en bloque**

- **Fecha**: 2026-08-09
- **Contexto**: El bloque de fin de semana de DEC-016 no se cumplió: la semana de prep no se hizo y el sábado 8 pasó sin código. El usuario propuso avanzar una hora por día sin fecha de cierre fijada.
- **Decisión**: Se adopta la cadencia diaria, con un entregable definido por sesión listado en `docs/daily-plan.md`. Se conserva DEC-012: el esqueleto caminante sigue siendo lo primero, y "hora 6" pasa a ser "día 2".
- **Motivo**: Sostenida, la cadencia diaria entrega más horas por semana que un bloque de fin de semana (≈7 contra 8–12 una sola vez), y encaja mejor con un proyecto que compite con Plata Juntos. El costo es el cambio de contexto: sin un entregable definido de antemano, una sesión de una hora pierde ~15 minutos en reorientarse. De ahí que el plan diario sea parte de la decisión y no un anexo.
- **Impacto**: Sin fecha de entrega, desaparece la presión que garantizaba que el video se grabara. Se compensa de dos formas: el video es el entregable del día 10 y no un "después", y **tres días sin avance se tratan como señal de replanificar**, no como una pausa. El contrato de alcance sigue siendo el video de 2 minutos (DEC-002).

---

## **Decisiones Pendientes**

| # | Tema | Cuándo se resuelve |
|---|---|---|
| 1 | Modelo exacto de Whisper (`small.en` vs `medium.en`) | Sale del spike de DEC-011 |
| 2 | Modelo LLM exacto (default propuesto: Qwen3 4B Q4, ~2.5 GB, buen multilingüe) | Semana de prep |
| 3 | Nombre definitivo del repo (`speaklens` es provisional) | Antes del primer commit |
| 4 | Qué se hace con el audio grabado (propuesta: no persistir, guardar sólo el transcript) | Antes del primer commit |
| 5 | Loop conversacional hablado con TTS (`say` de macOS, 0 GB de RAM) | v2, fuera de alcance |
| 6 | Evaluación de pronunciación a nivel fonema | Descartado para v1 por DEC-003 |
