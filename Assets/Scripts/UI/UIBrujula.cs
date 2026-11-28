using UnityEngine;
using UnityEngine.AI;
using UnityEngine.UI;

/// <summary>
/// BRÚJULA: flechita dorada arriba al centro que apunta hacia lo que sigue.
///  ¿Hacia dónde apunta? (se decide cada medio segundo en ElegirObjetivo)
///   - Si llevas en la mano la pieza que sigue  -> al ÁRBOL.
///   - Si la pieza que sigue está bloqueada (la guirnalda enredada en el reno):
///       llevas la zanahoria -> al RENO;   si no -> a la ZANAHORIA.
///   - Si no -> a la pieza más cercana del tipo que pide la etapa actual.
///  ¿Hacia dónde gira? NO en línea recta (te mandaba a atravesar paredes): pide al NavMesh el CAMINO
///  (NavMesh.CalculatePath, el mismo que usan los cascanueces) y apunta a la siguiente vuelta del camino
///  (la puerta, la esquina). Los metros son metros de camino.
///  Para que no brinque de un lado a otro, solo cambia de pieza si la nueva está 30% más cerca (por camino).
///  El giro de la flecha = ángulo entre "hacia donde mira la cámara" y "hacia la siguiente vuelta", en el piso.
///  INTERFERENCIA (Difícil / Imposible): la flecha tiembla y gira loca y los metros salen "??":
///   - en Difícil e Imposible durante las VENTISCAS y siempre cerca de la Máquina 7 descompuesta (< 7 m);
///   - en Imposible además a ratos al azar (cada 25-45 s, unos 4-6 s).
/// </summary>
public class UIBrujula : MonoBehaviour
{
    RectTransform flecha; Text texto; CanvasGroup grupo;
    Transform objetivo; string nombreObjetivo;
    Transform jugador; Inventario inventario; ArbolNavidad arbol;
    float siguienteBusqueda;
    // interferencia
    Transform maquina; float locaHasta, siguienteLoca = 30f, giroLoco, tiempoJuego; bool locaAntes;

    void Start()
    {
        var j = GameObject.FindGameObjectWithTag("Player");
        if (j != null) { jugador = j.transform; inventario = j.GetComponent<Inventario>(); }
        arbol = ArbolNavidad.Instancia;
        camino = new NavMeshPath();
        var fe = FindAnyObjectByType<FabricaEstrella>(); if (fe != null) maquina = fe.transform;   // Siete (la Máquina 7)
        else { var mr = FindAnyObjectByType<MaquinaRota>(); if (mr != null) maquina = mr.transform; }

        var capa = UIConstructor.Capa("Brujula", 5);
        var raiz = UIConstructor.Rect("Contenido", capa, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(400, 150), new Vector2(0, -85));
        grupo = UIConstructor.Grupo(raiz, 0f);
        var aro = UIConstructor.Rect("Aro", raiz, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(84, 84), new Vector2(0, -42));
        UIConstructor.Imagen(aro, new Color(0.02f, 0.03f, 0.08f, 0.55f)).sprite = UIConstructor.SpriteCirculo();
        flecha = UIConstructor.Rect("Flecha", aro, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(54, 54));
        var img = UIConstructor.Imagen(flecha, new Color(1f, 0.82f, 0.3f)); img.sprite = UIConstructor.SpriteFlecha();
        UIConstructor.Sombra(img, 2f);
        texto = UIConstructor.Texto(UIConstructor.Rect("Texto", raiz, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(520, 50), new Vector2(0, -124)),
                                    "", 26, Color.white, TextAnchor.UpperCenter);
        UIConstructor.Sombra(texto, 2f);
    }

    int metrosMostrados = -1; string nombreMostrado, extraMostrado;
    Vector3 siguienteVuelta; float metrosCamino; string extra = "";
    NavMeshPath camino;   // se crea en Start (Unity no deja crearlo en el inicializador)

    void Update()
    {
        if (jugador == null || arbol == null) return;
        if (Time.time > siguienteBusqueda) { siguienteBusqueda = Time.time + 0.4f; ElegirObjetivo(); if (objetivo != null) CalcularCamino(objetivo.position, out siguienteVuelta, out metrosCamino); }

        bool visible = objetivo != null && (Juego.Estado == Juego.Modo.Jugando || Juego.Estado == Juego.Modo.Leyendo);
        grupo.alpha = Mathf.MoveTowards(grupo.alpha, visible ? 1f : 0f, Time.unscaledDeltaTime * 3f);
        if (objetivo == null) return;

        // ya casi llegas: apunta directo al objeto
        Vector3 meta = (objetivo.position - jugador.position).sqrMagnitude < 9f ? objetivo.position : siguienteVuelta;
        Transform cam = Camera.main != null ? Camera.main.transform : jugador;
        Vector3 hacia = meta - jugador.position; hacia.y = 0f;
        Vector3 frente = cam.forward; frente.y = 0f;
        float angulo = Vector3.SignedAngle(frente, hacia, Vector3.up);   // + = a la derecha
        bool loca = Interferencia();
        if (loca)
        {
            if (!locaAntes) { GestorAudio.Efecto("interferencia", 0.6f, 0.1f); giroLoco = angulo; }
            // gira rápido con cambios de sentido + temblor
            giroLoco += Time.unscaledDeltaTime * 420f * (Mathf.PerlinNoise(Time.unscaledTime * 0.9f, 7f) - 0.45f) * 2f;
            angulo = giroLoco + Mathf.Sin(Time.unscaledTime * 47f) * 9f;
            flecha.localRotation = Quaternion.Euler(0f, 0f, -angulo);
        }
        locaAntes = loca;
        if (loca)
        {
            if (metrosMostrados != -2) { metrosMostrados = -2; texto.text = "<color=#9fe0ff>¡Interferencia!</color>  <color=#ffd36b>?? m</color>"; }
            return;
        }
        // en la UI girar positivo en Z es girar a la IZQUIERDA, por eso el signo menos
        flecha.localRotation = Quaternion.Slerp(flecha.localRotation, Quaternion.Euler(0f, 0f, -angulo), Time.unscaledDeltaTime * 10f);

        // ¿está arriba? (la estrella sobre la repisa): avisamos que hay que subir
        Vector3 d = objetivo.position - jugador.position;
        string e = extra;
        if (e == "" && d.y > 1.4f && new Vector2(d.x, d.z).magnitude < 6f) e = "  <color=#9fe0ff>(arriba)</color>";

        int metros = Mathf.RoundToInt(metrosCamino);
        // solo reescribir el texto si cambió (armar el texto en cada cuadro crea basura de memoria => tirones)
        if (metros != metrosMostrados || !ReferenceEquals(nombreObjetivo, nombreMostrado) || e != extraMostrado)
        {
            metrosMostrados = metros; nombreMostrado = nombreObjetivo; extraMostrado = e;
            texto.text = nombreObjetivo + "  <color=#ffd36b>" + metros + " m</color>" + e;
        }
    }

    /// <summary>¿La brújula está fallando ahorita? (ver reglas arriba)</summary>
    bool Interferencia()
    {
        if (Dificultad.Elegido < 2 || Juego.Estado != Juego.Modo.Jugando) return false;
        tiempoJuego += Time.deltaTime;
        if (Ventisca.Activa) return true;
        if (maquina != null && !MaquinaRota.Reparada && (maquina.position - jugador.position).sqrMagnitude < 49f) return true;
        if (Dificultad.Elegido >= 3)
        {
            if (tiempoJuego >= siguienteLoca) { locaHasta = tiempoJuego + Random.Range(4f, 6f); siguienteLoca = locaHasta + Random.Range(25f, 45f); }
            if (tiempoJuego < locaHasta) return true;
        }
        return false;
    }

    /// <summary>Camino por el NavMesh hasta 'destino'. Devuelve la siguiente vuelta (a más de 1.5 m) y el largo.
    /// Si no hay camino (algo fuera del NavMesh) usa la línea recta.</summary>
    bool CalcularCamino(Vector3 destino, out Vector3 vuelta, out float largo)
    {
        vuelta = destino; largo = Vector3.Distance(jugador.position, destino);
        NavMeshHit a, b;
        if (!NavMesh.SamplePosition(jugador.position, out a, 2f, NavMesh.AllAreas)) return false;
        if (!NavMesh.SamplePosition(destino, out b, 3.5f, NavMesh.AllAreas)) return false;
        if (!NavMesh.CalculatePath(a.position, b.position, NavMesh.AllAreas, camino) || camino.status == NavMeshPathStatus.PathInvalid) return false;
        var c = camino.corners;
        if (c.Length < 2) return false;
        largo = 0f; vuelta = c[c.Length - 1];
        bool elegida = false;
        for (int i = 1; i < c.Length; i++)
        {
            largo += Vector3.Distance(c[i - 1], c[i]);
            if (!elegida && Vector3.Distance(Plano(c[i]), Plano(jugador.position)) > 1.5f) { vuelta = c[i]; elegida = true; }
        }
        largo += Vector3.Distance(b.position, destino) * 0.5f;
        return true;
    }

    static Vector3 Plano(Vector3 v) { v.y = 0f; return v; }

    float Largo(Vector3 p) { Vector3 v; float l; CalcularCamino(p, out v, out l); return l; }

    void ElegirObjetivo()
    {
        var anterior = objetivo;
        objetivo = null; extra = "";
        if (arbol.Completo) return;
        string tipo = arbol.EtapaActual.tipoPieza;
        var reno = FindAnyObjectByType<RenoGuirnalda>();
        var enMano = inventario != null && inventario.TieneObjeto ? inventario.EnMano : null;
        // historia 1.5: las etapas EXTERNAS buscan otra cosa y se entregan en otro lado
        Transform entrega = arbol.transform; string nombreEntrega = "Árbol";
        if (tipo == MaquinaRota.Etapa)
        {
            var mr = FindAnyObjectByType<MaquinaRota>();
            tipo = mr != null ? mr.tipoRefaccion : "Refaccion";
            if (mr != null) { entrega = mr.transform; nombreEntrega = "Corazón de Siete"; }
        }
        else if (tipo == FabricaEstrella.Etapa)
        {
            var fe = FindAnyObjectByType<FabricaEstrella>();
            tipo = fe != null ? fe.tipoRota : "EstrellaRota";
            if (fe != null) { entrega = fe.transform; nombreEntrega = "Siete"; }
        }

        // 1) ya traigo la pieza correcta -> a donde se entrega (el árbol, el corazón de Siete o Siete)
        if (enMano != null && enMano.tipo == tipo)
        { objetivo = entrega; nombreObjetivo = nombreEntrega; return; }

        // 2) la pieza de ese tipo más cercana POR CAMINO (con preferencia a la que ya seguíamos)
        Recogible mejor = null; float mejorLargo = float.MaxValue;
        foreach (var r in FindObjectsByType<Recogible>())
        {
            if (r.tipo != tipo || r.EnMano) continue;
            float l = Largo(r.transform.position);
            if (r.transform == anterior) l *= 0.7f;   // histéresis: no cambiar por poquito
            if (l < mejorLargo) { mejorLargo = l; mejor = r; }
        }
        if (mejor == null) return;

        // 3) está bloqueada (guirnalda en el reno): primero la zanahoria y luego el reno
        if (mejor.bloqueado && reno != null)
        {
            bool traigoComida = enMano != null && enMano.tipo == reno.tipoComida;
            if (!traigoComida)
                foreach (var r in FindObjectsByType<Recogible>())
                    if (r.tipo == reno.tipoComida && !r.EnMano) { objetivo = r.transform; nombreObjetivo = r.nombreVisible; Mayuscula(); AvisoSoltar(enMano); return; }
            objetivo = reno.transform; nombreObjetivo = "Reno"; return;
        }
        objetivo = mejor.transform; nombreObjetivo = mejor.nombreVisible; Mayuscula(); AvisoSoltar(enMano);
    }

    /// <summary>Si llevas algo que no sirve ahora, la brújula te recuerda soltarlo.</summary>
    void AvisoSoltar(Recogible enMano)
    {
        if (enMano != null) extra = "\n<size=20><color=#ffb0a0>Lo que llevas no va ahora: suéltalo con [Q]</color></size>";
    }

    void Mayuscula()
    {
        if (!string.IsNullOrEmpty(nombreObjetivo)) nombreObjetivo = char.ToUpper(nombreObjetivo[0]) + nombreObjetivo.Substring(1);
    }
}
