using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEngine;
using UnityEngine.AI;

/// <summary>
/// GRABADOR DEL TRÁILER. Se agrega en Play (desde el editor) y graba tomas de cine del juego en dificultad IMPOSIBLE:
///  - Usa una cámara PROPIA (copia de la Main Camera con su post-proceso) que renderiza a una textura de 1920x1080.
///  - Time.captureFramerate = 30: el juego avanza exactamente 1/30 s por cuadro aunque guardar cada imagen tarde,
///    así el video sale fluido aunque la compu vaya lenta.
///  - Cada toma es una corrutina que acomoda la escena (elfo, cascanueces, ventisca, apagón...) y mueve la cámara.
///  - Los cuadros se guardan en Library/Trailer/&lt;toma&gt;/f_00000.jpg; luego Herramientas/trailer_montar.sh arma el video.
///  - El HUD no sale (la cámara del tráiler no dibuja la UI): los textos se ponen en el montaje.
/// Vista previa: GrabadorTrailer.Paso = 10 guarda solo 1 de cada 10 cuadros (para revisar encuadres rápido).
/// </summary>
[DefaultExecutionOrder(1000)]
public class GrabadorTrailer : MonoBehaviour
{
    public static string[] Solo;            // null = todas las tomas; o los nombres de las que se graban
    public static int Paso = 1;             // 1 = todos los cuadros
    public static string Estado = "";       // para consultar el avance desde el editor
    public static bool Termino;
    public const int Ancho = 1920, Alto = 1080, Fps = 30;
    const string Carpeta = "Library/Trailer";

    Camera cam; RenderTexture rt; Texture2D tex; Camera camOriginal; Light relleno;
    Transform jugador, rumbo; ElfoController elfo;
    DirectorJuego director; ArbolNavidad arbol;
    readonly List<Cascanueces> cascanueces = new List<Cascanueces>();
    readonly List<CascanuecesNevado> nevados = new List<CascanuecesNevado>();
    int dificultadAntes, secretoAntes, elfoAntes;
    VarianteElfo variante;

    // estado de la toma actual
    System.Action<float> camara;            // se llama en LateUpdate con el tiempo de la toma (después de que todo se movió)
    float tToma; bool grabando; int cuadro; string carpetaToma;
    Vector3? destinoElfo; bool elfoCorre; float temblor;
    Cascanueces persigue;
    bool globos;            // ¿se permiten los globitos de diálogo en esta toma?

    static readonly BindingFlags Priv = BindingFlags.NonPublic | BindingFlags.Instance;

    // ================================================================== preparación
    IEnumerator Start()
    {
        Termino = false; Estado = "preparando";
        Time.captureFramerate = Fps;
        director = FindAnyObjectByType<DirectorJuego>();
        arbol = ArbolNavidad.Instancia;
        if (director != null) { director.StopAllCoroutines(); director.enabled = false; }
        // sin cinemáticas de etapa (el director ya no escucha al árbol)
        var ev = typeof(ArbolNavidad).GetField("AlCompletarEtapa", Priv);
        if (ev != null && arbol != null) ev.SetValue(arbol, null);
        // la calidad automática bajaría los gráficos porque grabar es lento
        foreach (var mb in FindObjectsByType<MonoBehaviour>()) if (mb.GetType().Name == "AutoCalidad") Destroy(mb.gameObject);
        Graficos.ElegirNivel(2);

        var j = GameObject.FindGameObjectWithTag("Player");
        jugador = j.transform; elfo = j.GetComponent<ElfoController>();
        rumbo = new GameObject("RumboTrailer").transform;
        elfo.camara = rumbo;
        // los 4 elfos: Jengibre (secreto) se desbloquea SOLO mientras se graba; al terminar se regresa como estaba
        secretoAntes = PlayerPrefs.GetInt("ElfoSecreto", 0); elfoAntes = PlayerPrefs.GetInt("Elfo", 0);
        PlayerPrefs.SetInt("ElfoSecreto", 1);
        variante = j.GetComponentInChildren<VarianteElfo>(true);
        ElfoVar(0);          // Tilo, el clásico

        // IMPOSIBLE (se regresa la dificultad elegida al terminar)
        dificultadAntes = Dificultad.Elegido;
        Dificultad.Elegido = 3;
        Dificultad.NuevaPartida();
        Dificultad.Aplicar();
        Juego.Estado = Juego.Modo.Jugando;
        CamaraOrbitaMouse.BloquearCursor(false);
        var linterna = j.GetComponent<Linterna>();
        if (linterna != null) linterna.Configurar(99999f);
        foreach (var c in FindObjectsByType<Cascanueces>()) { cascanueces.Add(c); c.distanciaAtrapar = -10f; }
        foreach (var n in FindObjectsByType<CascanuecesNevado>()) { nevados.Add(n); n.enabled = false; }
        VentiscaApagada();

        // cámara de cine: copia de la Main Camera (mismo post-proceso), sin Cinemachine ni oído
        camOriginal = Camera.main;
        var go = Instantiate(camOriginal.gameObject);
        go.name = "CamTrailer"; go.tag = "Untagged";
        foreach (var comp in go.GetComponents<Component>())
            if (!(comp is Transform) && !(comp is Camera) && comp.GetType().Name != "UniversalAdditionalCameraData") Destroy(comp);
        cam = go.GetComponent<Camera>();
        rt = new RenderTexture(Ancho, Alto, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
        cam.targetTexture = rt; cam.fieldOfView = 45f;
        tex = new Texture2D(Ancho, Alto, TextureFormat.RGB24, false);
        camOriginal.enabled = false;          // no se dibuja dos veces la escena
        // luz de relleno pegada a la cámara (como en el cine) para que se vean las caras; se prende por toma
        relleno = new GameObject("Relleno").AddComponent<Light>();
        relleno.transform.SetParent(cam.transform, false);
        relleno.transform.localPosition = new Vector3(0.4f, 0.3f, 0f);
        relleno.type = LightType.Point; relleno.range = 8f; relleno.intensity = 1.6f; relleno.shadows = LightShadows.None;
        relleno.color = new Color(1f, 0.88f, 0.75f); relleno.enabled = false;
        // Imposible le baja 1 EV a la imagen (a propósito, para jugar a oscuras); en el tráiler se compensa para que
        // se aprecie, conservando lo nocturno, y la viñeta queda más suave
        foreach (var v in FindObjectsByType<UnityEngine.Rendering.Volume>())
        {
            UnityEngine.Rendering.Universal.ColorAdjustments ca; UnityEngine.Rendering.Universal.Vignette vi;
            if (v.profile.TryGet(out ca)) { ca.postExposure.overrideState = true; ca.postExposure.value = 0.25f; }
            if (v.profile.TryGet(out vi)) vi.intensity.value = 0.32f;
        }
        yield return null;

        foreach (var toma in Tomas())
        {
            if (Solo != null && System.Array.IndexOf(Solo, toma.Key) < 0) continue;
            Estado = "toma " + toma.Key;
            yield return toma.Value();
        }
        Estado = "listo"; Termino = true;
        Debug.Log("[Trailer] Listo: " + Path.GetFullPath(Carpeta));
    }

    void OnDestroy()
    {
        Time.captureFramerate = 0;
        Ventisca.Multiplicador = 1f;
        Tactil.Reiniciar();
        if (camOriginal != null) camOriginal.enabled = true;
        if (rt != null) rt.Release();
        Dificultad.Elegido = dificultadAntes;
        PlayerPrefs.SetInt("ElfoSecreto", secretoAntes); PlayerPrefs.SetInt("Elfo", elfoAntes); PlayerPrefs.Save();
    }

    /// <summary>0 Tilo, 1 Nieves, 2 Chispa, 3 Jengibre.</summary>
    void ElfoVar(int i) { if (variante != null) variante.Aplicar(i); }

    // ================================================================== bucle de cada cuadro
    void Update()
    {
        // piloto automático del elfo: sigue el camino del NavMesh hasta destinoElfo
        if (destinoElfo.HasValue && jugador != null)
        {
            var camino = new NavMeshPath();
            Vector3 siguiente = destinoElfo.Value;
            if (NavMesh.CalculatePath(jugador.position, destinoElfo.Value, NavMesh.AllAreas, camino) && camino.corners.Length > 1)
            {
                siguiente = camino.corners[1];
                if ((siguiente - jugador.position).sqrMagnitude < 0.25f && camino.corners.Length > 2) siguiente = camino.corners[2];
            }
            Vector3 d = siguiente - jugador.position; d.y = 0f;
            Vector3 aFin = destinoElfo.Value - jugador.position; aFin.y = 0f;
            if (aFin.magnitude > 0.5f && d.sqrMagnitude > 0.0001f)
            {
                rumbo.rotation = Quaternion.LookRotation(d.normalized);
                Tactil.Mover = new Vector2(0f, 1f); Tactil.Correr = elfoCorre;
            }
            else { Tactil.Mover = Vector2.zero; Tactil.Correr = false; }
        }
        // el cascanueces de la persecución siempre "sabe" dónde está el elfo
        if (persigue != null)
        {
            typeof(Cascanueces).GetField("ultimaPosVista", Priv).SetValue(persigue, jugador.position);
            typeof(Cascanueces).GetField("ultimaVezVisto", Priv).SetValue(persigue, Time.time);
        }
    }

    void LateUpdate()
    {
        if (camara != null) camara(tToma);
        AcomodarGlobos();
        if (temblor > 0f)
        {
            float k = temblor * temblor;
            cam.transform.position += new Vector3(Mathf.PerlinNoise(Time.time * 25f, 1f) - 0.5f, Mathf.PerlinNoise(2f, Time.time * 25f) - 0.5f, 0f) * 0.25f * k;
            cam.transform.rotation *= Quaternion.Euler((Mathf.PerlinNoise(Time.time * 20f, 5f) - 0.5f) * 4f * k, (Mathf.PerlinNoise(7f, Time.time * 20f) - 0.5f) * 4f * k, 0f);
            temblor = Mathf.MoveTowards(temblor, 0f, Time.deltaTime * 2.2f);
        }
    }

    /// <summary>GloboCascanueces se orienta y escala con Camera.main; en el tráiler esa cámara está apagada y el globo
    /// se quedaba de 4 m. Se repite aquí su misma cuenta, pero con la cámara del tráiler (sin tocar el código del juego).
    /// En las tomas donde no deben hablar, se esconden.</summary>
    void AcomodarGlobos()
    {
        foreach (var g in FindObjectsByType<GloboCascanueces>())
        {
            var t = g.transform.Find("Globo"); if (t == null || !t.gameObject.activeSelf) continue;
            if (!globos) { t.gameObject.SetActive(false); continue; }
            float escalaPadre = Mathf.Max(0.05f, g.transform.lossyScale.y);
            t.rotation = Quaternion.LookRotation(t.position - cam.transform.position, Vector3.up);
            float d = Vector3.Distance(cam.transform.position, t.position);
            t.localScale = Vector3.one * 0.0042f * Mathf.Clamp(d / 7f, 0.45f, 2.0f) / escalaPadre;
        }
    }

    /// <summary>Graba 'seg' segundos. 'previo' = segundos que corre la escena ANTES de grabar (para que arranque
    /// la acción). 'eventos' se llama cada cuadro con el tiempo de la toma (negativo durante el previo).</summary>
    IEnumerator Grabar(string nombre, float seg, System.Action<float> movCamara, System.Action<float> eventos = null, float previo = 0f)
    {
        camara = movCamara; tToma = -previo;
        carpetaToma = Path.Combine(Carpeta, nombre);
        if (Directory.Exists(carpetaToma)) foreach (var f in Directory.GetFiles(carpetaToma, "*.jpg")) File.Delete(f);
        Directory.CreateDirectory(carpetaToma);
        int total = Mathf.RoundToInt(seg * Fps);
        int previos = Mathf.RoundToInt(previo * Fps);
        for (int i = -previos; i < total; i++)
        {
            tToma = i / (float)Fps;
            if (eventos != null) eventos(tToma);
            yield return new WaitForEndOfFrame();
            if (i >= 0 && i % Paso == 0)
            {
                var antes = RenderTexture.active;
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, Ancho, Alto), 0, 0, false);
                RenderTexture.active = antes;
                File.WriteAllBytes(Path.Combine(carpetaToma, "f_" + i.ToString("00000") + ".jpg"), tex.EncodeToJPG(93));
            }
        }
        camara = null; relleno.enabled = false; globos = false;
    }

    // ================================================================== utilidades de cámara y escena
    static float Suave(float t) { t = Mathf.Clamp01(t); return t * t * (3f - 2f * t); }
    static float Salida(float t) { t = Mathf.Clamp01(t); return 1f - (1f - t) * (1f - t) * (1f - t); }

    void Poner(Vector3 pos, Vector3 mira, float fov = 45f)
    {
        cam.transform.position = pos;
        cam.transform.rotation = Quaternion.LookRotation(mira - pos);
        cam.fieldOfView = fov;
    }

    void Mover(float t, float dur, Vector3 p0, Vector3 p1, Vector3 m0, Vector3 m1, float fov0 = 45f, float fov1 = 45f)
    {
        float k = Suave(t / dur);
        Poner(Vector3.Lerp(p0, p1, k), Vector3.Lerp(m0, m1, k), Mathf.Lerp(fov0, fov1, k));
    }

    void Elfo(Vector3 pos, float yaw)
    {
        destinoElfo = null; Tactil.Mover = Vector2.zero; Tactil.Correr = false;
        NavMeshHit h; if (NavMesh.SamplePosition(pos, out h, 3f, NavMesh.AllAreas)) pos = h.position;
        elfo.Teletransportar(pos, Quaternion.Euler(0f, yaw, 0f));
        rumbo.rotation = Quaternion.Euler(0f, yaw, 0f);
    }

    void ElfoA(Vector3 destino, bool corre) { destinoElfo = destino; elfoCorre = corre; }
    void ElfoQuieto() { destinoElfo = null; Tactil.Mover = Vector2.zero; Tactil.Correr = false; }

    Cascanueces Cas(int n) { foreach (var c in cascanueces) if (c.name.EndsWith("_" + n)) return c; return cascanueces[0]; }

    void EstadoCas(Cascanueces c, Cascanueces.Estado e)
    {
        typeof(Cascanueces).GetMethod("CambiarA", Priv).Invoke(c, new object[] { e });
    }

    void PonerCas(Cascanueces c, Vector3 pos, float yaw)
    {
        var ag = c.GetComponent<NavMeshAgent>();
        NavMeshHit h; if (NavMesh.SamplePosition(pos, out h, 3f, NavMesh.AllAreas)) pos = h.position;
        if (ag != null && ag.enabled) ag.Warp(pos); else c.transform.position = pos;
        c.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
    }

    /// <summary>Todos los cascanueces dormidos en su lugar de inicio (entre tomas).</summary>
    void DormirTodos()
    {
        persigue = null;
        foreach (var c in cascanueces)
        {
            var p0 = (Vector3)typeof(Cascanueces).GetField("posInicial", Priv).GetValue(c);
            var r0 = (Quaternion)typeof(Cascanueces).GetField("rotInicial", Priv).GetValue(c);
            EstadoCas(c, Cascanueces.Estado.Dormido);
            PonerCas(c, p0, r0.eulerAngles.y);
        }
    }

    Vector3 Cabeza(Component c)
    {
        foreach (var t in c.GetComponentsInChildren<Transform>()) if (t.name == "Cas_Cabeza") { var rr = t.GetComponent<Renderer>(); return rr != null ? rr.bounds.center : t.position + Vector3.up * 0.4f; }
        return c.transform.position + Vector3.up * 1.8f;
    }

    void Exposicion(float ev)
    {
        foreach (var v in FindObjectsByType<UnityEngine.Rendering.Volume>())
        {
            UnityEngine.Rendering.Universal.ColorAdjustments ca;
            if (v.profile.TryGet(out ca)) ca.postExposure.value = ev;
        }
    }

    // ---- ventisca y apagón (sus temporizadores son privados: se mueven por reflexión)
    Ventisca Vent() { return FindAnyObjectByType<Ventisca>(); }

    void VentiscaApagada()
    {
        var v = Vent(); if (v == null) return;
        var tp = typeof(Ventisca);
        tp.GetField("siguiente", Priv).SetValue(v, 1e9f);
        tp.GetField("inicio", Priv).SetValue(v, -999f);
    }

    void VentiscaYa(Vector3 viento)
    {
        var v = Vent(); if (v == null) return;
        var tp = typeof(Ventisca);
        v.duracion = 999f;
        float tj = (float)tp.GetField("tiempoJuego", Priv).GetValue(v);
        tp.GetField("inicio", Priv).SetValue(v, tj - 4f);     // ya en plena tormenta
        tp.GetField("siguiente", Priv).SetValue(v, 1e9f);
        tp.GetField("direccion", Priv).SetValue(v, viento.normalized);
        tp.GetProperty("Intensidad").SetValue(null, 1f);
        v.nieblaMax = 0.11f;
        Ventisca.Multiplicador = 1.4f;
    }

    void VentiscaFuera()
    {
        Ventisca.Multiplicador = 1f;
        VentiscaApagada();
        var v = Vent(); if (v == null) return;
        typeof(Ventisca).GetProperty("Intensidad").SetValue(null, 0f);
    }

    Apagon Apag() { return FindAnyObjectByType<Apagon>(); }

    void ApagonYa()
    {
        var a = Apag(); if (a == null) return;
        typeof(Apagon).GetField("yaPaso", Priv).SetValue(a, true);
        a.StartCoroutine((IEnumerator)typeof(Apagon).GetMethod("Corte", Priv).Invoke(a, null));
    }

    void LuzDeVuelta()
    {
        var a = Apag(); if (a == null) return;
        a.StopAllCoroutines();
        typeof(Apagon).GetMethod("Poner", Priv).Invoke(a, new object[] { 1f });
        typeof(Apagon).GetProperty("Activo").SetValue(null, false);
    }

    // ================================================================== TOMAS (en el orden en que se graban)
    IEnumerable<KeyValuePair<string, System.Func<IEnumerator>>> Tomas()
    {
        // el orden importa: Siete se cura en 19 y los cascanueces se hacen chiquitos en 21 (lo último)
        yield return Toma("01_exterior", T01Exterior);
        yield return Toma("15_siete", T15Siete);
        yield return Toma("16_caja_ojos", T16CajaOjos);
        yield return Toma("03_cascanueces", T03Cascanueces);
        yield return Toma("17_elfos", T17Elfos);
        yield return Toma("05_elfo_corre", T05ElfoCorre);
        yield return Toma("06_persecucion", T06Persecucion);
        yield return Toma("18_nieve", T18Nieve);
        yield return Toma("07_bola", T07Bola);
        yield return Toma("08_apagon", T08Apagon);
        yield return Toma("09_ventisca", T09Ventisca);
        yield return Toma("10_nevado", T10Nevado);
        yield return Toma("11_congelado", T11Congelado);
        yield return Toma("04_caja", T04Caja);
        yield return Toma("12_galleta", T12Galleta);
        yield return Toma("13_arbol", T13Arbol);
        yield return Toma("19_siete_cura", T19SieteCura);
        yield return Toma("14_estrella", T14Estrella);
        yield return Toma("20_rayo", T20Rayo);
        yield return Toma("21_chiquitos", T21Chiquitos);
    }

    static KeyValuePair<string, System.Func<IEnumerator>> Toma(string n, System.Func<IEnumerator> f) { return new KeyValuePair<string, System.Func<IEnumerator>>(n, f); }

    Vector3 LejosDelTaller { get { return new Vector3(12f, 0f, -20f); } }

    // 1) Cielo con aurora que baja hasta el taller nevado
    IEnumerator T01Exterior()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        yield return Grabar("01_exterior", 6f, t => Mover(t, 6f, new Vector3(14f, 6f, -52f), new Vector3(10.5f, 8.5f, -34f),
                                                            new Vector3(6f, 30f, 10f), new Vector3(3f, 3.5f, 0f), 55f, 45f));
    }

    // 2) El tapete vacío: aquí iba el Gran Árbol
    IEnumerator T02Tapete()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        yield return Grabar("02_tapete", 5f, t => Mover(t, 5f, new Vector3(4.2f, 2.8f, -6.4f), new Vector3(2.2f, 1.5f, -3.3f),
                                                         new Vector3(0f, 0.7f, 0.5f), new Vector3(0f, 0.4f, 0.5f), 45f, 40f));
    }

    // 3) Un cascanueces dormido... que abre los ojos (se sacude y se le prenden los ojos rojos, sin moverse)
    IEnumerator T03Cascanueces()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        var c = Cas(1);
        Vector3 cab = Cabeza(c) - Vector3.up * 0.27f, f = c.transform.forward, r = c.transform.right;
        bool desperto = false;
        relleno.enabled = true; relleno.intensity = 0.7f;
        yield return Grabar("03_cascanueces", 6.5f,
            t => Mover(t, 6.5f, cab + f * 2.1f + r * 0.35f - Vector3.up * 0.15f, cab + f * 0.95f + r * 0.06f - Vector3.up * 0.04f,
                       cab - Vector3.up * 0.08f, cab, 40f, 36f),
            t =>
            {
                if (!desperto && t >= 4.2f)
                {
                    desperto = true;
                    Juego.Estado = Juego.Modo.Cinematica;     // "enemigos en pausa": despierta pero se queda en su lugar
                    EstadoCas(c, Cascanueces.Estado.Patrulla);
                    temblor = 1f;
                }
            });
        Juego.Estado = Juego.Modo.Jugando;
    }

    // 4) Caja sorpresa que salta
    IEnumerator T04Caja()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        CajaSorpresa caja = null;
        foreach (var k in FindObjectsByType<CajaSorpresa>()) if (k.name.StartsWith("Caja_1")) caja = k;
        if (caja == null) yield break;
        Vector3 p = caja.transform.position, f = caja.transform.forward, r = caja.transform.right;
        bool salto = false;
        relleno.enabled = true; relleno.intensity = 1.2f;
        yield return Grabar("04_caja", 3f,
            t => Mover(t, 3f, p + f * 2.4f + r * 0.6f + Vector3.up * 0.45f, p + f * 1.9f + r * 0.4f + Vector3.up * 0.55f,
                       p + Vector3.up * 0.5f, p + Vector3.up * 0.9f, 40f, 44f),
            t => { if (!salto && t >= 0.7f) { salto = true; caja.Saltar(); temblor = 0.5f; } });
    }

    // 5) El elfo corre por el pasillo del taller con su linterna (cámara detrás, baja)
    IEnumerator T05ElfoCorre()
    {
        DormirTodos();
        ElfoVar(1);   // Nieves
        Elfo(new Vector3(-7.5f, 0f, -4.5f), 90f);
        float velAntes = elfo.velocidadCorrer; elfo.velocidadCorrer = 4.2f;
        ElfoA(new Vector3(7f, 0f, -4.5f), true);
        relleno.enabled = true; relleno.intensity = 1.0f;
        yield return Grabar("05_elfo_corre", 3.5f, t =>
        {
            Vector3 e = jugador.position, fw = jugador.forward;
            Poner(e - fw * 2.3f + Vector3.up * 0.95f + jugador.right * 0.45f, e + fw * 3f + Vector3.up * 0.9f, 50f);
        }, null, 0.4f);
        elfo.velocidadCorrer = velAntes; ElfoQuieto();
    }

    // 6) Persecución: el cascanueces viene detrás y lo alcanza (cámara delante del elfo, mirando hacia atrás)
    IEnumerator T06Persecucion()
    {
        DormirTodos();
        ElfoVar(2);   // Chispa
        Elfo(new Vector3(3f, 0f, -4.5f), -90f);
        var c = Cas(2);
        PonerCas(c, new Vector3(6.6f, 0f, -4.5f), -90f);
        EstadoCas(c, Cascanueces.Estado.Persecucion);
        persigue = c;
        float velAntes = elfo.velocidadCorrer;
        elfo.velocidadCorrer = 3.7f;
        var ag = c.GetComponent<NavMeshAgent>();
        ElfoA(new Vector3(-8f, 0f, -4.5f), true);
        relleno.enabled = true; relleno.intensity = 1.6f; globos = true;
        yield return Grabar("06_persecucion", 3.0f, t =>
        {
            if (ag != null) ag.speed = 4.9f;
            Vector3 e = jugador.position;
            Poner(e + new Vector3(-2.4f, 0.65f, -0.95f), e + new Vector3(1.4f, 1.05f, 0.3f), 52f);   // del lado sin mesas
        }, null, 0.2f);
        elfo.velocidadCorrer = velAntes;
        ElfoQuieto(); persigue = null;
    }

    // 7) Bola de nieve al cascanueces => aturdido (cámara baja detrás del elfo, de lado)
    IEnumerator T07Bola()
    {
        DormirTodos();
        PonerCas(Cas(1), LejosDelTaller + Vector3.right * 4f, 0f);       // que no estorbe a la cámara
        ElfoVar(0);   // Tilo
        Elfo(new Vector3(-6f, 0f, -4.5f), 90f);
        var c = Cas(2);
        PonerCas(c, new Vector3(-0.5f, 0f, -4.5f), -90f);
        EstadoCas(c, Cascanueces.Estado.Persecucion);
        persigue = c;
        var ag = c.GetComponent<NavMeshAgent>();
        var lanzador = jugador.GetComponent<LanzadorNieve>();
        if (lanzador != null) lanzador.bolas = lanzador.maximo;
        bool lanzo = false;
        relleno.enabled = true; relleno.intensity = 1.2f; globos = true;
        yield return Grabar("07_bola", 3.5f, t =>
        {
            if (ag != null && !lanzo) ag.speed = 2.6f;
            Poner(new Vector3(-8.4f, 1.15f, -6.4f), new Vector3(-3.0f, 1.0f, -4.5f), 50f);
        }, t =>
        {
            if (!lanzo && t >= 0.7f && lanzador != null)
            {
                lanzo = true;
                // sin Main Camera la puntería asistida no busca objetivo: se lo damos directo
                typeof(LanzadorNieve).GetField("objetivo", Priv).SetValue(lanzador, c);
                typeof(LanzadorNieve).GetMethod("Lanzar", Priv).Invoke(lanzador, null);
            }
            if (lanzo && c.EstadoActual == Cascanueces.Estado.Aturdido) persigue = null;
        });
        persigue = null;
    }

    // 8) Apagón: en el pasillo, bajo las lámparas; se va la luz y al fondo se prenden unos ojos rojos
    IEnumerator T08Apagon()
    {
        DormirTodos();
        ElfoVar(2);   // Chispa
        Elfo(new Vector3(0.2f, 0f, -5.2f), -100f);
        bool apago = false, ojos = false;
        var c = Cas(1);
        yield return Grabar("08_apagon", 4.5f,
            t => Mover(t, 4.5f, new Vector3(3.0f, 0.8f, -4.6f), new Vector3(2.4f, 0.9f, -4.8f),
                       new Vector3(-4f, 2.2f, -6.2f), new Vector3(-4f, 1.7f, -6.6f), 52f, 46f),
            t =>
            {
                Exposicion(t < 2.3f ? 0.25f : Mathf.Lerp(0.25f, -0.55f, Mathf.Clamp01((t - 2.3f) / 0.5f)));
                if (!apago && t >= 0.9f) { apago = true; ApagonYa(); }
                if (!ojos && t >= 3.0f) { ojos = true; Juego.Estado = Juego.Modo.Cinematica; EstadoCas(c, Cascanueces.Estado.Patrulla); }
            });
        Juego.Estado = Juego.Modo.Jugando;
        Exposicion(0.25f);
        LuzDeVuelta();
    }

    // 9) Ventisca afuera: el elfo avanza contra la tormenta
    IEnumerator T09Ventisca()
    {
        DormirTodos();
        ElfoVar(0);   // Tilo
        Elfo(new Vector3(22f, 0f, -6f), -100f);
        VentiscaYa(new Vector3(1f, 0f, 0.2f));
        ElfoA(new Vector3(8f, 0f, -11f), true);
        relleno.enabled = true; relleno.intensity = 0.8f;
        yield return Grabar("09_ventisca", 3.4f, t =>
        {
            Vector3 e = jugador.position, f = jugador.forward;
            Poner(e - f * 3.2f + Vector3.up * 1.6f + jugador.right * 0.6f, e + f * 4f + Vector3.up * 1.0f, 50f);
        }, null, 2.4f);
        ElfoQuieto();
        VentiscaFuera();
    }

    // 10) Cascanueces NEVADO lanzando bolas de nieve (cámara detrás de su hombro)
    IEnumerator T10Nevado()
    {
        DormirTodos();
        CascanuecesNevado n = null;
        foreach (var x in nevados) if (x.name.StartsWith("Nevado_5")) n = x;
        if (n == null) yield break;
        n.enabled = true;
        Vector3 p = n.transform.position, f = n.transform.forward, r = n.transform.right;
        ElfoVar(1);   // Nieves
        Elfo(p + f * 6.5f + r * 3f, n.transform.eulerAngles.y - 90f);
        ElfoA(p + f * 6.5f - r * 4f, false);
        relleno.enabled = true; relleno.intensity = 0.9f;
        yield return Grabar("10_nevado", 3.5f, t =>
        {
            Vector3 q = n.transform.position, fw = n.transform.forward, rg = n.transform.right;
            Vector3 medio = Vector3.Lerp(q, jugador.position, 0.45f);
            // detrás del hombro del nevado, un poco de lado: se ve él apuntando y al elfo enfrente
            Poner(q - fw * 0.9f + rg * 2.3f + Vector3.up * 1.9f, medio + Vector3.up * 1.0f, 46f);
        }, null, 0.5f);
        n.enabled = false; ElfoQuieto();
    }

    // 11) El elfo congelado en un bloque de hielo (la cámara gira a su alrededor)
    IEnumerator T11Congelado()
    {
        DormirTodos();
        ElfoVar(3);   // Jengibre
        Elfo(new Vector3(14f, 0f, -11f), 200f);
        var frio = FrioJugador.Del(jugador.gameObject);
        bool congelo = false;
        relleno.enabled = true; relleno.intensity = 1.0f;
        yield return Grabar("11_congelado", 3f, t =>
        {
            Vector3 e = jugador.position + Vector3.up * 0.75f;
            float a = Mathf.Lerp(158f, 172f, Suave(t / 3f)) * Mathf.Deg2Rad;
            Poner(e + new Vector3(Mathf.Sin(a), 0f, Mathf.Cos(a)) * Mathf.Lerp(2.7f, 2.0f, Suave(t / 3f)) + Vector3.up * 0.35f, e, 42f);
        }, t =>
        {
            if (!congelo && t >= 0.35f && frio != null) { congelo = true; typeof(FrioJugador).GetMethod("Congelar", Priv).Invoke(frio, null); temblor = 0.6f; }
        });
    }

    // 12) Galleta de jengibre girando
    IEnumerator T12Galleta()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        Galleta g = null;
        foreach (var x in FindObjectsByType<Galleta>()) if (x.name == "Galleta_9") g = x;
        if (g == null) yield break;
        Vector3 p = g.transform.position;
        relleno.enabled = true; relleno.intensity = 1.4f;
        yield return Grabar("12_galleta", 2.5f, t => Mover(t, 2.5f, p + new Vector3(1.4f, 0.4f, -1.4f), p + new Vector3(1.05f, 0.3f, -1.05f),
                                                            p, p + Vector3.up * 0.05f, 40f, 38f));
    }

    // 13) El árbol se arma pieza por pieza (cámara girando)
    IEnumerator T13Arbol()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        int colocadas = 0;
        Vector3 c = arbol.transform.position;
        yield return Grabar("13_arbol", 4f, t =>
        {
            float a = Mathf.Lerp(195f, 250f, Suave(t / 4f)) * Mathf.Deg2Rad;
            float rad = Mathf.Lerp(8.5f, 7.6f, Suave(t / 4f));
            Poner(c + new Vector3(Mathf.Sin(a), 0f, Mathf.Cos(a)) * rad + Vector3.up * Mathf.Lerp(2.4f, 3.4f, t / 4f), c + Vector3.up * 2.6f, 50f);
        }, t =>
        {
            // 11 piezas (todo menos la estrella), una cada 0.3 s; las etapas de Siete (externas) se saltan solas
            while (arbol.PiezasColocadas < arbol.TotalPiezas - 1 && t >= 0.2f + colocadas * 0.3f)
            {
                int antes = arbol.PiezasColocadas;
                arbol.ColocarSiguiente();
                if (arbol.PiezasColocadas > antes) colocadas++;
            }
        });
        DormirTodos();
    }

    // 14) La estrella y las luces del árbol se encienden (solo un vistazo)
    IEnumerator T14Estrella()
    {
        Elfo(LejosDelTaller, 0f);
        for (int k = 0; k < 40 && arbol.PiezasColocadas < arbol.TotalPiezas - 1; k++) arbol.ColocarSiguiente();
        for (int k = 0; k < 5 && !arbol.Completo && arbol.EtapaActual.externa; k++) arbol.ColocarSiguiente();   // curar a Siete / fabricar
        Vector3 c = arbol.transform.position;
        bool puesta = false;
        yield return Grabar("14_estrella", 5.5f,
            t => Mover(t, 5.5f, c + new Vector3(0.3f, 4.9f, -3.6f), c + new Vector3(0.6f, 2.6f, -8.3f),
                       c + Vector3.up * 5.7f, c + Vector3.up * 3.0f, 40f, 50f),
            t => { if (!puesta && t >= 0.6f) { puesta = true; arbol.ColocarSiguiente(); } });
        foreach (var x in cascanueces) EstadoCas(x, Cascanueces.Estado.Congelado);
    }

    // ================================================================== tomas de la historia 1.5
    static readonly Vector3 PosSiete = new Vector3(8f, 1.8f, 5.3f);          // la carita de Siete (igual que DirectorJuego)
    static readonly Vector3 PosCajaLote = new Vector3(1.5f, 0.35f, -7.7f);   // la caja del lote 24
    static readonly Vector3 RepisaChiquitos = new Vector3(-3f, 2.5f, -8.35f);

    DescargaMaquina Descarga() { return FindAnyObjectByType<DescargaMaquina>(); }

    // 15) Siete tiene hipo: cara triste y sale el rayo azul por los cables del techo
    IEnumerator T15Siete()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        var d = Descarga();
        bool tos = false, rayo = false;
        relleno.enabled = true; relleno.intensity = 0.5f;
        Vector3 a = PosSiete + new Vector3(-1.6f, 0.4f, -3.2f), b = PosSiete + new Vector3(-0.9f, 0.2f, -2.2f), arriba = new Vector3(3f, 3.2f, -3.5f);
        yield return Grabar("15_siete", 3.4f, t =>
        {
            if (t < 1.9f) Mover(t, 1.9f, a, b, PosSiete, PosSiete, 42f, 40f);
            else Mover(t - 1.9f, 1.5f, b, PosSiete + new Vector3(-2.6f, 0.4f, -4.2f), PosSiete, new Vector3(6.6f, 6.2f, 6.6f), 40f, 52f);    // sigue el rayo al techo
        }, t =>
        {
            if (!tos && t >= 0.7f) { tos = true; if (Siete.Instancia != null) Siete.Instancia.Descarga(0); }
            if (!rayo && t >= 1.5f) { rayo = true; temblor = 0.5f; if (d != null) StartCoroutine(d.Rayo(d.colorRayo)); }
        });
    }

    // 16) ¡ZAAP! El rayo cae en la caja del lote 24 y se prenden tres pares de ojos rojos
    IEnumerator T16CajaOjos()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        var d = Descarga();
        var ojos = new List<GameObject>();
        Material rojo = null; var foco = GameObject.Find("Siete_Foco_1"); if (foco) rojo = foco.GetComponent<Renderer>().sharedMaterial;
        bool cayo = false; int pares = 0;
        yield return Grabar("16_caja_ojos", 3.0f,
            t => Mover(t, 3f, PosCajaLote + new Vector3(0.35f, 0.9f, 2.3f), PosCajaLote + new Vector3(0.1f, 0.35f, 1.15f),
                       PosCajaLote + Vector3.up * 0.15f, PosCajaLote + Vector3.up * 0.1f, 44f, 40f),
            t =>
            {
                if (!cayo && t >= 0.05f)
                {
                    cayo = true; temblor = 0.6f;
                    if (d != null) StartCoroutine(d.RayoEntre(new[] { new Vector3(0f, 6.7f, 0f), new Vector3(0.8f, 4f, -4f), PosCajaLote + Vector3.up * 0.3f }, d.colorRayo, 0.45f));
                }
                while (pares < 3 && t >= 0.9f + pares * 0.45f) { OjosRojos(pares, rojo, ojos); pares++; }
            });
        foreach (var o in ojos) Destroy(o);
    }

    void OjosRojos(int i, Material rojo, List<GameObject> ojos)
    {
        for (int lado = -1; lado <= 1; lado += 2)
        {
            var o = GameObject.CreatePrimitive(PrimitiveType.Sphere); Destroy(o.GetComponent<Collider>());
            o.transform.position = PosCajaLote + new Vector3(-0.32f + i * 0.32f + lado * 0.035f, 0.05f + (i % 2) * 0.06f, 0.08f);
            o.transform.localScale = Vector3.one * 0.035f;
            var r = o.GetComponent<Renderer>(); if (rojo) r.sharedMaterial = rojo; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            var mpb = new MaterialPropertyBlock();
            mpb.SetColor("baseColorFactor", new Color(1f, 0.05f, 0.03f)); mpb.SetColor("_BaseColor", new Color(1f, 0.05f, 0.03f));
            mpb.SetColor("emissiveFactor", new Color(1f, 0.04f, 0.02f) * 1.6f); mpb.SetColor("_EmissionColor", new Color(1f, 0.04f, 0.02f) * 1.6f);
            r.SetPropertyBlock(mpb);
            ojos.Add(o);
        }
        var l = new GameObject("OjosLuz").AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(1f, 0.1f, 0.05f); l.range = 0.35f; l.intensity = 0.5f;
        l.transform.position = PosCajaLote + new Vector3(-0.32f + i * 0.32f, 0.08f, 0.18f); ojos.Add(l.gameObject);
    }

    // 17) "Elige a tu elfo": los cuatro, uno tras otro, con un brinquito (los nombres se ponen en el montaje)
    IEnumerator T17Elfos()
    {
        DormirTodos();
        Elfo(new Vector3(0.6f, 0f, -2.8f), 180f);
        Transform modelo = variante != null ? variante.transform : jugador;
        Vector3 esc0 = modelo.localScale;
        var luz = new GameObject("LuzSeleccionTrailer").AddComponent<Light>();
        luz.type = LightType.Point; luz.color = new Color(1f, 0.9f, 0.75f); luz.intensity = 2.5f; luz.range = 5f; luz.shadows = LightShadows.None;
        luz.transform.position = jugador.position + new Vector3(0.5f, 1.6f, -1.3f);
        int cual = -1;
        yield return Grabar("17_elfos", 3.0f,
            t => Mover(t, 3f, new Vector3(1.0f, 1.0f, -5.4f), new Vector3(0.85f, 0.95f, -4.9f),
                       jugador.position + Vector3.up * 0.75f, jugador.position + Vector3.up * 0.7f, 40f, 38f),
            t =>
            {
                int i = Mathf.Clamp(Mathf.FloorToInt((t + 0.001f) / 0.72f), 0, 3);
                if (i != cual) { cual = i; ElfoVar(i); }
                float k = (t - i * 0.72f) / 0.25f;                 // brinquito al cambiar
                float pop = k < 1f ? Mathf.Sin(Mathf.Clamp01(k) * Mathf.PI) * 0.12f : 0f;
                modelo.localScale = esc0 * (1f + pop);
            });
        modelo.localScale = esc0;
        Destroy(luz.gameObject);
        ElfoVar(0);
    }

    // 18) Afuera, en Difícil/Imposible, un cascanueces sigue las HUELLAS del elfo en la nieve
    IEnumerator T18Nieve()
    {
        DormirTodos();
        ElfoVar(3);   // Jengibre
        Elfo(new Vector3(4f, 0f, -11.5f), -90f);
        var c = Cas(3);
        PonerCas(c, new Vector3(6.6f, 0f, -11.5f), -90f);
        EstadoCas(c, Cascanueces.Estado.Persecucion);
        persigue = c;
        var ag = c.GetComponent<NavMeshAgent>();
        float velAntes = elfo.velocidadCorrer; elfo.velocidadCorrer = 3.4f;
        ElfoA(new Vector3(-14f, 0f, -11.5f), true);
        bool grito = false;
        relleno.enabled = true; relleno.intensity = 1.0f; globos = true;
        yield return Grabar("18_nieve", 2.8f, t =>
        {
            if (ag != null) ag.speed = 4.4f;
            Vector3 q = c.transform.position, e = jugador.position;
            Poner(q + new Vector3(1.9f, 0.5f, 1.7f), Vector3.Lerp(q, e, 0.5f) + Vector3.up * 0.6f, 52f);   // bajita: se ven las huellas
        }, t =>
        {
            if (!grito && t >= 0.2f) { grito = true; GloboCascanueces.Decir(c.gameObject, "¡Sigan las huellas!", 2.45f, true); }
        }, 1.4f);
        elfo.velocidadCorrer = velAntes;
        ElfoQuieto(); persigue = null;
    }

    // 19) Siete se cura: sus tres focos se ponen verdes, sonríe, jala la palanca y echa chispas doradas
    IEnumerator T19SieteCura()
    {
        DormirTodos(); Elfo(LejosDelTaller, 0f);
        var maq = FindAnyObjectByType<MaquinaRota>();
        var fab = FindAnyObjectByType<FabricaEstrella>();
        int puestas = 0; bool curada = false, palanca = false; int rafagas = 0;
        relleno.enabled = true; relleno.intensity = 0.6f;
        yield return Grabar("19_siete_cura", 3.2f,
            t => Mover(t, 3.2f, PosSiete + new Vector3(-1.3f, 0.1f, -2.7f), PosSiete + new Vector3(-0.9f, 0.0f, -2.1f),
                       PosSiete - Vector3.up * 0.35f, PosSiete - Vector3.up * 0.25f, 46f, 44f),
            t =>
            {
                while (puestas < 3 && t >= 0.2f + puestas * 0.35f)
                {
                    if (Siete.Instancia != null) Siete.Instancia.Instalada(puestas);
                    if (maq != null && maq.chispas != null) maq.chispas.Emit(20);
                    puestas++; temblor = 0.15f;
                }
                if (!curada && t >= 1.3f)
                {
                    curada = true;
                    if (maq != null)
                    {
                        if (maq.chispas != null) { maq.chispas.Emit(50); maq.chispas.Stop(true, ParticleSystemStopBehavior.StopEmitting); }
                        if (maq.luzAlerta != null) { maq.luzAlerta.modo = BrilloEmisivo.Modo.Titilar; maq.luzAlerta.velocidad = 0.5f; maq.luzAlerta.minimo = 0.6f; maq.luzAlerta.CambiarColor(new Color(0.25f, 1f, 0.35f)); }
                    }
                    if (Siete.Instancia != null) Siete.Instancia.Curar();
                }
                if (!palanca && t >= 1.8f) { palanca = true; if (Siete.Instancia != null) StartCoroutine(Siete.Instancia.JalarPalanca()); }
                while (rafagas < 4 && t >= 2.2f + rafagas * 0.22f) { if (fab != null && fab.chispas != null) fab.chispas.Emit(18); rafagas++; temblor = 0.2f; }
            });
    }

    // 20) Final: Siete regresa una descarga DORADA al árbol encendido
    IEnumerator T20Rayo()
    {
        Elfo(LejosDelTaller, 0f);
        var d = Descarga();
        bool rayo = false;
        Vector3 cima = arbol.transform.position + Vector3.up * 3f;
        yield return Grabar("20_rayo", 2.6f, t =>
        {
            Mover(t, 2.6f, new Vector3(-2.5f, 3.0f, -5.5f), new Vector3(-1.4f, 3.4f, -6.8f), new Vector3(4.5f, 6.6f, 4.5f), new Vector3(0f, 5.4f, 0f), 55f, 50f);
        }, t =>
        {
            if (!rayo && t >= 0.15f) { rayo = true; temblor = 0.3f; if (d != null) StartCoroutine(d.Rayo(d.colorRayoBueno)); }
            float k = Mathf.Clamp01(1f - Mathf.Abs(t - 1.0f) / 0.5f);        // destello dorado (en el juego es un fundido de la UI)
            Exposicion(0.25f + 0.6f * k);
        });
        Exposicion(0.25f);
    }

    // 21) Los tres cascanueces, chiquitos y juntitos en la repisa, se les prenden los ojos AZULES
    IEnumerator T21Chiquitos()
    {
        Elfo(LejosDelTaller, 0f);
        var lista = new List<Cascanueces>(cascanueces);
        lista.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
        int i = 0;
        foreach (var c in lista)
        {
            var ag = c.GetComponent<NavMeshAgent>(); if (ag) ag.enabled = false;
            c.enabled = false;
            float alto = 2f; var rs = c.GetComponentsInChildren<Renderer>();
            if (rs.Length > 0) { var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); alto = Mathf.Max(0.1f, b.size.y); }
            c.transform.localScale = c.transform.localScale * (0.42f / alto);
            c.transform.SetPositionAndRotation(RepisaChiquitos + new Vector3((i - 1) * 0.19f, 0f, Mathf.Abs(i - 1) * -0.03f), Quaternion.Euler(0f, (i - 1) * -15f, 0f));
            i++;
        }
        var anims = FindObjectsByType<CascanuecesAnimador>();
        foreach (var a in anims) { a.ojosBuenos = true; a.parpadeo = 0f; }
        var luz = new GameObject("LuzOjosBuenosTrailer").AddComponent<Light>();
        luz.type = LightType.Point; luz.color = new Color(0.35f, 0.6f, 1f); luz.range = 0.6f; luz.intensity = 0f; luz.shadows = LightShadows.None;
        luz.transform.position = RepisaChiquitos + new Vector3(0f, 0.34f, 0.45f);
        Vector3 mira = RepisaChiquitos + Vector3.up * 0.22f;
        relleno.enabled = true; relleno.intensity = 0.25f; relleno.range = 3f;
        Exposicion(0.85f);
        yield return Grabar("21_chiquitos", 3.0f,
            t => Mover(t, 3f, RepisaChiquitos + new Vector3(0.3f, 0.4f, 1.3f), RepisaChiquitos + new Vector3(0.05f, 0.27f, 0.68f), mira, mira, 40f, 40f),
            t =>
            {
                float k = Mathf.Clamp01((t - 0.7f) / 0.6f);
                foreach (var a in anims) a.parpadeo = k;
                luz.intensity = k * 0.05f;
            });
    }
}
