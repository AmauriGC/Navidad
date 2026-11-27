using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

/// <summary>
/// Entrada táctil para teléfono (y navegador del teléfono). Los demás scripts preguntan aquí además del teclado:
///   Tactil.Mover   -> joystick (mitad izquierda; aparece donde pones el dedo). Empujado a fondo = correr.
///   Tactil.Camara  -> arrastrar el dedo en la mitad derecha (pixeles de este cuadro).
///   Tactil.Zoom    -> pellizcar con dos dedos en la mitad derecha.
///   Tactil.Saltar / Usar / Lanzar / Soltar / Pausa -> true SOLO en el cuadro en que se tocó el botón.
/// Se activa solo en teléfono (Application.isMobilePlatform) o si PlayerPrefs "ForzarTactil" = 1 (para probar).
/// </summary>
public static class Tactil
{
    public static bool Activo
    {
        get
        {
            if (Touchscreen.current == null) return false;
            return Application.isMobilePlatform || PlayerPrefs.GetInt("ForzarTactil", 0) == 1;
        }
    }

    public static Vector2 Mover;
    public static bool Correr;
    public static Vector2 Camara;
    public static float Zoom;
    internal static int fSaltar = -1, fUsar = -1, fLanzar = -1, fSoltar = -1, fPausa = -1;
    public static bool Saltar { get { return fSaltar == Time.frameCount; } }
    public static bool Usar { get { return fUsar == Time.frameCount; } }
    public static bool Lanzar { get { return fLanzar == Time.frameCount; } }
    public static bool Soltar { get { return fSoltar == Time.frameCount; } }
    public static bool Pausa { get { return fPausa == Time.frameCount; } }

    /// <summary>Toque o clic que EMPIEZA en este cuadro (para menús y diálogos). Funciona con mouse y con dedo.</summary>
    public static bool Toque { get { return Pointer.current != null && Pointer.current.press.wasPressedThisFrame; } }
    public static Vector2 PosicionToque { get { return Pointer.current != null ? Pointer.current.position.ReadValue() : Vector2.zero; } }

    /// <summary>Domain Reload apagado: se llama desde Juego.Reiniciar.</summary>
    public static void Reiniciar()
    {
        Mover = Vector2.zero; Correr = false; Camara = Vector2.zero; Zoom = 0f;
        fSaltar = fUsar = fLanzar = fSoltar = fPausa = -1;
    }
}

/// <summary>
/// Dibuja y lee los controles táctiles. Corre ANTES que los demás scripts (orden -500) para que los botones
/// se vean como "presionados este cuadro" cuando el elfo, el interactor o el director los revisan.
/// Lee los dedos directo del Touchscreen (varios a la vez: caminar y girar la cámara al mismo tiempo).
/// </summary>
[DefaultExecutionOrder(-500)]
public class ControlesTactiles : MonoBehaviour
{
    const float RadioJoystick = 110f;      // en pixeles de la pantalla de referencia (1920x1080)

    CanvasGroup grupo;
    RectTransform capa, baseJoy, perilla;
    RectTransform bSaltar, bUsar, bLanzar, bSoltar, bPausa;
    Image imgUsar;
    Vector2 baseInicial = new Vector2(260, 250);

    int dedoJoy = -1, dedoCam = -1, dedoCam2 = -1;
    Vector2 inicioJoy;
    float distPellizco;
    Interactor interactor;
    Inventario inventario;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Crear()
    {
        if (!Tactil.Activo || FindAnyObjectByType<ControlesTactiles>() != null) return;
        new GameObject("ControlesTactiles").AddComponent<ControlesTactiles>();
    }

    void Start()
    {
        capa = UIConstructor.Capa("Tactil", 30);
        grupo = UIConstructor.Grupo(capa, 0f);
        grupo.blocksRaycasts = false;      // los dedos se leen a mano: la UI de abajo no debe tapar nada

        baseJoy = Circulo("JoyBase", new Vector2(0, 0), baseInicial, 2 * RadioJoystick + 40, new Color(1f, 1f, 1f, 0.16f));
        perilla = Circulo("JoyPerilla", Vector2.zero, Vector2.zero, 110, new Color(1f, 0.85f, 0.45f, 0.75f));
        perilla.SetParent(baseJoy, false);
        perilla.anchorMin = perilla.anchorMax = new Vector2(0.5f, 0.5f);
        perilla.anchoredPosition = Vector2.zero;

        bSaltar = Boton("Saltar", new Vector2(1, 0), new Vector2(-170, 175), 190, "Saltar", 36);
        bUsar = Boton("Usar", new Vector2(1, 0), new Vector2(-395, 135), 150, "E", 60);
        imgUsar = bUsar.GetComponent<Image>();
        bLanzar = Boton("Lanzar", new Vector2(1, 0), new Vector2(-190, 400), 135, "Bola", 34);
        bSoltar = Boton("Soltar", new Vector2(1, 0), new Vector2(-405, 345), 115, "Q", 48);
        bPausa = Boton("Pausa", new Vector2(1, 1), new Vector2(-80, -185), 100, "II", 40);   // debajo del reloj

        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { interactor = j.GetComponent<Interactor>(); inventario = j.GetComponent<Inventario>(); }
    }

    RectTransform Circulo(string nombre, Vector2 ancla, Vector2 pos, float tam, Color color)
    {
        var rt = UIConstructor.Rect(nombre, capa, ancla, ancla, new Vector2(tam, tam), pos);
        var img = UIConstructor.Imagen(rt, color);
        img.sprite = UIConstructor.SpriteCirculo();
        img.raycastTarget = false;
        return rt;
    }

    RectTransform Boton(string nombre, Vector2 ancla, Vector2 pos, float tam, string texto, int letra)
    {
        var rt = Circulo(nombre, ancla, pos, tam, new Color(1f, 1f, 1f, 0.22f));
        var t = UIConstructor.Texto(UIConstructor.PantallaCompleta("Texto", rt), texto, letra, new Color(1f, 1f, 1f, 0.9f));
        t.raycastTarget = false;
        UIConstructor.Sombra(t);
        return rt;
    }

    static bool Dentro(RectTransform rt, Vector2 p)
    {
        return rt.gameObject.activeInHierarchy && RectTransformUtility.RectangleContainsScreenPoint(rt, p, null);
    }

    /// <summary>Pixeles de pantalla -> pixeles de la pantalla de referencia del Canvas.</summary>
    static float Escala { get { return UIConstructor.Canvas.scaleFactor; } }

    void Update()
    {
        bool jugando = Juego.Estado == Juego.Modo.Jugando;
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, jugando ? 1f : 0f, Time.unscaledDeltaTime * 4f);
        Tactil.Mover = Vector2.zero; Tactil.Camara = Vector2.zero; Tactil.Zoom = 0f; Tactil.Correr = false;

        // botones que solo salen cuando sirven
        bool lleva = inventario != null && inventario.TieneObjeto;
        if (bSoltar.gameObject.activeSelf != lleva) bSoltar.gameObject.SetActive(lleva);
        bool hayAlgo = interactor != null && interactor.Actual != null;
        imgUsar.color = hayAlgo ? new Color(1f, 0.8f, 0.35f, 0.75f) : new Color(1f, 1f, 1f, 0.22f);

        var ts = Touchscreen.current;
        if (ts == null || !jugando) { SoltarJoy(); dedoCam = dedoCam2 = -1; return; }

        foreach (var toque in ts.touches)
        {
            int id = toque.touchId.ReadValue();
            var fase = toque.phase.ReadValue();
            Vector2 p = toque.position.ReadValue();

            if (fase == UnityEngine.InputSystem.TouchPhase.Began)
            {
                if (Dentro(bPausa, p)) { Tactil.fPausa = Time.frameCount; continue; }
                if (Dentro(bSaltar, p)) { Tactil.fSaltar = Time.frameCount; continue; }
                if (Dentro(bUsar, p)) { Tactil.fUsar = Time.frameCount; continue; }
                if (Dentro(bLanzar, p)) { Tactil.fLanzar = Time.frameCount; continue; }
                if (Dentro(bSoltar, p)) { Tactil.fSoltar = Time.frameCount; continue; }
                if (p.x < Screen.width * 0.45f && p.y < Screen.height * 0.75f && dedoJoy < 0)
                {
                    dedoJoy = id; inicioJoy = p;
                    baseJoy.position = p;          // joystick flotante: aparece bajo el dedo
                }
                else if (p.x >= Screen.width * 0.45f)
                {
                    if (dedoCam < 0) dedoCam = id;
                    else if (dedoCam2 < 0) { dedoCam2 = id; distPellizco = -1f; }
                }
                continue;
            }

            bool termina = fase == UnityEngine.InputSystem.TouchPhase.Ended || fase == UnityEngine.InputSystem.TouchPhase.Canceled;
            if (id == dedoJoy)
            {
                if (termina) { SoltarJoy(); continue; }
                Vector2 off = (p - inicioJoy) / Escala;
                Vector2 v = Vector2.ClampMagnitude(off / RadioJoystick, 1f);
                Tactil.Mover = v;
                Tactil.Correr = v.magnitude > 0.92f;
                perilla.anchoredPosition = v * RadioJoystick;
            }
            else if (id == dedoCam || id == dedoCam2)
            {
                if (termina)
                {
                    if (id == dedoCam) { dedoCam = dedoCam2; }
                    dedoCam2 = -1;
                    continue;
                }
                if (dedoCam2 < 0 && id == dedoCam) Tactil.Camara += toque.delta.ReadValue() / Escala;
            }
        }

        // pellizco: dos dedos en el lado de la cámara
        if (dedoCam >= 0 && dedoCam2 >= 0)
        {
            Vector2 a = Vector2.zero, b = Vector2.zero;
            foreach (var t in ts.touches)
            {
                int id = t.touchId.ReadValue();
                if (id == dedoCam) a = t.position.ReadValue(); else if (id == dedoCam2) b = t.position.ReadValue();
            }
            float d = Vector2.Distance(a, b) / Escala;
            if (distPellizco > 0f) Tactil.Zoom = d - distPellizco;
            distPellizco = d;
        }
    }

    void SoltarJoy()
    {
        dedoJoy = -1;
        if (baseJoy == null) return;
        baseJoy.anchoredPosition = baseInicial;
        perilla.anchoredPosition = Vector2.zero;
    }
}
