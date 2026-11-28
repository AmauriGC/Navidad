# -*- coding: utf-8 -*-
"""
CARITA DEL ELFO PEGADA (27-nov, detallitos). Pedido: "me gusta su carita así, lo que no me gusta es que esté separado".
Misma cara (ojos negros ovalados con brillito, nariz rosa, cachetes rosas, sonrisa café, cejas), mismos objetos y
materiales (OjoL/R, BrilloL/R, MejillaL/R, Nariz, Boca y la Acc_Nieves_Pestanas), pero cada pieza se construye
SOBRE la superficie de la cabeza: centrada en la piel, orientada con su normal y medio hundida, así se ve
"pintada/incrustada" y no flotando enfrente. Sirve para los 4 elfos (comparten cabeza; los accesorios van aparte).
Usa cab_pt() de elfos_variantes.py (misma fórmula que elfo_v2.cabeza).
Uso: exec(modelado.py); exec(elfos_variantes.py); exec(elfo_cara_v3.py); hacer_cara_elfo()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

RAIZ_ELFO = bpy.data.objects["Elfo"]

def _mundo(o):
    """Matriz de mundo armada con la cadena de padres (matrix_world puede venir vieja si la ventana muestra la Vitrina)."""
    if o.parent is None: return o.matrix_basis.copy()
    return _mundo(o.parent) @ o.matrix_parent_inverse @ o.matrix_basis

def a_s(x, z):
    """(x, z) de la cara -> (a, s) de cab_pt (inverso aproximado de la fórmula de la cabeza)."""
    s = (z - 1.04) / (0.175 if z > 1.04 else 0.18)
    s = max(-0.98, min(0.98, s))
    c = math.sqrt(1 - s * s)
    ancho = 1.0 + 0.05 * math.exp(-((s + 0.25) / 0.3) ** 2) - (0.22 * s * s if s < 0 else 0.0)
    return math.asin(max(-1.0, min(1.0, x / (c * 0.195 * ancho)))), s

_BVH = None
def _bvh_cabeza():
    """BVH de la malla REAL de la Cabeza en coords del elfo: la cabeza low-poly tiene caras planas que quedan unos
    milímetros DENTRO de la fórmula curva; con la fórmula sola los cachetes se veían salidos."""
    global _BVH
    if _BVH is None:
        from mathutils.bvhtree import BVHTree
        cab = bpy.data.objects["Cabeza"]
        M = _mundo(RAIZ_ELFO).inverted() @ _mundo(cab)
        me = cab.data
        _BVH = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])
    return _BVH

def piel(x, z, extra=0.0):
    """Punto sobre la piel REAL de la cabeza (rayo hacia el centro), empujado 'extra' metros hacia afuera."""
    a, s = a_s(x, z)
    p = cab_pt(a, s, 0.0); n = (cab_pt(a, s, 0.01) - p).normalized()
    hit = _bvh_cabeza().ray_cast(p + n * 0.05, -n, 0.2)[0]
    return (hit if hit is not None else p) + n * extra

def marco(x, z):
    """Ejes sobre la piel en (x, z): lado (horizontal), normal (hacia afuera), arriba (sobre la piel)."""
    p0 = piel(x, z); n = (piel(x, z, 0.01) - p0).normalized()
    lado = Vector((0, 0, 1)).cross(n).normalized() * -1      # +X en la cara
    arriba = n.cross(lado).normalized() * -1
    if arriba.z < 0: arriba = -arriba
    return p0, lado, n, arriba

def pegado(bm, x, z, rx, rz, alto, hundido=0.0, segs=14, anillos=6, giro=0.0):
    """Elipsoide pegado a la piel: rx/rz sobre la cara, 'alto' = cuánto sobresale; 'hundido' lo mete más.
    El centro queda dentro de la cabeza => solo se ve un domo bajito que nace de la piel (sin hueco detrás)."""
    p0, lado, n, arriba = marco(x, z)
    if giro:
        R = Matrix.Rotation(giro, 3, n); lado = R @ lado; arriba = R @ arriba
    centro = p0 - n * (alto * 0.35 + hundido)
    res = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=anillos, radius=1.0)
    for v in res["verts"]:
        c = v.co.copy()
        v.co = centro + lado * (c.x * rx) + n * (c.y * alto * 1.35) + arriba * (c.z * rz)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.smooth = False

def tira(bm, pts_xz, radio, alto, extra=0.0, segs=8):
    """Tubo que sigue la piel (sonrisa, cejas): medio hundido."""
    pts = [piel(x, z, extra - radio * 0.35) for (x, z) in pts_xz]
    loft(bm, pts, [(radio, alto)] * len(pts), segs=segs, sub=3, domo=0.9)

# ------------------------------------------------------------------ piezas (mismos lugares y tamaños de elfo_v2)
OJO = dict(x=0.068, z=1.065, rx=0.026, rz=0.036)

def ojo(s):
    def b(bm): pegado(bm, s * OJO["x"], OJO["z"], OJO["rx"], OJO["rz"], alto=0.007)
    return b

def brillo(s):
    def b(bm): pegado(bm, s * 0.075, 1.081, 0.008, 0.009, alto=0.003, hundido=-0.0062, segs=8, anillos=4)
    return b

def mejilla(s):
    def b(bm): pegado(bm, s * 0.112, 0.995, 0.034, 0.022, alto=0.0025, segs=12, anillos=4)
    return b

def nariz(bm):
    pegado(bm, 0.0, 1.0, 0.03, 0.028, alto=0.026, hundido=0.004, segs=14, anillos=8)

def boca(bm):
    arco = [(0.045 * math.sin(a), 0.948 + 0.018 * (1 - math.cos(a))) for a in (-1.1, -0.55, 0, 0.55, 1.1)]
    tira(bm, arco, 0.007, 0.006)
    for s in (-1, 1):
        tira(bm, [(s * 0.04, 1.118), (s * 0.07, 1.128), (s * 0.1, 1.122)], 0.008, 0.006)

def pestanas_pegadas(bm):
    """Pestañas de Nieves: nacen de la orilla de arriba-afuera del ojo pegado (antes flotaban 5 mm enfrente)."""
    for lado in (1, -1):
        for k in range(3):
            ang = math.radians(35 + 22 * k)                      # alrededor de la orilla del ojo
            x = lado * (OJO["x"] + OJO["rx"] * 0.95 * math.cos(ang)); z = OJO["z"] + OJO["rz"] * 0.95 * math.sin(ang)
            p0, ladoV, n, arriba = marco(x, z)
            base = p0 + n * 0.004
            fuera = (ladoV * lado * math.cos(ang) + arriba * math.sin(ang)).normalized()
            loft(bm, [base, base + fuera * 0.013 + n * 0.006], [(0.0035, 0.0035), (0.0015, 0.0015)], segs=6, sub=1, domo=0.5)

PIEZAS = {"Nariz": nariz, "Boca": boca, "OjoL": ojo(1), "OjoR": ojo(-1), "BrilloL": brillo(1), "BrilloR": brillo(-1),
          "MejillaL": mejilla(1), "MejillaR": mejilla(-1), "Acc_Nieves_Pestanas": pestanas_pegadas}

def _poner_elfo(nombre, construir):
    obj = bpy.data.objects[nombre]
    M = _mundo(obj).inverted() @ _mundo(RAIZ_ELFO)
    def envuelto(bm):
        construir(bm)
        bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    viejo = obj.data
    poner_malla(obj, envuelto, materiales=[s.material for s in obj.material_slots], subsurf=0)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.name = nombre + "_v3"
    # las copias de la Vitrina comparten malla: que apunten a la nueva
    for o in bpy.data.objects:
        if o is not obj and o.data is viejo: o.data = obj.data

def hacer_cara_elfo():
    global _BVH; _BVH = None
    for n, f in PIEZAS.items():
        _poner_elfo(n, f)
        print(n, "tris", sum(len(p.vertices) - 2 for p in bpy.data.objects[n].data.polygons))
