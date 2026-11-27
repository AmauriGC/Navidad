using System.Collections;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// TRANSICIONES: fundido a negro / desde negro, y destellos de color (ej. rojo cuando te atrapan).
/// Uso: yield return UIFundido.A(1f, 0.8f);   // a negro en 0.8 s
///      UIFundido.Destello(Color.red);
/// </summary>
public class UIFundido : MonoBehaviour
{
    static UIFundido inst;
    Image negro, destello;

    static UIFundido Inst
    {
        get
        {
            if (inst != null) return inst;
            var rt = UIConstructor.Capa("Fundido", 20);   // encima del juego y del banner, debajo de la historia
            inst = rt.gameObject.AddComponent<UIFundido>();
            inst.destello = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Destello", rt), new Color(1, 0, 0, 0));
            inst.negro = UIConstructor.Imagen(UIConstructor.PantallaCompleta("Negro", rt), new Color(0, 0, 0, 0));
            return inst;
        }
    }

    /// <summary>Lleva la pantalla negra al alfa indicado (1 = todo negro, 0 = se ve el juego).</summary>
    public static IEnumerator A(float alfa, float duracion)
    {
        var img = Inst.negro;
        float inicio = img.color.a;
        for (float t = 0f; t < 1f; t += Time.unscaledDeltaTime / Mathf.Max(0.01f, duracion))
        {
            img.color = new Color(0, 0, 0, Mathf.Lerp(inicio, alfa, Mathf.SmoothStep(0f, 1f, t)));
            yield return null;
        }
        img.color = new Color(0, 0, 0, alfa);
    }

    public static void Negro(float alfa) { Inst.negro.color = new Color(0, 0, 0, alfa); }

    /// <summary>Destello de color que se desvanece solo.</summary>
    public static void Destello(Color c)
    {
        Inst.StopCoroutine("Apagar");
        Inst.destello.color = c;
        Inst.StartCoroutine("Apagar");
    }

    IEnumerator Apagar()
    {
        Color c = destello.color; float a0 = c.a;
        for (float t = 0f; t < 1f; t += Time.unscaledDeltaTime / 0.6f)
        {
            c.a = Mathf.Lerp(a0, 0f, t); destello.color = c;
            yield return null;
        }
        c.a = 0f; destello.color = c;
    }
}
