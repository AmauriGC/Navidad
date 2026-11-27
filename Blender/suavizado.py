# Generadores "suaves" (estilo caricatura esponjosa) — Blender 5, bpy + bmesh.
# Se ejecuta dentro de Blender:  exec(open(".../Blender/suavizado.py").read())
# Idea: en lugar de un zigzag (punta / hueco / punta) que deja filos, el borde de cada capa de follaje
# es una ONDA (coseno): lóbulos redondos. Además el borde se "enrolla" hacia abajo para que no quede
# como cuchilla, y todo usa sombreado suave (normales interpoladas).
import bpy, bmesh, math, random
from mathutils import Vector

PROYECTO = "/home/cris/Escritorio/10A/ulises/Navidad"


def exportar(objs, nombre):
    """Exporta los objetos (con sus hijos) a Assets/Modelos/<nombre> como .glb (Unity lo importa con glTFast)."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.hide_set(False); o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f"{PROYECTO}/Assets/Modelos/{nombre}", use_selection=True,
                              export_apply=True, export_yup=True)


def falda_suave(bm, z_apex, z_rim, R, lobulos, caida, giro, seed, material, K=5, muestras=3, rizo=0.06, domo=0.16):
    """Una capa de follaje con forma de campana y borde ondulado.
    material(k, j, lobulo, t) -> índice de material para cada cara (k = anillo, t = 0 arriba .. 1 borde)."""
    rnd = random.Random(seed)
    N = lobulos * muestras
    alto = z_apex - z_rim
    var = [0.9 + 0.2 * rnd.random() for _ in range(lobulos)]      # cada lóbulo de tamaño un poco distinto
    apex = bm.verts.new((0, 0, z_apex))
    filas = []
    ts = [domo] + [k / K for k in range(1, K + 1)]   # primer anillo muy cerca de la punta => punta redondeada (domo)
    for t in ts:
        fila = []
        for j in range(N):
            a = giro + 2 * math.pi * j / N
            fase = (j / muestras) % 1.0                         # 0 = centro del lóbulo
            onda = 0.5 + 0.5 * math.cos(2 * math.pi * fase)     # 1 en el centro del lóbulo, 0 entre lóbulos
            lob = var[j // muestras]
            r = R * t * (0.86 + 0.14 * onda ** 0.6) * lob    # onda ** 0.6 => lóbulos anchos y redondos
            z = z_apex - alto * (1 - (1 - t) ** 1.3) * 0.9
            if t == domo: z = z_apex - alto * 0.035                # anillo del domo casi a la altura de la punta
            z -= caida * R * (t ** 2.2) * (0.4 + 0.6 * onda)     # el lóbulo cae un poco, sin punta
            fila.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        filas.append(fila)
    # borde enrollado hacia abajo/adentro: dos anillos más => el canto se ve redondo
    ult = filas[-1]
    rizo1 = [bm.verts.new((v.co.x * 0.97, v.co.y * 0.97, v.co.z - rizo * R * 0.6)) for v in ult]
    rizo2 = [bm.verts.new((v.co.x * 0.86, v.co.y * 0.86, v.co.z - rizo * R * 0.75)) for v in ult]
    centro = bm.verts.new((0, 0, z_rim + alto * 0.3))
    caras = []
    for j in range(N):
        f = bm.faces.new((apex, filas[0][j], filas[0][(j + 1) % N])); f.material_index = material(0, j, j // muestras, 0.1); caras.append(f)
    for k in range(len(filas) - 1):
        for j in range(N):
            f = bm.faces.new((filas[k][j], filas[k + 1][j], filas[k + 1][(j + 1) % N], filas[k][(j + 1) % N]))
            f.material_index = material(k + 1, j, j // muestras, (ts[k] + ts[k + 1]) / 2); caras.append(f)
    for a_, b_ in ((ult, rizo1), (rizo1, rizo2)):
        for j in range(N):
            f = bm.faces.new((a_[j], b_[j], b_[(j + 1) % N], a_[(j + 1) % N]))
            f.material_index = material(K, j, j // muestras, 1.0); caras.append(f)
    for j in range(N):
        f = bm.faces.new((rizo2[(j + 1) % N], rizo2[j], centro)); f.material_index = material(K + 1, j, j // muestras, 1.1); caras.append(f)
    for f in caras: f.smooth = True
    return caras


def pino_suave(me, H, R, niveles, lobulos, caida, nieve, seed, ancho_tronco=0.035, angosto=1.0, traslape=1.55):
    """Pino esponjoso. Materiales: 0 = tronco, 1 = verde, 2 = nieve (igual que el generador anterior)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    seg = 10
    anillos = []
    for z, r in ((-0.02, ancho_tronco * 1.8), (0.03, ancho_tronco * 1.15), (H * 0.35, ancho_tronco * 0.7)):
        anillos.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
    for a, b in zip(anillos, anillos[1:]):
        for j in range(seg):
            f = bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j])); f.material_index = 0; f.smooth = True
    zb = H * 0.13
    paso = (H - zb) / (niveles + traslape - 1)
    for i in range(niveles):
        frac = i / max(1, niveles - 1)
        Ri = R * (1.0 - frac * 0.8) ** angosto * (0.94 + rnd.random() * 0.12)
        ultimo = i == niveles - 1
        z_rim = zb + paso * i
        z_apex = H if ultimo else z_rim + paso * traslape
        nl = max(5, int(lobulos * (1.0 - frac * 0.35)))
        hay_nieve = [rnd.random() < nieve * 0.75 for _ in range(nl)]
        def mat(k, j, l, t, ultimo=ultimo, hay_nieve=hay_nieve):
            if ultimo and t < 0.2 + 0.25 * nieve: return 2            # gorrito de nieve en la punta
            if 0.35 < t < 0.75 and hay_nieve[l]: return 2             # almohadilla de nieve sobre el lóbulo
            return 1
        falda_suave(bm, z_apex, z_rim, Ri, nl, caida, rnd.random() * math.pi, seed * 31 + i, mat, K=5, muestras=3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me.clear_geometry(); bm.to_mesh(me); bm.free()
    for e in me.edges: e.use_edge_sharp = False
    me.update()


# ======================================================================================
# GRAN ÁRBOL (colección "Arbol"): Nivel1-3 = 2 faldas cada uno; materiales Arbol_Verde / Arbol_VerdeClaro.
# Alturas en coordenadas del mundo de Blender (z arriba). Cada Nivel tiene su origen en "origen".
NIVELES_ARBOL = {
    #           origen  (z_apex, z_rim, R, lóbulos, caída)
    "Nivel1": (1.5,  [(3.75, 1.35, 2.45, 12, 0.20), (3.35, 1.62, 2.12, 10, 0.18)]),
    "Nivel2": (2.9,  [(4.85, 2.72, 1.95, 10, 0.20), (4.50, 2.98, 1.66, 9, 0.18)]),
    "Nivel3": (4.15, [(5.85, 3.95, 1.38, 8, 0.22), (5.62, 4.20, 1.10, 7, 0.20)]),
}


def arbol_ramas():
    for nombre, (origen, faldas) in NIVELES_ARBOL.items():
        me = bpy.data.objects[nombre].data
        mats = [m.name for m in me.materials]
        osc, cla = mats.index("Arbol_Verde"), mats.index("Arbol_VerdeClaro")
        bm = bmesh.new()
        for i, (za, zr, R, lob, caida) in enumerate(faldas):
            rnd = random.Random(hash(nombre) % 1000 + i)
            def mat(k, j, l, t, rnd=rnd, lob=lob):
                # verde claro en el centro de los lóbulos del borde (donde "pega la luz") y unas manchas al azar
                return cla if (t > 0.7 and j % 3 == 0) or rnd.random() < 0.15 else osc
            falda_suave(bm, za - origen, zr - origen, R, lob, caida, i * math.pi / lob, 7 + i, mat, K=6, muestras=3, rizo=0.05)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()


def bvh_ramas():
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    for n in NIVELES_ARBOL:
        o = bpy.data.objects[n]; tmp = bmesh.new(); tmp.from_mesh(o.data); tmp.transform(o.matrix_world)
        m = bpy.data.meshes.new("tmp"); tmp.to_mesh(m); tmp.free(); bm.from_mesh(m); bpy.data.meshes.remove(m)
    bvh = BVHTree.FromBMesh(bm); bm.free()
    return bvh


def superficie(bvh, ang, z, extra=0.0):
    """Punto de la superficie del follaje a esa altura y ángulo: lanza un rayo desde afuera hacia el tronco."""
    d = Vector((math.cos(ang), math.sin(ang), 0))
    hit = bvh.ray_cast(Vector((0, 0, z)) + d * 4, -d)
    return (None, None) if hit[0] is None else (hit[0] + d * extra, d)


def recolocar_esferas(bvh, separacion=0.14):
    """Mueve cada Esfera_N (con su tapa y su racimo, que son hijos) hasta quedar apoyada en la superficie nueva."""
    for i in range(1, 7):
        o = bpy.data.objects[f"Esfera_{i}"]
        p = o.matrix_world.translation.copy()
        ang = math.atan2(p.y, p.x)
        q, d = superficie(bvh, ang, p.z, separacion)
        if q is None: continue
        delta = q - p
        o.location += delta if o.parent is None else o.parent.matrix_world.inverted().to_3x3() @ delta
        print(o.name, "movida", round(delta.length, 3), "m")


def guirnalda_espiral(bvh, vueltas=3.6, z0=1.55, z1=5.25, cada=0.3):
    """Cable + focos en espiral sobre la superficie (materiales: 4 focos + Arbol_Cable)."""
    from mathutils import Matrix
    g = bpy.data.objects["Guirnalda"]; me = g.data
    ic = [m.name for m in me.materials].index("Arbol_Cable")
    bm = bmesh.new(); pts = []
    n = 260
    for i in range(n + 1):
        t = i / n
        p, d = superficie(bvh, t * vueltas * 2 * math.pi, z0 + (z1 - z0) * t, 0.05)
        if p is not None: pts.append((p, d))
    def caras(r): return {f for v in r["verts"] for f in v.link_faces}
    for (a, _), (b, _) in zip(pts, pts[1:]):
        v = b - a
        if v.length < 1e-4: continue
        rot = v.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        r = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=0.012, radius2=0.012, depth=v.length, matrix=Matrix.Translation((a + b) / 2) @ rot)
        for f in caras(r): f.material_index = ic; f.smooth = True
    acum, k, ultimo = 0, 0, pts[0][0]
    for p, d in pts:
        acum += (p - ultimo).length; ultimo = p
        if acum < cada: continue
        acum = 0
        c = p + d * 0.04 + Vector((0, 0, -0.03))
        r = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.05, matrix=Matrix.Translation(c) @ Matrix.Diagonal((1, 1, 1.35, 1)))
        for f in caras(r): f.material_index = k % 4; f.smooth = True
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.026, radius2=0.026, depth=0.045, matrix=Matrix.Translation(c + Vector((0, 0, 0.075))))
        for f in caras(r): f.material_index = ic
        k += 1
    bm.transform(g.matrix_world.inverted())
    me.clear_geometry(); bm.to_mesh(me); bm.free()
    print("guirnalda: focos", k)


def estrella_inflada(me, R1=0.48, R2=0.22, prof=0.14, soporte=True, escala=1.0):
    """Estrella de 5 puntas redondeadas y abombada (como galleta/peluche), sombreado suave.
    El contorno se suaviza con Chaikin (cada pasada corta las esquinas => puntas redondas).
    Mira hacia -Y de Blender (= +Z... el frente de la escena); 'soporte' agrega el cono que abraza la punta del árbol."""
    from mathutils import Matrix
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = R1 if i % 2 == 0 else R2
        pts.append(Vector((r * math.cos(a), r * math.sin(a))))
    for _ in range(3):                                   # Chaikin x3
        nuevo = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            nuevo += [p * 0.75 + q * 0.25, p * 0.25 + q * 0.75]
        pts = nuevo
    bm = bmesh.new()
    # anillos: borde (grosor delgado) -> 2 anillos intermedios inflados -> centro
    capas = [(1.0, 0.25), (0.8, 0.7), (0.5, 0.92), (0.22, 1.0)]   # (escala del contorno, fracción de la profundidad)
    def anillo(s, h, lado):
        return [bm.verts.new((p.x * s * escala, lado * prof * h * escala, p.y * s * escala)) for p in pts]
    n = len(pts)
    borde_f = None
    for lado in (-1, 1):
        filas = [anillo(s, h, lado) for s, h in capas]
        centro = bm.verts.new((0, lado * prof * 1.05 * escala, 0))
        for a, b in zip(filas, filas[1:]):
            for j in range(n):
                f = bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j])); f.smooth = True
        for j in range(n):
            f = bm.faces.new((filas[-1][j], filas[-1][(j + 1) % n], centro)); f.smooth = True
        if borde_f is None: borde_f = filas[0]
        else:
            for j in range(n):   # costura entre el frente y la espalda
                f = bm.faces.new((borde_f[j], filas[0][j], filas[0][(j + 1) % n], borde_f[(j + 1) % n])); f.smooth = True
    if soporte:
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.09 * escala, radius2=0.05 * escala, depth=0.25 * escala,
                                  matrix=Matrix.Translation((0, 0, -0.42 * escala)))
        for f in {f for v in r["verts"] for f in v.link_faces}: f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()


# ======================================================================================
# PERSONAJES Y PROPS (modelos hechos con cajas/cilindros biselados)
def suavizar_normales(o, angulo_filo=70, peso=50):
    """Sin agregar triángulos: quita la marca 'sharp' a las aristas del bisel (ángulo < angulo_filo) y agrega el
    modificador Weighted Normal (por área de cara): las caras grandes conservan su normal plana y las del bisel
    se sombrean curvas => la esquina se ve REDONDA. glTF exporta estas normales personalizadas."""
    me = o.data
    for p in me.polygons: p.use_smooth = True
    bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0) < math.radians(angulo_filo)
    bm.to_mesh(me); bm.free()
    m = o.modifiers.get("NormalesSuaves") or o.modifiers.new("NormalesSuaves", 'WEIGHTED_NORMAL')
    m.mode = 'FACE_AREA'; m.weight = peso; m.keep_sharp = True


def redondear(o, niveles=1):
    """Redondeo de verdad: Subdivision Surface (Catmull-Clark). El bisel que ya tiene el modelo actúa como
    'borde de apoyo' y la esquina queda redondeada sin deformar todo el objeto. Multiplica los triángulos x4."""
    for e in o.data.edges: e.use_edge_sharp = False
    for p in o.data.polygons: p.use_smooth = True
    m = o.modifiers.get("Redondeo") or o.modifiers.new("Redondeo", 'SUBSURF')
    m.levels = niveles; m.render_levels = niveles
    # el subsurf debe ir ANTES de las normales ponderadas
    if "NormalesSuaves" in o.modifiers:
        o.modifiers.move(o.modifiers.find("Redondeo"), 0)


def islas_de(bm):
    """Grupos de caras conectadas (cada caja/cilindro del Builder es una isla de UN solo material)."""
    vistos = set(); res = []
    for f in bm.faces:
        if f.index in vistos: continue
        pila = [f]; isla = []
        while pila:
            g = pila.pop()
            if g.index in vistos: continue
            vistos.add(g.index); isla.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in vistos: pila.append(h)
        res.append(isla)
    return res


def corregir_bisel(o):
    """El biselado de la noche del 23 dejó las caras NUEVAS del bisel con el material del slot 0.
    En cada isla cuyo material principal (por área) NO es el slot 0, esas caras toman el material de su isla."""
    from collections import defaultdict
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); n = 0
    for isla in islas_de(bm):
        area = defaultdict(float)
        for f in isla: area[f.material_index] += f.calc_area()
        dom = max(area, key=area.get)
        if dom == 0: continue
        for f in isla:
            if f.material_index == 0: f.material_index = dom; n += 1
    bm.to_mesh(me); bm.free()
    return n


def regalo_bonito(o, seed=5):
    """Regalo clásico en UNA malla (origen en la base, 1 x 1 x ~1.25 con moño). Materiales:
    0 = papel (Regalo_Rojo), 1 = listón (Regalo_Oro), 2 = lunares (Regalo_Lunar).
    En Unity el script ColorRegalo cambia los colores de papel/listón por instancia."""
    from mathutils import Matrix
    rnd = random.Random(seed)
    me = o.data
    lunar = bpy.data.materials.get("Regalo_Lunar") or bpy.data.materials.new("Regalo_Lunar")
    lunar.use_nodes = True
    b = next(n for n in lunar.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.95, 0.92, 0.85, 1); b.inputs["Roughness"].default_value = 0.6
    me.materials.clear()
    for n in ("Regalo_Rojo", "Regalo_Oro", "Regalo_Lunar"): me.materials.append(bpy.data.materials[n])
    bm = bmesh.new()
    def caras(r): return {f for v in r["verts"] for f in v.link_faces}
    def caja(c, s, mat, bisel):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]: v.co = Vector((v.co.x * s[0] + c[0], v.co.y * s[1] + c[1], v.co.z * s[2] + c[2]))
        aristas = list({e for v in r["verts"] for e in v.link_edges})
        bmesh.ops.bevel(bm, geom=aristas + r["verts"], offset=bisel, segments=3, affect='EDGES', profile=0.5)
    def pintar(fs, mat):
        for f in fs: f.material_index = mat; f.smooth = True
    antes = set(bm.faces)
    caja((0, 0, 0.4), (0.94, 0.94, 0.8), 0, 0.04); pintar(set(bm.faces) - antes, 0); antes = set(bm.faces)
    caja((0, 0, 0.89), (1.0, 1.0, 0.2), 0, 0.035); pintar(set(bm.faces) - antes, 0); antes = set(bm.faces)   # tapa
    # listones: dos bandas en cruz que rodean caja + tapa
    for sx, sy in ((0.16, 1.03), (1.03, 0.16)):
        caja((0, 0, 0.4), (sx, sy * 0.94 / 1.0 + 0.0, 0.81), 1, 0.012); pintar(set(bm.faces) - antes, 1); antes = set(bm.faces)
        caja((0, 0, 0.89), (sx if sx < 1 else 1.04, sy if sy < 1 else 1.04, 0.215), 1, 0.012); pintar(set(bm.faces) - antes, 1); antes = set(bm.faces)
    # lunares en los 4 costados de la caja (discos aplanados)
    for lado in range(4):
        ang = lado * math.pi / 2
        n = Vector((math.cos(ang), math.sin(ang), 0)); t = Vector((-n.y, n.x, 0))
        puestos = []
        intentos = 0
        while len(puestos) < 4 and intentos < 200:      # sorteo con distancia mínima: los lunares no se enciman
            intentos += 1
            u = rnd.choice([-1, 1]) * rnd.uniform(0.17, 0.38); z = rnd.uniform(0.12, 0.68)
            if any((u - u2) ** 2 + (z - z2) ** 2 < 0.19 ** 2 for u2, z2 in puestos): continue
            puestos.append((u, z))
        for u, z in puestos:
            c = n * 0.472 + t * u + Vector((0, 0, z))
            rot = n.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            r = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.055, radius2=0.05, depth=0.012, matrix=Matrix.Translation(c) @ rot)
            pintar(caras(r), 2)
    # moño: 4 lazos (esferas aplastadas) + nudo
    ztop = 1.0
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
        for v in r["verts"]:
            p = v.co.copy()
            # lazo = esfera aplanada y estirada hacia afuera, inclinada hacia arriba
            loc = d * (0.2 + p.x * 0.19) + Vector((-d.y, d.x, 0)) * (p.y * 0.1) + Vector((0, 0, ztop + 0.13 + p.x * 0.11 + p.z * 0.06))
            v.co = loc
        pintar(caras(r), 1)
    r = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=0.1, matrix=Matrix.Translation((0, 0, ztop + 0.1)))
    pintar(caras(r), 1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()
    for h in list(o.children): bpy.data.objects.remove(h)   # listones/moño viejos (ahora todo va en una malla)
    for m in list(o.modifiers): o.modifiers.remove(m)
