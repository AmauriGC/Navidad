using System.Collections;
using UnityEngine;

/// <summary>
/// LUCES DEL GRAN ÁRBOL.
///  - Mientras el árbol no está completo, los focos de la guirnalda están APAGADOS (se ven como vidrio de color).
///  - Cuando se coloca la última pieza (la estrella): se prenden COLOR POR COLOR (rojo, verde, azul, amarillo),
///    parpadean todos juntos 3 veces y luego quedan "persiguiéndose" (cada color sube y baja desfasado).
///  - La estrella hace un destello fuerte y luego late suave; se encienden luces de colores alrededor del árbol.
/// Los materiales de glTFast guardan la emisión en "emissiveFactor"; usamos .materials (copias) para no tocar otros objetos.
/// </summary>
public class LucesArbol : MonoBehaviour
{
    public ArbolNavidad arbol;
    public Renderer guirnalda;
    public Renderer estrella;
    [Tooltip("Luces de colores alrededor del árbol (empiezan apagadas).")]
    public Light[] lucesColores;
    [Range(0, 1)] public float brilloApagado = 0.04f;
    public float velocidadPersecucion = 1.6f;

    static readonly int Emision = Shader.PropertyToID("emissiveFactor");
    Material[] focos; Color[] baseFocos;
    Material[] matsEstrella; Color[] baseEstrella;
    float[] intensidadLuces;
    float[] nivel;          // 0..1 encendido de cada material de foco
    bool encendido, persiguiendo;

    void Start()
    {
        if (arbol == null) arbol = GetComponentInParent<ArbolNavidad>();
        if (guirnalda != null)
        {
            var viejo = guirnalda.GetComponent<BrilloEmisivo>();
            if (viejo != null) viejo.enabled = false;          // antes titilaba desde el principio
            focos = guirnalda.materials;
            baseFocos = new Color[focos.Length];
            nivel = new float[focos.Length];
            for (int i = 0; i < focos.Length; i++)
                baseFocos[i] = focos[i].HasProperty(Emision) ? focos[i].GetColor(Emision) : Color.black;
        }
        if (estrella != null)
        {
            matsEstrella = estrella.materials;
            baseEstrella = new Color[matsEstrella.Length];
            for (int i = 0; i < matsEstrella.Length; i++)
                baseEstrella[i] = matsEstrella[i].HasProperty(Emision) ? matsEstrella[i].GetColor(Emision) : Color.black;
        }
        if (lucesColores != null)
        {
            intensidadLuces = new float[lucesColores.Length];
            for (int i = 0; i < lucesColores.Length; i++)
                if (lucesColores[i]) { intensidadLuces[i] = lucesColores[i].intensity; lucesColores[i].intensity = 0f; lucesColores[i].enabled = false; }
        }
        Aplicar();
        if (arbol != null) arbol.AlCambiar += Revisar;
        Revisar();
    }

    void OnDestroy() { if (arbol != null) arbol.AlCambiar -= Revisar; }

    void Revisar()
    {
        if (!encendido && arbol != null && arbol.Completo) { encendido = true; StartCoroutine(Encender()); }
    }

    /// <summary>Para probar desde el editor o desde otro script.</summary>
    [ContextMenu("Encender ahora")]
    public void EncenderAhora() { if (!encendido) { encendido = true; StartCoroutine(Encender()); } }

    IEnumerator Encender()
    {
        yield return new WaitForSeconds(0.6f);
        GestorAudio.Efecto("encender", 0.8f, 0f);   // zumbido eléctrico que sube + chispitas
        // 1) color por color, con un "pop"
        for (int i = 0; i < nivel.Length; i++)
        {
            if (baseFocos[i].maxColorComponent < 0.01f) continue;     // el cable no brilla
            for (float t = 0; t < 1f; t += Time.deltaTime / 0.25f) { nivel[i] = Mathf.Lerp(brilloApagado, 1.6f, t); yield return null; }
            nivel[i] = 1f;
            GestorAudio.Efecto("colocar", 0.5f, 0.15f);
            yield return new WaitForSeconds(0.25f);
        }
        // 2) destello de la estrella y luces de colores
        StartCoroutine(Estrella());
        StartCoroutine(LucesAlrededor());
        // 3) tres parpadeos todos juntos
        for (int k = 0; k < 3; k++)
        {
            Todos(0.25f); yield return new WaitForSeconds(0.18f);
            Todos(1.3f); yield return new WaitForSeconds(0.22f);
        }
        persiguiendo = true;
    }

    void Todos(float v) { for (int i = 0; i < nivel.Length; i++) nivel[i] = v; }

    IEnumerator Estrella()
    {
        for (float t = 0; t < 1f; t += Time.deltaTime / 0.5f) { BrilloEstrella(Mathf.Lerp(1f, 6f, t)); yield return null; }
        for (float t = 0; t < 1f; t += Time.deltaTime / 1.2f) { BrilloEstrella(Mathf.Lerp(6f, 2.2f, t)); yield return null; }
        while (true) { BrilloEstrella(2.2f + 0.6f * Mathf.Sin(Time.time * 2.2f)); yield return null; }
    }

    void BrilloEstrella(float k)
    {
        if (matsEstrella == null) return;
        for (int i = 0; i < matsEstrella.Length; i++) matsEstrella[i].SetColor(Emision, baseEstrella[i] * k);
    }

    IEnumerator LucesAlrededor()
    {
        if (lucesColores == null) yield break;
        foreach (var l in lucesColores) if (l) l.enabled = true;
        for (float t = 0; t < 1f; t += Time.deltaTime / 1.5f)
        {
            for (int i = 0; i < lucesColores.Length; i++) if (lucesColores[i]) lucesColores[i].intensity = intensidadLuces[i] * t;
            yield return null;
        }
    }

    void Update()
    {
        if (persiguiendo)
        {
            float t = Time.time * velocidadPersecucion;
            for (int i = 0; i < nivel.Length; i++)
                nivel[i] = Mathf.Lerp(0.45f, 1.25f, 0.5f + 0.5f * Mathf.Sin((t - i * 0.5f) * Mathf.PI));
            if (lucesColores != null)
                for (int i = 0; i < lucesColores.Length; i++)
                    if (lucesColores[i]) lucesColores[i].intensity = intensidadLuces[i] * (0.75f + 0.25f * Mathf.Sin((t - i * 0.5f) * Mathf.PI));
        }
        Aplicar();
    }

    void Aplicar()
    {
        if (focos == null) return;
        for (int i = 0; i < focos.Length; i++)
            focos[i].SetColor(Emision, baseFocos[i] * (encendido ? nivel[i] : brilloApagado));
    }
}
