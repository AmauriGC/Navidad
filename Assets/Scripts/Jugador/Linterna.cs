using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// LINTERNA CON PILA (Difícil / Imposible): la luz del elfo ("LuzElfo") gasta pila mientras juegas.
///  - Dura 'duracion' segundos (Difícil 4 min, Imposible 2.5 min). Abajo de 25% parpadea y se debilita; en 0 se apaga.
///  - Se RECARGA parado junto a una fuente de luz cálida: la chimenea, los faroles del patio o los farolitos del pueblo
///    (a menos de 3.2 m en el piso). Se llena en ~4 s.
///  - HUD: una pila con 4 rayitas debajo de los corazones (verde → amarillo → rojo).
/// Dificultad.Aplicar() la agrega al jugador solo en los niveles que la usan (en Fácil/Medio la luz es infinita).
/// </summary>
public class Linterna : MonoBehaviour
{
    public static bool Activa { get; private set; }

    public float duracion = 240f;
    public const float DistanciaRecarga = 3.2f, SegundosRecarga = 4f;

    public float Carga { get; private set; } = 1f;
    Light luz; float intensidad0, rango0;
    readonly List<Transform> fuentes = new List<Transform>();
    bool avisoBaja, avisoApagada, recargando, avisoRecarga;
    float parpadeo;

    // HUD
    RectTransform fila; CanvasGroup grupo; Image[] rayas; Image marco, punta;

    public void Configurar(float segundos)
    {
        duracion = segundos; Carga = 1f; Activa = true;
        var t = transform.Find("LuzElfo");
        luz = t != null ? t.GetComponent<Light>() : GetComponentInChildren<Light>();
        if (luz != null)
        {
            // en la oscuridad de estos modos la linterna alumbra un poco más (si no, ni se notaría la diferencia)
            intensidad0 = luz.intensity * 1.5f; rango0 = luz.range * 1.35f;
            luz.intensity = intensidad0; luz.range = rango0;
        }
        // fuentes de recarga: chimenea, faroles del patio y farolitos del pueblo
        foreach (var l in FindObjectsByType<Light>())
        {
            string n = l.name;
            if (n.StartsWith("Luz_Chimenea") || n.StartsWith("Luz_Farol") || (l.transform.parent != null && l.transform.parent.name.Contains("Farolitos")))
                fuentes.Add(l.transform);
        }
    }

    void Update()
    {
        if (luz == null) return;
        bool jugando = Juego.Estado == Juego.Modo.Jugando;
        // ¿estoy junto a una fuente de luz?
        recargando = false;
        if (jugando)
            foreach (var f in fuentes)
            {
                Vector3 d = f.position - transform.position;
                if (Mathf.Abs(d.y) < 5f && new Vector2(d.x, d.z).magnitude < DistanciaRecarga) { recargando = true; break; }
            }
        if (recargando && Carga < 1f)
        {
            if (!avisoRecarga) { avisoRecarga = true; GestorAudio.Efecto("recarga", 0.7f, 0f); UIAviso.Mensaje("Recargando la linterna junto a la luz...", 2f); }
            Carga = Mathf.Min(1f, Carga + Time.deltaTime / SegundosRecarga);
            avisoBaja = avisoApagada = false;
        }
        else
        {
            if (!recargando) avisoRecarga = false;
            if (jugando) Carga = Mathf.Max(0f, Carga - Time.deltaTime / duracion);
        }

        if (Carga < 0.25f && Carga > 0f && !avisoBaja)
        {
            avisoBaja = true; GestorAudio.Efecto("pila_baja", 0.7f, 0f);
            UIAviso.Mensaje("¡Tu linterna se está quedando sin pila!\nRecárgala junto a la chimenea o un farol.", 4f);
        }
        if (Carga <= 0f && !avisoApagada)
        {
            avisoApagada = true; GestorAudio.Efecto("pila_baja", 0.9f, 0f);
            UIAviso.Mensaje("Se apagó tu linterna... busca la chimenea o un farol.", 3.5f);
        }

        // brillo: normal; abajo de 25% se debilita y parpadea (cada vez más seguido); en 0 apagada
        float k = 1f;
        if (Carga <= 0f) k = 0f;
        else if (Carga < 0.25f)
        {
            k = Mathf.Lerp(0.35f, 1f, Carga / 0.25f);
            parpadeo -= Time.deltaTime;
            if (parpadeo < 0f) { parpadeo = Random.Range(0.05f, Mathf.Lerp(0.4f, 2f, Carga / 0.25f)); }
            if (parpadeo < 0.06f) k *= 0.15f;
        }
        luz.intensity = intensidad0 * k;
        luz.range = rango0 * Mathf.Lerp(0.6f, 1f, k);
        HUD(jugando);
    }

    void HUD(bool jugando)
    {
        if (fila == null)
        {
            var canvas = UIConstructor.Canvas; if (canvas == null) return;
            fila = UIConstructor.Rect("Pila", canvas.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(200, 40), new Vector2(30 + 100, -300));
            grupo = UIConstructor.Grupo(fila, 0f);
            var m = UIConstructor.Rect("Marco", fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(84, 34), new Vector2(44, 0));
            marco = UIConstructor.Imagen(m, new Color(1f, 1f, 1f, 0.85f)); UIConstructor.Sombra(marco, 2f);
            UIConstructor.Imagen(UIConstructor.Rect("Fondo", m, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(76, 26)), new Color(0.05f, 0.06f, 0.1f, 1f));
            punta = UIConstructor.Imagen(UIConstructor.Rect("Punta", fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(8, 16), new Vector2(90, 0)), new Color(1f, 1f, 1f, 0.85f));
            rayas = new Image[4];
            for (int i = 0; i < 4; i++)
                rayas[i] = UIConstructor.Imagen(UIConstructor.Rect("Raya" + i, m, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(15, 20), new Vector2(-27 + i * 18, 0)), Color.white);
            var txt = UIConstructor.Texto(UIConstructor.Rect("Texto", fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(120, 34), new Vector2(160, 0)), "Linterna", 22, new Color(1f, 0.9f, 0.7f), TextAnchor.MiddleLeft);
            UIConstructor.Sombra(txt);
        }
        // debajo de los corazones (que están debajo del panel del objetivo)
        fila.anchoredPosition = new Vector2(fila.anchoredPosition.x, -(UIObjetivo.Abajo + 12f + (Dificultad.ConVidas ? 50f : 0f) + 20f));
        bool ver = jugando || Juego.Estado == Juego.Modo.Pausa;
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, ver ? 1f : 0f, Time.unscaledDeltaTime * 3f);
        Color c = Carga > 0.5f ? new Color(0.45f, 0.95f, 0.5f) : Carga > 0.25f ? new Color(1f, 0.85f, 0.3f) : new Color(1f, 0.3f, 0.25f);
        bool late = Carga < 0.25f && Mathf.Repeat(Time.unscaledTime, 0.8f) < 0.4f;
        for (int i = 0; i < 4; i++)
        {
            float lleno = Mathf.Clamp01(Carga * 4f - i);      // cada rayita = 25%
            rayas[i].color = new Color(c.r, c.g, c.b, lleno > 0.01f ? Mathf.Lerp(0.35f, 1f, lleno) * (late ? 0.4f : 1f) : 0.08f);
        }
        // mientras recarga, el marco brilla amarillo
        marco.color = punta.color = recargando && Carga < 1f ? Color.Lerp(Color.white, new Color(1f, 0.85f, 0.3f), 0.5f + 0.5f * Mathf.Sin(Time.unscaledTime * 8f)) : new Color(1f, 1f, 1f, 0.85f);
    }

    void OnDestroy() { Activa = false; if (fila != null) Destroy(fila.gameObject); }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Activa = false; }
}
