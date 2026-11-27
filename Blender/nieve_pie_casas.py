# -*- coding: utf-8 -*-
"""
NIEVE AL PIE DE LAS CASAS: antes había montoncitos sueltos (islas de 60 caras cortadas en plano contra la pared)
y montones redondos en las esquinas (islas de 121 caras) que se encimaban unos con otros.
Ahora es UNA sola superficie continua alrededor de cada casa (no se puede encimar consigo misma):
  - Se recorre el contorno de la casa (rectángulo con esquinas redondeadas) con un parámetro s (metros de perímetro)
    y hacia afuera con t (0 = pegado a la pared, W = orilla).
  - Altura contra la pared A(s): base + bultitos (ruido) + más alta en las esquinas, y casi nada frente a la puerta.
  - Perfil hacia afuera: z = suelo + A * (1 - (t/W)^2)^1.3  - 0.22 * (t/W)^3   -> en la orilla queda HUNDIDA bajo
    el suelo, así que la orilla visible es una curva limpia (como nieve_campo en las rocas).
  - La primera fila empieza 10 cm DENTRO de la pared (no se ve una orilla abierta junto a la pared).
El rectángulo de la pared y el nivel del suelo se sacan de los montoncitos viejos antes de borrarlos.
Uso: exec(nieve_pie_casas.py); hacer_nieve_pie()
"""
import bpy, bmesh, math
from mathutils import Vector, noise

def suave01(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def islas(bm, filtro):
    bm.faces.ensure_lookup_table(); vist = set(); res = []
    for f in bm.faces:
        if f.index in vist or not filtro(f): continue
        pila = [f]; isla = []; vist.add(f.index)
        while pila:
            x = pila.pop(); isla.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in vist and filtro(y): vist.add(y.index); pila.append(y)
        res.append(isla)
    return res

# puertas (coords locales): centro x/y y lado ; huecos extra (porche, terraza)
PUERTAS = {"CasaRoja": [(1.1, 1)], "CasaAzul": [(1.1, 1)], "CasaVerde": [(1.1, 1)], "CasaTroncos": [(0.0, 1)], "CasaA": []}

def contorno(x0, x1, y0, y1, rc, paso):
    """Puntos del contorno (rectángulo de esquinas redondeadas radio rc) con su normal hacia afuera."""
    pts = []
    tramos = [((x0 + rc, y0), (x1 - rc, y0), (0, -1)), ((x1, y0 + rc), (x1, y1 - rc), (1, 0)),
              ((x1 - rc, y1), (x0 + rc, y1), (0, 1)), ((x0, y1 - rc), (x0, y0 + rc), (-1, 0))]
    esquinas = [((x1 - rc, y0 + rc), -math.pi / 2), ((x1 - rc, y1 - rc), 0.0), ((x0 + rc, y1 - rc), math.pi / 2), ((x0 + rc, y0 + rc), math.pi)]
    for (a, b, n), (ce, a0) in zip(tramos, esquinas):
        a = Vector(a); b = Vector(b); L = (b - a).length; k = max(1, int(L / paso))
        for i in range(k):
            pts.append((a.lerp(b, i / k), Vector(n), 0.0))
        k = max(3, int(rc * math.pi / 2 / paso))
        for i in range(k):
            ang = a0 + (math.pi / 2) * i / k
            n2 = Vector((math.cos(ang), math.sin(ang)))
            pts.append((Vector(ce) + n2 * rc, n2, math.sin(math.pi * i / k)))   # 3er valor: "qué tan esquina"
    return pts

def hacer_malla(mn, semilla):
    me = bpy.data.meshes[mn]; nm = [m.name for m in me.materials]; ni = nm.index("Ext_NieveBrillo")
    bm = bmesh.new(); bm.from_mesh(me)
    viejas = [i for i in islas(bm, lambda f: f.material_index == ni) if len(i) in (60, 121)]
    paredes = [i for i in viejas if len(i) == 60]
    if not paredes:
        g = me.get("nieve_pie")
        if not g: bm.free(); print(mn, "sin datos"); return
        x0, x1, y0, y1, zs = g
    else:
        cs = [sum((v.co for f in i for v in f.verts), Vector()) / sum(len(f.verts) for f in i) for i in paredes]
        x0 = min(c.x for c in cs); x1 = max(c.x for c in cs); y0 = min(c.y for c in cs); y1 = max(c.y for c in cs)
        zs = min(v.co.z for i in paredes for f in i for v in f.verts) + 0.02
        me["nieve_pie"] = [x0, x1, y0, y1, zs]
    bmesh.ops.delete(bm, geom=[f for i in viejas for f in i], context="FACES")
    off = Vector((semilla * 3.7, semilla * 1.3, 0))
    pts = contorno(x0, x1, y0, y1, 0.35, 0.1)
    NT = 9
    filas = []
    for p, n, esq in pts:
        q = Vector((p.x, p.y, 0))
        A = 0.32 + 0.18 * noise.noise(q * 0.9 + off) + 0.08 * noise.noise(q * 2.7 + off) + 0.22 * esq
        for (dx, lado) in PUERTAS.get(mn, []):
            if n.y * lado > 0.5:                                    # pared de la puerta
                A *= suave01((abs(p.x - dx) - 0.75) / 0.5)
        if mn == "CasaTroncos" and n.y > 0.5: A *= 0.25            # porche al frente
        A = max(A, 0.0)
        W = 0.55 + 1.5 * A
        fila = []
        for k in range(NT + 1):
            t = -0.1 + (W + 0.1) * k / NT
            u = max(t, 0.0) / W
            z = zs + A * max(0.0, 1 - u * u) ** 1.3 - 0.22 * u ** 3
            fila.append(bm.verts.new((p.x + n.x * t, p.y + n.y * t, z)))
        filas.append(fila)
    nuevas = []
    for a, b in zip(filas, filas[1:] + filas[:1]):
        for k in range(NT):
            f = bm.faces.new((a[k], a[k + 1], b[k + 1], b[k])); f.material_index = ni; f.smooth = True; nuevas.append(f)
    bm.normal_update()
    if sum(f.normal.z for f in nuevas) < 0: bmesh.ops.reverse_faces(bm, faces=nuevas)
    bm.to_mesh(me); bm.free(); me.update()
    print(mn, "montones viejos quitados:", len(viejas), "| caras nuevas:", len(nuevas), "| caja", round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), "suelo", round(zs, 2))

def hacer_nieve_pie():
    for i, mn in enumerate(("CasaRoja", "CasaAzul", "CasaVerde", "CasaTroncos", "CasaA")):
        hacer_malla(mn, i + 1)


# ---------------------------------------------------------------------------------------------------
# v2: el terreno cambia hasta ±1.5 m de casa a casa (lomas) y las 9 casas comparten 5 mallas, así que la nieve NO
# puede ir dentro de la malla de la casa. Va en un objeto aparte "NieveCasas" (colección Ambientacion2 -> Pueblo_Luces.glb)
# en coordenadas de mundo: cada punto toma la altura REAL del suelo con un rayo hacia abajo y encima se suma el perfil.
def quitar_viejos():
    for i, mn in enumerate(("CasaRoja", "CasaAzul", "CasaVerde", "CasaTroncos", "CasaA")):
        me = bpy.data.meshes[mn]; nm = [m.name for m in me.materials]; ni = nm.index("Ext_NieveBrillo")
        bm = bmesh.new(); bm.from_mesh(me)
        g = me.get("nieve_pie")
        # quitar montones viejos (60/121 caras) y también la capa de la v1 (anillo de 1800+ caras pegado al piso)
        quitar = [f for isla in islas(bm, lambda f: f.material_index == ni) if len(isla) in (60, 121) or
                  (len(isla) > 1000 and max(v.co.z for f in isla for v in f.verts) < (g[4] if g else 0) + 1.2) for f in isla]
        bmesh.ops.delete(bm, geom=quitar, context="FACES"); bm.to_mesh(me); bm.free(); me.update()
        print(mn, "caras de nieve al pie quitadas:", len(quitar))

def hacer_nieve_casas():
    from mathutils.bvhtree import BVHTree
    s = bpy.data.objects["SueloNieve"]; b = bmesh.new(); b.from_mesh(s.data); b.transform(s.matrix_world)
    suelo = BVHTree.FromBMesh(b); b.free()
    def altura(x, y):
        hit = suelo.ray_cast(Vector((x, y, 100)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else 0.0
    obj = bpy.data.objects.get("NieveCasas")
    if obj is None:
        me = bpy.data.meshes.new("NieveCasas"); obj = bpy.data.objects.new("NieveCasas", me)
        bpy.data.collections["Ambientacion2"].objects.link(obj)
        me.materials.append(bpy.data.materials["Ext_NieveBrillo"])
    bm = bmesh.new(); NT = 9; total = 0
    for semilla, casa in enumerate(sorted([o for o in bpy.data.objects if o.name.startswith("Casa_")], key=lambda o: o.name)):
        mn = casa.data.name; x0, x1, y0, y1, zs = casa.data["nieve_pie"]
        M = casa.matrix_world; R = M.to_3x3()
        off = Vector((semilla * 3.7, semilla * 1.3, 0))
        filas = []
        for p, n, esq in contorno(x0, x1, y0, y1, 0.35, 0.1):
            q = Vector((p.x, p.y, 0))
            A = 0.32 + 0.18 * noise.noise(q * 0.9 + off) + 0.08 * noise.noise(q * 2.7 + off) + 0.22 * esq
            for (dx, lado) in PUERTAS.get(mn, []):
                if n.y * lado > 0.5: A *= suave01((abs(p.x - dx) - 0.75) / 0.5)
            if mn == "CasaTroncos" and n.y > 0.5: A *= 0.25
            A = max(A, 0.0); W = 0.55 + 1.5 * A
            fila = []
            for k in range(NT + 1):
                t = -0.1 + (W + 0.1) * k / NT; u = max(t, 0.0) / W
                w = M @ Vector((p.x + n.x * t, p.y + n.y * t, 0))
                z = altura(w.x, w.y) + A * max(0.0, 1 - u * u) ** 1.3 - 0.22 * u ** 3 - 0.03
                fila.append(bm.verts.new((w.x, w.y, z)))
            filas.append(fila)
        nuevas = []
        for a, c in zip(filas, filas[1:] + filas[:1]):
            for k in range(NT):
                f = bm.faces.new((a[k], a[k + 1], c[k + 1], c[k])); f.smooth = True; nuevas.append(f)
        bm.normal_update()
        if sum(f.normal.z for f in nuevas) < 0: bmesh.ops.reverse_faces(bm, faces=nuevas)
        total += len(nuevas)
    obj.data.clear_geometry(); bm.to_mesh(obj.data); bm.free(); obj.data.update()
    print("NieveCasas caras:", total)
