using UnityEngine;

/// <summary>
/// Objeto que el elfo puede levantar con E (piezas de juguete, juguetes armados, regalos).
/// Mientras está en el piso flota y gira un poquito para que se note que se puede tomar.
/// </summary>
public class Recogible : Interactuable
{
    [Tooltip("Identificador que usan las recetas: Madera, Rueda, Mono, Tornillo, Carrito, Regalo...")]
    public string tipo = "Pieza";
    public string nombreVisible = "pieza";
    public bool flotarEnPiso = true;
    [Tooltip("Si está bloqueado no se puede tomar (ej. la guirnalda enredada en el reno).")]
    public bool bloqueado = false;

    public bool EnMano { get; private set; }

    Rigidbody rb;
    Collider[] colliders;
    Vector3 posReposo;
    float semilla;
    bool saltando;
    Light[] luces; float[] intensidades;   // el brillo de la pieza en el piso; en la mano deslumbraba al elfo

    // Dónde empezó (para regresarlo si un cascanueces te lo quita)
    Vector3 posInicial; Quaternion rotInicial; Transform padreInicial;

    void Awake()
    {
        posInicial = transform.position; rotInicial = transform.rotation; padreInicial = transform.parent;
        rb = GetComponent<Rigidbody>();
        colliders = GetComponentsInChildren<Collider>();
        posReposo = transform.position;
        semilla = Random.value * 10f;
        luces = GetComponentsInChildren<Light>(true);
        intensidades = new float[luces.Length];
        for (int i = 0; i < luces.Length; i++) intensidades[i] = luces[i].intensity;
        if (string.IsNullOrEmpty(textoAccion) || textoAccion == "Usar") textoAccion = "Recoger";
    }

    public override string Texto(Interactor quien) { return textoAccion + " " + nombreVisible; }

    public override bool PuedeInteractuar(Interactor quien)
    {
        return !EnMano && !bloqueado && quien.Inventario != null && !quien.Inventario.TieneObjeto;
    }

    public override void Interactuar(Interactor quien) { quien.Inventario.Tomar(this); }

    void Update()
    {
        if (EnMano || bloqueado || saltando || !flotarEnPiso || (rb != null && !rb.isKinematic)) return;
        float t = Time.time + semilla;
        transform.position = posReposo + Vector3.up * (Mathf.Sin(t * 2f) * 0.05f);
        transform.Rotate(0f, 40f * Time.deltaTime, 0f, Space.World);
    }

    public void AlTomar(Transform mano)
    {
        EnMano = true;
        if (rb != null) rb.isKinematic = true;
        foreach (var c in colliders) c.enabled = false;
        transform.SetParent(mano, false);
        transform.localPosition = Vector3.zero;
        transform.localRotation = Quaternion.identity;
        Brillo(0.12f);
    }

    /// <summary>En la mano la luz baja casi a nada (pegada al elfo lo dejaba blanco); en el piso vuelve.</summary>
    void Brillo(float factor)
    {
        for (int i = 0; i < luces.Length; i++) if (luces[i] != null) luces[i].intensity = intensidades[i] * factor;
    }

    public void AlSoltar(Vector3 posicion)
    {
        EnMano = false;
        transform.SetParent(null, true);
        transform.SetPositionAndRotation(posicion, Quaternion.identity);
        foreach (var c in colliders) c.enabled = true;
        if (rb != null) { rb.isKinematic = false; }
        else posReposo = posicion;
        Brillo(1f);
    }

    /// <summary>
    /// Desbloquea el objeto y lo hace "brincar" en arco hasta 'destino'
    /// (una parábola: se mueve en línea recta y le sumamos una altura con forma de seno).
    /// </summary>
    public void Liberar(Vector3 destino, float altura = 1.2f, float duracion = 0.7f)
    {
        StartCoroutine(Brincar(destino, altura, duracion));
    }

    System.Collections.IEnumerator Brincar(Vector3 destino, float altura, float duracion)
    {
        saltando = true;
        transform.SetParent(null, true);
        Vector3 inicio = transform.position;
        Quaternion rotInicio = transform.rotation;
        for (float t = 0f; t < 1f; t += Time.deltaTime / duracion)
        {
            transform.position = Vector3.Lerp(inicio, destino, t) + Vector3.up * Mathf.Sin(t * Mathf.PI) * altura;
            transform.rotation = Quaternion.Slerp(rotInicio, Quaternion.identity, t);
            yield return null;
        }
        transform.SetPositionAndRotation(destino, Quaternion.identity);
        posReposo = destino;
        posInicial = destino; rotInicial = Quaternion.identity; padreInicial = null;   // si se pierde, regresa aquí (no al reno)
        foreach (var c in colliders) c.enabled = true;
        bloqueado = false; saltando = false;
    }

    /// <summary>Regresa el objeto a donde estaba al inicio del juego (lo "esconden" otra vez).</summary>
    public void VolverAlInicio()
    {
        StopAllCoroutines(); saltando = false;
        EnMano = false;
        transform.SetParent(padreInicial, true);
        transform.SetPositionAndRotation(posInicial, rotInicial);
        posReposo = posInicial;
        Brillo(1f);
        foreach (var c in colliders) c.enabled = true;
        if (rb != null) rb.isKinematic = true;
    }

    /// <summary>Cuando una estación consume el objeto (ej. la mesa usa la madera).</summary>
    public void Consumir() { Destroy(gameObject); }
}
