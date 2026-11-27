using UnityEngine;

/// <summary>
/// Bola de nieve que lanza un CASCANUECES NEVADO. No usa Rigidbody: se mueve sola con su velocidad y la gravedad,
/// y cada cuadro revisa con un SphereCast (esfera de 0.18 m) si chocó con algo entre la posición anterior y la nueva.
///  - Si choca con el jugador => FrioJugador.Golpe() (frío, y a la tercera en 5 s te congela).
///  - Con cualquier otra cosa => "puf" de nieve y desaparece.
/// </summary>
public class BolaEnemiga : MonoBehaviour
{
    Vector3 vel; Transform lanzador; float vida;

    public void Lanzar(Vector3 velocidad, Transform quien) { vel = velocidad; lanzador = quien; }

    void Update()
    {
        if (Juego.Estado != Juego.Modo.Jugando) { if (Juego.Estado != Juego.Modo.Pausa) Destroy(gameObject); return; }
        vida += Time.deltaTime;
        if (vida > 5f) { Destroy(gameObject); return; }
        Vector3 antes = transform.position;
        vel += Physics.gravity * Time.deltaTime;
        Vector3 despues = antes + vel * Time.deltaTime;
        Vector3 d = despues - antes;
        RaycastHit hit;
        if (Physics.SphereCast(antes, 0.18f, d.normalized, out hit, d.magnitude, ~(1 << 9), QueryTriggerInteraction.Ignore)
            && (lanzador == null || !hit.collider.transform.IsChildOf(lanzador)))
        {
            Chocar(hit);
            return;
        }
        transform.position = despues;
        transform.Rotate(400f * Time.deltaTime, 0f, 0f, Space.Self);
    }

    void Chocar(RaycastHit hit)
    {
        if (hit.collider.CompareTag("Player") || hit.collider.GetComponentInParent<ElfoController>() != null)
            FrioJugador.Del(hit.collider.GetComponentInParent<ElfoController>().gameObject).Golpe();
        else GestorAudio.Efecto3D("impacto_nieve", hit.point, 0.7f);
        BolaNieve.Puf(hit.point, 25, new Color(0.95f, 0.97f, 1f), 1f);
        Destroy(gameObject);
    }
}
