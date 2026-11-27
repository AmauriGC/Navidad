using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// Prueba de rendimiento (solo herramienta de desarrollo). Se activa ÚNICAMENTE si el ejecutable se abre con
/// el argumento "-benchmark": quita VSync, pone la cámara en 3 vistas fijas (taller, árbol, pueblo) y mide los
/// milisegundos por cuadro con distintas opciones gráficas. Escribe el resultado en
/// Application.persistentDataPath/benchmark.txt y cierra el juego. Sin el argumento no hace nada.
/// </summary>
public class Benchmark : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Iniciar()
    {
        if (!System.Array.Exists(System.Environment.GetCommandLineArgs(), a => a == "-benchmark")) return;
        Application.runInBackground = true;   // si no, el build se pausa cuando la ventana no tiene el foco
        var go = new GameObject("Benchmark");
        DontDestroyOnLoad(go);
        go.AddComponent<Benchmark>();
    }

    static readonly Vector3[][] Vistas = {
        new[] { new Vector3(1, 3, -2), new Vector3(-3, 1, -8) },      // taller (repisas)
        new[] { new Vector3(0, 3, -9), new Vector3(0, 2, 5) },        // árbol y taller completo
        new[] { new Vector3(20, 6, -25), new Vector3(-20, 2, 30) },   // pueblo (pinos, casas, luces)
    };
    static readonly string[] NombresVista = { "taller", "arbol", "pueblo" };

    IEnumerator Start()
    {
        Debug.Log("[Benchmark] inicio");
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = -1;
        yield return new WaitForSecondsRealtime(4f);

        Graficos.ElegirPreset(2);   // empezar en Alto (= como está la escena)
        QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1;
        var cam = Camera.main;
        foreach (var b in cam.GetComponents<Behaviour>())
            if (b.GetType().Name.Contains("CinemachineBrain")) b.enabled = false;

        var urp = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
        ScriptableRendererFeature ssao = null;
        // rendererDataList devuelve un ReadOnlySpan (no se puede leer por reflexión): se lee el campo interno
        var campo = typeof(UniversalRenderPipelineAsset).GetField("m_RendererDataList",
            System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
        if (campo != null)
            foreach (var d in (ScriptableRendererData[])campo.GetValue(urp))
                if (d != null) foreach (var f in d.rendererFeatures) if (f.name.Contains("Ambient")) ssao = f;
        var luces = GameObject.Find("--- AMBIENTACION ---/Pueblo_Luces/LucesPueblo");
        float dist0 = urp.shadowDistance, escala0 = urp.renderScale, bias0 = QualitySettings.lodBias;

        var sb = new StringBuilder();
        sb.AppendLine("GPU: " + SystemInfo.graphicsDeviceName + " | " + SystemInfo.graphicsDeviceType);
        sb.AppendLine("CPU: " + SystemInfo.processorType + " | pantalla " + Screen.width + "x" + Screen.height);
        int enNav = 0, ags = 0;
        foreach (var a in FindObjectsByType<UnityEngine.AI.NavMeshAgent>()) { ags++; if (a.isOnNavMesh) enNav++; }
        sb.AppendLine("cascanueces sobre el NavMesh: " + enNav + "/" + ags);
        sb.AppendLine("ms por cuadro (FPS) en vistas: taller / arbol / pueblo");

        string[] pruebas = { "base (como esta)", "sin SSAO", "sin sombras", "sombras 20 m", "renderScale 0.75",
                             "lodBias 1", "sin LucesPueblo", "sin postproceso", "preset ALTO", "preset MEDIO", "preset BAJO" };
        for (int p = 0; p < pruebas.Length; p++)
        {
            // aplicar (las pruebas 8-10 usan los presets reales del menú de gráficos)
            if (p >= 8)
            {
                if (luces) luces.SetActive(true);
                cam.GetUniversalAdditionalCameraData().renderPostProcessing = true;
                Graficos.ElegirPreset(10 - p);
                QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1;   // medir sin tope
            }
            else
            {
                if (ssao) ssao.SetActive(p != 1);
                urp.shadowDistance = p == 2 ? 0f : p == 3 ? 20f : dist0;
                urp.renderScale = p == 4 ? 0.75f : escala0;
                QualitySettings.lodBias = p == 5 ? 1f : bias0;
                if (luces) luces.SetActive(p != 6);
                cam.GetUniversalAdditionalCameraData().renderPostProcessing = p != 7;
            }

            sb.Append(pruebas[p].PadRight(22) + ": ");
            Debug.Log("[Benchmark] prueba " + pruebas[p]);
            for (int v = 0; v < Vistas.Length; v++)
            {
                cam.farClipPlane = Graficos.Actual.distancia;
                cam.transform.position = Vistas[v][0];
                cam.transform.LookAt(Vistas[v][1]);
                yield return new WaitForSecondsRealtime(1f);
                int cuadros = 0; float t = 0f;
                while (t < 3f) { yield return null; t += Time.unscaledDeltaTime; cuadros++; }
                float ms = t * 1000f / cuadros;
                sb.Append(ms.ToString("F1") + " ms (" + (1000f / ms).ToString("F0") + ")   ");
            }
            sb.AppendLine();
        }
        if (ssao) ssao.SetActive(true);
        urp.shadowDistance = dist0; urp.renderScale = escala0; QualitySettings.lodBias = bias0;

        string ruta = System.IO.Path.Combine(Application.persistentDataPath, "benchmark.txt");
        System.IO.File.WriteAllText(ruta, sb.ToString());
        Debug.Log("[Benchmark] " + ruta + "\n" + sb);
        Application.Quit();
    }
}
