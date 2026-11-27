# -*- coding: utf-8 -*-
"""
CABAÑA DE TRONCOS v3 (26-nov): malla "CasaTroncos" rehecha COMPLETA en low-poly redondeado y con más detalle.
Coordenadas locales de la casa: frente = +Y, suelo = z 0. Se respetan las posiciones de lo que depende de la casa:
  - puerta en x -0.5..0.5 con su cara en y≈2.66 (la CORONA de Coronas_Casas se ancla en (0, 2.685, 1.91));
  - chimenea centrada en (-1.8, -0.9) con la boca en z 6.0 (de ahí sale el humo de Unity);
  - caja de paredes ±2.9 x ±2.7 (NieveCasas usa la prop "nieve_pie"); porche hasta y 4.15; leña a la derecha atrás.
Partes: cimiento de piedras facetadas, paredes de troncos de 8 lados cruzados en las esquinas (cortes con anillos),
recortadas alrededor de puerta/ventanas y siguiendo en los hastiales; techo de tejas escalonadas + tablas de orilla
+ ALMOHADA de nieve (rejilla con grosor que se adelgaza en las orillas, se dobla en el alero, cumbrera redonda),
grumos y carámbanos; porche (piso de tablas, escalones, postes de tronco, barandal, techito con nieve); puerta de
tablas con refuerzo en Z, manija y farolito; ventanas con marco, cruz, repisa nevada, postigos y jardinera;
ojo de buey en los hastiales; chimenea de piedras; leña apilada; tocón con hacha. TODO con sombreado plano.
Uso: exec(modelado.py); exec(casa_troncos_v3.py); hacer_casa_troncos()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise

MATS = ["Amb_Piedra2", "Amb_Piedra", "Ext_Tronco2", "Ext_Tronco", "Ext_CorteLena", "Ext_AnilloLena",
        "Amb_MaderaOscura", "Amb_Madera2", "Amb_Madera", "Ext_Tejado", "Ext_NieveBrillo", "Ext_Hielo",
        "Ext_PinturaRoja", "Ext_PinturaVerde", "Amb_Laton", "Ext_VentanaCalida", "Ext_LuzFarol",
        "Ext_MetalNegro", "Ext_PinoD", "Amb_Rojo"]
M = {n: i for i, n in enumerate(MATS)}

# medidas
WC, DC, R = 2.73, 2.53, 0.17          # centro de los troncos de pared (x, y) y radio => cara exterior ±2.9 / ±2.7
Z0, PASO = 0.32, 0.31                 # arriba del cimiento; distancia entre troncos (se enciman un poco)
ALERO = 3.0                           # arriba de las paredes del frente/atrás
CUMBRE, PEND = 5.0, 0.711             # z de la cumbrera (y = 0) y pendiente del techo
XT, YT = 3.6, 3.25                    # vuelo del techo (x) y alero (y)
PUERTA = (-0.55, 0.55, Z0, 2.38)
VENT_FRENTE = [(1.4, 2.4), (-2.4, -1.4)]
VENT_Z = (1.28, 2.22)
CHIM = (-1.8, -0.9, 0.4)              # centro x, y, medio lado

def z_techo(y):
    return CUMBRE - PEND * abs(y)

# ------------------------------------------------------------------ piezas básicas
def prisma(bm, base, arriba, mat):
    """Prisma de 4 lados: base = 4 vértices (en orden), arriba = vector de grosor."""
    a = [bm.verts.new(p) for p in base]; b = [bm.verts.new(p + arriba) for p in base]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    for i in range(4):
        fs.append(bm.faces.new((a[i], a[(i + 1) % 4], b[(i + 1) % 4], b[i])))
    for f in fs: f.material_index = mat
    return fs

def tabla(bm, c, tam, mat, bisel=0.012, giro=None):
    caja(bm, c, tam, mat=mat, bisel=bisel, segs=1, giro=giro)

def piedra(bm, c, tam, mat, rnd):
    """Piedra facetada redondita: casco convexo de puntos sobre un elipsoide (poco ruido => sin picos)."""
    vs = []; g0 = rnd.uniform(0, 6.28)
    tam = (tam[0] * rnd.uniform(0.8, 1.1), tam[1] * rnd.uniform(0.8, 1.1), tam[2] * rnd.uniform(0.85, 1.05))
    for i in range(12):
        z = -1 + 2 * (i + 0.5) / 12; r = math.sqrt(1 - z * z); a = g0 + i * 2.39996 + rnd.uniform(-0.4, 0.4)
        k = rnd.uniform(0.78, 1.0)
        vs.append(bm.verts.new(Vector(c) + Vector((math.cos(a) * r * k * tam[0] / 2, math.sin(a) * r * k * tam[1] / 2, z * 0.92 * tam[2] / 2))))
    res = bmesh.ops.convex_hull(bm, input=vs)
    sueltos = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if sueltos: bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    for g in res["geom"]:
        if isinstance(g, bmesh.types.BMFace): g.material_index = mat

def tronco(bm, p0, p1, r, rnd, corteza=None, lados=8, cortes=True):
    """Tronco de 'lados' caras con orilla biselada; en las puntas, corte con anillos."""
    corteza = M["Ext_Tronco2"] if corteza is None else corteza
    eje = p1 - p0; L = eje.length; d = eje.normalized()
    rot = d.to_track_quat("Z", "Y").to_matrix()
    giro = rnd.uniform(0, 6.28)
    radios = [r * rnd.uniform(0.95, 1.05) for _ in range(lados)]
    def anillo(t, k):
        return [bm.verts.new(p0 + d * t * L + rot @ Vector((math.cos(giro + 6.2832 * j / lados) * radios[j] * k,
                                                             math.sin(giro + 6.2832 * j / lados) * radios[j] * k, 0)))
                for j in range(lados)]
    b = min(0.03 / max(L, 0.1), 0.2)
    filas = [anillo(0, 0.9), anillo(b, 1.0), anillo(1 - b, 1.0), anillo(1, 0.9)]
    osc = {j for j in range(lados) if rnd.random() < 0.3}
    for a, c in zip(filas, filas[1:]):
        for j in range(lados):
            f = bm.faces.new((a[j], a[(j + 1) % lados], c[(j + 1) % lados], c[j]))
            f.material_index = M["Ext_Tronco"] if j in osc else corteza
    for fila, signo, t in ((filas[0], -1, 0.0), (filas[-1], 1, 1.0)):
        prev = fila
        anillos = ((0.8, M["Ext_CorteLena"]), (0.62, M["Ext_AnilloLena"]), (0.55, M["Ext_CorteLena"]), (0.25, M["Ext_AnilloLena"])) if cortes else ()
        for k, mat in anillos:
            nueva = anillo(t, k)
            for j in range(lados):
                vs = (prev[j], prev[(j + 1) % lados], nueva[(j + 1) % lados], nueva[j])
                f = bm.faces.new(vs if signo > 0 else tuple(reversed(vs))); f.material_index = mat
            prev = nueva
        cen = bm.verts.new(p0 + d * t * L)
        for j in range(lados):
            vs = (prev[j], prev[(j + 1) % lados], cen)
            f = bm.faces.new(vs if signo > 0 else tuple(reversed(vs))); f.material_index = M["Ext_CorteLena"] if cortes else corteza

def bola(bm, c, rad, mat, sub=1, rnd=None):
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in res["verts"]:
        k = 1 + (rnd.uniform(-0.12, 0.12) if rnd else 0)
        v.co = Vector(c) + Vector((v.co.x * rad[0] * k, v.co.y * rad[1] * k, v.co.z * rad[2] * k))
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mat

def carambano(bm, p, largo, r=0.035):
    lados = 5
    a = [bm.verts.new(p + Vector((math.cos(6.2832 * j / lados) * r, math.sin(6.2832 * j / lados) * r, 0))) for j in range(lados)]
    m = [bm.verts.new(p + Vector((math.cos(6.2832 * j / lados + 0.6) * r * 0.55, math.sin(6.2832 * j / lados + 0.6) * r * 0.55, -largo * 0.45))) for j in range(lados)]
    t = bm.verts.new(p + Vector((0, 0, -largo)))
    for j in range(lados):
        k = (j + 1) % lados
        bm.faces.new((a[k], a[j], m[j], m[k])).material_index = M["Ext_Hielo"]
        bm.faces.new((m[k], m[j], t)).material_index = M["Ext_Hielo"]
    bm.faces.new(a).material_index = M["Ext_Hielo"]

# ------------------------------------------------------------------ techo (agua) + nieve
def agua(bm, x0, x1, y_alto, z_alto, y_bajo, z_bajo, rnd, nieve=0.22, tejas=True, lateral=0.08, carambanos=True, semilla=0, hasta=None, margen=0.0):
    """Una agua del techo: tabla base + tejas escalonadas + almohada de nieve. Devuelve la orilla baja (para focos)."""
    dv = Vector((0, y_bajo - y_alto, z_bajo - z_alto))
    largo = dv.length; dvn = dv.normalized()
    n = Vector((1, 0, 0)).cross(dvn)
    if n.z < 0: n = -n
    P = lambda x, v: Vector((x, y_alto, z_alto)) + dv * v
    # tabla base
    prisma(bm, [P(x0, 0) - n * 0.12, P(x1, 0) - n * 0.12, P(x1, 1) - n * 0.12, P(x0, 1) - n * 0.12], n * 0.12, M["Amb_MaderaOscura"])
    # tejas: filas desde abajo, cada una un poco encima de la anterior, piezas de ~0.55 alternadas
    if tejas:
        filas = max(3, int(largo / 0.3))
        for i in range(filas):
            v0 = 1 - (i + 1) / filas; v1 = min(1.0, v0 + 1.35 / filas)
            x = x0 + (0.27 if i % 2 else 0.0) - 0.27
            while x < x1:
                xa, xb = max(x0, x + 0.015), min(x1, x + 0.55 - 0.015)
                if xb - xa > 0.08:
                    lev = n * (0.005 + 0.012 * rnd.random())
                    prisma(bm, [P(xa, v0) + lev, P(xb, v0) + lev, P(xb, v1) + lev, P(xa, v1) + lev], n * 0.045, M["Ext_Tejado"])
                x += 0.55
    # tablas de orilla en los extremos (hastiales)
    for x in (x0, x1):
        s = 1 if x == x1 else -1
        prisma(bm, [P(x, 0) - n * 0.16, P(x + s * 0.06, 0) - n * 0.16, P(x + s * 0.06, 1) - n * 0.16, P(x, 1) - n * 0.16], n * 0.26, M["Amb_MaderaOscura"])
    # ALMOHADA de nieve: rejilla nu x nv; grosor h(x, v) que se adelgaza en los extremos y se dobla en el alero
    if nieve:
        nu, nv = 28, (9 if hasta is None else max(9, int(largo * hasta / 0.45)))
        base = 0.07
        vuelo = 0.14 / largo
        lateral = lateral - margen
        off = Vector((semilla * 3.3, 1.7, 0))
        def h(u, v):
            x = x0 - lateral + (x1 - x0 + 2 * lateral) * u
            ex = min(u, 1 - u) * (x1 - x0 + 2 * lateral)
            borde = math.sqrt(min(1.0, ex / 0.28))
            if hasta is None:
                alero = math.sqrt(max(0.0, min(1.0, (1 + vuelo - v) / (vuelo + 0.12))))
            else:   # la nieve termina antes del alero con orilla ondulada (deja ver las tejas)
                hl = hasta - 0.1 * (0.5 + 0.5 * noise.noise(Vector((x * 1.7, 0.3, semilla)))) - 0.04 * (0.5 + 0.5 * math.sin(x * 4.1 + semilla))
                alero = math.sqrt(max(0.0, min(1.0, (hl - v) / 0.1)))
            g = nieve * borde * alero * (0.85 + 0.25 * noise.noise(Vector((x * 0.9, v * 3.0, 0)) + off))
            return x, g
        top, bot = [], []
        for i in range(nu + 1):
            ft, fb = [], []
            for j in range(nv + 1):
                u = i / nu; v = (j / nv) * ((1 + vuelo) if hasta is None else hasta)
                x, g = h(u, v)
                p = P(x, v) + n * base
                if hasta is not None and g < 0.06: p -= n * (0.06 - g) * 2.2   # se hunde bajo las tejas => orilla ondulada
                caida = max(0.0, v - 0.97) / (vuelo + 0.03)
                p -= Vector((0, 0, 0.12 * caida * caida))          # el alero se dobla hacia abajo
                ft.append(bm.verts.new(p + n * g)); fb.append(bm.verts.new(p))
            top.append(ft); bot.append(fb)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1])).material_index = M["Ext_NieveBrillo"]
                bm.faces.new((bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j], bot[i][j])).material_index = M["Ext_NieveBrillo"]
        borde = [(top[i][0], bot[i][0], top[i + 1][0], bot[i + 1][0]) for i in range(nu)] + \
                [(top[i + 1][nv], bot[i + 1][nv], top[i][nv], bot[i][nv]) for i in range(nu)] + \
                [(top[0][j + 1], bot[0][j + 1], top[0][j], bot[0][j]) for j in range(nv)] + \
                [(top[nu][j], bot[nu][j], top[nu][j + 1], bot[nu][j + 1]) for j in range(nv)]
        for a, b, c, d in borde:
            try: bm.faces.new((a, c, d, b)).material_index = M["Ext_NieveBrillo"]
            except ValueError: pass
        # grumos colgando del alero y carámbanos
        y_al, z_al = y_bajo + dvn.y * 0.14, z_bajo - 0.06
        x = x0 + 0.2
        while hasta is None and x < x1 - 0.1:
            if rnd.random() < 0.35:
                bola(bm, (x, y_al, z_al + 0.02), (0.12, 0.08, 0.07), M["Ext_NieveBrillo"], rnd=rnd)
            if carambanos and rnd.random() < 0.55:
                carambano(bm, Vector((x + rnd.uniform(-0.08, 0.08), y_al - dvn.y * 0.05, z_al)), rnd.uniform(0.12, 0.42))
            x += rnd.uniform(0.22, 0.4)
    return P

# ------------------------------------------------------------------ paredes de troncos
def huecos_frente():
    hs = [(PUERTA[0] - 0.1, PUERTA[1] + 0.1, PUERTA[2], PUERTA[3] + 0.12)]
    for a, b in VENT_FRENTE: hs.append((a - 0.1, b + 0.1, VENT_Z[0] - 0.12, VENT_Z[1] + 0.12))
    return hs

def fila_troncos(bm, eje, fijo, a0, a1, zc, huecos, rnd):
    """Tronco a lo largo de 'eje' ('x' o 'y') entre a0 y a1, partido donde cruce un hueco (puerta/ventana)."""
    tramos = [(a0, a1)]
    for h0, h1, hz0, hz1 in huecos:
        if zc + R * 0.7 < hz0 or zc - R * 0.7 > hz1: continue
        nuevos = []
        for t0, t1 in tramos:
            if h1 <= t0 or h0 >= t1: nuevos.append((t0, t1)); continue
            if h0 - t0 > 0.12: nuevos.append((t0, h0))
            if t1 - h1 > 0.12: nuevos.append((h1, t1))
        tramos = nuevos
    for t0, t1 in tramos:
        if eje == "x": p0, p1 = Vector((t0, fijo, zc)), Vector((t1, fijo, zc))
        else: p0, p1 = Vector((fijo, t0, zc)), Vector((fijo, t1, zc))
        tronco(bm, p0, p1, R * rnd.uniform(0.95, 1.04), rnd)

def paredes(bm, rnd):
    hf = huecos_frente()
    ha = [(-0.6, 0.6, VENT_Z[0] - 0.12, VENT_Z[1] + 0.12)]           # ventana de atrás
    hl = [(-0.55, 0.55, VENT_Z[0] - 0.12, VENT_Z[1] + 0.12)]          # ventana del lado izquierdo (x = -)
    k = 0
    while True:
        zc = Z0 + R + k * PASO
        if zc + R > ALERO + 0.05: break
        fila_troncos(bm, "x", DC, -WC - 0.3 + rnd.uniform(-0.05, 0.05), WC + 0.3 + rnd.uniform(-0.05, 0.05), zc, hf, rnd)
        fila_troncos(bm, "x", -DC, -WC - 0.3 + rnd.uniform(-0.05, 0.05), WC + 0.3 + rnd.uniform(-0.05, 0.05), zc, ha, rnd)
        k += 1
    # lados (y hastiales): medio paso más arriba; se acortan siguiendo el techo
    k = 0
    while True:
        zc = Z0 + R + PASO / 2 + k * PASO
        mitad = min(DC + 0.3, (z_techo(0) - 0.14 - (zc + R)) / PEND)
        if mitad < 0.25: break
        for x, hs in ((WC, []), (-WC, hl)):
            fila_troncos(bm, "y", x, -mitad + rnd.uniform(-0.04, 0.04), mitad + rnd.uniform(-0.04, 0.04), zc, hs, rnd)
        k += 1
    # viga de la cumbrera (asoma en los hastiales)
    tronco(bm, Vector((-XT + 0.15, 0, CUMBRE - 0.2)), Vector((XT - 0.15, 0, CUMBRE - 0.2)), 0.13, rnd)

def cimiento(bm, rnd):
    for (xa, ya), (xb, yb) in (((-2.85, -2.65), (2.85, -2.65)), ((2.85, -2.65), (2.85, 2.65)),
                               ((2.85, 2.65), (-2.85, 2.65)), ((-2.85, 2.65), (-2.85, -2.65))):
        L = math.hypot(xb - xa, yb - ya); n = int(L / 0.36)
        for i in range(n):
            t = (i + 0.5) / n
            for fila, (zc, alto) in enumerate(((0.09, 0.2), (0.25, 0.16))):
                tt = t + (0.5 / n if fila else 0)
                if tt > 1: continue
                c = (xa + (xb - xa) * tt, ya + (yb - ya) * tt, zc)
                piedra(bm, c, (0.4 if ya == yb else 0.3, 0.3 if ya == yb else 0.4, alto), M["Amb_Piedra2"] if rnd.random() < 0.7 else M["Amb_Piedra"], rnd)

# ------------------------------------------------------------------ puerta, ventanas, farol
def marco(bm, x0, x1, z0, z1, y, ancho=0.1, fondo=0.42, mat=None):
    mat = M["Amb_MaderaOscura"] if mat is None else mat
    for x in (x0 - ancho / 2, x1 + ancho / 2):
        tabla(bm, (x, y, (z0 + z1) / 2), (ancho, fondo, z1 - z0), mat)
    tabla(bm, ((x0 + x1) / 2, y, z1 + ancho / 2), (x1 - x0 + 2 * ancho + 0.08, fondo, ancho), mat)

def puerta(bm, rnd):
    x0, x1, z0, z1 = PUERTA
    marco(bm, x0, x1, z0, z1, DC)
    yP = 2.62
    n = 5; w = (x1 - x0) / n
    for i in range(n):
        tabla(bm, (x0 + w * (i + 0.5), yP, (z0 + z1) / 2), (w - 0.015, 0.08, z1 - z0 - 0.02), M["Ext_PinturaRoja"], bisel=0.008)
    for z in (z0 + 0.35, z1 - 0.35):
        tabla(bm, ((x0 + x1) / 2, yP + 0.05, z), (x1 - x0 - 0.12, 0.035, 0.12), M["Ext_PinturaRoja"], bisel=0.006)
    ang = math.atan2(z1 - z0 - 0.7, x1 - x0 - 0.2)
    tabla(bm, ((x0 + x1) / 2, yP + 0.05, (z0 + z1) / 2), (math.hypot(z1 - z0 - 0.7, x1 - x0 - 0.2), 0.035, 0.1),
          M["Ext_PinturaRoja"], bisel=0.006, giro=Matrix.Rotation(-ang, 3, "Y"))
    # manija de latón y bisagras
    bola(bm, (-0.38, yP + 0.09, 1.35), (0.04, 0.04, 0.04), M["Amb_Laton"])
    tabla(bm, (-0.38, yP + 0.05, 1.35), (0.05, 0.03, 0.16), M["Amb_Laton"], bisel=0.005)
    for z in (z0 + 0.35, z1 - 0.35):
        tabla(bm, (x1 - 0.18, yP + 0.075, z), (0.3, 0.02, 0.05), M["Ext_MetalNegro"], bisel=0.004)
    # tapete
    tabla(bm, (0, DC + 0.65, 0.565), (0.9, 0.55, 0.02), M["Amb_Rojo"], bisel=0.005)
    # farolito colgando del techo del porche (a un lado: la corona va en la puerta)
    c = Vector((1.0, 3.55, 1.98))
    for k in range(5):                                                   # cadenita
        tabla(bm, c + Vector((0, 0, 0.3 + k * 0.05)), (0.02, 0.02, 0.045), M["Ext_MetalNegro"], bisel=0.0)
    tabla(bm, c, (0.2, 0.2, 0.26), M["Ext_LuzFarol"], bisel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tabla(bm, c + Vector((sx * 0.1, sy * 0.1, 0)), (0.03, 0.03, 0.28), M["Ext_MetalNegro"], bisel=0.004)
    tabla(bm, c + Vector((0, 0, 0.16)), (0.28, 0.28, 0.04), M["Ext_MetalNegro"], bisel=0.006)
    tabla(bm, c + Vector((0, 0, 0.21)), (0.14, 0.14, 0.06), M["Ext_MetalNegro"], bisel=0.006)
    tabla(bm, c + Vector((0, 0, -0.15)), (0.24, 0.24, 0.04), M["Ext_MetalNegro"], bisel=0.006)

def ventana(bm, eje, fijo, a0, a1, rnd, hacia=1, postigos=True, jardinera=True):
    """Ventana en pared de normal (+/-) eje. a0..a1 sobre la pared, z VENT_Z."""
    z0, z1 = VENT_Z
    def P(a, z, prof):            # prof: hacia afuera de la pared
        return Vector((a, fijo + hacia * prof, z)) if eje == "x" else Vector((fijo + hacia * prof, a, z))
    def tam(a, z, prof):
        return (a, prof, z) if eje == "x" else (prof, a, z)
    am = (a0 + a1) / 2; zm = (z0 + z1) / 2; w = a1 - a0; h = z1 - z0
    tabla(bm, P(am, zm, 0.05), tam(w, h, 0.04), M["Ext_VentanaCalida"], bisel=0.0)
    # marco y cruz
    for a in (a0 - 0.045, a1 + 0.045):
        tabla(bm, P(a, zm, 0.12), tam(0.09, h + 0.18, 0.16), M["Amb_MaderaOscura"])
    for z in (z0 - 0.045, z1 + 0.045):
        tabla(bm, P(am, z, 0.12), tam(w + 0.18, 0.09, 0.16), M["Amb_MaderaOscura"])
    tabla(bm, P(am, zm, 0.09), tam(0.05, h, 0.05), M["Amb_MaderaOscura"])
    tabla(bm, P(am, zm, 0.09), tam(w, 0.05, 0.05), M["Amb_MaderaOscura"])
    # repisa con nieve
    tabla(bm, P(am, z0 - 0.12, 0.24), tam(w + 0.3, 0.06, 0.22), M["Amb_Madera"])
    bola(bm, P(am, z0 - 0.07, 0.25), tam((w + 0.22) / 2, 0.045, 0.1), M["Ext_NieveBrillo"], rnd=rnd)
    if postigos:
        for s, a in ((-1, a0 - 0.1 - w * 0.25), (1, a1 + 0.1 + w * 0.25)):
            tabla(bm, P(a, zm, 0.2), tam(w * 0.48, h + 0.12, 0.05), M["Ext_PinturaVerde"])
            for z in (z0 + 0.12, z1 - 0.12):
                tabla(bm, P(a, z, 0.235), tam(w * 0.42, 0.06, 0.025), M["Ext_PinturaVerde"], bisel=0.005)
            # arbolito calado (rombo oscuro) en el postigo
            tabla(bm, P(a, zm + 0.05, 0.228), tam(0.07, 0.07, 0.02), M["Amb_MaderaOscura"], bisel=0.0,
                  giro=Matrix.Rotation(math.pi / 4, 3, "Y" if eje == "x" else "X"))
    if jardinera:
        tabla(bm, P(am, z0 - 0.32, 0.33), tam(w + 0.1, 0.22, 0.2), M["Amb_Madera2"])
        bola(bm, P(am, z0 - 0.2, 0.33), tam((w + 0.04) / 2, 0.06, 0.1), M["Ext_NieveBrillo"], rnd=rnd)
        for k in range(6):   # ramitas de pino y bayas
            a = a0 + w * (k + 0.5) / 6
            bola(bm, P(a, z0 - 0.17, 0.33 + rnd.uniform(-0.05, 0.05)), tam(0.08, 0.07, 0.05), M["Ext_PinoD"], rnd=rnd)
            if k % 2: bola(bm, P(a + 0.03, z0 - 0.13, 0.4), (0.03, 0.03, 0.03), M["Amb_Rojo"])

def ojo_de_buey(bm, x, s):
    c = Vector((x + s * 0.02, 0, 3.95)); lados = 8
    for r0, r1, prof, mat in ((0.0, 0.26, 0.04, M["Ext_VentanaCalida"]), (0.26, 0.36, 0.1, M["Amb_MaderaOscura"])):
        for j in range(lados):
            a, b = 6.2832 * j / lados, 6.2832 * (j + 1) / lados
            pts = [Vector((0, math.cos(a) * r0, math.sin(a) * r0)), Vector((0, math.cos(b) * r0, math.sin(b) * r0)),
                   Vector((0, math.cos(b) * r1, math.sin(b) * r1)), Vector((0, math.cos(a) * r1, math.sin(a) * r1))]
            prisma(bm, [c + p for p in pts], Vector((s * prof, 0, 0)), mat)
    for ang in (0, math.pi / 2):
        tabla(bm, c + Vector((s * 0.05, 0, 0)), (0.04, 0.52, 0.04), M["Amb_MaderaOscura"], bisel=0.0, giro=Matrix.Rotation(ang, 3, "X"))

# ------------------------------------------------------------------ porche, chimenea, leña, tocón
def porche(bm, rnd):
    zp = 0.55; y0, y1 = 2.72, 4.15
    for i in range(8):                                   # tablas del piso (a lo largo de Y)
        x = -1.8 + 3.6 * (i + 0.5) / 8
        tabla(bm, (x, (y0 + y1) / 2, zp - 0.05), (3.6 / 8 - 0.025, y1 - y0, 0.1), M["Amb_Madera"], bisel=0.01)
    tabla(bm, (0, y1 - 0.05, zp - 0.2), (3.7, 0.14, 0.22), M["Amb_MaderaOscura"])          # viga del frente
    for x in (-1.65, 1.65, 0.0):
        piedra(bm, (x, y1 - 0.1, 0.17), (0.32, 0.32, 0.34), M["Amb_Piedra2"], rnd)        # bases de piedra
    for k, (y, z) in enumerate(((y1 + 0.25, 0.37), (y1 + 0.55, 0.19))):                    # escalones
        tabla(bm, (0, y, z - 0.05), (1.3 - k * 0.0, 0.3, 0.1), M["Amb_Madera"], bisel=0.01)
        tabla(bm, (0, y + 0.02, z / 2 - 0.03), (1.2, 0.24, z - 0.06), M["Amb_MaderaOscura"], bisel=0.01)
        bola(bm, (0.42, y, z + 0.01), (0.14, 0.1, 0.04), M["Ext_NieveBrillo"], rnd=rnd)
    techo_y0, techo_z0, techo_y1, techo_z1 = 2.72, 2.74, 4.38, 2.33
    zt = lambda y: techo_z0 + (techo_z1 - techo_z0) * (y - techo_y0) / (techo_y1 - techo_y0)
    for x in (-1.65, 1.65):                                                                  # postes de tronco
        tronco(bm, Vector((x, 4.0, zp)), Vector((x, 4.0, zt(4.0) - 0.08)), 0.09, rnd, lados=7)
        tabla(bm, (x, 4.0, zt(4.0) - 0.1), (0.24, 0.24, 0.06), M["Amb_MaderaOscura"])
    tronco(bm, Vector((-1.85, 4.0, zt(4.0) - 0.16)), Vector((1.85, 4.0, zt(4.0) - 0.16)), 0.08, rnd, lados=7)
    # barandal: lados y frente (con hueco para los escalones)
    for x in (-1.65, 1.65):
        tronco(bm, Vector((x, 2.75, zp + 0.75)), Vector((x, 4.0, zp + 0.75)), 0.05, rnd, lados=6, cortes=False)
        for y in (3.05, 3.4, 3.7):
            tabla(bm, (x, y, zp + 0.38), (0.06, 0.06, 0.72), M["Amb_Madera2"])
    for s in (-1, 1):
        tronco(bm, Vector((s * 1.65, 4.0, zp + 0.75)), Vector((s * 0.75, 4.0, zp + 0.75)), 0.05, rnd, lados=6, cortes=False)
        for x in (1.05, 1.35):
            tabla(bm, (s * x, 4.0, zp + 0.38), (0.06, 0.06, 0.72), M["Amb_Madera2"])
        bola(bm, (s * 1.2, 4.0, zp + 0.82), (0.35, 0.07, 0.04), M["Ext_NieveBrillo"], rnd=rnd)
    # banquito
    tabla(bm, (-1.15, 2.95, zp + 0.42), (1.0, 0.32, 0.06), M["Amb_Madera"])
    for x in (-1.55, -0.75):
        tabla(bm, (x, 2.95, zp + 0.2), (0.07, 0.28, 0.4), M["Amb_MaderaOscura"])
    # techito del porche
    agua(bm, -1.95, 1.95, techo_y0, techo_z0 + 0.04, techo_y1, techo_z1, rnd, nieve=0.15, lateral=0.05, semilla=7)

def chimenea(bm, rnd):
    cx, cy, m = CHIM
    z = 3.0; fila = 0
    while z < 5.85:
        alto = rnd.uniform(0.2, 0.23)
        for lado in range(4):
            n = 3
            for i in range(n):
                t = (i + (0.5 if fila % 2 else 0.0)) / n
                if lado == 0: c = (cx - m + 2 * m * t, cy - m, z + alto / 2)
                elif lado == 1: c = (cx + m, cy - m + 2 * m * t, z + alto / 2)
                elif lado == 2: c = (cx + m - 2 * m * t, cy + m, z + alto / 2)
                else: c = (cx - m, cy + m - 2 * m * t, z + alto / 2)
                piedra(bm, c, (0.3, 0.3, alto * 1.0), M["Amb_Piedra2"] if rnd.random() < 0.6 else M["Amb_Piedra"], rnd)
        tabla(bm, (cx, cy, z + alto / 2), (2 * m - 0.1, 2 * m - 0.1, alto), M["Amb_Piedra2"], bisel=0.0)   # relleno
        z += alto; fila += 1
    tabla(bm, (cx, cy, 5.92), (2 * m + 0.22, 2 * m + 0.22, 0.12), M["Amb_Piedra"], bisel=0.02)            # remate
    tabla(bm, (cx, cy, 5.99), (2 * m - 0.25, 2 * m - 0.25, 0.04), M["Ext_MetalNegro"], bisel=0.0)          # boca
    for sx in (-1, 1):                                                                                     # nieve en el remate
        bola(bm, (cx + sx * (m - 0.02), cy, 6.0), (0.12, m + 0.1, 0.06), M["Ext_NieveBrillo"], rnd=rnd)

def lena(bm, rnd):
    r = 0.12
    for fila, n in enumerate((4, 3, 2)):
        for k in range(n):
            x = 3.55 + (k - (n - 1) / 2) * r * 2.02 * 0.62
            z = r + fila * r * 1.75
            y0 = -2.4 + rnd.uniform(-0.05, 0.05); y1 = -0.9 + rnd.uniform(-0.05, 0.05)
            tronco(bm, Vector((x, y0, z)), Vector((x, y1, z)), r * rnd.uniform(0.9, 1.05), rnd, lados=7)
    bola(bm, (3.55, -1.65, 0.12 * 3.5 + 0.06), (0.16, 0.75, 0.07), M["Ext_NieveBrillo"], rnd=rnd)
    # tejabán de la leña
    agua(bm, -2.6 + 0.0, -0.7, 2.98, 1.35, 3.95, 1.05, rnd, nieve=0.1, tejas=False, lateral=0.03, carambanos=False, semilla=9) if False else None

def tocon(bm, rnd):
    c = Vector((2.45, 3.7, 0.0))
    tronco(bm, c + Vector((0, 0, -0.05)), c + Vector((0, 0, 0.42)), 0.24, rnd, lados=8)
    # hacha clavada
    giro = Matrix.Rotation(0.5, 3, "Y")
    tabla(bm, c + Vector((0.05, 0, 0.62)), (0.05, 0.05, 0.55), M["Amb_Madera"], bisel=0.01, giro=giro)
    tabla(bm, c + Vector((-0.06, 0, 0.42)), (0.2, 0.03, 0.12), M["Ext_MetalNegro"], bisel=0.008, giro=giro)
    bola(bm, c + Vector((0.08, -0.05, 0.43)), (0.14, 0.1, 0.03), M["Ext_NieveBrillo"], rnd=rnd)

# ------------------------------------------------------------------ todo
def hacer_casa_troncos(semilla=5):
    rnd = random.Random(semilla)
    me = bpy.data.meshes["CasaTroncos"]
    for n in MATS:
        if n not in bpy.data.materials:
            raise RuntimeError("falta material " + n)
    me.materials.clear()
    for n in MATS: me.materials.append(bpy.data.materials[n])
    bm = bmesh.new()
    cimiento(bm, rnd)
    paredes(bm, rnd)
    puerta(bm, rnd)
    for a, b in VENT_FRENTE: ventana(bm, "x", DC, a, b, rnd, hacia=1)
    ventana(bm, "x", -DC, -0.45, 0.45, rnd, hacia=-1)
    ventana(bm, "y", -WC, -0.45, 0.45, rnd, hacia=-1, jardinera=False)
    for s in (-1, 1): ojo_de_buey(bm, s * (WC + R), s)
    # techo: dos aguas (frente y atrás) que se encuentran en la cumbrera + capa redonda de nieve en la cumbrera
    agua(bm, -XT, XT, 0.0, CUMBRE, YT, z_techo(YT), rnd, semilla=1)
    agua(bm, -XT, XT, 0.0, CUMBRE, -YT, z_techo(YT), rnd, semilla=2)
    loft(bm, [Vector((-XT - 0.05, 0, CUMBRE + 0.2)), Vector((XT + 0.05, 0, CUMBRE + 0.2))], [(0.26, 0.16)] * 2,
         mat=M["Ext_NieveBrillo"], segs=6, sub=6, tapas=(True, True), domo=0.5)
    porche(bm, rnd)
    chimenea(bm, rnd)
    lena(bm, rnd)
    tocon(bm, rnd)
    for f in bm.faces: f.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index in (M["Amb_Piedra2"], M["Amb_Piedra"])])
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    for e in me.edges: e.use_edge_sharp = False
    print("CasaTroncos tris =", sum(len(p.vertices) - 2 for p in me.polygons))


# ------------------------------------------------------------------ focos del alero (luces_pueblo.py)
def instalar_alero_troncos():
    """Cambia lineas_alero (de luces_pueblo.py, ya cargado con exec) para que en la cabaña los focos vayan en el
    alero de atrás, en la orilla del techito del porche y en los tramos del alero de enfrente a los lados del porche."""
    viejo = globals()["lineas_alero"]
    def lineas(c):
        if c.data.name != "CasaTroncos": return viejo(c)
        zA = z_techo(YT); fr, at = Vector((0, 1, 0)), Vector((0, -1, 0))
        return [(Vector((-XT + 0.15, -YT, zA)), Vector((XT - 0.15, -YT, zA)), at),
                (Vector((-1.8, 4.38, 2.33)), Vector((1.8, 4.38, 2.33)), fr),
                (Vector((-XT + 0.15, YT, zA)), Vector((-2.15, YT, zA)), fr),
                (Vector((2.15, YT, zA)), Vector((XT - 0.15, YT, zA)), fr)], 2.33
    globals()["lineas_alero"] = lineas
