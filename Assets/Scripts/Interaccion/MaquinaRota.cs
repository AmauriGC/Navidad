using System.Collections;
using UnityEngine;

/// <summary>
/// EL CORAZÓN DE SIETE (historia 1.5) — antes "Máquina 7 descompuesta" opcional; ahora es OBLIGATORIO.
/// Va en el motor del cuarto de máquinas (atrás de Siete). Le faltan 3 refacciones: engrane, resorte y fusible.
///  - Sin refacción en la mano: [E] Revisar -> dice cuáles faltan y dónde buscarlas.
///  - Con una refacción: [E] Instalar -> la pieza vuela a SU lugar en el motor y aparece puesta ahí;
///    en la cara de Siete se prende su foco verde (Siete.Instalada).
///  - Con las 3: Siete se CURA: se apagan las chispas, la luz de alerta pasa a verde, ya no hay descargas,
///    los cascanueces se calman y se completa la etapa "CurarSiete" del árbol (ArbolNavidad.CompletarExterna).
///    Si la curas antes de llegar a esa etapa, el DirectorJuego la da por buena en cuanto el árbol llegue ahí.
/// Es otro hijo de Interactuable (igual que RenoGuirnalda), así el Interactor lo detecta solo.
/// (Se llama MaquinaRota por compatibilidad: muchos scripts preguntan MaquinaRota.Reparada.)
/// </summary>
public class MaquinaRota : Interactuable
{
    public const string Etapa = "CurarSiete";

    public string tipoRefaccion = "Refaccion";
    public string[] faltan = { "engrane", "resorte", "fusible" };
    [Tooltip("A dónde vuela cada refacción (mismo orden que 'faltan'). Si falta, vuela a 'boca'.")]
    public Transform[] destinos;
    public ParticleSystem chispas;
    public BrilloEmisivo luzAlerta;
    public Light luzRoja;
    public Transform boca;

    public static bool Reparada { get; private set; }
    public static int Instaladas { get; private set; }
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Reparada = false; Instaladas = 0; }

    bool[] puesta;

    void Awake()
    {
        Reparada = false; Instaladas = 0;
        puesta = new bool[faltan.Length];
        if (boca == null) boca = transform;
    }

    Recogible Refaccion(Interactor quien)
    {
        var r = quien.Inventario != null ? quien.Inventario.EnMano : null;
        return r != null && r.tipo == tipoRefaccion ? r : null;
    }

    public override bool PuedeInteractuar(Interactor quien) { return !Reparada && Instaladas < faltan.Length; }

    public override string Texto(Interactor quien)
    {
        var r = Refaccion(quien);
        return r != null ? "Instalar " + r.nombreVisible + " (" + (Instaladas + 1) + "/" + faltan.Length + ")" : "Revisar el corazón de Siete";
    }

    public override void Interactuar(Interactor quien)
    {
        var r = Refaccion(quien);
        if (r == null)
        {
            string lista = "";
            for (int i = 0; i < faltan.Length; i++) if (!puesta[i]) lista += (lista == "" ? "" : ", ") + faltan[i];
            UIAviso.Mensaje("El corazón de Siete está fallando: por eso da descargas.\nLe falta: " + lista + ".\n" +
                            "<size=24>(El engrane quedó en lo alto de la repisa del oeste, el resorte en el establo y el fusible en el patio.)</size>", 7f);
            return;
        }
        quien.Inventario.Entregar();
        int indice = 0;
        for (int i = 0; i < faltan.Length; i++) if (!puesta[i] && faltan[i] == r.nombreVisible) { indice = i; break; }
        if (puesta[indice]) for (int i = 0; i < faltan.Length; i++) if (!puesta[i]) { indice = i; break; }   // por si el nombre no coincide
        puesta[indice] = true;
        Instaladas++;
        StartCoroutine(Instalar(r, indice, Instaladas));
    }

    IEnumerator Instalar(Recogible r, int indice, int numero)
    {
        // la refacción vuela en arco hasta su lugar en el motor y se encoge
        Transform destino = destinos != null && indice < destinos.Length && destinos[indice] != null ? destinos[indice] : boca;
        Transform t = r.transform; t.SetParent(null, true);
        Vector3 a = t.position, b = destino.position; Vector3 esc = t.localScale;
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.6f)
        {
            t.position = Vector3.Lerp(a, b, k) + Vector3.up * Mathf.Sin(k * Mathf.PI) * 0.8f;
            t.Rotate(0f, 720f * Time.deltaTime, 0f);
            t.localScale = esc * (1f - k * 0.8f);
            yield return null;
        }
        r.Consumir();
        if (Siete.Instancia != null) Siete.Instancia.Instalada(indice);   // aparece puesta en el motor + foco verde
        GestorAudio.Efecto3D("instalar", b, 1f);
        TemblorCamara.Sacudir(0.12f);
        if (numero < faltan.Length)
        {
            UIAviso.Mensaje("¡" + Mayus(faltan[indice]) + " instalado! " + numero + "/" + faltan.Length, 3f);
            if (chispas != null) chispas.Emit(25);
            yield break;
        }
        yield return Reparar();
    }

    static string Mayus(string s) { return string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s.Substring(1); }

    IEnumerator Reparar()
    {
        if (Reparada) yield break;   // solo una vez
        Reparada = true;
        if (chispas != null) { chispas.Emit(60); chispas.Stop(true, ParticleSystemStopBehavior.StopEmitting); }
        yield return new WaitForSeconds(0.5f);
        if (luzAlerta != null) { luzAlerta.modo = BrilloEmisivo.Modo.Titilar; luzAlerta.velocidad = 0.5f; luzAlerta.minimo = 0.6f; luzAlerta.CambiarColor(new Color(0.25f, 1f, 0.35f)); }
        else if (luzRoja != null) luzRoja.color = new Color(0.25f, 1f, 0.35f);
        if (Siete.Instancia != null) Siete.Instancia.Curar();
        GestorAudio.Efecto("reparada", 0.9f, 0f);
        GestorAudio.Efecto("melodia_siete", 0.8f, 0f);   // la cajita musical de las gracias (historia 1.5)
        GestorAudio.MaquinaReparada();
        foreach (var c in FindObjectsByType<Cascanueces>()) c.Calmar();
        // la etapa del árbol: si todavía no toca, el DirectorJuego la completa al llegar a ella
        if (ArbolNavidad.Instancia == null || !ArbolNavidad.Instancia.CompletarExterna(Etapa))
            UIAviso.Mensaje("¡CURASTE A SIETE!\nYa no da descargas y los cascanueces se calman.", 5f);
    }
}
