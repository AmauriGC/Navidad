# -*- coding: utf-8 -*-
"""
ARBUSTO y LEÑA v3 (26-nov): mismo estilo que rocas_v3 = low-poly REDONDEADO (caras planas, sin picos).
Arbusto: grumos de icoesfera (subdiv 2) deformados con ruido, sombreado PLANO y dos tonos de verde por cara
  (se notan las facetas); nieve solo en las copas (nieve_campo, caras de arriba subdivididas); racimos de 3 bayas
  con 2 hojitas de acebo; ramitas asomando abajo.
Leña: leños de 9 lados con orillas biseladas, largos y puntas disparejas; cortes con anillos (madera cálida
  Ext_CorteLena + anillo oscuro + médula); nieve en capita solo arriba de los leños de arriba.
Las dos se escalan a su caja original (datos_rocas.json) => los colliders de Unity quedan del mismo tamaño.
Uso: exec(modelado.py); exec(rocas_arbustos.py); exec(rocas_v3.py); exec(arbusto_lena_v3.py); hacer_arbusto(); hacer_lena()
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

def _slots(me, nombres):
    me.materials.clear()
    for n in nombres: me.materials.append(bpy.data.materials[n])

def grumo(bm, centro, radios, semilla, sub=2, rugoso=0.14):
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = Vector((semilla * 3.1, semilla * 1.7, semilla * 5.3))
    for v in res["verts"]:
        n = v.co.normalized()
        d = 1 + rugoso * noise.noise(n * 1.8 + off)
        v.co = Vector(centro) + Vector((n.x * radios[0] * d, n.y * radios[1] * d, n.z * radios[2] * d))
    return list({f for v in res["verts"] for f in v.link_faces})

def hojita(bm, base, direc, largo, ancho, mat):
    """Hoja de acebo plana (rombo con 2 picos suaves de cada lado), doble cara."""
    d = direc.normalized(); lado = d.cross(Vector((0, 0, 1)))
    if lado.length < 0.1: lado = Vector((1, 0, 0))
    lado.normalize(); arriba = lado.cross(d).normalized()
    pts = [(0, 0), (0.3, 0.55), (0.55, 0.35), (0.8, 0.5), (1, 0), (0.8, -0.5), (0.55, -0.35), (0.3, -0.55)]
    vs = [bm.verts.new(base + d * largo * t + lado * ancho * s + arriba * largo * 0.12 * t * t) for t, s in pts]
    f1 = bm.faces.new(vs); f1.material_index = mat
    f2 = bm.faces.new([bm.verts.new(v.co - arriba * 0.002) for v in reversed(vs)]); f2.material_index = mat

def ramita(bm, p0, p1, r, mat, lados=5):
    d = (p1 - p0).normalized(); rot = d.to_track_quat("Z", "Y").to_matrix()
    a = [bm.verts.new(p0 + rot @ Vector((math.cos(6.2832 * j / lados) * r, math.sin(6.2832 * j / lados) * r, 0))) for j in range(lados)]
    b = [bm.verts.new(p1 + rot @ Vector((math.cos(6.2832 * j / lados) * r * 0.5, math.sin(6.2832 * j / lados) * r * 0.5, 0))) for j in range(lados)]
    for j in range(lados):
        f = bm.faces.new((a[j], a[(j + 1) % lados], b[(j + 1) % lados], b[j])); f.material_index = mat
    f = bm.faces.new(b); f.material_index = mat

def construir_arbusto(bm, caja, semilla=23):
    rnd = random.Random(semilla)
    # 0 verde, 1 nieve, 2 bayas, 3 verde oscuro, 4 acebo, 5 ramitas
    # grumos: uno grande al centro y 9 alrededor/arriba, de tamaños disparejos
    bolas = [((0, 0, 0.5), (0.55, 0.55, 0.48))]
    for k in range(9):
        a = k * 2.4 + rnd.uniform(-0.3, 0.3)
        anillo = 0.5 if k < 6 else 0.22
        r = rnd.uniform(0.27, 0.38) if k < 6 else rnd.uniform(0.25, 0.32)
        z = (0.3 if k < 6 else 0.78) + rnd.uniform(-0.05, 0.08)
        bolas.append(((math.cos(a) * anillo, math.sin(a) * anillo, z), (r, r * rnd.uniform(0.85, 1.1), r * 0.9)))
    hojas = []
    for k, (c, r) in enumerate(bolas):
        caras = grumo(bm, c, r, semilla + k, rugoso=0.24)
        for f in caras:
            f.smooth = False
        hojas += caras
    bm.normal_update()
    for f in hojas:   # sombra natural: lo que mira hacia abajo/afuera abajo va en verde oscuro (+ unas pocas al azar)
        f.material_index = 3 if (f.normal.z < -0.15 or rnd.random() < 0.12) else 0
    # ramitas asomando abajo (prismas de 5 lados)
    for k in range(5):
        a = rnd.uniform(0, 6.28)
        p0 = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.06)); p1 = p0 + Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, 0.12))
        ramita(bm, p0, p1, 0.028, 5)
    ajustar_a_caja(bm, caja)
    bm.normal_update()
    hojas = [f for f in hojas if f.is_valid]
    arriba = [f for f in hojas if f.normal.z > 0.15]
    bmesh.ops.subdivide_edges(bm, edges=list({e for f in arriba for e in f.edges}), cuts=2, use_grid_fill=True)
    bm.normal_update()
    zmn, zmx = caja[0][2], caja[1][2]; H = zmx - zmn
    def campo(p, n):
        corte = zmn + H * (0.72 + 0.06 * noise.noise(p * 3.0))
        return suave01((n.z - 0.55) / 0.3) * suave01((p.z - corte) / (H * 0.07))
    hojas = [f for f in bm.faces if f.material_index in (0, 3)]
    nieve_campo(bm, [f for f in hojas if f.normal.z > 0.2], campo, H * 0.05, 1, hundir=0.008)
    # racimos de bayas + 2 hojitas de acebo en los costados
    esc = (caja[1][0] - caja[0][0]) / 1.5
    costados = [f for f in bm.faces if f.material_index in (0, 3) and -0.1 < f.normal.z < 0.45
                and f.calc_center_median().z > zmn + H * 0.3]
    rnd.shuffle(costados)
    usados = []
    for f in costados:
        p = f.calc_center_median()
        if any((p - q).length < 0.35 * esc for q in usados): continue
        usados.append(p)
        n = f.normal.copy()
        base = p + n * 0.015 * esc
        for b in range(3):
            q = base + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * 0.045 * esc
            esfera(bm, q, (0.045 * esc,) * 3, mat=2, segs=8, anillos=6)
        for s in (-1, 1):
            d = (n + Vector((0, 0, 0.6)) + n.cross(Vector((0, 0, 1))) * s * 0.9)
            hojita(bm, base, d, 0.15 * esc, 0.05 * esc, 4)
        if len(usados) >= 6: break

def hacer_arbusto():
    d = cajas_originales()
    me = bpy.data.meshes["Arbusto"]
    _slots(me, ["Ext_PinoD", "Ext_NieveBrillo", "Amb_Rojo", "Ext_PinoA", "Acebo_Verde", "Ext_Tronco"])
    poner("Arbusto", lambda bm, me: construir_arbusto(bm, d["Arbusto"]))

# ---------------------------------------------------------------- LEÑA
def leno(bm, p0, p1, r, rnd, lados=9):
    """Leño low-poly: prisma de 'lados' caras con orilla biselada; tapas con anillos.
    materiales: 0 corteza, 3 corteza oscura (algunas caras), 1 corte (madera), 4 anillo oscuro."""
    eje = p1 - p0; L = eje.length; d = eje.normalized()
    rot = d.to_track_quat("Z", "Y").to_matrix()
    giro = rnd.uniform(0, 6.28)
    radios = [r * rnd.uniform(0.93, 1.07) for _ in range(lados)]
    def anillo(t, k, dz=0.0):
        return [bm.verts.new(p0 + d * (t * L + dz) + rot @ Vector((math.cos(giro + 6.2832 * j / lados) * radios[j] * k,
                                                                    math.sin(giro + 6.2832 * j / lados) * radios[j] * k, 0)))
                for j in range(lados)]
    b = min(0.035 / max(L, 0.1), 0.05)
    filas = [anillo(0, 0.9), anillo(b * 0.4, 0.985), anillo(b, 1.0), anillo(0.5, rnd.uniform(0.98, 1.03)),
             anillo(1 - b, 1.0), anillo(1 - b * 0.4, 0.985), anillo(1, 0.9)]
    oscuras = {j for j in range(lados) if rnd.random() < 0.35}
    for a, c in zip(filas, filas[1:]):
        for j in range(lados):
            f = bm.faces.new((a[j], a[(j + 1) % lados], c[(j + 1) % lados], c[j]))
            f.material_index = 3 if j in oscuras else 0; f.smooth = False
    for fila, signo, t in ((filas[0], -1, 0.0), (filas[-1], 1, 1.0)):
        prev = fila
        for k, mat in ((0.82, 1), (0.66, 1), (0.6, 4), (0.32, 1), (0.26, 4)):
            nueva = anillo(t, k)
            for j in range(lados):
                vs = (prev[j], prev[(j + 1) % lados], nueva[(j + 1) % lados], nueva[j])
                f = bm.faces.new(vs if signo > 0 else tuple(reversed(vs))); f.material_index = mat
            prev = nueva
        cen = bm.verts.new(p0 + d * t * L)
        for j in range(lados):
            vs = (prev[j], prev[(j + 1) % lados], cen)
            f = bm.faces.new(vs if signo > 0 else tuple(reversed(vs))); f.material_index = 1

def construir_lena(bm, caja, semilla=33):
    rnd = random.Random(semilla)
    r = 0.16; L = 1.5
    for fila, n in enumerate((4, 3, 2)):
        for k in range(n):
            x = (k - (n - 1) / 2) * r * 2.02
            z = r + fila * r * 1.75
            largo = L * rnd.uniform(0.86, 1.0)
            y0 = -largo / 2 + rnd.uniform(-0.1, 0.1)
            leno(bm, Vector((x, y0, z)), Vector((x + rnd.uniform(-0.03, 0.03), y0 + largo, z + rnd.uniform(-0.02, 0.02))),
                 r * rnd.uniform(0.9, 1.06), rnd)
    ajustar_a_caja(bm, caja)
    bm.normal_update()
    corteza = [f for f in bm.faces if f.material_index in (0, 3) and f.normal.z > 0.3]
    bmesh.ops.subdivide_edges(bm, edges=list({e for f in corteza for e in f.edges}), cuts=2, use_grid_fill=True)
    bm.normal_update()
    zmn, zmx = caja[0][2], caja[1][2]; H = zmx - zmn
    def campo(p, n):
        return suave01((n.z - 0.6) / 0.25) * suave01((p.z - (zmn + H * 0.55)) / (H * 0.06)) * \
               suave01(0.5 + 1.5 * noise.noise(p * 2.5 + Vector((7, 1, 3))))
    corteza = [f for f in bm.faces if f.material_index in (0, 3) and f.normal.z > 0.3]
    nieve_campo(bm, corteza, campo, H * 0.035, 2, hundir=0.006)

def hacer_lena():
    d = cajas_originales()
    corte = bpy.data.materials.get("Ext_CorteLena") or material("Ext_CorteLena", (0.72, 0.52, 0.3), rugosidad=0.85)
    anillo = bpy.data.materials.get("Ext_AnilloLena") or material("Ext_AnilloLena", (0.42, 0.26, 0.13), rugosidad=0.9)
    me = bpy.data.meshes["Troncos"]
    _slots(me, ["Ext_Tronco2", "Ext_CorteLena", "Ext_NieveBrillo", "Ext_Tronco", "Ext_AnilloLena"])
    poner("Troncos", lambda bm, me: construir_lena(bm, d["Troncos"]))
