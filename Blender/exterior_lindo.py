# -*- coding: utf-8 -*-
"""
AMBIENTACIÓN EXTERIOR v2 ("una linda ambientación para explorar, con lucecitas").
Crea objetos NUEVOS (no toca Exterior.glb, así sus colisiones siguen igual):
  Montanas_v2.glb : anillo de montañas con crestas (ruido "ridged"), roca azulada y nieve en cumbres y laderas suaves.
  Pueblo_Luces.glb:
     - Senderos    : caminos de nieve pisada del patio a cada casa (pegados al suelo con rayos).
     - Farolito_N  : farolitos de poste a lo largo de los senderos (objetos separados => cada uno con collider en Unity).
     - LucesPueblo : focos de colores: guirnaldas entre farolitos, en los aleros de las 9 casas y en espiral en 10 pinos.
     - Coronas     : corona con moño en la puerta de cada casa.
Coordenadas: Unity (ux, uy, uz) = Blender (-bx, bz, -by).
Uso: exec(modelado.py); exec(exterior_lindo.py)
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree

rnd = random.Random(24)

def B(ux, uz, z=0.0):            # Unity (x, z) -> Blender
    return Vector((-ux, -uz, z))

def coleccion(nombre):
    c = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c

COL = coleccion("Ambientacion2")

def objeto(nombre, construir, mats):
    viejo = bpy.data.objects.get(nombre)
    if viejo: bpy.data.objects.remove(viejo, do_unlink=True)
    bm = bmesh.new(); construir(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(nombre, me); COL.objects.link(o)
    return o

def bvh_obj(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); return t

SUELO = bvh_obj(bpy.data.objects["SueloNieve"])

def altura(p):
    hit = SUELO.ray_cast(Vector((p.x, p.y, 60)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0

# ------------------------------------------------------------------ materiales
M_ROCA = material("Mon_Roca", (0.16, 0.19, 0.3), rugosidad=0.9)
M_NIEVE = material("Mon_Nieve", (0.82, 0.87, 0.98), rugosidad=0.6)
M_SENDERO = material("Ext_Sendero", (0.4, 0.44, 0.6), rugosidad=0.95)
M_POSTE = bpy.data.materials["Ext_MetalNegro"]
M_LUZ = bpy.data.materials["Ext_LuzFarol"]
M_NIEVEB = bpy.data.materials["Ext_NieveBrillo"]
FOCOS = [bpy.data.materials[n] for n in ("Amb_FocoRojo", "Amb_FocoVerde", "Amb_FocoAzul", "Foco_Amarillo")]
M_CABLE = bpy.data.materials["Arbol_Cable"]
M_CORONA = material("Corona_Verde", (0.05, 0.25, 0.1), rugosidad=0.7)
M_MONO = bpy.data.materials["Arbol_Mono"]

# ------------------------------------------------------------------ montañas
def montanas(bm):
    NA, NR = 400, 46
    r0, r1 = 118.0, 200.0
    filas = []
    for i in range(NR):
        t = i / (NR - 1)
        r = r0 + (r1 - r0) * (t ** 0.85)
        fila = []
        for j in range(NA):
            a = 2 * math.pi * j / NA
            p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
            q = p * 0.012
            cresta = noise.ridged_multi_fractal(q, 1.0, 2.1, 5, 1.0, 2.0)            # crestas afiladas
            suave = noise.fractal(q * 0.5 + Vector((7, 3, 1)), 0.6, 2.0, 3)
            sube = min(1.0, max(0.0, (r - 122) / 45.0)) ** 1.8
            h = sube * (8 + 20 * max(cresta, 0) ** 1.3 + 9 * suave)
            if r > 180: h += (r - 180) * 0.9                                         # el anillo de atrás sube: tapa el borde
            fila.append(bm.verts.new((p.x, p.y, h - 2.0)))
        filas.append(fila)
    for i in range(NR - 1):
        for j in range(NA):
            f = bm.faces.new((filas[i][j], filas[i][(j + 1) % NA], filas[i + 1][(j + 1) % NA], filas[i + 1][j]))
            f.smooth = True
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        n = f.normal if f.normal.z > 0 else -f.normal
        manchas = noise.noise(c * 0.08) * 6
        nieve = (c.z + manchas > 17) or (n.z > 0.8 and c.z > 4) or (n.z > 0.9)
        f.material_index = 1 if nieve else 0

# ------------------------------------------------------------------ senderos, farolitos y guirnaldas
CASAS = [o for o in bpy.data.objects if o.name.startswith("Casa_")]
PATIO = (-16.0, 26.0, -13.0, 13.0)          # x min, x max, z min, z max (Unity)

def rutas():
    """Para cada casa: puntos (Blender) del sendero, desde afuera del patio hasta enfrente de la casa."""
    lista = []
    for c in CASAS:
        ux, uz = -c.location.x, -c.location.y
        # punto de salida: el borde del patio más cercano a la casa, 2 m hacia afuera
        sx = min(max(ux, PATIO[0]), PATIO[1]); sz = min(max(uz, PATIO[2]), PATIO[3])
        d = Vector((ux - sx, uz - sz)); d.normalize()
        ini = Vector((sx, sz)) + d * 2.0
        fin = Vector((ux, uz)) - (Vector((ux, uz)) - ini).normalized() * 5.5
        largo = (fin - ini).length
        n = max(2, int(largo / 1.2))
        perp = Vector((-d.y, d.x))
        pts = []
        for k in range(n + 1):
            t = k / n
            p = ini.lerp(fin, t) + perp * math.sin(t * math.pi * 2.0) * 1.2          # el camino serpentea un poco
            pts.append(p)
        lista.append((c, pts))
    return lista

RUTAS = rutas()

def senderos(bm):
    for c, pts in RUTAS:
        izq, der = [], []
        for k, p in enumerate(pts):
            a = pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]; a.normalize()
            perp = Vector((-a.y, a.x)) * (0.85 + 0.15 * math.sin(k * 1.7))
            for lado, lista in ((1, izq), (-1, der)):
                q = p + perp * lado
                b = B(q.x, q.y); b.z = altura(b) + 0.07
                lista.append(bm.verts.new(b))
        for k in range(len(pts) - 1):
            f = bm.faces.new((izq[k], der[k], der[k + 1], izq[k + 1])); f.smooth = True

FAROLITOS = []          # (posición Blender del foco del farolito)

def farolito(bm, base):
    x, y, z = base
    loft(bm, [(x, y, z - 0.1), (x, y, z + 1.35)], [(0.045, 0.045)] * 2, mat=0, segs=10, sub=1, domo=0.0)
    caja(bm, (x, y, z + 0.06), (0.2, 0.2, 0.16), mat=0, bisel=0.03, segs=2)                     # base
    loft(bm, [(x, y, z + 1.3), (x, y - 0.1, z + 1.55), (x, y - 0.25, z + 1.58)], [(0.025, 0.025)] * 3, mat=0, segs=8, sub=3)   # gancho
    c = Vector((x, y - 0.27, z + 1.32))
    caja(bm, tuple(c), (0.2, 0.2, 0.26), mat=1, bisel=0.02, segs=1)                             # vidrio que brilla
    for sx in (-1, 1):
        for sy in (-1, 1):
            loft(bm, [tuple(c + Vector((sx * 0.1, sy * 0.1, -0.14))), tuple(c + Vector((sx * 0.1, sy * 0.1, 0.14)))], [(0.012, 0.012)] * 2,
                 mat=0, segs=6, sub=1, domo=0.0)
    loft(bm, [tuple(c + Vector((0, 0, 0.13))), tuple(c + Vector((0, 0, 0.26)))], [(0.17, 0.17), (0.02, 0.02)], mat=0, segs=4, sub=1, domo=0.0)  # techito
    loft(bm, [tuple(c + Vector((0, 0, 0.16))), tuple(c + Vector((0, 0, 0.22)))], [(0.15, 0.15), (0.05, 0.05)], mat=2, segs=8, sub=1, domo=0.3)  # nieve
    esfera(bm, tuple(c + Vector((0, 0, -0.2))), (0.07, 0.07, 0.05), mat=0, segs=8, anillos=5)
    return c

def crear_farolitos():
    for o in [o for o in COL.objects if o.name.startswith("Farolito_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    n = 0
    for c, pts in RUTAS:
        paso = 4
        for k in range(1, len(pts) - 1, paso):
            a = pts[min(k + 1, len(pts) - 1)] - pts[k - 1]; a.normalize()
            lado = 1 if (k // paso) % 2 == 0 else -1
            q = pts[k] + Vector((-a.y, a.x)) * 1.35 * lado
            b = B(q.x, q.y); b.z = altura(b)
            o = objeto(f"Farolito_{n:02d}", lambda bm, b=b: FAROLITOS.append((farolito(bm, (0, 0, 0)) + b, c.name)), [M_POSTE, M_LUZ, M_NIEVEB])
            o.location = b
            o.rotation_euler.z = math.atan2(-a.y, -a.x) * 0 + rnd.uniform(-0.3, 0.3)
            n += 1
    return n

def foco(bm, p, k, s=1.0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.05 * s)
    for v in res["verts"]: v.co = Vector((v.co.x, v.co.y, v.co.z * 1.3)) + p
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = k % 4; f.smooth = True

def cable(bm, a, b, colgado=0.35, cada=0.32, k0=0):
    """Cable colgando (catenaria aproximada) de a a b con focos."""
    L = (b - a).length; n = max(2, int(L / 0.15))
    pts = [a.lerp(b, i / n) - Vector((0, 0, colgado * math.sin(math.pi * i / n))) for i in range(n + 1)]
    loft(bm, [tuple(p) for p in pts], [(0.008, 0.008)] * len(pts), mat=4, segs=4, sub=1, domo=0.0)
    acum, k = 0.0, k0
    for p0, p1 in zip(pts, pts[1:]):
        acum += (p1 - p0).length
        if acum >= cada:
            acum = 0; foco(bm, p1 - Vector((0, 0, 0.06)), k); k += 1
    return k

def aleros(bm):
    k = 0
    for c in CASAS:
        me = c.data
        techo = [i for i, s in enumerate(c.material_slots) if s.material and s.material.name.startswith("Ext_Tejado")]
        vs = {v for p in me.polygons if p.material_index in techo for v in p.vertices}
        cos = [me.vertices[i].co for i in vs]
        zmin = min(v.z for v in cos)
        bajos = [v for v in cos if v.z < zmin + 0.25]
        xs = [v.x for v in bajos]; ys = [v.y for v in bajos]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        M = c.matrix_world
        if (x1 - x0) >= (y1 - y0):
            lineas = [(Vector((x0, y, zmin - 0.08)), Vector((x1, y, zmin - 0.08))) for y in (y0, y1)]
        else:
            lineas = [(Vector((x, y0, zmin - 0.08)), Vector((x, y1, zmin - 0.08))) for x in (x0, x1)]
        for a, b in lineas:
            a, b = M @ a, M @ b
            tramos = max(1, int((b - a).length / 1.6))
            for t in range(tramos):
                k = cable(bm, a.lerp(b, t / tramos), a.lerp(b, (t + 1) / tramos), colgado=0.22, cada=0.3, k0=k)
    return k

def entre_farolitos(bm):
    k = 0
    por_casa = {}
    for p, casa in FAROLITOS: por_casa.setdefault(casa, []).append(p)
    for casa, ps in por_casa.items():
        for a, b in zip(ps, ps[1:]):
            k = cable(bm, a + Vector((0, 0, 0.25)), b + Vector((0, 0, 0.25)), colgado=0.6, cada=0.35, k0=k)
    return k

def pinos_con_luces(bm, cuantos=10):
    # pinos más cercanos a los senderos (fuera del patio)
    pts = [B(q.x, q.y) for _, r in RUTAS for q in r[::4]]
    pinos = []
    for o in bpy.data.objects:
        if not o.name.startswith("Pino_"): continue
        d = min((o.location.xy - p.xy).length for p in pts)
        if 3.0 < d < 9.0 and o.dimensions.z < 12: pinos.append((d, o))
    pinos.sort(key=lambda t: t[0])
    elegidos = []
    for d, o in pinos:
        if all((o.location - e.location).length > 8 for e in elegidos): elegidos.append(o)
        if len(elegidos) >= cuantos: break
    k = 0
    for o in elegidos:
        bvh = bvh_obj(o)
        base = o.location; H = o.dimensions.z
        vueltas = 4.0; n = 220
        prev = None
        for i in range(n + 1):
            t = i / n
            a = t * vueltas * 2 * math.pi
            z = base.z + H * (0.12 + 0.78 * t)
            d = Vector((math.cos(a), math.sin(a), 0))
            hit = bvh.ray_cast(Vector((base.x, base.y, z)) + d * 20, -d)
            if hit[0] is None: continue
            p = hit[0] + d * 0.06
            if prev is not None:
                loft(bm, [tuple(prev), tuple(p)], [(0.012, 0.012)] * 2, mat=4, segs=4, sub=1, domo=0.0)
            if i % 4 == 0: foco(bm, p, k, 1.6); k += 1
            prev = p
    return k, [o.name for o in elegidos]

def coronas(bm):
    for c in CASAS:
        # la puerta mira hacia el sendero: ponemos la corona en la pared del lado del sendero, a 2.1 m
        ux, uz = -c.location.x, -c.location.y
        hacia = (Vector((4.0, 0.0)) - Vector((ux, uz))).normalized()
        me = c.data; M = c.matrix_world
        bvh = bvh_obj(c)
        origen = c.location + Vector((-hacia.x, -hacia.y, 0)) * 12 + Vector((0, 0, 2.0))
        hit = bvh.ray_cast(origen, -Vector((-hacia.x, -hacia.y, 0)))
        if hit[0] is None: continue
        p = hit[0] + hit[1] * 0.08
        n = hit[1]
        rot = n.to_track_quat("Y", "Z").to_matrix()
        anillo = []
        for j in range(14):
            a = 2 * math.pi * j / 14
            q = p + rot @ Vector((math.cos(a) * 0.32, 0, math.sin(a) * 0.32))
            esfera(bm, tuple(q), (0.1, 0.1, 0.1), mat=5, segs=8, anillos=6)
            if j % 3 == 0: esfera(bm, tuple(q + n * 0.08), (0.035, 0.035, 0.035), mat=0, segs=6, anillos=4)
        esfera(bm, tuple(p + rot @ Vector((0, 0.06, -0.3))), (0.09, 0.05, 0.07), mat=6, segs=8, anillos=6)    # moño

# ------------------------------------------------------------------ construir
o_mon = objeto("Montanas_v2", montanas, [M_ROCA, M_NIEVE])
o_sen = objeto("Senderos", senderos, [M_SENDERO])
n_far = crear_farolitos()
def luces(bm):
    global INFO
    k1 = entre_farolitos(bm); k2 = aleros(bm); k3, nombres = pinos_con_luces(bm)
    INFO = (k1, k2, k3, nombres)
o_luz = objeto("LucesPueblo", luces, FOCOS + [M_CABLE])
o_cor = objeto("Coronas_Casas", coronas, [FOCOS[0], M_CABLE, M_CABLE, M_CABLE, M_CABLE, M_CORONA, M_MONO])
print("farolitos", n_far, "focos (farolitos, aleros, pinos)", INFO[:3], "pinos:", INFO[3])
