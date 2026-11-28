# -*- coding: utf-8 -*-
"""
CARA DEL CASCANUECES v3 (27-nov, detallitos): rehace SOLO Cas_Cabeza y Cas_Mandibula en low-poly (caras planas).
Problemas de la v2: la boca era un cilindro de piel pegado abajo del bigote ("caja"), los dientes flotaban por fuera,
la cabeza era un cilindro liso y el pivote de la mandíbula estaba 12 cm DETRÁS de la cara: al abrir 28° toda la
barba bajaba y se metía al pecho.

Cara de JUGUETE de madera (pedido: "más como si fuera un juguete"):
  - Cabeza: cilindro torneado (14 lados) con acabado de laca (rugosidad 0.3 en los materiales Cas_*).
  - Ojos, cachetes, cejas y delineado PINTADOS (discos casi planos pegados al cilindro con _sup/_pintado).
  - Pelo: una sola pieza lisa que abraza lados y nuca (loft abierto), nariz de perilla, bigote liso enroscado.
  - BOCA de cascanueces: ranura oscura (Cas_Boca) donde entra la PALANCA-mandíbula curva, con dientes cuadrados
    arriba (cabeza) y abajo (palanca). La barba lisa cuelga de la palanca y se mueve con ella.
  - Bisagra (PIVOTE_MAND) dentro de la cabeza, a la altura de la boca: al abrir 12° la barba casi no baja y,
    con la cabeza echándose atrás (CascanuecesAnimador), no choca con el pecho. probar_boca(g) lo simula.
Mismos nombres y jerarquía (Cascanueces -> Cas_Cuerpo -> Cas_Cabeza -> Cas_Mandibula) para CascanuecesAnimador.
Se modela en coordenadas del cascanueces: pies en z=0, mira a -Y, 2.1 m de alto.
Uso: exec(modelado.py); exec(cascanueces_cara_v3.py); hacer_cara()
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

PIVOTE_MAND = Vector((0.0, -0.02, 1.255))         # bisagra de la palanca-mandíbula (coords del cascanueces)
Z_BOCA = 1.255                                      # línea de la boca
RC = 0.15                                           # radio del cilindro de la cabeza (juguete de madera torneado)

def _mundo_cas(o):
    """Matriz del objeto en coords del cascanueces usando la cadena de padres (matrix_world puede estar
    desactualizada si la ventana muestra otra escena, p. ej. la Vitrina)."""
    M = o.matrix_basis.copy(); p = o.parent
    while p is not None:          # (los padres de estas piezas tienen matrix_parent_inverse = identidad)
        M = p.matrix_basis @ M
        p = p.parent
    return M

def _poner(nombre, construir, mats):
    obj = bpy.data.objects[nombre]
    M = _mundo_cas(obj).inverted()
    def envuelto(bm):
        construir(bm)
        bmesh.ops.transform(bm, matrix=M, verts=list(bm.verts))
    poner_malla(obj, envuelto, materiales=[bpy.data.materials[m] for m in mats], subsurf=0)
    for p in obj.data.polygons: p.use_smooth = False           # low-poly: caras planas
    obj.data.name = nombre + "_v3"
    # las copias de la Vitrina (VT_*) comparten malla: que vean la nueva
    vt = bpy.data.objects.get("VT_" + nombre)
    if vt: vt.data = obj.data; vt.location = obj.location
    return obj

def _arco(r, ang_grados, y0=0.0):
    """Punto (x, y) sobre el arco del frente de la cara: 90° = al frente (-Y)."""
    a = math.radians(ang_grados)
    return (r * math.cos(a), y0 - r * math.sin(a))

# ------------------------------------------------------------------ cabeza (juguete de madera)
def _sup(x, fuera=0.0):
    """y de la superficie del cilindro (cara al frente = -Y) en la x dada, empujada 'fuera' metros."""
    return -math.sqrt(max(RC * RC - x * x, 0.0)) - fuera

def _pintado(bm, x, z, rx, rz, mat, fuera=0.002, grosor=0.004, segs=14):
    """Disco 'pintado' pegado al cilindro (ojos, cachetes): casi plano, como pintura sobre madera."""
    esfera(bm, (x, _sup(x, fuera), z), (rx, grosor, rz), mat=mat, segs=segs, anillos=4)

# ventana de la boca en el cilindro: entre los ángulos A0..A1 (90 = al frente) y las alturas Z0..Z1
SEG = 24                         # lados del cilindro: con 24 las orillas de la ventana caen justo en 52.5° y 127.5°
A0, A1 = 52.5, 127.5
Z0, Z1 = 1.165, Z_BOCA
R_HUECO = 0.105                  # qué tan hondo es el hueco oscuro de la boca

def _p(r, a, z):
    x, y = _arco(r, a); return Vector((x, y, z))

def _cara(bm, vs, mat):
    f = bm.faces.new(vs); f.material_index = mat; f.smooth = False

def cilindro_con_boca(bm, P, BO):
    """Cilindro de la cabeza con una VENTANA recortada para la boca y un hueco oscuro detrás (paredes y fondo).
    Cerrada, la palanca tapa la ventana al ras: solo se ve una línea fina, como en un cascanueces de madera."""
    angs = [7.5 + 15 * j for j in range(SEG)]
    anillos = [(1.12, RC - 0.012), (1.14, RC), (Z0, RC), (Z1, RC), (1.5, RC)]
    V = [[bm.verts.new(_p(r, a, z)) for a in angs] for (z, r) in anillos]
    j0, j1 = angs.index(A0), angs.index(A1)
    for i in range(len(anillos) - 1):
        for j in range(SEG):
            if i == 2 and j0 <= j < j1: continue                    # la ventana de la boca
            k = (j + 1) % SEG
            _cara(bm, (V[i][j], V[i + 1][j], V[i + 1][k], V[i][k]), P)
    # hueco: paredes de la ventana hacia adentro + fondo curvo, todo oscuro
    arriba = [bm.verts.new(_p(R_HUECO, angs[j], Z1)) for j in range(j0, j1 + 1)]
    abajo = [bm.verts.new(_p(R_HUECO, angs[j], Z0)) for j in range(j0, j1 + 1)]
    for n, j in enumerate(range(j0, j1)):
        _cara(bm, (V[3][j], V[3][j + 1], arriba[n + 1], arriba[n]), BO)       # techo
        _cara(bm, (V[2][j + 1], V[2][j], abajo[n], abajo[n + 1]), BO)         # piso
        _cara(bm, (arriba[n], arriba[n + 1], abajo[n + 1], abajo[n]), BO)     # fondo
    _cara(bm, (V[2][j0], V[3][j0], arriba[0], abajo[0]), BO)                  # paredes de los lados
    _cara(bm, (V[3][j1], V[2][j1], abajo[-1], arriba[-1]), BO)

def dientes_pintados(bm, z0, z1, mat, a0=58, a1=122, n=5, raya=None):
    """Franja de dientes PINTADA al ras del cilindro (curva, continua) con rayitas finas entre diente y diente."""
    pasos = 12
    fila = [[bm.verts.new(_p(RC + 0.0012, a0 + (a1 - a0) * k / pasos, z)) for k in range(pasos + 1)] for z in (z0, z1)]
    for k in range(pasos):
        _cara(bm, (fila[0][k], fila[0][k + 1], fila[1][k + 1], fila[1][k]), mat)
    if raya is not None:
        for k in range(1, n):
            a = a0 + (a1 - a0) * k / n
            x, y = _arco(RC + 0.0022, a)
            caja(bm, (x, y, (z0 + z1) / 2), (0.0025, 0.0016, z1 - z0), mat=raya, bisel=0.0,
                 giro=Matrix.Rotation(math.radians(a - 90), 3, "Z"))

def cabeza(bm):
    P, B, OJ, N, M, O, R, BO = range(8)
    # cuello blanco (lo tapa la barba)
    loft(bm, [(0, 0, 1.08), (0, 0, 1.16)], [(0.12, 0.12)] * 2, mat=B, segs=10, sub=1, domo=0.0)
    # CABEZA: cilindro torneado de madera pintada con la ventana de la boca recortada
    cilindro_con_boca(bm, P, BO)
    # dientes de arriba pintados justo encima de la boca (bajo el bigote)
    dientes_pintados(bm, Z_BOCA + 0.0015, Z_BOCA + 0.02, B, raya=BO)
    # PELO: una sola pieza lisa que abraza los lados y la nuca (no bolitas), con ondas suaves abajo
    loft(bm, [(0, 0.004, 1.13), (0, 0.004, 1.25), (0, 0.004, 1.38), (0, 0.004, 1.49)],
         [(0.172, 0.172), (0.178, 0.178), (0.175, 0.175), (0.17, 0.17)], mat=B, segs=16, sub=2,
         abierto=(-28, 208))
    # OJOS pintados: blanco plano + pupila roja chiquita (Cas_Ojos) + delineado negro arriba
    for s in (-1, 1):
        _pintado(bm, s * 0.06, 1.395, 0.034, 0.03, B, fuera=0.001)
        _pintado(bm, s * 0.058, 1.392, 0.014, 0.016, OJ, fuera=0.005, grosor=0.004, segs=10)
        loft(bm, [(s * 0.028, _sup(0.028, 0.004), 1.418), (s * 0.06, _sup(0.06, 0.005), 1.43), (s * 0.092, _sup(0.092, 0.004), 1.418)],
             [(0.006, 0.005)] * 3, mat=N, segs=6, sub=2)
        # cejas negras pintadas, gruesas y enojadas (bajan hacia la nariz)
        loft(bm, [(s * 0.022, _sup(0.022, 0.004), 1.448), (s * 0.06, _sup(0.06, 0.005), 1.462), (s * 0.1, _sup(0.1, 0.004), 1.47)],
             [(0.012, 0.006), (0.014, 0.007), (0.009, 0.005)], mat=N, segs=6, sub=2)
        # cachetes: círculo rosa pintado
        _pintado(bm, s * 0.1, 1.315, 0.026, 0.024, M, fuera=0.001)
    # nariz: perilla torneada
    esfera(bm, (0, _sup(0) - 0.022, 1.335), (0.03, 0.03, 0.036), mat=P, segs=10, anillos=6)
    # BIGOTE: una pieza lisa con las puntas enroscadas hacia arriba
    for s in (-1, 1):
        loft(bm, [(0, _sup(0, 0.016), 1.3), (s * 0.05, _sup(0.05, 0.016), 1.292), (s * 0.095, _sup(0.095, 0.014), 1.3),
                  (s * 0.12, _sup(0.12, 0.012), 1.322), (s * 0.108, _sup(0.108, 0.012), 1.342)],
             [(0.022, 0.017), (0.024, 0.019), (0.018, 0.015), (0.012, 0.01), (0.007, 0.007)], mat=B, segs=8, sub=2)
    # SHAKO: copa negra, bandas doradas, visera, escudo y pluma roja
    loft(bm, [(0, 0, 1.49), (0, 0, 1.7), (0, 0, 1.92)], [(0.175, 0.17), (0.185, 0.18), (0.2, 0.195)], mat=N, segs=16, sub=1, domo=0.1)
    toro(bm, (0, 0, 1.515), 0.18, 0.02, mat=O, segs=16, lados=4)
    toro(bm, (0, 0, 1.915), 0.2, 0.02, mat=O, segs=16, lados=4)
    loft(bm, [(-0.15, -0.12, 1.505), (0, -0.215, 1.495), (0.15, -0.12, 1.505)], [(0.03, 0.008)] * 3, mat=N, segs=6, sub=2)
    esfera(bm, (0, -0.185, 1.69), (0.065, 0.015, 0.08), mat=O, segs=4, anillos=4)
    esfera(bm, (0, -0.198, 1.69), (0.025, 0.01, 0.025), mat=R, segs=8, anillos=4)
    loft(bm, [(0, 0.0, 1.92), (0, 0.01, 1.98), (0, 0.0, 2.05), (0, -0.015, 2.1)],
         [(0.03, 0.03), (0.055, 0.05), (0.045, 0.04), (0.012, 0.012)], mat=R, segs=8, sub=2, domo=0.5)
    esfera(bm, (0, 0, 1.925), (0.035, 0.035, 0.02), mat=O, segs=8, anillos=4)

# ------------------------------------------------------------------ mandíbula (palanca de juguete)
def mandibula(bm):
    """La palanca es un PEDAZO DEL MISMO CILINDRO (mismo radio): cerrada queda al ras de la cara."""
    P, B = 0, 1
    angs = [A0 + (A1 - A0) * k / 5 for k in range(6)]
    za, zb = Z0 + 0.0006, Z1 - 0.0006
    afuera = [[bm.verts.new(_p(RC, a, z)) for a in angs] for z in (za, zb)]
    adentro = [[bm.verts.new(_p(RC - 0.03, a, z)) for a in angs] for z in (za, zb)]
    for k in range(5):
        _cara(bm, (afuera[0][k], afuera[0][k + 1], afuera[1][k + 1], afuera[1][k]), P)      # frente
        _cara(bm, (adentro[0][k + 1], adentro[0][k], adentro[1][k], adentro[1][k + 1]), P)  # atrás
        _cara(bm, (afuera[1][k], afuera[1][k + 1], adentro[1][k + 1], adentro[1][k]), P)    # arriba
        _cara(bm, (afuera[0][k + 1], afuera[0][k], adentro[0][k], adentro[0][k + 1]), P)    # abajo
    for k, sig in ((0, 1), (5, -1)):                                                         # lados
        _cara(bm, (afuera[0][k], afuera[1][k], adentro[1][k], adentro[0][k])[::sig], P)
    # dientes de abajo pintados en la orilla de arriba de la palanca
    dientes_pintados(bm, Z_BOCA - 0.019, Z_BOCA - 0.0015, B, raya=2)
    # BARBA: pieza lisa y redondeada que cuelga de la palanca (tapa la orilla de abajo y se mueve con la boca)
    y0 = _sup(0.0)
    loft(bm, [(0, y0 - 0.008, 1.19), (0, y0 - 0.02, 1.15), (0, y0 - 0.03, 1.115)],
         [(0.09, 0.022), (0.08, 0.024), (0.045, 0.02)], mat=B, segs=12, sub=3, domo=0.7,
         arriba=Vector((0, 1, 0)))

def hacer_cara():
    if "Cas_Boca" not in bpy.data.materials:
        material("Cas_Boca", (0.16, 0.02, 0.03), rugosidad=0.9)
    # ojos: pupila roja (antes café oscuro: con la emisión roja encima se veía rosa deslavado)
    material("Cas_Ojos", (0.45, 0.01, 0.01), rugosidad=0.25)
    # acabado de juguete: madera pintada con laca (brillante)
    for n in ("Cas_Piel", "Cas_Blanco", "Cas_Mejilla", "Cas_Negro", "Cas_Rojo", "Cas_Boca"):
        b = next(x for x in bpy.data.materials[n].node_tree.nodes if x.type == "BSDF_PRINCIPLED")
        b.inputs["Roughness"].default_value = 0.3
    # mover la bisagra de la mandíbula (la cabeza no se mueve)
    cab = bpy.data.objects["Cas_Cabeza"]; mand = bpy.data.objects["Cas_Mandibula"]
    piv_cab = _mundo_cas(cab).translation
    mand.location = PIVOTE_MAND - piv_cab
    _poner("Cas_Cabeza", cabeza, ["Cas_Piel", "Cas_Blanco", "Cas_Ojos", "Cas_Negro", "Cas_Mejilla", "Cas_Oro", "Cas_Rojo", "Cas_Boca"])
    _poner("Cas_Mandibula", mandibula, ["Cas_Piel", "Cas_Blanco", "Cas_Boca"])
    for n in ("Cas_Cabeza", "Cas_Mandibula"):
        o = bpy.data.objects[n]; print(n, "tris", sum(len(p.vertices) - 2 for p in o.data.polygons), "loc", tuple(round(v, 3) for v in o.location))

def probar_boca(grados):
    """Abre la mandíbula en Blender para revisar: +X abre (igual que en Unity) y la cabeza se echa atrás
    -grados*0.45, como hace CascanuecesAnimador en Persecución."""
    for n in ("Cas_Mandibula", "VT_Cas_Mandibula"):
        o = bpy.data.objects.get(n)
        if o: o.rotation_euler = (math.radians(grados), 0, 0)
    for n in ("Cas_Cabeza", "VT_Cas_Cabeza"):
        o = bpy.data.objects.get(n)
        if o: o.rotation_euler = (math.radians(-grados * 0.45), 0, 0)
