# MAESTRO · Detallitos del juego

- Estado: En progreso
- Creado: 27/11/2026 · Actualizado: 27/11/2026

## Objetivo
Versión destino: **1.5** (junto con la historia nueva de la Máquina 7; hoy está la 1.4 en GitHub).
Pulir detalles que se notan al jugar: cara y sonidos de los cascanueces, ventisca, perseguidores
afuera, bola de nieve, bloque de hielo, galletas, menú de pausa y reno.

## Alcance
- Incluye: modelos de Blender (estilo low-poly con caras planas), scripts de juego, sonidos nuevos.
- No incluye: el tráiler.

## Fases (de una en una; el autor revisa en Blender/Unity antes de seguir)
- [x] Fase 1 — Caras (27/11, aprobadas): cascanueces con el DISEÑO ORIGINAL (pelito, cejas, bigote, barba de bolitas)
      y la boca corregida (`Blender/cascanueces_cara_v4.py`, usa helpers de `cascanueces_cara_v3.py`): cráneo con ventana
      de boca recortada y hueco oscuro `Cas_Boca`, palanca = pedazo del mismo cráneo al ras, dientes pintados, barba
      pegada a la palanca, pupila roja chica; bisagra en (0,-0.02,1.255). La v3 (juguete pintado) se descartó.
      `CascanuecesAnimador`: mordida máx. 12°, la cabeza se echa atrás al morder; ojos (1,0,0.02) × 1.4
      (con ACES, 2.5 ya se aclaraba). Elfo (`Blender/elfo_cara_v3.py`): misma carita pegada a la piel real de la
      cabeza (rayos contra la malla), sirve para los 4 elfos. Partida automática hasta el Final: 0 errores.
- [ ] Fase 2 — Sonidos de los cascanueces (entrada 3D, clac y pasos más audibles, voces `voz_cas`; semilla nueva).
- [ ] Fase 3 — Ventisca bonita (copos en capas, ráfagas al ras del suelo) y mancha negra sobre el establo.
- [ ] Fase 4 — Cascanueces que persiguen afuera en Difícil/Imposible (`Dificultad.Datos`).
- [ ] Fase 5 — Bola de nieve: estela al lanzar, explosión con trocitos al pegar.
- [ ] Fase 6 — Bloque de hielo de cristal low-poly.
- [ ] Fase 7 — Galletas que brillan parejo por los dos lados.
- [ ] Fase 8 — Menú de pausa navideño.
- [ ] Fase 9 — Reno: la cabeza gira desde el cuello sin "romperse".

## Criterios de aceptación
- Cada fase aprobada por el autor en Blender/Unity.
- 0 errores en consola en Play; partida automática completa.

## Pruebas
- Capturas antes/después en `Library/Capturas/`.
- Respaldos en `Library/BlenderBackup/` (`antes_cara_cascanueces.blend`, `Cascanueces_antes_cara_v3.glb`).
