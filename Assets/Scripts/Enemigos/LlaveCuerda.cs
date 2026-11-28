using UnityEngine;

/// <summary>
/// LLAVE DE CUERDA (historia 1.5): gira la llave de latón de la espalda del cascanueces (hijo "Cas_Llave").
/// Qué tan rápido gira cuenta cómo está el juguete:
///   dormido = quieta · patrullando = despacio · persiguiendo = rápido · con cuerda extra de una descarga = ¡rapidísimo!
///   Siete curada (Calmado) = la mitad · árbol completo (congelado) = se va frenando hasta pararse.
/// Si no hay componente Cascanueces (los nevados), gira despacio siempre.
/// En Blender la llave sale hacia +Y (la espalda); en Unity ese eje es el -Z local, por eso gira sobre Vector3.forward.
/// </summary>
public class LlaveCuerda : MonoBehaviour
{
    public float velocidadPatrulla = 120f, velocidadPersecucion = 320f, velocidadCuerdaExtra = 1100f;

    Transform llave; Cascanueces cas; float velocidad;

    void Start()
    {
        cas = GetComponent<Cascanueces>();
        foreach (var t in GetComponentsInChildren<Transform>(true)) if (t.name == "Cas_Llave") { llave = t; break; }
        if (llave == null) enabled = false;
    }

    void Update()
    {
        float objetivo = velocidadPatrulla * 0.6f;
        if (cas != null)
        {
            switch (cas.EstadoActual)
            {
                case Cascanueces.Estado.Dormido: case Cascanueces.Estado.Congelado: objetivo = 0f; break;
                case Cascanueces.Estado.Persecucion: objetivo = velocidadPersecucion; break;
                case Cascanueces.Estado.Aturdido: objetivo = velocidadPatrulla * 0.3f; break;
                default: objetivo = velocidadPatrulla; break;
            }
            if (cas.ConCuerdaExtra) objetivo = velocidadCuerdaExtra;
            else if (cas.Calmado) objetivo *= 0.5f;
        }
        if (ArbolNavidad.Instancia != null && ArbolNavidad.Instancia.Completo) objetivo = 0f;
        // acelera rápido y frena despacio (como un juguete que se queda sin cuerda)
        velocidad = Mathf.MoveTowards(velocidad, objetivo, Time.deltaTime * (objetivo > velocidad ? 2000f : 260f));
        llave.Rotate(Vector3.forward, velocidad * Time.deltaTime, Space.Self);
    }
}
