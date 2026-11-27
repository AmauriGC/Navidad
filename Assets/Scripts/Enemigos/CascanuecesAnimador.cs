using UnityEngine;
using UnityEngine.AI;

/// <summary>
/// Animación PROCEDURAL del cascanueces (sin Animator, puro código con senos):
///  - Dormido/Congelado: rígido como juguete.
///  - Caminando: paso de soldadito (piernas rectas, brazos contrarios, rebote).
///  - Sospecha: gira la cabeza de lado a lado.
///  - Persecución: la mandíbula "muerde" (clac-clac-clac) y se inclina hacia adelante.
///  - Aturdido: la cabeza da vueltas tambaleándose.
///  - Los OJOS brillan en rojo según qué tan alerta está (emisión del material).
/// </summary>
public class CascanuecesAnimador : MonoBehaviour
{
    public Cascanueces ia;
    public float amplitudPaso = 32f;
    public Color colorOjos = new Color(1f, 0.08f, 0.05f);
    public float brilloOjos = 6f;

    Transform piernaL, piernaR, brazoL, brazoR, cuerpo, cabeza, mandibula;
    Vector3 cuerpoPos0;
    NavMeshAgent agente;
    Material matOjos; int propEmision;
    float fase, despertarT = -1f;
    bool estabaDespierto;

    void Awake()
    {
        if (ia == null) ia = GetComponentInParent<Cascanueces>();
        agente = GetComponentInParent<NavMeshAgent>();
        piernaL = Buscar("Cas_PiernaL"); piernaR = Buscar("Cas_PiernaR");
        brazoL = Buscar("Cas_BrazoL"); brazoR = Buscar("Cas_BrazoR");
        cuerpo = Buscar("Cas_Cuerpo"); cabeza = Buscar("Cas_Cabeza"); mandibula = Buscar("Cas_Mandibula");
        if (cuerpo) cuerpoPos0 = cuerpo.localPosition;

        // Buscamos el material de los ojos en la cabeza (glTFast guarda la emisión en "emissiveFactor")
        if (cabeza != null)
        {
            var r = cabeza.GetComponent<Renderer>();
            if (r != null)
            {
                var mats = r.materials;   // copia propia: cada cascanueces brilla por separado
                foreach (var m in mats) if (m.name.StartsWith("Cas_Ojos")) matOjos = m;
                propEmision = Shader.PropertyToID(matOjos != null && matOjos.HasProperty("emissiveFactor") ? "emissiveFactor" : "_EmissionColor");
            }
        }
    }

    Transform Buscar(string n)
    {
        foreach (var t in GetComponentsInChildren<Transform>(true)) if (t.name == n) return t;
        return null;
    }

    static Quaternion X(float g) { return Quaternion.Euler(g, 0f, 0f); }

    void Update()
    {
        if (ia == null) return;
        var e = ia.EstadoActual;
        float vel = agente != null ? agente.velocity.magnitude : 0f;
        float t = Time.time;

        // al despertar: sacudida de 1 segundo
        if (ia.Despierto && !estabaDespierto) despertarT = t;
        estabaDespierto = ia.Despierto;
        float sacudida = (despertarT > 0 && t - despertarT < 1f) ? Mathf.Sin((t - despertarT) * 60f) * 8f * (1f - (t - despertarT)) : 0f;

        bool quieto = e == Cascanueces.Estado.Dormido || e == Cascanueces.Estado.Congelado || Juego.EnemigosEnPausa;
        if (quieto)
        {
            Suavizar(piernaL, Quaternion.identity); Suavizar(piernaR, Quaternion.identity);
            Suavizar(brazoL, Quaternion.identity); Suavizar(brazoR, Quaternion.identity);
            Suavizar(cabeza, Quaternion.identity); Suavizar(mandibula, Quaternion.identity);
            if (cuerpo) cuerpo.localRotation = Quaternion.Euler(0f, 0f, sacudida);
            Ojos(e == Cascanueces.Estado.Congelado || e == Cascanueces.Estado.Dormido ? 0f : Mathf.Max(0.6f, ia.Alerta));   // despierto: ojos encendidos
            return;
        }

        // ---- caminar (paso de soldadito)
        fase += Time.deltaTime * (2f + vel * 2.2f);
        float k = Mathf.Clamp01(vel / 1.5f);
        float s = Mathf.Sin(fase);
        if (piernaL) piernaL.localRotation = X(s * amplitudPaso * k);
        if (piernaR) piernaR.localRotation = X(-s * amplitudPaso * k);
        if (brazoL) brazoL.localRotation = X(-s * amplitudPaso * 1.2f * k);
        if (brazoR) brazoR.localRotation = X(e == Cascanueces.Estado.Persecucion ? -80f + s * 10f : s * amplitudPaso * 1.2f * k);  // sable al frente
        float inclinacion = e == Cascanueces.Estado.Persecucion ? 12f : 0f;
        if (cuerpo)
        {
            cuerpo.localPosition = cuerpoPos0 + Vector3.up * Mathf.Abs(Mathf.Cos(fase)) * 0.05f * k;
            cuerpo.localRotation = Quaternion.Euler(inclinacion, 0f, sacudida);
        }

        // ---- cabeza y mandíbula según el estado
        Quaternion rotCabeza = Quaternion.identity;
        float abrir = 0f;
        switch (e)
        {
            case Cascanueces.Estado.Sospecha: rotCabeza = Quaternion.Euler(0f, Mathf.Sin(t * 5f) * 35f, 0f); abrir = 8f; break;
            case Cascanueces.Estado.Persecucion: abrir = (Mathf.Sin(t * 18f) * 0.5f + 0.5f) * 28f; break;   // clac clac
            case Cascanueces.Estado.Aturdido: rotCabeza = Quaternion.Euler(Mathf.Sin(t * 7f) * 12f, t * 400f % 360f, Mathf.Cos(t * 7f) * 12f); abrir = 20f; break;
        }
        if (cabeza) cabeza.localRotation = Quaternion.Slerp(cabeza.localRotation, rotCabeza, 12f * Time.deltaTime);
        if (mandibula) mandibula.localRotation = X(abrir);
        Ojos(e == Cascanueces.Estado.Aturdido ? 0.1f : 0.25f + ia.Alerta * 0.75f);
    }

    void Suavizar(Transform tr, Quaternion q) { if (tr) tr.localRotation = Quaternion.Slerp(tr.localRotation, q, 8f * Time.deltaTime); }

    void Ojos(float k)
    {
        if (matOjos == null) return;
        matOjos.SetColor(propEmision, colorOjos * brilloOjos * k);
    }
}
