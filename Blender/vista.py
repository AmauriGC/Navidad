# -*- coding: utf-8 -*-
"""
VISTA PREVIA: renderiza uno o varios objetos solos (escena temporal "Vista") para revisar modelos sin abrir Unity.
Uso: exec(modelado.py); exec(vista.py); ver(["CasaRoja_obj"], "casa_roja", vistas=[(az, elev)], dist=1.0)
La imagen queda en Library/Capturas/<nombre>_<i>.png
"""
import bpy, math
from mathutils import Vector

def ver(nombres, archivo, vistas=((35, 20),), dist=1.0, res=(900, 600), noche=False, centro=None, radio=None):
    """centro/radio: para acercarse a una parte de un objeto grande (p. ej. un tramo de la cerca)."""
    sc = bpy.data.scenes.get("Vista") or bpy.data.scenes.new("Vista")
    for o in list(sc.collection.objects): sc.collection.objects.unlink(o)
    objs = [bpy.data.objects[n] for n in nombres]
    # posición original guardada: se dibujan en su lugar, la cámara los encuadra
    for o in objs: sc.collection.objects.link(o)
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    centro = Vector(centro) if centro is not None else (mn + mx) / 2
    radio = radio if radio is not None else (mx - mn).length / 2
    cam = bpy.data.objects.get("Vista_Cam") or bpy.data.objects.new("Vista_Cam", bpy.data.cameras.new("Vista_Cam"))
    sol = bpy.data.objects.get("Vista_Sol") or bpy.data.objects.new("Vista_Sol", bpy.data.lights.new("Vista_Sol", "SUN"))
    rel = bpy.data.objects.get("Vista_Relleno") or bpy.data.objects.new("Vista_Relleno", bpy.data.lights.new("Vista_Relleno", "SUN"))
    for o in (cam, sol, rel): sc.collection.objects.link(o)
    sol.data.energy = 0.8 if noche else 3.0; sol.data.color = (0.75, 0.85, 1.0) if noche else (1.0, 0.95, 0.88)
    sol.rotation_euler = (math.radians(50), 0, math.radians(30))
    rel.data.energy = 0.6; rel.data.color = (0.6, 0.7, 1.0); rel.rotation_euler = (math.radians(70), 0, math.radians(200))
    w = bpy.data.worlds.get("Vista_Mundo") or bpy.data.worlds.new("Vista_Mundo"); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.05, 0.07, 0.16, 1) if noche else (0.35, 0.42, 0.6, 1); bg.inputs["Strength"].default_value = 1.0
    sc.camera = cam; cam.data.lens = 50; cam.data.clip_end = 1000
    eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in eng else "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x, sc.render.resolution_y = res; sc.eevee.taa_render_samples = 24
    rutas = []
    win = bpy.context.window_manager.windows[0]; anterior = win.scene
    try:
        win.scene = sc
        for i, (az, el) in enumerate(vistas):
            a, e = math.radians(az), math.radians(el)
            d = radio * 2.9 * dist
            cam.location = centro + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
            cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = f"{PROYECTO}/Library/Capturas/{archivo}_{i}.png"
            with bpy.context.temp_override(window=win, scene=sc):
                bpy.ops.render.render(write_still=True, scene=sc.name)
            rutas.append(sc.render.filepath)
    finally:
        win.scene = anterior
        for o in list(sc.collection.objects): sc.collection.objects.unlink(o)
    return rutas


def enfocar(nombres, distancia=1.6, angulo=(60, 35), material=True):
    """Mueve la vista 3D de la ventana de Blender del alumno para que vea lo que se está trabajando.
    angulo = (giro alrededor, inclinación) en grados. material=True pone la vista 'Material Preview' (con color)."""
    import mathutils
    objs = [bpy.data.objects[n] for n in nombres if n in bpy.data.objects]
    if not objs: return "nada que enfocar"
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    centro = (mn + mx) / 2; radio = max((mx - mn).length / 2, 0.5)
    rot = mathutils.Euler((math.radians(90 - angulo[1]), 0, math.radians(angulo[0])), "XYZ").to_quaternion()
    n = 0
    for win in bpy.context.window_manager.windows:
        if win.scene.name != "Scene": continue
        for area in win.screen.areas:
            if area.type != "VIEW_3D": continue
            for sp in area.spaces:
                if sp.type != "VIEW_3D": continue
                r3 = sp.region_3d
                r3.view_perspective = "PERSP"
                r3.view_location = centro; r3.view_distance = radio * distancia * 1.8; r3.view_rotation = rot
                if material: sp.shading.type = "MATERIAL"
                n += 1
            area.tag_redraw()
    return f"vista enfocada en {len(objs)} objetos ({n} ventanas 3D)"


def ver_grupo(nombres, archivo, vistas=((-20, 10),), res=(1000, 700), margen=1.15, noche=False):
    """Como ver(), pero el encuadre sale de la caja de TODOS los descendientes con malla (sirve con raíces vacías)."""
    import mathutils
    bpy.context.view_layer.update()
    objs = []
    def hijos(o):
        r = [o]
        for h in o.children: r += hijos(h)
        return r
    for n in nombres: objs += hijos(bpy.data.objects[n])
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == "MESH" and o.visible_get() for c in o.bound_box]
    mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return ver([o.name for o in objs if o.type == "MESH"], archivo, vistas=vistas, res=res, centro=(mn + mx) / 2,
               radio=(mx - mn).length / 2 * margen, noche=noche)
