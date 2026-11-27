# Estándar de documentación

> Define cómo se escribe y se mueve la documentación del proyecto.

## 1. Estructura

```
documentacion/
├── README.md          <- mapa e índice
├── ESTANDAR.md        <- este archivo
├── git/               <- reglas de Git
└── md/
    ├── pendientes/    <- temas escritos, aún sin empezar
    ├── en_progreso/   <- lo que se está trabajando ahora
    ├── hechos/        <- terminado y probado en el juego
    └── analisis/      <- mediciones, dudas y riesgos por decidir
```

Un documento por tema. No se duplica contenido: se enlaza.

## 2. Ciclo de vida

| Carpeta | Significa |
|---|---|
| `pendientes/` | Está escrito y acordado, pero no se ha empezado |
| `en_progreso/` | Se está trabajando |
| `hechos/` | Terminado, probado en el editor y en el build |

El cambio de estado es un movimiento real del archivo:

```bash
git mv documentacion/md/pendientes/MAESTRO_graficos.md documentacion/md/en_progreso/
git commit -m "docs(graficos): pasa el maestro de gráficos a en_progreso"
```

`analisis/` no es un estado: guarda mediciones, discrepancias y riesgos. Un archivo por
tema, cada hallazgo numerado con severidad, dónde está y propuesta de arreglo.

## 3. Nombres

- `MAESTRO_<tema>.md`: tema completo dividido en fases.
- `FASE_<nn>_<tema>.md`: fase grande que necesita su propio archivo.
- `ANALISIS_<TEMA>.md`: hallazgos por revisar.
- `<tema>` en minúsculas, sin acentos ni espacios.

## 4. Plantilla de maestro

```markdown
# MAESTRO · <Tema>

- Estado: Pendiente | En progreso | Hecho
- Creado: <dd/mm/aaaa> · Actualizado: <dd/mm/aaaa>

## Objetivo
## Alcance
- Incluye: ...
- No incluye: ...
## Fases
- [ ] Fase 1 — ...
## Dependencias
## Criterios de aceptación
## Pruebas
```

## 5. Definition of Done

- Cumple su objetivo y criterios de aceptación.
- Se probó en Play (0 errores en consola) y en el build de Linux.
- El maestro refleja el estado final y los pendientes quedan anotados.
