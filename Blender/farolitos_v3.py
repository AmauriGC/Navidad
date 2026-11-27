# -*- coding: utf-8 -*-
"""
FAROLITOS v3 (26-nov): sobre farolitos.py (v2). Cambios:
  - el listón rojo sube en espiral por TODO el poste (antes solo a media altura) => bastón de caramelo;
  - ramita de pino (agujas = conos verdes) con 3 bayas detrás del moño;
  - montoncito de nieve low-poly al pie (icoesfera achatada, facetada).
El centro del vidrio sigue en (0, -0.27, 1.32) => luces de Unity y guirnaldas entre farolitos no se mueven.
Materiales: 0 metal negro, 1 vidrio, 2 nieve, 3 rojo, 4 verde pino (nuevo).
Uso: exec(modelado.py); exec(cerca_faroles.py); exec(farolitos.py); exec(farolitos_v3.py); hacer_farolitos_v3()
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

VER = 4
_farolito_v2 = farolito

def _espiral_completa(bm, TOP=1.78):
    hel = []
    for s in range(53):
        t = s / 52; a = t * 2 * math.pi * 6.5; z = 0.22 + t * (TOP - 0.3)
        r = 0.04 - 0.01 * z / TOP + 0.004
        hel.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    loft(bm, hel, [(0.009, 0.03)] * len(hel), mat=ROJ, segs=4, sub=1, tapas=(True, True), arriba=Vector((0, 0, 1)))

def _ramita(bm, rnd, zm):
    # agujas: conitos verdes en abanico detrás del moño
    for k in range(7):
        a = -1.2 + k * 0.4 + rnd.uniform(-0.08, 0.08)
        d = Vector((math.sin(a), -0.15, math.cos(a) * 0.55 + 0.1)).normalized()
        p0 = Vector((0, -0.03, zm)); p1 = p0 + d * rnd.uniform(0.09, 0.12)
        loft(bm, [p0, p1], [(0.026, 0.016), (0.012, 0.008)], mat=VER, segs=6, sub=1, tapas=(True, True), arriba=Vector((0, -1, 0)))
    for k in range(3):
        esfera(bm, (0.03 * (k - 1), -0.07, zm - 0.03 + 0.02 * (k % 2)), (0.018,) * 3, mat=ROJ, segs=8, anillos=6)

def _monton(bm, rnd):
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in res["verts"]:
        n = v.co.normalized()
        d = 1 + 0.15 * noise.noise(n * 2.5 + Vector((rnd.random() * 9, 0, 0)))
        v.co = Vector((n.x * 0.24 * d, n.y * 0.24 * d, n.z * 0.09 * d - 0.02))
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = NIE; f.smooth = False

def farolito_v3(bm, rnd):
    _farolito_v2(bm, rnd)
    # quitar el listón v2 (era la única hélice roja abajo de z 1.25) y poner la completa
    viejo = [f for f in bm.faces if f.material_index == ROJ and all(0.3 < v.co.z < 1.26 and v.co.xy.length < 0.09 for v in f.verts)]
    bmesh.ops.delete(bm, geom=viejo, context="FACES")
    _espiral_completa(bm)
    _ramita(bm, rnd, 1.78 - 0.12)
    _monton(bm, rnd)
    for f in bm.faces: f.smooth = False      # LOW-POLY parejo: todo con caras planas

def hacer_farolitos_v3(semilla=11):
    rojo = bpy.data.materials["Amb_Rojo"]; verde = bpy.data.materials["Ext_PinoD"]
    n = 0
    for o in sorted([o for o in bpy.data.objects if o.name.startswith("Farolito_")], key=lambda o: o.name):
        me = o.data
        while len(me.materials) < 4: me.materials.append(rojo)
        if len(me.materials) < 5: me.materials.append(verde)
        rnd = random.Random(semilla + n)
        bm = bmesh.new(); farolito_v3(bm, rnd)
        me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
        n += 1
    print("farolitos v3:", n, "| tris c/u:", sum(len(p.vertices) - 2 for p in o.data.polygons))
