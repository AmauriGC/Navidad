using UnityEngine;
using UnityEngine.InputSystem;
using Unity.Cinemachine;

/// <summary>
/// Gira la cámara de Cinemachine alrededor del elfo con el mouse.
/// Cinemachine (OrbitalFollow) ya sabe "orbitar" a un objetivo; este script solo le dice
/// cuántos grados girar (eje horizontal) y qué tan arriba/abajo mirar (eje vertical).
/// Rueda del mouse: acercar/alejar. Click: volver a capturar el cursor si se liberó.
/// </summary>
[RequireComponent(typeof(CinemachineOrbitalFollow))]
public class CamaraOrbitaMouse : MonoBehaviour
{
    public float sensibilidad = 0.12f;
    public bool invertirY = false;
    public float zoomMin = 2.5f, zoomMax = 7f, velocidadZoom = 0.004f;

    CinemachineOrbitalFollow orbita;

    void Awake() { orbita = GetComponent<CinemachineOrbitalFollow>(); }

    void Update()
    {
        var mouse = Mouse.current;
        // Esc ahora lo maneja el DirectorJuego (menú de pausa). Si el juego no está en modo "Jugando"
        // (título, cinemática, letrero, pausa) la cámara no se mueve con el mouse.
        if (mouse == null || Juego.Bloqueado) return;
        if (mouse.leftButton.wasPressedThisFrame && Cursor.lockState != CursorLockMode.Locked) BloquearCursor(true);
        if (Cursor.lockState != CursorLockMode.Locked) return;

        Vector2 d = mouse.delta.ReadValue() * sensibilidad * Opciones.Sensibilidad;   // Opciones: menú de pausa

        // InputAxis es un struct: se copia, se modifica y se vuelve a asignar.
        var h = orbita.HorizontalAxis;
        h.Value = h.ClampValue(h.Value + d.x);   // Wrap: da la vuelta completa
        orbita.HorizontalAxis = h;

        var v = orbita.VerticalAxis;
        v.Value = v.ClampValue(v.Value + (invertirY ? d.y : -d.y));
        orbita.VerticalAxis = v;

        float scroll = mouse.scroll.ReadValue().y;
        if (Mathf.Abs(scroll) > 0.01f)
            orbita.Radius = Mathf.Clamp(orbita.Radius - scroll * velocidadZoom * orbita.Radius, zoomMin, zoomMax);
    }

    /// <summary>Pone la cámara DETRÁS del objetivo (se usa al terminar una cinemática: si no, regresaba al ángulo viejo
    /// y podía quedar metida en el árbol, que está en la capa que la cámara ignora).</summary>
    public void DetrasDe(Transform t, float alturaGrados = 20f)
    {
        if (orbita == null) orbita = GetComponent<CinemachineOrbitalFollow>();
        var h = orbita.HorizontalAxis;
        h.Value = h.ClampValue(Mathf.DeltaAngle(0f, t.eulerAngles.y));
        orbita.HorizontalAxis = h;
        var v = orbita.VerticalAxis;
        v.Value = v.ClampValue(alturaGrados);
        orbita.VerticalAxis = v;
    }

    public static void BloquearCursor(bool bloquear)
    {
        Cursor.lockState = bloquear ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !bloquear;
    }
}
