# -*- coding: utf-8 -*-
"""
MEDALLA (Fase 9.4): se gana al terminar la noche; su color depende de la dificultad (bronce/plata/oro/diamante).
UNA malla, origen en el centro del disco, el frente mira a -Y (= +Z en Unity):
  - disco con orilla redondeada (toro) y canto dentado (24 muescas),
  - estrella de 5 puntas abombada en relieve al centro, rodeada de un anillo de bolitas,
  - argolla arriba y listón en V (rojo y verde con raya blanca).
Material 0 "Medalla_Metal" (Unity lo pinta del color de la medalla con MaterialPropertyBlock), 1 listón rojo,
2 listón verde, 3 raya blanca, 4 estrella (Unity la pinta más clara que el disco).
Uso: exec(modelado.py); exec(este); hacer_medalla()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

R = 0.5   # radio del disco (la medalla mide ~1 m; Unity la escala)


def estrella(bm, centro_y, radio, alto, mat):
    """Estrella de 5 puntas abombada: abanico desde un centro elevado hacia la orilla en zigzag."""
    tmp = bmesh.new()
    c = tmp.verts.new(Vector((0, centro_y - alto, 0)))
    orilla = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = radio if k % 2 == 0 else radio * 0.45
        orilla.append(tmp.verts.new(Vector((math.cos(a) * r, centro_y - alto * 0.25, math.sin(a) * r))))
    base = [tmp.verts.new(Vector((v.co.x, centro_y, v.co.z))) for v in orilla]
    for k in range(10):
        j = (k + 1) % 10
        tmp.faces.new((c, orilla[j], orilla[k]))
        tmp.faces.new((orilla[k], orilla[j], base[j], base[k]))
    for f in tmp.faces: f.material_index = mat; f.smooth = False
    unir(bm, tmp)


def hacer_medalla():
    metal = material("Medalla_Metal", (1.0, 0.78, 0.3), metal=1.0, rugosidad=0.25)
    rojo = material("Medalla_Rojo", (0.8, 0.08, 0.1), rugosidad=0.55)
    verde = material("Medalla_Verde", (0.08, 0.5, 0.22), rugosidad=0.55)
    blanco = material("Medalla_Blanco", (0.95, 0.95, 0.92), rugosidad=0.55)
    brillo = material("Medalla_Estrella", (1.0, 0.92, 0.6), metal=1.0, rugosidad=0.12)

    def construir(bm):
        eje = Matrix.Rotation(math.pi / 2, 3, "X")   # loft/toro van en Z: los giramos para que el disco mire a -Y
        # disco: cilindro corto
        tmp = bmesh.new()
        loft(tmp, [Vector((0, 0, -0.04)), Vector((0, 0, 0.04))], [(R * 0.93, R * 0.93)] * 2, 0, segs=48, sub=1, domo=0.05)
        for v in tmp.verts: v.co = eje @ v.co
        unir(bm, tmp)
        # orilla redondeada
        tmp = bmesh.new(); toro(tmp, (0, 0, 0), R * 0.93, 0.065, 0, segs=64, lados=12)
        for v in tmp.verts: v.co = eje @ v.co
        unir(bm, tmp)
        # canto dentado: 24 muescas (bolitas) alrededor
        for k in range(24):
            a = k * 2 * math.pi / 24
            esfera(bm, (math.cos(a) * R * 1.0, 0, math.sin(a) * R * 1.0), (0.045, 0.06, 0.045), 0, segs=10, anillos=6)
        # anillo de bolitas en la cara de enfrente y la estrella
        for k in range(20):
            a = k * 2 * math.pi / 20
            esfera(bm, (math.cos(a) * R * 0.72, -0.045, math.sin(a) * R * 0.72), (0.025, 0.02, 0.025), 0, segs=8, anillos=5)
        estrella(bm, -0.04, R * 0.55, 0.13, 4)
        estrella(bm, 0.04, R * 0.55, -0.13, 4)      # también atrás (la medalla gira)
        # argolla arriba
        tmp = bmesh.new(); toro(tmp, (0, 0, 0), 0.07, 0.022, 0, segs=24, lados=8)
        for v in tmp.verts: v.co = Matrix.Rotation(math.pi / 2, 3, "Y") @ v.co + Vector((0, 0, R + 0.1))
        unir(bm, tmp)
        # listón en V: dos tiras que suben desde la argolla (rojo con raya blanca / verde con raya blanca)
        for s, mat in ((-1, 1), (1, 2)):
            p0 = Vector((s * 0.02, 0.01, R + 0.15)); p1 = Vector((s * 0.32, 0.03, R + 0.85))
            d = (p1 - p0).normalized(); lado = Vector((d.z, 0, -d.x)) * s
            for (off, ancho, m, prof) in ((0.0, 0.13, mat, 0.0), (0.0, 0.035, 3, -0.006)):
                q = [p0 + lado * (off - ancho), p0 + lado * (off + ancho), p1 + lado * (off + ancho), p1 + lado * (off - ancho)]
                vs = [bm.verts.new(v + Vector((0, prof, 0))) for v in q]
                vs2 = [bm.verts.new(v + Vector((0, prof + 0.012, 0))) for v in q]
                caras = [bm.faces.new(vs[::-1]), bm.faces.new(vs2)]
                for i in range(4):
                    j = (i + 1) % 4
                    caras.append(bm.faces.new((vs[i], vs[j], vs2[j], vs2[i])))
                for f in caras: f.material_index = m; f.smooth = False

    col = bpy.data.collections.get("Trampas") or bpy.data.collections.new("Trampas")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    o = bpy.data.objects.get("Medalla")
    if o is None:
        o = bpy.data.objects.new("Medalla", bpy.data.meshes.new("Medalla_tmp")); col.objects.link(o)
    o.location = (10, -6, 1.5)
    poner_malla(o, construir, materiales=[metal, rojo, verde, blanco, brillo], subsurf=0)
    o.data.name = "Medalla"
    exportar_glb([o], "Medalla.glb", raiz=o)
    return len(o.data.polygons)
