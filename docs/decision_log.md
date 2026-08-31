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

### **DEC-021: Las explicaciones se precomputan por regla; el LLM no corre en tiempo de ejecución**

- **Fecha**: 2026-08-09
- **Contexto**: Medido en la máquina real, `qwen3:4b` tardó **89 s** en explicar un solo error — es un modelo de razonamiento y emitió 1.646 tokens de cadena de pensamiento antes de dos frases de respuesta. El sufijo `/no_think` lo bajó a 48 s, todavía inviable: un diagnóstico con 15 errores tardaría entre 12 y 22 minutos.
- **Decisión**: Las explicaciones se generan **una sola vez por `rule_id` de LanguageTool**, se revisan a mano y se versionan como YAML. En ejecución es un lookup de diccionario. Si aparece una regla sin entrada, se muestra el `message` propio de LanguageTool como respaldo.
- **Motivo**: Los `rule_id` son un conjunto cerrado y la explicación de una regla no depende del hablante ni de la frase, así que generarla por request es recomputar siempre lo mismo pagando 48 s. Es exactamente el razonamiento de DEC-009 aplicado a DEC-004: si el contenido no varía por usuario, es data, no inferencia.
- **Impacto**: Latencia de explicación pasa de ~48 s a ~0. Desaparece la alucinación en runtime, porque cada texto pasó por revisión humana antes de entrar al repo. **El LLM local deja de correr en tiempo de ejecución y pasa a ser herramienta de build.** Para el portfolio esto no debilita la historia sino que la mejora: medir, descubrir que la latencia es inaceptable y mover el cómputo a build-time es mejor ingeniería que llamar a un modelo y aguantar. El modelo sigue corriendo local en 8 GB, sólo que una vez.

### **DEC-022: La fluidez deja de ser plan B y pasa a ser la mitad principal**

- **Fecha**: 2026-08-09
- **Contexto**: Primera medición sobre **habla espontánea real**, no sobre frases de prueba. 39 segundos respondiendo la consigna 1. Transcripción: *"Okay, I work in the project Plata Juntos. This project is designed for me, is the web This app is a financial app for finance personnel"*. Hay errores visibles — *work **in** the project*, una frase abandonada a la mitad, *for finance personnel*. **LanguageTool detectó cero.**
- **Decisión**: Se corrige la expectativa sobre el diagnóstico gramatical y se promueve la fluidez de red de seguridad a mitad protagónica del producto.
- **Motivo**: El 11/15 de las frases curadas era optimista y no representa el habla real. Las frases de prueba tenían errores de manual, aislados y prolijos; el habla real falla distinto — preposiciones con verbos puntuales, estructuras abandonadas, palabras aproximadas — que es justo donde LanguageTool es ciego, y en habla real eso es **la mayoría** de lo que pasa, no una minoría. En la misma muestra la fluidez midió perfecto: 2,2 palabras seguidas antes de frenar y 67% de silencio, con una pausa de 12,3 s. Eso es *"trabarme al hablar"* cuantificado.
- **Impacto**: El informe se ordena alrededor de la fluidez, con la gramática como complemento honesto sobre lo que sí detecta. El README no puede prometer detección gramatical amplia. **Nota metodológica**: la muestra fue de 26 palabras a −42 dB, así que no se descarta que se haya perdido audio; la conclusión sobre gramática debería confirmarse con una toma más fuerte y más larga antes de darla por firme.

### **DEC-023: Sin muestra suficiente, el informe no estima**

- **Fecha**: 2026-08-09
- **Contexto**: Dos veces en el mismo día el sistema afirmó algo que no podía sostener: las métricas de fluidez diagnosticaron un tartamudeo sobre una grabación leída, y la heurística que debía impedirlo clasificó habla espontánea como lectura porque el hablante hace pausas silenciosas en vez de decir *"uh"*.
- **Decisión**: Toda métrica declara su condición de validez y se abstiene cuando no se cumple, en lugar de degradar en silencio. Las heurísticas se fijan contra muestras reales medidas, no contra intuiciones.
- **Motivo**: El usuario está en B1 y no puede detectar que el informe se equivoca — el mismo razonamiento de DEC-004 aplicado a las métricas y no sólo al LLM. Un número inventado con formato lindo es peor que un "no puedo medir esto".
- **Impacto**: `Fluency.looks_read_aloud` se abstiene y explica qué muestra hace falta. La estimación de nivel (DEC-005) necesita un mínimo de palabras antes de arrojar un número.

### **DEC-024: El informe lista errores, no los rankea**

- **Fecha**: 2026-08-30
- **Contexto**: Recall medido del detector sobre habla de aprendiz anotada: **27%**, con 90% de precisión (`tests/recall.py`). Encuentra uno de cada cuatro errores, y los que se le escapan no son al azar sino categorías enteras: preposición según el verbo, sujeto vacío, artículo espurio, calcos de estructura, tiempo verbal sin marca explícita.
- **Decisión**: El informe muestra los errores encontrados **agrupados por tema y sin ordenar por frecuencia**, y los presenta como "esto es lo que pudimos detectar con seguridad" en lugar de como un perfil del hablante. Se elimina el ranking de temas de la salida.
- **Motivo**: Con 27% de recall, un ranking por frecuencia **mide la cobertura del detector, no las debilidades del hablante**. Diría "los artículos son tu punto débil" porque los artículos son lo que sabemos ver. Es un ranking de nuestra propia ceguera presentado como diagnóstico del usuario — y el usuario está en B1 y no puede detectar el sesgo, que es el mismo razonamiento de DEC-004 y DEC-023.
- **Impacto**: **Revisa DEC-006**: el "mapa que evoluciona" ya no puede sostenerse sobre conteos de errores gramaticales. La persistencia sigue teniendo sentido para la fluidez, que sí es confiable y sí es comparable en el tiempo. La precisión del 90% es lo que hace que la lista siga valiendo: pocas marcas, pero casi todas ciertas.

### **DEC-025: El informe es un archivo HTML que se escribe, no una página que se sirve**

- **Fecha**: 2026-08-30
- **Contexto**: DEC-007 preveía FastAPI con una página HTML/JS sin framework. Al llegar al día 8, el CLI ya produce todos los datos y la pantalla es sólo presentación: no hay nada que pedirle a un servidor.
- **Decisión**: `speaklens/report.py` renderiza un `report.html` autocontenido — sin CDN, sin fuente web, sin proceso— que el mismo comando del CLI escribe al terminar. `--open` lo abre en el navegador. La parte de FastAPI de DEC-007 queda sin usar; el "sin framework de frontend" se mantiene.
- **Motivo**: Un servidor agrega un proceso que arrancar, un puerto y una dependencia, a cambio de cero funcionalidad visible. Además, en el video (DEC-002) un servidor es una explicación de más: un comando que termina abriendo el informe se cuenta en una frase. Y el requisito real es más fuerte que "sin framework": el archivo no puede pedir **nada** por red, porque el argumento del proyecto es que corre con el wifi apagado (DEC-001) y el informe es el único artefacto que un evaluador mira de verdad.
- **Impacto**: FastAPI sale del stack y de `requirements.txt` (nunca llegó a entrar). `report.html` queda gitignoreado: contiene la transcripción de la voz del usuario, igual que `sessions.db`. Si algún día hace falta una demo web, el HTML ya está separado del cálculo y servirlo es un `FileResponse`.

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
