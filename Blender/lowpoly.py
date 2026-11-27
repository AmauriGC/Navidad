# -*- coding: utf-8 -*-
"""
LOW-POLY (27-nov): pasa un modelo hecho con el estilo anterior (bisel + Subsurf + normales suaves) al estilo
low-poly redondeado aprobado: SIN Subsurf (queda la malla base biselada), caras planas y, si sobra detalle,
Decimate (colapso) hasta un tope de triángulos. Respeta nombres de objetos y mallas, materiales y pivotes
(las animaciones por código siguen funcionando porque los objetos no se mueven).
Uso: exec(lowpoly.py); lowpolizar("Elfo", tope=0.6)
  - raiz: nombre del objeto raíz; se procesan él y todos sus hijos (también accesorios Acc_*).
  - ratio: proporción de Decimate (1 = no reducir) aplicada solo a mallas con más de 'min_tris' triángulos.
"""
import bpy, bmesh

QUITAR = {"SUBSURF", "WEIGHTED_NORMAL", "DECIMATE"}

def _hijos(o):
    res = [o]
    for h in o.children: res += _hijos(h)
    return res

def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)

def lowpolizar_obj(o, ratio=1.0, min_tris=400):
    if o.type != "MESH": return 0, 0
    me = o.data
    antes = tris(me)
    if me.users > 1:            # malla compartida (instancias): se procesa una vez por nombre
        pass
    for m in list(o.modifiers):
        if m.type in QUITAR: o.modifiers.remove(m)
    if ratio < 1.0 and antes > min_tris:
        d = o.modifiers.new("lp_dec", "DECIMATE"); d.ratio = ratio; d.use_collapse_triangulate = False
    if len(o.modifiers):
        esc = o.users_scene[0] if o.users_scene else bpy.context.scene
        dg = esc.view_layers[0].depsgraph
        dg.update()
        nueva = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        for m in list(o.modifiers):
            if m.name == "lp_dec": o.modifiers.remove(m)
        bm = bmesh.new(); bm.from_mesh(nueva); bpy.data.meshes.remove(nueva)
        for m in list(o.modifiers): o.modifiers.remove(m)      # todo ya aplicado
    else:
        bm = bmesh.new(); bm.from_mesh(me)
    for f in bm.faces: f.smooth = False
    bm.to_mesh(me); bm.free()
    for e in me.edges: e.use_edge_sharp = False
    if me.has_custom_normals:
        try: bpy.ops.object.select_all(action="DESELECT")
        except Exception: pass
        me.normals_split_custom_set([])  # quita normales personalizadas
    me.update()
    return antes, tris(me)

def lowpolizar(raiz, ratio=1.0, min_tris=400, saltar=()):
    hechas = set(); tot0 = tot1 = 0
    for o in _hijos(bpy.data.objects[raiz]):
        if o.type != "MESH" or o.name in saltar: continue
        if o.data.name in hechas:
            for m in list(o.modifiers):
                if m.type in QUITAR: o.modifiers.remove(m)
            continue
        hechas.add(o.data.name)
        a, b = lowpolizar_obj(o, ratio, min_tris)
        tot0 += a; tot1 += b
    print(raiz, "tris base", tot0, "->", tot1, "(mallas", len(hechas), ")")
    return tot1
