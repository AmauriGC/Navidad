# -*- coding: utf-8 -*-
"""
TRINEO v2 y SANTA v2 (Blender).  Reemplaza la malla de los objetos 'Trineo' (establo) y 'TrineoSanta' (final),
conservando sus nombres y orígenes. Ejes: frente = -Y, arriba = +Z, el piso en z = 0.
Uso:  exec(open(".../Blender/modelado.py").read()); exec(open(".../Blender/trineo_santa.py").read())
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

MATS = [bpy.data.materials["Cas_Oro"], bpy.data.materials["Tri_Rojo"], bpy.data.materials["Tri_Asiento"],
        bpy.data.materials["Tri_Costal"], bpy.data.materials["Amb_FocoRojo"], bpy.data.materials["Amb_FocoVerde"],
        bpy.data.materials["Amb_FocoAzul"], bpy.data.materials["Santa_Rojo"], bpy.data.materials["Cas_Negro"],
        bpy.data.materials["Cas_Piel"], bpy.data.materials["Santa_Blanco"],
        material("Acebo_Verde", (0.05, 0.3, 0.1), rugosidad=0.4), material("Santa_Mejilla", (0.95, 0.45, 0.42), rugosidad=0.7)]
ORO, ROJO, COJIN, COSTAL, F_ROJO, F_VERDE, F_AZUL, S_ROJO, NEGRO, PIEL, BLANCO, ACEBO, MEJILLA = range(13)

# ------------------------------------------------------------------ la "tina" del trineo
# secciones de adelante (-Y) hacia atrás (+Y): (y, medio ancho, z del fondo, z de la orilla)
SECCIONES = [(-1.05, 0.46, 0.66, 0.96), (-0.88, 0.57, 0.52, 1.12), (-0.62, 0.62, 0.47, 0.97), (-0.30, 0.64, 0.45, 0.80),
             (0.10, 0.64, 0.45, 0.80), (0.45, 0.64, 0.46, 1.00), (0.74, 0.62, 0.48, 1.30), (0.96, 0.57, 0.53, 1.40)]


def perfil_u(w, zb, zt, grosor=0.05, r=0.14, n_arco=5):
    """Contorno cerrado de una sección en U (pared exterior + pared interior) en el plano XZ."""
    ext, inte = [], []
    wt = w * 1.06                         # las paredes se abren un poco hacia arriba
    ext.append((-wt, zt))
    for k in range(n_arco + 1):           # esquina redonda izquierda
        a = math.pi + (math.pi / 2) * k / n_arco
        ext.append((-w + r + r * math.cos(a), zb + r + r * math.sin(a)))
    for k in range(n_arco + 1):           # esquina redonda derecha
        a = 1.5 * math.pi + (math.pi / 2) * k / n_arco
        ext.append((w - r + r * math.cos(a), zb + r + r * math.sin(a)))
    ext.append((wt, zt))
    for (x, z) in reversed(ext):          # pared interior: el mismo contorno hacia adentro
        dx = -grosor if x > 0 else grosor
        inte.append((x + dx * (1 if abs(x) > 0.05 else 0), max(z, zb) + (grosor if z < zt - 0.01 else 0)))
    return ext + inte


def tina(bm, mat=ROJO, sub=3):
    # interpolar las secciones con Catmull-Rom (suave) y construir anillos
    ys = [s[0] for s in SECCIONES]
    pts, rad = suavizar_camino([(s[1], s[0], s[2]) for s in SECCIONES], [(s[3], 0) for s in SECCIONES], sub)
    anillos = []
    for p, (zt, _) in zip(pts, rad):
        w, y, zb = p.x, p.y, p.z
        anillos.append([bm.verts.new((x, y, z)) for (x, z) in perfil_u(w, zb, zt)])
    m = len(anillos[0])
    for i in range(len(anillos) - 1):
        a, b = anillos[i], anillos[i + 1]
        for j in range(m):
            f = bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j])); f.material_index = mat; f.smooth = True
    for an in (anillos[0], anillos[-1]):   # tapas adelante y atrás
        f = bm.faces.new(an if an is anillos[-1] else list(reversed(an))); f.material_index = mat
    return pts, rad


def orilla(i_sec, lado):
    """Punto de la orilla superior (exterior) de una sección interpolada."""
    return None


def trineo(bm):
    pts, rad = tina(bm)
    # barandal dorado sobre la orilla de cada lado + foquitos de colores colgando abajo del barandal
    for s in (-1, 1):
        camino = [(s * p.x * 1.06, p.y, zt + 0.015) for p, (zt, _) in zip(pts, rad)]
        loft(bm, camino, [(0.03, 0.03)] * len(camino), mat=ORO, segs=8, sub=2, domo=0.8)
        for k in range(2, len(camino) - 2, 2):
            x, y, z = camino[k]
            esfera(bm, (x + s * 0.012, y, z - 0.07), (0.022, 0.022, 0.03), mat=(F_ROJO, F_VERDE, F_AZUL)[(k // 2) % 3], segs=10, anillos=6)
            esfera(bm, (x + s * 0.004, y, z - 0.008), (0.033, 0.033, 0.012), mat=ORO, segs=8, anillos=4)   # remache
        # voluta (espiral) dorada en la esquina de adelante y en la de atrás
        for (y0, z0, sentido) in ((-0.96, 1.08, -1), (0.92, 1.38, 1)):
            espiral = []
            for k in range(14):
                a = k * 0.5
                r = 0.13 * (1 - k / 16)
                espiral.append((s * 0.6, y0 + sentido * r * math.sin(a), z0 - r * (1 - math.cos(a))))
            loft(bm, espiral, [(0.028 * (1 - k / 20), 0.028 * (1 - k / 20)) for k in range(14)], mat=ORO, segs=8, sub=2, domo=0.9)
        # patín dorado continuo (de atrás, por el piso, y adelante sube en espiral)
        x = s * 0.55
        patin = [(x, 1.18, 0.24), (x, 1.05, 0.08), (x, 0.6, 0.05), (x, -0.4, 0.05), (x, -0.95, 0.07), (x, -1.22, 0.16),
                 (x, -1.38, 0.38), (x, -1.32, 0.60), (x, -1.15, 0.67), (x, -1.03, 0.58), (x, -1.07, 0.46), (x, -1.17, 0.48)]
        loft(bm, patin, [(0.04, 0.034)] * 9 + [(0.034, 0.03), (0.03, 0.026), (0.026, 0.024)], mat=ORO, segs=10, sub=4, domo=0.9)
        # soportes curvos del patín a la tina
        for y in (-0.62, 0.05, 0.68):
            loft(bm, [(x, y, 0.06), (x * 0.98, y, 0.26), (x * 0.86, y, 0.50)], [(0.03, 0.03), (0.026, 0.026), (0.034, 0.034)],
                 mat=ORO, segs=8, sub=3, tapas=(False, False))
    # cojín del asiento y respaldo acolchado con botones dorados
    caja(bm, (0, 0.28, 0.63), (1.08, 0.62, 0.17), mat=COJIN, bisel=0.07, segs=3)
    caja(bm, (0, 0.74, 0.98), (1.02, 0.16, 0.5), mat=COJIN, bisel=0.07, segs=3, giro=Matrix.Rotation(math.radians(-12), 3, "X"))
    for bx in (-0.3, 0, 0.3):
        for bz in (0.88, 1.08):
            esfera(bm, (bx, 0.645 + (bz - 0.98) * 0.21, bz), (0.022, 0.015, 0.022), mat=ORO, segs=8, anillos=5)
    # acebo al frente (3 hojas + 3 bayas)
    for k, ang in enumerate((-35, 0, 35)):
        a = math.radians(ang)
        base = Vector((0, -1.0, 1.08))
        d = Vector((math.sin(a), -0.25, math.cos(a))).normalized()
        loft(bm, [tuple(base), tuple(base + d * 0.09), tuple(base + d * 0.18)], [(0.01, 0.004), (0.05, 0.008), (0.005, 0.003)],
             mat=ACEBO, segs=8, sub=3, domo=0.3, arriba=Vector((0, 1, 0)))
    for (bx, bz) in ((-0.03, 1.1), (0.03, 1.1), (0, 1.14)):
        esfera(bm, (bx, -1.03, bz), (0.028, 0.028, 0.028), mat=F_ROJO, segs=10, anillos=6)


def costal(bm, centro, escala=1.0, seed=3):
    """Costal de tela con regalos asomándose."""
    rnd = random.Random(seed)
    cx, cy, cz = centro
    e = escala
    loft(bm, [(cx, cy, cz), (cx, cy, cz + 0.14 * e), (cx + 0.01, cy, cz + 0.3 * e), (cx + 0.02, cy + 0.01, cz + 0.42 * e), (cx + 0.02, cy + 0.01, cz + 0.5 * e)],
         [(0.2 * e, 0.18 * e), (0.27 * e, 0.25 * e), (0.25 * e, 0.24 * e), (0.12 * e, 0.11 * e), (0.07 * e, 0.07 * e)], mat=COSTAL, segs=16, sub=3, domo=0.4)
    toro(bm, (cx + 0.02, cy + 0.01, cz + 0.47 * e), 0.075 * e, 0.016 * e, mat=ORO, segs=16, lados=6)
    loft(bm, [(cx + 0.02, cy + 0.01, cz + 0.5 * e), (cx + 0.03, cy, cz + 0.56 * e)], [(0.08 * e, 0.075 * e), (0.13 * e, 0.12 * e)],
         mat=COSTAL, segs=16, sub=2, tapas=(False, True), domo=0.1)
    for k, (dx, dy, col) in enumerate(((-0.06, -0.03, F_VERDE), (0.07, 0.04, F_AZUL), (0.0, 0.08, ROJO))):
        giro = Matrix.Rotation(rnd.uniform(-0.4, 0.4), 3, "X") @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 3, "Y")
        c = Vector((cx + dx * e, cy + dy * e, cz + (0.62 + 0.03 * k) * e))
        t = (0.13 - 0.02 * k) * e
        caja(bm, tuple(c), (t, t, t), mat=col, bisel=0.012, segs=2, giro=giro)
        caja(bm, tuple(c), (t * 1.04, t * 0.22, t * 1.04), mat=ORO, bisel=0.004, segs=1, giro=giro)   # listón
        caja(bm, tuple(c), (t * 0.22, t * 1.04, t * 1.04), mat=ORO, bisel=0.004, segs=1, giro=giro)


def santa(bm, cx=0.12):
    """Santa sentado en el cojín, mirando al frente (-Y), con las riendas en las manos."""
    # cuerpo: panza redonda (los centros se adelantan un poco a la altura de la panza)
    loft(bm, [(cx, 0.32, 0.72), (cx, 0.29, 0.85), (cx, 0.26, 0.98), (cx, 0.27, 1.15), (cx, 0.29, 1.32), (cx, 0.30, 1.45), (cx, 0.30, 1.53)],
         [(0.27, 0.25), (0.33, 0.31), (0.355, 0.335), (0.31, 0.29), (0.26, 0.24), (0.17, 0.16), (0.10, 0.10)], mat=S_ROJO, segs=20, sub=3, domo=0.3)
    esfera(bm, (cx, -0.03, 1.13), (0.06, 0.035, 0.3), mat=BLANCO)                       # franja de peluche al frente
    toro(bm, (cx, 0.31, 0.77), 0.285, 0.05, mat=BLANCO, segs=28, lados=8)                 # orilla de peluche abajo
    toro(bm, (cx, 0.265, 0.95), 0.345, 0.034, mat=NEGRO, segs=28, lados=6)                # cinturón
    caja(bm, (cx, -0.085, 0.95), (0.13, 0.035, 0.1), mat=ORO, bisel=0.012)                # hebilla
    caja(bm, (cx, -0.1, 0.95), (0.07, 0.01, 0.05), mat=NEGRO, bisel=0.005, segs=1)
    for s in (-1, 1):
        x = cx + s * 0.15
        loft(bm, [(x, 0.30, 0.84), (x, 0.05, 0.84), (x, -0.13, 0.80)], [(0.13, 0.12), (0.125, 0.115), (0.12, 0.11)], mat=S_ROJO, segs=14, sub=3, domo=0.6)
        loft(bm, [(x, -0.14, 0.80), (x, -0.17, 0.68), (x, -0.18, 0.60)], [(0.105, 0.1), (0.095, 0.09), (0.09, 0.09)], mat=S_ROJO, segs=14, sub=2, tapas=(False, False))
        toro(bm, (x, -0.18, 0.64), 0.098, 0.03, mat=BLANCO, segs=16, lados=6)              # peluche de la bota
        loft(bm, [(x, -0.15, 0.60), (x, -0.22, 0.57), (x, -0.33, 0.56)], [(0.095, 0.08), (0.09, 0.075), (0.065, 0.06)], mat=NEGRO, segs=14, sub=2, domo=0.8)
        # brazos: hombro -> codo -> mano (sostiene las riendas)
        loft(bm, [(cx + s * 0.27, 0.30, 1.38), (cx + s * 0.37, 0.20, 1.13), (cx + s * 0.25, -0.05, 1.05)],
             [(0.095, 0.095), (0.085, 0.085), (0.075, 0.075)], mat=S_ROJO, segs=12, sub=4, domo=0.5)
        toro(bm, (cx + s * 0.255, -0.06, 1.05), 0.075, 0.028, mat=BLANCO, segs=14, lados=6, inclinacion=math.radians(80))
        esfera(bm, (cx + s * 0.24, -0.13, 1.05), (0.07, 0.075, 0.068), mat=NEGRO)            # guante
        # riendas hacia el frente del trineo
        loft(bm, [(cx + s * 0.24, -0.16, 1.05), (cx * 0.5 + s * 0.2, -0.6, 1.06), (s * 0.17, -1.0, 1.12), (s * 0.15, -1.3, 0.95)],
             [(0.012, 0.012)] * 4, mat=NEGRO, segs=6, sub=3)
    # cabeza
    hx, hy, hz = cx, 0.26, 1.70
    esfera(bm, (hx, hy, hz), (0.165, 0.155, 0.175), mat=PIEL)
    esfera(bm, (hx, hy - 0.16, hz - 0.01), (0.042, 0.04, 0.038), mat=MEJILLA)                 # nariz
    for s in (-1, 1):
        esfera(bm, (hx + s * 0.085, hy - 0.125, hz - 0.03), (0.04, 0.02, 0.03), mat=MEJILLA)    # cachetes
        esfera(bm, (hx + s * 0.06, hy - 0.142, hz + 0.045), (0.02, 0.014, 0.024), mat=NEGRO, segs=10, anillos=6)   # ojos
        esfera(bm, (hx + s * 0.055, hy - 0.155, hz + 0.055), (0.006, 0.004, 0.006), mat=BLANCO, segs=6, anillos=4)
        loft(bm, [(hx + s * 0.03, hy - 0.14, hz + 0.09), (hx + s * 0.07, hy - 0.14, hz + 0.105), (hx + s * 0.11, hy - 0.12, hz + 0.095)],
             [(0.016, 0.02), (0.022, 0.024), (0.012, 0.014)], mat=BLANCO, segs=8, sub=2, domo=0.8)   # cejas pobladas
        # bigote rizado
        loft(bm, [(hx, hy - 0.175, hz - 0.055), (hx + s * 0.06, hy - 0.17, hz - 0.065), (hx + s * 0.12, hy - 0.14, hz - 0.045), (hx + s * 0.15, hy - 0.12, hz - 0.01)],
             [(0.035, 0.03), (0.04, 0.032), (0.025, 0.022), (0.01, 0.01)], mat=BLANCO, segs=10, sub=3, domo=0.7)
    # barba esponjada: una base y "nubecitas" alrededor
    esfera(bm, (hx, hy - 0.07, hz - 0.17), (0.17, 0.11, 0.17), mat=BLANCO)
    for k in range(-3, 4):
        esfera(bm, (hx + k * 0.052, hy - 0.11 + abs(k) * 0.012, hz - 0.3 + abs(k) * 0.045), (0.07, 0.06, 0.08), mat=BLANCO, segs=12, anillos=8)
    for s in (-1, 1):
        esfera(bm, (hx + s * 0.15, hy - 0.04, hz - 0.08), (0.06, 0.07, 0.1), mat=BLANCO, segs=12, anillos=8)
    # gorro doblado hacia atrás con pompón
    toro(bm, (hx, hy + 0.01, hz + 0.12), 0.158, 0.048, mat=BLANCO, segs=24, lados=8, inclinacion=math.radians(8))
    loft(bm, [(hx, hy + 0.02, hz + 0.13), (hx, hy + 0.04, hz + 0.28), (hx, hy + 0.13, hz + 0.40), (hx, hy + 0.27, hz + 0.42), (hx, hy + 0.35, hz + 0.33)],
         [(0.16, 0.155), (0.13, 0.125), (0.09, 0.085), (0.055, 0.05), (0.03, 0.03)], mat=S_ROJO, segs=16, sub=3, domo=0.5)
    esfera(bm, (hx, hy + 0.37, hz + 0.29), (0.065, 0.065, 0.065), mat=BLANCO)


def trineo_vacio(bm):
    trineo(bm)
    costal(bm, (0.25, 0.32, 0.71), 1.15, seed=7)


def trineo_con_santa(bm):
    trineo(bm)
    santa(bm, cx=0.12)
    costal(bm, (-0.33, 0.36, 0.71), 0.9, seed=3)


poner_malla(bpy.data.objects["Trineo"], trineo_vacio, materiales=MATS)
poner_malla(bpy.data.objects["TrineoSanta"], trineo_con_santa, materiales=MATS)
print("trineos v2 listos")
