using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Funciones de ayuda para CREAR UI POR CÓDIGO (paneles, textos, imágenes).
/// Así cada pantalla (historia, banner, títulos...) se arma sola al iniciar el juego
/// y no hay que acomodar cientos de objetos a mano en el editor.
/// </summary>
public static class UIConstructor
{
    // Fuentes (en Assets/Resources/Fuentes, se cargan por nombre con Resources.Load):
    //  - Fredoka Medium (licencia OFL): redondita y fácil de leer => textos normales. Se sacó de la fuente
    //    variable de Google Fonts con: fonttools varLib.instancer Fredoka.ttf wght=500 wdth=100
    //  - Mountains of Christmas (licencia Apache 2.0): letras navideñas => títulos.
    // Si alguna faltara, se usa la fuente de Unity para que el juego no se rompa.
    static Font fuente, fuenteTitulo;
    public static Font Fuente
    {
        get
        {
            if (fuente == null) fuente = Resources.Load<Font>("Fuentes/Fredoka-Medium");
            if (fuente == null) fuente = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            return fuente;
        }
    }
    public static Font FuenteTitulo
    {
        get
        {
            if (fuenteTitulo == null) fuenteTitulo = Resources.Load<Font>("Fuentes/MountainsofChristmas-Bold");
            return fuenteTitulo != null ? fuenteTitulo : Fuente;
        }
    }

    static Canvas canvas;
    /// <summary>Canvas compartido de la UI del juego (encima del HUD).</summary>
    public static Canvas Canvas
    {
        get
        {
            if (canvas != null) return canvas;
            var go = new GameObject("UI_Juego");
            canvas = go.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 10;
            var esc = go.AddComponent<CanvasScaler>();
            esc.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            esc.referenceResolution = new Vector2(1920, 1080);
            esc.matchWidthOrHeight = 0.5f;
            go.AddComponent<GraphicRaycaster>();
            return canvas;
        }
    }

    /// <summary>Crea un RectTransform hijo. anclaMin/anclaMax en 0..1 de la pantalla.</summary>
    public static RectTransform Rect(string nombre, Transform padre, Vector2 anclaMin, Vector2 anclaMax, Vector2 tam = default(Vector2), Vector2 pos = default(Vector2))
    {
        var go = new GameObject(nombre, typeof(RectTransform));
        var rt = (RectTransform)go.transform;
        rt.SetParent(padre, false);
        rt.anchorMin = anclaMin; rt.anchorMax = anclaMax;
        rt.sizeDelta = tam; rt.anchoredPosition = pos;
        return rt;
    }

    public static RectTransform PantallaCompleta(string nombre, Transform padre)
    {
        var rt = Rect(nombre, padre, Vector2.zero, Vector2.one);
        rt.offsetMin = rt.offsetMax = Vector2.zero;
        return rt;
    }

    public static Image Imagen(RectTransform rt, Color color)
    {
        var img = rt.gameObject.AddComponent<Image>();
        img.color = color; img.raycastTarget = false;
        return img;
    }

    public static Text Texto(RectTransform rt, string texto, int tam, Color color, TextAnchor alineacion = TextAnchor.MiddleCenter, FontStyle estilo = FontStyle.Normal)
    {
        var t = rt.gameObject.AddComponent<Text>();
        t.font = Fuente; t.text = texto; t.fontSize = tam; t.color = color;
        t.alignment = alineacion; t.fontStyle = estilo; t.supportRichText = true;
        t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Overflow;
        t.raycastTarget = false;
        return t;
    }

    /// <summary>Texto de TÍTULO con la fuente navideña. Mismos parámetros que Texto; la fuente ya es gruesa,
    /// así que no se le aplica negrita extra, y se agranda un poco porque sus letras son más chicas.</summary>
    public static Text Titulo(RectTransform rt, string texto, int tam, Color color, TextAnchor alineacion = TextAnchor.MiddleCenter, FontStyle estilo = FontStyle.Normal)
    {
        var t = Texto(rt, texto, Mathf.RoundToInt(tam * 1.15f), color, alineacion, FontStyle.Normal);
        t.font = FuenteTitulo;
        return t;
    }

    /// <summary>Sombra suave para que el texto se lea sobre cualquier fondo.</summary>
    public static void Sombra(Graphic g, float d = 2f)
    {
        var s = g.gameObject.AddComponent<Shadow>();
        s.effectColor = new Color(0, 0, 0, 0.8f); s.effectDistance = new Vector2(d, -d);
    }

    /// <summary>Raíz de una capa de UI con su propio orden de dibujo (más alto = más encima).</summary>
    public static RectTransform Capa(string nombre, int orden)
    {
        var rt = PantallaCompleta(nombre, Canvas.transform);
        var c = rt.gameObject.AddComponent<Canvas>();
        c.overrideSorting = true; c.sortingOrder = 10 + orden;
        rt.gameObject.AddComponent<GraphicRaycaster>();
        return rt;
    }

    /// <summary>Para que la UI responda al mouse (sliders) hace falta un EventSystem con el módulo
    /// del Input System nuevo. Si la escena no tiene, se crea uno.</summary>
    public static void AsegurarEventSystem()
    {
        if (Object.FindAnyObjectByType<UnityEngine.EventSystems.EventSystem>() != null) return;
        var go = new GameObject("EventSystem");
        go.AddComponent<UnityEngine.EventSystems.EventSystem>();
        go.AddComponent<UnityEngine.InputSystem.UI.InputSystemUIInputModule>();
    }

    /// <summary>Slider horizontal (fondo + relleno + perilla redonda) con etiqueta a la izquierda.
    /// 'alCambiar' recibe el valor nuevo (0..1 o el rango que se indique).</summary>
    public static Slider Deslizador(Transform padre, string etiqueta, Vector2 pos, float valor, System.Action<float> alCambiar, float min = 0f, float max = 1f)
    {
        AsegurarEventSystem();
        var fila = Rect("Fila_" + etiqueta, padre, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(900, 56), pos);
        Texto(Rect("Etiqueta", fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(330, 56), new Vector2(165, 0)),
              etiqueta, 34, Color.white, TextAnchor.MiddleRight);
        var zona = Rect("Slider", fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(480, 40), new Vector2(370 + 240, 0));
        var fondo = PantallaCompleta("Fondo", zona); fondo.offsetMin = new Vector2(0, 12); fondo.offsetMax = new Vector2(0, -12);
        var imgFondo = Imagen(fondo, new Color(1f, 1f, 1f, 0.18f)); imgFondo.raycastTarget = true;
        var areaRelleno = PantallaCompleta("AreaRelleno", zona); areaRelleno.offsetMin = new Vector2(0, 12); areaRelleno.offsetMax = new Vector2(0, -12);
        var relleno = PantallaCompleta("Relleno", areaRelleno);
        Imagen(relleno, new Color(1f, 0.8f, 0.35f));
        var areaPerilla = PantallaCompleta("AreaPerilla", zona); areaPerilla.offsetMin = new Vector2(14, 0); areaPerilla.offsetMax = new Vector2(-14, 0);
        var perilla = Rect("Perilla", areaPerilla, Vector2.zero, new Vector2(0, 1), new Vector2(36, 0));
        var imgPerilla = Imagen(perilla, Color.white); imgPerilla.sprite = SpriteCirculo(); imgPerilla.raycastTarget = true;

        var s = zona.gameObject.AddComponent<Slider>();
        s.fillRect = relleno; s.handleRect = perilla; s.targetGraphic = imgPerilla;
        s.direction = Slider.Direction.LeftToRight; s.minValue = min; s.maxValue = max; s.value = valor;
        var colores = s.colors; colores.highlightedColor = new Color(1f, 0.9f, 0.6f); colores.pressedColor = new Color(1f, 0.75f, 0.3f); s.colors = colores;
        if (alCambiar != null) s.onValueChanged.AddListener(v => alCambiar(v));
        return s;
    }

    static Sprite circulo, flecha;
    /// <summary>Círculo suave dibujado pixel por pixel (no hace falta una imagen en el proyecto).</summary>
    public static Sprite SpriteCirculo()
    {
        if (circulo != null) return circulo;
        const int n = 64; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f));
            tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(n / 2f - 1f - d)));   // borde suave de 1 pixel
        }
        tex.Apply();
        return circulo = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f));
    }

    static Sprite aro;
    /// <summary>Aro (círculo hueco) con 4 muescas, para la mirilla de la bola de nieve.</summary>
    public static Sprite SpriteAro()
    {
        if (aro != null) return aro;
        const int n = 96; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            Vector2 p = new Vector2(x + 0.5f - n / 2f, y + 0.5f - n / 2f);
            float d = p.magnitude;
            float a = Mathf.Clamp01(4f - Mathf.Abs(d - 38f));                        // aro de ~8 px de grueso
            float ang = Mathf.Repeat(Mathf.Atan2(p.y, p.x) * Mathf.Rad2Deg, 90f);
            if (ang < 12f || ang > 78f) a = 0f;                                          // 4 cortes (arriba/abajo/lados)
            tex.SetPixel(x, y, new Color(1, 1, 1, a));
        }
        tex.Apply();
        return aro = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f));
    }

    /// <summary>Flecha (punta hacia arriba) dibujada por código: un triángulo con una muesca abajo.</summary>
    public static Sprite SpriteFlecha()
    {
        if (flecha != null) return flecha;
        const int n = 64; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float u = (x + 0.5f) / n - 0.5f, v = (y + 0.5f) / n;          // u: -0.5..0.5, v: 0 abajo .. 1 arriba
            float ancho = (1f - v) * 0.45f;                               // triángulo: más ancho abajo
            float muesca = 0.28f - Mathf.Abs(u) * 0.9f;                  // "V" recortada en la base
            float a = Mathf.Clamp01((ancho - Mathf.Abs(u)) * n) * Mathf.Clamp01((v - muesca) * n) * Mathf.Clamp01((0.97f - v) * n);
            tex.SetPixel(x, y, new Color(1, 1, 1, a));
        }
        tex.Apply();
        return flecha = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f));
    }

    static Sprite copo, vineta;
    /// <summary>Copo de nieve: 6 brazos con ramitas (distancia a segmentos).</summary>
    public static Sprite SpriteCopo()
    {
        if (copo != null) return copo;
        const int n = 64; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        var segs = new System.Collections.Generic.List<Vector4>();
        for (int k = 0; k < 6; k++)
        {
            float a = k * Mathf.PI / 3f; Vector2 d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            segs.Add(new Vector4(0, 0, d.x * 0.46f, d.y * 0.46f));
            foreach (float s in new[] { -1f, 1f })
            {
                Vector2 b = d * 0.26f, r = new Vector2(Mathf.Cos(a + s * 0.8f), Mathf.Sin(a + s * 0.8f)) * 0.14f;
                segs.Add(new Vector4(b.x, b.y, b.x + r.x, b.y + r.y));
            }
        }
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            Vector2 p = new Vector2((x + 0.5f) / n - 0.5f, (y + 0.5f) / n - 0.5f);
            float dm = 1f;
            foreach (var sg in segs)
            {
                Vector2 a0 = new Vector2(sg.x, sg.y), a1 = new Vector2(sg.z, sg.w), ab = a1 - a0;
                float t = Mathf.Clamp01(Vector2.Dot(p - a0, ab) / ab.sqrMagnitude);
                dm = Mathf.Min(dm, (p - (a0 + ab * t)).magnitude);
            }
            tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01((0.045f - dm) * n)));
        }
        tex.Apply();
        return copo = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f));
    }

    /// <summary>Viñeta: transparente al centro y opaca en las orillas (escarcha del frío).</summary>
    public static Sprite SpriteVineta()
    {
        if (vineta != null) return vineta;
        const int n = 128; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float u = (x + 0.5f) / n * 2f - 1f, v = (y + 0.5f) / n * 2f - 1f;
            float d = Mathf.Sqrt(u * u * 0.8f + v * v * 0.8f);
            float ruido = Mathf.PerlinNoise(x * 0.3f, y * 0.3f) * 0.12f;
            tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.78f, 1.3f, d + ruido))));
        }
        tex.wrapMode = TextureWrapMode.Clamp; tex.Apply();
        return vineta = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f));
    }

    static Sprite corazon;
    /// <summary>Corazón dibujado con la curva (x²+y²-1)³ - x²·y³ ≤ 0 (adentro = opaco), con orilla suave.</summary>
    public static Sprite SpriteCorazon()
    {
        if (corazon != null) return corazon;
        const int n = 64; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float u = ((x + 0.5f) / n - 0.5f) * 2.6f, v = ((y + 0.5f) / n - 0.45f) * 2.6f;
            float a = u * u + v * v - 1f;
            float f = a * a * a - u * u * v * v * v;
            tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(-f * 40f)));
        }
        tex.Apply();
        return corazon = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f));
    }

    public static CanvasGroup Grupo(RectTransform rt, float alfa)
    {
        var g = rt.gameObject.AddComponent<CanvasGroup>();
        g.alpha = alfa; g.blocksRaycasts = false; g.interactable = false;
        return g;
    }
}
