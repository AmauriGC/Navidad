using UnityEngine;

/// <summary>
/// VARIEDAD DE CASCANUECES: el mismo modelo y la misma IA, pero cada tipo tiene otros colores y otras "estadísticas".
///  - Soldado   : rojo y azul (el normal).
///  - Explorador: chaqueta verde; RÁPIDO al perseguir pero ve menos lejos (puedes esconderte más fácil).
///  - Capitán   : azul rey con dorado y más grande; lento, pero ve MUY lejos, con ángulo amplio y oye mejor.
/// Los colores se cambian con MaterialPropertyBlock (no crea materiales nuevos) solo en los materiales de la ropa.
/// Corre antes que Cascanueces (DefaultExecutionOrder) para que la IA ya use los valores nuevos.
/// </summary>
[DefaultExecutionOrder(-50)]
[ExecuteAlways]
public class VarianteCascanueces : MonoBehaviour
{
    public enum Tipo { Soldado, Explorador, Capitan, Nevado }   // Nevado = el que lanza bolas afuera (Difícil/Imposible)
    public Tipo tipo = Tipo.Soldado;

    static readonly int BaseColorFactor = Shader.PropertyToID("baseColorFactor");
    static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

    void Awake()
    {
        if (!Application.isPlaying) return;
        var c = GetComponent<Cascanueces>();
        if (c == null) return;
        switch (tipo)
        {
            case Tipo.Explorador:
                c.nombre = "Cascanueces explorador";
                c.velocidadPatrulla *= 1.3f; c.velocidadPersecucion *= 1.25f;
                c.distanciaVision *= 0.75f; c.anguloVision *= 0.85f;
                break;
            case Tipo.Capitan:
                c.nombre = "Capitán cascanueces";
                c.velocidadPatrulla *= 0.85f; c.velocidadPersecucion *= 0.85f;
                c.distanciaVision *= 1.4f; c.anguloVision = Mathf.Min(170f, c.anguloVision * 1.25f);
                c.distanciaOido *= 1.4f;
                break;
        }
    }

    void OnEnable() { Pintar(); }
    void OnValidate() { Pintar(); }

    void Pintar()
    {
        Color chaqueta, pantalon;
        switch (tipo)
        {
            case Tipo.Explorador: chaqueta = new Color(0.08f, 0.45f, 0.18f); pantalon = new Color(0.35f, 0.22f, 0.1f); break;
            case Tipo.Capitan: chaqueta = new Color(0.1f, 0.18f, 0.65f); pantalon = new Color(0.95f, 0.95f, 0.92f); break;
            case Tipo.Nevado: chaqueta = new Color(0.9f, 0.94f, 1f); pantalon = new Color(0.3f, 0.58f, 0.92f); break;
            default: chaqueta = new Color(0.7f, 0.05f, 0.06f); pantalon = new Color(0.08f, 0.12f, 0.45f); break;
        }
        var bloque = new MaterialPropertyBlock();
        foreach (var r in GetComponentsInChildren<Renderer>(true))
        {
            var mats = r.sharedMaterials;
            for (int i = 0; i < mats.Length; i++)
            {
                if (mats[i] == null) continue;
                string n = mats[i].name;
                bool esChaqueta = n.StartsWith("Cas_Rojo"), esPantalon = n.StartsWith("Cas_Azul");
                r.GetPropertyBlock(bloque, i);
                if (tipo == Tipo.Soldado || !(esChaqueta || esPantalon)) { bloque.Clear(); r.SetPropertyBlock(bloque, i); continue; }
                Color col = esChaqueta ? chaqueta : pantalon;
                bloque.SetColor(BaseColorFactor, col); bloque.SetColor(BaseColor, col);
                r.SetPropertyBlock(bloque, i);
            }
        }
    }
}
