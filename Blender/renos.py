# -*- coding: utf-8 -*-
"""
RENOS v2: modelos orgánicos hechos con "LOFT" (anillos elípticos conectados a lo largo de un camino).
Se ejecuta dentro de Blender:  exec(open(".../Blender/renos.py").read())
Reemplaza la MALLA de los objetos existentes (Reno_Cuerpo, Reno_Cabeza, Reno_OrejaL/R, Reno_Cola y los de
RenoNarizRoja) sin cambiar sus nombres ni sus orígenes, para que en Unity sigan funcionando la animación
(RenoAnimador mueve cabeza y cola) y la guirnalda que cuelga de la cabeza.
Ejes de Blender: frente = -Y, arriba = +Z.
"""
import bpy, bmesh, math
from mathutils import Vector


# ------------------------------------------------------------------ camino suave (Catmull-Rom)
def suavizar_camino(puntos, radios, sub=4):
    """Interpola puntos y radios con Catmull-Rom para que el tubo no tenga 'codos'."""
    P = [Vector(p) for p in puntos]
    salida_p, salida_r = [], []
    n = len(P)
    for i in range(n - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n - 1)]
        r1, r2 = radios[i], radios[i + 1]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            p = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            salida_p.append(p)
            salida_r.append((r1[0] + (r2[0] - r1[0]) * t, r1[1] + (r2[1] - r1[1]) * t))
    salida_p.append(P[-1]); salida_r.append(radios[-1])
    return salida_p, salida_r


def loft(bm, puntos, radios, mat=0, segs=18, sub=4, tapas=(True, True), domo=0.6, arriba=Vector((0, 0, 1)), abierto=None):
    """
    Tubo de anillos elípticos a lo largo de 'puntos'. radios = [(ancho, alto), ...] por punto.
    El marco de cada anillo se calcula con 'transporte paralelo' (el anillo no se tuerce).
    tapas: cerrar inicio/fin con un domo redondo. abierto=(a0,a1) en grados -> solo un arco (mantita).
    """
    P, R = suavizar_camino(puntos, radios, sub)
    n = len(P)
    tang = []
    for i in range(n):
        t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]); t.normalize(); tang.append(t)
    ref = arriba if abs(tang[0].dot(arriba)) < 0.9 else Vector((0, 1, 0))
    lado = tang[0].cross(ref).normalized()
    anillos = []
    if abierto:
        angs = [math.radians(abierto[0] + (abierto[1] - abierto[0]) * j / segs) for j in range(segs + 1)]
    else:
        angs = [2 * math.pi * j / segs for j in range(segs)]
    for i in range(n):
        if i > 0:   # transporte paralelo: quitar al 'lado' la componente sobre la tangente nueva
            lado = (lado - tang[i] * lado.dot(tang[i])).normalized()
        up = lado.cross(tang[i]).normalized()
        rx, rz = R[i]
        anillo = [bm.verts.new(P[i] + lado * (math.cos(a) * rx) + up * (math.sin(a) * rz)) for a in angs]
        anillos.append(anillo)
    m = len(angs)
    for i in range(n - 1):
        a, b = anillos[i], anillos[i + 1]
        rango = range(m - 1) if abierto else range(m)
        for j in rango:
            f = bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
            f.material_index = mat; f.smooth = True
    if not abierto:
        for idx, (cual, signo) in enumerate(((0, -1), (n - 1, 1))):
            if not tapas[idx]: continue
            r = max(R[cual])
            c = bm.verts.new(P[cual] + tang[cual] * signo * r * domo)
            an = anillos[cual]
            for j in range(m):
                vs = (an[j], an[(j + 1) % m], c) if signo > 0 else (an[(j + 1) % m], an[j], c)
                f = bm.faces.new(vs); f.material_index = mat; f.smooth = True
    return anillos


def esfera(bm, centro, radios, mat=0, segs=16, anillos=10):
    """Elipsoide (esfera escalada) con caras suaves."""
    res = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=anillos, radius=1.0)
    for v in res["verts"]:
        v.co = Vector((v.co.x * radios[0], v.co.y * radios[1], v.co.z * radios[2])) + Vector(centro)
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat; f.smooth = True


def toro(bm, centro, R, r, mat=0, segs=24, lados=8, inclinacion=0.0):
    """Dona (collar). inclinacion = giro en X (radianes) para que abrace el cuello."""
    import mathutils
    rot = mathutils.Matrix.Rotation(inclinacion, 3, "X")
    vs = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        fila = []
        for j in range(lados):
            b = 2 * math.pi * j / lados
            p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            fila.append(bm.verts.new(rot @ p + Vector(centro)))
        vs.append(fila)
    for i in range(segs):
        for j in range(lados):
            f = bm.faces.new((vs[i][j], vs[(i + 1) % segs][j], vs[(i + 1) % segs][(j + 1) % lados], vs[i][(j + 1) % lados]))
            f.material_index = mat; f.smooth = True


def poner_malla(obj, construir):
    """Crea una malla nueva con 'construir(bm)', conserva los materiales del objeto y la asigna."""
    mats = [s.material for s in obj.material_slots]
    bm = bmesh.new()
    construir(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(obj.name + "_v2")
    bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    viejo = obj.data
    obj.data = me
    if viejo.users == 0: bpy.data.meshes.remove(viejo)
    for mod in list(obj.modifiers): obj.modifiers.remove(mod)
    s = obj.modifiers.new("Redondeo", "SUBSURF"); s.levels = 1; s.render_levels = 1


# ------------------------------------------------------------------ partes del reno
# materiales del CUERPO: 0 café, 1 crema, 2 pezuña, 3 collar (rojo), 4 oro
def cuerpo(bm):
    # torso + cuello en un solo loft (de la cola hacia el pecho y sube al cuello)
    loft(bm,
         [(0, 0.60, 0.99), (0, 0.50, 0.99), (0, 0.28, 0.97), (0, 0.0, 0.95), (0, -0.26, 0.98), (0, -0.44, 1.05),
          (0, -0.54, 1.17), (0, -0.58, 1.31), (0, -0.57, 1.42)],
         [(0.13, 0.13), (0.25, 0.26), (0.29, 0.29), (0.30, 0.28), (0.29, 0.30), (0.24, 0.28),
          (0.16, 0.17), (0.125, 0.13), (0.11, 0.11)], mat=0, segs=20, sub=4, domo=0.7)
    # panza y pecho color crema (un poco salidos del cuerpo)
    esfera(bm, (0, 0.02, 0.73), (0.20, 0.46, 0.08), mat=1)
    esfera(bm, (0, -0.635, 1.0), (0.14, 0.065, 0.2), mat=1)                      # pechera crema (casi toda dentro del cuerpo)
    for (x, z, dz) in ((0, 0.86, 0.075), (-0.045, 0.88, 0.06), (0.045, 0.88, 0.06)):   # puntita esponjada hacia abajo
        esfera(bm, (x, -0.62, z), (0.042, 0.04, dz), mat=1, segs=12, anillos=8)
    # patas: muslo -> rodilla/corvejón -> caña -> pezuña
    for x in (-0.15, 0.15):
        loft(bm, [(x, -0.34, 0.92), (x, -0.36, 0.62), (x, -0.37, 0.40), (x, -0.35, 0.16), (x, -0.35, 0.10)],
             [(0.10, 0.11), (0.075, 0.08), (0.055, 0.06), (0.048, 0.05), (0.05, 0.05)], mat=0, segs=12, tapas=(False, False))
        loft(bm, [(x, 0.38, 0.92), (x, 0.44, 0.64), (x, 0.47, 0.44), (x, 0.39, 0.18), (x, 0.39, 0.10)],
             [(0.12, 0.14), (0.085, 0.09), (0.06, 0.06), (0.048, 0.05), (0.05, 0.05)], mat=0, segs=12, tapas=(False, False))
        for y in (-0.35, 0.39):   # pezuñas oscuras
            loft(bm, [(x, y, 0.115), (x, y - 0.005, 0.05), (x, y - 0.01, 0.0)],
                 [(0.052, 0.052), (0.06, 0.062), (0.062, 0.066)], mat=2, segs=12, domo=0.15)
    # arnés: collar rojo con cascabel dorado
    # el collar es perpendicular al cuello: el cuello se inclina ~28° hacia el frente (-Y)
    toro(bm, (0, -0.55, 1.20), 0.172, 0.032, mat=3, inclinacion=math.radians(28))
    esfera(bm, (0, -0.735, 1.10), (0.06, 0.06, 0.06), mat=4, segs=14, anillos=8)                    # cascabel
    toro(bm, (0, -0.735, 1.10), 0.061, 0.009, mat=4, segs=16, lados=6, inclinacion=math.radians(90))
    # mantita sobre el lomo (arco abierto del torso un poco más grande) con orillas doradas
    loft(bm, [(0, 0.20, 0.975), (0, 0.0, 0.955), (0, -0.20, 0.985)],
         [(0.315, 0.305), (0.322, 0.298), (0.315, 0.315)], mat=3, segs=14, sub=3, abierto=(20, 160))
    for y in (0.21, -0.21):
        loft(bm, [(0, y + 0.012, 0.97 + (0.005 if y > 0 else 0.015)), (0, y - 0.012, 0.97 + (0.005 if y > 0 else 0.015))],
             [(0.325, 0.32), (0.325, 0.32)], mat=4, segs=14, sub=1, abierto=(18, 162))


# materiales de la CABEZA: 0 café, 1 crema, 2 nariz, 3 ojo, 4 asta. Coordenadas LOCALES (origen en el cuello).
def cabeza(bm, nariz_roja=False):
    loft(bm, [(0, -0.06, 0.30), (0, -0.17, 0.33), (0, -0.29, 0.29), (0, -0.40, 0.23), (0, -0.49, 0.19), (0, -0.53, 0.18)],
         [(0.13, 0.13), (0.165, 0.155), (0.13, 0.12), (0.10, 0.09), (0.088, 0.078), (0.06, 0.055)], mat=0, segs=18, sub=4, domo=0.8)
    esfera(bm, (0, -0.23, 0.24), (0.12, 0.11, 0.07), mat=0)                    # mejillas / quijada
    esfera(bm, (0, -0.43, 0.14), (0.075, 0.09, 0.045), mat=1)                  # barbilla crema
    rn = 0.062 if nariz_roja else 0.045
    esfera(bm, (0, -0.545, 0.205), (rn, rn * 0.9, rn * 0.85), mat=2)          # nariz
    for x in (-0.095, 0.095):
        esfera(bm, (x, -0.29, 0.355), (0.036, 0.03, 0.04), mat=3, segs=12, anillos=8)          # ojo
        esfera(bm, (x * 0.93, -0.316, 0.37), (0.011, 0.008, 0.011), mat=1, segs=8, anillos=5)  # brillito
        esfera(bm, (x * 1.05, -0.28, 0.40), (0.05, 0.02, 0.012), mat=0, segs=10, anillos=5)    # ceja
    # cornamenta: tronco principal + 3 puntas por lado, tubos que se adelgazan con punta redonda
    for s in (-1, 1):
        tronco = [(s * 0.07, -0.13, 0.43), (s * 0.13, -0.10, 0.55), (s * 0.20, -0.06, 0.68), (s * 0.27, -0.01, 0.80), (s * 0.30, 0.05, 0.93)]
        loft(bm, tronco, [(0.034, 0.034), (0.03, 0.03), (0.027, 0.027), (0.023, 0.023), (0.017, 0.017)], mat=4, segs=8, sub=3, domo=0.9)
        puntas = [[(s * 0.13, -0.10, 0.55), (s * 0.15, -0.20, 0.64), (s * 0.15, -0.27, 0.71)],
                  [(s * 0.20, -0.06, 0.68), (s * 0.27, -0.15, 0.77), (s * 0.30, -0.20, 0.85)],
                  [(s * 0.27, -0.01, 0.80), (s * 0.36, -0.03, 0.87), (s * 0.41, -0.06, 0.93)]]
        for pt in puntas:
            loft(bm, pt, [(0.022, 0.022), (0.018, 0.018), (0.013, 0.013)], mat=4, segs=8, sub=3, domo=0.9)


def oreja(bm, s):
    """Oreja en forma de hoja, apunta hacia afuera (s = -1 izquierda, +1 derecha) y un poco abajo."""
    loft(bm, [(0, 0, 0), (s * 0.07, -0.005, 0.0), (s * 0.15, -0.01, -0.02), (s * 0.20, -0.01, -0.035)],
         [(0.03, 0.022), (0.05, 0.026), (0.035, 0.02), (0.006, 0.006)], mat=0, segs=10, sub=3, domo=0.4, arriba=Vector((0, 1, 0)))
    esfera(bm, (s * 0.10, -0.022, -0.01), (0.055, 0.008, 0.024), mat=1, segs=10, anillos=6)   # interior crema


def cola(bm):
    loft(bm, [(0, 0.0, 0.0), (0, 0.07, 0.05), (0, 0.11, 0.12), (0, 0.12, 0.17)],
         [(0.05, 0.05), (0.07, 0.07), (0.05, 0.05), (0.012, 0.012)], mat=0, segs=12, sub=3, domo=0.5)


def rehacer(prefijo, nariz_roja):
    O = bpy.data.objects
    poner_malla(O[prefijo + "_Cuerpo"], cuerpo)
    poner_malla(O[prefijo + "_Cabeza"], lambda bm: cabeza(bm, nariz_roja))
    poner_malla(O[prefijo + "_OrejaL"], lambda bm: oreja(bm, -1))
    poner_malla(O[prefijo + "_OrejaR"], lambda bm: oreja(bm, 1))
    poner_malla(O[prefijo + "_Cola"], cola)
    # orejas un poco más atrás y abajo de la cornamenta
    O[prefijo + "_OrejaL"].location = (-0.12, -0.13, 0.38)
    O[prefijo + "_OrejaR"].location = (0.12, -0.13, 0.38)


rehacer("Reno", False)
rehacer("RenoNarizRoja", True)
print("renos v2 listos")


# ---------------------------------------------------------------- v1.5: cuello que gira sin "romperse"
def cuello_redondo(nc="Reno_Cuerpo", nh="Reno_Cabeza", eje=(0, -0.3, 0.95)):
    """La cabeza voltea sobre el EJE DEL CUELLO (RenoAnimador usa el mismo eje). La punta del cuello del CUERPO
    se jala hacia ese eje (radio máx 0.24 m en el collar → 0.085 m donde empieza la cabeza): un cuerpo de revolución
    alrededor del eje de giro no cambia al girar, así que se queda escondido dentro del cuello de la cabeza.
    El collar no se toca. Correr con nc/nh = RenoNarizRoja_Cuerpo/_Cabeza también."""
    from mathutils import Vector
    def ss(a, b, x):
        t = max(0, min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t)
    c = bpy.data.objects[nc]; h = bpy.data.objects[nh]; me = c.data
    ci = [i for i, m in enumerate(me.materials) if m.name == "Ren_Collar"]
    collar = set()
    for f in me.polygons:
        if f.material_index in ci: collar.update(f.vertices)
    mw = c.matrix_world; mi = mw.inverted()
    P = h.matrix_world.translation.copy(); A = Vector(eje).normalized()
    n = 0
    for v in me.vertices:
        if v.index in collar: continue
        p = mw @ v.co; d = p - P; t = d.dot(A)
        if t < 0.06: continue
        rv = d - A * t; r = rv.length
        rmax = 0.24 + (0.085 - 0.24) * ss(0.06, 0.2, t)
        if r > rmax:
            v.co = mi @ (P + A * t + rv * (rmax / r)); n += 1
    me.update()
    return n
