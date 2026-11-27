# -*- coding: utf-8 -*-
"""
CORONAS DE LAS CASAS (una por casa, en la puerta).
Antes había DOS: una de 12 bolitas dentro de la malla de cada casa (en la puerta) y otra extra en el objeto
Coronas_Casas que quedó a la mitad dentro de la pared (se veía como una "C"), encima de la otra o flotando.
Ahora:
  1. quitar_coronas_puerta(): borra de las mallas de las casas las 12 bolitas verdes (islas de 140 caras con
     Amb_VerdePino) y las moras rojas pegadas a ellas, y devuelve dónde estaba la corona (centro, pared, hacia afuera).
  2. hacer_coronas(): rehace TODA la malla Coronas_Casas (coordenadas de mundo) con una corona bonita por casa,
     con la parte de atrás pegada a la puerta (nunca atraviesa la pared):
       - aro base de follaje oscuro
       - ~70 hojitas (elipsoides aplanados) encimadas en 2 tonos, cada una girada un poco al azar
       - racimos de 3 moras rojas, 3 piñitas
       - moño rojo abajo (2 lazos + nudo + 2 colas)
     La casa en A (sin puerta al frente) lleva su corona colgada arriba del ventanal, por delante de los marcos.
Uso: exec(modelado.py); exec(coronas.py); hacer_coronas()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

def islas(bm, filtro):
    bm.faces.ensure_lookup_table(); vist = set(); res = []
    for f in bm.faces:
        if f.index in vist or not filtro(f): continue
        pila = [f]; isla = []; vist.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vist and filtro(y): vist.add(y.index); pila.append(y)
        res.append(isla)
    return res

def quitar_coronas_puerta(nombre_malla):
    """Quita la corona de bolitas de la malla. Devuelve (centro, normal, radio) en coordenadas locales, o None."""
    me = bpy.data.meshes[nombre_malla]
    nm = [m.name if m else "" for m in me.materials]
    if "Amb_VerdePino" not in nm: return None
    iv = nm.index("Amb_VerdePino"); ir = nm.index("Amb_Rojo") if "Amb_Rojo" in nm else -1
    bm = bmesh.new(); bm.from_mesh(me)
    bolitas = [i for i in islas(bm, lambda f: f.material_index == iv) if len(i) == 140]
    if not bolitas: bm.free(); return None
    vs = list({v for isla in bolitas for f in isla for v in f.verts})
    c = sum((v.co for v in vs), Vector()) / len(vs)
    ext = [max(v.co[k] for v in vs) - min(v.co[k] for v in vs) for k in range(3)]
    eje = 0 if ext[0] < ext[1] else 1                         # eje delgado = perpendicular a la pared
    n = Vector((0, 0, 0)); n[eje] = 1.0 if c[eje] > 0 else -1.0
    atras = min(v.co.dot(n) for v in vs)                       # plano de la puerta
    radio = max(ext[1 - eje], ext[2]) / 2
    borrar = {f for isla in bolitas for f in isla}
    if ir >= 0:
        for isla in islas(bm, lambda f: f.material_index == ir):
            ci = sum((v.co for f in isla for v in f.verts), Vector()) / sum(len(f.verts) for f in isla)
            if (ci - c).length < radio + 0.15: borrar.update(isla)
    bmesh.ops.delete(bm, geom=list(borrar), context="FACES")
    bm.to_mesh(me); bm.free(); me.update()
    centro = c - n * (c.dot(n) - atras)                        # centro sobre la superficie de la puerta
    return centro, n, radio, len(bolitas)

def elipsoide(bm, centro, ejes, radios, mat, segs=6, anillos=4):
    res = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=anillos, radius=1.0)
    M = Matrix((ejes[0] * radios[0], ejes[1] * radios[1], ejes[2] * radios[2])).transposed()
    for v in res["verts"]: v.co = centro + M @ v.co
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mat; f.smooth = True

def corona(bm, p, n, R, rnd, M):
    """p = punto en la superficie (centro de la corona), n = hacia afuera. M = índices de materiales."""
    up = Vector((0, 0, 1)); u = up.cross(n).normalized(); v = n.cross(u).normalized()
    base = p + n * 0.045
    # aro base
    segs = 28
    anillo = [base + (u * math.cos(2 * math.pi * k / segs) + v * math.sin(2 * math.pi * k / segs)) * R for k in range(segs)]
    loft(bm, anillo + anillo[:3], [(0.05, 0.035)] * (segs + 3), mat=M["oscuro"], segs=8, sub=1, tapas=(False, False), arriba=n)
    # hojitas
    for k in range(76):
        a = 2 * math.pi * k / 76 + rnd.uniform(-0.05, 0.05)
        rad = R + rnd.uniform(-0.06, 0.06)
        radial = u * math.cos(a) + v * math.sin(a)
        tang = -u * math.sin(a) + v * math.cos(a)
        q = base + radial * rad + n * rnd.uniform(0.0, 0.035)
        giro = Matrix.Rotation(rnd.uniform(-0.8, 0.8), 3, n) @ Matrix.Rotation(rnd.uniform(-0.4, 0.4), 3, tang)
        e1 = giro @ tang; e3 = (giro @ n).normalized(); e2 = e3.cross(e1).normalized()
        elipsoide(bm, q, (e1, e2, e3), (0.055, 0.024, 0.011), M["hoja"] if k % 3 else M["oscuro"])
    # moras (racimos de 3)
    for k in range(7):
        a = 2 * math.pi * (k + 0.5) / 7 + 0.3
        radial = u * math.cos(a) + v * math.sin(a)
        if radial.dot(v) < -0.75: continue                     # abajo va el moño
        q = base + radial * (R + rnd.uniform(-0.03, 0.03)) + n * 0.05
        for j in range(3):
            d = (u * math.cos(j * 2.1 + k) + v * math.sin(j * 2.1 + k)) * 0.018
            esfera(bm, q + d, (0.017, 0.017, 0.017), mat=M["rojo"], segs=8, anillos=6)
    # piñitas
    for a in (0.9, 2.3, 4.0):
        radial = u * math.cos(a) + v * math.sin(a)
        q = base + radial * R + n * 0.045
        tang = -u * math.sin(a) + v * math.cos(a)
        elipsoide(bm, q, (tang, n.cross(tang), n), (0.04, 0.026, 0.024), M["pina"], segs=8, anillos=6)
    # moño abajo
    m0 = base - v * R + n * 0.06
    for s in (-1, 1):
        lazo = [m0, m0 + u * s * 0.07 + v * 0.05 + n * 0.01, m0 + u * s * 0.12 + v * 0.01, m0 + u * s * 0.07 - v * 0.035, m0]
        loft(bm, lazo, [(0.028, 0.008)] * len(lazo), mat=M["mono"], segs=8, sub=3, tapas=(False, False), arriba=n)
        cola = [m0, m0 + u * s * 0.04 - v * 0.08, m0 + u * s * 0.06 - v * 0.17]
        loft(bm, cola, [(0.022, 0.006), (0.024, 0.006), (0.026, 0.006)], mat=M["mono"], segs=6, sub=3, tapas=(False, True), arriba=n)
    esfera(bm, m0 + n * 0.008, (0.03, 0.022, 0.026), mat=M["mono"], segs=10, anillos=8)

def hacer_coronas(semilla=5):
    rnd = random.Random(semilla)
    # 1) quitar las coronas de bolitas de las mallas de casas (una vez; si ya no están, None)
    datos = {}
    for mn in ("CasaRoja", "CasaAzul", "CasaVerde", "CasaTroncos"):
        r = quitar_coronas_puerta(mn)
        if r: bpy.data.meshes[mn]["corona_puerta"] = [*r[0], *r[1], r[2]]
        g = bpy.data.meshes[mn].get("corona_puerta")
        if g: datos[mn] = (Vector(g[0:3]), Vector(g[3:6]), g[6])
        print(mn, "bolitas quitadas" if r else "ya estaba limpia", datos.get(mn))
    datos["CasaA"] = (Vector((3.2, 0.0, 3.55)), Vector((1, 0, 0)), 0.32)
    # 2) materiales de Coronas_Casas
    obj = bpy.data.objects["Coronas_Casas"]; me = obj.data
    mats = ["Amb_VerdePino", "Corona_Verde", "Amb_Rojo", "Amb_MaderaOscura", "Arbol_Mono"]
    me.materials.clear()
    for m in mats: me.materials.append(bpy.data.materials[m])
    M = {"oscuro": 0, "hoja": 1, "rojo": 2, "pina": 3, "mono": 4}
    obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, 0); obj.scale = (1, 1, 1)
    bm = bmesh.new(); n_coronas = 0
    for casa in bpy.data.objects:
        if not casa.name.startswith("Casa_"): continue
        d = datos.get(casa.data.name)
        if not d: print("sin datos", casa.name); continue
        c, n, R = d
        mw = casa.matrix_world
        p = mw @ c; nw = (mw.to_3x3() @ n).normalized()
        corona(bm, p, nw, 0.26, rnd, M); n_coronas += 1
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print("coronas:", n_coronas, "tris:", sum(len(p.vertices) - 2 for p in me.polygons))
