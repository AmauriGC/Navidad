# Convención de commits

> Conventional Commits en español: `tipo(alcance): descripción`.

## 1. Formato

```
tipo(alcance): descripción en minúscula

[cuerpo opcional: qué y por qué]
```

- **tipo**: ver la tabla de abajo.
- **alcance**: área del juego en minúsculas. Ej.: `elfo`, `cascanueces`, `arbol`,
  `ui`, `audio`, `modelos`, `escena`, `blender`, `graficos`, `movil`, `docs`, `git`.
- **descripción**: en español, minúscula, sin punto final, verbo en presente
  ("agrega", "corrige", "ajusta").
- Sin líneas de coautor ni firmas automáticas.

## 2. Tipos

| Tipo | Cuándo |
|---|---|
| `feat` | Algo nuevo en el juego (mecánica, modelo, pantalla) |
| `fix` | Corrección de un error |
| `docs` | Solo documentación |
| `refactor` | Cambio interno sin cambiar cómo se juega |
| `perf` | Mejora de rendimiento |
| `chore` | Configuración, herramientas, mantenimiento |
| `test` | Pruebas |

## 3. Commits chiquitos

Un commit = un cambio. Ideal 10 archivos o menos. Si un commit toca muchos archivos
porque es un solo cambio (por ejemplo, re-exportar todos los modelos), se explica en
el cuerpo.

```
feat(cascanueces): agrega el estado de sospecha
fix(cascanueces): recoloca al agente si arranca fuera del navmesh
feat(modelos): re-exporta las casas con el estilo low-poly
docs(graficos): crea el maestro del menú de gráficos
```

## 4. Antes de commitear

1. `git status` para ver qué se va a subir.
2. Que no entren `Library/`, `Builds/` ni secretos (ver `REGLAS_IGNORE.md`).
3. `git add` por rutas, no `git add .` a ciegas.
4. Cada asset va con su `.meta`: si falta, Unity pierde las referencias.
