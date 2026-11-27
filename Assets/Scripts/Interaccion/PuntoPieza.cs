using UnityEngine;

/// <summary>
/// Marcador vacío: un lugar donde PUEDE aparecer una pieza del árbol.
/// El RepartidorPiezas elige al azar entre todos estos puntos al empezar cada partida.
/// Se pueden mover, copiar o borrar en el editor para cambiar dónde aparecen las piezas.
/// </summary>
public class PuntoPieza : MonoBehaviour
{
    [Tooltip("Nombre del lugar para las pistas, ej. \"el establo\", \"la casa roja\".")]
    public string zona = "el taller";
    [Tooltip("Está lejos del taller (afuera del patio). Se limita cuántas piezas caen en lugares lejanos.")]
    public bool lejos = false;

    void OnDrawGizmos()
    {
        Gizmos.color = lejos ? new Color(1f, 0.5f, 0.2f) : new Color(1f, 0.85f, 0.3f);
        Gizmos.DrawWireSphere(transform.position, 0.35f);
        Gizmos.DrawLine(transform.position, transform.position + Vector3.down * 0.5f);
    }
}
