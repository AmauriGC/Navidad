# -*- coding: utf-8 -*-
"""
PINOS v4 (26-nov): low-poly REDONDEADO completo (estilo aprobado: rocas/arbusto/muñeco).
Mismos 4 tipos y mismo alto H / radio R (props H_original/R_original) => colliders, LODGroup, NavMesh y luces igual.
  - Faldas: falda_suave con pocas divisiones (K=4, 3 muestras por lóbulo) => lóbulos redondos con caras planas.
  - Dos verdes: caras que miran hacia abajo/adentro en verde sombra (Ext_PinoSombra) => se separan los pisos.
  - Nieve: banda delgada solo en la parte de arriba-afuera de cada falda (caras subdivididas para orilla curva),
    gorrito en la punta.
  - Tronco de 7 lados con raíz, que asoma bajo la primera falda.
  - TODO con sombreado plano.
Materiales: 0 Ext_Tronco, 1 Ext_PinoX (el de cada tipo), 2 Ext_NieveBrillo, 3 Ext_PinoSombra (nuevo).
Uso (cada uno en su propia llamada): exec(modelado.py); exec(suavizado.py); exec(montanas_nieve.py); exec(pinos_v3.py);
     exec(pinos_v4.py); hacer_pinos_v4(); hacer_pinos_lod1_v4()
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

TIPOS_V4 = {
    #              pisos lóbulos caída  nieve  traslape angosto tronco
    "PinoAbeto":  (5,    7,      0.38,  0.55,  1.6,     1.0,    0.05),
    "PinoPicea":  (7,    6,      0.42,  0.45,  1.7,     0.8,    0.04),
    "PinoNevado": (4,    7,      0.32,  0.9,   1.55,    1.1,    0.055),
    "PinoJoven":  (3,    6,      0.3,   0.5,   1.5,     1.2,    0.045),
}

def falda_lp(bm, z_apex, z_rim, R, lobulos, caida, giro, seed, K=4, muestras=4, rizo=0.08, domo=0.16):
    """Falda low-poly: como falda_suave pero con LÓBULOS MARCADOS (radio 72%..100%) que caen en la punta y perfil más
    cónico. Devuelve las caras."""
    rnd = random.Random(seed)
    N = lobulos * muestras
    alto = z_apex - z_rim
    var = [0.9 + 0.2 * rnd.random() for _ in range(lobulos)]
    apex = bm.verts.new((0, 0, z_apex))
    filas = []
    ts = [domo] + [k / K for k in range(1, K + 1)]
    for t in ts:
        fila = []
        for j in range(N):
            a = giro + 2 * math.pi * j / N
            fase = (j / muestras) % 1.0
            # perfil de NUBE (festón): |cos| => cada lóbulo es una curva redonda y el hueco entre lóbulos una muesca
            onda = abs(math.cos(math.pi * fase))
            lob = var[j // muestras]
            r = R * t * (0.76 + 0.24 * onda) * lob
            z = z_apex - alto * (t ** 0.9) * 0.92
            if t == domo: z = z_apex - alto * 0.04
            z -= caida * R * (t ** 2.0) * (0.25 + 0.75 * onda)
            fila.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        filas.append(fila)
    ult = filas[-1]
    rizo1 = [bm.verts.new((v.co.x * 0.96, v.co.y * 0.96, v.co.z - rizo * R * 0.6)) for v in ult]
    rizo2 = [bm.verts.new((v.co.x * 0.82, v.co.y * 0.82, v.co.z - rizo * R * 0.7)) for v in ult]
    centro = bm.verts.new((0, 0, z_rim + alto * 0.3))
    caras = []
    for j in range(N):
        caras.append(bm.faces.new((apex, filas[0][j], filas[0][(j + 1) % N])))
    for k in range(len(filas) - 1):
        for j in range(N):
            caras.append(bm.faces.new((filas[k][j], filas[k + 1][j], filas[k + 1][(j + 1) % N], filas[k][(j + 1) % N])))
    for a_, b_ in ((ult, rizo1), (rizo1, rizo2)):
        for j in range(N):
            caras.append(bm.faces.new((a_[j], b_[j], b_[(j + 1) % N], a_[(j + 1) % N])))
    for j in range(N):
        caras.append(bm.faces.new((rizo2[(j + 1) % N], rizo2[j], centro)))
    return caras

def tronco_lp(bm, H, a, seg=7):
    filas = []
    for z, r in ((-0.03, a * 1.9), (0.0, a * 1.6), (0.035, a * 1.15), (0.09, a), (H * 0.4, a * 0.6)):
        filas.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg + 0.3), r * math.sin(2 * math.pi * j / seg + 0.3), z)) for j in range(seg)])
    for f0, f1 in zip(filas, filas[1:]):
        for j in range(seg):
            f = bm.faces.new((f0[j], f0[(j + 1) % seg], f1[(j + 1) % seg], f1[j])); f.material_index = 0

def pino_v4(me, H, R, pisos, lobulos, caida, nieve, traslape, angosto, ancho, seed, K=3, muestras=4, seg_tronco=7, cortes=1):
    rnd = random.Random(seed)
    bm = bmesh.new()
    tronco_lp(bm, H, ancho * H / 0.9, seg=seg_tronco)
    zb = H * 0.17
    paso = (H - zb) / (pisos + traslape - 1)
    off = Vector((seed * 1.7, seed * 0.3, 0))
    for i in range(pisos):
        frac = i / max(1, pisos - 1)
        Ri = R * (1.0 - frac * 0.82) ** angosto * (0.95 + rnd.random() * 0.1)
        ultimo = i == pisos - 1
        z_rim = zb + paso * i
        z_apex = min(H, z_rim + paso * 1.35) if ultimo else z_rim + paso * traslape
        if ultimo: Ri = max(Ri * 1.25, R * 0.3)
        nl = max(5, int(round(lobulos * (1.0 - frac * 0.35))))
        antes = set(bm.faces)
        falda_lp(bm, z_apex, z_rim, Ri, nl, caida, rnd.random() * math.pi, seed * 31 + i,
                 K=K, muestras=muestras, domo=0.24 if ultimo else 0.14)
        caras = [f for f in bm.faces if f not in antes]
        bmesh.ops.recalc_face_normals(bm, faces=caras)
        bm.normal_update()
        # orientación: las caras deben mirar HACIA AFUERA y arriba (pesado por área). Con solo n.z la punta (muy
        # empinada) a veces quedaba volteada => salía en verde sombra y su gorrito de nieve se escondía.
        def afuera(f):
            c = f.calc_center_median(); rad = Vector((c.x, c.y, 0))
            rad = rad.normalized() if rad.length > 1e-6 else Vector((0, 0, 0))
            return f.normal.dot(rad + Vector((0, 0, 0.5))) * f.calc_area()
        if sum(afuera(f) for f in caras) < 0: bmesh.ops.reverse_faces(bm, faces=caras)
        bm.normal_update()
        # sombra: lo que mira hacia abajo (orilla enrollada, parte de abajo de los lóbulos)
        for f in caras: f.material_index = 3 if f.normal.z < -0.05 else 1
        # caras de arriba subdivididas => la orilla de la nieve sale curva (no en dientes)
        if cortes:
            arriba = [f for f in caras if f.normal.z > 0.3]
            bmesh.ops.subdivide_edges(bm, edges=list({e for f in arriba for e in f.edges}), cuts=cortes, use_grid_fill=True)
            caras = [f for f in bm.faces if f not in antes]
            bm.normal_update()
        inicio = 0.99 - 0.18 * nieve        # banda delgada: la nieve solo en la orilla de arriba
        alto = z_apex - z_rim
        def campo(p, n, z_apex=z_apex, alto=alto, ultimo=ultimo, inicio=inicio):
            u = (z_apex - p.z) / alto
            ini = inicio + 0.04 * noise.noise(Vector((p.x, p.y, 0)).normalized() * 1.5 + off)
            arriba = suave01((n.z - 0.3) / 0.25)
            if ultimo:
                banda = suave01((u - 0.02) / 0.05) if u < 0.4 else suave01((u - ini) / 0.1)
                arriba = 1.0 if u < 0.4 else arriba
            else:
                banda = suave01((u - ini) / 0.1)
            return banda * arriba * (0.85 + 0.15 * noise.noise(p * (8.0 / H) + off))
        nieve_campo(bm, [f for f in caras if f.material_index == 1 or ultimo], campo, grosor=0.02 * H, mat=2, hundir=0.006 * H)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    for f in bm.faces: f.smooth = False
    me.clear_geometry(); bm.to_mesh(me); bm.free()
    me.update()

def _material_sombra(me):
    s = bpy.data.materials.get("Ext_PinoSombra") or material("Ext_PinoSombra", (0.02, 0.12, 0.07), rugosidad=0.9)
    s.diffuse_color = (0.02, 0.12, 0.07, 1)      # color en la vista SÓLIDA de Blender (si no, se ve gris)
    while len(me.materials) < 4: me.materials.append(s)
    me.materials[3] = s

def hacer_pinos_v4():
    for k, (mn, (pisos, lob, caida, nieve, tras, ang, anc)) in enumerate(TIPOS_V4.items()):
        me = bpy.data.meshes[mn]
        _material_sombra(me)
        pino_v4(me, me["H_original"], me["R_original"], pisos, lob, caida, nieve, tras, ang, anc, seed=k + 3)
        print(mn, "tris", sum(len(p.vertices) - 2 for p in me.polygons))

def hacer_pinos_lod1_v4(proporcion=0.35):
    """LOD1 (de lejos) = la malla de cerca SIMPLIFICADA con Decimate (Collapse): conserva nieve, sombra y colores
    (con menos divisiones la nieve desaparecía y el pino 'cambiaba de color' al alejarse)."""
    sc = bpy.context.window_manager.windows[0].scene
    dg = bpy.context.evaluated_depsgraph_get()
    for mn in TIPOS_V4:
        base = bpy.data.meshes[mn]
        tmp = bpy.data.objects.new("TMP_dec", base); sc.collection.objects.link(tmp)
        mod = tmp.modifiers.new("dec", "DECIMATE"); mod.ratio = proporcion; mod.use_collapse_triangulate = True
        dg.update()
        ev = tmp.evaluated_get(dg)
        bm = bmesh.new(); bm.from_mesh(ev.to_mesh()); ev.to_mesh_clear()
        for f in bm.faces: f.smooth = False
        me = bpy.data.meshes[mn + "_LOD1"]
        me.materials.clear()
        for m in base.materials: me.materials.append(m)
        me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
        bpy.data.objects.remove(tmp)
        print(mn + "_LOD1", "tris", sum(len(p.vertices) - 2 for p in me.polygons))
