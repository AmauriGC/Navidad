# -*- coding: utf-8 -*-
"""
ROCAS v3 (26-nov): peñas de caras planas (estilo low-poly bonito) en vez de bolas lisas.
1. Se tiran puntos al azar sobre un elipsoide y se saca su CASCO CONVEXO (convex_hull) => roca con caras.
2. dissolve_limit junta triángulos casi del mismo plano => caras grandes (facetas).
3. bevel en las aristas => orillas redonditas (atrapan la luz, sin picos).
4. Se subdivide para tener vértices donde poner la nieve y nieve_campo pone una capa SOLO en las caras que miran
   hacia arriba, con orilla curva suave y escurridos.
5. Piedritas al pie (cascos chiquitos). Todo se escala a la caja original (datos_rocas.json) => el MeshCollider
   convexo de Unity queda del mismo tamaño.
Materiales: 0 Ext_Roca, 1 Ext_NieveBrillo (los mismos de antes).
Uso: exec(modelado.py); exec(rocas_arbustos.py); exec(rocas_v3.py); hacer_rocas()
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

ESTILOS = {
    # nombre: (semilla, radios del bloque, puntos, piedritas, nieve: altura relativa donde empieza)
    "Roca0": (40, (1.0, 0.85, 0.95), 22, 4, 0.7),   # alta y robusta
    "Roca1": (41, (1.15, 0.9, 0.5), 20, 3, 0.62),    # laja plana
    "Roca2": (42, (0.9, 0.85, 0.75), 30, 2, 0.68),    # chiquita y más redonda (más puntos = más caras)
}

def casco(bm, centro, radios, n, rnd, mat, angulo=10.0, bisel=0.06, cortes=2, oscuras=0.0):
    """Roca de caras planas: casco convexo + facetas + bisel. Devuelve sus caras."""
    antes = set(bm.faces)
    vs = []
    for i in range(n):
        # puntos bien repartidos (espiral de Fibonacci) con ruido => facetas de tamaños parecidos
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(1 - z * z); a = i * 2.39996 + rnd.uniform(-0.4, 0.4)
        p = Vector((math.cos(a) * r, math.sin(a) * r, z)) * rnd.uniform(0.82, 1.0)
        vs.append(bm.verts.new(Vector(centro) + Vector((p.x * radios[0], p.y * radios[1], p.z * radios[2]))))
    res = bmesh.ops.convex_hull(bm, input=vs)
    sueltos = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if sueltos: bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    caras = [f for f in bm.faces if f not in antes]
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(angulo), verts=list({v for f in caras for v in f.verts}),
                             edges=list({e for f in caras for e in f.edges}))
    caras = [f for f in bm.faces if f not in antes]
    aristas = list({e for f in caras for e in f.edges})
    bmesh.ops.bevel(bm, geom=aristas + list({v for e in aristas for v in e.verts}), offset=bisel, offset_type="OFFSET",
                    segments=2, profile=0.6, affect="EDGES", clamp_overlap=True)
    caras = [f for f in bm.faces if f not in antes]
    # facetas grandes: ~1 de cada 3 con el tono oscuro (material 2) => se notan las caras de la peña
    if oscuras:
        grandes = sorted(caras, key=lambda f: -f.calc_area())[:max(3, len(caras) // 4)]
        for f in grandes:
            if rnd.random() < oscuras: f.material_index = 2
    for f in caras:
        if f.material_index != 2: f.material_index = mat
    bmesh.ops.triangulate(bm, faces=caras)
    caras = [f for f in bm.faces if f not in antes]
    if cortes:
        # solo se subdivide lo que mira hacia arriba (ahí va la nieve); los lados se quedan con sus caras planas
        arriba = [f for f in caras if f.normal.z > 0.15]
        bmesh.ops.subdivide_edges(bm, edges=list({e for f in arriba for e in f.edges}), cuts=cortes, use_grid_fill=True)
    caras = [f for f in bm.faces if f not in antes]
    for f in caras: f.smooth = False
    return caras

def roca_v3(nombre, caja):
    semilla, radios, n, n_pied, ini = ESTILOS[nombre]
    def construir(bm, me):
        rnd = random.Random(semilla)
        principal = casco(bm, (0, 0, 0), radios, n, rnd, 0, angulo=11, bisel=0.07, cortes=2, oscuras=0.0)
        # base: lo de abajo se aplana (la roca se asienta, queda medio enterrada)
        zmn = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            if v.co.z < zmn + 0.2 * radios[2]: v.co.z = zmn + 0.2 * radios[2] - (zmn + 0.2 * radios[2] - v.co.z) * 0.25
        ajustar_a_caja(bm, caja)
        # piedritas al pie, a NIVEL DEL SUELO (z = 0 local: lo de abajo de la caja va enterrado en el mapa)
        cx = (caja[1][0] - caja[0][0]) / 2; cy = (caja[1][1] - caja[0][1]) / 2
        mx_ = (caja[1][0] + caja[0][0]) / 2; my_ = (caja[1][1] + caja[0][1]) / 2
        piedritas = []
        a = rnd.uniform(0, 6.28)
        for k in range(n_pied):
            a += rnd.uniform(1.3, 2.3)
            r = rnd.uniform(0.07, 0.11)
            c = Vector((mx_ + math.cos(a) * cx * 0.97, my_ + math.sin(a) * cy * 0.97, r * 0.15))
            piedritas += casco(bm, c, (r, r * rnd.uniform(0.8, 1.1), r * 0.65), 12, rnd, 0, angulo=14, bisel=0.012, cortes=0,
                               oscuras=0.0)
        bm.normal_update()
        zmn = caja[0][2]; zmx = caja[1][2]; H = zmx - zmn
        escurre = [(rnd.uniform(0, 6.28), rnd.uniform(0.08, 0.16)) for _ in range(5)]
        def campo(p, nrm):
            ang = math.atan2(p.y, p.x)
            baja = sum(g * math.exp(-((math.atan2(math.sin(ang - a), math.cos(ang - a))) / 0.25) ** 2) for a, g in escurre)
            corte = zmn + H * (ini + 0.08 * noise.noise(p * 2.0 + Vector((semilla, 0, 0)))) - H * baja
            # solo donde la cara mira hacia arriba (la nieve no se pega en lo vertical)
            return suave01((p.z - corte) / (H * 0.08)) * suave01((nrm.z - 0.45) / 0.3)
        cand = [f for f in principal if f.is_valid and f.normal.z > 0.1]
        nieve_campo(bm, cand, campo, H * 0.06, 1, hundir=0.01)
        # piedritas: una pizca de nieve arriba
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index == 0])
    poner(nombre, construir)

def materiales_roca():
    """Ext_Roca un poco más oscuro y Ext_RocaOscura nueva (slot 2) en las 3 mallas."""
    base = bpy.data.materials["Ext_Roca"]
    b = next(n for n in base.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.24, 0.26, 0.32, 1)
    osc = bpy.data.materials.get("Ext_RocaOscura") or material("Ext_RocaOscura", (0.13, 0.14, 0.18), rugosidad=0.95)
    for n in ("Roca0", "Roca1", "Roca2"):
        me = bpy.data.meshes[n]
        while len(me.materials) < 3: me.materials.append(None)
        me.materials[2] = osc

def hacer_rocas():
    materiales_roca()
    d = cajas_originales()
    for n in ("Roca0", "Roca1", "Roca2"):
        roca_v3(n, d[n])
