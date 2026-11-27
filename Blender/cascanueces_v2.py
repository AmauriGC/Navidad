# -*- coding: utf-8 -*-
"""
CASCANUECES v2 (Fase 4): rehace la malla de las 7 piezas conservando NOMBRE, PIVOTE y JERARQUÍA, porque
CascanuecesAnimador busca Cas_Cuerpo, Cas_Cabeza, Cas_Mandibula, Cas_BrazoL/R, Cas_PiernaL/R y las gira sobre su pivote;
y VarianteCascanueces cambia los colores de Cas_Rojo / Cas_Azul; los ojos (Cas_Ojos) se encienden al despertar.
Se modela en "coordenadas del cascanueces" (pies en z=0, mira a -Y, 2.1 m de alto) y se pasa al espacio de cada pieza.
Estilo: formas redondeadas (loft/esfera/toro + Subsurf 1), como el elfo v2.
Uso: exec(modelado.py); exec(cascanueces_v2.py); hacer_cascanueces()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

RAIZ_CAS = bpy.data.objects["Cascanueces"]

def parte_cas(nombre, construir, mats):
    obj = bpy.data.objects[nombre]
    M = obj.matrix_world.inverted() @ RAIZ_CAS.matrix_world
    def envuelto(bm):
        construir(bm)
        bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    poner_malla(obj, envuelto, materiales=[bpy.data.materials[m] for m in mats])

# ------------------------------------------------------------------ cuerpo
def cuerpo(bm):
    R, N, O, B = 0, 1, 2, 3
    # faldón de la casaca (abajo, se abre un poco)
    loft(bm, [(0, 0, 0.56), (0, 0, 0.62), (0, 0, 0.68)], [(0.25, 0.18), (0.245, 0.175), (0.235, 0.165)], mat=R, segs=24, sub=2, domo=0.15)
    # casaca: pecho ancho, hombros redondos
    loft(bm, [(0, 0, 0.66), (0, -0.005, 0.8), (0, -0.01, 0.95), (0, 0, 1.08), (0, 0, 1.14)],
         [(0.225, 0.16), (0.235, 0.17), (0.24, 0.172), (0.235, 0.16), (0.2, 0.14)], mat=R, segs=24, sub=3, domo=0.35)
    # cinturón negro con hebilla dorada
    loft(bm, [(0, 0, 0.665), (0, 0, 0.735)], [(0.245, 0.178), (0.245, 0.178)], mat=N, segs=24, sub=1, domo=0.0)
    caja(bm, (0, -0.182, 0.70), (0.1, 0.025, 0.075), mat=O, bisel=0.012)
    caja(bm, (0, -0.19, 0.70), (0.05, 0.015, 0.035), mat=N, bisel=0.006)
    # pechera blanca (plastrón) con alamares dorados y botones
    loft(bm, [(0, -0.155, 0.76), (0, -0.172, 0.9), (0, -0.17, 1.08)], [(0.12, 0.02), (0.13, 0.02), (0.11, 0.02)], mat=B, segs=12, sub=2, domo=0.3)
    for z in (0.8, 0.88, 0.96, 1.04):
        w = 0.1 - 0.012 * (z - 0.8) / 0.08
        loft(bm, [(-w, -0.188, z), (0, -0.193, z - 0.008), (w, -0.188, z)], [(0.009, 0.009)] * 3, mat=O, segs=6, sub=3)
        esfera(bm, (-w, -0.19, z), (0.016, 0.012, 0.016), mat=O, segs=8, anillos=6)
        esfera(bm, (w, -0.19, z), (0.016, 0.012, 0.016), mat=O, segs=8, anillos=6)
    # cuello dorado
    toro(bm, (0, 0, 1.135), 0.165, 0.018, mat=O, segs=24, lados=6)
    # charreteras: disco dorado + flecos
    for s in (-1, 1):
        esfera(bm, (s * 0.27, 0, 1.13), (0.09, 0.085, 0.03), mat=O, segs=14, anillos=6)
        for k in range(9):
            a = math.pi * (k / 8.0) - math.pi / 2
            p = Vector((s * (0.27 + 0.085 * math.cos(a) * (1 if s > 0 else 1)), 0.085 * math.sin(a), 1.12))
            if (p.x - s * 0.27) * s < -0.02: continue
            loft(bm, [p, p + Vector((s * 0.012, 0, -0.06))], [(0.008, 0.008)] * 2, mat=O, segs=5, sub=1, domo=0.8)

# ------------------------------------------------------------------ cabeza
def cabeza(bm):
    P, B, OJ, N, M, O, R = 0, 1, 2, 3, 4, 5, 6
    # cuello alto blanco
    loft(bm, [(0, 0, 1.08), (0, 0, 1.18)], [(0.15, 0.14), (0.14, 0.13)], mat=B, segs=20, sub=1, domo=0.1)
    # cabeza: ovalada, cara un poco al frente
    loft(bm, [(0, 0, 1.16), (0, -0.005, 1.3), (0, -0.005, 1.42), (0, 0, 1.52)],
         [(0.155, 0.15), (0.165, 0.16), (0.16, 0.155), (0.15, 0.145)], mat=P, segs=22, sub=3, domo=0.4)
    # pelo blanco (lados y atrás), esponjado
    for s in (-1, 1):
        for k, (y, z, r) in enumerate(((-0.02, 1.42, 0.07), (0.05, 1.36, 0.075), (0.09, 1.27, 0.07), (0.06, 1.2, 0.06))):
            esfera(bm, (s * 0.155, y, z), (r * 0.7, r, r), mat=B, segs=10, anillos=8)
    for z, r in ((1.42, 0.09), (1.32, 0.1), (1.22, 0.09)):
        esfera(bm, (0, 0.14, z), (0.14, r * 0.7, r), mat=B, segs=12, anillos=8)
    # ojos: blanco + pupila (Cas_Ojos) + cejas pobladas
    for s in (-1, 1):
        esfera(bm, (s * 0.068, -0.15, 1.4), (0.045, 0.025, 0.04), mat=B, segs=14, anillos=10)
        esfera(bm, (s * 0.066, -0.172, 1.4), (0.022, 0.012, 0.026), mat=OJ, segs=12, anillos=8)
        loft(bm, [(s * 0.025, -0.165, 1.455), (s * 0.07, -0.172, 1.468), (s * 0.115, -0.16, 1.455)],
             [(0.016, 0.012), (0.02, 0.014), (0.012, 0.01)], mat=B, segs=8, sub=3)
        esfera(bm, (s * 0.115, -0.115, 1.3), (0.035, 0.02, 0.028), mat=M, segs=12, anillos=8)   # cachete
    # nariz grande redonda
    esfera(bm, (0, -0.19, 1.335), (0.035, 0.045, 0.04), mat=P, segs=14, anillos=10)
    # bigote en dos rizos
    for s in (-1, 1):
        loft(bm, [(0, -0.185, 1.29), (s * 0.06, -0.18, 1.285), (s * 0.11, -0.16, 1.3), (s * 0.13, -0.14, 1.33)],
             [(0.022, 0.016), (0.026, 0.02), (0.018, 0.014), (0.008, 0.008)], mat=B, segs=10, sub=4)
    # sombrero (shako): copa negra, bandas doradas, visera, escudo y pluma roja
    loft(bm, [(0, 0, 1.49), (0, 0, 1.7), (0, 0, 1.92)], [(0.175, 0.17), (0.185, 0.18), (0.2, 0.195)], mat=N, segs=24, sub=2, domo=0.12)
    toro(bm, (0, 0, 1.515), 0.18, 0.02, mat=O, segs=24, lados=6)
    toro(bm, (0, 0, 1.915), 0.2, 0.02, mat=O, segs=24, lados=6)
    loft(bm, [(-0.15, -0.12, 1.505), (0, -0.215, 1.495), (0.15, -0.12, 1.505)], [(0.03, 0.008)] * 3, mat=N, segs=8, sub=4)   # visera
    # escudo: rombo dorado con sol
    esfera(bm, (0, -0.185, 1.69), (0.065, 0.015, 0.08), mat=O, segs=4, anillos=6)
    esfera(bm, (0, -0.198, 1.69), (0.025, 0.01, 0.025), mat=R, segs=10, anillos=6)
    # pluma
    loft(bm, [(0, 0.0, 1.92), (0, 0.01, 1.98), (0, 0.0, 2.05), (0, -0.015, 2.1)], [(0.03, 0.03), (0.055, 0.05), (0.045, 0.04), (0.012, 0.012)], mat=R, segs=12, sub=3, domo=0.5)
    esfera(bm, (0, 0, 1.925), (0.035, 0.035, 0.02), mat=O, segs=10, anillos=6)

# ------------------------------------------------------------------ mandíbula
def mandibula(bm):
    P, B = 0, 1
    loft(bm, [(0, -0.02, 1.13), (0, -0.04, 1.2), (0, -0.04, 1.24)], [(0.13, 0.12), (0.145, 0.13), (0.15, 0.13)], mat=P, segs=18, sub=2, domo=0.3)
    # barba blanca esponjada abajo y a los lados
    for k in range(7):
        a = math.pi * (0.15 + 0.7 * k / 6)
        x = math.cos(a) * 0.13; y = -math.sin(a) * 0.13 - 0.03
        esfera(bm, (x, y, 1.14), (0.045, 0.04, 0.055), mat=B, segs=10, anillos=8)
    esfera(bm, (0, -0.15, 1.12), (0.06, 0.045, 0.06), mat=B, segs=12, anillos=8)
    # dientes (25-nov): fila de 6 dientes redondeados, juntitos, siguiendo el arco del frente de la mandíbula
    # (antes eran 5 cajitas rectas con huecos que no seguían la curva y se veían chimuelos)
    for k in range(6):
        a = -0.5 + 0.2 * k
        x = 0.147 * math.sin(a); y = -0.04 - 0.128 * math.cos(a)
        caja(bm, (x, y, 1.24), (0.027, 0.02, 0.032), mat=B, bisel=0.009, segs=3, giro=Matrix.Rotation(a, 3, "Z"))

# ------------------------------------------------------------------ brazos
def brazo(s, sable):
    def construir(bm):
        R, O, B, PL = 0, 1, 2, 3
        x = s * 0.3
        loft(bm, [(x, 0, 1.1), (x + s * 0.01, 0, 0.95), (x + s * 0.005, -0.005, 0.72)], [(0.075, 0.075), (0.07, 0.07), (0.066, 0.066)], mat=R, segs=16, sub=3, domo=0.6)
        toro(bm, (x + s * 0.005, -0.005, 0.7), 0.066, 0.02, mat=O, segs=18, lados=6)   # puño dorado
        # guante: mano redonda + pulgar
        esfera(bm, (x + s * 0.005, -0.01, 0.62), (0.058, 0.06, 0.07), mat=B, segs=14, anillos=10)
        esfera(bm, (x - s * 0.035, -0.045, 0.64), (0.022, 0.022, 0.03), mat=B, segs=8, anillos=6)
        if sable:
            # empuñadura, guarda curva y hoja apuntando al frente
            loft(bm, [(x, 0.03, 0.62), (x, -0.06, 0.62)], [(0.016, 0.016)] * 2, mat=O, segs=8, sub=1)
            loft(bm, [(x - 0.06, -0.07, 0.6), (x, -0.08, 0.63), (x + 0.06, -0.07, 0.6)], [(0.01, 0.01)] * 3, mat=O, segs=6, sub=3)
            loft(bm, [(x, -0.08, 0.62), (x, -0.3, 0.625), (x, -0.47, 0.615)], [(0.03, 0.009), (0.028, 0.008), (0.006, 0.003)], mat=PL, segs=8, sub=3, domo=0.3)
            esfera(bm, (x, 0.04, 0.62), (0.022, 0.022, 0.022), mat=O, segs=10, anillos=6)
    return construir

# ------------------------------------------------------------------ piernas
def pierna(s):
    def construir(bm):
        A, N, O = 0, 1, 2
        x = s * 0.12
        loft(bm, [(x, 0, 0.7), (x, 0, 0.5), (x, 0, 0.32)], [(0.1, 0.1), (0.09, 0.09), (0.085, 0.085)], mat=A, segs=16, sub=3, domo=0.5)
        # franja dorada al costado
        loft(bm, [(x + s * 0.092, 0, 0.66), (x + s * 0.086, 0, 0.36)], [(0.008, 0.018)] * 2, mat=O, segs=6, sub=1)
        # bota negra con borde dorado
        loft(bm, [(x, 0, 0.0), (x, 0, 0.2), (x, 0, 0.34)], [(0.1, 0.105), (0.095, 0.1), (0.105, 0.105)], mat=N, segs=16, sub=2, domo=0.15)
        toro(bm, (x, 0, 0.335), 0.105, 0.018, mat=O, segs=18, lados=6)
        # puntera redonda
        loft(bm, [(x, -0.02, 0.06), (x, -0.16, 0.055), (x, -0.25, 0.05)], [(0.095, 0.06), (0.09, 0.055), (0.07, 0.04)], mat=N, segs=14, sub=3, domo=0.7)
        caja(bm, (x, -0.08, 0.012), (0.2, 0.36, 0.025), mat=N, bisel=0.01)   # suela
    return construir

def hacer_cascanueces():
    parte_cas("Cas_Cuerpo", cuerpo, ["Cas_Rojo", "Cas_Negro", "Cas_Oro", "Cas_Blanco"])
    parte_cas("Cas_Cabeza", cabeza, ["Cas_Piel", "Cas_Blanco", "Cas_Ojos", "Cas_Negro", "Cas_Mejilla", "Cas_Oro", "Cas_Rojo"])
    parte_cas("Cas_Mandibula", mandibula, ["Cas_Piel", "Cas_Blanco"])
    parte_cas("Cas_BrazoL", brazo(-1, False), ["Cas_Rojo", "Cas_Oro", "Cas_Blanco"])
    parte_cas("Cas_BrazoR", brazo(1, True), ["Cas_Rojo", "Cas_Oro", "Cas_Blanco", "Cas_Plata"])
    parte_cas("Cas_PiernaL", pierna(-1), ["Cas_Azul", "Cas_Negro", "Cas_Oro"])
    parte_cas("Cas_PiernaR", pierna(1), ["Cas_Azul", "Cas_Negro", "Cas_Oro"])
    for n in ("Cas_Cuerpo", "Cas_Cabeza", "Cas_Mandibula", "Cas_BrazoL", "Cas_BrazoR", "Cas_PiernaL", "Cas_PiernaR"):
        o = bpy.data.objects[n]; print(n, "tris base", sum(len(p.vertices) - 2 for p in o.data.polygons))
