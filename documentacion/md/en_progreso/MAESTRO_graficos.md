# MAESTRO · Menú de gráficos

- Estado: Pendiente (propuesta, falta aprobarla)
- Creado: 27/11/2026 · Actualizado: 27/11/2026

## Objetivo
Agregar a la pausa (y al título) un apartado de Gráficos con presets Bajo, Medio, Alto
y Personalizado, para que el juego corra bien en computadoras modestas y en teléfono
sin perder calidad en las que sí pueden.

## Alcance
- Incluye: presets, opciones sueltas en Personalizado, guardado en PlayerPrefs,
  aplicar en caliente (sin reiniciar).
- No incluye: cambiar modelos ni texturas (eso va en optimizaciones, ver análisis).

## Opciones propuestas

| Opción | Bajo | Medio | Alto |
|---|---|---|---|
| Escala de render | 0.7 | 0.85 | 1.0 |
| Sombras (distancia) | 15 m, mapa 1024 | 25 m, 2048 | 35 m, 2048 |
| Oclusión ambiental (SSAO) | No | No | Sí |
| Bloom | Sí (bajo) | Sí | Sí |
| Detalle a distancia (lodBias) | 0.8 | 1.2 | 2.0 |
| Luces del pueblo (puntuales) | Solo cercanas | Cercanas | Todas |
| Partículas (nieve, humo) | 35 % | 70 % | 100 % |
| Distancia de dibujado | 120 m | 200 m | 300 m |
| VSync / límite de FPS | 30 | 60 | VSync |

Personalizado = cada fila editable con un deslizador o selector.

## Fases
- [ ] Fase 1 — `Graficos` (static, PlayerPrefs) que aplica cada opción sobre el asset
      URP en tiempo de ejecución (renderScale, shadowDistance, lodBias, SSAO, etc.).
- [ ] Fase 2 — Pantalla en la pausa con `UIConstructor` (selector de preset + filas).
- [ ] Fase 3 — Detección inicial: si es teléfono o GPU integrada, arrancar en Bajo/Medio.
- [ ] Fase 4 — Medir con el `Benchmark` del build cada preset y ajustar valores.

## Dependencias
- `documentacion/md/analisis/ANALISIS_RENDIMIENTO.md` (qué opción cuesta más).

## Criterios de aceptación
- Cambiar de preset se nota al momento y se recuerda al reiniciar el juego.
- Bajo da al menos 60 FPS en la laptop de desarrollo en las tres vistas del benchmark.
