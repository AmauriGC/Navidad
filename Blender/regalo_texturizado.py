# -*- coding: utf-8 -*-
"""
REGALO TEXTURIZADO (low-poly + texturas).
Idea de optimización: la MALLA es muy sencilla (caja, tapa y un moño de tiras planas) y todo el detalle
va en las TEXTURAS de un solo "atlas" de 1024 x 1024:
  - Regalo_Albedo.png : color (papel rojo con estrellas doradas, listón verde con orillas doradas, moño satinado).
  - Regalo_Normal.png : normal map (formato OpenGL / glTF). Se calcula a partir de un MAPA DE ALTURA:
                        grano del papel, listón en relieve, estrellas grabadas y BORDES REDONDEADOS falsos
                        (la caja no tiene bisel en la malla; el normal map hace que la luz "crea" que sí).
  - Regalo_ORM.png    : R = oclusión, G = rugosidad, B = metálico (convención glTF): el oro brilla, el papel es mate.
Atlas (u, v):
  P = lados de la caja   [0.0-0.5] x [0.5-1.0]   (papel + listón vertical al centro)
  T = tapa de arriba     [0.5-1.0] x [0.5-1.0]   (papel + listón en cruz)
  L = lados de la tapa   [0.0-1.0] x [0.36-0.5]  (papel + listón + orilla dorada)
  R = listón del moño    [0.0-1.0] x [0.0-0.34]  (satín verde con orillas doradas)
Uso: exec(modelado.py); exec(regalo_texturizado.py)
"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector

N = 1024
TEX = PROYECTO + "/Assets/Texturas"
import os; os.makedirs(TEX, exist_ok=True)

REG = {"P": (0.0, 0.5, 0.5, 1.0), "T": (0.5, 1.0, 0.5, 1.0), "L": (0.0, 1.0, 0.36, 0.5), "R": (0.0, 1.0, 0.0, 0.34)}

# ------------------------------------------------------------------ TEXTURAS (numpy)
ys, xs = np.mgrid[0:N, 0:N]
U = (xs + 0.5) / N; V = (ys + 0.5) / N          # fila 0 = v pequeña (las imágenes de Blender empiezan abajo)
rng = np.random.default_rng(7)

def ruido(escala, semilla):
    """Ruido suave: rejilla aleatoria pequeña agrandada con interpolación bilineal."""
    g = np.random.default_rng(semilla).random((escala + 1, escala + 1))
    x = U * escala; y = V * escala
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    x0 = np.clip(x0, 0, escala - 1); y0 = np.clip(y0, 0, escala - 1)
    a = g[y0, x0]; b = g[y0, x0 + 1]; c = g[y0 + 1, x0]; d = g[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def local(reg):
    u0, u1, v0, v1 = REG[reg]
    m = (U >= u0) & (U < u1) & (V >= v0) & (V < v1)
    return m, (U - u0) / (u1 - u0), (V - v0) / (v1 - v0)

def borde_suave(lu, lv, ancho_u, ancho_v):
    """0 en la orilla de la región -> 1 hacia adentro (curva redonda): simula el bisel en el normal map."""
    eu = np.clip(np.minimum(lu, 1 - lu) / ancho_u, 0, 1); ev = np.clip(np.minimum(lv, 1 - lv) / ancho_v, 0, 1)
    return np.sqrt(1 - (1 - np.minimum(eu, ev)) ** 2)

ROJO = np.array([0.62, 0.05, 0.07]); ROJO2 = np.array([0.45, 0.03, 0.05])
ORO = np.array([1.0, 0.76, 0.3]); VERDE = np.array([0.04, 0.36, 0.16]); VERDE2 = np.array([0.1, 0.55, 0.26])

alb = np.zeros((N, N, 3)); alt = np.zeros((N, N)); rug = np.full((N, N), 0.8); met = np.zeros((N, N)); ao = np.ones((N, N))
grano = ruido(180, 1) * 0.6 + ruido(60, 2) * 0.4

def estrellas(lu, lv, celdas):
    """Estrellitas de 5 puntas en rejilla escalonada. Devuelve máscara 0..1 con orilla suave."""
    x = lu * celdas; y = lv * celdas
    fila = np.floor(y)
    x = x + 0.5 * (fila % 2)
    cx = x - np.floor(x) - 0.5; cy = y - fila - 0.5
    r = np.hypot(cx, cy); a = np.arctan2(cy, cx) + (fila % 3) * 0.4
    radio = 0.17 * (0.62 + 0.38 * np.cos(5 * a))
    return np.clip((radio - r) * 60, 0, 1)

def papel(reg, celdas, ancho_bisel_u, ancho_bisel_v, liston_u=None, liston_v=None, ancho_liston=0.1):
    m, lu, lv = local(reg)
    base = ROJO[None, None, :] * (1 - grano[..., None] * 0.25) + ROJO2 * (grano[..., None] * 0.25)
    rayas = (np.sin((lu + lv) * 60) > 0.6).astype(float) * 0.08                      # rayitas diagonales tenues
    col = base * (1 - rayas[..., None])
    est = estrellas(lu, lv, celdas)
    col = col * (1 - est[..., None]) + ORO * est[..., None]
    h = grano * 0.04 + est * 0.12
    r_ = 0.75 - est * 0.45; me = est * 0.9
    # listón (vertical y/o horizontal) con orillas doradas
    lis = np.zeros_like(lu)
    for centro, coord in ((liston_u, lu), (liston_v, lv)):
        if centro is None: continue
        d = np.abs(coord - centro)
        dentro = np.clip((ancho_liston - d) * 400, 0, 1)
        orilla = dentro * np.clip((d - (ancho_liston - 0.014)) * 400, 0, 1)
        lis = np.maximum(lis, dentro)
        satin = 0.5 + 0.5 * np.sin(coord * 0 + (lv if coord is lu else lu) * 0 + d * 900)
        c_lis = VERDE * (1 - satin[..., None] * 0.3) + VERDE2 * (satin[..., None] * 0.3)
        c_lis = c_lis * (1 - orilla[..., None]) + ORO * orilla[..., None]
        col = col * (1 - dentro[..., None]) + c_lis * dentro[..., None]
        h = h + dentro * 0.35 + orilla * 0.05 + dentro * satin * 0.02
        r_ = r_ * (1 - dentro) + dentro * (0.35 - orilla * 0.1)
        me = me * (1 - dentro) + orilla * 0.9
    bis = borde_suave(lu, lv, ancho_bisel_u, ancho_bisel_v)
    h = h * bis + bis * 0.6
    occl = 0.55 + 0.45 * bis
    alb[m] = (col * occl[..., None])[m]; alt[m] = h[m]; rug[m] = r_[m]; met[m] = me[m]; ao[m] = occl[m]

papel("P", 7, 0.025, 0.03, liston_u=0.5, ancho_liston=0.1)
papel("T", 7, 0.025, 0.025, liston_u=0.5, liston_v=0.5, ancho_liston=0.1)
papel("L", 22, 0.02, 0.12, liston_u=0.5, ancho_liston=0.05)
# orilla dorada abajo de la tapa (región L, parte baja)
m, lu, lv = local("L")
o = np.clip((0.16 - lv) * 80, 0, 1) * m
alb[:] = alb * (1 - o[..., None]) + ORO * o[..., None]; met[:] = np.maximum(met, o * 0.9); rug[:] = rug * (1 - o) + 0.3 * o
alt[:] = alt + o * 0.08

# R: satín del moño
m, lu, lv = local("R")
satin = 0.5 + 0.5 * np.sin(lv * 260 + np.sin(lu * 9) * 2)
brillo = 0.5 + 0.5 * np.sin(lu * 12)
col = VERDE * (1 - brillo[..., None] * 0.4) + VERDE2 * (brillo[..., None] * 0.4)
orilla = np.clip((0.09 - np.minimum(lv, 1 - lv)) * 200, 0, 1)
col = col * (1 - orilla[..., None]) + ORO * orilla[..., None]
alb[m] = col[m]; alt[m] = (satin * 0.03 + orilla * 0.15 + borde_suave(lu, lv, 0.001, 0.05) * 0.2)[m]
rug[m] = (0.32 - orilla * 0.1)[m]; met[m] = (orilla * 0.9)[m]; ao[m] = 1

# normal map desde la altura (diferencias finitas) -> RGB en [0,1]  (glTF: verde = +V, convención OpenGL)
fuerza = 6.0
dx = np.gradient(alt, axis=1) * N / 256 * fuerza
dy = np.gradient(alt, axis=0) * N / 256 * fuerza
nrm = np.dstack((-dx, -dy, np.ones_like(alt)))
nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
nrm_rgb = nrm * 0.5 + 0.5
orm = np.dstack((ao, rug, met))

def guardar(nombre, rgb, lineal):
    img = bpy.data.images.get(nombre)
    if img: bpy.data.images.remove(img)
    img = bpy.data.images.new(nombre, N, N, alpha=False)
    if lineal: img.colorspace_settings.name = "Non-Color"
    px = np.dstack((np.clip(rgb, 0, 1), np.ones((N, N)))).astype(np.float32)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = f"{TEX}/{nombre}.png"; img.file_format = "PNG"; img.save()
    return img

# los colores de arriba ya están pensados en sRGB (como en un programa de dibujo): se guardan tal cual
I_ALB = guardar("Regalo_Albedo", alb, False)
I_NRM = guardar("Regalo_Normal", nrm_rgb, True)
I_ORM = guardar("Regalo_ORM", orm, True)

# ------------------------------------------------------------------ MATERIAL
mat = bpy.data.materials.get("Regalo_Texturizado") or bpy.data.materials.new("Regalo_Texturizado")
mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
t_alb = nt.nodes.new("ShaderNodeTexImage"); t_alb.image = I_ALB
t_nrm = nt.nodes.new("ShaderNodeTexImage"); t_nrm.image = I_NRM
t_orm = nt.nodes.new("ShaderNodeTexImage"); t_orm.image = I_ORM
sep = nt.nodes.new("ShaderNodeSeparateColor"); nmap = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(t_alb.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(t_orm.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
nt.links.new(t_nrm.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
for i, n in enumerate((t_alb, t_orm, t_nrm)): n.location = (-700, 300 - i * 300)
sep.location = (-350, 0); nmap.location = (-350, -300); bsdf.location = (0, 0); out.location = (300, 0)

# ------------------------------------------------------------------ MALLA LOW-POLY con UVs a mano
bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")

def quad(p, reg, sub=(0, 1, 0, 1)):
    """Cara de 4 vértices p[0..3] (antihorario visto desde afuera: abajo-izq, abajo-der, arriba-der, arriba-izq)
    mapeada al rectángulo 'sub' (fracción) de la región 'reg' del atlas."""
    u0, u1, v0, v1 = REG[reg]
    a0, a1, b0, b1 = sub
    cu = [u0 + (u1 - u0) * a0, u0 + (u1 - u0) * a1]; cv = [v0 + (v1 - v0) * b0, v0 + (v1 - v0) * b1]
    vs = [bm.verts.new(q) for q in p]
    f = bm.faces.new(vs)
    for loop, uv in zip(f.loops, ((cu[0], cv[0]), (cu[1], cv[0]), (cu[1], cv[1]), (cu[0], cv[1]))):
        loop[uvl].uv = uv
    return f

def caja(c, tam, regiones):
    """Caja con UVs: regiones = {'lado': reg, 'arriba': reg, 'abajo': reg}."""
    x, y, z = c; sx, sy, sz = (t / 2 for t in tam)
    P = lambda i, j, k: (x + i * sx, y + j * sy, z + k * sz)
    lados = [((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))]
    for (a, b) in lados:
        quad([P(a[0], a[1], -1), P(b[0], b[1], -1), P(b[0], b[1], 1), P(a[0], a[1], 1)], regiones["lado"])
    quad([P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1)], regiones["arriba"])
    quad([P(-1, 1, -1), P(1, 1, -1), P(1, -1, -1), P(-1, -1, -1)], regiones["abajo"])

caja((0, 0, 0.21), (0.6, 0.6, 0.42), {"lado": "P", "arriba": "P", "abajo": "P"})          # cuerpo
caja((0, 0, 0.465), (0.645, 0.645, 0.11), {"lado": "L", "arriba": "T", "abajo": "L"})      # tapa

def tira(camino, ancho, grosor=0.008, normal_ref=Vector((0, 0, 1)), lado_fijo=None):
    """Listón plano a lo largo de 'camino' (pocas caras): sección rectangular ancho x grosor, UV a lo largo en R."""
    n = len(camino)
    largo = [0.0]
    for a, b in zip(camino, camino[1:]): largo.append(largo[-1] + (Vector(b) - Vector(a)).length)
    anillos = []
    for i, p in enumerate(camino):
        p = Vector(p)
        t = (Vector(camino[min(i + 1, n - 1)]) - Vector(camino[max(i - 1, 0)])).normalized()
        if lado_fijo is not None:
            lado = (lado_fijo - t * lado_fijo.dot(t)).normalized()      # el ancho apunta a una dirección fija
        else:
            lado = t.cross(normal_ref).normalized() if abs(t.dot(normal_ref)) < 0.95 else Vector((1, 0, 0))
        arriba = lado.cross(t).normalized()
        w, g = lado * ancho / 2, arriba * grosor / 2
        anillos.append([p - w - g, p + w - g, p + w + g, p - w + g])
    for i in range(n - 1):
        u_a = largo[i] / largo[-1]; u_b = largo[i + 1] / largo[-1]
        A, Bn = anillos[i], anillos[i + 1]
        for k in range(4):
            j = (k + 1) % 4
            # cara de arriba/abajo usan todo el ancho del satín; los cantos delgados solo la orilla
            sub = (u_a, u_b, 0, 1) if k in (0, 2) else (u_a, u_b, 0.0, 0.08)
            quad([A[k], Bn[k], Bn[j], A[j]], "R", sub)

top = 0.52
# dos lazos (ojos del moño): elipses de 10 tramos, inclinadas hacia afuera
for s in (-1, 1):
    pts = []
    for k in range(11):
        a = math.pi * 2 * k / 10
        x = s * (0.035 + 0.085 * (1 - math.cos(a)))
        z = top + 0.03 + 0.1 * math.sin(a) * (1 if math.sin(a) > 0 else 0.2)
        pts.append((x, 0.0, z))
    tira(pts, 0.085, lado_fijo=Vector((0, 1, 0)))
# dos colas que caen sobre la tapa
for s in (-1, 1):
    tira([(s * 0.03, -0.02, top + 0.02), (s * 0.09, -0.12, top + 0.008), (s * 0.13, -0.24, top + 0.004), (s * 0.15, -0.31, top - 0.02)], 0.07)
# nudo central
caja((0, 0, top + 0.035), (0.07, 0.06, 0.05), {"lado": "R", "arriba": "R", "abajo": "R"})

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
viejo = bpy.data.objects.get("RegaloTexturizado")
if viejo: bpy.data.objects.remove(viejo, do_unlink=True)
me = bpy.data.meshes.new("RegaloTexturizado"); bm.to_mesh(me); bm.free()
me.materials.append(mat)
for p in me.polygons: p.use_smooth = False
o = bpy.data.objects.new("RegaloTexturizado", me)
col = bpy.data.collections.get("PropsJuego") or bpy.data.collections.new("PropsJuego")
col.objects.link(o)
o.location = (-8, -4, 0)
exportar_glb([o], "RegaloTexturizado.glb", raiz=o)
print("regalo texturizado: tris =", sum(len(p.vertices) - 2 for p in me.polygons), "| verts =", len(me.vertices))
