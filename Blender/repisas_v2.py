# -*- coding: utf-8 -*-
"""
REPISAS v2 (Fase 4): los juguetes de las 3 repisas (Repisa_Sur_A, Repisa_Sur_B, Repisa_Oeste) eran cajitas y cilindros.
El script:
  1. Separa la ESTRUCTURA (tablas, laterales y fondo de madera: islas grandes) de los JUGUETES (islas chicas).
  2. Junta las islas de cada juguete (mismo entrepaño y se enciman a lo largo de la repisa) y ADIVINA qué era
     por sus piezas: oso (Amb_CafeOso), tren (ruedas + chimenea), carrito (ruedas), soldadito (cuerpo rojo + Amb_Vela),
     regalo (listón amarillo delgado), pelota (esfera sola), cubos (lo demás).
  3. Borra los viejos y pone en el MISMO lugar y del MISMO tamaño un juguete nuevo redondeado, con sus colores.
     El frente de cada juguete mira hacia afuera de la repisa (lado contrario al fondo).
Uso: exec(modelado.py); exec(repisas_v2.py); hacer_repisas()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

MADERAS = {"Amb_Madera", "Amb_Madera2", "Amb_Madera3", "Amb_MaderaOscura"}

def _islas(bm):
    bm.faces.ensure_lookup_table(); vist = set(); res = []
    for f in bm.faces:
        if f.index in vist: continue
        pila = [f]; isla = []; vist.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vist: vist.add(y.index); pila.append(y)
        res.append(isla)
    return res

def _caja(isla):
    vs = [v.co for f in isla for v in f.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi

# ------------------------------------------------------------------ juguetes (coords locales: x a lo largo,
# -y = frente, z arriba, base en z=0, centrados en x=y=0). m(nombre) -> índice de material.
def oso(bm, w, d, h, m, rnd):
    s = min(w / 0.3, d / 0.26, h / 0.6)
    C, B, N, R = m("Amb_CafeOso"), m("Amb_Blanco"), m("Amb_Negro"), m("Amb_Rojo")
    esfera(bm, (0, 0, 0.17 * s), (0.12 * s, 0.1 * s, 0.15 * s), mat=C, segs=16, anillos=12)          # panza
    esfera(bm, (0, -0.07 * s, 0.16 * s), (0.075 * s, 0.04 * s, 0.09 * s), mat=B, segs=12, anillos=8)  # panza clara
    esfera(bm, (0, 0, 0.42 * s), (0.11 * s, 0.1 * s, 0.1 * s), mat=C, segs=16, anillos=12)           # cabeza
    esfera(bm, (0, -0.085 * s, 0.4 * s), (0.05 * s, 0.04 * s, 0.038 * s), mat=B, segs=12, anillos=8)  # trompita
    esfera(bm, (0, -0.122 * s, 0.415 * s), (0.018 * s, 0.012 * s, 0.013 * s), mat=N, segs=8, anillos=6)
    for x in (-1, 1):
        esfera(bm, (x * 0.04 * s, -0.09 * s, 0.45 * s), (0.013 * s, 0.01 * s, 0.015 * s), mat=N, segs=8, anillos=6)  # ojos
        esfera(bm, (x * 0.085 * s, 0, 0.51 * s), (0.04 * s, 0.025 * s, 0.04 * s), mat=C, segs=12, anillos=8)       # orejas
        esfera(bm, (x * 0.085 * s, -0.012 * s, 0.51 * s), (0.022 * s, 0.015 * s, 0.022 * s), mat=B, segs=8, anillos=6)
        loft(bm, [(x * 0.1 * s, -0.01 * s, 0.25 * s), (x * 0.13 * s, -0.05 * s, 0.17 * s)], [(0.035 * s, 0.035 * s)] * 2, mat=C, segs=10, sub=1)  # brazos
        esfera(bm, (x * 0.07 * s, -0.06 * s, 0.045 * s), (0.045 * s, 0.065 * s, 0.045 * s), mat=C, segs=12, anillos=8)    # patas
        esfera(bm, (x * 0.07 * s, -0.12 * s, 0.045 * s), (0.03 * s, 0.008 * s, 0.03 * s), mat=B, segs=10, anillos=6)
        loft(bm, [(0, -0.075 * s, 0.33 * s), (x * 0.05 * s, -0.085 * s, 0.35 * s), (x * 0.07 * s, -0.08 * s, 0.32 * s), (x * 0.03 * s, -0.08 * s, 0.32 * s)],
             [(0.018 * s, 0.01 * s)] * 4, mat=R, segs=6, sub=3)   # moño
    esfera(bm, (0, -0.08 * s, 0.33 * s), (0.018 * s, 0.014 * s, 0.018 * s), mat=R, segs=8, anillos=6)

def rueda(bm, p, r, ancho, mat, mat_tapa, eje="x"):
    a = Vector((ancho / 2, 0, 0))
    loft(bm, [p - a, p + a], [(r, r)] * 2, mat=mat, segs=16, sub=1, domo=0.25, arriba=Vector((0, 0, 1)))
    s = 1 if p.x > 0 else -1
    esfera(bm, tuple(p + Vector((s * ancho / 2, 0, 0))), (0.01, r * 0.45, r * 0.45), mat=mat_tapa, segs=12, anillos=6)

def carrito(bm, w, d, h, m, rnd, color):
    # mira de lado: largo a lo largo de la repisa (x)
    N, A, B = m("Amb_Negro"), m("Amb_Amarillo"), m("Amb_Blanco")
    r = min(0.06, h * 0.25)
    caja(bm, (0, 0, r + 0.06), (w * 0.95, d * 0.8, 0.11), mat=color, bisel=0.03, segs=3)
    caja(bm, (-w * 0.12, 0, r + 0.16), (w * 0.45, d * 0.7, 0.12), mat=color, bisel=0.035, segs=3)    # cabina
    for sx in (-1, 1):
        caja(bm, (-w * 0.12 + sx * 0.0, -d * 0.36, r + 0.165), (w * 0.34, 0.01, 0.07), mat=B, bisel=0.008)   # ventana
    esfera(bm, (w * 0.47, -d * 0.25, r + 0.07), (0.012, 0.025, 0.02), mat=A, segs=8, anillos=6)              # faro
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Vector((sx * w * 0.3, sy * d * 0.42, r))
            loft(bm, [p - Vector((0, 0.02, 0)), p + Vector((0, 0.02, 0))], [(r, r)] * 2, mat=N, segs=16, sub=1, domo=0.3)
            esfera(bm, tuple(p + Vector((0, sy * 0.022, 0))), (r * 0.45, 0.01, r * 0.45), mat=A, segs=12, anillos=6)

def tren(bm, w, d, h, m, rnd, color):
    N, A, R = m("Amb_Negro"), m("Amb_Amarillo"), m("Amb_Rojo")
    r = min(0.055, h * 0.15)
    caja(bm, (0, 0, r + 0.03), (w * 0.95, d * 0.75, 0.06), mat=N, bisel=0.015)                          # chasis
    loft(bm, [(w * 0.45, 0, r + 0.12), (-w * 0.05, 0, r + 0.12)], [(0.07, 0.075)] * 2, mat=color, segs=16, sub=1, domo=0.15)  # caldera
    for xx in (w * 0.3, w * 0.1):
        loft(bm, [(xx - 0.008, 0, r + 0.12), (xx + 0.008, 0, r + 0.12)], [(0.08, 0.085)] * 2, mat=A, segs=16, sub=1, domo=0.0)
    caja(bm, (-w * 0.28, 0, r + 0.15), (w * 0.38, d * 0.75, 0.18), mat=color, bisel=0.025, segs=3)       # cabina
    caja(bm, (-w * 0.28, 0, r + 0.255), (w * 0.44, d * 0.85, 0.03), mat=R, bisel=0.012)                  # techo
    loft(bm, [(w * 0.33, 0, r + 0.17), (w * 0.33, 0, h - 0.04), (w * 0.33, 0, h)], [(0.025, 0.025), (0.03, 0.03), (0.045, 0.045)], mat=N, segs=12, sub=2, domo=0.2)  # chimenea
    esfera(bm, (w * 0.47, 0, r + 0.12), (0.012, 0.03, 0.03), mat=A, segs=10, anillos=6)                    # faro
    for sx in (-0.32, 0.0, 0.32):
        for sy in (-1, 1):
            p = Vector((sx * w, sy * d * 0.4, r))
            loft(bm, [p - Vector((0, 0.015, 0)), p + Vector((0, 0.015, 0))], [(r, r)] * 2, mat=R, segs=16, sub=1, domo=0.3)
            esfera(bm, tuple(p + Vector((0, sy * 0.017, 0))), (r * 0.4, 0.008, r * 0.4), mat=A, segs=10, anillos=6)

def soldadito(bm, w, d, h, m, rnd):
    R, V, N, B, A, Az = m("Amb_Rojo"), m("Amb_Vela"), m("Amb_Negro"), m("Amb_Blanco"), m("Amb_Amarillo"), m("Amb_Azul")
    s = h / 0.58; rr = min(w, d) * 0.5
    loft(bm, [(0, 0, 0), (0, 0, 0.02 * s)], [(rr, rr)] * 2, mat=m("Amb_Madera2"), segs=16, sub=1, domo=0.1)       # base
    for x in (-1, 1):
        loft(bm, [(x * 0.025 * s, 0, 0.02 * s), (x * 0.025 * s, 0, 0.15 * s)], [(0.022 * s, 0.022 * s)] * 2, mat=Az, segs=10, sub=1, domo=0.3)
        esfera(bm, (x * 0.025 * s, -0.008 * s, 0.03 * s), (0.025 * s, 0.035 * s, 0.02 * s), mat=N, segs=10, anillos=6)
    loft(bm, [(0, 0, 0.14 * s), (0, 0, 0.24 * s), (0, 0, 0.3 * s)], [(0.05 * s, 0.045 * s), (0.052 * s, 0.047 * s), (0.045 * s, 0.04 * s)], mat=R, segs=14, sub=2, domo=0.35)
    loft(bm, [(0, 0, 0.15 * s), (0, 0, 0.165 * s)], [(0.053 * s, 0.048 * s)] * 2, mat=B, segs=14, sub=1, domo=0.0)  # cinturón
    for z in (0.2, 0.235, 0.27):
        esfera(bm, (0, -0.046 * s, z * s), (0.007 * s, 0.005 * s, 0.007 * s), mat=A, segs=6, anillos=4)
    for x in (-1, 1):
        loft(bm, [(x * 0.058 * s, 0, 0.29 * s), (x * 0.062 * s, -0.005 * s, 0.2 * s)], [(0.016 * s, 0.016 * s)] * 2, mat=R, segs=8, sub=1, domo=0.6)
        esfera(bm, (x * 0.062 * s, -0.006 * s, 0.19 * s), (0.016 * s, 0.016 * s, 0.016 * s), mat=B, segs=8, anillos=6)
        esfera(bm, (x * 0.055 * s, 0, 0.3 * s), (0.025 * s, 0.022 * s, 0.01 * s), mat=A, segs=10, anillos=4)        # charretera
    esfera(bm, (0, 0, 0.345 * s), (0.045 * s, 0.043 * s, 0.05 * s), mat=V, segs=14, anillos=10)                     # cabeza
    for x in (-1, 1):
        esfera(bm, (x * 0.017 * s, -0.04 * s, 0.355 * s), (0.006 * s, 0.004 * s, 0.007 * s), mat=N, segs=6, anillos=4)
        esfera(bm, (x * 0.028 * s, -0.035 * s, 0.335 * s), (0.009 * s, 0.004 * s, 0.006 * s), mat=R, segs=6, anillos=4)
    loft(bm, [(0, 0, 0.37 * s), (0, 0, 0.47 * s)], [(0.044 * s, 0.042 * s), (0.048 * s, 0.046 * s)], mat=N, segs=14, sub=1, domo=0.15)  # gorro alto
    esfera(bm, (0, -0.045 * s, 0.42 * s), (0.014 * s, 0.005 * s, 0.014 * s), mat=A, segs=8, anillos=6)
    esfera(bm, (0, 0, 0.49 * s), (0.016 * s, 0.016 * s, 0.022 * s), mat=R, segs=8, anillos=6)

def regalo(bm, w, d, h, m, rnd, papel, liston):
    caja(bm, (0, 0, h * 0.42), (w * 0.95, d * 0.95, h * 0.84), mat=papel, bisel=0.02, segs=3)
    caja(bm, (0, 0, h * 0.85), (w * 1.0, d * 1.0, h * 0.1), mat=papel, bisel=0.015, segs=2)          # tapa
    caja(bm, (0, 0, h * 0.45), (w * 0.14, d * 1.02, h * 0.92), mat=liston, bisel=0.006)
    caja(bm, (0, 0, h * 0.45), (w * 1.02, d * 0.14, h * 0.92), mat=liston, bisel=0.006)
    b = min(w, d) * 0.22
    for sx in (-1, 1):
        loft(bm, [(0, 0, h * 0.9), (sx * b, -b * 0.3, h * 0.9 + b * 0.8), (sx * b * 1.4, 0, h * 0.9 + b * 0.3), (sx * b * 0.3, 0, h * 0.9)],
             [(b * 0.35, b * 0.12)] * 4, mat=liston, segs=8, sub=3)
    esfera(bm, (0, 0, h * 0.92), (b * 0.25, b * 0.25, b * 0.2), mat=liston, segs=10, anillos=6)

def pelota(bm, w, d, h, m, rnd, c1, c2):
    r = min(w, d, h) * 0.5
    # gajos de dos colores (como pelota de playa)
    tmp = bmesh.new()
    res = bmesh.ops.create_uvsphere(tmp, u_segments=24, v_segments=14, radius=r)
    for f in tmp.faces:
        c = f.calc_center_median()
        a = math.atan2(c.y, c.x)
        f.material_index = c1 if int((a + math.pi) / (2 * math.pi) * 6) % 2 == 0 else c2
        f.smooth = True
    bmesh.ops.translate(tmp, verts=tmp.verts, vec=Vector((0, 0, r)))
    me = bpy.data.meshes.new("_tmp"); tmp.to_mesh(me); tmp.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bm.faces.ensure_lookup_table()

def cubos(bm, w, d, h, m, rnd, colores):
    # torre de cubitos con letras en relieve
    n = max(1, min(3, int(round(h / max(0.12, min(w, d) * 0.9)))))
    t = min(w, d, h / n) * 0.92
    for k in range(n):
        c = colores[k % len(colores)]
        g = Matrix.Rotation(rnd.uniform(-0.3, 0.3), 3, "Z")
        caja(bm, (0, 0, t * (k + 0.5)), (t, t, t), mat=c, bisel=t * 0.12, segs=2, giro=g)
        # marco blanco en las 4 caras de los lados + cuadro de color adentro (cubo ABC)
        for tam_b, tam_c in (((t * 0.8, t * 1.02, t * 0.8), (t * 0.62, t * 1.04, t * 0.62)),
                             ((t * 1.02, t * 0.8, t * 0.8), (t * 1.04, t * 0.62, t * 0.62))):
            caja(bm, (0, 0, t * (k + 0.5)), tam_b, mat=m("Amb_Blanco"), bisel=0.006, giro=g)
            caja(bm, (0, 0, t * (k + 0.5)), tam_c, mat=colores[(k + 1) % len(colores)] if len(colores) > 1 else m("Amb_Rojo") if c != m("Amb_Rojo") else m("Amb_Azul"), bisel=0.005, giro=g)

# ------------------------------------------------------------------ repisa
def hacer_repisa(nombre, semilla):
    o = bpy.data.objects[nombre]; me = o.data
    rnd = random.Random(semilla)
    bm = bmesh.new(); bm.from_mesh(me)
    nombres = [mt.name for mt in me.materials]
    def m(n):
        if n not in nombres:
            me.materials.append(bpy.data.materials[n]); nombres.append(n)
        return nombres.index(n)
    islas = _islas(bm)
    info = []
    for isla in islas:
        lo, hi = _caja(isla)
        mats = {nombres[f.material_index] for f in isla}
        tam = hi - lo
        estructura = max(tam.x, tam.y) > 0.7 and mats <= MADERAS
        info.append((isla, lo, hi, mats, estructura))
    est = [i for i in info if i[4]]
    lo_t = Vector((min(i[1].x for i in est), min(i[1].y for i in est), 0)); hi_t = Vector((max(i[2].x for i in est), max(i[2].y for i in est), 0))
    a_lo_largo = Vector((1, 0, 0)) if hi_t.x - lo_t.x > hi_t.y - lo_t.y else Vector((0, 1, 0))
    centro = (lo_t + hi_t) / 2
    # fondo: tabla alta y delgada a lo largo
    fondo = [i for i in est if (i[2] - i[1]).z > 2 and (i[2] - i[1]).dot(a_lo_largo) > 3][0]
    cf = (fondo[1] + fondo[2]) / 2
    frente = Vector((centro.x - cf.x, centro.y - cf.y, 0)) * Vector((1 - abs(a_lo_largo.x), 1 - abs(a_lo_largo.y), 0))
    frente.normalize()
    tablas = sorted({round(i[2].z, 3) for i in est if (i[2] - i[1]).z < 0.12})
    # agrupar juguetes por entrepaño y por traslape a lo largo
    jug = [i for i in info if not i[4]]
    grupos = []
    def tabla_de(i): return max([t for t in tablas if t <= i[1].z + 0.03] or [0])
    for i in sorted(jug, key=lambda i: (tabla_de(i), min(i[1].dot(a_lo_largo), i[2].dot(a_lo_largo)))):
        tabla = tabla_de(i)
        a0, a1 = sorted((i[1].dot(a_lo_largo), i[2].dot(a_lo_largo)))
        g = grupos[-1] if grupos else None
        if g and g["tabla"] == tabla and a0 < g["a1"] - 0.005:          # mezcla de intervalos (ordenados)
            g["islas"].append(i); g["a1"] = max(g["a1"], a1)
        else:
            grupos.append({"tabla": tabla, "islas": [i], "a0": a0, "a1": a1})
    borrar = [f for i in jug for f in i[0]]
    bmesh.ops.delete(bm, geom=borrar, context="FACES")
    cuenta = {}
    for g in grupos:
        lo = Vector((min(i[1].x for i in g["islas"]), min(i[1].y for i in g["islas"]), min(i[1].z for i in g["islas"])))
        hi = Vector((max(i[2].x for i in g["islas"]), max(i[2].y for i in g["islas"]), max(i[2].z for i in g["islas"])))
        tam = hi - lo
        w = abs(tam.dot(a_lo_largo)); d = abs(tam.dot(frente)); h = hi.z - g["tabla"]
        mats = set().union(*[i[3] for i in g["islas"]])
        caras = [len(i[0]) for i in g["islas"]]
        colores = [nombres.index(n) for i in g["islas"] for n in i[3] if n not in MADERAS | {"Amb_Negro", "Amb_Vela", "Amb_Blanco"}]
        color = colores[0] if colores else m("Amb_Rojo")
        ruedas = sum(1 for i in g["islas"] if len(i[0]) == 106 and i[3] == {"Amb_Negro"})
        if "Amb_CafeOso" in mats: tipo = "oso"
        elif ruedas >= 4 and any(len(i[0]) == 80 and i[3] == {"Amb_Negro"} for i in g["islas"]): tipo = "tren"
        elif ruedas >= 4: tipo = "carrito"
        elif "Amb_Vela" in mats and "Amb_Rojo" in mats: tipo = "soldado"
        elif len(g["islas"]) == 1 and caras[0] == 80: tipo = "pelota"
        elif len(g["islas"]) == 2 and any(abs((i[2] - i[1]).dot(frente)) < 0.08 or abs((i[2] - i[1]).dot(a_lo_largo)) < 0.08 for i in g["islas"]): tipo = "regalo"
        else: tipo = "cubos"
        cuenta[tipo] = cuenta.get(tipo, 0) + 1
        nuevo = bmesh.new()
        if tipo == "oso": oso(nuevo, w, d, h, m, rnd)
        elif tipo == "tren": tren(nuevo, w, d, h, m, rnd, color)
        elif tipo == "carrito": carrito(nuevo, w, d, h, m, rnd, color)
        elif tipo == "soldado": soldadito(nuevo, w, d, h, m, rnd)
        elif tipo == "pelota": pelota(nuevo, w, d, h, m, rnd, color, m("Amb_Blanco"))
        elif tipo == "regalo":
            papel = max(g["islas"], key=lambda i: (i[2] - i[1]).length)[3]; papel = nombres.index(sorted(papel)[0])
            liston = [nombres.index(sorted(i[3])[0]) for i in g["islas"] if nombres.index(sorted(i[3])[0]) != papel]
            li = liston[0] if liston else m("Amb_Amarillo")
            if li == papel: li = m("Amb_Amarillo") if papel != m("Amb_Amarillo") else m("Amb_Rojo")
            regalo(nuevo, w, d, h, m, rnd, papel, li)
        else: cubos(nuevo, w, d, h, m, rnd, list(dict.fromkeys(colores)) or [color])
        # local (x a lo largo, -y frente, z) -> repisa
        lado = a_lo_largo; atras = -frente
        R = Matrix(((lado.x, atras.x, 0), (lado.y, atras.y, 0), (0, 0, 1)))
        c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, g["tabla"]))
        bmesh.ops.transform(nuevo, matrix=Matrix.Translation(c) @ R.to_4x4(), verts=list(nuevo.verts))
        for f in nuevo.faces: f.smooth = True
        tmp = bpy.data.meshes.new("_tmp"); nuevo.to_mesh(tmp); nuevo.free(); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    bm.to_mesh(me); bm.free(); me.update()
    print(nombre, "juguetes:", cuenta, "| tris", sum(len(p.vertices) - 2 for p in me.polygons))

def hacer_repisas():
    for k, n in enumerate(("Repisa_Sur_A", "Repisa_Sur_B", "Repisa_Oeste")):
        hacer_repisa(n, 40 + k)

def restaurar_repisas(blend=PROYECTO + "/Library/BlenderBackup/antes_repisas_v2.blend"):
    """Regresa la geometría original de las 3 repisas (para poder correr hacer_repisas() otra vez)."""
    nombres = ["Repisa_Sur_A", "Repisa_Sur_B", "Repisa_Oeste"]
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.meshes = list(nombres)
    for mm in dst.meshes:
        tgt = bpy.data.objects[mm.name.rsplit(".", 1)[0]].data
        bm = bmesh.new(); bm.from_mesh(mm)
        viejos = [x.name.rsplit(".", 1)[0] if x.name.rsplit(".", 1)[-1].isdigit() else x.name for x in mm.materials]
        tn = [x.name for x in tgt.materials]
        for nm in viejos:
            if nm not in tn: tgt.materials.append(bpy.data.materials[nm]); tn.append(nm)
        for f in bm.faces: f.material_index = tn.index(viejos[f.material_index])
        bm.to_mesh(tgt); bm.free(); tgt.update()
        bpy.data.meshes.remove(mm)
    for mt in [x for x in bpy.data.materials if x.users == 0 and x.name.rsplit(".", 1)[-1].isdigit()]: bpy.data.materials.remove(mt)
