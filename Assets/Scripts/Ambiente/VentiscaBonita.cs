using UnityEngine;

/// <summary>
/// Detallitos v1.5 · Capas extra de la VENTISCA para que se vea bonita (no solo rayitas):
///   1) Copos grandes y esponjados que pasan cerca de la cámara, despacio y bamboleándose.
///   2) Ráfagas AL RAS DEL SUELO: nieve "barrida" por el viento, larguita y transparente, a la altura de los pies.
///   3) Velo: manchas grandes y muy transparentes de nieve en el aire que cruzan rápido (se ve el viento).
/// Va en el mismo objeto que <see cref="Ventisca"/> y solo lee su intensidad y su dirección; las tres capas siguen al
/// jugador y se apagan bajo techo (mismo rayo de arriba hacia abajo que la Ventisca).
/// </summary>
public class VentiscaBonita : MonoBehaviour
{
    Ventisca ventisca; System.Reflection.FieldInfo campoDir;
    Transform jugador;
    ParticleSystem grandes, ras, velo;
    float afuera = 1f, siguienteRevision;

    void Start()
    {
        ventisca = GetComponent<Ventisca>();
        campoDir = typeof(Ventisca).GetField("direccion", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) jugador = j.transform;
    }

    Vector3 Direccion
    {
        get
        {
            if (ventisca != null && campoDir != null) return (Vector3)campoDir.GetValue(ventisca);
            return new Vector3(1f, 0f, 0.3f).normalized;
        }
    }

    void Update()
    {
        if (jugador == null) return;
        if (Time.time > siguienteRevision)
        {
            siguienteRevision = Time.time + 0.4f;
            afuera = Ventisca.EstaBajoTecho(jugador.position) ? 0f : 1f;
        }
        float k = Ventisca.Intensidad * afuera;
        Cielo();
        if (k <= 0.001f && grandes == null) return;   // nunca ha habido ventisca: no creamos nada
        if (grandes == null) Crear();

        Vector3 dir = Direccion; dir.y = 0f; dir.Normalize();
        float rafaga = 0.7f + 0.6f * Mathf.PerlinNoise(Time.time * 0.6f, 7.3f);
        // todo nace "contra el viento" del jugador para que cruce frente a la cámara
        Vector3 p = jugador.position;
        grandes.transform.position = p + Vector3.up * 2.2f - dir * 6f;
        ras.transform.position = p + Vector3.up * 0.25f - dir * 10f;
        velo.transform.position = p + Vector3.up * 1.6f - dir * 14f;
        ras.transform.rotation = velo.transform.rotation = grandes.transform.rotation = Quaternion.LookRotation(dir);

        Viento(grandes, dir * 5f * rafaga, -0.8f, 0.6f);
        Viento(ras, dir * 13f * rafaga, -0.05f, 0.25f);
        Viento(velo, dir * 11f * rafaga, -0.3f, 0.35f);

        var e1 = grandes.emission; e1.rateOverTime = 70f * k;
        var e2 = ras.emission; e2.rateOverTime = 260f * k * rafaga;
        var e3 = velo.emission; e3.rateOverTime = 14f * k * rafaga;
    }

    static readonly int idNiebla = Shader.PropertyToID("_Niebla"), idColorNiebla = Shader.PropertyToID("_ColorNiebla");
    float nieblaCielo = -1f;

    /// <summary>El skybox no recibe la niebla: lo tapamos a mano con el color de la niebla de la tormenta
    /// (antes, con todo gris, el cielo negro arriba del establo se veía como una mancha).</summary>
    void Cielo()
    {
        var m = RenderSettings.skybox;
        if (m == null || !m.HasProperty(idNiebla)) return;
        float n = Ventisca.Intensidad * Mathf.Lerp(0.55f, 0.97f, afuera);
        if (Mathf.Abs(n - nieblaCielo) < 0.002f) return;
        nieblaCielo = n;
        m.SetFloat(idNiebla, n);
        m.SetColor(idColorNiebla, RenderSettings.fogColor);
    }

    static void Viento(ParticleSystem ps, Vector3 v, float abajo, float variacion)
    {
        var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
        vel.x = new ParticleSystem.MinMaxCurve(v.x * (1f - variacion), v.x * (1f + variacion));
        vel.y = new ParticleSystem.MinMaxCurve(abajo * 1.5f, abajo * 0.2f + 0.15f);
        vel.z = new ParticleSystem.MinMaxCurve(v.z * (1f - variacion), v.z * (1f + variacion));
    }

    void Crear()
    {
        Material mat = BolaNieve.matParticulas;
        // 1) copos grandes esponjados (billboard, bamboleo con ruido)
        grandes = Sistema("Ventisca_CoposGrandes", mat, 2.6f, 260, new Vector2(0.12f, 0.26f), new Color(1f, 1f, 1f, 0.95f), new Vector3(16f, 5f, 4f), 0f);
        var ruido = grandes.noise; ruido.enabled = true; ruido.strength = 0.9f; ruido.frequency = 0.6f; ruido.scrollSpeed = 0.4f;
        var rot = grandes.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-2f, 2f);
        // 2) al ras del suelo: estiradas por la velocidad, muy transparentes
        ras = Sistema("Ventisca_RasDelSuelo", mat, 1.6f, 700, new Vector2(0.18f, 0.4f), new Color(0.93f, 0.97f, 1f, 0.35f), new Vector3(22f, 0.5f, 3f), 0f);
        var r2 = ras.GetComponent<ParticleSystemRenderer>();
        r2.renderMode = ParticleSystemRenderMode.Stretch; r2.velocityScale = 0.12f; r2.lengthScale = 2.5f;
        var ruido2 = ras.noise; ruido2.enabled = true; ruido2.strength = 0.35f; ruido2.frequency = 1.2f; ruido2.scrollSpeed = 1f;
        // 3) velo: manchas grandes casi invisibles (cuando pasan, "se borra" un poquito el paisaje)
        velo = Sistema("Ventisca_Velo", mat, 2.8f, 60, new Vector2(3.5f, 7f), new Color(0.85f, 0.9f, 0.98f, 0.10f), new Vector3(24f, 3f, 4f), 0f);
        var rot3 = velo.rotationOverLifetime; rot3.enabled = true; rot3.z = new ParticleSystem.MinMaxCurve(-0.5f, 0.5f);
    }

    static ParticleSystem Sistema(string nombre, Material mat, float vida, int max, Vector2 tam, Color color, Vector3 caja, float gravedad)
    {
        var go = new GameObject(nombre);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var m = ps.main; m.loop = true; m.startLifetime = new ParticleSystem.MinMaxCurve(vida * 0.7f, vida); m.startSpeed = 0f; m.maxParticles = max;
        m.startSize = new ParticleSystem.MinMaxCurve(tam.x, tam.y); m.startColor = color; m.gravityModifier = gravedad;
        m.simulationSpace = ParticleSystemSimulationSpace.World;
        m.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = caja;
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                  new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.2f), new GradientAlphaKey(1f, 0.75f), new GradientAlphaKey(0f, 1f) });
        col.color = g;
        var em = ps.emission; em.rateOverTime = 0f;
        var r = go.GetComponent<ParticleSystemRenderer>();
        if (mat != null) r.sharedMaterial = mat;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
        r.sortingFudge = -2f;
        ps.Play();
        return ps;
    }

    void OnDestroy()
    {
        if (RenderSettings.skybox != null && RenderSettings.skybox.HasProperty(idNiebla)) RenderSettings.skybox.SetFloat(idNiebla, 0f);
        if (grandes != null) Destroy(grandes.gameObject);
        if (ras != null) Destroy(ras.gameObject);
        if (velo != null) Destroy(velo.gameObject);
    }
}
