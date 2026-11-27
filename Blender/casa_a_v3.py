# -*- coding: utf-8 -*-
"""
CASA A (A-frame) v3 (27-nov): malla "CasaA" rehecha COMPLETA en low-poly redondeado. Frente = +X (ventanal),
techo de dos aguas que llega casi al suelo (cumbrera z 6.25 en y = 0, aleros y ±3.6), suelo z 0.
Se respeta: ventanal en x ≈ 3.1 (la corona de Coronas_Casas va en (3.2, 0, 3.55)); terraza x 3.0..4.75;
tubo de la estufa en (-1.2, -1.4) con la boca en z ≈ 6.9; caja "nieve_pie".
Partes: techo de tejas + almohada de nieve, hastiales de tablas verticales, ventanal triangular con cuadrícula y
puerta de madera con ventanita, estrella de luz colgando bajo la cumbrera, terraza de tablas con barandal nevado y
escalones al costado, piedras en la base, tubo de estufa con sombrerito, esquíes clavados en la nieve, leñita.
Uso: exec(modelado.py); exec(casa_troncos_v3.py); exec(casa_a_v3.py); hacer_casa_a()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

MATS_A = ["Amb_Piedra2", "Amb_Piedra", "Ext_Tejado", "Ext_NieveBrillo", "Ext_Hielo", "Amb_Madera3", "Amb_MaderaOscura",
          "Amb_Madera", "Amb_Madera2", "Ext_VentanaCalida", "Ext_LuzFarol", "Ext_MetalNegro", "Amb_Laton", "Amb_Rojo",
          "Ext_PinoD", "Ext_Tronco2", "Ext_Tronco", "Ext_CorteLena", "Ext_AnilloLena", "Ext_Crema"]

CA, YA, ZE = 6.25, 3.6, -0.15          # cumbrera, alero (y), altura del alero
PA = (CA - ZE) / YA
XG = 3.0                               # hastiales en x = ±XG
ZP = 0.4                               # piso

def z_bajo_techo(y):
    return CA - 0.32 - PA * abs(y)

def hastial(bm, s, mat):
    """Tablas verticales en el hastial x = s*XG (recortadas por el techo)."""
    ancho = 0.26
    y = 0.0
    tablas = []
    while True:
        y1 = y + ancho
        if z_bajo_techo(y) < ZP + 0.1: break
        tablas += [(y, y1), (-y1, -y)]
        y = y1
    for y0, y1 in tablas:
        z0 = ZP
        za, zb = z_bajo_techo(y0), z_bajo_techo(y1)
        if max(za, zb) <= z0 + 0.05: continue
        za, zb = max(za, z0 + 0.02), max(zb, z0 + 0.02)
        g = 0.012
        pts = [Vector((s * XG, y0 + g, z0)), Vector((s * XG, y1 - g, z0)), Vector((s * XG, y1 - g, zb)), Vector((s * XG, y0 + g, za))]
        prisma(bm, pts, Vector((-s * 0.06, 0, 0)), mat)
    # vigas del marco (siguen el techo) y travesaño del piso
    for sy in (-1, 1):
        a = Vector((s * (XG + 0.04), 0, CA - 0.3)); b = Vector((s * (XG + 0.04), sy * (CA - 0.3 - ZP + 0.1) / PA, ZP - 0.1))
        d = (b - a).normalized(); n = Vector((0, -d.z, d.y)) * (1 if sy > 0 else -1)
        if n.z < 0: n = -n
        prisma(bm, [a, b, b - n * 0.2, a - n * 0.2], Vector((s * 0.1, 0, 0)), M["Amb_Madera3"])
    yb = (CA - 0.32 - ZP) / PA
    tabla(bm, (s * (XG + 0.05), 0, ZP - 0.05), (0.12, 2 * yb, 0.16), M["Amb_Madera3"], bisel=0.012)

def ventanal(bm, rnd):
    x = XG + 0.06
    z0, z1, w0 = 0.9, 5.0, 2.3
    hw = lambda z: w0 * (z1 - z) / (z1 - z0)
    vs = [bm.verts.new((x, -w0, z0)), bm.verts.new((x, w0, z0)), bm.verts.new((x, 0, z1))]
    vb = [bm.verts.new((x - 0.03, -w0, z0)), bm.verts.new((x - 0.03, w0, z0)), bm.verts.new((x - 0.03, 0, z1))]
    bm.faces.new(vs).material_index = M["Ext_VentanaCalida"]; bm.faces.new(vb[::-1]).material_index = M["Ext_VentanaCalida"]
    for i in range(3): bm.faces.new((vs[i], vb[i], vb[(i + 1) % 3], vs[(i + 1) % 3])).material_index = M["Ext_VentanaCalida"]
    xm = x + 0.05; mo = M["Amb_MaderaOscura"]
    # marco perimetral
    for sy in (-1, 1):
        a = Vector((xm, sy * (w0 + 0.05), z0 - 0.04)); b = Vector((xm, 0, z1 + 0.08))
        d = (b - a).normalized(); n = Vector((0, -d.z, d.y)) * sy
        if n.z < 0: n = -n
        prisma(bm, [a - n * 0.0, b, b + n * 0.12, a + n * 0.12 - Vector((0, 0, 0))], Vector((0.06, 0, 0)), mo)
    tabla(bm, (xm + 0.03, 0, z0 - 0.04), (0.08, 2 * w0 + 0.2, 0.12), mo, bisel=0.01)
    # cuadrícula
    for y in (-1.5, -0.75, 0.75, 1.5):
        ztop = z1 - (z1 - z0) * abs(y) / w0
        tabla(bm, (xm, y, (z0 + ztop) / 2), (0.05, 0.06, ztop - z0), mo, bisel=0.0)
    for z in (2.7, 3.65, 4.4):
        tabla(bm, (xm, 0, z), (0.05, 2 * hw(z), 0.06), mo, bisel=0.0)
    tabla(bm, (xm, 0, (2.7 + z1) / 2), (0.05, 0.06, z1 - 2.7), mo, bisel=0.0)
    # puerta al centro (madera con ventanita), marco y manija
    zp0, zp1 = ZP + 0.2, 2.55
    tabla(bm, (x + 0.06, 0, (zp0 + zp1) / 2), (0.08, 1.0, zp1 - zp0), M["Amb_Madera"], bisel=0.012)
    for k in range(5):
        tabla(bm, (x + 0.105, -0.4 + k * 0.2, (zp0 + zp1) / 2 - 0.25), (0.02, 0.15, zp1 - zp0 - 0.7), M["Amb_Madera2"], bisel=0.0)
    tabla(bm, (x + 0.1, 0, zp1 - 0.35), (0.04, 0.55, 0.4), M["Ext_VentanaCalida"], bisel=0.0)
    tabla(bm, (x + 0.12, 0, zp1 - 0.35), (0.03, 0.04, 0.4), mo, bisel=0.0)
    for sy in (-1, 1): tabla(bm, (x + 0.1, sy * 0.56, (zp0 + zp1) / 2), (0.12, 0.1, zp1 - zp0 + 0.05), mo, bisel=0.01)
    tabla(bm, (x + 0.1, 0, zp1 + 0.04), (0.12, 1.22, 0.1), mo, bisel=0.01)
    bola(bm, (x + 0.14, -0.36, 1.45), (0.04, 0.04, 0.04), M["Amb_Laton"])
    # estrella de luz colgando bajo la cumbrera
    c = Vector((XG + 0.45, 0, 5.15))
    for k in range(4): tabla(bm, c + Vector((0, 0, 0.3 + k * 0.06)), (0.02, 0.02, 0.05), M["Ext_MetalNegro"], bisel=0.0)
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5; r = 0.24 if k % 2 == 0 else 0.1
        pts.append(Vector((0, math.cos(a) * r, math.sin(a) * r)))
    fr = [bm.verts.new(c + p + Vector((0.04, 0, 0))) for p in pts]; at = [bm.verts.new(c + p - Vector((0.04, 0, 0))) for p in pts]
    cf, ca = bm.verts.new(c + Vector((0.08, 0, 0))), bm.verts.new(c - Vector((0.08, 0, 0)))
    for k in range(10):
        j = (k + 1) % 10
        bm.faces.new((fr[k], fr[j], cf)).material_index = M["Ext_LuzFarol"]
        bm.faces.new((at[j], at[k], ca)).material_index = M["Ext_LuzFarol"]
        bm.faces.new((fr[j], fr[k], at[k], at[j])).material_index = M["Ext_LuzFarol"]

def ventana_atras(bm, rnd):
    x = -XG - 0.06
    tabla(bm, (x, 0, 2.2), (0.04, 1.0, 1.0), M["Ext_VentanaCalida"], bisel=0.0)
    for sy in (-1, 1): tabla(bm, (x - 0.04, sy * 0.55, 2.2), (0.1, 0.1, 1.2), M["Amb_MaderaOscura"], bisel=0.01)
    for z in (1.65, 2.75): tabla(bm, (x - 0.04, 0, z), (0.1, 1.2, 0.1), M["Amb_MaderaOscura"], bisel=0.01)
    tabla(bm, (x - 0.03, 0, 2.2), (0.04, 0.05, 1.0), M["Amb_MaderaOscura"], bisel=0.0)
    tabla(bm, (x - 0.03, 0, 2.2), (0.04, 1.0, 0.05), M["Amb_MaderaOscura"], bisel=0.0)
    tabla(bm, (x - 0.12, 0, 1.58), (0.22, 1.3, 0.06), M["Amb_Madera"], bisel=0.01)
    bola(bm, (x - 0.13, 0, 1.62), (0.1, 0.6, 0.04), M["Ext_NieveBrillo"], rnd=rnd)
    # ventanita redonda arriba
    c = Vector((x, 0, 4.1)); lados = 8
    for r0, r1, prof, mat in ((0.0, 0.28, 0.04, M["Ext_VentanaCalida"]), (0.28, 0.38, 0.1, M["Amb_MaderaOscura"])):
        for j in range(lados):
            a, b = 6.2832 * j / lados, 6.2832 * (j + 1) / lados
            ps = [Vector((0, math.cos(a) * r0, math.sin(a) * r0)), Vector((0, math.cos(b) * r0, math.sin(b) * r0)),
                  Vector((0, math.cos(b) * r1, math.sin(b) * r1)), Vector((0, math.cos(a) * r1, math.sin(a) * r1))]
            prisma(bm, [c + p for p in ps], Vector((-prof, 0, 0)), mat)

def terraza(bm, rnd):
    x0, x1, yy, zp = XG, 4.75, 2.0, 0.6
    n = 7
    for i in range(n):                                     # tablas (a lo largo de Y)
        x = x0 + (x1 - x0) * (i + 0.5) / n
        tabla(bm, (x, 0, zp - 0.05), ((x1 - x0) / n - 0.025, 2 * yy, 0.1), M["Amb_Madera"], bisel=0.01)
    for y in (-yy + 0.1, 0, yy - 0.1):                     # pilotes de tronco
        tronco(bm, Vector((x1 - 0.15, y, -0.4)), Vector((x1 - 0.15, y, zp - 0.1)), 0.09, rnd, lados=7)
    tabla(bm, (x1 - 0.1, 0, zp - 0.17), (0.14, 2 * yy + 0.1, 0.16), M["Amb_MaderaOscura"], bisel=0.01)
    # barandal: frente y lado -y completos; lado +y con hueco para los escalones
    def poste(x, y):
        tabla(bm, (x, y, zp + 0.42), (0.1, 0.1, 0.84), M["Amb_Madera2"], bisel=0.012)
        bola(bm, (x, y, zp + 0.88), (0.08, 0.08, 0.05), M["Ext_NieveBrillo"], rnd=rnd)
    def riel(a, b):
        d = b - a; L = d.length; c = (a + b) / 2
        giro = Matrix.Rotation(math.atan2(d.y, d.x), 3, "Z")
        tabla(bm, c, (L, 0.08, 0.06), M["Amb_Madera2"], bisel=0.01, giro=giro)
        tabla(bm, c - Vector((0, 0, 0.42)), (L, 0.05, 0.05), M["Amb_Madera2"], bisel=0.0, giro=giro)
        bola(bm, c + Vector((0, 0, 0.05)), (L * 0.45, 0.06, 0.04) if abs(d.x) > abs(d.y) else (0.06, L * 0.45, 0.04), M["Ext_NieveBrillo"], rnd=rnd)
        k = int(L / 0.25)
        for i in range(1, k):
            p = a + d * (i / k)
            tabla(bm, (p.x, p.y, zp + 0.42), (0.04, 0.04, 0.8), M["Amb_Madera2"], bisel=0.0)
    xs = x1 - 0.1
    for (ax, ay), (bx, by) in (((xs, -yy + 0.05), (xs, yy - 0.05)), ((x0 + 0.15, -yy + 0.05), (xs, -yy + 0.05)),
                               ((x0 + 0.15, yy - 0.05), (3.35, yy - 0.05))):
        poste(ax, ay); poste(bx, by)
        riel(Vector((ax, ay, zp + 0.84)), Vector((bx, by, zp + 0.84)))
    poste(4.35, yy - 0.05); riel(Vector((4.35, yy - 0.05, zp + 0.84)), Vector((xs, yy - 0.05, zp + 0.84)))
    # escalones al costado (+y)
    for k, (y, z) in enumerate(((yy + 0.22, 0.4), (yy + 0.52, 0.2))):
        tabla(bm, (3.85, y, z - 0.05), (1.0, 0.3, 0.1), M["Amb_Madera"], bisel=0.01)
        tabla(bm, (3.85, y + 0.02, (z - 0.1) / 2 - 0.1), (0.9, 0.24, z + 0.1), M["Amb_MaderaOscura"], bisel=0.01)
        bola(bm, (3.6 + 0.4 * k, y, z + 0.01), (0.14, 0.1, 0.04), M["Ext_NieveBrillo"], rnd=rnd)
    # nieve acumulada en las esquinas de la terraza, tapete y faroles en el barandal del frente
    for y in (-yy + 0.3, yy - 0.35):
        bola(bm, (xs - 0.25, y, zp + 0.03), (0.28, 0.26, 0.06), M["Ext_NieveBrillo"], rnd=rnd)
    tabla(bm, (XG + 0.6, 0, zp + 0.01), (0.55, 0.9, 0.02), M["Amb_Rojo"], bisel=0.005)
    for y in (-yy + 0.05, yy - 0.05):
        c = Vector((xs, y, zp + 1.12))
        tabla(bm, c, (0.16, 0.16, 0.2), M["Ext_LuzFarol"], bisel=0.01)
        for sx in (-1, 1):
            for sy in (-1, 1):
                tabla(bm, c + Vector((sx * 0.08, sy * 0.08, 0)), (0.025, 0.025, 0.22), M["Ext_MetalNegro"], bisel=0.0)
        tabla(bm, c + Vector((0, 0, 0.13)), (0.22, 0.22, 0.04), M["Ext_MetalNegro"], bisel=0.006)
        tabla(bm, c + Vector((0, 0, 0.18)), (0.1, 0.1, 0.05), M["Ext_MetalNegro"], bisel=0.006)

def tubo_estufa(bm, rnd):
    cx, cy = -1.2, -1.4
    lados = 8
    loft(bm, [Vector((cx, cy, 3.8)), Vector((cx, cy, 6.75))], [(0.17, 0.17)] * 2, mat=M["Ext_MetalNegro"], segs=lados, sub=1, tapas=(False, False))
    for z in (5.0, 6.0):
        loft(bm, [Vector((cx, cy, z - 0.04)), Vector((cx, cy, z + 0.04))], [(0.2, 0.2)] * 2, mat=M["Ext_MetalNegro"], segs=lados, sub=1, tapas=(True, True), domo=0.1)
    # sombrerito cónico separado del tubo
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        tabla(bm, (cx + math.cos(a) * 0.15, cy + math.sin(a) * 0.15, 6.83), (0.025, 0.025, 0.14), M["Ext_MetalNegro"], bisel=0.0)
    base = [bm.verts.new((cx + math.cos(6.2832 * j / lados) * 0.32, cy + math.sin(6.2832 * j / lados) * 0.32, 6.9)) for j in range(lados)]
    punta = bm.verts.new((cx, cy, 7.12))
    for j in range(lados):
        bm.faces.new((base[j], base[(j + 1) % lados], punta)).material_index = M["Ext_MetalNegro"]
    bm.faces.new(base[::-1]).material_index = M["Ext_MetalNegro"]
    sn = [bm.verts.new((cx + math.cos(6.2832 * j / lados) * 0.27, cy + math.sin(6.2832 * j / lados) * 0.27, 6.98)) for j in range(lados)]
    ps = bm.verts.new((cx, cy, 7.2))
    for j in range(lados):
        bm.faces.new((sn[j], sn[(j + 1) % lados], ps)).material_index = M["Ext_NieveBrillo"]
    bm.faces.new(sn[::-1]).material_index = M["Ext_NieveBrillo"]

def base_piedras(bm, rnd):
    for s in (-1, 1):                                  # bajo los hastiales
        yb = (CA - 0.32 - ZP) / PA
        n = int(2 * yb / 0.38)
        for i in range(n):
            for fila, (zc, alto) in enumerate(((0.12, 0.24), (0.32, 0.18))):
                t = (i + 0.5 + (0.5 if fila else 0)) / n
                if t > 1: continue
                piedra(bm, (s * XG, -yb + 2 * yb * t, zc), (0.3, 0.4, alto), M["Amb_Piedra2"] if rnd.random() < 0.7 else M["Amb_Piedra"], rnd)

def esquies(bm, rnd):
    c = Vector((5.25, -1.6, 0.0))
    for k, (dy, col) in enumerate(((0.0, M["Amb_Rojo"]), (0.16, M["Amb_Rojo"]))):
        g = Matrix.Rotation(0.12 * (1 if k else -1), 3, "Y")
        tabla(bm, c + Vector((0, dy, 0.85)), (0.03, 0.09, 1.7), col, bisel=0.008, giro=g)
        tabla(bm, c + Vector((0, dy, 1.0)), (0.06, 0.1, 0.1), M["Ext_MetalNegro"], bisel=0.008, giro=g)
    for dy in (-0.25, 0.42):                              # bastones
        loft(bm, [c + Vector((0.05, dy, 0.0)), c + Vector((-0.05, dy, 1.25))], [(0.015, 0.015)] * 2, mat=M["Ext_MetalNegro"], segs=5, sub=1, tapas=(True, True))
        loft(bm, [c + Vector((0.04, dy, 0.18)), c + Vector((0.04, dy, 0.2))], [(0.07, 0.07)] * 2, mat=M["Ext_MetalNegro"], segs=6, sub=1, tapas=(True, True), domo=0.05)
    bola(bm, c + Vector((0, 0.08, 0.0)), (0.45, 0.5, 0.16), M["Ext_NieveBrillo"], rnd=rnd)

def lenita_a(bm, rnd):
    r = 0.1
    for fila, n in enumerate((4, 3, 2)):
        for k in range(n):
            x = -XG - 0.35 + 0.0
            y = 1.3 + (k - (n - 1) / 2) * r * 2.05
            z = r + fila * r * 1.75
            tronco(bm, Vector((x - 0.3, y, z)), Vector((x + 0.25, y, z)), r * rnd.uniform(0.9, 1.05), rnd, lados=7)
    bola(bm, (-XG - 0.4, 1.3, r * 3.5 + 0.06), (0.33, 0.38, 0.06), M["Ext_NieveBrillo"], rnd=rnd)

def hacer_casa_a(semilla=21):
    global M
    for n in MATS_A:
        if n not in bpy.data.materials: raise RuntimeError("falta material " + n)
    M = {n: i for i, n in enumerate(MATS_A)}
    rnd = random.Random(semilla)
    me = bpy.data.meshes["CasaA"]
    me.materials.clear()
    for n in MATS_A: me.materials.append(bpy.data.materials[n])
    bm = bmesh.new()
    base_piedras(bm, rnd)
    for s in (-1, 1): hastial(bm, s, M["Amb_Madera3"])
    # relleno interior entre hastiales (para que nunca se vea a través)
    for s in (-1, 1):
        yb = (CA - 0.32 - ZP) / PA
        pts = [Vector((s * (XG - 0.07), -yb, ZP)), Vector((s * (XG - 0.07), yb, ZP)), Vector((s * (XG - 0.07), 0, CA - 0.32))]
        v0 = [bm.verts.new(p) for p in pts]; v1 = [bm.verts.new(p - Vector((s * 0.04, 0, 0))) for p in pts]
        bm.faces.new(v0 if s > 0 else v0[::-1]).material_index = M["Amb_MaderaOscura"]
        bm.faces.new(v1[::-1] if s > 0 else v1).material_index = M["Amb_MaderaOscura"]
    ventanal(bm, rnd)
    ventana_atras(bm, rnd)
    agua(bm, -3.4, 3.4, 0.0, CA, YA, ZE, rnd, nieve=0.26, carambanos=False, semilla=3, hasta=0.74, margen=0.3)
    agua(bm, -3.4, 3.4, 0.0, CA, -YA, ZE, rnd, nieve=0.26, carambanos=False, semilla=4, hasta=0.7, margen=0.3)
    loft(bm, [Vector((-3.45, 0, CA + 0.24)), Vector((3.45, 0, CA + 0.24))], [(0.24, 0.17)] * 2,
         mat=M["Ext_NieveBrillo"], segs=6, sub=6, tapas=(True, True), domo=0.5)
    for s in (-1, 1):                                  # carámbanos en la orilla del hastial delantero
        for k in range(6):
            y = s * (0.6 + k * 0.45)
            carambano(bm, Vector((3.38, y, z_bajo_techo(y) + 0.12)), rnd.uniform(0.1, 0.25))
    terraza(bm, rnd)
    tubo_estufa(bm, rnd)
    esquies(bm, rnd)
    lenita_a(bm, rnd)
    for f in bm.faces: f.smooth = False
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    for e in me.edges: e.use_edge_sharp = False
    print("CasaA tris =", sum(len(p.vertices) - 2 for p in me.polygons))

def instalar_alero_a():
    """Focos de la CasaA: siguen las dos orillas inclinadas del hastial delantero (como antes)."""
    viejo = globals()["lineas_alero"]
    def lineas(c):
        if c.data.name != "CasaA": return viejo(c)
        fuera = Vector((1, 0, 0))
        return [(Vector((3.3, -3.2, 0.45)), Vector((3.3, -0.25, 5.7)), fuera),
                (Vector((3.3, 0.25, 5.7)), Vector((3.3, 3.2, 0.45)), fuera)], 0.4
    globals()["lineas_alero"] = lineas
