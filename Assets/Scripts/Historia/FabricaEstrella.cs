using System.Collections;
using UnityEngine;

/// <summary>
/// FABRICAR LA ESTRELLA NUEVA (historia 1.5). Va en la Máquina 7 (Siete).
///  - Siete enferma: [E] Revisar -> "está enferma: cúrala en el cuarto de máquinas".
///  - Curada y sin la estrella rota: te dice que se la traigas (está arriba de la repisa del oeste).
///  - Curada y con la estrella rota en la mano: [E] Fabricar ->
///      1) Tilo: "Aquí va la estrella rota... ¡la palanca!" (Guion.JalarPalanca)
///      2) la estrella rota vuela al embudo y desaparece; Siete jala su palanca; chispas doradas
///      3) por la boca de la máquina sale la ESTRELLA NUEVA (prefab Pieza_Estrella) y brinca al piso
///      4) se completa la etapa "FabricarEstrella" del árbol (ArbolNavidad.CompletarExterna).
/// </summary>
public class FabricaEstrella : Interactuable
{
    public const string Etapa = "FabricarEstrella";

    public string tipoRota = "EstrellaRota";
    public GameObject prefabEstrella;
    [Tooltip("Por dónde entra la estrella rota (el embudo de arriba).")]
    public Transform embudo;
    [Tooltip("Por dónde sale la estrella nueva (la boca sobre la banda).")]
    public Transform salida;
    [Tooltip("Dónde cae la estrella nueva (en el piso, enfrente de Siete).")]
    public Vector3 aterrizaje = new Vector3(7.0f, 0.5f, 4.2f);
    public ParticleSystem chispas;

    public static bool Fabricada { get; private set; }
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Fabricada = false; }

    bool ocupada;

    void Awake() { Fabricada = false; }

    Recogible Rota(Interactor quien)
    {
        var r = quien.Inventario != null ? quien.Inventario.EnMano : null;
        return r != null && r.tipo == tipoRota ? r : null;
    }

    public override bool PuedeInteractuar(Interactor quien) { return !Fabricada && !ocupada; }

    public override string Texto(Interactor quien)
    {
        var a = ArbolNavidad.Instancia;
        bool toca = a == null || a.Completo || a.EtapaActual.tipoPieza == Etapa;
        if (MaquinaRota.Reparada && toca && Rota(quien) != null) return "Fabricar una estrella nueva";
        return "Revisar a Siete";
    }

    public override void Interactuar(Interactor quien)
    {
        if (!MaquinaRota.Reparada)
        {
            UIAviso.Mensaje("Siete está enferma: da descargas y no puede trabajar.\nCura su corazón en el cuarto de máquinas (la puerta de al lado).", 5.5f);
            return;
        }
        var r = Rota(quien);
        var arbol = ArbolNavidad.Instancia;
        if (arbol != null && !arbol.Completo && arbol.EtapaActual.tipoPieza != Etapa)
        {
            // solo se fabrica en su etapa: antes, la historia todavía no llega ahí
            UIAviso.Mensaje("Siete está lista para trabajar... pero primero termina el Gran Árbol.\nFalta: " + arbol.EtapaActual.nombre.ToLower() + ".", 5f);
            return;
        }
        if (r == null)
        {
            UIAviso.Mensaje("Siete puede hacer una estrella nueva...\nsi le traes la estrella rota (quedó arriba de la repisa del oeste).", 5f);
            return;
        }
        quien.Inventario.Entregar();
        StartCoroutine(Fabricar(r));
    }

    IEnumerator Fabricar(Recogible r)
    {
        ocupada = true;
        yield return UIHistoria.Esperar(Guion.JalarPalanca);
        var antes = Juego.Estado;
        Juego.Estado = Juego.Modo.Cinematica;
        // 1) la estrella rota vuela al embudo
        Transform t = r.transform; t.SetParent(null, true);
        Vector3 a = t.position, b = embudo != null ? embudo.position : transform.position + Vector3.up * 3f;
        Vector3 esc = t.localScale;
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.8f)
        {
            t.position = Vector3.Lerp(a, b, k) + Vector3.up * Mathf.Sin(k * Mathf.PI) * 1.2f;
            t.Rotate(0f, 540f * Time.deltaTime, 0f);
            t.localScale = esc * (1f - k * 0.6f);
            yield return null;
        }
        r.Consumir();
        GestorAudio.Efecto3D("instalar", b, 0.9f);
        // 2) la palanca, la máquina zumba bonito y echa chispas doradas
        if (Siete.Instancia != null) StartCoroutine(Siete.Instancia.JalarPalanca());
        yield return new WaitForSeconds(0.45f);
        GestorAudio.Efecto("fabricar", 0.9f, 0f);
        TemblorCamara.Sacudir(0.2f);
        for (int i = 0; i < 6; i++) { if (chispas != null) chispas.Emit(18); yield return new WaitForSeconds(0.25f); }
        // 3) ¡sale la estrella nueva!
        Vector3 p = salida != null ? salida.position : transform.position + Vector3.up;
        GameObject nueva = prefabEstrella != null ? Instantiate(prefabEstrella, p, Quaternion.identity) : null;
        if (nueva != null)
        {
            var rec = nueva.GetComponent<Recogible>();
            if (rec != null) rec.Liberar(aterrizaje, 1.4f, 0.9f);
        }
        GestorAudio.Efecto("etapa", 1f, 0f);
        yield return new WaitForSeconds(1.0f);
        Fabricada = true;
        ocupada = false;
        Juego.Estado = antes == Juego.Modo.Cinematica ? Juego.Modo.Jugando : antes;
        if (ArbolNavidad.Instancia != null) ArbolNavidad.Instancia.CompletarExterna(Etapa);
    }
}
