# -*- coding: utf-8 -*-
"""
FAROLITOS DEL PUEBLO v2 (los 42 Farolito_NN de los senderos), mismo estilo que los faroles del patio.
Se reemplaza la geometría de cada malla; el objeto, su nombre, lugar y giro no cambian (Unity conserva su collider).
Diseño "bastón de caramelo":
  - base escalonada redonda y poste negro con anillos;
  - listón rojo en espiral por el poste y moño rojo;
  - arriba el poste se curva como bastón (arco) y de la punta cuelga la linterna;
  - linterna = la misma de los faroles del patio a escala 0.5: copa, vidrio de 4 lados que se abre,
    4 parantes, techo de 4 aguas con bolita y capa de nieve que sigue el techo (no lo atraviesa).
El CENTRO DEL VIDRIO queda en (0, -0.27, 1.32) local, igual que antes: ahí están las luces de Unity y de ahí
salen las guirnaldas entre farolitos (luces_pueblo.py).
Materiales: 0 metal negro, 1 vidrio con luz, 2 nieve, 3 rojo (se agrega Amb_Rojo si falta).
Uso: exec(modelado.py); exec(cerca_faroles.py); exec(farolitos.py); hacer_farolitos()
"""
import bpy, bmesh, math, random
from mathutils import Vector

N, VID, NIE, ROJ = 0, 1, 2, 3
VIDRIO = Vector((0.0, -0.27, 1.32))

def linterna(bm, c, k, rnd):
    """Linterna de los faroles del patio, a escala k, con el centro del vidrio en c."""
    x, y = c.x, c.y
    zv0, zv1 = c.z - 0.24 * k, c.z + 0.24 * k
    zc = zv0 - 0.16 * k
    anillo_perfil(bm, x, y, [(zc, 0.0), (zc, 0.05 * k), (zc + 0.08 * k, 0.1 * k), (zc + 0.14 * k, 0.17 * k),
                             (zc + 0.17 * k, 0.19 * k), (zc + 0.19 * k, 0.0)], N, segs=12)
    esfera(bm, (x, y, zc - 0.03 * k), (0.035 * k, 0.035 * k, 0.04 * k), mat=N, segs=8, anillos=5)   # gotita de abajo
    vid = []
    for z, r in ((zv0, 0.15 * k), (zv1, 0.19 * k)):
        vid.append([bm.verts.new((x + math.cos(math.pi / 4 + i * math.pi / 2) * r, y + math.sin(math.pi / 4 + i * math.pi / 2) * r, z)) for i in range(4)])
    for i in range(4):
        f = bm.faces.new((vid[0][i], vid[0][(i + 1) % 4], vid[1][(i + 1) % 4], vid[1][i])); f.material_index = VID
    f = bm.faces.new(vid[1]); f.material_index = VID
    f = bm.faces.new(list(reversed(vid[0]))); f.material_index = VID
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        p0 = Vector((x + math.cos(a) * 0.165 * k, y + math.sin(a) * 0.165 * k, zv0 - 0.02 * k))
        p1 = Vector((x + math.cos(a) * 0.205 * k, y + math.sin(a) * 0.205 * k, zv1 + 0.02 * k))
        loft(bm, [p0, p1], [(0.02 * k, 0.02 * k)] * 2, mat=N, segs=4, sub=1, tapas=(True, True), domo=0.0)
    zt = zv1 + 0.02 * k
    anillo_perfil(bm, x, y, [(zt, 0.0), (zt, 0.27 * k), (zt + 0.05 * k, 0.27 * k), (zt + 0.2 * k, 0.08 * k),
                             (zt + 0.26 * k, 0.03 * k), (zt + 0.27 * k, 0.0)], N, segs=4, suave=False)
    capa_nieve(bm, x, y, [(zt + 0.07 * k, 0.3 * k), (zt + 0.1 * k, 0.285 * k), (zt + 0.17 * k, 0.2 * k),
                          (zt + 0.24 * k, 0.11 * k), (zt + 0.29 * k, 0.05 * k), (zt + 0.305 * k, 0.0)],
               NIE, rnd, segs=12, gotas=4, caida=0.03)
    toro(bm, (x, y, zt + 0.33 * k), 0.03 * k, 0.012, mat=N, segs=10, lados=5, inclinacion=math.pi / 2)  # argolla
    return zt + 0.36 * k            # altura de la argolla (de ahí cuelga)

def farolito(bm, rnd):
    # base y poste
    anillo_perfil(bm, 0, 0, [(-0.08, 0), (-0.08, 0.13), (0.03, 0.13), (0.05, 0.11), (0.07, 0.085), (0.13, 0.075),
                             (0.16, 0.055), (0.2, 0.04)], N, segs=12)
    TOP = 1.78
    anillo_perfil(bm, 0, 0, [(0.18, 0.04), (TOP, 0.03)], N, segs=10)
    for zr in (0.3, 1.25):
        toro(bm, (0, 0, zr), 0.036, 0.012, mat=N, segs=10, lados=5)
    # listón en espiral
    hel = []
    for s in range(49):
        t = s / 48; a = t * 2 * math.pi * 3.5; z = 0.38 + t * 0.82
        r = 0.04 - 0.01 * z / TOP + 0.004
        hel.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    loft(bm, hel, [(0.009, 0.034)] * len(hel), mat=ROJ, segs=6, sub=1, tapas=(True, True), arriba=Vector((0, 0, 1)))
    # bastón: arco de la punta del poste hacia -Y hasta encima de la linterna
    R = abs(VIDRIO.y) / 2
    arco = [Vector((0, -R + math.cos(a) * R, TOP + math.sin(a) * R)) for a in [i * math.pi / 10 for i in range(11)]]
    loft(bm, [Vector((0, 0, TOP - 0.05))] + arco, [(0.03, 0.03)] * (len(arco) + 1), mat=N, segs=10, sub=2, tapas=(False, True))
    # rayitas rojas en el arco (bastón de caramelo)
    for i in range(1, 10, 2):
        a = i * math.pi / 10
        p = Vector((0, -R + math.cos(a) * R, TOP + math.sin(a) * R))
        tang = Vector((0, -math.sin(a), math.cos(a)))
        n = tang.normalized()
        # anillo rojo perpendicular al arco
        anillo = []
        for j in range(10):
            b = 2 * math.pi * j / 10
            u = Vector((1, 0, 0)); w = n.cross(u).normalized()
            anillo.append(p + (u * math.cos(b) + w * math.sin(b)) * 0.033)
        loft(bm, anillo + anillo[:3], [(0.008, 0.008)] * 13, mat=ROJ, segs=5, sub=1, tapas=(False, False))
    # moño debajo del arco
    zm = TOP - 0.12
    for s in (-1, 1):
        lazo = [Vector((0, -0.035, zm)), Vector((s * 0.06, -0.045, zm + 0.05)), Vector((s * 0.1, -0.04, zm + 0.01)),
                Vector((s * 0.07, -0.04, zm - 0.025)), Vector((s * 0.01, -0.035, zm))]
        loft(bm, lazo, [(0.022, 0.008)] * 5, mat=ROJ, segs=6, sub=3, tapas=(True, True))
        cola = [Vector((s * 0.008, -0.035, zm - 0.005)), Vector((s * 0.03, -0.045, zm - 0.08)), Vector((s * 0.045, -0.04, zm - 0.15))]
        loft(bm, cola, [(0.018, 0.006)] * 3, mat=ROJ, segs=6, sub=3, tapas=(True, True))
    esfera(bm, (0, -0.04, zm), (0.022, 0.02, 0.022), mat=ROJ, segs=8, anillos=6)
    # linterna colgando de la punta del arco
    arg = linterna(bm, VIDRIO, 0.5, rnd)
    punta = Vector((0, -2 * R, TOP))
    loft(bm, [punta, Vector((0, VIDRIO.y, arg))], [(0.007, 0.007)] * 2, mat=N, segs=5, sub=1, tapas=(True, True), domo=0.0)
    # gorrito de nieve sobre el arco
    domo_nieve(bm, (0, -R, TOP + R + 0.025), 0.05, 0.03, NIE, rnd, segs=10, gotas=2, caida=0.02)

def hacer_farolitos(semilla=11):
    rojo = bpy.data.materials["Amb_Rojo"]
    n = 0
    for o in sorted([o for o in bpy.data.objects if o.name.startswith("Farolito_")], key=lambda o: o.name):
        me = o.data
        while len(me.materials) < 4: me.materials.append(rojo)
        rnd = random.Random(semilla + n)
        bm = bmesh.new(); farolito(bm, rnd)
        me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
        n += 1
    print("farolitos:", n, "| tris c/u:", sum(len(p.vertices) - 2 for p in o.data.polygons))
