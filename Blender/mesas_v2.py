# -*- coding: utf-8 -*-
"""
MESAS v2 (Fase 4): Mesa_1..3 eran 6 cajas (cubierta, 4 patas, entrepaño) + cosas encima.
Se rehace SOLO la estructura (mismo tamaño y lugar); las herramientas, latas, rollos y martillos se quedan.
  - Cubierta de 5 tablones con biselito y separación, travesaños en las puntas.
  - Faldón (tablas bajo la cubierta) y patas torneadas: bloque cuadrado arriba, anillos y bulbos, pie redondo.
  - Entrepaño de tablones con travesaños; los cubos de color que había en el entrepaño ahora son regalos
    (función regalo de repisas_v2.py).
Uso: exec(modelado.py); exec(repisas_v2.py); exec(mesas_v2.py); hacer_mesas()   (restaurar_mesas() para repetir)
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

def hacer_mesa(nombre, semilla):
    o = bpy.data.objects[nombre]; me = o.data; rnd = random.Random(semilla)
    bm = bmesh.new(); bm.from_mesh(me)
    nombres = [mt.name for mt in me.materials]
    def m(n):
        if n not in nombres: me.materials.append(bpy.data.materials[n]); nombres.append(n)
        return nombres.index(n)
    info = []
    for isla in _islas(bm):
        lo, hi = _caja(isla); info.append((isla, lo, hi, {nombres[f.material_index] for f in isla}))
    tapa = max(info, key=lambda i: (i[2] - i[1]).x * (i[2] - i[1]).y if (i[2] - i[1]).z < 0.2 and i[1].z > 0.5 else 0)
    patas = [i for i in info if (i[2] - i[1]).z > 0.8 and i[3] <= MADERAS]
    entre = max(info, key=lambda i: (i[2] - i[1]).x * (i[2] - i[1]).y if i[2].z < 0.4 and (i[2] - i[1]).z < 0.1 else 0)
    cubos = [i for i in info if len(i[0]) == 54 and len(i[3]) == 1 and not (i[3] <= MADERAS) and i[1].z > entre[2].z - 0.02 and i[2].z < 0.7]
    lo, hi = tapa[1], tapa[2]
    largo_x = (hi.x - lo.x) >= (hi.y - lo.y)
    bmesh.ops.delete(bm, geom=[f for i in [tapa, entre] + patas + cubos for f in i[0]], context="FACES")
    T3, MO, M2 = m("Amb_Madera3"), m("Amb_MaderaOscura"), m("Amb_Madera2")
    nuevo = bmesh.new()
    def rect(x0, x1, y0, y1, z0, z1, mat, bisel):
        caja(nuevo, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat=mat, bisel=bisel, segs=2)
    # cubierta: tablones a lo largo
    n = 5; g = 0.008
    if largo_x:
        ancho = (hi.y - lo.y - g * (n - 1)) / n
        for k in range(n):
            y0 = lo.y + k * (ancho + g)
            rect(lo.x + 0.06, hi.x - 0.06, y0, y0 + ancho, lo.z + 0.02, hi.z, T3, 0.012)
        for x in (lo.x, hi.x - 0.07):
            rect(x, x + 0.07, lo.y, hi.y, lo.z + 0.02, hi.z + 0.004, MO, 0.012)
    else:
        ancho = (hi.x - lo.x - g * (n - 1)) / n
        for k in range(n):
            x0 = lo.x + k * (ancho + g)
            rect(x0, x0 + ancho, lo.y + 0.06, hi.y - 0.06, lo.z + 0.02, hi.z, T3, 0.012)
        for y in (lo.y, hi.y - 0.07):
            rect(lo.x, hi.x, y, y + 0.07, lo.z + 0.02, hi.z + 0.004, MO, 0.012)
    # patas torneadas + faldón
    cs = [((i[1] + i[2]) / 2) for i in patas]
    for c in cs:
        x, y = c.x, c.y
        rect(x - 0.075, x + 0.075, y - 0.075, y + 0.075, 0.6, lo.z + 0.02, MO, 0.015)
        perfil = [(0.6, 0.05), (0.56, 0.065), (0.5, 0.05), (0.38, 0.055), (0.3, 0.065), (0.24, 0.05), (0.12, 0.045), (0.06, 0.06), (0.0, 0.065)]
        loft(nuevo, [Vector((x, y, z)) for z, r in perfil], [(r, r) for z, r in perfil], mat=MO, segs=14, sub=2, domo=0.2)
    xs = sorted({round(c.x, 3) for c in cs}); ys = sorted({round(c.y, 3) for c in cs})
    for x in (xs[0], xs[-1]):
        rect(x - 0.03, x + 0.03, ys[0] + 0.07, ys[-1] - 0.07, 0.74, lo.z + 0.02, MO, 0.01)
    for y in (ys[0], ys[-1]):
        rect(xs[0] + 0.07, xs[-1] - 0.07, y - 0.03, y + 0.03, 0.74, lo.z + 0.02, MO, 0.01)
    # entrepaño de tablones
    e0, e1 = entre[1], entre[2]
    if largo_x:
        ancho = (e1.y - e0.y - g * 3) / 4
        for k in range(4):
            y0 = e0.y + k * (ancho + g); rect(e0.x, e1.x, y0, y0 + ancho, e0.z, e1.z, M2, 0.008)
        for x in (xs[0], xs[-1]): rect(x - 0.035, x + 0.035, ys[0], ys[-1], e0.z - 0.06, e0.z, MO, 0.01)
    else:
        ancho = (e1.x - e0.x - g * 3) / 4
        for k in range(4):
            x0 = e0.x + k * (ancho + g); rect(x0, x0 + ancho, e0.y, e1.y, e0.z, e1.z, M2, 0.008)
        for y in (ys[0], ys[-1]): rect(xs[0], xs[-1], y - 0.035, y + 0.035, e0.z - 0.06, e0.z, MO, 0.01)
    # cubos de color del entrepaño -> regalos
    for i in cubos:
        c = (i[1] + i[2]) / 2; t = i[2] - i[1]
        papel = nombres.index(next(iter(i[3])))
        liston = m("Amb_Amarillo") if papel != m("Amb_Amarillo") else m("Amb_Rojo")
        r = bmesh.new(); regalo(r, t.x * 0.95, t.y * 0.95, t.z, m, rnd, papel, liston)
        g_ = Matrix.Rotation(rnd.uniform(-0.25, 0.25), 4, "Z")
        bmesh.ops.transform(r, matrix=Matrix.Translation((c.x, c.y, i[1].z)) @ g_, verts=list(r.verts))
        tmp = bpy.data.meshes.new("_tmp"); r.to_mesh(tmp); r.free(); nuevo.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    for f in nuevo.faces: f.smooth = True
    tmp = bpy.data.meshes.new("_tmp"); nuevo.to_mesh(tmp); nuevo.free(); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    bm.to_mesh(me); bm.free(); me.update()
    print(nombre, "patas", len(patas), "regalos", len(cubos), "| tris", sum(len(p.vertices) - 2 for p in me.polygons))

def hacer_mesas():
    for k, n in enumerate(("Mesa_1", "Mesa_2", "Mesa_3")): hacer_mesa(n, 70 + k)

def restaurar_mesas(blend=PROYECTO + "/Library/BlenderBackup/antes_mesas_v2.blend"):
    nombres = ["Mesa_1", "Mesa_2", "Mesa_3"]
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.meshes = list(nombres)
    for mm in dst.meshes:
        tgt = bpy.data.objects[mm.name.rsplit(".", 1)[0]].data
        bm = bmesh.new(); bm.from_mesh(mm)
        viejos = [x.name.rsplit(".", 1)[0] if x.name.rsplit(".", 1)[-1].isdigit() else x.name for x in mm.materials]
        tn = [x.name for x in tgt.materials]
        for nm in viejos:
            if nm not in tn: tgt.materials.append(bpy.data.materials[nm]); tn.append(nm)
        for f in bm.faces: f.material_index = tn.index(viejos[f.material_index])
        bm.to_mesh(tgt); bm.free(); tgt.update(); bpy.data.meshes.remove(mm)
    for mt in [x for x in bpy.data.materials if x.users == 0 and x.name.rsplit(".", 1)[-1].isdigit()]: bpy.data.materials.remove(mt)
