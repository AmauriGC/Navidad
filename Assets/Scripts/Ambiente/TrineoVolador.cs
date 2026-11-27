using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// ANIMACIÓN DEL TRINEO DE SANTA (final). El DirectorJuego mueve el objeto raíz por la ruta; este script anima
/// lo de adentro para que se vea vivo:
///  - cada reno "galopa" en el aire (sube/baja y cabecea) con su propio desfase, y mueve la cabeza;
///  - el trineo se mece y se INCLINA en las curvas (Inclinar() lo llama el director con qué tan rápido gira);
///  - riendas (LineRenderer) de las manos de Santa al cuello de cada reno, con una pequeña comba;
///  - mientras está activo sigue flotando aunque ya no avance (para los diálogos del final).
/// </summary>
public class TrineoVolador : MonoBehaviour
{
    public Transform trineo;               // el modelo TrineoSanta (hijo)
    public Transform[] renos;              // hijos con el modelo de reno (mirando a +Z)
    public Material materialRiendas;
    public Vector3 manosSanta = new Vector3(0f, 1.35f, 0.75f);   // local al trineo raíz
    public Vector3 collarReno = new Vector3(0f, 1.15f, 0.55f);   // local a cada reno
    public float ritmo = 7f;

    readonly List<Vector3> basePos = new List<Vector3>();
    readonly List<Transform> cabezas = new List<Transform>();
    readonly List<LineRenderer> riendas = new List<LineRenderer>();
    Vector3 baseTrineo; float inclinacion, inclinacionObjetivo;

    void Awake()
    {
        if (trineo != null) baseTrineo = trineo.localPosition;
        foreach (var r in renos)
        {
            basePos.Add(r.localPosition);
            Transform cab = null;
            foreach (var t in r.GetComponentsInChildren<Transform>(true)) if (t.name.EndsWith("_Cabeza")) cab = t;
            cabezas.Add(cab);
            var go = new GameObject("Rienda"); go.transform.SetParent(transform, false);
            var lr = go.AddComponent<LineRenderer>();
            lr.positionCount = 8; lr.useWorldSpace = true; lr.widthMultiplier = 0.035f;
            lr.material = materialRiendas; lr.numCapVertices = 2;
            lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            lr.startColor = lr.endColor = new Color(0.45f, 0.22f, 0.08f);
            riendas.Add(lr);
        }
    }

    /// <summary>giro = grados por segundo que está girando la ruta (positivo = a la derecha).</summary>
    public void Inclinar(float giro) { inclinacionObjetivo = Mathf.Clamp(-giro * 0.6f, -25f, 25f); }

    void LateUpdate()
    {
        float t = Time.time * ritmo;
        // renos: galope con desfase (los de adelante un poco antes)
        for (int i = 0; i < renos.Length; i++)
        {
            float fase = t + i * 1.3f;
            renos[i].localPosition = basePos[i] + Vector3.up * (Mathf.Sin(fase) * 0.14f);
            renos[i].localRotation = Quaternion.Euler(Mathf.Sin(fase + 1.2f) * 9f, 0f, Mathf.Sin(fase * 0.5f) * 3f);
            if (cabezas[i] != null) cabezas[i].localRotation = Quaternion.Euler(Mathf.Sin(fase + 2.2f) * 10f, 0f, 0f);
        }
        // trineo: se mece y se inclina en las curvas
        inclinacion = Mathf.Lerp(inclinacion, inclinacionObjetivo, Time.deltaTime * 2f);
        if (trineo != null)
        {
            trineo.localPosition = baseTrineo + Vector3.up * Mathf.Sin(t * 0.45f) * 0.12f;
            trineo.localRotation = Quaternion.Euler(Mathf.Sin(t * 0.3f) * 2.5f, 0f, inclinacion + Mathf.Sin(t * 0.37f) * 3f);
        }
        // riendas con comba
        Vector3 a = transform.TransformPoint(manosSanta);
        for (int i = 0; i < renos.Length; i++)
        {
            Vector3 b = renos[i].TransformPoint(collarReno);
            var lr = riendas[i];
            for (int k = 0; k < lr.positionCount; k++)
            {
                float u = k / (lr.positionCount - 1f);
                lr.SetPosition(k, Vector3.Lerp(a, b, u) + Vector3.down * Mathf.Sin(u * Mathf.PI) * 0.18f);
            }
        }
    }
}
