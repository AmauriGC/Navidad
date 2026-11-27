# -*- coding: utf-8 -*-
"""
PINOS v2 (exterior) — estilo "tarjetas" optimizado para juegos.
  - Tronco: PRISMA TRIANGULAR (triángulo extruido, 8 triángulos) con textura de corteza + normal map.
  - Follaje: varios "pisos" apilados; cada piso = 3 PLANOS cruzados a 60° con una textura de rama con
    transparencia (alpha recortado). Los pisos se hacen más angostos hacia arriba => forma de pino.
  - Texturas 512x512 generadas con numpy:
        Pino_Corteza_Albedo / Pino_Corteza_Normal
        Pino_Hojas_Albedo (RGBA) / Pino_Hojas_Normal
        Pino_HojasNieve_Albedo (RGBA) / Pino_HojasNieve_Normal   (las mismas ramas con nieve encima)
  - Luces (solo para ALGUNOS pinos): cable = cajas muy delgadas (material negro, sin normal map) en espiral,
    focos = icoesferas de 20 caras con materiales EMISIVOS de colores fuertes (con Bloom se ven brillar).
Mismas medidas que los pinos viejos (alto ~0.9, origen en la base; en el juego cada pino se escala ~7x).
Uso: exec(modelado.py); exec(pinos_v2.py)  -> Assets/Modelos/Pinos_v2.glb  (objetos PinoV2_* y LucesPino_*)
"""
import bpy, bmesh, math, random, os
import numpy as np
from mathutils import Vector, Matrix

N = 512
TEX = PROYECTO + "/Assets/Texturas"; os.makedirs(TEX, exist_ok=True)
ys, xs = np.mgrid[0:N, 0:N]
X = (xs + 0.5) / N; Y = (ys + 0.5) / N

def ruido(escala, semilla, ex=X, ey=Y):
    g = np.random.default_rng(semilla).random((escala + 2, escala + 2))
    x = ex * escala; y = ey * escala
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    x0 = np.clip(x0, 0, escala); y0 = np.clip(y0, 0, escala)
    return (g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx) * (1 - fy) + (g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx) * fy

def ruido2(fx, fy, semilla, ex, ey):
    """Ruido con escala distinta en cada eje (sirve para hacer 'rayitas' alargadas como agujas)."""
    g = np.random.default_rng(semilla).random((fy + 2, fx + 2))
    x = (ex % 1.0) * fx; y = (ey % 1.0) * fy
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    tx = x - x0; ty = y - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
    return (g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx) * (1 - ty) + (g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx) * ty

def normal_desde_altura(h, fuerza):
    dx = np.gradient(h, axis=1) * N / 128 * fuerza
    dy = np.gradient(h, axis=0) * N / 128 * fuerza
    n = np.dstack((-dx, -dy, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5

def guardar(nombre, rgb, alfa=None, lineal=False):
    img = bpy.data.images.get(nombre)
    if img: bpy.data.images.remove(img)
    img = bpy.data.images.new(nombre, N, N, alpha=alfa is not None)
    if lineal: img.colorspace_settings.name = "Non-Color"
    a = alfa if alfa is not None else np.ones((N, N))
    img.pixels.foreach_set(np.dstack((np.clip(rgb, 0, 1), a)).astype(np.float32).ravel())
    img.filepath_raw = f"{TEX}/{nombre}.png"; img.file_format = "PNG"; img.save()
    return img

# ------------------------------------------------------------------ CORTEZA
surco = ruido(40, 3)
fase = X * 2 * math.pi * 7 + surco * 4 + ruido(8, 4) * 3
h_cor = np.abs(np.sin(fase)) ** 0.6 * 0.7 + ruido(120, 5) * 0.25 - (np.abs(np.sin(Y * 37 + X * 5)) > 0.97) * 0.3
c1 = np.array([0.2, 0.12, 0.07]); c2 = np.array([0.42, 0.28, 0.17])
alb_cor = c1 + (c2 - c1) * h_cor[..., None].clip(0, 1)
I_COR = guardar("Pino_Corteza_Albedo", alb_cor)
I_COR_N = guardar("Pino_Corteza_Normal", normal_desde_altura(h_cor, 2.5), lineal=True)

# ------------------------------------------------------------------ RAMAS (con y sin nieve)
d = np.abs(X - 0.5)                                       # distancia al centro (tronco)
ARRIBA, ABAJO = 0.985, 0.04
w = 0.49 * np.clip((ARRIBA - Y) / (ARRIBA - ABAJO), 0, 1) ** 0.9   # medio ancho del triángulo a esa altura
g = ((Y + d * 0.8) * 6.0) % 1.0                           # "chevrones": cada banda es una rama que cae hacia afuera
fleco = 0.018 * np.sin(Y * 420 + d * 90) + 0.012 * (ruido(90, 6) - 0.5)
w_rama = w * (0.8 + 0.28 * np.sin(np.pi * np.clip(1 - g, 0, 1)) ** 0.6) + fleco    # las puntas de cada rama sobresalen
# agujas: rayitas alargadas en la dirección de la rama (ruido estirado), en vez de una onda regular
a_perp = (Y - d * 1.25) * 0.5 + 0.5                       # coordenada perpendicular a las agujas
a_larg = d * 2.0
agujas = np.clip((ruido2(170, 1, 7, a_larg, a_perp) * 0.0 + ruido2(14, 230, 7, a_larg, a_perp)) * 1.6 - 0.3, 0, 1)
# orilla de abajo de cada rama con FLECO de agujas: huecos entre ramas, solo cuelgan las puntas
fleco_abajo = 0.2 * (1 - agujas) + 0.03
alfa = ((d < w_rama) & (Y > ABAJO) & (Y < ARRIBA) & ((g > fleco_abajo) | (d < 0.035))).astype(float)
cresta = np.sin(np.pi * np.clip(g, 0, 1)) ** 0.7                                      # cada rama abombada
punta = np.clip(d / np.maximum(w, 1e-3), 0, 1)                                         # 0 centro, 1 orilla
h_hoj = cresta * (0.55 + 0.45 * punta) + agujas * 0.18
v_osc = np.array([0.04, 0.16, 0.09]); v_cla = np.array([0.14, 0.4, 0.2])
mezcla = np.clip(0.25 + 0.45 * punta + 0.3 * (1 - g) - 0.25 * (1 - agujas), 0, 1)
alb_hoj = (v_osc + (v_cla - v_osc) * mezcla[..., None]) * (0.75 + 0.25 * cresta[..., None])
I_HOJ = guardar("Pino_Hojas_Albedo", alb_hoj, alfa)
I_HOJ_N = guardar("Pino_Hojas_Normal", normal_desde_altura(h_hoj, 1.1), lineal=True)

# nieve: sobre la parte de ARRIBA de cada rama (g chico) y más en las puntas, con bordes irregulares
borde_nieve = 0.2 + 0.1 * ruido(50, 8) + 0.08 * punta
nieve = np.clip((borde_nieve + fleco_abajo - g) * 25, 0, 1) * alfa
nieve = np.maximum(nieve, np.clip((Y - 0.9) * 20, 0, 1) * alfa)                       # la puntita del piso nevada
grumos = ruido(70, 9) * 0.6 + ruido(160, 10) * 0.4
blanco = np.array([0.86, 0.9, 0.98]); azul = np.array([0.62, 0.7, 0.88])
alb_nie = blanco + (azul - blanco) * (1 - grumos[..., None]) * 0.6
alb_nev = alb_hoj * (1 - nieve[..., None]) + alb_nie * nieve[..., None]
h_nev = h_hoj * (1 - nieve) + nieve * (1.0 + grumos * 0.35)
I_NEV = guardar("Pino_HojasNieve_Albedo", alb_nev, alfa)
I_NEV_N = guardar("Pino_HojasNieve_Normal", normal_desde_altura(h_nev, 1.1), lineal=True)

# ------------------------------------------------------------------ MATERIALES
def mat_textura(nombre, img_alb, img_nrm, rug, recorte=False):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ta = nt.nodes.new("ShaderNodeTexImage"); ta.image = img_alb
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img_nrm
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(ta.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rug
    if recorte:
        # "alpha clip": Round(alfa) => 0 o 1. El exportador glTF lo reconoce como alphaMode = MASK
        rd = nt.nodes.new("ShaderNodeMath"); rd.operation = "ROUND"
        nt.links.new(ta.outputs["Alpha"], rd.inputs[0]); nt.links.new(rd.outputs[0], b.inputs["Alpha"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    m.use_backface_culling = False            # los planos se ven por los dos lados (glTF doubleSided)
    return m

def mat_color(nombre, color, emision=0.0, rug=0.15):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rug
    if emision:
        b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emision
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m

M_COR = mat_textura("Pino_Corteza", I_COR, I_COR_N, 0.9)
M_HOJ = mat_textura("Pino_Hojas", I_HOJ, I_HOJ_N, 0.75, recorte=True)
M_NEV = mat_textura("Pino_HojasNieve", I_NEV, I_NEV_N, 0.6, recorte=True)
M_CABLE = mat_color("Pino_Cable", (0.0, 0.0, 0.0), rug=0.6)   # solo color negro, sin texturas ni normal map
FOCOS = [mat_color("FocoPino_Rojo", (1.0, 0.05, 0.08), 9), mat_color("FocoPino_Verde", (0.1, 1.0, 0.25), 9),
         mat_color("FocoPino_Azul", (0.15, 0.35, 1.0), 10), mat_color("FocoPino_Amarillo", (1.0, 0.75, 0.1), 8),
         mat_color("FocoPino_Rosa", (1.0, 0.2, 0.7), 9)]

# ------------------------------------------------------------------ GEOMETRÍA
TIPOS = {
    #            alto,  radio, pisos, pisos de arriba con nieve, radio tronco
    "Abeto":   (0.94, 0.40, 6, 2, 0.035),
    "Picea":   (0.88, 0.28, 7, 3, 0.028),
    "Nevado":  (0.88, 0.50, 5, 5, 0.04),
    "Joven":   (0.82, 0.37, 5, 1, 0.03),
}

def pisos(H, R, n):
    """(z_abajo, alto, medio_ancho) de cada piso."""
    z0 = 0.12 * H
    alto = (H - z0) * 1.75 / n
    paso = (H - z0 - alto) / (n - 1)
    return [(z0 + i * paso, alto, R * (1.05 - 0.72 * i / (n - 1))) for i in range(n)]

def pino(bm, uvl, H, R, n, n_nieve, rt, semilla):
    rnd = random.Random(semilla)
    # tronco: prisma triangular (3 lados + tapas)
    alto_t = 0.42 * H
    abajo = [Vector((math.cos(a) * rt, math.sin(a) * rt, -0.02)) for a in (0, 2.094, 4.189)]
    arriba = [Vector((p.x * 0.6, p.y * 0.6, alto_t)) for p in abajo]
    for k in range(3):
        j = (k + 1) % 3
        f = bm.faces.new([bm.verts.new(abajo[k]), bm.verts.new(abajo[j]), bm.verts.new(arriba[j]), bm.verts.new(arriba[k])])
        for lp, uv in zip(f.loops, ((k / 3, 0), ((k + 1) / 3, 0), ((k + 1) / 3, 2), (k / 3, 2))): lp[uvl].uv = uv
        f.material_index = 0
    for cara in (arriba, list(reversed(abajo))):
        f = bm.faces.new([bm.verts.new(p) for p in cara]); f.material_index = 0
        for lp, uv in zip(f.loops, ((0.1, 0.1), (0.5, 0.9), (0.9, 0.1))): lp[uvl].uv = uv
    # follaje: pisos de 3 planos cruzados
    for i, (zb, alto, w) in enumerate(pisos(H, R, n)):
        giro = rnd.uniform(0, math.pi / 3)
        mat = 2 if i >= n - n_nieve else 1
        for k in range(3):
            a = giro + k * math.pi / 3
            dx, dy = math.cos(a) * w, math.sin(a) * w
            vs = [Vector((-dx, -dy, zb)), Vector((dx, dy, zb)), Vector((dx, dy, zb + alto)), Vector((-dx, -dy, zb + alto))]
            f = bm.faces.new([bm.verts.new(v) for v in vs]); f.material_index = mat
            for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv

def caja_entre(bm, a, b, grosor, mat):
    """Cubo extruido muy delgado de a a b (el cable)."""
    a, b = Vector(a), Vector(b); v = b - a
    if v.length < 1e-6: return
    rot = v.to_track_quat("Z", "Y").to_matrix().to_4x4()
    M = Matrix.Translation((a + b) / 2) @ rot @ Matrix.Diagonal((grosor, grosor, v.length, 1))
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    for f in {f for vv in r["verts"] for f in vv.link_faces}: f.material_index = mat

def luces(bm, H, R, n, semilla):
    """Espiral de cable con focos alrededor del pino (en coordenadas del pino)."""
    rnd = random.Random(semilla)
    P = pisos(H, R, n)
    z0, z1 = P[0][0] + 0.03 * H, H * 0.9
    vueltas, pasos = 3.5, 84
    pts = []
    for i in range(pasos + 1):
        t = i / pasos
        z = z0 + (z1 - z0) * t
        # radio del follaje a esa altura (interpolando la orilla de los pisos), un poco hacia adentro
        r = R * (1.0 - 0.8 * (z - z0) / (H - z0)) * 0.72
        a = t * vueltas * 2 * math.pi + semilla
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, z - 0.012 * abs(math.sin(t * vueltas * 2 * math.pi * 2)))))
    for p, q in zip(pts, pts[1:]): caja_entre(bm, p, q, 0.0016, 5)
    for i, p in enumerate(pts[::2]):
        r = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.0085)
        for v in r["verts"]: v.co = Vector((v.co.x, v.co.y, v.co.z * 1.35)) + p - Vector((0, 0, 0.012))
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = i % 5; f.smooth = True

col = bpy.data.collections.get("PinosV2") or bpy.data.collections.new("PinosV2")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)

def objeto(nombre, mats, construir):
    viejo = bpy.data.objects.get(nombre)
    if viejo: bpy.data.objects.remove(viejo, do_unlink=True)
    for me_v in [m for m in bpy.data.meshes if m.name == nombre or m.name.startswith(nombre + ".")]:
        bpy.data.meshes.remove(me_v)          # la malla vieja también (si no, la nueva se llamaría "X.001")
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    construir(bm, uvl)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    return o

creados = []
for k, (tipo, (H, R, n, nn, rt)) in enumerate(TIPOS.items()):
    o = objeto("PinoV2_" + tipo, [M_COR, M_HOJ, M_NEV], lambda bm, uvl: pino(bm, uvl, H, R, n, nn, rt, k * 13))
    l = objeto("LucesPino_" + tipo, FOCOS + [M_CABLE], lambda bm, uvl: luces(bm, H, R, n, k * 1.7))
    o.location = l.location = (-20 - k * 2, 20, 0)
    creados += [o, l]
    print(tipo, "pino tris:", sum(len(p.vertices) - 2 for p in o.data.polygons), "| luces tris:", sum(len(p.vertices) - 2 for p in l.data.polygons))

for o in creados: o.location = (0, 0, 0)
exportar_glb(creados, "Pinos_v2.glb")
for k, o in enumerate(creados): o.location = (-20 - (k // 2) * 2, 20, 0)
print("pinos v2 exportados")
