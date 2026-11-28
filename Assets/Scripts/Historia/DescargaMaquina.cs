using System.Collections;
using UnityEngine;

/// <summary>
/// DESCARGAS DE SIETE (historia 1.5). Mientras Siete esté enferma, cada cierto tiempo da una DESCARGA
/// ("hipo eléctrico"): zumbido, las luces del taller parpadean, chispas, y un rayo viaja por los cables del techo
/// desde la máquina hasta arriba del Gran Árbol. Cada descarga le da CUERDA a los cascanueces.
///
/// ¿Cada cuánto? Dificultad.Actual.segundosDescarga (Fácil 3 min · Medio 2 · Difícil 90 s · Imposible 60 s).
/// El reloj solo corre mientras se JUEGA (no en diálogos, pausa ni cinemáticas). La primera descarga es el tutorial:
/// la dispara el DirectorJuego al terminar la etapa de la maceta y desde ahí empieza a contar.
///
/// ¿Qué hace cada descarga?
///   - Suave (Fácil/Medio): los cascanueces despiertos van más rápido 5 s (su llave gira rapidísimo).
///   - Grave (Difícil/Imposible): además despierta ANTES DE TIEMPO al cascanueces dormido más cercano a Siete,
///     y la cuerda extra dura más (8 s, x1.35).
///   - Siete pone cara triste (Siete.Descarga) y la aguja de su manómetro sube.
///   - Aviso en pantalla (Guion.AvisoDescarga): 3/10... 8/10 "está muy mal"... 9/10 "¡una más y se sobrecarga!".
/// DESCARGA 10 = SOBRECARGA:
///   - Difícil/Imposible: DERROTA (DirectorJuego.Sobrecarga, Guion.DerrotaSobrecarga).
///   - Fácil/Medio: solo un SUSTO: apagón de unos segundos, todos los cascanueces despiertos corren hacia ti
///     con cuerda extra, y el contador baja a 6 (puede volver a pasar si no curas a Siete).
/// Al curar a Siete (MaquinaRota.Reparada) ya no hay descargas.
/// </summary>
public class DescargaMaquina : MonoBehaviour
{
    public static DescargaMaquina Instancia { get; private set; }
    public static int Cuenta { get; private set; }
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Cuenta = 0; }

    public const int Maximo = 10;

    [Tooltip("Material del rayo (transparente/aditivo).")]
    public Material materialRayo;
    public Color colorRayo = new Color(0.55f, 0.9f, 1f);
    public Color colorRayoBueno = new Color(1f, 0.82f, 0.35f);   // el del final (dorado)
    public float duracionRayo = 0.9f;
    [Tooltip("Camino de los cables (de Siete a arriba del árbol). Sale de Blender/datos_siete.json.")]
    public Vector3[] camino =
    {
        new Vector3(7.6f, 2.8f, 7.35f), new Vector3(7.6f, 6.9f, 7.9f), new Vector3(6.97f, 6.95f, 7.23f), new Vector3(6.33f, 6.95f, 6.57f),
        new Vector3(5.7f, 7.2f, 5.9f), new Vector3(5.07f, 6.95f, 5.25f), new Vector3(4.43f, 6.95f, 4.6f), new Vector3(3.8f, 7.2f, 3.95f),
        new Vector3(3.17f, 6.95f, 3.3f), new Vector3(2.53f, 6.95f, 2.65f), new Vector3(1.9f, 7.2f, 2.0f), new Vector3(1.27f, 6.95f, 1.33f),
        new Vector3(0.63f, 6.95f, 0.67f), new Vector3(0f, 7.2f, 0f), new Vector3(0f, 6.7f, 0f)
    };

    Light[] luces; float[] intensidades;
    float reloj, siguiente; bool contando, sinLuz;

    void Awake() { Instancia = this; Cuenta = 0; }

    void Start()
    {
        var lista = new System.Collections.Generic.List<Light>();
        foreach (var l in FindObjectsByType<Light>())
            if (l.name.StartsWith("Luz_Taller") || l.name == "Luz_Establo" || l.name == "Luz_Cuarto") lista.Add(l);   // (las del árbol no: él sube su brillo solo)
        luces = lista.ToArray();
        intensidades = new float[luces.Length];
        for (int i = 0; i < luces.Length; i++) intensidades[i] = luces[i].intensity;
    }

    float Segundos { get { float s = Dificultad.Actual.segundosDescarga; return s > 0f ? s : 120f; } }
    bool Grave { get { return Dificultad.Actual.descargaGrave; } }

    /// <summary>Lo llama el DirectorJuego después de la descarga del tutorial: desde aquí cuenta el tiempo.</summary>
    public void Empezar() { contando = true; siguiente = reloj + Segundos; }

    void Update()
    {
        if (!contando || MaquinaRota.Reparada || Juego.Perdio || Juego.Estado != Juego.Modo.Jugando) return;
        reloj += Time.deltaTime;
        if (reloj >= siguiente) { Disparar(); siguiente = reloj + Segundos; }
    }

    /// <summary>Una descarga de Siete (también la usa el apagón de las 3 AM: "la descarga más grande").</summary>
    public void Disparar(bool tutorial = false)
    {
        if (MaquinaRota.Reparada) return;
        Cuenta++;
        if (Siete.Instancia != null) Siete.Instancia.Descarga(Cuenta);
        StartCoroutine(Rayo(colorRayo));
        StartCoroutine(Parpadeo(0.9f));
        GestorAudio.Efecto("descarga", 0.85f, 0.05f);
        TemblorCamara.Sacudir(tutorial ? 0.15f : 0.22f);

        // cuerda extra a los cascanueces
        var todos = FindObjectsByType<Cascanueces>();
        if (!tutorial && Grave)
        {
            Cascanueces cerca = null; float mejor = float.MaxValue;
            Vector3 siete = camino.Length > 0 ? camino[0] : transform.position;
            foreach (var c in todos)
            {
                if (c.Despierto || c.EstadoActual == Cascanueces.Estado.Congelado) continue;
                float d = (c.transform.position - siete).sqrMagnitude;
                if (d < mejor) { mejor = d; cerca = c; }
            }
            if (cerca != null && cerca.DespertarYa()) UIAviso.Mensaje("¡La descarga despertó a " + cerca.nombre + " antes de tiempo!", 4f);
        }
        foreach (var c in todos)
            if (c.Despierto) { c.DarCuerda(Grave ? 1.35f : 1.15f, Grave ? 8f : 5f); GestorAudio.Efecto3D("cuerda", c.transform.position + Vector3.up, 0.7f); }

        if (!tutorial && Cuenta < Maximo) UIAviso.Mensaje(Guion.AvisoDescarga(Cuenta), 3.5f);
        if (Cuenta >= Maximo) Sobrecarga();
    }

    void Sobrecarga()
    {
        if (Grave)
        {
            var dir = FindAnyObjectByType<DirectorJuego>();
            if (dir != null) dir.Sobrecarga();
            return;
        }
        // Fácil / Medio: solo un susto
        UIAviso.Mensaje(Guion.AvisoSobrecargaSusto, 5f);
        StartCoroutine(Apagon(7f));
        var j = GameObject.FindGameObjectWithTag("Player");
        foreach (var c in FindObjectsByType<Cascanueces>())
            if (c.Despierto) { c.DarCuerda(1.25f, 10f); if (j != null) c.OirRuido(j.transform.position, 999f); }
        StartCoroutine(UIHistoria.Esperar(Guion.SobrecargaSusto));
        Cuenta = 6;
        if (Siete.Instancia != null) Siete.Instancia.Descarga(Cuenta);
    }

    // ------------------------------------------------------------------ efectos
    /// <summary>Un rayito de luz viaja por los cables (una luz con estela que recorre el camino).
    /// Público: el final lo usa al revés y en dorado (la "descarga buena").</summary>
    public IEnumerator Rayo(Color color, bool alReves = false) { return RayoEntre(camino, color, duracionRayo, alReves); }

    /// <summary>Un rayito con estela que recorre los puntos 'pts' en 'dur' segundos (la intro lo usa del techo a la caja).</summary>
    public IEnumerator RayoEntre(Vector3[] pts, Color color, float dur, bool alReves = false)
    {
        if (pts == null || pts.Length < 2) yield break;
        var go = new GameObject("Rayo");
        var luz = go.AddComponent<Light>(); luz.type = LightType.Point; luz.color = color; luz.range = 4f; luz.intensity = 8f; luz.shadows = LightShadows.None;
        var estela = go.AddComponent<TrailRenderer>();
        estela.time = 0.28f; estela.minVertexDistance = 0.05f; estela.widthMultiplier = 0.18f;
        estela.widthCurve = AnimationCurve.Linear(0f, 1f, 1f, 0f);
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(color, 0.4f), new GradientColorKey(color, 1f) },
                  new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(0f, 1f) });
        estela.colorGradient = g;
        estela.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        if (materialRayo != null) estela.sharedMaterial = materialRayo;
        float total = 0f; for (int i = 1; i < pts.Length; i++) total += Vector3.Distance(pts[i - 1], pts[i]);
        go.transform.position = Punto(pts, alReves ? 1f : 0f, total);
        for (float t = 0f; t < 1f; t += Time.deltaTime / dur)
        {
            go.transform.position = Punto(pts, alReves ? 1f - t : t, total) + Random.insideUnitSphere * 0.04f;
            luz.intensity = 7f + Random.Range(-2f, 2f);
            yield return null;
        }
        go.transform.position = Punto(pts, alReves ? 0f : 1f, total);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.3f) { luz.intensity = Mathf.Lerp(12f, 0f, t); yield return null; }
        Destroy(go);
    }

    static Vector3 Punto(Vector3[] pts, float t, float total)
    {
        float meta = Mathf.Clamp01(t) * total, andado = 0f;
        for (int i = 1; i < pts.Length; i++)
        {
            float l = Vector3.Distance(pts[i - 1], pts[i]);
            if (andado + l >= meta) return Vector3.Lerp(pts[i - 1], pts[i], l > 0f ? (meta - andado) / l : 0f);
            andado += l;
        }
        return pts[pts.Length - 1];
    }

    IEnumerator Parpadeo(float duracion)
    {
        if (luces == null || sinLuz) yield break;
        for (float t = 0f; t < duracion; t += 0.07f)
        {
            bool prendida = Random.value > 0.45f;
            for (int i = 0; i < luces.Length; i++) if (luces[i]) luces[i].intensity = intensidades[i] * (prendida ? Random.Range(0.6f, 1.2f) : 0.1f);
            yield return new WaitForSeconds(0.07f);
        }
        if (!sinLuz) Restaurar();
    }

    IEnumerator Apagon(float segundos)
    {
        sinLuz = true;
        for (int i = 0; i < luces.Length; i++) if (luces[i]) luces[i].intensity = 0f;
        yield return new WaitForSeconds(segundos);
        sinLuz = false;
        Restaurar();
        GestorAudio.Efecto("luz_vuelve", 0.7f, 0f);
    }

    void Restaurar() { for (int i = 0; i < luces.Length; i++) if (luces[i]) luces[i].intensity = intensidades[i]; }
}
