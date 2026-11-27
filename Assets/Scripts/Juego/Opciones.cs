using UnityEngine;

/// <summary>
/// Opciones del jugador (volúmenes y sensibilidad del mouse).
/// Se guardan con PlayerPrefs: un pequeño archivo de preferencias que Unity guarda en la computadora,
/// así al cerrar y volver a abrir el juego se conservan.
/// </summary>
public static class Opciones
{
    public static float Musica { get { return PlayerPrefs.GetFloat("op_musica", 1f); } set { PlayerPrefs.SetFloat("op_musica", value); } }
    public static float Efectos { get { return PlayerPrefs.GetFloat("op_efectos", 1f); } set { PlayerPrefs.SetFloat("op_efectos", value); } }
    public static float Ambiente { get { return PlayerPrefs.GetFloat("op_ambiente", 1f); } set { PlayerPrefs.SetFloat("op_ambiente", value); } }
    /// <summary>Multiplicador de la sensibilidad del mouse (1 = normal).</summary>
    public static float Sensibilidad { get { return PlayerPrefs.GetFloat("op_sensibilidad", 1f); } set { PlayerPrefs.SetFloat("op_sensibilidad", value); } }

    public static void Guardar() { PlayerPrefs.Save(); }
}
