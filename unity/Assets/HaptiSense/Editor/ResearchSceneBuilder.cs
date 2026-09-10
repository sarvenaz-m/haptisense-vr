#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace HaptiSense.Editor
{
    public static class ResearchSceneBuilder
    {
        [MenuItem("HaptiSense/Create desktop replay scene")]
        public static void Create()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("HaptiSense computational replay");
            var lab = root.AddComponent<HaptiSense.ResearchReplayLab>();
            lab.sessionJson = AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/HaptiSense/Data/default-session.json");
            Selection.activeGameObject = root;
            EditorSceneManager.MarkSceneDirty(root.scene);
            Debug.Log("Save this new scene, assign a session JSON if needed, and press Play. No device output is enabled.");
        }
    }
}
#endif
