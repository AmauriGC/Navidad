using UnityEngine;
using UnityEngine.AI;

/// <summary>
/// IA del cascanueces: una MÁQUINA DE ESTADOS sobre un NavMeshAgent.
///
///   Dormido ──(se colocan N piezas en el árbol)──► Patrulla
///   Patrulla ──(te ve o te oye correr)──► Sospecha ──(te sigue viendo)──► Persecucion
///   Persecucion ──(te alcanza)──► te quita la pieza y regresa a Patrulla
///   Persecucion ──(te pierde de vista unos segundos)──► Patrulla
///   Cualquiera ──(bola de nieve)──► Aturdido ──► Patrulla
///   Cualquiera ──(árbol completo)──► Congelado (vuelve a ser juguete)
///
/// El NavMeshAgent calcula el camino por el NavMesh (el "mapa" de zonas caminables)
/// y esquiva paredes y mesas solo; nosotros solo le decimos a dónde ir (SetDestination).
/// </summary>
[RequireComponent(typeof(NavMeshAgent))]
public class Cascanueces : MonoBehaviour
{
    public enum Estado { Dormido, Patrulla, Sospecha, Persecucion, Aturdido, Congelado }

    [Header("Despertar")]
    [Tooltip("Despierta cuando el árbol tenga al menos estas piezas colocadas.")]
    public int despertarConPiezas = 1;
    public string nombre = "Cascanueces";

    [Header("Patrulla")]
    public Transform[] puntosPatrulla;
    public float velocidadPatrulla = 1.6f;
    public float esperaEnPunto = 1.5f;

    [Header("Sentidos")]
    public float distanciaVision = 9f;
    [Range(10, 180)] public float anguloVision = 110f;
    [Tooltip("Si corres a menos de esta distancia, te oye aunque no te vea.")]
    public float distanciaOido = 4.5f;
    public float tiempoSospecha = 0.7f;

    [Header("Persecución")]
    public float velocidadPersecucion = 3.6f;
    public float distanciaAtrapar = 1.0f;
    public float olvidarTras = 3.5f;

    [Header("Aturdido")]
    public float duracionAturdido = 4f;
    public ParticleSystem estrellasAturdido;

    public Estado EstadoActual { get; private set; }
    /// <summary>0..1, lo usa el animador para la mandíbula y los ojos.</summary>
    public float Alerta { get; private set; }

    NavMeshAgent agente;
    Transform jugador; ElfoController elfo; Inventario inventario;
    int indicePatrulla; float temporizador; float ultimaVezVisto; Vector3 ultimaPosVista;
    Vector3 posInicial; Quaternion rotInicial;

    void Awake()
    {
        agente = GetComponent<NavMeshAgent>();
        posInicial = transform.position; rotInicial = transform.rotation;
    }

    void Start()
    {
        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { jugador = j.transform; elfo = j.GetComponent<ElfoController>(); inventario = j.GetComponent<Inventario>(); }
        if (ArbolNavidad.Instancia != null)
        {
            ArbolNavidad.Instancia.AlCambiar += RevisarDespertar;
            ArbolNavidad.Instancia.alCompletar.AddListener(Congelar);
        }
        CambiarA(Estado.Dormido);
        if (GetComponent<LlaveCuerda>() == null) gameObject.AddComponent<LlaveCuerda>();   // la llave de la espalda gira
    }

    void OnDestroy()
    {
        if (ArbolNavidad.Instancia != null) ArbolNavidad.Instancia.AlCambiar -= RevisarDespertar;
    }

    void RevisarDespertar()
    {
        if (EstadoActual == Estado.Dormido && ArbolNavidad.Instancia.PiezasColocadas >= despertarConPiezas)
            CambiarA(Estado.Patrulla);
    }

    public bool Despierto { get { return EstadoActual != Estado.Dormido && EstadoActual != Estado.Congelado; } }

    // ------------------------------------------------------------------ cambio de estado
    void CambiarA(Estado nuevo)
    {
        // sonidos de cada cambio de estado
        Vector3 p = transform.position + Vector3.up;
        if (EstadoActual == Estado.Dormido && nuevo == Estado.Patrulla)
        {
            GestorAudio.Efecto3D("despertar", p);
            GestorAudio.Efecto("susto", 0.55f, 0f);          // golpe dramático: ¡despertó uno!
        }
        else if (nuevo == Estado.Sospecha) { GestorAudio.Efecto3D("clac", p, 1.3f); Gritar(Guion.GritoSospecha); }
        else if (nuevo == Estado.Persecucion) { GestorAudio.Efecto("alerta", 0.7f); GestorAudio.Efecto3D("clac", p, 1.3f); Gritar(Guion.GritoVer, true); }
        else if (EstadoActual == Estado.Persecucion && nuevo == Estado.Patrulla) { GestorAudio.Efecto("escapaste", 0.6f); Gritar(Guion.GritoPerder); }   // te perdió
        EstadoActual = nuevo;
        temporizador = 0f;
        AplicarEstado(nuevo);
    }

    /// Ajusta el NavMeshAgent al estado (sin sonidos). Se llama al cambiar de estado y al acomodarse en el NavMesh.
    void AplicarEstado(Estado nuevo)
    {
        if (!agente.isOnNavMesh) return;
        switch (nuevo)
        {
            case Estado.Dormido:
            case Estado.Congelado:
                agente.isStopped = true; agente.ResetPath(); break;
            case Estado.Patrulla:
                agente.isStopped = false; agente.speed = velocidadPatrulla * FactorCuerda; IrAlPunto(); break;
            case Estado.Sospecha:
                agente.isStopped = true; break;
            case Estado.Persecucion:
                agente.isStopped = false; agente.speed = velocidadPersecucion * FactorCuerda; break;
            case Estado.Aturdido:
                agente.isStopped = true; agente.ResetPath();
                if (estrellasAturdido) estrellasAturdido.Play();
                break;
        }
    }

    // ------------------------------------------------------------------ cada frame
    /// En el juego compilado el NavMesh puede cargarse DESPUÉS de que el agente se activa ("Failed to create agent
    /// because there is no valid NavMesh"); el agente queda fuera del NavMesh para siempre. Aquí se recoloca solo
    /// (punto del NavMesh más cercano + Warp) y se vuelve a aplicar el estado actual.
    float siguienteAcomodo;
    bool AcomodarEnNavMesh()
    {
        if (agente.isOnNavMesh) return true;
        if (Time.time < siguienteAcomodo) return false;
        siguienteAcomodo = Time.time + 0.5f;
        if (!agente.enabled) return false;
        NavMeshHit hit;
        if (NavMesh.SamplePosition(transform.position, out hit, 3f, NavMesh.AllAreas) && agente.Warp(hit.position))
        {
            AplicarEstado(EstadoActual);
            return true;
        }
        return false;
    }

    void Update()
    {
        AcomodarEnNavMesh();
        if (Juego.EnemigosEnPausa || !agente.isOnNavMesh)
        {
            if (agente.isOnNavMesh) agente.isStopped = true;
            return;
        }
        if (EstadoActual == Estado.Patrulla || EstadoActual == Estado.Persecucion) agente.isStopped = false;
        if (Despierto && !arrancado) Arrancar();

        temporizador += Time.deltaTime;
        Pasos();
        bool loVeo = Despierto && EstadoActual != Estado.Aturdido && PuedeVerAlJugador();
        if (loVeo) { ultimaVezVisto = Time.time; ultimaPosVista = jugador.position; }

        switch (EstadoActual)
        {
            case Estado.Patrulla:
                Alerta = Mathf.MoveTowards(Alerta, 0f, Time.deltaTime);
                if (loVeo) { CambiarA(Estado.Sospecha); break; }
                if (!agente.pathPending && agente.remainingDistance < 0.4f)
                {
                    if (temporizador > esperaEnPunto) { indicePatrulla++; IrAlPunto(); temporizador = 0f; }
                }
                else temporizador = 0f;
                break;

            case Estado.Sospecha:
                Alerta = Mathf.MoveTowards(Alerta, 0.6f, Time.deltaTime * 2f);
                Girar(ultimaPosVista);
                if (temporizador > tiempoSospecha) CambiarA(loVeo ? Estado.Persecucion : Estado.Patrulla);
                break;

            case Estado.Persecucion:
                Alerta = Mathf.MoveTowards(Alerta, 1f, Time.deltaTime * 3f);
                agente.SetDestination(ultimaPosVista);
                if (Vector3.Distance(transform.position, jugador.position) < distanciaAtrapar) { Atrapar(); break; }
                if (Time.time - ultimaVezVisto > olvidarTras) CambiarA(Estado.Patrulla);
                break;

            case Estado.Aturdido:
                Alerta = 0f;
                if (temporizador > DuracionAturdido) CambiarA(Estado.Patrulla);
                break;
        }
    }

    void IrAlPunto()
    {
        if (puntosPatrulla == null || puntosPatrulla.Length == 0) { agente.SetDestination(posInicial); return; }
        indicePatrulla %= puntosPatrulla.Length;
        agente.SetDestination(puntosPatrulla[indicePatrulla].position);
    }

    void Girar(Vector3 hacia)
    {
        Vector3 d = hacia - transform.position; d.y = 0f;
        if (d.sqrMagnitude > 0.01f)
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(d), 6f * Time.deltaTime);
    }

    // ------------------------------------------------------------------ sentidos
    /// <summary>
    /// Vista: distancia + ángulo (cono frente a él) + que no haya paredes en medio (Linecast).
    /// Oído: si el elfo corre cerca, lo detecta aunque esté detrás.
    /// </summary>
    bool PuedeVerAlJugador()
    {
        if (jugador == null) return false;
        Vector3 ojos = transform.position + Vector3.up * 1.4f;
        Vector3 objetivo = jugador.position + Vector3.up * 0.8f;
        Vector3 dir = objetivo - ojos;
        float dist = dir.magnitude;

        bool loOye = elfo != null && elfo.Corriendo && dist < distanciaOido;
        bool enCono = dist < distanciaVision * Apagon.FactorVision && Vector3.Angle(transform.forward, new Vector3(dir.x, 0f, dir.z)) < anguloVision * 0.5f;
        if (!loOye && !enCono) return false;

        RaycastHit hit;
        if (Physics.Linecast(ojos, objetivo, out hit, ~(1 << 9), QueryTriggerInteraction.Ignore))   // ignora la capa SoloCamara
            return hit.collider.transform.IsChildOf(jugador) || loOye;
        return true;
    }

    // ------------------------------------------------------------------ pasos (toc-toc de madera)
    // Cada cascanueces tiene su propia fuente 3D: los oyes acercarse aunque no los veas.
    AudioSource fuentePasos; float distanciaPaso; int pie;

    void Pasos()
    {
        float v = agente.velocity.magnitude;
        if (!Despierto || v < 0.2f) return;
        distanciaPaso += v * Time.deltaTime;
        float zancada = EstadoActual == Estado.Persecucion ? 0.9f : 0.7f;
        if (distanciaPaso < zancada) return;
        distanciaPaso = 0f; pie = 1 - pie;
        if (fuentePasos == null) { fuentePasos = GestorAudio.FuentePropia(gameObject, 3f, 24f); fuentePasos.priority = 64; }
        fuentePasos.pitch = (EstadoActual == Estado.Persecucion ? 1.1f : 0.95f) + Random.Range(-0.05f, 0.05f);
        // detallitos v1.5: bota de madera más pesada y más fuerte (paso_cas3/4); antes casi no se oían
        fuentePasos.PlayOneShot(Resources.Load<AudioClip>("Audio/paso_cas" + (pie + 3)), 0.95f * GestorAudio.VolumenEfectos);
    }

    // ------------------------------------------------------------------ acciones
    void Atrapar()
    {
        string quitado = null;
        if (inventario != null && inventario.TieneObjeto)
        {
            var pieza = inventario.Entregar();
            quitado = pieza.nombreVisible;
            pieza.VolverAlInicio();          // la vuelve a esconder donde estaba
        }
        if (elfo != null)
        {
            Vector3 empuje = (jugador.position - transform.position); empuje.y = 0f;
            // antes te aventaba 7 m/s hacia atrás sin mirar: si atrás había un rincón, ahí te quedabas.
            // Ahora el empujón se acorta si hay pared/rincón (lo mide el NavMesh) y brinca menos alto.
            float seguro = elfo.EmpujeSeguro(empuje, 1.2f) / 1.2f;   // 0..1
            elfo.Empujar(empuje.normalized * 7f * seguro + Vector3.up * 2.5f, 1.0f);
        }
        UIFundido.Destello(new Color(0.8f, 0.05f, 0.05f, 0.45f));
        GestorAudio.Efecto("atrapado", 0.8f, 0f);
        Gritar(Guion.GritoAtrapar, true);
        TemblorCamara.Sacudir(0.9f);
        UIAviso.Mensaje(quitado != null
            ? "¡El " + nombre + " te quitó la " + quitado + " y la volvió a esconder!"
            : "¡El " + nombre + " te atrapó!", 3f);
        // Difícil / Imposible: cada vez que te atrapan pierdes una vida; sin vidas se acaba la noche
        if (Dificultad.ConVidas)
        {
            bool fin = Vidas.Perder();
            if (fin) { var dir = FindAnyObjectByType<DirectorJuego>(); if (dir != null) dir.SinVidas(); }
            else UIAviso.Mensaje((quitado != null ? "¡Te quitó la " + quitado + "!  " : "¡Te atraparon!  ")
                                 + "<color=#ff8080>-1 vida</color>  (te quedan " + Vidas.Actual + ")", 3f);
        }
        // después de atrapar se va un ratito a patrullar (para no atraparte en cadena)
        ultimaVezVisto = -99f;
        CambiarA(Estado.Aturdido);
        temporizador = DuracionAturdido - 1.5f;
    }

    /// <summary>Un ruido fuerte (caja sorpresa): si está despierto y lo alcanza a oír, corre a ver qué pasó.
    /// Va en "Persecución" hacia el lugar del ruido; si ahí no te ve, a los pocos segundos regresa a patrullar.</summary>
    public bool OirRuido(Vector3 pos, float radio)
    {
        if (!Despierto || EstadoActual == Estado.Aturdido || EstadoActual == Estado.Persecucion) return false;
        if ((pos - transform.position).sqrMagnitude > radio * radio) return false;
        ultimaPosVista = pos; ultimaVezVisto = Time.time;
        CambiarA(Estado.Persecucion);
        return true;
    }

    /// <summary>Lo llama la bola de nieve.</summary>
    public void Aturdir()
    {
        if (!Despierto) return;
        GestorAudio.Efecto3D("aturdido", transform.position + Vector3.up);
        CambiarA(Estado.Aturdido);
        Gritar(Guion.GritoAturdido, true);
    }

    /// <summary>Con el poder de galleta (las 10 galletas) las bolas de nieve aturden el doble.</summary>
    public float DuracionAturdido { get { return duracionAturdido * (Galleta.Todas ? 2f : 1f); } }

    /// <summary>La Máquina 7 reparada deja de hacer ruido y chispas: los cascanueces se calman
    /// (más lentos, ven y oyen menos). Lo llama MaquinaRota al terminar la reparación.</summary>
    public void Calmar()
    {
        Calmado = true;
        velocidadPatrulla *= 0.85f; velocidadPersecucion *= 0.85f;
        distanciaVision *= 0.75f; distanciaOido *= 0.7f;
        if (agente != null) agente.speed *= 0.85f;
    }

    /// <summary>Lo llama Dificultad.Aplicar() al empezar la partida (Medio = todo x1).</summary>
    public void AplicarDificultad(Dificultad.Datos d)
    {
        velocidadPatrulla *= d.velocidad; velocidadPersecucion *= d.velocidad;
        distanciaVision *= d.vista; distanciaOido *= d.oido;
        duracionAturdido *= d.aturdido;
        // despertar antes/después se mueve por ETAPAS completas (no por piezas): la presentación del cascanueces
        // ("¡ha despertado!") sale al terminar una etapa; si despertaba a media etapa ya andaba suelto antes de presentarlo.
        if (d.despertarAntes != 0 && ArbolNavidad.Instancia != null)
        {
            var et = ArbolNavidad.Instancia.etapas;
            var finales = new System.Collections.Generic.List<int>();   // piezas acumuladas al terminar cada etapa
            int suma = 0;
            foreach (var e in et) { suma += e.partes.Length; finales.Add(suma); }
            int k = finales.IndexOf(despertarConPiezas);
            if (k >= 0)
            {
                k = Mathf.Clamp(k - d.despertarAntes, 0, finales.Count - 2);   // nunca al poner la última pieza
                despertarConPiezas = finales[k];
            }
        }
        if (agente != null) agente.speed *= d.velocidad;
    }

    public void Congelar() { CambiarA(Estado.Congelado); Alerta = 0f; }

    // ------------------------------------------------------------------ historia 1.5: la CUERDA que les da Siete
    float factorCuerda = 1f, cuerdaHasta = -1f;
    /// <summary>Siete ya está curada: van más lentos (y la llave de cuerda gira despacito).</summary>
    public bool Calmado { get; private set; }
    /// <summary>¿Trae cuerda extra de una descarga? (la llave gira rapidísimo y va más rápido).</summary>
    public bool ConCuerdaExtra { get { return Time.time < cuerdaHasta; } }
    float FactorCuerda { get { return ConCuerdaExtra ? factorCuerda : 1f; } }

    /// <summary>Una descarga de Siete le da cuerda: x'factor' de velocidad durante 'segundos'.</summary>
    public void DarCuerda(float factor, float segundos)
    {
        factorCuerda = factor; cuerdaHasta = Time.time + segundos;
        if (Despierto) Gritar(Guion.GritoDescarga, true);
        AjustarVelocidad();
        CancelInvoke(nameof(AjustarVelocidad));
        Invoke(nameof(AjustarVelocidad), segundos + 0.05f);   // al acabarse la cuerda vuelve a su velocidad normal
    }

    void AjustarVelocidad()
    {
        if (agente == null || !agente.isOnNavMesh) return;
        if (EstadoActual == Estado.Patrulla) agente.speed = velocidadPatrulla * FactorCuerda;
        else if (EstadoActual == Estado.Persecucion) agente.speed = velocidadPersecucion * FactorCuerda;
    }

    // ------------------------------------------------------------------ detallitos v1.5: voz y arranque
    bool arrancado;

    /// <summary>La primera vez que se mueve después de despertar: la llave da cuerda, CLAC-CLAC y "¡Uno, dos!".
    /// (Al despertar suele estar la cinemática; este sonido sale cuando de verdad empieza a caminar.)</summary>
    void Arrancar()
    {
        arrancado = true;
        if (fuenteVoz == null) fuenteVoz = GestorAudio.FuentePropia(gameObject, 3f, 26f);
        var c = Resources.Load<AudioClip>("Audio/cas_arranque");
        if (c != null) fuenteVoz.PlayOneShot(c, 1f * GestorAudio.VolumenEfectos);
        Gritar(new[] { "¡Uno, dos! ¡Uno, dos!" }, true);
    }
    AudioSource fuenteVoz;

    /// <summary>Globito sobre la cabeza + voz de madera (ver GloboCascanueces).</summary>
    void Gritar(string[] frases, bool forzar = false)
    {
        if (frases == null || frases.Length == 0) return;
        GloboCascanueces.Decir(gameObject, frases, 2.45f, forzar);
    }

    /// <summary>Descarga GRAVE (Difícil/Imposible): si estaba dormido, despierta antes de tiempo.</summary>
    public bool DespertarYa()
    {
        if (EstadoActual != Estado.Dormido) return false;
        CambiarA(Estado.Patrulla);
        return true;
    }
}
