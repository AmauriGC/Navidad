using UnityEngine;

/// <summary>
/// Todo lo que pasa cuando el elfo camina:
///  - PASOS: un sonido cada cierta distancia recorrida (madera adentro, nieve afuera).
///  - HUELLAS: en la nieve deja huellas (partículas planas pegadas al piso, pie izquierdo y derecho)
///    que se desvanecen solas después de un rato.
///  - VAHO: afuera, cada par de segundos sale una nubecita blanca de la boca (hace frío).
/// Para saber si pisa nieve lanza un rayo hacia abajo y lee el nombre del objeto que toca.
/// Las partículas se crean por código (no necesitan prefab).
/// </summary>
[RequireComponent(typeof(ElfoController))]
public class PasosElfo : MonoBehaviour
{
    public Material materialParticulas;     // material transparente de partículas (Particulas_Alfa)
    public float largoPaso = 0.7f, largoPasoCorriendo = 0.95f;
    public float duracionHuella = 18f;
    public float cadaCuantoVaho = 2.6f;

    ElfoController elfo; CharacterController cc; Transform cabeza;
    ParticleSystem huellas, vaho;
    float distancia, siguienteVaho; bool pieIzquierdo; bool enNieve;

    void Awake()
    {
        elfo = GetComponent<ElfoController>(); cc = GetComponent<CharacterController>();
        foreach (var t in GetComponentsInChildren<Transform>()) if (t.name == "Cabeza") cabeza = t;
        huellas = CrearHuellas(); vaho = CrearVaho();
    }

    void Update()
    {
        if (!elfo.EnSuelo || Juego.Bloqueado) { distancia = 0f; return; }
        Vector3 v = cc.velocity; v.y = 0f;
        if (Time.time > siguienteVaho) { siguienteVaho = Time.time + cadaCuantoVaho * Random.Range(0.8f, 1.2f); if (enNieve) Vaho(); }
        if (v.magnitude < 0.5f) return;
        distancia += v.magnitude * Time.deltaTime;
        if (distancia < (elfo.Corriendo ? largoPasoCorriendo : largoPaso)) return;
        distancia = 0f;
        Paso();
    }

    void Paso()
    {
        RaycastHit hit;
        bool toca = Physics.Raycast(transform.position + Vector3.up * 0.3f, Vector3.down, out hit, 1.5f, ~(1 << 9), QueryTriggerInteraction.Ignore);
        enNieve = toca && EsNieve(hit.collider);
        GestorAudio.Efecto((enNieve ? "paso_nieve" : "paso_madera") + Random.Range(1, 4), elfo.Corriendo ? 0.55f : 0.4f, 0.1f);
        if (enNieve) Huella(hit.point, hit.normal);
        pieIzquierdo = !pieIzquierdo;
    }

    static bool EsNieve(Collider c)
    {
        string n = c.name.ToLower();
        return n.Contains("nieve") || n.Contains("suelo");
    }

    // ------------------------------------------------------------------ huellas
    void Huella(Vector3 punto, Vector3 normal)
    {
        // un pie a cada lado del centro del elfo
        Vector3 lado = transform.right * (pieIzquierdo ? -0.11f : 0.11f);
        var p = new ParticleSystem.EmitParams();
        p.position = punto + lado + normal * 0.03f;
        // el quad viene parado; 90° en X lo acuesta en el piso y el giro en Y lo apunta hacia donde camina
        p.rotation3D = new Vector3(90f, transform.eulerAngles.y, 0f);
        p.startSize3D = new Vector3(0.15f, 0.27f, 1f);
        p.applyShapeToPosition = false;
        huellas.Emit(p, 1);
    }

    ParticleSystem CrearHuellas()
    {
        var go = new GameObject("Huellas");      // fuera del jugador: las huellas se quedan en el mundo
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.startLifetime = duracionHuella; main.startSpeed = 0f; main.maxParticles = 400;
        main.startSize3D = true; main.startRotation3D = true; main.playOnAwake = false;
        main.startColor = new Color(0.22f, 0.27f, 0.42f, 0.8f);   // gris azulado: sombra de la nieve hundida
        var em = ps.emission; em.enabled = false;
        var sh = ps.shape; sh.enabled = false;
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                  new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 0.7f), new GradientAlphaKey(0f, 1f) });
        col.color = g;
        var r = go.GetComponent<ParticleSystemRenderer>();
        r.renderMode = ParticleSystemRenderMode.Mesh;          // un quad acostado en el piso
        r.mesh = Resources.GetBuiltinResource<Mesh>("Quad.fbx");
        r.alignment = ParticleSystemRenderSpace.World;
        r.material = materialParticulas;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
        ps.Play();
        return ps;
    }

    // ------------------------------------------------------------------ vaho
    void Vaho()
    {
        if (vaho == null) return;
        Transform t = cabeza != null ? cabeza : transform;
        vaho.transform.position = t.position + transform.forward * 0.22f + Vector3.up * (cabeza != null ? 0.12f : 1.0f);
        vaho.transform.rotation = Quaternion.LookRotation(transform.forward + Vector3.up * 0.3f);
        vaho.Emit(Random.Range(5, 8));
    }

    ParticleSystem CrearVaho()
    {
        var go = new GameObject("Vaho");
        go.transform.SetParent(transform, false);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.startLifetime = new ParticleSystem.MinMaxCurve(0.9f, 1.4f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(0.25f, 0.5f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.09f);
        main.startColor = new Color(0.9f, 0.95f, 1f, 0.35f);
        main.gravityModifier = -0.03f; main.playOnAwake = false; main.maxParticles = 60;
        var em = ps.emission; em.enabled = false;
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 18f; sh.radius = 0.02f;
        var tam = ps.sizeOverLifetime; tam.enabled = true; tam.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 4f));
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                  new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.15f), new GradientAlphaKey(0f, 1f) });
        col.color = g;
        var r = go.GetComponent<ParticleSystemRenderer>();
        r.material = materialParticulas;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
        ps.Play();
        return ps;
    }

    void OnDestroy() { if (huellas != null) Destroy(huellas.gameObject); }
}
