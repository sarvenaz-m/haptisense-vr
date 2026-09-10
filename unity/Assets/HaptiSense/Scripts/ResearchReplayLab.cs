using System;
using System.IO;
using UnityEngine;

namespace HaptiSense
{
    /// <summary>
    /// Desktop scene generated at runtime from an exported computational session.
    /// This replays Python/browser results; it does not drive an actuator or XR rig.
    /// Unity Editor execution is not part of the recorded host validation.
    /// </summary>
    public sealed class ResearchReplayLab : MonoBehaviour
    {
        [Serializable] public sealed class Sample
        {
            public float t_s, depth_m, normal_n, memory_n, friction_n, command_n;
            public float amplitude, frequency_hz;
        }
        [Serializable] public sealed class Config { public float duration; public int rate; }
        [Serializable] public sealed class Session
        {
            public string schema, version, evidence;
            public Config config;
            public Sample[] rows;
        }

        public TextAsset sessionJson;
        private Session session;
        private Mesh mesh;
        private Vector3[] vertices;
        private Transform probe;
        private Material surfaceMaterial, toolMaterial;
        private float elapsed;
        private bool playing;
        private string error;
        private Sample current;
        private const int NX = 32, NZ = 22;

        void Start()
        {
            try
            {
                if (sessionJson == null) throw new InvalidDataException("Assign a v0.3 session JSON in the Inspector.");
                if (sessionJson.text.Length > 8000000) throw new InvalidDataException("Session exceeds 8 MB.");
                session = JsonUtility.FromJson<Session>(sessionJson.text);
                Validate(session);
                BuildScene();
                elapsed = session.config.duration * .325f;
                RenderSample();
            }
            catch (Exception ex) { error = ex.Message; Debug.LogError("HaptiSense: " + error); enabled = false; }
        }

        private static bool Finite(float value) { return !float.IsNaN(value) && !float.IsInfinity(value); }
        private static void Validate(Session s)
        {
            if (s == null || s.schema != "haptisense.research.v1" || s.version != "0.3.0" ||
                s.evidence != "synthetic_computational" || s.config == null ||
                s.config.rate < 100 || s.config.rate > 2000 || !Finite(s.config.duration) ||
                s.config.duration < 1 || s.config.duration > 12 || s.rows == null ||
                s.rows.Length != (int)(s.config.rate * s.config.duration) + 1)
                throw new InvalidDataException("Expected a bounded computational v0.3 session.");
            for (int i = 0; i < s.rows.Length; i++)
            {
                Sample r = s.rows[i];
                if (r == null || !Finite(r.t_s) || !Finite(r.depth_m) || !Finite(r.normal_n) ||
                    !Finite(r.memory_n) || !Finite(r.friction_n) || !Finite(r.command_n) ||
                    !Finite(r.amplitude) || !Finite(r.frequency_hz) ||
                    Mathf.Abs(r.t_s - (float)i / s.config.rate) > .0001f ||
                    r.depth_m < 0 || r.depth_m > .02f || r.command_n < 0 || r.command_n > 12.001f ||
                    r.amplitude < 0 || r.amplitude > .851f || r.frequency_hz < 0 || r.frequency_hz > 250.001f)
                    throw new InvalidDataException("Invalid trace row " + i);
            }
        }

        private Material Material(Color color)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");
            if (shader == null) throw new InvalidOperationException("A supported lit shader is required.");
            return new Material(shader) { color = color };
        }

        private void BuildScene()
        {
            surfaceMaterial = Material(new Color(.2f, .65f, .52f));
            toolMaterial = Material(new Color(.85f, .84f, .72f));
            var surface = new GameObject("Illustrative contact surface"); surface.transform.SetParent(transform, false);
            mesh = new Mesh { name = "Illustrative Gaussian indentation (not FEM)" };
            vertices = new Vector3[(NX + 1) * (NZ + 1)];
            var triangles = new int[NX * NZ * 6]; int n = 0;
            for (int z = 0; z < NZ; z++) for (int x = 0; x < NX; x++)
            {
                int a = z * (NX + 1) + x;
                triangles[n++] = a; triangles[n++] = a + NX + 1; triangles[n++] = a + 1;
                triangles[n++] = a + 1; triangles[n++] = a + NX + 1; triangles[n++] = a + NX + 2;
            }
            mesh.vertices = vertices; mesh.triangles = triangles;
            surface.AddComponent<MeshFilter>().sharedMesh = mesh;
            surface.AddComponent<MeshRenderer>().sharedMaterial = surfaceMaterial;
            var tool = GameObject.CreatePrimitive(PrimitiveType.Capsule); tool.name = "Virtual probe";
            tool.transform.SetParent(transform, false); tool.transform.localScale = new Vector3(.004f, .018f, .004f);
            Destroy(tool.GetComponent<Collider>()); tool.GetComponent<Renderer>().sharedMaterial = toolMaterial; probe = tool.transform;
            var cameraObject = new GameObject("HaptiSense camera"); cameraObject.transform.SetParent(transform, false);
            var cam = cameraObject.AddComponent<Camera>(); cam.nearClipPlane = .001f; cam.farClipPlane = 10;
            cam.backgroundColor = new Color(.035f, .06f, .08f); cam.clearFlags = CameraClearFlags.SolidColor;
            cam.transform.localPosition = new Vector3(.08f, .07f, -.09f); cam.transform.LookAt(transform.position);
            var lightObject = new GameObject("HaptiSense key light"); lightObject.transform.SetParent(transform, false);
            var light = lightObject.AddComponent<Light>(); light.type = LightType.Directional; light.intensity = 1.2f;
            light.transform.localRotation = Quaternion.Euler(50, -30, 0);
        }

        void Update()
        {
            if (session == null || mesh == null) return;
            if (playing) { elapsed = Mathf.Min(elapsed + Time.deltaTime, session.config.duration); if (elapsed >= session.config.duration) playing = false; }
            RenderSample();
        }

        private void RenderSample()
        {
            current = session.rows[Mathf.Clamp(Mathf.RoundToInt(elapsed * session.config.rate), 0, session.rows.Length - 1)];
            for (int z = 0; z <= NZ; z++) for (int x = 0; x <= NX; x++)
            {
                float px = -.04f + .08f * x / NX, pz = -.028f + .056f * z / NZ;
                float y = -current.depth_m * Mathf.Exp(-(px * px + pz * pz) / .00018f);
                vertices[z * (NX + 1) + x] = new Vector3(px, y, pz);
            }
            mesh.vertices = vertices; mesh.RecalculateNormals(); mesh.RecalculateBounds();
            probe.localPosition = new Vector3(0, .018f - current.depth_m, 0);
        }

        void OnGUI()
        {
            GUILayout.BeginArea(new Rect(20, 20, 360, 230), GUI.skin.box);
            GUILayout.Label("HaptiSense | Computational trace replay");
            if (error != null) GUILayout.Label(error);
            else if (session != null && current != null)
            {
                GUILayout.Label("No hardware connected | Illustrative geometry");
                GUILayout.Label(string.Format("t {0:F3} s | depth {1:F2} mm", current.t_s, current.depth_m * 1000));
                GUILayout.Label(string.Format("command {0:F3} N | memory {1:F3} N", current.command_n, current.memory_n));
                GUILayout.Label(string.Format("cue {0:F1} Hz | amplitude {1:F3}", current.frequency_hz, current.amplitude));
                if (GUILayout.Button(playing ? "Pause" : "Play")) { if (elapsed >= session.config.duration) elapsed = 0; playing = !playing; }
                float value = GUILayout.HorizontalSlider(elapsed, 0, session.config.duration);
                if (Mathf.Abs(value - elapsed) > .0001f) { elapsed = value; playing = false; }
            }
            GUILayout.EndArea();
        }

        void OnDestroy()
        {
            if (mesh != null) Destroy(mesh);
            if (surfaceMaterial != null) Destroy(surfaceMaterial);
            if (toolMaterial != null) Destroy(toolMaterial);
        }
    }
}
