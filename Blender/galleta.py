# -*- coding: utf-8 -*-
"""
GALLETA DE JENGIBRE (coleccionable). Muñequito plano de galleta con glaseado blanco en zigzag,
ojos, sonrisa y botones de dulce. Mira a -Y (frente), ~0.5 m de alto, origen en el centro.
Uso: exec(modelado.py); exec(galleta.py)   -> Assets/Modelos/Galleta.glb
"""
import bpy, bmesh, math
from mathutils import Vector

MATS = [material("Galleta_Masa", (0.55, 0.28, 0.1), rugosidad=0.85),
        material("Galleta_Glaseado", (0.97, 0.95, 0.92), rugosidad=0.4, emision=(1, 1, 1), fuerza=0.25),
        material("Galleta_DulceRojo", (0.85, 0.08, 0.1), rugosidad=0.3, emision=(1, 0.1, 0.1), fuerza=0.4),
        material("Galleta_DulceVerde", (0.1, 0.65, 0.2), rugosidad=0.3, emision=(0.1, 1, 0.2), fuerza=0.4),
        bpy.data.materials["Cas_Negro"]]
MASA, GLAS, ROJO, VERDE, NEGRO = range(5)
G = 0.045      # medio grosor de la galleta

def galleta(bm):
    esfera(bm, (0, 0, 0.17), (0.115, G, 0.11), mat=MASA, segs=24, anillos=12)                     # cabeza
    loft(bm, [(0, 0, 0.08), (0, 0, -0.02), (0, 0, -0.1)], [(0.1, G), (0.115, G), (0.1, G)], mat=MASA, segs=20, sub=3, domo=0.5,
         arriba=Vector((0, 1, 0)))                                                                 # cuerpo
    for s in (-1, 1):
        brazo = [(s * 0.06, 0, 0.04), (s * 0.15, 0, 0.06), (s * 0.21, 0, 0.1)]
        loft(bm, brazo, [(0.05, G * 0.95), (0.045, G * 0.95), (0.042, G * 0.95)], mat=MASA, segs=16, sub=3, domo=0.9, arriba=Vector((0, 1, 0)))
        pierna = [(s * 0.04, 0, -0.08), (s * 0.08, 0, -0.17), (s * 0.11, 0, -0.25)]
        loft(bm, pierna, [(0.055, G * 0.95), (0.05, G * 0.95), (0.048, G * 0.95)], mat=MASA, segs=16, sub=3, domo=0.9, arriba=Vector((0, 1, 0)))
        # glaseado en zigzag en la punta de brazos y piernas (frente y atrás)
        for lado in (-1, 1):
            y = lado * (G + 0.004)
            for (cx, cz, ang) in ((s * 0.19, 0.09, 0.4 * s), (s * 0.1, -0.22, 1.3 * s)):
                zz = []
                for k in range(7):
                    t = (k / 6 - 0.5) * 0.085
                    d = Vector((math.cos(ang), 0, math.sin(ang)))
                    perp = Vector((-d.z, 0, d.x))
                    p = Vector((cx, y, cz)) + perp * t + d * (0.014 if k % 2 else -0.014)
                    zz.append(tuple(p))
                loft(bm, zz, [(0.008, 0.006)] * 7, mat=GLAS, segs=6, sub=2, domo=0.9)
        # ojos, mejillas
        esfera(bm, (s * 0.04, -G - 0.003, 0.19), (0.016, 0.01, 0.02), mat=NEGRO, segs=10, anillos=6)
        esfera(bm, (s * 0.075, -G - 0.002, 0.14), (0.016, 0.006, 0.012), mat=ROJO, segs=8, anillos=5)
    # sonrisa de glaseado
    arco = [(0.045 * math.sin(a), -G - 0.004, 0.135 - 0.02 * math.cos(a)) for a in (-1.2, -0.6, 0, 0.6, 1.2)]
    loft(bm, arco, [(0.007, 0.006)] * 5, mat=GLAS, segs=6, sub=3, domo=0.9)
    # botones de dulce
    for k, z in enumerate((0.04, -0.01, -0.06)):
        esfera(bm, (0, -G - 0.006, z), (0.022, 0.012, 0.022), mat=ROJO if k % 2 == 0 else VERDE, segs=12, anillos=8)
    # moñito rojo en el cuello
    for s in (-1, 1):
        loft(bm, [(0, -G - 0.004, 0.075), (s * 0.035, -G - 0.008, 0.09), (s * 0.045, -G - 0.006, 0.07), (0, -G - 0.004, 0.075)],
             [(0.012, 0.006)] * 4, mat=ROJO, segs=6, sub=3, domo=0.5)


col = bpy.data.collections.get("PropsJuego") or bpy.data.collections.new("PropsJuego")
viejo = bpy.data.objects.get("Galleta")
if viejo: bpy.data.objects.remove(viejo, do_unlink=True)
me = bpy.data.meshes.new("Galleta"); o = bpy.data.objects.new("Galleta", me); col.objects.link(o)
poner_malla(o, galleta, materiales=MATS, subsurf=1)
o.location = (-6, -4, 1)
exportar_glb([o], "Galleta.glb", raiz=o)
print("galleta lista")
