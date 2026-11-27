# -*- coding: utf-8 -*-
"""
1) ELFO SECRETO "JENGIBRE" (premio por juntar las 10 galletas): accesorios Acc_Jengibre_* sobre el mismo elfo.
   - Glaseado: zigzag blanco alrededor de la túnica y del gorro (puntos sacados con RAYOS contra la malla real,
     así el glaseado queda pegado a la tela sin flotar ni hundirse).
   - Botones: 3 gomitas (rojo/verde/rojo) al frente de la túnica.
   Reusa los materiales de la galleta coleccionable (Galleta_Glaseado, Galleta_DulceRojo/Verde).
2) REFACCIONES de la Máquina 7 (misión opcional): Engrane (latón), Resorte (cobre), Llave inglesa (acero + mango rojo).
   Cada una es UNA malla con el origen al centro -> Assets/Modelos/Refaccion_*.glb
Uso: exec(modelado.py); exec(elfo_v2.py SIN el ciclo final); exec(elfos_variantes.py); exec(este);
     hacer_jengibre(); hacer_refacciones()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

# ------------------------------------------------------------------ utilidades de rayos (coords del elfo)
def _hit(obj, origen_elfo, dir_elfo):
    dg = bpy.context.evaluated_depsgraph_get()
    W = RAIZ.matrix_world; inv = obj.matrix_world.inverted()
    o = inv @ (W @ origen_elfo); d = (inv.to_3x3() @ (W.to_3x3() @ dir_elfo)).normalized()
    ok, loc, nor, idx = obj.ray_cast(o, d, depsgraph=dg)
    if not ok: return None, None
    p = W.inverted() @ (obj.matrix_world @ loc)
    n = (W.inverted().to_3x3() @ (obj.matrix_world.to_3x3() @ nor)).normalized()
    return p, n

def _centro_rebanada(obj, z):
    dg = bpy.context.evaluated_depsgraph_get(); oe = obj.evaluated_get(dg)
    W = RAIZ.matrix_world.inverted() @ obj.matrix_world
    vs = [W @ v.co for v in oe.data.vertices]
    cerca = [v for v in vs if abs(v.z - z) < 0.03] or vs
    return Vector((sum(v.x for v in cerca) / len(cerca), sum(v.y for v in cerca) / len(cerca), z))

def zigzag(bm, obj, z, amp=0.016, picos=14, afuera=0.006, grosor=0.0085, mat=0, n=112):
    """Tubo de glaseado en zigzag alrededor de 'obj' a la altura z (coords del elfo)."""
    c = _centro_rebanada(obj, z)
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        zz = z + amp * (2 * abs(((k * picos / n) % 1.0) - 0.5) * 2 - 1)   # onda triangular
        d = Vector((math.sin(a), -math.cos(a), 0))
        p, nor = _hit(obj, Vector((c.x, c.y, zz)) + d * 0.6, -d)
        if p is None: continue
        pts.append(p + nor * afuera)
    loft(bm, pts, [(grosor, grosor)] * len(pts), mat=mat, segs=8, sub=1, tapas=(False, False), domo=0.0)

def gomita(bm, p, nor, r=0.024, mat=0):
    """Gomita de dulce: domo achatado orientado con la normal de la tela."""
    tmp = bmesh.new()
    res = bmesh.ops.create_uvsphere(tmp, u_segments=16, v_segments=10, radius=1.0)
    rot = nor.to_track_quat("Z", "Y").to_matrix()
    for v in tmp.verts:
        q = Vector((v.co.x * r, v.co.y * r, max(v.co.z, -0.2) * r * 0.75))
        v.co = rot @ q + p + nor * (r * 0.1)
    for f in tmp.faces: f.material_index = mat; f.smooth = True
    unir(bm, tmp)

def hacer_jengibre():
    cuerpo = bpy.data.objects["Cuerpo"]; gorro = bpy.data.objects["Gorro"]; falda = bpy.data.objects["Falda"]
    glas = bpy.data.materials["Galleta_Glaseado"]; rojo = bpy.data.materials["Galleta_DulceRojo"]; verde = bpy.data.materials["Galleta_DulceVerde"]
    def glaseado_tunica(bm):
        zigzag(bm, falda, 0.385, amp=0.014, picos=16)
    def glaseado_gorro(bm):
        zigzag(bm, gorro, 1.165, amp=0.014, picos=14, grosor=0.0075)
    def botones(bm):
        for k, z in enumerate((0.735, 0.655, 0.575)):
            p, nor = _hit(cuerpo, Vector((0, -0.6, z)), Vector((0, 1, 0)))
            if p is not None: gomita(bm, p, nor, r=0.031, mat=k % 2)
    acc("Acc_Jengibre_Glaseado", "Cuerpo", glaseado_tunica, [glas])
    acc("Acc_Jengibre_GlaseadoGorro", "Gorro", glaseado_gorro, [glas])
    acc("Acc_Jengibre_Botones", "Cuerpo", botones, [rojo, verde])
    for o in bpy.data.objects:
        if o.name.startswith("Acc_Jengibre"): o.modifiers.clear(); print(o.name, len(o.data.polygons), "caras")

# ------------------------------------------------------------------ REFACCIONES
def _objeto(nombre):
    col = bpy.data.collections.get("Refacciones")
    if col is None:
        col = bpy.data.collections.new("Refacciones"); bpy.context.scene.collection.children.link(col)
    o = bpy.data.objects.get(nombre)
    if o is None:
        o = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre + "_tmp")); col.objects.link(o)
    else:
        o.data.name = nombre + "_viejo"
    return o

def engrane(bm, R=0.16, r_in=0.055, h=0.055, dientes=12, mat=0):
    N = dientes * 4
    def ext(k):
        f = k % 4
        return R if f in (1, 2) else R * 0.8
    anillos = []
    for z in (-h / 2, h / 2):
        fuera = []; dentro = []
        for k in range(N):
            a = 2 * math.pi * (k + (0.15 if k % 4 in (1, 3) else 0) * (1 if k % 4 == 1 else -1)) / N
            fuera.append(bm.verts.new((math.cos(a) * ext(k), z, math.sin(a) * ext(k))))
            b = 2 * math.pi * k / N
            dentro.append(bm.verts.new((math.cos(b) * r_in, z, math.sin(b) * r_in)))
        anillos.append((fuera, dentro))
    (f0, d0), (f1, d1) = anillos
    for k in range(N):
        j = (k + 1) % N
        for cara in ((f0[k], f0[j], f1[j], f1[k]), (d0[j], d0[k], d1[k], d1[j]),
                     (f1[k], f1[j], d1[j], d1[k]), (d0[k], d0[j], f0[j], f0[k])):
            bm.faces.new(cara).material_index = mat
    # cubo central con rayos
    toro(bm, (0, 0, 0), r_in, 0.016, mat=mat, segs=24, lados=8, inclinacion=math.pi / 2)

def resorte(bm, mat=0, tapa=1):
    vueltas, r, alto = 6, 0.07, 0.3
    pts = []
    for k in range(vueltas * 24 + 1):
        t = k / 24.0; a = 2 * math.pi * t
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, -alto / 2 + alto * t / vueltas)))
    loft(bm, pts, [(0.014, 0.014)] * len(pts), mat=mat, segs=10, sub=1, domo=0.6)
    for z in (-alto / 2 - 0.012, alto / 2 + 0.012):
        loft(bm, [Vector((0, 0, z - 0.012)), Vector((0, 0, z + 0.012))], [(0.085, 0.085), (0.085, 0.085)], mat=tapa, segs=24, sub=1, domo=0.15)

def llave(bm, acero=0, rojo=1):
    caja(bm, (0, 0, 0.0), (0.05, 0.022, 0.26), mat=acero, bisel=0.008, segs=2)                       # mango
    caja(bm, (0, 0, -0.07), (0.064, 0.034, 0.13), mat=rojo, bisel=0.014, segs=3)                      # empuñadura roja
    toro(bm, (0, 0, -0.165), 0.032, 0.014, mat=acero, segs=20, lados=8, inclinacion=math.pi / 2)    # argolla
    # cabeza abierta (C): base + dos mandíbulas
    caja(bm, (0, 0, 0.15), (0.12, 0.03, 0.05), mat=acero, bisel=0.01, segs=2)
    for s in (-1, 1):
        caja(bm, (s * 0.045, 0, 0.2), (0.035, 0.03, 0.08), mat=acero, bisel=0.01, segs=2, giro=Matrix.Rotation(-s * 0.18, 3, "Y"))

def hacer_refacciones():
    laton = material("Ref_Laton", (0.95, 0.66, 0.22), metal=0.85, rugosidad=0.3, emision=(1, 0.7, 0.3), fuerza=0.15)
    cobre = material("Ref_Cobre", (0.85, 0.4, 0.18), metal=0.85, rugosidad=0.35, emision=(1, 0.5, 0.25), fuerza=0.12)
    acero = material("Ref_Acero", (0.8, 0.83, 0.88), metal=0.55, rugosidad=0.35, emision=(0.7, 0.8, 1), fuerza=0.1)
    rojo = material("Ref_Rojo", (0.8, 0.08, 0.08), rugosidad=0.45)
    piezas = (("Refaccion_Engrane", lambda bm: engrane(bm), [laton]),
              ("Refaccion_Resorte", lambda bm: resorte(bm), [cobre, laton]),
              ("Refaccion_Llave", lambda bm: llave(bm), [acero, rojo]))
    for x, (n, f, ms) in enumerate(piezas):
        o = _objeto(n); o.location = (3 + x * 0.6, -3, 0.3)
        poner_malla(o, f, materiales=ms, subsurf=0)
        if n != "Refaccion_Engrane":
            for p in o.data.polygons: p.use_smooth = True
        o.data.name = n
        exportar_glb([o], n + ".glb", raiz=o)
        print(n, len(o.data.polygons), "caras")
