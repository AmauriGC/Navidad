using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Pestaña "Gráficos" del menú de pausa: fila de presets (Bajo / Medio / Alto / Personalizado) y una fila por
/// ajuste. Mover cualquier ajuste cambia el preset a Personalizado; elegir un preset mueve todos los controles.
/// Todo se aplica al instante (ver Graficos.cs) y se guarda al cerrar la pausa.
/// </summary>
public class UIGraficos : MonoBehaviour
{
    Image[] botonesPreset;
    Slider escala, detalle, particulas, distancia;
    Text vEscala, vDetalle, vParticulas, vDistancia;
    Text vSombras, vSsao, vBloom, vLuces, vFps;

    static readonly Color ColorBoton = new Color(1f, 1f, 1f, 0.14f);
    static readonly Color ColorElegido = new Color(1f, 0.75f, 0.3f, 0.85f);

    public static UIGraficos Construir(RectTransform padre)
    {
        var panel = UIConstructor.PantallaCompleta("PanelGraficos", padre);
        var ui = panel.gameObject.AddComponent<UIGraficos>();
        ui.Crear(panel);
        return ui;
    }

    void Crear(RectTransform p)
    {
        // ---- presets
        int n = Graficos.NombresPreset.Length;
        botonesPreset = new Image[n];
        for (int i = 0; i < n; i++)
        {
            int k = i;
            var b = UIConstructor.Boton(p, Graficos.NombresPreset[i], new Vector2(i == 3 ? 260 : 190, 56),
                                        new Vector2(-345 + i * 210 + (i == 3 ? 35 : 0), 115), () => Graficos.ElegirPreset(k), 32);
            botonesPreset[i] = (Image)b.targetGraphic;
        }

        // ---- ajustes (x desplazado para dejar lugar al valor a la derecha de los sliders)
        const float x = -60f, y0 = 40f, dy = -55f;
        float y = y0;
        escala = Fila(p, "Resolución", new Vector2(x, y), 0.5f, 1f, v => Graficos.Cambiar(a => a.escala = v), out vEscala); y += dy;
        vSombras = UIConstructor.Selector(p, "Sombras", new Vector2(x, y), d => Graficos.Cambiar(a => a.sombras = Ciclo(a.sombras + d, 4))); y += dy;
        vSsao = UIConstructor.Selector(p, "Oclusión (SSAO)", new Vector2(x, y), d => Graficos.Cambiar(a => a.ssao = !a.ssao)); y += dy;
        vBloom = UIConstructor.Selector(p, "Resplandor", new Vector2(x, y), d => Graficos.Cambiar(a => a.bloom = !a.bloom)); y += dy;
        vLuces = UIConstructor.Selector(p, "Luces del pueblo", new Vector2(x, y), d => Graficos.Cambiar(a => a.luces = Ciclo(a.luces + d, 3))); y += dy;
        detalle = Fila(p, "Detalle lejano", new Vector2(x, y), 0.5f, 2f, v => Graficos.Cambiar(a => a.detalle = v), out vDetalle); y += dy;
        particulas = Fila(p, "Partículas", new Vector2(x, y), 0.2f, 1f, v => Graficos.Cambiar(a => a.particulas = v), out vParticulas); y += dy;
        distancia = Fila(p, "Distancia", new Vector2(x, y), 180f, 300f, v => Graficos.Cambiar(a => a.distancia = v), out vDistancia); y += dy;
        vFps = UIConstructor.Selector(p, "Cuadros por seg.", new Vector2(x, y), d => Graficos.Cambiar(a => a.fps = Ciclo(a.fps + d, 4)));

        Graficos.AlCambiar += Refrescar;
        Refrescar();
    }

    void OnDestroy() { Graficos.AlCambiar -= Refrescar; }

    static int Ciclo(int v, int n) { return ((v % n) + n) % n; }

    static Slider Fila(RectTransform p, string etiqueta, Vector2 pos, float min, float max, System.Action<float> alCambiar, out Text valor)
    {
        var s = UIConstructor.Deslizador(p, etiqueta, pos, min, alCambiar, min, max);
        var fila = s.transform.parent;
        valor = UIConstructor.Texto(UIConstructor.Rect("Valor", fila, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(150, 56), new Vector2(940, 0)),
                                    "", 30, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleLeft);
        return s;
    }

    /// <summary>Pone todos los controles con los valores actuales (sin disparar sus eventos).</summary>
    public void Refrescar()
    {
        var a = Graficos.Actual;
        for (int i = 0; i < botonesPreset.Length; i++)
            botonesPreset[i].color = i == Graficos.Preset ? ColorElegido : ColorBoton;
        escala.SetValueWithoutNotify(a.escala); vEscala.text = Mathf.RoundToInt(a.escala * 100f) + "%";
        detalle.SetValueWithoutNotify(a.detalle); vDetalle.text = "x" + a.detalle.ToString("0.0");
        particulas.SetValueWithoutNotify(a.particulas); vParticulas.text = Mathf.RoundToInt(a.particulas * 100f) + "%";
        distancia.SetValueWithoutNotify(a.distancia); vDistancia.text = Mathf.RoundToInt(a.distancia) + " m";
        vSombras.text = Graficos.NombresSombras[a.sombras];
        vSsao.text = a.ssao ? "Sí" : "No";
        vBloom.text = a.bloom ? "Sí" : "No";
        vLuces.text = Graficos.NombresLuces[a.luces];
        vFps.text = Graficos.NombresFps[a.fps];
    }
}
