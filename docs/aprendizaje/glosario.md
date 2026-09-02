# Glosario

Conceptos técnicos que fueron apareciendo mientras se construía SpeakLens, explicados
una vez para no volver a explicarlos. Orden de aparición.

---

## Taxonomía (capa de indirección) ✅ entendido 2026-08-09

**Qué es.** Una lista intermedia entre dos cosas que cambian a ritmos distintos. En vez
de conectar A con B directamente, conectás A con la lista y la lista con B. Acá: en vez
de escribir una explicación por cada regla de LanguageTool (cientos, con nombres
crípticos), escribís once temas y mapeás cada regla a un tema.

**Analogía.** Un plan de cuentas. No creás una cuenta contable por cada factura: tenés
cincuenta cuentas y cada factura se imputa a una. Los reportes salen por cuenta, no por
factura, y por eso son legibles.

**Dónde falla la analogía.** Un plan de cuentas es excluyente, exhaustivo y auditado por
un tercero. Una taxonomía gramatical es difusa: *"I have hungry"* es a la vez un calco y
una elección de verbo equivocada, y quien decide dónde va sos vos, sin nadie que revise.

**Por qué acá.** Colapsa tres cosas que se estaban resolviendo por separado —las
explicaciones, las unidades del currículum y el ranking de errores— en una sola lista.
Y baja la autoría de cientos de textos a once.

**El costo.** Indirección: agregás una capa que hay que mantener. Si una regla queda mal
clasificada, el usuario recibe la explicación equivocada y es difícil que alguien lo
note. Y la categoría `otros` crece en silencio si nadie la mira: por eso está marcada
como bandeja de entrada y no como cajón de sastre.

---

## Esqueleto caminante ✅ entendido 2026-08-09

**Qué es.** Construir primero el camino completo de punta a punta, feo pero funcionando,
antes que cualquier parte en detalle. No una capa entera bien hecha: una línea fina que
atraviesa todas las capas.

**Analogía.** Abrir un local. En vez de terminar la decoración, el depósito y la vidriera
y recién ahí vender, hacés una venta completa el primer día: entra alguien, paga, se lleva
el producto, la plata queda en la caja. Con una mesa prestada si hace falta. Lo que probás
es que el circuito cierra.

**Dónde falla la analogía.** Esa primera venta es plata real. El esqueleto caminante no le
sirve a ningún usuario todavía, y buena parte se tira. Nadie te paga por él.

**Por qué acá.** Es lo que destapó el bug de la puntuación en el día 2: la detección caía
de 11 a 8 errores y la salida seguía pareciendo razonable. Ninguna prueba de LanguageTool
por su cuenta lo habría mostrado, porque el defecto vivía en la unión entre Whisper y el
detector, no adentro de ninguno de los dos.

**El costo.** Construís algo que sabés que está feo, y después cuesta tirarlo: se queda por
inercia. Y da poca satisfacción, porque al terminar el día no tenés nada lindo que mostrar,
sólo la certeza de que el circuito cierra.

---

## Recall y precisión 👁 visto 2026-09-01

**Qué es.** Dos números que hacen falta juntos para saber si un detector sirve, medidos
contra una muestra donde alguien ya marcó a mano cuál era la respuesta correcta. **Recall**:
de todos los errores que realmente había, qué proporción encontró — responde *¿cuánto se me
escapa?*. **Precisión**: de todo lo que marcó, qué proporción era realmente un error —
responde *¿cuánto de lo que me dice es cierto?*. Casi siempre se compran uno con otro:
aflojás las reglas y sube el recall mientras baja la precisión.

**Analogía.** Un control de facturas duplicadas. Recall: de todas las duplicadas que hubo en
el período, cuántas frenó el control. Precisión: de todas las que frenó, cuántas eran de
verdad duplicadas y no falsas alarmas que le hicieron perder la mañana a alguien. Un control
que frena todo tiene recall perfecto y lo empiezan a ignorar; uno que no frena nada tiene
precisión perfecta y no sirve.

**Dónde falla la analogía.** En el control contable el universo verdadero **existe**: con
tiempo suficiente podés revisar el 100% del período y saber cuántas duplicadas había. Acá no
existe — alguien tiene que decidir a mano qué cuenta como error, y ese alguien sos vos, con
tus sesgos. El denominador del recall no es un hecho, es una opinión anotada. Segunda
diferencia: en la factura los dos errores se miden en pesos y se comparan; acá un error no
detectado significa que no aprendés algo, y un falso positivo significa que te enseñan algo
falso que no podés detectar. No están en la misma unidad.

**Por qué acá.** `tests/recall.py` corre el detector sobre `tests/fixtures/learner_speech.yaml`
—cinco respuestas con 32 errores marcados a mano— y cuenta superposiciones de posición. Fue
lo que destapó que el 14/15 sobre frases curadas era un espejismo: contra habla real el recall
era **27%**. Ese número decidió DEC-024, que el informe no rankee los errores por frecuencia:
con recall parcial, el ranking ordena la ceguera del detector y la presenta como el perfil del
hablante. Hoy está en 88% de recall con 97% de precisión.

**El costo.** Anotar la muestra a mano es trabajo aburrido y es el trabajo que sostiene todo
lo demás. Y la métrica es código, así que tiene bugs: la primera versión de `recall.py`
comparaba substrings y contaba la `a` de *a/an* como acierto adentro de "since March",
inflando el recall 18 puntos. Los bugs de una métrica tienden a favorecer lo que uno quiere
ver, porque uno deja de investigar cuando el número le gusta.

**Cómo se evita cada falla.**

| Falla | El arreglo más barato |
|---|---|
| Medir contra datos que armaste vos | Que anote otro; si no hay otro, anotar **antes** de escribir la solución y no retocar la anotación después |
| Muestra chica | Calcular cuánto vale un caso (32 casos = 3 puntos) y no reportar por debajo de eso. Sin decimales |
| Bug en la métrica | Probarla con un detector que no marca nada (recall debe dar 0) y otro que marca todo (precisión ≈ 0). Y **desconfiar de las buenas noticias**: si un número salta, buscar el bug antes de festejar |
| Sobreajuste al set | Cada regla tiene que explicarse como un fenómeno del idioma, no como un caso del fixture. `ES_ARTICLE_JOB_AN` sí; `ES_CASO_17` se delata solo |
| Reportar uno solo | Los dos juntos, con el denominador y el conteo crudo a la vista, como termina `recall.py` |
| El denominador es una opinión | No se elimina: se hace **auditable**. La anotación vive versionada en el repo y cualquiera puede impugnar un caso |

**En mis palabras.**

---

## Cola de pendientes

Conceptos que aparecieron y todavía no se abrieron:

- **Sobreajuste al set de prueba** — agregar reglas que agarran exactamente los casos del
  fixture: el número sube y el detector no mejora.
- **Datos etiquetados / ground truth** — quién decide la respuesta correcta, y qué pasa
  cuando es la misma persona que construye.
- **Costos asimétricos de error** — visto de paso el 1/9; merece sesión propia con el caso
  de `looks_read_aloud`.

