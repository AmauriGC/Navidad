# -*- coding: utf-8 -*-
"""
VENTANAL DE LA CASA EN A: tenía DOS cuadrículas encimadas (una vieja de barras biseladas y otra nueva de barras
delgadas) que no coincidían, y barras que se salían del triángulo del vidrio -> se veía "chueco y a destiempo".
Ahora: se borran las dos (Amb_MaderaOscura delante del vidrio, x > 3.1) y se hace UNA cuadrícula limpia:
  - el vidrio es un triángulo: abajo z = 0.9 con medio ancho 2.29; punta arriba en z = 4.99 (y = 0)
  - 5 verticales parejas (y = 0, ±0.76, ±1.52) que terminan justo en la orilla inclinada
  - 3 horizontales (z = 1.95, 2.97, 3.98) recortadas al ancho del triángulo a esa altura
  - marco interior por las dos orillas inclinadas + alféizar abajo
Todas las barras con bisel suave, en el mismo material (Amb_MaderaOscura). Se aplica a la malla CasaA (las 2 casas en A).
Uso: exec(modelado.py); exec(ventanal_casaA.py); hacer_ventanal()
"""
import bpy, bmesh, math
from mathutils import Vector

Z0, Z1, W0, X = 0.9, 4.99, 2.29, 3.165       # base, punta, medio ancho abajo, plano de las barras (centro en x)
G = 0.075                                     # grosor de barra

def medio_ancho(z):
    return W0 * (Z1 - z) / (Z1 - Z0)

def hacer_ventanal():
    me = bpy.data.meshes["CasaA"]; nm = [m.name for m in me.materials]
    im = nm.index("Amb_MaderaOscura")
    bm = bmesh.new(); bm.from_mesh(me)
    viejas = [f for f in bm.faces if f.material_index == im and all(v.co.x > 3.1 and Z0 - 0.05 < v.co.z < Z1 + 0.05 and abs(v.co.y) < W0 + 0.05 for v in f.verts)]
    bmesh.ops.delete(bm, geom=viejas, context="FACES")
    nuevo = bmesh.new()
    prof = 0.09                                                # de x = 3.12 a 3.21
    # verticales
    for y in (0.0, -0.76, 0.76, -1.52, 1.52):
        ztop = Z1 - abs(y) / W0 * (Z1 - Z0) - G * 0.6
        caja(nuevo, (X, y, (Z0 + ztop) / 2), (prof, G, ztop - Z0), mat=0, bisel=0.015, segs=2)
    # horizontales
    for z in (1.95, 2.97, 3.98):
        w = medio_ancho(z) - G * 0.5
        caja(nuevo, (X, 0, z), (prof, 2 * w, G), mat=0, bisel=0.015, segs=2)
    # marco interior por las orillas inclinadas: una barra larga hecha en el origen, girada y llevada a su orilla
    L = math.hypot(W0, Z1 - Z0); ang = math.atan2(Z1 - Z0, W0)
    for s in (-1, 1):
        antes = set(nuevo.verts)
        caja(nuevo, (0, 0, 0), (prof + 0.01, L, G * 1.3), mat=0, bisel=0.015, segs=2)
        a = -s * ang
        ca, sa = math.cos(a), math.sin(a)
        for v in nuevo.verts:
            if v in antes: continue
            y, z = v.co.y, v.co.z
            v.co.y = y * ca - z * sa + s * W0 / 2
            v.co.z = y * sa + z * ca + (Z0 + Z1) / 2
            v.co.x += X
    # alféizar
    caja(nuevo, (X + 0.03, 0, Z0 + 0.01), (prof + 0.08, 2 * W0 + 0.1, 0.07), mat=0, bisel=0.02, segs=2)
    for f in nuevo.faces: f.material_index = im
    tmp = bpy.data.meshes.new("_tmp"); nuevo.to_mesh(tmp); nuevo.free()
    bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    bm.to_mesh(me); bm.free(); me.update()
    print("barras viejas borradas (caras):", len(viejas))
