# -*- coding: utf-8 -*-
"""
PINOS v3 (los 4 tipos del pueblo: PinoAbeto, PinoPicea, PinoNevado, PinoJoven; 150 instancias).
Mismo tamaño que antes (alto H y radio R de cada malla) => los colliders, LODGroup y posiciones de Unity siguen igual.
Qué cambia:
  - Follaje: faldas suaves (falda_suave, como el Gran Árbol) con lóbulos redondos que caen, borde enrollado.
    Cada tipo tiene su carácter: Abeto clásico, Picea delgada y alta con muchos pisos, Nevado gordito y muy nevado,
    Joven chiquito y redondo.
  - Nieve EN CAPAS: ya no es "cara verde o cara blanca" (salía en cuadritos). Encima de cada falda va una capa
    (nieve_campo) que solo se queda donde la superficie mira hacia arriba y en manchas de ruido, más en la parte de
    afuera del lóbulo (donde cae la nieve de verdad). Donde el campo es 0 queda hundida => orilla limpia y redonda.
  - Tronco de 12 lados con raíz ensanchada.
Materiales (los mismos): 0 Ext_Tronco, 1 Ext_PinoX, 2 Ext_NieveBrillo.
Uso: exec(modelado.py); exec(suavizado.py); exec(montanas_nieve.py); exec(pinos_v3.py); hacer_pinos()
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

TIPOS = {
    #              pisos lóbulos caída  nieve  traslape angosto ancho_tronco
    "PinoAbeto":  (6,    9,      0.30,  0.55,  1.6,     1.0,    0.045),
    "PinoPicea":  (8,    8,      0.38,  0.45,  1.7,     0.8,    0.035),
    "PinoNevado": (5,    9,      0.26,  0.95,  1.55,    1.1,    0.05),
    "PinoJoven":  (4,    7,      0.24,  0.5,   1.5,     1.2,    0.04),
}

def tronco(bm, H, a, seg=12):
    filas = []
    for z, r in ((-0.03, a * 2.0), (0.0, a * 1.7), (0.03, a * 1.2), (0.08, a), (H * 0.4, a * 0.6)):
        filas.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
    for f0, f1 in zip(filas, filas[1:]):
        for j in range(seg):
            f = bm.faces.new((f0[j], f0[(j + 1) % seg], f1[(j + 1) % seg], f1[j])); f.material_index = 0; f.smooth = True

def pino_v3(me, H, R, pisos, lobulos, caida, nieve, traslape, angosto, ancho, seed, K=5, muestras=4, seg_tronco=12):
    rnd = random.Random(seed)
    bm = bmesh.new()
    tronco(bm, H, ancho * H / 0.9, seg=seg_tronco)
    zb = H * 0.12
    paso = (H - zb) / (pisos + traslape - 1)
    off = Vector((seed * 1.7, seed * 0.3, 0))
    for i in range(pisos):
        frac = i / max(1, pisos - 1)
        Ri = R * (1.0 - frac * 0.82) ** angosto * (0.95 + rnd.random() * 0.1)
        ultimo = i == pisos - 1
        z_rim = zb + paso * i
        z_apex = min(H, z_rim + paso * 1.35) if ultimo else z_rim + paso * traslape   # punta corta y redonda
        if ultimo: Ri = max(Ri * 1.25, R * 0.3)
        nl = max(5, int(round(lobulos * (1.0 - frac * 0.4))))
        caras = falda_suave(bm, z_apex, z_rim, Ri, nl, caida, rnd.random() * math.pi, seed * 31 + i,
                            lambda k, j, l, t: 1, K=K, muestras=muestras, rizo=0.07, domo=0.24 if ultimo else 0.14)
        bmesh.ops.recalc_face_normals(bm, faces=caras)
        bm.normal_update()
        if sum(f.normal.z for f in caras) < 0: bmesh.ops.reverse_faces(bm, faces=caras)
        bm.normal_update()
        # campo de nieve de esta falda: una BANDA sobre la parte de afuera de los lóbulos (u = 0 punta .. 1 borde,
        # medido con la altura => la orilla de la nieve sigue la forma de los lóbulos) con grosor que varía con ruido
        # pero nunca llega a 0 dentro de la banda => no salen manchas en cuadritos.
        inicio = 0.97 - 0.3 * nieve                                   # más nieve => la banda empieza más arriba
        alto = z_apex - z_rim
        def campo(p, n, z_apex=z_apex, alto=alto, ultimo=ultimo, inicio=inicio):
            u = (z_apex - p.z) / alto
            inicio = inicio + 0.1 * noise.noise(Vector((p.x, p.y, 0)).normalized() * 2.5 + off)   # unos lóbulos con más nieve
            arriba = suave01((n.z - 0.25) / 0.25)
            if ultimo:                                                # gorrito: toda la punta, sin importar lo empinado
                banda = suave01((u - 0.02) / 0.05) if u < 0.5 else suave01((u - inicio) / 0.12)
                arriba = 1.0 if u < 0.5 else arriba
            else:
                banda = suave01((u - inicio) / 0.12)
            grueso = 0.7 + 0.3 * noise.noise(p * (14.0 / H) + off)
            return banda * arriba * grueso
        nieve_campo(bm, caras, campo, grosor=0.022 * H, mat=2, hundir=0.006 * H)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me.clear_geometry(); bm.to_mesh(me); bm.free()
    for e in me.edges: e.use_edge_sharp = False
    me.update()

def hacer_pinos():
    for k, (mn, (pisos, lob, caida, nieve, tras, ang, anc)) in enumerate(TIPOS.items()):
        me = bpy.data.meshes[mn]
        H = me.get("H_original") or max(v.co.z for v in me.vertices)
        R = me.get("R_original") or max(v.co.xy.length for v in me.vertices)
        me["H_original"] = H; me["R_original"] = R
        pino_v3(me, H, R, pisos, lob, caida, nieve, tras, ang, anc, seed=k + 3)
        print(mn, "tris", sum(len(p.vertices) - 2 for p in me.polygons), "H", round(H, 2), "R", round(R, 2))


def hacer_pinos_lod1():
    """Versión de LEJOS (LOD1) de cada tipo: misma silueta y misma semilla, pero menos divisiones.
    Se guarda en mallas <Tipo>_LOD1 dentro de objetos de la colección PinosLOD (en el origen) para exportarlas."""
    col = bpy.data.collections.get("PinosLOD")
    if col is None:
        col = bpy.data.collections.new("PinosLOD"); bpy.context.scene.collection.children.link(col)
    for k, (mn, (pisos, lob, caida, nieve, tras, ang, anc)) in enumerate(TIPOS.items()):
        base = bpy.data.meshes[mn]
        nombre = mn + "_LOD1"
        me = bpy.data.meshes.get(nombre) or bpy.data.meshes.new(nombre)
        if not me.materials:
            for m in base.materials: me.materials.append(m)
        o = bpy.data.objects.get(nombre) or bpy.data.objects.new(nombre, me)
        if o.name not in col.objects: col.objects.link(o)
        pino_v3(me, base["H_original"], base["R_original"], pisos, max(5, lob - 2), caida, min(1.0, nieve + 0.35), tras, ang, anc, seed=k + 3, K=3, muestras=3, seg_tronco=6)
        print(nombre, "tris", sum(len(p.vertices) - 2 for p in me.polygons))
