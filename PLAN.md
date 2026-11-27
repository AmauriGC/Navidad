# Plan de pulido — "Turno de Noche en el Taller"

Objetivo (24-nov-2026): ya no es solo la tarea. Es un juego propio para enseñarlo a la familia y amigos,
y que **me guste a mí**. Vamos paso a pasito: primero lo que está roto, luego lo que se ve mal y al final lo bonito,
para no regresarnos a arreglar cosas.

Marcar `[x]` cuando quede hecho y revisado en el juego.

---

## Fase 1 — Bugs que se notan al jugar
- [x] **Galletas inalcanzables** (Galleta_5/6 junto a Casa_7/Casa_2; Galleta_7 y 4 PuntosPieza sacados de pinos): Galleta_5 (11.8 m de alto) y Galleta_6 (8.5 m) quedaron ENCIMA de un pino
      (Pino_112 y Pino_119). Bajarlas a un lugar al que se pueda llegar (escondidas, pero alcanzables).
- [x] **Textos del HUD encimados**: "Galletas 1/10" (y = -150) cae encima de la pista "Dicen que quedó por el
      taller..." (que baja hasta y = -164). Reacomodar el panel de arriba a la izquierda.
- [x] **Reloj difícil de leer**: con la letra Mountains of Christmas el cero parece "o" ("11:1o PM").
      Los números van con Fredoka.
- [ ] **Se atraviesan cosas**:
  - [x] (cápsula = 80% del radio de las ramas entre 0.2 y 1.4 m; promedio 1.7 → 3.6 m) Pinos: el collider es solo el tronco (cápsula con radio de 0.42 del pino), así que el elfo se mete
        entre las ramas. Hacer la cápsula más ancha abajo, o subir las ramas de abajo.
  - [x] (casas = MeshCollider con su propia malla, BoxCollider apagado) Cabaña de troncos: su BoxCollider (7.1 × 6.6) no cubre el porche ni los postes (el modelo mide 8.7 × 8).
  - [x] Revisar las demás casas: la casa en A (collider 7.5 vs. 13.6 de modelo) y las de 2 pisos con tejabán.
- [x] **Piezas del árbol iguales a las partes del árbol** (`piezas_arbol.py`: copia de la malla real; faldas de Nivel1-3
      sin hojitas que se salen; rollo de guirnalda con focos lisos; tronco redondo)
- [ ] (la hace el alumno cuando quiera) Partida completa a mano (no automática), anotando todo lo raro: dificultad, cascanueces, reloj, final.

## Fase 2 — Errores visuales del exterior
- [x] (`coronas.py`: una corona bonita por casa en la puerta; bolitas viejas quitadas) **Coronas encimadas ("C" verde)**: `Pueblo_Luces/Coronas_Casas` puso coronas que quedaron a la mitad dentro
      de la pared (por eso se ven como una "C") y repiten la corona que ya trae la puerta. Quitarlas o
      reacomodarlas bien.
- [x] (`luces_pueblo.py`: enganche con rayos bajo alero/nieve, 12 cm fuera de la pared; espirales en pinos acomodados) **Cables que cruzan las fachadas**: las líneas negras de `LucesPueblo` (focos en los aleros) atraviesan la
      pared de la casa roja. Rehacer los cables pegados al alero.
- [x] (`caramblanos.py`) **Focos y carámbanos del alero**: con la nieve nueva de los techos quedaron flotando o dentro de la nieve
      (cabaña de troncos). Moverlos a la orilla nueva.
- [x] (`ventanal_casaA.py`: una sola cuadrícula recortada al triángulo; 120 caritas de bisel viejo quitadas) **Ventanal de la casa en A**: la cuadrícula está chueca y a destiempo. Rehacerla alineada.
- [x] (`montanas_nieve.py`) **Montañas del fondo**: la nieve está pintada por caras y se ve en escalones cuadrados. Usar la nieve con
      orilla suave (`nieve_campo`).
- [x] (`acomodar_pinos.py`, SEPARACION 1.15; NavMesh rehecho en Taller_NavMesh_v2.asset) **Pinos encimados**: 33 pares de pinos casi en el mismo lugar. Separarlos o quitar algunos, y dejar claros
      (espacios abiertos) para que se vea bonito.
- [x] (`nieve_pie_casas.py`: objeto NieveCasas que sigue el terreno de cada casa) Montoncitos de nieve al pie de las casas: revisar que no se encimen ni floten.

- [x] Tablones de las casas de 2 pisos que se salían por las esquinas (postes de esquina engrosados 8 cm)

## Fase 3 — Diseño del exterior (terminar)
- [x] (`farolitos.py`, bastón de caramelo + linterna del patio a escala 0.5) **Farolitos del pueblo** (42 en los senderos): mismo diseño que los faroles del patio, en chiquito.
- [x] (`pinos_v3.py`, nieve en banda sobre los lóbulos; espirales de luces regeneradas) **Pinos** (4 tipos): más bonitos, en el estilo de la tarde (capas suaves, nieve en capas con `nieve_campo`).

## Fase 4 — Interior del taller
- [x] (`cascanueces_v2.py`) **Cascanueces** (enemigo): se ve de cajitas. Rehacerlo redondeado como el elfo (mismos nombres y pivotes
      para que siga funcionando su animación).
- [x] (`repisas_v2.py`: reconoce cada juguete y lo cambia por uno redondeado) Repisas y juguetes (trenecitos, ositos, pelotas, regalos): más detalle.
- [x] (`mesas_v2.py`, `chimenea_v2.py`; máquina ya era v2; cajas y lámparas ya tenían bisel) Mesas, máquina, chimenea, cajas, lámparas y paredes/piso.

## Fase 5 — Establo
- [x] Establo (`nieve_techos.py`: nieve almohada en establo y taller), heno (`heno_v2.py`), cerca y portón (se quedan), trineo (v2), renos (v2).

## Fase 6 — Rendimiento (para que corra bien en otras compus)
La escena tiene **2.1 millones de triángulos**. Los más pesados:
- [x] Renos: Decimate 0.35 después del Subsurf (265k → ~93k en los 7).
- [x] Trineo de Santa: Decimate 0.35 (91k → 32k).
- [x] Indicadores "!": Decimate 0.3 (34k → 10k). Galletas: Decimate 0.12 (177k → 21k). Cabeza cascanueces 0.45.
- [x] Pinos con LOD1 (`hacer_pinos_lod1()` → Pinos_LOD1.glb, hijo "LOD1" en los 150): 530k → 252k de lejos. Focos del pueblo más ligeros (234k → 145k).
- [ ] Medir FPS en Play con Unity enfocado.

## Fase 7 — Limpieza (cosas que ya no se usan)
Nada se borra sin preguntar:
- [x] Pinos de planos que salieron de las indicaciones de mi hermano: 150 hijos `PinoV2`, 10 `LucesPino_*`, 10 `LuzColor`
      (apagados), `Efectos/LucesPinos`, `RegaloTexturizado`, `Pinos_v2.glb`, `RegaloTexturizado.glb` y su prefab,
      las texturas `Pino_*` y `Regalo_*` y el script `LucesPinos.cs`.
- [x] Greybox viejo (solo los 44 inactivos; los de renderer apagado siguen como colisión): 44 objetos inactivos y 27 con el renderer apagado en `--- NIVEL (greybox) ---`.
      Revisar cuáles siguen sirviendo como colisión.
- [x] Materiales greybox sin uso (`Elfo.mat`, `Oscuro.mat`).
- [ ] Respaldos viejos en `Library/BlenderBackup/` (cuando todo esté aprobado).

Todo lo quitado está en `Library/Limpieza_25nov/` (lista de objetos + archivos con su .meta) por si hay que regresarlo.

## Fase 8 — Compartir
- [x] Build para MI compu (Linux): `Builds/Linux/TurnoDeNoche.x86_64` (25-nov, 0 errores). Volver a hacerlo después de cambios.
- [x] Pantalla de título y créditos con mi nombre (Cristian Amauri Gonzaga Castañeda).
- [ ] Subirlo a GitHub (cuando yo diga).

## Fase 9 — Más reto en Difícil / Imposible (pedido 25-nov noche)
Ya hecho antes: niveles de dificultad, vidas, oscuridad, cascanueces nevados + frío/congelado.

### 9.1 — Luz: linterna con pila + apagón ✔ (25-nov)
- [x] **Linterna con pila** (la luz del elfo): Difícil dura 4 min, Imposible 2.5 min (solo gasta mientras juegas).
      Abajo de 25% parpadea y se debilita; en 0 se apaga. Se recarga parado junto a la **chimenea** o un **farol/farolito**.
      HUD: pila con 4 rayitas bajo los corazones. Fácil/Medio: sin pila (luz infinita, no se ve el HUD).
- [x] **Apagón a las 3:00 AM** (Difícil/Imposible) si la Máquina 7 NO está reparada: parpadean y se apagan lámparas
      del taller/establo, foco del árbol y foquitos de guirnaldas por 60 s (la chimenea sigue: es fuego). Los cascanueces
      ven un poco menos a oscuras. Si la reparaste: mensaje "gracias a ti no hubo apagón".
- [x] Sonidos: recarga, pila baja, apagón, regresa la luz.

### 9.2 — Clima y brújula ✔ (25-nov)
- [x] **Ventiscas**: cada 2-3 min (Difícil) / 1.5-2 min (Imposible) una tormenta de 20 s: niebla espesa, nieve de lado,
      viento fuerte (sonido) y un empujoncito al elfo AFUERA (adentro de taller/establo no).
- [x] **Brújula con interferencia** (Imposible; en Difícil solo durante ventiscas): tiembla y gira loca unos segundos;
      cerca de la Máquina 7 sin reparar se vuelve loca siempre.

### 9.3 — Munición y trampas ✔ (25-nov)
- [x] **Bolas de nieve limitadas** (ya existían con máx 5: ahora Fácil 6, Medio 5, Difícil 4, Imposible 3): se recargan en montones de nieve y cubetas (E). HUD con bolitas.
- [x] **Cajas sorpresa** (modelo nuevo en Blender: caja de juguete con payaso de resorte): escondidas en el piso;
      si pasas cerca sin agacharte... ¡BOING! ruido fuerte que atrae a los cascanueces cercanos. Se ven poquito (reto).

### 9.4 — Medallas y cierre (medallas ✔; falta playtest del alumno)
- [x] **Medallas** en los créditos según la dificultad en que ganaste (bronce Fácil, plata Medio, oro Difícil,
      diamante Imposible) + extra si sin perder vidas / con las 10 galletas. Modelo de medalla en Blender girando.
      Se guardan (PlayerPrefs) y se ven en el título.
- [ ] Balance con playtest del alumno, build.
