# -*- coding: utf-8 -*-
"""
CARÁMBANOS EN SU LUGAR: con la nieve nueva de los techos (almohada que escurre), los carámbanos (Ext_Hielo) quedaron
flotando 9-20 cm abajo, escondidos detrás de la orilla de nieve, o colgando de nada (casa en A).
Regla: un carámbano real cuelga de la ORILLA de la nieve. Para cada carámbano:
  1. Dirección "hacia afuera" = eje horizontal dominante desde el centro de la casa hasta el carámbano.
  2. Se prueba moverlo hacia afuera/adentro (-0.4 a +0.4 m, de 2 en 2 cm); en cada posición un rayo HACIA ARRIBA
     mide dónde está la parte de abajo de la nieve/techo. Se elige la posición con la orilla MÁS BAJA (la punta del
     escurrido), SOLO de nieve o techo (no marcos de ventana) y a menos de 0.5 m de altura de diferencia.
  3. Se mueve ahí y se sube/baja para que su parte de arriba quede 1.5 cm metida en la nieve (pegado, nunca flotando).
Uso: exec(caramblanos.py); arreglar_caramblanos()
"""
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def arreglar_malla(me, meter=0.015):
    nm = [m.name if m else "" for m in me.materials]
    if "Ext_Hielo" not in nm: return 0, 0
    ih = nm.index("Ext_Hielo")
    validos = {i for i, n in enumerate(nm) if n == "Ext_NieveBrillo" or n.startswith("Ext_Tejado")}
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    vidx = {}; verts = []; polys = []; mat_poly = []
    for f in bm.faces:
        if f.material_index == ih: continue
        mat_poly.append(f.material_index)
        p = []
        for v in f.verts:
            if v.index not in vidx: vidx[v.index] = len(verts); verts.append(v.co.copy())
            p.append(vidx[v.index])
        polys.append(p)
    bvh = BVHTree.FromPolygons(verts, polys)
    vist = set(); islas = []
    for f in bm.faces:
        if f.index in vist or f.material_index != ih: continue
        pila = [f]; isla = []; vist.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vist and y.material_index == ih: vist.add(y.index); pila.append(y)
        islas.append(isla)
    movidos = sin_lugar = 0
    for isla in islas:
        vs = list({v for f in isla for v in f.verts})
        top = max(v.co.z for v in vs)
        c = sum((v.co for v in vs), Vector()) / len(vs)
        d = Vector((c.x, 0, 0)) if abs(c.x) > abs(c.y) else Vector((0, c.y, 0))
        if d.length < 1e-4: d = Vector((1, 0, 0))
        d.normalize()
        mejor = None
        for k in range(-20, 21):
            q = Vector((c.x, c.y, 0)) + d * (k * 0.02)
            hit = bvh.ray_cast(Vector((q.x, q.y, top - 0.8)), Vector((0, 0, 1)), 1.6)
            if hit[0] is None: continue
            if hit[1].z > -0.2: continue          # que sea una cara que mira hacia abajo (parte de abajo)
            if mat_poly[hit[2]] not in validos: continue   # solo nieve o techo (no marcos de ventana)
            z = hit[0].z
            if abs(z - top) > 0.5: continue
            if mejor is None or z < mejor[0] - 0.005: mejor = (z, q)
        if mejor is None: sin_lugar += 1; continue
        z, q = mejor
        delta = Vector((q.x - c.x, q.y - c.y, (z + meter) - top))
        for v in vs: v.co += delta
        movidos += 1
    bm.to_mesh(me); bm.free(); me.update()
    return movidos, sin_lugar

def arreglar_caramblanos():
    for mn in ("CasaRoja", "CasaAzul", "CasaVerde", "CasaTroncos", "CasaA"):
        print(mn, "movidos / sin lugar:", arreglar_malla(bpy.data.meshes[mn]))

def restaurar_desde(blend):
    """Regresa las posiciones de vértices de las 5 mallas de casas desde un .blend de respaldo (misma topología)."""
    nombres = ["CasaRoja", "CasaAzul", "CasaVerde", "CasaTroncos", "CasaA"]
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.meshes = [n for n in src.meshes if n in nombres]
    for m in dst.meshes:
        original = bpy.data.meshes[m.name[:-4]] if m.name.endswith(".001") else None
        if original and len(original.vertices) == len(m.vertices):
            for a, b in zip(original.vertices, m.vertices): a.co = b.co
            original.update()
        bpy.data.meshes.remove(m)
    print("restauradas")
