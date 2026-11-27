# -*- coding: utf-8 -*-
"""
BLOQUE DE HIELO (modos Difícil/Imposible): cuando un cascanueces nevado te pega 3 bolas en 5 segundos te congelas
y el elfo queda dentro de este bloque.
 - Bloque: CASCO CONVEXO (convex hull) de puntos al azar alrededor de una caja => caras planas en ángulos raros,
   como hielo tallado. Material transparente (alpha BLEND) azul clarito con un poquito de brillo.
 - Cristales: 7 prismas hexagonales con punta que salen del bloque (arriba y a los lados).
 - Escarcha: anillo blanco abombado en la base (pegado al piso).
El origen queda en la BASE (el piso del elfo). Exporta Assets/Modelos/BloqueHielo.glb.
Uso: exec(modelado.py); exec(este); hacer_hielo()
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix


def bloque(bm, mat=0, seed=3):
    rnd = random.Random(seed)
    tmp = bmesh.new()
    half = Vector((0.5, 0.47, 0.8))
    for _ in range(60):
        # punto al azar proyectado sobre una CAJA (0.95 x 0.9 x 1.6) y metido un poquito => caras talladas
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))
        esc = max(abs(d.x) / half.x, abs(d.y) / half.y, abs(d.z) / half.z)
        p = Vector((d.x / esc, d.y / esc, d.z / esc)) * rnd.uniform(0.86, 1.0)
        p.z += 0.8
        tmp.verts.new(p)
    for x in (-1, 1):            # esquinas de la base para que asiente parejo en el piso
        for y in (-1, 1):
            tmp.verts.new(Vector((x * 0.44, y * 0.41, 0.0)))
    bmesh.ops.convex_hull(tmp, input=tmp.verts)
    for f in tmp.faces: f.material_index = mat; f.smooth = False
    unir(bm, tmp)


def cristal(bm, base, direccion, largo, radio, mat=0):
    """Prisma hexagonal con punta, de 'base' hacia 'direccion'."""
    tmp = bmesh.new()
    rot = direccion.normalized().to_track_quat("Z", "Y").to_matrix()
    abajo, arriba = [], []
    for k in range(6):
        a = k * math.pi / 3
        v = Vector((math.cos(a) * radio, math.sin(a) * radio, 0))
        abajo.append(tmp.verts.new(base + rot @ v))
        arriba.append(tmp.verts.new(base + rot @ (v + Vector((0, 0, largo * 0.75)))))
    punta = tmp.verts.new(base + rot @ Vector((0, 0, largo)))
    for k in range(6):
        j = (k + 1) % 6
        tmp.faces.new((abajo[k], abajo[j], arriba[j], arriba[k]))
        tmp.faces.new((arriba[k], arriba[j], punta))
    tmp.faces.new(list(reversed(abajo)))
    for f in tmp.faces: f.material_index = mat; f.smooth = False
    unir(bm, tmp)


def escarcha(bm, mat=1):
    pts = [Vector((0, 0, -0.02)), Vector((0, 0, 0.03))]
    loft(bm, pts, [(0.78, 0.78), (0.7, 0.7)], mat=mat, segs=28, sub=1, domo=0.5)


def hacer_hielo():
    hielo = material("Hielo", (0.7, 0.9, 1.0), rugosidad=0.06, emision=(0.45, 0.78, 1.0), fuerza=0.9)
    bsdf = next(n for n in hielo.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Alpha"].default_value = 0.62
    try: hielo.surface_render_method = "BLENDED"
    except Exception: hielo.blend_method = "BLEND"
    blanco = material("Hielo_Escarcha", (0.92, 0.96, 1.0), rugosidad=0.8)

    def construir(bm):
        bloque(bm, 0)
        rnd = random.Random(9)
        for k in range(6):       # cristales: salen de la parte de ARRIBA, inclinados hacia afuera
            a = k * 2 * math.pi / 6 + rnd.uniform(-0.25, 0.25)
            r = rnd.uniform(0.1, 0.3)
            base = Vector((math.cos(a) * r, math.sin(a) * r * 0.9, 1.45))
            d = Vector((math.cos(a) * rnd.uniform(0.4, 0.9), math.sin(a) * rnd.uniform(0.4, 0.9), 1.0))
            cristal(bm, base, d, rnd.uniform(0.3, 0.5), rnd.uniform(0.06, 0.09), 0)
        for k in range(4):       # unos chiquitos en las esquinas de abajo
            a = math.pi / 4 + k * math.pi / 2
            cristal(bm, Vector((math.cos(a) * 0.45, math.sin(a) * 0.42, 0.12)), Vector((math.cos(a), math.sin(a), 0.9)), 0.28, 0.06, 0)
        escarcha(bm, 1)

    col = bpy.data.collections.get("Efectos") or bpy.data.collections.new("Efectos")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    o = bpy.data.objects.get("BloqueHielo")
    if o is None:
        o = bpy.data.objects.new("BloqueHielo", bpy.data.meshes.new("BloqueHielo_tmp")); col.objects.link(o)
    o.location = (6, -3, 0)
    poner_malla(o, construir, materiales=[hielo, blanco], subsurf=0)
    o.data.name = "BloqueHielo"
    exportar_glb([o], "BloqueHielo.glb", raiz=o)
    print("BloqueHielo", len(o.data.polygons), "caras")
