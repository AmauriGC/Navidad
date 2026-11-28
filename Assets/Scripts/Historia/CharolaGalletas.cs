using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using Unity.Cinemachine;

/// <summary>
/// LA CHAROLA DE SANTA (historia 1.5) — minijuego de acomodar las galletas NOCHEBUENA por su forma.
/// Va en la mesita junto a la chimenea. [E] -> la cámara se pone ARRIBA de la charola (vista cenital) y las galletas
/// que traes en la bolsa aparecen en fila enfrente, cada una girada al azar (de 45° en 45°).
///   - Arrastra una galleta con el mouse (o el dedo) hasta su hueco.
///   - Gírala con la rueda, el clic derecho, [R] o el botón "Girar".
///   - SOLO encaja si es SU hueco (la misma forma) y si la letra quedó DERECHA (giro 0°). Si no, rebota a su lugar.
///   - Al encajar: brinca a su hueco con rebote, suena y su letra queda puesta (en el HUD se pinta dorada).
///   - [Esc], [E] o "Listo" para salir; puedes regresar cuando traigas más galletas. La noche sigue avanzando.
/// Con las 10: las letras se prenden una por una (N-O-C-H-E-B-U-E-N-A) con campanitas, sale Jengibre (diálogo) y
/// te da el PODER DE GALLETA; se desbloquea el elfo secreto y el final especial (Galleta.CharolaLlena).
/// Cómo funciona por dentro: la cámara deja de seguir a Cinemachine (se apaga el CinemachineBrain un ratito), el
/// puntero se convierte en un rayo contra un plano horizontal a la altura de la charola y la galleta sigue ese punto.
/// </summary>
public class CharolaGalletas : Interactuable
{
    [Tooltip("Galletas_Formas.glb (10 hijos GalletaForma_0..9).")]
    public GameObject formas;
    [Tooltip("La charola del modelo (tiene los hijos Hueco_0..9).")]
    public Transform charola;
    public float escalaEnCharola = 0.5f;      // los huecos son de la mitad del tamaño de la galleta
    public float alturaCamara = 1.3f;

    class Pieza { public GameObject go; public int idx; public int giro; public Vector3 casa; }

    readonly List<Pieza> bolsa = new List<Pieza>();
    readonly Dictionary<int, GameObject> puestas = new Dictionary<int, GameObject>();
    Transform[] huecos = new Transform[10];
    bool abierto, salir, completando;
    /// <summary>¿Está abierto el minijuego? (el HUD de galletas se queda visible mientras).</summary>
    public static bool Abierta { get { var c = FindAnyObjectByType<CharolaGalletas>(); return c != null && c.abierto; } }
    Pieza agarrada, ultima;
    float alturaPlano;
    Camera cam; CinemachineBrain cerebro;
    RectTransform capa; Text textoAyuda;
    RelojAmanecer reloj;

    void Start()
    {
        if (charola == null) { var g = GameObject.Find("Charola"); if (g) charola = g.transform; }
        if (charola != null) for (int i = 0; i < 10; i++) huecos[i] = charola.Find("Hueco_" + i);
        reloj = FindAnyObjectByType<RelojAmanecer>();
    }

    public GameObject Forma(int i)
    {
        if (formas == null || i < 0) return null;
        var t = formas.transform.Find("GalletaForma_" + i);
        return t ? t.gameObject : null;
    }

    // ------------------------------------------------------------------ Interactuable
    public override bool PuedeInteractuar(Interactor quien) { return !abierto && charola != null; }

    public override string Texto(Interactor quien)
    {
        int n = Galleta.EnBolsa.Count;
        return n > 0 && !Galleta.CharolaLlena ? "Acomodar galletas (" + n + ")" : "Ver la charola de Santa";
    }

    public override void Interactuar(Interactor quien)
    {
        if (Galleta.EnBolsa.Count == 0 && !Galleta.CharolaLlena)
            UIAviso.Mensaje((Galleta.Puestas.Count > 0 ? "Ya hay " + Galleta.Puestas.Count + " acomodadas. " : "") + "Busca las galletas NOCHEBUENA por el pueblo.", 4f);
        StartCoroutine(Minijuego());   // sin galletas en la bolsa (o con la charola llena) solo se ve
    }

    // ------------------------------------------------------------------ el minijuego
    IEnumerator Minijuego()
    {
        abierto = true; salir = false;
        Juego.Estado = Juego.Modo.Cinematica;
        CamaraOrbitaMouse.BloquearCursor(false);
        UIConstructor.AsegurarEventSystem();
        alturaPlano = huecos[0] != null ? huecos[0].position.y + 0.03f : charola.position.y + 0.05f;

        // cámara: se suelta de Cinemachine y baja encima de la charola mirando hacia abajo (arriba de la pantalla = chimenea)
        cam = Camera.main;
        cerebro = cam.GetComponent<CinemachineBrain>();
        if (cerebro) cerebro.enabled = false;
        Vector3 p0 = cam.transform.position; Quaternion r0 = cam.transform.rotation; float fov0 = cam.fieldOfView;
        Vector3 p1 = charola.position + new Vector3(0f, alturaCamara, -0.2f); Quaternion r1 = Quaternion.Euler(90f, 0f, 0f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.6f)
        {
            float k = t * t * (3f - 2f * t);
            cam.transform.SetPositionAndRotation(Vector3.Lerp(p0, p1, k), Quaternion.Slerp(r0, r1, k));
            cam.fieldOfView = Mathf.Lerp(fov0, 55f, k);
            yield return null;
        }
        cam.transform.SetPositionAndRotation(p1, r1); cam.fieldOfView = 55f;

        // un foquito cálido MUY suave arriba de la charola (con más luz las galletas se veían deslavadas)
        var foco = new GameObject("Luz_Charola").AddComponent<Light>();
        foco.type = LightType.Point; foco.color = new Color(1f, 0.82f, 0.6f); foco.intensity = 0.3f; foco.range = 3.2f; foco.shadows = LightShadows.None;
        foco.transform.position = charola.position + Vector3.up * 1.8f;
        ConstruirUI();
        SacarGalletas();
        GestorAudio.Efecto("papel", 0.6f, 0.1f);
        float auto = 0f;
        bool traiaGalletas = bolsa.Count > 0;
        while (!salir)
        {
            if (reloj != null) reloj.Avanzar(Time.deltaTime);   // la noche sigue avanzando
            if (Juego.PruebaAutomatica) { auto += Time.deltaTime; if (auto > 0.4f && bolsa.Count > 0 && !completando) { auto = 0f; var pz = bolsa[0]; pz.giro = 0; Encajar(pz); } }
            else Entrada();
            if (traiaGalletas && bolsa.Count == 0 && !completando && Galleta.Puestas.Count < 10) { yield return new WaitForSeconds(0.8f); salir = true; }
            yield return null;
        }
        while (completando) yield return null;

        // regresar las galletas que no se acomodaron (siguen en la bolsa) y la cámara
        foreach (var pz in bolsa) Destroy(pz.go);
        bolsa.Clear(); agarrada = null; ultima = null;
        if (capa) Destroy(capa.gameObject);
        if (servilleta) Destroy(servilleta);
        if (foco) Destroy(foco.gameObject);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.5f)
        {
            float k = t * t * (3f - 2f * t);
            cam.transform.SetPositionAndRotation(Vector3.Lerp(p1, p0, k), Quaternion.Slerp(r1, r0, k));
            cam.fieldOfView = Mathf.Lerp(55f, fov0, k);
            yield return null;
        }
        cam.fieldOfView = fov0;
        if (cerebro) cerebro.enabled = true;
        if (Galleta.CharolaLlena && !premioDado) { premioDado = true; yield return Premio(); }
        Juego.Estado = Juego.Modo.Jugando;
        CamaraOrbitaMouse.BloquearCursor(true);
        abierto = false;
    }

    GameObject servilleta; bool premioDado;

    void SacarGalletas()
    {
        var lista = new List<int>(Galleta.EnBolsa); lista.Sort();
        if (Galleta.CharolaLlena) lista.Clear();
        float ancho = 0.21f, x0 = -(lista.Count - 1) * ancho / 2f;
        if (lista.Count > 0)
        {
            // una servilleta de papel donde descansan las galletas de la bolsa (arriba del vaso y la notita de la mesa)
            servilleta = GameObject.CreatePrimitive(PrimitiveType.Cube);
            servilleta.name = "Servilleta"; Destroy(servilleta.GetComponent<Collider>());
            servilleta.transform.position = charola.position + new Vector3(0f, 0f, -0.53f) + Vector3.up * (alturaPlano + 0.13f - charola.position.y);
            servilleta.transform.localScale = new Vector3(lista.Count * ancho + 0.12f, 0.006f, 0.27f);
            var mr = servilleta.GetComponent<MeshRenderer>(); mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            Material papel = null;
            var mesita = GameObject.Find("Mesita_Charola");
            if (mesita) foreach (var m in mesita.GetComponent<Renderer>().sharedMaterials) if (m != null && m.name.StartsWith("Nota_Papel")) papel = m;
            if (papel != null) mr.sharedMaterial = papel;
        }
        for (int k = 0; k < lista.Count; k++)
        {
            int idx = lista[k];
            var modelo = Forma(idx); if (modelo == null) continue;
            var pz = new Pieza { idx = idx, giro = Random.Range(0, 8) };
            if (Random.value < 0.25f) pz.giro = 0;
            pz.go = Instantiate(modelo);
            pz.go.name = "Charola_" + modelo.name;
            pz.go.transform.localScale = Vector3.one * escalaEnCharola;
            pz.casa = charola.position + new Vector3(x0 + k * ancho, 0f, -0.53f);
            pz.casa.y = alturaPlano + 0.16f;     // encima de la servilleta
            pz.go.transform.position = pz.casa;
            Orientar(pz);
            bolsa.Add(pz);
        }
    }

    /// <summary>Acostada boca arriba con la letra hacia la chimenea (+Z), más su giro en pasos de 45°.
    /// El modelo mira a +Z en Unity y su "arriba" es +Y: LookRotation(arriba del mundo, hacia la chimenea).</summary>
    void Orientar(Pieza pz)
    {
        pz.go.transform.rotation = Quaternion.AngleAxis(-45f * pz.giro, Vector3.up) * Quaternion.LookRotation(Vector3.up, Vector3.forward);
    }

    void Entrada()
    {
        var kb = Keyboard.current;
        if (kb != null && (kb.escapeKey.wasPressedThisFrame || kb.eKey.wasPressedThisFrame || kb.enterKey.wasPressedThisFrame)) { salir = true; return; }
        if (kb != null && kb.rKey.wasPressedThisFrame) Girar();

        Vector2 pos; bool baja, sube, presionado;
        var ts = Touchscreen.current;
        if (ts != null && (ts.primaryTouch.press.isPressed || ts.primaryTouch.press.wasReleasedThisFrame))
        {
            pos = ts.primaryTouch.position.ReadValue();
            baja = ts.primaryTouch.press.wasPressedThisFrame; sube = ts.primaryTouch.press.wasReleasedThisFrame; presionado = ts.primaryTouch.press.isPressed;
        }
        else
        {
            var m = Mouse.current; if (m == null) return;
            pos = m.position.ReadValue();
            baja = m.leftButton.wasPressedThisFrame; sube = m.leftButton.wasReleasedThisFrame; presionado = m.leftButton.isPressed;
            if (m.rightButton.wasPressedThisFrame) Girar();
            float rueda = m.scroll.ReadValue().y;
            if (Mathf.Abs(rueda) > 0.1f) Girar(rueda > 0f ? 1 : -1);
        }
        Vector3 punto;
        if (!PuntoEnPlano(pos, out punto)) return;
        bool sobreUI = EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();

        if (baja && !sobreUI)
        {
            // se elige EN LA PANTALLA (donde se ve la galleta), no en el piso: así no hay que picarle "abajo" de ella
            float mejor = Screen.height * 0.07f;
            foreach (var pz in bolsa)
            {
                Vector2 c = cam.WorldToScreenPoint(Centro(pz.go));
                float d = Vector2.Distance(c, pos);
                if (d < mejor) { mejor = d; agarrada = pz; desfase = c - pos; }
            }
            if (agarrada != null) { ultima = agarrada; GestorAudio.Efecto("tick", 0.5f, 0.1f); }
        }
        if (agarrada != null && presionado)
        {
            Vector3 p2;
            if (PuntoEnPlano(pos + desfase, out p2))   // la galleta se queda pegada al puntero justo donde la agarraste
            {
                Vector3 meta = new Vector3(p2.x, alturaPlano + 0.06f, p2.z);
                agarrada.go.transform.position = Vector3.Lerp(agarrada.go.transform.position, meta, Time.unscaledDeltaTime * 25f);
            }
        }
        if (agarrada != null && sube) { Soltar(agarrada); agarrada = null; }
    }

    void Girar(int sentido = 1)
    {
        var pz = agarrada ?? ultima;
        if (pz == null && bolsa.Count > 0) pz = bolsa[0];
        if (pz == null) return;
        pz.giro = ((pz.giro + sentido) % 8 + 8) % 8;
        Orientar(pz);
        GestorAudio.Efecto("tick", 0.4f, 0.15f);
    }

    void Soltar(Pieza pz)
    {
        Vector3 p = pz.go.transform.position;
        Transform suyo = huecos[pz.idx];
        if (suyo != null && (Plano(p) - Plano(suyo.position)).sqrMagnitude < 0.09f * 0.09f)
        {
            if (pz.giro == 0) { Encajar(pz); return; }
            Mensaje("¡Casi! Gírala para que la letra quede derecha.");
        }
        else
        {
            for (int i = 0; i < 10; i++)
                if (i != pz.idx && huecos[i] != null && (Plano(p) - Plano(huecos[i].position)).sqrMagnitude < 0.09f * 0.09f)
                { Mensaje("Esa galleta no tiene esa forma."); break; }
        }
        GestorAudio.Efecto("boing", 0.45f, 0.1f);
        StartCoroutine(Mover(pz.go.transform, pz.casa, 0.25f, 0.06f));
    }

    void Encajar(Pieza pz)
    {
        bolsa.Remove(pz);
        if (agarrada == pz) agarrada = null;
        if (ultima == pz) ultima = null;
        Galleta.EnBolsa.Remove(pz.idx);
        Galleta.Puestas.Add(pz.idx);
        Galleta.ActualizarHUD();
        pz.go.transform.SetParent(charola, true);
        puestas[pz.idx] = pz.go;
        Vector3 destino = huecos[pz.idx].position + Vector3.up * 0.012f;
        Orientar(pz);
        StartCoroutine(EncajarAnim(pz.go.transform, destino));
        GestorAudio.Efecto("encajo", 0.8f, 0.05f);
        Mensaje(Guion.AvisoEncajo + "  " + Guion.PalabraGalletas[pz.idx]);
        if (Galleta.Puestas.Count >= 10) StartCoroutine(Completar());
    }

    IEnumerator EncajarAnim(Transform t, Vector3 destino)
    {
        yield return Mover(t, destino, 0.22f, 0.08f);
        Vector3 e = t.localScale;
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.35f)
        {
            float x = k - 1f; const float c = 2.2f;
            t.localScale = e * (1f + (c + 1f) * x * x * x + c * x * x);   // rebote al caer en su hueco
            yield return null;
        }
        t.localScale = e;
    }

    IEnumerator Mover(Transform t, Vector3 destino, float dur, float altura)
    {
        Vector3 a = t.position;
        for (float k = 0f; k < 1f; k += Time.deltaTime / dur)
        {
            t.position = Vector3.Lerp(a, destino, k) + Vector3.up * Mathf.Sin(k * Mathf.PI) * altura;
            yield return null;
        }
        t.position = destino;
    }

    /// <summary>¡La charola está llena! Las letras se prenden una por una: N-O-C-H-E-B-U-E-N-A.</summary>
    IEnumerator Completar()
    {
        completando = true;
        yield return new WaitForSeconds(0.6f);
        string palabra = "";
        for (int i = 0; i < 10; i++)
        {
            GameObject g; if (!puestas.TryGetValue(i, out g) || g == null) continue;
            palabra += Guion.PalabraGalletas[i];
            if (textoAyuda) textoAyuda.text = "<size=60><color=#ffd36b>" + palabra + "</color></size>";
            GestorAudio.Efecto("campanada", 0.5f, 0f);
            StartCoroutine(Brinco(g.transform));
            yield return new WaitForSeconds(0.32f);
        }
        GestorAudio.Efecto("poder", 0.8f, 0f);
        UIBanner.Mostrar("¡" + Guion.PalabraGalletas + "!", "La charola de Santa está completa", "", 3f, new Color(1f, 0.82f, 0.35f));
        yield return new WaitForSeconds(2.2f);
        Galleta.CharolaLlena = true;
        completando = false;
        salir = true;
    }

    IEnumerator Brinco(Transform t)
    {
        Vector3 a = t.position, e = t.localScale;
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.4f)
        {
            t.position = a + Vector3.up * Mathf.Sin(k * Mathf.PI) * 0.05f;
            t.localScale = e * (1f + Mathf.Sin(k * Mathf.PI) * 0.25f);
            yield return null;
        }
        t.position = a; t.localScale = e;
    }

    /// <summary>Jengibre sale a dar las gracias y te da el poder de galleta.</summary>
    IEnumerator Premio()
    {
        bool esJengibre = VarianteElfo.Actual.nombre == "Jengibre";
        yield return UIHistoria.Esperar(esJengibre ? Guion.CharolaCompletaJengibre : Guion.CharolaCompleta);
        bool yaEraTuyo = PlayerPrefs.GetInt("ElfoSecreto", 0) == 1;
        VarianteElfo.DesbloquearSecreto();
        TemblorCamara.Sacudir(0.15f);
        UIAviso.Mensaje("★ " + (yaEraTuyo ? Guion.PoderGalletaYaDesbloqueado : Guion.PoderGalleta) + "\n★ Santa te tiene preparado el FINAL ESPECIAL", 7f);
        Galleta.ActualizarHUD();
    }

    // ------------------------------------------------------------------ ayudantes
    bool PuntoEnPlano(Vector2 pantalla, out Vector3 punto)
    {
        var rayo = cam.ScreenPointToRay(pantalla);
        var plano = new Plane(Vector3.up, new Vector3(0f, alturaPlano, 0f));
        float d;
        if (plano.Raycast(rayo, out d)) { punto = rayo.GetPoint(d); return true; }
        punto = Vector3.zero; return false;
    }

    static Vector3 Plano(Vector3 v) { v.y = 0f; return v; }
    Vector2 desfase;
    static Vector3 Centro(GameObject g) { var r = g.GetComponentInChildren<Renderer>(); return r != null ? r.bounds.center : g.transform.position; }

    void ConstruirUI()
    {
        capa = UIConstructor.Capa("Charola", 40);
        // panel redondeado con la ayuda (arriba al centro) y un titulito navideño
        var fondo = UIConstructor.Rect("Panel", capa, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(1240, 120), new Vector2(0, -78));
        UIConstructor.Redondear(UIConstructor.Imagen(fondo, new Color(0.08f, 0.04f, 0.04f, 0.72f)), 1f);
        UIConstructor.Sombra(UIConstructor.Titulo(UIConstructor.Rect("Titulo", fondo, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(1200, 56), new Vector2(0, -30)),
                                                  Galleta.CharolaLlena ? "La charola de Santa · ¡NOCHEBUENA!" : "La charola de Santa", 40, new Color(1f, 0.83f, 0.42f)), 2f);
        var rt = UIConstructor.Rect("Ayuda", fondo, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(1200, 50), new Vector2(0, 30));
        textoAyuda = UIConstructor.Texto(rt, Ayuda(), 26, Color.white);
        UIConstructor.Sombra(textoAyuda, 2f);
        System.Action<Button, Color> pintar = (b, c) => { ((Image)b.targetGraphic).color = c; var cb = b.colors; cb.highlightedColor = Color.Lerp(c, Color.white, 0.25f); cb.pressedColor = Color.Lerp(c, Color.black, 0.2f); b.colors = cb; };
        if (bolsa.Count > 0 || Galleta.EnBolsa.Count > 0)
        {
            var b1 = UIConstructor.Boton(capa, "Girar", new Vector2(200, 72), Vector2.zero, () => Girar(), 30);
            var r1 = (RectTransform)b1.transform; r1.anchorMin = r1.anchorMax = new Vector2(1f, 1f); r1.anchoredPosition = new Vector2(-135, -72);
            pintar(b1, new Color(0.85f, 0.6f, 0.15f, 0.95f));
        }
        var b2 = UIConstructor.Boton(capa, "Listo", new Vector2(200, 72), Vector2.zero, () => salir = true, 30);
        var r2 = (RectTransform)b2.transform; r2.anchorMin = r2.anchorMax = new Vector2(1f, 1f); r2.anchoredPosition = new Vector2(-135, -158);
        pintar(b2, new Color(0.2f, 0.6f, 0.3f, 0.95f));
    }

    string Ayuda()
    {
        if (Galleta.CharolaLlena || (bolsa.Count == 0 && Galleta.EnBolsa.Count == 0))
            return Galleta.CharolaLlena ? "¡Todas en su lugar! · <b>[Esc]</b> o <b>Listo</b> para salir" : "Todavía no traes galletas · <b>[Esc]</b> o <b>Listo</b> para salir";
        return Tactil.Activo
            ? "Arrastra cada galleta a su hueco · botón <b>Girar</b> para enderezar la letra"
            : "Arrastra cada galleta a su hueco con el mouse · <b>[Rueda]</b> o <b>[Clic derecho]</b> para girar · <b>[Esc]</b> salir";
    }

    float mensajeHasta;
    void Mensaje(string m)
    {
        if (textoAyuda == null || completando) return;
        textoAyuda.text = m; mensajeHasta = Time.time + 1.6f;
    }

    void Update()
    {
        if (abierto && !completando && textoAyuda != null && mensajeHasta > 0f && Time.time > mensajeHasta) { mensajeHasta = 0f; textoAyuda.text = Ayuda(); }
    }
}
