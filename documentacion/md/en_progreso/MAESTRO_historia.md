# MAESTRO · Historia nueva: Siete (la Máquina 7)

- Estado: En progreso
- Creado: 27/11/2026 · Actualizado: 27/11/2026
- Versión destino: **1.5**
- Escrita entre Cristian y Claude. Las notas de Cristian mandan.

## Objetivo
La Máquina 7 deja de ser adorno y se vuelve parte de la historia. **Siete** es la máquina más vieja del taller
(la primera que armó Santa): pinta ojos y da cuerda a los juguetes. Esta noche se enfermó: un chispazo despertó a
los cascanueces del lote 24, que tumbaron el Gran Árbol y **rompieron la estrella**. El elfo arma el árbol,
**cura a Siete** (obligatorio) y con ella **fabrica una estrella nueva** antes del amanecer.
Las **galletas** ganan protagonismo: son la charola de Santa y se acomodan por forma.

## Decisiones (27/11)
| Tema | Decisión |
|---|---|
| Máquina 7 | Obligatoria. Tiene personalidad ("Siete"): sus descargas son hipo eléctrico, su foco parpadea triste pidiendo perdón, al curarla toca una melodía de caja musical. |
| Estrella | Se rompe en la intro. La estrella rota queda arriba de la repisa oeste (mismo acertijo de las cajas). Siete fabrica la nueva con la palanca. |
| Descargas | En todas las dificultades. Fácil 3 min · Medio 2 min · Difícil 90 s · Imposible 60 s. Fácil/Medio: suaves, sin nada grave. Difícil/Imposible: fuertes. |
| Sobrecarga | Descarga 10 sin curar a Siete: **derrota** en Difícil/Imposible; en Fácil/Medio solo un susto (apagón corto + todos en alerta). |
| Refacciones | Engrane, resorte y **fusible** (antes "llave"; se cambió para no confundirla con la llave de cuerda). Cada una vigilada: un cascanueces, una caja sorpresa (activa en todas las dificultades), un lugar alto. Se instalan en el cuarto de máquinas. |
| Cuarto de máquinas | Nuevo, atrás de la Máquina 7 (x 6–11, z 9.2–13.5, revisado: está libre), puerta en la pared norte del taller. Adentro: el motor "corazón" y el plano de Santa. |
| Cascanueces | No son malos: Siete les pintó ojos de soldado y creen que protegen el taller. Llave de cuerda en la espalda. Al final quedan **buenos, ojos azules, chiquitos y juntitos en la repisa**. |
| Galletas | La charola de Santa (junto a la chimenea) con 10 huecos de forma. Cada galleta trae una letra: **N**·estrella **O**·campana **C**·arbolito **H**·muñeco de nieve **E**·bastón **B**·copo **U**·calcetín **E**·regalo **N**·reno **A**·corazón → NOCHEBUENA. Minijuego cenital: arrastrar y girar hasta que encaje. Las horneó **Jengibre** (el elfo secreto). Vidas: al recoger; poder + Jengibre + final especial: al completar la charola. |
| Reloj | Fácil 25 · Medio 20 · Difícil 15 · Imposible 12 minutos. |
| Etapas | 1 Maceta · 2 Ramas · 3 Esferas · 4 Guirnalda · 5 Curar a Siete · 6 Fabricar la estrella · 7 Poner la estrella. |

## Alcance
- Incluye: guion, mecánicas (descargas, sobrecarga, etapas 5-6, charola), modelos low-poly de caras planas,
  cuarto de máquinas, cinemáticas, sonidos nuevos (función y semilla propias), prueba automática.
- No incluye: el tráiler. Los detallitos van después (`MAESTRO_detallitos.md`, fases 2-9).

## Fases (de una en una; Cristian revisa en Blender/Unity antes de seguir)
- [ ] H1 — Guion: todos los textos (`FASE_01_historia_guion.md`) → aprobado → `Guion.cs` y letreros.
- [ ] H2 — Modelos (Vitrina → aprobar → .glb): a) Siete v3 (tablero 3 focos, palanca, foco-carita, cables al techo);
      b) cuarto de máquinas (motor, plano, puerta); c) llave de cuerda, estrella rota, caja del lote 24, Refaccion_Fusible;
      d) charola + 10 galletas con forma y letra.
- [ ] H3 — Escenario en Unity: puerta, colisiones/capas, luces, cámara, NavMesh, letreros nuevos, estrella rota en la repisa.
- [ ] H4 — Mecánicas: 7 etapas, `DescargaMaquina`, sobrecarga, refacciones vigiladas, palanca, brújula, reloj, HUD.
- [ ] H5 — Charola de galletas (minijuego con mouse y táctil, animación NOCHEBUENA, recompensas).
- [ ] H6 — Cinemáticas: ZAAP de la intro, primera descarga, melodía de Siete, fabricar la estrella, final dorado,
      cascanueces chiquitos juntitos, Jengibre, epílogo.
- [ ] H7 — Sonidos (`generar_audio`, función nueva con semilla propia).
- [ ] H8 — Partida automática por las 7 etapas y la charola, 0 errores; playtest de Cristian.

## Dependencias
- Sistemas existentes: `ArbolNavidad`/`EtapaArbol`, `MaquinaRota`, `Recogible`, `RepartidorPiezas`, `DirectorJuego`,
  `Dificultad.Datos`, `RelojAmanecer`, `Apagon`, `CajaSorpresa`, `Galleta`, `VarianteElfo` (Jengibre), `UIBrujula`, `Tactil`.

## Criterios de aceptación
- No se puede ganar sin curar a Siete y fabricar la estrella.
- Descargas y sobrecarga se comportan según la dificultad.
- La charola se puede completar con mouse y con pantalla táctil.
- 0 errores en consola; partida automática completa; build de Linux.

## Pruebas
- Partida automática (`Juego.PruebaAutomatica`) con las 7 etapas y la charola.
- Probar sobrecarga en Medio (susto) y en Difícil (derrota).
- Capturas en `Library/Capturas/`; respaldos en `Library/BlenderBackup/`.

---

## Anexo: notas originales de Cristian (27/11)
- Quiero que sea necesario reparar la máquina 7 para poder pasar el juego.
- Me gusta la idea (cuerda + estrella rota). Ufff me gusta la intro. Las descargas son buena idea.
- Darle más historia en general; la máquina es un elemento de la historia; darle protagonismo a las galletas.
- Final: me parece bien. Derrota por sobrecarga: sí.
- La estrella se rompe y la máquina hace la nueva; descargas en todas pero Fácil/Medio poquitas y sin nada grave,
  Difícil/Imposible sí algo grave; cuarto de máquinas nuevo; terminan buenos con ojos azules, chiquitos sobre la
  repisa y en la cinemática se ven juntitos.
- Galletas por formas, acomodarlas en la charola vista desde arriba, con animación bonita.
