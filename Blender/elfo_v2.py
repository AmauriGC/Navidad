# -*- coding: utf-8 -*-
"""
ELFO v2: rehace la malla de CADA pieza del elfo conservando nombre, origen (pivote) y jerarquía,
porque ElfoAnimador busca "PiernaL", "BrazoL", "Cabeza", "Gorro"... y gira cada pieza sobre su pivote.
Todo se modela en "coordenadas del elfo" (pies en z=0, mira a -Y) y luego se pasa al espacio local de cada pieza.
Uso:  exec(open(".../Blender/modelado.py").read()); exec(open(".../Blender/elfo_v2.py").read())
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

RAIZ = bpy.data.objects["Elfo"]


def parte(nombre, construir, materiales=None):
    """Construye en coordenadas del elfo y convierte al espacio local de la pieza 'nombre'."""
    obj = bpy.data.objects[nombre]
    M = obj.matrix_world.inverted() @ RAIZ.matrix_world
    def envuelto(bm):
        construir(bm)
        bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    poner_malla(obj, envuelto, materiales=materiales)


def mat(n): return bpy.data.materials[n]


# ------------------------------------------------------------------ torso
def cuerpo(bm):
    # túnica: más angosta en los hombros, panza redondita
    loft(bm, [(0, 0, 0.38), (0, -0.005, 0.5), (0, -0.01, 0.62), (0, 0, 0.74), (0, 0.005, 0.82)],
         [(0.19, 0.165), (0.2, 0.175), (0.19, 0.168), (0.165, 0.145), (0.11, 0.1)], segs=22, sub=3, domo=0.3)

def cuello(bm):
    # cuello de picos (como hojas) rojo alrededor del cuello
    n = 8
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Vector((math.sin(a), -math.cos(a), 0))
        base = Vector((0, 0, 0.815)) + d * 0.09
        punta = Vector((0, 0, 0.775)) + d * 0.2
        loft(bm, [tuple(base), tuple(base.lerp(punta, 0.5) + Vector((0, 0, 0.01))), tuple(punta)],
             [(0.045, 0.012), (0.05, 0.014), (0.006, 0.005)], segs=8, sub=2, domo=0.4, arriba=Vector((0, 0, 1)))
    toro(bm, (0, 0, 0.82), 0.1, 0.025, segs=20, lados=6)

def falda(bm):
    # orilla de la túnica con 8 picos redondeados (una "campana" con borde en onda)
    n, filas = 64, 5
    anillos = []
    for i in range(filas):
        t = i / (filas - 1)
        z = 0.5 - 0.15 * t
        ring = []
        for j in range(n):
            a = 2 * math.pi * j / n
            onda = 0.5 + 0.5 * math.cos(8 * a)               # 8 picos
            r = 0.2 + 0.035 * t + 0.008 * t * onda
            zz = z - 0.05 * t * onda * t
            ring.append(bm.verts.new((r * math.sin(a), -r * math.cos(a) * 0.92, zz)))
        anillos.append(ring)
    for i in range(filas - 1):
        for j in range(n):
            f = bm.faces.new((anillos[i][j], anillos[i][(j + 1) % n], anillos[i + 1][(j + 1) % n], anillos[i + 1][j]))
            f.smooth = True
    # orilla gruesita hacia adentro (para que no se vea de papel)
    ult = anillos[-1]
    dentro = [bm.verts.new(v.co * Vector((0.9, 0.9, 1)) + Vector((0, 0, 0.02))) for v in ult]
    for j in range(n):
        f = bm.faces.new((ult[j], dentro[j], dentro[(j + 1) % n], ult[(j + 1) % n])); f.smooth = True

def cinturon(bm):
    loft(bm, [(-0.0, 0, 0.5)], [(0.2, 0.18)], segs=1) if False else None
    toro(bm, (0, 0, 0.5), 0.188, 0.028, segs=32, lados=6)

def hebilla(bm):
    caja(bm, (0, -0.205, 0.5), (0.085, 0.02, 0.07), bisel=0.008, segs=2)

def boton(z, y):
    def b(bm):
        esfera(bm, (0, y, z), (0.02, 0.012, 0.02), segs=12, anillos=8)
    return b

# ------------------------------------------------------------------ brazos
def brazo(s):
    def b(bm):
        # manga que se ensancha hacia la muñeca
        loft(bm, [(s * 0.175, 0, 0.75), (s * 0.215, 0, 0.66), (s * 0.235, -0.005, 0.57), (s * 0.24, -0.005, 0.53)],
             [(0.048, 0.045), (0.05, 0.047), (0.058, 0.055), (0.062, 0.06)], segs=14, sub=3, tapas=(True, False), domo=0.5)
    return b

def hombro(s):
    def b(bm):
        esfera(bm, (s * 0.175, 0, 0.745), (0.06, 0.058, 0.055))
    return b

def puno(s):
    def b(bm):
        toro(bm, (s * 0.24, -0.005, 0.525), 0.055, 0.02, segs=18, lados=6)
    return b

def mano(s):
    def b(bm):
        esfera(bm, (s * 0.24, -0.005, 0.47), (0.045, 0.04, 0.052))                          # palma (manopla)
        loft(bm, [(s * 0.215, -0.035, 0.49), (s * 0.205, -0.055, 0.465)], [(0.016, 0.016), (0.014, 0.014)],
             segs=8, sub=2, domo=0.9)                                                          # pulgar
    return b

# ------------------------------------------------------------------ cabeza
def cabeza(bm, segs=32, anillos=22):
    # cabeza = esfera deformada (v3, 25-nov): la versión de anillos + tapa plana dejaba la "mollera sumida" arriba
    # y picos en el cráneo. Aquí cada punto sale de una esfera lisa: cachetes un poco más anchos, barbilla más
    # angosta, nuca redonda. Misma caja que antes (z 0.86..1.215, ancho 0.39, fondo 0.36).
    zc, rz_arr, rz_ab = 1.04, 0.175, 0.18
    filas = []
    for i in range(1, anillos):
        t = -math.pi / 2 + math.pi * i / anillos           # latitud
        s, c = math.sin(t), math.cos(t)
        z = zc + s * (rz_arr if s > 0 else rz_ab)
        ancho = 1.0 + 0.05 * math.exp(-((s + 0.25) / 0.3) ** 2) - (0.22 * (-s) ** 2 if s < 0 else 0.0)   # cachetes / barbilla
        fila = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            x = math.sin(a) * c * 0.195 * ancho
            y = -math.cos(a) * c * 0.18 * (ancho if math.cos(a) > 0 else 1.0)   # la nuca no se angosta
            fila.append(bm.verts.new((x, y + 0.003, z)))
        filas.append(fila)
    for f0, f1 in zip(filas, filas[1:]):
        for k in range(segs):
            bm.faces.new((f0[k], f0[(k + 1) % segs], f1[(k + 1) % segs], f1[k]))
    abajo = bm.verts.new((0, 0.003, zc - rz_ab)); arriba = bm.verts.new((0, 0.003, zc + rz_arr))
    for k in range(segs):
        bm.faces.new((abajo, filas[0][(k + 1) % segs], filas[0][k]))
        bm.faces.new((arriba, filas[-1][k], filas[-1][(k + 1) % segs]))
    # CUELLO (25-nov): la esfera termina angosta abajo y entre la barbilla y el cuello de picos se veía un hueco.
    # Un tubo de piel que entra en el cuerpo (z 0.76) y en la cabeza (z 0.97) tapa la unión aunque la cabeza se mueva.
    loft(bm, [(0, 0.012, 0.76), (0, 0.01, 0.84), (0, 0.006, 0.9), (0, 0.003, 0.97)],
         [(0.075, 0.07), (0.072, 0.068), (0.085, 0.08), (0.11, 0.1)], segs=20, sub=2, domo=0.3)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces: f.smooth = True

def oreja(s):
    def b(bm):
        # oreja de elfo: hoja puntiaguda que sale hacia el lado y hacia arriba
        loft(bm, [(s * 0.17, 0.03, 1.05), (s * 0.22, 0.04, 1.09), (s * 0.28, 0.06, 1.15), (s * 0.32, 0.08, 1.2)],
             [(0.045, 0.018), (0.04, 0.016), (0.022, 0.011), (0.004, 0.004)], segs=10, sub=3, domo=0.3,
             arriba=Vector((0, 1, 0)))
    return b

def nariz(bm):
    esfera(bm, (0, -0.2, 1.0), (0.03, 0.032, 0.028))

def ojo(s):
    def b(bm):
        esfera(bm, (s * 0.068, -0.172, 1.065), (0.026, 0.014, 0.036), segs=14, anillos=8)
    return b

def brillo(s):
    def b(bm):
        esfera(bm, (s * 0.074, -0.186, 1.08), (0.008, 0.004, 0.009), segs=8, anillos=5)
    return b

def mejilla(s):
    def b(bm):
        esfera(bm, (s * 0.115, -0.15, 0.995), (0.034, 0.012, 0.022), segs=12, anillos=6)
    return b

def boca(bm):
    # sonrisa (arco) + cejas cafés
    arco = [(0.045 * math.sin(a), -0.188 + 0.02 * (1 - math.cos(a)), 0.948 + 0.018 * (1 - math.cos(a)))
            for a in (-1.1, -0.55, 0, 0.55, 1.1)]
    loft(bm, arco, [(0.007, 0.007)] * 5, segs=8, sub=3, domo=0.9)
    for s in (-1, 1):
        loft(bm, [(s * 0.04, -0.175, 1.118), (s * 0.07, -0.172, 1.128), (s * 0.1, -0.158, 1.122)],
             [(0.007, 0.008), (0.009, 0.01), (0.005, 0.006)], segs=8, sub=2, domo=0.9)

# ------------------------------------------------------------------ gorro
def gorro(bm):
    # cono que se dobla hacia atrás y cuelga, termina donde está el cascabel
    loft(bm, [(0, 0.0, 1.13), (0, 0.01, 1.24), (0, 0.06, 1.35), (0, 0.17, 1.44), (0, 0.29, 1.46), (0, 0.36, 1.43)],
         [(0.205, 0.2), (0.17, 0.165), (0.12, 0.115), (0.075, 0.07), (0.04, 0.038), (0.02, 0.02)], segs=22, sub=4, domo=0.4)

def gorro_borde(bm):
    # orilla de peluche esponjada: dona con bultitos
    n, lados = 48, 8
    filas = []
    for i in range(n):
        a = 2 * math.pi * i / n
        bulto = 1 + 0.12 * math.cos(12 * a)
        R, r = 0.205, 0.038 * bulto
        fila = []
        for j in range(lados):
            b = 2 * math.pi * j / lados
            fila.append(bm.verts.new(((R + r * math.cos(b)) * math.sin(a), -(R + r * math.cos(b)) * math.cos(a), 1.125 + r * 1.1 * math.sin(b))))
        filas.append(fila)
    for i in range(n):
        for j in range(lados):
            f = bm.faces.new((filas[i][j], filas[(i + 1) % n][j], filas[(i + 1) % n][(j + 1) % lados], filas[i][(j + 1) % lados]))
            f.smooth = True

def cascabel(bm):
    c = Vector((0, 0.375, 1.405))
    esfera(bm, tuple(c), (0.045, 0.045, 0.045))
    toro(bm, tuple(c + Vector((0, 0, 0.045))), 0.012, 0.005, segs=10, lados=4)
    loft(bm, [tuple(c + Vector((-0.03, -0.0, -0.01))), tuple(c + Vector((0.03, 0, -0.01)))], [(0.006, 0.006)] * 2, segs=6, sub=1)

# ------------------------------------------------------------------ piernas y zapatos
def pierna(s):
    def b(bm):
        loft(bm, [(s * 0.085, 0, 0.4), (s * 0.085, 0, 0.24), (s * 0.085, 0, 0.08)],
             [(0.058, 0.058), (0.052, 0.052), (0.048, 0.048)], segs=16, sub=2, domo=0.3)
    return b

def raya(s, z):
    def b(bm):
        toro(bm, (s * 0.085, 0, z), 0.054 - (0.4 - z) * 0.02, 0.016, segs=20, lados=6)
    return b

def zapato(s):
    def b(bm):
        x = s * 0.085
        # zapato de elfo: puntiagudo y se enrosca hacia arriba al frente
        loft(bm, [(x, 0.07, 0.05), (x, 0.0, 0.055), (x, -0.08, 0.05), (x, -0.15, 0.06)],
             [(0.06, 0.05), (0.068, 0.058), (0.06, 0.045), (0.042, 0.032)], segs=16, sub=3, tapas=(True, False), domo=0.6)
        loft(bm, [(x, 0.0, 0.04), (x, 0.0, 0.1)], [(0.058, 0.055), (0.055, 0.052)], segs=16, sub=1, domo=0.2)   # tobillo
        toro(bm, (x, 0.0, 0.105), 0.056, 0.014, segs=16, lados=6)                                            # orilla
    return b

def punta(s):
    def b(bm):
        x = s * 0.085
        loft(bm, [(x, -0.15, 0.06), (x, -0.2, 0.08), (x, -0.225, 0.12), (x, -0.215, 0.16), (x, -0.19, 0.17)],
             [(0.042, 0.032), (0.03, 0.025), (0.02, 0.018), (0.012, 0.011), (0.006, 0.006)], segs=12, sub=3, tapas=(False, True), domo=0.6)
    return b

def cascabel_pie(s):
    def b(bm):
        c = (s * 0.085, -0.19, 0.19)
        esfera(bm, c, (0.024, 0.024, 0.024), segs=12, anillos=8)
    return b


PARTES = {
    "Cuerpo": cuerpo, "Cuello": cuello, "Falda": falda, "Cinturon": cinturon, "Hebilla": hebilla,
    "Boton0": boton(0.65, -0.18), "Boton1": boton(0.73, -0.163),
    "Cabeza": cabeza, "Nariz": nariz, "Boca": boca, "Gorro": gorro, "GorroBorde": gorro_borde, "Cascabel": cascabel,
}
for s, L in ((1, "L"), (-1, "R")):
    PARTES.update({
        "Brazo" + L: brazo(s), "Hombro" + L: hombro(s), "Puno" + L: puno(s), "Mano" + L: mano(s),
        "Oreja" + L: oreja(s), "Ojo" + L: ojo(s), "Brillo" + L: brillo(s), "Mejilla" + L: mejilla(s),
        "Pierna" + L: pierna(s), "Raya" + L + "0": raya(s, 0.16), "Raya" + L + "1": raya(s, 0.28),
        "Zapato" + L: zapato(s), "Punta" + L: punta(s), "CascabelPie" + L: cascabel_pie(s),
    })
for n, f in PARTES.items():
    obj = bpy.data.objects[n]
    parte(n, f, materiales=[obj.material_slots[0].material])
print("elfo v2 listo:", len(PARTES), "piezas")
