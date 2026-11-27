using UnityEngine;

/// <summary>
/// La nieve que cae va pegada al jugador (así nieva en todo el mapa sin llenar el mundo de partículas).
/// Cada medio segundo revisa con un rayo si hay techo encima del jugador: si lo hay (taller, establo), deja de emitir;
/// los copos que ya iban cayendo terminan solos (la simulación está en espacio del mundo).
/// </summary>
[RequireComponent(typeof(ParticleSystem))]
public class NieveSigueJugador : MonoBehaviour
{
    public float alturaRevision = 30f;
    ParticleSystem ps; float siguiente;

    void Awake() { ps = GetComponent<ParticleSystem>(); }

    void Update()
    {
        if (Time.time < siguiente) return;
        siguiente = Time.time + 0.5f;
        Vector3 origen = transform.parent != null ? transform.parent.position + Vector3.up * 1.6f : transform.position;
        // El rayo va de ARRIBA hacia ABAJO: los MeshCollider de los techos solo se detectan por su cara de afuera.
        // Todas las capas (los techos tienen collider "ColCamara" en la capa SoloCamara); si choca con algo
        // antes de llegar a la cabeza del elfo => hay techo encima.
        Vector3 arriba = origen + Vector3.up * alturaRevision;
        RaycastHit hit;
        bool bajoTecho = Physics.Raycast(arriba, Vector3.down, out hit, alturaRevision - 0.2f, ~0, QueryTriggerInteraction.Ignore)
                         && !hit.collider.transform.IsChildOf(transform.root);
        var em = ps.emission;
        em.enabled = !bajoTecho;
    }
}
