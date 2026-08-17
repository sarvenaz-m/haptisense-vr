using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

namespace HaptiSense
{
    [Serializable]
    public class ContactStatePacket
    {
        public float penetration_m;
        public float vx;
        public float vy;
        public float vz;
        public float nx;
        public float ny;
        public float nz;
        public float ax;
        public float ay;
        public float az;
        public string texture;
    }

    /// <summary>
    /// Publishes a compact contact state. It does not drive hardware directly.
    /// </summary>
    [RequireComponent(typeof(Rigidbody))]
    public sealed class HapticContactPublisher : MonoBehaviour
    {
        [SerializeField] private string bridgeHost = "127.0.0.1";
        [SerializeField] private int bridgePort = 9051;
        [SerializeField] private string textureProfile = "soft_tissue";

        private UdpClient client;
        private IPEndPoint bridge;
        private Rigidbody body;
        private Vector3 previousVelocity;
        private ContactStatePacket latestContact;

        private void OnEnable()
        {
            body = GetComponent<Rigidbody>();
            previousVelocity = body.velocity;
            client = new UdpClient();
            bridge = new IPEndPoint(IPAddress.Parse(bridgeHost), bridgePort);
        }

        private void FixedUpdate()
        {
            Vector3 acceleration = (body.velocity - previousVelocity) / Mathf.Max(Time.fixedDeltaTime, 0.0001f);
            previousVelocity = body.velocity;
            ContactStatePacket packet = latestContact ?? EmptyPacket();
            packet.vx = body.velocity.x;
            packet.vy = body.velocity.y;
            packet.vz = body.velocity.z;
            packet.ax = acceleration.x;
            packet.ay = acceleration.y;
            packet.az = acceleration.z;
            Send(packet);
            latestContact = null;
        }

        private void OnCollisionStay(Collision collision)
        {
            if (collision.contactCount == 0) return;
            ContactPoint contact = collision.GetContact(0);
            latestContact = new ContactStatePacket
            {
                penetration_m = Mathf.Max(0.0001f, -contact.separation),
                nx = contact.normal.x,
                ny = contact.normal.y,
                nz = contact.normal.z,
                texture = textureProfile
            };
        }

        private ContactStatePacket EmptyPacket()
        {
            return new ContactStatePacket
            {
                penetration_m = 0f,
                nx = 0f,
                ny = 1f,
                nz = 0f,
                texture = textureProfile
            };
        }

        private void Send(ContactStatePacket packet)
        {
            if (client == null) return;
            byte[] bytes = Encoding.UTF8.GetBytes(JsonUtility.ToJson(packet));
            client.Send(bytes, bytes.Length, bridge);
        }

        private void OnDisable()
        {
            if (client != null) client.Close();
            client = null;
        }
    }
}
