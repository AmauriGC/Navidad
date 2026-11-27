using UnityEngine;

/// <summary>
/// Clase base de TODO lo que el elfo puede usar con la tecla E:
/// piezas, mesa de trabajo, estación de envoltura, trineo, renos...
/// Cada uno hereda de aquí y decide qué pasa en Interactuar().
/// (Necesita un Collider para que el Interactor lo detecte.)
/// </summary>
public abstract class Interactuable : MonoBehaviour
{
    [Tooltip("Texto que aparece en pantalla: [E] <texto>")]
    public string textoAccion = "Usar";

    /// <summary>Texto del aviso. Se puede cambiar según el estado (ej. "Armar carrito").</summary>
    public virtual string Texto(Interactor quien) { return textoAccion; }

    /// <summary>¿Se puede usar ahora mismo? Si devuelve false el aviso no aparece.</summary>
    public virtual bool PuedeInteractuar(Interactor quien) { return enabled; }

    public abstract void Interactuar(Interactor quien);
}
