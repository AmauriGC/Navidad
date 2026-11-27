# -*- coding: utf-8 -*-
"""
ACOMODAR PINOS: separa los pinos encimados y deja claros alrededor de casas, senderos y patio.
Cómo funciona ("relajación"): cada pino es un círculo (radio de su follaje). En cada vuelta:
  - si dos pinos se enciman, cada uno se empuja la mitad de lo que se enciman, en sentido contrario;
  - si un pino cae sobre una casa, el patio, un sendero, una roca o un arbusto, se empuja hacia afuera.
Se repite muchas veces hasta que ya casi nadie se encima. Los pinos que de plano no caben se reportan.
Después cada pino se baja/sube para quedar sobre el terreno (rayo hacia abajo contra SueloNieve).
La posición ORIGINAL se guarda en el pino (propiedad "pos_original"), así se puede regresar con restaurar().
Uso: exec(acomodar_pinos.py); acomodar()   |   restaurar()
"""
import bpy, math, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CENTRO = Vector((-5.0, 0.0))      # centro del área de juego (en Blender; Unity (5, 0))
R_JUEGO = 74.0                     # dentro de este radio se juega; afuera los pinos son "fondo"
R_MAX_DENTRO = 5.2                 # radio máximo de follaje para pinos dentro del área de juego
SEPARACION = 1.0                   # 1.0 = los follajes apenas se tocan

def pinos():
    return [o for o in bpy.data.objects if o.name.startswith("Pino_")]

def radio_malla(me, cache={}):
    if me.name not in cache: cache[me.name] = max(math.hypot(v.co.x, v.co.y) for v in me.vertices)
    return cache[me.name]

def guardar_originales():
    for o in pinos():
        if "pos_original" not in o:
            o["pos_original"] = list(o.location); o["escala_original"] = list(o.scale)

def restaurar():
    for o in pinos():
        if "pos_original" in o:
            o.location = o["pos_original"]; o.scale = o["escala_original"]
    print("pinos restaurados")

def obstaculos():
    obs = []   # (centro2D, radio)
    for c in bpy.data.objects:
        if c.name.startswith("Casa_"):
            obs.append((c.location.xy.copy(), max(c.dimensions.x, c.dimensions.y) / 2 + 3.0))
        elif c.name.startswith(("Roca_", "Arbusto_", "Patio_")):
            obs.append((c.location.xy.copy(), max(c.dimensions.x, c.dimensions.y) / 2 + 1.0))
    s = bpy.data.objects.get("Senderos")
    if s:
        vis = set()
        for v in s.data.vertices:
            p = (s.matrix_world @ v.co).xy
            k = (round(p.x / 2), round(p.y / 2))       # un punto cada ~2 m basta
            if k in vis: continue
            vis.add(k); obs.append((p.copy(), 2.2))
    return obs

def dentro_patio(p, margen):
    # patio + taller + establo: Unity X -16..26, Z -13..13  => Blender x 16..-26, y 13..-13
    return -26 - margen < p.x < 16 + margen and -13 - margen < p.y < 13 + margen

def acomodar(vueltas=400, semilla=1):
    guardar_originales()
    rnd = random.Random(semilla)
    P = pinos()
    for o in P:                                     # empezar SIEMPRE desde la posición original
        o.location = o["pos_original"]; o.scale = o["escala_original"]
    pos = [o.location.xy.copy() for o in P]
    rad = []
    for o in P:
        r = radio_malla(o.data) * o.scale.x
        dentro = (o.location.xy - CENTRO).length < R_JUEGO
        if dentro and r > R_MAX_DENTRO:              # los gigantes dentro del área se achican
            f = R_MAX_DENTRO / r
            o.scale = o.scale * f; r = R_MAX_DENTRO
        rad.append(r)
    obs = obstaculos()
    n = len(P)
    for it in range(vueltas):
        mov = 0.0
        # pinos contra pinos
        for i in range(n):
            for j in range(i + 1, n):
                d = pos[j] - pos[i]; L = d.length
                minimo = (rad[i] + rad[j]) * SEPARACION
                if L < minimo:
                    if L < 1e-3: d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1))); L = d.length
                    emp = d / L * (minimo - L) * 0.5
                    pos[i] -= emp; pos[j] += emp; mov += (minimo - L)
        # pinos contra obstáculos
        for i in range(n):
            for (c, r) in obs:
                d = pos[i] - c; L = d.length
                minimo = r + rad[i] * 0.55
                if L < minimo:
                    if L < 1e-3: d = Vector((1, 0)); L = 1
                    pos[i] += d / L * (minimo - L); mov += minimo - L
            if dentro_patio(pos[i], rad[i] * 0.6 + 2):
                # sacar del patio por el lado más cercano
                p = pos[i]; m = rad[i] * 0.6 + 2
                opciones = [(p.x - (16 + m), Vector((16 + m, p.y))), ((-26 - m) - p.x, Vector((-26 - m, p.y))),
                            (p.y - (13 + m), Vector((p.x, 13 + m))), ((-13 - m) - p.y, Vector((p.x, -13 - m)))]
                pos[i] = max(opciones, key=lambda t: t[0])[1].copy()
        if mov < 0.05: break
    # quién sigue encimado
    encimados = set()
    for i in range(n):
        for j in range(i + 1, n):
            if (pos[j] - pos[i]).length < (rad[i] + rad[j]) * 0.8: encimados.update((P[i].name, P[j].name))
    # aplicar posiciones y pegar al terreno
    suelo = bpy.data.objects["SueloNieve"]
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(suelo, dg)
    inv = suelo.matrix_world.inverted()
    def altura(p2):
        orig = inv @ Vector((p2.x, p2.y, 500)); dirc = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
        hit = bvh.ray_cast(orig, dirc)
        return (suelo.matrix_world @ hit[0]).z if hit[0] else None
    movidos = 0
    for o, p in zip(P, pos):
        po = Vector(o["pos_original"])
        h0 = altura(po.xy); h1 = altura(p)
        hundido = (po.z - h0) if h0 is not None else 0.0
        z = (h1 + hundido) if h1 is not None else po.z
        if (p - po.xy).length > 0.05: movidos += 1
        o.location = (p.x, p.y, z)
    print(f"vueltas: {it + 1} | pinos movidos: {movidos} de {n} | siguen encimados: {len(encimados)}", sorted(encimados)[:10])
    return encimados
