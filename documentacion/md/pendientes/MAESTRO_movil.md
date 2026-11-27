# MAESTRO · Versión para teléfono (Android)

- Estado: Pendiente (propuesta, falta aprobarla)
- Creado: 27/11/2026 · Actualizado: 27/11/2026

## Objetivo
Que el juego se pueda instalar y jugar en un teléfono Android con controles táctiles.

## Lo que falta hoy
1. **Módulo Android** en Unity Hub para 6000.6.10f1 (Android Build Support + OpenJDK
   + SDK & NDK Tools). Hoy solo está instalado Linux Build Support.
2. **Controles táctiles**: el juego usa teclado y mouse. Se necesita:
   joystick virtual (mover), arrastrar en la mitad derecha (cámara), botones de
   Saltar, Correr, Interactuar (E), Lanzar bola y Soltar (Q), botón de Pausa, y que
   los menús (elfo, dificultad, diálogos) acepten toques.
3. **Rendimiento**: la escena tiene ~2.4 millones de triángulos, ~56 luces y SSAO.
   Un teléfono necesita el preset Bajo del menú de gráficos y además:
   LOD en casas y farolitos, luces del pueblo horneadas o como emisión, menos partículas.
4. **Pantalla**: orientación horizontal, interfaz que se acomode a distintas
   proporciones (Canvas Scaler) y zonas seguras (notch).

## Fases
- [ ] Fase 1 — Instalar el módulo Android y hacer un build de prueba (APK) tal cual.
- [ ] Fase 2 — `ControlesTactiles`: joystick + botones con el Input System
      (On-Screen Stick / On-Screen Button) que escriben en las mismas acciones que el teclado.
- [ ] Fase 3 — Menús e historia con toques.
- [ ] Fase 4 — Preset gráfico Móvil (depende de `MAESTRO_graficos.md`) y optimizaciones.
- [ ] Fase 5 — Firma del APK (keystore fuera del repo) y prueba en el teléfono.

## Dependencias
- `MAESTRO_graficos.md` y `../analisis/ANALISIS_RENDIMIENTO.md`.

## Criterios de aceptación
- Se instala el APK, se juega una partida completa solo con toques a 30 FPS estables.
