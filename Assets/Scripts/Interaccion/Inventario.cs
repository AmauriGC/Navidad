using UnityEngine;

/// <summary>
/// El elfo carga UN objeto a la vez. Al tomarlo, el objeto se vuelve hijo del "PuntoMano"
/// del modelo (así se mueve junto con el elfo) y se apaga su física.
/// </summary>
public class Inventario : MonoBehaviour
{
    [Tooltip("Punto del modelo donde se sostiene el objeto (empty 'PuntoMano' de Blender).")]
    public Transform puntoMano;

    public Recogible EnMano { get; private set; }
    public bool TieneObjeto { get { return EnMano != null; } }

    public bool Tomar(Recogible r)
    {
        if (TieneObjeto || r == null) return false;
        EnMano = r;
        r.AlTomar(puntoMano != null ? puntoMano : transform);
        GestorAudio.Efecto("recoger");
        return true;
    }

    /// <summary>Deja el objeto en el piso frente al elfo.</summary>
    public void Soltar()
    {
        if (!TieneObjeto) return;
        var r = EnMano; EnMano = null;
        r.AlSoltar(transform.position + transform.forward * 0.8f + Vector3.up * 0.5f);
        GestorAudio.Efecto("soltar");
    }

    /// <summary>Saca el objeto de las manos para dárselo a una estación (mesa, trineo...).</summary>
    public Recogible Entregar()
    {
        var r = EnMano; EnMano = null;
        return r;
    }
}
