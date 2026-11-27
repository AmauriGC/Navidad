# MAESTRO · Menú de gráficos

- Estado: Hecho
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
| Resolución (escala de render) | 70 % | 85 % | 100 % |
| Sombras | 15 m, mapa 1024, 1 cascada | 25 m, 2048, 2 cascadas | 35 m, 2048, 2 cascadas |
| Oclusión ambiental (SSAO) | No | No | Sí |
| Resplandor (bloom) | Sí | Sí | Sí |
| Detalle lejano (lodBias) | 0.7 | 1.2 | 2.0 |
| Luces del pueblo (puntuales) | Pocas (25 m) | Cercanas (55 m) | Todas |
| Partículas (nieve, humo) | 40 % | 70 % | 100 % |
| Distancia de dibujado | 210 m | 250 m | 300 m |
| VSync / límite de FPS | 60 | VSync | VSync |

Personalizado = cada fila editable con un deslizador o selector.

## Fases
- [x] Fase 1 — `Graficos` (static, PlayerPrefs) que aplica cada opción sobre el asset
      URP en tiempo de ejecución (renderScale, shadowDistance, lodBias, SSAO, etc.).
- [x] Fase 2 — Pantalla en la pausa con `UIConstructor` (selector de preset + filas).
- [x] Fase 3 — Detección inicial: si es teléfono o GPU integrada, arrancar en Bajo/Medio.
- [x] Fase 4 — Medir con el `Benchmark` del build cada preset y ajustar valores.

## Dependencias
- `documentacion/md/analisis/ANALISIS_RENDIMIENTO.md` (qué opción cuesta más).

## Criterios de aceptación
- Cambiar de preset se nota al momento y se recuerda al reiniciar el juego.
- Bajo da al menos 60 FPS en la laptop de desarrollo en las tres vistas del benchmark.

## Resultado
- Código: `Assets/Scripts/Juego/Graficos.cs` (presets, guardado y `LucesCercanas`) y
  `Assets/Scripts/UI/UIGraficos.cs` (pestaña). En la pausa: pestañas Opciones | Gráficos (clic o [Tab]).
- Primera vez: Bajo en teléfono/navegador, Medio con gráficos integrados, Alto con tarjeta dedicada.
- Medición en el build: Bajo 60-72 FPS, Medio 46-55, Alto 33-38 (ver `../analisis/ANALISIS_RENDIMIENTO.md`).
- En el editor, al salir de Play el asset URP regresa a sus valores (verificado: no queda modificado).
