using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Unity.Cinemachine;

/// <summary>
/// EL DIRECTOR: maneja el flujo completo del juego (como el director de una película).
///   Título → Intro narrada → Jugando ⇄ (Cinemáticas al terminar etapas, Pausa) → Final → Créditos
///
/// Las CINEMÁTICAS usan una segunda cámara de Cinemachine ("camCinematica"). Normalmente tiene
/// prioridad 0; cuando el director le sube la prioridad, el CinemachineBrain hace una transición
/// suave (blend) desde la cámara del jugador hacia ella, y al bajarla regresa sola.
/// Todo el flujo está hecho con CORRUTINAS: funciones que pueden "esperar" (yield) sin congelar el juego.
/// </summary>
public class DirectorJuego : MonoBehaviour
{
    [Header("Referencias")]
    public CinemachineCamera camCinematica;
    public Transform jugador;
    public ArbolNavidad arbol;
    public Cascanueces[] cascanueces;

    [Header("Tomas de cámara")]
    public Transform tomaTitulo;          // posición de cámara para el título (mira hacia miraTitulo)
    public Transform miraTitulo;
    public Transform tomaIntro;           // vista del tapete vacío
    public Transform tomaExterior;        // vista del taller desde afuera (final)

    [Header("Final")]
    public Transform trineo;              // trineo de Santa (vuela en el final)
    public Transform[] rutaTrineo;        // puntos de la ruta (curva)
    public Light[] lucesFinal;            // luces que se encienden al final
    public ParticleSystem fuegosFinal;    // destellos grandes del final

    [Header("Pruebas")]
    [Tooltip("Para probar rápido: empieza directo jugando.")]
    public bool saltarIntro = false;

    ElfoController elfo; Inventario inventario;
    RectTransform capaTitulo, capaPausa, capaCreditos, capaDerrota;
    CanvasGroup grupoTitulo, grupoPausa, grupoCreditos, grupoDerrota;
    Text textoPresiona, textoCreditos;
    bool primeraPieza, primeraPersecucion;
    HashSet<Cascanueces> presentados = new HashSet<Cascanueces>();
    Material cieloCopia;
    // selección de elfo
    RectTransform capaSeleccion; CanvasGroup grupoSeleccion;
    Text textoDerrotaTitulo, textoDerrotaSub;
    RectTransform capaDificultad; CanvasGroup grupoDificultad;
    RectTransform botonRegresar; bool regresarAElfo;
    Image[] tarjetas; Text[] tarjetasTexto;
    Text textoNombreElfo, textoDescElfo, flechaIzq, flechaDer; Image[] puntosElfo; RectTransform panelElfo;
    VarianteElfo variante;

    // ================================================================== INICIO
    void Start()
    {
        Time.timeScale = 1f;
        Dificultad.NuevaPartida();   // la escena se recarga al reintentar: vidas y dificultad desde cero
        Graficos.Aplicar();          // calidad gráfica guardada (preset o personalizada)
        if (jugador == null) jugador = GameObject.FindGameObjectWithTag("Player").transform;
        elfo = jugador.GetComponent<ElfoController>();
        inventario = jugador.GetComponent<Inventario>();
        if (arbol == null) arbol = ArbolNavidad.Instancia;
        if (cascanueces == null || cascanueces.Length == 0) cascanueces = FindObjectsByType<Cascanueces>();
        arbol.AlCompletarEtapa += EtapaTerminada;
        if (trineo) trineo.gameObject.SetActive(false);

        // el elfo elegido (Tilo / Nieves / Chispa): VarianteElfo va en el modelo (donde está ElfoAnimador)
        var anim = jugador.GetComponentInChildren<ElfoAnimador>(true);
        if (anim != null) { variante = anim.GetComponent<VarianteElfo>(); if (variante == null) variante = anim.gameObject.AddComponent<VarianteElfo>(); }

        // copia del cielo para poder pintarlo de amanecer sin modificar el material original
        if (RenderSettings.skybox != null) { cieloCopia = new Material(RenderSettings.skybox); RenderSettings.skybox = cieloCopia; }

        ConstruirUI();
        if (Juego.Reintento)
        {
            // "Reintentar" después de perder: directo a jugar, sin título ni intro
            Juego.Reintento = false;
            grupoTitulo.alpha = 0f;
            StartCoroutine(OtroIntento());
        }
        else if (saltarIntro)
        {
            Juego.Estado = Juego.Modo.Jugando;
            CamaraOrbitaMouse.BloquearCursor(true);
            grupoTitulo.alpha = 0f;
        }
        else StartCoroutine(PantallaTitulo());
    }

    void OnDestroy() { if (arbol != null) arbol.AlCompletarEtapa -= EtapaTerminada; }

    // ================================================================== UPDATE: teclas globales
    void Update()
    {
        var kb = Keyboard.current;
        bool esc = kb != null && kb.escapeKey.wasPressedThisFrame;
        bool r = kb != null && kb.rKey.wasPressedThisFrame;
        bool q = kb != null && kb.qKey.wasPressedThisFrame;

        if (Juego.Estado == Juego.Modo.Jugando && (esc || Tactil.Pausa)) Pausar(true);
        else if (Juego.Estado == Juego.Modo.Pausa)
        {
            if (esc || (kb != null && kb.enterKey.wasPressedThisFrame)) Pausar(false);
            else if (kb != null && kb.tabKey.wasPressedThisFrame) MostrarSeccion((seccion + 1) % NombresSeccion.Length);
            else if (r) Reintentar();
            else if (kb != null && kb.mKey.wasPressedThisFrame) MenuPrincipal();
            else if (q) Salir();
        }
        else if (Juego.Estado == Juego.Modo.Final)
        {
            // en los créditos (ganaste) un toque también sirve para jugar otra vez; en la derrota hay botones
            if (r || (Tactil.Activo && !Juego.Perdio && grupoCreditos.alpha > 0.9f && Tactil.Toque)) { if (Juego.Perdio) Reintentar(); else MenuPrincipal(); }
            else if (q) Salir();
        }

        if (Juego.Estado == Juego.Modo.Jugando) Consejos();
    }

    // Consejos que aparecen UNA sola vez, la primera vez que pasa algo
    void Consejos()
    {
        if (!primeraPieza && inventario != null && inventario.TieneObjeto && inventario.EnMano.tipo == arbol.EtapaActual?.tipoPieza)
        {
            primeraPieza = true;
            UIAviso.Mensaje("¡Encontraste una pieza! Llévala al tapete del centro y presiona [E] junto al árbol.\n[Q] para soltarla.", 4.5f);
        }
        if (!primeraPersecucion)
            foreach (var c in cascanueces)
                if (c != null && c.EstadoActual == Cascanueces.Estado.Persecucion)
                {
                    primeraPersecucion = true;
                    UIAviso.Mensaje("¡Te vio! ¡Corre con [Shift]! O lánzale una bola de nieve con [F].", 3f);
                    break;
                }
    }

    // ================================================================== TÍTULO E INTRO
    IEnumerator PantallaTitulo()
    {
        Juego.Estado = Juego.Modo.Titulo;
        CamaraOrbitaMouse.BloquearCursor(false);
        UIFundido.Negro(1f);
        Tomar(tomaTitulo, miraTitulo, true);
        StartCoroutine(UIFundido.A(0f, 2f));
        // aparece el título
        for (float t = 0f; t < 1f; t += Time.deltaTime / 1.5f) { grupoTitulo.alpha = t; yield return null; }
        grupoTitulo.alpha = 1f;
        // espera tecla; mientras, la cámara se mueve lento (paneo)
        Vector3 p0 = tomaTitulo.position;
        float tiempo = 0f;
        while (true)
        {
            tiempo += Time.deltaTime;
            camCinematica.transform.position = p0 + new Vector3(Mathf.Sin(tiempo * 0.15f) * 3f, Mathf.Sin(tiempo * 0.1f) * 0.6f, 0f);
            camCinematica.transform.LookAt(miraTitulo);
            textoPresiona.color = new Color(1f, 1f, 1f, 0.55f + 0.45f * Mathf.Sin(tiempo * 3f));
            var kb = Keyboard.current; var m = Mouse.current;
            if (Juego.PruebaAutomatica && tiempo > 2f) break;
            if ((kb != null && (kb.enterKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame)) || (m != null && m.leftButton.wasPressedThisFrame) || Tactil.Toque) break;
            yield return null;
        }
        yield return SeleccionElfo();
        yield return Intro();
    }

    // ================================================================== ELEGIR ELFO
    // La cámara se pone frente al elfo, que gira presumiendo su ropa. [A]/[D] o flechas (o clic a los lados) cambian
    // de elfo EN VIVO (VarianteElfo.Aplicar); [Enter]/[Espacio] confirma. Se guarda en PlayerPrefs.
    IEnumerator SeleccionElfo()
    {
        if (variante == null) yield break;
        // se va el título y fundido a negro
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.5f) { grupoTitulo.alpha = 1f - t; yield return null; }
        grupoTitulo.alpha = 0f;
        yield return UIFundido.A(1f, 0.4f);
        Transform modelo = variante.transform;
        Quaternion rot0 = modelo.localRotation; Vector3 esc0 = modelo.localScale;
        // el elfo queda en el tercio izquierdo de la pantalla (la cámara mira un poco a su lado); a la derecha va el panel
        // (la cámara se gira en cada cuadro con ColocarCamaraElfo para que el elfo caiga justo entre las flechas fijas)
        Vector3 pos = jugador.position + jugador.forward * 2.5f + Vector3.up * 1.05f;
        camCinematica.transform.position = pos;
        ColocarCamaraElfo();
        // luz cálida de frente SOLO mientras eliges (en el taller la luz le llega por detrás y se ve oscuro)
        var luz = new GameObject("LuzSeleccion").AddComponent<Light>();
        luz.type = LightType.Point; luz.color = new Color(1f, 0.9f, 0.75f); luz.intensity = 2.5f; luz.range = 5f; luz.shadows = LightShadows.None;
        luz.transform.position = jugador.position + jugador.forward * 1.3f + Vector3.up * 1.6f + jugador.right * 0.5f;
        camCinematica.Priority.Value = 100; camCinematica.PreviousStateIsValid = false;
        int i = VarianteElfo.Elegido;
        MostrarElfo(i);
        yield return null;
        StartCoroutine(UIFundido.A(0f, 0.6f));
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.5f) { grupoSeleccion.alpha = t; yield return null; }
        grupoSeleccion.alpha = 1f;

        while (true)      // elegir elfo -> dificultad; con "Regresar" en la dificultad se vuelve aquí
        {
        float tiempo = 0f, salto = 0f, empujeIzq = 0f, empujeDer = 0f;
        flechaIzq.rectTransform.anchorMin = flechaIzq.rectTransform.anchorMax = new Vector2(0.5f, 0.5f);
        flechaDer.rectTransform.anchorMin = flechaDer.rectTransform.anchorMax = new Vector2(0.5f, 0.5f);
        while (true)
        {
            tiempo += Time.deltaTime;
            // FLECHAS FIJAS: el elfo va en ElfoX del ancho y las flechas a una distancia fija de él (no se recalculan
            // con la posición del modelo, que se movía al dar el brinquito y en el teléfono quedaban muy pegadas).
            // Es la cámara la que se acomoda para que el elfo caiga en ese punto.
            ColocarCamaraElfo();
            float ancho = capaSeleccion.rect.width;
            float centroX = (ElfoX - 0.5f) * ancho;
            float sep = Mathf.Max(260f, ancho * 0.15f);
            var kb = Keyboard.current; var m = Mouse.current;
            int cambio = 0;
            if (kb != null && (kb.aKey.wasPressedThisFrame || kb.leftArrowKey.wasPressedThisFrame)) cambio = -1;
            if (kb != null && (kb.dKey.wasPressedThisFrame || kb.rightArrowKey.wasPressedThisFrame)) cambio = 1;
            bool tocoElfo = false;
            Vector2 toque;
            if (Tactil.Toque && RectTransformUtility.ScreenPointToLocalPointInRectangle(capaSeleccion, Tactil.PosicionToque, null, out toque))
            {   // clic o dedo: en una flecha (zona generosa) = cambiar; sobre el elfo = elegirlo
                float dx = toque.x - centroX;
                if (dx < -sep * 0.55f && dx > -sep - 170f) cambio = -1;
                else if (dx > sep * 0.55f && dx < sep + 170f) cambio = 1;
                else if (Mathf.Abs(dx) <= sep * 0.55f && tiempo > 0.3f) tocoElfo = true;
            }
            if (cambio != 0)
            {
                i = (i + cambio + VarianteElfo.Elfos.Length) % VarianteElfo.Elfos.Length;
                MostrarElfo(i); salto = 1f;
                if (cambio < 0) empujeIzq = 1f; else empujeDer = 1f;
                GestorAudio.Efecto("cambio", 0.7f);
            }
            bool listo = (kb != null && (kb.enterKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame)) || tocoElfo || (Juego.PruebaAutomatica && tiempo > 1f);
            if (listo && !VarianteElfo.Desbloqueado(i))
            {   // el secreto todavía no se puede elegir
                listo = false; salto = 0.6f;
                GestorAudio.Efecto("tick", 0.8f);
                textoDescElfo.text = "<color=#ffb0a0>¡Todavía no!</color> Encuentra las 10 galletas de jengibre\nescondidas por el pueblo para desbloquearlo.";
            }
            // el elfo gira despacio de un lado a otro y da un brinquito al cambiar
            salto = Mathf.MoveTowards(salto, 0f, Time.deltaTime * 2.5f);
            modelo.localRotation = rot0 * Quaternion.Euler(0f, Mathf.Sin(tiempo * 0.9f) * 40f, 0f);
            float pop = Mathf.Sin(salto * Mathf.PI) * 0.12f;
            modelo.localScale = esc0 * (1f + pop);
            empujeIzq = Mathf.MoveTowards(empujeIzq, 0f, Time.deltaTime * 4f); empujeDer = Mathf.MoveTowards(empujeDer, 0f, Time.deltaTime * 4f);
            // la flecha > ya no puede caer encima del panel: el panel se acomoda A LA DERECHA de la flecha
            // (antes el panel iba fijo al 70% del ancho y su orilla izquierda tapaba la >)
            flechaIzq.rectTransform.anchoredPosition = new Vector2(centroX - sep - 30f * empujeIzq, 0f);
            flechaDer.rectTransform.anchoredPosition = new Vector2(centroX + sep + 30f * empujeDer, 0f);
            AcomodarPanelElfo(centroX + sep + 100f);
            float brillo = 0.6f + 0.4f * Mathf.Sin(tiempo * 3f);
            flechaIzq.color = flechaDer.color = new Color(1f, 0.85f, 0.45f, brillo);
            if (listo) break;
            yield return null;
        }
        VarianteElfo.Elegido = i;
        GestorAudio.Efecto("etapa", 0.7f);
        // un brinco de gusto y se acomoda
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.45f)
        {
            modelo.localRotation = Quaternion.Slerp(modelo.localRotation, rot0, t);
            modelo.localScale = esc0 * (1f + Mathf.Sin(t * Mathf.PI) * 0.15f);
            grupoSeleccion.alpha = 1f - t;
            yield return null;
        }
        modelo.localRotation = rot0; modelo.localScale = esc0; grupoSeleccion.alpha = 0f;
        yield return SeleccionDificultad();
        if (!regresarAElfo) break;
        MostrarElfo(i);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.3f) { grupoSeleccion.alpha = t; yield return null; }
        grupoSeleccion.alpha = 1f;
        }
        yield return UIFundido.A(1f, 0.5f);
        Destroy(luz.gameObject);
    }

    /// <summary>Los créditos crecen (galletas, dificultad, medalla) y en pantallas anchas de teléfono el lienzo mide
    /// ~966 de alto: se cortaban arriba y abajo. Se mide el alto real del texto y se achica para que quepa todo.</summary>
    void AjustarCreditos()
    {
        if (textoCreditos == null) return;
        var rt = textoCreditos.rectTransform;
        float alto = textoCreditos.preferredHeight;
        float disponible = capaCreditos.rect.height - 70f;
        rt.sizeDelta = new Vector2(rt.sizeDelta.x, alto);
        rt.localScale = Vector3.one * Mathf.Min(1f, disponible / Mathf.Max(1f, alto));
    }

    /// <summary>Pantalla de dificultad (después de elegir elfo). Se recuerda la última elegida.</summary>
    IEnumerator SeleccionDificultad()
    {
        regresarAElfo = false;
        int i = Dificultad.Elegido;
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.35f) { grupoDificultad.alpha = t; MarcarDificultad(i, t); yield return null; }
        grupoDificultad.alpha = 1f;
        float tiempo = 0f;
        while (true)
        {
            tiempo += Time.deltaTime;
            var kb = Keyboard.current; var m = Mouse.current;
            int cambio = 0;
            if (kb != null && (kb.aKey.wasPressedThisFrame || kb.leftArrowKey.wasPressedThisFrame)) cambio = -1;
            if (kb != null && (kb.dKey.wasPressedThisFrame || kb.rightArrowKey.wasPressedThisFrame)) cambio = 1;
            bool listo = (kb != null && (kb.enterKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame)) || (Juego.PruebaAutomatica && tiempo > 1f);
            // regresar a elegir elfo: [Esc] / [Retroceso] o el botón de arriba a la izquierda
            if (tiempo > 0.3f && ((kb != null && (kb.escapeKey.wasPressedThisFrame || kb.backspaceKey.wasPressedThisFrame))
                || (Tactil.Toque && RectTransformUtility.RectangleContainsScreenPoint(botonRegresar, Tactil.PosicionToque, null))))
            {
                regresarAElfo = true;
                GestorAudio.Efecto("cambio", 0.7f);
                break;
            }
            if (Tactil.Toque && tiempo > 0.3f)
                for (int k = 0; k < tarjetas.Length; k++)
                    if (RectTransformUtility.RectangleContainsScreenPoint(tarjetas[k].rectTransform, Tactil.PosicionToque, null))
                    { if (k == i) listo = true; else cambio = k - i; }
            if (cambio != 0)
            {
                i = Mathf.Clamp(i + cambio, 0, tarjetas.Length - 1);
                GestorAudio.Efecto("cambio", 0.7f);
            }
            MarcarDificultad(i, tiempo);
            if (listo) break;
            yield return null;
        }
        if (!regresarAElfo) { Dificultad.Elegido = i; GestorAudio.Efecto("etapa", 0.7f); }
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.35f) { grupoDificultad.alpha = 1f - t; yield return null; }
        grupoDificultad.alpha = 0f;
    }

    /// <summary>La tarjeta elegida se hace grande y se ilumina; las otras quedan chicas y opacas.</summary>
    void MarcarDificultad(int i, float tiempo)
    {
        for (int k = 0; k < tarjetas.Length; k++)
        {
            bool sel = k == i;
            float objetivo = sel ? 1.08f + Mathf.Sin(tiempo * 3f) * 0.015f : 0.92f;
            var rt = tarjetas[k].rectTransform;
            rt.localScale = Vector3.one * Mathf.Lerp(rt.localScale.x, objetivo, Time.deltaTime * 12f);
            var c = Dificultad.Niveles[k].color;
            // opacas: el Outline de Unity dibuja una COPIA de la imagen detrás, si es transparente se ve rellena de color
            tarjetas[k].color = sel ? new Color(c.r * 0.3f, c.g * 0.3f, c.b * 0.3f, 1f) : new Color(0.06f, 0.07f, 0.12f, 1f);
            tarjetasTexto[k].color = new Color(0.88f, 0.92f, 1f, sel ? 1f : 0.5f);
        }
    }

    /// <summary>Fracción del ancho de la pantalla donde se ve el elfo en "Elige a tu elfo".</summary>
    const float ElfoX = 0.28f;

    /// <summary>Gira la cámara de la selección para que el elfo (a media altura) quede en ElfoX del ancho, sin
    /// importar la proporción de la pantalla (16:9 en PC, 20:9 en teléfono).</summary>
    void ColocarCamaraElfo()
    {
        var cam = camCinematica.transform;
        Vector3 objetivo = jugador.position + Vector3.up * 0.8f;
        Vector3 haciaElfo = objetivo - cam.position;
        float aspecto = (float)Screen.width / Mathf.Max(1, Screen.height);
        float tanMedioH = Mathf.Tan(camCinematica.Lens.FieldOfView * 0.5f * Mathf.Deg2Rad) * aspecto;
        // ángulo del elfo respecto al centro de la vista: negativo = a la izquierda
        float angulo = Mathf.Atan((2f * ElfoX - 1f) * tanMedioH) * Mathf.Rad2Deg;
        cam.rotation = Quaternion.AngleAxis(-angulo, Vector3.up) * Quaternion.LookRotation(haciaElfo);
    }

    /// <summary>Pone el panel del elfo entre 'orillaIzq' (justo después de la flecha >) y la orilla derecha de la
    /// pantalla. Si no cabe a tamaño completo, lo achica (escala) en vez de encimarlo sobre la flecha.</summary>
    void AcomodarPanelElfo(float orillaIzq)
    {
        if (panelElfo == null) return;
        float mitad = capaSeleccion.rect.width * 0.5f;
        float disponible = (mitad - 40f) - orillaIzq;
        float escala = Mathf.Clamp(disponible / 760f, 0.55f, 1f);
        float ancho = 760f * escala;
        panelElfo.anchorMin = panelElfo.anchorMax = new Vector2(0.5f, 0.5f);
        panelElfo.localScale = Vector3.one * escala;
        // centrado en el espacio libre (si sobra espacio no se pega a la flecha)
        float centro = orillaIzq + Mathf.Max(ancho, disponible) * 0.5f;
        panelElfo.anchoredPosition = new Vector2(centro, 0f);
    }

    void MostrarElfo(int i)
    {
        var d = VarianteElfo.Elfos[i];
        if (VarianteElfo.Desbloqueado(i))
        {
            variante.Aplicar(i);
            textoNombreElfo.text = d.nombre;
            textoDescElfo.text = d.descripcion;
        }
        else
        {
            variante.Silueta(i);
            textoNombreElfo.text = "???";
            textoDescElfo.text = "Elfo secreto.\nJunta las 10 galletas de jengibre para desbloquearlo.";
        }
        for (int k = 0; k < puntosElfo.Length; k++)
            puntosElfo[k].color = k == i ? new Color(1f, 0.85f, 0.45f, 1f) : new Color(1f, 1f, 1f, 0.35f);
    }

    IEnumerator Intro()
    {
        Juego.Estado = Juego.Modo.Cinematica;
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.8f) { grupoTitulo.alpha = 1f - t; yield return null; }
        grupoTitulo.alpha = 0f;
        yield return UIHistoria.Esperar(Guion.Intro);
        // vista del taller con el árbol desarmado
        UIFundido.Negro(1f);
        Tomar(tomaIntro, arbol.transform, true);
        yield return null;
        StartCoroutine(UIFundido.A(0f, 1.2f));
        yield return MoverCamara(tomaIntro.position, tomaIntro.position + tomaIntro.forward * 2f + Vector3.up * 0.5f, arbol.transform.position + Vector3.up, 4f, false);
        yield return UIHistoria.Esperar(Guion.IntroTaller);
        SoltarCamara();
        yield return new WaitForSeconds(0.8f);
        yield return UIBanner.Esperar("NUEVO OBJETIVO", "Arma el Gran Árbol antes del amanecer", "Primero: " + arbol.EtapaActual.nombre, 3.5f, new Color(0.6f, 0.9f, 1f));
        EmpezarAJugar();
    }

    IEnumerator OtroIntento()
    {
        Juego.Estado = Juego.Modo.Cinematica;
        UIFundido.Negro(1f);
        yield return null;
        StartCoroutine(UIFundido.A(0f, 1.2f));
        yield return UIBanner.Esperar("OTRO INTENTO", "La noche vuelve a empezar", "Primero: " + arbol.EtapaActual.nombre, 3f, new Color(0.6f, 0.9f, 1f));
        EmpezarAJugar();
    }

    void EmpezarAJugar()
    {
        Dificultad.Aplicar();        // solo la primera vez: cascanueces, reloj y vidas según el nivel elegido
        Graficos.Aplicar();          // otra vez: alcanza a las partículas que la dificultad acaba de crear (ventisca)
        Juego.Estado = Juego.Modo.Jugando;
        CamaraOrbitaMouse.BloquearCursor(true);
    }

    // ================================================================== ETAPAS
    void EtapaTerminada(int etapa)
    {
        if (arbol.Completo) StartCoroutine(Final());
        else StartCoroutine(CinematicaEtapa(etapa));
    }

    IEnumerator CinematicaEtapa(int etapa)
    {
        Juego.Estado = Juego.Modo.Cinematica;
        yield return new WaitForSeconds(0.4f);
        // 1) la cámara rodea el árbol mientras sale el banner
        Vector3 centro = arbol.transform.position + Vector3.up * 2.2f;
        Vector3 desde = centro + (jugador.position - centro).normalized * 7f + Vector3.up * 1.5f;
        desde.y = Mathf.Max(desde.y, 2.5f);
        Vector3 hasta = centro + Quaternion.Euler(0, 50, 0) * (desde - centro);
        StartCoroutine(MoverCamara(desde, hasta, centro, 4.5f, true));
        string nombre = etapa < Guion.NombreMision.Length ? Guion.NombreMision[etapa] : arbol.etapas[etapa].nombre;
        yield return UIBanner.Esperar("¡MISIÓN COMPLETADA!", nombre, "Etapa " + (etapa + 1) + " de " + arbol.etapas.Length);
        // 2) diálogo de la etapa (en la de la maceta, Siete da su PRIMERA descarga: el tutorial)
        var descarga = FindAnyObjectByType<DescargaMaquina>();
        if (etapa == 0 && descarga != null) StartCoroutine(DescargaTutorial(descarga));
        if (etapa < Guion.FinEtapa.Length) yield return UIHistoria.Esperar(Guion.FinEtapa[etapa]);
        if (etapa == 0 && descarga != null) { descarga.Empezar(); UIAviso.Mensaje(Guion.ConsejoDescarga, 6f); }
        // 3) ¿despertó algún cascanueces? lo presentamos
        int orden = 0;
        foreach (var c in cascanueces)
        {
            if (c == null) continue;
            if (c.Despierto && !presentados.Contains(c))
            {
                presentados.Add(c);
                yield return PresentarCascanueces(c, presentados.Count - 1);
            }
            orden++;
        }
        // 4) nuevo objetivo (esperamos a que la cámara regrese con el elfo)
        SoltarCamara();
        yield return new WaitForSeconds(1.5f);
        var e = arbol.EtapaActual;
        if (e == null) yield break;            // el árbol ya se completó (lo maneja el final)
        // historia 1.5: si la etapa que sigue es EXTERNA y ya la cumpliste antes (curaste a Siete temprano),
        // se completa en este momento (eso lanza otra cinemática de etapa).
        if (e.externa && ExternaLista(e.tipoPieza)) { arbol.CompletarExterna(e.tipoPieza); yield break; }
        string cuenta = e.partes.Length > 1 ? " (" + e.partes.Length + ")" : "";
        yield return UIBanner.Esperar("NUEVO OBJETIVO", e.nombre + cuenta, e.pista, 3.5f, new Color(0.6f, 0.9f, 1f));
        EmpezarAJugar();
    }

    /// <summary>¿Ya se cumplió esta etapa externa? (historia 1.5)</summary>
    static bool ExternaLista(string tipo)
    {
        if (tipo == MaquinaRota.Etapa) return MaquinaRota.Reparada;
        if (tipo == FabricaEstrella.Etapa) return FabricaEstrella.Fabricada;
        return false;
    }

    /// <summary>La primera descarga sale justo cuando el diálogo dice "¡ZAP!" (la 2a línea).</summary>
    IEnumerator DescargaTutorial(DescargaMaquina d)
    {
        yield return new WaitForSecondsRealtime(1.6f);
        d.Disparar(true);
    }

    IEnumerator PresentarCascanueces(Cascanueces c, int indice)
    {
        float alto = c.transform.localScale.y;
        Vector3 cara = c.transform.position + Vector3.up * 1.4f * alto;
        Vector3 cam = cara + c.transform.forward * 2.8f * alto - Vector3.up * 0.2f;
        // miramos un poco ARRIBA de la cara para que quede en la parte baja de la pantalla (el banner va arriba)
        yield return MoverCamara(cam + c.transform.right * 1.2f, cam, cara + Vector3.up * 0.55f * alto, 1.5f, false);
        UIFundido.Destello(new Color(0.6f, 0f, 0f, 0.35f));
        yield return UIBanner.Esperar(c.nombre.ToUpper(), "¡ha despertado!", "", 2.6f, new Color(1f, 0.3f, 0.25f));
        if (indice < Guion.Despertar.Length) yield return UIHistoria.Esperar(Guion.Despertar[indice]);
        if (indice < Guion.ConsejoDespertar.Length) UIAviso.Mensaje(Guion.ConsejoDespertar[indice], 6f);
    }

    // ================================================================== FINAL
    IEnumerator Final()
    {
        Juego.Estado = Juego.Modo.Cinematica;
        yield return new WaitForSeconds(0.5f);
        Vector3 centro = arbol.transform.position + Vector3.up * 3f;
        StartCoroutine(MoverCamara(centro + new Vector3(0, 0.5f, -8f), centro + new Vector3(5f, 2f, -6f), centro, 6f, true));
        // explosión de luz
        UIFundido.Destello(new Color(1f, 0.95f, 0.8f, 0.85f));
        if (fuegosFinal) fuegosFinal.Play();
        StartCoroutine(EncenderLuces());
        yield return UIBanner.Esperar("¡EL GRAN ÁRBOL ESTÁ COMPLETO!", "La estrella brilla otra vez", "Misión final", 4f);
        yield return UIHistoria.Esperar(Guion.FinalArbol);

        // los cascanueces congelados (escondemos al elfo para que no se atraviese frente a la cámara)
        var modeloElfo = new System.Collections.Generic.List<Renderer>();
        if (jugador != null) foreach (var r in jugador.GetComponentsInChildren<Renderer>()) if (r.enabled) { r.enabled = false; modeloElfo.Add(r); }
        foreach (var c in cascanueces)
            if (c != null && presentados.Contains(c))
            {
                Vector3 cara = c.transform.position + Vector3.up * 1.3f * c.transform.localScale.y;
                yield return MoverCamara(cara + c.transform.forward * 2.2f + Vector3.up * 0.4f, cara + c.transform.forward * 1.8f + Vector3.up * 0.2f, cara, 2f, false);
                break;
            }
        yield return UIHistoria.Esperar(Guion.FinalCascanueces);
        foreach (var r in modeloElfo) r.enabled = true;

        // afuera: llega el trineo y amanece
        yield return UIFundido.A(1f, 0.8f);
        Tomar(tomaExterior, arbol.transform, true);
        StartCoroutine(Amanecer(14f));
        yield return null;
        StartCoroutine(UIFundido.A(0f, 1f));
        if (trineo != null && rutaTrineo != null && rutaTrineo.Length >= 2) yield return VolarTrineo(9f);
        else yield return new WaitForSeconds(3f);
        yield return UIHistoria.Esperar(Guion.LineasFinalSanta(MaquinaRota.Reparada));
        if (Galleta.Todas && trineo != null) yield return EscenaGalletas();
        yield return UIFundido.A(1f, 1.5f);
        yield return UIHistoria.Esperar(Guion.Epilogo);
        // créditos (+ cuántas galletas de jengibre encontró)
        if (textoCreditos != null && !textoCreditos.text.Contains("Galletas")) textoCreditos.text += Galleta.Resumen();
        if (textoCreditos != null && !textoCreditos.text.Contains("Dificultad"))
            textoCreditos.text += "\n\nDificultad: " + Dificultad.Actual.nombre
                + (Dificultad.ConVidas ? "   ·   Vidas al final: " + Vidas.Actual + (Vidas.Ganadas > 0 ? "  (+" + Vidas.Ganadas + " por galletas)" : "") : "");
        // MEDALLA: se guarda y se muestra girando a la derecha de los créditos
        if (textoCreditos != null && !textoCreditos.text.Contains("Medalla de")) { textoCreditos.text += Medallas.Ganar(); textoCreditos.fontSize = 29; }
        var rtMedalla = Medallas.Estudio(Dificultad.Elegido);
        if (rtMedalla != null)
        {
            var img = UIConstructor.Rect("Medalla", capaCreditos, new Vector2(1f, 0.5f), new Vector2(1f, 0.5f), new Vector2(420, 420), new Vector2(-260, 40)).gameObject.AddComponent<RawImage>();
            img.texture = rtMedalla; img.raycastTarget = false;
        }
        AjustarCreditos();
        GestorAudio.Efecto("medalla", 0.8f, 0f);
        Juego.Estado = Juego.Modo.Final;
        CamaraOrbitaMouse.BloquearCursor(false);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 1.5f) { grupoCreditos.alpha = t; yield return null; }
        grupoCreditos.alpha = 1f;
    }

    // ================================================================== DERROTA (amaneció)
    /// <summary>La llama el RelojAmanecer cuando llegan las 6:00 AM sin terminar el árbol.</summary>
    public void Amanecio()
    {
        if (Juego.Perdio || arbol.Completo) return;
        Juego.Perdio = true;          // el GestorAudio cambia a la música triste
        StartCoroutine(Derrota());
    }

    /// <summary>Difícil / Imposible: te atraparon con la última vida.</summary>
    public void SinVidas()
    {
        if (Juego.Perdio || arbol.Completo) return;
        Juego.Perdio = true;
        textoDerrotaTitulo.text = "¡Te atraparon!";
        textoDerrotaSub.text = "Te quedaste sin vidas (" + Dificultad.Actual.nombre + ")";
        StartCoroutine(Derrota(Guion.DerrotaAtrapado));
    }

    /// <summary>Historia 1.5 · Difícil / Imposible: Siete llegó a 10 descargas sin que la curaras.</summary>
    public void Sobrecarga()
    {
        if (Juego.Perdio || arbol.Completo) return;
        Juego.Perdio = true;
        textoDerrotaTitulo.text = "¡SOBRECARGA!";
        textoDerrotaSub.text = "Siete llegó a " + DescargaMaquina.Maximo + " descargas (" + Dificultad.Actual.nombre + ")";
        StartCoroutine(Derrota(Guion.DerrotaSobrecarga));
    }

    IEnumerator Derrota() { return Derrota(Guion.LineasDerrota(MaquinaRota.Reparada)); }

    IEnumerator Derrota(Linea[] lineas)
    {
        while (Juego.Estado == Juego.Modo.Leyendo || Juego.Estado == Juego.Modo.Cinematica) yield return null;
        Juego.Estado = Juego.Modo.Cinematica;
        CamaraOrbitaMouse.BloquearCursor(false);
        // la cámara sale y mira el taller mientras amanece del todo
        yield return UIFundido.A(1f, 1f);
        Tomar(tomaExterior, arbol.transform, true);
        StartCoroutine(Amanecer(8f));
        yield return null;
        StartCoroutine(UIFundido.A(0f, 1.5f));
        yield return new WaitForSeconds(2.5f);
        yield return UIHistoria.Esperar(lineas);
        Juego.Estado = Juego.Modo.Final;
        for (float t = 0f; t < 1f; t += Time.deltaTime / 1.2f) { grupoDerrota.alpha = t; yield return null; }
        grupoDerrota.alpha = 1f;
        grupoDerrota.blocksRaycasts = grupoDerrota.interactable = true;    // botones Reintentar / Salir
        CamaraOrbitaMouse.BloquearCursor(false);
    }

    /// <summary>Partida nueva directa (mismo elfo y dificultad, sin título ni intro).</summary>
    void Reintentar()
    {
        Juego.Reintento = true;
        MenuPrincipal();
    }

    IEnumerator EncenderLuces()
    {
        if (lucesFinal == null) yield break;
        var objetivo = new float[lucesFinal.Length];
        for (int i = 0; i < lucesFinal.Length; i++) if (lucesFinal[i]) { objetivo[i] = lucesFinal[i].intensity; lucesFinal[i].intensity = 0f; lucesFinal[i].gameObject.SetActive(true); }
        for (float t = 0f; t < 1f; t += Time.deltaTime / 2f)
        {
            for (int i = 0; i < lucesFinal.Length; i++) if (lucesFinal[i]) lucesFinal[i].intensity = objetivo[i] * t;
            yield return null;
        }
    }

    /// <summary>Pinta el cielo hacia colores de amanecer poco a poco (lerp de colores del shader).</summary>
    IEnumerator Amanecer(float dur)
    {
        if (cieloCopia == null) yield break;
        Color h0 = cieloCopia.GetColor("_ColorHorizonte"), a0 = cieloCopia.GetColor("_ColorArriba");
        Color h1 = new Color(0.85f, 0.45f, 0.35f), a1 = new Color(0.12f, 0.15f, 0.35f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / dur)
        {
            cieloCopia.SetColor("_ColorHorizonte", Color.Lerp(h0, h1, t));
            cieloCopia.SetColor("_ColorArriba", Color.Lerp(a0, a1, t));
            yield return null;
        }
    }

    /// <summary>El trineo recorre la ruta con una curva suave (Catmull-Rom). Mira hacia donde va pero SIN clavar la
    /// nariz (cabeceo limitado a ±8°) y se inclina en las curvas (TrineoVolador anima renos, riendas y balanceo).</summary>
    IEnumerator VolarTrineo(float dur)
    {
        trineo.gameObject.SetActive(true);
        GestorAudio.Efecto("trineo", 0.8f, 0f);     // cascabeles que se acercan
        var volador = trineo.GetComponent<TrineoVolador>();
        int n = rutaTrineo.Length;
        Vector3 Punto(float t)
        {
            float u = Mathf.Clamp01(t) * (n - 1); int i = Mathf.Min((int)u, n - 2); float f = u - i;
            return CatmullRom(rutaTrineo[Mathf.Max(i - 1, 0)].position, rutaTrineo[i].position, rutaTrineo[i + 1].position, rutaTrineo[Mathf.Min(i + 2, n - 1)].position, f);
        }
        trineo.position = Punto(0f);
        float yawPrevio = Quaternion.LookRotation(Punto(0.02f) - Punto(0f)).eulerAngles.y;
        trineo.rotation = Quaternion.Euler(0f, yawPrevio, 0f);
        Vector3 mira = trineo.position;
        for (float t = 0f; t < 1f; t += Time.deltaTime / dur)
        {
            // frena al final (ease-out) para "estacionarse" en el aire
            float k = 1f - (1f - t) * (1f - t);
            Vector3 p = Punto(k);
            Vector3 dir = Punto(Mathf.Min(1f, k + 0.02f)) - p;
            trineo.position = p;
            if (dir.sqrMagnitude > 0.0001f)
            {
                var r = Quaternion.LookRotation(dir).eulerAngles;
                float pitch = Mathf.Clamp(Mathf.DeltaAngle(0f, r.x), -8f, 8f);
                float giro = Mathf.DeltaAngle(yawPrevio, r.y) / Mathf.Max(Time.deltaTime, 0.001f);
                yawPrevio = r.y;
                trineo.rotation = Quaternion.Slerp(trineo.rotation, Quaternion.Euler(pitch, r.y, 0f), 3f * Time.deltaTime);
                if (volador != null) volador.Inclinar(giro);
            }
            mira = Vector3.Lerp(mira, trineo.position + Vector3.up * 1f, 5f * Time.deltaTime);
            camCinematica.transform.rotation = Quaternion.Slerp(camCinematica.transform.rotation, Quaternion.LookRotation(mira - camCinematica.transform.position), 6f * Time.deltaTime);
            yield return null;
        }
        if (volador != null) volador.Inclinar(0f);
        // queda flotando (TrineoVolador sigue animando) mientras Santa habla; la cámara lo sigue mirando
        StartCoroutine(MirarTrineo());
    }

    bool seguirTrineo;

    /// <summary>FINAL ESPECIAL (10 galletas): la cámara se acerca a Santa, que se come las galletas
    /// (lluvia de migajas + estrellitas) mientras platica.</summary>
    IEnumerator EscenaGalletas()
    {
        seguirTrineo = false;
        Vector3 santa = trineo.TransformPoint(new Vector3(0f, 1.5f, 0.1f));
        Vector3 dir = camCinematica.transform.position - santa; dir.y = 0f; dir.Normalize();
        yield return MoverCamara(camCinematica.transform.position, santa + dir * 4.5f + Vector3.up * 0.6f, santa, 2f, true);
        var migajas = CrearMigajas(santa);
        // antes era un UIAviso abajo y se encimaba con la caja de diálogo de Santa: ahora es un banner ARRIBA
        // y el diálogo empieza cuando el banner ya se fue
        GestorAudio.Efecto("poder", 0.8f, 0f);
        yield return UIBanner.Esperar("★ FINAL ESPECIAL ★", "Las 10 galletas de jengibre", "", 2.8f, new Color(1f, 0.78f, 0.35f));
        yield return UIHistoria.Esperar(Guion.FinalGalletas);
        if (migajas != null) Destroy(migajas.gameObject, 3f);
    }

    ParticleSystem CrearMigajas(Vector3 donde)
    {
        var go = new GameObject("MigajasSanta"); go.transform.position = donde; go.transform.SetParent(trineo, true);
        var ps = go.AddComponent<ParticleSystem>();
        var main = ps.main; main.startLifetime = new ParticleSystem.MinMaxCurve(0.8f, 1.6f); main.startSpeed = new ParticleSystem.MinMaxCurve(0.6f, 1.8f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.04f, 0.1f); main.gravityModifier = 0.6f;
        main.startColor = new ParticleSystem.MinMaxGradient(new Color(0.55f, 0.28f, 0.1f), new Color(1f, 0.85f, 0.4f));
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        var em = ps.emission; em.rateOverTime = 18f;
        em.SetBursts(new[] { new ParticleSystem.Burst(0.2f, 30), new ParticleSystem.Burst(2.5f, 30), new ParticleSystem.Burst(5f, 30) });
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.15f;
        var r = go.GetComponent<ParticleSystemRenderer>();
        var polvo = trineo.Find("PolvoMagico");
        if (polvo != null) r.sharedMaterial = polvo.GetComponent<ParticleSystemRenderer>().sharedMaterial;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        ps.Play();
        return ps;
    }

    IEnumerator MirarTrineo()
    {
        seguirTrineo = true;
        while (seguirTrineo && trineo != null && trineo.gameObject.activeInHierarchy && camCinematica.Priority.Value > 0)
        {
            var objetivo = Quaternion.LookRotation(trineo.position + Vector3.up - camCinematica.transform.position);
            camCinematica.transform.rotation = Quaternion.Slerp(camCinematica.transform.rotation, objetivo, 3f * Time.deltaTime);
            yield return null;
        }
    }

    static Vector3 CatmullRom(Vector3 a, Vector3 b, Vector3 c, Vector3 d, float t)
    {
        return 0.5f * (2f * b + (c - a) * t + (2f * a - 5f * b + 4f * c - d) * t * t + (3f * b - a - 3f * c + d) * t * t * t);
    }

    // ================================================================== CÁMARA
    void Tomar(Transform pos, Transform mira, bool corte)
    {
        if (pos == null) return;
        camCinematica.transform.position = pos.position;
        if (mira != null) camCinematica.transform.LookAt(mira.position + Vector3.up * 0.5f);
        else camCinematica.transform.rotation = pos.rotation;
        camCinematica.Priority.Value = 100;
        if (corte) camCinematica.PreviousStateIsValid = false;
    }

    IEnumerator MoverCamara(Vector3 desde, Vector3 hasta, Vector3 mira, float dur, bool suave)
    {
        camCinematica.Priority.Value = 100;
        for (float t = 0f; t < 1f; t += Time.deltaTime / dur)
        {
            float k = Mathf.SmoothStep(0f, 1f, t);
            camCinematica.transform.position = Vector3.Lerp(desde, hasta, k);
            camCinematica.transform.LookAt(mira);
            yield return null;
        }
    }

    // La cámara del jugador tiene prioridad 10; al soltar bajamos la de cinemáticas a -1 para que NUNCA empaten
    // (si empatan, Cinemachine se queda con la última que se activó y la cámara se "congela").
    void SoltarCamara()
    {
        camCinematica.Priority.Value = -1;
        // la cámara del juego regresa DETRÁS del elfo (no al ángulo que tenía antes de la cinemática)
        var orbita = FindAnyObjectByType<CamaraOrbitaMouse>();
        if (orbita != null && jugador != null) orbita.DetrasDe(jugador);
    }

    // ================================================================== PAUSA
    void Pausar(bool pausa)
    {
        Juego.Estado = pausa ? Juego.Modo.Pausa : Juego.Modo.Jugando;
        Time.timeScale = pausa ? 0f : 1f;
        GestorAudio.Efecto("pausa", 0.6f, 0f);
        grupoPausa.alpha = pausa ? 1f : 0f;
        grupoPausa.blocksRaycasts = grupoPausa.interactable = pausa;   // los sliders solo responden en pausa
        CamaraOrbitaMouse.BloquearCursor(!pausa);
        if (!pausa) { Opciones.Guardar(); Graficos.Guardar(); }
        else MostrarSeccion(0);
    }

    // SECCIONES de la pausa: la columna de la izquierda elige cuál se ve en la tarjeta de la derecha
    static readonly string[] NombresSeccion = { "Sonido", "Gráficos", "Controles", "Medallas" };
    int seccion;
    RectTransform[] panelesSeccion;
    Image[] botonesSeccion;
    Text tituloSeccion;
    void MostrarSeccion(int i)
    {
        seccion = i;
        for (int k = 0; k < panelesSeccion.Length; k++)
        {
            panelesSeccion[k].gameObject.SetActive(k == i);
            botonesSeccion[k].color = k == i ? new Color(1f, 0.75f, 0.3f, 0.9f) : new Color(1f, 1f, 1f, 0.1f);
        }
        tituloSeccion.text = NombresSeccion[i];
    }

    /// <summary>Sección Controles: dos columnas de "tecla → acción" y abajo los consejos de Difícil/Imposible.</summary>
    static void ListaControles(RectTransform p)
    {
        string[,] filas = Tactil.Activo ? new string[,] {
            { "Joystick", "Caminar (a fondo: correr)" }, { "Arrastrar", "Mover la cámara" }, { "Pellizcar", "Acercar / alejar" },
            { "Saltar", "Saltar" }, { "E", "Recoger, colocar o juntar nieve" }, { "Q", "Soltar lo que llevas" },
            { "Bola", "Lanzar bola de nieve" }, { "II", "Pausa" } }
        : new string[,] {
            { "W A S D", "Caminar" }, { "Shift", "Correr (¡hace ruido!)" }, { "Espacio", "Saltar" }, { "Mouse", "Mover la cámara" },
            { "Rueda", "Acercar / alejar" }, { "E", "Recoger, colocar o juntar nieve" }, { "Q", "Soltar lo que llevas" },
            { "F / Clic", "Lanzar bola de nieve" }, { "Esc", "Pausa" }, { "Tab", "Cambiar de sección (aquí)" } };
        int n = filas.GetLength(0), mitad = (n + 1) / 2;
        for (int i = 0; i < n; i++)
        {
            float cx = i < mitad ? -310 : 310, y = 250 - (i % mitad) * 78;
            var tecla = UIConstructor.Rect("Tecla_" + i, p, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(170, 56), new Vector2(cx - 190, y));
            UIConstructor.Redondear(UIConstructor.Imagen(tecla, new Color(1f, 0.82f, 0.45f, 0.95f)), 0.6f);
            UIConstructor.Texto(UIConstructor.PantallaCompleta("Texto", tecla), filas[i, 0], 26, new Color(0.15f, 0.1f, 0.2f), TextAnchor.MiddleCenter, FontStyle.Bold);
            var acc = UIConstructor.Texto(UIConstructor.Rect("Accion_" + i, p, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(380, 56), new Vector2(cx + 100, y)),
                                          filas[i, 1], 28, Color.white, TextAnchor.MiddleLeft);
            UIConstructor.Sombra(acc);
        }
        var caja = UIConstructor.Rect("Consejos", p, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1180, 150), new Vector2(0, -290));
        UIConstructor.Redondear(UIConstructor.Imagen(caja, new Color(0.45f, 0.75f, 1f, 0.12f)));
        UIConstructor.Texto(UIConstructor.PantallaCompleta("Texto", caja),
            "<b><color=#9fe0ff>En Difícil e Imposible</color></b>\nRecarga la linterna junto a la chimenea o un farol\n" +
            "Refúgiate bajo techo en las ventiscas  ·  Rodea las cajas sorpresa", 25, new Color(0.88f, 0.92f, 1f)).lineSpacing = 1.1f;
    }

    /// <summary>Recarga la escena y vuelve a la pantalla de título (o a jugar directo si Juego.Reintento).</summary>
    void MenuPrincipal()
    {
        Time.timeScale = 1f;
        Juego.Estado = Juego.Modo.Titulo;
        Juego.Perdio = false;
        Opciones.Guardar();
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    void Salir()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }

    // ================================================================== UI (creada por código)
    void ConstruirUI()
    {
        // ---- título
        capaTitulo = UIConstructor.Capa("Titulo", 25);
        grupoTitulo = UIConstructor.Grupo(capaTitulo, 0f);
        var vin = UIConstructor.PantallaCompleta("Vineta", capaTitulo);
        UIConstructor.Imagen(vin, new Color(0f, 0f, 0.05f, 0.25f));
        var t = UIConstructor.Titulo(UIConstructor.Rect("Nombre", capaTitulo, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1600, 300), new Vector2(0, 180)),
                                    Guion.Titulo, 110, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold);
        t.lineSpacing = 0.9f; UIConstructor.Sombra(t, 5f);
        var o = t.gameObject.AddComponent<Outline>(); o.effectColor = new Color(0.35f, 0.08f, 0.05f); o.effectDistance = new Vector2(3, -3);
        var st = UIConstructor.Texto(UIConstructor.Rect("Sub", capaTitulo, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1200, 70), new Vector2(0, 10)),
                                     Guion.Subtitulo, 42, new Color(0.75f, 0.9f, 1f), TextAnchor.MiddleCenter, FontStyle.Italic);
        UIConstructor.Sombra(st);
        var autor = UIConstructor.Texto(UIConstructor.Rect("Autor", capaTitulo, new Vector2(1f, 0f), new Vector2(1f, 0f), new Vector2(900, 50), new Vector2(-470, 35)),
                                        "un juego de Cristian Amauri Gonzaga Castañeda", 26, new Color(1f, 0.9f, 0.7f, 0.85f), TextAnchor.MiddleRight);
        UIConstructor.Sombra(autor);
        textoPresiona = UIConstructor.Texto(UIConstructor.Rect("Presiona", capaTitulo, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(1200, 80), new Vector2(0, 260)),
                                            Tactil.Activo ? "Toca la pantalla para comenzar" : "Presiona [Enter] para comenzar", 40, Color.white);
        UIConstructor.Sombra(textoPresiona);
        // (los controles y las medallas ahora están en el menú de PAUSA: el título queda más limpio)

        // ---- pausa: COLUMNA a la izquierda (título + secciones + acciones) y TARJETA a la derecha con la sección
        capaPausa = UIConstructor.Capa("Pausa", 40);
        grupoPausa = UIConstructor.Grupo(capaPausa, 0f);
        UIConstructor.Imagen(UIConstructor.PantallaCompleta("Fondo", capaPausa), new Color(0.02f, 0.03f, 0.08f, 0.72f));
        bool web = Application.platform == RuntimePlatform.WebGLPlayer;     // en el navegador no se puede "salir"
        bool tactil = Tactil.Activo;

        var columna = UIConstructor.Rect("Columna", capaPausa, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(460, 900), new Vector2(270, 0));
        UIConstructor.Redondear(UIConstructor.Imagen(columna, new Color(0.05f, 0.07f, 0.16f, 0.88f)));
        var tp = UIConstructor.Titulo(UIConstructor.Rect("Titulo", columna, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(440, 120), new Vector2(0, -80)),
                                      "PAUSA", 84, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIConstructor.Sombra(tp, 4f);
        var bc = UIConstructor.Boton(columna, tactil ? "Continuar" : "Continuar  [Esc]", new Vector2(380, 76), new Vector2(0, 270), () => Pausar(false), 34);
        bc.targetGraphic.color = new Color(0.35f, 0.75f, 0.45f, 0.9f);
        botonesSeccion = new Image[NombresSeccion.Length];
        for (int i = 0; i < NombresSeccion.Length; i++)
        {
            int k = i;
            botonesSeccion[i] = (Image)UIConstructor.Boton(columna, NombresSeccion[i], new Vector2(380, 66), new Vector2(0, 160 - i * 80), () => MostrarSeccion(k), 32).targetGraphic;
        }
        UIConstructor.Imagen(UIConstructor.Rect("Separador", columna, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(340, 3), new Vector2(0, -150)), new Color(1f, 1f, 1f, 0.15f));
        UIConstructor.Boton(columna, tactil ? "Reiniciar" : "Reiniciar  [R]", new Vector2(380, 62), new Vector2(0, -200), Reintentar, 30);
        UIConstructor.Boton(columna, tactil ? "Menú principal" : "Menú principal  [M]", new Vector2(380, 62), new Vector2(0, -272), MenuPrincipal, 30);
        if (!web) UIConstructor.Boton(columna, tactil ? "Salir del juego" : "Salir del juego  [Q]", new Vector2(380, 62), new Vector2(0, -344), Salir, 30);
        if (!tactil)
            UIConstructor.Texto(UIConstructor.Rect("Ayuda", columna, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(440, 40), new Vector2(0, 38)),
                                "[Tab] cambia de sección", 22, new Color(1f, 1f, 1f, 0.5f));

        // tarjeta: ocupa del lado derecho de la columna hasta la orilla (se adapta a pantallas anchas de teléfono)
        var tarjeta = UIConstructor.Rect("Tarjeta", capaPausa, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), new Vector2(-580, 900), new Vector2(270, 0));
        UIConstructor.Redondear(UIConstructor.Imagen(tarjeta, new Color(0.05f, 0.07f, 0.16f, 0.82f)));
        tituloSeccion = UIConstructor.Titulo(UIConstructor.Rect("TituloSeccion", tarjeta, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(900, 90), new Vector2(0, -62)),
                                             "", 60, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIConstructor.Sombra(tituloSeccion, 3f);
        UIConstructor.Imagen(UIConstructor.Rect("Linea", tarjeta, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(700, 3), new Vector2(0, -112)), new Color(1f, 0.85f, 0.45f, 0.35f));
        panelesSeccion = new RectTransform[NombresSeccion.Length];
        for (int i = 0; i < NombresSeccion.Length; i++)
        {
            var c = UIConstructor.PantallaCompleta("Seccion_" + NombresSeccion[i], tarjeta);
            c.offsetMax = new Vector2(0, -80);          // debajo del título
            panelesSeccion[i] = c;
        }
        // SONIDO (y sensibilidad de la cámara): sliders que guardan su valor en Opciones (PlayerPrefs)
        var ps = panelesSeccion[0];
        UIConstructor.Deslizador(ps, "Música", new Vector2(-40, 150), Opciones.Musica, v => Opciones.Musica = v);
        UIConstructor.Deslizador(ps, "Efectos", new Vector2(-40, 60), Opciones.Efectos, v => { Opciones.Efectos = v; GestorAudio.Efecto("tick", 1f, 0f); });
        UIConstructor.Deslizador(ps, "Ambiente", new Vector2(-40, -30), Opciones.Ambiente, v => Opciones.Ambiente = v);
        UIConstructor.Deslizador(ps, tactil ? "Cámara" : "Mouse", new Vector2(-40, -120), Opciones.Sensibilidad, v => Opciones.Sensibilidad = v, 0.3f, 2.5f);
        UIConstructor.Texto(UIConstructor.Rect("Nota", ps, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(900, 36), new Vector2(0, -170)),
                            "Qué tan rápido gira la cámara", 22, new Color(0.75f, 0.85f, 1f, 0.8f));
        // GRÁFICOS
        var pg = (RectTransform)UIGraficos.Construir(panelesSeccion[1]).transform;
        pg.offsetMax = new Vector2(0, 0);
        // CONTROLES y MEDALLAS
        ListaControles(panelesSeccion[2]);
        Medallas.Lista(panelesSeccion[3]);
        MostrarSeccion(0);

        // ---- derrota (amaneció sin terminar el árbol)
        capaDerrota = UIConstructor.Capa("Derrota", 44);
        grupoDerrota = UIConstructor.Grupo(capaDerrota, 0f);
        UIConstructor.Imagen(UIConstructor.PantallaCompleta("Fondo", capaDerrota), new Color(0.05f, 0.02f, 0.04f, 0.6f));
        var td = textoDerrotaTitulo = UIConstructor.Titulo(UIConstructor.Rect("Titulo", capaDerrota, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1400, 160), new Vector2(0, 120)),
                                      "Amaneció...", 110, new Color(1f, 0.7f, 0.5f));
        UIConstructor.Sombra(td, 5f);
        UIConstructor.Sombra(textoDerrotaSub = UIConstructor.Texto(UIConstructor.Rect("Sub", capaDerrota, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1400, 60), new Vector2(0, 10)),
                             "El Gran Árbol no estuvo listo a tiempo", 40, new Color(0.9f, 0.85f, 0.85f)));
        UIConstructor.Boton(capaDerrota, Tactil.Activo ? "Reintentar" : "[R] Reintentar", new Vector2(360, 72), new Vector2(web ? 0 : -200, -110), Reintentar, 38);
        if (!web) UIConstructor.Boton(capaDerrota, Tactil.Activo ? "Salir" : "[Q] Salir", new Vector2(360, 72), new Vector2(200, -110), Salir, 38);

        // ---- elegir dificultad: 4 tarjetas en fila
        capaDificultad = UIConstructor.Capa("Dificultad", 27);
        grupoDificultad = UIConstructor.Grupo(capaDificultad, 0f);
        UIConstructor.Imagen(UIConstructor.PantallaCompleta("Fondo", capaDificultad), new Color(0.02f, 0.03f, 0.08f, 0.55f));
        UIConstructor.Sombra(UIConstructor.Titulo(UIConstructor.Rect("Titulo", capaDificultad, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(1400, 130), new Vector2(0, -130)),
                             "¿Qué tan difícil es la noche?", 80, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold), 4f);
        int nd = Dificultad.Niveles.Length;
        tarjetas = new Image[nd]; tarjetasTexto = new Text[nd];
        for (int k = 0; k < nd; k++)
        {
            var d = Dificultad.Niveles[k];
            var rt = UIConstructor.Rect("Tarjeta" + k, capaDificultad, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(400, 420), new Vector2((k - (nd - 1) / 2f) * 430f, -10f));
            tarjetas[k] = UIConstructor.Imagen(rt, new Color(0.05f, 0.06f, 0.12f, 0.85f));
            var borde = rt.gameObject.AddComponent<Outline>(); borde.effectDistance = new Vector2(4, -4); borde.effectColor = d.color;
            UIConstructor.Sombra(UIConstructor.Titulo(UIConstructor.Rect("Nombre", rt, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(380, 100), new Vector2(0, -70)),
                                 d.nombre, 70, d.color, TextAnchor.MiddleCenter, FontStyle.Bold), 3f);
            // corazones (o "sin vidas")
            if (d.vidas > 0)
                for (int v = 0; v < d.vidas; v++)
                {
                    var c = UIConstructor.Imagen(UIConstructor.Rect("Vida" + v, rt, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(40, 40), new Vector2((v - (d.vidas - 1) / 2f) * 46f, -150)), new Color(1f, 0.25f, 0.3f));
                    c.sprite = UIConstructor.SpriteCorazon();
                }
            else UIConstructor.Texto(UIConstructor.Rect("SinVidas", rt, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(380, 40), new Vector2(0, -150)), "sin vidas", 26, new Color(1f, 1f, 1f, 0.55f));
            tarjetasTexto[k] = UIConstructor.Texto(UIConstructor.Rect("Descripcion", rt, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(370, 200), new Vector2(0, 120)),
                                                   d.descripcion, 24, new Color(0.88f, 0.92f, 1f));
        }
        UIConstructor.Sombra(UIConstructor.Texto(UIConstructor.Rect("Ayuda", capaDificultad, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(1600, 60), new Vector2(0, 55)),
                             Tactil.Activo ? "Toca una tarjeta para elegirla y tócala otra vez para ¡empezar!" : "[A] / [D] cambiar      ·      [Enter] ¡empezar!      ·      [Esc] regresar", 30, new Color(1f, 1f, 1f, 0.85f)));
        // botón para volver a elegir elfo (el toque se revisa a mano en SeleccionDificultad, como las tarjetas)
        var esquina = UIConstructor.Rect("Regresar", capaDificultad, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(300, 76), new Vector2(200, -90));
        botonRegresar = (RectTransform)UIConstructor.Boton(esquina, Tactil.Activo ? "<  Regresar" : "<  Regresar  [Esc]", new Vector2(300, 76), Vector2.zero, null, 30).transform;

        // ---- elegir elfo
        capaSeleccion = UIConstructor.Capa("Seleccion", 26);
        grupoSeleccion = UIConstructor.Grupo(capaSeleccion, 0f);
        var tsel = UIConstructor.Titulo(UIConstructor.Rect("Elige", capaSeleccion, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(1400, 130), new Vector2(0, -95)),
                                        "Elige a tu elfo", 84, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIConstructor.Sombra(tsel, 4f);
        // panel de la derecha: nombre, puntitos y descripción
        var panel = UIConstructor.Rect("Panel", capaSeleccion, new Vector2(0.7f, 0.5f), new Vector2(0.7f, 0.5f), new Vector2(760, 360), new Vector2(0, 0));
        panelElfo = panel;
        UIConstructor.Imagen(panel, new Color(0.02f, 0.03f, 0.08f, 0.72f));
        textoNombreElfo = UIConstructor.Titulo(UIConstructor.Rect("Nombre", panel, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(700, 130), new Vector2(0, 80)),
                                               "Tilo", 100, Color.white, TextAnchor.MiddleCenter, FontStyle.Bold);
        UIConstructor.Sombra(textoNombreElfo, 4f);
        textoDescElfo = UIConstructor.Texto(UIConstructor.Rect("Descripcion", panel, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(700, 120), new Vector2(0, -75)),
                                            "", 32, new Color(0.85f, 0.92f, 1f));
        UIConstructor.Sombra(textoDescElfo);
        puntosElfo = new Image[VarianteElfo.Elfos.Length];
        for (int k = 0; k < puntosElfo.Length; k++)
        {
            puntosElfo[k] = UIConstructor.Imagen(UIConstructor.Rect("Punto" + k, panel, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(18, 18),
                                                 new Vector2((k - (puntosElfo.Length - 1) / 2f) * 34f, 5)), Color.white);
            puntosElfo[k].sprite = UIConstructor.SpriteCirculo();
        }
        var ayuda = UIConstructor.Texto(UIConstructor.Rect("Ayuda", capaSeleccion, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(1400, 60), new Vector2(0, 55)),
                                        Tactil.Activo ? "Toca < > para cambiar de elfo      ·      toca al elfo: ¡a trabajar!" : "[A] / [D] cambiar elfo      ·      [Enter] ¡a trabajar!", 30, new Color(1f, 1f, 1f, 0.85f));
        UIConstructor.Sombra(ayuda);
        // flechas a los lados del elfo (tercio izquierdo)
        flechaIzq = UIConstructor.Titulo(UIConstructor.Rect("FlechaIzq", capaSeleccion, new Vector2(0.3f, 0.5f), new Vector2(0.3f, 0.5f), new Vector2(200, 260), new Vector2(-290, 0)),
                                         "<", 200, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold);
        flechaDer = UIConstructor.Titulo(UIConstructor.Rect("FlechaDer", capaSeleccion, new Vector2(0.3f, 0.5f), new Vector2(0.3f, 0.5f), new Vector2(200, 260), new Vector2(290, 0)),
                                         ">", 200, new Color(1f, 0.85f, 0.45f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIConstructor.Sombra(flechaIzq, 4f); UIConstructor.Sombra(flechaDer, 4f);

        // ---- créditos
        capaCreditos = UIConstructor.Capa("Creditos", 45);
        grupoCreditos = UIConstructor.Grupo(capaCreditos, 0f);
        UIConstructor.Imagen(UIConstructor.PantallaCompleta("Fondo", capaCreditos), new Color(0.01f, 0.01f, 0.03f, 1f));
        textoCreditos = UIConstructor.Texto(UIConstructor.Rect("Texto", capaCreditos, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(1600, 900)),
                                            Guion.Creditos.Replace("{OTRA_VEZ}", Guion.OtraVez), 34, new Color(0.92f, 0.92f, 0.95f));
        textoCreditos.lineSpacing = 1.1f;
        textoCreditos.verticalOverflow = VerticalWrapMode.Overflow;     // que nunca se corte (con las galletas crece)
    }
}
