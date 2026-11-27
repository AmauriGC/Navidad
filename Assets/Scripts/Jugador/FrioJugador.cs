using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// FRÍO (Difícil / Imposible): lo que pasa cuando te pega una bola de un CASCANUECES NEVADO.
///  - Cada bola: FRÍO por 1.5 s => caminas a la mitad de velocidad. NO se acumula: si te pega otra mientras
///    tienes frío, el contador vuelve a 1.5 s (no suma 3 s).
///  - Si te pegan 3 bolas dentro de una ventana de 5 s => te CONGELAS: quedas dentro de un bloque de hielo
///    sin poder moverte unos segundos (se cuentan solo los golpes de los últimos 5 s).
///  - HUD: 3 copos abajo al centro (se prenden con cada golpe reciente), escarcha azul en las orillas de la pantalla
///    y copitos alrededor del elfo mientras tiene frío.
/// Se agrega solo al jugador la primera vez que lo golpean (no hace falta ponerlo en el prefab).
/// </summary>
public class FrioJugador : MonoBehaviour
{
    public const float DuracionFrio = 1.5f, VentanaGolpes = 5f, DuracionCongelado = 2.5f, Lentitud = 0.5f;
    public const int GolpesParaCongelar = 3;

    public static FrioJugador Del(GameObject jugador)
    {
        var f = jugador.GetComponent<FrioJugador>();
        return f != null ? f : jugador.AddComponent<FrioJugador>();
    }

    public bool TieneFrio => Time.time < frioHasta;
    public bool Congelado => Time.time < congeladoHasta;

    readonly List<float> golpes = new List<float>();
    float frioHasta = -1f, congeladoHasta = -1f;
    ElfoController elfo;
    GameObject bloque; ParticleSystem copitos;
    CanvasGroup grupoHUD; Image[] copos; Image escarcha;
    bool avisado;

    /// <summary>El modelo del bloque de hielo (BloqueHielo.glb); lo pone Dificultad desde un cascanueces nevado.</summary>
    public static GameObject modeloBloque;

    void Awake() { elfo = GetComponent<ElfoController>(); }

    /// <summary>Te pegó una bola de nieve enemiga.</summary>
    public void Golpe()
    {
        if (Congelado) return;   // ya estás congelado: no cuenta
        float ahora = Time.time;
        golpes.Add(ahora);
        golpes.RemoveAll(t => ahora - t > VentanaGolpes);
        frioHasta = ahora + DuracionFrio;            // se REINICIA, no se suma
        TemblorCamara.Sacudir(0.2f);
        GestorAudio.Efecto("impacto_nieve", 0.9f);
        UIFundido.Destello(new Color(0.6f, 0.85f, 1f, 0.25f));
        if (!avisado)
        {
            avisado = true;
            UIAviso.Mensaje("¡Te pegó un cascanueces NEVADO! El frío te hace lento.\n3 bolas en 5 segundos y te congelas. Lánzale una bola de nieve [F] para aturdirlo.", 5f);
        }
        if (golpes.Count >= GolpesParaCongelar) Congelar();
    }

    void Congelar()
    {
        golpes.Clear();
        congeladoHasta = Time.time + DuracionCongelado;
        frioHasta = congeladoHasta + DuracionFrio;   // al salir del hielo todavía tienes un poco de frío
        if (elfo != null) elfo.Inmovilizar(DuracionCongelado);
        GestorAudio.Efecto("congelar", 0.9f, 0f);
        TemblorCamara.Sacudir(0.5f);
        UIAviso.Mensaje("¡TE CONGELARON!", 2f);
        if (bloque == null && modeloBloque != null)
        {
            bloque = Instantiate(modeloBloque, transform);
            bloque.name = "BloqueHielo";
            foreach (var c in bloque.GetComponentsInChildren<Collider>()) Destroy(c);
            foreach (var r in bloque.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }
        if (bloque != null) { bloque.SetActive(true); bloque.transform.localPosition = Vector3.zero; bloque.transform.localRotation = Quaternion.identity; }
    }

    void Update()
    {
        // lentitud por frío (ElfoController multiplica su velocidad por esto)
        if (elfo != null) elfo.factorFrio = TieneFrio ? Lentitud : 1f;

        // bloque de hielo: aparece "creciendo" y al terminar se rompe
        if (bloque != null && bloque.activeSelf)
        {
            float queda = congeladoHasta - Time.time;
            if (queda <= 0f)
            {
                bloque.SetActive(false);
                GestorAudio.Efecto("descongelar", 0.9f, 0.05f);
                Romper();
            }
            else
            {
                float t = Mathf.Clamp01((DuracionCongelado - queda) / 0.25f);
                bloque.transform.localScale = Vector3.one * Mathf.Lerp(0.6f, 1f, 1f - (1f - t) * (1f - t));
            }
        }
        Copitos(TieneFrio);
        HUD();
    }

    // ------------------------------------------------------------------ efectos visuales
    void Copitos(bool prender)
    {
        if (copitos == null)
        {
            if (!prender) return;
            var go = new GameObject("CopitosFrio"); go.transform.SetParent(transform, false); go.transform.localPosition = Vector3.up * 0.8f;
            copitos = go.AddComponent<ParticleSystem>();
            copitos.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var m = copitos.main; m.loop = true; m.startLifetime = 0.9f; m.startSpeed = 0.3f; m.startSize = new ParticleSystem.MinMaxCurve(0.03f, 0.07f);
            m.startColor = new Color(0.85f, 0.95f, 1f); m.gravityModifier = -0.05f; m.simulationSpace = ParticleSystemSimulationSpace.World;
            var em = copitos.emission; em.rateOverTime = 28f;
            var sh = copitos.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.45f;
            var col = copitos.colorOverLifetime; col.enabled = true;
            var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                                              new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.2f), new GradientAlphaKey(0f, 1f) });
            col.color = g;
            go.GetComponent<ParticleSystemRenderer>().sharedMaterial = BolaNieve.matParticulas;
        }
        if (prender && !copitos.isEmitting) copitos.Play();
        else if (!prender && copitos.isEmitting) copitos.Stop();
    }

    void Romper()
    {
        // estallido de pedacitos de hielo
        BolaNieve.Puf(transform.position + Vector3.up * 0.8f, 60, new Color(0.7f, 0.9f, 1f), 2.5f);
    }

    void HUD()
    {
        if (grupoHUD == null)
        {
            var canvas = UIConstructor.Canvas; if (canvas == null) return;
            // escarcha en las orillas de la pantalla
            var pc = UIConstructor.PantallaCompleta("Escarcha", canvas.transform);
            escarcha = UIConstructor.Imagen(pc, new Color(0.7f, 0.9f, 1f, 0f)); escarcha.sprite = UIConstructor.SpriteVineta(); escarcha.raycastTarget = false;
            // 3 copos abajo al centro
            var fila = UIConstructor.Rect("CoposFrio", canvas.transform, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(200, 50), new Vector2(0, 270));   // arriba de la caja de avisos
            grupoHUD = UIConstructor.Grupo(fila, 0f);
            copos = new Image[GolpesParaCongelar];
            for (int k = 0; k < copos.Length; k++)
            {
                copos[k] = UIConstructor.Imagen(UIConstructor.Rect("Copo" + k, fila, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(42, 42), new Vector2((k - 1) * 52f, 0)), Color.white);
                copos[k].sprite = UIConstructor.SpriteCopo();
                UIConstructor.Sombra(copos[k], 2f);
            }
        }
        float ahora = Time.time;
        golpes.RemoveAll(t => ahora - t > VentanaGolpes);
        bool jugando = Juego.Estado == Juego.Modo.Jugando;
        bool ver = jugando && (golpes.Count > 0 || Congelado);
        grupoHUD.alpha = Mathf.MoveTowards(grupoHUD.alpha, ver ? 1f : 0f, Time.unscaledDeltaTime * 4f);
        for (int k = 0; k < copos.Length; k++)
        {
            bool lleno = Congelado || k < golpes.Count;
            copos[k].color = lleno ? new Color(0.55f, 0.85f, 1f) : new Color(1f, 1f, 1f, 0.25f);
            copos[k].rectTransform.localRotation = Quaternion.Euler(0, 0, lleno ? Mathf.Sin(ahora * 6f + k) * 8f : 0f);
        }
        float a = !jugando ? 0f : Congelado ? 0.6f : TieneFrio ? 0.32f : 0f;
        var c = escarcha.color; c.a = Mathf.MoveTowards(c.a, a, Time.unscaledDeltaTime * 2f); escarcha.color = c;
    }

    void OnDestroy()
    {
        if (grupoHUD != null) Destroy(grupoHUD.gameObject);
        if (escarcha != null) Destroy(escarcha.gameObject);
    }
}
