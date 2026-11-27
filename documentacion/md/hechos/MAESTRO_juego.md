# MAESTRO · Juego (sistemas y escena)

- Estado: Hecho
- Creado: 22/11/2026 · Actualizado: 27/11/2026

## Objetivo
Prototipo 3D jugable con temática de "una navidad diferente": el elfo arma el gran
árbol del taller antes del amanecer mientras los cascanueces lo persiguen.

## Escena
`Assets/Scenes/Taller.unity` (única escena del build). Raíces principales:

| Objeto | Qué tiene |
|---|---|
| `--- AMBIENTACION ---` | Edificio, props del taller, exterior, pueblo, luces, efectos |
| `--- NIVEL (greybox) ---` | Cubos de colisión con el render apagado |
| `--- PIEZAS ---` | Piezas del árbol, `RepartidorPiezas`, puntos al azar y refacciones |
| `--- ENEMIGOS ---` | Cascanueces, cascanueces nevados y cajas sorpresa |
| `--- HISTORIA ---` | Letreros y notas |
| `--- COLECCIONABLES ---` | 10 galletas |
| `--- DIRECTOR ---` | `DirectorJuego`, `RelojAmanecer`, cámaras de cinemática |
| `--- NAVMESH ---` | NavMeshSurface (`Taller_NavMesh_v2.asset`) |
| `Jugador` | Prefab del elfo con controlador, inventario, interacción y cámara |

## Sistemas (Assets/Scripts)

| Carpeta | Scripts principales |
|---|---|
| `Juego/` | `Juego` (estado global), `DirectorJuego` (título, menús, cinemáticas, final), `Dificultad`, `Vidas`, `Medallas`, `GestorAudio`, `Opciones`, `Benchmark` |
| `Jugador/` | `ElfoController`, `ElfoAnimador` (animación procedural), `VarianteElfo`, `Inventario`, `Interactor`, `LanzadorNieve`, `Linterna`, `FrioJugador` |
| `Enemigos/` | `Cascanueces` (máquina de estados sobre NavMeshAgent), `CascanuecesAnimador`, `CascanuecesNevado`, `CajaSorpresa` |
| `Arbol/` | `ArbolNavidad` (etapas y piezas), `LucesArbol` |
| `Interaccion/` | `Interactuable`, `Recogible`, `RenoGuirnalda`, `MaquinaRota`, `Galleta`, `Letrero` |
| `Ambiente/` | Luces parpadeantes, brillo emisivo, nieve, ventisca, apagón, trineo volador |
| `UI/` | HUD (objetivo, brújula, avisos, corazones), historia, banners, fundidos |

## Flujo de una partida
Título -> elegir elfo -> elegir dificultad -> intro -> 5 etapas (Maceta, 3 Ramas,
6 Esferas, Guirnalda con el reno, Estrella) -> árbol encendido -> trineo de Santa ->
créditos con medallas. Si amanece (6 AM) o se acaban las vidas: derrota con reintento.

## Dificultad
Fácil, Medio, Difícil e Imposible cambian velocidad, vista y oído de los cascanueces,
minutos del reloj, vidas, linterna con pila, apagón, ventisca, cascanueces nevados y
cajas sorpresa. Todo se configura en `Dificultad.Datos`.

## Notas técnicas
- Domain Reload desactivado: cualquier `static` nuevo se reinicia en `Juego.Reiniciar()`.
- Input System nuevo (`Keyboard.current`, `Mouse.current`).
- La animación de personajes es por código: los modelos deben conservar nombres y pivotes.

## Pruebas
- `Juego.PruebaAutomatica = true` + `ArbolNavidad.ColocarSiguiente()` x12 recorre la
  partida completa hasta los créditos sin errores.
- Build de Linux: `Builds/Linux/TurnoDeNoche.x86_64`.
