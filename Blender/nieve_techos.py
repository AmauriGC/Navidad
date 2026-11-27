# -*- coding: utf-8 -*-
"""
NIEVE DE LOS TECHOS DEL ESTABLO Y DEL TALLER (Fase 5): eran losas planas (cajas biseladas de 54 caras, Amb_Nieve).
Se cambian por la misma ALMOHADA de nieve de las casas (almohada_nieve de casas_v2.py): encima del techo, orilla
redondeada, y en los aleros se dobla y escurre en gotitas. En la cumbrera sigue derecho.
Uso: exec(modelado.py); exec(casas_v2.py); exec(nieve_techos.py); hacer_nieve_techos()
"""
import bpy, bmesh, random
from collections import Counter

def nieve_techo(nombre_obj, semilla):
    o = bpy.data.objects[nombre_obj]; me = o.data
    nm = [m.name if m else "" for m in me.materials]
    if "Amb_Nieve" not in nm: print(nombre_obj, "sin Amb_Nieve"); return
    ni = nm.index("Amb_Nieve")
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    rnd = random.Random(semilla)
    losas = []
    for g in islas(bm):
        area = Counter()
        for f in g: area[f.material_index] += f.calc_area()
        if area[ni] / max(sum(area.values()), 1e-9) < 0.85 or len(g) != 54: continue
        c, e1, e2, e3, h = caja_orientada(g)
        if h[0] * h[1] * 4 > 0.25 and e3.z > 0.3: losas.append((g, (c, e1, e2, e3, h)))
    bmesh.ops.delete(bm, geom=list({v for g, _ in losas for f in g for v in f.verts}), context="VERTS")
    for _, (c, e1, e2, e3, h) in losas:
        almohada_nieve(bm, c, e1, e2, e3, h, ni, rnd)
    bm.to_mesh(me); bm.free(); me.update()
    print(nombre_obj, "losas -> almohadas:", len(losas), "| tris", sum(len(p.vertices) - 2 for p in me.polygons))

def hacer_nieve_techos():
    nieve_techo("Establo", 3)
    nieve_techo("Taller_Techo", 4)
