using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// GALLETAS NOCHEBUENA (historia 1.5): las 10 galletas de la charola de Santa, horneadas por Jengibre.
/// Cada una tiene una FORMA y una LETRA (índice 0..9 = N·O·C·H·E·B·U·E·N·A, ver Guion.FormaGalleta).
///  - Flota y gira para que se note de lejos; al tocarla (trigger) se guarda "en la bolsa" (Galleta.EnBolsa).
///  - En Difícil/Imposible cada galleta RECOGIDA cuenta para las vidas (Vidas.PorGalleta), como antes.
///  - Se ve con su forma: al empezar esconde el muñequito viejo y pone su GalletaForma_N (Galletas_Formas.glb).
///  - HUD: la palabra N O C H E B U E N A; las letras que traes en blanco y las que ya están en la charola en dorado.
///  PREMIOS: ahora se ganan al LLENAR LA CHAROLA (CharolaGalletas), no solo al juntarlas:
///   poder de galleta (corres +20%, bolas de nieve aturden el doble), elfo secreto JENGIBRE y final especial.
/// El estado vive en variables static que se reinician solas (el proyecto tiene Domain Reload desactivado).
/// </summary>
[RequireComponent(typeof(SphereCollider))]
public class Galleta : MonoBehaviour
{
    public static int Encontradas, Total;
    /// <summary>Galletas recogidas que todavía no se acomodan en la charola.</summary>
    public static readonly HashSet<int> EnBolsa = new HashSet<int>();
    /// <summary>Galletas ya acomodadas en la charola.</summary>
    public static readonly HashSet<int> Puestas = new HashSet<int>();
    /// <summary>La charola está llena: poder de galleta, Jengibre y final especial.</summary>
    public static bool CharolaLlena;
    public static bool Todas { get { return CharolaLlena; } }
    static Text textoHUD;

    [Tooltip("0..9 = N O C H E B U E N A. -1 = se saca del nombre (Galleta_3 -> 3).")]
    public int indice = -1;
    [Tooltip("Escala de la forma (las formas miden ~0.42 m; la galleta vieja ~0.5 m).")]
    public float escalaForma = 1.25f;
    public float flotar = 0.12f, giro = 90f;
    Vector3 inicio; float fase;
    bool recogida;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar() { Encontradas = 0; Total = 0; textoHUD = null; EnBolsa.Clear(); Puestas.Clear(); CharolaLlena = false; }

    void OnEnable() { Total++; }
    void OnDisable() { if (!recogida) Total--; }

    void Start()
    {
        inicio = transform.position;
        fase = Random.value * 10f;
        GetComponent<SphereCollider>().isTrigger = true;
        if (indice < 0) { int n; string s = name.Substring(name.LastIndexOf('_') + 1); if (int.TryParse(s, out n)) indice = n; }
        PonerForma();
    }

    /// <summary>Cambia el muñequito de jengibre por la forma con letra que le toca.</summary>
    void PonerForma()
    {
        var charola = FindAnyObjectByType<CharolaGalletas>();
        var modelo = charola != null ? charola.Forma(indice) : null;
        if (modelo == null) return;
        foreach (var r in GetComponentsInChildren<MeshRenderer>()) r.enabled = false;
        var f = Instantiate(modelo, transform);
        f.name = "Forma"; f.transform.localPosition = Vector3.zero; f.transform.localRotation = Quaternion.identity;
        f.transform.localScale = Vector3.one * escalaForma;
        foreach (var r in f.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
    }

    void Update()
    {
        transform.position = inicio + Vector3.up * Mathf.Sin(Time.time * 2f + fase) * flotar;
        transform.Rotate(0f, giro * Time.deltaTime, 0f, Space.World);
    }

    void OnTriggerEnter(Collider otro)
    {
        if (recogida || !otro.CompareTag("Player")) return;
        recogida = true;
        Encontradas++;
        if (indice >= 0) EnBolsa.Add(indice);
        GestorAudio.Efecto("galleta", 0.9f, 0.1f);   // crujido + campanita
        if (Encontradas == 1) UIHistoria.Mostrar(Guion.PrimeraGalleta);
        if (Encontradas >= Total && Total > 0)
            UIAviso.Mensaje("¡Encontraste las " + Total + " galletas!\nLlévalas a la charola de Santa, junto a la chimenea.", 6f);
        else if (indice >= 0 && indice < Guion.FormaGalleta.Length)
            UIAviso.Mensaje(Guion.AvisoGalleta(indice, Encontradas, Total), 3f);
        Vidas.PorGalleta(Encontradas);   // Difícil: cada 2 => +1 vida; Imposible: cada 5 (su mensaje reemplaza al de arriba)
        ActualizarHUD();
        gameObject.SetActive(false);
    }

    /// <summary>"N O C H E B U E N A": dorado = en la charola · blanco = en la bolsa · gris = falta.</summary>
    public static void ActualizarHUD()
    {
        if (textoHUD == null)
        {
            var canvas = UIConstructor.Canvas;
            if (canvas == null) return;
            var rt = UIConstructor.Rect("Galletas", canvas.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(760, 40), new Vector2(30 + 22 + 260, -30 - 170 - 26 - (Dificultad.ConVidas ? 114 : 0)));
            textoHUD = UIConstructor.Texto(rt, "", 26, new Color(1f, 0.85f, 0.6f), TextAnchor.MiddleLeft);
            rt.gameObject.AddComponent<SeguirPanel>();
            UIConstructor.Sombra(textoHUD);
        }
        var sb = new System.Text.StringBuilder("Galletas  ");
        for (int i = 0; i < Guion.PalabraGalletas.Length; i++)
        {
            string c = Puestas.Contains(i) ? "#ffd36b" : (EnBolsa.Contains(i) ? "#ffffff" : "#ffffff40");
            sb.Append("<color=").Append(c).Append(">").Append(Guion.PalabraGalletas[i]).Append("</color> ");
        }
        if (CharolaLlena) sb.Append("  <color=#ffd36b>★ Poder de galleta</color>");
        textoHUD.text = sb.ToString();
    }

    /// <summary>El texto de galletas va debajo del panel del objetivo (y debajo de los corazones si hay vidas).</summary>
    class SeguirPanel : MonoBehaviour
    {
        void LateUpdate()
        {
            var rt = (RectTransform)transform;
            // como los corazones: solo mientras juegas (en cinemáticas y diálogos se esconde)
            bool ver = Juego.Estado == Juego.Modo.Jugando || Juego.Estado == Juego.Modo.Pausa || (Juego.Estado == Juego.Modo.Cinematica && CharolaGalletas.Abierta);
            if (textoHUD != null && textoHUD.enabled != ver) textoHUD.enabled = ver;
            float y = UIObjetivo.Abajo + 12f + (Dificultad.ConVidas ? 50f : 0f) + (Linterna.Activa ? 45f : 0f) + 20f;
            rt.anchoredPosition = new Vector2(rt.anchoredPosition.x, -y);
        }
    }

    /// <summary>Línea para los créditos.</summary>
    public static string Resumen()
    {
        if (Total == 0) return "";
        return "\n\nGalletas NOCHEBUENA: " + Encontradas + " / " + Total + " encontradas, " + Puestas.Count + " en la charola"
            + (CharolaLlena ? "  ¡Charola completa! ★\nSanta se comió hasta las migajas. ¡Jengibre ya trabaja en el taller!"
                            : (PlayerPrefs.GetInt("ElfoSecreto", 0) == 1
                               ? "\n(Llena la charola en una misma noche para el final especial)"
                               : "\n(Llena la charola de Santa para un final especial y un elfo secreto)"));
    }
}
