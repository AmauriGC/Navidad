# Reglas de ignore

> Qué no se sube a Git y por qué. El archivo real es `.gitignore` en la raíz.

| Ruta / patrón | Por qué no se sube |
|---|---|
| `Library/`, `Temp/`, `Obj/`, `Logs/` | Unity los regenera al abrir el proyecto (pesan GB) |
| `UserSettings/` | Preferencias personales del editor |
| `Builds/`, `*.apk`, `*.aab` | Ejecutables: se generan con File > Build |
| `*.csproj`, `*.sln`, `*.slnx`, `.vscode/`, `.idea/` | Los genera el IDE |
| `*.blend1`, `*.blend2` | Respaldos automáticos de Blender |
| `__pycache__/` | Caché de Python |
| `.env`, `*.keystore`, `*.jks` | Secretos y llaves de firma de Android |

## Sí se suben

- `Assets/` con todos sus `.meta` (guardan los GUID que unen escenas, prefabs y modelos).
- `Packages/manifest.json` y `packages-lock.json`.
- `ProjectSettings/`.
- `Blender/Navidad_modelos.blend` y los scripts `.py`.

## Tamaño

GitHub rechaza archivos de más de 100 MB. Hoy el más grande es
`Modelos_Vitrina/Vitrina_todos_los_modelos.glb` (29 MB). Si algo pasa de 50 MB,
usar Git LFS (`git lfs track "*.blend"`).
