using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

/// <summary>
/// Una línea de la historia.
///  - Narracion: pantalla negra, texto centrado (como película).
///  - Dialogo: caja abajo con el nombre de quien habla.
///  - Nota: hoja de papel al centro (letreros, cartas, diarios).
/// </summary>
[Serializable]
public class Linea
{
    public enum Tipo { Narracion, Dialogo, Nota }
    public Tipo tipo;
    public string quien;     // en Dialogo: quién habla. En Nota: el título.
    [TextArea] public string texto;

    public static Linea N(string t) { return new Linea { tipo = Tipo.Narracion, texto = t }; }
    public static Linea D(string q, string t) { return new Linea { tipo = Tipo.Dialogo, quien = q, texto = t }; }
    public static Linea Nota(string titulo, string t) { return new Linea { tipo = Tipo.Nota, quien = titulo, texto = t }; }
}

/// <summary>
/// Muestra secuencias de líneas con efecto MÁQUINA DE ESCRIBIR.
/// [E] / [Enter] / [Espacio] / [Clic]: la primera vez completa el texto, la segunda pasa a la siguiente.
/// Mientras está abierta pone el juego en modo "Leyendo" (el elfo y los cascanueces se detienen).
/// </summary>
public class UIHistoria : MonoBehaviour
{
    static UIHistoria inst;
    public static bool Abierta { get { return inst != null && inst.abierta; } }

    public float letrasPorSegundo = 45f;

    RectTransform raiz;
    // narración
    CanvasGroup gNarr; Text tNarr;
    // diálogo
    CanvasGroup gDial; Text tQuien, tDial;
    // nota
    CanvasGroup gNota; Text tNotaTitulo, tNotaTexto;
    Text tContinuar;

    bool abierta;

    static UIHistoria Inst
    {
        get
        {
            if (inst != null) return inst;
            var rt = UIConstructor.Capa("Historia", 30);
            inst = rt.gameObject.AddComponent<UIHistoria>();
            inst.Construir(rt);
            return inst;
        }
    }

    void Construir(RectTransform rt)
    {
        raiz = rt;
        // ---- narración (fondo negro, texto centrado)
        var n = UIConstructor.PantallaCompleta("Narracion", rt);
        UIConstructor.Imagen(n, new Color(0.01f, 0.01f, 0.03f, 1f));
        gNarr = UIConstructor.Grupo(n, 0f);
        tNarr = UIConstructor.Texto(UIConstructor.Rect("Texto", n, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1300, 500)),
                                    "", 46, new Color(0.95f, 0.92f, 0.85f), TextAnchor.MiddleCenter);
        tNarr.lineSpacing = 1.2f;

        // ---- diálogo (caja abajo)
        var d = UIConstructor.Rect("Dialogo", rt, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(1400, 230), new Vector2(0, 170));
        UIConstructor.Imagen(d, new Color(0.04f, 0.05f, 0.1f, 0.88f));
        var borde = UIConstructor.Rect("Borde", d, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, 4), new Vector2(0, -2));
        UIConstructor.Imagen(borde, new Color(1f, 0.78f, 0.3f, 0.9f));
        gDial = UIConstructor.Grupo(d, 0f);
        tQuien = UIConstructor.Titulo(UIConstructor.Rect("Quien", d, new Vector2(0, 1), new Vector2(0, 1), new Vector2(600, 60), new Vector2(330, -40)),
                                     "", 36, new Color(1f, 0.8f, 0.35f), TextAnchor.MiddleLeft, FontStyle.Bold);
        tDial = UIConstructor.Texto(UIConstructor.Rect("Texto", d, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1320, 130), new Vector2(0, -20)),
                                    "", 34, Color.white, TextAnchor.UpperLeft);

        // ---- nota (papel)
        var p = UIConstructor.Rect("Nota", rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(900, 640));
        UIConstructor.Imagen(UIConstructor.PantallaCompleta("Oscurecer", p), new Color(0, 0, 0, 0f));
        var sombra = UIConstructor.Rect("Sombra", p, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(12, -12));
        UIConstructor.Imagen(sombra, new Color(0, 0, 0, 0.5f));
        var papel = UIConstructor.Rect("Papel", p, Vector2.zero, Vector2.one);
        papel.offsetMin = papel.offsetMax = Vector2.zero;
        UIConstructor.Imagen(papel, new Color(0.96f, 0.91f, 0.78f));
        var cinta = UIConstructor.Rect("Cinta", p, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(180, 44), new Vector2(0, 0));
        UIConstructor.Imagen(cinta, new Color(0.75f, 0.15f, 0.15f, 0.9f)).rectTransform.localRotation = Quaternion.Euler(0, 0, 3);
        gNota = UIConstructor.Grupo(p, 0f);
        tNotaTitulo = UIConstructor.Titulo(UIConstructor.Rect("Titulo", p, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(800, 80), new Vector2(0, -80)),
                                          "", 40, new Color(0.35f, 0.12f, 0.08f), TextAnchor.MiddleCenter, FontStyle.Bold);
        tNotaTexto = UIConstructor.Texto(UIConstructor.Rect("Texto", p, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(780, 440), new Vector2(0, -40)),
                                         "", 31, new Color(0.18f, 0.12f, 0.08f), TextAnchor.UpperLeft, FontStyle.Italic);
        tNotaTexto.lineSpacing = 1.15f;

        tContinuar = UIConstructor.Texto(UIConstructor.Rect("Continuar", rt, new Vector2(1, 0), new Vector2(1, 0), new Vector2(500, 50), new Vector2(-280, 40)),
                                         "[E] continuar", 26, new Color(1f, 1f, 1f, 0f), TextAnchor.MiddleRight);
        UIConstructor.Sombra(tContinuar);
    }

    // ------------------------------------------------------------------ API
    /// <summary>Muestra las líneas en orden. Al terminar llama alTerminar (puede ser null).</summary>
    public static void Mostrar(Linea[] lineas, Action alTerminar = null)
    {
        Inst.StartCoroutine(Inst.Secuencia(lineas, alTerminar));
    }

    /// <summary>Versión para usar dentro de otra corrutina: yield return UIHistoria.Esperar(lineas);</summary>
    public static IEnumerator Esperar(Linea[] lineas)
    {
        bool fin = false;
        Mostrar(lineas, () => fin = true);
        while (!fin) yield return null;
    }

    IEnumerator Secuencia(Linea[] lineas, Action alTerminar)
    {
        while (abierta) yield return null;   // si ya hay otra abierta, espera su turno
        abierta = true;
        var previo = Juego.Estado;
        if (previo == Juego.Modo.Jugando) Juego.Estado = Juego.Modo.Leyendo;
        yield return null;   // evita que la misma tecla E que abrió la nota la cierre

        CanvasGroup actual = null;
        foreach (var original in lineas)
        {
            // copia con el nombre del elfo elegido (no se modifica el guion original)
            var l = new Linea { tipo = original.tipo, quien = Guion.Personalizar(original.quien), texto = Guion.Personalizar(original.texto) };
            CanvasGroup g; Text t;
            if (l.tipo == Linea.Tipo.Narracion) { g = gNarr; t = tNarr; }
            else if (l.tipo == Linea.Tipo.Dialogo) { g = gDial; t = tDial; tQuien.text = l.quien; }
            else { g = gNota; t = tNotaTexto; tNotaTitulo.text = l.quien; }

            if (actual != g)
            {
                if (actual != null) yield return Alfa(actual, 0f, 0.2f);
                actual = g;
                t.text = "";
                if (l.tipo == Linea.Tipo.Nota) GestorAudio.Efecto("papel");
                yield return Alfa(g, 1f, l.tipo == Linea.Tipo.Narracion ? 0.6f : 0.2f);
            }

            // máquina de escribir: vamos mostrando más letras cada frame
            tContinuar.color = new Color(1, 1, 1, 0);
            float n = 0f;
            // VOZ al escribir: cada ~3 letras suena una "sílaba" corta (estilo Animal Crossing).
            // Santa = voz grave, el elfo = voz aguda, narración y notas = cajita musical suave.
            string voz = l.tipo != Linea.Tipo.Dialogo ? "voz_narr" : (l.quien == "Santa" ? "voz_santa" : "voz_elfo");
            int ultimaSilaba = -1; float siguienteVoz = 0f;
            while (n < l.texto.Length)
            {
                if (Avanzar()) { n = l.texto.Length; break; }
                n += Time.unscaledDeltaTime * letrasPorSegundo;
                t.text = TextoParcial(l.texto, (int)n);
                int silaba = (int)n / 3;
                if (silaba != ultimaSilaba && Time.unscaledTime >= siguienteVoz)
                {
                    ultimaSilaba = silaba; siguienteVoz = Time.unscaledTime + 0.055f;
                    GestorAudio.Voz(voz + UnityEngine.Random.Range(1, 5), l.tipo == Linea.Tipo.Dialogo ? 0.45f : 0.3f, 0.06f);
                }
                yield return null;
            }
            t.text = l.texto;
            yield return null;
            // esperar a que el jugador pase a la siguiente
            float parpadeo = 0f;
            while (!Avanzar())
            {
                parpadeo += Time.unscaledDeltaTime;
                tContinuar.color = new Color(1, 1, 1, 0.5f + 0.5f * Mathf.Sin(parpadeo * 4f));
                yield return null;
            }
            tContinuar.color = new Color(1, 1, 1, 0);
            GestorAudio.Efecto("tick", 0.6f);
            yield return null;
        }
        if (actual != null) yield return Alfa(actual, 0f, actual == gNarr ? 0.6f : 0.25f);

        if (Juego.Estado == Juego.Modo.Leyendo) Juego.Estado = previo == Juego.Modo.Leyendo ? Juego.Modo.Jugando : previo;
        abierta = false;
        if (alTerminar != null) alTerminar();
    }

    /// <summary>Corta el texto sin romper etiquetas de formato como &lt;b&gt; o &lt;color&gt;.</summary>
    static string TextoParcial(string s, int n)
    {
        var sb = new System.Text.StringBuilder();
        int visibles = 0; bool enEtiqueta = false;
        for (int i = 0; i < s.Length; i++)
        {
            char c = s[i];
            if (c == '<') enEtiqueta = true;
            if (enEtiqueta || visibles < n) sb.Append(c);
            if (!enEtiqueta) visibles++;
            if (c == '>') enEtiqueta = false;
        }
        return sb.ToString();
    }

    static float ultimoAuto;
    static bool Avanzar()
    {
        if (Juego.PruebaAutomatica && Time.unscaledTime - ultimoAuto > 0.6f) { ultimoAuto = Time.unscaledTime; return true; }
        var k = Keyboard.current; var m = Mouse.current;
        return (k != null && (k.eKey.wasPressedThisFrame || k.enterKey.wasPressedThisFrame || k.spaceKey.wasPressedThisFrame))
            || (m != null && m.leftButton.wasPressedThisFrame);
    }

    static IEnumerator Alfa(CanvasGroup g, float a, float dur)
    {
        float a0 = g.alpha;
        for (float t = 0f; t < 1f; t += Time.unscaledDeltaTime / dur) { g.alpha = Mathf.Lerp(a0, a, t); yield return null; }
        g.alpha = a;
    }
}
