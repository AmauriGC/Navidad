using UnityEngine;

/// <summary>
/// Anima la EMISIÓN (el brillo propio) de los materiales de un objeto.
///  - Modo Titilar: cada material sube y baja desfasado (guirnaldas de focos).
///  - Modo Alerta: prende y apaga como sirena (luz roja de la máquina descompuesta).
/// Opcionalmente sincroniza una Light con el mismo ritmo.
/// Los materiales de glTFast guardan la emisión en la propiedad "emissiveFactor".
/// </summary>
public class BrilloEmisivo : MonoBehaviour
{
    public enum Modo { Titilar, Alerta }
    public Modo modo = Modo.Titilar;
    public float velocidad = 1.5f;
    [Range(0, 1)] public float minimo = 0.25f;
    public Light luzSincronizada;

    static readonly int[] Props = { Shader.PropertyToID("emissiveFactor"), Shader.PropertyToID("_EmissionColor") };
    Material[] mats; Color[] colorBase; int prop; float luzBase;

    void Start()
    {
        var r = GetComponent<Renderer>();
        mats = r.materials;   // .materials crea copias: así no cambiamos los materiales de otros objetos
        prop = Props[0];
        foreach (var p in Props) if (mats[0].HasProperty(p)) { prop = p; break; }
        colorBase = new Color[mats.Length];
        for (int i = 0; i < mats.Length; i++) colorBase[i] = mats[i].HasProperty(prop) ? mats[i].GetColor(prop) : Color.black;
        if (luzSincronizada) luzBase = luzSincronizada.intensity;
    }

    /// <summary>Cambia el color del brillo (conserva la fuerza original). La usa MaquinaRota: rojo -> verde.</summary>
    public void CambiarColor(Color c)
    {
        if (mats == null) Start();
        for (int i = 0; i < mats.Length; i++)
        {
            float f = Mathf.Max(colorBase[i].r, Mathf.Max(colorBase[i].g, colorBase[i].b));
            colorBase[i] = c * f;
        }
        if (luzSincronizada) luzSincronizada.color = c;
    }

    void Update()
    {
        float t = Time.time * velocidad;
        float k0 = 1f;
        for (int i = 0; i < mats.Length; i++)
        {
            float k;
            if (modo == Modo.Titilar) k = Mathf.Lerp(minimo, 1f, 0.5f + 0.5f * Mathf.Sin(t * Mathf.PI + i * 1.7f));
            else k = Mathf.Repeat(t, 1f) < 0.5f ? 1f : minimo;
            if (i == 0) k0 = k;
            mats[i].SetColor(prop, colorBase[i] * k);
        }
        if (luzSincronizada) luzSincronizada.intensity = luzBase * k0;
    }
}
