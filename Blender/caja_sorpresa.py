# -*- coding: utf-8 -*-
"""
CAJA SORPRESA (trampa de Difícil / Imposible): caja de juguete con payaso de resorte.
Si pasas muy cerca... ¡BOING! se abre, salta el payaso y el ruido atrae a los cascanueces.
Piezas (para que Unity las anime por separado; mismo truco de pivotes que el elfo):
  CajaSorpresa (raíz, origen en la BASE)   = caja hueca de 4 paredes + piso, paneles de color, orillas doradas, manivela
    ├ Caja_Tapa    (origen en la BISAGRA, orilla de atrás arriba)  -> Unity la gira en X para abrir
    ├ Caja_Resorte (origen en el piso de la caja; resorte ESTIRADO de 0.5 m) -> Unity lo escala en Y (aplastado = 0.12)
    └ Caja_Payaso  (origen en la base de la cabeza)             -> Unity lo pone encima del resorte
Frente de la caja = -Y en Blender (+Z en Unity).
Uso: exec(modelado.py); exec(vista.py); exec(este); hacer_caja()
"""
import bpy, bmesh, math
from mathutils import Vector

ALTO = 0.5        # alto de la caja
LADO = 0.46       # ancho/fondo
PISO = 0.06       # grosor del piso (el resorte sale de aquí)
LARGO_RESORTE = 0.5


def caja_cuerpo(bm, M):
    h, l, g = ALTO, LADO, 0.03
    caja(bm, (0, 0, PISO / 2), (l, l, PISO), M["madera"], bisel=0.01)
    caja(bm, (0, -l / 2 + g / 2, h / 2), (l, g, h), M["rojo"], bisel=0.008)      # frente
    caja(bm, (0, l / 2 - g / 2, h / 2), (l, g, h), M["azul"], bisel=0.008)       # atrás
    caja(bm, (-l / 2 + g / 2, 0, h / 2), (g, l - 2 * g, h), M["verde"], bisel=0.008)
    caja(bm, (l / 2 - g / 2, 0, h / 2), (g, l - 2 * g, h), M["amarillo"], bisel=0.008)
    # paneles con estrella al frente y a los lados (un rombo en relieve + círculo)
    for (eje, s, col) in (("y", -1, "amarillo"), ("y", 1, "rojo"), ("x", -1, "rojo"), ("x", 1, "azul")):
        c = Vector((0, s * (l / 2 + 0.004), h / 2)) if eje == "y" else Vector((s * (l / 2 + 0.004), 0, h / 2))
        tam = (l * 0.62, 0.012, h * 0.62) if eje == "y" else (0.012, l * 0.62, h * 0.62)
        caja(bm, c, tam, M[col], bisel=0.006)
        rot = math.radians(45)
        # rombo (caja girada 45°) más adentro
        from mathutils import Matrix
        giro = Matrix.Rotation(rot, 3, "Y" if eje == "y" else "X")
        c2 = c + (Vector((0, s * 0.008, 0)) if eje == "y" else Vector((s * 0.008, 0, 0)))
        t2 = (l * 0.28, 0.01, l * 0.28) if eje == "y" else (0.01, l * 0.28, l * 0.28)
        caja(bm, c2, t2, M["blanco"], bisel=0.004, giro=giro)
    # orillas doradas en las 4 esquinas verticales y arriba
    for x in (-1, 1):
        for y in (-1, 1):
            loft(bm, [Vector((x * l / 2, y * l / 2, 0.0)), Vector((x * l / 2, y * l / 2, h))], [(0.018, 0.018)] * 2, M["oro"], segs=8, sub=1)
    esq = [Vector((-l / 2, -l / 2, 0)), Vector((l / 2, -l / 2, 0)), Vector((l / 2, l / 2, 0)), Vector((-l / 2, l / 2, 0))]
    for k in range(4):
        p0, p1 = esq[k], esq[(k + 1) % 4]
        for z in (h, 0.012):
            loft(bm, [p0 + Vector((0, 0, z)), p1 + Vector((0, 0, z))], [(0.016, 0.016)] * 2, M["oro"], segs=8, sub=1)
    # patitas redondas
    for x in (-1, 1):
        for y in (-1, 1):
            esfera(bm, (x * (l / 2 - 0.04), y * (l / 2 - 0.04), 0.0), (0.035, 0.035, 0.025), M["oro"], segs=12, anillos=6)
    # MANIVELA del lado derecho (+X): eje, brazo y perilla
    x0 = l / 2
    loft(bm, [Vector((x0, 0, h * 0.5)), Vector((x0 + 0.06, 0, h * 0.5))], [(0.014, 0.014)] * 2, M["oro"], segs=10, sub=1)
    esfera(bm, (x0 + 0.005, 0, h * 0.5), (0.012, 0.04, 0.04), M["oro"], segs=14, anillos=8)
    caja(bm, (x0 + 0.065, 0, h * 0.5 - 0.06), (0.018, 0.03, 0.15), M["oro"], bisel=0.006)
    loft(bm, [Vector((x0 + 0.065, 0, h * 0.5 - 0.12)), Vector((x0 + 0.12, 0, h * 0.5 - 0.12))], [(0.01, 0.01)] * 2, M["oro"], segs=8, sub=1)
    esfera(bm, (x0 + 0.13, 0, h * 0.5 - 0.12), (0.03, 0.025, 0.025), M["rojo"], segs=14, anillos=8)


def tapa(bm, M):
    # vértices relativos a la bisagra (orilla de atrás, arriba): la tapa se extiende hacia -Y
    l = LADO + 0.02
    caja(bm, (0, -l / 2, 0.015), (l, l, 0.03), M["rojo"], bisel=0.01)
    caja(bm, (0, -l / 2, 0.034), (l * 0.7, l * 0.7, 0.012), M["amarillo"], bisel=0.005)
    # moño de listón arriba
    esfera(bm, (0, -l / 2, 0.05), (0.03, 0.03, 0.022), M["azul"], segs=12, anillos=6)
    for s in (-1, 1):
        loft(bm, [Vector((0, -l / 2, 0.05)), Vector((s * 0.06, -l / 2 + 0.02, 0.07)), Vector((s * 0.09, -l / 2, 0.05)), Vector((s * 0.05, -l / 2 - 0.02, 0.045)), Vector((0, -l / 2, 0.05))],
             [(0.012, 0.025)] * 5, M["azul"], segs=8, sub=3)
    # bisagras
    for x in (-0.12, 0.12):
        loft(bm, [Vector((x - 0.03, 0, 0)), Vector((x + 0.03, 0, 0))], [(0.012, 0.012)] * 2, M["oro"], segs=8, sub=1)


def resorte(bm, M):
    # hélice de alambre: 8 vueltas, de z=0 a LARGO_RESORTE (relativo a su origen en el piso de la caja)
    pts, rad = [], []
    vueltas, n = 8, 8 * 14
    for i in range(n + 1):
        t = i / n
        a = t * vueltas * 2 * math.pi
        r = 0.065
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, t * LARGO_RESORTE)))
        rad.append((0.009, 0.009))
    loft(bm, pts, rad, M["metal"], segs=8, sub=1)
    # platito arriba (de ahí sale el cuello del payaso)
    loft(bm, [Vector((0, 0, LARGO_RESORTE - 0.01)), Vector((0, 0, LARGO_RESORTE + 0.01))], [(0.075, 0.075)] * 2, M["metal"], segs=18, sub=1)


def payaso(bm, M):
    # origen = base del cuello (encima del resorte)
    # cuello de olanes: 12 bolitas aplastadas alternando colores
    for k in range(12):
        a = k * 2 * math.pi / 12
        esfera(bm, (math.cos(a) * 0.085, math.sin(a) * 0.085, 0.02), (0.045, 0.045, 0.022), M["rojo" if k % 2 else "blanco"], segs=10, anillos=6)
    zc = 0.13   # centro de la cabeza
    esfera(bm, (0, 0, zc), (0.11, 0.105, 0.11), M["piel"], segs=24, anillos=14)
    esfera(bm, (0, -0.108, zc - 0.005), (0.03, 0.03, 0.03), M["rojo"], segs=14, anillos=8)          # nariz
    for s in (-1, 1):
        esfera(bm, (s * 0.04, -0.092, zc + 0.03), (0.016, 0.01, 0.022), M["negro"], segs=10, anillos=6)   # ojos
        esfera(bm, (s * 0.044, -0.1, zc + 0.038), (0.005, 0.004, 0.006), M["blanco"], segs=6, anillos=4)  # brillito
        esfera(bm, (s * 0.065, -0.08, zc - 0.02), (0.022, 0.01, 0.016), M["rosa"], segs=10, anillos=6)    # cachetes
        # cejas arqueadas (sorpresa)
        loft(bm, [Vector((s * 0.022, -0.099, zc + 0.065)), Vector((s * 0.04, -0.1, zc + 0.075)), Vector((s * 0.058, -0.096, zc + 0.066))], [(0.005, 0.005)] * 3, M["negro"], segs=6, sub=3)
        # pelo esponjado a los lados (naranja)
        for j in range(4):
            esfera(bm, (s * (0.1 + 0.012 * (j % 2)), 0.01 + (j - 1.5) * 0.03, zc + 0.02 + 0.02 * (j % 2)), (0.04, 0.035, 0.04), M["naranja"], segs=10, anillos=6)
    # sonrisa grande (arco rojo)
    arco = [Vector((math.sin(a) * 0.05, -0.1 + abs(math.sin(a)) * 0.012, zc - 0.045 + (1 - math.cos(a)) * 0.03)) for a in [math.radians(x) for x in range(-70, 71, 20)]]
    loft(bm, arco, [(0.008, 0.008)] * len(arco), M["rojo"], segs=6, sub=3)
    # gorro cónico de rayas con pompón (corto para que quepa con la tapa cerrada)
    z0 = zc + 0.075
    pasos = 5
    for i in range(pasos):
        a0, a1 = i / pasos, (i + 1) / pasos
        loft(bm, [Vector((0, 0.01, z0 + a0 * 0.13)), Vector((0, 0.01 + a1 * 0.01, z0 + a1 * 0.13))],
             [(0.085 * (1 - a0) + 0.008, 0.085 * (1 - a0) + 0.008), (0.085 * (1 - a1) + 0.008, 0.085 * (1 - a1) + 0.008)],
             M["azul" if i % 2 else "amarillo"], segs=18, sub=1, tapas=(i == 0, False))
    esfera(bm, (0, 0.02, z0 + 0.14), (0.025, 0.025, 0.025), M["blanco"], segs=12, anillos=8)


def hacer_caja():
    M = {
        "rojo": material("Caja_Rojo", (0.85, 0.1, 0.12), rugosidad=0.35),
        "azul": material("Caja_Azul", (0.12, 0.35, 0.9), rugosidad=0.35),
        "verde": material("Caja_Verde", (0.1, 0.65, 0.3), rugosidad=0.35),
        "amarillo": material("Caja_Amarillo", (1.0, 0.78, 0.15), rugosidad=0.35),
        "blanco": material("Caja_Blanco", (0.95, 0.95, 0.92), rugosidad=0.4),
        "oro": material("Caja_Oro", (1.0, 0.75, 0.3), metal=1.0, rugosidad=0.3),
        "madera": material("Caja_Madera", (0.45, 0.28, 0.15), rugosidad=0.7),
        "metal": material("Caja_Metal", (0.8, 0.82, 0.85), metal=1.0, rugosidad=0.25),
        "piel": material("Caja_Piel", (1.0, 0.86, 0.75), rugosidad=0.5),
        "negro": material("Caja_Negro", (0.03, 0.03, 0.04), rugosidad=0.3),
        "rosa": material("Caja_Rosa", (1.0, 0.5, 0.55), rugosidad=0.5),
        "naranja": material("Caja_Naranja", (1.0, 0.45, 0.1), rugosidad=0.6),
    }
    orden = ["rojo", "azul", "verde", "amarillo", "blanco", "oro", "madera", "metal", "piel", "negro", "rosa", "naranja"]
    mats = [M[k] for k in orden]
    I = {k: i for i, k in enumerate(orden)}

    col = bpy.data.collections.get("Trampas") or bpy.data.collections.new("Trampas")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)

    def obj(nombre, padre=None, pos=(0, 0, 0)):
        o = bpy.data.objects.get(nombre)
        if o is None:
            o = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre + "_tmp")); col.objects.link(o)
        o.parent = padre; o.location = pos; o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
        return o

    raiz = obj("CajaSorpresa"); raiz.location = (8, -6, 0)
    t = obj("Caja_Tapa", raiz, (0, LADO / 2 + 0.01, ALTO))
    r = obj("Caja_Resorte", raiz, (0, 0, PISO))
    p = obj("Caja_Payaso", raiz, (0, 0, PISO + LARGO_RESORTE))
    poner_malla(raiz, lambda bm: caja_cuerpo(bm, I), materiales=mats, subsurf=0)
    poner_malla(t, lambda bm: tapa(bm, I), materiales=mats, subsurf=0)
    poner_malla(r, lambda bm: resorte(bm, I), materiales=mats, subsurf=0)
    poner_malla(p, lambda bm: payaso(bm, I), materiales=mats, subsurf=0)
    for o in (raiz, t, r, p): o.data.name = o.name
    exportar_glb(con_hijos(raiz), "CajaSorpresa.glb", raiz=raiz)
    return {o.name: len(o.data.polygons) for o in (raiz, t, r, p)}
