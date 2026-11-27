# -*- coding: utf-8 -*-
"""
MÁQUINA DE JUGUETES v2 (objeto 'Maquina' de Props_Taller.glb). Mismo lugar y tamaño que la anterior
(cuerpo x -9.35..-6.65, y -7.6..-5.4, z 0.3..2.6 en Blender) para que sus colisiones sigan sirviendo.
  - cuerpo con esquinas redondeadas, franjas de acero y remaches
  - cara hacia el árbol (y = -5.4): pantalla con marco, 4 botones redondos, manómetro con aguja, palanca
  - cara +X: 2 engranes de verdad (dientes y rayos) y tornillos
  - tapa en domo, embudo de latón liso con orilla, tubos de cobre con codos y bridas hasta el techo
  - rampa de salida curva (donde caen los juguetes a la banda) y escotilla lateral con manija
Uso: exec(modelado.py); exec(maquina_v2.py)
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

ACERO, TURQ, LATON, COBRE, NEGRO, PANTALLA, ROJO, AMARILLO, HOLLIN = range(9)
CX, CY = -8.0, -6.5            # centro del cuerpo
HX, HY = 1.35, 1.1             # medio ancho (x) y medio fondo (y)
FRENTE = CY + HY               # y = -5.4 (cara que mira al árbol)
LADO = CX + HX                 # x = -6.65 (cara de los engranes)


def cilindro(bm, a, b, r, mat, segs=24, tapas=(True, True)):
    """Cilindro con lados suaves y tapas PLANAS (sombreado plano en las tapas para que no se vean abolladas)."""
    antes = len(bm.faces)
    loft(bm, [a, b], [(r, r), (r, r)], mat=mat, segs=segs, sub=1, tapas=tapas, domo=0.0)
    eje = (Vector(b) - Vector(a)).normalized()
    bm.faces.ensure_lookup_table()
    for i in range(antes, len(bm.faces)):
        f = bm.faces[i]
        f.normal_update()
        if abs(f.normal.dot(eje)) > 0.9: f.smooth = False


def perfil_extruido(bm, centro, eje_u, eje_v, normal, contorno, grosor, mat):
    """Extruye un contorno 2D (lista de (u, v)) en el plano (eje_u, eje_v) con 'grosor' hacia 'normal'."""
    c = Vector(centro)
    frente = [bm.verts.new(c + eje_u * u + eje_v * v + normal * grosor) for (u, v) in contorno]
    atras = [bm.verts.new(c + eje_u * u + eje_v * v) for (u, v) in contorno]
    cf = bm.verts.new(c + normal * grosor); ca = bm.verts.new(c)
    n = len(contorno)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((cf, frente[i], frente[j])).material_index = mat
        bm.faces.new((ca, atras[j], atras[i])).material_index = mat
        f = bm.faces.new((frente[i], atras[i], atras[j], frente[j])); f.material_index = mat


def engrane(bm, centro, R, dientes, grosor, mat, eje_u=Vector((0, 1, 0)), eje_v=Vector((0, 0, 1)), normal=Vector((1, 0, 0))):
    cont = []
    pasos = dientes * 4
    for k in range(pasos):
        a = 2 * math.pi * k / pasos
        fase = k % 4
        r = R if fase in (1, 2) else R * 0.84
        cont.append((r * math.cos(a), r * math.sin(a)))
    # anillo exterior (con dientes) y centro: se hace como disco dentado + "hueco" simulado con un disco oscuro
    perfil_extruido(bm, centro, eje_u, eje_v, normal, cont, grosor, mat)
    c = Vector(centro) + normal * grosor
    loft(bm, [tuple(c - normal * 0.005), tuple(c + normal * 0.012)], [(R * 0.62, R * 0.62)] * 2, mat=HOLLIN, segs=24, sub=1, domo=0.0)
    for k in range(5):   # rayos
        a = 2 * math.pi * k / 5 + 0.3
        d = eje_u * math.cos(a) + eje_v * math.sin(a)
        loft(bm, [tuple(c + d * R * 0.12 + normal * 0.01), tuple(c + d * R * 0.66 + normal * 0.01)], [(R * 0.07, 0.012)] * 2,
             mat=mat, segs=8, sub=1, domo=0.0, arriba=normal)
    cilindro(bm, tuple(c), tuple(c + normal * 0.05), R * 0.18, mat)              # eje
    cilindro(bm, tuple(c + normal * 0.05), tuple(c + normal * 0.07), R * 0.09, ACERO, segs=6)   # tuerca


def remaches_fila(bm, p0, p1, n, normal, r=0.022):
    p0, p1 = Vector(p0), Vector(p1)
    for k in range(n):
        p = p0.lerp(p1, k / (n - 1))
        esfera(bm, tuple(p + normal * 0.004), (r, r, r) if normal.z else (r * (0.6 if normal.x else 1), r * (0.6 if normal.y else 1), r), mat=LATON, segs=8, anillos=5)


def maquina(bm):
    # base de acero con patas
    caja(bm, (CX, CY, 0.17), (2 * HX + 0.3, 2 * HY + 0.3, 0.26), mat=ACERO, bisel=0.05, segs=3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cilindro(bm, (CX + sx * (HX + 0.05), CY + sy * (HY + 0.05), 0.0), (CX + sx * (HX + 0.05), CY + sy * (HY + 0.05), 0.06), 0.1, NEGRO, segs=16)
    # cuerpo redondeado
    caja(bm, (CX, CY, 1.45), (2 * HX, 2 * HY, 2.3), mat=TURQ, bisel=0.12, segs=4)
    # franjas de acero (abajo y arriba) con remaches
    for z in (0.5, 2.42):
        caja(bm, (CX, CY, z), (2 * HX + 0.04, 2 * HY + 0.04, 0.12), mat=ACERO, bisel=0.05, segs=3)
        remaches_fila(bm, (CX - HX + 0.15, FRENTE + 0.02, z), (CX + HX - 0.15, FRENTE + 0.02, z), 9, Vector((0, 1, 0)))
        remaches_fila(bm, (LADO + 0.02, CY - HY + 0.15, z), (LADO + 0.02, CY + HY - 0.15, z), 7, Vector((1, 0, 0)))
    # tapa en domo + cuello
    loft(bm, [(CX, CY, 2.48), (CX, CY, 2.66), (CX, CY, 2.82), (CX, CY, 2.94), (CX, CY, 3.0), (CX, CY, 3.02)],
         [(0.95, 0.8), (0.92, 0.77), (0.8, 0.67), (0.6, 0.5), (0.35, 0.3), (0.08, 0.07)], mat=TURQ, segs=32, sub=3, tapas=(False, True), domo=0.1)
    toro(bm, (CX, CY, 2.5), 0.88, 0.05, mat=LATON, segs=40, lados=8)
    # embudo de latón liso con orilla
    loft(bm, [(CX, CY, 2.95), (CX, CY, 3.2), (CX, CY, 3.45), (CX, CY, 3.6)],
         [(0.2, 0.2), (0.32, 0.32), (0.5, 0.5), (0.56, 0.56)], mat=LATON, segs=32, sub=3, tapas=(True, False), domo=0.0)
    toro(bm, (CX, CY, 3.6), 0.56, 0.04, mat=LATON, segs=40, lados=8)
    # tubos de cobre: salen de la tapa, hacen codo y suben al techo, con bridas
    for (x, y, dx) in ((-7.1, -7.2, 0.25), (-8.9, -7.3, -0.25)):
        camino = [(x, y, 2.55), (x, y, 3.0), (x + dx * 0.4, y, 3.35), (x + dx, y, 3.6), (x + dx, y, 4.2), (x + dx, y, 7.6)]
        loft(bm, camino, [(0.11, 0.11)] * len(camino), mat=COBRE, segs=20, sub=5, tapas=(False, False))
        for z in (2.62, 4.0, 5.6, 7.2):
            px = x if z < 3 else x + dx
            cilindro(bm, (px, y, z - 0.04), (px, y, z + 0.04), 0.155, LATON, segs=20)
            for k in range(6):
                a = 2 * math.pi * k / 6
                esfera(bm, (px + 0.135 * math.cos(a), y + 0.135 * math.sin(a), z + 0.045), (0.014, 0.014, 0.01), mat=ACERO, segs=6, anillos=4)
    # --- cara hacia el árbol: pantalla con marco
    caja(bm, (-8.0, FRENTE + 0.03, 1.8), (1.45, 0.08, 0.85), mat=NEGRO, bisel=0.04, segs=3)
    caja(bm, (-8.0, FRENTE + 0.065, 1.8), (1.25, 0.02, 0.67), mat=PANTALLA, bisel=0.03, segs=2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            esfera(bm, (-8.0 + sx * 0.66, FRENTE + 0.075, 1.8 + sz * 0.36), (0.022, 0.012, 0.022), mat=LATON, segs=8, anillos=5)
    # botones redondos con aro
    for k, col in enumerate((AMARILLO, AMARILLO, ROJO, ROJO)):
        x = -8.8 + k * 0.5
        cilindro(bm, (x, FRENTE, 1.05), (x, FRENTE + 0.04, 1.05), 0.12, ACERO, segs=24)
        loft(bm, [(x, FRENTE + 0.03, 1.05), (x, FRENTE + 0.08, 1.05)], [(0.085, 0.085), (0.08, 0.08)], mat=col, segs=20, sub=1, domo=0.5)
    # manómetro (reloj de presión) con aguja, a la izquierda
    gx, gz = -9.0, 1.45
    cilindro(bm, (gx, FRENTE, gz), (gx, FRENTE + 0.06, gz), 0.25, LATON, segs=32)
    cilindro(bm, (gx, FRENTE + 0.05, gz), (gx, FRENTE + 0.065, gz), 0.21, HOLLIN, segs=32)
    for k in range(9):
        a = math.radians(-135 + k * 33.75)
        esfera(bm, (gx + 0.17 * math.sin(a), FRENTE + 0.07, gz + 0.17 * math.cos(a)), (0.012, 0.006, 0.012), mat=AMARILLO, segs=6, anillos=4)
    a = math.radians(40)
    loft(bm, [(gx, FRENTE + 0.075, gz), (gx + 0.16 * math.sin(a), FRENTE + 0.075, gz + 0.16 * math.cos(a))], [(0.014, 0.006), (0.004, 0.004)],
         mat=ROJO, segs=6, sub=1, domo=0.3, arriba=Vector((0, 1, 0)))
    esfera(bm, (gx, FRENTE + 0.08, gz), (0.025, 0.012, 0.025), mat=ROJO, segs=10, anillos=6)
    # palanca con perilla roja (a la derecha)
    caja(bm, (-6.95, FRENTE + 0.04, 1.2), (0.16, 0.06, 0.5), mat=ACERO, bisel=0.02, segs=2)
    loft(bm, [(-6.95, FRENTE + 0.07, 1.05), (-6.95, FRENTE + 0.25, 1.3), (-6.95, FRENTE + 0.3, 1.45)], [(0.025, 0.025)] * 3, mat=ACERO, segs=10, sub=3)
    esfera(bm, (-6.95, FRENTE + 0.3, 1.48), (0.06, 0.06, 0.06), mat=ROJO)
    # --- boca de salida sobre la banda (los juguetes salen de aquí): marco + techito curvo + rampita
    bx, bz = -9.25, 0.98
    caja(bm, (bx, FRENTE + 0.02, bz), (0.46, 0.05, 0.36), mat=ACERO, bisel=0.03, segs=2)
    caja(bm, (bx, FRENTE + 0.035, bz - 0.02), (0.34, 0.03, 0.26), mat=HOLLIN, bisel=0.02, segs=2)
    loft(bm, [(bx, FRENTE + 0.02, bz + 0.12), (bx, FRENTE + 0.22, bz + 0.1)], [(0.24, 0.12), (0.24, 0.12)], mat=TURQ,
         segs=16, sub=1, tapas=(False, False), abierto=(0, 180), arriba=Vector((0, 0, 1)))
    caja(bm, (bx, FRENTE + 0.12, bz - 0.17), (0.34, 0.22, 0.03), mat=ACERO, bisel=0.01, segs=1,
         giro=Matrix.Rotation(math.radians(-18), 3, "X"))
    # --- cara +X: dos engranes y tornillos
    engrane(bm, (LADO, -6.2, 1.8), 0.42, 12, 0.06, LATON)
    engrane(bm, (LADO, -7.0, 1.0), 0.32, 10, 0.06, LATON)
    for (y, z) in ((-5.6, 2.2), (-7.4, 2.2), (-5.6, 0.75), (-7.4, 0.75)):
        cilindro(bm, (LADO, y, z), (LADO + 0.03, y, z), 0.04, ACERO, segs=6)
    # --- cara -X: escotilla redonda con manija
    hx0 = CX - HX
    cilindro(bm, (hx0, -6.5, 1.3), (hx0 - 0.06, -6.5, 1.3), 0.5, ACERO, segs=32)
    cilindro(bm, (hx0 - 0.05, -6.5, 1.3), (hx0 - 0.09, -6.5, 1.3), 0.4, TURQ, segs=32)
    for k in range(10):
        a = 2 * math.pi * k / 10
        esfera(bm, (hx0 - 0.065, -6.5 + 0.45 * math.cos(a), 1.3 + 0.45 * math.sin(a)), (0.012, 0.02, 0.02), mat=LATON, segs=8, anillos=5)
    loft(bm, [(hx0 - 0.09, -6.65, 1.3), (hx0 - 0.2, -6.6, 1.3), (hx0 - 0.2, -6.4, 1.3), (hx0 - 0.09, -6.35, 1.3)], [(0.025, 0.025)] * 4, mat=LATON, segs=10, sub=3)
    # chimenea pequeña con hollín en la parte de atrás de la tapa
    cilindro(bm, (-8.5, -7.15, 2.6), (-8.5, -7.15, 3.4), 0.12, ACERO, segs=20, tapas=(False, False))
    loft(bm, [(-8.5, -7.15, 3.4), (-8.5, -7.15, 3.5)], [(0.17, 0.17), (0.15, 0.15)], mat=HOLLIN, segs=20, sub=1, tapas=(False, True), domo=0.0)


poner_malla(bpy.data.objects["Maquina"], maquina, subsurf=0)
print("maquina v2 lista")
