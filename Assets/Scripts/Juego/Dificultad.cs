using UnityEngine;

/// <summary>
/// NIVELES DE DIFICULTAD (Fácil, Medio, Difícil, Imposible). Clase ESTÁTICA: cualquier script la consulta con
/// Dificultad.Actual. Se elige en la pantalla que sale después de "Elige a tu elfo" y se guarda en PlayerPrefs.
///
/// ¿Qué cambia cada nivel?
///  - VIDAS: Fácil/Medio no tienen (te atrapan y solo pierdes la pieza). Difícil empieza con 3, Imposible con 1.
///    Si se acaban: derrota ("¡Te atraparon!").
///  - GALLETAS -> VIDA: en Difícil cada 2 galletas dan +1 vida; en Imposible cada 5. Tope: 5 vidas.
///  - CASCANUECES: multiplicadores de velocidad, vista, oído y tiempo aturdido; en Imposible despiertan una pieza antes.
///  - RELOJ: minutos reales hasta el amanecer (25 / 20 / 15 / 12; la historia 1.5 tiene 7 etapas).
///  - DESCARGAS DE SIETE (1.5): segundos entre descargas (180 / 120 / 90 / 60). En Fácil/Medio son suaves (solo
///    alertan un ratito) y la descarga 10 es un susto; en Difícil/Imposible son GRAVES (despiertan al cascanueces
///    dormido más cercano) y la descarga 10 = derrota por SOBRECARGA.
/// Medio = el juego como estaba antes (todos los multiplicadores en 1).
/// </summary>
public static class Dificultad
{
    public class Datos
    {
        public string nombre, descripcion;
        public Color color;
        public int vidas;               // 0 = sin vidas (no puedes perder por atrapado)
        public int galletasPorVida;     // 0 = las galletas no dan vidas
        public float velocidad, vista, oido, aturdido, minutos;
        public int despertarAntes;      // etapas antes (+) o después (-) que despiertan los cascanueces
        public float oscuridad;         // exposición (EV) que se le quita a la imagen: más negativo = más oscuro
        public float cadenciaNevados;   // segundos entre bolas de los cascanueces nevados (0 = no hay nevados)
        public float pilaSegundos;      // duración de la pila de la linterna (0 = luz infinita)
        public bool apagon;             // ¿hay apagón a las 3:00 AM si la Máquina 7 sigue rota?
        public float ventiscaMin, ventiscaMax;   // segundos entre ventiscas (0 = sin ventiscas)
        public int bolasMax;            // cuántas bolas de nieve caben en tus manos
        public int cajasSorpresa;       // cuántas cajas sorpresa se prenden (0 = ninguna)
        public float segundosDescarga;  // tiempo entre descargas de Siete (historia 1.5)
        public bool descargaGrave;      // Difícil/Imposible: despiertan cascanueces y la descarga 10 es derrota
        public float rastreoAfuera;     // v1.5: segundos que siguen tus HUELLAS si te escapas afuera (0 = te pierden en la puerta)
    }

    public const int MaxVidas = 5;

    public static readonly Datos[] Niveles =
    {
        new Datos { nombre = "Fácil", color = new Color(0.45f, 0.9f, 0.55f),
            descripcion = "Cascanueces lentos y despistados.\nTienes 25 minutos.\nSin vidas: solo te quitan la pieza.",
            vidas = 0, galletasPorVida = 0, velocidad = 0.8f, vista = 0.7f, oido = 0.7f, aturdido = 1.4f, minutos = 25f, despertarAntes = -1, oscuridad = 0f, cadenciaNevados = 0f, pilaSegundos = 0f, apagon = false, ventiscaMin = 0f, ventiscaMax = 0f, bolasMax = 6, cajasSorpresa = 0, segundosDescarga = 180f, descargaGrave = false },
        new Datos { nombre = "Medio", color = new Color(0.5f, 0.8f, 1f),
            descripcion = "La noche normal del taller.\nTienes 20 minutos.\nSin vidas: solo te quitan la pieza.",
            vidas = 0, galletasPorVida = 0, velocidad = 1f, vista = 1f, oido = 1f, aturdido = 1f, minutos = 20f, despertarAntes = 0, oscuridad = 0f, cadenciaNevados = 0f, pilaSegundos = 0f, apagon = false, ventiscaMin = 0f, ventiscaMax = 0f, bolasMax = 5, cajasSorpresa = 0, segundosDescarga = 120f, descargaGrave = false },
        new Datos { nombre = "Difícil", color = new Color(1f, 0.7f, 0.3f),
            descripcion = "Más oscuro, nevados afuera,\nlinterna con pila, ventiscas,\napagón y cajas sorpresa.\n15 min · 3 vidas · 2 galletas = +1",
            vidas = 3, galletasPorVida = 2, velocidad = 1.12f, vista = 1.15f, oido = 1.2f, aturdido = 0.85f, minutos = 15f, despertarAntes = 0, oscuridad = -0.55f, cadenciaNevados = 2.4f, pilaSegundos = 240f, apagon = true, ventiscaMin = 120f, ventiscaMax = 180f, bolasMax = 4, cajasSorpresa = 5, segundosDescarga = 90f, descargaGrave = true, rastreoAfuera = 7f },
        new Datos { nombre = "Imposible", color = new Color(1f, 0.35f, 0.35f),
            descripcion = "Casi a oscuras, pila corta,\nmás nevados y cajas, brújula\nloca y despiertan antes.\n12 min · 1 vida · 5 galletas = +1",
            vidas = 1, galletasPorVida = 5, velocidad = 1.25f, vista = 1.3f, oido = 1.4f, aturdido = 0.7f, minutos = 12f, despertarAntes = 1, oscuridad = -1.0f, cadenciaNevados = 1.7f, pilaSegundos = 150f, apagon = true, ventiscaMin = 90f, ventiscaMax = 120f, bolasMax = 3, cajasSorpresa = 8, segundosDescarga = 60f, descargaGrave = true, rastreoAfuera = 11f },
    };

    /// <summary>Índice elegido (0 Fácil .. 3 Imposible). Por defecto Medio.</summary>
    public static int Elegido
    {
        get { if (elegido < 0) elegido = Mathf.Clamp(PlayerPrefs.GetInt("Dificultad", 1), 0, Niveles.Length - 1); return elegido; }
        set { elegido = Mathf.Clamp(value, 0, Niveles.Length - 1); PlayerPrefs.SetInt("Dificultad", elegido); PlayerPrefs.Save(); }
    }
    static int elegido = -1;
    public static Datos Actual => Niveles[Elegido];
    public static bool ConVidas => Actual.vidas > 0;

    static bool aplicada;

    /// <summary>Aplica el nivel a la partida (cascanueces, reloj, vidas). Solo una vez por partida.</summary>
    public static void Aplicar()
    {
        if (aplicada) return;
        aplicada = true;
        var d = Actual;
        foreach (var c in Object.FindObjectsByType<Cascanueces>()) c.AplicarDificultad(d);
        var reloj = Object.FindAnyObjectByType<RelojAmanecer>();
        if (reloj != null) reloj.minutosReales = d.minutos;
        Vidas.Empezar(d.vidas);

        // CASCANUECES NEVADOS: están en la escena APAGADOS; se prenden los que tocan a este nivel
        foreach (var n in Object.FindObjectsByType<CascanuecesNevado>(FindObjectsInactive.Include))
        {
            bool activo = d.cadenciaNevados > 0f && Elegido >= n.desdeNivel;
            n.gameObject.SetActive(activo);
            if (activo) { n.cadencia = d.cadenciaNevados; if (Elegido >= 3) n.alcance *= 1.2f; }
        }

        // LINTERNA CON PILA y APAGÓN DE LAS 3 AM
        var jug = GameObject.FindGameObjectWithTag("Player");
        if (jug != null && d.pilaSegundos > 0f)
        {
            var lin = jug.GetComponent<Linterna>(); if (lin == null) lin = jug.AddComponent<Linterna>();
            lin.Configurar(d.pilaSegundos);
        }
        if (d.apagon && Object.FindAnyObjectByType<Apagon>() == null) new GameObject("Apagon").AddComponent<Apagon>();
        // BOLAS DE NIEVE: cuántas caben
        if (jug != null) { var lan = jug.GetComponent<LanzadorNieve>(); if (lan != null) { lan.maximo = d.bolasMax; lan.bolas = Mathf.Min(lan.bolas, lan.maximo); } }
        // CAJAS SORPRESA: están APAGADAS en la escena; se prenden las primeras N (en orden)
        var todas = Object.FindObjectsByType<CajaSorpresa>(FindObjectsInactive.Include);
        var lista = new System.Collections.Generic.List<CajaSorpresa>();
        foreach (var c in todas) { if (c.siempreActiva) c.gameObject.SetActive(true); else lista.Add(c); }   // la que cuida el fusible no cuenta
        var cajas = lista.ToArray();
        System.Array.Sort(cajas, (a, b) => string.CompareOrdinal(a.name, b.name));
        for (int i = 0; i < cajas.Length; i++) cajas[i].gameObject.SetActive(i < d.cajasSorpresa);
        if (d.ventiscaMin > 0f && Object.FindAnyObjectByType<Ventisca>() == null)
        {
            var gv = new GameObject("Ventisca");
            gv.AddComponent<Ventisca>().Configurar(d.ventiscaMin, d.ventiscaMax);
            gv.AddComponent<VentiscaBonita>();   // v1.5: copos grandes, ráfagas al ras del suelo y velo
        }

        // OSCURIDAD: baja la exposición del Global Volume (volume.profile es una COPIA en Play: no cambia el asset)
        if (d.oscuridad != 0f)
            foreach (var v in Object.FindObjectsByType<UnityEngine.Rendering.Volume>())
            {
                if (!v.isGlobal || v.sharedProfile == null) continue;
                UnityEngine.Rendering.Universal.ColorAdjustments ca;
                if (!v.profile.TryGet(out ca)) ca = v.profile.Add<UnityEngine.Rendering.Universal.ColorAdjustments>(true);
                ca.postExposure.overrideState = true;
                ca.postExposure.value += d.oscuridad;
                UnityEngine.Rendering.Universal.Vignette vi;
                if (v.profile.TryGet(out vi)) { vi.intensity.overrideState = true; vi.intensity.value = Mathf.Min(0.6f, vi.intensity.value + 0.08f - d.oscuridad * 0.1f); }
                break;
            }
    }

    /// <summary>La escena se recarga al reintentar: el DirectorJuego llama esto en su Start.</summary>
    public static void NuevaPartida() { aplicada = false; Vidas.Empezar(0); }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { elegido = -1; aplicada = false; }
}
