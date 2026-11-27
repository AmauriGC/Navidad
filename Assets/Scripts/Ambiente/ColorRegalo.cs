using UnityEngine;

/// <summary>
/// Le da a CADA regalo su propio color de papel y de listón, aunque todos usen el mismo modelo y los mismos
/// materiales. Usa un MaterialPropertyBlock: es como un "post-it" con valores que se pegan solo a este
/// renderer, sin crear materiales nuevos (si hiciéramos renderer.material = ..., Unity duplicaría el material).
/// El modelo Regalo.glb tiene 3 materiales: 0 = papel, 1 = listón, 2 = lunares.
/// [ExecuteAlways] => también se ve el color en el editor, sin dar Play.
/// </summary>
[ExecuteAlways]
public class ColorRegalo : MonoBehaviour
{
    public Color papel = new Color(0.8f, 0.1f, 0.12f);
    public Color liston = new Color(1f, 0.8f, 0.3f);
    public Color lunares = new Color(0.95f, 0.92f, 0.85f);

    // glTFast guarda el color base en "baseColorFactor"; los shaders de URP en "_BaseColor"
    static readonly int BaseColorFactor = Shader.PropertyToID("baseColorFactor");
    static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
    static readonly int EmissiveFactor = Shader.PropertyToID("emissiveFactor");

    [Tooltip("Qué tanto brilla el listón con su propio color (con el Bloom se ve como satinado).")]
    [Range(0f, 1f)] public float brilloListon = 0.25f;

    void OnEnable() { Aplicar(); }
    void OnValidate() { Aplicar(); }   // al cambiar un color en el Inspector

    public void Aplicar()
    {
        var r = GetComponentInChildren<Renderer>();
        if (r == null) return;
        var colores = new[] { papel, liston, lunares };
        var bloque = new MaterialPropertyBlock();
        int n = Mathf.Min(colores.Length, r.sharedMaterials.Length);
        for (int i = 0; i < n; i++)
        {
            bloque.Clear();
            bloque.SetColor(BaseColorFactor, colores[i]);
            bloque.SetColor(BaseColor, colores[i]);
            // El material del listón trae emisión dorada: la reemplazamos por el color del listón (si no, todos se ven dorados)
            bloque.SetColor(EmissiveFactor, i == 1 ? colores[i] * brilloListon : Color.black);
            r.SetPropertyBlock(bloque, i);   // solo afecta al material número i de ESTE renderer
        }
    }
}
