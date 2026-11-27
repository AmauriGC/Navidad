using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Cartel, nota o carta que se puede LEER con E. Abre la hoja de papel de UIHistoria.
/// Opcionalmente, después de leerla, el elfo comenta algo (líneas de diálogo).
/// Mientras no se ha leído, un indicador (ej. un "!" que flota) llama la atención.
/// </summary>
public class Letrero : Interactuable
{
    public string titulo = "Nota";
    [TextArea(4, 12)] public string texto = "...";
    [Tooltip("Comentario del elfo después de leer (opcional).")]
    [TextArea(2, 4)] public string comentarioTilo = "";
    [Tooltip("Se apaga cuando ya se leyó.")]
    public GameObject indicadorNuevo;
    public UnityEvent alLeer;

    public bool Leido { get; private set; }

    void Awake()
    {
        if (string.IsNullOrEmpty(textoAccion) || textoAccion == "Usar") textoAccion = "Leer";
    }

    public override string Texto(Interactor quien) { return textoAccion + ": " + titulo; }

    public override void Interactuar(Interactor quien)
    {
        Linea[] lineas = string.IsNullOrEmpty(comentarioTilo)
            ? new[] { Linea.Nota(titulo, texto) }
            : new[] { Linea.Nota(titulo, texto), Linea.D("Tilo", comentarioTilo) };
        UIHistoria.Mostrar(lineas, () =>
        {
            if (!Leido) { Leido = true; if (indicadorNuevo) indicadorNuevo.SetActive(false); alLeer.Invoke(); }
        });
    }
}
