# ANALISIS · Rendimiento

- Fecha: 27/11/2026
- Equipo: laptop Intel Core Ultra 5 225H, gráficos Intel Arc integrados (Mesa, OpenGL), 16 GB RAM.
- Herramienta: `Assets/Scripts/Juego/Benchmark.cs`. Se corre el build con
  `./TurnoDeNoche.x86_64 -benchmark` y escribe `benchmark.txt` en la carpeta de datos del juego
  (`~/.config/unity3d/DefaultCompany/Turno de Noche en el Taller/`). Mide 3 s por vista sin VSync.

## Escena

| Grupo | Triángulos (LOD0) |
|---|---|
| `--- AMBIENTACION ---` | ~2.0 M (pinos 700 k, luces del pueblo 177 k, casas 280 k) |
| Resto (árbol, personajes, piezas, historia) | ~0.35 M |
| Luces | 56 activas (49 puntuales), 5 con sombra |
| Partículas | 23 sistemas |

## Resultados (ms por cuadro, FPS entre paréntesis, ventana 1920x1200)

| Prueba | Taller | Árbol | Pueblo |
|---|---|---|---|
| Como estaba (= Alto) | 29.3 (34) | 30.2 (33) | 27.8 (36) |
| Sin SSAO | 25.2 (40) | 27.1 (37) | 25.0 (40) |
| Sin sombras | 22.6 (44) | 23.8 (42) | 24.4 (41) |
| Sombras a 20 m | 27.5 (36) | 29.8 (34) | 25.8 (39) |
| Resolución 75 % | 21.8 (46) | 29.5 (34) | 22.6 (44) |
| Sin luces del pueblo | 27.2 (37) | 32.8 (30) | 26.9 (37) |
| Sin postproceso | 26.7 (37) | 29.5 (34) | 26.2 (38) |
| **Preset Alto** | 26.1 (38) | 29.3 (34) | 26.3 (38) |
| **Preset Medio** | 19.6 (51) | 21.6 (46) | 18.2 (55) |
| **Preset Bajo** | 15.5 (64) | 16.6 (60) | 14.0 (72) |

## Hallazgos

| # | Severidad | Hallazgo | Estado |
|---|---|---|---|
| R1 | Alta | En el build los cascanueces nacían fuera del NavMesh ("Failed to create agent") y se quedaban quietos. | Resuelto: `Cascanueces.AcomodarEnNavMesh` (SamplePosition + Warp). Medido 3/3 sobre el NavMesh. |
| R2 | Media | Lo que más cuesta es la GPU: sombras (~6 ms), SSAO (~4 ms) y resolución. Los triángulos casi no pesan (lodBias no cambia el resultado). | Resuelto con los presets de `MAESTRO_graficos.md`. |
| R3 | Media | Sin foco, el build se pausa (`runInBackground` apagado) y el editor corre a 1 FPS: no medir así. | Documentado; el benchmark prende `runInBackground`. |
| R4 | Baja | Distancia de dibujado menor a 200 m borra las montañas (radio 118-200 m) y el horizonte queda como mancha de niebla. | Resuelto: mínimo 180 m, Bajo usa 210 m. |
| R5 | Pendiente | Para teléfono y navegador (WebGL) hará falta más: LOD en casas y farolitos, luces del pueblo como emisión. | Ver `MAESTRO_movil.md`. |
