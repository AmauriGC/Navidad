"""
MONTAJE DEL TRÁILER con ffmpeg.
Toma los cuadros que grabó GrabadorTrailer (Library/Trailer/<toma>/f_00000.jpg, 30 fps), los corta según la
línea de tiempo de abajo, les pone los textos (fuentes del juego), agrega las tarjetas negras, la música
(Herramientas/trailer_musica.py -> Library/Trailer/musica.wav) y los efectos de sonido del juego.
Sale en Builds/Trailer/TurnoDeNoche_Trailer.mp4 (1920x1080, 30 fps, H.264 + AAC).
Uso:  python3 Herramientas/trailer_montar.py
"""
import os, subprocess, shutil

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOMAS = os.path.join(RAIZ, "Library", "Trailer")
TMP = os.path.join(TOMAS, "_montaje")
SALIDA = os.path.join(RAIZ, "Builds", "Trailer", "TurnoDeNoche_Trailer.mp4")
FUENTE_TITULO = os.path.join(RAIZ, "Assets", "Resources", "Fuentes", "MountainsofChristmas-Bold.ttf")
FUENTE_TEXTO = os.path.join(RAIZ, "Assets", "Resources", "Fuentes", "Fredoka-Medium.ttf")
AUDIO = os.path.join(RAIZ, "Assets", "Resources", "Audio")
FPS = 30
ORO, BLANCO, ROJO, HIELO = "0xFFD166", "0xF2F2F7", "0xFF4A3D", "0x9FE0FF"

# ------------------------------------------------------------------------------------------- línea de tiempo
# ("toma", desde_seg_en_la_toma, duración, [textos])     ó     ("tarjeta", duración, [textos])
# texto = (cadena, fuente, tamaño, color, y, aparece, desaparece)   (tiempos relativos al inicio del clip)
T, F = FUENTE_TITULO, FUENTE_TEXTO
LINEA = [
    ("01_exterior", 0.5, 4.0, [("En la víspera de Navidad...", T, 84, ORO, 0.80, 1.0, 4.0)]),
    ("15_siete", 0.2, 3.2, [("Siete, la máquina más vieja del taller...", T, 76, ORO, 0.82, 0.3, 3.2)]),
    ("16_caja_ojos", 0.0, 2.8, [("...despertó a los cascanueces.", T, 84, ORO, 0.82, 0.8, 2.8)]),
    ("03_cascanueces", 2.6, 3.0, [("Y no estás solo.", T, 92, ROJO, 0.82, 1.6, 3.0)]),
    ("negro", 0.4, []),
    ("tarjeta", 1.6, [("DIFICULTAD", F, 46, BLANCO, 0.40, 0.0, 1.6), ("IMPOSIBLE", T, 190, ROJO, 0.52, 0.0, 1.6)]),
    ("17_elfos", 0.0, 2.8, [("ELIGE A TU ELFO", F, 56, BLANCO, 0.12, 0.0, 2.8, 0.2),
                            ("Tilo", T, 110, ORO, 0.84, 0.0, 0.72, 0.1), ("Nieves", T, 110, ORO, 0.84, 0.72, 1.44, 0.1),
                            ("Chispa", T, 110, ORO, 0.84, 1.44, 2.16, 0.1), ("Jengibre", T, 110, ORO, 0.84, 2.16, 2.8, 0.1)]),
    ("05_elfo_corre", 0.3, 1.8, []),
    ("06_persecucion", 0.2, 2.2, []),
    ("18_nieve", 0.0, 2.6, [("TE SIGUEN POR TUS HUELLAS", F, 64, HIELO, 0.86, 0.3, 2.6)]),
    ("09_ventisca", 0.6, 2.0, [("VENTISCAS", F, 64, HIELO, 0.86, 0.2, 2.0)]),
    ("10_nevado", 0.5, 2.0, [("CASCANUECES NEVADOS", F, 64, HIELO, 0.86, 0.2, 2.0)]),
    ("04_caja", 0.4, 1.4, []),
    ("08_apagon", 0.6, 2.8, [("3:00 AM", T, 110, ORO, 0.80, 0.4, 2.8)]),
    ("07_bola", 0.5, 1.8, []),
    ("11_congelado", 0.1, 1.6, []),
    ("12_galleta", 0.3, 1.8, [("10 galletas de jengibre escondidas", F, 52, ORO, 0.86, 0.2, 1.8)]),
    ("tarjeta", 2.6, [("Cura a Siete y arma el Gran Árbol", T, 100, ORO, 0.44, 0.2, 2.6), ("antes del amanecer.", T, 96, BLANCO, 0.58, 0.6, 2.6)]),
    ("13_arbol", 0.0, 3.6, []),
    ("19_siete_cura", 0.1, 3.0, []),
    ("14_estrella", 0.3, 3.0, []),
    ("20_rayo", 0.0, 2.0, []),
    ("21_chiquitos", 0.3, 2.4, []),
    ("tarjeta", 3.4, "14_estrella", [("Turno de Noche", T, 190, ORO, 0.40, 0.2, 3.4), ("en el Taller", T, 150, ORO, 0.58, 0.4, 3.4),
                      ("Una Navidad diferente", F, 48, HIELO, 0.74, 1.0, 3.4)]),
    ("tarjeta", 3.2, "21_chiquitos", [("Juega gratis en el navegador y en Android", F, 54, BLANCO, 0.42, 0.2, 3.2),
                      ("amaurigc.github.io/Navidad", T, 110, ORO, 0.55, 0.4, 3.2),
                      ("Un juego de Cristian Amauri Gonzaga Castañeda", F, 36, HIELO, 0.72, 0.6, 3.2)]),
]

# efectos de sonido: (archivo, toma, segundo dentro de ESE clip, volumen)  -> se acomodan solos si cambian duraciones
EFECTOS = [
    ("voz_siete2", "15_siete", 0.5, 0.8), ("descarga", "15_siete", 1.3, 1.0),
    ("instalar", "16_caja_ojos", 0.0, 0.9), ("clac", "16_caja_ojos", 0.9, 0.9), ("clac", "16_caja_ojos", 1.35, 0.9),
    ("clac", "16_caja_ojos", 1.8, 0.9), ("cuerda", "16_caja_ojos", 2.0, 0.8),
    ("cas_arranque", "03_cascanueces", 1.5, 0.9), ("despertar", "03_cascanueces", 1.6, 0.5), ("susto", "03_cascanueces", 1.65, 0.9),
    ("cambio", "17_elfos", 0.0, 0.7), ("cambio", "17_elfos", 0.72, 0.7), ("cambio", "17_elfos", 1.44, 0.7), ("cambio", "17_elfos", 2.16, 0.7),
    ("alerta", "06_persecucion", 0.0, 0.6), ("voz_cas1", "06_persecucion", 0.1, 0.8), ("voz_cas3", "06_persecucion", 0.3, 0.8),
    ("voz_cas2", "06_persecucion", 0.5, 0.8), ("paso_cas3", "06_persecucion", 0.8, 0.7), ("paso_cas4", "06_persecucion", 1.3, 0.7),
    ("paso_cas3", "06_persecucion", 1.8, 0.7),
    ("voz_cas2", "18_nieve", 0.2, 0.8), ("voz_cas4", "18_nieve", 0.4, 0.8), ("voz_cas1", "18_nieve", 0.6, 0.8),
    ("paso_nieve1", "18_nieve", 0.3, 0.6), ("paso_nieve2", "18_nieve", 0.65, 0.6), ("paso_nieve3", "18_nieve", 1.0, 0.6),
    ("paso_cas4", "18_nieve", 1.2, 0.6), ("paso_cas3", "18_nieve", 1.7, 0.6),
    ("ventisca", "09_ventisca", 0.0, 0.9),
    ("lanzar", "10_nevado", 0.8, 0.6), ("impacto_nieve", "10_nevado", 1.6, 0.7),
    ("boing", "04_caja", 0.3, 0.9),
    ("apagon", "08_apagon", 0.3, 1.0), ("alerta", "08_apagon", 2.4, 0.6),
    ("lanzar", "07_bola", 0.2, 0.8), ("impacto_nieve", "07_bola", 0.75, 0.9), ("aturdido", "07_bola", 0.8, 0.8),
    ("voz_cas4", "07_bola", 0.95, 0.7), ("voz_cas1", "07_bola", 1.15, 0.7),
    ("congelar", "11_congelado", 0.25, 0.9),
    ("galleta", "12_galleta", 0.7, 0.8),
    ("instalar", "19_siete_cura", 0.1, 0.8), ("instalar", "19_siete_cura", 0.45, 0.8), ("instalar", "19_siete_cura", 0.8, 0.8),
    ("reparada", "19_siete_cura", 1.2, 0.8), ("melodia_siete", "19_siete_cura", 1.25, 0.5),
    ("palanca", "19_siete_cura", 1.7, 0.9), ("fabricar", "19_siete_cura", 2.0, 0.8),
    ("colocar", "14_estrella", 0.3, 0.8), ("encender", "14_estrella", 0.9, 0.9),
    ("voz_siete3", "20_rayo", 0.0, 0.7), ("etapa", "20_rayo", 0.9, 0.8),
    ("encender", "21_chiquitos", 0.4, 0.6),
]
for i in range(11):                                   # piezas del árbol: una cada 0.3 s
    EFECTOS.append(("colocar", "13_arbol", 0.2 + i * 0.3, 0.4))


def alfa(a, b, fundido=0.35):
    return (f"if(lt(t,{a}),0,if(lt(t,{a + fundido}),(t-{a})/{fundido},"
            f"if(lt(t,{b - fundido}),1,if(lt(t,{b}),({b}-t)/{fundido},0))))")


def textos(lista, idx):
    filtros = []
    for k, txt in enumerate(lista):
        cad, fuente, tam, color, y, a, b = txt[:7]
        fundido = txt[7] if len(txt) > 7 else 0.35
        ruta = os.path.join(TMP, f"texto_{idx}_{k}.txt")
        with open(ruta, "w", encoding="utf-8") as f: f.write(cad)
        filtros.append(f"drawtext=fontfile='{fuente}':textfile='{ruta}':fontsize={tam}:fontcolor={color}"
                       f":x=(w-text_w)/2:y=h*{y}-text_h/2:shadowcolor=black@0.75:shadowx=4:shadowy=4"
                       f":alpha='{alfa(a, b, fundido)}'")
    return filtros


def correr(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(cmd)); print(r.stderr[-3000:]); raise SystemExit(1)


def clip(i, item):
    salida = os.path.join(TMP, f"clip_{i:02d}.mp4")
    if item[0] in ("tarjeta", "negro"):
        dur, fondo, lista = (item[1], item[2], item[3]) if len(item) == 4 else (item[1], None, item[2])
        filtros = textos(lista, i)
        if fondo:
            # fondo = último cuadro de una toma, desenfocado y oscurecido, con un acercamiento lento
            cuadros = sorted(os.listdir(os.path.join(TOMAS, fondo)))
            imagen = os.path.join(TOMAS, fondo, cuadros[-1])
            n = round(dur * FPS)
            filtros = [f"scale=2112:1188,zoompan=z='1+0.04*on/{n}':d={n}:s=1920x1080:fps={FPS}",
                       "boxblur=18:2", "eq=brightness=-0.22:saturation=0.85", "vignette=PI/4",
                       "fade=t=in:st=0:d=0.5"] + filtros
            entrada = ["-loop", "1", "-framerate", str(FPS), "-i", imagen, "-t", str(dur)]
        else:
            entrada = ["-f", "lavfi", "-i", f"color=c=0x05060c:s=1920x1080:r={FPS}:d={dur}"]
        correr(["ffmpeg", "-y", "-loglevel", "error"] + entrada +
               ["-vf", ",".join(filtros or ["null"]), "-frames:v", str(round(dur * FPS)),
                "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS), salida])
        return salida, dur
    toma, desde, dur, lista = item
    carpeta = os.path.join(TOMAS, toma)
    filtros = textos(lista, i)
    # pequeños fundidos al principio y final de las tomas tranquilas del inicio
    if toma in ("01_exterior",): filtros.insert(0, f"fade=t=in:st=0:d=1.2")
    if toma == "20_rayo": filtros.append(f"fade=t=out:st={dur - 0.35}:d=0.35:color=white")
    if toma == "21_chiquitos": filtros.insert(0, "fade=t=in:st=0:d=0.35:color=white")
    correr(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", str(round(desde * FPS)),
            "-i", os.path.join(carpeta, "f_%05d.jpg"), "-frames:v", str(round(dur * FPS)),
            "-vf", ",".join(filtros) if filtros else "null", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS), salida])
    return salida, dur


def main():
    if os.path.isdir(TMP): shutil.rmtree(TMP)
    os.makedirs(TMP); os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    clips, total, inicio = [], 0.0, {}
    for i, item in enumerate(LINEA):
        ruta, dur = clip(i, item)
        print(f"  {total:5.1f}s  {item[0]:16s} {dur:.1f}s")
        inicio.setdefault(item[0], total)
        clips.append(ruta); total += dur
    lista = os.path.join(TMP, "lista.txt")
    with open(lista, "w") as f:
        for c in clips: f.write(f"file '{c}'\n")
    video = os.path.join(TMP, "video.mp4")
    correr(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", video])

    # audio: música + efectos con retraso
    entradas = ["-i", os.path.join(TOMAS, "musica.wav")]
    partes = ["[1:a]volume=1.0[m]"]   # entrada 0 = video, 1 = música
    nombres = ["[m]"]
    for k, (nombre, toma, dt, vol) in enumerate(EFECTOS):
        entradas += ["-i", os.path.join(AUDIO, nombre + ".wav")]
        ms = int((inicio[toma] + dt) * 1000)
        extra = ",atrim=0:2.6,afade=t=out:st=2.0:d=0.6" if nombre == "ventisca" else ""
        partes.append(f"[{k + 2}:a]aformat=sample_rates=44100:channel_layouts=stereo{extra},volume={vol * 0.55},adelay={ms}|{ms}[e{k}]")
        nombres.append(f"[e{k}]")
    partes.append("".join(nombres) + f"amix=inputs={len(nombres)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    correr(["ffmpeg", "-y", "-loglevel", "error", "-i", video] + entradas +
           ["-filter_complex", ";".join(partes), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
            "-t", f"{total:.2f}", "-movflags", "+faststart", SALIDA])
    print(f"Listo: {SALIDA}  ({total:.1f} s)")


if __name__ == "__main__":
    main()
