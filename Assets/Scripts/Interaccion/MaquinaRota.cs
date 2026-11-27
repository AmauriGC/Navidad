using System.Collections;
using UnityEngine;

/// <summary>
/// MISIÓN OPCIONAL — LA MÁQUINA 7 DESCOMPUESTA.
/// Le faltan 3 refacciones (Engrane, Resorte, Llave) que están tiradas por el taller, el establo y el patio.
///  - Sin refacción en la mano: [E] Revisar -> dice cuáles faltan.
///  - Con una refacción: [E] Instalar -> la pieza vuela a la máquina, se encoge y desaparece (Recogible.Consumir).
///  - Con las 3: la máquina se REPARA: se apagan las chispas, la luz de alerta pasa de rojo a verde y parpadea
///    tranquila, el ruido baja... y los cascanueces se CALMAN (Cascanueces.Calmar: más lentos, ven y oyen menos).
/// Es otro hijo de Interactuable (igual que RenoGuirnalda), así el Interactor lo detecta solo.
/// </summary>
public class MaquinaRota : Interactuable
{
    public string tipoRefaccion = "Refaccion";
    public string[] faltan = { "engrane", "resorte", "llave inglesa" };
    public ParticleSystem chispas;
    public BrilloEmisivo luzAlerta;
    public Light luzRoja;
    public Transform boca;              // a dónde vuela la refacción al instalarla

    public static bool Reparada { get; private set; }
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Reparada = false; }

    int instaladas;
    bool[] puesta;

    void Awake()
    {
        Reparada = false;
        puesta = new bool[faltan.Length];
        if (boca == null) boca = transform;
    }

    Recogible Refaccion(Interactor quien)
    {
        var r = quien.Inventario != null ? quien.Inventario.EnMano : null;
        return r != null && r.tipo == tipoRefaccion ? r : null;
    }

    public override bool PuedeInteractuar(Interactor quien) { return !Reparada && instaladas < faltan.Length; }

    public override string Texto(Interactor quien)
    {
        var r = Refaccion(quien);
        return r != null ? "Instalar " + r.nombreVisible + " (" + (instaladas + 1) + "/" + faltan.Length + ")" : "Revisar la Máquina 7";
    }

    public override void Interactuar(Interactor quien)
    {
        var r = Refaccion(quien);
        if (r == null)
        {
            string lista = "";
            for (int i = 0; i < faltan.Length; i++) if (!puesta[i]) lista += (lista == "" ? "" : ", ") + faltan[i];
            UIAviso.Mensaje("La Máquina 7 está descompuesta: echa chispas y hace un ruidazo\nque mantiene despiertos a los cascanueces.\nLe falta: " + lista + ". (Búscalos por el taller, el establo y el patio)", 6f);
            return;
        }
        quien.Inventario.Entregar();
        for (int i = 0; i < faltan.Length; i++) if (!puesta[i] && faltan[i] == r.nombreVisible) { puesta[i] = true; break; }
        instaladas++;
        StartCoroutine(Instalar(r, instaladas));
    }

    IEnumerator Instalar(Recogible r, int numero)
    {
        // la refacción vuela en arco hasta la boca de la máquina y se encoge
        Transform t = r.transform; t.SetParent(null, true);
        Vector3 a = t.position, b = boca.position; Vector3 esc = t.localScale;
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.6f)
        {
            t.position = Vector3.Lerp(a, b, k) + Vector3.up * Mathf.Sin(k * Mathf.PI) * 0.8f;
            t.Rotate(0f, 720f * Time.deltaTime, 0f);
            t.localScale = esc * (1f - k * 0.8f);
            yield return null;
        }
        r.Consumir();
        GestorAudio.Efecto3D("instalar", b, 1f);   // matraca + golpe metálico
        TemblorCamara.Sacudir(0.12f);
        if (numero < faltan.Length)
        {
            UIAviso.Mensaje("¡Refacción instalada! " + numero + "/" + faltan.Length, 3f);
            if (chispas != null) chispas.Emit(25);
            yield break;
        }
        yield return Reparar();
    }

    IEnumerator Reparar()
    {
        if (Reparada) yield break;   // solo una vez
        Reparada = true;
        if (chispas != null) { chispas.Emit(60); chispas.Stop(true, ParticleSystemStopBehavior.StopEmitting); }
        yield return new WaitForSeconds(0.5f);
        if (luzAlerta != null) { luzAlerta.modo = BrilloEmisivo.Modo.Titilar; luzAlerta.velocidad = 0.5f; luzAlerta.minimo = 0.6f; luzAlerta.CambiarColor(new Color(0.25f, 1f, 0.35f)); }
        else if (luzRoja != null) luzRoja.color = new Color(0.25f, 1f, 0.35f);
        GestorAudio.Efecto("reparada", 0.9f, 0f);  // el motor se apaga + campanita de listo
        GestorAudio.MaquinaReparada();
        foreach (var c in FindObjectsByType<Cascanueces>()) c.Calmar();
        UIAviso.Mensaje("¡REPARASTE LA MÁQUINA 7!\nYa no hace ruido: los cascanueces se calman (son más lentos y ven menos).", 6f);
    }
}
