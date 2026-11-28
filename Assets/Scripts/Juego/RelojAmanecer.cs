using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// RELOJ DEL AMANECER: la noche va de las 10:00 PM a las 6:00 AM (8 horas de juego)
/// comprimidas en 'minutosReales' minutos de verdad.
///  - El reloj SOLO avanza mientras juegas (no en el título, cinemáticas, letreros ni pausa).
///  - Conforme se acerca el amanecer, el cielo se aclara poco a poco y salen avisos.
///  - Si llegan las 6:00 AM y el árbol no está completo -> el DirectorJuego muestra la derrota.
/// Fórmula: hora = 22 + 8 · (tiempo / duración)   (después de las 24 se le resta 24).
/// </summary>
public class RelojAmanecer : MonoBehaviour
{
    [Tooltip("Minutos REALES que dura la noche completa.")]
    public float minutosReales = 15f;
    public float horaInicio = 22f, horasNoche = 8f;
    [Tooltip("A partir de qué fracción de la noche el cielo empieza a clarear.")]
    [Range(0, 1)] public float empiezaAClarear = 0.6f;

    public float Progreso { get { return Mathf.Clamp01(segundos / (minutosReales * 60f)); } }
    public bool SeAcabo { get; private set; }

    /// <summary>Historia 1.5: el minijuego de la charola pausa el juego, pero la noche sigue avanzando.</summary>
    public void Avanzar(float s) { segundos += s; }

    float segundos; Text texto; CanvasGroup grupo;
    Material cielo; Color horizonte0, arriba0; Color ambiente0;
    int avisosDados;
    static readonly float[] avisos = { 0.75f, 0.875f, 0.9375f };   // 4:00, 5:00 y 5:30 AM

    void Start()
    {
        var capa = UIConstructor.Capa("Reloj", 5);
        var raiz = UIConstructor.Rect("Contenido", capa, new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(330, 110), new Vector2(-185, -70));
        grupo = UIConstructor.Grupo(raiz, 0f);
        UIConstructor.Imagen(raiz, new Color(0.02f, 0.03f, 0.08f, 0.55f));
        UIConstructor.Texto(UIConstructor.Rect("Etiqueta", raiz, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(320, 34), new Vector2(0, -22)),
                            "Amanece a las 6:00 AM", 22, new Color(0.75f, 0.85f, 1f));
        texto = UIConstructor.Texto(UIConstructor.Rect("Hora", raiz, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(320, 70), new Vector2(0, 38)),
                                     "", 50, new Color(1f, 0.85f, 0.45f));   // Fredoka: en la letra navideña el 0 parecía "o"
        UIConstructor.Sombra(texto, 3f);
        ambiente0 = RenderSettings.ambientLight;
    }

    int horaMostrada = -1;

    void Update()
    {
        var arbol = ArbolNavidad.Instancia;
        bool corre = Juego.Estado == Juego.Modo.Jugando && !SeAcabo && (arbol == null || !arbol.Completo);
        if (corre) segundos += Time.deltaTime;

        bool visible = (Juego.Estado == Juego.Modo.Jugando || Juego.Estado == Juego.Modo.Leyendo) && (arbol == null || !arbol.Completo);
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, visible ? 1f : 0f, Time.unscaledDeltaTime * 3f);

        // hora del juego
        float hora = horaInicio + horasNoche * Progreso;
        if (hora >= 24f) hora -= 24f;
        int h = Mathf.FloorToInt(hora), m = Mathf.FloorToInt((hora - h) * 60f / 5f) * 5;   // de 5 en 5 minutos
        int h12 = h % 12 == 0 ? 12 : h % 12;
        int clave = h * 100 + m;
        if (clave != horaMostrada) { horaMostrada = clave; texto.text = h12 + ":" + m.ToString("00") + (h >= 12 ? " PM" : " AM"); }
        // la última hora el reloj se pone rojizo y late
        if (Progreso > 0.875f) texto.color = Color.Lerp(new Color(1f, 0.85f, 0.45f), new Color(1f, 0.35f, 0.25f), 0.5f + 0.5f * Mathf.Sin(Time.time * 5f));

        if (corre) { Avisos(); Clarear(); }

        if (corre && Progreso >= 1f)
        {
            SeAcabo = true;
            var director = FindAnyObjectByType<DirectorJuego>();
            if (director != null) director.Amanecio();
        }
    }

    void Avisos()
    {
        if (avisosDados >= avisos.Length || Progreso < avisos[avisosDados]) return;
        string[] textos = { "Son las 4:00 AM... el cielo empieza a clarear. ¡Date prisa!",
                            "¡Las 5:00 AM! Queda una hora para el amanecer.",
                            "¡Las 5:30 AM! ¡Santa está por llegar!" };
        UIAviso.Mensaje(textos[avisosDados], 3.5f);
        GestorAudio.Efecto("campanada", 0.7f, 0f);   // campanadas de reloj
        avisosDados++;
    }

    /// <summary>El cielo se pinta un poco hacia el amanecer (sin llegar del todo: eso queda para el final).</summary>
    void Clarear()
    {
        if (cielo == null)
        {
            cielo = RenderSettings.skybox;   // es la COPIA que hace el DirectorJuego (no se modifica el material original)
            if (cielo == null || !cielo.HasProperty("_ColorHorizonte")) return;
            horizonte0 = cielo.GetColor("_ColorHorizonte"); arriba0 = cielo.GetColor("_ColorArriba");
        }
        float k = Mathf.InverseLerp(empiezaAClarear, 1f, Progreso) * 0.55f;   // hasta 55% del color del amanecer
        cielo.SetColor("_ColorHorizonte", Color.Lerp(horizonte0, new Color(0.85f, 0.45f, 0.35f), k));
        cielo.SetColor("_ColorArriba", Color.Lerp(arriba0, new Color(0.12f, 0.15f, 0.35f), k));
        RenderSettings.ambientLight = Color.Lerp(ambiente0, new Color(0.32f, 0.3f, 0.4f), k);
    }
}
