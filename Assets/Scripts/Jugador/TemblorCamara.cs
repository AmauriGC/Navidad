using UnityEngine;
using Unity.Cinemachine;

/// <summary>
/// TEMBLOR DE CÁMARA: una "extensión" de Cinemachine. Cinemachine calcula la posición de la cámara
/// por etapas (seguir, apuntar, ruido...); al final de la etapa de ruido nosotros le sumamos un
/// pequeño desplazamiento y giro que se apaga poco a poco.
/// Uso desde cualquier script:  TemblorCamara.Sacudir(0.5f);
/// El movimiento usa ruido Perlin (aleatorio pero suave), no saltos al azar.
/// </summary>
public class TemblorCamara : CinemachineExtension
{
    static float intensidad;          // 0..1, baja sola con el tiempo
    public float desplazamientoMax = 0.25f;   // metros
    public float giroMax = 3f;                // grados
    public float velocidad = 25f;
    public float recuperacion = 1.8f;         // cuánto baja por segundo

    public static void Sacudir(float fuerza) { intensidad = Mathf.Clamp01(Mathf.Max(intensidad, fuerza)); }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { intensidad = 0f; }   // Domain Reload desactivado

    protected override void PostPipelineStageCallback(CinemachineVirtualCameraBase vcam, CinemachineCore.Stage stage, ref CameraState state, float deltaTime)
    {
        if (stage != CinemachineCore.Stage.Noise || intensidad <= 0f) return;
        float t = Time.time * velocidad;
        float k = intensidad * intensidad;   // al cuadrado: se apaga más natural
        Vector3 d = new Vector3(Mathf.PerlinNoise(t, 0f) - 0.5f, Mathf.PerlinNoise(0f, t) - 0.5f, 0f) * 2f * desplazamientoMax * k;
        float giro = (Mathf.PerlinNoise(t, t) - 0.5f) * 2f * giroMax * k;
        state.PositionCorrection += state.GetCorrectedOrientation() * d;
        state.OrientationCorrection = state.OrientationCorrection * Quaternion.Euler(0f, 0f, giro);
        if (deltaTime > 0f) intensidad = Mathf.Max(0f, intensidad - recuperacion * deltaTime);
    }
}
