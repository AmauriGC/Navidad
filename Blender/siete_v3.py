# -*- coding: utf-8 -*-
"""
SIETE v3 (la Máquina 7 con personalidad) — objeto 'Maquina' de Props_Taller.glb. Estilo LOW-POLY de caras planas.
Mismo lugar y tamaño que la v2 (cuerpo x -9.35..-6.65, y -7.6..-5.4, z 0.3..2.6 en Blender) para que sus colisiones,
la boca de salida sobre la banda y la luz de alerta (Maquina_LuzAlerta) sigan sirviendo.

Piezas que Unity anima (hijos de 'Maquina', pivote en su punto de giro; coords de Blender):
  Siete_OjoL / Siete_OjoR   ojitos emisivos de la pantalla (escala Z = parpadeo, giro Y = cara triste)
  Siete_Boca                sonrisa emisiva (escala Z = -1 => carita triste)
  Siete_Foco_1..3           focos del tablero (engrane, resorte, fusible); Unity los pinta rojo/verde
  Siete_Aguja               aguja del manómetro de SOBRECARGA (0..10): Y local = 120° - 24°·descargas
  Siete_Palanca             palanca grande, bisagra en el eje X de Blender
  Siete_Engrane_1 / _2      engranes del costado +X, giran en el eje X de Blender cuando Siete está curada
  Siete_Cables              cables de colores de la máquina al techo y hasta arriba del Gran Árbol (fijo)
El camino de los cables se guarda en Blender/datos_siete.json (coords de UNITY) para animar el rayo.
Uso: exec(modelado.py); exec(siete_v3.py); hacer_siete()
"""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

ACERO, TURQ, LATON, COBRE, NEGRO, PANTALLA, ROJO, AMARILLO, HOLLIN = range(9)
CX, CY = -8.0, -6.5
HX, HY = 1.35, 1.1
FRENTE = CY + HY               # y = -5.4 (mira al árbol)
LADO = CX + HX                 # x = -6.65
S = 10                         # lados de los cilindros (low-poly)
DATOS = f"{PROYECTO}/Blender/datos_siete.json"


# ------------------------------------------------------------------ ayudantes
def cil(bm, a, b, r, mat, segs=S, r2=None):
    """Cilindro (o cono si r2) de caras planas con tapas."""
    r2 = r if r2 is None else r2
    a, b = Vector(a), Vector(b)
    eje = (b - a).normalized()
    u = eje.orthogonal().normalized(); v = eje.cross(u)
    ra = [bm.verts.new(a + (u * math.cos(2 * math.pi * k / segs) + v * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)]
    rb = [bm.verts.new(b + (u * math.cos(2 * math.pi * k / segs) + v * math.sin(2 * math.pi * k / segs)) * r2) for k in range(segs)]
    for k in range(segs):
        j = (k + 1) % segs
        bm.faces.new((ra[k], ra[j], rb[j], rb[k])).material_index = mat
    bm.faces.new(list(reversed(ra))).material_index = mat
    bm.faces.new(rb).material_index = mat


def domo(bm, c, r, mat, segs=S, anillos=3, normal=Vector((0, 0, 1)), aplastar=1.0):
    """Media esfera low-poly apoyada en c, abombada hacia 'normal'."""
    c = Vector(c); n = normal.normalized()
    u = n.orthogonal().normalized(); v = n.cross(u)
    filas = []
    for i in range(anillos):
        t = math.pi / 2 * i / anillos
        rr, h = r * math.cos(t), r * math.sin(t) * aplastar
        filas.append([bm.verts.new(c + n * h + (u * math.cos(2 * math.pi * k / segs) + v * math.sin(2 * math.pi * k / segs)) * rr) for k in range(segs)])
    tope = bm.verts.new(c + n * r * aplastar)
    for i in range(anillos - 1):
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((filas[i][k], filas[i][j], filas[i + 1][j], filas[i + 1][k])).material_index = mat
    for k in range(segs):
        bm.faces.new((filas[-1][k], filas[-1][(k + 1) % segs], tope)).material_index = mat
    bm.faces.new(list(reversed(filas[0]))).material_index = mat


def placa(bm, c, tam, mat, bisel=0.02):
    caja(bm, c, tam, mat=mat, bisel=bisel, segs=1)


def contorno(bm, centro, pts, grosor, mat, eje_u=Vector((-1, 0, 0)), eje_v=Vector((0, 0, 1)), normal=Vector((0, 1, 0))):
    """Extruye un contorno 2D (u, v) hacia 'normal' (abanico desde el centro: sirve para formas casi convexas)."""
    c = Vector(centro)
    fr = [bm.verts.new(c + eje_u * p[0] + eje_v * p[1] + normal * grosor) for p in pts]
    at = [bm.verts.new(c + eje_u * p[0] + eje_v * p[1]) for p in pts]
    cf = bm.verts.new(c + normal * grosor + eje_u * sum(p[0] for p in pts) / len(pts) + eje_v * sum(p[1] for p in pts) / len(pts))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((cf, fr[i], fr[j])).material_index = mat
        bm.faces.new((fr[i], at[i], at[j], fr[j])).material_index = mat


def tira(bm, pts, r, mat, segs=6):
    """Tubo low-poly que sigue una lista de puntos (cable, alambre)."""
    pts = [Vector(p) for p in pts]
    anillos = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.orthogonal().normalized(); v = d.cross(u)
        anillos.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / segs) + v * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)])
    for i in range(len(pts) - 1):
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((anillos[i][k], anillos[i][j], anillos[i + 1][j], anillos[i + 1][k])).material_index = mat
    bm.faces.new(list(reversed(anillos[0]))).material_index = mat
    bm.faces.new(anillos[-1]).material_index = mat


def plano(bm):
    for f in bm.faces: f.smooth = False


def materiales_siete():
    base = [bpy.data.materials[n] for n in ("Amb_Acero", "Amb_MetalTurquesa", "Amb_Laton", "Amb_Cobre", "Amb_Negro",
                                             "Amb_Pantalla", "Amb_Rojo", "Amb_Amarillo", "Amb_Hollin")]
    ojo = material("Siete_Ojo", (0.55, 0.95, 1.0), rugosidad=0.4, emision=(0.45, 0.9, 1.0), fuerza=3.0)
    foco = material("Siete_Foco", (1.0, 0.35, 0.25), rugosidad=0.25, emision=(1.0, 0.25, 0.15), fuerza=2.0)
    pant = material("Siete_Pantalla", (0.03, 0.06, 0.1), rugosidad=0.3)
    return base, ojo, foco, pant


def reemplazar_malla(obj, bm, mats):
    """Pone la malla de bm en obj CONSERVANDO el nombre de la malla (Unity la busca por nombre)."""
    plano(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("_siete_tmp")
    bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    viejo = obj.data; nombre = viejo.name if viejo else obj.name
    obj.data = me
    if viejo and viejo.users == 0: bpy.data.meshes.remove(viejo)
    otro = bpy.data.meshes.get(nombre)            # si alguien más tiene el nombre (copia vieja), se lo quitamos
    if otro is not None and otro != me: otro.name = nombre + "_viejo"
    me.name = nombre
    for mod in list(obj.modifiers): obj.modifiers.remove(mod)


def pieza(nombre, pivote, construir, mats, mundo=False):
    """Hijo de 'Maquina' con su origen en 'pivote' (coords de mundo de Blender).
    construir() arma la forma alrededor de (0,0,0); con mundo=True la arma en coords de mundo y se le resta el pivote."""
    maq = bpy.data.objects["Maquina"]
    o = bpy.data.objects.get(nombre)
    if o is None:
        o = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre))
        for c in maq.users_collection: c.objects.link(o)
    bm = bmesh.new(); construir(bm)
    p = Vector(pivote)
    if mundo:
        for v in bm.verts: v.co -= p
    reemplazar_malla(o, bm, mats)
    o.parent = maq; o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = p; o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    return o


# ------------------------------------------------------------------ cuerpo (malla 'Maquina')
def cuerpo(bm):
    # base con patas
    placa(bm, (CX, CY, 0.17), (2 * HX + 0.3, 2 * HY + 0.3, 0.26), ACERO, 0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cil(bm, (CX + sx * (HX + 0.05), CY + sy * (HY + 0.05), 0.0), (CX + sx * (HX + 0.05), CY + sy * (HY + 0.05), 0.06), 0.1, NEGRO, segs=8)
    # cuerpo con chaflán
    placa(bm, (CX, CY, 1.45), (2 * HX, 2 * HY, 2.3), TURQ, 0.12)
    # franjas con remaches (low-poly: remaches de 6 lados)
    for z in (0.5, 2.42):
        placa(bm, (CX, CY, z), (2 * HX + 0.04, 2 * HY + 0.04, 0.12), ACERO, 0.04)
        for k in range(9):
            x = CX - HX + 0.15 + k * (2 * HX - 0.3) / 8
            if z > 2 and abs(x - CX) < 0.3: continue          # ahí va la placa del 7
            cil(bm, (x, FRENTE + 0.02, z), (x, FRENTE + 0.04, z), 0.022, LATON, segs=6)
        for k in range(7):
            y = CY - HY + 0.15 + k * (2 * HY - 0.3) / 6
            cil(bm, (LADO + 0.02, y, z), (LADO + 0.04, y, z), 0.022, LATON, segs=6)
    # placa del "7"
    placa(bm, (CX, FRENTE + 0.04, 2.42), (0.42, 0.04, 0.22), LATON, 0.03)
    siete = [(-0.11, 0.075), (0.11, 0.075), (0.11, 0.04), (0.0, -0.085), (-0.05, -0.085), (0.05, 0.035), (-0.11, 0.035)]
    contorno(bm, (CX, FRENTE + 0.06, 2.42), siete, 0.015, ROJO)
    # tapa en domo (12 lados) + aro
    filas = [(2.48, 0.95, 0.8), (2.7, 0.88, 0.74), (2.88, 0.66, 0.55), (2.98, 0.36, 0.3), (3.02, 0.08, 0.07)]
    anillos = []
    for z, rx, ry in filas:
        anillos.append([bm.verts.new((CX + rx * math.cos(2 * math.pi * k / 12), CY + ry * math.sin(2 * math.pi * k / 12), z)) for k in range(12)])
    for i in range(len(anillos) - 1):
        for k in range(12):
            j = (k + 1) % 12
            bm.faces.new((anillos[i][k], anillos[i][j], anillos[i + 1][j], anillos[i + 1][k])).material_index = TURQ
    bm.faces.new(anillos[-1]).material_index = TURQ
    cil(bm, (CX, CY, 2.46), (CX, CY, 2.54), 0.93, LATON, segs=12)
    # embudo
    cil(bm, (CX, CY, 2.95), (CX, CY, 3.2), 0.2, LATON, segs=S, r2=0.32)
    cil(bm, (CX, CY, 3.2), (CX, CY, 3.6), 0.32, LATON, segs=S, r2=0.56)
    cil(bm, (CX, CY, 3.58), (CX, CY, 3.66), 0.6, LATON, segs=S)
    # tubos de cobre al techo con bridas
    for (x, y, dx) in ((-7.1, -7.2, 0.25), (-8.9, -7.3, -0.25)):
        camino = [(x, y, 2.55), (x, y, 3.05), (x + dx * 0.5, y, 3.4), (x + dx, y, 3.7), (x + dx, y, 7.6)]
        tira(bm, camino, 0.11, COBRE, segs=8)
        for z in (2.62, 4.0, 5.6, 7.2):
            px = x if z < 3 else x + dx
            cil(bm, (px, y, z - 0.04), (px, y, z + 0.04), 0.155, LATON, segs=8)
    # pantalla (cara de Siete): marco negro + fondo oscuro
    placa(bm, (CX, FRENTE + 0.03, 1.85), (1.4, 0.08, 0.86), NEGRO, 0.05)
    placa(bm, (CX, FRENTE + 0.065, 1.85), (1.22, 0.02, 0.7), 9, 0.04)          # 9 = Siete_Pantalla
    for sx in (-1, 1):
        for sz in (-1, 1):
            cil(bm, (CX + sx * 0.63, FRENTE + 0.07, 1.85 + sz * 0.36), (CX + sx * 0.63, FRENTE + 0.09, 1.85 + sz * 0.36), 0.022, LATON, segs=6)
    # tablero de los 3 focos: placa de latón con 3 bases y 3 dibujitos (engrane, resorte, fusible)
    placa(bm, (CX, FRENTE + 0.03, 1.17), (1.2, 0.05, 0.42), LATON, 0.03)
    for i, x in enumerate((CX + 0.4, CX, CX - 0.4)):     # +X se ve a la IZQUIERDA desde el frente
        cil(bm, (x, FRENTE + 0.05, 1.25), (x, FRENTE + 0.1, 1.25), 0.12, ACERO, segs=S)
        ic = Vector((x, FRENTE + 0.055, 1.05))
        if i == 0:      # engrane
            pts = []
            for k in range(24):
                a = 2 * math.pi * k / 24
                r = 0.055 if (k % 3) else 0.04
                pts.append((r * math.cos(a), r * math.sin(a)))
            contorno(bm, ic, pts, 0.012, NEGRO)
        elif i == 1:    # resorte (zigzag)
            zz = [(-0.06 + 0.02 * k, 0.03 if k % 2 else -0.03, 0) for k in range(7)]
            tira(bm, [ic + Vector((p[0], 0.008, p[1])) for p in zz], 0.007, NEGRO, segs=4)
        else:           # fusible: cápsula con tapitas
            placa(bm, tuple(ic + Vector((0, 0.008, 0))), (0.09, 0.012, 0.035), ROJO, 0.01)
            for s in (-1, 1):
                placa(bm, tuple(ic + Vector((s * 0.055, 0.01, 0))), (0.025, 0.016, 0.045), ACERO, 0.005)
    # manómetro de sobrecarga (0..10; las 3 últimas marcas rojas)
    gx, gz = -9.0, 1.5
    cil(bm, (gx, FRENTE, gz), (gx, FRENTE + 0.06, gz), 0.25, LATON, segs=12)
    cil(bm, (gx, FRENTE + 0.05, gz), (gx, FRENTE + 0.066, gz), 0.21, AMARILLO, segs=12)
    for k in range(11):
        a = math.radians(120 - k * 24)          # 0 a la izquierda (vista de frente), 10 a la derecha
        p = Vector((gx + 0.165 * math.sin(a), FRENTE + 0.068, gz + 0.165 * math.cos(a)))
        d = Vector((math.sin(a), 0, math.cos(a)))
        tira(bm, [p, p + d * 0.03], 0.007, ROJO if k >= 8 else NEGRO, segs=4)
    # base de la palanca grande (soporte con ranura)
    px, pz = -6.97, 0.85
    placa(bm, (px, FRENTE + 0.04, pz + 0.05), (0.3, 0.06, 0.55), ACERO, 0.03)
    for s in (-1, 1):
        placa(bm, (px + s * 0.11, FRENTE + 0.12, pz), (0.04, 0.16, 0.2), ACERO, 0.01)
    # boca de salida sobre la banda (mismo lugar que la v2)
    bx, bz = -9.25, 0.98
    placa(bm, (bx, FRENTE + 0.02, bz), (0.46, 0.05, 0.36), ACERO, 0.03)
    placa(bm, (bx, FRENTE + 0.035, bz - 0.02), (0.34, 0.03, 0.26), HOLLIN, 0.02)
    placa(bm, (bx, FRENTE + 0.13, bz + 0.17), (0.5, 0.24, 0.04), TURQ, 0.015)
    caja(bm, (bx, FRENTE + 0.12, bz - 0.17), (0.34, 0.22, 0.03), mat=ACERO, bisel=0.01, segs=1,
         giro=Matrix.Rotation(math.radians(-18), 3, "X"))
    # ejes y tornillos del costado +X (los engranes son piezas aparte)
    for (y, z, r) in ((-6.2, 1.8, 0.42), (-7.0, 1.0, 0.32)):
        cil(bm, (LADO, y, z), (LADO + 0.03, y, z), r * 0.5, HOLLIN, segs=S)
    for (y, z) in ((-5.6, 2.2), (-7.4, 2.2), (-5.6, 0.75), (-7.4, 0.75)):
        cil(bm, (LADO, y, z), (LADO + 0.03, y, z), 0.04, ACERO, segs=6)
    # escotilla del costado -X
    hx0 = CX - HX
    cil(bm, (hx0, -6.5, 1.3), (hx0 - 0.06, -6.5, 1.3), 0.5, ACERO, segs=12)
    cil(bm, (hx0 - 0.05, -6.5, 1.3), (hx0 - 0.09, -6.5, 1.3), 0.4, TURQ, segs=12)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cil(bm, (hx0 - 0.05, -6.5 + 0.45 * math.cos(a), 1.3 + 0.45 * math.sin(a)), (hx0 - 0.08, -6.5 + 0.45 * math.cos(a), 1.3 + 0.45 * math.sin(a)), 0.02, LATON, segs=6)
    tira(bm, [(hx0 - 0.09, -6.65, 1.3), (hx0 - 0.2, -6.6, 1.3), (hx0 - 0.2, -6.4, 1.3), (hx0 - 0.09, -6.35, 1.3)], 0.025, LATON, segs=6)
    # chimenea chiquita atrás
    cil(bm, (-8.5, -7.15, 2.6), (-8.5, -7.15, 3.4), 0.12, ACERO, segs=8)
    cil(bm, (-8.5, -7.15, 3.4), (-8.5, -7.15, 3.5), 0.17, HOLLIN, segs=8, r2=0.15)
    # caja de conexión de los cables en la parte de atrás del domo
    placa(bm, (-7.6, -7.25, 2.75), (0.36, 0.2, 0.3), ACERO, 0.03)


# ------------------------------------------------------------------ piezas animadas
def ojo(bm):
    # cápsula vertical aplanada (8 lados), mirando al frente
    pts = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        pts.append((0.085 * math.cos(a), 0.14 * math.sin(a)))
    contorno(bm, (0, 0, 0), pts, 0.018, 0)


def boca(bm):
    arco = []
    for k in range(7):
        t = -1 + 2 * k / 6
        arco.append((t * 0.17, 0.0, -0.06 * (1 - t * t)))
    tira(bm, [Vector(p) for p in arco], 0.022, 0, segs=6)


def foco(bm):
    cil(bm, (0, -0.02, 0), (0, 0.02, 0), 0.1, 1, segs=S)                    # aro de latón
    domo(bm, (0, 0.02, 0), 0.085, 0, segs=S, anillos=3, normal=Vector((0, 1, 0)))


def aguja(bm):
    tira(bm, [(0, 0, 0), (0, 0, 0.15)], 0.012, 0, segs=4)
    cil(bm, (0, -0.005, 0), (0, 0.02, 0), 0.03, 0, segs=8)


def palanca(bm):
    # palanca GRANDE: varilla gruesa inclinada hacia el frente con perilla roja; eje de la bisagra = X
    cil(bm, (-0.09, 0, 0), (0.09, 0, 0), 0.07, 0, segs=8)
    tira(bm, [(0, 0, 0), (0, 0.08, 0.5), (0, 0.16, 1.0)], 0.04, 0, segs=6)
    cil(bm, (0, 0.16, 1.0), (0, 0.175, 1.07), 0.05, 0, segs=6)
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=0.12)
    for v in tmp.verts: v.co += Vector((0, 0.18, 1.16))
    for f in tmp.faces: f.material_index = 1
    unir(bm, tmp)


def engrane_pieza(R, dientes):
    def construir(bm):
        pts = []
        for k in range(dientes * 4):
            a = 2 * math.pi * k / (dientes * 4)
            r = R if (k % 4) in (1, 2) else R * 0.82
            pts.append((r * math.cos(a), r * math.sin(a)))
        contorno(bm, (0, 0, 0), pts, 0.06, 0, eje_u=Vector((0, 1, 0)), eje_v=Vector((0, 0, 1)), normal=Vector((1, 0, 0)))
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.3
            d = Vector((0, math.cos(a), math.sin(a)))
            tira(bm, [d * R * 0.15 + Vector((0.065, 0, 0)), d * R * 0.62 + Vector((0.065, 0, 0))], R * 0.06, 0, segs=4)
        cil(bm, (0.06, 0, 0), (0.12, 0, 0), R * 0.2, 0, segs=6)
        cil(bm, (0.12, 0, 0), (0.15, 0, 0), R * 0.1, 1, segs=6)
    return construir


# ------------------------------------------------------------------ cables al techo
def camino_cables():
    """Sale de la caja de conexión (atrás del domo), sube junto a los tubos y cruza el techo hasta arriba del árbol (0,0)."""
    pts = [Vector((-7.6, -7.35, 2.8)), Vector((-7.6, -7.8, 3.2)), Vector((-7.6, -7.9, 6.9))]
    ganchos = [Vector((-7.6, -7.9, 7.2)), Vector((-5.7, -5.9, 7.2)), Vector((-3.8, -3.95, 7.2)),
               Vector((-1.9, -2.0, 7.2)), Vector((0.0, 0.0, 7.2))]
    for a, b in zip(ganchos[:-1], ganchos[1:]):
        for k in range(1, 7):
            t = k / 6
            p = a.lerp(b, t); p.z -= 0.28 * 4 * t * (1 - t)       # comba entre ganchos
            pts.append(p)
    pts.append(Vector((0.0, 0.0, 6.7)))                           # baja un poquito hacia la punta del árbol
    return pts, ganchos


def cables(bm):
    pts, ganchos = camino_cables()
    lado = [Vector((0.07, -0.07, 0)), Vector((-0.07, 0.07, 0)), Vector((0, 0, 0.08))]
    for i, mat in enumerate((ROJO, AMARILLO, NEGRO)):
        tira(bm, [p + lado[i] for p in pts], 0.025, mat, segs=5)
    for g in ganchos:                                             # ganchos al techo
        cil(bm, tuple(g + Vector((0, 0, 0.05))), tuple(g + Vector((0, 0, 0.22))), 0.03, ACERO, segs=6)
        cil(bm, tuple(g - Vector((0, 0, 0.02))), tuple(g + Vector((0, 0, 0.06))), 0.13, LATON, segs=8)
    cil(bm, (0, 0, 6.62), (0, 0, 6.72), 0.16, LATON, segs=10)        # remate dorado sobre el árbol


def guardar_camino():
    pts, _ = camino_cables()
    unity = [[-p.x, p.z, -p.y] for p in pts]
    with open(DATOS, "w") as f:
        json.dump({"camino_cables_unity": [[round(c, 3) for c in p] for p in unity],
                   "nota": "camino del rayo: de la Máquina 7 (inicio) a arriba del Gran Árbol (fin)"}, f, indent=1)


# ------------------------------------------------------------------ vitrina
def vitrina_maquina():
    """Rehace solo las copias VT_ de la Maquina (comparten malla) en el mismo lugar de la Vitrina."""
    sc = bpy.data.scenes["Vitrina"]
    vt = bpy.data.objects.get("VT_Maquina")
    delta = Vector((52.06, 31.87, 0.0)) if vt is None else vt.matrix_world.translation - bpy.data.objects["Maquina"].matrix_world.translation
    for o in list(sc.collection.all_objects):
        if o.name == "VT_Maquina" or o.name.startswith("VT_Siete_"): bpy.data.objects.remove(o)
    maq = bpy.data.objects["Maquina"]
    raiz = maq.copy(); raiz.name = "VT_Maquina"; sc.collection.objects.link(raiz)
    raiz.matrix_world = Matrix.Translation(delta) @ maq.matrix_world
    for h in maq.children:
        c = h.copy(); c.name = "VT_" + h.name; sc.collection.objects.link(c)
        c.parent = raiz; c.matrix_parent_inverse = Matrix.Identity(4)
        c.location = h.location.copy()
    alerta = bpy.data.objects["Maquina_LuzAlerta"]
    va = bpy.data.objects.get("VT_Siete_LuzAlerta")
    if va is None:
        va = alerta.copy(); va.name = "VT_Siete_LuzAlerta"; sc.collection.objects.link(va)
    va.matrix_world = Matrix.Translation(delta) @ alerta.matrix_world
    return delta


# ------------------------------------------------------------------ todo
def hacer_siete():
    base, ojo_m, foco_m, pant = materiales_siete()
    maq = bpy.data.objects["Maquina"]
    bm = bmesh.new(); cuerpo(bm)
    reemplazar_malla(maq, bm, base + [pant])
    F = FRENTE + 0.08
    pieza("Siete_OjoL", (CX - 0.25, F, 1.92), ojo, [ojo_m])
    pieza("Siete_OjoR", (CX + 0.25, F, 1.92), ojo, [ojo_m])
    pieza("Siete_Boca", (CX, F, 1.66), boca, [ojo_m])
    for i, x in enumerate((CX + 0.4, CX, CX - 0.4)):     # Foco_1 (engrane) a la izquierda vista de frente
        pieza(f"Siete_Foco_{i + 1}", (x, FRENTE + 0.1, 1.25), foco, [foco_m, base[LATON]])
    pieza("Siete_Aguja", (-9.0, FRENTE + 0.07, 1.5), aguja, [base[ROJO]])
    pieza("Siete_Palanca", (-6.97, FRENTE + 0.14, 0.85), palanca, [base[ACERO], base[ROJO]])
    pieza("Siete_Engrane_1", (LADO, -6.2, 1.8), engrane_pieza(0.42, 12), [base[LATON], base[ACERO]])
    pieza("Siete_Engrane_2", (LADO, -7.0, 1.0), engrane_pieza(0.32, 10), [base[LATON], base[ACERO]])
    pieza("Siete_Cables", (-7.6, -7.25, 2.8), cables, base, mundo=True)
    # la aguja empieza en 0 (+120° en su eje Y local); cada descarga le resta 24°
    bpy.data.objects["Siete_Aguja"].rotation_euler = (0, math.radians(120), 0)
    guardar_camino()
    vitrina_maquina()
    tris = 0
    for o in [maq] + list(maq.children):
        if o.type == "MESH": tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    return f"Siete v3 lista: {len(maq.children)} piezas, {tris} triángulos"
