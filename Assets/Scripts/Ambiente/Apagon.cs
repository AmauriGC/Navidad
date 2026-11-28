using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// APAGÓN DE LAS 3:00 AM (Difícil / Imposible): si a esa hora la Máquina 7 sigue descompuesta, su sobrecarga tumba la luz.
///  - Las lámparas del taller y del establo y el foco del árbol parpadean y se apagan; también se apagan los focos
///    de las lámparas, las guirnaldas y la pantalla de la máquina (su brillo/emisión).
///  - La CHIMENEA sigue (es fuego) y afuera siguen los faroles: ahí también recargas la linterna.
///  - Dura 'duracion' segundos (60). Si reparas la Máquina 7 durante el apagón, la luz regresa en ese momento.
///  - A oscuras los cascanueces ven menos (FactorVision 0.8).
///  - Si la Máquina 7 ya estaba reparada a las 3:00: no hay apagón y sale un mensaje de premio.
/// Dificultad.Aplicar() lo crea solo en los niveles que lo usan.
/// </summary>
public class Apagon : MonoBehaviour
{
    public static bool Activo { get; private set; }
    /// <summary>Multiplica la distancia de vista de los cascanueces (lo usa Cascanueces).</summary>
    public static float FactorVision => Activo ? 0.8f : 1f;

    public float progresoHora = 0.625f;   // 3:00 AM = 5 de las 8 horas de la noche (10 PM → 6 AM)
    public float duracion = 60f;

    RelojAmanecer reloj; bool yaPaso;
    readonly List<Light> luces = new List<Light>(); readonly List<float> intensidades = new List<float>();
    readonly List<Renderer> brillantes = new List<Renderer>();
    static readonly int Emision = Shader.PropertyToID("emissiveFactor");

    void Start()
    {
        reloj = FindAnyObjectByType<RelojAmanecer>();
        foreach (var l in FindObjectsByType<Light>())
        {
            string n = l.name;
            if (n.StartsWith("Luz_Taller") || n.StartsWith("Luz_Establo") || n.StartsWith("Luz_Foco_Arbol")) { luces.Add(l); intensidades.Add(l.intensity); }
        }
        foreach (var r in FindObjectsByType<MeshRenderer>())
        {
            string n = r.name;
            if (n == "Lamparas" || n == "Guirnaldas_Focos" || n == "Guirnaldas" || n == "Maquina") brillantes.Add(r);
        }
    }

    void Update()
    {
        if (yaPaso || reloj == null || Juego.Estado != Juego.Modo.Jugando) return;
        if (reloj.Progreso < progresoHora) return;
        yaPaso = true;
        if (MaquinaRota.Reparada)
        {
            UIAviso.Mensaje("Son las 3:00 AM... la luz parpadea, ¡pero la Máquina 7 reparada aguantó!\nGracias a ti no hubo apagón.", 5f);
            GestorAudio.Efecto("reparada", 0.5f, 0f);
        }
        else StartCoroutine(Corte());
    }

    IEnumerator Corte()
    {
        GestorAudio.Efecto("apagon", 1f, 0f);
        TemblorCamara.Sacudir(0.2f);
        if (DescargaMaquina.Instancia != null) DescargaMaquina.Instancia.Disparar();   // historia 1.5: la descarga más grande (cuenta)
        // parpadeo antes de apagarse
        for (float t = 0f; t < 1.4f; t += 0.07f) { Poner(Random.value < 0.45f ? 1f : 0.05f); yield return new WaitForSeconds(0.07f); }
        Poner(0f); Activo = true;
        UIAviso.Mensaje("¡APAGÓN! La descarga más grande de Siete tumbó la luz del taller.\nLa chimenea y los faroles siguen prendidos... y los cascanueces ven menos.", 5f);
        float fin = Time.time + duracion;
        while (Time.time < fin && !MaquinaRota.Reparada)
        {
            if (Juego.Estado == Juego.Modo.Jugando || Juego.Estado == Juego.Modo.Pausa) { }
            else fin += Time.deltaTime;   // en diálogos/cinemáticas no corre el tiempo del apagón
            yield return null;
        }
        // regresa la luz (con parpadeo)
        GestorAudio.Efecto("luz_vuelve", 1f, 0f);
        for (float t = 0f; t < 1f; t += 0.08f) { Poner(Random.value < 0.6f ? 1f : 0.1f); yield return new WaitForSeconds(0.08f); }
        Poner(1f); Activo = false;
        UIAviso.Mensaje(MaquinaRota.Reparada ? "¡Reparaste la Máquina 7 y volvió la luz!" : "¡Volvió la luz!", 3f);
    }

    /// <summary>k = 1 luz normal, 0 apagado. Las luces bajan su intensidad; los focos pierden su brillo (emisión).</summary>
    void Poner(float k)
    {
        for (int i = 0; i < luces.Count; i++) if (luces[i] != null) luces[i].intensity = intensidades[i] * k;
        var bloque = new MaterialPropertyBlock();
        foreach (var r in brillantes)
        {
            if (r == null) continue;
            var mats = r.sharedMaterials;
            for (int i = 0; i < mats.Length; i++)
            {
                if (k >= 0.99f) { bloque.Clear(); r.SetPropertyBlock(bloque, i); continue; }   // sin bloque = brillo normal
                if (mats[i] == null || !mats[i].HasProperty(Emision)) continue;
                bloque.Clear();
                bloque.SetColor(Emision, mats[i].GetColor(Emision) * k);
                r.SetPropertyBlock(bloque, i);
            }
        }
    }

    void OnDestroy() { Activo = false; }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Activo = false; }
}
