# Proyecto Navidad (Unity) — Mini Game Jam — contexto para Claude Code

## La actividad
**🎄 Mini Game Jam — "Una navidad diferente" 💀 (3D OBLIGATORIO)** — 100 puntos.
- **Fecha límite: 4 de diciembre de 2026, 11:59 p.m.**
- Crear un **prototipo jugable propio en 3D** usando lo aprendido en el curso.
- Temática (solo condición visual/conceptual): **una navidad distinta a la ordinaria**.
  Se vale la navidad normal o una navidad "diferente" (ej. terror, apocalíptica, rara).
- El alumno quiere hacerlo **más interesante** y crear los **modelos 3D con Blender**.
- Idea del juego: **por definir** (platicarla antes de empezar a construir).

## Entorno
- Unity **6000.6.10f1**, **URP 17.6**, Input System nuevo (`activeInputHandler: 1`, usar `Keyboard.current` / `Mouse.current`).
- Proyecto recién creado: solo tiene `Assets/Scenes/SampleScene.unity`.
- SO: **Arch Linux**. Python, `uv`/`uvx` y git instalados.
- **Blender 5.3 (Flatpak `org.blender.Blender`)** con el addon **"MCP for Blender"** (ahujasid/blender-mcp v2.0)
  escuchando en `127.0.0.1:9876`. Las opciones de Poly Haven / Sketchfab / Hyper3D / etc. van **apagadas**.

## MCP
- **UnityMCP** (paquete `com.coplaydev.unity-mcp`) por HTTP en `http://127.0.0.1:8080/mcp`.
  En Unity: Window > MCP for Unity debe decir **Session Active (Navidad)**.
- **Blender NO aparece en `/mcp`**: se usa a través de Unity con la herramienta `blender_bridge`
  (Claude → UnityMCP → Blender). Acciones útiles: `status`, `scene_info`, `run_python` (modelar con bpy),
  `screenshot`, `import_model` (exporta .glb e importa/coloca en Unity), `compare_screenshot`, `setup_bloom`.
- Orden de arranque: Blender (addon conectado) → Unity (Session Active) → Claude Code en esta carpeta.
- Si Blender se cierra, hay que volver a presionar **Connect** en el panel N > "MCP for Blender".
- **`import_model` NO funciona** con Blender Flatpak (su `/tmp` está aislado). Flujo que sí funciona:
  `run_python` exportando con `bpy.ops.export_scene.gltf(filepath=".../Navidad/Assets/Modelos/X.glb", use_selection=True)`
  → Unity lo importa con **glTFast** (`com.unity.cloud.gltfast`, ya instalado) → crear prefab en `Assets/Prefabs/`.
- En Blender 5 el nodo Principled BSDF se busca por tipo (`n.type == "BSDF_PRINCIPLED"`), no por nombre (Blender está en español).
- Al emparentar en bpy sin `matrix_parent_inverse`, los hijos quedan relativos al origen del padre: poner el origen en la base del modelo.
- Capturas de Unity: usar `output_folder="Library/Capturas"` para no ensuciar Assets.

## Estado del juego ("Turno de Noche en el Taller")
**Idea central (confirmada 2026-11-22):** los cascanueces tumbaron el gran árbol del taller y escondieron sus partes;
el elfo recoge piezas por la fábrica y ARMA EL ÁRBOL al centro antes del amanecer. Etapas (12 piezas):
Maceta (establo) → 3 Ramas → 6 Esferas → Guirnalda (enredada en un reno; darle zanahoria — pendiente) → Estrella
(arriba de Repisa_Oeste, con Caja_Escalon_1/2). Al completar: árbol se ilumina + cinemática (pendiente).
- `ArbolNavidad` (en `Assets/Prefabs/ArbolNavidad.prefab`, modelo `Arbol.glb` con hijos Maceta, Nivel1-3,
  Esfera_1-6, Guirnalda, Estrella): Interactuable con `EtapaArbol[]`; oculta partes en Awake y las muestra con
  easeOutBack; collider trigger hasta tener maceta; `lucesProgreso`; eventos `alColocarPieza`, `alCompletar`, `AlCambiar`.
- Piezas: `Assets/Prefabs/Piezas/Pieza_*.prefab` (Recogible tipo Maceta/Rama/Esfera/Guirnalda/Estrella), en `--- PIEZAS ---`.
- `UIObjetivo` (HUD/Objetivo): título X/12, barra y pista de la etapa.
- **Día 28 (hecho):** `RenoGuirnalda` en Reno_1 (Interactuable): la Guirnalda empieza encima del reno con
  `Recogible.bloqueado`; al darle la `Zanahoria` (Pieza_Zanahoria, nariz del muñeco de nieve en el patio junto al
  establo, (16, 2.14, -10)) brinca y la guirnalda cae con `Recogible.Liberar` (arco). Portón nuevo en la cerca
  este del establo (`Establo_Porton`, colisiones Cerca_Este_Sur/Norte) = salida al patio.
  `UIAviso.Mensaje(texto, seg)` = mensajes temporales con prioridad. `ArbolNavidad.destellos` (partículas al
  colocar) + mensaje "¡X colocada!". `Interactor.SeVe` = línea de visión (Linecast desde 1.5 m) para no
  interactuar a través de paredes. Luz_Estrella (point sin sombra) en la pieza Estrella.
- **Pendiente pedido por el alumno:** (1) poder explorar AFUERA del patio (colisiones en pinos/casas/lomas,
  quitar paredes invisibles de `Colisiones_Patio`); (2) subir calidad de modelos: más segmentos en
  cilindros/esferas, biselado en cajas, smooth en lo redondo. Ambos para días de pulido.
- Las capturas posicionadas (`view_position`) NO muestran UI ni partículas transparentes; la captura de
  game_view con Main Camera en Play sí. Para revisar algo concreto, teletransportar al Jugador (`Teletransportar`).
- **Piezas recogibles:** cada una es UNA sola malla (jerarquía horneada en Blender), si no la escala se rompe.

## Ambientación (días 26–27, hecha)
- Blender: helpers en `bpy.app.driver_namespace["H"]` (se pierden al cerrar Blender): `H.U(x,y,z)` convierte
  coordenadas de Unity → Blender (unity = (-bx, bz, -by)), `H.Builder` (cajas/cilindros/esferas en coords Unity en una
  sola malla), `H.exportar(objs, "X.glb")`, `H.M` paleta. Colecciones: Edificio, Props, Exterior, Arbol, Piezas, Elfo.
- `Edificio.glb` (paredes con ventanas, piso, techo, establo), `Props_Taller.glb` (Chimenea, Repisas, Mesa_1-3, Cajas,
  Maquina, Maquina_LuzAlerta, Heno, Lamparas, Guirnaldas, Guirnaldas_Focos, Coronas), `Exterior.glb` (suelo con
  lomas, montañas, pinos, cabañas, muñeco de nieve, faroles, cerca). Todo bajo `--- AMBIENTACION ---`.
- Los cubos greybox siguen siendo las COLISIONES (renderer apagado). Pinos greybox desactivados.
- Exterior (rehecho 23-nov): patio cercado X -16..26, Z -13..13 con colisiones invisibles de 1.8 m
  (`--- NIVEL (greybox) ---/Exterior/Colisiones_Patio`: cerca, faroles, muñeco, rocas, arbustos, troncos);
  SueloNieve visual con MeshCollider. Fuera del patio: 4 tipos de pino (Abeto, Picea, Nevado, Joven), 5 casas
  (CasaTroncos, CasaRoja/Azul/Verde de 2 pisos, CasaA) con humo (`Efectos/Humo`), rocas y arbustos. Las mallas
  base se reutilizan como instancias (`bpy.app.driver_namespace["EXT"]`).
- Luces: solo Luz_Chimenea es Point con sombra; lámparas del taller/establo son Spot hacia abajo (evita el
  aviso de "too many shadowed punctual lights": cada Point usa 6 mapas de sombra, cada Spot 1).
- Cielo: shader `Assets/Shaders/CieloNocturno.shader` (degradado, estrellas, luna, aurora) → material skybox.
- Efectos (`--- AMBIENTACION ---/Efectos`): fuego/brasas (emisor girado -90° en X), chispas de la máquina (bursts +
  colisión), 4 zonas de nieve alrededor del edificio, luz de alerta, luces de faroles.
- Scripts: `LuzParpadeante` (Perlin, en Luz_Chimenea), `BrilloEmisivo` (anima "emissiveFactor" de glTFast; Titilar
  en guirnaldas y guirnalda del árbol, Alerta en la máquina).
- Escena principal: `Assets/Scenes/Taller.unity` (en Build Settings). Greybox con taller, establo, exterior, luces nocturnas
  y Global Volume (`Assets/Settings/TallerVolumeProfile.asset`: Bloom, ACES, Viñeta, Color).
- Materiales de prueba en `Assets/Materials/Greybox/`. Primer modelo: `Assets/Modelos/Regalo.glb` → `Assets/Prefabs/Regalo.prefab`.
- **Elfo** (`Assets/Modelos/Elfo.glb`, colección "Elfo" en Blender): piezas separadas con pivote en articulaciones
  (PiernaL/R, Cuerpo→BrazoL/R, Cabeza→Gorro→Cascabel, empty PuntoMano). Mira a +Z en Unity.
- **Jugador** (`Assets/Prefabs/Jugador.prefab`, tag Player): CharacterController + `ElfoController` + `Inventario` +
  `Interactor`; hijo `Modelo_Elfo` con `ElfoAnimador` (animación procedural con senos); `LuzElfo`; `ObjetivoCamara`.
- Cámara: Main Camera con CinemachineBrain + `CamaraJugador` (CinemachineCamera, OrbitalFollow Sphere en
  BindingMode WorldSpace, RotationComposer, Deoccluder ignorando tag Player, `CamaraOrbitaMouse`).
- Interacción: `Interactuable` (base abstracta) → `Recogible` (tipo string). `UIAviso` en el Canvas `HUD`
  (uGUI Text legacy por ahora; cambiar a TextMeshPro en el día de UI).
- Controles: WASD mover, Shift correr, Espacio saltar, mouse cámara, rueda zoom, E interactuar, Q soltar, Esc cursor.
- Simular teclas con `InputSystem.QueueStateEvent` no sirve si el Game View no tiene foco: pedir al alumno que pruebe.

## Lecciones de la práctica anterior (proyecto Practica)
- Para cambiar valores de **instancias de prefab** desde código usar `SerializedObject` (o `Undo.RecordObject` +
  `PrefabUtility.RecordPrefabInstancePropertyModifications`); si no, el cambio no se guarda en la escena.
- Si se usa NavMesh: instalar **AI Navigation** (`com.unity.ai.navigation`), NavMesh Surface + Bake guardando el
  NavMeshData como asset junto a la escena; poner `NavMeshModifier (ignoreFromBuild)` a objetos que se mueven.
- Las escenas que se recargan con `SceneManager.LoadScene` deben estar en **Build Settings**.
- `execute_code` del MCP usa compilador CodeDom (C# 6): usar `UnityEngine.Object` explícito.
- Este proyecto tiene **Domain Reload desactivado** (Enter Play Mode Options): los `static` NO se reinician al dar Play.
  `Juego.Reiniciar()` ([RuntimeInitializeOnLoadMethod]) resetea Estado/PruebaAutomatica/timeScale; cualquier static
  nuevo debe reiniciarse ahí. Cámaras: CamaraJugador prioridad 10, CamCinematica 100 en escena / -1 al soltar.

## Organización sugerida
- `Assets/Scenes/`, `Assets/Scripts/`, `Assets/Prefabs/`, `Assets/Materials/`,
  `Assets/Modelos/` (los .glb importados desde Blender), `Assets/Audio/`.
- Estilo de modelos sugerido: **low-poly** con colores planos / emisión (+ Bloom para luces navideñas).

## Reglas de trabajo
- Explicar lo que se hace: el alumno debe entender cómo funciona cada sistema (para poder presentarlo).
- Antes de construir algo grande, proponer el plan y confirmarlo.
- No eliminar objetos existentes de la escena sin preguntar. Guardar la escena después de cambios.
- **No usar git** a menos que el alumno lo pida (el repo se hará después en GitHub).

## Sesión nocturna 23-nov (hecho / pendiente)
- HECHO: cascanueces (modelo, `Cascanueces` IA NavMesh + `CascanuecesAnimador`), NavMesh (`--- NAVMESH ---`,
  Taller_NavMesh.asset), bolas de nieve (`LanzadorNieve`, `BolaNieve`, `MontonNieve`), narrativa (`Guion.cs`,
  `UIHistoria`, `UIBanner`, `UIFundido`, `Letrero` x10 en `--- HISTORIA ---`), `DirectorJuego` (título, intro,
  cinemáticas por etapa, pausa Esc, final con trineo, créditos), renos y trineos modelados, exterior explorable
  (colliders, límite circular). `Juego.PruebaAutomatica` = solo pruebas (avanza diálogos solo).
- Verificado en Play (partida automática completa, 0 errores): título, intro, banners, las 5 etapas con sus
  cinemáticas, despertar de los 3 cascanueces, persecución/atrapar, aturdido, final (árbol encendido, cascanueces
  congelados, amanecer + trineo de Santa) y créditos.
- Modelos pulidos (biselado + smooth) EXPORTADOS a todos los .glb y reimportados. Archivo de Blender completo en
  `Blender/Navidad_modelos.blend` (respaldos en Library/BlenderBackup/). Toma_Exterior en (10, 9, -34).
- PENDIENTE: audio (música/efectos); que el alumno juegue a mano y ajuste dificultad.

## Colisiones y cámara (23-nov, bloque 1 del plan de pulido)
- Capas: 8 `Decoracion` (el elfo choca, la cámara la ignora: muebles, regalos, renos, cerca, rocas, letreros, árbol,
  cascanueces, piezas), 9 `SoloCamara` (no choca con nada; solo la ve el Deoccluder: MeshCollider `ColCamara` en
  Taller_Techo y Establo). Deoccluder: CollideAgainst = Default+SoloCamara, TransparentLayers = Decoracion, suavizado.
- Pinos: MeshCollider CONVEXO con su propia malla (forma de cono); la cápsula vieja quedó desactivada.
  Si se re-exporta Exterior.glb, revisar que los MeshCollider sigan apuntando a la malla nueva.
- `OcultarSiCamaraCerca` en Jugador: si la cámara está a <1.1 m del ObjetivoCamara, el elfo queda solo como sombra.
- Plan acordado: (1) colisiones/cámara ✔ → (2) modelos más suaves y detallados (rocas, pinos, cerca, casas, props;
  LOD para pinos) → (3) Gran Árbol CLÁSICO muy bonito (verde, esferas rojas/doradas, focos, estrella) + piezas a juego
  → (4) audio, playtest, build, presentación.

## Rendimiento y bloque 2 (23-nov)
- Rendimiento: sin sombra en lo chico/plano (guirnaldas, focos, coronas, letreros, piezas, rocas, suelo, montañas);
  luna con 2 cascadas y 35 m de sombra; solo Luz_Taller_A/C, Luz_Foco_Arbol y Luz_Chimenea con sombra; atlas 2048;
  props del taller con Batching Static. Resultado (misma vista): draw calls 1294→592, tris 1.85M→728k, sombras 1107→405.
  OJO: con Unity sin foco el editor corre a 1 FPS (no medir así; Application.runInBackground no lo evita en el editor).
- Bloque 2 (hecho): pinos (4 tipos, capas con puntas caídas y nieve en la parte visible), rocas (peñas con cortes),
  cerca del patio (postes de tronco, travesaños, nieve, focos colgando). Código en `Blender/generadores_exterior.py`.
- Bloque 2 (hecho también): casas Roja/Azul/Verde con tablones (recortados alrededor de ventanas y bajo el techo con
  BVH), escalón, farolito y nieve al pie; CasaTroncos con leña; CasaA con cuadrícula en el ventanal. Taller: objeto nuevo
  `Detalles_Taller` (Props_Taller.glb): Máquina 7 con manómetros, remaches, franjas, tubería+válvula y banda con juguetes
  con ojos (collider `Col_BandaMaquina`, capa Decoracion); mesas con rollos, carretes, martillos, latas, regalos.
  Guirnaldas/Focos/Coronas restauradas SIN bisel (124k → 9.7k tris). Escena: 845k → 762k tris.
- LECCIÓN: el bisel NO dejó caras con material equivocado en general (el slot 0 suele ser legítimo); solo las casas
  tenían micro-caras (<0.002 m²) con Amb_Piedra2. No hacer correcciones masivas de materiales sin revisar por malla.
- Bloque 3 (hecho, aprobado por el alumno): Gran Árbol CLÁSICO en `Arbol.glb`. Nivel1-3 = 2 faldas de agujas cada uno
  (sin bolitas de nieve); esferas rojo/dorado metálico colocadas sobre la superficie con BVH ray-cast, cada una con hijo
  `Esfera_N_Racimo` (3 bolitas + moño, aparece junto con la esfera); Guirnalda = espiral de 87 focos sobre cable
  (`Arbol_Cable`); Estrella de 5 puntas en diamante + rayitos, emisiva. Piezas a juego: Pieza_Rama (rama de abeto con
  listón), Pieza_Estrella (la misma estrella a escala 0.6), Pieza_Guirnalda (rollo de focos); Esfera/Maceta comparten
  materiales con el árbol. Verificado en Play con `ColocarSiguiente()` x12: todas las partes aparecen, 0 errores.
- Suavizado (24-nov, pedido: "muy puntiagudos"): `Blender/suavizado.py` (se carga con exec en Blender; trae `exportar`,
  ya no depende de H). `falda_suave` = capa de follaje con borde en ONDA (lóbulos redondos, 3 muestras/lóbulo), punta en
  domo y borde enrollado; usada por `pino_suave` (4 pinos) y `arbol_ramas` (Nivel1-3) + `recolocar_esferas` +
  `guirnalda_espiral`; `estrella_inflada` (Chaikin x3, abombada) en Estrella y Pieza_Estrella. Rocas: todo smooth.
  Escena 762k → 864k tris (pinos +~115k). Colliders de pinos verificados (150/150).
- Suavizado parte 2: `corregir_bisel` (por ISLA: caras del bisel con material slot 0 → material de su isla; corrigió la
  franja crema del gorro del cascanueces y ~36k caras en personajes/props/muebles). `redondear` = modificador SUBSURF
  (nivel 1; el bisel hace de borde de apoyo) en Cascanueces, Elfo, cabezas de Renos, Trineos, Cubeta, Regalo.
  `suavizar_normales` = quita sharp < 70° + modificador WEIGHTED_NORMAL (sin triángulos extra) en cuerpos de renos,
  letreros, notas, tablero, montón y muebles (Props). Los modificadores se aplican al exportar (export_apply).
  Exportar personajes/props: raíz en (0,0,0) temporalmente (los .glb tienen la raíz en el origen).
- Regalo.glb rehecho (`regalo_bonito`): una malla, caja + tapa redondeadas, listón, moño de 4 lazos, lunares
  (materiales 0 papel, 1 listón, 2 lunares). Script `ColorRegalo` (MaterialPropertyBlock, [ExecuteAlways]) da color de
  papel/listón por instancia y reemplaza la emisión dorada del listón. Los 6 regalos del árbol con colores distintos.
- Escena ≈ 1.03M tris tras todo el suavizado (Play: 0 errores).
- Cámara al iniciar (24-nov): se metía en Repisa_Sur_A (capa Decoracion la ignora). Fix: hijos `ColCamara` (BoxCollider,
  capa 9 SoloCamara) en Repisa_Sur_A/B, Repisa_Oeste, Chimenea y Maquina. Los Linecast de `Interactor.SeVe` y
  `Cascanueces` usan máscara `~(1 << 9)` para ignorar SoloCamara (si no, la Estrella sobre la repisa no se vería).
- Fuentes (24-nov): `Assets/Resources/Fuentes/` = Fredoka-Medium.ttf (OFL; instancia wght=500 sacada de la variable con
  `uvx --from fonttools fonttools varLib.instancer`) y MountainsofChristmas-Bold.ttf (Apache 2.0), con sus licencias.
  `UIConstructor.Fuente` (Fredoka) para todo; `UIConstructor.Titulo(...)` (Mountains, x1.15) para nombre del juego,
  PAUSA, banners, quién habla, título de notas; UIObjetivo/UIAviso asignan la fuente en Start/Awake.
- El error "PlayerLoop internal function has been called recursively" viene del ScreenshotUtility del MCP al capturar
  en Play; no es del juego.
- Audio (24-nov): TODO sintetizado con `Herramientas/generar_audio.py` (numpy; re-ejecutar para regenerar) →
  `Assets/Resources/Audio/*.wav` (música en Streaming, efectos DecompressOnLoad, Vorbis). Música = villancicos de dominio
  público en caja musical: titulo (Noche de Paz), taller (We Wish You...), persecucion (Carol of the Bells, sol menor),
  final (Jingle Bells). `GestorAudio` (objeto en escena; se crea solo si falta): elige canción por Juego.Estado /
  cascanueces en Persecucion / árbol completo, crossfade con 2 AudioSource; `GestorAudio.Efecto(nombre)` (2D) y
  `Efecto3D(nombre, pos)`; bucles 3D fuego (Luz_Chimenea) y maquina (Maquina), viento 2D; pasos por distancia
  (madera en Piso/Piso_Establo, nieve si el collider se llama *nieve*/*suelo*). Pausa = AudioListener.pause (la música
  sigue, más baja). Efectos conectados en ElfoController (salto), Inventario (recoger/soltar), ArbolNavidad
  (colocar/etapa), LanzadorNieve, BolaNieve, Cascanueces (despertar/clac/alerta/atrapado/aturdido), UIHistoria
  (papel/tick), RenoGuirnalda (reno).
- Bloque 🟢 (24-nov, hecho y verificado en Play):
  * `UIBrujula` (en HUD): flecha arriba al centro → pieza más cercana del tipo de la etapa; si la llevas → árbol;
    si está bloqueada (guirnalda) → zanahoria y luego reno. Sprites de flecha/círculo generados en `UIConstructor`.
  * `RelojAmanecer` (en `--- DIRECTOR ---`): 10 PM → 6 AM en `minutosReales` (15) solo mientras Jugando; avisos a las
    4:00/5:00/5:30; el cielo y ambientLight clarean desde 60%. A las 6 → `DirectorJuego.Amanecio()` → Derrota
    (Guion.Derrota, capa "Amaneció...", [R] Reintentar / [Q] Salir). `Juego.Perdio` (música Noche de Paz) y
    `Juego.Reintento` (salta título/intro → `OtroIntento`), ambos reseteados en Juego.Reiniciar.
  * `Opciones` (PlayerPrefs: Musica, Efectos, Ambiente, Sensibilidad) con sliders en la pausa
    (`UIConstructor.Deslizador`, crea EventSystem + InputSystemUIInputModule si falta). GestorAudio y
    CamaraOrbitaMouse multiplican por ellas. Efectos 2D con ignoreListenerPause.
  * `TemblorCamara` (CinemachineExtension en CamaraJugador, etapa Noise): `TemblorCamara.Sacudir(f)` al atrapar (0.9)
    y al pegarle con bola de nieve (0.25).
  * `PasosElfo` (prefab Jugador; los pasos salieron del GestorAudio): sonido por distancia, huellas (partículas
    Mesh=Quad acostado, rotation3D (90,yaw,0), 18 s) y vaho afuera, con material `Assets/Materials/Particulas_Alfa.mat`.
- Correcciones del playtest (24-nov noche):
  * Hitboxes: cubetas/montones/rocas/arbustos/troncos = MeshCollider CONVEXO con su malla (BoxCollider viejo desactivado);
    pinos = CapsuleCollider radio 0.42·R de su malla (el MeshCollider convexo hacía rampa y el elfo se trepaba);
    faroles radio 0.14; trineo del establo ajustado a 2.45×1.2×1.4.
  * Bola de nieve: PUNTERÍA ASISTIDA en LanzadorNieve (cascanueces despierto más cerca del centro, cono 28°, 18 m,
    Linecast solo capa Default), tiro parabólico con adelanto + mirilla (UIConstructor.SpriteAro). Modelo
    `BolaNieve.glb` (LanzadorNieve.modeloBola está como componente agregado en la escena, no en el prefab).
  * Piezas al azar: `RepartidorPiezas` (en `--- PIEZAS ---`, DefaultExecutionOrder -100) + 38 `PuntoPieza`
    (`--- PIEZAS ---/PuntosPieza`, con zona y 'lejos'); Maceta siempre cerca, máx 3 lejos, zonas distintas por etapa;
    reescribe EtapaArbol.pista. Guirnalda/Estrella/Zanahoria fijas.
  * Modelos: el alumno quiere TODO modelado en Blender (nada de primitivas de Unity). `Blender/renos.py` (renos v2
    con loft orgánico, mismos nombres/pivotes) y `Blender/props_juego.py` (Indicador.glb "!" dorado en los 10
    letreros, Tapete.glb bajo el árbol, BolaNieve.glb). Primitivas viejas con renderer apagado (no borradas).
- Modelos v2 (24-nov noche, pedido: trineo, Santa, elfo, máquina, esferas). Librería común `Blender/modelado.py`
  (loft, esfera, toro, caja con bisel, poner_malla, material, con_hijos, exportar_glb(objs, archivo, raiz)); cargarla con
  exec ANTES de cada script (el namespace de run_python no persiste entre llamadas).
  * `trineo_santa.py`: Trineo (establo) y TrineoSanta (final): tina con secciones Catmull-Rom, patines con voluta,
    barandal dorado con foquitos, cojín/respaldo con botones, acebo; Santa con barba esponjada, bigote, gorro doblado, riendas.
  * `elfo_v2.py`: rehace las 41 piezas del elfo EN COORDENADAS DEL ELFO y las pasa al espacio local de cada pieza
    (mismos nombres/pivotes para ElfoAnimador): cuello de picos, falda con onda, orejas puntiagudas, zapatos enroscados.
  * `maquina_v2.py`: objeto Maquina (Props_Taller.glb, mismo tamaño): cuerpo redondeado, franjas con remaches, pantalla,
    botones, manómetro, palanca, domo, embudo liso, tubos con codos y bridas, engranes con dientes, escotilla, boca de salida
    sobre la banda. Se borraron 38 remaches sueltos de Detalles_Taller. Exportar Props_Taller = toda la colección "Props".
  * `esferas.py`: Esfera_1-6 (lisas 36x22, 3 estilos de decoración) + Esfera_N_Tapa (corona estriada + argolla) y Pieza_Esfera.
  * Respaldos de los .glb anteriores en Library/BlenderBackup/.
- Árbol v3 + ambientación + bloque 🟡 (24-nov noche):
  * `Blender/arbol_bonito.py` (exec suavizado.py + modelado.py antes): Nivel1-3 con 3 faldas, más lóbulos, nervadura clara,
    oropel de cuentas doradas (slot Arbol_Oro); Maceta con aros y moño; recoloca esferas; guirnalda con 117 focos.
  * `LucesArbol` (en ArbolNavidad, hijo LucesColores con 4 Point sin sombra): focos APAGADOS hasta completar; al poner la
    estrella se prenden color por color, 3 parpadeos, luego persecución; estrella destella y late. Desactiva el BrilloEmisivo
    de la Guirnalda.
  * Aurora nueva en `CieloNocturno.shader`: 36 capas de cortinas (orilla verde abajo → violeta → rosa _AuroraC), tramado
    con hash para que no se vean rayas, intensidad 0.085.
  * `Blender/exterior_lindo.py` → `Montanas_v2.glb` (anillo r 118-200, ridged noise, nieve por altura/pendiente; las
    Montanas viejas con renderer apagado) y `Pueblo_Luces.glb` (Senderos a cada casa, 42 Farolito_N con CapsuleCollider
    capa Decoracion, LucesPueblo = focos entre farolitos + aleros de las 9 casas + 10 pinos en espiral con BrilloEmisivo,
    Coronas_Casas). 21 Point cálidas sin sombra en `Pueblo_Luces/Luces_Farolitos`. El script tarda ~2 min y la importación
    del .glb tumba la sesión MCP un rato (esperar y reintentar).
  * `NieveJugador` (hijo del Jugador, copia de Nieve_2, World space) + `NieveSigueJugador`: rayo de ARRIBA hacia abajo
    (los MeshCollider de techos no se detectan por detrás) => no nieva bajo techo.
  * 🟡 `VarianteCascanueces` (Soldado rojo, Explorador verde rápido/ve menos, Capitán azul lento/ve lejos/oye más; colores
    con MaterialPropertyBlock sobre Cas_Rojo/Cas_Azul). `Galleta` (coleccionable, `Blender/galleta.py` → Galleta.glb,
    prefab `Assets/Prefabs/Galleta.prefab`, 10 en `--- COLECCIONABLES ---`, statics Encontradas/Total reiniciados,
    texto HUD "Galletas x/10", resumen en créditos). LODGroup en los pinos (cull 1.5%). Bake de luz NO hecho: los .glb no
    traen UV2 de lightmap y la luz es dinámica (fuego, focos, amanecer).
- Regalo texturizado (pedido de la actividad: low-poly + normal map + texturas): `Blender/regalo_texturizado.py`.
  Malla de 244 triángulos con UVs a mano en un atlas (P lados, T tapa, L canto de la tapa, R listón del moño).
  Texturas 1024² generadas con numpy dentro de Blender → `Assets/Texturas/Regalo_Albedo.png` (sRGB),
  `Regalo_Normal.png` (desde un mapa de altura con diferencias finitas, convención OpenGL/glTF; incluye bisel falso en
  las orillas) y `Regalo_ORM.png` (R oclusión, G rugosidad, B metálico). Material Principled → glTF;
  glTFast lo importa como glTF-pbrMetallicRoughness con las 3 texturas. Prefab `Assets/Prefabs/RegaloTexturizado.prefab`
  (BoxCollider, capa Decoracion), una instancia junto al árbol en (2.6, 0, -1.6).
- Pinos v2 (pedido: tronco = prisma/cubo, follaje = planos con textura apilados, texturas 512 con normales):
  `Blender/pinos_v2.py` → `Assets/Modelos/Pinos_v2.glb` (PinoV2_Abeto/Picea/Nevado/Joven, 38-50 tris: tronco prisma
  triangular + pisos de 3 planos cruzados a 60° con alpha MASK y doble cara) y LucesPino_* (cable = cajitas negras
  sin normal map, focos icoesfera nivel 2 con 5 materiales emisivos FocoPino_*). Texturas 512² en `Assets/Texturas/`:
  Pino_Corteza_Albedo/Normal, Pino_Hojas_Albedo(RGBA)/Normal, Pino_HojasNieve_Albedo/Normal (normales desde mapa de
  altura). En la escena: cada Pino_* conserva objeto + collider + LODGroup; su MeshRenderer viejo está APAGADO y tiene
  hijo `PinoV2` (y en 10 pinos: `LucesPino_*` + `LuzColor` Point sin sombra). LODGroup LOD0 apunta a los renderers nuevos.
  `LucesPinos` (en Efectos): una copia compartida por color, emisión ×3 (con ×7 el ACES los volvía blancos), titileo y
  LuzColor cambiando de tono. Las espirales viejas de 10 pinos se borraron de LucesPueblo (Pueblo_Luces.glb re-exportado;
  respaldo en Library/BlenderBackup/). OJO en scripts: borrar también la malla vieja antes de recrear (si no queda "X.001"
  y Unity pierde la referencia). Blender Flatpak no lee /tmp: copias .blend dentro del proyecto.
- **REVERTIDO (24-nov, 22:30):** el alumno descartó Pinos_v2 y RegaloTexturizado (venían de indicaciones de su hermano).
  En la escena: MeshRenderer de cada Pino_* encendido otra vez, hijos PinoV2/LucesPino_*/LuzColor DESACTIVADOS, LODGroup
  LOD0 = renderer propio; `Efectos/LucesPinos` y `RegaloTexturizado` desactivados (no borrados). Pueblo_Luces.glb
  restaurado desde Library/BlenderBackup/Pueblo_Luces_antes_pinos2.glb (vuelven las espirales de 10 pinos) y la malla
  LucesPueblo del .blend también; colección PinosV2 oculta. Estilo a seguir = el de la tarde (bisel + smooth + subsurf,
  colores tipo plástico). Plan nuevo, DE UNO EN UNO: (1) exterior del pueblo → (2) interior del taller → (3) establo →
  (4) pinos; mejorar el diseño de lo que ya existe, sin agregar elementos nuevos.
- Bloque exterior 1/4 — CASAS (24-nov, hecho): `Blender/casas_v2.py` (exec modelado.py antes; `hacer_casas()`).
  Restaura las mallas originales desde Library/BlenderBackup/antes_casas_v2.blend (se puede repetir), busca las losas de
  nieve (islas de 54 caras = caja biselada con Ext_NieveBrillo), saca su caja orientada (cara más grande = arriba) y la
  cambia por una ALMOHADA de nieve (rejilla arriba/abajo, orilla redondeada, en aleros se enrolla y escurre en gotitas;
  en la cumbrera sigue derecho). Montones al pie (islas de 180 caras) → montoncitos redondos suaves; chimeneas
  (Amb_Piedra, 54 caras) → corona de piedra. Exterior.glb re-exportado (respaldo Exterior_antes_casas_v2.glb): 195 hijos,
  182 MeshCollider OK. OJO: hay DOS objetos "Exterior" (greybox y ambientación): buscar por `--- AMBIENTACION ---/Exterior`.
  `Blender/vista.py` → `ver([objs], "nombre", vistas=((az, elev),))` renderiza objetos solos a Library/Capturas.
  CAPAS (pedido del alumno): la nieve nunca debe atravesar lo de abajo. En casas_v2 la almohada se queda ENCIMA del
  techo mientras haya techo y solo se dobla hacia abajo en la parte que sobresale ('fuera' = metros más allá de la orilla).
- Bloque exterior completo (24-nov noche), todo sobre Exterior.glb (respaldos .blend en Library/BlenderBackup/antes_*):
  * `Blender/cerca_faroles.py` (`hacer_cerca()`, `hacer_faroles()`): posiciones de 68 postes y 6 faroles guardadas en
    `Blender/datos_cerca.json`. Cerca = postes de tronco con domo + gorrito de nieve que escurre, travesaños pandeados
    (loft), tira de nieve abombada, catenaria con 4 focos tipo gota por tramo (47k tris). Faroles = base escalonada,
    poste con anillos, listón rojo en espiral + moño, linterna de 4 vidrios (vidrio a z≈3.23 como antes), techo de 4
    aguas con `capa_nieve` (revolución que sigue el techo, más ancha => capas). Farolitos del pueblo (Pueblo_Luces) NO tocados.
  * `Blender/muneco.py` (`hacer_muneco()`): cabeza centrada en (0,0,2.35) local para que la Zanahoria siga en su nariz;
    bolas esponjadas (ruido), montoncito base, ojos con brillito, cachetes, sonrisa, botones, bufanda tejida con flecos,
    sombrero de copa ladeado con cinta y acebo (se agregó Amb_VerdePino como material 7), brazos de rama.
  * `Blender/rocas_arbustos.py` (`hacer_todo()`): Roca0/1/2, Arbusto (+ bayas Amb_Rojo, material 3), Troncos (leña en
    pirámide 4-3-2 con anillos en los cortes). Cada malla se escala a su caja original (`datos_rocas.json`).
    `nieve_campo` = capa de nieve con ORILLA SUAVE: duplica caras, empuja cada vértice grosor*campo(p, n); donde el campo
    es 0 queda hundida 1.2 cm => la orilla visible es una curva limpia (sin dientes). Usar esto para nieve en lo que siga.
- Siguiente: build y presentación (variedad de cascanueces, coleccionables, bake de luz, LOD pinos),
  build y presentación.

## Pulido personal (24-nov noche) — ver PLAN.md (fases con casillas)
- El juego ahora es proyecto personal; se juega en SU compu (Linux). Trabajar PLAN.md en orden.
- `Blender/vista.py` → `enfocar([nombres], distancia, angulo)` mueve la vista 3D de la ventana de Blender del alumno
  para que vea en vivo lo que se trabaja (él revisa en Blender ANTES de exportar a Unity).
- `Blender/acomodar_pinos.py` (`acomodar()` / `restaurar()`): relajación de círculos; 115/150 pinos movidos, 0 encimados,
  posiciones originales guardadas en la propiedad "pos_original". PENDIENTE: aprobación → exportar Exterior.glb,
  rebake NavMesh y re-revisar galletas/PuntosPieza/letreros contra colliders de pinos.
- Fase 1: Galletas HUD en y=-226 (bajo el panel Objetivo); hora del reloj con Fredoka; Galleta_5/6 bajadas junto a
  Casa_7/Casa_2; casas = MeshCollider de su malla (BoxCollider apagado); cápsula de pinos = 80% del radio de ramas a
  0.2–1.4 m de altura.
- Fase 1 cerrada (24-nov 23:40): `Blender/piezas_arbol.py` → Pieza_Maceta/Rama/Esfera/Estrella = copia (malla evaluada,
  mismos materiales) de Maceta+Tierra+Tronco / Nivel3 / Esfera_1+Tapa / Estrella, escalada a la caja de la pieza vieja;
  Pieza_Guirnalda = `rollo_liso` (hélice de cable + focos gota lisos). `faldas_en_capas(me)` jala hacia adentro las faldas
  interiores de Nivel1-3 que se salían por la exterior (rayo horizontal desde el eje). Tronco de la maceta: 24 lados.
  Pinos con SEPARACION 1.15 exportados; NavMesh nuevo = `Assets/Scenes/Taller_NavMesh_v2.asset` (el viejo
  Taller_NavMesh.asset ya no se usa → limpieza). Galleta_7 y PuntosPieza 26/28/29/32 movidos fuera de pinos.
  Respaldos: Library/BlenderBackup/*_antes_fase1.glb, antes_piezas_arbol.blend, antes_faldas_capas.blend.
- Fase 2 (25-nov madrugada): `Blender/coronas.py` (Coronas_Casas = 9 coronas de hojitas/moras/piñas/moño pegadas a la puerta;
  bolitas viejas borradas de las mallas Casa*, centro guardado en la propiedad de malla "corona_puerta"; CasaA en el ventanal).
  `Blender/luces_pueblo.py` (`hacer_luces()` rehace la malla LucesPueblo: aleros con rayos, farolitos, espirales en 10 pinos;
  ~227k tris → bajar en Fase 6; tarda y corta la sesión MCP: esperar a que salgan las imágenes).
  `Blender/caramblanos.py` (`restaurar_desde(blend)` + `arreglar_caramblanos()`: cada carámbano cuelga de la orilla más baja
  de nieve/techo a <0.5 m, metido 1.5 cm). Respaldos antes_coronas/antes_luces_pueblo/antes_caramblanos.blend.
- `Blender/ventanal_casaA.py` (CasaA: una cuadrícula limpia, barras Amb_MaderaOscura en x≈3.165). `Blender/montanas_nieve.py`
  (Montanas_v2 = roca + capa nieve_campo; OJO recalcular normales hacia arriba ANTES de nieve_campo o la nieve sale al revés).
  Hay niebla Exp² 0.009: las montañas (r 118-200) solo se aprecian desde la orilla del mapa; revisar ahí, no desde el patio.
- Fase 2 cerrada (25-nov): `Blender/nieve_pie_casas.py` → objeto NUEVO `NieveCasas` (Ambientacion2 → Pueblo_Luces.glb, sin sombra):
  anillo continuo de nieve por casa en coords de mundo pegado al SueloNieve con rayos (el terreno varía ±1.5 m entre casas,
  por eso no puede ir en la malla compartida). Caja de pared/suelo guardada en la propiedad de malla "nieve_pie".
  Postes de esquina (Ext_Crema) de CasaRoja/Azul/Verde engrosados 8 cm hacia afuera (tapaban mal las puntas de los tablones).
- Fase 3 farolitos (25-nov, aprobado): `Blender/farolitos.py` (exec modelado.py + cerca_faroles.py antes; `hacer_farolitos()`)
  rehace las 42 mallas Farolito_NN: poste bastón de caramelo con listón y moño, arco con rayitas rojas, linterna de los
  faroles del patio a escala 0.5 colgando; centro del vidrio en (0,-0.27,1.32) local como antes (luces y guirnaldas intactas).
  ~3.2k tris c/u (126k en total → revisar en Fase 6). Respaldo Pueblo_Luces_antes_farolitos.glb / antes_farolitos.blend.
- Fase 3 cerrada (25-nov, el alumno autorizó de noche modelar y pasar a Unity sin revisar; revisa en la mañana):
  `Blender/pinos_v3.py` (exec modelado + suavizado + montanas_nieve antes; `hacer_pinos()`): mismas H/R (guardadas en
  props de malla H_original/R_original), faldas suaves K=5 muestras=4, nieve = `nieve_campo` en BANDA medida con la altura
  de cada falda (u > inicio=0.97-0.3·nieve, ruido por lóbulo), gorrito en la punta. Tris: Abeto 3.8k, Picea 4.6k,
  Nevado 3.3k, Joven 2.1k (≈530k en los 150 pinos → LOD en Fase 6). Espirales de luces regeneradas (hacer_luces).
- SIGUIENTE (Fase 4, sin empezar): cascanueces = 7 piezas en colección "Cascanueces" (empty Cascanueces → Cas_Cuerpo
  (0,0,0.66) → Cas_BrazoL/R, Cas_Cabeza (→ Cas_Mandibula); Cas_PiernaL/R), alto 2.1 m, ya tienen SUBSURF. Render "antes"
  en Library/Capturas/cas_antes_*.png. Rehacer redondeado como elfo_v2 (mismos nombres/pivotes), luego repisas/juguetes,
  muebles; Fase 5 establo; 6 rendimiento (LOD pinos, LucesPueblo 234k tris, farolitos 126k); 7 limpieza; 8 build.
- Fase 4 (25-nov mañana): `Blender/cascanueces_v2.py` (`hacer_cascanueces()`; mismas 7 piezas/pivotes/materiales, mira -Y
  en Blender; shako con escudo y pluma, pelo/bigote/barba esponjados, pechera con alamares, charreteras con flecos, sable)
  → Cascanueces.glb (respaldo Cascanueces_antes_v2.glb). `Blender/repisas_v2.py` (`restaurar_repisas()` + `hacer_repisas()`):
  separa estructura (islas de madera >0.7 m) de juguetes, agrupa por entrepaño con mezcla de intervalos, adivina el tipo
  (oso/tren/carrito/soldado/pelota/regalo/cubos ABC) y pone uno redondeado del mismo tamaño mirando al frente → Props_Taller.glb.
- Fase 4 cerrada (25-nov): `Blender/mesas_v2.py` (rehace solo la estructura de Mesa_1-3: cubierta de 5 tablones, patas
  torneadas, faldón, entrepaño; cubos de color del entrepaño → regalos; `restaurar_mesas()`), `Blender/chimenea_v2.py`
  (corona de coronas.py escalada y pegada a la piedra con rayo, 3 botas redondas, troncos con cortes; `restaurar_chimenea()`).
  `Blender/heno_v2.py` (paca en 7 rebanadas + pajitas + cordel; caja original en la prop de malla "caja_heno").
  Todo en Props_Taller.glb (respaldos Props_Taller_antes_*.glb en Library/BlenderBackup/).
- Fase 5-6-8 (25-nov mañana): `Blender/nieve_techos.py` (almohada_nieve de casas_v2 en Establo y Taller_Techo → Edificio.glb;
  ColCamara sigue apuntando a la malla). Rendimiento: modificador DECIMATE "Rendimiento" después del Subsurf en Galleta 0.12,
  Indicador 0.3, Reno*/RenoNarizRoja* Cuerpo/Cabeza 0.35, TrineoSanta 0.35, Cas_Cabeza 0.45 (exportar con
  exportar_glb(con_hijos(raiz), archivo, raiz=raiz)); pinos LOD1 (colección PinosLOD oculta, Pinos_LOD1.glb, LODGroup
  0.12 / 0.015); focos de luces_pueblo más ligeros. Escena LOD0 2.85M → 2.38M tris. Partida automática completa en Play:
  0 errores. Guardia en DirectorJuego.CinematicaEtapa (EtapaActual null). Build Linux en Builds/Linux/TurnoDeNoche.x86_64
  (product_name "Turno de Noche en el Taller"). PENDIENTE: créditos con el nombre del alumno, Fase 7 (preguntar antes de
  borrar), medir FPS con Unity enfocado o en el build.
- Limpieza (25-nov, autorizada): quitados de la escena 150 PinoV2, 10 LucesPino_*, 10 LuzColor, Efectos/LucesPinos,
  RegaloTexturizado y los 44 greybox INACTIVOS (Reno_1-4 viejos del establo, Pino_0-39 greybox); lista en
  Library/Limpieza_25nov/objetos_quitados_de_la_escena.txt. Archivos movidos (no borrados) a Library/Limpieza_25nov/Assets/:
  Pinos_v2.glb, RegaloTexturizado.glb/.prefab, carpeta Texturas (Pino_*, Regalo_*), LucesPinos.cs, Greybox Elfo/Oscuro.mat,
  Taller_NavMesh.asset viejo. Colección PinosV2 quitada del .blend. Créditos y título con el nombre del alumno:
  "Cristian Amauri Gonzaga Castañeda" (Guion.Creditos + texto "Autor" en ConstruirUI). Build Linux rehecho.
- Detallitos del playtest (25-nov tarde): LetreroPoste enderezado (el tablero estaba girado 3°) y texto = título + 3 renglones
  (Prop_Letras); dientes del cascanueces = fila de 6 dientes redondeados siguiendo el arco (cascanueces_v2.mandibula);
  cabeza del elfo = esfera deformada (elfo_v2.cabeza; la de anillos + tapa dejaba la "mollera sumida"; malla Cabeza_v2).
  Pinos: la cápsula tenía la punta redonda a ras de suelo (a la altura del elfo medía ~60% del radio) => ahora la parte
  redonda va BAJO el suelo y radio = 82% de las ramas a 0.2–1.8 m; 7 pinos achicados para no tapar galletas/puntos/farolitos;
  prueba de alcance (flood fill con CheckCapsule desde afuera del patio): 39/39 objetos alcanzables.
  Rendimiento: VSync 1, SSAO Source=Depth (sin prepass DepthNormals) + Downsample + Low, sombras suaves Low;
  UIBrujula/RelojAmanecer solo reescriben el texto si cambia. Respaldos en Library/Respaldo_rendimiento/ y
  Library/BlenderBackup/*_antes_detallitos.glb, antes_letrero/antes_cabeza_elfo/antes_dientes.blend. Build rehecho.
- SELECTOR DE ELFO (25-nov): 3 elfos con el MISMO cuerpo. `VarianteElfo` (en Modelo_Elfo del prefab Jugador; Elfos[] con
  nombre/descr/colores; MaterialPropertyBlock en Elfo_Verde/Rojo/VerdeOscuro/Blanco/Oro (+emissiveFactor del oro); prende
  solo los hijos "Acc_<Nombre>_*"; oculta piezas de `ocultar`; elección en PlayerPrefs "Elfo"). Tilo = colores originales.
  Nieves (turquesa/rosa, melena + trenzas + moños + pestañas + pompón en vez de Cascabel), Chispa (morado/naranja, lentes,
  copete+rizo, pecas, bufanda a rayas). Accesorios en `Blender/elfos_variantes.py` (`hacer_accesorios()`, usa cab_pt =
  misma fórmula de la cabeza). Menú: `DirectorJuego.SeleccionElfo()` entre el título y la intro (A/D, flechas o clic,
  Enter; luz de relleno temporal "LuzSeleccion"; panel a la derecha). `Guion.Personalizar` cambia "Tilo" por el nombre
  elegido (y "el elfo del turno" -> "la elfa" con Nieves) en UIHistoria. SSAO final: DepthNormals + Downsample + Medium
  (Depth a media resolución dejaba granito y oscurecía la cabeza bajo el gorro).
  Cabeza del elfo con CUELLO de piel (loft z 0.76-0.97 dentro de elfo_v2.cabeza): la esfera sola dejaba hueco con el cuerpo.
- Playtest 25-nov (tarde 2):
  * Renos encimados: RenoNarizRoja_Cuerpo tenía desfase -2.09 dentro de su raíz en Blender => Rodolfo salía encima de
    Cometa. Corregido (desfase pasado a la raíz) y RenoNarizRoja.glb re-exportado.
  * Cámara tras cinemáticas: `CamaraOrbitaMouse.DetrasDe(t)` (eje H = yaw del elfo, V 20°), llamado en
    `DirectorJuego.SoltarCamara`. El árbol tiene hijo `ColCamara` (CapsuleCollider capa 9, r 1.6, alto 5.9).
  * Trineo de Santa: `TrineoVolador` (en TrineoSanta_Vuelo): renos galopan con desfase, cabeceo de cabezas, trineo se
    mece e INCLINA en curvas (Inclinar(giro)), riendas LineRenderer con comba (Assets/Materials/Riendas.mat), estela
    `PolvoMagico`. 4 renos en 2 parejas + `Reno_Guia` (RenoNarizRoja). VolarTrineo: ease-out, cabeceo ±8°, cámara suave;
    al llegar `MirarTrineo` (flag seguirTrineo) lo sigue mirando.
  * Brújula: sigue el CAMINO del NavMesh (NavMesh.CalculatePath, apunta a la siguiente vuelta >1.5 m), metros = de
    camino, histéresis 30% para no brincar de pieza, "(arriba)" si está alto, aviso si llevas algo que no va (soltar Q).
  * GALLETAS (10/10 => `Galleta.Todas`): poder (correr x1.2 en ElfoController, `Cascanueces.DuracionAturdido` x2),
    desbloquea el elfo secreto JENGIBRE (PlayerPrefs "ElfoSecreto"; `VarianteElfo.Desbloqueado/Silueta`; en el menú
    sale como silueta "???"), FINAL ESPECIAL (`DirectorJuego.EscenaGalletas`: cámara a Santa, migajas,
    `Guion.FinalGalletas`) + línea en créditos. Accesorios Acc_Jengibre_Glaseado (Falda), _GlaseadoGorro, _Botones
    con `Blender/jengibre_refacciones.py` (zigzag con rayos contra la malla real; OJO la falda es el objeto "Falda").
    Las pruebas desbloquean el secreto: regresar PlayerPrefs "ElfoSecreto" a 0 después de probar.
  * MÁQUINA 7: `MaquinaRota` (Interactuable en Estaciones/MaquinaJuguetes) + 3 refacciones Recogible tipo "Refaccion"
    (prefabs Assets/Prefabs/Piezas/Refaccion_Engrane/Resorte/Llave, modelos Refaccion_*.glb) en
    `--- PIEZAS ---/Refacciones`: engrane taller (-2.5,0.5,6.6), resorte establo (16.5,0.5,-1.3), llave patio (5,0.47,-11).
    Al instalar las 3: chispas se apagan, alerta pasa a verde tranquila (`BrilloEmisivo.CambiarColor`), ruido baja
    (`GestorAudio.MaquinaReparada`), `Cascanueces.Calmar()` (x0.85 velocidad, x0.75 vista, x0.7 oído) y Santa lo menciona
    (`Guion.LineasFinalSanta`). La brújula NO apunta a refacciones (son opcionales).
- Playtest 25-nov (tarde 3): `Recogible` baja sus Light hijas a 12% mientras está EnMano (la luz "Brillo" de las
  refacciones/estrella deslumbraba al elfo). Atorones: el empujón al atrapar se acorta con `ElfoController.EmpujeSeguro`
  (NavMesh.Raycast) y brinca menos (2.5); `ElfoController.RevisarAtorado`: guarda el último punto seguro (en NavMesh y en
  suelo) y si estás FUERA del NavMesh, intentando moverte sin avanzar 1.5 s, y te acaban de empujar (<10 s) o estás
  trabado en el aire → te regresa ahí ("¡Uf! Saliste del rincón"). Encima de repisa/cajas no se activa. Menú de elfo:
  flechas < > se centran en la posición del elfo en pantalla (WorldToScreenPoint), clic relativo a esa posición; panel
  de descripción alfa 0.72. La transparencia en las capturas del alumno es de su escritorio, no del juego.
- Sonidos extra (25-nov): `generar_audio.extras()` (semilla propia 25; se corre al final => no cambia los sonidos viejos;
  solo extras: `cd Herramientas && python3 -c "import generar_audio as g; g.extras()"`). Voces al escribir (UIHistoria,
  cada 3 letras, `GestorAudio.Voz` con fuente propia): voz_elfo1-4, voz_santa1-4, voz_narr1-4 (narración/notas), voz_cas1-4
  (sin uso aún). `susto` al despertar un cascanueces, `paso_cas1/2` (fuente 3D propia por cascanueces, `GestorAudio.FuentePropia`),
  `escapaste` (Persecución→Patrulla), `galleta`, `poder` (10/10), `instalar`/`reparada` (Máquina 7), `campanada` (avisos
  del reloj), `cambio` (menú de elfo), `pausa`, `trineo` (VolarTrineo), `encender` (LucesArbol). Importación igual a tick.wav.
- DIFICULTAD (25-nov): `Dificultad` (static, PlayerPrefs "Dificultad", default 1 Medio) con Niveles[] Fácil/Medio/Difícil/Imposible:
  vidas 0/0/3/1, galletasPorVida 0/0/2/5 (tope `MaxVidas` 5), multiplicadores velocidad/vista/oído/aturdido de cascanueces
  (`Cascanueces.AplicarDificultad`), minutos del reloj 20/15/12/10, despertarAntes -1/0/0/+1 (despertarConPiezas, mín 1).
  `Dificultad.Aplicar()` (idempotente) en `DirectorJuego.EmpezarAJugar`; `NuevaPartida()` en DirectorJuego.Start (la escena se
  recarga al reintentar; se conserva la dificultad elegida). Pantalla `SeleccionDificultad()` (4 tarjetas, A/D/clic/Enter) después
  de "Elige a tu elfo"; las Image con Outline deben ser OPACAS (el Outline dibuja una copia detrás). `Vidas` (static + HUD de
  corazones `UIConstructor.SpriteCorazon`, en (190,-300) bajo el panel Objetivo, solo visible Jugando/Pausa; "Galletas" baja a
  -340 si hay vidas). Atrapar => `Vidas.Perder()`; en 0 => `DirectorJuego.SinVidas()` ("¡Te atraparon!", `Guion.DerrotaAtrapado`,
  misma pantalla de derrota con [R]/[Q]). Galleta => `Vidas.PorGalleta(n)`. Créditos muestran dificultad y vidas.
- Playtest 25-nov (noche): despertar por dificultad ahora se mueve por ETAPAS completas (Cascanueces.AplicarDificultad usa las
  piezas acumuladas al final de cada etapa; antes en Fácil despertaban a media etapa y la presentación salía después).
  `UIObjetivo.Acomodar()` ajusta el alto del panel a la pista y publica `UIObjetivo.Abajo`; corazones (Vidas) y "Galletas"
  (Galleta.SeguirPanel) se colocan debajo. `UIAviso` se esconde mientras `UIHistoria.Abierta`. Final especial: banner
  "★ FINAL ESPECIAL ★" en vez de UIAviso. Mensaje de 10 galletas distinto si Jengibre ya estaba desbloqueado.
  OJO: los PlayerPrefs del editor y del build son distintos archivos (~/.config/unity3d/DefaultCompany/Navidad vs
  ".../Turno de Noche en el Taller"); el alumno juega en el editor.
- DIFÍCIL/IMPOSIBLE extra: `Dificultad.Datos.oscuridad` (-0.55 / -1.0 EV en ColorAdjustments.postExposure de volume.profile, +viñeta)
  y `cadenciaNevados` (2.4 / 1.7 s). CASCANUECES NEVADOS: prefab `Assets/Prefabs/CascanuecesNevado.prefab` (modelo Cascanueces.glb
  x1.2 con `VarianteCascanueces.Tipo.Nevado` abrigo blanco/pantalón azul, CubetaNieve al lado, Estrellas_Aturdido, CapsuleCollider capa 8),
  5 instancias APAGADAS en `--- ENEMIGOS ---/Nevados` (1-3 desdeNivel 2, 4-5 desdeNivel 3); Dificultad.Aplicar las prende.
  `CascanuecesNevado`: estático, gira hacia ti, Linecast de vista, alcance 16 (x1.2 Imposible), tiro parabólico con medio adelanto,
  brazo Cas_BrazoL (+X = mano derecha real); tu bola de nieve lo aturde 4 s. `BolaEnemiga` (sin Rigidbody, SphereCast r 0.18).
  `FrioJugador` (se agrega solo al jugador): golpe = frío 1.5 s (se REINICIA, no suma) => `ElfoController.factorFrio` 0.5;
  3 golpes en ventana de 5 s => congelado 2.5 s (`ElfoController.Inmovilizar`, bloque `BloqueHielo.glb` de `Blender/hielo.py`,
  sonidos congelar/descongelar), HUD 3 copos (`UIConstructor.SpriteCopo`) + escarcha (`SpriteVineta`).
- FASE 9 (25-nov noche, hecha): todo se configura en `Dificultad.Datos` (pilaSegundos 240/150, apagon, ventiscaMin/Max
  120-180 / 90-120, bolasMax 6/5/4/3, cajasSorpresa 0/0/5/8) y lo prende `Dificultad.Aplicar()`.
  * `Linterna` (se agrega al Jugador): LuzElfo x1.5 intensidad/x1.35 rango, gasta solo Jugando, <25% parpadea, recarga a <3.2 m de
    Luz_Chimenea / Luz_Farol_* / hijos de Luces_Farolitos; HUD pila bajo los corazones (Galleta baja 45 px si `Linterna.Activa`).
  * `Apagon` (objeto creado al aplicar): a reloj.Progreso 0.625 (3 AM) si la Máquina 7 sigue rota: Luz_Taller_*, Luz_Establo,
    Luz_Foco_Arbol a 0 y emisión de Lamparas/Guirnaldas/Guirnaldas_Focos/Maquina con MaterialPropertyBlock, 60 s (no corre en
    cinemáticas) o hasta reparar; `Apagon.FactorVision` 0.8 en Cascanueces.PuedeVerAlJugador.
  * `Ventisca`: intensidad 0→1→0 (rampas 3 s, 20 s); niebla 0.009→0.06 y fogColor → gris azul; partículas NieveVentisca (Stretch)
    pegadas al jugador; bucle "ventisca"; `ElfoController.empujeExterno` (m/s) solo afuera. `Ventisca.EstaBajoTecho(pos)` = rayo de
    arriba (ojo: el ColCamara del Taller_Techo/Establo cubre también los aleros).
  * `UIBrujula.Interferencia()`: Difícil+ durante ventisca o a <7 m de la Máquina 7 rota; Imposible además cada 25-45 s por 4-6 s.
  * `CajaSorpresa` (Blender/caja_sorpresa.py → CajaSorpresa.glb: raíz caja, Caja_Tapa con pivote en bisagra, Caja_Resorte escala Y,
    Caja_Payaso), prefab Assets/Prefabs/Trampas/CajaSorpresa.prefab (BoxCollider capa 8), 8 instancias APAGADAS en
    `--- ENEMIGOS ---/CajasSorpresa` (Caja_1..5 Difícil, 6-8 Imposible; se prenden por orden de nombre). Radio 1.0 caminando /
    2.3 corriendo, `Cascanueces.OirRuido(pos, 20)` => van en Persecución al ruido; se cierra a los 6 s y se rearma a los 18 s.
  * `Medallas` (static): PlayerPrefs Medalla_0..3 (Bronce/Plata/Oro/Diamante), Medalla_Galletas, Medalla_Intacto (Difícil+ sin perder
    vidas: `Vidas.Perdidas`). Créditos: `Medallas.Estudio(nivel)` = medalla (Resources/Medalla.prefab de Blender/medalla.py, material 0
    disco y 4 estrella pintados con MPB) + luces + cámara en y=-500 → RenderTexture → RawImage. Título: `Medallas.FilaTitulo`.
  * Sonidos `generar_audio.fase9()` (semilla 26): recarga, pila_baja, apagon, luz_vuelve, ventisca (bucle), interferencia,
    recoger_nieve, sin_bolas, boing, medalla.
  * OJO: Blender abrió un archivo vacío esta vez; antes de modelar revisar que esté abierto Blender/Navidad_modelos.blend.
- Menú de pausa (25-nov noche): los CONTROLES (Guion.Controles, 3 renglones + consejos de Difícil/Imposible) y la fila de
  MEDALLAS (`Medallas.Fila(capa, ancla, pos)`) se movieron del título a la pausa; el título ya no los muestra.
  UIAviso se esconde en Pausa (se encimaba con los controles).
- Casas v3 (26-nov, low-poly completo): `Blender/casa_troncos_v3.py` (`hacer_casa_troncos()`; exec modelado.py antes) rehace
  la malla CasaTroncos (37k tris): troncos de 8 lados con cortes, cimiento de piedras, tejas + almohada de nieve, porche con
  farolito colgante, ventanas con postigos/jardinera, ojos de buey, chimenea de piedras (boca en z 6), leña, tocón con hacha.
  Focos del alero: `instalar_alero_troncos()` después de exec luces_pueblo.py y antes de `hacer_luces()` (4.5 min).
  Respaldos: Library/BlenderBackup/antes_casa_troncos_v3.blend, *_antes_casa_troncos.glb.
  `Blender/casa_2pisos_v3.py` (`hacer_casa_2pisos("CasaRoja"|"CasaAzul"|"CasaVerde")`, exec casa_troncos_v3.py antes; VARIANTES
  con color/puerta/postigos/cortina/extras) y `Blender/casa_a_v3.py` (`hacer_casa_a()`; `agua(..., hasta=, margen=)` deja ver
  tejas abajo con orilla ondulada). Focos: exec luces_pueblo + los 3 scripts, `instalar_alero_troncos/2pisos/a()`, `hacer_luces()`
  (~7 min). Exportadas 27-nov (respaldos *_antes_casas_v3.glb). Capturas en Unity: scratchpad foto.sh (cámara temporal → PNG).
- Modelos de la Vitrina restantes (27-nov, autorizado de noche): `Blender/lowpoly.py` (`lowpolizar(raiz, ratio)`) quita
  Subsurf/WeightedNormal/Decimate, caras planas y Decimate opcional, mismos nombres/pivotes (animaciones por código intactas).
  HECHO 27-nov madrugada: Props del taller (Mesas, Repisas, Cajas, Heno, Chimenea, Maquina, Detalles_Taller, Lamparas, Coronas,
  Maquina_LuzAlerta → Props_Taller.glb) y los 29 modelos con .glb propio (personajes, renos, trineos, Arbol, Pieza_*, Regalo y
  objetos del juego) pasados por lowpolizar y exportados con exportar_glb(con_hijos(r), n+".glb", raiz=r). Nodos idénticos a los
  respaldos (Library/BlenderBackup/antes_lowpoly_glb/, Props_Taller_antes_lowpoly.glb, antes_lowpoly_*.blend). Las copias VT_
  de la Vitrina también sin Subsurf. Unity: 739 renderers y 17 prefabs sin desfase; partida automática hasta el Final sin errores;
  build Linux rehecho. `vista.py` → `ver_grupo(nombres, archivo)` encuadra raíces vacías (personajes).
  OJO: en lowpoly.py el depsgraph debe ser el de la escena del objeto ("Scene"), no el de la ventana (Vitrina).
