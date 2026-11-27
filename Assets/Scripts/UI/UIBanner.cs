using System.Collections;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Banner animado tipo videojuego: "¡MISIÓN COMPLETADA!" / "NUEVO OBJETIVO".
/// Animación hecha a mano con curvas:
///   1) el título entra GRANDE y transparente y "aterriza" con rebote (easeOutBack)
///   2) una línea dorada se abre del centro hacia los lados
///   3) aparece el subtítulo
///   4) destellos (estrellitas) giran alrededor
///   5) todo se desvanece hacia arriba
/// </summary>
public class UIBanner : MonoBehaviour
{
    static UIBanner inst;
    RectTransform raiz, linea, contTitulo;
    Text titulo, subtitulo, etiqueta;
    CanvasGroup grupo;
    RectTransform[] chispas;
    Coroutine actual;

    public static bool Mostrando { get { return inst != null && inst.actual != null; } }

    static UIBanner Inst
    {
        get
        {
            if (inst != null) return inst;
            var capa = UIConstructor.Capa("Banner", 15);
            inst = capa.gameObject.AddComponent<UIBanner>();
            inst.Construir(capa);
            return inst;
        }
    }

    void Construir(RectTransform capa)
    {
        raiz = UIConstructor.Rect("Contenido", capa, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1600, 400), new Vector2(0, 180));
        grupo = UIConstructor.Grupo(raiz, 0f);
        var fondo = UIConstructor.Rect("Franja", raiz, new Vector2(0, 0.5f), new Vector2(1, 0.5f), new Vector2(0, 230), Vector2.zero);
        UIConstructor.Imagen(fondo, new Color(0.02f, 0.03f, 0.08f, 0.65f));
        etiqueta = UIConstructor.Texto(UIConstructor.Rect("Etiqueta", raiz, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1400, 50), new Vector2(0, 85)),
                                       "", 30, new Color(0.75f, 0.9f, 1f), TextAnchor.MiddleCenter, FontStyle.Bold);
        contTitulo = UIConstructor.Rect("Titulo", raiz, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1500, 110), new Vector2(0, 20));
        titulo = UIConstructor.Titulo(contTitulo, "", 84, new Color(1f, 0.82f, 0.3f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIConstructor.Sombra(titulo, 4f);
        var outline = titulo.gameObject.AddComponent<Outline>(); outline.effectColor = new Color(0.4f, 0.15f, 0f, 0.8f); outline.effectDistance = new Vector2(2, -2);
        linea = UIConstructor.Rect("Linea", raiz, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0, 5), new Vector2(0, -42));
        UIConstructor.Imagen(linea, new Color(1f, 0.85f, 0.4f));
        subtitulo = UIConstructor.Texto(UIConstructor.Rect("Subtitulo", raiz, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1400, 60), new Vector2(0, -80)),
                                        "", 38, Color.white, TextAnchor.MiddleCenter);
        UIConstructor.Sombra(subtitulo);
        chispas = new RectTransform[8];
        for (int i = 0; i < chispas.Length; i++)
        {
            chispas[i] = UIConstructor.Rect("Chispa" + i, raiz, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(18, 18));
            UIConstructor.Imagen(chispas[i], new Color(1f, 0.95f, 0.6f, 0f));
            chispas[i].localRotation = Quaternion.Euler(0, 0, 45);
        }
    }

    /// <summary>Muestra el banner. etiqueta = texto pequeño arriba (ej. "Etapa 2 de 5").</summary>
    public static void Mostrar(string tituloTxt, string subtituloTxt, string etiquetaTxt = "", float duracion = 3.2f, Color? color = null)
    {
        var b = Inst;
        if (b.actual != null) b.StopCoroutine(b.actual);
        b.actual = b.StartCoroutine(b.Animar(tituloTxt, subtituloTxt, etiquetaTxt, duracion, color ?? new Color(1f, 0.82f, 0.3f)));
    }

    public static IEnumerator Esperar(string t, string s, string e = "", float dur = 3.2f, Color? color = null)
    {
        Mostrar(t, s, e, dur, color);
        yield return null;
        while (Mostrando) yield return null;
    }

    static float EaseOutBack(float x) { const float c = 1.70158f; x -= 1f; return 1f + (c + 1f) * x * x * x + c * x * x; }

    IEnumerator Animar(string t, string s, string e, float dur, Color color)
    {
        titulo.text = t; subtitulo.text = s; etiqueta.text = e; titulo.color = color;
        raiz.anchoredPosition = new Vector2(0, 180);
        grupo.alpha = 1f;
        subtitulo.color = new Color(1, 1, 1, 0); etiqueta.color = new Color(0.75f, 0.9f, 1f, 0f);
        linea.sizeDelta = new Vector2(0, 5);

        // 1) título aterriza con rebote
        for (float k = 0f; k < 1f; k += Time.unscaledDeltaTime / 0.55f)
        {
            float esc = Mathf.LerpUnclamped(2.4f, 1f, EaseOutBack(k));
            contTitulo.localScale = Vector3.one * esc;
            titulo.color = new Color(color.r, color.g, color.b, Mathf.Clamp01(k * 2f));
            yield return null;
        }
        contTitulo.localScale = Vector3.one;
        // 2) línea se abre + 3) subtítulo y etiqueta aparecen
        for (float k = 0f; k < 1f; k += Time.unscaledDeltaTime / 0.4f)
        {
            float ease = 1f - Mathf.Pow(1f - k, 3f);
            linea.sizeDelta = new Vector2(Mathf.Lerp(0, 1100, ease), 5);
            subtitulo.color = new Color(1, 1, 1, k);
            etiqueta.color = new Color(0.75f, 0.9f, 1f, k);
            yield return null;
        }
        // 4) espera con chispas girando y título "respirando"
        float tiempo = 0f, quieto = Mathf.Max(0.5f, dur - 1.6f);
        while (tiempo < quieto)
        {
            tiempo += Time.unscaledDeltaTime;
            contTitulo.localScale = Vector3.one * (1f + 0.03f * Mathf.Sin(tiempo * 5f));
            for (int i = 0; i < chispas.Length; i++)
            {
                float a = tiempo * 1.3f + i * Mathf.PI * 2f / chispas.Length;
                chispas[i].anchoredPosition = new Vector2(Mathf.Cos(a) * 640f, 20f + Mathf.Sin(a) * 85f);
                float brillo = Mathf.Clamp01(Mathf.Sin(tiempo * 6f + i * 1.9f));
                chispas[i].GetComponent<Image>().color = new Color(1f, 0.95f, 0.6f, brillo * Mathf.Clamp01(tiempo * 3f));
                chispas[i].localScale = Vector3.one * (0.5f + brillo);
            }
            yield return null;
        }
        // 5) se desvanece subiendo
        for (float k = 0f; k < 1f; k += Time.unscaledDeltaTime / 0.6f)
        {
            grupo.alpha = 1f - k;
            raiz.anchoredPosition = new Vector2(0, 180 + 60 * k * k);
            yield return null;
        }
        grupo.alpha = 0f;
        foreach (var c in chispas) c.GetComponent<Image>().color = new Color(1, 1, 1, 0);
        actual = null;
    }
}
