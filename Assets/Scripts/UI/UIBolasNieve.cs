using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Contador de bolas de nieve (abajo a la derecha). Se crea solo por código y escucha
/// el evento AlCambiar del LanzadorNieve. Hace un pequeño "salto" de escala al cambiar.
/// </summary>
public class UIBolasNieve : MonoBehaviour
{
    public LanzadorNieve lanzador;
    Text texto; RectTransform caja; CanvasGroup grupo;
    float salto;

    void Start()
    {
        if (lanzador == null) lanzador = FindAnyObjectByType<LanzadorNieve>();
        var capa = UIConstructor.Capa("BolasNieve", 5);
        caja = UIConstructor.Rect("Caja", capa, new Vector2(1, 0), new Vector2(1, 0), new Vector2(330, 70), new Vector2(-200, 60));
        UIConstructor.Imagen(caja, new Color(0.04f, 0.06f, 0.12f, 0.7f));
        grupo = UIConstructor.Grupo(caja, 0f);
        var bola = UIConstructor.Rect("Icono", caja, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(40, 40), new Vector2(40, 0));
        UIConstructor.Imagen(bola, new Color(0.93f, 0.97f, 1f));
        texto = UIConstructor.Texto(UIConstructor.Rect("Texto", caja, Vector2.zero, Vector2.one, new Vector2(-80, 0), new Vector2(30, 0)), "", 30, Color.white, TextAnchor.MiddleLeft);
        if (lanzador != null) lanzador.AlCambiar += Actualizar;
        Actualizar();
    }

    void OnDestroy() { if (lanzador != null) lanzador.AlCambiar -= Actualizar; }

    void Actualizar()
    {
        if (lanzador == null) return;
        texto.text = "Bolas de nieve  <b>" + lanzador.bolas + "</b>/" + lanzador.maximo + "   <size=22>[F]</size>";
        salto = 1f;
    }

    void Update()
    {
        bool visible = lanzador != null && lanzador.bolas > 0 && (Juego.Estado == Juego.Modo.Jugando);
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, visible ? 1f : 0f, Time.deltaTime * 4f);
        salto = Mathf.MoveTowards(salto, 0f, Time.deltaTime * 4f);
        caja.localScale = Vector3.one * (1f + salto * 0.15f);
    }
}
