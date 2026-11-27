using UnityEngine;

/// <summary>
/// Animaciones sencillas y reutilizables para dar vida a la escena, sin Animator:
///  - Girar: rota sin parar (engranes, estrella, ventiladores).
///  - Flotar: sube y baja suave (adornos, indicadores "!").
///  - Balancear: se mece como péndulo (lámparas colgantes, letreros con viento).
///  - Latir: crece y se encoge (cosas importantes que llaman la atención).
///  - Respirar: escala vertical muy leve (animales dormidos).
/// Todas usan funciones seno: valor = sin(tiempo · velocidad + desfase) · amplitud.
/// </summary>
public class AnimacionSimple : MonoBehaviour
{
    public enum Tipo { Girar, Flotar, Balancear, Latir, Respirar }
    public Tipo tipo = Tipo.Flotar;
    public float velocidad = 1f;
    public float amplitud = 1f;
    [Tooltip("Eje (local) de giro o balanceo.")]
    public Vector3 eje = Vector3.up;
    [Tooltip("Desfase aleatorio para que varios objetos no se muevan iguales.")]
    public bool desfaseAleatorio = true;

    Vector3 pos0, esc0; Quaternion rot0; float fase;

    void Start()
    {
        pos0 = transform.localPosition; esc0 = transform.localScale; rot0 = transform.localRotation;
        fase = desfaseAleatorio ? Random.value * 10f : 0f;
    }

    void Update()
    {
        float t = Time.time * velocidad + fase;
        switch (tipo)
        {
            case Tipo.Girar:
                transform.Rotate(eje, 60f * velocidad * amplitud * Time.deltaTime, Space.Self); break;
            case Tipo.Flotar:
                transform.localPosition = pos0 + Vector3.up * Mathf.Sin(t * 2f) * 0.1f * amplitud; break;
            case Tipo.Balancear:
                transform.localRotation = rot0 * Quaternion.AngleAxis(Mathf.Sin(t) * 8f * amplitud, eje); break;
            case Tipo.Latir:
                transform.localScale = esc0 * (1f + Mathf.Abs(Mathf.Sin(t * 2f)) * 0.12f * amplitud); break;
            case Tipo.Respirar:
                transform.localScale = new Vector3(esc0.x, esc0.y * (1f + Mathf.Sin(t * 1.5f) * 0.03f * amplitud), esc0.z); break;
        }
    }
}
