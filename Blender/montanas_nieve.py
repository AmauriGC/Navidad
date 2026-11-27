# -*- coding: utf-8 -*-
"""
MONTAÑAS DEL FONDO con nieve de ORILLA SUAVE (rehace la malla de Montanas_v2, mismo objeto y forma).
Antes: cada cara era roca O nieve (material por cara) -> la orilla de la nieve salía en escalones cuadrados.
Ahora:
  1. La montaña se hace igual que antes (anillo con crestas "ridged" + ruido suave), toda de ROCA.
  2. Encima va una CAPA de nieve (nieve_campo, igual que en las rocas del patio): se copian las caras, y cada vértice
     se empuja hacia afuera grosor * campo. El campo (0 a 1) mezcla suavemente:
        - altura: más arriba de ~19 m (con manchas de ruido) hay nieve,
        - pendiente: en lo plano (normal casi vertical) también se acumula nieve.
     Donde el campo vale 0 la capa queda hundida dentro de la roca y no se ve => la orilla es una curva limpia.
Uso: exec(modelado.py); exec(montanas_nieve.py); hacer_montanas()
"""
import bpy, bmesh, math
from mathutils import Vector, noise

def suave01(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def nieve_campo(bm, caras, campo, grosor, mat, hundir=0.012):
    if not caras: return
    bm.normal_update()
    normales = {v: v.normal.copy() for f in caras for v in f.verts}
    dup = bmesh.ops.duplicate(bm, geom=list(caras))
    vmap = dup["vert_map"]
    nuevas = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
    peso = {}
    for o, v in vmap.items():
        if not isinstance(o, bmesh.types.BMVert) or o not in normales: continue
        n = normales[o]; w = campo(o.co, n); peso[v] = w
        v.co = o.co + n * (grosor * w - hundir)
    borrar = [f for f in nuevas if all(peso.get(v, 0) < 0.02 for v in f.verts)]
    for f in nuevas: f.material_index = mat; f.smooth = True
    bmesh.ops.delete(bm, geom=borrar, context="FACES")

def roca(bm, NA=400, NR=46):
    r0, r1 = 118.0, 200.0
    filas = []
    for i in range(NR):
        t = i / (NR - 1)
        r = r0 + (r1 - r0) * (t ** 0.85)
        fila = []
        for j in range(NA):
            a = 2 * math.pi * j / NA
            p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
            q = p * 0.012
            cresta = noise.ridged_multi_fractal(q, 1.0, 2.1, 5, 1.0, 2.0)
            suave = noise.fractal(q * 0.5 + Vector((7, 3, 1)), 0.6, 2.0, 3)
            sube = min(1.0, max(0.0, (r - 122) / 45.0)) ** 1.8
            h = sube * (8 + 20 * max(cresta, 0) ** 1.3 + 9 * suave)
            if r > 180: h += (r - 180) * 0.9
            fila.append(bm.verts.new((p.x, p.y, h - 2.0)))
        filas.append(fila)
    caras = []
    for i in range(NR - 1):
        for j in range(NA):
            f = bm.faces.new((filas[i][j], filas[i][(j + 1) % NA], filas[i + 1][(j + 1) % NA], filas[i + 1][j]))
            f.smooth = True; f.material_index = 0; caras.append(f)
    return caras

def campo_nieve(p, n):
    nz = abs(n.z)
    manchas = noise.noise(p * 0.08) * 6 + noise.noise(p * 0.25) * 1.5
    alto = suave01((p.z + manchas - 19.0) / 4.0)
    plano = suave01((nz - 0.9) / 0.06) * suave01((p.z - 6.0) / 4.0)
    return max(alto, plano)

def hacer_montanas():
    o = bpy.data.objects["Montanas_v2"]; me = o.data
    bm = bmesh.new()
    caras = roca(bm)
    bmesh.ops.recalc_face_normals(bm, faces=caras)          # normales hacia AFUERA (arriba): si no, la nieve sale al revés
    bm.normal_update()
    if sum(f.normal.z for f in caras) < 0: bmesh.ops.reverse_faces(bm, faces=caras)
    nieve_campo(bm, caras, campo_nieve, grosor=0.9, mat=1, hundir=0.25)
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    print("montañas tris:", sum(len(p.vertices) - 2 for p in me.polygons))
