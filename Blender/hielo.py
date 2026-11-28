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


# ================================================================== v1.5 (detallitos fase 6): CRISTAL low-poly
def hacer_hielo_cristal():
    """Bloque de hielo como CRISTAL TALLADO low-poly (detallitos v1.5). Mismo tamaño y origen en la base.
    - Pocas facetas GRANDES (casco convexo de ~24 puntos sobre una caja) => se leen como gema.
    - 3 tonos por faceta (claro / medio / profundo) según hacia dónde mira cada cara: así se distinguen las caras
      aunque el material sea transparente (es el truco clásico del low-poly de cristal).
    - Aristas: tiritas delgadas blancas sobre las orillas más marcadas (brillo de corte).
    - Picos de cristal más grandes alrededor y arriba, con la punta más clara.
    - Escarcha: anillo blanco bajito (opaco) en la base.
    Uso: exec(modelado.py); exec(hielo.py); hacer_hielo_cristal()"""
    def mat_hielo(nombre, color, alfa, emi, fuerza):
        m = material(nombre, color, rugosidad=0.04, emision=emi, fuerza=fuerza)
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Alpha"].default_value = alfa
        try: m.surface_render_method = "BLENDED"
        except Exception: m.blend_method = "BLEND"
        return m
    claro = mat_hielo("Hielo_Claro", (0.82, 0.96, 1.0), 0.38, (0.55, 0.85, 1.0), 0.55)
    medio = mat_hielo("Hielo_Medio", (0.5, 0.82, 1.0), 0.45, (0.3, 0.65, 1.0), 0.5)
    hondo = mat_hielo("Hielo_Profundo", (0.25, 0.55, 0.95), 0.52, (0.15, 0.4, 0.95), 0.45)
    arista = material("Hielo_Arista", (0.95, 1.0, 1.0), rugosidad=0.2, emision=(0.75, 0.93, 1.0), fuerza=1.4)
    blanco = material("Hielo_Escarcha", (0.92, 0.96, 1.0), rugosidad=0.8)
    luz = Vector((-0.4, -0.6, 0.7)).normalized()

    def tono(n):
        d = n.dot(luz)
        return 0 if d > 0.35 else (1 if d > -0.15 else 2)

    def gema(bm, seed=11):
        rnd = random.Random(seed)
        tmp = bmesh.new()
        half = Vector((0.5, 0.47, 0.82))
        for _ in range(24):
            d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))
            esc = max(abs(d.x) / half.x, abs(d.y) / half.y, abs(d.z) / half.z)
            p = Vector((d.x / esc, d.y / esc, d.z / esc)) * rnd.uniform(0.9, 1.0)
            p.z += 0.82
            tmp.verts.new(p)
        for x in (-1, 1):
            for y in (-1, 1):
                tmp.verts.new(Vector((x * 0.42, y * 0.39, 0.0)))
        tmp.verts.new(Vector((0.05, -0.02, 1.78)))         # cima: punta de gema
        bmesh.ops.convex_hull(tmp, input=tmp.verts)
        bmesh.ops.dissolve_limit(tmp, angle_limit=math.radians(4), verts=tmp.verts, edges=tmp.edges)   # caras grandes
        bmesh.ops.triangulate(tmp, faces=tmp.faces)
        tmp.normal_update()
        for f in tmp.faces: f.material_index = tono(f.normal); f.smooth = False
        # aristas marcadas => tiritas blancas (prisma delgadito sobre la orilla)
        orillas = [(e.verts[0].co.copy(), e.verts[1].co.copy(), (e.link_faces[0].normal + e.link_faces[1].normal).normalized())
                   for e in tmp.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(28)]
        unir(bm, tmp)   # (unir libera tmp: las orillas se copian antes)
        for a, b, n in orillas:
            tira(bm, a + n * 0.004, b + n * 0.004, 0.0065, 3)

    def tira(bm, a, b, r, mat):
        d = (b - a)
        if d.length < 0.02: return
        rot = d.normalized().to_track_quat("Z", "Y").to_matrix()
        tmp = bmesh.new(); ab, ar = [], []
        for k in range(3):
            ang = k * 2 * math.pi / 3
            v = rot @ Vector((math.cos(ang) * r, math.sin(ang) * r, 0))
            ab.append(tmp.verts.new(a + v)); ar.append(tmp.verts.new(b + v))
        for k in range(3):
            j = (k + 1) % 3
            tmp.faces.new((ab[k], ab[j], ar[j], ar[k]))
        for f in tmp.faces: f.material_index = mat; f.smooth = False
        unir(bm, tmp)

    def pico(bm, base, direccion, largo, radio, lados=5):
        """Cristal con punta: cuerpo de 'lados' caras + punta clara (arista)."""
        tmp = bmesh.new()
        rot = direccion.normalized().to_track_quat("Z", "Y").to_matrix()
        ab, ar = [], []
        for k in range(lados):
            a = k * 2 * math.pi / lados
            v = Vector((math.cos(a) * radio, math.sin(a) * radio, 0))
            ab.append(tmp.verts.new(base + rot @ v))
            ar.append(tmp.verts.new(base + rot @ (v * 0.92 + Vector((0, 0, largo * 0.7)))))
        punta = tmp.verts.new(base + rot @ Vector((0, 0, largo)))
        for k in range(lados):
            j = (k + 1) % lados
            f = tmp.faces.new((ab[k], ab[j], ar[j], ar[k]))
            g = tmp.faces.new((ar[k], ar[j], punta))
        tmp.faces.new(list(reversed(ab)))
        tmp.normal_update()
        for f in tmp.faces:
            f.smooth = False
            f.material_index = 3 if len(f.verts) == 3 and punta in f.verts and f.normal.dot(luz) > 0 else tono(f.normal)
        unir(bm, tmp)

    def construir(bm):
        gema(bm)
        rnd = random.Random(21)
        for k in range(5):           # picos de arriba, abiertos como corona
            a = k * 2 * math.pi / 5 + rnd.uniform(-0.3, 0.3)
            r = rnd.uniform(0.12, 0.26)
            base = Vector((math.cos(a) * r, math.sin(a) * r * 0.9, 1.4))
            d = Vector((math.cos(a) * rnd.uniform(0.35, 0.8), math.sin(a) * rnd.uniform(0.35, 0.8), 1.0))
            pico(bm, base, d, rnd.uniform(0.38, 0.62), rnd.uniform(0.07, 0.11))
        for k in range(7):           # picos alrededor de la base, saliendo del piso hacia afuera
            a = k * 2 * math.pi / 7 + rnd.uniform(-0.2, 0.2)
            base = Vector((math.cos(a) * 0.5, math.sin(a) * 0.47, 0.02))
            d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.9, 1.6)))
            pico(bm, base, d, rnd.uniform(0.22, 0.42), rnd.uniform(0.05, 0.08), lados=4)
        loft(bm, [Vector((0, 0, -0.02)), Vector((0, 0, 0.025))], [(0.74, 0.74), (0.66, 0.66)], mat=4, segs=14, sub=1, domo=0.4)

    col = bpy.data.collections.get("Efectos") or bpy.data.collections.new("Efectos")
    o = bpy.data.objects.get("BloqueHielo")
    if o is None:
        o = bpy.data.objects.new("BloqueHielo", bpy.data.meshes.new("BloqueHielo_tmp")); col.objects.link(o)
    poner_malla(o, construir, materiales=[claro, medio, hondo, arista, blanco], subsurf=0)
    o.data.name = "BloqueHielo"
    for p in o.data.polygons: p.use_smooth = False
    print("BloqueHielo cristal", len(o.data.polygons), "caras")
    return o
