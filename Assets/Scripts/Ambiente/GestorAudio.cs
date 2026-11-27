using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// GESTOR DE AUDIO: uno solo en la escena (singleton). Hace 3 cosas:
///  1) MÚSICA: elige la canción según lo que pasa (título, taller, persecución, final) y cambia
///     entre ellas con un CROSSFADE (dos AudioSource: una baja de volumen mientras la otra sube).
///  2) EFECTOS: cualquier script llama GestorAudio.Efecto("recoger") o GestorAudio.Efecto3D("clac", posicion).
///     Los 3D se oyen más fuerte cerca y más bajo lejos (spatialBlend = 1).
///  3) AMBIENTE: bucles 3D del fuego de la chimenea y de la máquina y viento suave de fondo.
///  (Los pasos los hace PasosElfo.) Los volúmenes se multiplican por los del menú de Opciones.
/// Todos los sonidos son .wav en Assets/Resources/Audio, generados con Herramientas/generar_audio.py.
/// </summary>
public class GestorAudio : MonoBehaviour
{
    static GestorAudio instancia;
    static readonly Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>();

    [Header("Volúmenes")]
    [Range(0, 1)] public float volumenMusica = 0.45f;
    [Range(0, 1)] public float volumenEfectos = 0.8f;
    [Range(0, 1)] public float volumenAmbiente = 0.5f;
    public float duracionCrossfade = 1.5f;

    AudioSource[] musica = new AudioSource[2];   // dos fuentes para el crossfade
    int activa;                                  // cuál de las dos suena ahora
    string cancionActual;
    AudioSource efectos2D, voces2D;
    readonly List<AudioSource> ambientes = new List<AudioSource>();
    readonly List<float> volAmbientes = new List<float>();
    Cascanueces[] cascanueces;
    AudioSource bucleMaquina;

    /// <summary>La Máquina 7 reparada: su ruido baja a un zumbido suave.</summary>
    public static void MaquinaReparada()
    {
        var g = Obtener(); if (g == null || g.bucleMaquina == null) return;
        int i = g.ambientes.IndexOf(g.bucleMaquina);
        if (i >= 0) g.volAmbientes[i] = 0.12f;
        g.bucleMaquina.pitch = 0.75f;
        g.bucleMaquina.volume = 0.12f * g.volumenAmbiente * Opciones.Ambiente;
    }

    // ------------------------------------------------------------------ API para otros scripts
    public static void Efecto(string nombre, float volumen = 1f, float variacionTono = 0.05f)
    {
        var g = Obtener(); var c = Clip(nombre); if (g == null || c == null) return;
        g.efectos2D.pitch = 1f + Random.Range(-variacionTono, variacionTono);
        g.efectos2D.PlayOneShot(c, volumen * g.volumenEfectos * Opciones.Efectos);
    }

    /// <summary>Sílabas de voz al escribir los diálogos: van en su propia fuente para que su cambio de tono
    /// (cada sílaba suena un poquito distinta) no desafine los demás efectos.</summary>
    public static void Voz(string nombre, float volumen = 0.4f, float variacionTono = 0.06f)
    {
        var g = Obtener(); var c = Clip(nombre); if (g == null || c == null) return;
        if (g.voces2D == null) { g.voces2D = g.gameObject.AddComponent<AudioSource>(); g.voces2D.playOnAwake = false; g.voces2D.ignoreListenerPause = true; }
        g.voces2D.pitch = 1f + Random.Range(-variacionTono, variacionTono);
        g.voces2D.PlayOneShot(c, volumen * g.volumenEfectos * Opciones.Efectos);
    }

    /// <summary>Fuente 3D propia para algo que suena seguido (pasos de los cascanueces).</summary>
    public static AudioSource FuentePropia(GameObject go, float min = 1.5f, float max = 18f) { return Fuente3D(go, min, max); }

    /// <summary>Volumen de efectos con las opciones del jugador (para fuentes propias).</summary>
    public static float VolumenEfectos { get { var g = Obtener(); return g != null ? g.volumenEfectos * Opciones.Efectos : 1f; } }

    public static void Efecto3D(string nombre, Vector3 posicion, float volumen = 1f, float variacionTono = 0.08f)
    {
        var g = Obtener(); var c = Clip(nombre); if (g == null || c == null) return;
        var go = new GameObject("Sonido_" + nombre);
        go.transform.position = posicion;
        var s = Fuente3D(go, 2f, 25f);
        s.clip = c; s.volume = volumen * g.volumenEfectos * Opciones.Efectos;
        s.pitch = 1f + Random.Range(-variacionTono, variacionTono);
        s.Play();
        Destroy(go, c.length / s.pitch + 0.1f);
    }

    static GestorAudio Obtener()
    {
        if (instancia == null) instancia = FindAnyObjectByType<GestorAudio>();
        if (instancia == null) instancia = new GameObject("GestorAudio").AddComponent<GestorAudio>();
        return instancia;
    }

    static AudioClip Clip(string nombre)
    {
        AudioClip c;
        if (!clips.TryGetValue(nombre, out c) || c == null)
        {
            c = Resources.Load<AudioClip>("Audio/" + nombre);
            if (c == null) Debug.LogWarning("GestorAudio: no existe Audio/" + nombre);
            clips[nombre] = c;
        }
        return c;
    }

    static AudioSource Fuente3D(GameObject go, float min, float max)
    {
        var s = go.AddComponent<AudioSource>();
        s.spatialBlend = 1f; s.rolloffMode = AudioRolloffMode.Linear;
        s.minDistance = min; s.maxDistance = max; s.dopplerLevel = 0f; s.playOnAwake = false;
        return s;
    }

    // Domain Reload desactivado: el diccionario static se vacía al dar Play.
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { clips.Clear(); instancia = null; }

    // ------------------------------------------------------------------ preparación
    void Awake()
    {
        if (instancia != null && instancia != this) { Destroy(this); return; }
        instancia = this;
        for (int i = 0; i < 2; i++)
        {
            musica[i] = gameObject.AddComponent<AudioSource>();
            musica[i].loop = true; musica[i].volume = 0f; musica[i].playOnAwake = false;
            musica[i].ignoreListenerPause = true;
        }
        efectos2D = gameObject.AddComponent<AudioSource>();
        efectos2D.playOnAwake = false;
        efectos2D.ignoreListenerPause = true;   // los sonidos de la UI se oyen aunque el juego esté en pausa
        Bucle(gameObject, "viento", 0.35f, false);
    }

    void Start()
    {
        cascanueces = FindObjectsByType<Cascanueces>(FindObjectsInactive.Exclude);
        // bucles 3D pegados a los objetos que hacen ruido
        var chimenea = GameObject.Find("Luz_Chimenea");
        if (chimenea != null) Bucle(chimenea, "fuego", 0.9f, true, 1.5f, 12f);
        var maquina = GameObject.Find("Maquina");
        if (maquina != null) bucleMaquina = Bucle(maquina, "maquina", 0.55f, true, 1.5f, 11f);
    }

    AudioSource Bucle(GameObject donde, string nombre, float volumen, bool en3D, float min = 1f, float max = 20f)
    {
        var s = en3D ? Fuente3D(donde, min, max) : donde.AddComponent<AudioSource>();
        s.clip = Clip(nombre); s.loop = true; s.volume = volumen * volumenAmbiente * Opciones.Ambiente;
        ambientes.Add(s); volAmbientes.Add(volumen);
        s.time = Random.Range(0f, s.clip != null ? s.clip.length : 0f);   // que no empiecen todos igual
        s.Play();
        return s;
    }

    // ------------------------------------------------------------------ cada frame
    void Update()
    {
        // Pausa: AudioListener.pause detiene todo menos la música (ignoreListenerPause).
        AudioListener.pause = Juego.Estado == Juego.Modo.Pausa;

        Cancion(ElegirCancion());
        float volObjetivo = volumenMusica * Opciones.Musica * (Juego.Estado == Juego.Modo.Pausa ? 0.4f : 1f);
        float paso = Time.unscaledDeltaTime / Mathf.Max(0.01f, duracionCrossfade);
        for (int i = 0; i < 2; i++)
        {
            float meta = i == activa ? volObjetivo : 0f;
            musica[i].volume = Mathf.MoveTowards(musica[i].volume, meta, paso * Mathf.Max(volumenMusica, 0.01f));
            if (i != activa && musica[i].volume <= 0f && musica[i].isPlaying) musica[i].Stop();
        }
        // volumen del ambiente (por si cambió en el menú de opciones)
        for (int i = 0; i < ambientes.Count; i++)
            if (ambientes[i] != null) ambientes[i].volume = volAmbientes[i] * volumenAmbiente * Opciones.Ambiente;
    }

    /// <summary>Qué canción toca según el estado del juego.</summary>
    string ElegirCancion()
    {
        if (Juego.Estado == Juego.Modo.Titulo || Juego.Perdio) return "musica_titulo";   // Noche de Paz: también para la derrota
        var arbol = ArbolNavidad.Instancia;
        if (Juego.Estado == Juego.Modo.Final || (arbol != null && arbol.Completo)) return "musica_final";
        if (cascanueces != null)
            foreach (var c in cascanueces)
                if (c != null && c.EstadoActual == Cascanueces.Estado.Persecucion) return "musica_persecucion";
        return "musica_taller";
    }

    /// <summary>Crossfade: la canción nueva entra en la fuente que no está sonando.</summary>
    void Cancion(string nombre)
    {
        if (nombre == cancionActual) return;
        cancionActual = nombre;
        activa = 1 - activa;
        musica[activa].clip = Clip(nombre);
        musica[activa].volume = 0f;
        musica[activa].Play();
    }
}
