using UnityEngine;

/// <summary>
/// VENTISCAS (Difícil / Imposible): cada cierto tiempo llega una tormenta de nieve de 'duracion' segundos.
///  - Intensidad 0 → 1 → 0 (sube 3 s, se mantiene, baja 3 s). Todo se mezcla con esa intensidad:
///    · NIEBLA: RenderSettings.fogDensity sube de la normal (0.009) hasta 'nieblaMax' => casi no ves lejos.
///      Bajo techo sube mucho menos (adentro no hay tormenta, solo se ve por las ventanas).
///    · NIEVE DE LADO: un sistema de partículas propio pegado al jugador, con los copos volando en la dirección del viento.
///    · SONIDO: bucle "ventisca" 2D (más bajito bajo techo).
///    · EMPUJE: AFUERA el elfo se mueve un poquito con el viento (ElfoController.empujeExterno, m/s).
///  - La dirección del viento cambia un poco en cada ventisca.
///  - Mientras hay ventisca la brújula falla en Difícil (UIBrujula lee Ventisca.Activa).
/// Dificultad.Aplicar() la crea solo en los niveles que la usan.
/// </summary>
public class Ventisca : MonoBehaviour
{
    public static float Intensidad { get; private set; }
    public static bool Activa => Intensidad > 0.3f;

    public float intervaloMin = 120f, intervaloMax = 180f;
    public float duracion = 20f;
    public float nieblaMax = 0.06f;
    public float fuerzaEmpuje = 1.1f;

    Color colorBase; public Color colorTormenta = new Color(0.32f, 0.38f, 0.48f);
    float nieblaBase, siguiente, inicio = -999f, tiempoJuego;
    Vector3 direccion = new Vector3(1f, 0f, 0.3f).normalized;
    Transform jugador; ElfoController elfo;
    ParticleSystem copos; AudioSource sonido;
    float bajoTecho, siguienteRevision; bool avisado;

    public void Configurar(float min, float max) { intervaloMin = min; intervaloMax = max; siguiente = Random.Range(min * 0.5f, min * 0.8f); }

    void Start()
    {
        nieblaBase = RenderSettings.fogDensity; colorBase = RenderSettings.fogColor;
        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { jugador = j.transform; elfo = j.GetComponent<ElfoController>(); }
        sonido = gameObject.AddComponent<AudioSource>();
        sonido.clip = Resources.Load<AudioClip>("Audio/ventisca"); sonido.loop = true; sonido.volume = 0f; sonido.playOnAwake = false;
        if (sonido.clip != null) sonido.Play();
        if (siguiente <= 0f) siguiente = intervaloMin * 0.6f;
    }

    void Update()
    {
        bool jugando = Juego.Estado == Juego.Modo.Jugando;
        // el tiempo de la ventisca solo corre mientras juegas (en diálogos/cinemáticas se congela)
        if (jugando) tiempoJuego += Time.deltaTime;
        if (jugando && tiempoJuego >= siguiente && tiempoJuego > inicio + duracion)
        {
            inicio = tiempoJuego;
            siguiente = tiempoJuego + duracion + Random.Range(intervaloMin, intervaloMax);
            float a = Random.Range(0f, 360f);
            direccion = Quaternion.Euler(0f, a, 0f) * Vector3.forward;
            if (!avisado) { avisado = true; UIAviso.Mensaje("¡Se viene una VENTISCA! Casi no se ve nada y el viento te empuja.\nRefúgiate en el taller o en el establo.", 5f); }
            else UIAviso.Mensaje("¡Otra ventisca!", 2.5f);
        }
        float t = tiempoJuego - inicio;
        float objetivo = t < 0f || t > duracion ? 0f : Mathf.Min(Mathf.Clamp01(t / 3f), Mathf.Clamp01((duracion - t) / 3f));
        if (Juego.Estado == Juego.Modo.Final) objetivo = 0f;
        Intensidad = Mathf.MoveTowards(Intensidad, objetivo, Time.deltaTime * 0.8f);

        // ¿bajo techo? (rayo de arriba hacia abajo, igual que NieveSigueJugador)
        if (jugador != null && Time.time > siguienteRevision)
        {
            siguienteRevision = Time.time + 0.4f;
            bajoTecho = EstaBajoTecho(jugador.position) ? 1f : 0f;
        }
        float afuera = 1f - bajoTecho;

        RenderSettings.fogDensity = Mathf.Lerp(nieblaBase, Mathf.Lerp(nieblaBase * 2f, nieblaMax, afuera), Intensidad);
        // la niebla de noche es azul oscuro: en la tormenta se vuelve gris-azul claro (nieve en el aire que refleja la luz)
        RenderSettings.fogColor = Color.Lerp(colorBase, colorTormenta, Intensidad * Mathf.Lerp(0.4f, 1f, afuera));
        if (sonido != null) sonido.volume = Intensidad * Mathf.Lerp(0.3f, 0.85f, afuera) * Opciones.Ambiente;
        if (elfo != null)
        {
            // ráfagas: el empuje sube y baja con un ruido suave
            float rafaga = 0.6f + 0.8f * Mathf.PerlinNoise(Time.time * 0.7f, 3.1f);
            elfo.empujeExterno = jugando ? direccion * fuerzaEmpuje * rafaga * Intensidad * afuera : Vector3.zero;
        }
        Copos(Intensidad * afuera);
    }

    public static bool EstaBajoTecho(Vector3 pos)
    {
        Vector3 cabeza = pos + Vector3.up * 1.6f;
        RaycastHit hit;
        return Physics.Raycast(cabeza + Vector3.up * 30f, Vector3.down, out hit, 29.8f, ~0, QueryTriggerInteraction.Ignore)
               && hit.collider.GetComponentInParent<ElfoController>() == null;
    }

    void Copos(float k)
    {
        if (jugador == null) return;
        if (copos == null)
        {
            var go = new GameObject("NieveVentisca");
            go.transform.SetParent(jugador, false); go.transform.localPosition = Vector3.up * 2f;
            copos = go.AddComponent<ParticleSystem>();
            copos.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var m = copos.main; m.loop = true; m.startLifetime = 1.6f; m.startSpeed = 0f; m.maxParticles = 1500;
            m.startSize = new ParticleSystem.MinMaxCurve(0.06f, 0.14f); m.startColor = new Color(0.92f, 0.96f, 1f, 0.9f);
            m.simulationSpace = ParticleSystemSimulationSpace.World; m.gravityModifier = 0.15f;
            var sh = copos.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(26f, 6f, 26f);
            var col = copos.colorOverLifetime; col.enabled = true;
            var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                                              new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.15f), new GradientAlphaKey(1f, 0.8f), new GradientAlphaKey(0f, 1f) });
            col.color = g;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = BolaNieve.matParticulas;
            r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.04f; r.lengthScale = 1.5f;   // copos "estirados" por la velocidad
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            copos.Play();
        }
        // el viento: velocidad en la dirección de la ventisca (en espacio del mundo)
        var vel = copos.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
        Vector3 v = direccion * 14f;
        vel.x = new ParticleSystem.MinMaxCurve(v.x * 0.8f, v.x * 1.2f);
        vel.y = new ParticleSystem.MinMaxCurve(-2f, -0.5f);
        vel.z = new ParticleSystem.MinMaxCurve(v.z * 0.8f, v.z * 1.2f);
        // los copos nacen "contra el viento" para que crucen frente al jugador
        copos.transform.position = jugador.position + Vector3.up * 2f - direccion * 9f;
        var em = copos.emission; em.rateOverTime = 1100f * k;
    }

    void OnDestroy()
    {
        Intensidad = 0f;
        if (nieblaBase > 0f) { RenderSettings.fogDensity = nieblaBase; RenderSettings.fogColor = colorBase; }
        if (elfo != null) elfo.empujeExterno = Vector3.zero;
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Intensidad = 0f; }
}
