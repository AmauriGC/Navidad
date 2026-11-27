using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// COLECCIONABLE OPCIONAL: galletas de jengibre escondidas por el pueblo.
///  - Flota y gira (seno + rotación) para que se note de lejos; tiene una lucecita propia.
///  - Al tocarla (trigger) se suma al contador, suena, sale un mensaje y desaparece.
///  - El contador vive en variables static (Encontradas / Total) que se reinician en Juego.Reiniciar,
///    porque el proyecto tiene Domain Reload desactivado.
///  - Un texto pequeño en el HUD (arriba a la izquierda) muestra "Galletas 3/10" cuando ya encontraste una.
///  PREMIOS al juntar TODAS (Galleta.Todas):
///   1) PODER "leche y galletas" el resto de la noche: el elfo corre 20% más rápido (ElfoController) y las bolas
///      de nieve aturden el DOBLE de tiempo (Cascanueces.DuracionAturdido).
///   2) Se desbloquea el elfo secreto JENGIBRE en el menú (VarianteElfo.DesbloquearSecreto, se guarda para siempre).
///   3) FINAL ESPECIAL: Santa se come las galletas (DirectorJuego.Final + Guion.FinalGalletas) y sale en los créditos.
/// </summary>
[RequireComponent(typeof(SphereCollider))]
public class Galleta : MonoBehaviour
{
    public static int Encontradas, Total;
    public static bool Todas { get { return Total > 0 && Encontradas >= Total; } }
    static Text textoHUD;

    public float flotar = 0.12f, giro = 90f;
    Vector3 inicio; float fase;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Encontradas = 0; Total = 0; textoHUD = null; }

    void OnEnable() { Total++; }
    void OnDisable() { if (!recogida) Total--; }

    bool recogida;

    void Start()
    {
        inicio = transform.position;
        fase = Random.value * 10f;
        GetComponent<SphereCollider>().isTrigger = true;
    }

    void Update()
    {
        transform.position = inicio + Vector3.up * Mathf.Sin(Time.time * 2f + fase) * flotar;
        transform.Rotate(0f, giro * Time.deltaTime, 0f, Space.World);
    }

    void OnTriggerEnter(Collider otro)
    {
        if (recogida || !otro.CompareTag("Player")) return;
        recogida = true;
        Encontradas++;
        GestorAudio.Efecto("galleta", 0.9f, 0.1f);   // crujido + campanita
        if (Todas)
        {
            bool yaEraTuyo = PlayerPrefs.GetInt("ElfoSecreto", 0) == 1;   // ¿lo desbloqueaste en otra partida?
            VarianteElfo.DesbloquearSecreto();
            GestorAudio.Efecto("poder", 0.9f, 0f);      // ¡poder de galleta!
            TemblorCamara.Sacudir(0.15f);
            UIAviso.Mensaje("¡Encontraste TODAS las galletas de jengibre!\n★ PODER DE GALLETA: corres más rápido y tus bolas de nieve aturden el doble\n"
                + (yaEraTuyo ? "★ Santa te tiene preparado el FINAL ESPECIAL" : "★ Desbloqueaste al elfo secreto JENGIBRE"), 7f);
        }
        else UIAviso.Mensaje("¡Galleta de jengibre! " + Encontradas + "/" + Total, 2.5f);
        Vidas.PorGalleta(Encontradas);   // Difícil: cada 2 => +1 vida; Imposible: cada 5 (su mensaje reemplaza al de arriba)
        ActualizarHUD();
        gameObject.SetActive(false);
    }

    static void ActualizarHUD()
    {
        if (textoHUD == null)
        {
            var canvas = UIConstructor.Canvas;
            if (canvas == null) return;
            var rt = UIConstructor.Rect("Galletas", canvas.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(320, 40), new Vector2(30 + 22 + 160, -30 - 170 - 26 - (Dificultad.ConVidas ? 114 : 0)));   // debajo del panel Objetivo (30,-30, alto 170); con vidas, debajo de los corazones
            textoHUD = UIConstructor.Texto(rt, "", 26, new Color(1f, 0.85f, 0.6f), TextAnchor.MiddleLeft);
            rt.gameObject.AddComponent<SeguirPanel>();
            UIConstructor.Sombra(textoHUD);
        }
        textoHUD.text = "Galletas  " + Encontradas + "/" + Total + (Todas ? "   <color=#ffd36b>★ Poder de galleta</color>" : "");
    }

    /// <summary>El texto "Galletas x/10" va debajo del panel del objetivo (y debajo de los corazones si hay vidas).</summary>
    class SeguirPanel : MonoBehaviour
    {
        void LateUpdate()
        {
            var rt = (RectTransform)transform;
            float y = UIObjetivo.Abajo + 12f + (Dificultad.ConVidas ? 50f : 0f) + (Linterna.Activa ? 45f : 0f) + 20f;
            rt.anchoredPosition = new Vector2(rt.anchoredPosition.x, -y);
        }
    }

    /// <summary>Línea para los créditos.</summary>
    public static string Resumen()
    {
        if (Total == 0) return "";
        return "\n\nGalletas de jengibre encontradas: " + Encontradas + " / " + Total
            + (Todas ? "  ¡Todas! ★\nSanta se comió hasta las migajas. ¡Jengibre ya puede trabajar en el taller!"
                     : (PlayerPrefs.GetInt("ElfoSecreto", 0) == 1
                        ? "\n(Junta las " + Total + " en una misma noche para el final especial)"
                        : "\n(Junta las " + Total + " para un final especial y un elfo secreto)"));
    }
}
