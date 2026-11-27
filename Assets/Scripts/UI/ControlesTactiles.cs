using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.EnhancedTouch;
using UnityEngine.UI;
using Toque = UnityEngine.InputSystem.EnhancedTouch.Touch;
using FaseToque = UnityEngine.InputSystem.TouchPhase;

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
///
/// Usa EnhancedTouch (Touch.activeTouches): Unity lleva la cuenta de cada dedo de principio a fin, aunque un
/// toque empiece y termine entre dos cuadros. Antes se leían los "slots" crudos del Touchscreen y, si se
/// perdía la fase Ended de un dedo, el joystick se quedaba trabado. Además, cada cuadro se revisa que el
/// dedo del joystick y el de la cámara SIGAN existiendo; si no, se sueltan.
/// </summary>
[DefaultExecutionOrder(-500)]
public class ControlesTactiles : MonoBehaviour
{
    const float RadioJoystick = 105f;      // pixeles de la pantalla de referencia (1920x1080)
    static readonly Color Oro = new Color(1f, 0.82f, 0.4f);

    class Boton
    {
        public RectTransform rt; public Image fondo, borde, icono; public Text texto;
        public float pulso;                // 1 al tocarlo, baja solo (animación)
        public bool visible = true;
    }

    CanvasGroup grupo;
    RectTransform capa, baseJoy, perilla;
    Image bordeJoy, perillaImg;
    Boton bSaltar, bUsar, bLanzar, bSoltar, bPausa;
    readonly List<Boton> botones = new List<Boton>();
    Vector2 baseInicial = new Vector2(270, 250);

    int dedoJoy = -1, dedoCam = -1, dedoCam2 = -1;
    Vector2 inicioJoy;
    float distPellizco = -1f, joyActivo;
    Interactor interactor;
    Inventario inventario;
    LanzadorNieve lanzador;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Crear()
    {
        if (!Tactil.Activo || FindAnyObjectByType<ControlesTactiles>() != null) return;
        new GameObject("ControlesTactiles").AddComponent<ControlesTactiles>();
    }

    void OnEnable() { EnhancedTouchSupport.Enable(); }
    void OnDisable() { EnhancedTouchSupport.Disable(); Tactil.Reiniciar(); }

    void Start()
    {
        capa = UIConstructor.Capa("Tactil", 30);
        grupo = UIConstructor.Grupo(capa, 0f);
        grupo.blocksRaycasts = false;      // los dedos se leen a mano: la UI de abajo no debe tapar nada

        // ---- joystick: aro + disco tenue de fondo, perilla con volumen
        baseJoy = UIConstructor.Rect("JoyBase", capa, Vector2.zero, Vector2.zero, new Vector2(2 * RadioJoystick + 70, 2 * RadioJoystick + 70), baseInicial);
        var fondoJoy = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Fondo", baseJoy), new Color(0.05f, 0.08f, 0.18f, 0.35f));
        fondoJoy.sprite = UIConstructor.SpriteCirculo(); fondoJoy.raycastTarget = false;
        bordeJoy = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Aro", baseJoy), new Color(1f, 1f, 1f, 0.45f));
        bordeJoy.sprite = UIConstructor.SpriteAnillo(); bordeJoy.raycastTarget = false;
        for (int i = 0; i < 4; i++)        // 4 flechitas que indican hacia dónde se puede mover
        {
            var f = UIConstructor.Imagen(UIConstructor.Rect("Flecha" + i, baseJoy, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(26, 26),
                                         Quaternion.Euler(0, 0, i * 90f) * new Vector3(0, RadioJoystick + 8f, 0)), new Color(1f, 1f, 1f, 0.4f));
            f.sprite = UIConstructor.SpriteFlecha(); f.raycastTarget = false;
            f.rectTransform.localRotation = Quaternion.Euler(0, 0, i * 90f);
        }
        perilla = UIConstructor.Rect("Perilla", baseJoy, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(120, 120));
        var sombra = UIConstructor.Imagen(UIConstructor.Rect("Sombra", perilla, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(124, 124), new Vector2(0, -6)), new Color(0f, 0f, 0f, 0.3f));
        sombra.sprite = UIConstructor.SpriteCirculo(); sombra.raycastTarget = false;
        perillaImg = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Disco", perilla), Oro);
        perillaImg.sprite = UIConstructor.SpriteDisco(); perillaImg.raycastTarget = false;

        // ---- botones (abajo a la derecha, en arco cómodo para el pulgar)
        bSaltar = CrearBoton("Saltar", new Vector2(1, 0), new Vector2(-175, 185), 200, "Saltar", UIConstructor.SpriteFlecha(), "");
        bUsar = CrearBoton("Usar", new Vector2(1, 0), new Vector2(-410, 140), 150, "Usar", null, "E");
        bLanzar = CrearBoton("Lanzar", new Vector2(1, 0), new Vector2(-215, 420), 140, "Bola", UIConstructor.SpriteCopo(), "");
        bSoltar = CrearBoton("Soltar", new Vector2(1, 0), new Vector2(-430, 360), 115, "Soltar", null, "Q");
        bPausa = CrearBoton("Pausa", new Vector2(1, 1), new Vector2(-80, -190), 96, "", null, "II");

        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { interactor = j.GetComponent<Interactor>(); inventario = j.GetComponent<Inventario>(); lanzador = j.GetComponent<LanzadorNieve>(); }
    }

    Boton CrearBoton(string nombre, Vector2 ancla, Vector2 pos, float tam, string etiqueta, Sprite icono, string letra)
    {
        var b = new Boton();
        b.rt = UIConstructor.Rect(nombre, capa, ancla, ancla, new Vector2(tam, tam), pos);
        b.fondo = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Fondo", b.rt), new Color(0.06f, 0.09f, 0.2f, 0.55f));
        b.fondo.sprite = UIConstructor.SpriteDisco(); b.fondo.raycastTarget = false;
        b.borde = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Aro", b.rt), new Color(1f, 1f, 1f, 0.7f));
        b.borde.sprite = UIConstructor.SpriteAnillo(); b.borde.raycastTarget = false;
        bool hayEtiqueta = etiqueta.Length > 0 && tam >= 130;
        float subir = hayEtiqueta ? tam * 0.1f : 0f;          // el ícono sube un poco para dejar lugar a la etiqueta
        if (icono != null)
        {
            b.icono = UIConstructor.Imagen(UIConstructor.Rect("Icono", b.rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(tam * 0.34f, tam * 0.34f), new Vector2(0, subir + tam * 0.04f)), Color.white);
            b.icono.sprite = icono; b.icono.raycastTarget = false;
        }
        else
        {
            b.texto = UIConstructor.Titulo(UIConstructor.Rect("Letra", b.rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(tam, tam * 0.6f), new Vector2(0, subir)),
                                           letra, Mathf.RoundToInt(tam * 0.38f), Color.white, TextAnchor.MiddleCenter, FontStyle.Bold);
            b.texto.raycastTarget = false; UIConstructor.Sombra(b.texto);
        }
        if (hayEtiqueta)
        {
            var t = UIConstructor.Texto(UIConstructor.Rect("Etiqueta", b.rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(tam, 30), new Vector2(0, -tam * 0.26f)),
                                        etiqueta, Mathf.RoundToInt(Mathf.Clamp(tam * 0.15f, 18f, 26f)), new Color(1f, 1f, 1f, 0.85f));
            t.raycastTarget = false;
        }
        botones.Add(b);
        return b;
    }

    static bool Dentro(Boton b, Vector2 p)
    {
        if (!b.visible) return false;
        // círculo un poco más grande que el dibujo (dedos gordos)
        Vector2 centro = RectTransformUtility.WorldToScreenPoint(null, b.rt.position);
        float r = b.rt.rect.width * 0.5f * UIConstructor.Canvas.scaleFactor * 1.15f;
        return (p - centro).sqrMagnitude <= r * r;
    }

    static float Escala { get { return UIConstructor.Canvas.scaleFactor; } }

    void Pulsar(Boton b) { b.pulso = 1f; }

    void Update()
    {
        bool jugando = Juego.Estado == Juego.Modo.Jugando;
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, jugando ? 1f : 0f, Time.unscaledDeltaTime * 4f);
        Tactil.Mover = Vector2.zero; Tactil.Camara = Vector2.zero; Tactil.Zoom = 0f; Tactil.Correr = false;

        // botones que solo salen cuando sirven, y el de usar brilla si hay algo cerca
        bSoltar.visible = inventario != null && inventario.TieneObjeto;
        bLanzar.visible = lanzador == null || lanzador.enabled;
        bool hayAlgo = interactor != null && interactor.Actual != null;
        foreach (var b in botones)
        {
            if (b.rt.gameObject.activeSelf != b.visible) b.rt.gameObject.SetActive(b.visible);
            b.pulso = Mathf.MoveTowards(b.pulso, 0f, Time.unscaledDeltaTime * 5f);
            float s = 1f - 0.12f * Mathf.Sin(b.pulso * Mathf.PI);
            b.rt.localScale = new Vector3(s, s, 1f);
            bool resalta = b.pulso > 0.01f || (b == bUsar && hayAlgo);
            b.fondo.color = resalta ? new Color(0.95f, 0.62f, 0.18f, 0.75f) : new Color(0.06f, 0.09f, 0.2f, 0.55f);
            b.borde.color = resalta ? Oro : new Color(1f, 1f, 1f, 0.7f);
        }

        if (!jugando) { SoltarTodo(); return; }

        // ¿siguen vivos los dedos que teníamos? (si no, se sueltan: nada se queda trabado)
        bool vivoJoy = false, vivoCam = false, vivoCam2 = false;
        foreach (var t in Toque.activeTouches)
        {
            int id = t.touchId;
            if (id == dedoJoy) vivoJoy = true;
            if (id == dedoCam) vivoCam = true;
            if (id == dedoCam2) vivoCam2 = true;
        }
        if (!vivoJoy) SoltarJoy();
        if (!vivoCam2) { dedoCam2 = -1; distPellizco = -1f; }
        if (!vivoCam) { dedoCam = dedoCam2; dedoCam2 = -1; distPellizco = -1f; }

        foreach (var t in Toque.activeTouches)
        {
            int id = t.touchId;
            Vector2 p = t.screenPosition;

            if (t.phase == FaseToque.Began)
            {
                if (Dentro(bPausa, p)) { Tactil.fPausa = Time.frameCount; Pulsar(bPausa); continue; }
                if (Dentro(bSaltar, p)) { Tactil.fSaltar = Time.frameCount; Pulsar(bSaltar); continue; }
                if (Dentro(bUsar, p)) { Tactil.fUsar = Time.frameCount; Pulsar(bUsar); continue; }
                if (Dentro(bLanzar, p)) { Tactil.fLanzar = Time.frameCount; Pulsar(bLanzar); continue; }
                if (Dentro(bSoltar, p)) { Tactil.fSoltar = Time.frameCount; Pulsar(bSoltar); continue; }
                if (p.x < Screen.width * 0.45f && p.y < Screen.height * 0.8f)
                {
                    if (dedoJoy < 0) { dedoJoy = id; inicioJoy = p; baseJoy.position = p; }   // joystick flotante
                }
                else if (p.x >= Screen.width * 0.45f)
                {
                    if (dedoCam < 0) dedoCam = id;
                    else if (dedoCam2 < 0) { dedoCam2 = id; distPellizco = -1f; }
                }
                continue;
            }
            if (t.phase == FaseToque.Ended || t.phase == FaseToque.Canceled) continue;   // se suelta arriba en el siguiente cuadro

            if (id == dedoJoy)
            {
                Vector2 off = (p - inicioJoy) / Escala;
                Vector2 v = Vector2.ClampMagnitude(off / RadioJoystick, 1f);
                Tactil.Mover = v;
                Tactil.Correr = v.magnitude > 0.92f;
                perilla.anchoredPosition = v * RadioJoystick;
            }
            else if (id == dedoCam && dedoCam2 < 0)
                Tactil.Camara += t.delta / Escala;
        }

        // al soltar en el mismo cuadro (Ended), también se libera
        foreach (var t in Toque.activeTouches)
            if (t.phase == FaseToque.Ended || t.phase == FaseToque.Canceled)
            {
                if (t.touchId == dedoJoy) SoltarJoy();
                if (t.touchId == dedoCam2) { dedoCam2 = -1; distPellizco = -1f; }
                if (t.touchId == dedoCam) { dedoCam = dedoCam2; dedoCam2 = -1; distPellizco = -1f; }
            }

        // pellizco: dos dedos en el lado de la cámara
        if (dedoCam >= 0 && dedoCam2 >= 0)
        {
            Vector2 a = Vector2.zero, b = Vector2.zero;
            foreach (var t in Toque.activeTouches)
            {
                if (t.touchId == dedoCam) a = t.screenPosition; else if (t.touchId == dedoCam2) b = t.screenPosition;
            }
            float d = Vector2.Distance(a, b) / Escala;
            if (distPellizco > 0f) Tactil.Zoom = d - distPellizco;
            distPellizco = d;
        }

        // el joystick brilla mientras se usa
        joyActivo = Mathf.MoveTowards(joyActivo, dedoJoy >= 0 ? 1f : 0f, Time.unscaledDeltaTime * 6f);
        bordeJoy.color = Color.Lerp(new Color(1f, 1f, 1f, 0.45f), Oro, joyActivo);
        float sp = 1f + 0.08f * joyActivo;
        perilla.localScale = new Vector3(sp, sp, 1f);
    }

    void SoltarJoy()
    {
        dedoJoy = -1;
        if (baseJoy == null) return;
        baseJoy.anchoredPosition = baseInicial;
        perilla.anchoredPosition = Vector2.zero;
    }

    void SoltarTodo()
    {
        SoltarJoy();
        dedoCam = dedoCam2 = -1; distPellizco = -1f;
    }
}
