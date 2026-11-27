# -*- coding: utf-8 -*-
"""
PROPS DEL JUEGO hechos en Blender (antes eran figuras básicas de Unity):
  - Indicador.glb : signo "!" dorado brillante que flota sobre los letreros.
  - Tapete.glb    : tapete redondo bajo el árbol (orilla trenzada tipo bastón de caramelo y copos de nieve).
  - BolaNieve.glb : bola de nieve con grumos (no una esfera perfecta).
Se ejecuta dentro de Blender después de renos.py (usa sus funciones loft/esfera/toro):
  exec(open(".../Blender/renos.py").read()); exec(open(".../Blender/props_juego.py").read())
Ejes de Blender: arriba = +Z.  Los .glb quedan en Assets/Modelos/.
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

PROYECTO = "/home/cris/Escritorio/10A/ulises/Navidad"


def material(nombre, color, metal=0.0, rugosidad=0.6, emision=None, fuerza=1.0):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rugosidad
    if emision:
        bsdf.inputs["Emission Color"].default_value = (*emision, 1)
        bsdf.inputs["Emission Strength"].default_value = fuerza
    return m


def objeto_nuevo(nombre, construir, mats, coleccion="PropsJuego", subsurf=1):
    """Crea (o reemplaza) un objeto con la malla de construir(bm)."""
    viejo = bpy.data.objects.get(nombre)
    if viejo: bpy.data.objects.remove(viejo, do_unlink=True)
    bm = bmesh.new(); construir(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(nombre, me)
    col = bpy.data.collections.get(coleccion) or bpy.data.collections.new(coleccion)
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    col.objects.link(o)
    if subsurf:
        s = o.modifiers.new("Redondeo", "SUBSURF"); s.levels = subsurf; s.render_levels = subsurf
    return o


def exportar_obj(o, archivo):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=f"{PROYECTO}/Assets/Modelos/{archivo}", use_selection=True, export_apply=True, export_yup=True)


# ------------------------------------------------------------------ "!" dorado
def indicador(bm):
    # barra: más ancha arriba, redondeada en las puntas (loft con domos)
    loft(bm, [(0, 0, 0.30), (0, 0, 0.20), (0, 0, 0.08), (0, 0, 0.0)],
         [(0.05, 0.035), (0.045, 0.031), (0.032, 0.024), (0.026, 0.02)], mat=0, segs=14, sub=3, domo=0.9, arriba=Vector((0, 1, 0)))
    esfera(bm, (0, 0, -0.085), (0.034, 0.03, 0.034), mat=0)            # punto
    # destellos de 4 puntas a los lados
    for (x, z, t) in ((0.11, 0.24, 0.035), (-0.10, 0.06, 0.026)):
        for ang in (0, 90):
            a = math.radians(ang)
            d = Vector((math.cos(a), 0, math.sin(a)))
            loft(bm, [tuple(Vector((x, 0, z)) - d * t), (x, 0, z), tuple(Vector((x, 0, z)) + d * t)],
                 [(0.002, 0.002), (0.011, 0.006), (0.002, 0.002)], mat=0, segs=6, sub=2, domo=0.3, arriba=Vector((0, 1, 0)))


# ------------------------------------------------------------------ tapete redondo
def tapete(bm, R=2.3):
    def disco(r0, r1, z, mat, segs=96):
        """Anillo plano entre r0 y r1 (r0 = 0 => disco lleno)."""
        if r0 <= 0:
            c = bm.verts.new((0, 0, z))
            ext = [bm.verts.new((r1 * math.cos(2 * math.pi * i / segs), r1 * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
            for i in range(segs):
                f = bm.faces.new((c, ext[i], ext[(i + 1) % segs])); f.material_index = mat
            return
        a = [bm.verts.new((r0 * math.cos(2 * math.pi * i / segs), r0 * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
        b = [bm.verts.new((r1 * math.cos(2 * math.pi * i / segs), r1 * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)]
        for i in range(segs):
            f = bm.faces.new((a[i], b[i], b[(i + 1) % segs], a[(i + 1) % segs])); f.material_index = mat
    # base roja con un poco de grosor (lado del disco)
    disco(0, R - 0.08, 0.012, 0)
    segs = 96
    lado_a = [bm.verts.new(((R - 0.08) * math.cos(2 * math.pi * i / segs), (R - 0.08) * math.sin(2 * math.pi * i / segs), 0.0)) for i in range(segs)]
    lado_b = [bm.verts.new(((R - 0.08) * math.cos(2 * math.pi * i / segs), (R - 0.08) * math.sin(2 * math.pi * i / segs), 0.012)) for i in range(segs)]
    for i in range(segs):
        f = bm.faces.new((lado_a[i], lado_a[(i + 1) % segs], lado_b[(i + 1) % segs], lado_b[i])); f.material_index = 0
    # anillos decorativos: dorado fino, verde y dorado
    disco(R - 0.42, R - 0.38, 0.014, 3)
    disco(R - 0.62, R - 0.50, 0.014, 2)
    disco(1.05, 1.09, 0.014, 3)
    # orilla trenzada tipo bastón de caramelo: dona con franjas rojo/blanco en espiral
    Rt, rt, n, lados = R - 0.06, 0.055, 160, 10
    filas = []
    for i in range(n):
        a = 2 * math.pi * i / n
        fila = []
        for j in range(lados):
            b = 2 * math.pi * j / lados
            p = Vector(((Rt + rt * math.cos(b)) * math.cos(a), (Rt + rt * math.cos(b)) * math.sin(a), 0.04 + rt * 0.75 * math.sin(b)))
            fila.append(bm.verts.new(p))
        filas.append(fila)
    for i in range(n):
        for j in range(lados):
            f = bm.faces.new((filas[i][j], filas[(i + 1) % n][j], filas[(i + 1) % n][(j + 1) % lados], filas[i][(j + 1) % lados]))
            f.smooth = True
            franja = (i * 2 + j * 3) // 9 % 2          # espiral: depende de i y j
            f.material_index = 1 if franja else 0
    # 12 copos de nieve blancos entre los anillos
    for k in range(12):
        a = 2 * math.pi * k / 12 + math.pi / 12
        c = Vector((math.cos(a) * (R - 0.82), math.sin(a) * (R - 0.82), 0.016))
        for brazo in range(6):
            b = a + math.pi / 3 * brazo
            d = Vector((math.cos(b), math.sin(b), 0)); perp = Vector((-d.y, d.x, 0))
            for (u0, u1, ancho) in ((0.0, 0.16, 0.014),):
                p0, p1 = c + d * u0, c + d * u1
                vs = [bm.verts.new(p0 - perp * ancho), bm.verts.new(p1 - perp * ancho * 0.6), bm.verts.new(p1 + perp * ancho * 0.6), bm.verts.new(p0 + perp * ancho)]
                bm.faces.new(vs).material_index = 1
            for s in (-1, 1):   # ramitas en V
                q0 = c + d * 0.09
                e = (d + perp * s * 0.9).normalized(); pe = Vector((-e.y, e.x, 0))
                vs = [bm.verts.new(q0 - pe * 0.008), bm.verts.new(q0 + e * 0.06 - pe * 0.005), bm.verts.new(q0 + e * 0.06 + pe * 0.005), bm.verts.new(q0 + pe * 0.008)]
                bm.faces.new(vs).material_index = 1
    # estrella dorada de 8 puntas en el centro (se ve alrededor del árbol)
    puntas = 8
    c = bm.verts.new((0, 0, 0.016))
    contorno = []
    for i in range(puntas * 2):
        r = 1.0 if i % 2 == 0 else 0.62
        a = math.pi * i / puntas
        contorno.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0.016)))
    for i in range(len(contorno)):
        bm.faces.new((c, contorno[i], contorno[(i + 1) % len(contorno)])).material_index = 3


# ------------------------------------------------------------------ bola de nieve con grumos
def bola(bm):
    res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.5)
    for v in res["verts"]:
        n = v.co.normalized()
        g = noise.noise(n * 2.3) * 0.06 + noise.noise(n * 5.1 + Vector((3, 1, 2))) * 0.025
        v.co = n * (0.5 + g)
    for f in bm.faces: f.smooth = True


M_ORO = material("Indicador_Oro", (1.0, 0.78, 0.22), metal=0.6, rugosidad=0.3, emision=(1.0, 0.72, 0.18), fuerza=2.5)
o_ind = objeto_nuevo("Indicador", indicador, [M_ORO])
mats_tap = [material("Tap_Rojo", (0.55, 0.06, 0.07), rugosidad=0.9), material("Tap_Blanco", (0.92, 0.9, 0.86), rugosidad=0.85),
            material("Tap_Verde", (0.08, 0.32, 0.16), rugosidad=0.9), material("Tap_Oro", (0.95, 0.72, 0.25), metal=0.7, rugosidad=0.35)]
o_tap = objeto_nuevo("Tapete", tapete, mats_tap, subsurf=0)
o_bola = objeto_nuevo("BolaNieve", bola, [material("Nieve_Bola", (0.93, 0.96, 1.0), rugosidad=0.75)], subsurf=0)
# los props quedan apartados a un lado para no estorbar en la escena de Blender
o_ind.location = (-6, -6, 1); o_tap.location = (-6, -10, 0); o_bola.location = (-6, -6, 0.5)
for o, archivo in ((o_ind, "Indicador.glb"), (o_tap, "Tapete.glb"), (o_bola, "BolaNieve.glb")):
    guardado = o.location.copy(); o.location = (0, 0, 0)
    exportar_obj(o, archivo)
    o.location = guardado
print("props exportados")
