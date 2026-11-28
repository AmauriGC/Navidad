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
- [x] Fase 2 — Sonidos de los cascanueces (entrada 3D, clac y pasos más audibles, voces `voz_cas`; semilla nueva).
  Hecho 28/11: `GloboCascanueces` (globito de diálogo con voz de madera `voz_cas`), gritos al sospechar/ver/perder/atrapar/aturdir/descarga, `cas_arranque` al despertar y pasos `paso_cas3/4` (semilla 28, `generar_audio.detallitos()`).
- [x] Fase 3 — Ventisca bonita (copos en capas, ráfagas al ras del suelo) y mancha negra sobre el establo.
  Hecho 28/11: `VentiscaBonita` (copos grandes, ráfagas al ras, velo) y el cielo se tapa con la niebla de la tormenta (`_Niebla` en CieloNocturno.shader): ya no queda la mancha negra.
- [x] Fase 4 — Cascanueces que persiguen afuera en Difícil/Imposible (`Dificultad.Datos`).
  Hecho 28/11: `Dificultad.Datos.rastreoAfuera` (Difícil 7 s, Imposible 11 s): afuera siguen tus huellas y tardan más en olvidarte.
- [x] Fase 5 — Bola de nieve: estela al lanzar, explosión con trocitos al pegar.
  Hecho 28/11: `BolaNieve.Estela()` (TrailRenderer + polvito) y `Trocitos()` (partículas Mesh que rebotan).
- [x] Fase 6 — Bloque de hielo de cristal low-poly.
  Hecho 28/11: `Blender/hielo.py` → `hacer_hielo_cristal()` (gema con aristas blancas y picos de cristal).
- [x] Fase 7 — Galletas que brillan parejo por los dos lados.
  Hecho 28/11: `Galleta.BrilloParejo` (emisión propia de cada material + luz centrada arriba).
- [x] Fase 8 — Menú de pausa navideño.
  Hecho 28/11: `UIPausaNavidad.Decorar` (copos, bastón de caramelo, acebo, foquitos que titilan, nieve en la tarjeta).
- [x] Fase 9 — Reno: la cabeza gira desde el cuello sin "romperse".
  Hecho 28/11: la cabeza gira sobre el eje del cuello (`RenoAnimador`) y la punta del cuello del cuerpo quedó redonda alrededor de ese eje (`renos.cuello_redondo`).

## Criterios de aceptación
- Cada fase aprobada por el autor en Blender/Unity.
- 0 errores en consola en Play; partida automática completa.

## Pruebas
- Capturas antes/después en `Library/Capturas/`.
- Respaldos en `Library/BlenderBackup/` (`antes_cara_cascanueces.blend`, `Cascanueces_antes_cara_v3.glb`).
