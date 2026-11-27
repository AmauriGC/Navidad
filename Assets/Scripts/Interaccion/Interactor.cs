using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Va en el Jugador. Cada frame busca el Interactuable más cercano frente al elfo
/// (con Physics.OverlapSphere), muestra el aviso "[E] ..." y al presionar E lo usa.
/// Q suelta lo que tenga en las manos.
/// </summary>
public class Interactor : MonoBehaviour
{
    public float radio = 1.3f;
    [Tooltip("Qué tan adelante del elfo se busca.")]
    public float distanciaFrente = 0.8f;
    public float altura = 0.7f;

    public Inventario Inventario { get; private set; }
    public Interactuable Actual { get; private set; }

    readonly Collider[] resultados = new Collider[16];

    void Awake() { Inventario = GetComponent<Inventario>(); }

    void Update()
    {
        if (Juego.Bloqueado) { Actual = null; UIAviso.Mostrar(null); return; }
        Actual = BuscarMasCercano();
        UIAviso.Mostrar(Actual != null ? "[E] " + Actual.Texto(this) : null);

        var kb = Keyboard.current;
        bool usar = (kb != null && kb.eKey.wasPressedThisFrame) || Tactil.Usar;        // E o botón táctil
        bool soltar = (kb != null && kb.qKey.wasPressedThisFrame) || Tactil.Soltar;    // Q o botón táctil
        if (usar && Actual != null) Actual.Interactuar(this);
        else if (soltar && Inventario != null && Inventario.TieneObjeto) Inventario.Soltar();
    }

    Interactuable BuscarMasCercano()
    {
        Vector3 centro = transform.position + Vector3.up * altura + transform.forward * distanciaFrente;
        int n = Physics.OverlapSphereNonAlloc(centro, radio, resultados, ~0, QueryTriggerInteraction.Collide);
        Interactuable mejor = null; float mejorDist = float.MaxValue;
        for (int i = 0; i < n; i++)
        {
            var it = resultados[i].GetComponentInParent<Interactuable>();
            if (it == null || !it.PuedeInteractuar(this)) continue;
            if (Inventario != null && Inventario.EnMano != null && it.gameObject == Inventario.EnMano.gameObject) continue;
            if (!SeVe(resultados[i], it)) continue;   // hay una pared en medio
            float d = (resultados[i].ClosestPoint(centro) - centro).sqrMagnitude;
            if (d < mejorDist) { mejorDist = d; mejor = it; }
        }
        return mejor;
    }

    /// <summary>
    /// Línea de visión: traza una línea desde arriba de la cabeza del elfo hasta el objeto.
    /// Si choca con algo sólido que NO es el propio objeto (una pared), no cuenta.
    /// Los triggers se ignoran (QueryTriggerInteraction.Ignore).
    /// </summary>
    bool SeVe(Collider col, Interactuable it)
    {
        Vector3 ojo = transform.position + Vector3.up * 1.5f;   // arriba del gorro: así ve lo que hay sobre las mesas
        Vector3 punto = col.bounds.center;
        RaycastHit hit;
        // ~(1 << 9): todas las capas MENOS "SoloCamara" (colliders invisibles que solo usa la cámara)
        if (!Physics.Linecast(ojo, punto, out hit, ~(1 << 9), QueryTriggerInteraction.Ignore)) return true;
        if (hit.collider.transform.IsChildOf(transform)) return true;            // el propio elfo
        if ((hit.point - punto).sqrMagnitude < 0.36f) return true;                // choca justo junto al objeto (ej. la nariz del muñeco)
        return hit.collider.GetComponentInParent<Interactuable>() == it;           // chocó con el objeto mismo
    }

    void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position + Vector3.up * altura + transform.forward * distanciaFrente, radio);
    }
}
