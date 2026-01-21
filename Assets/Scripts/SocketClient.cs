using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using System.Threading;

public class SocketClient : MonoBehaviour
{
    [Header("Connection Settings")]
    private const string host = "127.0.0.1"; // localhost
    private const int port = 12345;
    private const int connectionTimeout = 5000; // 5 seconds
    private const int receiveTimeout = 10000; // 10 seconds
    private const float reconnectDelay = 2f; // seconds

    private TcpClient client;
    private NetworkStream stream;
    private Thread receiveThread;
    private bool isRunning = true;
    private bool isConnected = false;
    private float lastReconnectAttempt = 0f;

    // 이벤트: 메시지 수신 시 발생
    public event Action<string> OnMessageReceived;

    // 연결 상태 프로퍼티
    public bool IsConnected => isConnected;

    private void Awake()
    {
        ConnectToServer();
    }

    private void OnDestroy()
    {
        isRunning = false;
        DisconnectFromServer();
        
        // Wait for receive thread to finish (with timeout)
        if (receiveThread != null && receiveThread.IsAlive)
        {
            if (!receiveThread.Join(1000)) // Wait up to 1 second
            {
                Debug.LogWarning("Receive thread did not terminate gracefully");
            }
        }
    }

    private void OnApplicationQuit()
    {
        isRunning = false;
        DisconnectFromServer();
    }

    private void Update()
    {
        // Auto-reconnect logic
        if (!isConnected && isRunning && Time.time - lastReconnectAttempt > reconnectDelay)
        {
            lastReconnectAttempt = Time.time;
            ConnectToServer();
        }
    }

    public void ConnectToServer()
    {
        try
        {
            // Close existing connection if any
            DisconnectFromServer();

            Debug.Log($"Attempting to connect to AI server at {host}:{port}...");
            
            client = new TcpClient();
            var connectTask = client.BeginConnect(host, port, null, null);
            var success = connectTask.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(connectionTimeout));

            if (!success || !client.Connected)
            {
                Debug.LogWarning("Failed to connect to AI server. Will retry...");
                client?.Close();
                client = null;
                isConnected = false;
                return;
            }

            client.EndConnect(connectTask);
            stream = client.GetStream();
            stream.ReadTimeout = receiveTimeout;
            stream.WriteTimeout = receiveTimeout;

            isConnected = true;
            Debug.Log("Successfully connected to AI server!");

            // Start the receive thread
            if (receiveThread == null || !receiveThread.IsAlive)
            {
                receiveThread = new Thread(new ThreadStart(ReceiveData))
                {
                    IsBackground = true,
                    Name = "AICommunicationThread"
                };
                receiveThread.Start();
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Exception connecting to server: {e.Message}");
            isConnected = false;
            client?.Close();
            client = null;
        }
    }

    private void DisconnectFromServer()
    {
        try
        {
            isConnected = false;
            if (stream != null)
            {
                stream.Close();
                stream = null;
            }
            if (client != null)
            {
                client.Close();
                client = null;
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning($"Error disconnecting: {e.Message}");
        }
    }

    private void ReceiveData()
    {
        Debug.Log("AI communication thread started!");
        byte[] data = new byte[4096]; // Increased buffer size for better performance
        
        while (isRunning)
        {
            try
            {
                if (!isConnected || client == null || !client.Connected || stream == null)
                {
                    Thread.Sleep(1000); // Wait before attempting reconnect
                    continue;
                }

                int bytesRead = stream.Read(data, 0, data.Length);
                if (bytesRead > 0)
                {
                    string message = Encoding.UTF8.GetString(data, 0, bytesRead).Trim();
                    if (string.IsNullOrEmpty(message))
                        continue;

                    Debug.Log($"Received from AI: {message}");
                    
                    // 이벤트를 통해 메시지 전달
                    OnMessageReceived?.Invoke(message);
                }
                else
                {
                    // Connection closed by remote host
                    Debug.LogWarning("AI server closed the connection");
                    isConnected = false;
                    DisconnectFromServer();
                }
            }
            catch (System.IO.IOException e)
            {
                // Connection lost or timeout
                Debug.LogWarning($"Connection error: {e.Message}");
                isConnected = false;
                DisconnectFromServer();
            }
            catch (Exception e)
            {
                Debug.LogError($"Exception in ReceiveData: {e.Message}\n{e.StackTrace}");
                isConnected = false;
                DisconnectFromServer();
            }
        }
        
        Debug.Log("AI communication thread stopped");
    }

    public void SendToAI(string message)
    {
        try
        {
            if (!isConnected || stream == null || !stream.CanWrite)
            {
                Debug.LogWarning("Cannot send message: not connected to AI server");
                return;
            }

            byte[] dataToSend = Encoding.UTF8.GetBytes(message);
            stream.Write(dataToSend, 0, dataToSend.Length);
            stream.Flush();
        }
        catch (Exception e)
        {
            Debug.LogError($"Error sending message to AI: {e.Message}");
            isConnected = false;
            DisconnectFromServer();
        }
    }
}
