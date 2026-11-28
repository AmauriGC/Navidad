using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Detallitos v1.5 · Globito de diálogo sobre la cabeza del cascanueces + su voz de madera.
/// Un Canvas en espacio de mundo (chiquito, escala 0.01) que siempre mira a la cámara; el texto sale con un
/// "pop", se queda un ratito y se desvanece. Cada 3 letras suena una sílaba "voz_cas" en 3D (desde el cascanueces).
/// Uso: GloboCascanueces.Decir(gameObject, "¡Alto!", altura).
/// </summary>
public class GloboCascanueces : MonoBehaviour
{
    const float Escala = 0.0042f;
    Canvas canvas; CanvasGroup grupo; Text texto; RectTransform fondo;
    AudioSource voz;
    string frase = ""; int letras; float tiempoLetra, visibleHasta, siguientePermitido, inicio;
    float altura = 2.5f;

    /// <summary>Muestra 'frase' sobre el cascanueces 'quien'. Devuelve false si todavía está hablando (para no encimar).</summary>
    public static bool Decir(GameObject quien, string frase, float altura, bool forzar = false)
    {
        var g = quien.GetComponent<GloboCascanueces>();
        if (g == null) g = quien.AddComponent<GloboCascanueces>();
        return g.Hablar(frase, altura, forzar);
    }

    /// <summary>Elige una frase al azar de la lista.</summary>
    public static bool Decir(GameObject quien, string[] frases, float altura, bool forzar = false)
    {
        if (frases == null || frases.Length == 0) return false;
        return Decir(quien, frases[Random.Range(0, frases.Length)], altura, forzar);
    }

    bool Hablar(string f, float alt, bool forzar)
    {
        if (!forzar && Time.time < siguientePermitido) return false;
        Construir();
        frase = f; letras = 0; tiempoLetra = 0f; altura = alt; inicio = Time.time;
        visibleHasta = Time.time + 1.3f + f.Length * 0.05f;
        siguientePermitido = Time.time + 2.2f;
        texto.text = "";
        canvas.gameObject.SetActive(true);
        grupo.alpha = 1f;
        return true;
    }

    void Construir()
    {
        if (canvas != null) return;
        var go = new GameObject("Globo", typeof(RectTransform));
        go.transform.SetParent(transform, false);
        canvas = go.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;
        canvas.sortingOrder = 5;
        var rt = (RectTransform)go.transform;
        rt.sizeDelta = new Vector2(420, 120);
        grupo = go.AddComponent<CanvasGroup>(); grupo.blocksRaycasts = false; grupo.interactable = false;
        // fondo: globito redondeado crema con orilla roja (colores de soldadito)
        fondo = UIConstructor.Rect("Fondo", go.transform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(380, 84), Vector2.zero);
        var img = UIConstructor.Redondear(UIConstructor.Imagen(fondo, new Color(1f, 0.96f, 0.86f, 1f)), 1f);   // opaca: el Outline dibuja una copia detrás
        var borde = img.gameObject.AddComponent<Outline>(); borde.effectColor = new Color(0.75f, 0.12f, 0.12f, 1f); borde.effectDistance = new Vector2(3, -3);
        // piquito del globo (un cuadrito girado)
        var pico = UIConstructor.Rect("Pico", fondo, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(22, 22), new Vector2(0, -4));
        UIConstructor.Imagen(pico, new Color(1f, 0.96f, 0.86f, 1f)); pico.localRotation = Quaternion.Euler(0, 0, 45);
        pico.SetAsFirstSibling();
        texto = UIConstructor.Texto(UIConstructor.Rect("Texto", fondo, Vector2.zero, Vector2.one, new Vector2(-24, -10), Vector2.zero), "", 30, new Color(0.35f, 0.08f, 0.08f), TextAnchor.MiddleCenter, FontStyle.Bold);
        texto.horizontalOverflow = HorizontalWrapMode.Wrap; texto.resizeTextForBestFit = true; texto.resizeTextMinSize = 18; texto.resizeTextMaxSize = 30;
        texto.raycastTarget = false; img.raycastTarget = false;
        voz = GestorAudio.FuentePropia(gameObject, 2f, 22f);
        voz.priority = 90;
    }

    void LateUpdate()
    {
        if (canvas == null || !canvas.gameObject.activeSelf) return;
        var cam = Camera.main;
        float escalaPadre = Mathf.Max(0.05f, transform.lossyScale.y);
        var t = canvas.transform;
        t.position = transform.position + Vector3.up * altura * escalaPadre;
        if (cam != null)
        {
            t.rotation = Quaternion.LookRotation(t.position - cam.transform.position, Vector3.up);
            // tamaño casi constante en pantalla (de lejos no se vuelve una manchita) y sin heredar la escala del cascanueces
            float d = Vector3.Distance(cam.transform.position, t.position);
            float k = Mathf.Clamp(d / 7f, 0.45f, 2.0f);
            t.localScale = Vector3.one * Escala * k / escalaPadre;
        }
        // las letras van saliendo y suena una sílaba de madera cada 3
        if (letras < frase.Length)
        {
            tiempoLetra += Time.deltaTime;
            while (tiempoLetra > 0.035f && letras < frase.Length)
            {
                tiempoLetra -= 0.035f; letras++;
                if (letras % 3 == 1 && voz != null && !char.IsWhiteSpace(frase[letras - 1]))
                {
                    var c = Resources.Load<AudioClip>("Audio/voz_cas" + Random.Range(1, 5));
                    voz.pitch = 0.9f + Random.Range(-0.08f, 0.12f);
                    if (c != null) voz.PlayOneShot(c, 0.9f * GestorAudio.VolumenEfectos);
                }
            }
            texto.text = frase.Substring(0, letras);
        }
        // "pop" al salir
        float vida = Time.time - inicio;
        float pop = vida < 0.18f ? Mathf.Lerp(0.6f, 1.1f, vida / 0.18f) : Mathf.Lerp(1.1f, 1f, Mathf.Clamp01((vida - 0.18f) / 0.1f));
        fondo.localScale = Vector3.one * pop;
        // se desvanece al final; en cinemáticas no estorba
        float a = Mathf.Clamp01((visibleHasta - Time.time) / 0.35f);
        if (Juego.Estado != Juego.Modo.Jugando) a = 0f;
        grupo.alpha = a;
        if (Time.time > visibleHasta) canvas.gameObject.SetActive(false);
    }
}
