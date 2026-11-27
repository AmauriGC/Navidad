using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// MEDALLAS: al terminar la noche (árbol completo) ganas la medalla de la dificultad en que jugaste:
///   Fácil = BRONCE · Medio = PLATA · Difícil = ORO · Imposible = DIAMANTE
/// y dos medallas EXTRA (en cualquier dificultad):
///   ★ GALLETERA: terminaste con las 10 galletas de jengibre.
///   ♥ INTACTO: terminaste Difícil o Imposible SIN perder ninguna vida.
/// Se guardan en PlayerPrefs ("Medalla_0".."Medalla_3", "Medalla_Galletas", "Medalla_Intacto"): se quedan para siempre.
///  - En los CRÉDITOS: la medalla 3D (Resources/Medalla, de Blender/medalla.py) gira junto al texto. Como los créditos
///    tapan toda la pantalla, la medalla no está en el mundo del juego: una CÁMARA APARTE (lejos, abajo del mapa) la
///    graba a una RenderTexture y esa textura se muestra en la UI con un RawImage.
///  - En el menú de PAUSA: fila de medallas (las que no tienes salen grises).
/// </summary>
public static class Medallas
{
    public static readonly string[] Nombres = { "Bronce", "Plata", "Oro", "Diamante" };
    public static readonly Color[] Colores =
    {
        new Color(0.80f, 0.48f, 0.25f),   // bronce
        new Color(0.82f, 0.86f, 0.92f),   // plata
        new Color(1.00f, 0.76f, 0.25f),   // oro
        new Color(0.55f, 0.90f, 1.00f),   // diamante
    };

    public static bool Tiene(int nivel) => PlayerPrefs.GetInt("Medalla_" + nivel, 0) == 1;
    public static bool TieneGalletas => PlayerPrefs.GetInt("Medalla_Galletas", 0) == 1;
    public static bool TieneIntacto => PlayerPrefs.GetInt("Medalla_Intacto", 0) == 1;

    /// <summary>Lo llama el DirectorJuego al ganar. Guarda y devuelve el texto para los créditos.</summary>
    public static string Ganar()
    {
        int n = Dificultad.Elegido;
        var nuevas = new List<string>();
        if (!Tiene(n)) nuevas.Add(Nombres[n]);
        PlayerPrefs.SetInt("Medalla_" + n, 1);
        string extra = "";
        if (Galleta.Todas) { if (!TieneGalletas) nuevas.Add("Galletera"); PlayerPrefs.SetInt("Medalla_Galletas", 1); extra += "   <color=#ffd36b>★ Galletera</color>"; }
        if (Dificultad.ConVidas && Vidas.Perdidas == 0) { if (!TieneIntacto) nuevas.Add("Intacto"); PlayerPrefs.SetInt("Medalla_Intacto", 1); extra += "   <color=#ff8a8a>♥ Intacto</color>"; }
        PlayerPrefs.Save();
        string c = ColorUtility.ToHtmlStringRGB(Colores[n]);
        return "\n\n<size=40><color=#" + c + ">Medalla de " + Nombres[n].ToUpper() + "</color></size>" + extra
               + (nuevas.Count > 0 ? "\n<size=28><color=#9fe0ff>¡Nueva" + (nuevas.Count > 1 ? "s" : "") + ": " + string.Join(", ", nuevas) + "!</color></size>" : "");
    }

    // ------------------------------------------------------------------ medalla 3D en una RenderTexture
    static GameObject estudio;

    /// <summary>Crea (una vez) el "estudio": medalla + luces + cámara lejos del mapa, y devuelve la textura que graba.</summary>
    public static RenderTexture Estudio(int nivel)
    {
        Limpiar();
        var prefab = Resources.Load<GameObject>("Medalla");
        if (prefab == null) return null;
        estudio = new GameObject("EstudioMedalla");
        estudio.transform.position = new Vector3(0f, -500f, 0f);   // muy abajo: nada del juego sale en la toma
        var m = Object.Instantiate(prefab, estudio.transform);
        m.name = "Medalla"; m.transform.localPosition = new Vector3(0f, -0.35f, 0f);
        m.AddComponent<Girar>();
        Pintar(m, Colores[nivel]);

        var luz = new GameObject("Luz").AddComponent<Light>(); luz.transform.SetParent(estudio.transform, false);
        luz.type = LightType.Directional; luz.intensity = 2.2f; luz.transform.rotation = Quaternion.Euler(30f, -30f, 0f);
        var luz2 = new GameObject("Relleno").AddComponent<Light>(); luz2.transform.SetParent(estudio.transform, false);
        luz2.type = LightType.Point; luz2.range = 6f; luz2.intensity = 3f; luz2.color = new Color(0.7f, 0.8f, 1f);
        luz2.transform.localPosition = new Vector3(1.5f, 0.8f, 2f);

        var rt = new RenderTexture(512, 512, 24, RenderTextureFormat.ARGB32); rt.name = "RT_Medalla";
        var cam = new GameObject("Camara").AddComponent<Camera>(); cam.transform.SetParent(estudio.transform, false);
        cam.transform.localPosition = new Vector3(0f, 0f, 3.2f); cam.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
        cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(0f, 0f, 0f, 0f);
        cam.fieldOfView = 32f; cam.nearClipPlane = 0.1f; cam.farClipPlane = 10f;
        cam.targetTexture = rt; cam.depth = -50;
        return rt;
    }

    public static void Limpiar() { if (estudio != null) Object.Destroy(estudio); estudio = null; }

    /// <summary>Pinta el disco (material 0) y la estrella (material 4) del color de la medalla.</summary>
    static void Pintar(GameObject m, Color c)
    {
        foreach (var r in m.GetComponentsInChildren<Renderer>())
        {
            var mats = r.sharedMaterials;
            for (int i = 0; i < mats.Length; i++)
            {
                if (mats[i] == null || !(mats[i].name.StartsWith("Medalla_Metal") || mats[i].name.StartsWith("Medalla_Estrella"))) continue;
                bool estrella = mats[i].name.StartsWith("Medalla_Estrella");
                var b = new MaterialPropertyBlock();
                Color col = estrella ? Color.Lerp(c, Color.white, 0.45f) : c;
                b.SetColor("baseColorFactor", col); b.SetColor("_BaseColor", col);
                b.SetColor("emissiveFactor", col * (estrella ? 0.25f : 0.08f));
                r.SetPropertyBlock(b, i);
            }
        }
    }

    class Girar : MonoBehaviour
    {
        void Update() { transform.localRotation = Quaternion.Euler(0f, Time.unscaledTime * 70f, Mathf.Sin(Time.unscaledTime * 1.3f) * 4f); }
    }

    // ------------------------------------------------------------------ fila de medallas (menú de pausa)
    /// <summary>Fila con las 6 medallas (las que no tienes, en gris). 'ancla' y 'pos' dicen dónde va en la capa.</summary>
    public static void Fila(Transform capa, Vector2 ancla, Vector2 pos)
    {
        var fila = UIConstructor.Rect("Medallas", capa, ancla, ancla, new Vector2(560, 110), pos);
        var t = UIConstructor.Texto(UIConstructor.Rect("Titulo", fila, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(560, 30), new Vector2(280, -12)),
                                    "Medallas", 26, new Color(1f, 0.85f, 0.45f, 0.95f), TextAnchor.MiddleCenter);
        UIConstructor.Sombra(t);
        string[] etiquetas = { "Fácil", "Medio", "Difícil", "Imposible", "Galletas", "Intacto" };
        for (int i = 0; i < 6; i++)
        {
            bool tiene = i < 4 ? Tiene(i) : i == 4 ? TieneGalletas : TieneIntacto;
            Color c = i < 4 ? Colores[i] : i == 4 ? new Color(1f, 0.82f, 0.4f) : new Color(1f, 0.5f, 0.55f);
            var aro = UIConstructor.Rect("M" + i, fila, new Vector2(0f, 0f), new Vector2(0f, 0f), new Vector2(56, 56), new Vector2(60 + i * 88, 50));
            var img = UIConstructor.Imagen(aro, tiene ? c : new Color(0.3f, 0.32f, 0.38f, 0.6f)); img.sprite = UIConstructor.SpriteCirculo();
            UIConstructor.Sombra(img, 2f);
            var s = UIConstructor.Texto(UIConstructor.Rect("Simbolo", aro, Vector2.zero, Vector2.one), i == 5 ? "♥" : "★", 32,
                                        tiene ? Color.Lerp(c, Color.white, 0.6f) : new Color(0.55f, 0.58f, 0.65f, 0.8f));
            var e = UIConstructor.Texto(UIConstructor.Rect("Nombre", aro, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(110, 24), new Vector2(0, -14)),
                                        etiquetas[i], 17, tiene ? Color.white : new Color(0.7f, 0.72f, 0.8f, 0.6f));
            UIConstructor.Sombra(e);
        }
    }

    /// <summary>Sección "Medallas" de la pausa: 6 tarjetas (2 columnas) con la medalla, su nombre y cómo se gana.</summary>
    public static void Lista(Transform padre)
    {
        string[] nombres = { "Bronce", "Plata", "Oro", "Diamante", "Galletera", "Intacto" };
        string[] como = { "Termina la noche en Fácil", "Termina la noche en Medio", "Termina la noche en Difícil",
                          "Termina la noche en Imposible", "Termina con las 10 galletas", "Gana Difícil o Imposible sin perder vidas" };
        int tienes = 0;
        for (int i = 0; i < 6; i++)
        {
            bool tiene = i < 4 ? Tiene(i) : i == 4 ? TieneGalletas : TieneIntacto;
            if (tiene) tienes++;
            Color c = i < 4 ? Colores[i] : i == 4 ? new Color(1f, 0.82f, 0.4f) : new Color(1f, 0.5f, 0.55f);
            var tarjeta = UIConstructor.Rect("Medalla_" + i, padre, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(560, 130),
                                             new Vector2(i % 2 == 0 ? -300 : 300, 170 - (i / 2) * 160));
            UIConstructor.Redondear(UIConstructor.Imagen(tarjeta, tiene ? new Color(c.r, c.g, c.b, 0.16f) : new Color(1f, 1f, 1f, 0.05f)));
            var aro = UIConstructor.Rect("Circulo", tarjeta, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(84, 84), new Vector2(70, 0));
            var img = UIConstructor.Imagen(aro, tiene ? c : new Color(0.3f, 0.32f, 0.38f, 0.7f)); img.sprite = UIConstructor.SpriteCirculo();
            UIConstructor.Texto(UIConstructor.Rect("Simbolo", aro, Vector2.zero, Vector2.one), i == 5 ? "♥" : "★", 46,
                                tiene ? Color.Lerp(c, Color.white, 0.6f) : new Color(0.55f, 0.58f, 0.65f, 0.8f));
            var n = UIConstructor.Titulo(UIConstructor.Rect("Nombre", tarjeta, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(420, 50), new Vector2(340, 22)),
                                         nombres[i], 36, tiene ? Color.Lerp(c, Color.white, 0.35f) : new Color(0.75f, 0.77f, 0.85f, 0.7f), TextAnchor.MiddleLeft, FontStyle.Bold);
            UIConstructor.Sombra(n);
            UIConstructor.Texto(UIConstructor.Rect("Como", tarjeta, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(420, 40), new Vector2(340, -22)),
                                (tiene ? "¡Ganada! " : "") + como[i], 22, tiene ? new Color(0.85f, 1f, 0.85f) : new Color(0.8f, 0.82f, 0.9f, 0.75f), TextAnchor.MiddleLeft);
        }
        var total = UIConstructor.Texto(UIConstructor.Rect("Total", padre, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(900, 40), new Vector2(0, -330)),
                                        "Tienes " + tienes + " de 6 medallas", 28, new Color(1f, 0.85f, 0.45f));
        UIConstructor.Sombra(total);
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { estudio = null; }
}
