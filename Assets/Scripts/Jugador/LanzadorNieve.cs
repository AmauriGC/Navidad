using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Va en el Jugador. F (o clic izquierdo) lanza una bola de nieve.
/// Las bolas se recargan en los montones / cubetas de nieve (MontonNieve).
/// La bola es un objeto con Rigidbody: la física de Unity se encarga de la parábola.
///
/// PUNTERÍA ASISTIDA: la cámara está detrás y arriba del elfo, así que "hacia donde mira la cámara"
/// no es exactamente a lo que el jugador le quiere dar. Por eso:
///  1) Buscamos el cascanueces despierto más cercano al CENTRO de la pantalla (dentro de un cono de
///     'anguloAsistencia' grados y a menos de 'alcance' metros, y que se vea sin paredes en medio).
///  2) Si hay uno, se marca con una MIRILLA y la bola se lanza con el ángulo exacto para caerle encima
///     (fórmula del tiro parabólico), apuntando un poquito adelante si va caminando.
///  3) Si no hay ninguno, la bola sale hacia donde mira la cámara, con un arco suave.
/// </summary>
public class LanzadorNieve : MonoBehaviour
{
    public int bolas = 0;
    public int maximo = 5;
    public float fuerza = 14f;
    public float enfriamiento = 0.35f;
    [Tooltip("Modelo de la bola (BolaNieve.glb, hecho en Blender). Si falta, usa una esfera de Unity.")]
    public GameObject modeloBola;
    public Material materialBola;
    public Material materialParticulas;

    [Header("Puntería asistida")]
    public float anguloAsistencia = 28f;
    public float alcance = 18f;

    public System.Action AlCambiar;   // lo escucha la UI (contador)
    float ultimoLanzamiento = -9f;
    Cascanueces objetivo;
    RectTransform mirilla; CanvasGroup grupoMirilla;
    Cascanueces[] enemigos;

    void Awake() { if (materialParticulas != null) BolaNieve.matParticulas = materialParticulas; }

    void Start()
    {
        enemigos = FindObjectsByType<Cascanueces>();
        // mirilla: un aro dorado que se dibuja encima del cascanueces apuntado
        var capa = UIConstructor.Capa("Mirilla", 4);
        mirilla = UIConstructor.Rect("Aro", capa, Vector2.zero, Vector2.zero, new Vector2(70, 70));
        grupoMirilla = UIConstructor.Grupo(mirilla, 0f);
        var aro = UIConstructor.Imagen(mirilla, new Color(1f, 0.85f, 0.35f, 0.9f));
        aro.sprite = UIConstructor.SpriteAro();
    }

    /// <summary>El cascanueces despierto más cerca del centro de la pantalla (o null).</summary>
    Cascanueces BuscarObjetivo()
    {
        if (enemigos == null || Camera.main == null) return null;
        Transform cam = Camera.main.transform;
        Vector3 frente = cam.forward; frente.y = 0f; frente.Normalize();
        Cascanueces mejor = null; float mejorAngulo = anguloAsistencia;
        foreach (var c in enemigos)
        {
            if (c == null || !c.Despierto) continue;
            Vector3 d = c.transform.position - transform.position; d.y = 0f;
            if (d.magnitude > alcance || d.magnitude < 0.5f) continue;
            float ang = Vector3.Angle(frente, d);
            if (ang >= mejorAngulo) continue;
            Vector3 ojo = transform.position + Vector3.up * 1.2f, pecho = c.transform.position + Vector3.up * 1.1f;
            // que no haya una PARED en medio: solo cuenta la capa Default (paredes, casas);
            // los muebles y regalos (capa Decoracion) y la capa SoloCamara no tapan la puntería
            RaycastHit hit;
            if (Physics.Linecast(ojo, pecho, out hit, 1 << 0, QueryTriggerInteraction.Ignore)
                && hit.collider.GetComponentInParent<Cascanueces>() != c && !hit.collider.transform.IsChildOf(transform)) continue;
            mejor = c; mejorAngulo = ang;
        }
        return mejor;
    }

    void LateUpdate()
    {
        objetivo = (bolas > 0 && Juego.Estado == Juego.Modo.Jugando) ? BuscarObjetivo() : null;
        bool ver = false;
        if (objetivo != null && Camera.main != null)
        {
            Vector3 p = Camera.main.WorldToScreenPoint(objetivo.transform.position + Vector3.up * 1.2f);
            if (p.z > 0f)
            {
                var canvas = (RectTransform)mirilla.parent;
                Vector2 local;
                RectTransformUtility.ScreenPointToLocalPointInRectangle(canvas, p, null, out local);
                mirilla.anchoredPosition = local + canvas.rect.size * 0.5f;
                mirilla.localScale = Vector3.one * (1f + 0.08f * Mathf.Sin(Time.time * 8f));
                ver = true;
            }
        }
        grupoMirilla.alpha = Mathf.MoveTowards(grupoMirilla.alpha, ver ? 1f : 0f, Time.deltaTime * 8f);
    }

    /// <summary>
    /// Velocidad para que un proyectil con rapidez 'v' caiga en 'destino' (tiro parabólico, arco bajo):
    ///   tan θ = (v² − √(v⁴ − g(g·x² + 2·y·v²))) / (g·x)
    /// x = distancia horizontal, y = diferencia de altura. Si no alcanza (raíz negativa) usa 45°.
    /// </summary>
    static Vector3 VelocidadParabolica(Vector3 origen, Vector3 destino, float v)
    {
        Vector3 d = destino - origen; float y = d.y; d.y = 0f; float x = d.magnitude;
        float g = -Physics.gravity.y;
        float raiz = v * v * v * v - g * (g * x * x + 2f * y * v * v);
        float theta = raiz >= 0f ? Mathf.Atan((v * v - Mathf.Sqrt(raiz)) / (g * x)) : Mathf.PI / 4f;
        return d.normalized * Mathf.Cos(theta) * v + Vector3.up * Mathf.Sin(theta) * v;
    }

    public void Recargar()
    {
        bolas = maximo;
        if (AlCambiar != null) AlCambiar();
    }

    void Update()
    {
        if (Juego.Bloqueado) return;
        bool f = Keyboard.current != null && Keyboard.current.fKey.wasPressedThisFrame;
        bool clic = Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame && Cursor.lockState == CursorLockMode.Locked;
        if (!(f || clic || Tactil.Lanzar)) return;
        if (bolas <= 0) { UIAviso.Mensaje("No tienes bolas de nieve. Junta nieve en un montón o una cubeta.", 2f); return; }
        if (Time.time - ultimoLanzamiento < enfriamiento) return;
        Lanzar();
    }

    void Lanzar()
    {
        ultimoLanzamiento = Time.time;
        GestorAudio.Efecto("lanzar", 0.7f);
        bolas--;
        if (AlCambiar != null) AlCambiar();

        Transform cam = Camera.main != null ? Camera.main.transform : transform;
        Vector3 origen = transform.position + Vector3.up * 1.2f;
        Vector3 velocidad;
        if (objetivo != null)
        {
            // puntería asistida: al pecho del cascanueces, adelantándonos a donde va a estar
            var agente = objetivo.GetComponent<UnityEngine.AI.NavMeshAgent>();
            Vector3 destino = objetivo.transform.position + Vector3.up * 1.1f;
            float tiempoVuelo = Vector3.Distance(origen, destino) / fuerza;
            if (agente != null) destino += agente.velocity * tiempoVuelo;
            velocidad = VelocidadParabolica(origen, destino, fuerza);
        }
        else
        {
            // sin objetivo: hacia donde mira la cámara (en horizontal), con un arco suave
            Vector3 plano = cam.forward; plano.y = 0f; plano.Normalize();
            velocidad = (plano + Vector3.up * 0.18f).normalized * fuerza;
        }
        Vector3 dir = velocidad.normalized;
        transform.rotation = Quaternion.LookRotation(new Vector3(dir.x, 0f, dir.z));   // el elfo voltea a lanzar

        GameObject bola;
        if (modeloBola != null)
        {
            bola = Instantiate(modeloBola);
            bola.AddComponent<SphereCollider>().radius = 0.5f;      // la malla mide 1 m de diámetro
            bola.transform.rotation = Random.rotation;              // cada bola con los grumos en otro lado
        }
        else
        {
            bola = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            if (materialBola != null) bola.GetComponent<Renderer>().sharedMaterial = materialBola;
        }
        bola.name = "BolaNieve";
        bola.transform.localScale = Vector3.one * 0.22f;
        bola.transform.position = origen + dir * 0.6f;
        var rb = bola.AddComponent<Rigidbody>();
        rb.mass = 0.2f;
        rb.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;   // para que no atraviese cosas rápido
        rb.linearVelocity = velocidad;
        bola.AddComponent<BolaNieve>();
        Physics.IgnoreCollision(bola.GetComponent<Collider>(), GetComponent<Collider>());
    }
}
