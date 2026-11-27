"""VITRINA: escena "Vitrina" con TODOS los modelos ordenados en filas y con su nombre.
Son copias ENLAZADAS (obj.copy(): comparten la malla con el original), así que cualquier cambio a la malla
se ve en los dos lados. No mueve nada de la escena principal ni cambia lo que se exporta a Unity.
Uso:  exec(open(".../Blender/vitrina.py").read()); hacer_vitrina()      (se puede repetir: borra y rehace)
      ir_a("Roca0")  -> pone la vista de la ventana sobre ese modelo en la vitrina
"""
import bpy
from mathutils import Vector

FILAS = [
    ("Personajes", ["Elfo", "Cascanueces", "Reno", "RenoNarizRoja", "Trineo", "TrineoSanta"]),
    ("Arbol y piezas", ["Arbol", "Pieza_Maceta", "Pieza_Rama", "Pieza_Esfera", "Pieza_Guirnalda",
                        "Pieza_Estrella", "Pieza_Zanahoria", "Regalo"]),
    ("Juego", ["CubetaNieve", "MontonNieve", "LetreroPoste", "NotaPared", "TableroCorcho", "Indicador",
               "Tapete", "BolaNieve", "Galleta", "Refaccion_Engrane", "Refaccion_Resorte", "Refaccion_Llave",
               "BloqueHielo", "CajaSorpresa", "Medalla"]),
    ("Taller", ["Mesa_1", "Mesa_2", "Mesa_3", "Repisa_Oeste", "Repisa_Sur_A", "Repisa_Sur_B",
                "Cajas", "Heno", "Chimenea", "Maquina"]),
    ("Exterior", ["Roca_0", "Roca_1", "Roca_24", "Arbusto_6", "Patio_Troncos", "MunecoNieve", "Farolito_00",
                  "Pino_000", "Pino_001", "Pino_002", "Pino_003"]),
    ("Casas", ["Casa_0_CasaTroncos", "Casa_1_CasaRoja", "Casa_2_CasaA", "Casa_3_CasaAzul", "Casa_4_CasaVerde"]),
]
NOMBRES = {"Roca_0": "Roca 0", "Roca_1": "Roca 1", "Roca_24": "Roca 2", "Arbusto_6": "Arbusto",
           "Patio_Troncos": "Troncos", "Pino_000": "Pino Joven", "Pino_001": "Pino Nevado",
           "Pino_002": "Pino Picea", "Pino_003": "Pino Abeto", "Farolito_00": "Farolito"}
SALTAR = ("Acc_",)          # accesorios de las otras variantes del elfo (en el juego se prenden de a uno)
HUECO, SEP_FILA = 1.5, 4.0


def _descendientes(o):
    r = [o]
    for h in o.children:
        if not h.name.startswith(SALTAR):
            r += _descendientes(h)
    return r


def _caja(objs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        if o.type not in {'MESH', 'CURVE', 'FONT'}:
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
    if mn.x > mx.x:
        mn = mx = objs[0].matrix_world.translation.copy()
    return mn, mx


def hacer_vitrina():
    sc = bpy.data.scenes.get("Vitrina") or bpy.data.scenes.new("Vitrina")
    for o in list(sc.collection.all_objects):
        if o.name.startswith("VT_"):
            bpy.data.objects.remove(o)
    col = sc.collection
    y = 0.0
    faltan = []
    for titulo, nombres in FILAS:
        x, prof = 0.0, 0.0
        for n in nombres:
            org = bpy.data.objects.get(n)
            if org is None:
                faltan.append(n); continue
            objs = _descendientes(org)
            mn, mx = _caja(objs)
            mapa = {}
            for o in objs:
                c = o.copy()                      # comparte la malla (enlazada)
                c.name = "VT_" + o.name
                col.objects.link(c)
                mapa[o] = c
            for o, c in mapa.items():
                if o.parent in mapa:
                    c.parent = mapa[o.parent]; c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
                else:
                    c.parent = None
                    c.matrix_world = o.matrix_world.copy()
            raiz = mapa[org]
            delta = Vector((x - mn.x, y - mn.y, -org.matrix_world.translation.z))   # el origen = el suelo (lo de abajo va enterrado)
            raiz.matrix_world.translation += delta
            # etiqueta
            t = bpy.data.curves.get("VT_txt_" + n) or bpy.data.curves.new("VT_txt_" + n, 'FONT')
            t.body = NOMBRES.get(n, n); t.size = 0.35; t.align_x = 'CENTER'
            et = bpy.data.objects.new("VT_Etiqueta_" + n, t); col.objects.link(et)
            et.location = (x + (mx.x - mn.x) / 2, y - 0.5, 0.02); et.rotation_euler = (1.5708, 0, 0)
            x += (mx.x - mn.x) + HUECO
            prof = max(prof, mx.y - mn.y)
        # título de la fila
        t = bpy.data.curves.get("VT_fila_" + titulo) or bpy.data.curves.new("VT_fila_" + titulo, 'FONT')
        t.body = titulo.upper(); t.size = 0.9; t.align_x = 'RIGHT'
        et = bpy.data.objects.new("VT_Fila_" + titulo, t); col.objects.link(et)
        et.location = (-1.5, y - 0.5, 0.02); et.rotation_euler = (1.5708, 0, 0)
        y += prof + SEP_FILA
    # luz y mundo para Vista Material
    if "VT_Sol" not in sc.objects:
        sol = bpy.data.objects.new("VT_Sol", bpy.data.lights.get("VT_Sol") or bpy.data.lights.new("VT_Sol", 'SUN'))
        sol.data.energy = 3.0; sol.rotation_euler = (0.8, 0.2, 0.6); col.objects.link(sol)
    sc.world = bpy.context.scene.world if bpy.context.scene != sc else sc.world
    return faltan


def mostrar_vitrina():
    sc = bpy.data.scenes["Vitrina"]
    for w in bpy.context.window_manager.windows:
        w.scene = sc


def ir_a(nombre, distancia=1.8, angulo=(-35, 25)):
    """Encuadra la ventana 3D de Blender sobre el modelo VT_<nombre> de la vitrina."""
    import math
    o = bpy.data.objects.get("VT_" + nombre)
    objs = _descendientes(o) if o else []
    mn, mx = _caja(objs)
    centro = (mn + mx) / 2; radio = max((mx - mn).length / 2, 0.3)
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'VIEW_3D':
                r3 = a.spaces.active.region_3d
                r3.view_location = centro
                r3.view_distance = radio * distancia * 2
                from mathutils import Euler
                r3.view_rotation = Euler((math.radians(90 - angulo[1]), 0, math.radians(angulo[0])), 'XYZ').to_quaternion()
                a.spaces.active.shading.type = 'MATERIAL'
