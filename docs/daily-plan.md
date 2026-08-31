# Plan diario — 1 hora por día

Reemplaza el fin de semana en bloque de DEC-016, que no se cumplió.

**La regla:** cada sesión tiene un entregable definido *antes* de sentarse, y termina
nombrando el de mañana. En sesiones de una hora, arrancar sin saber qué vas a hacer te
cuesta 15 minutos de reorientación — un cuarto de la sesión.

**Se mantiene DEC-012:** el esqueleto caminante es lo primero. Nada de UI, nada de nivel
CEFR, nada lindo hasta que el camino punta a punta exista aunque sea por terminal. En esta
cadencia, "hora 6" pasa a ser "día 2".

| Día | Entregable | Termina cuando |
|----|-----------|---------------|
| ~~0~~ | ~~Instalaciones~~ ✅ **hecho 9/8** | Ollama + `qwen3:4b`, OpenJDK 26, LanguageTool 6.8. Ver hallazgos abajo |
| ~~1~~ | ~~Reglas propias de LanguageTool~~ ✅ **hecho 9/8** | `rules/grammar-l2-es.xml` + `install_rules.py`. Cobertura 9/15 → 11/15 |
| ~~2~~ | ~~Esqueleto caminante (DEC-012)~~ ✅ **hecho 9/8** | `python -m speaklens.cli <audio>` corre el camino entero. 11 errores en 6 temas |
| ~~3~~ | ~~Métricas de fluidez (DEC-010)~~ ✅ **hecho 9/8** | `speaklens/fluency.py`. Pendiente: validarlas con una grabación espontánea, no leída |
| ~~4~~ | ~~Estimación de nivel (DEC-005)~~ ✅ **hecho 9/8** | `speaklens/level.py`. Se abstiene bajo 40 palabras de contenido. Checks en `tests/check.py` |
| ~~5~~ | ~~Persistencia (DEC-006)~~ ✅ **hecho 30/8** | `speaklens/storage.py`. La fluidez es lo que se compara en el tiempo; los errores se listan sin rankear (DEC-024) |
| ~~6~~ | ~~Currículum (DEC-009)~~ ✅ **hecho 30/8** | `data/curriculum.yaml`, 9 unidades en orden pedagógico fijo. Escrito a mano, no generado |
| ~~7~~ | ~~Explicaciones precomputadas (DEC-021)~~ ✅ **hecho 30/8** | `data/explanations.yaml`, 40 reglas en español. Lookup con 3 niveles de respaldo |
| 8 | Informe en pantalla | La web local muestra nivel, errores agrupados y plan. Fea pero completa |
| 9 | `setup.sh` (DEC-015) | Alguien que clona el repo puede correrlo |
| 10 | README + **video** | Los 2 minutos grabados. No es opcional (DEC-002) |

Unas dos semanas de días hábiles. Al terminar cada sesión, anotá en una línea qué quedó y
cuál es el entregable de mañana.

## Los dos riesgos de esta cadencia

**Deriva de alcance.** Con más días, más tentación de agregar cosas. El contrato sigue
siendo el video de 2 minutos (DEC-002): lo que no aparece en pantalla, no se construye.

**Abandono silencioso.** Los hábitos diarios de proyectos personales mueren más rápido que
los bloques de fin de semana, y sin fecha límite nadie avisa. Si pasan tres días sin
avance, no es una pausa: es la señal de replanificar en serio.
