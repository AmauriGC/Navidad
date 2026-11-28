# -*- coding: utf-8 -*-
"""
CARA DEL CASCANUECES v4 (27-nov): el DISEÑO ORIGINAL de cascanueces_v2.py (pelo esponjado, cejas blancas pobladas,
ojos con su blanco, cachetes, nariz redonda, bigote en dos rizos, barba de bolitas, shako) que le gustó al alumno,
pero con la BOCA corregida como en la v3:
  - el cráneo tiene una VENTANA recortada y un hueco oscuro (Cas_Boca) detrás;
  - la palanca-mandíbula es un pedazo del mismo cráneo => cerrada queda AL RAS, solo se ve la franja de dientes;
  - dientes pintados (franja continua con rayitas), la barba de bolitas cuelga de la palanca y se mueve con ella;
  - bisagra dentro de la cabeza (PIVOTE_MAND de la v3) + mordida de 12° con la cabeza echándose atrás.
Materiales: vuelven a su rugosidad original (la v3 les había puesto laca 0.3).
Uso: exec(modelado.py); exec(cascanueces_cara_v3.py); exec(cascanueces_cara_v4.py); hacer_cara_v4()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

# perfil del cráneo (z, radio): un poco abombado como el original (antes loft de 0.155 a 0.165)
PERFIL = [(1.12, 0.148), (1.14, 0.158), (Z0, 0.16), (Z1, 0.162), (1.33, 0.166), (1.42, 0.163), (1.5, 0.152)]
R_BOCA = 0.161                     # radio a la altura de la boca (promedio de Z0 y Z1): palanca y dientes

def _pb(r, a, z):
    x, y = _arco(r, a); return Vector((x, y, z))

def craneo_con_boca(bm, P, BO):
    angs = [7.5 + 15 * j for j in range(SEG)]
    V = [[bm.verts.new(_pb(r, a, z)) for a in angs] for (z, r) in PERFIL]
    j0, j1 = angs.index(A0), angs.index(A1)
    iv = [i for i, (z, _) in enumerate(PERFIL) if z == Z0][0]          # anillo de abajo de la ventana
    for i in range(len(PERFIL) - 1):
        for j in range(SEG):
            if i == iv and j0 <= j < j1: continue
            k = (j + 1) % SEG
            _cara(bm, (V[i][j], V[i + 1][j], V[i + 1][k], V[i][k]), P)
    arriba = [bm.verts.new(_pb(R_HUECO, angs[j], Z1)) for j in range(j0, j1 + 1)]
    abajo = [bm.verts.new(_pb(R_HUECO, angs[j], Z0)) for j in range(j0, j1 + 1)]
    A, B = V[iv + 1], V[iv]
    for n, j in enumerate(range(j0, j1)):
        _cara(bm, (A[j], A[j + 1], arriba[n + 1], arriba[n]), BO)
        _cara(bm, (B[j + 1], B[j], abajo[n], abajo[n + 1]), BO)
        _cara(bm, (arriba[n], arriba[n + 1], abajo[n + 1], abajo[n]), BO)
    _cara(bm, (B[j0], A[j0], arriba[0], abajo[0]), BO)
    _cara(bm, (A[j1], B[j1], abajo[-1], arriba[-1]), BO)

def dientes_v4(bm, z0, z1, mat, raya, a0=58, a1=122, n=5):
    pasos = 12
    fila = [[bm.verts.new(_pb(R_BOCA + 0.0012, a0 + (a1 - a0) * k / pasos, z)) for k in range(pasos + 1)] for z in (z0, z1)]
    for k in range(pasos):
        _cara(bm, (fila[0][k], fila[0][k + 1], fila[1][k + 1], fila[1][k]), mat)
    for k in range(1, n):
        a = a0 + (a1 - a0) * k / n
        x, y = _arco(R_BOCA + 0.0022, a)
        caja(bm, (x, y, (z0 + z1) / 2), (0.0025, 0.0016, z1 - z0), mat=raya, bisel=0.0,
             giro=Matrix.Rotation(math.radians(a - 90), 3, "Z"))

# ------------------------------------------------------------------ cabeza (diseño original v2 + boca nueva)
def cabeza_v4(bm):
    P, B, OJ, N, M, O, R, BO = range(8)
    # cuello alto blanco
    loft(bm, [(0, 0, 1.08), (0, 0, 1.18)], [(0.15, 0.14), (0.14, 0.13)], mat=B, segs=20, sub=1, domo=0.1)
    # cráneo con la boca recortada
    craneo_con_boca(bm, P, BO)
    dientes_v4(bm, Z_BOCA + 0.0015, Z_BOCA + 0.02, B, BO)
    # pelo blanco (lados y atrás), esponjado
    for s in (-1, 1):
        for (y, z, r) in ((-0.02, 1.42, 0.07), (0.05, 1.36, 0.075), (0.09, 1.27, 0.07), (0.06, 1.2, 0.06)):
            esfera(bm, (s * 0.155, y, z), (r * 0.7, r, r), mat=B, segs=10, anillos=8)
    for z, r in ((1.42, 0.09), (1.32, 0.1), (1.22, 0.09)):
        esfera(bm, (0, 0.14, z), (0.14, r * 0.7, r), mat=B, segs=12, anillos=8)
    # ojos: blanco + pupila (Cas_Ojos) + cejas pobladas
    for s in (-1, 1):
        esfera(bm, (s * 0.068, -0.15, 1.4), (0.045, 0.025, 0.04), mat=B, segs=14, anillos=10)
        esfera(bm, (s * 0.065, -0.171, 1.398), (0.016, 0.01, 0.019), mat=OJ, segs=12, anillos=8)   # pupila roja chiquita
        loft(bm, [(s * 0.025, -0.165, 1.455), (s * 0.07, -0.172, 1.468), (s * 0.115, -0.16, 1.455)],
             [(0.016, 0.012), (0.02, 0.014), (0.012, 0.01)], mat=B, segs=8, sub=3)
        esfera(bm, (s * 0.115, -0.115, 1.3), (0.035, 0.02, 0.028), mat=M, segs=12, anillos=8)   # cachete
    # nariz grande redonda
    esfera(bm, (0, -0.19, 1.335), (0.035, 0.045, 0.04), mat=P, segs=14, anillos=10)
    # bigote en dos rizos (un poquito más arriba: deja ver los dientes de arriba)
    for s in (-1, 1):
        loft(bm, [(0, -0.185, 1.296), (s * 0.06, -0.18, 1.29), (s * 0.11, -0.16, 1.305), (s * 0.13, -0.14, 1.335)],
             [(0.022, 0.016), (0.026, 0.02), (0.018, 0.014), (0.008, 0.008)], mat=B, segs=10, sub=4)
    # shako
    loft(bm, [(0, 0, 1.49), (0, 0, 1.7), (0, 0, 1.92)], [(0.175, 0.17), (0.185, 0.18), (0.2, 0.195)], mat=N, segs=24, sub=2, domo=0.12)
    toro(bm, (0, 0, 1.515), 0.18, 0.02, mat=O, segs=24, lados=6)
    toro(bm, (0, 0, 1.915), 0.2, 0.02, mat=O, segs=24, lados=6)
    loft(bm, [(-0.15, -0.12, 1.505), (0, -0.215, 1.495), (0.15, -0.12, 1.505)], [(0.03, 0.008)] * 3, mat=N, segs=8, sub=4)
    esfera(bm, (0, -0.185, 1.69), (0.065, 0.015, 0.08), mat=O, segs=4, anillos=6)
    esfera(bm, (0, -0.198, 1.69), (0.025, 0.01, 0.025), mat=R, segs=10, anillos=6)
    loft(bm, [(0, 0.0, 1.92), (0, 0.01, 1.98), (0, 0.0, 2.05), (0, -0.015, 2.1)], [(0.03, 0.03), (0.055, 0.05), (0.045, 0.04), (0.012, 0.012)], mat=R, segs=12, sub=3, domo=0.5)
    esfera(bm, (0, 0, 1.925), (0.035, 0.035, 0.02), mat=O, segs=10, anillos=6)

# ------------------------------------------------------------------ mandíbula: palanca al ras + barba de bolitas
def mandibula_v4(bm):
    P, B, BO = 0, 1, 2
    angs = [A0 + (A1 - A0) * k / 5 for k in range(6)]
    za, zb = Z0 + 0.0006, Z1 - 0.0006
    ra = lambda z: 0.16 + 0.002 * (z - Z0) / (Z1 - Z0)               # sigue el perfil del cráneo
    afuera = [[bm.verts.new(_pb(ra(z), a, z)) for a in angs] for z in (za, zb)]
    adentro = [[bm.verts.new(_pb(ra(z) - 0.03, a, z)) for a in angs] for z in (za, zb)]
    for k in range(5):
        _cara(bm, (afuera[0][k], afuera[0][k + 1], afuera[1][k + 1], afuera[1][k]), P)
        _cara(bm, (adentro[0][k + 1], adentro[0][k], adentro[1][k], adentro[1][k + 1]), P)
        _cara(bm, (afuera[1][k], afuera[1][k + 1], adentro[1][k + 1], adentro[1][k]), P)
        _cara(bm, (afuera[0][k + 1], afuera[0][k], adentro[0][k], adentro[0][k + 1]), P)
    for k, sig in ((0, 1), (5, -1)):
        _cara(bm, (afuera[0][k], afuera[1][k], adentro[1][k], adentro[0][k])[::sig], P)
    dientes_v4(bm, Z_BOCA - 0.019, Z_BOCA - 0.0015, B, BO)
    # BARBA esponjada (como la original): fila siguiendo la cara, fila de abajo y piocha; todo pegado a la palanca
    for k in range(9):
        a = 30 + 120 * k / 8
        x, y = _arco(0.16, a)
        esfera(bm, (x, y, 1.165), (0.045, 0.04, 0.048), mat=B, segs=10, anillos=8)
    for k in range(5):
        a = 55 + 70 * k / 4
        x, y = _arco(0.18, a, -0.016)                    # adelante del cuello dorado: al abrir sigue tapándolo
        esfera(bm, (x, y, 1.135), (0.04, 0.034, 0.04), mat=B, segs=10, anillos=8)
    esfera(bm, (0, -0.215, 1.11), (0.042, 0.032, 0.042), mat=B, segs=12, anillos=8)   # piocha

ROUGH_ORIGINAL = {"Cas_Rojo": 0.5, "Cas_Blanco": 0.8, "Cas_Piel": 0.6, "Cas_Negro": 0.25, "Cas_Mejilla": 0.6, "Cas_Ojos": 0.2, "Cas_Boca": 0.9}

def hacer_cara_v4():
    if "Cas_Boca" not in bpy.data.materials:
        material("Cas_Boca", (0.16, 0.02, 0.03), rugosidad=0.9)
    material("Cas_Ojos", (0.45, 0.01, 0.01), rugosidad=0.2)       # pupila roja (con emisión se ve rojo intenso)
    for n, r in ROUGH_ORIGINAL.items():
        b = next(x for x in bpy.data.materials[n].node_tree.nodes if x.type == "BSDF_PRINCIPLED")
        b.inputs["Roughness"].default_value = r
    cab = bpy.data.objects["Cas_Cabeza"]; mand = bpy.data.objects["Cas_Mandibula"]
    mand.location = PIVOTE_MAND - _mundo_cas(cab).translation
    _poner("Cas_Cabeza", cabeza_v4, ["Cas_Piel", "Cas_Blanco", "Cas_Ojos", "Cas_Negro", "Cas_Mejilla", "Cas_Oro", "Cas_Rojo", "Cas_Boca"])
    _poner("Cas_Mandibula", mandibula_v4, ["Cas_Piel", "Cas_Blanco", "Cas_Boca"])
    for n in ("Cas_Cabeza", "Cas_Mandibula"):
        o = bpy.data.objects[n]; print(n, "tris", sum(len(p.vertices) - 2 for p in o.data.polygons))
