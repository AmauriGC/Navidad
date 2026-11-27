using UnityEngine;

/// <summary>
/// Hace que una luz "respire" como fuego, usando ruido Perlin (cambia suave, no al azar brusco).
/// También puede mover un poquito la luz para que las sombras bailen.
/// </summary>
[RequireComponent(typeof(Light))]
public class LuzParpadeante : MonoBehaviour
{
    public float variacion = 0.35f;     // cuánto cambia la intensidad (0.35 = ±35%)
    public float velocidad = 3f;
    public float movimiento = 0.05f;

    Light luz; float baseIntensidad; Vector3 basePos; float semilla;

    void Awake() { luz = GetComponent<Light>(); baseIntensidad = luz.intensity; basePos = transform.localPosition; semilla = Random.value * 100f; }

    void Update()
    {
        float t = Time.time * velocidad + semilla;
        float n = Mathf.PerlinNoise(t, 0.3f) * 2f - 1f;      // -1..1
        luz.intensity = baseIntensidad * (1f + n * variacion);
        transform.localPosition = basePos + new Vector3(Mathf.PerlinNoise(t, 5f) - 0.5f, Mathf.PerlinNoise(t, 9f) - 0.5f, 0) * movimiento;
    }
}
