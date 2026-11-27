using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Muestra el aviso de interacción ("[E] Recoger rueda") abajo al centro de la pantalla.
/// Es un "singleton": hay uno solo en la escena y cualquier script lo usa con UIAviso.Mostrar(...).
/// Además puede mostrar MENSAJES temporales (UIAviso.Mensaje) que tienen prioridad
/// sobre el aviso de interacción durante unos segundos ("¡Rama colocada!").
/// </summary>
public class UIAviso : MonoBehaviour
{
    static UIAviso instancia;

    public Text texto;
    public CanvasGroup grupo;
    public float velocidadFade = 10f;

    float alfaObjetivo;
    float mensajeHasta;   // mientras Time.time < mensajeHasta, se ignora Mostrar()

    void Awake()
    {
        instancia = this; if (grupo) grupo.alpha = 0f;
        if (texto) texto.font = UIConstructor.Fuente;   // fuente bonita (ver UIConstructor)
    }

    /// <summary>Aviso de interacción (lo llama el Interactor cada frame).</summary>
    public static void Mostrar(string mensaje)
    {
        if (instancia == null || Time.time < instancia.mensajeHasta) return;
        bool hay = !string.IsNullOrEmpty(mensaje);
        if (hay) instancia.texto.text = mensaje;
        instancia.alfaObjetivo = hay ? 1f : 0f;
    }

    /// <summary>Mensaje importante que se queda unos segundos en pantalla.</summary>
    public static void Mensaje(string mensaje, float segundos = 2.5f)
    {
        if (instancia == null) return;
        instancia.texto.text = mensaje;
        instancia.alfaObjetivo = 1f;
        instancia.mensajeHasta = Time.time + segundos;
    }

    void Update()
    {
        // mientras hay un diálogo/nota abierto el aviso se esconde (iban en el mismo lugar y se encimaban)
        float objetivo = UIHistoria.Abierta || Juego.Estado == Juego.Modo.Pausa ? 0f : alfaObjetivo;   // en pausa no se encima con el menú
        if (grupo) grupo.alpha = Mathf.MoveTowards(grupo.alpha, objetivo, velocidadFade * Time.unscaledDeltaTime);
    }
}
