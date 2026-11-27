# -*- coding: utf-8 -*-
"""
GENERADOR DE AUDIO de "Turno de Noche en el Taller".
Todos los sonidos y la música se SINTETIZAN con matemáticas (numpy), no hay grabaciones:
  - Un tono puro es un seno:            sin(2·π·f·t)
  - Una campana / caja musical suma varios senos ("parciales") que se apagan a distinta velocidad.
  - Un golpe, la nieve o el fuego son RUIDO (números al azar) FILTRADO (le quitamos graves o agudos con la FFT).
  - Una ENVOLVENTE (volumen que sube y baja) le da forma a cada sonido.
Las melodías son villancicos de DOMINIO PÚBLICO (Noche de Paz, We Wish You a Merry Christmas,
Carol of the Bells, Jingle Bells) tocados por un "secuenciador" (lista de notas y duraciones).

Uso:  python3 Herramientas/generar_audio.py      -> escribe los .wav en Assets/Resources/Audio/
"""
import os, wave
import numpy as np

SR = 44100                                   # muestras por segundo
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Assets", "Resources", "Audio")
rng = np.random.default_rng(7)               # semilla fija: siempre salen los mismos sonidos


# ----------------------------------------------------------------------------- utilidades
def tiempo(seg):
    return np.arange(int(seg * SR)) / SR


def guardar(nombre, x, pico=0.89):
    """Normaliza (el punto más fuerte queda en 'pico') y guarda WAV mono de 16 bits."""
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x))
    if m > 0: x = x / m * pico
    os.makedirs(SALIDA, exist_ok=True)
    with wave.open(os.path.join(SALIDA, nombre + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print(f"  {nombre}.wav  {len(x) / SR:5.2f} s")


def filtro(x, bajo=None, alto=None):
    """Filtro con FFT: deja pasar solo las frecuencias entre 'bajo' y 'alto' (Hz), con bordes suaves."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if bajo: g *= 1 / (1 + (bajo / np.maximum(f, 1)) ** 4)    # quita graves
    if alto: g *= 1 / (1 + (f / alto) ** 4)                   # quita agudos
    return np.fft.irfft(X * g, len(x))


def ruido(seg):
    return rng.uniform(-1, 1, int(seg * SR))


def env(n, ataque=0.005, caida=None):
    """Envolvente: sube en 'ataque' segundos y luego cae exponencialmente ('caida' = segundos hasta ~5%)."""
    t = np.arange(n) / SR
    a = np.clip(t / max(ataque, 1e-4), 0, 1)
    if caida: a *= np.exp(-3 * t / caida)
    return a


def mezclar(destino, sonido, inicio_seg, vol=1.0):
    i = int(inicio_seg * SR)
    j = min(len(destino), i + len(sonido))
    if j > i: destino[i:j] += sonido[: j - i] * vol


def suma(*partes):
    """Suma sonidos de distinto largo (rellena con silencio al final los más cortos)."""
    n = max(len(p) for p in partes)
    return sum(np.pad(p, (0, n - len(p))) for p in partes)


def bucle(x, cruce=0.5):
    """Hace que un sonido se pueda repetir sin 'clic': el final se funde con el principio."""
    F = int(cruce * SR)
    cuerpo = x[:-F].copy()
    rampa = np.linspace(0, 1, F)
    cuerpo[:F] = cuerpo[:F] * rampa + x[-F:] * (1 - rampa)
    return cuerpo


NOTAS = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3, "Gb": -3,
         "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}


def hz(nota):
    """'A4' -> 440 Hz. Cada semitono multiplica la frecuencia por 2^(1/12)."""
    nombre, octava = nota[:-1], int(nota[-1])
    return 440.0 * 2 ** ((NOTAS[nombre] + 12 * (octava - 4)) / 12)


# ----------------------------------------------------------------------------- instrumentos
def cajita(f, dur=1.6):
    """Caja musical: parciales casi armónicos que se apagan rápido (los agudos más rápido)."""
    t = tiempo(max(dur, 1.6))
    x = np.zeros_like(t)
    for mult, amp, caida in ((1, 1.0, 1.4), (2, 0.35, 0.8), (3.01, 0.15, 0.5), (4.2, 0.08, 0.25), (6.8, 0.04, 0.12)):
        x += amp * np.sin(2 * np.pi * f * mult * t) * np.exp(-3 * t / caida)
    return x * env(len(t), 0.002)


def campana(f, dur=2.5):
    """Campanita (glockenspiel): parciales INarmónicos 1 : 2.76 : 5.4 : 8.93 => suena metálico."""
    t = tiempo(dur)
    x = np.zeros_like(t)
    for mult, amp, caida in ((1, 1.0, dur), (2.76, 0.5, dur * 0.5), (5.40, 0.25, dur * 0.25), (8.93, 0.12, dur * 0.12)):
        x += amp * np.sin(2 * np.pi * f * mult * t) * np.exp(-3 * t / caida)
    return x * env(len(t), 0.001)


def bajo(f, dur):
    t = tiempo(dur + 0.15)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return x * env(len(t), 0.01, dur * 1.2)


def pad(frecuencias, dur):
    """Colchón suave de acorde: ondas triangulares un poco desafinadas entre sí (suena 'coro')."""
    t = tiempo(dur + 0.6)
    x = np.zeros_like(t)
    for f in frecuencias:
        for d in (-0.4, 0.4):
            fase = (f + d) * t
            x += 2 * np.abs(2 * (fase - np.floor(fase + 0.5))) - 1        # onda triangular
    a = np.clip(t / 0.35, 0, 1) * np.clip((dur + 0.6 - t) / 0.6, 0, 1)
    return filtro(x * a, alto=1800)


def bombo(vol=1.0):
    t = tiempo(0.35)
    f = 45 + 80 * np.exp(-t * 30)                                     # la frecuencia baja rápido: "bum"
    return vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def madera(f=1800, vol=1.0):
    """Bloque de madera / 'clac' de cascanueces."""
    t = tiempo(0.06)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 90) + 0.5 * filtro(ruido(0.06), 1500, 5000) * np.exp(-t * 150)
    return vol * x


def cascabeles(dur=0.18, vol=1.0):
    """Cascabeles de trineo: ráfaga de ruido muy agudo con 'temblor'."""
    t = tiempo(dur)
    x = filtro(ruido(dur), 5000, 12000) * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * t)) * env(len(t), 0.004, dur)
    return vol * x


# ----------------------------------------------------------------------------- secuenciador
def tocar(pista, melodia, bpm, instrumento, octava=0, vol=1.0, inicio=0.0):
    """melodia = [(nota o None, pulsos), ...]. Devuelve en qué pulso terminó."""
    seg_pulso = 60 / bpm
    p = 0.0
    for nota, pulsos in melodia:
        if nota:
            f = hz(nota) * 2 ** octava
            mezclar(pista, instrumento(f, pulsos * seg_pulso), inicio + p * seg_pulso, vol)
        p += pulsos
    return p


def acordes(pista, lista, bpm, pulsos_por_acorde, vol_pad=0.12, vol_bajo=0.5, inicio=0.0, patron_bajo=None):
    seg = 60 / bpm
    TRIADAS = {"C": ("C3", "E3", "G3"), "F": ("F3", "A3", "C4"), "G": ("G3", "B3", "D4"), "G7": ("G3", "B3", "F4"),
               "D": ("D3", "F#3", "A3"), "D7": ("D3", "F#3", "C4"), "A": ("A3", "C#4", "E4"), "B7": ("B2", "D#3", "A3"),
               "Em": ("E3", "G3", "B3"), "Gm": ("G3", "Bb3", "D4"), "Eb": ("Eb3", "G3", "Bb3"), "Cm": ("C3", "Eb3", "G3"),
               "D7m": ("D3", "F#3", "C4")}
    for i, a in enumerate(lista):
        t0 = inicio + i * pulsos_por_acorde * seg
        notas = TRIADAS[a]
        mezclar(pista, pad([hz(n) for n in notas], pulsos_por_acorde * seg), t0, vol_pad)
        raiz = hz(notas[0]) / 2
        if patron_bajo is None:
            mezclar(pista, bajo(raiz, pulsos_por_acorde * seg * 0.9), t0, vol_bajo)
        else:   # patrón "um-pa": raíz y quinta alternadas
            for k, (cual, p) in enumerate(patron_bajo):
                f = raiz if cual == 0 else hz(notas[2]) / 2
                mezclar(pista, bajo(f, seg * 0.8), t0 + p * seg, vol_bajo)


def cancion(duracion_seg, construir, cola=2.5):
    """Crea la pista, deja que 'construir' la llene, y dobla la cola al inicio => bucle perfecto."""
    n = int(duracion_seg * SR)
    pista = np.zeros(n + int(cola * SR))
    construir(pista)
    salida = pista[:n].copy()
    salida[: len(pista) - n] += pista[n:]          # lo que suena después del final continúa al empezar
    return salida


# ============================================================================= MÚSICA
def noche_de_paz():
    """Título: 'Noche de Paz' (Franz Gruber, 1818) en caja musical, compás 6/8 (pulso = corchea)."""
    m = [("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6), ("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6),
         ("D5", 4), ("D5", 2), ("B4", 6), ("C5", 4), ("C5", 2), ("G4", 6),
         ("A4", 4), ("A4", 2), ("C5", 3), ("B4", 1), ("A4", 2), ("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6),
         ("A4", 4), ("A4", 2), ("C5", 3), ("B4", 1), ("A4", 2), ("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6),
         ("D5", 4), ("D5", 2), ("F5", 3), ("D5", 1), ("B4", 2), ("C5", 6), ("E5", 6),
         ("C5", 2), ("G4", 1), ("E4", 3), ("G4", 2), ("F4", 1), ("D4", 3), ("C4", 12)]
    bpm = 130                                   # corcheas por minuto (lento)
    total = sum(p for _, p in m)
    def construir(pista):
        tocar(pista, m, bpm, cajita, octava=1, vol=0.55)
        arm = ["C", "C", "C", "C", "G", "G", "C", "C", "F", "F", "C", "C", "F", "F", "C", "C", "G", "G7", "C", "C", "C", "G7", "C", "C"]
        acordes(pista, arm, bpm, 6, vol_pad=0.10, vol_bajo=0.35)
        # arpegio suave de campanitas en cada compás
        seg = 60 / bpm
        for i, a in enumerate(arm):
            for k, n in enumerate(("C5", "E5", "G5") if a == "C" else ("F4", "A4", "C5") if a == "F" else ("G4", "B4", "D5")):
                mezclar(pista, campana(hz(n) * 2, 1.2), (i * 6 + k * 2) * seg, 0.07)
    return cancion(total * 60 / bpm, construir)


def we_wish():
    """Explorar el taller: 'We Wish You a Merry Christmas' (tradicional inglés), 3/4, dos vueltas (la 2a con campanas)."""
    m = [("G4", 1), ("G4", .5), ("A4", .5), ("G4", .5), ("F#4", .5), ("E4", 1), ("C4", 1), ("E4", 1),
         ("A4", 1), ("A4", .5), ("B4", .5), ("A4", .5), ("G4", .5), ("F#4", 1), ("D4", 1), ("F#4", 1),
         ("B4", 1), ("B4", .5), ("C5", .5), ("B4", .5), ("A4", .5), ("G4", 1), ("E4", 1), ("D4", .5), ("D4", .5),
         ("E4", 1), ("A4", 1), ("F#4", 1), ("G4", 2), ("D4", 1)]
    arm = ["G", "C", "A", "D", "B7", "Em", "D7", "G"]
    bpm = 96
    vuelta = 24                                    # pulsos por vuelta (8 compases de 3)
    def construir(pista):
        seg = 60 / bpm
        tocar(pista, m, bpm, cajita, octava=1, vol=0.5)
        tocar(pista, m, bpm, lambda f, d: suma(0.6 * cajita(f, d), 0.4 * campana(f, 1.5)), octava=1, vol=0.5, inicio=vuelta * seg)
        for v in range(2):
            acordes(pista, arm, bpm, 3, vol_pad=0.08, vol_bajo=0.4, inicio=v * vuelta * seg, patron_bajo=[(0, 0), (1, 1), (1, 2)])
            for b in range(8):   # cascabel suave en el 2 y 3 (vals)
                for p in (1, 2): mezclar(pista, cascabeles(0.12), (v * vuelta + b * 3 + p) * seg, 0.05)
    return cancion(2 * vuelta * 60 / bpm, construir)


def carol_persecucion():
    """Persecución: 'Carol of the Bells' (Mykola Leontovych, 1914) en sol menor, rápido y tenso."""
    bpm = 168
    def ostinato(n1, n2, n3, n4, veces):
        return [(n1, 1), (n2, .5), (n1, .5), (n3, 1)] * veces
    m = (ostinato("Bb4", "A4", None, None, 0) +
         [("Bb4", 1), ("A4", .5), ("Bb4", .5), ("G4", 1)] * 8 +
         [("D5", 1), ("C5", .5), ("D5", .5), ("Bb4", 1)] * 4 +
         [("G5", 1), ("F5", .5), ("G5", .5), ("D5", 1)] * 4)
    compases = 16
    def construir(pista):
        seg = 60 / bpm
        tocar(pista, m, bpm, lambda f, d: campana(f, 1.0), octava=0, vol=0.45)
        tocar(pista, m, bpm, cajita, octava=-1, vol=0.25)          # doblado una octava abajo
        # bajo que desciende cada 2 compases: G F Eb D (el famoso descenso del villancico)
        bajos = ["G2", "G2", "F2", "F2", "Eb2", "Eb2", "D2", "D2"] * 2
        for i, b in enumerate(bajos):
            mezclar(pista, bajo(hz(b), 3 * seg * 0.95), i * 3 * seg, 0.55)
        arm = ["Gm", "Gm", "Gm", "Gm", "Eb", "Eb", "D", "D"] * 2
        acordes(pista, arm, bpm, 3, vol_pad=0.07, vol_bajo=0.0)
        for c in range(compases):   # percusión: bombo en el 1, "clac" de cascanueces en el 2 y 3
            t0 = c * 3 * seg
            mezclar(pista, bombo(), t0, 0.6)
            mezclar(pista, madera(1500), t0 + 1 * seg, 0.35)
            mezclar(pista, madera(1900), t0 + 2 * seg, 0.3)
            if c % 2 == 1: mezclar(pista, madera(1700), t0 + 2.5 * seg, 0.25)
    return cancion(compases * 3 * 60 / bpm, construir, cola=1.5)


def jingle_final():
    """Final / créditos: 'Jingle Bells' (James Lord Pierpont, 1857), alegre, con cascabeles."""
    m = [("E5", 1), ("E5", 1), ("E5", 2), ("E5", 1), ("E5", 1), ("E5", 2), ("E5", 1), ("G5", 1), ("C5", 1.5), ("D5", .5), ("E5", 4),
         ("F5", 1), ("F5", 1), ("F5", 1.5), ("F5", .5), ("F5", 1), ("E5", 1), ("E5", 1), ("E5", .5), ("E5", .5),
         ("E5", 1), ("D5", 1), ("D5", 1), ("E5", 1), ("D5", 2), ("G5", 2),
         ("E5", 1), ("E5", 1), ("E5", 2), ("E5", 1), ("E5", 1), ("E5", 2), ("E5", 1), ("G5", 1), ("C5", 1.5), ("D5", .5), ("E5", 4),
         ("F5", 1), ("F5", 1), ("F5", 1.5), ("F5", .5), ("F5", 1), ("E5", 1), ("E5", 1), ("E5", .5), ("E5", .5),
         ("G5", 1), ("G5", 1), ("F5", 1), ("D5", 1), ("C5", 4)]
    arm = ["C", "C", "C", "C", "F", "C", "D7", "G", "C", "C", "C", "C", "F", "C", "G7", "C"]
    bpm = 150
    def construir(pista):
        seg = 60 / bpm
        tocar(pista, m, bpm, lambda f, d: suma(0.6 * cajita(f, d), 0.5 * campana(f, 1.2)), octava=0, vol=0.5)
        acordes(pista, arm, bpm, 4, vol_pad=0.07, vol_bajo=0.45, patron_bajo=[(0, 0), (1, 2)])
        for c in range(16):
            for k in range(8): mezclar(pista, cascabeles(0.1), (c * 4 + k * 0.5) * seg, 0.12 if k % 2 == 0 else 0.07)
            mezclar(pista, bombo(0.7), c * 4 * seg, 0.4); mezclar(pista, bombo(0.5), (c * 4 + 2) * seg, 0.3)
    return cancion(64 * 60 / bpm, construir)


# ============================================================================= EFECTOS
def arpegio(notas, sep, inst=campana, dur=1.2, vol=1.0):
    x = np.zeros(int((sep * len(notas) + dur) * SR))
    for i, n in enumerate(notas): mezclar(x, inst(hz(n), dur), i * sep, vol)
    return x


def efectos():
    print("Efectos:")
    guardar("recoger", arpegio(["E6", "B6"], 0.07, dur=0.8) + 0.3 * np.pad(cascabeles(0.25), (0, int(0.9 * SR))) [: int((0.14 + 0.8) * SR)])
    x = arpegio(["C6", "E6", "G6", "C7", "E7"], 0.045, dur=1.4)                      # destello mágico al colocar
    sh = filtro(ruido(len(x) / SR), 6000, 14000) * env(len(x), 0.05, 1.0)
    guardar("colocar", x + 0.25 * sh)
    f = np.zeros(int(2.2 * SR))                                                       # fanfarria de etapa completa
    for i, n in enumerate(["C5", "E5", "G5"]): mezclar(f, suma(cajita(hz(n), 0.3), 0.5 * campana(hz(n) * 2, 0.8)), i * 0.11)
    for n in ("C5", "E5", "G5", "C6"): mezclar(f, suma(cajita(hz(n), 1.5), 0.6 * campana(hz(n) * 2, 1.8)), 0.36, 0.6)
    mezclar(f, cascabeles(0.5), 0.36, 0.4)
    guardar("etapa", f)
    for i in range(3):                                                                # pasos en madera
        t = tiempo(0.12); p = rng.uniform(0.85, 1.15)
        x = np.sin(2 * np.pi * 110 * p * t) * np.exp(-t * 45) + 0.6 * filtro(ruido(0.12), 200, 2500 * p) * np.exp(-t * 60)
        guardar(f"paso_madera{i + 1}", x, 0.7)
    for i in range(3):                                                                # pasos en nieve (crujido)
        n = int(0.16 * SR); x = np.zeros(n)
        for _ in range(28):
            g = filtro(ruido(0.012), 1200, 6000) * np.hanning(int(0.012 * SR))
            mezclar(x, g, rng.uniform(0, 0.13), rng.uniform(0.3, 1.0))
        guardar(f"paso_nieve{i + 1}", x * env(n, 0.01, 0.16), 0.7)
    t = tiempo(0.25)                                                                  # salto: "fwip" hacia arriba
    guardar("salto", np.sin(2 * np.pi * np.cumsum(300 + 500 * t / 0.25) / SR) * env(len(t), 0.01, 0.2) * 0.6 + 0.3 * filtro(ruido(0.25), 800, 4000) * env(len(t), 0.02, 0.15))
    n = int(0.35 * SR); x = np.zeros(n)                                               # lanzar: "whoosh" (barrido de ruido)
    for k in range(7):
        seg = filtro(ruido(0.35), 300 + k * 350, 700 + k * 500)
        ven = np.exp(-((np.arange(n) / n - (k + 0.5) / 7) ** 2) / 0.01)
        x += seg * ven
    guardar("lanzar", x, 0.6)
    t = tiempo(0.3)                                                                   # impacto de bola de nieve: "puf"
    guardar("impacto_nieve", filtro(ruido(0.3), 100, 1800) * np.exp(-t * 14) + 0.5 * np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30))
    x = np.zeros(int(0.2 * SR)); mezclar(x, madera(1400), 0); mezclar(x, madera(1100, 0.8), 0.09)
    guardar("clac", x)                                                                # mandíbula del cascanueces
    x = np.zeros(int(1.2 * SR))                                                       # ¡alerta! (te vieron)
    for n in ("B5", "C6", "F6"): mezclar(x, campana(hz(n), 1.0), 0, 0.5)
    mezclar(x, bombo(), 0, 0.8)
    t = tiempo(0.25); mezclar(x, np.sin(2 * np.pi * np.cumsum(500 + 1200 * t / 0.25) / SR) * env(len(t), 0.005, 0.3), 0, 0.3)
    guardar("alerta", x)
    x = np.zeros(int(2.4 * SR))                                                       # atrapado: "wah wah waaah"
    for i, (n, d) in enumerate((("G4", .4), ("F#4", .4), ("F4", .4), ("E4", 1.1))):
        t = tiempo(d + 0.1); f0 = hz(n) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t) * (t > 0.2))
        onda = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f0) / SR)
        mezclar(x, filtro(onda, alto=1400) * env(len(t), 0.02, d * 1.3), i * 0.42)
    guardar("atrapado", x)
    t = tiempo(1.2)                                                                   # aturdido: "boing" + pajaritos
    x = np.sin(2 * np.pi * np.cumsum(330 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 3)) / SR) * np.exp(-t * 3)
    for k in range(5):
        tt = tiempo(0.09); mezclar(x, np.sin(2 * np.pi * np.cumsum(2600 + 900 * tt / 0.09) / SR) * env(len(tt), 0.005, 0.09), 0.3 + k * 0.16, 0.25)
    guardar("aturdido", x)
    t = tiempo(0.9)                                                                   # despertar: crujido de madera + clac
    cr = np.sign(np.sin(2 * np.pi * (35 + 25 * np.sin(2 * np.pi * 1.3 * t)) * t)) * filtro(ruido(0.9), 300, 2500)
    x = filtro(cr, 200, 3000) * env(len(t), 0.1, 0.9); mezclar(x, madera(1300), 0.75, 1.5)
    guardar("despertar", x)
    n = int(0.45 * SR); x = np.zeros(n)                                               # papel (abrir nota)
    for _ in range(40): mezclar(x, filtro(ruido(0.02), 2000, 8000) * np.hanning(int(0.02 * SR)), rng.uniform(0, 0.42), rng.uniform(0.2, 1))
    guardar("papel", x, 0.6)
    t = tiempo(0.03); guardar("tick", np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 200), 0.4)   # avanzar texto
    x = np.zeros(int(0.9 * SR))                                                       # reno sacudiendo cascabeles
    for k in range(6): mezclar(x, cascabeles(0.12), k * 0.11, 1 - k * 0.12)
    guardar("reno", x)
    t = tiempo(0.18); guardar("soltar", np.sin(2 * np.pi * 140 * t) * np.exp(-t * 30) + 0.3 * filtro(ruido(0.18), 200, 1500) * np.exp(-t * 40), 0.6)


# ============================================================================= AMBIENTE (bucles)
def ambiente():
    print("Ambiente:")
    # chimenea: retumbo grave + chasquidos al azar
    d = 8.5; n = int(d * SR)
    x = filtro(ruido(d), 30, 300) * 0.5
    for _ in range(140):
        L = rng.uniform(0.003, 0.02); c = filtro(ruido(L), 1000, 7000) * np.exp(-np.arange(int(L * SR)) / SR * 300)
        mezclar(x, c, rng.uniform(0, d - 0.05), rng.uniform(0.2, 1.0))
    guardar("fuego", bucle(x, 0.5), 0.7)
    # viento: ruido cuyo filtro y volumen cambian lento (por pedacitos que se solapan)
    d = 12.5; n = int(d * SR); x = np.zeros(n); paso = int(0.1 * SR); ven = np.hanning(2 * paso)
    for k, i in enumerate(range(0, n - 2 * paso, paso)):
        s = k * 0.1
        centro = 450 + 250 * np.sin(2 * np.pi * s / 6.25) + 120 * np.sin(2 * np.pi * s / 2.5)
        vol = 0.55 + 0.45 * np.sin(2 * np.pi * s / 12.5 + 1)
        x[i:i + 2 * paso] += filtro(ruido(2 * paso / SR), centro * 0.6, centro * 1.6) * ven * vol
    guardar("viento", bucle(x, 0.5), 0.6)
    # máquina: zumbido eléctrico + golpe metálico rítmico + vapor
    d = 6.9; t = tiempo(d)
    x = 0.4 * np.sin(2 * np.pi * 55 * t) + 0.2 * np.sin(2 * np.pi * 110 * t) + 0.05 * np.sign(np.sin(2 * np.pi * 55 * t))
    for k in range(8):
        tt = tiempo(0.25); golpe = (np.sin(2 * np.pi * 420 * tt) + 0.6 * np.sin(2 * np.pi * 1130 * tt)) * np.exp(-tt * 25)
        mezclar(x, golpe, k * 0.8, 0.5)
    mezclar(x, filtro(ruido(1.2), 2500, 9000) * env(int(1.2 * SR), 0.3, 1.2), 3.0, 0.3)
    guardar("maquina", bucle(x, 0.5), 0.6)


# ----------------------------------------------------------------------------- sonidos extra (25-nov)
# Van en su propia función con su PROPIA semilla: así regenerar estos no cambia los sonidos anteriores.
def voz(f, dur=0.07, formante=1.0, timbre="elfo"):
    """Una 'sílaba' de voz de caricatura (estilo Animal Crossing): tono corto con 2 resonancias de vocal."""
    t = tiempo(dur)
    f0 = f * (1 + 0.04 * np.sin(2 * np.pi * 18 * t))                      # temblorcito de voz
    fase = 2 * np.pi * np.cumsum(f0) / SR
    if timbre == "madera":                                                 # cascanueces: golpecito hueco
        onda = np.sign(np.sin(fase)) * 0.5 + 0.5 * np.sin(fase * 2)
        onda = filtro(onda, 300, 2200)
    else:
        onda = sum(np.sin(fase * k) / k ** (1.3 if timbre == "elfo" else 0.9) for k in range(1, 9))
        onda = filtro(onda, 120 * formante, 2600 * formante)
    return onda * env(len(t), 0.006, dur * 0.9)


def extras():
    global rng
    guardado = rng; rng = np.random.default_rng(25)
    print("Extras:")
    # voces al escribir: 4 sílabas por personaje (UIHistoria elige una al azar cada 2 letras)
    for i, n in enumerate(("A5", "C6", "D6", "E6")): guardar(f"voz_elfo{i + 1}", voz(hz(n), 0.06, 1.3), 0.5)
    for i, n in enumerate(("C3", "D3", "E3", "G3")): guardar(f"voz_santa{i + 1}", voz(hz(n), 0.09, 0.7, "santa"), 0.55)
    for i, n in enumerate(("E4", "G4", "A4", "B4")): guardar(f"voz_cas{i + 1}", voz(hz(n), 0.05, 1.0, "madera"), 0.5)
    for i, n in enumerate(("E6", "G6", "A6", "B6")):                      # narración / notas: cajita musical suave
        t = tiempo(0.12); guardar(f"voz_narr{i + 1}", np.sin(2 * np.pi * hz(n) * t) * np.exp(-t * 40) + 0.3 * np.sin(4 * np.pi * hz(n) * t) * np.exp(-t * 60), 0.35)
    # SUSTO: un cascanueces despierta (golpe grave + acorde disonante que sube + clac)
    x = np.zeros(int(2.0 * SR))
    mezclar(x, bombo(1.2), 0, 1.0)
    t = tiempo(1.6)
    for f in (hz("C3"), hz("F#3"), hz("C4"), hz("C#4")):
        sube = f * (1 + 0.06 * t)
        mezclar(x, filtro(np.sign(np.sin(2 * np.pi * np.cumsum(sube) / SR)), alto=1800) * env(len(t), 0.25, 1.4), 0.05, 0.22)
    mezclar(x, madera(1300, 1.3), 0.0); mezclar(x, madera(1000, 1.1), 0.12)
    guardar("susto", x, 0.8)
    # pasos del cascanueces: TOC de madera + rechinido de resorte
    for i in range(2):
        t = tiempo(0.22); p = (1.0, 0.88)[i]
        x = 0.9 * np.sin(2 * np.pi * 180 * p * t) * np.exp(-t * 40) + 0.7 * filtro(ruido(0.22), 600 * p, 3000 * p) * np.exp(-t * 55)
        mezclar(x, np.sin(2 * np.pi * np.cumsum(900 + 400 * np.sin(2 * np.pi * 14 * tiempo(0.12))) / SR) * env(int(0.12 * SR), 0.01, 0.12), 0.05, 0.12)
        guardar(f"paso_cas{i + 1}", x, 0.7)
    # te perdió de vista: escala que baja suave ("uf")
    x = arpegio(["G5", "E5", "C5"], 0.09, dur=0.9); guardar("escapaste", x, 0.6)
    # galleta: crujido + campanita
    n = int(0.5 * SR); x = np.zeros(n)
    for _ in range(18): mezclar(x, filtro(ruido(0.015), 1500, 7000) * np.hanning(int(0.015 * SR)), rng.uniform(0, 0.12), rng.uniform(0.4, 1))
    mezclar(x, arpegio(["A6", "E7"], 0.06, dur=0.4), 0.1, 0.6)
    guardar("galleta", x, 0.75)
    # poder de galleta: arpegio grande hacia arriba + cascabeles + brillo
    x = arpegio(["C5", "E5", "G5", "C6", "E6", "G6", "C7"], 0.06, dur=1.6)
    x = np.pad(x, (0, int(0.6 * SR))); mezclar(x, cascabeles(0.8), 0.1, 0.5)
    mezclar(x, filtro(ruido(1.5), 6000, 14000) * env(int(1.5 * SR), 0.3, 1.5), 0.2, 0.25)
    guardar("poder", x)
    # instalar refacción: matraca (clics rápidos) + golpe metálico
    x = np.zeros(int(0.8 * SR))
    for k in range(7): mezclar(x, filtro(ruido(0.02), 2000, 9000) * np.exp(-tiempo(0.02) * 200), k * 0.05, 0.7)
    t = tiempo(0.6); metal = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((520, 6), (1370, 9), (2410, 12), (3800, 16)))
    mezclar(x, metal, 0.38, 0.6)
    guardar("instalar", x, 0.75)
    # máquina reparada: motor que se apaga (baja de tono) + campanita de "listo"
    t = tiempo(1.6); f = 140 * np.exp(-t * 1.2) + 30
    x = filtro(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), alto=900) * env(len(t), 0.01, 1.5) * 0.5
    x = np.pad(x, (0, int(1.2 * SR))); mezclar(x, arpegio(["C6", "G6", "C7"], 0.1, dur=1.2), 1.2, 0.8)
    guardar("reparada", x)
    # campanada del reloj (aviso de la hora)
    x = np.zeros(int(3.0 * SR))
    for k, n in enumerate(("E5", "C5")): mezclar(x, campana(hz(n), 2.4) + 0.5 * campana(hz(n) * 0.5, 2.4), k * 0.55, 0.8)
    guardar("campanada", x, 0.7)
    # menú: "fwip" de cambio de elfo y pausa (abrir/cerrar)
    t = tiempo(0.16); guardar("cambio", np.sin(2 * np.pi * np.cumsum(700 + 900 * t / 0.16) / SR) * env(len(t), 0.005, 0.15) + 0.2 * filtro(ruido(0.16), 2000, 8000) * env(len(t), 0.02, 0.1), 0.5)
    guardar("pausa", arpegio(["E6", "C6"], 0.06, inst=cajita, dur=0.5), 0.5)
    # trineo de Santa: muchos cascabeles que se acercan (crescendo)
    x = np.zeros(int(4.0 * SR))
    for k in range(26): mezclar(x, cascabeles(0.14), k * 0.14, 0.3 + 0.7 * k / 25)
    guardar("trineo", x * env(len(x), 0.05, 6.0), 0.8)
    # árbol se enciende: zumbido eléctrico que sube + chispitas
    t = tiempo(1.4); x = np.sin(2 * np.pi * np.cumsum(60 + 180 * t / 1.4) / SR) * env(len(t), 0.4, 2.0) * 0.4
    for _ in range(25): mezclar(x, campana(rng.uniform(2000, 4500), 0.3), rng.uniform(0.3, 1.2), rng.uniform(0.05, 0.2))
    guardar("encender", x, 0.7)
    # congelar: crujido de hielo que crece + campanitas frías agudas
    n = int(1.3 * SR); x = np.zeros(n)
    for k in range(70):
        tt = rng.uniform(0, 0.9); mezclar(x, filtro(ruido(0.012), 3000, 12000) * np.hanning(int(0.012 * SR)), tt, 0.3 + tt)
    for k, nota in enumerate(("E7", "B6", "G7", "D7")): mezclar(x, campana(hz(nota), 0.9), 0.5 + k * 0.08, 0.35)
    t = tiempo(1.0); mezclar(x, np.sin(2 * np.pi * np.cumsum(1800 - 900 * t) / SR) * env(len(t), 0.4, 0.8) * 0.15, 0.1)
    guardar("congelar", x, 0.8)
    # descongelar: el hielo se rompe (golpe + vidrios que caen)
    n = int(1.0 * SR); x = np.zeros(n)
    t = tiempo(0.3); mezclar(x, filtro(ruido(0.3), 800, 9000) * np.exp(-t * 18), 0, 1.0)
    for k in range(22):
        f = rng.uniform(2500, 6000); tt = tiempo(0.25)
        mezclar(x, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 30), 0.05 + rng.uniform(0, 0.6), rng.uniform(0.1, 0.35))
    guardar("descongelar", x, 0.8)
    rng = guardado


def fase9():
    """Sonidos de la Fase 9 (semilla propia 26 => no cambia ningún sonido anterior).
    Uso: cd Herramientas && python3 -c "import generar_audio as g; g.fase9()" """
    global rng
    guardado = rng; rng = np.random.default_rng(26)
    print("Fase 9:")
    # recarga de linterna: zumbido que sube + 4 bips (las 4 rayitas)
    t = tiempo(0.9); x = np.sin(2 * np.pi * np.cumsum(200 + 500 * t / 0.9) / SR) * env(len(t), 0.05, 0.4) * 0.35
    for k in range(4): mezclar(x, cajita(hz(("C6", "E6", "G6", "C7")[k]), 0.4), 0.15 + k * 0.15, 0.6)
    guardar("recarga", x, 0.6)
    # pila baja: dos bips graves descendentes tipo "uh-oh"
    x = np.zeros(int(0.7 * SR))
    for k, f in enumerate((660, 440)):
        t = tiempo(0.18); mezclar(x, np.sign(np.sin(2 * np.pi * f * t)) * 0.3 * env(len(t), 0.005, 0.15), k * 0.22, 0.7)
    guardar("pila_baja", filtro(x, None, 3500), 0.55)
    # apagón: chispazo eléctrico + zumbido que muere (baja de tono) + golpe grave
    n = int(2.2 * SR); x = np.zeros(n)
    for k in range(18): mezclar(x, filtro(ruido(0.02), 2000, 9000) * np.hanning(int(0.02 * SR)), rng.uniform(0, 0.6), rng.uniform(0.3, 0.8))
    t = tiempo(1.8); mezclar(x, (np.sin(2 * np.pi * np.cumsum(120 - 90 * t / 1.8) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(240 - 180 * t / 1.8) / SR)) * np.exp(-t * 1.6) * 0.5, 0.2)
    t = tiempo(0.8); mezclar(x, np.sin(2 * np.pi * 55 * t) * np.exp(-t * 6), 0.55, 0.9)
    guardar("apagon", x, 0.9)
    # regresa la luz: "clac" de interruptor + zumbido que sube + acorde brillante
    n = int(1.6 * SR); x = np.zeros(n)
    t = tiempo(0.05); mezclar(x, filtro(ruido(0.05), 1000, 6000) * np.exp(-t * 80), 0, 1.0)
    t = tiempo(1.0); mezclar(x, np.sin(2 * np.pi * np.cumsum(60 + 60 * t) / SR) * env(len(t), 0.3, 0.6) * 0.4, 0.05)
    for k, nota in enumerate(("C5", "E5", "G5", "C6")): mezclar(x, campana(hz(nota), 1.0), 0.35 + k * 0.05, 0.3)
    guardar("luz_vuelve", x, 0.75)
    # ventisca: viento fuerte en bucle (ruido con filtro que silba y ráfagas)
    dur = 8.0; n = int(dur * SR); x = np.zeros(n); paso = int(0.5 * SR)
    for i in range(0, n - paso, paso // 2):
        c = rng.uniform(300, 1400); trozo = filtro(ruido(1.0)[:paso], c * 0.6, c * 1.6) * np.hanning(paso) * rng.uniform(0.6, 1.0)
        x[i:i + paso] += trozo
    x += 0.35 * filtro(ruido(dur)[:n], 80, 400)
    guardar("ventisca", bucle(x, 0.5), 0.8)
    # interferencia de la brújula: estática + "uiii" que tiembla
    t = tiempo(0.6); x = filtro(ruido(0.6), 1500, 7000) * 0.35 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 23 * t)))
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(1200 + 400 * np.sin(2 * np.pi * 9 * t)) / SR)
    guardar("interferencia", x * env(len(t), 0.02, 0.2), 0.45)
    # recoger nieve: "crunch" de puño en la nieve
    t = tiempo(0.25); x = filtro(ruido(0.25), 300, 3000) * env(len(t), 0.01, 0.2)
    for k in range(6): mezclar(x, filtro(ruido(0.01), 1500, 6000), rng.uniform(0, 0.15), 0.6)
    guardar("recoger_nieve", x, 0.6)
    # sin bolas: "pff" vacío
    t = tiempo(0.2); guardar("sin_bolas", filtro(ruido(0.2), 200, 1200) * env(len(t), 0.01, 0.15) + 0.2 * np.sin(2 * np.pi * 150 * t) * np.exp(-t * 20), 0.4)
    # caja sorpresa: manivela (clics) + ¡BOING! de resorte + bocina
    n = int(1.6 * SR); x = np.zeros(n)
    for k in range(6): mezclar(x, madera(2600, 0.5), k * 0.05, 0.5)
    t = tiempo(1.0); f = 220 + 160 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3)
    mezclar(x, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5), 0.32, 1.0)
    t = tiempo(0.5); mezclar(x, (np.sign(np.sin(2 * np.pi * 330 * t)) * 0.4 + np.sin(2 * np.pi * 495 * t) * 0.4) * env(len(t), 0.01, 0.3), 0.4, 0.5)
    guardar("boing", filtro(x, None, 7000), 0.95)
    # medalla: fanfarria corta con campanas
    x = arpegio(["C5", "E5", "G5", "C6", "E6", "G6"], 0.08, dur=1.8)
    mezclar(x, cascabeles(0.6, 0.6), 0.45, 0.5)
    guardar("medalla", x, 0.85)
    rng = guardado


if __name__ == "__main__":
    print("Música:")
    guardar("musica_titulo", noche_de_paz(), 0.8)
    guardar("musica_taller", we_wish(), 0.8)
    guardar("musica_persecucion", carol_persecucion(), 0.85)
    guardar("musica_final", jingle_final(), 0.8)
    efectos()
    ambiente()
    extras()
    print("Listo ->", os.path.abspath(SALIDA))
