# -*- coding: utf-8 -*-
"""
CASAS v2 — nieve "acolchonada" en techos, chimeneas y tejabanes (mismo estilo y materiales de la tarde).
Qué hace con cada malla de casa (CasaRoja, CasaAzul, CasaVerde, CasaTroncos, CasaA):
  1) Busca las LOSAS DE NIEVE viejas: islas de la malla (piezas sueltas) hechas de una caja biselada (54 caras)
     con material Ext_NieveBrillo. De cada una saca su "caja orientada" (centro, ejes y medidas) usando la cara
     más grande (la de arriba) para saber hacia dónde mira.
  2) Borra la losa y en su lugar construye una ALMOHADA de nieve: una rejilla de arriba (abombada, con grumitos)
     y una de abajo, unidas en la orilla. El grosor se redondea en la orilla (perfil (1-|x|^8)^0.5).
  3) En las orillas que van hacia ABAJO (aleros) la nieve sobresale, se ENROLLA hacia abajo y ESCURRE en gotitas
     (lengüitas redondas a lo largo del alero). En la cumbrera (arriba) la nieve sigue derecho para que las dos
     aguas del techo se junten sin hueco. En los copetes de chimenea (losa plana) escurre por los 4 lados.
  4) Los montones de nieve al pie de la casa (islas de 180 caras) pasan a sombreado SUAVE.
Para poder repetirlo, cada corrida RESTAURA primero las mallas originales desde Library/BlenderBackup/antes_casas_v2.blend.
Uso: exec(modelado.py); exec(casas_v2.py); hacer_casas()
"""
import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector
from collections import Counter

RESPALDO = PROYECTO + "/Library/BlenderBackup/antes_casas_v2.blend"
MALLAS = ["CasaRoja", "CasaAzul", "CasaVerde", "CasaTroncos", "CasaA"]

def restaurar(nombres):
    """Cambia las mallas por las originales del respaldo (en todos los objetos que las usan)."""
    with bpy.data.libraries.load(RESPALDO, link=False) as (src, dst):
        dst.meshes = [f"{n}" for n in nombres]
    for nueva, nombre in zip(dst.meshes, nombres):
        vieja = bpy.data.meshes[nombre]
        for o in bpy.data.objects:
            if o.data == vieja: o.data = nueva
        # los materiales del respaldo vienen como copias ".001": usar los de este archivo
        for i, m in enumerate(nueva.materials):
            if m and m.name[-4:-3] == "." and bpy.data.materials.get(m.name[:-4]):
                nueva.materials[i] = bpy.data.materials[m.name[:-4]]
        bpy.data.meshes.remove(vieja)
        nueva.name = nombre
    for m in [m for m in bpy.data.materials if m.users == 0 and m.name[-4:-3] == "."]:
        bpy.data.materials.remove(m)

def islas(bm):
    vistos = set(); res = []
    for f in bm.faces:
        if f.index in vistos: continue
        pila = [f]; grupo = []; vistos.add(f.index)
        while pila:
            g = pila.pop(); grupo.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in vistos: vistos.add(h.index); pila.append(h)
        res.append(grupo)
    return res

def caja_orientada(grupo):
    """Centro, ejes (e1 largo, e2, e3 = arriba) y medio-tamaños de una caja biselada."""
    arriba = max(grupo, key=lambda f: f.calc_area() * (1 if f.normal.z > 0 else 0.001))
    e3 = arriba.normal.copy()
    borde = max(arriba.edges, key=lambda e: e.calc_length())
    e1 = (borde.verts[1].co - borde.verts[0].co); e1 = (e1 - e3 * e1.dot(e3)).normalized()
    e2 = e3.cross(e1).normalized()
    vs = {v for f in grupo for v in f.verts}
    P = np.array([v.co[:] for v in vs])
    E = np.array([e1[:], e2[:], e3[:]])
    q = P @ E.T
    mn, mx = q.min(0), q.max(0)
    c = Vector(((mn + mx) / 2) @ E); h = (mx - mn) / 2
    if h[1] > h[0]:                      # que e1 sea el eje largo
        e1, e2 = e2, -e1; h = np.array([h[1], h[0], h[2]])
    return c, e1, e2, e3, h

def suav(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def almohada_nieve(bm, c, e1, e2, e3, h, mat, rnd):
    a1, a2, a3 = float(h[0]), float(h[1]), float(h[2])
    plano = abs(e3.z) > 0.97
    # tipo de cada orilla: (eje, signo) -> 'alero' (escurre), 'lado' (se redondea poquito), 'cumbre' (sigue derecho)
    tipo = {}
    for eje, vec in ((0, e1), (1, e2)):
        for s in (-1, 1):
            dz = (vec * s).z
            tipo[(eje, s)] = "alero" if (plano or dz < -0.15) else ("cumbre" if dz > 0.15 else "lado")
    T = max(2 * a3, 0.12) * 1.45                      # grosor de la almohada
    nu = max(8, int(a1 * 2 / 0.2)); nv = max(8, int(a2 * 2 / 0.2))
    U = [-math.cos(math.pi * i / nu) for i in range(nu + 1)]     # más divisiones cerca de las orillas
    V = [-math.cos(math.pi * j / nv) for j in range(nv + 1)]
    # gotitas a lo largo de cada alero: posiciones y largos al azar
    gotas = {}
    for k, t in tipo.items():
        largo = a1 if k[0] == 1 else a2          # una orilla del eje v corre a lo largo de u, y viceversa
        n = max(2, int(largo * 2 / 0.55))
        gotas[k] = [(-1 + (i + 0.5 + rnd.uniform(-0.25, 0.25)) * 2 / n, rnd.uniform(0.04, 0.11), rnd.uniform(0.1, 0.16)) for i in range(n)]
    grumos = [(rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(0.15, 0.35), rnd.uniform(0.06, 0.14)) for _ in range(int(a1 * a2 * 3) + 2)]

    def punto(u, v, arriba):
        perfil = 1.0
        desplaz = Vector((0, 0, 0)); caida = 0.0
        for (eje, s), t in tipo.items():
            x = u if eje == 0 else v
            otro = v if eje == 0 else u
            largo_eje = a1 if eje == 0 else a2
            k = suav((x * s - 0.45) / 0.55)          # 0 lejos de esta orilla, 1 en la orilla
            if t == "cumbre":
                if x * s > 0: desplaz += (e1 if eje == 0 else e2) * s * 0.06 * k
                continue
            perfil *= (1 - max(x * s, 0) ** 10) ** 0.45 if x * s > 0 else 1.0
            # CAPAS: mientras haya techo abajo, la nieve se queda ENCIMA (sin bajar). Solo la parte que sale más
            # allá de la orilla del techo ('fuera') se dobla hacia abajo y cubre la orilla por fuera.
            sale = 0.16 if t == "alero" else 0.05
            xs = max(x * s, 0.0)
            desplaz += (e1 if eje == 0 else e2) * s * sale * xs          # estira la nieve hasta sobresalir 'sale'
            if t == "alero":
                fuera = max(0.0, xs * (largo_eje + sale) - largo_eje)      # metros más allá de la orilla del techo
                gota = 0.0
                for (pos, amp, ancho) in gotas[(eje, s)]:
                    gota += amp * math.exp(-(((otro - pos) * (a2 if eje == 0 else a1)) / ancho) ** 2)
                caida += (fuera / sale) ** 1.6 * (0.14 + gota)
        z = -a3 + 0.015
        if arriba:
            bulto = 1.0 + sum(g[3] * math.exp(-(((u - g[0]) * a1) ** 2 + ((v - g[1]) * a2) ** 2) / g[2] ** 2) for g in grumos)
            z += T * perfil * bulto
        return c + e1 * (a1 * u) + e2 * (a2 * v) + e3 * (z - caida) + desplaz

    arr = [[bm.verts.new(punto(u, v, True)) for v in V] for u in U]
    aba = [[(arr[i][j] if i in (0, nu) or j in (0, nv) else bm.verts.new(punto(U[i], V[j], False)))
            for j in range(nv + 1)] for i in range(nu + 1)]
    # en la cumbre la orilla se cierra con una tapa derecha (queda dentro de la otra agua del techo)
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new([arr[i][j], arr[i + 1][j], arr[i + 1][j + 1], arr[i][j + 1]]); f.material_index = mat; f.smooth = True
            f = bm.faces.new([aba[i][j + 1], aba[i + 1][j + 1], aba[i + 1][j], aba[i][j]]); f.material_index = mat; f.smooth = True

def monton(bm, centro, tam, mat, rnd, segs=20, anillos=6):
    """Montoncito de nieve: domo achatado con 2-3 'bolas' encimadas y orilla ondulada, todo suave."""
    rx, ry, alto = tam.x / 2, tam.y / 2, max(tam.z, 0.3)
    base_z = centro.z - tam.z / 2
    bolas = [(rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), rnd.uniform(0.5, 0.75), rnd.uniform(0.15, 0.3)) for _ in range(3)]
    fase = rnd.uniform(0, 6.28)
    filas = []
    for k in range(anillos + 1):
        t = k / anillos * 0.93                           # 0 = orilla de abajo, ~1 = cima (se cierra con tapa)
        r = math.cos(t * math.pi / 2)
        fila = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            onda = 1 + 0.08 * math.sin(3 * a + fase) * (1 - t)
            x, y = math.cos(a) * r * onda, math.sin(a) * r * onda
            z = math.sin(t * math.pi / 2) ** 0.8
            z += sum(b[3] * math.exp(-((x - b[0]) ** 2 + (y - b[1]) ** 2) / (b[2] ** 2 * 0.5)) for b in bolas) * t
            fila.append(bm.verts.new((centro.x + x * rx, centro.y + y * ry, base_z + z * alto * 0.85)))
        filas.append(fila)
    for k in range(anillos):
        for j in range(segs):
            i2 = (j + 1) % segs
            f = bm.faces.new([filas[k][j], filas[k][i2], filas[k + 1][i2], filas[k + 1][j]]); f.material_index = mat; f.smooth = True
    f = bm.faces.new(filas[-1]); f.material_index = mat; f.smooth = True

def procesar(nombre, semilla):
    me = bpy.data.meshes[nombre]
    nombres_mat = [m.name if m else "" for m in me.materials]
    i_nieve = nombres_mat.index("Ext_NieveBrillo")
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    rnd = random.Random(semilla)
    losas, montones = [], []
    for g in islas(bm):
        area = Counter()
        for f in g: area[f.material_index] += f.calc_area()
        frac = area[i_nieve] / max(sum(area.values()), 1e-9)
        if frac < 0.85: continue
        if len(g) == 54:
            c, e1, e2, e3, h = caja_orientada(g)
            if h[0] * h[1] * 4 > 0.25 and e3.z > 0.3:
                losas.append((g, (c, e1, e2, e3, h)))
        elif len(g) >= 100:
            vs = {v for f in g for v in f.verts}
            mn = Vector([min(v.co[i] for v in vs) for i in range(3)]); mx = Vector([max(v.co[i] for v in vs) for i in range(3)])
            montones.append((g, mn, mx))
    chimeneas = []
    i_piedra = nombres_mat.index("Amb_Piedra") if "Amb_Piedra" in nombres_mat else -1
    for g in islas(bm):
        area = Counter()
        for f in g: area[f.material_index] += f.calc_area()
        if i_piedra >= 0 and area.most_common(1)[0][0] == i_piedra and len(g) == 54:
            vs = {v for f in g for v in f.verts}
            mn = Vector([min(v.co[i] for v in vs) for i in range(3)]); mx = Vector([max(v.co[i] for v in vs) for i in range(3)])
            if mx.z - mn.z > 1.0 and (mx.x - mn.x) < 1.5 and (mx.y - mn.y) < 1.5:
                chimeneas.append((mn, mx))
    borrar = {v for g, _ in losas for f in g for v in f.verts} | {v for g, _, _ in montones for f in g for v in f.verts}
    bmesh.ops.delete(bm, geom=list(borrar), context="VERTS")
    for _, (c, e1, e2, e3, h) in losas:
        almohada_nieve(bm, c, e1, e2, e3, h, i_nieve, rnd)
    for _, mn, mx in montones:
        monton(bm, (mn + mx) / 2, mx - mn, i_nieve, rnd)
    for mn, mx in chimeneas:      # corona: un anillo de piedra más ancho justo abajo del copete de nieve
        caja(bm, ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mx.z - 0.12), (mx.x - mn.x + 0.16, mx.y - mn.y + 0.16, 0.22), i_piedra, bisel=0.04, segs=2)
    bm.to_mesh(me); bm.free(); me.update()
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    print(f"{nombre}: {len(losas)} losas -> almohadas, {len(montones)} montones redondos, {len(chimeneas)} chimeneas con corona, tris = {tris}")

def hacer_casas():
    restaurar(MALLAS)
    for k, n in enumerate(MALLAS):
        procesar(n, 11 + k)
