# -*- coding: utf-8 -*-
"""
ESFERAS v2 (del Gran Árbol y la pieza recogible). Antes: esfera de 320 triángulos sin suavizar (se veía facetada).
Ahora: esfera lisa (32x20) + decoración que cambia según el estilo, y tapa de corona con argolla.
  estilo 0: franja ecuatorial + dos filetes + puntitos en zigzag
  estilo 1: gajos (6 costillas de polo a polo)
  estilo 2: dos anillos y perlitas
Las rojas llevan adornos dorados (Arbol_Oro); las doradas, adornos rojos (Esfera_Roja).
Conserva nombres y orígenes: Esfera_N (centro de la esfera), Esfera_N_Tapa (a +0.25 en Z), Pieza_Esfera.
Uso: exec(modelado.py); exec(esferas.py)
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

ORO = bpy.data.materials["Arbol_Oro"]; ROJA = bpy.data.materials["Esfera_Roja"]; DORADA = bpy.data.materials["Esfera_Dorada"]


def punto_sup(r, rz, lat, lon, extra=0.0):
    """Punto sobre el elipsoide en latitud/longitud (radianes), salido 'extra' hacia afuera."""
    n = Vector((math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)))
    return Vector((n.x * (r + extra), n.y * (r + extra), n.z * (rz + extra))), n


def bola(bm, r, estilo, c=Vector((0, 0, 0))):
    rz = r * 1.04
    esfera(bm, tuple(c), (r, r, rz), mat=0, segs=36, anillos=22)
    if estilo == 0:
        toro(bm, tuple(c), r * 1.0, r * 0.065, mat=1, segs=48, lados=8)
        for lat in (0.2, -0.2):
            z = c.z + math.sin(lat) * rz
            toro(bm, (c.x, c.y, z), r * math.cos(lat) * 1.0, r * 0.022, mat=1, segs=40, lados=6)
        for k in range(16):
            lon = 2 * math.pi * k / 16
            lat = 0.36 if k % 2 == 0 else -0.36
            p, n = punto_sup(r, rz, lat, lon, 0.0)
            esfera(bm, tuple(c + p), (r * 0.05, r * 0.05, r * 0.05), mat=1, segs=8, anillos=6)
    elif estilo == 1:
        for k in range(6):
            lon = 2 * math.pi * k / 6
            camino = [tuple(c + punto_sup(r, rz, math.radians(a), lon, 0.0)[0]) for a in range(-70, 75, 14)]
            loft(bm, camino, [(r * 0.035, r * 0.035)] * len(camino), mat=1, segs=8, sub=2, domo=0.8)
        toro(bm, tuple(c), r * 1.0, r * 0.04, mat=1, segs=48, lados=6)
    else:
        for lat in (0.42, -0.42):
            z = c.z + math.sin(lat) * rz
            toro(bm, (c.x, c.y, z), r * math.cos(lat), r * 0.045, mat=1, segs=40, lados=8)
        for k in range(10):
            lon = 2 * math.pi * k / 10 + math.pi / 10
            p, n = punto_sup(r, rz, 0.0, lon, 0.0)
            esfera(bm, tuple(c + p), (r * 0.085, r * 0.085, r * 0.085), mat=1, segs=10, anillos=8)


def tapa(bm, r, c=Vector((0, 0, 0)), z0=None):
    """Corona estriada + argolla. c = centro de la esfera; se construye arriba del polo."""
    rz = r * 1.04
    base = c.z + rz * 0.93
    rc = r * 0.27
    # corona con 12 estrías (radio que sube y baja alrededor)
    n, filas = 48, 4
    anillos = []
    for i in range(filas):
        z = base + r * 0.3 * i / (filas - 1)
        rr = rc * (1.0 - 0.12 * i / (filas - 1))
        anillos.append([bm.verts.new((c.x + rr * (1 + 0.08 * math.cos(12 * 2 * math.pi * j / n)) * math.cos(2 * math.pi * j / n),
                                      c.y + rr * (1 + 0.08 * math.cos(12 * 2 * math.pi * j / n)) * math.sin(2 * math.pi * j / n), z)) for j in range(n)])
    for i in range(filas - 1):
        for j in range(n):
            f = bm.faces.new((anillos[i][j], anillos[i][(j + 1) % n], anillos[i + 1][(j + 1) % n], anillos[i + 1][j])); f.smooth = True
    cen = bm.verts.new((c.x, c.y, base + r * 0.33))
    for j in range(n):
        f = bm.faces.new((anillos[-1][j], anillos[-1][(j + 1) % n], cen)); f.smooth = True
    toro(bm, (c.x, c.y, base + r * 0.02), rc * 1.05, r * 0.03, mat=0, segs=32, lados=6)       # orillita de abajo
    # argolla vertical
    toro(bm, (c.x, c.y, base + r * 0.48), r * 0.13, r * 0.03, mat=0, segs=20, lados=6, inclinacion=math.radians(90))


def esfera_arbol(i):
    e = bpy.data.objects[f"Esfera_{i}"]; t = bpy.data.objects[f"Esfera_{i}_Tapa"]
    roja = e.material_slots[0].material == ROJA
    estilo = (i - 1) % 3
    poner_malla(e, lambda bm: bola(bm, 0.225, estilo), materiales=[ROJA if roja else DORADA, ORO if roja else ROJA], subsurf=0)
    # la tapa: construida en coordenadas de la esfera y movida al origen de la Tapa (+0.25 en Z)
    M = t.matrix_world.inverted() @ e.matrix_world
    def construir(bm):
        tapa(bm, 0.225)
        bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    poner_malla(t, construir, materiales=[ORO], subsurf=0)


for i in range(1, 7):
    esfera_arbol(i)

def pieza(bm):
    c = Vector((0, 0, -0.03))
    bola(bm, 0.15, 0, c)
    antes = len(bm.verts)
    tapa(bm, 0.15, c)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        if all(v.index >= antes for v in f.verts): f.material_index = 1   # la tapa usa el material dorado (slot 1)

poner_malla(bpy.data.objects["Pieza_Esfera"], pieza, materiales=[ROJA, ORO], subsurf=0)
print("esferas v2 listas")
