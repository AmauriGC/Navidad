using System.Collections;
using UnityEngine;

/// <summary>
/// CASCANUECES NEVADO (solo Difícil e Imposible): un cascanueces de abrigo blanco que se queda PARADO afuera, en la nieve,
/// junto a su cubeta, y te lanza bolas de nieve cuando te ve.
///  - Te ve si estás a menos de 'alcance' y nada se atraviesa (Linecast de sus ojos a tu pecho).
///  - Gira hacia ti y cada 'cadencia' segundos lanza una bola en ARCO (tiro parabólico) con un poco de adelanto:
///    apunta a donde vas a estar, pero solo a la mitad => si te mueves de lado la puedes esquivar.
///  - Si le pegas con tu bola de nieve queda aturdido 'duracionAturdido' segundos (no lanza).
///  - Las bolas (BolaEnemiga) dan FRÍO al jugador (ver FrioJugador).
/// Dificultad.Aplicar() prende solo los que tocan: 'desdeNivel' 2 = desde Difícil, 3 = solo en Imposible.
/// </summary>
public class CascanuecesNevado : MonoBehaviour
{
    [Tooltip("2 = aparece desde Difícil; 3 = solo en Imposible.")]
    public int desdeNivel = 2;
    public float alcance = 16f;
    public float cadencia = 2.4f;
    public float velocidadBola = 12f;
    public float duracionAturdido = 4f;
    public Transform modelo, brazoLanzar;
    public GameObject modeloBola, modeloBloqueHielo;
    public ParticleSystem estrellas;

    Transform jugador; ElfoController elfo;
    float siguienteTiro, aturdidoHasta;
    Quaternion rotBrazo0; Vector3 posModelo0;
    bool lanzando;
    Vector3 velJugador, posJugadorAntes;

    public bool Aturdido => Time.time < aturdidoHasta;

    void Start()
    {
        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { jugador = j.transform; elfo = j.GetComponent<ElfoController>(); posJugadorAntes = jugador.position; }
        if (brazoLanzar != null) rotBrazo0 = brazoLanzar.localRotation;
        if (modelo != null) posModelo0 = modelo.localPosition;
        if (modeloBloqueHielo != null) FrioJugador.modeloBloque = modeloBloqueHielo;
        siguienteTiro = Time.time + Random.Range(1f, 2.5f);
    }

    public void Aturdir()
    {
        aturdidoHasta = Time.time + duracionAturdido;
        GestorAudio.Efecto3D("aturdido", transform.position + Vector3.up * 1.5f);
        if (estrellas != null) estrellas.Play();
    }

    void Update()
    {
        if (jugador == null) return;
        // velocidad del jugador (para el adelanto del tiro)
        if (Time.deltaTime > 0f) velJugador = Vector3.Lerp(velJugador, (jugador.position - posJugadorAntes) / Time.deltaTime, Time.deltaTime * 5f);
        posJugadorAntes = jugador.position;

        float t = Time.time;
        // aturdido: se tambalea
        if (modelo != null)
        {
            float tambaleo = Aturdido ? Mathf.Sin(t * 9f) * 10f : 0f;
            modelo.localPosition = posModelo0 + Vector3.up * Mathf.Sin(t * 2.2f) * 0.015f;
            modelo.localRotation = Quaternion.Euler(0f, 0f, tambaleo);
        }
        if (estrellas != null && !Aturdido && estrellas.isPlaying) estrellas.Stop();
        if (Juego.Estado != Juego.Modo.Jugando || Aturdido) return;

        Vector3 ojos = transform.position + Vector3.up * 1.9f;
        Vector3 pecho = jugador.position + Vector3.up * 0.8f;
        Vector3 hacia = pecho - ojos;
        if (hacia.magnitude > alcance) return;
        // ¿hay algo en medio? (ignora la capa SoloCamara y a sí mismo)
        RaycastHit hit;
        if (Physics.Linecast(ojos, pecho, out hit, ~(1 << 9), QueryTriggerInteraction.Ignore) && !hit.collider.transform.IsChildOf(jugador) && !hit.collider.transform.IsChildOf(transform))
            return;

        // girar hacia el jugador
        Vector3 plano = hacia; plano.y = 0f;
        if (plano.sqrMagnitude > 0.01f)
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(plano), Time.deltaTime * 5f);

        if (t >= siguienteTiro && !lanzando && Vector3.Angle(transform.forward, plano) < 25f)
        {
            siguienteTiro = t + cadencia * Random.Range(0.85f, 1.15f);
            StartCoroutine(Lanzar());
        }
    }

    IEnumerator Lanzar()
    {
        lanzando = true;
        // 1) brazo hacia atrás (se prepara)  2) tira hacia adelante y suelta la bola
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.35f) { Brazo(140f * Mathf.SmoothStep(0, 1, k)); yield return null; }
        Brazo(140f);
        Soltar();
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.18f) { Brazo(Mathf.Lerp(140f, -40f, k)); yield return null; }
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.4f) { Brazo(Mathf.Lerp(-40f, 0f, k)); yield return null; }
        Brazo(0f);
        lanzando = false;
    }

    void Brazo(float grados) { if (brazoLanzar != null) brazoLanzar.localRotation = rotBrazo0 * Quaternion.Euler(grados, 0f, 0f); }

    void Soltar()
    {
        if (jugador == null) return;
        Vector3 salida = transform.position + Vector3.up * 2.2f + transform.forward * 0.4f + transform.right * 0.35f;
        Vector3 destino = jugador.position + Vector3.up * 0.7f;
        float dist = Vector3.Distance(new Vector3(salida.x, 0, salida.z), new Vector3(destino.x, 0, destino.z));
        float tiempo = Mathf.Max(0.35f, dist / velocidadBola);
        Vector3 v = velJugador; v.y = 0f;
        destino += v * tiempo * 0.5f;                       // adelanto a medias: esquivable
        Vector3 g = Physics.gravity;
        Vector3 vel = (destino - salida - 0.5f * g * tiempo * tiempo) / tiempo;   // tiro parabólico exacto
        var go = new GameObject("BolaEnemiga");
        go.transform.position = salida;
        if (modeloBola != null)
        {
            var m = Instantiate(modeloBola, go.transform); m.transform.localPosition = Vector3.zero; m.transform.localScale = Vector3.one * 1.1f;
            foreach (var c in m.GetComponentsInChildren<Collider>()) Destroy(c);
        }
        go.AddComponent<BolaEnemiga>().Lanzar(vel, transform);
        GestorAudio.Efecto3D("lanzar", salida, 0.8f);
    }
}
