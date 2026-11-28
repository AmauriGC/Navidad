using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

/// <summary>
/// Builds desde la línea de comandos (sin abrir el editor):
///   Unity -batchmode -quit -projectPath . -executeMethod Construir.Android
///   Unity -batchmode -quit -projectPath . -executeMethod Construir.Web
/// Usa las escenas de Build Settings y los ajustes guardados del proyecto.
/// </summary>
public static class Construir
{
    static string[] Escenas() { return EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(); }

    static void Hacer(BuildTarget destino, string ruta)
    {
        var r = BuildPipeline.BuildPlayer(new BuildPlayerOptions { scenes = Escenas(), target = destino, locationPathName = ruta });
        Debug.Log("[Construir] " + destino + ": " + r.summary.result + " (" + r.summary.totalErrors + " errores) -> " + ruta);
        if (Application.isBatchMode) EditorApplication.Exit(r.summary.result == BuildResult.Succeeded ? 0 : 1);
    }

    public static void Android() { Hacer(BuildTarget.Android, "Builds/Android/TurnoDeNoche.apk"); }

    /// <summary>Renderer móvil en Forward clásico (Forward+ dejaba la pantalla negra en algunos teléfonos) con
    /// 8 luces por objeto (antes 4: las luces parpadeaban). LucesCercanas sigue limitando las decorativas.</summary>
    public static void MovilForward()
    {
        var datos = AssetDatabase.LoadAssetAtPath<ScriptableObject>("Assets/Settings/Mobile_Renderer.asset");
        var so = new SerializedObject(datos);
        so.FindProperty("m_RenderingMode").intValue = 0;
        so.ApplyModifiedPropertiesWithoutUndo();
        var rp = AssetDatabase.LoadAssetAtPath<UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset>("Assets/Settings/Mobile_RPAsset.asset");
        rp.maxAdditionalLightsCount = 8;
        EditorUtility.SetDirty(datos); EditorUtility.SetDirty(rp);
        AssetDatabase.SaveAssets();
        Debug.Log("[Construir] Mobile_Renderer -> Forward, luces por objeto = " + rp.maxAdditionalLightsCount);
    }

    public static void AndroidForward() { MovilForward(); Android(); }
    public static void Web() { Hacer(BuildTarget.WebGL, "Builds/WebGL"); }
    public static void Linux() { Hacer(BuildTarget.StandaloneLinux64, "Builds/Linux/TurnoDeNoche.x86_64"); }
}
