# -*- coding: utf-8 -*-
"""
GRAN ÁRBOL v3 ("aún más bonito"). Usa falda_suave / recolocar_esferas / guirnalda_espiral de suavizado.py
y loft / esfera / toro de modelado.py.
  - Nivel1-3: 3 capas de follaje por nivel, más lóbulos y más muestras (más redondo, menos "papel"),
    cada lóbulo con una NERVADURA más clara al centro (parece rama).
  - Cadenas de cuentas doradas (oropel) colgando en arcos alrededor de cada nivel.
  - Maceta: barril redondeado con aros dorados y un listón rojo con moño al frente.
  - Esferas recolocadas sobre la superficie nueva y guirnalda con MÁS focos (cada 0.22 m).
Uso: exec(modelado.py); exec(suavizado.py); exec(arbol_bonito.py)
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ORO = bpy.data.materials["Arbol_Oro"]
NIEVE = bpy.data.materials["Arbol_Nieve"]

NIVELES_V3 = {
    #           origen  (z_apex, z_rim, R, lóbulos, caída)
    "Nivel1": (1.5,  [(3.80, 1.32, 2.48, 16, 0.20), (3.45, 1.58, 2.22, 14, 0.18), (3.15, 1.85, 1.86, 12, 0.16)]),
    "Nivel2": (2.9,  [(4.90, 2.70, 1.98, 14, 0.20), (4.60, 2.95, 1.74, 12, 0.18), (4.35, 3.22, 1.44, 10, 0.16)]),
    "Nivel3": (4.15, [(5.92, 3.95, 1.42, 11, 0.22), (5.70, 4.20, 1.18, 10, 0.20), (5.52, 4.45, 0.92, 8, 0.18)]),
}
MUESTRAS = 5


def bvh_de(bm):
    return BVHTree.FromBMesh(bm)


def nivel(nombre, origen, faldas):
    o = bpy.data.objects[nombre]; me = o.data
    if "Arbol_Oro" not in [m.name for m in me.materials]: me.materials.append(ORO)
    mats = [m.name for m in me.materials]
    osc, cla, nie, oro = (mats.index(n) for n in ("Arbol_Verde", "Arbol_VerdeClaro", "Arbol_Nieve", "Arbol_Oro"))
    bm = bmesh.new()
    for i, (za, zr, R, lob, caida) in enumerate(faldas):
        rnd = random.Random(hash(nombre) % 1000 + i * 7)
        def mat(k, j, l, t, rnd=rnd):
            centro = (j % MUESTRAS) == MUESTRAS // 2            # la muestra del centro del lóbulo = nervadura
            if centro and t > 0.35: return cla
            return cla if rnd.random() < 0.08 else osc
        falda_suave(bm, za - origen, zr - origen, R, lob, caida, i * math.pi / lob + 0.13 * i, 11 + i, mat, K=8, muestras=MUESTRAS, rizo=0.05)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bvh = bvh_de(bm)
    # oropel: arcos de cuentas doradas pegados a la superficie (rayos horizontales hacia el tronco)
    za, zr, R, lob, caida = faldas[0]
    z_alto = zr - origen + (za - zr) * 0.42
    arcos = max(6, lob // 2)
    n = arcos * 26
    for k in range(n):
        t = k / n
        a = 2 * math.pi * t + 0.2
        fase = (t * arcos) % 1.0
        z = z_alto - 0.28 * math.sin(math.pi * fase)                 # cuelga entre dos puntos
        d = Vector((math.cos(a), math.sin(a), 0))
        hit = bvh.ray_cast(Vector((0, 0, z)) + d * 5, -d)
        if hit[0] is None: continue
        c = hit[0] + d * 0.035
        res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.032 if k % 3 else 0.042)
        for v in res["verts"]: v.co += c
        for f in {f for v in res["verts"] for f in v.link_faces}:
            f.material_index = oro; f.smooth = True
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    for p in me.polygons: pass
    o.modifiers.clear()


def maceta():
    o = bpy.data.objects["Maceta"]
    MAC, ORO_I = 0, 1
    def construir(bm):
        # barril/maceta redondeada: se ensancha arriba con labio grueso
        loft(bm, [(0, 0, 0.02), (0, 0, 0.3), (0, 0, 0.7), (0, 0, 1.05), (0, 0, 1.18)],
             [(0.9, 0.9), (0.98, 0.98), (1.06, 1.06), (1.1, 1.1), (1.12, 1.12)], mat=MAC, segs=48, sub=3, tapas=(True, False), domo=0.05)
        toro(bm, (0, 0, 1.18), 1.1, 0.07, mat=MAC, segs=64, lados=10)                 # labio
        for z, R in ((0.14, 0.935), (1.02, 1.1)):                                       # aros dorados
            toro(bm, (0, 0, z), R, 0.035, mat=ORO_I, segs=64, lados=8)
        # listón rojo (mismo material de la maceta pero un poco salido) con moño dorado al frente
        toro(bm, (0, 0, 0.62), 1.045, 0.05, mat=ORO_I, segs=64, lados=8)
        for s in (-1, 1):
            loft(bm, [(0, -1.08, 0.66), (s * 0.18, -1.13, 0.8), (s * 0.34, -1.1, 0.7), (s * 0.18, -1.1, 0.6), (0, -1.08, 0.64)],
                 [(0.05, 0.03), (0.09, 0.03), (0.1, 0.03), (0.08, 0.03), (0.05, 0.03)], mat=ORO_I, segs=10, sub=4, domo=0.5,
                 arriba=Vector((0, 1, 0)))
            loft(bm, [(s * 0.04, -1.08, 0.6), (s * 0.14, -1.12, 0.42), (s * 0.2, -1.1, 0.3)],
                 [(0.06, 0.02), (0.07, 0.02), (0.06, 0.02)], mat=ORO_I, segs=8, sub=3, domo=0.4, arriba=Vector((0, 1, 0)))
        esfera(bm, (0, -1.11, 0.65), (0.07, 0.05, 0.07), mat=ORO_I)
    poner_malla(o, construir, subsurf=0)


for nombre, (origen, faldas) in NIVELES_V3.items():
    nivel(nombre, origen, faldas)
maceta()
bvh = bvh_ramas()
recolocar_esferas(bvh)
guirnalda_espiral(bvh, vueltas=4.2, z0=1.6, z1=5.4, cada=0.22)
print("árbol v3 listo")
