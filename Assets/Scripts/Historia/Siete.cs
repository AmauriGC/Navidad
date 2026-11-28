using System.Collections;
using UnityEngine;

/// <summary>
/// SIETE (historia 1.5): la Máquina 7 con personalidad. Anima las piezas que vienen del modelo de Blender
/// (hijos de "Maquina" en Props_Taller.glb y del corazón en el cuarto de máquinas). No usa animaciones de Unity:
/// solo cambia rotaciones, escalas y colores por código.
///   - Carita (Siete_OjoL/R, Siete_Boca): parpadea sola; después de una DESCARGA pone cara triste unos segundos
///     (ojos caídos y la sonrisa al revés = escala Y negativa), como pidiendo perdón. Curada: brilla más y rebota.
///   - Tablero (Siete_Foco_1..3 = engrane, resorte, fusible): rojos; cada uno se pone verde al instalar su refacción.
///   - Manómetro (Siete_Aguja): marca cuántas descargas lleva (0..10).
///   - Palanca (Siete_Palanca): se jala al fabricar la estrella nueva.
///   - Engranes del costado y volante del corazón: quietos mientras está enferma; giran cuando la curas.
///   - Corazón: Corazon_Engrane/Resorte/Fusible empiezan escondidos y aparecen (con rebote) al instalarse.
/// Los colores se ponen con MaterialPropertyBlock (no se modifican los materiales compartidos).
/// glTFast guarda el color en "baseColorFactor" y la emisión en "emissiveFactor".
/// </summary>
public class Siete : MonoBehaviour
{
    public static Siete Instancia { get; private set; }

    [Header("Colores")]
    public Color ojoNormal = new Color(0.45f, 0.9f, 1f), ojoTriste = new Color(0.25f, 0.45f, 0.95f), ojoFeliz = new Color(0.6f, 1f, 0.85f);
    public float brilloOjo = 1.4f;          // con ACES, más de ~2 ya se ve blanco
    public Color focoApagado = new Color(1f, 0.2f, 0.12f), focoListo = new Color(0.25f, 1f, 0.35f);

    Transform ojoL, ojoR, boca, aguja, palanca, eng1, eng2, volante, corEngrane, corResorte;
    Renderer rOjoL, rOjoR, rBoca, rCorFoco;
    readonly Renderer[] focos = new Renderer[3];
    readonly GameObject[] piezasCorazon = new GameObject[3];   // 0 engrane, 1 resorte, 2 fusible
    readonly bool[] instalada = new bool[3];
    Vector3 escOjo, escBoca, escResorte; Quaternion rotPalanca;
    float tristeHasta, siguienteParpadeo, agujaActual, agujaObjetivo, giro;
    bool curada, jalando;
    MaterialPropertyBlock mpb;
    static readonly int idEmision = Shader.PropertyToID("emissiveFactor"), idBase = Shader.PropertyToID("baseColorFactor");

    public bool Curada { get { return curada; } }

    void Awake()
    {
        Instancia = this;
        mpb = new MaterialPropertyBlock();
        ojoL = Buscar("Siete_OjoL"); ojoR = Buscar("Siete_OjoR"); boca = Buscar("Siete_Boca");
        aguja = Buscar("Siete_Aguja"); palanca = Buscar("Siete_Palanca");
        eng1 = Buscar("Siete_Engrane_1"); eng2 = Buscar("Siete_Engrane_2"); volante = Buscar("Corazon_Volante");
        for (int i = 0; i < 3; i++) { var f = Buscar("Siete_Foco_" + (i + 1)); if (f) focos[i] = f.GetComponent<Renderer>(); }
        var cf = Buscar("Corazon_Foco"); if (cf) rCorFoco = cf.GetComponent<Renderer>();
        string[] nombres = { "Corazon_Engrane", "Corazon_Resorte", "Corazon_Fusible" };
        for (int i = 0; i < 3; i++) { var t = Buscar(nombres[i]); if (t) piezasCorazon[i] = t.gameObject; }
        corEngrane = piezasCorazon[0] ? piezasCorazon[0].transform : null;
        corResorte = piezasCorazon[1] ? piezasCorazon[1].transform : null;
        if (ojoL) { rOjoL = ojoL.GetComponent<Renderer>(); escOjo = ojoL.localScale; }
        if (ojoR) rOjoR = ojoR.GetComponent<Renderer>();
        if (boca) { rBoca = boca.GetComponent<Renderer>(); escBoca = boca.localScale; }
        if (corResorte) escResorte = corResorte.localScale;
        if (palanca) rotPalanca = palanca.localRotation;
    }

    static Transform Buscar(string n) { var g = GameObject.Find(n); return g ? g.transform : null; }

    void Start()
    {
        foreach (var p in piezasCorazon) if (p) p.SetActive(false);   // las refacciones aún no están puestas
        for (int i = 0; i < 3; i++) PintarFoco(focos[i], focoApagado, 1.2f);
        PintarFoco(rCorFoco, focoApagado, 2f);
        PonerAguja(0f);
        siguienteParpadeo = Time.time + Random.Range(2f, 4f);
    }

    void Update()
    {
        bool triste = Time.time < tristeHasta && !curada;
        // --- ojos: parpadeo + cara triste / feliz
        float parpadeo = 1f;
        if (Time.time > siguienteParpadeo)
        {
            float k = (Time.time - siguienteParpadeo) / 0.16f;
            parpadeo = k < 1f ? Mathf.Lerp(1f, 0.1f, Mathf.Sin(k * Mathf.PI)) : 1f;
            if (k >= 1f) siguienteParpadeo = Time.time + Random.Range(2.5f, 5f) * (triste ? 0.5f : 1f);
        }
        float rebote = curada ? 1f + Mathf.Abs(Mathf.Sin(Time.time * 3f)) * 0.08f : 1f;
        float alto = (triste ? 0.72f : 1f) * parpadeo * rebote;
        float inclinar = triste ? 16f : 0f;
        if (ojoL) { ojoL.localScale = new Vector3(escOjo.x, escOjo.y * alto, escOjo.z); ojoL.localRotation = Quaternion.Euler(0f, 0f, inclinar); }
        if (ojoR) { ojoR.localScale = new Vector3(escOjo.x, escOjo.y * alto, escOjo.z); ojoR.localRotation = Quaternion.Euler(0f, 0f, -inclinar); }
        if (boca) boca.localScale = new Vector3(escBoca.x, escBoca.y * (triste ? -0.8f : 1f), escBoca.z);   // escala Y negativa = sonrisa al revés
        Color c = curada ? ojoFeliz : (triste ? ojoTriste : ojoNormal);
        float b = brilloOjo * (triste ? 0.7f + Mathf.PerlinNoise(Time.time * 6f, 0f) * 0.3f : 1f) * (curada ? 1.25f : 1f);
        PintarEmision(rOjoL, c * b); PintarEmision(rOjoR, c * b); PintarEmision(rBoca, c * b);

        // --- manómetro: la aguja se acomoda despacito (con un temblorcito si va alta)
        agujaActual = Mathf.MoveTowards(agujaActual, agujaObjetivo, Time.deltaTime * 4f);
        PonerAguja(agujaActual + (agujaActual > 7.5f && !curada ? Mathf.Sin(Time.time * 40f) * 0.12f : 0f));

        // --- engranes y volante: giran solo cuando está curada
        if (curada)
        {
            giro += Time.deltaTime;
            if (eng1) eng1.Rotate(Vector3.right, 90f * Time.deltaTime, Space.Self);
            if (eng2) eng2.Rotate(Vector3.right, -118f * Time.deltaTime, Space.Self);
            if (volante) volante.Rotate(Vector3.right, 140f * Time.deltaTime, Space.Self);
            if (corEngrane && corEngrane.gameObject.activeSelf) corEngrane.Rotate(Vector3.forward, 120f * Time.deltaTime, Space.Self);
            if (corResorte && corResorte.gameObject.activeSelf) corResorte.localScale = new Vector3(escResorte.x, escResorte.y * (1f + Mathf.Sin(giro * 9f) * 0.08f), escResorte.z);
        }
    }

    // ------------------------------------------------------------------ lo que le pasa a Siete
    /// <summary>Una descarga: cara triste unos segundos y la aguja sube a 'cuenta'.</summary>
    public void Descarga(int cuenta)
    {
        tristeHasta = Time.time + 4f;
        agujaObjetivo = Mathf.Clamp(cuenta, 0, 10);
    }

    /// <summary>Se instaló una refacción (0 engrane, 1 resorte, 2 fusible).</summary>
    public void Instalada(int indice)
    {
        if (indice < 0 || indice > 2 || instalada[indice]) return;
        instalada[indice] = true;
        PintarFoco(focos[indice], focoListo, 2.2f);
        int n = 0; foreach (bool x in instalada) if (x) n++;
        PintarFoco(rCorFoco, n >= 3 ? focoListo : Color.Lerp(focoApagado, new Color(1f, 0.85f, 0.2f), 0.85f), 2.5f);
        if (piezasCorazon[indice]) StartCoroutine(Aparecer(piezasCorazon[indice].transform));
    }

    public void Curar()
    {
        curada = true;
        agujaObjetivo = 0f;
        for (int i = 0; i < 3; i++) if (!instalada[i]) Instalada(i);
    }

    /// <summary>Jala la palanca grande (al fabricar la estrella). Dura ~1.6 s.</summary>
    public IEnumerator JalarPalanca()
    {
        if (palanca == null || jalando) yield break;
        jalando = true;
        // en Unity girar NEGATIVO en X lleva la perilla hacia el frente (hacia el árbol)
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.45f) { palanca.localRotation = rotPalanca * Quaternion.AngleAxis(-70f * Suave(t), Vector3.right); yield return null; }
        palanca.localRotation = rotPalanca * Quaternion.AngleAxis(-70f, Vector3.right);
        yield return new WaitForSeconds(0.7f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.5f) { palanca.localRotation = rotPalanca * Quaternion.AngleAxis(-70f * (1f - Suave(t)), Vector3.right); yield return null; }
        palanca.localRotation = rotPalanca;
        jalando = false;
    }

    // ------------------------------------------------------------------ ayudantes
    static float Suave(float t) { t = Mathf.Clamp01(t); return t * t * (3f - 2f * t); }

    /// <summary>La aguja: 0 a la izquierda (vista de frente) .. 10 a la derecha. En Blender el ángulo es 120° - 24°·n
    /// alrededor de su eje Y; pasado a Unity (x,y,z)blender -> (-x, z, -y) la dirección queda en el plano XY.</summary>
    void PonerAguja(float n)
    {
        if (aguja == null) return;
        float a = (120f - 24f * n) * Mathf.Deg2Rad;
        var d = new Vector3(-Mathf.Sin(a), Mathf.Cos(a), 0f);
        aguja.localRotation = Quaternion.FromToRotation(Vector3.up, d);
    }

    IEnumerator Aparecer(Transform t)
    {
        t.gameObject.SetActive(true);
        Vector3 fin = t.localScale;
        for (float k = 0f; k < 1f; k += Time.deltaTime / 0.5f)
        {
            float x = k - 1f; const float c = 1.70158f;
            t.localScale = fin * (1f + (c + 1f) * x * x * x + c * x * x);   // easeOutBack, igual que las piezas del árbol
            yield return null;
        }
        t.localScale = fin;
    }

    void PintarEmision(Renderer r, Color c)
    {
        if (r == null) return;
        r.GetPropertyBlock(mpb); mpb.SetColor(idEmision, c); r.SetPropertyBlock(mpb);
    }

    void PintarFoco(Renderer r, Color c, float brillo)
    {
        if (r == null) return;
        // solo el material 0 (el vidrio del foco); el 1 es el aro de latón y se queda igual
        r.GetPropertyBlock(mpb, 0); mpb.SetColor(idBase, c); mpb.SetColor(idEmision, c * brillo); r.SetPropertyBlock(mpb, 0);
    }
}
