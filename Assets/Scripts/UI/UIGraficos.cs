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
    Image botonAuto;
    Text textoAuto;
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
        // ---- calidad: Auto + Bajo / Medio / Alto / Personalizado (una sola fila arriba)
        var b0 = UIConstructor.Boton(p, "Auto", new Vector2(150, 60), new Vector2(-470, 290), Graficos.ActivarAutomatico, 32);
        botonAuto = (Image)b0.targetGraphic;
        int n = Graficos.NombresPreset.Length;
        botonesPreset = new Image[n];
        for (int i = 0; i < n; i++)
        {
            int k = i;
            float ancho = i == 3 ? 250 : 170;
            float px = -290 + i * 185 + (i == 3 ? 40 : 0);
            var b = UIConstructor.Boton(p, Graficos.NombresPreset[i], new Vector2(ancho, 60), new Vector2(px, 290), () => Graficos.ElegirPreset(k), 32);
            botonesPreset[i] = (Image)b.targetGraphic;
        }
        textoAuto = UIConstructor.Texto(UIConstructor.Rect("Explicacion", p, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1100, 36), new Vector2(0, 232)),
                                        "", 22, new Color(0.75f, 0.85f, 1f, 0.9f));

        // ---- ajustes (x desplazado para dejar lugar al valor a la derecha de los sliders)
        bool ssaoDisponible = Graficos.HaySsao;
        const float x = -80f, dy = -58f;
        float y = ssaoDisponible ? 160f : 140f;
        escala = Fila(p, "Resolución", new Vector2(x, y), 0.5f, 1f, v => Graficos.Cambiar(a => a.escala = v), out vEscala); y += dy;
        vSombras = UIConstructor.Selector(p, "Sombras", new Vector2(x, y), d => Graficos.Cambiar(a => a.sombras = Ciclo(a.sombras + d, 4))); y += dy;
        vSsao = UIConstructor.Selector(p, "Oclusión (SSAO)", new Vector2(x, y), d => Graficos.Cambiar(a => a.ssao = !a.ssao));
        if (ssaoDisponible) y += dy; else vSsao.transform.parent.parent.gameObject.SetActive(false);   // en teléfono no existe
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
        bool auto = Graficos.Automatico;
        for (int i = 0; i < botonesPreset.Length; i++)
            botonesPreset[i].color = i == Graficos.Preset ? (auto ? new Color(1f, 0.75f, 0.3f, 0.45f) : ColorElegido) : ColorBoton;
        botonAuto.color = auto ? ColorElegido : ColorBoton;
        textoAuto.text = auto ? "Automático: empieza en " + Graficos.NombresPreset[Graficos.Preset] + " y baja solo si el juego se traba"
                              : "Elegiste la calidad a mano · toca Auto para que se ajuste sola";
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
