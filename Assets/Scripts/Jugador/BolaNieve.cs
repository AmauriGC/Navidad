using UnityEngine;

/// <summary>
/// La bola de nieve lanzada. Al chocar con algo:
///  - si es un cascanueces → lo aturde.
///  - siempre → se deshace en un "puf" de nieve (partículas) y desaparece.
/// </summary>
public class BolaNieve : MonoBehaviour
{
    bool usada;

    void Start()
    {
        Destroy(gameObject, 6f);   // por si cae al vacío
        Estela();
    }

    // ------------------------------------------------------------------ detallitos v1.5: estela al volar
    /// <summary>Una cola blanca que se desvanece (TrailRenderer) + polvito de nieve que se va cayendo atrás.</summary>
    void Estela()
    {
        if (matParticulas == null) return;   // sin material saldría rosa
        var tr = gameObject.AddComponent<TrailRenderer>();
        tr.time = 0.22f; tr.minVertexDistance = 0.05f;
        tr.widthCurve = new AnimationCurve(new Keyframe(0f, 0.16f), new Keyframe(1f, 0f));
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(new Color(0.8f, 0.9f, 1f), 1f) },
                  new[] { new GradientAlphaKey(0.75f, 0f), new GradientAlphaKey(0f, 1f) });
        tr.colorGradient = g;
        tr.sharedMaterial = matParticulas;
        tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; tr.receiveShadows = false;
        tr.numCapVertices = 2;

        var go = new GameObject("PolvitoNieve");
        go.transform.SetParent(transform, false);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var m = ps.main; m.loop = true; m.simulationSpace = ParticleSystemSimulationSpace.World;
        m.startLifetime = new ParticleSystem.MinMaxCurve(0.35f, 0.7f); m.startSpeed = new ParticleSystem.MinMaxCurve(0.05f, 0.3f);
        m.startSize = new ParticleSystem.MinMaxCurve(0.025f, 0.06f); m.startColor = new Color(0.95f, 0.98f, 1f, 0.9f);
        m.gravityModifier = 0.35f; m.maxParticles = 120; m.scalingMode = ParticleSystemScalingMode.Hierarchy;
        var em = ps.emission; em.rateOverTime = 0f; em.rateOverDistance = 14f;
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.4f;
        var col = ps.colorOverLifetime; col.enabled = true;
        var gr = new Gradient();
        gr.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                   new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(0f, 1f) });
        col.color = gr;
        var r = go.GetComponent<ParticleSystemRenderer>();
        r.sharedMaterial = matParticulas; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        ps.Play();
        polvito = ps;
    }
    ParticleSystem polvito;

    void OnCollisionEnter(Collision c)
    {
        if (usada) return;
        usada = true;
        var enemigo = c.collider.GetComponentInParent<Cascanueces>();
        if (enemigo != null && enemigo.Despierto)
        {
            enemigo.Aturdir();
            TemblorCamara.Sacudir(0.25f);
            UIAviso.Mensaje("¡Le diste! El cascanueces quedó aturdido.", 1.8f);
        }
        var nevado = c.collider.GetComponentInParent<CascanuecesNevado>();
        if (nevado != null)
        {
            nevado.Aturdir();
            TemblorCamara.Sacudir(0.25f);
            UIAviso.Mensaje("¡Le diste! El cascanueces nevado dejó de lanzar un rato.", 1.8f);
        }
        Puf(transform.position);
        Trocitos(transform.position, c.contactCount > 0 ? c.GetContact(0).normal : Vector3.up);
        GestorAudio.Efecto3D("impacto_nieve", transform.position);
        // el polvito que ya estaba en el aire se queda flotando y se apaga solo
        if (polvito != null)
        {
            polvito.transform.SetParent(null, true);
            polvito.Stop(false, ParticleSystemStopBehavior.StopEmitting);
            var mm = polvito.main; mm.stopAction = ParticleSystemStopAction.Destroy;
        }
        Destroy(gameObject);
    }

    /// <summary>Crea un estallido de partículas blancas por código (no necesita prefab).</summary>
    static void Puf(Vector3 pos) { Puf(pos, 25, new Color(0.95f, 0.97f, 1f), 1f); }

    /// <summary>Estallido de partículas (también lo usan las bolas enemigas y el hielo al romperse).</summary>
    public static void Puf(Vector3 pos, int cantidad, Color color, float fuerza)
    {
        var go = new GameObject("PufNieve");
        go.transform.position = pos;
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.duration = 0.3f; main.loop = false;
        main.startLifetime = new ParticleSystem.MinMaxCurve(0.4f, 0.8f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(1f * fuerza, 3f * fuerza);
        main.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.14f);
        main.startColor = color;
        main.gravityModifier = 1f;
        main.stopAction = ParticleSystemStopAction.Destroy;
        var em = ps.emission; em.rateOverTime = 0f;
        em.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)cantidad) });
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.1f;
        var r = go.GetComponent<ParticleSystemRenderer>();
        r.sharedMaterial = MaterialParticulas();
        ps.Play();
    }

    /// <summary>v1.5: la bola se rompe en TROCITOS low-poly (la misma malla de la bola, chiquita) que salen
    /// rebotados del lugar del golpe, caen, rebotan en el piso y se encogen hasta desaparecer.</summary>
    void Trocitos(Vector3 pos, Vector3 normal)
    {
        var mf = GetComponentInChildren<MeshFilter>(); var mr = GetComponentInChildren<MeshRenderer>();
        if (mf == null || mr == null || mf.sharedMesh == null) return;
        var go = new GameObject("TrocitosNieve");
        go.transform.position = pos + normal * 0.05f;
        go.transform.rotation = Quaternion.LookRotation(normal);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var m = ps.main; m.duration = 0.2f; m.loop = false;
        m.startLifetime = new ParticleSystem.MinMaxCurve(1.3f, 2.0f);
        m.startSpeed = new ParticleSystem.MinMaxCurve(1.5f, 3.8f);
        m.startSize = new ParticleSystem.MinMaxCurve(0.06f, 0.13f);
        m.startRotation3D = true;
        m.startRotationX = m.startRotationY = m.startRotationZ = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
        m.gravityModifier = 1.3f; m.stopAction = ParticleSystemStopAction.Destroy; m.maxParticles = 20;
        var em = ps.emission; em.rateOverTime = 0f; em.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)Random.Range(9, 14)) });
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 55f; sh.radius = 0.05f;
        var rot = ps.rotationOverLifetime; rot.enabled = true; rot.separateAxes = true;
        rot.x = rot.y = rot.z = new ParticleSystem.MinMaxCurve(-6f, 6f);
        var tam = ps.sizeOverLifetime; tam.enabled = true;
        tam.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(0.7f, 0.9f), new Keyframe(1f, 0f)));
        var col = ps.collision; col.enabled = true; col.type = ParticleSystemCollisionType.World; col.mode = ParticleSystemCollisionMode.Collision3D;
        col.bounce = 0.25f; col.dampen = 0.5f; col.lifetimeLoss = 0f; col.radiusScale = 0.5f; col.quality = ParticleSystemCollisionQuality.Medium;
        col.collidesWith = ~(1 << 9);
        var r = go.GetComponent<ParticleSystemRenderer>();
        r.renderMode = ParticleSystemRenderMode.Mesh; r.mesh = mf.sharedMesh;
        r.sharedMaterial = mr.sharedMaterial;
        r.alignment = ParticleSystemRenderSpace.World;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        ps.Play();
    }

    /// <summary>Lo asigna el LanzadorNieve (material de partículas del proyecto).</summary>
    public static Material matParticulas;
    static Material MaterialParticulas() { return matParticulas; }
}
