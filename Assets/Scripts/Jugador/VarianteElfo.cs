using UnityEngine;

/// <summary>
/// LOS 3 ELFOS: todos usan el MISMO cuerpo (mismas piezas y pivotes, así ElfoAnimador los anima igual).
/// Cada uno cambia:
///   1) COLORES de la ropa con MaterialPropertyBlock (como VarianteCascanueces: no crea materiales nuevos);
///   2) ACCESORIOS: piezas modeladas en Blender que se llaman "Acc_&lt;Nombre&gt;_..." (trenzas, lentes, bufanda...).
///      Solo se prenden los del elfo elegido;
///   3) PIEZAS OCULTAS: p. ej. Nieves cambia el cascabel del gorro por un pompón.
/// La elección se guarda en PlayerPrefs ("Elfo") para la siguiente partida.
/// ELFO SECRETO: Jengibre (secreto = true) se desbloquea al juntar las 10 galletas (PlayerPrefs "ElfoSecreto").
/// Mientras está bloqueado, en el menú se ve como SILUETA negra con "???".
/// </summary>
[DefaultExecutionOrder(-60)]
public class VarianteElfo : MonoBehaviour
{
    [System.Serializable]
    public class Datos
    {
        public string nombre, descripcion;
        public bool esElfa, secreto;
        public Color tunica, gorro, zapatos, blanco, oro;
        public string[] ocultar;
    }

    public static readonly Datos[] Elfos =
    {
        new Datos { nombre = "Tilo", descripcion = "El clásico del turno de noche.\nNunca suelta su cascabel dorado.",
            tunica = new Color(0.13f, 0.5f, 0.22f), gorro = new Color(0.78f, 0.1f, 0.12f), zapatos = new Color(0.07f, 0.28f, 0.13f),
            blanco = new Color(0.95f, 0.95f, 0.95f), oro = new Color(1f, 0.78f, 0.25f), ocultar = new string[0] },
        new Datos { nombre = "Nieves", esElfa = true, descripcion = "Trenzas de canela y un pompón esponjado.\nLa más rápida envolviendo regalos.",
            tunica = new Color(0.26f, 0.66f, 0.8f), gorro = new Color(0.96f, 0.52f, 0.72f), zapatos = new Color(0.15f, 0.27f, 0.52f),
            blanco = new Color(0.97f, 0.97f, 1f), oro = new Color(0.82f, 0.86f, 0.95f), ocultar = new[] { "Cascabel" } },
        new Datos { nombre = "Chispa", descripcion = "Inventor del taller: lentes, bufanda\ny un copete que nunca se peina.",
            tunica = new Color(0.42f, 0.24f, 0.64f), gorro = new Color(0.97f, 0.58f, 0.15f), zapatos = new Color(0.36f, 0.21f, 0.12f),
            blanco = new Color(1f, 0.93f, 0.76f), oro = new Color(1f, 0.78f, 0.25f), ocultar = new string[0] },
        new Datos { nombre = "Jengibre", secreto = true, descripcion = "¡Elfo secreto! Traje de galleta, glaseado\ny botones de gomita. Huele a canela.",
            tunica = new Color(0.58f, 0.3f, 0.11f), gorro = new Color(0.86f, 0.12f, 0.16f), zapatos = new Color(0.3f, 0.14f, 0.05f),
            blanco = new Color(1f, 0.97f, 0.93f), oro = new Color(1f, 0.78f, 0.25f), ocultar = new string[0] },
    };

    /// <summary>¿Ya se puede elegir? (los secretos piden las 10 galletas)</summary>
    public static bool Desbloqueado(int i) { return !Elfos[i].secreto || PlayerPrefs.GetInt("ElfoSecreto", 0) == 1; }
    public static void DesbloquearSecreto() { PlayerPrefs.SetInt("ElfoSecreto", 1); PlayerPrefs.Save(); }

    /// <summary>El elfo elegido (0 Tilo, 1 Nieves, 2 Chispa). Se lee de PlayerPrefs la primera vez.</summary>
    public static int Elegido
    {
        get
        {
            if (elegido < 0) elegido = Mathf.Clamp(PlayerPrefs.GetInt("Elfo", 0), 0, Elfos.Length - 1);
            if (!Desbloqueado(elegido)) elegido = 0;
            return elegido;
        }
        set { elegido = Mathf.Clamp(value, 0, Elfos.Length - 1); PlayerPrefs.SetInt("Elfo", elegido); PlayerPrefs.Save(); }
    }
    static int elegido = -1;
    public static Datos Actual => Elfos[Elegido];

    static readonly int BaseColorFactor = Shader.PropertyToID("baseColorFactor");
    static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
    static readonly int Emision = Shader.PropertyToID("emissiveFactor");

    Renderer[] renderers;
    Transform[] piezas;

    void Awake() { Aplicar(Elegido); }

    /// <summary>Elfo bloqueado: todo el cuerpo en negro (silueta), sin brillo.</summary>
    public void Silueta(int i)
    {
        Aplicar(i);
        var bloque = new MaterialPropertyBlock();
        Color negro = new Color(0.02f, 0.02f, 0.03f);
        foreach (var r in renderers)
        {
            if (r == null || r is ParticleSystemRenderer) continue;
            for (int k = 0; k < r.sharedMaterials.Length; k++)
            {
                bloque.Clear();
                bloque.SetColor(BaseColorFactor, negro); bloque.SetColor(BaseColor, negro);
                bloque.SetColor(Emision, Color.black);
                r.SetPropertyBlock(bloque, k);
            }
        }
    }

    public void Aplicar(int i)
    {
        var d = Elfos[Mathf.Clamp(i, 0, Elfos.Length - 1)];
        if (piezas == null) piezas = GetComponentsInChildren<Transform>(true);
        if (renderers == null) renderers = GetComponentsInChildren<Renderer>(true);

        // accesorios: "Acc_Nieves_Trenzas" se prende solo con Nieves
        foreach (var t in piezas)
        {
            if (t.name.StartsWith("Acc_")) t.gameObject.SetActive(t.name.StartsWith("Acc_" + d.nombre + "_"));
        }
        // piezas que este elfo no usa
        foreach (var t in piezas)
        {
            if (t.name.StartsWith("Acc_")) continue;
            var r = t.GetComponent<Renderer>();
            if (r == null) continue;
            bool oculta = System.Array.IndexOf(d.ocultar, t.name) >= 0;
            t.gameObject.SetActive(!oculta);
        }
        // colores de la ropa (los accesorios usan sus propios materiales "Acc_..." y no se pintan)
        var bloque = new MaterialPropertyBlock();
        foreach (var r in renderers)
        {
            if (r == null || r is ParticleSystemRenderer) continue;
            var mats = r.sharedMaterials;
            for (int k = 0; k < mats.Length; k++)
            {
                if (mats[k] == null) continue;
                Color c; string n = mats[k].name;
                if (n.StartsWith("Elfo_VerdeOscuro")) c = d.zapatos;
                else if (n.StartsWith("Elfo_Verde")) c = d.tunica;
                else if (n.StartsWith("Elfo_Rojo")) c = d.gorro;
                else if (n.StartsWith("Elfo_Blanco")) c = d.blanco;
                else if (n.StartsWith("Elfo_Oro")) c = d.oro;
                else c = Color.clear;
                if (c == Color.clear || i == 0) { bloque.Clear(); r.SetPropertyBlock(bloque, k); continue; }   // Tilo = colores originales
                bloque.Clear();
                bloque.SetColor(BaseColorFactor, c); bloque.SetColor(BaseColor, c);
                if (n.StartsWith("Elfo_Oro") && mats[k].HasProperty(Emision))   // el metal brilla: que el brillo siga al color nuevo
                {
                    Color e0 = mats[k].GetColor(Emision);
                    float fuerza = Mathf.Max(e0.r, Mathf.Max(e0.g, e0.b));
                    bloque.SetColor(Emision, c * fuerza);
                }
                r.SetPropertyBlock(bloque, k);
            }
        }
    }
}
