using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

namespace HaptiSense
{
    // Synthetic plane-contact sweep, not tracked XR motion or a participant task.
    // Not executed in the authoring environment; validate in your Unity Editor.
    public sealed class BenchContactSweep : MonoBehaviour
    {
        [Serializable] private class Packet
        {
            public float penetration_m, vx, vy, vz, ax, ay, az, nx, ny = 1f, nz;
            public string texture = "soft_tissue";
        }
        [SerializeField] private Transform visualTool;
        [SerializeField] private bool enableSyntheticContact = false;
        [SerializeField] private string texture = "soft_tissue";
        private UdpClient client;
        private IPEndPoint destination;
        private float elapsed;
        void OnEnable()
        {
            destination = new IPEndPoint(IPAddress.Loopback, 9051);
            client = new UdpClient(); elapsed = 0f;
        }
        void FixedUpdate()
        {
            elapsed += Time.fixedDeltaTime;
            var p = new Packet { texture = texture };
            // A repeated 2 s contact / 1 s lift-off cycle enables visible stop checks.
            if (enableSyntheticContact && elapsed % 3f < 2f)
            {
                float phase = 2f * Mathf.PI * .5f * elapsed;
                p.penetration_m = .004f + .002f * Mathf.Sin(phase);
                p.vx = .04f; p.vy = -.002f * Mathf.PI * Mathf.Cos(phase);
                p.ay = .002f * Mathf.PI * Mathf.PI * Mathf.Sin(phase);
            }
            if (visualTool != null) visualTool.localPosition = new Vector3(.025f * Mathf.Sin(elapsed), -p.penetration_m, 0f);
            byte[] bytes = Encoding.UTF8.GetBytes(JsonUtility.ToJson(p));
            client.Send(bytes, bytes.Length, destination);
        }
        void OnDisable()
        {
            if (client == null) return;
            try {
                byte[] bytes = Encoding.UTF8.GetBytes(JsonUtility.ToJson(new Packet()));
                client.Send(bytes, bytes.Length, destination);
            } catch (SocketException) { /* Python/firmware watchdog remains necessary. */ }
            finally { client.Close(); client = null; }
        }
    }
}
