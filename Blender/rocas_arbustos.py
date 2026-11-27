# -*- coding: utf-8 -*-
"""
ROCAS, ARBUSTOS y LEÑA v2 (estilo de la tarde: formas suaves y redondeadas, mismos materiales).
Se reemplaza la geometría de las mallas compartidas (Roca0/1/2, Arbusto, Troncos): todas sus copias en el
juego se actualizan solas. Cada malla nueva se ESCALA para ocupar la misma caja que la vieja (las medidas se
guardaron una vez en Blender/datos_rocas.json), así los colliders convexos de Unity quedan casi iguales.

NIEVE EN CAPAS (nieve_encima): en vez de pintar de blanco las caras de arriba, se COPIAN esas caras y la copia
se empuja hacia afuera siguiendo la normal (más gruesa al centro, delgadita en la orilla). Resultado: una capita
de nieve que va ENCIMA de la roca/hoja/tronco, con orilla redondita, y nunca la atraviesa.
Uso: exec(modelado.py); exec(rocas_arbustos.py); hacer_todo()
"""
import bpy, bmesh, math, random, json, os
from mathutils import Vector, noise

DATOS_R = PROYECTO + "/Blender/datos_rocas.json"
MALLAS_R = ["Roca0", "Roca1", "Roca2", "Arbusto", "Troncos"]

def cajas_originales():
    if os.path.exists(DATOS_R): return json.load(open(DATOS_R))
    d = {}
    for n in MALLAS_R:
        vs = [v.co for v in bpy.data.meshes[n].vertices]
        d[n] = [[min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]]
    json.dump(d, open(DATOS_R, "w"), indent=1); return d

def ajustar_a_caja(bm, caja, solo=None):
    """Escala y mueve los vértices para que ocupen la caja (mn, mx) de la malla original."""
    vs = solo if solo is not None else bm.verts
    mn = Vector([min(v.co[i] for v in vs) for i in range(3)]); mx = Vector([max(v.co[i] for v in vs) for i in range(3)])
    cmn, cmx = Vector(caja[0]), Vector(caja[1])
    for v in bm.verts:
        v.co = Vector([cmn[i] + (v.co[i] - mn[i]) / max(mx[i] - mn[i], 1e-6) * (cmx[i] - cmn[i]) for i in range(3)])

def nieve_encima(bm, caras, grosor, mat, rnd=None, gotas=0.0):
    """Capa de nieve: duplica 'caras' y empuja la copia hacia afuera (normal del vértice)."""
    if not caras: return
    bm.normal_update()
    normales = {v: v.normal.copy() for f in caras for v in f.verts}
    dup = bmesh.ops.duplicate(bm, geom=list(caras))
    vmap = dup["vert_map"]
    nuevas = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
    nverts = {v for f in nuevas for v in f.verts}
    origen = {vmap[o]: o for o in vmap if o in normales and vmap[o] in nverts}
    # distancia (en anillos) a la orilla de la capa
    conjunto = set(nuevas)
    orilla = {v for f in nuevas for e in f.edges if sum(1 for g in e.link_faces if g in conjunto) == 1 for v in e.verts}
    dist = {v: 0 for v in orilla}; frente = list(orilla)
    while frente:
        sig = []
        for v in frente:
            for e in v.link_edges:
                w = e.other_vert(v)
                if w in nverts and w not in dist: dist[w] = dist[v] + 1; sig.append(w)
        frente = sig
    perfil = [0.18, 0.55, 0.82, 0.95, 1.0]
    for v in nverts:
        n = normales.get(origen.get(v), Vector((0, 0, 1)))
        k = perfil[min(dist.get(v, 4), 4)]
        extra = 0.0
        if gotas and dist.get(v, 9) == 0 and rnd and rnd.random() < gotas: extra = 0.6
        v.co = v.co + n * grosor * k + Vector((0, 0, -grosor * extra))
    for f in nuevas: f.material_index = mat; f.smooth = True

def suave01(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def nieve_campo(bm, caras, campo, grosor, mat, hundir=0.012):
    """Capa de nieve con ORILLA SUAVE: se duplican las caras candidatas y cada vértice se empuja hacia afuera
    grosor * campo(punto, normal) (campo va de 0 a 1). Donde el campo vale 0 la copia queda un poquito
    HUNDIDA (-hundir) y no se ve: la orilla visible es donde la capa cruza la superficie => línea curva, sin
    dientes. Las caras que quedarían completamente hundidas se borran (no gastan triángulos)."""
    if not caras: return
    bm.normal_update()
    normales = {v: v.normal.copy() for f in caras for v in f.verts}
    dup = bmesh.ops.duplicate(bm, geom=list(caras))
    vmap = dup["vert_map"]
    nuevas = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
    peso = {}
    for o, v in vmap.items():
        if not isinstance(o, bmesh.types.BMVert) or o not in normales: continue
        n = normales[o]
        w = campo(o.co, n)
        peso[v] = w
        v.co = o.co + n * (grosor * w - hundir)
    borrar = [f for f in nuevas if all(peso.get(v, 0) < 0.02 for v in f.verts)]
    for f in nuevas: f.material_index = mat; f.smooth = True
    bmesh.ops.delete(bm, geom=borrar, context="FACES")

def bola_grumosa(bm, centro, radios, mat, semilla, sub=2, grumo=0.18, frec=1.6):
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = Vector((semilla * 5.3, semilla * 2.9, semilla * 7.1))
    for v in res["verts"]:
        n = v.co.normalized()
        d = 1 + grumo * noise.noise(n * frec + off) + grumo * 0.35 * noise.noise(n * frec * 2.6 + off)
        v.co = Vector(centro) + Vector((n.x * radios[0] * d, n.y * radios[1] * d, n.z * radios[2] * d))
    caras = list({f for v in res["verts"] for f in v.link_faces})
    for f in caras: f.material_index = mat; f.smooth = True
    return caras

def poner(nombre, construir):
    me = bpy.data.meshes[nombre]
    bm = bmesh.new(); construir(bm, me)
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print(nombre, "tris =", sum(len(p.vertices) - 2 for p in me.polygons))

# ------------------------------------------------------------------ ROCAS (0 roca, 1 nieve)
def roca(nombre, semilla, caja):
    def construir(bm, me):
        rnd = random.Random(semilla)
        caras = bola_grumosa(bm, (0, 0, 0), (1, 0.9, 0.7), 0, semilla, sub=4, grumo=0.2, frec=1.3)
        # dos "cortes" suaves (caras más planas, como peña) sin aristas filosas
        for _ in range(2):
            nrm = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 0.6))).normalized()
            lim = max(v.co.dot(nrm) for v in bm.verts) * rnd.uniform(0.75, 0.85)
            for v in bm.verts:
                exc = v.co.dot(nrm) - lim
                if exc > 0: v.co -= nrm * exc * 0.85
        zmn = min(v.co.z for v in bm.verts)
        for v in bm.verts:          # base aplastada (se asienta en el suelo)
            if v.co.z < zmn + 0.25: v.co.z = zmn + 0.25 - (zmn + 0.25 - v.co.z) * 0.3
        ajustar_a_caja(bm, caja)
        zmn = caja[0][2]; zmx = caja[1][2]
        H = zmx - zmn
        gotas = [(rnd.uniform(0, 6.28), rnd.uniform(0.06, 0.14)) for _ in range(5)]
        def campo(p, n):
            ang = math.atan2(p.y, p.x)
            baja = sum(g * math.exp(-((math.atan2(math.sin(ang - a), math.cos(ang - a))) / 0.22) ** 2) for a, g in gotas)
            corte = zmn + H * (0.6 + 0.06 * noise.noise(p * 1.2)) - H * baja
            return suave01((p.z - corte) / (H * 0.07)) * suave01((n.z + 0.1) / 0.4)
        nieve_campo(bm, [f for f in bm.faces if f.normal.z > -0.2], campo, H * 0.075, 1)
    poner(nombre, construir)

# ------------------------------------------------------------------ ARBUSTO (0 hojas, 1 nieve, 2 bayas rojas)
def arbusto(caja, semilla=21):
    me = bpy.data.meshes["Arbusto"]
    if len(me.materials) < 3: me.materials.append(bpy.data.materials["Amb_Rojo"])
    def construir(bm, me):
        rnd = random.Random(semilla)
        bolas = [((0, 0, 0.55), 0.62), ((0.55, 0.1, 0.4), 0.45), ((-0.52, -0.05, 0.42), 0.48),
                 ((0.15, 0.45, 0.38), 0.42), ((-0.1, -0.45, 0.36), 0.4), ((0.3, -0.25, 0.75), 0.38)]
        todas = []
        for k, (c, r) in enumerate(bolas):
            caras = bola_grumosa(bm, c, (r, r, r * 0.85), 0, semilla + k, sub=3, grumo=0.16, frec=2.2)
            todas.append((caras, c, r))
        ajustar_a_caja(bm, caja)
        zmn, zmx = caja[0][2], caja[1][2]
        H = zmx - zmn
        def campo(p, n):
            return suave01((n.z - 0.2) / 0.45) * suave01((p.z - (zmn + H * (0.5 + 0.05 * noise.noise(p * 3)))) / (H * 0.16))
        hojas_todas = [f for caras, _, _ in todas for f in caras if f.is_valid]
        nieve_campo(bm, [f for f in hojas_todas if f.normal.z > 0.1], campo, H * 0.06, 1)
        # racimos de bayas de acebo en los costados
        hojas = [f for f in hojas_todas if f.is_valid and f.material_index == 0 and 0.0 < f.normal.z < 0.4]
        rnd.shuffle(hojas)
        esc = (caja[1][0] - caja[0][0]) / 1.5
        for f in hojas[:5]:
            p = f.calc_center_median() + f.normal * 0.02 * esc
            for b in range(3):
                q = p + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.035 * esc
                esfera(bm, q, (0.04 * esc,) * 3, mat=2, segs=8, anillos=6)
    poner("Arbusto", construir)

# ------------------------------------------------------------------ LEÑA (0 corteza, 1 madera clara de los cortes, 2 nieve)
def tronco_lena(bm, p0, p1, r, rnd, segs=16):
    """Leño: tubo con corteza ondulada; en cada punta, tapa clara con anillos (círculos concéntricos)."""
    eje = (p1 - p0); L = eje.length; d = eje.normalized()
    rot = d.to_track_quat("Z", "Y").to_matrix()
    fase = rnd.uniform(0, 6)
    def anillo(t, rr, z_extra=0.0):
        return [bm.verts.new(p0 + d * (t * L + z_extra) + rot @ Vector((math.cos(2 * math.pi * j / segs) * rr * (1 + 0.06 * math.sin(3 * j + fase)),
                                                               math.sin(2 * math.pi * j / segs) * rr * (1 + 0.06 * math.sin(3 * j + fase)), 0))) for j in range(segs)]
    filas = [anillo(0, r * 0.97), anillo(0.02, r), anillo(0.5, r * rnd.uniform(0.97, 1.03)), anillo(0.98, r), anillo(1, r * 0.97)]
    for a, b in zip(filas, filas[1:]):
        for j in range(segs):
            f = bm.faces.new((a[j], a[(j + 1) % segs], b[(j + 1) % segs], b[j])); f.material_index = 0; f.smooth = True
    # tapas con anillos: corona de corteza + 2 aros de madera clara + centro
    for fila, signo, t in ((filas[0], -1, 0.0), (filas[-1], 1, 1.0)):
        prev = fila
        # anillos del corte: corteza | madera clara | anillo oscuro delgado | madera clara | centro oscuro
        for k, (rr, hund, mat) in enumerate(((0.84, 0.0, 0), (0.6, -0.006, 1), (0.53, -0.006, 0), (0.22, -0.004, 1))):
            nueva = anillo(t, r * rr, signo * hund)
            for j in range(segs):
                vs = (prev[j], prev[(j + 1) % segs], nueva[(j + 1) % segs], nueva[j])
                f = bm.faces.new(vs if signo > 0 else tuple(reversed(vs))); f.material_index = mat
            prev = nueva
        c = bm.verts.new(p0 + d * (t * L))
        for j in range(segs):
            vs = (prev[j], prev[(j + 1) % segs], c)
            f = bm.faces.new(vs if signo > 0 else tuple(reversed(vs))); f.material_index = 0
    return filas

def lena(caja, semilla=31):
    def construir(bm, me):
        rnd = random.Random(semilla)
        r = 0.16; L = 1.5
        lenos = []
        for fila, n in enumerate((4, 3, 2)):
            for k in range(n):
                x = (k - (n - 1) / 2) * r * 2.02
                z = r + fila * r * 1.75
                y0 = -L / 2 + rnd.uniform(-0.06, 0.06)
                lenos.append(tronco_lena(bm, Vector((x, y0, z)), Vector((x + rnd.uniform(-0.03, 0.03), y0 + L, z + rnd.uniform(-0.02, 0.02))), r * rnd.uniform(0.92, 1.06), rnd))
        ajustar_a_caja(bm, caja)
        zmn, zmx = caja[0][2], caja[1][2]
        bm.normal_update()
        # solo la parte de arriba de los leños de arriba (los de abajo quedan tapados por los de encima)
        H = zmx - zmn
        def campo(p, n):
            return suave01((n.z - 0.45) / 0.3) * suave01((p.z - (zmn + H * 0.5)) / (H * 0.05)) * (0.8 + 0.2 * noise.noise(p * 4))
        corteza = [f for f in bm.faces if f.material_index == 0 and f.normal.z > 0.2 and abs(f.normal.y) < 0.5]
        nieve_campo(bm, corteza, campo, H * 0.06, 2)
    poner("Troncos", construir)

def hacer_todo():
    d = cajas_originales()
    roca("Roca0", 10, d["Roca0"]); roca("Roca1", 11, d["Roca1"]); roca("Roca2", 12, d["Roca2"])
    arbusto(d["Arbusto"]); lena(d["Troncos"])
