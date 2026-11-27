using UnityEngine;

/// <summary>
/// Montón (o cubeta) de nieve: con E el elfo hace bolas de nieve (recarga el LanzadorNieve).
/// Es otro hijo de Interactuable, igual que las piezas y el reno.
/// </summary>
public class MontonNieve : Interactuable
{
    public override string Texto(Interactor quien) { return "Hacer bolas de nieve"; }

    public override bool PuedeInteractuar(Interactor quien)
    {
        var l = quien.GetComponent<LanzadorNieve>();
        return l != null && l.bolas < l.maximo;
    }

    public override void Interactuar(Interactor quien)
    {
        var l = quien.GetComponent<LanzadorNieve>();
        l.Recargar();
        GestorAudio.Efecto("recoger_nieve", 0.8f);
        UIAviso.Mensaje("Tienes " + l.bolas + " bolas de nieve.  [F] o [Clic] para lanzar", 2.5f);
    }
}
