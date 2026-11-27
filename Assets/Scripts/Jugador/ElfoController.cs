using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.AI;

/// <summary>
/// Movimiento del elfo en tercera persona.
/// - WASD / flechas: caminar (relativo a hacia dónde mira la cámara)
/// - Shift: correr      - Espacio: saltar
/// Usa un CharacterController: se mueve con Move() y choca con paredes sin necesitar Rigidbody.
/// </summary>
[RequireComponent(typeof(CharacterController))]
public class ElfoController : MonoBehaviour
{
    [Header("Movimiento")]
    public float velocidadCaminar = 3.5f;
    public float velocidadCorrer = 6f;
    [Tooltip("Qué tan rápido llega a la velocidad deseada (más alto = más brusco).")]
    public float aceleracion = 25f;
    [Tooltip("Qué tan rápido gira el elfo hacia donde camina.")]
    public float velocidadGiro = 12f;

    [Header("Salto y gravedad")]
    public float alturaSalto = 1.1f;
    public float gravedad = -20f;

    [Header("Referencias")]
    [Tooltip("Cámara usada para saber qué es 'adelante'. Si está vacío usa Camera.main.")]
    public Transform camara;

    /// <summary>Velocidad horizontal real (la usa el animador para mover piernas y brazos).</summary>
    public float VelocidadActual { get; private set; }
    public bool EnSuelo { get; private set; }
    /// <summary>Está corriendo con Shift (los cascanueces oyen los pasos rápidos).</summary>
    public bool Corriendo { get; private set; }
    /// <summary>Otros sistemas (GameManager, cinemáticas) pueden bloquear el control.</summary>
    [HideInInspector] public bool puedeMoverse = true;

    CharacterController cc;
    Vector3 velHorizontal;
    float velVertical;
    float aturdidoHasta;
    /// <summary>Lo pone FrioJugador: 0.5 mientras tienes frío (bolas de los cascanueces nevados), 1 normal.</summary>
    [HideInInspector] public float factorFrio = 1f;   // mientras Time.time < aturdidoHasta, no se puede mover
    [HideInInspector] public Vector3 empujeExterno;   // viento de la ventisca (m/s); lo pone Ventisca

    void Awake()
    {
        cc = GetComponent<CharacterController>();
        if (camara == null && Camera.main != null) camara = Camera.main.transform;
    }

    void Update()
    {
        Vector2 input = LeerInput();

        // 1) Convertir el input a una dirección en el mundo, relativa a la cámara.
        Vector3 adelante = Vector3.forward;
        if (camara != null) adelante = Vector3.ProjectOnPlane(camara.forward, Vector3.up).normalized;
        Vector3 derecha = Vector3.Cross(Vector3.up, adelante);
        Vector3 direccion = adelante * input.y + derecha * input.x;

        // 2) Acelerar suavemente hacia la velocidad deseada.
        bool corre = ((Keyboard.current != null && Keyboard.current.leftShiftKey.isPressed) || Tactil.Correr) && input.sqrMagnitude > 0.01f;
        Corriendo = corre;
        Vector3 objetivo = direccion * (corre ? velocidadCorrer : velocidadCaminar) * (Galleta.Todas ? 1.2f : 1f) * factorFrio;   // poder de galleta / frío
        velHorizontal = Vector3.MoveTowards(velHorizontal, objetivo, aceleracion * Time.deltaTime);

        // 3) Girar el cuerpo hacia donde camina.
        if (direccion.sqrMagnitude > 0.01f)
        {
            Quaternion rot = Quaternion.LookRotation(direccion);
            transform.rotation = Quaternion.Slerp(transform.rotation, rot, velocidadGiro * Time.deltaTime);
        }

        // 4) Gravedad y salto. v = sqrt(2·g·h) da justo la altura deseada.
        if (cc.isGrounded)
        {
            if (velVertical < 0f) velVertical = -2f; // lo mantiene pegado al piso
            if (puedeMoverse && !Juego.Bloqueado && Time.time >= aturdidoHasta && ((Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame) || Tactil.Saltar))
            {
                velVertical = Mathf.Sqrt(alturaSalto * -2f * gravedad);
                GestorAudio.Efecto("salto", 0.5f);
            }
        }
        velVertical += gravedad * Time.deltaTime;

        Vector3 viento = Time.time >= aturdidoHasta ? empujeExterno : Vector3.zero;
        cc.Move((velHorizontal + viento + Vector3.up * velVertical) * Time.deltaTime);

        EnSuelo = cc.isGrounded;
        Vector3 v = cc.velocity; v.y = 0f;
        VelocidadActual = v.magnitude;
        RevisarAtorado(input);
    }

    // ------------------------------------------------------------------ anti-atorones
    // Si un empujón (o un salto raro) te deja en un rincón FUERA del piso caminable (NavMesh) y por más que
    // intentas moverte no avanzas, te regresamos al último lugar seguro donde estuviste.
    Vector3 ultimoSeguro; bool haySeguro; float ultimoEmpujon = -99f; float siguienteRevision, tiempoAtorado; Vector3 posRevision;

    void RevisarAtorado(Vector2 input)
    {
        if (Time.time < siguienteRevision) return;
        siguienteRevision = Time.time + 0.25f;
        NavMeshHit h;
        bool enPiso = NavMesh.SamplePosition(transform.position, out h, 0.7f, NavMesh.AllAreas);
        if (enPiso && cc.isGrounded) { ultimoSeguro = h.position; haySeguro = true; tiempoAtorado = 0f; posRevision = transform.position; return; }
        // fuera del NavMesh: ¿estás intentando moverte sin avanzar?
        // (encima de la repisa o de las cajas también estás fuera del NavMesh y ahí NO hay que regresarte:
        //  solo cuenta si te acaban de empujar o si estás trabado en el aire)
        bool sospechoso = Time.time - ultimoEmpujon < 10f || !cc.isGrounded;
        bool intenta = sospechoso && (input.sqrMagnitude > 0.1f || Time.time < aturdidoHasta);
        float avance = Vector3.Distance(transform.position, posRevision);
        posRevision = transform.position;
        tiempoAtorado = (intenta && avance < 0.12f) ? tiempoAtorado + 0.25f : 0f;
        if (tiempoAtorado >= 1.5f && haySeguro)
        {
            tiempoAtorado = 0f;
            Teletransportar(ultimoSeguro + Vector3.up * 0.1f, transform.rotation);
            UIAviso.Mensaje("¡Uf! Saliste del rincón.", 2f);
        }
    }

    /// <summary>Hasta dónde se puede empujar al elfo en esa dirección sin meterlo en un rincón (por el NavMesh).</summary>
    public float EmpujeSeguro(Vector3 direccion, float maximo)
    {
        NavMeshHit a, b;
        if (!NavMesh.SamplePosition(transform.position, out a, 1f, NavMesh.AllAreas)) return maximo * 0.3f;
        if (NavMesh.Raycast(a.position, a.position + direccion.normalized * maximo, out b, NavMesh.AllAreas))
            return Mathf.Max(0f, b.distance - 0.4f);
        return maximo;
    }

    Vector2 LeerInput()
    {
        var kb = Keyboard.current;
        if (!puedeMoverse || Time.time < aturdidoHasta || Juego.Bloqueado) return Vector2.zero;
        Vector2 i = Tactil.Mover;       // joystick táctil (0 si no hay)
        if (kb != null)
        {
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) i.y += 1;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) i.y -= 1;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) i.x += 1;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) i.x -= 1;
        }
        return Vector2.ClampMagnitude(i, 1f);
    }

    /// <summary>Empuja al elfo (ej. cuando lo atrapa un cascanueces) y lo deja aturdido un momento.</summary>
    public void Empujar(Vector3 impulso, float segundosAturdido)
    {
        velHorizontal = new Vector3(impulso.x, 0f, impulso.z);
        velVertical = impulso.y;
        aturdidoHasta = Time.time + segundosAturdido;
        ultimoEmpujon = Time.time;
    }

    /// <summary>Congelado: no se puede mover ni saltar (pero la gravedad sigue).</summary>
    public void Inmovilizar(float segundos)
    {
        velHorizontal = Vector3.zero;
        aturdidoHasta = Mathf.Max(aturdidoHasta, Time.time + segundos);
    }

    /// <summary>Teletransporta al elfo (CharacterController necesita apagarse para mover transform).</summary>
    public void Teletransportar(Vector3 pos, Quaternion rot)
    {
        cc.enabled = false;
        transform.SetPositionAndRotation(pos, rot);
        velHorizontal = Vector3.zero; velVertical = 0f;
        cc.enabled = true;
    }
}
