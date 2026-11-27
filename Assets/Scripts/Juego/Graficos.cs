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

    static readonly Ajustes[] Presets = {
        new Ajustes { escala = 0.7f,  sombras = 1, ssao = false, bloom = true, detalle = 0.7f, luces = 0, particulas = 0.4f, distancia = 210f, fps = 1 },
        new Ajustes { escala = 0.85f, sombras = 2, ssao = false, bloom = true, detalle = 1.2f, luces = 1, particulas = 0.7f, distancia = 250f, fps = 2 },
        new Ajustes { escala = 1f,    sombras = 3, ssao = true,  bloom = true, detalle = 2f,   luces = 2, particulas = 1f,   distancia = 300f, fps = 2 },
    };

    /// <summary>Se avisa cuando cambia el preset o un ajuste (la UI se refresca).</summary>
    public static event System.Action AlCambiar;

    static int preset = -1;
    static Ajustes actual;

    public static int Preset { get { Cargar(); return preset; } }
    public static Ajustes Actual { get { Cargar(); return actual; } }

    /// <summary>Preset sugerido la primera vez: teléfono o navegador = Bajo; gráficos integrados (Intel, o poca
    /// memoria de video) = Medio; tarjeta dedicada = Alto. Medido: en la laptop con Intel Arc integrada
    /// Alto da ~35 FPS, Medio ~50 y Bajo ~65 (ver documentacion/md/analisis/ANALISIS_RENDIMIENTO.md).</summary>
    static int PresetInicial()
    {
        if (Application.isMobilePlatform || Application.platform == RuntimePlatform.WebGLPlayer) return 0;
        bool integrada = SystemInfo.graphicsDeviceVendor.ToLower().Contains("intel") || SystemInfo.graphicsMemorySize < 3000;
        return integrada ? 1 : 2;
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
        cambio(actual);
        preset = Personalizado;
        Aplicar();
        if (AlCambiar != null) AlCambiar();
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

        // Luces del pueblo
        LucesCercanas.Asegurar().Radio = a.luces == 0 ? 25f : a.luces == 1 ? 55f : float.PositiveInfinity;
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
/// Enciende solo las luces puntuales de la ambientación (farolitos, faroles, casas) que estén a menos de
/// 'Radio' metros de la cámara. Revisa 4 veces por segundo. Con Radio infinito quedan todas encendidas.
/// No toca luces con sombra, ni las del jugador, el árbol o las cinemáticas.
/// </summary>
public class LucesCercanas : MonoBehaviour
{
    public float Radio = float.PositiveInfinity;
    readonly List<Light> luces = new List<Light>();
    float siguiente;

    public static LucesCercanas Asegurar()
    {
        var l = FindAnyObjectByType<LucesCercanas>();
        if (l == null) l = new GameObject("LucesCercanas").AddComponent<LucesCercanas>();
        return l;
    }

    void Start()
    {
        var raiz = GameObject.Find("--- AMBIENTACION ---");
        if (raiz == null) return;
        foreach (var luz in raiz.GetComponentsInChildren<Light>(true))
            if (luz.enabled && luz.type == LightType.Point && luz.shadows == LightShadows.None) luces.Add(luz);
    }

    void Update()
    {
        if (Time.unscaledTime < siguiente) return;
        siguiente = Time.unscaledTime + 0.25f;
        var cam = Camera.main;
        if (cam == null) return;
        Vector3 p = cam.transform.position;
        float r2 = Radio * Radio;
        foreach (var luz in luces)
        {
            if (luz == null) continue;
            bool prender = float.IsInfinity(Radio) || (luz.transform.position - p).sqrMagnitude < r2;
            if (luz.enabled != prender) luz.enabled = prender;
        }
    }
}
