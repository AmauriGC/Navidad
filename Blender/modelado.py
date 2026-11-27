# -*- coding: utf-8 -*-
"""
LIBRERÍA DE MODELADO por código (bmesh) que usan renos.py, trineo_santa.py, elfo_v2.py, maquina_v2.py, etc.
  loft(...)   : tubo de anillos elípticos a lo largo de un camino suave (cuerpos, patas, cuernos, ramas).
  esfera(...) : elipsoide.     toro(...) : dona (collares, orillas).     caja(...) : caja con bordes redondeados.
  poner_malla(obj, construir) : reemplaza la malla de un objeto existente conservando nombre, origen y materiales.
  material(...) : crea/actualiza un material Principled.     exportar_glb(objs, archivo) : .glb a Assets/Modelos.
Uso en Blender:  exec(open(".../Blender/modelado.py").read())
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

PROYECTO = "/home/cris/Escritorio/10A/ulises/Navidad"

# ------------------------------------------------------------------ camino suave (Catmull-Rom)
def suavizar_camino(puntos, radios, sub=4):
    """Interpola puntos y radios con Catmull-Rom para que el tubo no tenga 'codos'."""
    P = [Vector(p) for p in puntos]
    salida_p, salida_r = [], []
    n = len(P)
    for i in range(n - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n - 1)]
        r1, r2 = radios[i], radios[i + 1]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            p = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            salida_p.append(p)
            salida_r.append((r1[0] + (r2[0] - r1[0]) * t, r1[1] + (r2[1] - r1[1]) * t))
    salida_p.append(P[-1]); salida_r.append(radios[-1])
    return salida_p, salida_r


def loft(bm, puntos, radios, mat=0, segs=18, sub=4, tapas=(True, True), domo=0.6, arriba=Vector((0, 0, 1)), abierto=None):
    """
    Tubo de anillos elípticos a lo largo de 'puntos'. radios = [(ancho, alto), ...] por punto.
    El marco de cada anillo se calcula con 'transporte paralelo' (el anillo no se tuerce).
    tapas: cerrar inicio/fin con un domo redondo. abierto=(a0,a1) en grados -> solo un arco (mantita).
    """
    P, R = suavizar_camino(puntos, radios, sub)
    n = len(P)
    tang = []
    for i in range(n):
        t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]); t.normalize(); tang.append(t)
    ref = arriba if abs(tang[0].dot(arriba)) < 0.9 else Vector((0, 1, 0))
    lado = tang[0].cross(ref).normalized()
    anillos = []
    if abierto:
        angs = [math.radians(abierto[0] + (abierto[1] - abierto[0]) * j / segs) for j in range(segs + 1)]
    else:
        angs = [2 * math.pi * j / segs for j in range(segs)]
    for i in range(n):
        if i > 0:   # transporte paralelo: quitar al 'lado' la componente sobre la tangente nueva
            lado = (lado - tang[i] * lado.dot(tang[i])).normalized()
        up = lado.cross(tang[i]).normalized()
        rx, rz = R[i]
        anillo = [bm.verts.new(P[i] + lado * (math.cos(a) * rx) + up * (math.sin(a) * rz)) for a in angs]
        anillos.append(anillo)
    m = len(angs)
    for i in range(n - 1):
        a, b = anillos[i], anillos[i + 1]
        rango = range(m - 1) if abierto else range(m)
        for j in rango:
            f = bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
            f.material_index = mat; f.smooth = True
    if not abierto:
        for idx, (cual, signo) in enumerate(((0, -1), (n - 1, 1))):
            if not tapas[idx]: continue
            r = max(R[cual])
            c = bm.verts.new(P[cual] + tang[cual] * signo * r * domo)
            an = anillos[cual]
            for j in range(m):
                vs = (an[j], an[(j + 1) % m], c) if signo > 0 else (an[(j + 1) % m], an[j], c)
                f = bm.faces.new(vs); f.material_index = mat; f.smooth = True
    return anillos


def esfera(bm, centro, radios, mat=0, segs=16, anillos=10):
    """Elipsoide (esfera escalada) con caras suaves."""
    res = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=anillos, radius=1.0)
    for v in res["verts"]:
        v.co = Vector((v.co.x * radios[0], v.co.y * radios[1], v.co.z * radios[2])) + Vector(centro)
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat; f.smooth = True


def toro(bm, centro, R, r, mat=0, segs=24, lados=8, inclinacion=0.0):
    """Dona (collar). inclinacion = giro en X (radianes) para que abrace el cuello."""
    import mathutils
    rot = mathutils.Matrix.Rotation(inclinacion, 3, "X")
    vs = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        fila = []
        for j in range(lados):
            b = 2 * math.pi * j / lados
            p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            fila.append(bm.verts.new(rot @ p + Vector(centro)))
        vs.append(fila)
    for i in range(segs):
        for j in range(lados):
            f = bm.faces.new((vs[i][j], vs[(i + 1) % segs][j], vs[(i + 1) % segs][(j + 1) % lados], vs[i][(j + 1) % lados]))
            f.material_index = mat; f.smooth = True


def caja(bm, centro, tam, mat=0, bisel=0.03, segs=2, giro=None):
    """Caja de tamaño tam=(x,y,z) con bordes redondeados (bisel). Se arma en un bmesh aparte y se une,
    así el bisel no afecta lo demás. giro = Matrix 3x3 opcional."""
    tmp = bmesh.new()
    res = bmesh.ops.create_cube(tmp, size=1.0)
    for v in tmp.verts:
        v.co = Vector((v.co.x * tam[0], v.co.y * tam[1], v.co.z * tam[2]))
    if bisel > 0:
        bmesh.ops.bevel(tmp, geom=list(tmp.edges) + list(tmp.verts), offset=bisel, segments=segs, affect="EDGES", profile=0.5)
    for v in tmp.verts:
        p = v.co.copy()
        if giro is not None: p = giro @ p
        v.co = p + Vector(centro)
    for f in tmp.faces:
        f.material_index = mat; f.smooth = bisel > 0
    unir(bm, tmp)


def unir(bm, otro):
    """Copia la geometría del bmesh 'otro' dentro de 'bm' (y libera 'otro')."""
    me = bpy.data.meshes.new("_tmp")
    otro.to_mesh(me); otro.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def material(nombre, color, metal=0.0, rugosidad=0.6, emision=None, fuerza=1.0):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rugosidad
    if emision:
        bsdf.inputs["Emission Color"].default_value = (*emision, 1)
        bsdf.inputs["Emission Strength"].default_value = fuerza
    return m


def poner_malla(obj, construir, materiales=None, subsurf=1):
    """Malla nueva con construir(bm). Conserva nombre, origen y (si no se dan otros) los materiales del objeto."""
    mats = materiales if materiales is not None else [s.material for s in obj.material_slots]
    bm = bmesh.new()
    construir(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(obj.name + "_v2")
    bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    viejo = obj.data
    obj.data = me
    if viejo.users == 0: bpy.data.meshes.remove(viejo)
    for mod in list(obj.modifiers): obj.modifiers.remove(mod)
    if subsurf:
        s = obj.modifiers.new("Redondeo", "SUBSURF"); s.levels = subsurf; s.render_levels = subsurf


def con_hijos(o):
    l = [o]
    for h in o.children: l += con_hijos(h)
    return l


def exportar_glb(objs, archivo, raiz=None):
    """Exporta objs a Assets/Modelos/archivo. Si se da 'raiz', la pone en el origen mientras exporta."""
    guard = None
    if raiz is not None: guard = raiz.location.copy(); raiz.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False); o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f"{PROYECTO}/Assets/Modelos/{archivo}", use_selection=True, export_apply=True, export_yup=True)
    if raiz is not None: raiz.location = guard
