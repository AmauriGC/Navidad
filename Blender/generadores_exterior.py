# Generadores procedurales del exterior (Blender 5, bpy + bmesh).
# Se ejecutan dentro de Blender (Scripting > Run, o por el MCP con run_python).
# Reemplazan la GEOMETRÍA de mallas existentes, así todas las instancias (150 pinos) se actualizan solas.
# Materiales esperados por índice:
#   pinos:  0 = Ext_Tronco, 1 = Ext_PinoX (verde), 2 = Ext_NieveBrillo
#   rocas:  0 = Ext_Roca, 1 = Ext_NieveBrillo
import bpy, bmesh, math, random
from mathutils import Vector, noise


def pino(me, H, R, niveles, puntas, caida, nieve, seed, ancho_tronco=0.035, angosto=1.0, traslape=1.55):
    """Pino en capas: cada capa es un cono con puntas en estrella que caen; la nieve va en la parte visible."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    # tronco con raíz un poco más ancha
    seg = 10
    anillos = []
    for z, r in ((-0.02, ancho_tronco * 1.8), (0.03, ancho_tronco * 1.15), (H * 0.35, ancho_tronco * 0.7)):
        anillos.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
    for a, b in zip(anillos, anillos[1:]):
        for j in range(seg):
            f = bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j])); f.material_index = 0; f.smooth = True
    zb = H * 0.13
    paso = (H - zb) / (niveles + traslape - 1)
    K = 5
    for i in range(niveles):
        frac = i / max(1, niveles - 1)
        Ri = R * (1.0 - frac * 0.8) ** angosto * (0.94 + rnd.random() * 0.12)
        ultimo = i == niveles - 1
        z_rim = zb + paso * i
        z_apex = H if ultimo else z_rim + paso * traslape
        tierH = z_apex - z_rim
        N = max(8, int(puntas * (1.0 - frac * 0.4)) // 2 * 2)
        giro = rnd.random() * math.pi
        apex = bm.verts.new((0, 0, z_apex))
        anillos = []
        for k in range(1, K + 1):
            t = k / K; fila = []
            for j in range(N):
                ang = giro + 2 * math.pi * j / N
                punta = (j % 2 == 0)
                r = Ri * t * ((1.0 if punta else 0.72 + 0.12 * (1 - t)) * (0.92 + 0.16 * rnd.random()))
                z = z_apex - tierH * (1.0 - (1.0 - t) ** 1.6) * 0.82
                if punta: z -= caida * Ri * t ** 2.2
                else: z += 0.04 * Ri * t
                fila.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), z)))
            anillos.append(fila)
        prof = [rnd.random() for _ in range(N)]
        def mat(k, j):
            tc = (k + 0.5) / K
            if ultimo and tc < 0.3 + 0.3 * nieve: return 2
            if 0.35 < tc < 0.95 and prof[j] < nieve and (tc < 0.8 or prof[j] < nieve * 0.5): return 2
            return 1
        for j in range(N):
            f = bm.faces.new((apex, anillos[0][j], anillos[0][(j + 1) % N])); f.material_index = mat(0, j); f.smooth = True
        for k in range(K - 1):
            a, b = anillos[k], anillos[k + 1]
            for j in range(N):
                f = bm.faces.new((a[j], b[j], b[(j + 1) % N], a[(j + 1) % N])); f.material_index = mat(k + 1, j); f.smooth = True
        c = bm.verts.new((0, 0, z_rim + tierH * 0.3))
        borde = anillos[-1]
        for j in range(N):
            f = bm.faces.new((borde[(j + 1) % N], borde[j], c)); f.material_index = 1; f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(55))
    me.clear_geometry(); bm.to_mesh(me); bm.free(); me.update()


def roca(me, sx, sy, sz, zmin, seed):
    """Peña: icosfera deformada con ruido + 3 cortes planos; nieve en las caras de arriba."""
    rnd = random.Random(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
    for v in bm.verts:
        n = v.co.normalized()
        d = 1.0 + 0.28 * noise.noise(n * 1.1 + off) + 0.1 * noise.noise(n * 2.7 + off)
        v.co = Vector((n.x * d * sx, n.y * d * sy, n.z * d * sz))
    for _ in range(3):
        nrm = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1))).normalized()
        lim = max(v.co.dot(nrm) for v in bm.verts) * rnd.uniform(0.72, 0.85)
        for v in bm.verts:
            exc = v.co.dot(nrm) - lim
            if exc > 0: v.co -= nrm * exc
    zmn = min(v.co.z for v in bm.verts)
    for v in bm.verts: v.co.z += zmin - zmn
    zmx = max(v.co.z for v in bm.verts)
    bm.normal_update()
    for f in bm.faces:
        f.smooth = True
        f.material_index = 1 if (f.normal.z > 0.5 and f.calc_center_median().z > zmin + (zmx - zmin) * 0.5) else 0
    for e in bm.edges: e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(28))
    me.clear_geometry(); bm.to_mesh(me); bm.free()


if __name__ == "__main__":
    pino(bpy.data.meshes["PinoAbeto"],  H=0.94, R=0.42, niveles=5, puntas=18, caida=0.28, nieve=0.55, seed=1)
    pino(bpy.data.meshes["PinoNevado"], H=0.88, R=0.46, niveles=4, puntas=18, caida=0.20, nieve=0.95, seed=2)
    pino(bpy.data.meshes["PinoJoven"],  H=0.82, R=0.40, niveles=3, puntas=14, caida=0.32, nieve=0.40, seed=3)
    pino(bpy.data.meshes["PinoPicea"],  H=0.88, R=0.27, niveles=7, puntas=14, caida=0.38, nieve=0.50, seed=4, angosto=0.8, traslape=1.7)
    roca(bpy.data.meshes["Roca0"], 0.55, 0.48, 0.38, -0.37, seed=10)
    roca(bpy.data.meshes["Roca1"], 0.56, 0.44, 0.30, -0.21, seed=11)
    roca(bpy.data.meshes["Roca2"], 0.52, 0.48, 0.36, -0.20, seed=12)
    # La cerca (malla "Cerca") se generó a partir de las posiciones de sus 68 postes (cada 2 m alrededor del patio):
    # poste = cilindro de 8 lados + domo de madera + gorrito de nieve; 2 travesaños cilíndricos por tramo,
    # tira de nieve con huecos en el de arriba, y serie de focos colgando en catenaria (5 focos por tramo).
