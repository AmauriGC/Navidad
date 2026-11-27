/// <summary>
/// Estado global del juego. Es una clase ESTÁTICA: no va en ningún objeto, cualquier script
/// la consulta con Juego.Estado o Juego.Bloqueado.
///  - Titulo: pantalla de inicio.      - Jugando: control normal.
///  - Cinematica: el jugador mira (no se mueve), ej. al completar una etapa.
///  - Leyendo: hay un letrero / diálogo abierto.   - Pausa.   - Final: créditos.
/// </summary>
public static class Juego
{
    public enum Modo { Titulo, Jugando, Cinematica, Leyendo, Pausa, Final }

    public static Modo Estado = Modo.Titulo;

    /// <summary>Solo para pruebas: los diálogos avanzan solos (como si presionaras E).</summary>
    public static bool PruebaAutomatica = false;

    /// <summary>True si amaneció sin terminar el árbol (para la música triste y la pantalla de derrota).</summary>
    public static bool Perdio = false;
    /// <summary>True al presionar "Reintentar": la siguiente partida se salta el título y la intro.</summary>
    public static bool Reintento = false;

    /// <summary>True cuando el elfo NO debe moverse ni interactuar.</summary>
    public static bool Bloqueado { get { return Estado != Modo.Jugando; } }

    /// <summary>True cuando los cascanueces deben quedarse quietos.</summary>
    public static bool EnemigosEnPausa { get { return Estado != Modo.Jugando; } }

    /// <summary>
    /// El proyecto tiene desactivado el "Domain Reload" (Play arranca más rápido), así que las variables
    /// static NO se reinician solas entre partidas. Este método corre automáticamente al presionar Play
    /// y las deja en su valor inicial.
    /// </summary>
    [UnityEngine.RuntimeInitializeOnLoadMethod(UnityEngine.RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reiniciar()
    {
        Estado = Modo.Titulo;
        PruebaAutomatica = false;
        Perdio = false;
        Reintento = false;
        UnityEngine.Time.timeScale = 1f;
    }
}
