using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

namespace HaptiSense
{
    [Serializable]
    public class HapticCommandPacket
    {
        public float timestamp_s;
        public float fx;
        public float fy;
        public float fz;
        public float vibration_amplitude;
        public float vibration_frequency_hz;
        public float contact_strength;
    }

    /// <summary>
    /// Receives safety-limited commands from the local Python bridge.
    /// A device-specific adapter can read LatestCommand on Unity's main thread.
    /// </summary>
    public sealed class HapticCommandReceiver : MonoBehaviour
    {
        [SerializeField] private int listenPort = 9050;
        [SerializeField] private bool visualizeContact = true;
        [SerializeField] private Transform contactIndicator;

        private UdpClient client;
        private Thread receiveThread;
        private volatile bool running;
        private readonly object commandLock = new object();
        private HapticCommandPacket latestCommand = new HapticCommandPacket();

        public HapticCommandPacket LatestCommand
        {
            get
            {
                lock (commandLock)
                {
                    return latestCommand;
                }
            }
        }

        private void OnEnable()
        {
            client = new UdpClient(listenPort);
            client.Client.ReceiveTimeout = 250;
            running = true;
            receiveThread = new Thread(ReceiveLoop) { IsBackground = true };
            receiveThread.Start();
        }

        private void Update()
        {
            if (!visualizeContact || contactIndicator == null) return;
            HapticCommandPacket command = LatestCommand;
            float scale = Mathf.Lerp(0.04f, 0.12f, Mathf.Clamp01(command.contact_strength));
            contactIndicator.localScale = Vector3.one * scale;
            Renderer rendererComponent = contactIndicator.GetComponent<Renderer>();
            if (rendererComponent != null)
            {
                rendererComponent.material.color = Color.Lerp(
                    new Color(0.0f, 0.49f, 0.51f),
                    new Color(0.93f, 0.42f, 0.35f),
                    Mathf.Clamp01(command.vibration_amplitude)
                );
            }
        }

        private void ReceiveLoop()
        {
            IPEndPoint sender = new IPEndPoint(IPAddress.Loopback, 0);
            while (running)
            {
                try
                {
                    byte[] bytes = client.Receive(ref sender);
                    string json = Encoding.UTF8.GetString(bytes);
                    HapticCommandPacket parsed = JsonUtility.FromJson<HapticCommandPacket>(json);
                    if (parsed == null) continue;
                    lock (commandLock)
                    {
                        latestCommand = parsed;
                    }
                }
                catch (SocketException exception)
                {
                    if (exception.SocketErrorCode != SocketError.TimedOut && running)
                        Debug.LogWarning("HaptiSense UDP receive error: " + exception.Message);
                }
                catch (Exception exception)
                {
                    if (running) Debug.LogWarning("HaptiSense packet error: " + exception.Message);
                }
            }
        }

        private void OnDisable()
        {
            running = false;
            if (client != null) client.Close();
            if (receiveThread != null && receiveThread.IsAlive) receiveThread.Join(400);
            client = null;
            receiveThread = null;
        }
    }
}
