# -*- coding: utf-8 -*-
"""
ACCESORIOS DE LOS 3 ELFOS (selector de elfo, 25-nov). El cuerpo es el MISMO para los 3 (mismas piezas y pivotes,
así ElfoAnimador los anima igual); cada elfo agrega piezas "Acc_<Nombre>_..." hijas de la pieza con la que se mueven
(Cabeza, Gorro o Cuerpo). En Unity, VarianteElfo prende solo las del elfo elegido y cambia los colores de la ropa.
  - Tilo   : el clásico (sin accesorios).
  - Nieves : flequillo + melena de canela, 2 trenzas con moño rosa, pestañas y pompón esponjado (en vez de cascabel).
  - Chispa : lentes redondos dorados, copete naranja con rizo, pecas y bufanda a rayas con flecos.
Las posiciones sobre la cara salen de la MISMA fórmula con la que se construye la cabeza (elfo_v2.cabeza) => el pelo
queda pegado a la cabeza sin flotar ni hundirse.
Uso: exec(modelado.py); exec(elfo_v2.py SIN el ciclo final); exec(elfos_variantes.py); hacer_accesorios()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

MATS_ACC = {
    "Acc_Pelo": ((0.42, 0.16, 0.05), 0.0, 0.7),        # canela (Nieves)
    "Acc_Rosa": ((0.9, 0.22, 0.38), 0.0, 0.5),         # moños
    "Acc_Blanco": ((0.95, 0.95, 0.97), 0.0, 0.95),     # pompón
    "Acc_Oro": ((1.0, 0.72, 0.22), 0.8, 0.3),          # lentes
    "Acc_PeloNaranja": ((0.8, 0.27, 0.04), 0.0, 0.7),  # copete de Chispa
    "Acc_Pecas": ((0.3, 0.12, 0.05), 0.0, 0.8),
    "Acc_Bufanda1": ((0.04, 0.42, 0.42), 0.0, 0.9),    # verde azulado
    "Acc_Bufanda2": ((0.95, 0.88, 0.72), 0.0, 0.9),    # crema
}

def mats(*nombres):
    res = []
    for n in nombres:
        if n in MATS_ACC:
            c, metal, rug = MATS_ACC[n]; res.append(material(n, c, metal=metal, rugosidad=rug))
        else: res.append(bpy.data.materials[n])
    return res

CENTRO = Vector((0, 0, 1.04))

def cab_pt(a, s, extra=0.0):
    """Punto sobre la cabeza del elfo: a = ángulo alrededor (0 = frente/-Y, +pi/2 = +X), s = altura (-1 abajo .. 1 arriba),
    extra = metros hacia afuera de la superficie. Misma fórmula que elfo_v2.cabeza."""
    c = math.sqrt(max(0.0, 1 - s * s))
    ancho = 1.0 + 0.05 * math.exp(-((s + 0.25) / 0.3) ** 2) - (0.22 * s * s if s < 0 else 0.0)
    x = math.sin(a) * c * 0.195 * ancho
    y = -math.cos(a) * c * 0.18 * (ancho if math.cos(a) > 0 else 1.0)
    z = 1.04 + s * (0.175 if s > 0 else 0.18)
    d = Vector((x, y, z)) - CENTRO
    return CENTRO + d * (1 + extra / max(d.length, 1e-6)) + Vector((0, 0.003, 0))

# ------------------------------------------------------------------ NIEVES
def casco_pelo(bm, A0, bajo, grosor=0.016, na=28, ns=10):
    """Pelo de atrás y de los lados: cascarón CERRADO (capa de afuera + capa de adentro + orillas) que sigue la cabeza.
    A0 = dónde empieza a los lados de la cara; bajo(a, i) = hasta dónde baja."""
    afuera, adentro = [], []
    for i in range(na + 1):
        a = A0 + (2 * math.pi - 2 * A0) * i / na
        s_bajo = bajo(a, i)
        fa, fi = [], []
        for j in range(ns + 1):
            s = s_bajo + (0.56 - s_bajo) * j / ns
            ola = 0.004 * math.sin(i * 2.3 + j * 0.7)
            fa.append(bm.verts.new(cab_pt(a, s, grosor + ola)))
            fi.append(bm.verts.new(cab_pt(a, s, -0.004)))
        afuera.append(fa); adentro.append(fi)
    for i in range(na):
        for j in range(ns):
            bm.faces.new((afuera[i][j], afuera[i + 1][j], afuera[i + 1][j + 1], afuera[i][j + 1]))
            bm.faces.new((adentro[i][j], adentro[i][j + 1], adentro[i + 1][j + 1], adentro[i + 1][j]))
    for i in range(na):   # orillas de arriba y abajo
        bm.faces.new((afuera[i][0], adentro[i][0], adentro[i + 1][0], afuera[i + 1][0]))
        bm.faces.new((afuera[i][ns], afuera[i + 1][ns], adentro[i + 1][ns], adentro[i][ns]))
    for j in range(ns):   # orillas de los lados
        bm.faces.new((afuera[0][j], afuera[0][j + 1], adentro[0][j + 1], adentro[0][j]))
        bm.faces.new((afuera[na][j], adentro[na][j], adentro[na][j + 1], afuera[na][j + 1]))

def melena(bm):
    rnd = random.Random(3)
    casco_pelo(bm, 0.36 * math.pi, lambda a, i: -0.27 - 0.25 * (1 - math.cos(a)) / 2 + 0.03 * math.sin(i * 1.7))
    # flequillo: mechoncitos redondos bajo el borde del gorro
    for k in range(7):
        a = -0.85 + 1.7 * k / 6
        p = cab_pt(a, 0.4 - 0.03 * (1 - abs(a)), 0.012)
        esfera(bm, tuple(p), (0.036, 0.022, 0.034 + 0.006 * rnd.random()), segs=12, anillos=8)
    # trenzas
    for lado in (1, -1):
        ini = cab_pt(lado * 0.7 * math.pi, -0.3, 0.02)
        fin = Vector((lado * 0.178, 0.115, 0.745))
        n = 7
        for k in range(n):
            t = k / (n - 1)
            p = ini.lerp(fin, t) + Vector((lado * 0.009 * (1 if k % 2 else -1), 0, 0))
            r = 0.034 - 0.01 * t
            esfera(bm, tuple(p), (r, r * 0.92, r * 1.2), segs=12, anillos=8)
        loft(bm, [fin + Vector((0, 0, -0.02)), fin + Vector((0, 0.008, -0.06)), fin + Vector((0, 0.012, -0.085))],
             [(0.022, 0.022), (0.016, 0.016), (0.004, 0.004)], segs=10, sub=2, domo=0.5)   # puntita de la trenza

def monos(bm):
    for lado in (1, -1):
        e = Vector((lado * 0.178, 0.115, 0.735))
        for sy in (1, -1):
            esfera(bm, tuple(e + Vector((lado * 0.006, sy * 0.032, 0.004))), (0.013, 0.03, 0.022), segs=12, anillos=8)
            loft(bm, [e + Vector((lado * 0.004, sy * 0.01, -0.01)), e + Vector((lado * 0.004, sy * 0.022, -0.045))],
                 [(0.009, 0.004), (0.007, 0.003)], segs=8, sub=1, domo=0.3)                         # colitas del moño
        esfera(bm, tuple(e + Vector((lado * 0.01, 0, 0))), (0.016, 0.016, 0.016), segs=10, anillos=6)  # nudo

def pestanas(bm):
    for lado in (1, -1):
        for k in range(3):
            base = Vector((lado * (0.078 + 0.008 * k), -0.183 + 0.004 * k, 1.093 - 0.006 * k))
            loft(bm, [base, base + Vector((lado * (0.012 + 0.003 * k), -0.006, 0.012 - 0.003 * k))],
                 [(0.0035, 0.0035), (0.0015, 0.0015)], segs=6, sub=1, domo=0.5)

def pompon(c):
    def b(bm):
        rnd = random.Random(7)
        esfera(bm, tuple(c), (0.052, 0.052, 0.05), segs=16, anillos=10)
        for k in range(14):
            u = rnd.uniform(-1, 1); fi = rnd.uniform(0, 2 * math.pi); r = math.sqrt(1 - u * u)
            d = Vector((r * math.cos(fi), r * math.sin(fi), u))
            esfera(bm, tuple(c + d * 0.04), (0.026, 0.026, 0.026), segs=10, anillos=6)
    return b

# ------------------------------------------------------------------ CHISPA
def lentes(bm):
    for lado in (1, -1):
        c = Vector((lado * 0.07, -0.197, 1.068))
        toro(bm, tuple(c), 0.043, 0.0065, segs=24, lados=8, inclinacion=math.pi / 2)
        # patita: del aro hacia atrás, por encima de la oreja
        loft(bm, [c + Vector((lado * 0.043, 0.004, 0.004)), Vector((lado * 0.168, -0.12, 1.078)), Vector((lado * 0.196, -0.03, 1.08)),
                  Vector((lado * 0.19, 0.02, 1.07))], [(0.0055, 0.0055)] * 4, segs=8, sub=3, domo=0.5)
    loft(bm, [Vector((-0.027, -0.2, 1.074)), Vector((0, -0.207, 1.083)), Vector((0.027, -0.2, 1.074))], [(0.0055, 0.0055)] * 3,
         segs=8, sub=3, domo=0.5)   # puente

def copete(bm):
    """Pelo corto alborotado: casco corto con picos redondeados abajo + mechones al frente + rizo sobre la ceja."""
    rnd = random.Random(11)
    casco_pelo(bm, 0.42 * math.pi, lambda a, i: 0.06 - 0.48 * (1 - math.cos(a)) / 2 + (0.06 if i % 2 else -0.04), grosor=0.02, na=26, ns=9)
    for k in range(7):   # mechones redondos bajo el gorro, al frente
        a = -0.8 + 1.6 * k / 6
        esfera(bm, tuple(cab_pt(a, 0.37 + 0.02 * (k % 2), 0.016)), (0.04, 0.026, 0.04 + 0.01 * rnd.random()), segs=12, anillos=8)
    # rizo grande que se escapa sobre la ceja izquierda
    pts = [Vector((-0.01, -0.19, 1.118)), Vector((-0.045, -0.222, 1.116)), Vector((-0.08, -0.232, 1.098)),
           Vector((-0.094, -0.22, 1.076)), Vector((-0.078, -0.208, 1.066)), Vector((-0.063, -0.214, 1.08))]
    loft(bm, pts, [(0.026, 0.026), (0.023, 0.023), (0.018, 0.018), (0.014, 0.014), (0.011, 0.011), (0.007, 0.007)], segs=12, sub=4, domo=0.6)

def pecas(bm):
    rnd = random.Random(5)
    for lado in (1, -1):
        for k in range(5):
            a = lado * rnd.uniform(0.3, 0.58); s = rnd.uniform(-0.12, -0.03)
            esfera(bm, tuple(cab_pt(a, s, 0.001)), (0.0065, 0.0045, 0.0065), segs=8, anillos=5)

def bufanda(bm):
    """Rosca gruesa alrededor del cuello (una sola pieza, rayas pintadas por cara) + punta colgando con flecos.
    mat 0/1 = las dos rayas."""
    z = 0.838; n = 32
    pts = [Vector((math.sin(a) * 0.14, -math.cos(a) * 0.13, z + 0.008 * math.sin(3 * a))) for a in [2 * math.pi * k / n for k in range(n + 1)]]
    antes = set(bm.faces)
    loft(bm, pts, [(0.047, 0.04)] * len(pts), mat=0, segs=14, sub=1, tapas=(False, False), domo=0.0)
    for f in set(bm.faces) - antes:   # raya según el ángulo alrededor del cuello
        c = f.calc_center_median(); a = math.atan2(c.x, -c.y)
        f.material_index = int(((a + math.pi) / (2 * math.pi)) * 10) % 2
    bmesh.ops.remove_doubles(bm, verts=list({v for f in set(bm.faces) - antes for v in f.verts}), dist=0.0005)
    # punta colgando (frente-derecha), 3 rayas + flecos
    camino = [Vector((0.08, -0.13, 0.83)), Vector((0.1, -0.165, 0.76)), Vector((0.11, -0.18, 0.68)), Vector((0.115, -0.182, 0.6))]
    for k in range(3):
        seg = [camino[k], camino[k + 1] + (camino[k + 1] - camino[k]) * 0.05]
        loft(bm, seg, [(0.045, 0.013), (0.043, 0.013)], mat=k % 2, segs=12, sub=1, domo=0.0, arriba=Vector((0, -1, 0)))
    for k in range(5):
        x = 0.115 + (k - 2) * 0.017
        loft(bm, [Vector((x, -0.182, 0.603)), Vector((x + 0.002, -0.184, 0.56))], [(0.0055, 0.0055), (0.003, 0.003)], mat=1, segs=6, sub=1, domo=0.5)

# ------------------------------------------------------------------ crear piezas
def acc(nombre, padre, construir, materiales):
    o = bpy.data.objects.get(nombre)
    if o is None:
        o = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre + "_tmp"))
        bpy.data.collections["Elfo"].objects.link(o)
    else:
        o.data.name = nombre + "_viejo"
    o.parent = bpy.data.objects[padre]; o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    parte(nombre, construir, materiales=materiales)
    o.data.name = nombre
    return o

def hacer_accesorios():
    cas = bpy.data.objects["Cascabel"]
    c_pompon = RAIZ.matrix_world.inverted() @ cas.matrix_world.translation
    vs = [cas.matrix_world @ v.co for v in cas.data.vertices]
    c_pompon = RAIZ.matrix_world.inverted() @ (sum(vs, Vector()) / len(vs))
    acc("Acc_Nieves_Pelo", "Cabeza", melena, mats("Acc_Pelo"))
    acc("Acc_Nieves_Monos", "Cabeza", monos, mats("Acc_Rosa"))
    acc("Acc_Nieves_Pestanas", "Cabeza", pestanas, mats("Elfo_Negro"))
    acc("Acc_Nieves_Pompon", "Gorro", pompon(c_pompon), mats("Acc_Blanco"))
    acc("Acc_Chispa_Lentes", "Cabeza", lentes, mats("Acc_Oro"))
    acc("Acc_Chispa_Copete", "Cabeza", copete, mats("Acc_PeloNaranja"))
    acc("Acc_Chispa_Pecas", "Cabeza", pecas, mats("Acc_Pecas"))
    acc("Acc_Chispa_Bufanda", "Cuerpo", bufanda, mats("Acc_Bufanda1", "Acc_Bufanda2"))
    for o in bpy.data.objects:
        if o.name.startswith("Acc_"):
            print(o.name, "padre", o.parent.name, "tris", sum(len(p.vertices) - 2 for p in o.data.polygons))
