# Turno de Noche en el Taller

Juego 3D navideño hecho en Unity para el Mini Game Jam "Una navidad diferente".
Los cascanueces tumbaron el gran árbol del taller y escondieron sus piezas: el elfo
tiene que encontrarlas por la fábrica, el establo y el pueblo, y armar el árbol antes
del amanecer sin que lo atrapen.

Autor: Cristian Amauri Gonzaga Castañeda.

## Jugar

- **En el navegador (compu o celular):** https://amaurigc.github.io/Navidad/
- **Android (APK):** https://github.com/AmauriGC/Navidad/releases/latest

## Estructura del repositorio

```
Navidad/
├── Assets/            <- proyecto de Unity (escenas, scripts, prefabs, modelos .glb, audio)
├── Packages/          <- paquetes de Unity (manifest)
├── ProjectSettings/   <- configuración del proyecto
├── Blender/           <- archivo .blend y scripts de Python que generan los modelos
├── Herramientas/      <- generador de música y efectos (Python + numpy)
├── Modelos_Vitrina/   <- todos los modelos juntos (.blend y .glb) para mostrarlos
├── documentacion/     <- documentación del proyecto (empieza por documentacion/README.md)
├── CLAUDE.md          <- notas técnicas detalladas para el asistente de IA
└── PLAN.md            <- plan de pulido por fases
```

## Requisitos

- Unity 6000.6.10f1 con URP 17.6 (módulo Linux Build Support; Android para teléfono).
- Blender 5.3 (solo para editar los modelos).
- Python 3 con numpy (solo para regenerar el audio).

## Cómo abrirlo

```bash
git clone https://github.com/AmauriGC/Navidad.git
cd Navidad
git switch develop
```

Abrir la carpeta con Unity Hub y cargar la escena `Assets/Scenes/Taller.unity`.
La primera vez Unity regenera la carpeta `Library/` (tarda unos minutos).

## Controles

| Acción | Teclado y mouse |
|---|---|
| Moverse | WASD |
| Correr | Shift |
| Saltar | Espacio |
| Cámara | Mouse (rueda = zoom) |
| Interactuar / lanzar | E / clic |
| Soltar | Q |
| Pausa | Esc |

## Ramas

`develop` es la rama de trabajo; `test` recibe lo que está listo para probar y `main`
la versión estable. Ver `documentacion/git/FLUJO_GIT.md`.
