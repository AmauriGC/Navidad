# -*- coding: utf-8 -*-
"""
GALLETAS NOCHEBUENA + CHAROLA DE SANTA (historia v1.5). Estilo LOW-POLY de caras planas.
  10 galletas con FORMA y una LETRA de betún (orden de la palabra NOCHEBUENA):
    0 N estrella · 1 O campana · 2 C arbolito · 3 H muñeco de nieve · 4 E bastón
    5 B copo · 6 U calcetín · 7 E regalo · 8 N reno · 9 A corazón
  GalletaForma_0..9 : una malla cada una, de pie (mira a -Y como la galleta vieja), origen al centro, ~0.42 m.
                      Colección "Galletas" -> Assets/Modelos/Galletas_Formas.glb (10 raíces en el origen).
  Charola           : charola roja con orilla dorada y 10 HUECOS con la silueta de cada forma (escala ESC_HUECO);
                      hijos vacíos Hueco_0..9 en el centro de cada hueco (Unity los usa para encajar).
  Mesita_Charola    : mesita redonda con mantel, vaso de leche y notita (estática).
  Charola y Mesita en la colección Props -> Props_Taller.glb. Lugar: Unity (-7.6, 0, 7.3), junto a la chimenea.
Uso: exec(modelado.py); exec(siete_v3.py); exec(cuarto_maquinas.py); exec(galletas_charola.py); hacer_todo()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

LETRAS = "NOCHEBUENA"
FORMAS = ("estrella", "campana", "arbolito", "muneco", "baston", "copo", "calcetin", "regalo", "reno", "corazon")
S = 0.2                        # escala de las formas (contornos de ~[-1, 1])
G = 0.035                      # medio grosor de la galleta
ESC_HUECO = 0.5                # en la charola las galletas van a la mitad de tamaño
MESITA = (7.6, -7.3)           # Blender (x, y) = Unity (-7.6, ?, 7.3)
ALTO_MESA = 0.78


# ------------------------------------------------------------------ contornos 2D (u derecha, v arriba)
def _estrella():
    return [((1.0 if k % 2 == 0 else 0.45) * math.sin(math.pi * k / 5), (1.0 if k % 2 == 0 else 0.45) * math.cos(math.pi * k / 5)) for k in range(10)]

def _campana():
    der = [(0.12, 1.0), (0.15, 0.86), (0.38, 0.74), (0.5, 0.4), (0.56, 0.0), (0.74, -0.42), (0.86, -0.6), (0.2, -0.6), (0.14, -0.8), (0.0, -0.88)]
    return der + [(-u, v) for (u, v) in reversed(der[:-1])]

def _arbolito():
    der = [(0.0, 1.0), (0.36, 0.55), (0.2, 0.55), (0.6, 0.05), (0.38, 0.05), (0.86, -0.5), (0.15, -0.5), (0.15, -0.88)]
    return der + [(-u, v) for (u, v) in reversed(der[1:])]

def _muneco():
    cab, rc = Vector((0, 0.5)), 0.4
    cue, rb = Vector((0, -0.35)), 0.58
    p = Vector((0, 0.17))
    pts = []
    for k in range(20):
        a = 2 * math.pi * k / 20
        q = cab + Vector((math.cos(a), math.sin(a))) * rc
        if (q - cue).length > rb: pts.append(q)
        q = cue + Vector((math.cos(a), math.sin(a))) * rb
        if (q - cab).length > rc: pts.append(q)
    pts.sort(key=lambda q: math.atan2(q.y - p.y, q.x - p.x))
    return [(q.x, q.y) for q in pts]

def _baston():
    t = 0.13
    camino = [Vector((0.2, -0.95)), Vector((0.2, -0.3)), Vector((0.2, 0.35))]
    for k in range(1, 9):
        a = math.pi * k / 8
        camino.append(Vector((-0.12 + 0.32 * math.cos(a), 0.35 + 0.32 * math.sin(a))))
    camino.append(Vector((-0.44, 0.12)))
    izq, der = [], []
    for i, p in enumerate(camino):
        d = (camino[min(i + 1, len(camino) - 1)] - camino[max(i - 1, 0)]).normalized()
        n = Vector((-d.y, d.x))
        izq.append(p + n * t); der.append(p - n * t)
    return [(q.x, q.y) for q in der + list(reversed(izq))]

def _copo():
    radios = (1.0, 0.4, 0.62, 0.4)
    return [(radios[k % 4] * math.sin(2 * math.pi * k / 24), radios[k % 4] * math.cos(2 * math.pi * k / 24)) for k in range(24)]

def _calcetin():
    return [(-0.38, 1.0), (0.34, 1.0), (0.34, 0.7), (0.26, 0.7), (0.26, -0.25), (0.16, -0.62), (-0.12, -0.86), (-0.6, -0.86),
            (-0.82, -0.72), (-0.78, -0.5), (-0.46, -0.34), (-0.3, -0.2), (-0.3, 0.7), (-0.38, 0.7)]

def _regalo():
    return [(-0.72, -0.82), (0.72, -0.82), (0.72, 0.42), (0.2, 0.42), (0.52, 0.82), (0.28, 0.96), (0.0, 0.6), (-0.28, 0.96),
            (-0.52, 0.82), (-0.2, 0.42), (-0.72, 0.42)]

def _reno():
    der = [(0.18, -0.95), (0.34, -0.6), (0.44, -0.12), (0.72, 0.02), (0.5, 0.24), (0.44, 0.36), (0.56, 0.56), (0.82, 0.74),
           (0.76, 0.96), (0.6, 0.76), (0.48, 0.92), (0.34, 0.6), (0.18, 0.42)]
    return der + [(-u, v) for (u, v) in reversed(der)]

def _corazon():
    pts = []
    for k in range(28):
        t = 2 * math.pi * k / 28
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 17.0, y / 17.0 + 0.15))
    return pts

CONTORNOS = {"estrella": _estrella, "campana": _campana, "arbolito": _arbolito, "muneco": _muneco, "baston": _baston,
             "copo": _copo, "calcetin": _calcetin, "regalo": _regalo, "reno": _reno, "corazon": _corazon}
# dónde va la letra (u, v) y su tamaño, por forma
LETRA_EN = {"estrella": (0, -0.05, 0.6), "campana": (0, 0.05, 0.62), "arbolito": (0, -0.1, 0.55), "muneco": (0, -0.38, 0.62),
            "baston": (0.2, -0.45, 0.42), "copo": (0, 0.0, 0.42), "calcetin": (-0.02, 0.2, 0.55), "regalo": (0, -0.22, 0.7),
            "reno": (0, -0.25, 0.55), "corazon": (0, 0.05, 0.75)}
COLOR_LETRA = (1, 2, 3, 1, 1, 3, 1, 2, 3, 1)      # 1 blanco, 2 rojo, 3 verde (el bastón va en blanco: ya tiene rayas rojas)      # 1 blanco, 2 rojo, 3 verde (alterna para que se distingan)


def contorno_de(i, escala=1.0):
    return [(u * S * escala, v * S * escala) for (u, v) in CONTORNOS[FORMAS[i]]()]


# ------------------------------------------------------------------ piezas
def prisma(bm, pts, y0, y1, mat, cx=0.0, cz=0.0):
    """Extruye el contorno (u -> x, v -> z) entre y0 y y1 (caras planas, ngon cóncavo permitido)."""
    a = [bm.verts.new((cx + u, y0, cz + v)) for (u, v) in pts]
    b = [bm.verts.new((cx + u, y1, cz + v)) for (u, v) in pts]
    n = len(pts)
    fa = bm.faces.new(a); fa.material_index = mat
    fb = bm.faces.new(list(reversed(b))); fb.material_index = mat
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((a[k], a[j], b[j], b[k])).material_index = mat


def orilla(pts, factor):
    """Contorno encogido/agrandado hacia su centro (para el betún de la orilla y el borde de los huecos)."""
    cu = sum(p[0] for p in pts) / len(pts); cv = sum(p[1] for p in pts) / len(pts)
    return [(cu + (u - cu) * factor, cv + (v - cv) * factor) for (u, v) in pts]


def galleta(i):
    def construir(bm):
        pts = contorno_de(i)
        prisma(bm, pts, -G, G, 0)
        # betún de la orilla (frente)
        if FORMAS[i] != "baston":         # el bastón es muy delgado: la orilla taparía la letra
            o = orilla(pts, 0.84)
            tira(bm, [(u, -G - 0.004, v) for (u, v) in o + [o[0]]], 0.008, 1, segs=4)
        # letra de betún
        lu, lv, tam = LETRA_EN[FORMAS[i]]
        texto(bm, LETRAS[i], (lu * S, -G - 0.006, lv * S - tam * S * 0.05), tam * S * 1.25, COLOR_LETRA[i], normal_y=-1)
        # detallitos por forma
        if FORMAS[i] == "reno":
            tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=0.028)
            for v in tmp.verts: v.co += Vector((0, -G - 0.01, -0.8 * S))
            for f in tmp.faces: f.material_index = 2
            unir(bm, tmp)
        if FORMAS[i] == "estrella":
            for k in range(5):
                a = 2 * math.pi * k / 5
                cil(bm, (0.62 * S * math.sin(a), -G - 0.002, 0.62 * S * math.cos(a)), (0.62 * S * math.sin(a), -G - 0.012, 0.62 * S * math.cos(a)), 0.012, 4, segs=6)
        if FORMAS[i] == "baston":
            for k in range(3):            # rayitas rojas del bastón (arriba; abajo va la letra)
                z = (-0.1 + k * 0.18) * S
                tira(bm, [(0.2 * S - 0.11 * S, -G - 0.004, z), (0.2 * S + 0.11 * S, -G - 0.004, z + 0.08 * S)], 0.01, 2, segs=4)
    return construir


def charola(bm):
    # charola redondeada roja con orilla dorada y dos asas; los huecos van en dos filas: N O C H E / B U E N A
    MRojo, MOro, MHueco = 0, 1, 2
    cx, cy = MESITA; z = ALTO_MESA + 0.03
    L, A = 1.36, 0.66
    caja(bm, (cx, cy, z), (L, A, 0.03), mat=MRojo, bisel=0.012, segs=1)
    for s in (-1, 1):
        caja(bm, (cx, cy + s * (A / 2 - 0.015), z + 0.03), (L, 0.03, 0.04), mat=MOro, bisel=0.008, segs=1)
        caja(bm, (cx + s * (L / 2 - 0.015), cy, z + 0.03), (0.03, A, 0.04), mat=MOro, bisel=0.008, segs=1)
        tira(bm, [(cx + s * (L / 2), cy - 0.12, z + 0.035), (cx + s * (L / 2 + 0.07), cy - 0.08, z + 0.05),
                  (cx + s * (L / 2 + 0.07), cy + 0.08, z + 0.05), (cx + s * (L / 2), cy + 0.12, z + 0.035)], 0.014, MOro, segs=5)
    huecos = []
    for i in range(10):
        fila, col = (0, i) if i < 5 else (1, i - 5)
        hx = cx + (col - 2) * 0.25
        hy = cy + (0.14 if fila == 0 else -0.14)          # fila 0 = la de atrás (más lejos del jugador que mira desde -Y)
        pts = contorno_de(i, ESC_HUECO)
        # silueta hundida (oscura) + bordecito dorado alrededor
        area = sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))
        orden = pts if area > 0 else list(reversed(pts))      # antihorario => la cara mira hacia arriba (+Z)
        a = [bm.verts.new((hx + u, hy + v, z + 0.016)) for (u, v) in orden]
        bm.faces.new(a).material_index = MHueco
        o = orilla(pts, 1.12)
        tira(bm, [(hx + u, hy + v, z + 0.018) for (u, v) in o + [o[0]]], 0.006, MOro, segs=4)
        huecos.append(Vector((hx, hy, z + 0.02)))
    return huecos


def mesita(bm):
    MAD, MANTEL, BLANCO, VIDRIO, PAPEL, ROJO = range(6)
    cx, cy = MESITA
    cil(bm, (cx, cy, ALTO_MESA - 0.04), (cx, cy, ALTO_MESA), 0.76, MAD, segs=12)                     # cubierta
    cil(bm, (cx, cy, ALTO_MESA - 0.3), (cx, cy, ALTO_MESA + 0.005), 0.84, MANTEL, segs=12, r2=0.78)   # mantel que cae
    for k in range(12):                                                                             # orilla blanca del mantel
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        tira(bm, [(cx + 0.845 * math.cos(a0), cy + 0.845 * math.sin(a0), ALTO_MESA - 0.29),
                  (cx + 0.845 * math.cos(a1), cy + 0.845 * math.sin(a1), ALTO_MESA - 0.29)], 0.02, BLANCO, segs=4)
    cil(bm, (cx, cy, 0.05), (cx, cy, ALTO_MESA - 0.1), 0.07, MAD, segs=8)                           # pata
    for k in range(3):
        a = 2 * math.pi * k / 3
        tira(bm, [(cx, cy, 0.12), (cx + 0.35 * math.cos(a), cy + 0.35 * math.sin(a), 0.02)], 0.035, MAD, segs=5)
    # vaso de leche y notita "Para Santa"
    vx, vy = cx + 0.4, cy - 0.5
    cil(bm, (vx, vy, ALTO_MESA), (vx, vy, ALTO_MESA + 0.16), 0.055, VIDRIO, segs=8)
    cil(bm, (vx, vy, ALTO_MESA + 0.005), (vx, vy, ALTO_MESA + 0.13), 0.048, BLANCO, segs=8)
    caja(bm, (cx - 0.38, cy - 0.5, ALTO_MESA + 0.004), (0.16, 0.11, 0.006), mat=PAPEL, bisel=0.0, segs=1,
         giro=Matrix.Rotation(0.3, 3, "Z"))
    texto_arriba_local(bm, "Para Santa", (cx - 0.38, cy - 0.5, ALTO_MESA + 0.009), 0.022, ROJO)


def texto_arriba_local(bm, cadena, centro, tam, mat):
    cu = bpy.data.curves.new("_txt", "FONT"); cu.body = cadena; cu.size = tam; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.001; cu.resolution_u = 2
    ob = bpy.data.objects.new("_txt", cu); bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    tmp = bmesh.new(); tmp.from_mesh(me); bpy.data.meshes.remove(me)
    rot = Matrix.Rotation(0.3, 3, "Z")
    for v in tmp.verts: v.co = rot @ v.co + Vector(centro)
    for f in tmp.faces: f.material_index = mat
    unir(bm, tmp)


# ------------------------------------------------------------------ objetos
def _obj(nombre, coleccion):
    o = bpy.data.objects.get(nombre)
    if o is None:
        o = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre))
        col = bpy.data.collections.get(coleccion)
        if col is None:
            col = bpy.data.collections.new(coleccion); bpy.data.scenes["Scene"].collection.children.link(col)
        col.objects.link(o)
    return o


def hacer_galletas():
    masa = bpy.data.materials["Galleta_Masa"]; glas = bpy.data.materials["Galleta_Glaseado"]
    rojo = bpy.data.materials["Galleta_DulceRojo"]; verde = bpy.data.materials["Galleta_DulceVerde"]
    oro = material("Galleta_Chispa", (1.0, 0.8, 0.3), metal=0.6, rugosidad=0.3, emision=(1.0, 0.75, 0.3), fuerza=0.4)
    res = []
    for i in range(10):
        o = _obj(f"GalletaForma_{i}", "Galletas")
        bm = bmesh.new(); galleta(i)(bm)
        reemplazar_malla(o, bm, [masa, glas, rojo, verde, oro])
        o.location = (12 + i * 0.6, -4, 1.0)            # en Blender quedan en fila para verlas; se exportan en el origen
        res.append(sum(len(p.vertices) - 2 for p in o.data.polygons))
    return f"galletas: {res} tris"


def hacer_charola():
    rojo = material("Charola_Roja", (0.75, 0.08, 0.08), metal=0.3, rugosidad=0.35)
    oro = bpy.data.materials["Amb_Laton"]
    hueco = material("Charola_Hueco", (0.25, 0.12, 0.06), rugosidad=0.85)
    o = _obj("Charola", "Props")
    bm = bmesh.new(); huecos = charola(bm)
    centro = Vector((MESITA[0], MESITA[1], ALTO_MESA + 0.03))
    for v in bm.verts: v.co -= centro                      # pivote de la charola = centro de su base (Unity la usa de referencia)
    reemplazar_malla(o, bm, [rojo, oro, hueco])
    o.location = centro
    o.rotation_euler = (0, 0, math.pi)       # el frente (-Y) mira al TALLER (Unity -Z), no a la chimenea
    for i, p in enumerate(huecos):
        e = bpy.data.objects.get(f"Hueco_{i}")
        if e is None:
            e = bpy.data.objects.new(f"Hueco_{i}", None)
            for c in o.users_collection: c.objects.link(e)
        e.empty_display_type = "PLAIN_AXES"; e.empty_display_size = 0.05
        e.parent = o; e.matrix_parent_inverse = Matrix.Identity(4); e.location = p - centro
    m = _obj("Mesita_Charola", "Props")
    bm = bmesh.new(); mesita(bm)
    giro = Matrix.Rotation(math.pi, 3, "Z"); c0 = Vector((MESITA[0], MESITA[1], 0))
    for v in bm.verts: v.co = giro @ (v.co - c0) + c0            # vaso y notita del lado del taller
    ms = [bpy.data.materials[n] for n in ("Amb_Madera", "Amb_Rojo", "Amb_Blanco", "Amb_Vidrio")] + \
         [material("Nota_Papel", (0.96, 0.93, 0.82), rugosidad=0.9), bpy.data.materials["Galleta_DulceRojo"]]
    reemplazar_malla(m, bm, ms)
    m.location = (0, 0, 0)
    t = lambda ob: sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return f"charola {t(o)} tris, mesita {t(m)} tris"


def hacer_todo():
    return [hacer_galletas(), hacer_charola()]
