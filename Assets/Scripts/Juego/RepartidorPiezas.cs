using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// REPARTIDOR DE PIEZAS: en cada partida las piezas del árbol aparecen en lugares distintos.
///  1) Junta todos los PuntoPieza de la escena y los BARAJA (algoritmo de Fisher-Yates).
///  2) A cada pieza (maceta, ramas, esferas) le da un punto, sin repetir, tratando de que
///     las piezas de una misma etapa queden en ZONAS DISTINTAS (más dispersas).
///  3) Reglas de dificultad: la maceta (la primera) siempre queda cerca, y como máximo
///     'maximoLejos' piezas caen en lugares lejanos.
///  4) Reescribe la pista de cada etapa con las zonas donde quedaron ("Están repartidas por: ...").
/// Corre ANTES que los demás scripts (DefaultExecutionOrder negativo), así cuando cada Recogible
/// guarda su "posición inicial" ya es la nueva (el cascanueces la regresa ahí si te la quita).
/// Las piezas de puzle (guirnalda en el reno, estrella en la repisa, zanahoria) NO se mueven.
/// </summary>
[DefaultExecutionOrder(-100)]
public class RepartidorPiezas : MonoBehaviour
{
    [Tooltip("Tipos de pieza que se reparten al azar.")]
    public string[] tiposRepartibles = { "Maceta", "Rama", "Esfera" };
    [Tooltip("Tipos que siempre quedan cerca (no en puntos 'lejos').")]
    public string[] siempreCerca = { "Maceta" };
    public int maximoLejos = 3;
    [Tooltip("Para pruebas: apagado = las piezas se quedan donde están en la escena.")]
    public bool repartir = true;

    void Awake()
    {
        if (!repartir) return;
        var puntos = new List<PuntoPieza>(FindObjectsByType<PuntoPieza>());
        if (puntos.Count == 0) return;
        Barajar(puntos);

        // piezas a repartir, agrupadas por tipo, en orden de etapa
        var arbol = FindAnyObjectByType<ArbolNavidad>();
        var todas = FindObjectsByType<Recogible>();
        var usados = new HashSet<PuntoPieza>();
        var zonasPorTipo = new Dictionary<string, List<string>>();
        int lejosUsados = 0;

        foreach (string tipo in tiposRepartibles)
        {
            var zonasTipo = new List<string>();
            zonasPorTipo[tipo] = zonasTipo;
            bool cerca = System.Array.IndexOf(siempreCerca, tipo) >= 0;
            foreach (var r in todas)
            {
                if (r.tipo != tipo) continue;
                PuntoPieza elegido = null;
                // 1a vuelta: zona nueva para este tipo; 2a vuelta: cualquiera libre
                for (int vuelta = 0; vuelta < 2 && elegido == null; vuelta++)
                    foreach (var p in puntos)
                    {
                        if (usados.Contains(p)) continue;
                        if (p.lejos && (cerca || lejosUsados >= maximoLejos)) continue;
                        if (vuelta == 0 && zonasTipo.Contains(p.zona)) continue;
                        elegido = p; break;
                    }
                if (elegido == null) continue;   // no hay más puntos: se queda donde estaba
                usados.Add(elegido);
                if (elegido.lejos) lejosUsados++;
                if (!zonasTipo.Contains(elegido.zona)) zonasTipo.Add(elegido.zona);
                r.transform.position = elegido.transform.position;
                r.transform.rotation = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);
            }
        }

        // pistas nuevas según dónde quedaron
        if (arbol != null && arbol.etapas != null)
            foreach (var e in arbol.etapas)
            {
                List<string> zonas;
                if (!zonasPorTipo.TryGetValue(e.tipoPieza, out zonas) || zonas.Count == 0) continue;
                e.pista = zonas.Count == 1 && e.partes.Length == 1
                    ? "Dicen que quedó por " + zonas[0] + ". (Sigue la brújula.)"
                    : "Están repartidas por " + Lista(zonas) + ".";
            }
    }

    /// <summary>Fisher-Yates: recorre la lista y cambia cada elemento por otro al azar de los que faltan.</summary>
    static void Barajar<T>(List<T> l)
    {
        for (int i = l.Count - 1; i > 0; i--)
        {
            int j = Random.Range(0, i + 1);
            T t = l[i]; l[i] = l[j]; l[j] = t;
        }
    }

    /// <summary>["a","b","c"] -> "a, b y c"</summary>
    static string Lista(List<string> z)
    {
        if (z.Count == 1) return z[0];
        return string.Join(", ", z.GetRange(0, z.Count - 1).ToArray()) + " y " + z[z.Count - 1];
    }
}
