# -*- coding: utf-8 -*-
"""
MUÑECO DE NIEVE v3 (26-nov, low-poly redondeado; basado en v2 = muneco.py) (malla "MunecoNieve.002" del objeto MunecoNieve; mira hacia -Y local).
Mismos lugares que el anterior para que la ZANAHORIA del juego (Pieza_Zanahoria) siga quedando en su nariz:
cabeza con centro en (0, 0, 2.35).
  - 3 bolas "esponjadas": esferas con ruido suave (grumitos de nieve) y un poco achatadas por el peso.
  - Montoncito de nieve en la base para que no se vea pegado al suelo.
  - Cara: ojos de carbón con brillito, sonrisa de 5 piedritas, cachetes chapeados (rojo achatado).
  - Botones de carbón sobre la superficie de la bola de en medio.
  - Bufanda: dona tejida (anillos marcados) + dos colas con flecos.
  - Sombrero de copa: ala redondeada, copa, cinta roja y ramita de acebo (2 hojas + 3 bayas).
  - Brazos de rama con deditos (uno saludando).
Materiales: 0 nieve, 1 carbón, 2 bufanda, 3 metal negro (sombrero), 4 rojo, 5 madera, 6 verde (acebo).
v3: bolas = icoesferas FACETADAS (sombreado plano) con grumitos; base = montón de nieve con grumos (antes
parecía una llanta) + 3 bolitas al pie; 3 botones en medio y 2 abajo, más grandes; colas de la bufanda a un lado.
Uso: exec(modelado.py); exec(muneco_v3.py); hacer_muneco()
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

NIE, CAR, BUF, NEG, ROJ, MAD, VER = range(7)

def bola(bm, centro, r, achatar=0.94, grumos=0.035, semilla=0, sub=3, plano=True):
    """Bola de nieve low-poly redondeada: icoesfera (caras parejas) con ruido suave, sombreado PLANO."""
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = Vector((semilla * 3.1, semilla * 1.7, semilla * 2.3))
    for v in res["verts"]:
        n = v.co.normalized()
        d = 1 + grumos * noise.noise(n * 2.2 + off) + grumos * 0.5 * noise.noise(n * 5 + off)
        v.co = Vector(centro) + Vector((n.x * r * d, n.y * r * d, n.z * r * d * achatar))
    caras = list({f for v in res["verts"] for f in v.link_faces})
    for f in caras: f.material_index = NIE; f.smooth = not plano
    return caras

def en_superficie(centro, r, achatar, direccion, salir=0.0):
    d = Vector(direccion).normalized()
    p = Vector((d.x * r, d.y * r, d.z * r * achatar))
    return Vector(centro) + p + d * salir

def piedrita(bm, p, normal, tam, mat=CAR, aplastar=0.55):
    """Carbón: esfera achatada en la dirección de la normal (pegada a la superficie)."""
    res = bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=1.0)
    rot = Vector(normal).normalized().to_track_quat("Z", "Y").to_matrix()
    for v in res["verts"]:
        v.co = p + rot @ Vector((v.co.x * tam, v.co.y * tam, v.co.z * tam * aplastar))
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mat; f.smooth = True

def hacer_muneco(semilla=3):
    rnd = random.Random(semilla)
    me = bpy.data.meshes["MunecoNieve.002"]
    # material verde para el acebo (si la malla no lo tiene todavía)
    if len(me.materials) < 7: me.materials.append(bpy.data.materials["Amb_VerdePino"])
    bm = bmesh.new()
    B1, R1, A1 = (0, 0, 0.55), 0.72, 0.92
    B2, R2, A2 = (0, 0, 1.55), 0.52, 0.93
    B3, R3, A3 = (0, 0, 2.35), 0.38, 0.97
    bola(bm, B1, R1, A1, grumos=0.05, semilla=1); bola(bm, B2, R2, A2, grumos=0.05, semilla=2); bola(bm, B3, R3, A3, grumos=0.03, semilla=3)
    # montón de nieve de la base: domo bajito con grumos (se funde con la bola de abajo y con el suelo)
    for f in bola(bm, (0, 0, -0.12), 0.98, achatar=0.3, grumos=0.12, semilla=7): pass
    for k, (a, rr) in enumerate(((0.3, 0.88), (1.9, 0.92), (3.9, 0.86))):
        bola(bm, (math.cos(a) * rr, math.sin(a) * rr, 0.0), 0.12 + 0.03 * (k % 2), achatar=0.85, grumos=0.08, semilla=20 + k, sub=2)
    bola(bm, (math.cos(0.3) * 0.88 + 0.05, math.sin(0.3) * 0.88 - 0.13, 0.16), 0.09, achatar=0.9, grumos=0.08, semilla=30, sub=2)
    # --- cara
    for s in (-1, 1):
        d = Vector((s * 0.36, -1, 0.34))
        p = en_superficie(B3, R3, A3, d)
        piedrita(bm, p, d, 0.048, aplastar=0.7)
        esfera(bm, p + Vector((s * 0.012 - 0.012, -0.03, 0.018)), (0.012, 0.006, 0.012), mat=NIE, segs=6, anillos=4)   # brillito
        dc = Vector((s * 0.62, -1, -0.05))
        piedrita(bm, en_superficie(B3, R3, A3, dc, 0.012), dc, 0.06, mat=ROJ, aplastar=0.3)                    # cachete (afuera de los grumos)
    for k in range(5):
        a = (k - 2) * 0.21
        d = Vector((math.sin(a) * 0.55, -1, -0.38 - 0.1 * math.cos(a * 2.4) + 0.1))
        piedrita(bm, en_superficie(B3, R3, A3, d), d, 0.026)
    # --- botones
    for z in (0.12, -0.22, -0.55):
        d = Vector((0, -1, z))
        piedrita(bm, en_superficie(B2, R2, A2, d), d, 0.068, aplastar=0.5)
    for z in (0.35, 0.0):
        d = Vector((0, -1, z))
        piedrita(bm, en_superficie(B1, R1, A1, d), d, 0.075, aplastar=0.5)
    # --- bufanda: dona con "tejido" (radio que sube y baja) + colas con flecos
    zb = 1.98
    filas = []
    for i in range(20):
        a = 2 * math.pi * i / 20
        fila = []
        for j in range(6):
            b = 2 * math.pi * j / 6
            r = 0.085 * (1 + 0.12 * math.cos(a * 10))          # anillos del tejido
            R = 0.34
            fila.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), zb + r * math.sin(b) * 0.9 - 0.04 * math.sin(a) * 0)))
        filas.append(fila)
    for i in range(20):
        for j in range(6):
            f = bm.faces.new((filas[i][j], filas[(i + 1) % 20][j], filas[(i + 1) % 20][(j + 1) % 6], filas[i][(j + 1) % 6])); f.material_index = BUF; f.smooth = True
    for x0, largo in ((0.33, 0.55), (0.22, 0.42)):     # a un lado, para que no tapen los botones
        cola = [Vector((x0, -0.38, zb - 0.02)), Vector((x0 - 0.04, -0.52, zb - 0.18)), Vector((x0 - 0.06, -0.58, zb - largo * 0.7)), Vector((x0 - 0.05, -0.6, zb - largo))]
        loft(bm, cola, [(0.085, 0.025)] * 4, mat=BUF, segs=5, sub=2, tapas=(True, False), arriba=Vector((0, -1, 0)))
        fin = cola[-1]
        for k in range(5):     # flecos
            x = fin.x - 0.07 + k * 0.035
            loft(bm, [Vector((x, fin.y, fin.z + 0.005)), Vector((x, fin.y - 0.005, fin.z - 0.08))], [(0.011, 0.011)] * 2, mat=BUF, segs=5, sub=1, tapas=(False, True))
        toro(bm, (fin.x, fin.y, fin.z + 0.01), 0.075, 0.012, mat=ROJ, segs=10, lados=5, inclinacion=0.0)   # orilla de color
    # --- sombrero de copa (un poco ladeado)
    import mathutils
    inc = mathutils.Matrix.Rotation(0.12, 3, "Y") @ mathutils.Matrix.Rotation(-0.06, 3, "X")
    cen = Vector((0.03, 0.02, 2.66))
    def rev(perfil, mat, segs=12, suave=False):
        filas = []
        for z, r in perfil:
            if r <= 1e-6: filas.append(bm.verts.new(cen + inc @ Vector((0, 0, z)))); continue
            filas.append([bm.verts.new(cen + inc @ Vector((math.cos(2 * math.pi * j / segs) * r, math.sin(2 * math.pi * j / segs) * r, z))) for j in range(segs)])
        for a, b in zip(filas, filas[1:]):
            for j in range(segs):
                k = (j + 1) % segs
                if isinstance(a, list) and isinstance(b, list): vs = (a[j], a[k], b[k], b[j])
                elif isinstance(a, list): vs = (a[j], a[k], b)
                else: vs = (a, b[k], b[j])
                f = bm.faces.new(vs); f.material_index = mat; f.smooth = suave
    rev([(0.0, 0.0), (0.0, 0.2), (-0.005, 0.3), (0.012, 0.335), (0.035, 0.33), (0.045, 0.3), (0.05, 0.215),
         (0.4, 0.205), (0.47, 0.215), (0.5, 0.2), (0.51, 0.0)], NEG)
    rev([(0.05, 0.218), (0.06, 0.222), (0.14, 0.222), (0.15, 0.217)], ROJ)
    # acebo en la cinta: 2 hojas + 3 bayas
    p0 = cen + inc @ Vector((-0.12, -0.18, 0.11))
    for s in (-1, 1):
        hoja = [p0, p0 + inc @ Vector((s * 0.06, -0.02, 0.05)), p0 + inc @ Vector((s * 0.12, -0.01, 0.07))]
        loft(bm, hoja, [(0.01, 0.002), (0.035, 0.008), (0.004, 0.002)], mat=VER, segs=6, sub=3, tapas=(True, True), arriba=Vector((0, -1, 0)))
    for k in range(3):
        esfera(bm, p0 + inc @ Vector(((k - 1) * 0.022, -0.035, 0.005 + (k % 2) * 0.02)), (0.019, 0.019, 0.019), mat=ROJ, segs=8, anillos=6)
    # --- brazos de rama (uno saludando)
    for s, sube in ((1, 0.42), (-1, 0.1)):
        hombro = en_superficie(B2, R2, A2, Vector((s, 0.05, 0.25)), -0.06)
        codo = hombro + Vector((s * 0.4, 0.02, sube * 0.6 + 0.05))
        mano = codo + Vector((s * 0.35, -0.02, sube))
        loft(bm, [hombro, codo, mano], [(0.035, 0.035), (0.028, 0.028), (0.018, 0.018)], mat=MAD, segs=5, sub=2, tapas=(True, True))
        for k, (dx, dz) in enumerate(((0.12, 0.12), (0.15, -0.02), (0.05, 0.16))):
            loft(bm, [mano - (mano - codo).normalized() * 0.03, mano + Vector((s * dx, rnd.uniform(-0.03, 0.03), dz))],
                 [(0.014, 0.014), (0.008, 0.008)], mat=MAD, segs=5, sub=1, tapas=(False, True))
        ramita = codo.lerp(mano, 0.3)
        loft(bm, [ramita, ramita + Vector((s * 0.07, 0, 0.15))], [(0.014, 0.014), (0.007, 0.007)], mat=MAD, segs=5, sub=1, tapas=(False, True))
    # LOW-POLY parejo: TODO con sombreado plano (sombrero, bufanda, brazos, botones, cara...)
    for f in bm.faces: f.smooth = False
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print("muñeco tris =", sum(len(p.vertices) - 2 for p in me.polygons))
