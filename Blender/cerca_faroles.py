# -*- coding: utf-8 -*-
"""
CERCA y FAROLES v2 (mismo estilo de la tarde: formas redondeadas + sombreado suave, mismos materiales).
Se reemplaza la GEOMETRÍA de las mallas "Cerca.001" y "Faroles.001" (los objetos Cerca / Faroles siguen igual,
mismo nombre, mismo lugar). Las posiciones de los 68 postes y de los 6 faroles se sacaron UNA vez de las mallas
viejas y se guardaron en Blender/datos_cerca.json, así el script se puede correr las veces que haga falta.

CERCA (materiales: 0 madera, 1 nieve, 2 cable, 3-6 focos rojo/verde/azul/amarillo)
  - Poste: tronco de 8 lados con radio un poco irregular y la punta redondeada (domo).
  - Gorrito de nieve: domo que sobresale del poste y escurre en 3-4 gotitas.
  - Travesaños: troncos delgados que se pandean un poquito al centro (curva Catmull-Rom, loft de modelado.py).
  - Nieve sobre el travesaño de arriba: tira abombada con puntas redondas (con huecos al azar).
  - Serie de foquitos: cable que cuelga en catenaria entre postes y 4 focos tipo gota con su casquillo.
FAROLES (materiales: 0 metal negro, 1 vidrio con luz, 2 nieve, 3 rojo)
  - Base escalonada redonda, poste que se adelgaza con anillos, listón rojo en espiral (bastón de caramelo)
    y un moño rojo arriba.
  - Linterna clásica: copa abajo, 4 parantes que se abren, vidrio luminoso, techo de 4 aguas con remate de
    bolita y un copete de nieve que escurre. El vidrio queda a la misma altura que antes (z ~3.23) para que las
    luces de Unity sigan en su lugar.
Uso: exec(modelado.py); exec(cerca_faroles.py); hacer_cerca(); hacer_faroles()
"""
import bpy, bmesh, math, random, json, os
from mathutils import Vector, Matrix
from collections import Counter

DATOS = PROYECTO + "/Blender/datos_cerca.json"

def _islas(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    vistos = set(); res = []
    for f in bm.faces:
        if f.index in vistos: continue
        pila = [f]; grupo = []; vistos.add(f.index)
        while pila:
            g = pila.pop(); grupo.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in vistos: vistos.add(h.index); pila.append(h)
        vs = {v for g in grupo for v in g.verts}
        res.append(([min(v.co[i] for v in vs) for i in range(3)], [max(v.co[i] for v in vs) for i in range(3)]))
    bm.free(); return res

def datos():
    if os.path.exists(DATOS):
        return json.load(open(DATOS))
    postes = [((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2], mx[2]) for mn, mx in _islas(bpy.data.meshes["Cerca.001"])
              if mx[2] - mn[2] > 0.7 and mx[0] - mn[0] < 0.5 and mx[1] - mn[1] < 0.5]
    faroles = [((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]) for mn, mx in _islas(bpy.data.meshes["Faroles.001"])
               if mx[2] - mn[2] > 2]
    d = {"postes": postes, "faroles": faroles}
    json.dump(d, open(DATOS, "w"), indent=1)
    return d

# ------------------------------------------------------------------ piezas
def domo_nieve(bm, centro, radio, alto, mat, rnd, segs=12, gotas=3, caida=0.05):
    """Gorrito de nieve: domo achatado; la orilla baja un poco más en 'gotas' lugares (escurre)."""
    pos = [rnd.uniform(0, 2 * math.pi) for _ in range(gotas)]
    filas = []
    for k, t in enumerate((0.0, 0.35, 0.65, 0.88)):
        fila = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            r = radio * math.cos(t * math.pi / 2) * (1 + 0.05 * math.sin(3 * a + pos[0]))
            z = alto * math.sin(t * math.pi / 2)
            if k == 0:
                g = sum(math.exp(-((math.atan2(math.sin(a - p), math.cos(a - p))) / 0.3) ** 2) for p in pos)
                z -= caida * (0.4 + g)
                r *= 0.97
            fila.append(bm.verts.new(Vector(centro) + Vector((math.cos(a) * r, math.sin(a) * r, z))))
        filas.append(fila)
    for a, b in zip(filas, filas[1:]):
        for j in range(segs):
            f = bm.faces.new((a[j], a[(j + 1) % segs], b[(j + 1) % segs], b[j])); f.material_index = mat; f.smooth = True
    tapa = bm.verts.new(Vector(centro) + Vector((0, 0, alto)))
    for j in range(segs):
        f = bm.faces.new((filas[-1][j], filas[-1][(j + 1) % segs], tapa)); f.material_index = mat; f.smooth = True
    # por debajo: un aro hacia adentro para que no se vea hueco desde abajo
    c = bm.verts.new(Vector(centro) + Vector((0, 0, -caida * 0.3)))
    for j in range(segs):
        f = bm.faces.new((filas[0][(j + 1) % segs], filas[0][j], c)); f.material_index = mat; f.smooth = True

def capa_nieve(bm, x, y, perfil, mat, rnd, segs=16, gotas=4, caida=0.05):
    """Capa de nieve de revolución (perfil de abajo hacia arriba, r=0 al final). La orilla de abajo escurre."""
    pos = [rnd.uniform(0, 2 * math.pi) for _ in range(gotas)]
    filas = []
    for k, (z, r) in enumerate(perfil):
        if r <= 1e-5: filas.append(bm.verts.new((x, y, z))); continue
        fila = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            zz = z
            if k == 0:
                g = sum(math.exp(-((math.atan2(math.sin(a - p), math.cos(a - p))) / 0.28) ** 2) for p in pos)
                zz -= caida * (0.3 + g)
            fila.append(bm.verts.new((x + math.cos(a) * r, y + math.sin(a) * r, zz)))
        filas.append(fila)
    for a, b in zip(filas, filas[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            vs = (a[j], a[k], b[k], b[j]) if isinstance(b, list) else (a[j], a[k], b)
            f = bm.faces.new(vs); f.material_index = mat; f.smooth = True
    # por abajo: anillo hacia adentro (no se ve hueco desde el suelo)
    c = bm.verts.new((x, y, perfil[0][0] - 0.01))
    for j in range(segs):
        f = bm.faces.new((filas[0][(j + 1) % segs], filas[0][j], c)); f.material_index = mat; f.smooth = True

def poste(bm, x, y, z0, z1, rnd, r=0.085, mat=0, segs=8):
    """Tronco vertical con radio irregular y punta en domo."""
    alturas = [z0, z0 + (z1 - z0) * 0.35, z0 + (z1 - z0) * 0.7, z1 - r * 0.6, z1 - r * 0.15]
    radios = [r * 1.06, r * rnd.uniform(0.95, 1.03), r * rnd.uniform(0.95, 1.03), r, r * 0.7]
    giro = rnd.uniform(0, 1)
    filas = []
    for z, rr in zip(alturas, radios):
        filas.append([bm.verts.new((x + math.cos(giro + 2 * math.pi * j / segs) * rr * rnd.uniform(0.97, 1.03),
                                    y + math.sin(giro + 2 * math.pi * j / segs) * rr * rnd.uniform(0.97, 1.03), z)) for j in range(segs)])
    for a, b in zip(filas, filas[1:]):
        for j in range(segs):
            f = bm.faces.new((a[j], a[(j + 1) % segs], b[(j + 1) % segs], b[j])); f.material_index = mat; f.smooth = True
    tapa = bm.verts.new((x, y, z1))
    for j in range(segs):
        f = bm.faces.new((filas[-1][j], filas[-1][(j + 1) % segs], tapa)); f.material_index = mat; f.smooth = True

def gota_foco(bm, p, eje, tam, mat_foco, mat_casq):
    """Foco tipo gota colgando de 'p' en dirección 'eje' (casquillo + bulbo)."""
    rot = eje.to_track_quat("Z", "Y").to_matrix()
    loft(bm, [p, p + eje * tam * 0.7], [(tam * 0.32, tam * 0.32)] * 2, mat=mat_casq, segs=6, sub=1, tapas=(True, False), domo=0.0)
    r = bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=5, radius=1.0)
    for v in r["verts"]:
        c = v.co.copy()
        ancho = tam * 0.48 * (1.0 - 0.3 * max(0.0, -c.z))      # se adelgaza hacia la punta (como gota)
        v.co = p + rot @ Vector((c.x * ancho, c.y * ancho, tam * 0.7 + tam * 0.75 * (1 - c.z)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mat_foco; f.smooth = True

def reemplazar(me, construir):
    bm = bmesh.new(); construir(bm)
    bm.normal_update()
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print(me.name, "tris =", sum(len(p.vertices) - 2 for p in me.polygons))

# ------------------------------------------------------------------ CERCA
def hacer_cerca(semilla=7):
    d = datos(); P = d["postes"]
    rnd = random.Random(semilla)
    def construir(bm):
        for (x, y, z0, z1) in P:
            poste(bm, x, y, z0, z1, rnd)
            domo_nieve(bm, (x, y, z1 - 0.035), 0.115, 0.075, 1, rnd, segs=10, gotas=rnd.choice((2, 3)), caida=0.045)
        # tramos: cada par de postes vecinos (a ~2 m)
        tramos = []
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if (Vector(P[i][:2]) - Vector(P[j][:2])).length < 2.4: tramos.append((i, j))
        print("tramos:", len(tramos))
        for n, (i, j) in enumerate(tramos):
            a, b = P[i], P[j]
            A, Bv = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
            dirr = (Bv - A).normalized()
            suelo = (a[2] + b[2]) / 2 + 0.25            # los postes están enterrados 25 cm
            alto = ((a[3] - a[2]) + (b[3] - b[2])) / 2 - 0.25
            for k, hrel in enumerate((0.36, 0.74)):
                z = suelo + alto * hrel
                pa = A - dirr * 0.04 + Vector((0, 0, z + rnd.uniform(-0.02, 0.02)))
                pb = Bv + dirr * 0.04 + Vector((0, 0, z + rnd.uniform(-0.02, 0.02)))
                medio = (pa + pb) / 2 + Vector((0, 0, -0.025))
                r = 0.042 * rnd.uniform(0.92, 1.08)
                loft(bm, [pa, medio, pb], [(r, r)] * 3, mat=0, segs=6, sub=2, tapas=(True, True), domo=0.4)
                if k == 1 and rnd.random() < 0.85:      # tira de nieve encima del travesaño de arriba
                    t0, t1 = rnd.uniform(0.08, 0.2), rnd.uniform(0.75, 0.92)
                    pts = []
                    for t in (t0, (t0 * 2 + t1) / 3, (t0 + t1 * 2) / 3, t1):
                        q = pa.lerp(pb, t) + Vector((0, 0, -0.1 * t * (1 - t) + r * 0.55))
                        pts.append(q)
                    rr = [(0.03, 0.02), (0.065, 0.05), (0.065, 0.05), (0.03, 0.02)]
                    loft(bm, pts, rr, mat=1, segs=8, sub=2, tapas=(True, True), domo=0.9)
            # serie de foquitos: catenaria entre las puntas de los postes
            za, zb = a[3] - 0.12, b[3] - 0.12
            cad = []
            for s in range(9):
                t = s / 8
                q = Vector((a[0], a[1], za)).lerp(Vector((b[0], b[1], zb)), t)
                q.z -= 0.16 * 4 * t * (1 - t)
                cad.append(q)
            loft(bm, cad, [(0.007, 0.007)] * len(cad), mat=2, segs=4, sub=1, tapas=(False, False))
            for f in range(4):
                t = (f + 0.6) / 4.2
                idx = t * 8; i0 = min(int(idx), 7)
                q = cad[i0].lerp(cad[i0 + 1], idx - i0)
                eje = Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), -1)).normalized()
                gota_foco(bm, q, eje, 0.065, 3 + (n + f) % 4, 2)
    reemplazar(bpy.data.meshes["Cerca.001"], construir)

# ------------------------------------------------------------------ FAROLES
def anillo_perfil(bm, x, y, perfil, mat, segs=12, suave=True):
    """Sólido de revolución: perfil = [(z, r), ...] de abajo hacia arriba (r=0 en los extremos lo cierra)."""
    filas = []
    for z, r in perfil:
        if r <= 1e-5: filas.append(bm.verts.new((x, y, z)))
        else: filas.append([bm.verts.new((x + math.cos(2 * math.pi * j / segs) * r, y + math.sin(2 * math.pi * j / segs) * r, z)) for j in range(segs)])
    for a, b in zip(filas, filas[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            if isinstance(a, list) and isinstance(b, list): vs = (a[j], a[k], b[k], b[j])
            elif isinstance(a, list): vs = (a[j], a[k], b)
            else: vs = (a, b[k], b[j])
            f = bm.faces.new(vs); f.material_index = mat; f.smooth = suave

def farol(bm, x, y, z0, rnd):
    N, VID, NIE, ROJ = 0, 1, 2, 3
    # base escalonada
    anillo_perfil(bm, x, y, [(z0 - 0.05, 0), (z0 - 0.05, 0.2), (z0 + 0.05, 0.2), (z0 + 0.08, 0.17), (z0 + 0.1, 0.13),
                             (z0 + 0.2, 0.12), (z0 + 0.24, 0.085), (z0 + 0.3, 0.06)], N, segs=14)
    # poste que se adelgaza, con anillos
    anillo_perfil(bm, x, y, [(z0 + 0.28, 0.058), (z0 + 2.85, 0.042)], N, segs=10)
    for zr in (0.45, 1.7, 2.62):
        toro(bm, (x, y, z0 + zr), 0.05, 0.018, mat=N, segs=12, lados=6)
    # listón rojo en espiral (bastón de caramelo)
    hel = []
    for s in range(61):
        t = s / 60
        a = t * 2 * math.pi * 4.5
        z = z0 + 0.55 + t * 1.95
        r = 0.058 - 0.016 * (z - z0) / 2.85 + 0.006
        hel.append(Vector((x + math.cos(a) * r, y + math.sin(a) * r, z)))
    loft(bm, hel, [(0.012, 0.05)] * len(hel), mat=ROJ, segs=6, sub=1, tapas=(True, True), arriba=Vector((0, 0, 1)))
    # moño rojo
    zm = z0 + 2.45
    for s in (-1, 1):
        lazo = [Vector((x, y - 0.05, zm)), Vector((x + s * 0.1, y - 0.07, zm + 0.08)), Vector((x + s * 0.17, y - 0.06, zm + 0.02)),
                Vector((x + s * 0.12, y - 0.06, zm - 0.04)), Vector((x + s * 0.02, y - 0.055, zm))]
        loft(bm, lazo, [(0.035, 0.012)] * 5, mat=ROJ, segs=6, sub=3, tapas=(True, True))
        cola = [Vector((x + s * 0.01, y - 0.055, zm - 0.01)), Vector((x + s * 0.05, y - 0.07, zm - 0.12)), Vector((x + s * 0.07, y - 0.065, zm - 0.24))]
        loft(bm, cola, [(0.028, 0.008)] * 3, mat=ROJ, segs=6, sub=3, tapas=(True, True))
    esfera(bm, (x, y - 0.06, zm), (0.035, 0.03, 0.035), mat=ROJ, segs=8, anillos=6)
    # linterna
    zc = z0 + 2.83   # copa
    anillo_perfil(bm, x, y, [(zc, 0.0), (zc, 0.05), (zc + 0.08, 0.1), (zc + 0.14, 0.17), (zc + 0.17, 0.19), (zc + 0.19, 0.0)], N, segs=4 * 3)
    zv0, zv1 = z0 + 2.99, z0 + 3.47
    # vidrio: prisma de 4 lados que se abre hacia arriba
    vid = []
    for z, r in ((zv0, 0.15), (zv1, 0.19)):
        vid.append([bm.verts.new((x + math.cos(math.pi / 4 + k * math.pi / 2) * r, y + math.sin(math.pi / 4 + k * math.pi / 2) * r, z)) for k in range(4)])
    for k in range(4):
        f = bm.faces.new((vid[0][k], vid[0][(k + 1) % 4], vid[1][(k + 1) % 4], vid[1][k])); f.material_index = VID
    f = bm.faces.new(vid[1]); f.material_index = VID
    # parantes en las 4 esquinas
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p0 = Vector((x + math.cos(a) * 0.165, y + math.sin(a) * 0.165, zv0 - 0.02))
        p1 = Vector((x + math.cos(a) * 0.205, y + math.sin(a) * 0.205, zv1 + 0.02))
        loft(bm, [p0, p1], [(0.018, 0.018)] * 2, mat=N, segs=4, sub=1, tapas=(True, True), domo=0.0)
    # techo de 4 aguas
    zt = zv1 + 0.02
    anillo_perfil(bm, x, y, [(zt, 0.0), (zt, 0.27), (zt + 0.05, 0.27), (zt + 0.2, 0.08), (zt + 0.26, 0.03), (zt + 0.27, 0.0)], N, segs=4, suave=False)
    esfera(bm, (x, y, zt + 0.33), (0.045, 0.045, 0.05), mat=N, segs=10, anillos=6)
    # copete de nieve sobre el techo
    # capa de nieve que SIGUE la forma del techo, un poco más ancha y más alta => no lo atraviesa y el techo
    # negro se asoma abajo como otra capa
    capa_nieve(bm, x, y, [(zt + 0.07, 0.3), (zt + 0.1, 0.285), (zt + 0.17, 0.2), (zt + 0.24, 0.11), (zt + 0.29, 0.05), (zt + 0.305, 0.0)],
               NIE, rnd, gotas=5, caida=0.05)

def hacer_faroles(semilla=5):
    d = datos(); rnd = random.Random(semilla)
    def construir(bm):
        for (x, y, z0) in d["faroles"]:
            farol(bm, x, y, z0, rnd)
    reemplazar(bpy.data.meshes["Faroles.001"], construir)
