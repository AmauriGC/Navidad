# -*- coding: utf-8 -*-
"""
CHIMENEA v2 (taller): la piedra, la repisa, las velas y el hogar se quedan; se cambian 3 cosas que eran de cajitas:
  - CORONA: era un anillo de 18 bolitas verdes + 4 bolitas rojas. Ahora es la misma corona de hojitas, moras, piñas
    y moño que pusimos en las puertas de las casas (corona() de coronas.py), escalada al tamaño de la de antes.
  - BOTAS NAVIDEÑAS (3): eran 2 cajas rojas + 1 blanca. Ahora: bota redonda (loft que baja y dobla hacia la punta),
    puño blanco esponjado, talón y punta blancos, franja verde y una argollita para colgarla del gancho.
  - TRONCOS del fuego (3): cilindros de 8 lados -> troncos con corteza irregular y cortes claros con anillos.
Mismo lugar y tamaño (se miden de las piezas viejas). El frente de la chimenea mira a +Y en Blender.
Uso: exec(modelado.py); exec(coronas.py); exec(chimenea_v2.py); hacer_chimenea()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

def _islas_cm(bm):
    bm.faces.ensure_lookup_table(); vist = set(); res = []
    for f in bm.faces:
        if f.index in vist: continue
        pila = [f]; isla = []; vist.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vist: vist.add(y.index); pila.append(y)
        res.append(isla)
    return res

def bota(bm, x, ytop, z_top, z_pie, ancho, largo_pie, R, B, V, rnd):
    """Bota colgando: la caña baja desde z_top, el pie apunta a -X. Plana en Y (grosor ~0.1)."""
    w = ancho / 2; g = 0.055
    z_t = z_pie + 0.1
    camino = [Vector((x, ytop, z_top - 0.05)), Vector((x, ytop, z_top - 0.3)), Vector((x + 0.01, ytop, z_t + 0.06)),
              Vector((x - 0.06, ytop, z_t - 0.04)), Vector((x - largo_pie * 0.55, ytop, z_t - 0.07)), Vector((x - largo_pie * 0.75, ytop, z_t - 0.05))]
    radios = [(w, g), (w * 0.96, g), (w * 1.05, g * 1.05), (w * 1.0, g * 1.05), (w * 0.85, g), (w * 0.55, g * 0.8)]
    loft(bm, camino, radios, mat=R, segs=16, sub=4, domo=0.8, arriba=Vector((0, 1, 0)))
    esfera(bm, (x + w * 0.55, ytop, z_t - 0.01), (0.07, g * 1.08, 0.075), mat=B, segs=12, anillos=8)                 # talón
    esfera(bm, (x - largo_pie * 0.68, ytop, z_t - 0.055), (0.075, g * 0.95, 0.06), mat=B, segs=12, anillos=8)      # punta
    loft(bm, [Vector((x, ytop, z_top - 0.2)), Vector((x, ytop, z_top - 0.25))], [(w * 1.01, g * 1.04)] * 2, mat=V, segs=16, sub=1, domo=0.0)   # franja
    # puño blanco esponjado
    loft(bm, [Vector((x, ytop, z_top - 0.12)), Vector((x, ytop, z_top))], [(w * 1.15, g * 1.35), (w * 1.12, g * 1.3)], mat=B, segs=16, sub=1, domo=0.5)
    for k in range(9):
        a = 2 * math.pi * k / 9
        esfera(bm, (x + math.cos(a) * w * 1.1, ytop + math.sin(a) * g * 1.25, z_top - 0.06 + rnd.uniform(-0.02, 0.02)), (0.04, 0.035, 0.04), mat=B, segs=8, anillos=6)
    toro(bm, (x + w * 0.8, ytop, z_top + 0.035), 0.03, 0.008, mat=R, segs=10, lados=5, inclinacion=math.pi / 2)   # argolla

def tronco_fuego(bm, p0, p1, r, CORT, CAS, rnd):
    eje = (p1 - p0); L = eje.length; d = eje.normalized()
    puntos = [p0 + d * (L * k / 6) for k in range(7)]
    radios = [(r * rnd.uniform(0.92, 1.06), r * rnd.uniform(0.92, 1.06)) for _ in puntos]
    antes = set(bm.faces)
    loft(bm, puntos, radios, mat=CAS, segs=14, sub=2, tapas=(False, False), domo=0.0)
    for p, s in ((p0, -1), (p1, 1)):
        c = bm.verts.new(p + d * s * 0.004)
        pts = []
        for k in range(14):
            a = 2 * math.pi * k / 14
            u = d.cross(Vector((0, 0, 1))).normalized(); v = d.cross(u).normalized()
            pts.append(bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r * 0.97))
        for k in range(14):
            f = bm.faces.new((c, pts[k], pts[(k + 1) % 14]) if s > 0 else (c, pts[(k + 1) % 14], pts[k])); f.material_index = CORT
        toro_pts = [p + d * s * 0.006 + (d.cross(Vector((0, 0, 1))).normalized() * math.cos(a) + d.cross(d.cross(Vector((0, 0, 1))).normalized()).normalized() * math.sin(a)) * r * 0.55 for a in [2 * math.pi * k / 14 for k in range(14)]]
        loft(bm, toro_pts + toro_pts[:3], [(0.006, 0.006)] * 17, mat=CAS, segs=4, sub=1, tapas=(False, False), domo=0.0)
    # nudos de corteza
    for _ in range(3):
        t = rnd.uniform(0.2, 0.8); a = rnd.uniform(0, 2 * math.pi)
        u = d.cross(Vector((0, 0, 1))).normalized(); v = d.cross(u).normalized()
        q = p0 + d * L * t + (u * math.cos(a) + v * math.sin(a)) * r * 0.95
        esfera(bm, tuple(q), (0.03, 0.03, 0.03), mat=CAS, segs=8, anillos=6)

def hacer_chimenea(semilla=9):
    o = bpy.data.objects["Chimenea"]; me = o.data; rnd = random.Random(semilla)
    bm = bmesh.new(); bm.from_mesh(me)
    nombres = [mt.name for mt in me.materials]
    def m(n):
        if n not in nombres: me.materials.append(bpy.data.materials[n]); nombres.append(n)
        return nombres.index(n)
    info = []
    for isla in _islas_cm(bm):
        vs = [v.co for f in isla for v in f.verts]
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        info.append((isla, lo, hi, {nombres[f.material_index] for f in isla}))
    corona_v = [i for i in info if i[1].z > 4.0 and (i[3] & {"Amb_VerdePino", "Amb_Rojo"})]
    botas_v = [i for i in info if 2.2 < i[1].z < 3.0 and i[3] <= {"Amb_Rojo", "Amb_Blanco"} and len(i[0]) == 54]
    troncos_v = [i for i in info if i[3] == {"Amb_Madera2"} and i[2].z < 1.0]
    if not corona_v: print("ya estaba hecho (sin piezas viejas)"); bm.free(); return
    lo = Vector((min(i[1].x for i in corona_v), min(i[1].y for i in corona_v), min(i[1].z for i in corona_v)))
    hi = Vector((max(i[2].x for i in corona_v), max(i[2].y for i in corona_v), max(i[2].z for i in corona_v)))
    c_cor = (lo + hi) / 2; R_cor = (hi.x - lo.x) / 2 - 0.15
    # cara de la piedra detrás de la corona: rayo desde el frente contra la piedra
    from mathutils.bvhtree import BVHTree
    piedra = [f for f in bm.faces if nombres[f.material_index].startswith("Amb_Piedra")]
    bm.verts.ensure_lookup_table()
    bvh = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in piedra])
    hit = bvh.ray_cast(Vector((c_cor.x, hi.y + 2.0, c_cor.z)), Vector((0, -1, 0)))
    y_pared = hit[0].y if hit[0] else lo.y + 0.09
    botas = []
    for x0 in sorted({round((i[1].x + i[2].x) / 2, 1) for i in botas_v if i[3] == {"Amb_Blanco"}}):
        grupo = [i for i in botas_v if i[1].x - 0.3 < x0 < i[2].x + 0.3]
        blo = Vector((min(i[1].x for i in grupo), min(i[1].y for i in grupo), min(i[1].z for i in grupo)))
        bhi = Vector((max(i[2].x for i in grupo), max(i[2].y for i in grupo), max(i[2].z for i in grupo)))
        botas.append((x0, blo, bhi))
    troncos = [((i[1] + i[2]) / 2, i[2] - i[1]) for i in troncos_v]
    bmesh.ops.delete(bm, geom=[f for i in corona_v + botas_v + troncos_v for f in i[0]], context="FACES")
    nuevo = bmesh.new()
    # corona (hecha a R=0.3 y escalada)
    M = {"oscuro": m("Amb_VerdePino"), "hoja": m("Corona_Verde"), "rojo": m("Amb_Rojo"), "pina": m("Amb_MaderaOscura"), "mono": m("Arbol_Mono")}
    tmp = bmesh.new(); corona(tmp, Vector((0, 0, 0)), Vector((0, 1, 0)), 0.3, rnd, M)
    k = R_cor / 0.3
    bmesh.ops.transform(tmp, matrix=Matrix.Translation((c_cor.x, y_pared, c_cor.z)) @ Matrix.Diagonal((k, k, k, 1)), verts=list(tmp.verts))
    mm = bpy.data.meshes.new("_tmp"); tmp.to_mesh(mm); tmp.free(); nuevo.from_mesh(mm); bpy.data.meshes.remove(mm)
    # botas
    R, B, V = m("Amb_Rojo"), m("Amb_Blanco"), m("Amb_VerdePino")
    for x0, blo, bhi in botas:
        bota(nuevo, x0 + 0.03, (blo.y + bhi.y) / 2, bhi.z - 0.02, blo.z, 0.26, bhi.x - blo.x, R, B, V, rnd)
    # troncos
    CORT, CAS = m("Amb_Madera3"), m("Amb_MaderaOscura")
    for c, t in troncos:
        r = min(t.y, t.z) / 2
        L = t.x - 2 * r * 0.2
        tronco_fuego(nuevo, c - Vector((L / 2, 0, 0)), c + Vector((L / 2, 0, 0)), r, CORT, CAS, rnd)
    for f in nuevo.faces: f.smooth = True
    mm = bpy.data.meshes.new("_tmp"); nuevo.to_mesh(mm); nuevo.free(); bm.from_mesh(mm); bpy.data.meshes.remove(mm)
    bm.to_mesh(me); bm.free(); me.update()
    print("corona R", round(R_cor, 2), "| botas", len(botas), "| troncos", len(troncos), "| tris", sum(len(p.vertices) - 2 for p in me.polygons))

def restaurar_chimenea(blend=PROYECTO + "/Library/BlenderBackup/antes_heno_chimenea.blend"):
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.meshes = ["Chimenea.001"]
    mm = dst.meshes[0]; tgt = bpy.data.objects["Chimenea"].data
    bm = bmesh.new(); bm.from_mesh(mm)
    viejos = [x.name.rsplit(".", 1)[0] if x.name.rsplit(".", 1)[-1].isdigit() else x.name for x in mm.materials]
    tn = [x.name for x in tgt.materials]
    for nm in viejos:
        if nm not in tn: tgt.materials.append(bpy.data.materials[nm]); tn.append(nm)
    for f in bm.faces: f.material_index = tn.index(viejos[f.material_index])
    bm.to_mesh(tgt); bm.free(); tgt.update(); bpy.data.meshes.remove(mm)
    for mt in [x for x in bpy.data.materials if x.users == 0 and x.name.rsplit(".", 1)[-1].isdigit()]: bpy.data.materials.remove(mt)
