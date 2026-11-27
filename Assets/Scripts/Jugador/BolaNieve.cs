using UnityEngine;

/// <summary>
/// La bola de nieve lanzada. Al chocar con algo:
///  - si es un cascanueces → lo aturde.
///  - siempre → se deshace en un "puf" de nieve (partículas) y desaparece.
/// </summary>
public class BolaNieve : MonoBehaviour
{
    bool usada;

    void Start() { Destroy(gameObject, 6f); }   // por si cae al vacío

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
        GestorAudio.Efecto3D("impacto_nieve", transform.position);
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

    /// <summary>Lo asigna el LanzadorNieve (material de partículas del proyecto).</summary>
    public static Material matParticulas;
    static Material MaterialParticulas() { return matParticulas; }
}
