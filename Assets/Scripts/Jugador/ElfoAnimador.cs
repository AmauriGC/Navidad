using UnityEngine;

/// <summary>
/// Animación PROCEDURAL del elfo: en lugar de un esqueleto con animaciones hechas a mano,
/// el modelo viene de Blender en piezas (piernas, brazos, cabeza, gorro) con el pivote en
/// cada articulación, y aquí las rotamos con funciones seno según la velocidad.
///   sin(fase) va de -1 a 1  → la pierna izquierda va adelante mientras la derecha va atrás.
/// Va en la raíz del modelo (hijo del Jugador).
/// </summary>
public class ElfoAnimador : MonoBehaviour
{
    public ElfoController controlador;
    public Inventario inventario;

    [Header("Caminar")]
    public float pasosPorSegundo = 2.2f;   // a velocidad de caminar
    public float anguloPiernas = 35f;
    public float anguloBrazos = 30f;
    public float rebote = 0.05f;

    [Header("Reposo")]
    public float respiracion = 0.015f;

    Transform piernaL, piernaR, brazoL, brazoR, cuerpo, cabeza, gorro;
    Quaternion rPiernaL, rPiernaR, rBrazoL, rBrazoR, rCabeza, rGorro;
    Vector3 posBase, escalaCuerpo;
    float fase, intensidad, cargar, aire;

    void Awake()
    {
        if (controlador == null) controlador = GetComponentInParent<ElfoController>();
        if (inventario == null) inventario = GetComponentInParent<Inventario>();
        piernaL = Buscar("PiernaL"); piernaR = Buscar("PiernaR");
        brazoL = Buscar("BrazoL"); brazoR = Buscar("BrazoR");
        cuerpo = Buscar("Cuerpo"); cabeza = Buscar("Cabeza"); gorro = Buscar("Gorro");
        // Guardamos la pose original para sumarle las rotaciones encima.
        rPiernaL = piernaL.localRotation; rPiernaR = piernaR.localRotation;
        rBrazoL = brazoL.localRotation; rBrazoR = brazoR.localRotation;
        rCabeza = cabeza.localRotation; rGorro = gorro.localRotation;
        posBase = transform.localPosition;
        escalaCuerpo = cuerpo.localScale;
    }

    void LateUpdate()
    {
        float vel = controlador ? controlador.VelocidadActual : 0f;
        float t = Time.time;

        // intensidad: 0 = quieto, 1 = caminando, >1 = corriendo (suavizado para que no salte)
        float objetivo = controlador ? vel / controlador.velocidadCaminar : 0f;
        intensidad = Mathf.Lerp(intensidad, objetivo, 10f * Time.deltaTime);
        float amt = Mathf.Clamp01(intensidad);

        // La fase avanza más rápido cuanto más rápido camina.
        fase += Time.deltaTime * pasosPorSegundo * Mathf.PI * Mathf.Max(intensidad, 0f);
        float s = Mathf.Sin(fase);

        bool enAire = controlador && !controlador.EnSuelo;
        aire = Mathf.Lerp(aire, enAire ? 1f : 0f, 12f * Time.deltaTime);
        bool lleva = inventario && inventario.TieneObjeto;
        cargar = Mathf.Lerp(cargar, lleva ? 1f : 0f, 10f * Time.deltaTime);

        // --- Piernas: se balancean en sentidos opuestos; en el aire se abren un poco.
        float pierna = s * anguloPiernas * amt * (1f - aire);
        piernaL.localRotation = rPiernaL * Quaternion.Euler(pierna - 15f * aire, 0, 0);
        piernaR.localRotation = rPiernaR * Quaternion.Euler(-pierna + 20f * aire, 0, 0);

        // --- Brazos: contrarios a las piernas. Si carga algo, se van al frente (X negativo).
        //     En el aire se levantan hacia los lados (Z).
        float brazo = -s * anguloBrazos * amt * (1f - cargar) * (1f - aire);
        float frente = -70f * cargar;
        float lados = 50f * aire * (1f - cargar);
        brazoL.localRotation = rBrazoL * Quaternion.Euler(brazo + frente, 0, -lados);
        brazoR.localRotation = rBrazoR * Quaternion.Euler(-brazo + frente, 0, lados);

        // --- Rebote al caminar (dos rebotes por ciclo → abs(sin)) + respiración en reposo.
        float bote = Mathf.Abs(s) * rebote * amt;
        transform.localPosition = posBase + Vector3.up * bote;
        float resp = Mathf.Sin(t * 2.2f) * respiracion * (1f - amt);
        cuerpo.localScale = new Vector3(escalaCuerpo.x * (1f - resp * 0.5f), escalaCuerpo.y * (1f + resp), escalaCuerpo.z * (1f - resp * 0.5f));

        // --- Cabeza: mira un poquito alrededor en reposo.
        cabeza.localRotation = rCabeza * Quaternion.Euler(Mathf.Sin(t * 0.9f) * 3f * (1f - amt), Mathf.Sin(t * 0.5f) * 12f * (1f - amt), s * 3f * amt);

        // --- Gorro: se va hacia atrás al correr y se bambolea.
        float atras = -12f * Mathf.Clamp(intensidad, 0f, 1.7f);
        gorro.localRotation = rGorro * Quaternion.Euler(atras + Mathf.Sin(fase * 2f) * 6f * amt + Mathf.Sin(t * 1.7f) * 3f, 0, Mathf.Sin(t * 1.3f) * 5f + s * 6f * amt);
    }

    Transform Buscar(string nombre)
    {
        foreach (var t in GetComponentsInChildren<Transform>(true))
            if (t.name == nombre) return t;
        Debug.LogError("ElfoAnimador: no encontré la pieza '" + nombre + "' en el modelo", this);
        return transform;
    }
}
