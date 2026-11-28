# -*- coding: utf-8 -*-
"""
CUARTO DE MÁQUINAS (historia v1.5): cuarto nuevo pegado por fuera a la pared norte del taller, detrás de Siete.
Estilo LOW-POLY de caras planas, mismos materiales del taller. Coordenadas de BLENDER (unity = (-bx, bz, -by)).
  Cuarto: x -11.6..-6.6, y -9.23 (cara exterior de la pared del taller) .. -13.6; piso z 0; techo de una agua 4.05 -> 3.3.
  Puerta: hueco en Taller_Paredes centrado en x -10.6 (1.6 x 2.3 m), puerta abierta hacia adentro pegada a la pared este.

Objetos:
  Cuarto_Maquinas (colección Edificio -> Edificio.glb): paredes de tablones, piso, techo con almohada de nieve, marcos de la
      puerta, hoja de la puerta, letrero "SALA DE MÁQUINAS", ojo de buey, banca con herramientas, foco colgante.
  Cuarto_Plano   (Edificio): el plano azul de Santa en la pared norte (Unity le pone el Letrero).
  Siete_Corazon  (colección Props -> Props_Taller.glb): motor con base, caja de fusibles, cables que vienen de Siete
      y estos hijos que Unity prende/anima (pivote en su punto de giro):
        Corazon_Engrane  engrane instalado (gira en el eje Y de Blender)   -> se ve al instalar el engrane
        Corazon_Resorte  resorte (escala Z = rebote)                       -> se ve al instalar el resorte
        Corazon_Fusible  fusible en sus pinzas                             -> se ve al instalar el fusible
        Corazon_Volante  volante rojo (gira en el eje X de Blender cuando Siete está curada)
        Corazon_Foco     foquito de estado de la caja de fusibles (material Siete_Foco)
La pared original se guarda como malla "Taller_Paredes_antes_cuarto" (fake user) => restaurar_pared().
Uso: exec(modelado.py); exec(siete_v3.py); exec(cuarto_maquinas.py); hacer_cuarto()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

X0, X1 = -11.6, -6.6           # este (Unity x 11.6) .. oeste (Unity x 6.6)
Y0, Y1 = -9.23, -13.6          # pared del taller .. pared norte del cuarto
H0, H1 = 4.05, 3.3             # alto del techo junto al taller / al norte
G = 0.12                       # grueso de los tablones
PX, PW, PH = -10.6, 1.6, 2.3   # puerta: centro x, ancho, alto (1.6 m: el NavMesh se hornea con radio 0.5)
VEN = (-11.5, 2.3, 0.32)       # ojo de buey en la pared oeste: (y, z, medio lado del hueco)


def alto_techo(y):
    t = (y - Y0) / (Y1 - Y0)
    return H0 + (H1 - H0) * t


def mats(*nombres):
    return [bpy.data.materials[n] for n in nombres]


# ------------------------------------------------------------------ cuarto (malla estática)
M_CUARTO = ("Amb_Madera3", "Amb_Madera2", "Amb_MaderaOscura", "Amb_Piso", "Amb_Techo", "Amb_Nieve", "Amb_Vidrio",
            "Amb_VerdePino", "Amb_Laton", "Amb_Negro", "Amb_FocoAmarillo", "Amb_Acero", "Amb_Rojo", "Amb_Madera")
MAD3, MAD2, OSC, PISO, TECHO, NIEVE, VIDRIO, VERDE, LATON_C, NEGRO_C, FOCO, ACERO_C, ROJO_C, MAD = range(14)


def pared_tablones(bm, inicio, fin, normal, alto_en, hueco=None, z0=-0.25):
    """Pared de tablones verticales de 'inicio' a 'fin' (puntos XY), cara hacia 'normal'. alto_en(p) = alto del tope.
    hueco = (centro_u, z, medio) => cuadro sin tablones (para la ventana)."""
    inicio, fin = Vector(inicio), Vector(fin)
    largo = (fin - inicio).length
    d = (fin - inicio).normalized()
    n = int(round(largo / 0.5))
    w = largo / n
    for i in range(n):
        u0, u1 = i * w + 0.002, (i + 1) * w - 0.002        # juntitos: el bisel marca la ranura sin dejar rendija
        top = alto_en(inicio + d * ((u0 + u1) / 2)) - 0.02
        mat = MAD3 if i % 2 == 0 else MAD2
        piezas = [(u0, u1, z0, top)]                         # (u desde, u hasta, z desde, z hasta)
        if hueco is not None:
            hu, hz, hm = hueco
            if u1 > hu - hm and u0 < hu + hm:                # este tablón cruza el hueco: se recorta solo el cuadro
                piezas = [(u0, u1, z0, hz - hm), (u0, u1, hz + hm, top)]
                if u0 < hu - hm: piezas.append((u0, hu - hm, hz - hm, hz + hm))
                if u1 > hu + hm: piezas.append((hu + hm, u1, hz - hm, hz + hm))
        for (ua, ub, za, zb) in piezas:
            c = inicio + d * ((ua + ub) / 2)
            centro = Vector((c.x, c.y, (za + zb) / 2)) - normal * (G / 2)
            tam = (abs(d.x) * (ub - ua) + abs(normal.x) * G, abs(d.y) * (ub - ua) + abs(normal.y) * G, zb - za)
            caja(bm, tuple(centro), tam, mat=mat, bisel=0.012, segs=1)


def techo(bm):
    # tablas del techo (inclinado: baja hacia el norte), con alero
    xa, xb = X0 - 0.3, X1 + 0.3
    ya, yb = Y0, Y1 - 0.35
    inclin = math.atan2(H0 - H1, abs(Y1 - Y0))
    giro = Matrix.Rotation(inclin, 3, "X")          # sube hacia +Y (hacia el taller)
    largo = abs(yb - ya) / math.cos(inclin)
    n = 10
    for i in range(n):
        x = xa + (i + 0.5) * (xb - xa) / n
        yc = (ya + yb) / 2
        zc = alto_techo(yc) + 0.07
        caja(bm, (x, yc, zc), ((xb - xa) / n - 0.01, largo, 0.14), mat=TECHO, bisel=0.015, segs=1, giro=giro)
    # almohada de nieve (encima del techo, se queda adentro de la orilla y se enrolla un poquito al norte)
    yc = (ya + yb) / 2 - 0.05
    caja(bm, ((xa + xb) / 2, yc, alto_techo(yc) + 0.24), (xb - xa - 0.12, largo - 0.05, 0.22), mat=NIEVE, bisel=0.09, segs=1, giro=giro)
    # gotitas de nieve escurriendo en la orilla norte
    zb = alto_techo(yb) + 0.12
    for k, x in enumerate((-11.4, -10.3, -9.4, -8.2, -7.3, -6.6)):
        tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=1.0)
        s = (0.2, 0.15, 0.13 + 0.03 * (k % 2))             # bolitas redondas pegadas a la orilla (mitad arriba)
        for v in tmp.verts:
            v.co = Vector((v.co.x * s[0] + x, v.co.y * s[1] + yb + 0.08, v.co.z * s[2] + zb + 0.02))
        for f in tmp.faces: f.material_index = NIEVE
        unir(bm, tmp)
    # tapajunta contra la pared del taller
    caja(bm, ((xa + xb) / 2, Y0 - 0.06, H0 + 0.22), (xb - xa, 0.12, 0.2), mat=OSC, bisel=0.02, segs=1)


def esquinas_y_zoclo(bm):
    for (x, y) in ((X0, Y1), (X1, Y1), (X0, Y0 - 0.05), (X1, Y0 - 0.05)):
        alto = alto_techo(y)
        caja(bm, (x, y, (alto - 0.25) / 2), (0.2, 0.2, alto + 0.25), mat=OSC, bisel=0.02, segs=1)
    # zoclo de afuera
    caja(bm, ((X0 + X1) / 2, Y1 - 0.08, 0.05), (X1 - X0 + 0.2, 0.06, 0.25), mat=OSC, bisel=0.01, segs=1)
    for x in (X0 - 0.08, X1 + 0.08):
        caja(bm, (x, (Y0 + Y1) / 2, 0.05), (0.06, abs(Y1 - Y0), 0.25), mat=OSC, bisel=0.01, segs=1)


def piso(bm):
    n = int(abs(Y1 - Y0) / 0.4)
    for i in range(n):
        y = Y0 - 0.02 - (i + 0.5) * (abs(Y1 - Y0) - 0.06) / n
        caja(bm, ((X0 + X1) / 2, y, -0.05), (X1 - X0 - 0.1, (abs(Y1 - Y0) - 0.06) / n - 0.012, 0.1), mat=PISO, bisel=0.01, segs=1)


def ojo_de_buey(bm):
    y, z, hm = VEN
    x = X1                                          # pared oeste (cara exterior en x = X1)
    r_ext, r_int, lados = 0.46, 0.3, 10
    for lado_x, dx in ((x + 0.02, 1), (x - G - 0.02, -1)):     # aro por fuera y por dentro
        anillo_e = [bm.verts.new((lado_x, y + r_ext * math.cos(2 * math.pi * k / lados), z + r_ext * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
        anillo_i = [bm.verts.new((lado_x, y + r_int * math.cos(2 * math.pi * k / lados), z + r_int * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
        anillo_e2 = [bm.verts.new((lado_x + dx * 0.06, v.co.y, v.co.z)) for v in anillo_e]
        anillo_i2 = [bm.verts.new((lado_x + dx * 0.06, v.co.y, v.co.z)) for v in anillo_i]
        for k in range(lados):
            j = (k + 1) % lados
            for quad in ((anillo_e2[k], anillo_e2[j], anillo_i2[j], anillo_i2[k]), (anillo_e[k], anillo_e[j], anillo_e2[j], anillo_e2[k]),
                         (anillo_i[k], anillo_i2[k], anillo_i2[j], anillo_i[j]), (anillo_e[k], anillo_i[k], anillo_i[j], anillo_e[j])):
                bm.faces.new(quad).material_index = LATON_C
    # vidrio (octágono en medio de la pared) + tapa de la orilla del hueco
    vid = [bm.verts.new((x - G / 2, y + r_int * 1.02 * math.cos(2 * math.pi * k / lados), z + r_int * 1.02 * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
    bm.faces.new(vid).material_index = VIDRIO
    for (dy, dz, sy, sz) in ((0, hm, 2 * hm, 0.02), (0, -hm, 2 * hm, 0.02), (hm, 0, 0.02, 2 * hm), (-hm, 0, 0.02, 2 * hm)):
        caja(bm, (x - G / 2, y + dy, z + dz), (G, sy, sz), mat=OSC, bisel=0.0, segs=1)


def puerta_y_letrero(bm):
    x0, x1 = PX - PW / 2, PX + PW / 2
    # marcos por las dos caras de la pared del taller y en el grueso
    for y in (-8.74, Y0 - 0.03):
        caja(bm, (x0 - 0.07, y, PH / 2), (0.14, 0.07, PH + 0.02), mat=OSC, bisel=0.015, segs=1)
        caja(bm, (x1 + 0.07, y, PH / 2), (0.14, 0.07, PH + 0.02), mat=OSC, bisel=0.015, segs=1)
        caja(bm, (PX, y, PH + 0.08), (PW + 0.3, 0.07, 0.16), mat=OSC, bisel=0.015, segs=1)
    for x in (x0 + 0.015, x1 - 0.015):
        caja(bm, (x, -9.0, PH / 2), (0.03, 0.5, PH), mat=MAD, bisel=0.0, segs=1)
    caja(bm, (PX, -9.0, PH - 0.015), (PW, 0.5, 0.03), mat=MAD, bisel=0.0, segs=1)
    caja(bm, (PX, -9.0, 0.01), (PW + 0.1, 0.55, 0.03), mat=OSC, bisel=0.0, segs=1)       # umbral
    # hoja de la puerta ABIERTA hacia adentro, pegada a la pared este (bisagra en x0, y = Y0)
    hx = x0 + 0.06
    for k in range(4):
        y = Y0 - 0.08 - (k + 0.5) * (PW - 0.06) / 4
        caja(bm, (hx, y, PH / 2 - 0.01), (0.06, (PW - 0.06) / 4 - 0.01, PH - 0.04), mat=VERDE, bisel=0.01, segs=1)
    for z in (0.35, PH - 0.35):
        caja(bm, (hx + 0.045, Y0 - 0.08 - PW / 2 + 0.03, z), (0.03, PW - 0.14, 0.12), mat=OSC, bisel=0.01, segs=1)
    caja(bm, (hx + 0.045, Y0 - 0.08 - PW / 2 + 0.03, PH / 2), (0.03, 0.12, PH - 0.7), mat=OSC, bisel=0.01, segs=1,
         giro=Matrix.Rotation(math.atan2(PW - 0.3, PH - 0.7), 3, "X"))
    caja(bm, (hx + 0.07, Y0 - PW + 0.02, 1.05), (0.04, 0.05, 0.16), mat=LATON_C, bisel=0.01, segs=1)       # manija
    # letrero sobre la puerta, del lado del TALLER (mira +Y)
    caja(bm, (PX, -8.70, PH + 0.45), (1.7, 0.05, 0.42), mat=MAD2, bisel=0.02, segs=1)
    caja(bm, (PX, -8.68, PH + 0.45), (1.6, 0.02, 0.34), mat=OSC, bisel=0.0, segs=1)
    texto(bm, "SALA DE MÁQUINAS", (PX, -8.665, PH + 0.5), 0.13, LATON_C)
    texto(bm, "Solo personal autorizado", (PX, -8.665, PH + 0.34), 0.07, NIEVE)


def texto(bm, cadena, centro, tam, mat, normal_y=1):
    """Texto en relieve (fuente de Blender) mirando a +Y (normal_y=1) o -Y."""
    cu = bpy.data.curves.new("_txt", "FONT"); cu.body = cadena; cu.size = tam; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.006
    cu.resolution_u = 2                      # curvas de la letra low-poly (la fuente trae 12)
    ob = bpy.data.objects.new("_txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    tmp = bmesh.new(); tmp.from_mesh(me); bpy.data.meshes.remove(me)
    # el texto queda en XY mirando a +Z: lo paramos para que mire a +Y (si mira -Y, se voltea para leerse bien)
    rot = Matrix.Rotation(math.pi, 3, "Z") @ Matrix.Rotation(math.pi / 2, 3, "X") if normal_y > 0 else Matrix.Rotation(math.pi / 2, 3, "X")
    for v in tmp.verts: v.co = rot @ v.co + Vector(centro)
    for f in tmp.faces: f.material_index = mat
    unir(bm, tmp)


def banca(bm):
    bx, by = X1 - G - 0.33, -11.0          # pegada por dentro a la pared oeste
    caja(bm, (bx, by, 0.85), (0.6, 1.5, 0.08), mat=MAD, bisel=0.015, segs=1)
    for sy in (-1, 1):
        for sx in (-1, 1):
            caja(bm, (bx + sx * 0.24, by + sy * 0.66, 0.41), (0.07, 0.07, 0.82), mat=OSC, bisel=0.01, segs=1)
    caja(bm, (bx, by, 0.25), (0.52, 1.4, 0.05), mat=MAD2, bisel=0.01, segs=1)
    # herramientas: llave, martillo, aceitera, caja de tornillos
    caja(bm, (bx - 0.05, by - 0.45, 0.905), (0.05, 0.36, 0.02), mat=ACERO_C, bisel=0.005, segs=1)
    cil(bm, (bx - 0.05, by - 0.66, 0.9), (bx - 0.05, by - 0.66, 0.92), 0.05, ACERO_C, segs=6)
    caja(bm, (bx + 0.1, by + 0.1, 0.91), (0.04, 0.32, 0.035), mat=MAD3, bisel=0.008, segs=1)
    caja(bm, (bx + 0.1, by + 0.28, 0.93), (0.15, 0.06, 0.06), mat=ACERO_C, bisel=0.01, segs=1)
    cil(bm, (bx - 0.05, by + 0.5, 0.89), (bx - 0.05, by + 0.5, 1.05), 0.07, ROJO_C, segs=8)
    cil(bm, (bx - 0.05, by + 0.5, 1.05), (bx - 0.05, by + 0.5, 1.12), 0.05, LATON_C, segs=8, r2=0.02)
    tira(bm, [(bx - 0.05, by + 0.5, 1.1), (bx - 0.05, by + 0.62, 1.18), (bx - 0.05, by + 0.72, 1.2)], 0.008, LATON_C, segs=4)
    caja(bm, (bx + 0.12, by - 0.2, 0.93), (0.18, 0.14, 0.08), mat=VERDE, bisel=0.01, segs=1)
    # engrane de repuesto colgado en la pared (decoración)
    for k in range(3):
        cil(bm, (X1 - G - 0.01, by - 0.4 + k * 0.4, 1.55), (X1 - G - 0.04, by - 0.4 + k * 0.4, 1.55), 0.04, ACERO_C, segs=6)


def foco_colgante(bm):
    fx, fy = -9.1, -11.4
    zt = alto_techo(fy)
    tira(bm, [(fx, fy, zt), (fx, fy, 2.95)], 0.01, NEGRO_C, segs=4)
    cil(bm, (fx, fy, 2.95), (fx, fy, 2.85), 0.05, NEGRO_C, segs=8)
    cil(bm, (fx, fy, 2.88), (fx, fy, 2.78), 0.28, VERDE, segs=10, r2=0.06)         # pantalla de lámina
    tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=0.08)
    for v in tmp.verts: v.co += Vector((fx, fy, 2.74))
    for f in tmp.faces: f.material_index = FOCO
    unir(bm, tmp)


def cuarto(bm):
    piso(bm)
    # pared norte (cara hacia -Y), este (cara hacia -X... en Blender la pared este está en x = X0 y mira a -X) y oeste
    pared_tablones(bm, (X0, Y1), (X1, Y1), Vector((0, -1, 0)), lambda p: alto_techo(p.y))
    pared_tablones(bm, (X0, Y0), (X0, Y1), Vector((-1, 0, 0)), lambda p: alto_techo(p.y))
    pared_tablones(bm, (X1, Y0), (X1, Y1), Vector((1, 0, 0)), lambda p: alto_techo(p.y),
                   hueco=(abs(VEN[0] - Y0), VEN[1], VEN[2]))
    esquinas_y_zoclo(bm)
    techo(bm)
    ojo_de_buey(bm)
    puerta_y_letrero(bm)
    banca(bm)
    foco_colgante(bm)


# ------------------------------------------------------------------ plano de Santa (malla estática aparte)
def plano_santa(bm):
    # tablero azul con dibujo blanco de Siete; mira a +Y (hacia la puerta), pegado a la pared norte
    y = Y1 + G + 0.02
    caja(bm, (0, y, 0), (0.95, 0.02, 0.7), mat=0, bisel=0.0, segs=1)
    yl = y + 0.012
    def linea(a, b, r=0.008):
        tira(bm, [(a[0], yl, a[1]), (b[0], yl, b[1])], r, 1, segs=4)
    def rect(cx, cz, w, h):
        pts = [(cx - w / 2, cz - h / 2), (cx + w / 2, cz - h / 2), (cx + w / 2, cz + h / 2), (cx - w / 2, cz + h / 2)]
        for i in range(4): linea(pts[i], pts[(i + 1) % 4])
    rect(0.05, -0.08, 0.42, 0.36)                 # cuerpo de la máquina
    rect(0.05, -0.02, 0.2, 0.12)                  # pantalla
    linea((-0.02, 0.0), (-0.02, -0.03)); linea((0.12, 0.0), (0.12, -0.03))      # ojitos
    for k in range(6):                            # sonrisa
        a, b = math.pi * (1 + k / 6), math.pi * (1 + (k + 1) / 6)
        linea((0.05 + 0.05 * math.cos(a), -0.04 + 0.025 * math.sin(a)), (0.05 + 0.05 * math.cos(b), -0.04 + 0.025 * math.sin(b)), 0.006)
    linea((0.05, 0.1), (-0.03, 0.2)); linea((0.05, 0.1), (0.13, 0.2)); linea((-0.03, 0.2), (0.13, 0.2))   # embudo
    for k in range(10):                           # engrane al lado
        a, b = 2 * math.pi * k / 10, 2 * math.pi * (k + 1) / 10
        linea((-0.3 + 0.09 * math.cos(a), -0.12 + 0.09 * math.sin(a)), (-0.3 + 0.09 * math.cos(b), -0.12 + 0.09 * math.sin(b)), 0.006)
    linea((-0.39, 0.28), (-0.39, -0.3), 0.004); linea((0.4, 0.28), (0.4, -0.3), 0.004)       # márgenes
    texto(bm, "No. 7  SIETE", (0.0, yl + 0.004, 0.27), 0.065, 1)
    texto(bm, "S. Claus", (0.28, yl + 0.004, -0.3), 0.045, 1)
    for (dx, dz) in ((-0.43, 0.31), (0.43, 0.31), (-0.43, -0.31), (0.43, -0.31)):          # chinchetas
        cil(bm, (dx, y + 0.01, dz), (dx, y + 0.035, dz), 0.022, 2, segs=6)


# ------------------------------------------------------------------ corazón de Siete (Props)
MC = ("Amb_Acero", "Amb_MetalTurquesa", "Amb_Laton", "Amb_Cobre", "Amb_Negro", "Amb_Rojo", "Amb_Amarillo", "Amb_Hollin")
C_ACERO, C_TURQ, C_LATON, C_COBRE, C_NEGRO, C_ROJO, C_AMAR, C_HOLLIN = range(8)
MX, MY, MZ = -8.75, -12.55, 0.9           # centro del tambor del motor (eje X)


def corazon(bm):
    caja(bm, (MX, MY, 0.08), (2.3, 1.3, 0.16), mat=C_ACERO, bisel=0.03, segs=1)
    for sx in (-1, 1):                                    # soportes del tambor
        caja(bm, (MX + sx * 0.7, MY, 0.35), (0.16, 0.9, 0.4), mat=C_ACERO, bisel=0.03, segs=1)
    cil(bm, (MX - 0.85, MY, MZ), (MX + 0.85, MY, MZ), 0.55, C_TURQ, segs=12)
    for x in (MX - 0.85, MX - 0.3, MX + 0.3, MX + 0.85):  # aros de latón
        cil(bm, (x - 0.04, MY, MZ), (x + 0.04, MY, MZ), 0.58, C_LATON, segs=12)
    # hueco del engrane al frente (mira a +Y): plato oscuro + eje
    cil(bm, (MX - 0.35, MY + 0.5, MZ + 0.12), (MX - 0.35, MY + 0.58, MZ + 0.12), 0.34, C_HOLLIN, segs=12)
    cil(bm, (MX - 0.35, MY + 0.58, MZ + 0.12), (MX - 0.35, MY + 0.72, MZ + 0.12), 0.05, C_ACERO, segs=6)
    # porta-resorte arriba del tambor: copa abajo y brazo arriba
    rx, ry = MX + 0.35, MY
    cil(bm, (rx, ry, MZ + 0.5), (rx, ry, MZ + 0.62), 0.14, C_ACERO, segs=8)
    caja(bm, (rx + 0.2, ry, MZ + 0.88), (0.08, 0.12, 0.56), mat=C_ACERO, bisel=0.01, segs=1)
    caja(bm, (rx + 0.08, ry, MZ + 1.17), (0.36, 0.14, 0.06), mat=C_ACERO, bisel=0.01, segs=1)
    # caja de fusibles en el lado este del motor (x más negativo), mira a +Y
    fx, fy = MX - 1.3, MY + 0.1
    caja(bm, (fx, fy, 1.1), (0.42, 0.3, 0.7), mat=C_ACERO, bisel=0.03, segs=1)
    caja(bm, (fx, fy + 0.155, 1.05), (0.32, 0.02, 0.44), mat=C_HOLLIN, bisel=0.0, segs=1)
    for z in (0.9, 1.2):                                  # pinzas del fusible
        caja(bm, (fx, fy + 0.18, z), (0.1, 0.04, 0.04), mat=C_LATON, bisel=0.005, segs=1)
    caja(bm, (fx, fy, 0.38), (0.12, 0.12, 0.76), mat=C_ACERO, bisel=0.01, segs=1)        # pata
    # cables desde Siete: de su caja de conexión atraviesan la pared y bajan al motor
    camino = [(-7.6, -7.38, 2.72), (-7.55, -8.1, 2.45), (-7.5, -8.8, 2.3), (-7.5, -9.6, 2.3), (-7.55, -10.6, 2.55),
              (-7.7, -11.7, 2.35), (-7.9, -12.35, 1.75), (MX + 0.6, MY, MZ + 0.45)]
    lado = [Vector((0.06, 0, 0)), Vector((-0.06, 0, 0)), Vector((0, 0.05, 0.05))]
    for i, mat in enumerate((C_ROJO, C_AMAR, C_NEGRO)):
        tira(bm, [Vector(p) + lado[i] for p in camino], 0.025, mat, segs=5)
    for (x, y, z) in ((-7.52, -9.0, 2.3), (-7.52, -9.25, 2.3)):            # pasamuros (por las 2 caras de la pared)
        cil(bm, (x, y - 0.03, z), (x, y + 0.03, z), 0.14, C_LATON, segs=8)


def corazon_engrane(bm):
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        r = 0.3 if (k % 4) in (1, 2) else 0.25
        pts.append((r * math.cos(a), r * math.sin(a)))
    contorno(bm, (0, 0, 0), pts, 0.07, 0)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        d = Vector((math.cos(a), 0, math.sin(a)))
        tira(bm, [d * 0.05 + Vector((0, 0.075, 0)), d * 0.19 + Vector((0, 0.075, 0))], 0.022, 0, segs=4)
    cil(bm, (0, 0, 0), (0, 0.11, 0), 0.07, 1, segs=6)


def corazon_resorte(bm):
    pts = []
    vueltas, n = 6, 6 * 8
    for k in range(n + 1):
        a = 2 * math.pi * vueltas * k / n
        pts.append((0.1 * math.cos(a), 0.1 * math.sin(a), 0.02 + 0.5 * k / n))
    tira(bm, pts, 0.016, 0, segs=4)
    cil(bm, (0, 0, 0.0), (0, 0, 0.03), 0.12, 1, segs=8)
    cil(bm, (0, 0, 0.52), (0, 0, 0.55), 0.12, 1, segs=8)


def corazon_fusible(bm):
    cil(bm, (0, 0, -0.16), (0, 0, 0.16), 0.05, 0, segs=8)            # vidrio rojo
    for s in (-1, 1):
        cil(bm, (0, 0, s * 0.14), (0, 0, s * 0.2), 0.058, 1, segs=8)   # tapas de metal


def corazon_volante(bm):
    lados = 14
    for (r0, r1) in ((0.5, 0.62),):
        e = [Vector((0, r1 * math.cos(2 * math.pi * k / lados), r1 * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
        i = [Vector((0, r0 * math.cos(2 * math.pi * k / lados), r0 * math.sin(2 * math.pi * k / lados))) for k in range(lados)]
        vs = [[bm.verts.new(p + Vector((dx, 0, 0))) for p in anillo] for anillo in (e, i) for dx in (-0.06, 0.06)]
        ea, eb, ia, ib = vs
        for k in range(lados):
            j = (k + 1) % lados
            for q in ((ea[k], ea[j], eb[j], eb[k]), (ia[k], ib[k], ib[j], ia[j]), (ea[k], ia[k], ia[j], ea[j]), (eb[k], eb[j], ib[j], ib[k])):
                bm.faces.new(q).material_index = 0
    for k in range(5):
        a = 2 * math.pi * k / 5
        d = Vector((0, math.cos(a), math.sin(a)))
        tira(bm, [d * 0.08, d * 0.52], 0.035, 0, segs=4)
    cil(bm, (-0.1, 0, 0), (0.1, 0, 0), 0.1, 1, segs=8)


def corazon_foco(bm):
    cil(bm, (0, 0, -0.02), (0, 0, 0.02), 0.07, 1, segs=8)
    domo(bm, (0, 0, 0.02), 0.06, 0, segs=8, anillos=3)


# ------------------------------------------------------------------ objetos
def objeto(nombre, coleccion, construir, materiales, pivote=(0, 0, 0), padre=None):
    o = bpy.data.objects.get(nombre)
    if o is None:
        o = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre))
        bpy.data.collections[coleccion].objects.link(o)
    bm = bmesh.new(); construir(bm)
    reemplazar_malla(o, bm, materiales)
    if padre is not None:
        o.parent = padre; o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = pivote; o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    return o


def hueco_puerta():
    """Abre el hueco de la puerta en Taller_Paredes (con una copia de respaldo de la malla original)."""
    pared = bpy.data.objects["Taller_Paredes"]
    resp = bpy.data.meshes.get("Taller_Paredes_antes_cuarto")
    if resp is None:
        resp = pared.data.copy(); resp.name = "Taller_Paredes_antes_cuarto"; resp.use_fake_user = True
    nombre = pared.data.name
    viejo = pared.data
    pared.data = resp.copy()
    if viejo.users == 0: bpy.data.meshes.remove(viejo)
    pared.data.name = nombre
    bm = bmesh.new(); bm.from_mesh(pared.data)
    # cortamos con 4 planos (bisect) y borramos lo que queda dentro de la caja de la puerta
    x0, x1, y0, y1, z1 = PX - PW / 2, PX + PW / 2, -9.5, -8.6, PH
    for co, no in (((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (1, 0, 0)), ((0, 0, z1), (0, 0, 1))):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    borrar = [f for f in bm.faces if x0 - 1e-4 < f.calc_center_median().x < x1 + 1e-4 and y0 < f.calc_center_median().y < y1
              and f.calc_center_median().z < z1 + 1e-4]
    bmesh.ops.delete(bm, geom=borrar, context="FACES")
    bm.to_mesh(pared.data); bm.free()
    return len(borrar)


def restaurar_pared():
    pared = bpy.data.objects["Taller_Paredes"]
    resp = bpy.data.meshes["Taller_Paredes_antes_cuarto"]
    nombre = pared.data.name; viejo = pared.data
    pared.data = resp.copy()
    if viejo.users == 0: bpy.data.meshes.remove(viejo)
    pared.data.name = nombre


def vitrina_cuarto():
    """Copias VT_ del cuarto y del corazón junto a VT_Maquina (mismo desfase que la Maquina)."""
    sc = bpy.data.scenes["Vitrina"]
    vt = bpy.data.objects["VT_Maquina"]
    delta = vt.matrix_world.translation - bpy.data.objects["Maquina"].matrix_world.translation
    for o in list(sc.collection.all_objects):
        if o.name.startswith(("VT_Cuarto", "VT_Corazon", "VT_Siete_Corazon")): bpy.data.objects.remove(o)
    for n in ("Cuarto_Maquinas", "Cuarto_Plano", "Siete_Corazon"):
        org = bpy.data.objects[n]
        c = org.copy(); c.name = "VT_" + n; sc.collection.objects.link(c)
        c.matrix_world = Matrix.Translation(delta) @ org.matrix_world
        for h in org.children:
            ch = h.copy(); ch.name = "VT_" + h.name; sc.collection.objects.link(ch)
            ch.parent = c; ch.matrix_parent_inverse = Matrix.Identity(4); ch.location = h.location.copy()
    return delta


def hacer_cuarto():
    nb = hueco_puerta()
    c = objeto("Cuarto_Maquinas", "Edificio", cuarto, mats(*M_CUARTO))
    pl_mat = material("Cuarto_PlanoAzul", (0.1, 0.28, 0.62), rugosidad=0.8)
    p = objeto("Cuarto_Plano", "Edificio", plano_santa, [pl_mat, bpy.data.materials["Amb_Blanco"], bpy.data.materials["Amb_Rojo"]],
               pivote=(-10.75, 0, 1.75))
    co = objeto("Siete_Corazon", "Props", corazon, mats(*MC))
    foco_m = bpy.data.materials["Siete_Foco"]
    objeto("Corazon_Engrane", "Props", corazon_engrane, mats("Amb_Laton", "Amb_Acero"), pivote=(MX - 0.35, MY + 0.62, MZ + 0.12), padre=co)
    objeto("Corazon_Resorte", "Props", corazon_resorte, mats("Amb_Acero", "Amb_Laton"), pivote=(MX + 0.35, MY, MZ + 0.62), padre=co)
    objeto("Corazon_Fusible", "Props", corazon_fusible, mats("Amb_Rojo", "Amb_Acero"), pivote=(MX - 1.3, MY + 0.31, 1.05), padre=co)
    objeto("Corazon_Volante", "Props", corazon_volante, mats("Amb_Rojo", "Amb_Acero"), pivote=(MX + 0.97, MY, MZ), padre=co)
    objeto("Corazon_Foco", "Props", corazon_foco, [foco_m, bpy.data.materials["Amb_Laton"]], pivote=(MX - 1.3, MY + 0.1, 1.47), padre=co)
    vitrina_cuarto()
    tris = lambda o: sum(len(q.vertices) - 2 for q in o.data.polygons)
    return (f"cuarto listo: hueco {nb} caras · Cuarto_Maquinas {tris(c)} tris · Plano {tris(p)} · "
            f"Corazón {tris(co) + sum(tris(h) for h in co.children)} tris ({len(co.children)} piezas)")
