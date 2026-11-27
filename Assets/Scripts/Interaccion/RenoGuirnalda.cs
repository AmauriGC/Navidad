using System.Collections;
using UnityEngine;

/// <summary>
/// Un reno se enredó con la guirnalda del árbol y no la suelta... tiene hambre.
/// Mini-misión: el elfo le trae una ZANAHORIA (la nariz del muñeco de nieve).
///  - Sin zanahoria: muestra una pista.
///  - Con zanahoria: el reno se la come, brinca contento y la guirnalda cae al piso
///    (Recogible.Liberar), ya lista para recogerse.
/// Es otro hijo de Interactuable: el Interactor lo detecta igual que a las piezas.
/// </summary>
public class RenoGuirnalda : Interactuable
{
    [Tooltip("La pieza de guirnalda que tiene enredada (empieza bloqueada).")]
    public Recogible guirnalda;
    public string tipoComida = "Zanahoria";
    [Tooltip("Dónde cae la guirnalda al soltarla.")]
    public Transform puntoSoltar;
    [Tooltip("Parte que brinca al comer (si es nulo, brinca todo el reno).")]
    public Transform cuerpo;

    public bool Satisfecho { get; private set; }

    void Awake()
    {
        if (string.IsNullOrEmpty(textoAccion) || textoAccion == "Usar") textoAccion = "Dar zanahoria";
        if (cuerpo == null) cuerpo = transform;
    }

    void Start()
    {
        if (guirnalda != null) guirnalda.bloqueado = true;
    }

    bool TraeComida(Interactor quien)
    {
        return quien.Inventario != null && quien.Inventario.EnMano != null && quien.Inventario.EnMano.tipo == tipoComida;
    }

    public override bool PuedeInteractuar(Interactor quien) { return !Satisfecho; }

    public override string Texto(Interactor quien)
    {
        return TraeComida(quien) ? "Dar zanahoria al reno" : "Hablar con el reno";
    }

    public override void Interactuar(Interactor quien)
    {
        if (!TraeComida(quien))
        {
            UIAviso.Mensaje("El reno se enredó con la guirnalda y no la suelta...\nTiene hambre. ¿Y la nariz del muñeco de nieve?", 4f);
            return;
        }
        quien.Inventario.Entregar().Consumir();
        Satisfecho = true;
        StartCoroutine(Comer());
    }

    IEnumerator Comer()
    {
        UIAviso.Mensaje("¡Ñam! El reno suelta la guirnalda", 3f);
        GestorAudio.Efecto3D("reno", transform.position, 1f);
        Vector3 basePos = cuerpo.localPosition;
        // 3 brinquitos de alegría (valor absoluto de un seno = rebotes)
        for (float t = 0f; t < 1.2f; t += Time.deltaTime)
        {
            cuerpo.localPosition = basePos + Vector3.up * Mathf.Abs(Mathf.Sin(t * Mathf.PI * 2.5f)) * 0.35f;
            yield return null;
        }
        cuerpo.localPosition = basePos;
        if (guirnalda != null)
        {
            Vector3 destino = puntoSoltar != null ? puntoSoltar.position : transform.position + transform.forward * 1.5f + Vector3.up * 0.5f;
            guirnalda.Liberar(destino);
        }
    }
}
