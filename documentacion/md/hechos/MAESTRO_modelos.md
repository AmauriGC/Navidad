# MAESTRO · Modelos 3D (Blender -> Unity)

- Estado: Hecho
- Creado: 22/11/2026 · Actualizado: 27/11/2026

## Objetivo
Que todos los modelos del juego estén hechos en Blender (nada de primitivas de Unity),
con un estilo low-poly redondeado: bisel, caras planas y colores tipo plástico.

## Flujo
1. Modelar con scripts de Python en `Blender/` (cada script rehace un modelo y respeta
   nombres y pivotes). Librerías comunes: `modelado.py`, `suavizado.py`, `lowpoly.py`.
2. Revisar en la escena "Vitrina" de Blender (copias `VT_*`) y aprobar.
3. Exportar a `Assets/Modelos/*.glb` con `exportar_glb(...)`.
4. Unity lo importa con glTFast; los prefabs de `Assets/Prefabs/` se actualizan solos.
5. Verificar en Unity: materiales contra submallas, colliders y una partida en Play.

## Reglas
- El origen va en la base del modelo; las piezas animadas tienen el pivote en la articulación.
- Coordenadas: Unity (x, y, z) = Blender (-x, z, -y).
- Antes de exportar, deseleccionar todo en la Vitrina (el exportador también toma lo
  seleccionado en otras escenas).
- Respaldos de cada .glb anterior en `Library/BlenderBackup/` (solo local).

## Archivos
- `Blender/Navidad_modelos.blend`: archivo maestro con todas las colecciones.
- `Modelos_Vitrina/`: todos los modelos juntos para enseñarlos.
- `Herramientas/generar_audio.py`: música y efectos sintetizados (no es de modelos,
  pero sigue la misma idea: todo se genera con código).
