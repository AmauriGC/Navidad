using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Detallitos v1.5 · Decoración NAVIDEÑA del menú de pausa (lo pidió Cristian). No cambia cómo funciona el menú:
/// el DirectorJuego lo arma igual (columna + tarjeta) y luego llama a <see cref="Decorar"/>, que agrega:
///   · Fondo: viñeta verde/roja oscura y copos de nieve que caen despacito.
///   · Columna: roja con borde dorado y franjas de BASTÓN DE CARAMELO arriba y abajo.
///   · "PAUSA" con ramitas de acebo (hojas + moras) a los lados.
///   · Tarjeta: verde pino con borde dorado, NIEVE acumulada arriba y guirnalda de foquitos que titilan.
/// Todo se anima con Time.unscaledTime porque en pausa Time.timeScale = 0.
/// Los sprites (rayas, hoja, copo) se dibujan por código: no hace falta ninguna imagen en el proyecto.
/// </summary>
public static class UIPausaNavidad
{
    public static readonly Color Rojo = new Color(0.46f, 0.07f, 0.09f, 1f);
    public static readonly Color VerdePino = new Color(0.05f, 0.2f, 0.13f, 1f);
    public static readonly Color Dorado = new Color(1f, 0.8f, 0.38f, 1f);
    public static readonly Color Nieve = new Color(0.96f, 0.98f, 1f, 1f);

    public static void Decorar(RectTransform capa, RectTransform fondo, RectTransform columna, RectTransform tarjeta, RectTransform titulo)
    {
        // ---- fondo: viñeta de color (verde arriba, rojo vino abajo) + copos
        var img = fondo.GetComponent<Image>();
        if (img != null) img.color = new Color(0.02f, 0.05f, 0.05f, 0.62f);
        var vin = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Vineta", capa), new Color(0.25f, 0.02f, 0.05f, 0.75f));
        vin.sprite = UIConstructor.SpriteVineta(); vin.raycastTarget = false;
        vin.transform.SetSiblingIndex(fondo.GetSiblingIndex() + 1);
        var copos = UIConstructor.PantallaCompleta("Copos", capa);
        copos.SetSiblingIndex(vin.transform.GetSiblingIndex() + 1);
        var anim = capa.gameObject.AddComponent<AnimPausa>();
        for (int i = 0; i < 46; i++) anim.Copo(copos, i);

        // ---- columna roja con borde dorado
        Panel(columna, Rojo);
        Franja(columna);
        if (titulo != null) { Acebo(columna, titulo.anchoredPosition + new Vector2(-176, 4), false); Acebo(columna, titulo.anchoredPosition + new Vector2(176, 4), true); }

        // ---- tarjeta verde pino con nieve arriba
        Panel(tarjeta, VerdePino);
        NieveArriba(tarjeta);
        Guirnalda(tarjeta, anim, 30, -1f, -26f);
    }

    /// <summary>Fondo opaco del color + borde dorado (Outline). Opaco porque el Outline dibuja una copia detrás.</summary>
    static void Panel(RectTransform rt, Color color)
    {
        var img = rt.GetComponent<Image>(); if (img == null) return;
        img.color = color;
        var o = rt.gameObject.GetComponent<Outline>() ?? rt.gameObject.AddComponent<Outline>();
        o.effectColor = Dorado; o.effectDistance = new Vector2(4, -4);
        // brillo interior suave (degradado de arriba) para que no se vea plano
        var brillo = UIConstructor.Imagen(UIConstructor.Rect("Brillo", rt, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(-16, 260), new Vector2(0, -130)), new Color(1f, 1f, 1f, 0.06f));
        brillo.sprite = SpriteDegradado(); brillo.raycastTarget = false;
        brillo.transform.SetAsFirstSibling();
    }

    /// <summary>Franja de bastón de caramelo (rayas diagonales rojo/blanco) pegada arriba de la columna.</summary>
    static void Franja(RectTransform columna)
    {
        var f = UIConstructor.Rect("Baston", columna, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(-24, 20), new Vector2(0, -16));
        var img = f.gameObject.AddComponent<RawImage>();
        img.texture = TexturaRayas(); img.uvRect = new Rect(0, 0, 9f, 1f); img.raycastTarget = false;
        var abajo = UIConstructor.Rect("BastonAbajo", columna, new Vector2(0f, 0f), new Vector2(1f, 0f), new Vector2(-24, 14), new Vector2(0, 14));
        var img2 = abajo.gameObject.AddComponent<RawImage>();
        img2.texture = TexturaRayas(); img2.uvRect = new Rect(0, 0, 12f, 1f); img2.raycastTarget = false;
    }

    static readonly Color[] ColoresFoco = { new Color(1f, 0.3f, 0.25f), new Color(1f, 0.82f, 0.3f), new Color(0.35f, 0.9f, 0.45f), new Color(0.4f, 0.7f, 1f), new Color(1f, 0.5f, 0.85f) };

    /// <summary>Cable que cuelga en curva por la orilla de arriba con foquitos de colores (titilan en AnimPausa).
    /// ancho &lt; 0 => usa el ancho real del panel.</summary>
    static void Guirnalda(RectTransform panel, AnimPausa anim, int focos, float ancho, float y)
    {
        var g = UIConstructor.Rect("Guirnalda", panel, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0, 40), new Vector2(0, y));
        if (ancho > 0f) { g.anchorMin = g.anchorMax = new Vector2(0.5f, 1f); g.sizeDelta = new Vector2(ancho, 40); }
        anim.Guirnalda(g, focos);
    }

    /// <summary>Ramita de acebo: 3 hojas verdes (sprite de hoja) y 3 moras rojas.</summary>
    static void Acebo(RectTransform padre, Vector2 pos, bool espejo)
    {
        var r = UIConstructor.Rect("Acebo", padre, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(90, 70), pos);
        float s = espejo ? -1f : 1f;
        float[] ang = { 25f, -20f, 70f };
        for (int i = 0; i < 3; i++)
        {
            var h = UIConstructor.Rect("Hoja" + i, r, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(46, 24), new Vector2(s * (i == 2 ? -4 : 14), i == 2 ? 14 : -2 + i * 6));
            var im = UIConstructor.Imagen(h, i == 1 ? new Color(0.12f, 0.5f, 0.22f) : new Color(0.16f, 0.6f, 0.28f));
            im.sprite = SpriteHoja(); im.raycastTarget = false;
            h.localRotation = Quaternion.Euler(0, 0, s * ang[i]);
        }
        for (int i = 0; i < 3; i++)
        {
            var m = UIConstructor.Rect("Mora" + i, r, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(17, 17), new Vector2(s * (-6 + i * 9), -8 + (i % 2) * 9));
            var im = UIConstructor.Imagen(m, new Color(0.9f, 0.1f, 0.12f)); im.sprite = UIConstructor.SpriteDisco(); im.raycastTarget = false;
        }
    }

    /// <summary>Nieve acumulada en la orilla de arriba: una tira blanca + bolitas encimadas con distinto tamaño.</summary>
    static void NieveArriba(RectTransform tarjeta)
    {
        var tira = UIConstructor.Rect("Nieve", tarjeta, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(-6, 16), new Vector2(0, -3));
        UIConstructor.Redondear(UIConstructor.Imagen(tira, Nieve), 0.5f).raycastTarget = false;
        var rnd = new System.Random(24);
        for (int i = 0; i < 40; i++)
        {
            float u = (i + 0.5f) / 40f;
            float d = 26f + (float)rnd.NextDouble() * 26f;
            var b = UIConstructor.Rect("Bolita" + i, tarjeta, new Vector2(u, 1f), new Vector2(u, 1f), new Vector2(d, d), new Vector2(0, -2 + (float)rnd.NextDouble() * 6f));
            var im = UIConstructor.Imagen(b, Nieve); im.sprite = UIConstructor.SpriteDisco(); im.raycastTarget = false;
        }
        // un par de "chorreados" que cuelgan
        for (int i = 0; i < 7; i++)
        {
            float u = 0.08f + i * 0.14f + (float)rnd.NextDouble() * 0.04f;
            var g = UIConstructor.Rect("Gota" + i, tarjeta, new Vector2(u, 1f), new Vector2(u, 1f), new Vector2(16, 26 + (float)rnd.NextDouble() * 18f), new Vector2(0, -16));
            UIConstructor.Redondear(UIConstructor.Imagen(g, Nieve), 2f).raycastTarget = false;
        }
    }

    // ------------------------------------------------------------------ sprites dibujados por código
    static Texture2D rayas; static Sprite hoja, degradado;

    static Texture2D TexturaRayas()
    {
        if (rayas != null) return rayas;
        const int n = 32; rayas = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float t = Mathf.Repeat((x + y) / (float)n, 1f);
            bool rojo = t < 0.5f;
            rayas.SetPixel(x, y, rojo ? new Color(0.86f, 0.1f, 0.13f) : new Color(1f, 0.97f, 0.94f));
        }
        rayas.wrapMode = TextureWrapMode.Repeat; rayas.filterMode = FilterMode.Bilinear; rayas.Apply();
        return rayas;
    }

    /// <summary>Hoja de acebo: óvalo puntiagudo con orilla ondulada (picos).</summary>
    static Sprite SpriteHoja()
    {
        if (hoja != null) return hoja;
        const int w = 64, h = 32; var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
        {
            float u = (x + 0.5f) / w * 2f - 1f, v = (y + 0.5f) / h * 2f - 1f;
            float ancho = Mathf.Pow(1f - u * u, 0.6f) * (0.82f + 0.18f * Mathf.Cos(u * Mathf.PI * 5f));   // picos de la orilla
            float d = Mathf.Abs(v) - ancho;
            float a = Mathf.Clamp01(-d * h * 0.5f + 0.5f);
            float vena = Mathf.Abs(v) < 0.08f && Mathf.Abs(u) < 0.85f ? 0.75f : 1f;               // venita al centro
            tex.SetPixel(x, y, new Color(vena, vena, vena, a));
        }
        tex.Apply();
        return hoja = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f));
    }

    static Sprite SpriteDegradado()
    {
        if (degradado != null) return degradado;
        var tex = new Texture2D(4, 64, TextureFormat.RGBA32, false);
        for (int y = 0; y < 64; y++) for (int x = 0; x < 4; x++) tex.SetPixel(x, y, new Color(1, 1, 1, y / 63f));
        tex.wrapMode = TextureWrapMode.Clamp; tex.Apply();
        return degradado = Sprite.Create(tex, new Rect(0, 0, 4, 64), new Vector2(0.5f, 0.5f));
    }

    // ------------------------------------------------------------------ animación (con tiempo real)
    class AnimPausa : MonoBehaviour
    {
        class CopoUI { public RectTransform rt; public float vel, fase, amp, x; }
        readonly List<CopoUI> copos = new List<CopoUI>();
        readonly List<Image> focos = new List<Image>(); readonly List<Color> colores = new List<Color>();
        RectTransform area;

        public void Copo(RectTransform padre, int i)
        {
            area = padre;
            float tam = Random.Range(10f, 26f);
            var rt = UIConstructor.Rect("Copo" + i, padre, new Vector2(0f, 0f), new Vector2(0f, 0f), new Vector2(tam, tam), Vector2.zero);
            var im = UIConstructor.Imagen(rt, new Color(1f, 1f, 1f, Random.Range(0.25f, 0.7f)));
            im.sprite = Random.value < 0.6f ? UIConstructor.SpriteCopo() : UIConstructor.SpriteCirculo(); im.raycastTarget = false;
            copos.Add(new CopoUI { rt = rt, vel = Random.Range(25f, 70f), fase = Random.Range(0f, 10f), amp = Random.Range(8f, 30f), x = Random.value });
            rt.anchoredPosition = new Vector2(0f, Random.Range(0f, 1100f));
        }

        public void Guirnalda(RectTransform g, int n)
        {
            for (int i = 0; i < n; i++)
            {
                float u = n == 1 ? 0.5f : (i + 0.5f) / n;
                float comba = -Mathf.Sin(Mathf.Repeat(u * 3f, 1f) * Mathf.PI) * 12f;    // el cable cuelga en 3 curvitas
                // cable: puntito oscuro entre focos
                var c = UIConstructor.Rect("Cable" + i, g, new Vector2(u, 0.5f), new Vector2(u, 0.5f), new Vector2(10, 4), new Vector2(0, comba + 6));
                UIConstructor.Imagen(c, new Color(0.08f, 0.15f, 0.08f, 0.9f)).raycastTarget = false;
                var f = UIConstructor.Rect("Foco" + i, g, new Vector2(u, 0.5f), new Vector2(u, 0.5f), new Vector2(14, 20), new Vector2(0, comba - 4));
                Color col = ColoresFoco[i % ColoresFoco.Length];
                var im = UIConstructor.Imagen(f, col); im.sprite = UIConstructor.SpriteDisco(); im.raycastTarget = false;
                var halo = UIConstructor.Rect("Halo", f, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(38, 38), Vector2.zero);
                var ih = UIConstructor.Imagen(halo, new Color(col.r, col.g, col.b, 0.35f)); ih.sprite = UIConstructor.SpriteCirculo(); ih.raycastTarget = false;
                halo.SetAsFirstSibling();
                focos.Add(im); colores.Add(col);
                focos.Add(ih); colores.Add(new Color(col.r, col.g, col.b, 0.35f));
            }
        }

        void Update()
        {
            float t = Time.unscaledTime;
            if (area != null)
            {
                Vector2 tam = area.rect.size;
                foreach (var c in copos)
                {
                    var p = c.rt.anchoredPosition;
                    p.y -= c.vel * Time.unscaledDeltaTime;
                    if (p.y < -30f) { p.y = tam.y + 30f; c.x = Random.value; }
                    p.x = c.x * tam.x + Mathf.Sin(t * 0.8f + c.fase) * c.amp;
                    c.rt.anchoredPosition = p;
                    c.rt.localRotation = Quaternion.Euler(0, 0, t * 20f + c.fase * 40f);
                }
            }
            // titileo: cada foco con su propio ritmo; de vez en cuando uno se apaga un instante
            for (int i = 0; i < focos.Count; i++)
            {
                int k = i / 2;
                float b = 0.65f + 0.35f * Mathf.Sin(t * (2.2f + (k % 5) * 0.37f) + k * 1.7f);
                if (Mathf.Repeat(t * 0.5f + k * 0.37f, 3f) < 0.12f) b = 0.25f;
                Color c = colores[i];
                focos[i].color = new Color(c.r * (0.55f + 0.45f * b), c.g * (0.55f + 0.45f * b), c.b * (0.55f + 0.45f * b), c.a * (i % 2 == 1 ? b : 1f));
            }
        }
    }
}
