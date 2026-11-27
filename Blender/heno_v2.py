# -*- coding: utf-8 -*-
"""
HENO v2 (establo): la paca era una caja lisa. Ahora (mismo tamaño y lugar):
  - 7 "rebanadas" (así vienen las pacas de verdad) con orillas redondeadas, cada una un poquito movida/girada;
  - pajitas que se salen por los lados y arriba (tubitos delgados en direcciones al azar);
  - 2 vueltas de cordel (Amb_Madera) que aprietan la paca.
Materiales: 0 Amb_Paja, 1 Amb_Madera.
Uso: exec(modelado.py); exec(heno_v2.py); hacer_heno()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

def hacer_heno(semilla=5):
    o = bpy.data.objects["Heno"]; me = o.data
    vs = [v.co for v in me.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    if "caja_heno" not in me: me["caja_heno"] = list(lo) + list(hi)
    lo = Vector(me["caja_heno"][:3]); hi = Vector(me["caja_heno"][3:])
    rnd = random.Random(semilla)
    t = hi - lo; c = (lo + hi) / 2
    largo_x = t.x >= t.y
    L = t.x if largo_x else t.y; A = t.y if largo_x else t.x; H = t.z
    bm = bmesh.new()
    n = 7; e = L / n
    for k in range(n):
        u = -L / 2 + e * (k + 0.5)
        g = Matrix.Rotation(rnd.uniform(-0.03, 0.03), 3, "X") @ Matrix.Rotation(rnd.uniform(-0.03, 0.03), 3, "Z")
        caja(bm, (u, rnd.uniform(-0.015, 0.015), H / 2 - 0.01 + rnd.uniform(-0.01, 0.01)),
             (e * 1.02, A * 0.97, H * 0.98), mat=0, bisel=0.03, segs=2, giro=g)
    # pajitas
    for _ in range(140):
        cara = rnd.choice(("arriba", "frente", "atras", "lado"))
        if cara == "arriba": p = Vector((rnd.uniform(-L / 2, L / 2), rnd.uniform(-A / 2, A / 2), H)); d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.6))
        elif cara == "frente": p = Vector((rnd.uniform(-L / 2, L / 2), -A / 2, rnd.uniform(0.05, H))); d = Vector((rnd.uniform(-1, 1), -0.7, rnd.uniform(-0.6, 0.6)))
        elif cara == "atras": p = Vector((rnd.uniform(-L / 2, L / 2), A / 2, rnd.uniform(0.05, H))); d = Vector((rnd.uniform(-1, 1), 0.7, rnd.uniform(-0.6, 0.6)))
        else:
            s = rnd.choice((-1, 1)); p = Vector((s * L / 2, rnd.uniform(-A / 2, A / 2), rnd.uniform(0.05, H))); d = Vector((s * 0.7, rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6)))
        d.normalize(); largo = rnd.uniform(0.05, 0.13)
        p0 = p - d * 0.03
        loft(bm, [p0, p0 + d * largo * 0.5 + Vector((0, 0, -0.01)), p0 + d * largo], [(0.005, 0.005), (0.004, 0.004), (0.002, 0.002)], mat=0, segs=4, sub=1, domo=0.0)
    # cordel: dos vueltas
    for u in (-L * 0.25, L * 0.25):
        pts = []
        for k in range(33):
            a = 2 * math.pi * k / 32
            y = math.cos(a) * (A / 2 + 0.01); z = H / 2 + math.sin(a) * (H / 2 + 0.01)
            y = max(-A / 2 - 0.012, min(A / 2 + 0.012, y * 1.25)); z = max(-0.002, min(H + 0.012, H / 2 + (z - H / 2) * 1.25))
            pts.append(Vector((u, y, z)))
        loft(bm, pts, [(0.012, 0.012)] * len(pts), mat=1, segs=6, sub=1, tapas=(False, False), domo=0.0)
    R = Matrix.Identity(4) if largo_x else Matrix.Rotation(math.pi / 2, 4, "Z")
    bmesh.ops.transform(bm, matrix=Matrix.Translation((c.x, c.y, lo.z)) @ R, verts=list(bm.verts))
    for f in bm.faces: f.smooth = True
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print("heno tris", sum(len(p.vertices) - 2 for p in me.polygons), [m.name for m in me.materials])
