using System.Collections.Generic;
using Unity.Cinemachine;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// Calidad gráfica con presets (Bajo, Medio, Alto) o Personalizado.
/// Cada ajuste se guarda en PlayerPrefs y se aplica EN CALIENTE (sin reiniciar el juego):
///   escala      -> renderScale del asset URP (dibuja a menos resolución y la estira; lo que más ayuda a GPUs chicas)
///   sombras     -> distancia, resolución y cascadas de las sombras de la luna/lámparas
///   ssao        -> oclusión ambiental (sombrita en rincones); cuesta bastante
///   bloom       -> resplandor de luces y focos
///   detalle     -> lodBias: a qué distancia los pinos pasan a su versión simple
///   luces       -> cuántas luces puntuales del pueblo se encienden (solo las cercanas a la cámara)
///   particulas  -> multiplicador de nieve, humo y chispas
///   distancia   -> hasta dónde dibuja la cámara (más allá está la niebla)
///   fps         -> 30, 60, VSync o sin límite
/// En el editor, al salir de Play se regresan los valores originales del asset URP (si no, se quedarían guardados).
/// </summary>
public static class Graficos
{
    [System.Serializable]
    public class Ajustes
    {
        public float escala = 1f;
        public int sombras = 3;        // 0 apagadas, 1 bajas, 2 medias, 3 altas
        public bool ssao = true;
        public bool bloom = true;
        public float detalle = 2f;
        public int luces = 2;          // 0 pocas, 1 cercanas, 2 todas
        public float particulas = 1f;
        public float distancia = 300f;
        public int fps = 2;            // 0 = 30, 1 = 60, 2 = VSync, 3 = sin límite

        public Ajustes Copia() { return (Ajustes)MemberwiseClone(); }
    }

    public static readonly string[] NombresPreset = { "Bajo", "Medio", "Alto", "Personalizado" };
    public const int Personalizado = 3;
    public static readonly string[] NombresSombras = { "Apagadas", "Bajas", "Medias", "Altas" };
    public static readonly string[] NombresLuces = { "Pocas", "Cercanas", "Todas" };
    public static readonly string[] NombresFps = { "30", "60", "VSync", "Sin límite" };

    // Computadora (medido en la laptop con Intel integrada: Bajo ~65 FPS, Medio ~50, Alto ~35)
    static readonly Ajustes[] PresetsPC = {
        new Ajustes { escala = 0.7f,  sombras = 1, ssao = false, bloom = true, detalle = 0.7f, luces = 0, particulas = 0.4f, distancia = 210f, fps = 1 },
        new Ajustes { escala = 0.85f, sombras = 2, ssao = false, bloom = true, detalle = 1.2f, luces = 1, particulas = 0.7f, distancia = 250f, fps = 2 },
        new Ajustes { escala = 1f,    sombras = 3, ssao = true,  bloom = true, detalle = 2f,   luces = 2, particulas = 1f,   distancia = 300f, fps = 2 },
    };
    // Teléfono y navegador: el "Alto" de aquí es un nivel ESTABLE (sin SSAO, resolución 85%, sombras medias);
    // el de computadora era demasiado para un celular.
    static readonly Ajustes[] PresetsMovil = {
        new Ajustes { escala = 0.6f,  sombras = 0, ssao = false, bloom = true, detalle = 0.6f, luces = 0, particulas = 0.3f, distancia = 200f, fps = 0 },
        new Ajustes { escala = 0.75f, sombras = 1, ssao = false, bloom = true, detalle = 1.0f, luces = 1, particulas = 0.5f, distancia = 230f, fps = 1 },
        new Ajustes { escala = 0.85f, sombras = 2, ssao = false, bloom = true, detalle = 1.4f, luces = 2, particulas = 0.8f, distancia = 270f, fps = 1 },
    };
    public static bool EsMovil { get { return Application.isMobilePlatform || Application.platform == RuntimePlatform.WebGLPlayer; } }
    static Ajustes[] Presets { get { return EsMovil ? PresetsMovil : PresetsPC; } }

    /// <summary>Calidad AUTOMÁTICA: empieza en el preset sugerido y, si el juego va lento, baja un nivel
    /// (ver AutoCalidad). Se apaga sola cuando el jugador elige un preset o mueve un ajuste.</summary>
    public static bool Automatico
    {
        get { return PlayerPrefs.GetInt("gr_auto", 1) == 1; }
        set { PlayerPrefs.SetInt("gr_auto", value ? 1 : 0); }
    }
    /// <summary>SSAO solo existe en el renderer de computadora.</summary>
    public static bool HaySsao { get { Cargar(); if (Urp != null) GuardarOriginales(Urp); return ssao != null; } }

    /// <summary>Se avisa cuando cambia el preset o un ajuste (la UI se refresca).</summary>
    public static event System.Action AlCambiar;

    static int preset = -1;
    static Ajustes actual;

    public static int Preset { get { Cargar(); return preset; } }
    public static Ajustes Actual { get { Cargar(); return actual; } }

    /// <summary>Preset sugerido la primera vez: teléfono o navegador = Medio (de su tabla); computadora = Alto.
    /// Con la calidad automática, si no va fluido baja sola (ver AutoCalidad).</summary>
    static int PresetInicial()
    {
        return EsMovil ? 1 : 2;
    }

    static void Cargar()
    {
        if (actual != null) return;
        preset = PlayerPrefs.GetInt("gr_preset", -1);
        if (preset < 0) preset = PresetInicial();
        actual = preset < Personalizado ? Presets[preset].Copia() : new Ajustes();
        if (preset == Personalizado)
        {
            var b = Presets[2];
            actual.escala = PlayerPrefs.GetFloat("gr_escala", b.escala);
            actual.sombras = PlayerPrefs.GetInt("gr_sombras", b.sombras);
            actual.ssao = PlayerPrefs.GetInt("gr_ssao", b.ssao ? 1 : 0) == 1;
            actual.bloom = PlayerPrefs.GetInt("gr_bloom", b.bloom ? 1 : 0) == 1;
            actual.detalle = PlayerPrefs.GetFloat("gr_detalle", b.detalle);
            actual.luces = PlayerPrefs.GetInt("gr_luces", b.luces);
            actual.particulas = PlayerPrefs.GetFloat("gr_particulas", b.particulas);
            actual.distancia = PlayerPrefs.GetFloat("gr_distancia", b.distancia);
            actual.fps = PlayerPrefs.GetInt("gr_fps", b.fps);
        }
    }

    public static void Guardar()
    {
        Cargar();
        PlayerPrefs.SetInt("gr_preset", preset);
        PlayerPrefs.SetFloat("gr_escala", actual.escala);
        PlayerPrefs.SetInt("gr_sombras", actual.sombras);
        PlayerPrefs.SetInt("gr_ssao", actual.ssao ? 1 : 0);
        PlayerPrefs.SetInt("gr_bloom", actual.bloom ? 1 : 0);
        PlayerPrefs.SetFloat("gr_detalle", actual.detalle);
        PlayerPrefs.SetInt("gr_luces", actual.luces);
        PlayerPrefs.SetFloat("gr_particulas", actual.particulas);
        PlayerPrefs.SetFloat("gr_distancia", actual.distancia);
        PlayerPrefs.SetInt("gr_fps", actual.fps);
        PlayerPrefs.Save();
    }

    /// <summary>Elige Bajo/Medio/Alto (copia sus valores) o Personalizado (se queda con los actuales).</summary>
    public static void ElegirPreset(int i)
    {
        Automatico = false;      // el jugador eligió: ya no se cambia solo
        ElegirNivel(i);
    }

    /// <summary>Cambia de preset SIN apagar la calidad automática (lo usa AutoCalidad).</summary>
    public static void ElegirNivel(int i)
    {
        Cargar();
        preset = Mathf.Clamp(i, 0, Personalizado);
        if (preset < Personalizado) actual = Presets[preset].Copia();
        Aplicar();
        if (AlCambiar != null) AlCambiar();
    }

    /// <summary>Cambia un ajuste suelto: el preset pasa a Personalizado.</summary>
    public static void Cambiar(System.Action<Ajustes> cambio)
    {
        Cargar();
        Automatico = false;
        cambio(actual);
        preset = Personalizado;
        Aplicar();
        if (AlCambiar != null) AlCambiar();
    }

    /// <summary>Botón "Auto" del menú: vuelve al preset sugerido y deja que se ajuste solo.</summary>
    public static void ActivarAutomatico()
    {
        Automatico = true;
        ElegirNivel(PresetInicial());
        var ac = Object.FindAnyObjectByType<AutoCalidad>();
        if (ac != null) ac.Reiniciar();
    }

    // ------------------------------------------------------------------ aplicar
    static bool originalesGuardados;
    static float origDistSombra, origEscala;
    static int origResPrincipal, origResAdicional, origCascadas;
    static bool origSsao;
    static ScriptableRendererFeature ssao;
    static readonly Dictionary<ParticleSystem, float> origParticulas = new Dictionary<ParticleSystem, float>();

    static UniversalRenderPipelineAsset Urp { get { return GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset; } }

    static void GuardarOriginales(UniversalRenderPipelineAsset urp)
    {
        if (originalesGuardados) return;
        originalesGuardados = true;
        origDistSombra = urp.shadowDistance; origEscala = urp.renderScale;
        origResPrincipal = urp.mainLightShadowmapResolution; origResAdicional = urp.additionalLightsShadowmapResolution;
        origCascadas = urp.shadowCascadeCount;
        foreach (var d in urp.rendererDataList)
            if (d != null) foreach (var f in d.rendererFeatures)
                if (f != null && f.GetType().Name.Contains("AmbientOcclusion")) ssao = f;
        origSsao = ssao != null && ssao.isActive;
#if UNITY_EDITOR
        Application.quitting += RestaurarAsset;    // en el editor: no dejar el asset modificado al salir de Play
#endif
    }

    static void RestaurarAsset()
    {
        Application.quitting -= RestaurarAsset;
        var urp = Urp;
        if (urp == null || !originalesGuardados) return;
        urp.shadowDistance = origDistSombra; urp.renderScale = origEscala;
        urp.mainLightShadowmapResolution = origResPrincipal; urp.additionalLightsShadowmapResolution = origResAdicional;
        urp.shadowCascadeCount = origCascadas;
        if (ssao != null) ssao.SetActive(origSsao);
    }

    /// <summary>Aplica todos los ajustes actuales. Se puede llamar las veces que sea (al iniciar, al empezar
    /// a jugar para alcanzar a las partículas creadas por la dificultad, y en cada cambio del menú).</summary>
    public static void Aplicar()
    {
        Cargar();
        var a = actual;
        var urp = Urp;
        if (urp != null)
        {
            GuardarOriginales(urp);
            urp.renderScale = Mathf.Clamp(a.escala, 0.5f, 1f);
            switch (a.sombras)
            {
                case 0: urp.shadowDistance = 0f; break;
                case 1: urp.shadowDistance = 15f; urp.mainLightShadowmapResolution = 1024; urp.additionalLightsShadowmapResolution = 1024; urp.shadowCascadeCount = 1; break;
                case 2: urp.shadowDistance = 25f; urp.mainLightShadowmapResolution = 2048; urp.additionalLightsShadowmapResolution = 1024; urp.shadowCascadeCount = 2; break;
                default:
                    urp.shadowDistance = origDistSombra; urp.mainLightShadowmapResolution = origResPrincipal;
                    urp.additionalLightsShadowmapResolution = origResAdicional; urp.shadowCascadeCount = origCascadas; break;
            }
            if (ssao != null) ssao.SetActive(a.ssao);
        }

        QualitySettings.lodBias = a.detalle;

        // FPS
        switch (a.fps)
        {
            case 0: QualitySettings.vSyncCount = 0; Application.targetFrameRate = 30; break;
            case 1: QualitySettings.vSyncCount = 0; Application.targetFrameRate = 60; break;
            case 2: QualitySettings.vSyncCount = 1; Application.targetFrameRate = -1; break;
            default: QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1; break;
        }

        // Bloom (en el perfil del volumen global; volume.profile ya es la copia de la partida)
        foreach (var v in Object.FindObjectsByType<Volume>())
        {
            if (!v.isGlobal || v.sharedProfile == null) continue;
            Bloom b;
            if (v.profile.TryGet(out b)) b.active = a.bloom;
        }

        // Distancia de dibujado: cámara principal y lentes de Cinemachine (el lente manda sobre la cámara)
        if (Camera.main != null) Camera.main.farClipPlane = a.distancia;
        foreach (var c in Object.FindObjectsByType<CinemachineCamera>(FindObjectsInactive.Include))
        {
            var l = c.Lens; l.FarClipPlane = a.distancia; c.Lens = l;
        }

        // Partículas: multiplicador sobre la emisión ORIGINAL de cada sistema
        var quitar = new List<ParticleSystem>();
        foreach (var kv in origParticulas) if (kv.Key == null) quitar.Add(kv.Key);
        foreach (var p in quitar) origParticulas.Remove(p);
        foreach (var ps in Object.FindObjectsByType<ParticleSystem>(FindObjectsInactive.Include))
        {
            var em = ps.emission;
            if (!origParticulas.ContainsKey(ps)) origParticulas[ps] = em.rateOverTimeMultiplier;
            em.rateOverTimeMultiplier = origParticulas[ps] * a.particulas;
        }

        // Luces del pueblo (se desvanecen con la distancia; no se apagan de golpe)
        LucesCercanas.Asegurar().Radio = a.luces == 0 ? 40f : a.luces == 1 ? 70f : float.PositiveInfinity;

        // Calidad automática (vigila los FPS mientras se juega)
        if (Automatico && Object.FindAnyObjectByType<AutoCalidad>() == null)
            new GameObject("AutoCalidad").AddComponent<AutoCalidad>();
    }

    /// <summary>Domain Reload está apagado: se llama desde Juego.Reiniciar al dar Play.</summary>
    public static void Reiniciar()
    {
        preset = -1; actual = null;
        originalesGuardados = false; ssao = null;
        origParticulas.Clear();
        AlCambiar = null;
    }
}

/// <summary>
/// Luces DECORATIVAS (farolitos del pueblo, faroles del patio y el brillo de las galletas). Dos reglas:
///  1) Radio: a partir de 'Radio' metros de la cámara se desvanecen en una franja de 15 m.
///  2) Cupo: en teléfono/navegador URP Forward+ solo dibuja 32 luces a la vez; la escena tiene ~55 y, si se pasan,
///     URP elige cuáles dibujar cada cuadro => luces que parpadean o desaparecen al moverse. Por eso aquí solo se
///     dejan prendidas las 'Maximo' más cercanas (12 en teléfono) y las demás se apagan. Todo cambio es gradual
///     (la intensidad sube/baja en ~0.5 s), así nunca "brincan".
/// Las luces importantes (taller, árbol, elfo, chimenea, estrella) no se tocan.
/// </summary>
public class LucesCercanas : MonoBehaviour
{
    public float Radio = float.PositiveInfinity;
    public int Maximo = 999;
    const float Franja = 15f;
    readonly List<Light> luces = new List<Light>();
    readonly List<float> baseInt = new List<float>();
    float[] actual, distancia;
    int[] orden;
    bool[] dentroCupo;
    float siguienteOrden;

    public static LucesCercanas Asegurar()
    {
        var l = FindAnyObjectByType<LucesCercanas>();
        if (l == null) l = new GameObject("LucesCercanas").AddComponent<LucesCercanas>();
        l.Maximo = Graficos.EsMovil ? 12 : 999;
        return l;
    }

    void Start()
    {
        foreach (var luz in FindObjectsByType<Light>(FindObjectsInactive.Include))
        {
            if (luz.type != LightType.Point || luz.shadows != LightShadows.None) continue;
            if (luz.GetComponent<LuzParpadeante>() != null) continue;
            var padre = luz.transform.parent;
            bool farolito = padre != null && padre.name == "Luces_Farolitos";
            bool galleta = padre != null && padre.GetComponent<Galleta>() != null;
            if (!farolito && !galleta && !luz.name.StartsWith("Luz_Farol")) continue;
            luces.Add(luz); baseInt.Add(luz.intensity);
        }
        int n = luces.Count;
        actual = new float[n]; distancia = new float[n]; orden = new int[n]; dentroCupo = new bool[n];
        for (int i = 0; i < n; i++) { actual[i] = 1f; orden[i] = i; dentroCupo[i] = true; }
    }

    void Update()
    {
        var cam = Camera.main;
        if (cam == null || actual == null) return;
        Vector3 p = cam.transform.position;
        int n = luces.Count;
        for (int i = 0; i < n; i++)
            distancia[i] = luces[i] != null && luces[i].gameObject.activeInHierarchy ? Vector3.Distance(luces[i].transform.position, p) : float.MaxValue;

        // el cupo se recalcula 4 veces por segundo (ordenar 40 números es barato)
        if (Time.unscaledTime >= siguienteOrden)
        {
            siguienteOrden = Time.unscaledTime + 0.25f;
            System.Array.Sort(orden, (a, b) => distancia[a].CompareTo(distancia[b]));
            for (int k = 0; k < n; k++) dentroCupo[orden[k]] = k < Maximo && distancia[orden[k]] < float.MaxValue;
        }

        bool todas = float.IsInfinity(Radio);
        float paso = Time.unscaledDeltaTime * 2f;
        for (int i = 0; i < n; i++)
        {
            var luz = luces[i];
            if (luz == null || distancia[i] == float.MaxValue) continue;
            float meta = 1f;
            if (!todas)
            {
                meta = 1f - Mathf.Clamp01((distancia[i] - Radio) / Franja);
                meta = meta * meta * (3f - 2f * meta);
            }
            if (!dentroCupo[i]) meta = 0f;
            actual[i] = Mathf.MoveTowards(actual[i], meta, paso);
            bool prender = actual[i] > 0.01f;
            if (luz.enabled != prender) luz.enabled = prender;
            if (prender) luz.intensity = baseInt[i] * actual[i];
        }
    }
}

/// <summary>
/// Calidad automática "estable": mientras se juega mide los FPS en ventanas de 6 s. Si el promedio queda
/// por debajo del mínimo (26 en teléfono/navegador, 30 en computadora) baja un preset y vuelve a medir.
/// Después de 4 ventanas buenas deja de vigilar. Solo actúa si Graficos.Automatico está prendido.
/// </summary>
public class AutoCalidad : MonoBehaviour
{
    float tiempo, espera = 4f;
    int cuadros, buenas;

    public void Reiniciar() { tiempo = 0f; cuadros = 0; buenas = 0; espera = 4f; enabled = true; }

    void Update()
    {
        if (!Graficos.Automatico || Juego.Estado != Juego.Modo.Jugando) return;
        if (espera > 0f) { espera -= Time.unscaledDeltaTime; return; }   // dejar que se acomode tras un cambio
        tiempo += Time.unscaledDeltaTime; cuadros++;
        if (tiempo < 6f) return;
        float fps = cuadros / tiempo;
        tiempo = 0f; cuadros = 0;
        float minimo = Graficos.EsMovil ? 26f : 30f;
        int nivel = Graficos.Preset;
        if (fps < minimo && nivel > 0 && nivel < Graficos.Personalizado)
        {
            Graficos.ElegirNivel(nivel - 1);
            Graficos.Guardar();
            UIAviso.Mensaje("Calidad ajustada a " + Graficos.NombresPreset[nivel - 1] + " para que vaya fluido", 3f);
            espera = 3f; buenas = 0;
        }
        else if (++buenas >= 4) enabled = false;     // estable: ya no hace falta vigilar
    }
}
