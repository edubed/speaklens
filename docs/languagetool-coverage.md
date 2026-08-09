# Cobertura real de LanguageTool — 2026-08-09

DEC-004 apoya todo el diagnóstico en que **LanguageTool detecta** y el LLM sólo explica.
Esa decisión asumía que LanguageTool detecta los errores de un hispanohablante. Medido
contra las 15 frases del spike, **detecta 9 y es ciego a 6**.

## Qué detecta

| # | Frase | Regla |
|---|---|---|
| 2 | Last week she **buy** a new laptop | `HE_VERB_AGR` |
| 3 | I **didn't went** to the party | `AUXILIARY_DO_WITH_INCORRECT_VERB_FORM` |
| 4 | She **don't** like the project | `HE_VERB_AGR` |
| 5 | He **have** two brothers | `HE_VERB_AGR` |
| 6 | My friends **is** coming tomorrow | `AGREEMENT_SENT_START` |
| 7 | I have **thirty two** years old | `EN_COMPOUNDS_THIRTY_TWO` ⚠️ |
| 8 | I **am agree** with you | `I_AM_VB` |
| 10 | **Explain me** the problem | `EXPLAIN_TO` |
| 11 | I **depend of** my parents | `DEPEND_ON` |

⚠️ El caso 7 es un **falso acierto**: marcó que *thirty-two* va con guion, no el calco
*"I have X years old"* → *"I am X years old"*. Cuenta como detección pero explicaría lo
que no es. La detección honesta es 8/15.

## Puntos ciegos

| # | Frase | Clase de error |
|---|---|---|
| 1 | Yesterday I **go** to the meeting | tiempo verbal con adverbio temporal |
| 9 | I **have hungry** | calco de *tener hambre* |
| 12 | She **arrived to** the airport | preposición según el verbo |
| 13 | I am **engineer** | falta artículo indefinido |
| 14 | **The life** is difficult | artículo definido de más |
| 15 | **Where you are** going? | orden en preguntas |

**El problema no es el tamaño de la brecha sino su forma.** Artículos, orden en preguntas
y tiempo verbal con adverbio son precisamente los errores más característicos del
hispanohablante. Un diagnóstico ciego a ellos le va a decir al usuario que está mejor de
lo que está — el modo de falla que DEC-004 existe para evitar.

La causa es estructural: las reglas por defecto de LanguageTool apuntan a la escritura de
un nativo (tipeos, estilo), no a errores de aprendiz. *"Yesterday I go to the meeting"* es
inglés válido en aislamiento (presente habitual); marcarlo exige razonar sobre el adverbio
temporal.

## Qué se probó y no sirvió

| Intento | Resultado |
|---|---|
| `picky = True` | 9/15, idéntico |
| `mother_tongue = 'es'` | 9/15, idéntico |
| `rulesFile` con XML propio | Las reglas no se registran; al habilitarlas explícitamente el resultado queda vacío |

El camino de reglas propias **es válido** — `rulesFile` es una clave de configuración
soportada — pero requiere acertar el esquema XML de LanguageTool, que no salió en un
intento corto. Es trabajo de una sesión entera, no de cinco minutos.

## Decisión pendiente

| Opción | Costo | Riesgo |
|---|---|---|
| **A. Reglas propias en XML** para las clases ciegas | ~1 sesión de pelear el esquema | Ninguno de calidad: sigue siendo determinístico y sin alucinación. Además es material de portfolio fuerte — extender LanguageTool con reglas específicas de L1 |
| **B. El LLM como detector acotado**, sólo para artículos, orden y tiempo verbal, con preguntas cerradas | ~medio día | Contradice el espíritu de DEC-004. Un 4B respondiendo "¿falta un artículo acá?" sigue pudiendo equivocarse, aunque menos que en abierto |
| **C. Aceptar y declararlo** en el README | Cero | El diagnóstico subestima sistemáticamente. Honesto, pero deja fuera los errores que más le importan al usuario |

**Recomendación: A, y C igual.** Las reglas propias cubren lo que más duele, y el README
declara lo que quede afuera. B queda descartada salvo que A falle.
