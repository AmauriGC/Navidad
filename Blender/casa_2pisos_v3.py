# -*- coding: utf-8 -*-
"""
CASAS DE 2 PISOS v3 (26-nov): mallas CasaRoja / CasaAzul / CasaVerde (misma forma, distinto color y detalles),
rehechas COMPLETAS en low-poly redondeado. Usa las piezas de casa_troncos_v3.py (agua, piedra, bola, carambano,
tabla, prisma, tronco). Frente = +Y, suelo z 0. Se respetan:
  - puerta x 0.6..1.6 con su cara en y≈2.45 (la corona de Coronas_Casas va en (1.1, 2.465, 1.91));
  - chimenea centrada en (1.4, -0.8) con la boca en z≈8.45 (humo de Unity);
  - caja de paredes ±2.66 x ±2.44 (NieveCasas, prop "nieve_pie"); techo ±2.9 x ±2.95, cumbrera z 7.62.
Paredes de TABLONES traslapados (cada tablón inclinado, recortado alrededor de puertas/ventanas y siguiendo el techo
en los hastiales), esquineros y cinturón blancos, ventanas blancas con cruz, cortinitas, repisa nevada y jardinera,
buhardilla al frente, ojo de buey en los hastiales, tejado de tejas + almohada de nieve + carámbanos, chimenea de
ladrillo, puerta de 4 tableros con escalones de piedra y techito, farol de pared y extras distintos por casa.
Uso: exec(modelado.py); exec(casa_troncos_v3.py); exec(casa_2pisos_v3.py); hacer_casa_2pisos("CasaRoja")
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

MATS = ["Amb_Piedra2", "Amb_Piedra", "Ext_PinturaRoja", "Ext_Crema", "Ext_Tejado2", "Ext_NieveBrillo", "Ext_Hielo",
        "Amb_MaderaOscura", "Amb_Madera", "Amb_Madera2", "Amb_Laton", "Ext_VentanaCalida", "Ext_LuzFarol",
        "Ext_MetalNegro", "Ext_PinoD", "Amb_Rojo", "Ext_Ladrillo", "Ext_PinturaVerde", "Ext_Tronco2", "Ext_Tronco",
        "Ext_CorteLena", "Ext_AnilloLena"]

VARIANTES = {
    "CasaRoja":  dict(pintura="Ext_PinturaRoja", puerta="Ext_Crema", postigos=None, cortina="Ext_PinturaVerde",
                      extras=("buzon", "trineo"), semilla=11),
    "CasaAzul":  dict(pintura="Ext_PinturaAzul", puerta="Ext_PinturaRoja", postigos="Ext_Crema", cortina="Amb_Rojo",
                      extras=("banca",), semilla=12),
    "CasaVerde": dict(pintura="Ext_PinturaVerde", puerta="Ext_PinturaRoja", postigos="Ext_Crema", cortina="Amb_Rojo",
                      extras=("lena", "trineo"), semilla=13),
}

X2, Y2 = 2.6, 2.38            # cara de los tablones
ZB = 0.4                      # arriba del cimiento
C2, P2, YT2, XT2 = 7.62, 0.91, 2.95, 2.9
PUERTA2 = (0.6, 1.6, 0.42, 2.32)
CHIM2 = (1.4, -0.8)

def zt2(y):
    return C2 - P2 * abs(y)

# ------------------------------------------------------------------ paredes
def cara_pared(lado):
    """Devuelve P(a, z, o) -> punto y tam(wa, h, prof) para la pared 'lado' (+y, -y, +x, -x); o = hacia afuera."""
    if lado in ("+y", "-y"):
        s = 1 if lado == "+y" else -1
        return (lambda a, z, o: Vector((a, s * (Y2 + o), z))), (lambda wa, h, d: (wa, d, h)), Vector((0, s, 0)), X2
    s = 1 if lado == "+x" else -1
    return (lambda a, z, o: Vector((s * (X2 + o), a, z))), (lambda wa, h, d: (d, wa, h)), Vector((s, 0, 0)), Y2

def tablones(bm, lado, huecos, mat, rnd):
    P, tam, n, L = cara_pared(lado)
    gablete = lado in ("+x", "-x")
    alto, paso = 0.2, 0.18
    z = ZB
    while True:
        zb, ztp = z, z + alto
        if gablete:
            hb = min(L, (C2 - 0.16 - zb) / P2); ht = min(L, (C2 - 0.16 - ztp) / P2)
            if ht < 0.06: break
        else:
            lim = zt2(Y2 + 0.06) - 0.16
            if zb > lim - 0.05: break
            ztp = min(ztp, lim); hb = ht = L
        cortes = [(-max(hb, ht), max(hb, ht))]
        for h0, h1, hz0, hz1 in huecos:
            if ztp < hz0 or zb > hz1: continue
            nuevos = []
            for t0, t1 in cortes:
                if h1 <= t0 or h0 >= t1: nuevos.append((t0, t1)); continue
                if h0 - t0 > 0.04: nuevos.append((t0, h0))
                if t1 - h1 > 0.04: nuevos.append((h1, t1))
            cortes = nuevos
        for t0, t1 in cortes:
            b0, b1 = max(t0, -hb), min(t1, hb); u0, u1 = max(t0, -ht), min(t1, ht)
            if b1 - b0 < 0.03 or u1 - u0 < 0.0: continue
            base = [P(b0, zb, 0.05), P(b1, zb, 0.05), P(u1, ztp, 0.014), P(u0, ztp, 0.014)]
            prisma(bm, base, -n * 0.045, mat)
        z += paso

def huecos_de(ventanas, puerta=None):
    hs = [(a0 - 0.08, a1 + 0.08, z0 - 0.08, z1 + 0.08) for a0, a1, z0, z1 in ventanas]
    if puerta: hs.append((puerta[0] - 0.08, puerta[1] + 0.08, puerta[2] - 0.1, puerta[3] + 0.08))
    return hs

def ventana2(bm, lado, a0, a1, z0, z1, V, rnd, jardinera=True):
    P, tam, n, L = cara_pared(lado)
    am, zm, w, h = (a0 + a1) / 2, (z0 + z1) / 2, a1 - a0, z1 - z0
    tabla(bm, P(am, zm, 0.0), tam(w, h, 0.06), M["Ext_VentanaCalida"], bisel=0.0)
    # cortinitas a los lados + cenefa arriba (atrás del marco)
    for s in (-1, 1):
        tabla(bm, P(am + s * (w / 2 - w * 0.12), zm + 0.04, 0.04), tam(w * 0.2, h - 0.12, 0.02), M[V["cortina"]], bisel=0.0)
    tabla(bm, P(am, z1 - 0.07, 0.045), tam(w - 0.04, 0.1, 0.02), M[V["cortina"]], bisel=0.0)
    # marco blanco, cruz
    for a in (a0 - 0.05, a1 + 0.05):
        tabla(bm, P(a, zm, 0.1), tam(0.1, h + 0.2, 0.1), M["Ext_Crema"], bisel=0.012)
    tabla(bm, P(am, z1 + 0.06, 0.1), tam(w + 0.3, 0.12, 0.12), M["Ext_Crema"], bisel=0.012)
    tabla(bm, P(am, z1 + 0.15, 0.12), tam(w + 0.4, 0.06, 0.16), M["Ext_Crema"], bisel=0.01)     # cornisita
    tabla(bm, P(am, zm, 0.07), tam(0.045, h, 0.04), M["Ext_Crema"], bisel=0.0)
    tabla(bm, P(am, zm + h * 0.08, 0.07), tam(w, 0.045, 0.04), M["Ext_Crema"], bisel=0.0)
    # repisa con nieve
    tabla(bm, P(am, z0 - 0.07, 0.15), tam(w + 0.32, 0.07, 0.2), M["Ext_Crema"], bisel=0.012)
    bola(bm, P(am, z0 - 0.025, 0.17), tam((w + 0.22) / 2, 0.04, 0.09), M["Ext_NieveBrillo"], rnd=rnd)
    if V["postigos"]:
        for s in (-1, 1):
            a = am + s * (w / 2 + 0.1 + w * 0.24)
            tabla(bm, P(a, zm, 0.08), tam(w * 0.46, h + 0.14, 0.05), M[V["postigos"]], bisel=0.012)
            for k in range(4):                                     # tablillas (persiana)
                tabla(bm, P(a, z0 + 0.12 + k * (h - 0.1) / 4, 0.115), tam(w * 0.38, 0.05, 0.025), M[V["postigos"]], bisel=0.0)
    if jardinera:
        tabla(bm, P(am, z0 - 0.28, 0.22), tam(w + 0.12, 0.22, 0.2), M["Amb_Madera2"], bisel=0.015)
        bola(bm, P(am, z0 - 0.16, 0.22), tam((w + 0.06) / 2, 0.06, 0.09), M["Ext_NieveBrillo"], rnd=rnd)
        for k in range(6):
            a = a0 + w * (k + 0.5) / 6
            bola(bm, P(a, z0 - 0.12, 0.22 + rnd.uniform(-0.04, 0.04)), tam(0.08, 0.07, 0.05), M["Ext_PinoD"], rnd=rnd)
            if k % 2: bola(bm, P(a + 0.03, z0 - 0.08, 0.3), (0.03, 0.03, 0.03), M["Amb_Rojo"])

def ojo2(bm, lado, z, r=0.3):
    P, tam, n, L = cara_pared(lado)
    lados = 8
    for r0, r1, prof, mat in ((0.0, r, 0.05, M["Ext_VentanaCalida"]), (r, r + 0.1, 0.11, M["Ext_Crema"])):
        for j in range(lados):
            a, b = 6.2832 * j / lados, 6.2832 * (j + 1) / lados
            pts = [P(math.cos(a) * r0, z + math.sin(a) * r0, 0.0), P(math.cos(b) * r0, z + math.sin(b) * r0, 0.0),
                   P(math.cos(b) * r1, z + math.sin(b) * r1, 0.0), P(math.cos(a) * r1, z + math.sin(a) * r1, 0.0)]
            prisma(bm, pts, n * prof, mat)
    tabla(bm, P(0, z, 0.06), tam(0.04, 2 * r, 0.03), M["Ext_Crema"], bisel=0.0)
    tabla(bm, P(0, z, 0.06), tam(2 * r, 0.04, 0.03), M["Ext_Crema"], bisel=0.0)

# ------------------------------------------------------------------ puerta, farol, escalones
def puerta2(bm, V, rnd):
    x0, x1, z0, z1 = PUERTA2; y = Y2
    xm, w, h = (x0 + x1) / 2, x1 - x0, z1 - z0
    mat = M[V["puerta"]]
    tabla(bm, (xm, y + 0.03, (z0 + z1) / 2), (w, 0.08, h), mat, bisel=0.01)
    for zc in (z0 + h * 0.27, z0 + h * 0.72):                       # 4 tableros en relieve
        for s in (-1, 1):
            tabla(bm, (xm + s * w * 0.23, y + 0.075, zc), (w * 0.34, 0.03, h * 0.36), mat, bisel=0.015)
    for a in (x0 - 0.06, x1 + 0.06):                                 # marco blanco
        tabla(bm, (a, y + 0.06, (z0 + z1) / 2), (0.12, 0.12, h + 0.12), M["Ext_Crema"], bisel=0.012)
    tabla(bm, (xm, y + 0.06, z1 + 0.08), (w + 0.36, 0.14, 0.14), M["Ext_Crema"], bisel=0.012)
    bola(bm, (0.75, y + 0.13, 1.35), (0.045, 0.045, 0.045), M["Amb_Laton"])
    tabla(bm, (0.75, y + 0.09, 1.3), (0.06, 0.03, 0.18), M["Amb_Laton"], bisel=0.006)
    # escalones de piedra + tapete
    for k, (yy, zz, ancho) in enumerate(((2.66, 0.4, 1.5), (2.98, 0.2, 1.7))):
        caja(bm, (xm, yy, zz / 2), (ancho, 0.34 if k else 0.5, zz), mat=M["Amb_Piedra2"], bisel=0.04, segs=1)
        bola(bm, (xm + (0.45 if k else -0.4), yy + 0.02, zz + 0.01), (0.16, 0.1, 0.04), M["Ext_NieveBrillo"], rnd=rnd)
    tabla(bm, (xm, 2.68, 0.41), (0.8, 0.36, 0.02), M["Amb_Rojo"], bisel=0.005)
    # techito sobre la puerta con ménsulas
    agua(bm, x0 - 0.35, x1 + 0.35, Y2 + 0.05, 2.98, 3.3, 2.66, rnd, nieve=0.13, lateral=0.04, semilla=4)
    for a in (x0 - 0.25, x1 + 0.25):
        pts = [Vector((a - 0.03, Y2 + 0.06, 2.55)), Vector((a - 0.03, Y2 + 0.06, 2.95)), Vector((a - 0.03, 3.05, 2.8))]
        v0 = [bm.verts.new(p) for p in pts]; v1 = [bm.verts.new(p + Vector((0.06, 0, 0))) for p in pts]
        bm.faces.new(v0[::-1]).material_index = M["Ext_Crema"]; bm.faces.new(v1).material_index = M["Ext_Crema"]
        for i in range(3):
            bm.faces.new((v0[i], v0[(i + 1) % 3], v1[(i + 1) % 3], v1[i])).material_index = M["Ext_Crema"]
    # farol de pared junto a la puerta
    c = Vector((2.05, Y2 + 0.2, 2.05))
    tabla(bm, (2.05, Y2 + 0.05, 2.3), (0.12, 0.06, 0.22), M["Ext_MetalNegro"], bisel=0.006)
    tabla(bm, (2.05, Y2 + 0.14, 2.38), (0.04, 0.2, 0.04), M["Ext_MetalNegro"], bisel=0.004)
    tabla(bm, c, (0.18, 0.18, 0.24), M["Ext_LuzFarol"], bisel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tabla(bm, c + Vector((sx * 0.09, sy * 0.09, 0)), (0.03, 0.03, 0.26), M["Ext_MetalNegro"], bisel=0.004)
    tabla(bm, c + Vector((0, 0, 0.15)), (0.26, 0.26, 0.04), M["Ext_MetalNegro"], bisel=0.006)
    tabla(bm, c + Vector((0, 0, 0.2)), (0.12, 0.12, 0.06), M["Ext_MetalNegro"], bisel=0.006)
    tabla(bm, c + Vector((0, 0, -0.14)), (0.22, 0.22, 0.04), M["Ext_MetalNegro"], bisel=0.006)

# ------------------------------------------------------------------ techo, buhardilla, chimenea
def techo2(bm, rnd):
    agua(bm, -XT2, XT2, 0.0, C2, YT2, zt2(YT2), rnd, nieve=0.24, semilla=1)
    agua(bm, -XT2, XT2, 0.0, C2, -YT2, zt2(YT2), rnd, nieve=0.24, semilla=2)
    loft(bm, [Vector((-XT2 - 0.05, 0, C2 + 0.22)), Vector((XT2 + 0.05, 0, C2 + 0.22))], [(0.26, 0.17)] * 2,
         mat=M["Ext_NieveBrillo"], segs=6, sub=6, tapas=(True, True), domo=0.5)
    # tablas blancas en las orillas del hastial (bajo el vuelo)
    for s in (-1, 1):
        for sy in (-1, 1):
            a = Vector((s * (X2 + 0.08), 0, C2 - 0.2)); b = Vector((s * (X2 + 0.08), sy * YT2, zt2(YT2) - 0.2))
            d = (b - a); n = Vector((0, -d.z, d.y)).normalized() * (1 if sy > 0 else -1)
            prisma(bm, [a, b, b - Vector((0, 0, 0.2)), a - Vector((0, 0, 0.2))], Vector((s * 0.06, 0, 0)), M["Ext_Crema"])

def buhardilla(bm, V, rnd):
    yf, x0, x1 = 1.75, -0.55, 0.55
    zr = 7.0; zc = 7.42
    # paredes (frente pentagonal y lados) de tablones sencillos
    pts = [Vector((x0, yf, 5.9)), Vector((x1, yf, 5.9)), Vector((x1, yf, zr)), Vector((0, yf, zc)), Vector((x0, yf, zr))]
    v0 = [bm.verts.new(p) for p in pts]; v1 = [bm.verts.new(p - Vector((0, 1.6, 0))) for p in pts]
    bm.faces.new(v0).material_index = M[V["pintura"]]; bm.faces.new(v1[::-1]).material_index = M[V["pintura"]]
    for i in range(5):
        bm.faces.new((v0[(i + 1) % 5], v0[i], v1[i], v1[(i + 1) % 5])).material_index = M[V["pintura"]]
    for k in range(4):                                         # líneas de tablón al frente
        z = 6.12 + k * 0.22
        if z > zr: break
        tabla(bm, (0, yf + 0.015, z), (x1 - x0, 0.03, 0.035), M[V["pintura"]], bisel=0.0)
    ventana2(bm, "+y", -0.25, 0.25, 6.4, 6.85, V, rnd, jardinera=False) if False else None
    P = lambda a, z, o: Vector((a, yf + o, z))
    tabla(bm, P(0, 6.62, 0.0), (0.5, 0.06, 0.45), M["Ext_VentanaCalida"], bisel=0.0)
    for a in (-0.29, 0.29): tabla(bm, P(a, 6.62, 0.06), (0.08, 0.1, 0.6), M["Ext_Crema"], bisel=0.01)
    for z in (6.36, 6.88): tabla(bm, P(0, z, 0.06), (0.66, 0.1, 0.08), M["Ext_Crema"], bisel=0.01)
    tabla(bm, P(0, 6.62, 0.04), (0.04, 0.04, 0.45), M["Ext_Crema"], bisel=0.0)
    tabla(bm, P(0, 6.64, 0.04), (0.5, 0.04, 0.04), M["Ext_Crema"], bisel=0.0)
    bola(bm, P(0, 6.33, 0.1), (0.3, 0.07, 0.05), M["Ext_NieveBrillo"], rnd=rnd)
    # techito de dos aguas (cumbrera a lo largo de Y) con nieve
    for s in (-1, 1):
        a0 = Vector((0, yf + 0.2, zc + 0.06)); a1 = Vector((0, 0.0, zc + 0.06))
        b0 = Vector((s * (x1 + 0.18), yf + 0.2, zr - 0.08)); b1 = Vector((s * (x1 + 0.18), 0.0, zr - 0.08))
        quad = [a0, b0, b1, a1] if s > 0 else [a1, b1, b0, a0]
        prisma(bm, quad, Vector((0, 0, 0.06)), M["Ext_Tejado2"])
        # nieve: losa encima de cada lado, un poco más corta en la orilla y con borde que cae
        a0n, a1n = a0 + Vector((0, 0.05, 0.06)), a1 + Vector((0, 0, 0.06))
        b0n = b0 + Vector((-s * 0.02, 0.05, 0.03)); b1n = b1 + Vector((-s * 0.02, 0, 0.03))
        qn = [a0n, b0n, b1n, a1n] if s > 0 else [a1n, b1n, b0n, a0n]
        prisma(bm, qn, Vector((0, 0, 0.09)), M["Ext_NieveBrillo"])
    loft(bm, [Vector((0, 0.0, zc + 0.16)), Vector((0, yf + 0.27, zc + 0.16))], [(0.09, 0.07)] * 2,
         mat=M["Ext_NieveBrillo"], segs=6, sub=2, tapas=(True, True), domo=0.5)
    for s in (-1, 1):
        for k in range(3):
            y = 0.5 + k * 0.5 + rnd.uniform(-0.1, 0.1)
            carambano(bm, Vector((s * (x1 + 0.16), y, zr - 0.08)), rnd.uniform(0.08, 0.2))

def chimenea2(bm, rnd):
    cx, cy = CHIM2; m = 0.33
    z = 5.6; fila = 0
    while z < 8.2:
        for lado in range(4):
            n = 3
            for i in range(n + (1 if fila % 2 else 0)):
                t = (i + (0.0 if fila % 2 else 0.5)) / n
                if t > 1: continue
                ln = 2 * m / n - 0.02
                if lado % 2 == 0:
                    c = (cx - m + 2 * m * t, cy + (m if lado == 0 else -m), z + 0.055); tam = (ln, 0.1, 0.1)
                else:
                    c = (cx + (m if lado == 1 else -m), cy - m + 2 * m * t, z + 0.055); tam = (0.1, ln, 0.1)
                caja(bm, c, tam, mat=M["Ext_Ladrillo"], bisel=0.012, segs=1)
        tabla(bm, (cx, cy, z + 0.055), (2 * m - 0.04, 2 * m - 0.04, 0.12), M["Amb_Piedra"], bisel=0.0)   # junta
        z += 0.12; fila += 1
    tabla(bm, (cx, cy, z + 0.06), (2 * m + 0.24, 2 * m + 0.24, 0.12), M["Amb_Piedra"], bisel=0.02)
    tabla(bm, (cx, cy, z + 0.13), (2 * m - 0.12, 2 * m - 0.12, 0.04), M["Ext_MetalNegro"], bisel=0.0)
    for sx in (-1, 1):
        bola(bm, (cx + sx * m, cy, z + 0.14), (0.13, m + 0.1, 0.06), M["Ext_NieveBrillo"], rnd=rnd)
    return z + 0.15

def detalles_pared(bm, V, rnd):
    # esquineros y cinturón blancos
    for sx in (-1, 1):
        for sy in (-1, 1):
            tabla(bm, (sx * (X2 + 0.0), sy * (Y2 + 0.0), (ZB + zt2(Y2) - 0.1) / 2), (0.16, 0.16, zt2(Y2) - 0.1 - ZB), M["Ext_Crema"], bisel=0.015)
    for lado in ("+y", "-y", "+x", "-x"):
        P, tam, n, L = cara_pared(lado)
        tabla(bm, P(0, 2.9, 0.06), tam(2 * L + 0.1, 0.12, 0.1), M["Ext_Crema"], bisel=0.012)
        tabla(bm, P(0, ZB + 0.04, 0.07), tam(2 * L + 0.1, 0.1, 0.1), M["Ext_Crema"], bisel=0.012)   # zoclo

def cimiento2(bm, rnd):
    for (xa, ya), (xb, yb) in (((-2.62, -2.4), (2.62, -2.4)), ((2.62, -2.4), (2.62, 2.4)),
                               ((2.62, 2.4), (-2.62, 2.4)), ((-2.62, 2.4), (-2.62, -2.4))):
        L = math.hypot(xb - xa, yb - ya); n = int(L / 0.36)
        for i in range(n):
            for fila, (zc, alto) in enumerate(((0.1, 0.2), (0.28, 0.17))):
                t = (i + 0.5 + (0.5 if fila else 0)) / n
                if t > 1: continue
                c = (xa + (xb - xa) * t, ya + (yb - ya) * t, zc)
                piedra(bm, c, (0.4 if ya == yb else 0.28, 0.28 if ya == yb else 0.4, alto),
                       M["Amb_Piedra2"] if rnd.random() < 0.7 else M["Amb_Piedra"], rnd)
    caja(bm, (0, 0, 0.2), (2 * X2 - 0.1, 2 * Y2 - 0.1, 0.4), mat=M["Amb_Piedra2"], bisel=0.0)

# ------------------------------------------------------------------ extras
def buzon(bm, rnd):
    c = Vector((-2.1, 3.7, 0))
    tabla(bm, c + Vector((0, 0, 0.5)), (0.09, 0.09, 1.0), M["Amb_Madera"], bisel=0.012)
    tabla(bm, c + Vector((0, 0, 1.0)), (0.2, 0.4, 0.04), M["Amb_Madera"], bisel=0.008)
    loft(bm, [c + Vector((0, -0.2, 1.12)), c + Vector((0, 0.2, 1.12))], [(0.13, 0.1)] * 2, mat=M["Amb_Rojo"], segs=8, sub=1, tapas=(True, True), domo=0.15)
    tabla(bm, c + Vector((0.14, -0.05, 1.22)), (0.02, 0.04, 0.18), M["Amb_Laton"], bisel=0.004)      # banderita
    bola(bm, c + Vector((0, 0, 1.24)), (0.13, 0.2, 0.04), M["Ext_NieveBrillo"], rnd=rnd)

def trineo(bm, rnd, c, giro):
    R = Matrix.Rotation(giro, 3, "Z")
    for s in (-1, 1):
        pts = [Vector((s * 0.22, -0.55, 0.05)), Vector((s * 0.22, 0.35, 0.05)), Vector((s * 0.22, 0.58, 0.16)), Vector((s * 0.22, 0.52, 0.3))]
        loft(bm, [c + R @ p for p in pts], [(0.025, 0.025)] * 4, mat=M["Amb_Rojo"], segs=5, sub=2, tapas=(True, True), domo=0.3)
        for y in (-0.35, 0.2):
            tabla(bm, c + R @ Vector((s * 0.22, y, 0.13)), (0.03, 0.03, 0.16), M["Amb_Rojo"], bisel=0.0)
    for k in range(5):
        tabla(bm, c + R @ Vector((0, -0.48 + k * 0.2, 0.22)), (0.56, 0.15, 0.035), M["Amb_Madera"], bisel=0.008, giro=R)
    bola(bm, c + R @ Vector((0, -0.1, 0.26)), (0.22, 0.3, 0.04), M["Ext_NieveBrillo"], rnd=rnd)

def banca(bm, rnd):
    c = Vector((-1.2, 2.85, 0.0))
    tabla(bm, c + Vector((0, 0, 0.45)), (1.3, 0.38, 0.06), M["Amb_Madera"], bisel=0.012)
    tabla(bm, c + Vector((0, -0.18, 0.75)), (1.3, 0.05, 0.3), M["Amb_Madera"], bisel=0.012)
    for s in (-1, 1):
        tabla(bm, c + Vector((s * 0.55, 0, 0.22)), (0.07, 0.34, 0.44), M["Ext_MetalNegro"], bisel=0.01)
    bola(bm, c + Vector((0.2, 0.02, 0.5)), (0.5, 0.16, 0.05), M["Ext_NieveBrillo"], rnd=rnd)

def lenita(bm, rnd):
    r = 0.11
    for fila, n in enumerate((4, 3, 2)):
        for k in range(n):
            x = -X2 - 0.25
            y = -1.2 + (k - (n - 1) / 2) * r * 2.05
            z = r + fila * r * 1.75
            tronco(bm, Vector((x - 0.35, y, z)), Vector((x + 0.25, y, z)), r * rnd.uniform(0.9, 1.05), rnd, lados=7)
    bola(bm, (-X2 - 0.3, -1.2, 0.11 * 3.5 + 0.06), (0.36, 0.42, 0.06), M["Ext_NieveBrillo"], rnd=rnd)

# ------------------------------------------------------------------ todo
def hacer_casa_2pisos(nombre="CasaRoja"):
    V = VARIANTES[nombre]
    global M
    mats = list(MATS)
    if V["pintura"] not in mats: mats.append(V["pintura"])
    for n in mats:
        if n not in bpy.data.materials: raise RuntimeError("falta material " + n)
    M = {n: i for i, n in enumerate(mats)}
    M["Ext_Tejado"] = M["Ext_Tejado2"]          # agua() usa "Ext_Tejado"
    rnd = random.Random(V["semilla"])
    me = bpy.data.meshes[nombre]
    me.materials.clear()
    for n in mats: me.materials.append(bpy.data.materials[n])
    bm = bmesh.new()
    pint = M[V["pintura"]]
    frente_v = [(-1.65, -0.75, 1.28, 2.12), (0.8, 1.6, 3.55, 4.45), (-1.6, -0.8, 3.55, 4.45)]
    atras_v = [(0.75, 1.65, 1.58, 2.42), (-1.65, -0.75, 1.58, 2.42), (-0.4, 0.4, 3.55, 4.45)]
    lado_v = [(-0.45, 0.45, 3.55, 4.45)]
    cimiento2(bm, rnd)
    tablones(bm, "+y", huecos_de(frente_v, PUERTA2), pint, rnd)
    tablones(bm, "-y", huecos_de([(-a1, -a0, z0, z1) for a0, a1, z0, z1 in atras_v]), pint, rnd)
    for lado in ("+x", "-x"):
        tablones(bm, lado, huecos_de(lado_v) + [(-0.42, 0.42, 5.6, 6.4)], pint, rnd)
    # relleno interior (para que no se vea a través de las rendijas)
    caja(bm, (0, 0, (ZB + zt2(Y2)) / 2), (2 * X2 - 0.06, 2 * Y2 - 0.06, zt2(Y2) - ZB), mat=pint, bisel=0.0)
    for s in (-1, 1):
        pts = [Vector((s * (X2 - 0.03), -Y2 + 0.03, zt2(Y2) - 0.05)), Vector((s * (X2 - 0.03), Y2 - 0.03, zt2(Y2) - 0.05)),
               Vector((s * (X2 - 0.03), 0, C2 - 0.15))]
        v0 = [bm.verts.new(p) for p in pts]; v1 = [bm.verts.new(p - Vector((s * 0.05, 0, 0))) for p in pts]
        bm.faces.new(v0).material_index = pint; bm.faces.new(v1[::-1]).material_index = pint
        for i in range(3): bm.faces.new((v0[i], v0[(i + 1) % 3], v1[(i + 1) % 3], v1[i])).material_index = pint
    detalles_pared(bm, V, rnd)
    for a0, a1, z0, z1 in frente_v: ventana2(bm, "+y", a0, a1, z0, z1, V, rnd, jardinera=z0 < 3)
    for a0, a1, z0, z1 in atras_v: ventana2(bm, "-y", -a1, -a0, z0, z1, V, rnd, jardinera=z0 < 3)
    for lado in ("+x", "-x"):
        for a0, a1, z0, z1 in lado_v: ventana2(bm, lado, a0, a1, z0, z1, V, rnd, jardinera=False)
        ojo2(bm, lado, 6.0)
    puerta2(bm, V, rnd)
    techo2(bm, rnd)
    buhardilla(bm, V, rnd)
    chimenea2(bm, rnd)
    if "buzon" in V["extras"]: buzon(bm, rnd)
    if "trineo" in V["extras"]: trineo(bm, rnd, Vector((-2.05, 2.95, 0.0)) if nombre == "CasaRoja" else Vector((-X2 - 0.5, 1.0, 0.0)), 0.35 if nombre == "CasaRoja" else 1.5708)
    if "banca" in V["extras"]: banca(bm, rnd)
    if "lena" in V["extras"]: lenita(bm, rnd)
    for f in bm.faces: f.smooth = False
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    for e in me.edges: e.use_edge_sharp = False
    print(nombre, "tris =", sum(len(p.vertices) - 2 for p in me.polygons))


def instalar_alero_2pisos():
    """lineas_alero para las casas de 2 pisos: alero del frente y de atrás (el techito de la puerta es más bajo
    y la función original lo tomaba como alero)."""
    viejo = globals()["lineas_alero"]
    def lineas(c):
        if c.data.name not in VARIANTES: return viejo(c)
        z = zt2(YT2)
        return [(Vector((-XT2 + 0.15, YT2, z)), Vector((XT2 - 0.15, YT2, z)), Vector((0, 1, 0))),
                (Vector((-XT2 + 0.15, -YT2, z)), Vector((XT2 - 0.15, -YT2, z)), Vector((0, -1, 0)))], z
    globals()["lineas_alero"] = lineas
