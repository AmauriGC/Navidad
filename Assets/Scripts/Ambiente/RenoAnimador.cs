using UnityEngine;

/// <summary>
/// Animación procedural del reno (idle): respira, mueve las orejas, menea la cola,
/// baja la cabeza a "comer" de vez en cuando y VOLTEA A VER al elfo si está cerca.
/// Las partes se buscan por nombre (terminan en _Cuerpo, _Cabeza, _OrejaL, _OrejaR, _Cola).
/// </summary>
public class RenoAnimador : MonoBehaviour
{
    public float distanciaMirar = 4f;
    Transform cuerpo, cabeza, orejaL, orejaR, cola, jugador;
    Quaternion cabeza0; Vector3 escCuerpo0;
    float semilla;

    void Start()
    {
        foreach (var t in GetComponentsInChildren<Transform>())
        {
            if (t.name.EndsWith("_Cuerpo")) cuerpo = t;
            else if (t.name.EndsWith("_Cabeza")) cabeza = t;
            else if (t.name.EndsWith("_OrejaL")) orejaL = t;
            else if (t.name.EndsWith("_OrejaR")) orejaR = t;
            else if (t.name.EndsWith("_Cola")) cola = t;
        }
        if (cabeza) cabeza0 = cabeza.localRotation;
        if (cuerpo) escCuerpo0 = cuerpo.localScale;
        var j = GameObject.FindGameObjectWithTag("Player"); if (j) jugador = j.transform;
        semilla = Random.value * 20f;
    }

    void Update()
    {
        float t = Time.time + semilla;
        if (cuerpo) cuerpo.localScale = new Vector3(escCuerpo0.x * (1f + Mathf.Sin(t * 1.6f) * 0.015f), escCuerpo0.y, escCuerpo0.z);
        if (cola) cola.localRotation = Quaternion.Euler(0f, Mathf.Sin(t * 9f) * 25f * Mathf.Clamp01(Mathf.Sin(t * 0.7f) * 3f), 0f);
        // las orejas se sacuden de vez en cuando (pulsos cortos)
        float pulso = Mathf.Pow(Mathf.Max(0f, Mathf.Sin(t * 0.9f)), 20f);
        if (orejaL) orejaL.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(t * 30f) * 20f * pulso);
        if (orejaR) orejaR.localRotation = Quaternion.Euler(0f, 0f, -Mathf.Sin(t * 30f + 1f) * 20f * pulso);

        if (cabeza == null) return;
        Quaternion objetivo;
        if (jugador != null && Vector3.Distance(jugador.position, transform.position) < distanciaMirar)
        {
            // voltear hacia el elfo (solo en horizontal, limitado a ±70°)
            Vector3 local = transform.InverseTransformPoint(jugador.position);
            float ang = Mathf.Clamp(Mathf.Atan2(local.x, local.z) * Mathf.Rad2Deg, -70f, 70f);
            objetivo = cabeza0 * Quaternion.Euler(-8f, ang, 0f);
        }
        else
        {
            // "comer": cada cierto tiempo baja la cabeza
            float comer = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(Mathf.Sin(t * 0.35f) * 2f - 1f));
            objetivo = cabeza0 * Quaternion.Euler(comer * 35f + Mathf.Sin(t * 0.8f) * 3f, Mathf.Sin(t * 0.3f) * 15f, 0f);
        }
        cabeza.localRotation = Quaternion.Slerp(cabeza.localRotation, objetivo, 3f * Time.deltaTime);
    }
}
