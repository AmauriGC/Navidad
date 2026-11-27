# -*- coding: utf-8 -*-
"""
LUCES DEL PUEBLO v2 (rehace la malla del objeto LucesPueblo; el objeto y su nombre se quedan igual para Unity).
  1. Aleros de las 9 casas: el cable ya NO es una línea recta en la orilla del techo (atravesaba paredes y la nieve
     nueva). Para cada punto del alero:
       - un rayo HORIZONTAL desde afuera encuentra la pared  -> el punto se queda al menos 12 cm afuera de la pared;
       - un rayo HACIA ARRIBA encuentra la parte de abajo del alero / de la nieve -> ahí se engancha el cable.
     Entre enganches el cable cuelga poquito (catenaria) y si algún punto quedara dentro de la casa se empuja afuera.
  2. Guirnaldas entre farolitos (igual que antes, calculadas desde los objetos Farolito_N).
  3. Espirales de focos en 10 pinos cerca de los senderos (con los pinos YA acomodados).
Uso: exec(modelado.py); exec(luces_pueblo.py); hacer_luces()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

FOCO, CABLE = 0, 4     # materiales: 0-3 focos, 4 cable

def bvh_de(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); return t

def foco(bm, p, k, s=1.0):
    """Foco tipo gota liso con cuellito."""
    esfera(bm, p + Vector((0, 0, 0.02 * s)), (0.018 * s, 0.018 * s, 0.022 * s), mat=CABLE, segs=6, anillos=4)
    res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=1.0)
    for v in res["verts"]:
        x, y, z = v.co
        kk = 1 - 0.25 * max(0.0, z)
        v.co = p + Vector((x * 0.036 * s * kk, y * 0.036 * s * kk, -0.03 * s + z * 0.05 * s))
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = k % 4; f.smooth = True

def cable(bm, pts, cada, k, bvh=None, s=1.0, grosor=0.008):
    """Cable por los puntos dados; un foco cada 'cada' metros. Si se da bvh, ningún punto queda dentro."""
    if bvh is not None:
        for i, p in enumerate(pts):
            loc, nor, _, d = bvh.find_nearest(p)
            if loc is not None and (p - loc).dot(nor) < 0.05:
                pts[i] = loc + nor * 0.06
    loft(bm, [tuple(p) for p in pts], [(grosor, grosor)] * len(pts), mat=CABLE, segs=5, sub=1, domo=0.0)
    acum = 0.0
    for p0, p1 in zip(pts, pts[1:]):
        acum += (p1 - p0).length
        if acum >= cada:
            acum = 0.0; foco(bm, p1, k, s); k += 1
    return k

def colgar(a, b, flecha, paso=0.12):
    L = (b - a).length; n = max(2, int(L / paso))
    return [a.lerp(b, i / n) - Vector((0, 0, flecha * math.sin(math.pi * i / n))) for i in range(n + 1)]

# ---------------------------------------------------------------- 1. aleros
def lineas_alero(c):
    """Las 2 orillas bajas del techo (en coords locales de la casa), como hacía el script viejo."""
    me = c.data
    techo = [i for i, s in enumerate(c.material_slots) if s.material and s.material.name.startswith("Ext_Tejado")]
    cos = [me.vertices[i].co for i in {v for p in me.polygons if p.material_index in techo for v in p.vertices}]
    zmin = min(v.z for v in cos)
    bajos = [v for v in cos if v.z < zmin + 0.25]
    x0, x1 = min(v.x for v in bajos), max(v.x for v in bajos)
    y0, y1 = min(v.y for v in bajos), max(v.y for v in bajos)
    if (x1 - x0) >= (y1 - y0):
        return [(Vector((x0 + 0.15, y, zmin)), Vector((x1 - 0.15, y, zmin)), Vector((0, 1 if y > 0 else -1, 0))) for y in (y0, y1)], zmin
    return [(Vector((x, y0 + 0.15, zmin)), Vector((x, y1 - 0.15, zmin)), Vector((1 if x > 0 else -1, 0, 0))) for x in (x0, x1)], zmin

def aleros(bm, k=0):
    casas = [c for c in bpy.data.objects if c.name.startswith("Casa_")]
    for c in casas:
        bvh = bvh_de(c)
        M = c.matrix_world; R = M.to_3x3().normalized()
        lineas, zmin = lineas_alero(c)
        for a, b, afuera in lineas:
            enganches = []
            n = max(2, int((b - a).length / 0.5))
            for i in range(n + 1):
                pl = a.lerp(b, i / n)
                fuera = (R @ afuera).normalized()
                p = M @ pl
                # pared: rayo horizontal desde 3 m afuera hacia adentro, 0.6 m abajo del alero
                origen = p + fuera * 3.0 - Vector((0, 0, 0.6))
                hit = bvh.ray_cast(origen, -fuera, 6.0)
                pared = hit[0] if hit[0] is not None else p
                dist_pared = (p - pared).dot(fuera)
                q = p + fuera * (0.12 - dist_pared) if dist_pared < 0.12 else p.copy()
                # techo / nieve: rayo hacia arriba desde 1.2 m abajo
                hit = bvh.ray_cast(q - Vector((0, 0, 1.2)), Vector((0, 0, 1)), 3.0)
                if hit[0] is None: continue
                enganches.append(hit[0] - Vector((0, 0, 0.03)))
            for e0, e1 in zip(enganches, enganches[1:]):
                k = cable(bm, colgar(e0, e1, 0.07), 0.25, k, bvh=bvh)
    return k

# ---------------------------------------------------------------- 2. entre farolitos
def faroles_vidrio(o):
    """Centro del vidrio del farolito (como lo construía exterior_lindo.farolito)."""
    return o.matrix_world @ Vector((0, -0.27, 1.32))

def entre_farolitos(bm, k=0):
    far = sorted([o for o in bpy.data.objects if o.name.startswith("Farolito_")], key=lambda o: o.name)
    # agrupar en caminos: farolitos consecutivos cerca uno del otro
    for a, b in zip(far, far[1:]):
        pa, pb = faroles_vidrio(a), faroles_vidrio(b)
        if (pa - pb).length > 9: continue
        k = cable(bm, colgar(pa + Vector((0, 0, 0.25)), pb + Vector((0, 0, 0.25)), 0.55, paso=0.15), 0.35, k)
    return k

# ---------------------------------------------------------------- 3. pinos con luces
def pinos_con_luces(bm, cuantos=10, k=0):
    sen = bpy.data.objects["Senderos"]
    pts = []; vis = set()
    for v in sen.data.vertices:
        p = sen.matrix_world @ v.co; key = (round(p.x / 3), round(p.y / 3))
        if key not in vis: vis.add(key); pts.append(p)
    cand = []
    for o in bpy.data.objects:
        if not o.name.startswith("Pino_"): continue
        d = min((o.location.xy - p.xy).length for p in pts)
        if 3.0 < d < 10.0 and o.dimensions.z < 12: cand.append((d, o))
    cand.sort(key=lambda t: t[0])
    elegidos = []
    for d, o in cand:
        if all((o.location - e.location).length > 8 for e in elegidos): elegidos.append(o)
        if len(elegidos) >= cuantos: break
    for o in elegidos:
        bvh = bvh_de(o); base = o.location; H = o.dimensions.z
        pts = []
        for i in range(221):
            t = i / 220; a = t * 4.0 * 2 * math.pi
            z = base.z + H * (0.12 + 0.78 * t)
            d = Vector((math.cos(a), math.sin(a), 0))
            hit = bvh.ray_cast(Vector((base.x, base.y, z)) + d * 20, -d)
            if hit[0] is not None: pts.append(hit[0] + d * 0.07)
        k = cable(bm, pts, 0.55, k, s=1.5, grosor=0.012)
    return k, [o.name for o in elegidos]

def hacer_luces():
    o = bpy.data.objects["LucesPueblo"]; me = o.data
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    bm = bmesh.new()
    k1 = aleros(bm); k2 = entre_farolitos(bm, k1); k3, nombres = pinos_con_luces(bm, k=k2)
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print("focos aleros", k1, "farolitos", k2 - k1, "pinos", k3 - k2, "| tris", sum(len(p.vertices) - 2 for p in me.polygons))
    print("pinos con luces:", nombres)
    return nombres
