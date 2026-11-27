using System.Collections;
using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Una etapa del árbol: qué pieza pide y qué partes del modelo se van mostrando
/// (una por cada pieza entregada). Ej: etapa "Ramas" pide 3 piezas tipo "Rama" y
/// muestra Nivel1, Nivel2 y Nivel3 en orden.
/// </summary>
[System.Serializable]
public class EtapaArbol
{
    public string nombre = "Maceta";
    [Tooltip("Debe coincidir con el 'tipo' del Recogible.")]
    public string tipoPieza = "Maceta";
    [Tooltip("Pista que aparece en el objetivo.")]
    public string pista = "Busca la maceta";
    public GameObject[] partes;
}

/// <summary>
/// EL CORAZÓN DEL JUEGO. El árbol empieza vacío (todas sus partes ocultas).
/// El elfo trae piezas y, si es la pieza que toca, la parte correspondiente
/// aparece con una animación de "rebote". Al completar todas las etapas se
/// dispara el evento alCompletar (victoria).
/// </summary>
public class ArbolNavidad : Interactuable
{
    public static ArbolNavidad Instancia { get; private set; }

    public EtapaArbol[] etapas;

    [Header("Efectos")]
    public float duracionAparecer = 0.6f;
    [Tooltip("Luces que se van encendiendo conforme avanza el árbol.")]
    public Light[] lucesProgreso;
    public float intensidadMaxima = 6f;
    [Tooltip("Partículas doradas que salen donde aparece la parte nueva.")]
    public ParticleSystem destellos;
    public int cantidadDestellos = 40;

    [Header("Colisión")]
    [Tooltip("Mientras no hay maceta es trigger (se puede atravesar); luego se vuelve sólido.")]
    public CapsuleCollider colision;
    public float radioConMaceta = 1.0f, radioConRamas = 1.45f;

    [Header("Eventos")]
    public UnityEvent alColocarPieza;
    public UnityEvent alCompletar;
    /// <summary>Lo escucha la UI para actualizar el objetivo.</summary>
    public event System.Action AlCambiar;
    /// <summary>Se dispara al terminar una etapa (índice de la etapa terminada). Lo escucha el DirectorJuego.</summary>
    public event System.Action<int> AlCompletarEtapa;

    int etapa;        // índice de la etapa actual
    int entregadas;   // piezas entregadas dentro de la etapa actual

    public bool Completo { get { return etapas == null || etapa >= etapas.Length; } }
    public EtapaArbol EtapaActual { get { return Completo ? null : etapas[etapa]; } }
    public int EntregadasEtapa { get { return entregadas; } }
    public int TotalPiezas { get { int n = 0; foreach (var e in etapas) n += e.partes.Length; return n; } }
    public int PiezasColocadas
    {
        get { int n = 0; for (int i = 0; i < etapa && i < etapas.Length; i++) n += etapas[i].partes.Length; return n + (Completo ? 0 : entregadas); }
    }
    public float Progreso { get { return TotalPiezas == 0 ? 1f : (float)PiezasColocadas / TotalPiezas; } }

    void Awake()
    {
        Instancia = this;
        // Al iniciar, el árbol está "desarmado": ocultamos todas sus partes.
        foreach (var e in etapas) foreach (var p in e.partes) if (p) p.SetActive(false);
        ActualizarColision();
        ActualizarLuces(true);
    }

    // ---------- Interactuable ----------
    public override bool PuedeInteractuar(Interactor quien) { return !Completo; }

    public override string Texto(Interactor quien)
    {
        var e = EtapaActual;
        if (TraeLaPieza(quien))
            return "Colocar " + e.nombre.ToLower() + " (" + (entregadas + 1) + "/" + e.partes.Length + ")";
        return "Falta: " + e.nombre.ToLower();
    }

    public override void Interactuar(Interactor quien)
    {
        if (!TraeLaPieza(quien)) return;   // trae otra cosa o nada → no pasa nada
        Recogible pieza = quien.Inventario.Entregar();
        pieza.Consumir();
        ColocarSiguiente();
    }

    bool TraeLaPieza(Interactor quien)
    {
        var e = EtapaActual;
        return e != null && quien.Inventario != null && quien.Inventario.EnMano != null
               && quien.Inventario.EnMano.tipo == e.tipoPieza;
    }

    // ---------- Lógica de etapas ----------
    /// <summary>Muestra la siguiente parte del árbol y avanza de etapa si ya se completó.</summary>
    public void ColocarSiguiente()
    {
        if (Completo) return;
        var e = EtapaActual;
        GameObject parte = e.partes[entregadas];
        parte.SetActive(true);
        StartCoroutine(Aparecer(parte.transform));

        if (destellos != null)
        {
            destellos.transform.position = parte.GetComponent<Renderer>() != null
                ? parte.GetComponent<Renderer>().bounds.center : parte.transform.position;
            destellos.Emit(cantidadDestellos);
        }

        entregadas++;
        string mensaje = "¡" + e.tipoPieza + " colocada!" + (e.partes.Length > 1 ? "  (" + entregadas + "/" + e.partes.Length + ")" : "");
        int etapaTerminada = -1;
        if (entregadas >= e.partes.Length) { etapaTerminada = etapa; etapa++; entregadas = 0; }
        else UIAviso.Mensaje(mensaje, 2.5f);   // al terminar etapa, el DirectorJuego muestra el banner

        GestorAudio.Efecto(etapaTerminada >= 0 ? "etapa" : "colocar");
        ActualizarColision();
        ActualizarLuces(false);
        alColocarPieza.Invoke();
        if (AlCambiar != null) AlCambiar();
        if (etapaTerminada >= 0 && AlCompletarEtapa != null) AlCompletarEtapa(etapaTerminada);
        if (Completo) alCompletar.Invoke();
    }

    /// <summary>Animación "ease out back": crece de 0 a un poquito más de 1 y regresa a 1.</summary>
    IEnumerator Aparecer(Transform t)
    {
        Vector3 final = t.localScale;
        float tiempo = 0f;
        while (tiempo < duracionAparecer)
        {
            tiempo += Time.deltaTime;
            float x = Mathf.Clamp01(tiempo / duracionAparecer) - 1f;
            const float c = 1.70158f;
            float k = 1f + (c + 1f) * x * x * x + c * x * x;   // easeOutBack
            t.localScale = final * k;
            yield return null;
        }
        t.localScale = final;
    }

    void ActualizarColision()
    {
        if (colision == null) return;
        int colocadas = PiezasColocadas;
        colision.isTrigger = colocadas == 0;
        colision.radius = colocadas >= 2 ? radioConRamas : radioConMaceta;
    }

    void ActualizarLuces(bool inmediato)
    {
        if (lucesProgreso == null) return;
        float objetivo = Progreso * Progreso * intensidadMaxima;   // al cuadrado: el final brilla mucho más
        foreach (var l in lucesProgreso)
        {
            if (l == null) continue;
            if (inmediato) l.intensity = objetivo;
            else StartCoroutine(SubirLuz(l, objetivo));
        }
    }

    IEnumerator SubirLuz(Light l, float objetivo)
    {
        float inicio = l.intensity;
        for (float t = 0; t < 1f; t += Time.deltaTime)
        {
            l.intensity = Mathf.Lerp(inicio, objetivo, t);
            yield return null;
        }
        l.intensity = objetivo;
    }
}
