using UnityEngine;

/// <summary>
/// CAJA SORPRESA (trampa de Difícil / Imposible): caja de juguete con payaso de resorte (CajaSorpresa.glb).
///  - Si pasas CERCA, la caja se abre: la tapa se avienta, el resorte se estira con rebote y el payaso se tambalea.
///    Caminando tienes que pasar MUY cerca para activarla (radioCaminando); corriendo basta con pasar a 'radioCorriendo'.
///    => Se esquivan viéndolas a tiempo y rodeándolas (o pasando despacio y con cuidado).
///  - ¡BOING! El ruido llega a 'radioRuido' metros: los cascanueces DESPIERTOS que lo oyen corren a ver qué pasó
///    (Cascanueces.OirRuido: van al lugar del ruido; si no te ven ahí, regresan a patrullar).
///  - Después de 'cerrarTras' segundos el payaso se guarda y la tapa se cierra; a los 'rearme' segundos vuelve a funcionar.
/// Las piezas se animan por separado gracias a sus pivotes (hechos en Blender, ver Blender/caja_sorpresa.py):
///  Caja_Tapa gira en X desde la bisagra, Caja_Resorte se escala en Y, Caja_Payaso se sube encima del resorte.
/// Dificultad.Aplicar() prende solo las primeras N cajas (Difícil 5, Imposible 8); en Fácil/Medio están apagadas.
/// </summary>
public class CajaSorpresa : MonoBehaviour
{
    public float radioCaminando = 1.0f, radioCorriendo = 2.3f, radioRuido = 20f;
    public float cerrarTras = 6f, rearme = 18f;
    public Transform tapa, resorte, payaso;
    [Tooltip("Historia 1.5: la caja que cuida el fusible está prendida en TODAS las dificultades (Dificultad no la apaga).")]
    public bool siempreActiva;

    const float Aplastado = 0.12f, LargoResorte = 0.5f;
    Transform jugador; ElfoController elfo;
    float abiertaDesde = -999f;
    Vector3 posResorte; Quaternion rotTapa0, rotPayaso0;
    static bool explicado;

    void Awake()
    {
        if (tapa == null) tapa = Buscar("Caja_Tapa");
        if (resorte == null) resorte = Buscar("Caja_Resorte");
        if (payaso == null) payaso = Buscar("Caja_Payaso");
        if (resorte != null) posResorte = resorte.localPosition;
        if (tapa != null) rotTapa0 = tapa.localRotation;
        if (payaso != null) rotPayaso0 = payaso.localRotation;
        Poner(0f, 0f);
    }

    Transform Buscar(string n)
    {
        foreach (var t in GetComponentsInChildren<Transform>(true)) if (t.name == n) return t;
        return null;
    }

    void Start()
    {
        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { jugador = j.transform; elfo = j.GetComponent<ElfoController>(); }
    }

    bool Abierta => Time.time - abiertaDesde < rearme;

    void Update()
    {
        float t = Time.time - abiertaDesde;
        if (t < cerrarTras + 1.5f) Animar(t);

        if (jugador == null || Juego.Estado != Juego.Modo.Jugando || Abierta) return;
        Vector3 d = jugador.position - transform.position; d.y = 0f;
        float radio = elfo != null && elfo.Corriendo ? radioCorriendo : radioCaminando;
        if (d.sqrMagnitude < radio * radio && Mathf.Abs(jugador.position.y - transform.position.y) < 1.5f) Saltar();
    }

    /// <summary>¡BOING!</summary>
    public void Saltar()
    {
        abiertaDesde = Time.time;
        GestorAudio.Efecto3D("boing", transform.position + Vector3.up * 0.5f, 1f, 0.05f);
        GestorAudio.Efecto("boing", 0.35f, 0.05f);      // también 2D: que se oiga fuerte aunque la cámara esté lejos
        TemblorCamara.Sacudir(0.2f);
        int cuantos = 0;
        foreach (var c in FindObjectsByType<Cascanueces>())
            if (c.OirRuido(transform.position, radioRuido)) cuantos++;
        string extra = cuantos == 0 ? "Uf... parece que nadie lo oyó." : cuantos == 1 ? "¡Un cascanueces lo oyó y viene para acá!" : "¡" + cuantos + " cascanueces lo oyeron y vienen para acá!";
        UIAviso.Mensaje(explicado ? "¡BOING!  " + extra
                                  : "¡BOING! Una CAJA SORPRESA... " + extra + "\nFíjate en el piso y rodéalas: si corres cerca, saltan antes.", explicado ? 2.5f : 5f);
        explicado = true;
    }

    void Animar(float t)
    {
        if (t < 0f) return;
        float abrir;      // 0 cerrada, 1 abierta (tapa y resorte)
        if (t < cerrarTras)
        {
            // resorte con rebote: 1 - e^(-5t)·cos(16t) (sube, se pasa, regresa, se pasa menos...)
            abrir = 1f - Mathf.Exp(-5f * t) * Mathf.Cos(16f * t);
        }
        else abrir = Mathf.SmoothStep(1f, 0f, (t - cerrarTras) / 1.5f);   // se guarda despacito
        float tapaK = t < cerrarTras ? Mathf.Clamp01(t / 0.1f) : abrir;
        Poner(abrir, tapaK);
        if (payaso != null)
        {
            float tambaleo = t < cerrarTras ? Mathf.Sin(t * 9f) * 18f * Mathf.Exp(-t * 0.6f) : 0f;
            payaso.localRotation = rotPayaso0 * Quaternion.Euler(tambaleo * 0.4f, 0f, tambaleo);
        }
    }

    /// <summary>k = estiramiento del resorte (0 aplastado .. 1 estirado, puede pasarse un poco), tapaK = 0 cerrada .. 1 abierta.</summary>
    void Poner(float k, float tapaK)
    {
        float s = Mathf.LerpUnclamped(Aplastado, 1f, k);
        if (resorte != null) resorte.localScale = new Vector3(1f, Mathf.Max(0.05f, s), 1f);
        if (payaso != null) payaso.localPosition = posResorte + Vector3.up * LargoResorte * Mathf.Max(0.05f, s);
        if (tapa != null) tapa.localRotation = rotTapa0 * Quaternion.Euler(-115f * Mathf.Clamp01(tapaK), 0f, 0f);
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { explicado = false; }
}
