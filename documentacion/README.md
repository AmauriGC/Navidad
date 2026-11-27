# Documentación — Mapa e índice de lectura

> Punto de entrada de la documentación de "Turno de Noche en el Taller".
> Dice qué documento leer según lo que quieras hacer. Cuando se agregue un documento
> nuevo, se registra en el índice de abajo el mismo día.

## 1. Orden de lectura general

| # | Documento | Para qué sirve |
|---|---|---|
| 1 | `README.md` (este archivo) | Mapa de la documentación |
| 2 | `ESTANDAR.md` | Cómo se documenta (maestro + fases + estados) |
| 3 | `git/FLUJO_GIT.md` | Ramas y cómo se sube el trabajo |
| 4 | `git/CONVENCION_COMMITS.md` | Cómo escribir los commits |
| 5 | `git/REGLAS_IGNORE.md` | Qué no se sube a Git |
| 6 | `md/hechos/MAESTRO_juego.md` | Cómo está hecho el juego (sistemas y escena) |
| 7 | `md/hechos/MAESTRO_modelos.md` | Cómo se hacen y exportan los modelos de Blender |

## 2. Orden según lo que quieras hacer

### A) Entender el juego
`md/hechos/MAESTRO_juego.md` -> `../PLAN.md` -> `../CLAUDE.md` (notas técnicas completas).

### B) Cambiar o agregar un modelo
`md/hechos/MAESTRO_modelos.md` -> `../Blender/` (scripts) -> exportar a `Assets/Modelos/`.

### C) Trabajar un tema nuevo
`ESTANDAR.md` -> revisar `md/analisis/` -> crear `md/pendientes/MAESTRO_<tema>.md`
-> moverlo a `en_progreso/` al empezar -> a `hechos/` al terminar y probar.

## 3. Índice

| Archivo | Contenido |
|---|---|
| `ESTANDAR.md` | Reglas de documentación |
| `git/` | Ramas, commits e ignores |
| `md/hechos/MAESTRO_juego.md` | Sistemas del juego, escena, controles, dificultad |
| `md/hechos/MAESTRO_modelos.md` | Flujo Blender -> glTF -> Unity, estilo low-poly |
| `md/hechos/MAESTRO_graficos.md` | Menú de gráficos Bajo / Medio / Alto / Personalizado |
| `md/pendientes/MAESTRO_movil.md` | Versión para teléfono (Android) |
| `md/analisis/ANALISIS_RENDIMIENTO.md` | Mediciones de rendimiento y hallazgos |

## 4. Convención rápida

`md/` dice "cómo va el trabajo" (pendiente, en progreso, hecho, análisis).
Lo demás de `documentacion/` dice "cómo es el proyecto" (estándares y reglas).
