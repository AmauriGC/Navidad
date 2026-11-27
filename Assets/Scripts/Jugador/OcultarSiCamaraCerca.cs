using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Cuando la cámara queda MUY cerca del elfo (por ejemplo, de espaldas contra un pino la cámara se acerca
/// para no atravesarlo), el modelo taparía toda la pantalla. Este script lo vuelve invisible en ese momento,
/// pero deja su SOMBRA (ShadowCastingMode.ShadowsOnly) para que el jugador siga sabiendo dónde está.
/// Usa shadowCastingMode y no "enabled", así no choca con otros scripts que ocultan al elfo en cinemáticas.
/// </summary>
public class OcultarSiCamaraCerca : MonoBehaviour
{
    public float distanciaOcultar = 1.1f;   // más cerca que esto: invisible
    public Transform centro;                // punto a medir (el ObjetivoCamara, a la altura del pecho/cabeza)

    Renderer[] partes;
    bool oculto;

    void Start()
    {
        partes = GetComponentsInChildren<Renderer>(true);
        if (centro == null) centro = transform;
    }

    void LateUpdate()
    {
        var cam = Camera.main;
        if (cam == null) return;
        bool ocultar = Vector3.Distance(cam.transform.position, centro.position) < distanciaOcultar;
        if (ocultar == oculto) return;
        oculto = ocultar;
        foreach (var r in partes)
            if (r != null && !(r is ParticleSystemRenderer))
                r.shadowCastingMode = ocultar ? ShadowCastingMode.ShadowsOnly : ShadowCastingMode.On;
    }
}
