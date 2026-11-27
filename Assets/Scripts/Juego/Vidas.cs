using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// VIDAS (solo en Difícil e Imposible). Clase ESTÁTICA con su HUD de corazones (arriba a la izquierda,
/// debajo del panel del objetivo).
///  - Perder(): la llama el Cascanueces al atraparte. Si llegan a 0 -> DirectorJuego.SinVidas() (derrota).
///  - PorGalleta(n): la llama Galleta al juntar una; cada 'galletasPorVida' galletas = +1 vida (tope 5).
/// El corazón que se pierde se encoge y se pone gris; el que se gana "late".
/// </summary>
public static class Vidas
{
    public static int Actual { get; private set; }
    public static int Ganadas { get; private set; }   // por galletas (para los créditos)
    static int inicio;
    /// <summary>Cuántas vidas perdiste en esta partida (para la medalla "Intacto").</summary>
    public static int Perdidas => Mathf.Max(0, inicio + Ganadas - Actual);

    static RectTransform fila;
    static readonly List<Image> corazones = new List<Image>();
    static float[] latido = new float[Dificultad.MaxVidas];

    public static void Empezar(int vidas)
    {
        Actual = inicio = vidas; Ganadas = 0;
        if (fila != null) Object.Destroy(fila.gameObject);
        fila = null; corazones.Clear();
        if (vidas > 0) Dibujar();
    }

    /// <summary>Te atraparon: -1 vida. Devuelve true si ya no quedan.</summary>
    public static bool Perder()
    {
        if (!Dificultad.ConVidas || Actual <= 0) return false;
        Actual--;
        Dibujar(); if (Actual < corazones.Count) latido[Actual] = 1f;
        return Actual <= 0;
    }

    public static void PorGalleta(int encontradas)
    {
        int cada = Dificultad.Actual.galletasPorVida;
        if (!Dificultad.ConVidas || cada <= 0 || encontradas % cada != 0) return;
        if (Actual >= Dificultad.MaxVidas) { UIAviso.Mensaje("¡+1 vida! ...pero ya tienes el máximo (" + Dificultad.MaxVidas + ").", 2.5f); return; }
        Actual++; Ganadas++;
        Dibujar(); latido[Actual - 1] = 1f;
        GestorAudio.Efecto("poder", 0.5f, 0f);
        UIAviso.Mensaje("¡Galleta de jengibre! <color=#ff8080>+1 vida</color>  (" + Actual + ")", 3f);
    }

    static void Dibujar()
    {
        if (fila == null)
        {
            var canvas = UIConstructor.Canvas; if (canvas == null) return;
            // mismo lugar donde estaba "Galletas x/10" (ese texto baja un renglón cuando hay vidas)
            fila = UIConstructor.Rect("Vidas", canvas.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(320, 46), new Vector2(30 + 160, -300));   // debajo del panel Objetivo (mide ~270 px con la pista)
            fila.gameObject.AddComponent<CanvasGroup>();
            fila.gameObject.AddComponent<AnimadorVidas>();
        }
        while (corazones.Count < Dificultad.MaxVidas)
        {
            int k = corazones.Count;
            var rt = UIConstructor.Rect("Corazon" + k, fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(42, 42), new Vector2(21 + k * 48, 0));
            var img = UIConstructor.Imagen(rt, Color.white); img.sprite = UIConstructor.SpriteCorazon();
            UIConstructor.Sombra(img, 2f);
            corazones.Add(img);
        }
        for (int k = 0; k < corazones.Count; k++)
        {
            bool lleno = k < Actual, existe = k < Mathf.Max(Actual, inicio);
            corazones[k].gameObject.SetActive(existe || k < Actual);
            corazones[k].color = lleno ? new Color(1f, 0.25f, 0.3f) : new Color(0.3f, 0.3f, 0.35f, 0.7f);
        }
    }

    /// <summary>Anima el latido de los corazones que cambiaron.</summary>
    class AnimadorVidas : MonoBehaviour
    {
        CanvasGroup grupo;
        void Update()
        {
            // solo se ven mientras juegas (no en cinemáticas, derrota ni créditos)
            if (grupo == null) grupo = GetComponent<CanvasGroup>();
            var rt = (RectTransform)transform;   // justo debajo del panel del objetivo (que cambia de alto)
            rt.anchoredPosition = new Vector2(rt.anchoredPosition.x, -(UIObjetivo.Abajo + 12f + 23f));
            bool ver = Juego.Estado == Juego.Modo.Jugando || Juego.Estado == Juego.Modo.Pausa;
            grupo.alpha = Mathf.MoveTowards(grupo.alpha, ver ? 1f : 0f, Time.unscaledDeltaTime * 3f);
            for (int k = 0; k < corazones.Count; k++)
            {
                latido[k] = Mathf.MoveTowards(latido[k], 0f, Time.unscaledDeltaTime * 1.5f);
                float s = 1f + Mathf.Sin(latido[k] * Mathf.PI * 3f) * 0.35f * latido[k];
                if (corazones[k] != null) corazones[k].rectTransform.localScale = Vector3.one * s;
            }
        }
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Actual = 0; Ganadas = 0; inicio = 0; fila = null; corazones.Clear(); latido = new float[Dificultad.MaxVidas]; }
}
