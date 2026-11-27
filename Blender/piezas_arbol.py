# -*- coding: utf-8 -*-
"""
PIEZAS A JUEGO CON EL ÁRBOL: cada pieza que recoge el elfo se hace COPIANDO la malla real de la parte del árbol
(con sus modificadores ya aplicados y sus mismos materiales) y se escala al tamaño de la pieza. Así lo que llevas
en la mano es exactamente lo que aparece en el árbol al colocarla.
  - Pieza_Maceta   = Maceta + Tierra + Tronco
  - Pieza_Rama     = Nivel3 (una capa de follaje del árbol, en chiquito)
  - Pieza_Esfera   = Esfera_1 + su Tapa (gancho dorado)
  - Pieza_Estrella = Estrella (con su base)
  - Pieza_Guirnalda= rollo: el mismo cable y los MISMOS focos de la guirnalda del árbol, enrollados (tamaño real)
Cada pieza sigue siendo UNA sola malla (la regla del juego: si no, la escala al recoger se rompe) y conserva el centro
de su caja donde estaba la anterior, para que el prefab de Unity no se mueva.
También: el Tronco de la maceta se rehace redondo (24 lados, liso) en lugar de octagonal.
Uso: exec(modelado.py); exec(piezas_arbol.py); hacer_piezas()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

def bm_evaluado(obj, m_rel):
    """bmesh con la malla evaluada (modificadores aplicados) de obj, transformada por m_rel."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); ev.to_mesh_clear()
    bm.transform(m_rel)
    return bm

def juntar(destino_me, partes):
    """partes = [(obj, matriz)]. Junta todo en destino_me reacomodando los índices de material."""
    mats = []
    bm = bmesh.new()
    for obj, m in partes:
        b = bm_evaluado(obj, m)
        mapa = {}
        for i, mt in enumerate(obj.data.materials):
            if mt not in mats: mats.append(mt)
            mapa[i] = mats.index(mt)
        for f in b.faces: f.material_index = mapa.get(f.material_index, 0)
        tmp = bpy.data.meshes.new("_tmp"); b.to_mesh(tmp); b.free()
        bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    return bm, mats

def ajustar(bm, centro_viejo, tam_viejo, eje="max"):
    """Escala uniforme para que la medida más grande sea la de antes, y centra la caja en el centro viejo."""
    mn = Vector((min(v.co[i] for v in bm.verts) for i in range(3)))
    mx = Vector((max(v.co[i] for v in bm.verts) for i in range(3)))
    s = max(tam_viejo) / max(mx - mn)
    c = (mn + mx) / 2
    for v in bm.verts: v.co = centro_viejo + (v.co - c) * s
    return s

def caja_local(me):
    mn = Vector((min(v.co[i] for v in me.vertices) for i in range(3)))
    mx = Vector((max(v.co[i] for v in me.vertices) for i in range(3)))
    return (mn + mx) / 2, mx - mn

def escribir(obj, bm, mats):
    me = obj.data
    me.clear_geometry(); me.materials.clear()
    for m in mats: me.materials.append(m)
    bm.to_mesh(me); bm.free(); me.update()
    obj.modifiers.clear()
    return sum(len(p.vertices) - 2 for p in me.polygons)

def relativo(obj, raiz):
    return raiz.matrix_world.inverted() @ obj.matrix_world

def tronco_redondo():
    t = bpy.data.objects["Tronco"]; me = t.data
    c, tam = caja_local(me)
    mat = me.materials[0]
    bm = bmesh.new()
    r = tam.x / 2; z0 = c.z - tam.z / 2; z1 = c.z + tam.z / 2
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r * 0.92, depth=z1 - z0,
                          matrix=Matrix.Translation((c.x, c.y, (z0 + z1) / 2)))
    for f in bm.faces: f.smooth = abs(f.normal.z) < 0.5; f.material_index = 0
    # cortecita: anillos con un poco de ruido en el radio
    for v in bm.verts:
        a = math.atan2(v.co.y - c.y, v.co.x - c.x)
        k = 1 + 0.03 * math.sin(a * 7 + v.co.z * 9)
        v.co.x = c.x + (v.co.x - c.x) * k; v.co.y = c.y + (v.co.y - c.y) * k
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    return sum(len(p.vertices) - 2 for p in me.polygons)

def rollo_guirnalda(pieza, escala_foco=0.6, paso=4, vueltas=3.2):
    """Rollo de luces: cable en hélice + copias de los focos de la guirnalda del árbol (tamaño real)."""
    g = bpy.data.objects["Guirnalda"]
    bmg = bm_evaluado(g, Matrix.Identity(4))
    nombres = [m.name for m in g.data.materials]
    i_cable = nombres.index("Arbol_Cable")
    # islas (cada foco es una isla)
    bmg.faces.ensure_lookup_table()
    vistos = set(); islas = []
    for f in bmg.faces:
        if f.index in vistos or f.material_index == i_cable: continue
        pila = [f]; isla = []; vistos.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vistos and y.material_index != i_cable: vistos.add(y.index); pila.append(y)
        islas.append(isla)
    # una plantilla por color: la isla más "mediana" en tamaño; se gira para mirar hacia +X
    plantillas = {}
    for isla in islas:
        mi = isla[0].material_index
        if mi in plantillas: continue
        vs = {v for f in isla for v in f.verts}
        c = sum((v.co for v in vs), Vector()) / len(vs)
        rot = Matrix.Rotation(-math.atan2(c.y, c.x), 3, "Z")
        locales = {v: rot @ (v.co - c) for v in vs}
        top = max(p.z for p in locales.values())
        plantillas[mi] = [(tuple(locales[v] - Vector((0, 0, top)) for v in f.verts)) for f in isla]
    bmg.free()
    bm = bmesh.new()
    # cable: hélice de 2.6 vueltas, radio 0.17, que sube un poquito (como un rollo amontonado)
    pts = []; n = 140
    for k in range(n + 1):
        t = k / n; a = t * vueltas * 2 * math.pi
        r = 0.16 + 0.03 * math.sin(a * 0.37)
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, 0.03 + t * 0.07 + 0.01 * math.sin(a * 2.3))))
    loft(bm, pts, [(0.007, 0.007)] * len(pts), mat=len(nombres) - 1 if False else 99, segs=8, sub=2, tapas=(True, True))
    colores = sorted(plantillas)
    for j, k in enumerate(range(0, n + 1, paso)):
        p = pts[k]; a = math.atan2(p.y, p.x)
        rot = Matrix.Rotation(a, 3, "Z")
        mi = colores[j % len(colores)]
        for cara in plantillas[mi]:
            vs = [bm.verts.new(p + rot @ (q * escala_foco) + Vector((0, 0, 0.003))) for q in cara]
            try:
                f = bm.faces.new(vs); f.material_index = mi; f.smooth = True
            except ValueError: pass
    mats = [bpy.data.materials[nm] for nm in nombres]
    for f in bm.faces:
        if f.material_index == 99: f.material_index = i_cable
    return bm, mats

def hacer_piezas():
    res = {}
    res["tronco"] = tronco_redondo()
    # Maceta
    maceta = bpy.data.objects["Maceta"]
    for nombre, partes in (
        ("Pieza_Maceta", [maceta, bpy.data.objects["Tierra"], bpy.data.objects["Tronco"]]),
        ("Pieza_Rama", [bpy.data.objects["Nivel3"]]),
        ("Pieza_Esfera", [bpy.data.objects["Esfera_1"], bpy.data.objects["Esfera_1_Tapa"]]),
        ("Pieza_Estrella", [bpy.data.objects["Estrella"]]),
    ):
        pz = bpy.data.objects[nombre]
        c, tam = caja_local(pz.data)
        raiz = partes[0]
        bm, mats = juntar(pz.data, [(o, relativo(o, raiz)) for o in partes])
        s = ajustar(bm, c, tam)
        res[nombre] = (escribir(pz, bm, mats), round(s, 3))
    pz = bpy.data.objects["Pieza_Guirnalda"]
    c, tam = caja_local(pz.data)
    bm, mats = rollo_guirnalda(pz)
    # centrar sin escalar (focos a tamaño real)
    mn = Vector((min(v.co[i] for v in bm.verts) for i in range(3))); mx = Vector((max(v.co[i] for v in bm.verts) for i in range(3)))
    d = c - (mn + mx) / 2
    for v in bm.verts: v.co += d
    res["Pieza_Guirnalda"] = (escribir(pz, bm, mats), 1.0)
    print(res)


# ---------------------------------------------------------------------------------------------------
# FALDAS SIN "HOJITAS EN MEDIO": cada capa del árbol (Nivel1-3) tiene 3 faldas de hojas, una dentro de otra.
# Las puntas de las faldas de adentro se salían por la de afuera. Arreglo: para cada vértice de una falda interior,
# se lanza un rayo horizontal desde el eje del árbol hacia el vértice; si choca con una falda MÁS externa antes de
# llegar al vértice, el vértice se jala hacia adentro (queda un poquito debajo). Así cada falda queda en su capa.
def islas_de(bm, filtro):
    bm.faces.ensure_lookup_table(); vist = set(); islas = []
    for f in bm.faces:
        if f.index in vist or not filtro(f): continue
        pila = [f]; isla = []; vist.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vist and filtro(y): vist.add(y.index); pila.append(y)
        islas.append(isla)
    return islas

def faldas_en_capas(me, margen=0.012):
    from mathutils.bvhtree import BVHTree
    verdes = {i for i, m in enumerate(me.materials) if m and m.name in ("Arbol_Verde", "Arbol_VerdeClaro")}
    bm = bmesh.new(); bm.from_mesh(me)
    islas = islas_de(bm, lambda f: f.material_index in verdes)
    islas = [i for i in islas if len(i) > 100]
    radio = lambda isla: max(math.hypot(v.co.x, v.co.y) for f in isla for v in f.verts)
    islas.sort(key=radio, reverse=True)                  # 0 = la de afuera
    escala = radio(islas[0])
    movidos = 0
    for k in range(1, len(islas)):
        exteriores = [f for isla in islas[:k] for f in isla]
        vs = [v.co.copy() for f in exteriores for v in f.verts]
        idx = {}; verts = []; polys = []
        for f in exteriores:
            p = []
            for v in f.verts:
                if v.index not in idx: idx[v.index] = len(verts); verts.append(v.co.copy())
                p.append(idx[v.index])
            polys.append(p)
        bvh = BVHTree.FromPolygons(verts, polys)
        for v in {v for f in islas[k] for v in f.verts}:
            r = math.hypot(v.co.x, v.co.y)
            if r < 1e-4: continue
            d = Vector((v.co.x / r, v.co.y / r, 0))
            hit = bvh.ray_cast(Vector((0, 0, v.co.z)), d, r)
            if hit[0] is not None:
                rh = hit[3]
                nuevo = max(rh - margen * escala, 0.0)
                if nuevo < r:
                    f = nuevo / r; v.co.x *= f; v.co.y *= f; movidos += 1
    bm.to_mesh(me); bm.free(); me.update()
    return movidos

def foco_liso(bm, p, mat, mat_socket, rx=0.021, rz=0.03):
    """Foco tipo gota, liso: cuello (socket) pegado al cable y bulbo ovalado colgando."""
    esfera(bm, p + Vector((0, 0, -0.012)), (0.009, 0.009, 0.012), mat=mat_socket, segs=10, anillos=6)
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=1.0)
    for v in res["verts"]:
        x, y, z = v.co
        k = 1 - 0.25 * max(0.0, z)                     # un poquito más angosto arriba (forma de gota)
        v.co = p + Vector((x * rx * k, y * rx * k, -0.012 - rz + z * rz))
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mat; f.smooth = True

def rollo_liso(pieza):
    nombres = ["Foco_Rojo", "Foco_Verde", "Foco_Azul", "Foco_Amarillo", "Arbol_Cable"]
    CAB = 4
    bm = bmesh.new(); pts = []; n = 140; vueltas = 3.2
    for k in range(n + 1):
        t = k / n; a = t * vueltas * 2 * math.pi
        r = 0.16 + 0.03 * math.sin(a * 0.37)
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, 0.05 + t * 0.07 + 0.01 * math.sin(a * 2.3))))
    loft(bm, pts, [(0.007, 0.007)] * len(pts), mat=CAB, segs=8, sub=2, tapas=(True, True))
    for j, k in enumerate(range(2, n + 1, 4)):
        foco_liso(bm, pts[k], j % 4, CAB)
    for f in bm.faces:
        if f.material_index == CAB: f.smooth = True
    return bm, [bpy.data.materials[x] for x in nombres]
