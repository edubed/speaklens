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
