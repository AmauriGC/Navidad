"""
Música del TRÁILER (60 s): "Carol of the Bells" (Mykola Leontovych, 1914, dominio público) en versión épica.
Todo sintetizado con numpy (mismas herramientas que generar_audio.py). Sale en estéreo a Library/Trailer/musica.wav.

Estructura (1 compás de 3/4 = 1 segundo, negra = 180 bpm):
   0-14 s  INTRO      campanitas y caja musical con el ostinato, colchón suave, sube un "riser" al final
  14 s     BRAAM      golpe grave + platillo: empieza la acción (tarjeta "IMPOSIBLE")
  14-30 s  ACCIÓN 1   tambores tipo taiko, cuerdas con el ostinato, bajo que desciende G-F-Eb-D
  30-44 s  ACCIÓN 2   entran las otras voces (D5, G5), redobles, más intensidad
  44-52 s  CLÍMAX     todo junto; en 48 el acorde cambia a SOL MAYOR (las luces del árbol)
  52 s     GOLPE FINAL y cola de campanas para el título
Uso:  python3 Herramientas/trailer_musica.py
"""
import os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import generar_audio as g
from generar_audio import SR, tiempo, filtro, env, hz, campana, cajita, bajo, pad, bombo, madera

rng = np.random.default_rng(2026)
DUR = 61.0
SEG = 1 / 3            # una negra
COMPAS = 1.0           # 3 negras


def pista():
    return np.zeros(int(DUR * SR) + SR * 4)


def poner(dest, x, t, vol=1.0):
    g.mezclar(dest, x, t, vol)


def ruido(seg):
    return rng.uniform(-1, 1, int(seg * SR))


# ----------------------------------------------------------------------------- instrumentos nuevos
def cuerdas(f, dur, brillo=2500):
    """Sierra con 3 osciladores desafinados + vibrato, filtrada: suena a sección de cuerdas."""
    t = tiempo(dur + 0.25)
    x = np.zeros_like(t)
    for d in (-0.25, 0.0, 0.3):
        fase = (f * (1 + d / 100) * t + 0.002 * np.sin(2 * np.pi * 5.2 * t))
        x += 2 * (fase - np.floor(fase + 0.5))
    a = np.clip(t / 0.03, 0, 1) * np.clip((dur + 0.25 - t) / 0.25, 0, 1)
    return filtro(x * a, alto=brillo) * 0.5


def coro(frecs, dur):
    """'Aah' de coro: pad con formantes (filtro de banda alrededor de 700 Hz) y entrada lenta."""
    t = tiempo(dur + 1.0)
    x = np.zeros_like(t)
    for f in frecs:
        for d in (-0.6, 0.0, 0.6):
            fase = (f + d) * t
            x += 2 * np.abs(2 * (fase - np.floor(fase + 0.5))) - 1
    a = np.clip(t / 0.8, 0, 1) * np.clip((dur + 1.0 - t) / 1.0, 0, 1)
    return filtro(x * a, 300, 1500)


def taiko(vol=1.0, f0=62):
    t = tiempo(0.9)
    f = f0 + 70 * np.exp(-t * 25)
    cuerpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    golpe = filtro(ruido(0.9), 100, 1200) * np.exp(-t * 40)
    return vol * (cuerpo + 0.35 * golpe)


def caja(vol=1.0):
    """Redoblante: ruido brillante + tono corto."""
    t = tiempo(0.25)
    x = filtro(ruido(0.25), 1200, 9000) * np.exp(-t * 22) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return vol * x


def platillo(dur=3.0, vol=1.0):
    t = tiempo(dur)
    return vol * filtro(ruido(dur), 4000, 16000) * np.exp(-3 * t / dur) * np.clip(t / 0.005, 0, 1)


def braam(f=hz("G1"), dur=3.5):
    """Golpe de cine: metales graves saturados + subgrave."""
    t = tiempo(dur)
    x = np.zeros_like(t)
    for d in (-0.5, 0, 0.5, 12.0):
        fase = (f * (2 ** (d / 12)) if d == 12.0 else f + d) * t
        x += 2 * (fase - np.floor(fase + 0.5))
    x = np.tanh(2.5 * x) * np.exp(-1.2 * t) * np.clip(t / 0.02, 0, 1)
    sub = np.sin(2 * np.pi * f * t) * np.exp(-1.0 * t)
    return filtro(x, alto=900) * 0.7 + sub * 0.8


def riser(dur=4.0):
    """Ruido que sube de tono y volumen hasta el golpe."""
    n = int(dur * SR)
    x = ruido(dur)
    out = np.zeros(n)
    trozos = 40
    for i in range(trozos):        # filtro que se va abriendo por trozos
        a, b = i * n // trozos, (i + 1) * n // trozos
        k = i / trozos
        seg = filtro(x[a:b] if b - a > 64 else np.zeros(64), 300 + 3000 * k, 1500 + 9000 * k)
        out[a:b] = seg[: b - a]
    return out * np.linspace(0, 1, n) ** 2


# ----------------------------------------------------------------------------- el villancico
# ostinato de 1 compás: negra, corchea, corchea, negra  (n1 n2 n1 n3)
def ostinato(dest, inst, n1, n2, n3, t0, compases, vol, oct=0):
    for c in range(compases):
        t = t0 + c * COMPAS
        for nota, dt, dur in ((n1, 0, SEG), (n2, SEG, SEG / 2), (n1, SEG * 1.5, SEG / 2), (n3, SEG * 2, SEG)):
            poner(dest, inst(hz(nota) * 2 ** oct, dur), t + dt, vol)


BAJOS = ["G", "F", "Eb", "D"]           # descenso cada 2 compases
ACORDES = {"G": ("G3", "Bb3", "D4"), "F": ("F3", "A3", "C4"), "Eb": ("Eb3", "G3", "Bb3"), "D": ("D3", "F#3", "A3"),
           "GM": ("G3", "B3", "D4")}


def construir():
    L, R = pista(), pista()
    def ambos(x, t, vol=1.0, pan=0.0):      # pan -1 izquierda, +1 derecha
        poner(L, x, t, vol * (1 - max(0, pan)))
        poner(R, x, t, vol * (1 + min(0, pan)))

    # ---------------- INTRO 0-14: campanitas suaves, crecen poco a poco
    for c in range(14):
        v = 0.18 + 0.22 * c / 14
        t = c * COMPAS
        for nota, dt, dur in (("Bb5", 0, SEG), ("A5", SEG, SEG / 2), ("Bb5", SEG * 1.5, SEG / 2), ("G5", SEG * 2, SEG)):
            ambos(campana(hz(nota), 1.4), t + dt, v, pan=-0.3)
            if c >= 6: ambos(cajita(hz(nota) / 2, 1.2), t + dt, v * 0.6, pan=0.3)
    for i in range(7):                       # colchón y bajo muy suaves (2 compases por acorde)
        a = BAJOS[i % 4]
        ambos(pad([hz(n) for n in ACORDES[a]], 2.0), i * 2.0, 0.05 + 0.03 * i / 7)
        if i >= 3: ambos(bajo(hz(a + "2"), 1.9), i * 2.0, 0.25)
    ambos(riser(3.6), 10.2, 0.35)            # sube hasta el golpe
    for k in range(4):                       # latidos antes del golpe
        ambos(taiko(0.5, 50), 11.0 + k * 0.75, 1.0)

    # ---------------- BRAAM 14
    ambos(braam(), 14.0, 1.0)
    ambos(platillo(3.5), 14.0, 0.35)
    ambos(taiko(1.0, 45), 14.0, 1.0)

    # ---------------- ACCIÓN 14-44
    for c in range(14, 44):
        t = c * COMPAS
        fuerte = c >= 30
        # cuerdas con el ostinato (dos octavas)
        for nota, dt, dur in (("Bb4", 0, SEG), ("A4", SEG, SEG / 2), ("Bb4", SEG * 1.5, SEG / 2), ("G4", SEG * 2, SEG)):
            ambos(cuerdas(hz(nota), dur * 0.95), t + dt, 0.22 if fuerte else 0.18, pan=-0.4)
            ambos(cuerdas(hz(nota) / 2, dur * 0.95, 1500), t + dt, 0.16, pan=0.4)
            ambos(campana(hz(nota) * 2, 0.8), t + dt, 0.10 if fuerte else 0.07, pan=0.2)
        if fuerte:   # segunda y tercera voz
            for nota, dt, dur in (("D5", 0, SEG), ("C5", SEG, SEG / 2), ("D5", SEG * 1.5, SEG / 2), ("Bb4", SEG * 2, SEG)):
                ambos(cuerdas(hz(nota), dur * 0.95, 3500), t + dt, 0.15, pan=0.5)
        if c >= 37:
            for nota, dt, dur in (("G5", 0, SEG), ("F5", SEG, SEG / 2), ("G5", SEG * 1.5, SEG / 2), ("D5", SEG * 2, SEG)):
                ambos(cuerdas(hz(nota), dur * 0.95, 4500), t + dt, 0.12, pan=-0.5)
        # tambores: taiko en el 1 (y en el 3 con fuerza), madera "clac" de cascanueces
        ambos(taiko(0.9, 55), t, 1.0)
        ambos(taiko(0.5, 70), t + SEG * 2, 1.0, pan=0.3)
        if fuerte:
            ambos(taiko(0.55, 75), t + SEG * 1.5, 1.0, pan=-0.3)
            ambos(caja(0.35), t + SEG, 1.0)
            ambos(caja(0.35), t + SEG * 2.5, 1.0)
        ambos(madera(1500, 0.25), t + SEG, 1.0, pan=0.5)
        ambos(madera(1900, 0.2), t + SEG * 2, 1.0, pan=-0.5)
        if c % 2 == 0:   # bajo y colchón cada 2 compases
            a = BAJOS[(c // 2) % 4]
            ambos(bajo(hz(a + "1"), 1.9), t, 0.55)
            ambos(bajo(hz(a + "2"), 1.9), t, 0.3)
            ambos(coro([hz(n) for n in ACORDES[a]], 2.0), t, 0.05 if not fuerte else 0.08)
    # golpes en los cambios de sección
    ambos(braam(hz("D2"), 2.5), 30.0, 0.6); ambos(platillo(2.5), 30.0, 0.3)
    for k in range(12):                      # redoble que crece hasta el clímax
        ambos(caja(0.15 + 0.5 * k / 12), 42.0 + k * SEG / 2, 1.0)
    ambos(riser(2.0), 42.0, 0.3)

    # ---------------- CLÍMAX 44-52 (en 48 cambia a SOL MAYOR: las luces del árbol)
    ambos(braam(), 44.0, 1.0); ambos(platillo(4.0), 44.0, 0.45)
    for c in range(44, 52):
        t = c * COMPAS
        mayor = c >= 48
        tercera = "B4" if mayor else "Bb4"
        for nota, dt, dur in ((tercera, 0, SEG), ("A4", SEG, SEG / 2), (tercera, SEG * 1.5, SEG / 2), ("G4", SEG * 2, SEG)):
            ambos(cuerdas(hz(nota), dur * 0.95, 4000), t + dt, 0.24, pan=-0.3)
            ambos(cuerdas(hz(nota) * 2, dur * 0.95, 5000), t + dt, 0.12, pan=0.3)
            ambos(campana(hz(nota) * 2, 1.0), t + dt, 0.16)
        ambos(taiko(1.0, 50), t, 1.0)
        ambos(taiko(0.7, 65), t + SEG, 1.0, pan=0.3)
        ambos(taiko(0.7, 65), t + SEG * 2, 1.0, pan=-0.3)
        ambos(caja(0.3), t + SEG * 1.5, 1.0)
        if c % 2 == 0:
            a = "GM" if mayor else BAJOS[(c // 2) % 4]
            raiz = "G" if mayor else a
            ambos(bajo(hz(raiz + "1"), 1.9), t, 0.6)
            ambos(coro([hz(n) for n in ACORDES[a]], 2.0), t, 0.12)
    ambos(platillo(3.0), 48.0, 0.35)

    # ---------------- GOLPE FINAL 52 y título
    ambos(braam(hz("G1"), 6.0), 52.0, 1.0)
    ambos(platillo(6.0), 52.0, 0.4)
    ambos(taiko(1.0, 40), 52.0, 1.0)
    ambos(coro([hz(n) for n in ACORDES["GM"]] + [hz("G4")], 7.0), 52.0, 0.12)
    for i, nota in enumerate(["G5", "B5", "D6", "G6"]):
        ambos(campana(hz(nota), 4.0), 52.3 + i * 0.35, 0.25, pan=(-0.4 + 0.27 * i))
    # eco final del ostinato, muy suave
    for c in range(55, 59):
        v = 0.12 * (59 - c) / 4
        for nota, dt, dur in (("B5", 0, SEG), ("A5", SEG, SEG / 2), ("B5", SEG * 1.5, SEG / 2), ("G5", SEG * 2, SEG)):
            ambos(campana(hz(nota), 1.5), c + dt, v, pan=0.3)
    ambos(madera(1700, 0.5), 59.2, 1.0)     # "clac" del cascanueces al final

    n = int(DUR * SR)
    return L[:n], R[:n]


def guardar_estereo(ruta, L, R, pico=0.9):
    m = max(np.max(np.abs(L)), np.max(np.abs(R)))
    L, R = L / m * pico, R / m * pico
    # compresión suave para que pegue más (tanh)
    L, R = np.tanh(L * 1.3) / np.tanh(1.3), np.tanh(R * 1.3) / np.tanh(1.3)
    fade = int(0.8 * SR)
    for x in (L, R): x[-fade:] *= np.linspace(1, 0, fade)
    datos = np.empty(2 * len(L)); datos[0::2], datos[1::2] = L, R
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((datos * 32767).astype(np.int16).tobytes())
    print("  ", ruta, f"{len(L) / SR:.1f} s")


if __name__ == "__main__":
    raiz = os.path.join(os.path.dirname(__file__), "..")
    L, R = construir()
    guardar_estereo(os.path.join(raiz, "Library", "Trailer", "musica.wav"), L, R)
