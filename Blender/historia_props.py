# -*- coding: utf-8 -*-
"""
PIEZAS DE LA HISTORIA v1.5 (estilo LOW-POLY de caras planas). Coordenadas de Blender (unity = (-bx, bz, -by)).
  hacer_llave()        Cas_Llave: llave de cuerda de latón en la espalda del cascanueces (hijo de Cas_Cuerpo,
                       pivote en la base del eje, gira en su eje Y LOCAL) -> Cascanueces.glb
  hacer_estrella_rota() Pieza_EstrellaRota: la estrella del árbol partida en 3 pedazos, apagada (UNA malla) -> .glb propio
  hacer_caja_lote()    Caja_Lote24: caja de juguetes de madera volcada, tapa abierta, paja y "LOTE 24" (colección Props)
  hacer_fusible()      Refaccion_Fusible: la 3a refacción (reemplaza a la llave inglesa) -> .glb propio
Uso: exec(modelado.py); exec(siete_v3.py); exec(cuarto_maquinas.py); exec(historia_props.py); hacer_todo()
(siete_v3 aporta cil/domo/tira/contorno/reemplazar_malla; cuarto_maquinas aporta texto()).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

CAJA_POS = (-1.5, 7.7, 0.0)        # Unity (1.5, 0, -7.7): entre Repisa_Sur_A y Repisa_Sur_B


# ------------------------------------------------------------------ llave de cuerda
def _espalda_cuerpo(z_mundo):
    """Punto de la espalda (+Y) de Cas_Cuerpo a la altura z (rayo contra la malla real)."""
    cu = bpy.data.objects["Cas_Cuerpo"]
    mw = cu.matrix_world.copy()
    bvh = BVHTree.FromObject(cu, bpy.context.evaluated_depsgraph_get())
    inv = mw.inverted()
    o = inv @ Vector((0, 2.0, z_mundo)); d = (inv.to_3x3() @ Vector((0, -1, 0))).normalized()
    hit, nor, _, _ = bvh.ray_cast(o, d)
    return hit, nor


def llave(bm):
    # eje (sale hacia +Y), collarín y las dos "alas" redondas de la mariposa
    cil(bm, (0, -0.01, 0), (0, 0.11, 0), 0.016, 0, segs=6)
    cil(bm, (0, 0.0, 0), (0, 0.025, 0), 0.035, 0, segs=8)
    cil(bm, (0, 0.1, 0), (0, 0.13, 0), 0.03, 0, segs=6)
    for s in (-1, 1):
        lados = 10
        c = Vector((s * 0.075, 0.115, 0.0))
        e = [c + Vector((0.07 * math.cos(2 * math.pi * k / lados), 0, 0.06 * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
        i = [c + Vector((0.035 * math.cos(2 * math.pi * k / lados), 0, 0.028 * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
        vs = [[bm.verts.new(p + Vector((0, dy, 0))) for p in anillo] for anillo in (e, i) for dy in (-0.012, 0.012)]
        ea, eb, ia, ib = vs
        for k in range(lados):
            j = (k + 1) % lados
            for q in ((ea[k], ea[j], eb[j], eb[k]), (ia[k], ib[k], ib[j], ia[j]), (ea[k], ia[k], ia[j], ea[j]), (eb[k], eb[j], ib[j], ib[k])):
                bm.faces.new(q).material_index = 0
        cil(bm, (s * 0.02, 0.115, 0), (s * 0.045, 0.115, 0), 0.02, 0, segs=6)   # brazo que une el eje con el ala


def hacer_llave():
    cu = bpy.data.objects["Cas_Cuerpo"]
    hit, nor = _espalda_cuerpo(0.98)
    if hit is None: raise RuntimeError("no encontré la espalda del cascanueces")
    o = bpy.data.objects.get("Cas_Llave")
    if o is None:
        o = bpy.data.objects.new("Cas_Llave", bpy.data.meshes.new("Cas_Llave"))
        for c in cu.users_collection: c.objects.link(o)
    bm = bmesh.new(); llave(bm)
    for v in bm.verts: v.co *= 1.6                     # grandota: es el símbolo de la historia
    reemplazar_malla(o, bm, [bpy.data.materials["Cas_Oro"]])
    o.parent = cu; o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = hit - Vector((0, 0.01, 0)); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    return f"llave en la espalda (local {tuple(round(v, 3) for v in o.location)}), {len(o.data.polygons)} caras"


# ------------------------------------------------------------------ estrella rota
def hacer_estrella_rota():
    base = bpy.data.objects["Pieza_Estrella"]
    dg = bpy.context.evaluated_depsgraph_get()
    me0 = bpy.data.meshes.new_from_object(base.evaluated_get(dg))
    rota = material("Estrella_Rota", (0.72, 0.56, 0.22), metal=0.5, rugosidad=0.55, emision=(1.0, 0.75, 0.3), fuerza=0.08)
    grieta = material("Estrella_Grieta", (0.32, 0.22, 0.08), rugosidad=0.9)
    total = bmesh.new()
    rnd = random.Random(24)
    angulos = (100, 220, 340)                       # rayos de corte (en el plano XZ, la estrella mira a -Y)
    for k in range(3):
        a0, a1 = math.radians(angulos[k]), math.radians(angulos[(k + 1) % 3] + (360 if k == 2 else 0))
        bm = bmesh.new(); bm.from_mesh(me0)
        for f in bm.faces: f.material_index = 0
        # sector [a0, a1] (120°) = dos semiplanos
        for (a, signo) in ((a0, 1), (a1, -1)):
            ray = Vector((math.cos(a), 0, math.sin(a)))
            n = Vector((-ray.z, 0, ray.x)) * signo          # normal hacia adentro del sector
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
            res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=n, clear_inner=True)
            bordes = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
            if bordes:
                nuevas = bmesh.ops.holes_fill(bm, edges=bordes, sides=0)["faces"]
                for f in nuevas: f.material_index = 1          # la cara del corte se ve oscura (grieta)
        # cada pedazo se separa un poquito del centro y se gira tantito (se ve "pegado de a mentiritas")
        medio = (a0 + a1) / 2
        dirm = Vector((math.cos(medio), 0, math.sin(medio)))
        giro = Matrix.Rotation(rnd.uniform(-0.12, 0.12), 3, "Y") @ Matrix.Rotation(rnd.uniform(-0.1, 0.1), 3, "Z")
        for v in bm.verts: v.co = giro @ v.co + dirm * 0.025 + Vector((0, rnd.uniform(-0.01, 0.01), 0))
        unir(total, bm)
    bpy.data.meshes.remove(me0)
    o = bpy.data.objects.get("Pieza_EstrellaRota")
    if o is None:
        o = bpy.data.objects.new("Pieza_EstrellaRota", bpy.data.meshes.new("Pieza_EstrellaRota"))
        bpy.data.collections["Piezas"].objects.link(o)
    reemplazar_malla(o, total, [rota, grieta])
    o.location = (base.location.x + 0.8, base.location.y, base.location.z)
    return f"estrella rota: {len(o.data.polygons)} caras"


# ------------------------------------------------------------------ caja del lote 24
def texto_arriba(bm, cadena, centro, tam, mat):
    """Texto en relieve acostado (mira a +Z); se lee bien desde -Y (desde el árbol)."""
    cu = bpy.data.curves.new("_txt", "FONT"); cu.body = cadena; cu.size = tam; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.004; cu.resolution_u = 2
    ob = bpy.data.objects.new("_txt", cu); bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    tmp = bmesh.new(); tmp.from_mesh(me); bpy.data.meshes.remove(me)
    for v in tmp.verts: v.co = v.co + Vector(centro)
    for f in tmp.faces: f.material_index = mat
    unir(bm, tmp)


def caja_lote(bm):
    MAD, MAD2, OSC, PAJA, NEGRO, ROJO, CREMA = range(7)
    # la caja está VOLCADA: acostada sobre su lado, con la boca hacia el árbol (+Y en Blender = -Z en Unity... la boca mira a -Y)
    L, A, H, G2 = 1.1, 0.62, 0.55, 0.05          # largo (x), alto acostada (z), fondo (y), grueso
    cx, cy, cz = CAJA_POS
    def tabla(c, t, m=MAD): caja(bm, (cx + c[0], cy + c[1], cz + c[2]), t, mat=m, bisel=0.012, segs=1)
    # piso (lado que quedó abajo), techo, fondo (atrás, +Y) y los dos costados
    for k in range(3):
        y = -H / 2 + (k + 0.5) * H / 3
        tabla((0, y, G2 / 2), (L, H / 3 - 0.01, G2), MAD if k % 2 else MAD2)
        tabla((0, y, A - G2 / 2), (L, H / 3 - 0.01, G2), MAD2 if k % 2 else MAD)
    for k in range(3):
        z = (k + 0.5) * A / 3
        tabla((0, H / 2 - G2 / 2, z), (L, G2, A / 3 - 0.01), MAD if k % 2 else MAD2)
    for s in (-1, 1):
        tabla((s * (L / 2 - G2 / 2), 0, A / 2), (G2, H, A))
    # refuerzos oscuros en las esquinas de la boca
    for s in (-1, 1):
        tabla((s * (L / 2 - 0.03), -H / 2 + 0.03, A / 2), (0.07, 0.07, A + 0.02), OSC)
    for z in (0.03, A - 0.03):
        tabla((0, -H / 2 + 0.03, z), (L + 0.02, 0.07, 0.07), OSC)
    # letrero pintado en el "techo" (que antes era un costado): LOTE 24 y NO ABRIR
    texto_arriba(bm, "LOTE 24", (cx, cy - 0.02, cz + A + 0.004), 0.16, NEGRO)
    texto_arriba(bm, "NO ABRIR", (cx, cy + 0.17, cz + A + 0.004), 0.075, ROJO)
    # la tapa se cayó al piso enfrente, un poco girada
    tapa = bmesh.new()
    for k in range(4):
        y = (k + 0.5 - 2) * (A / 4)
        caja(tapa, (0, y, 0.025), (L - 0.02, A / 4 - 0.01, 0.05), mat=MAD2 if k % 2 else MAD, bisel=0.012, segs=1)
    caja(tapa, (0, 0, 0.055), (0.07, A - 0.05, 0.02), mat=OSC, bisel=0.005, segs=1)
    caja(tapa, (0.4, 0, 0.055), (0.07, A - 0.05, 0.02), mat=OSC, bisel=0.005, segs=1)
    caja(tapa, (-0.4, 0, 0.055), (0.07, A - 0.05, 0.02), mat=OSC, bisel=0.005, segs=1)
    rot = Matrix.Rotation(math.radians(14), 3, "Z") @ Matrix.Rotation(math.radians(4), 3, "X")
    for v in tapa.verts: v.co = rot @ v.co + Vector((cx + 0.15, cy - H / 2 - 0.55, cz))
    unir(bm, tapa)
    # paja que se salió (palitos aplanados) y tres huecos de espuma con forma de soldadito (vacíos)
    rnd = random.Random(24)
    for k in range(40):
        p = Vector((cx + rnd.uniform(-0.55, 0.55), cy - H / 2 + rnd.uniform(-0.45, 0.25), cz + 0.012))
        if p.y > cy - H / 2 + 0.05: p.z = cz + G2 + 0.01
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
        tira(bm, [p - d * 0.07, p + d * 0.07], 0.006, PAJA, segs=3)
    for k, x in enumerate((-0.32, 0.0, 0.32)):
        caja(bm, (cx + x, cy + 0.02, cz + G2 + 0.02), (0.24, 0.42, 0.04), mat=ROJO, bisel=0.01, segs=1)       # terciopelo
        caja(bm, (cx + x, cy - 0.05, cz + G2 + 0.045), (0.09, 0.09, 0.012), mat=NEGRO, bisel=0.0, segs=1)     # hueco de la cabeza
        caja(bm, (cx + x, cy + 0.08, cz + G2 + 0.045), (0.13, 0.2, 0.012), mat=NEGRO, bisel=0.0, segs=1)      # hueco del cuerpo
    # etiqueta de inventario pegada en el costado
    caja(bm, (cx + L / 2 + 0.003, cy - 0.05, cz + A / 2), (0.006, 0.22, 0.15), mat=CREMA, bisel=0.0, segs=1)


def hacer_caja_lote():
    ms = [bpy.data.materials[n] for n in ("Amb_Madera", "Amb_Madera2", "Amb_MaderaOscura", "Amb_Paja", "Amb_Negro", "Amb_Rojo", "Amb_Blanco")]
    o = bpy.data.objects.get("Caja_Lote24")
    if o is None:
        o = bpy.data.objects.new("Caja_Lote24", bpy.data.meshes.new("Caja_Lote24"))
        bpy.data.collections["Props"].objects.link(o)
    bm = bmesh.new(); caja_lote(bm)
    reemplazar_malla(o, bm, ms)
    o.location = (0, 0, 0)
    return f"caja del lote 24: {sum(len(p.vertices) - 2 for p in o.data.polygons)} tris"


# ------------------------------------------------------------------ fusible (3a refacción)
def fusible(bm):
    # cilindro de vidrio rojo con tapas de latón y una argolla para cargarlo; ~0.34 m, origen al centro, de pie (eje Z)
    cil(bm, (0, 0, -0.11), (0, 0, 0.11), 0.06, 0, segs=8)                    # vidrio
    tira(bm, [(0, 0, -0.1), (0.02, 0, -0.04), (-0.02, 0, 0.04), (0, 0, 0.1)], 0.008, 2, segs=4)   # filamento
    for s in (-1, 1):
        cil(bm, (0, 0, s * 0.1), (0, 0, s * 0.15), 0.072, 1, segs=8)           # tapa
        cil(bm, (0, 0, s * 0.15), (0, 0, s * 0.17), 0.03, 1, segs=6)           # contacto
        for k in range(4):                                                      # remachitos de la tapa
            a = 2 * math.pi * k / 4 + 0.4
            cil(bm, (0.07 * math.cos(a), 0.07 * math.sin(a), s * 0.125), (0.08 * math.cos(a), 0.08 * math.sin(a), s * 0.125), 0.008, 1, segs=4)
    # rayito pintado en el vidrio (para que se lea "eléctrico")
    rayo = [(-0.015, 0.03), (0.01, 0.0), (-0.01, -0.005), (0.015, -0.035), (-0.005, 0.0), (0.012, 0.005)]
    contorno(bm, (0, -0.061, 0), rayo, 0.004, 3, eje_u=Vector((-1, 0, 0)), eje_v=Vector((0, 0, 1)), normal=Vector((0, -1, 0)))


def hacer_fusible():
    vidrio = material("Ref_VidrioRojo", (0.9, 0.18, 0.1), rugosidad=0.15, emision=(1.0, 0.25, 0.1), fuerza=0.6)
    laton = bpy.data.materials["Ref_Laton"]; filam = material("Ref_Filamento", (1.0, 0.85, 0.4), emision=(1.0, 0.8, 0.3), fuerza=2.0)
    amarillo = bpy.data.materials["Amb_Amarillo"]
    o = bpy.data.objects.get("Refaccion_Fusible")
    if o is None:
        o = bpy.data.objects.new("Refaccion_Fusible", bpy.data.meshes.new("Refaccion_Fusible"))
        bpy.data.collections["Refacciones"].objects.link(o)
    bm = bmesh.new(); fusible(bm)
    reemplazar_malla(o, bm, [vidrio, laton, filam, amarillo])
    o.location = (4.8, -3, 0.3)
    return f"fusible: {len(o.data.polygons)} caras"


def hacer_todo():
    return [hacer_llave(), hacer_estrella_rota(), hacer_caja_lote(), hacer_fusible()]
