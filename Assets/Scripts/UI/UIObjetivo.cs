using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Panel arriba a la izquierda: cuántas piezas lleva el árbol y qué sigue.
/// Escucha el evento AlCambiar del árbol (no revisa cada frame).
/// </summary>
public class UIObjetivo : MonoBehaviour
{
    public ArbolNavidad arbol;
    public Text titulo;
    public Text detalle;
    public Image barra;   // Image tipo "Filled"

    void Start()
    {
        // fuentes bonitas (ver UIConstructor): título navideño y detalle redondito
        if (titulo) { titulo.font = UIConstructor.FuenteTitulo; titulo.fontStyle = FontStyle.Normal; titulo.fontSize = Mathf.RoundToInt(titulo.fontSize * 1.15f); }
        if (detalle) detalle.font = UIConstructor.Fuente;
        if (arbol == null) arbol = ArbolNavidad.Instancia;
        if (arbol != null) arbol.AlCambiar += Actualizar;
        Actualizar();
    }

    CanvasGroup grupo;
    void Update()
    {
        // el panel de objetivo solo se ve mientras se juega (no en título ni cinemáticas)
        if (grupo == null) { grupo = GetComponent<CanvasGroup>(); if (grupo == null) grupo = gameObject.AddComponent<CanvasGroup>(); }
        bool visible = Juego.Estado == Juego.Modo.Jugando || Juego.Estado == Juego.Modo.Leyendo;
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, visible ? 1f : 0f, Time.unscaledDeltaTime * 3f);
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Abajo = 200f; }

    void OnDestroy() { if (arbol != null) arbol.AlCambiar -= Actualizar; }

    void Actualizar()
    {
        if (arbol == null) return;
        titulo.text = "Árbol de Navidad  " + arbol.PiezasColocadas + "/" + arbol.TotalPiezas;
        if (barra) barra.fillAmount = arbol.Progreso;
        if (arbol.Completo) { detalle.text = "¡El árbol está completo!"; Acomodar(); return; }
        var e = arbol.EtapaActual;
        string cuenta = e.partes.Length > 1 ? "  (" + arbol.EntregadasEtapa + "/" + e.partes.Length + ")" : "";
        detalle.text = "Siguiente: " + e.nombre + cuenta + "\n<i>" + e.pista + "</i>";
        Acomodar();
    }

    /// <summary>Borde de abajo del panel (en unidades del canvas de 1920x1080, medido desde arriba de la pantalla).
    /// Galletas y corazones se ponen debajo de esto (antes tenían una altura fija y la pista larga se les encimaba).</summary>
    public static float Abajo = 200f;

    /// <summary>El panel crece o se encoge según cuántos renglones ocupa la pista.</summary>
    void Acomodar()
    {
        var rt = (RectTransform)transform;
        var rd = detalle.rectTransform;
        float alto = Mathf.Max(60f, detalle.preferredHeight + 4f);
        rd.sizeDelta = new Vector2(rd.sizeDelta.x, alto);
        float panel = -rd.anchoredPosition.y + alto + 16f;
        rt.sizeDelta = new Vector2(rt.sizeDelta.x, panel);
        Abajo = -rt.anchoredPosition.y + panel;
    }
}
