using System.Collections;
using System.Collections.Generic;
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using System.Threading;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;
using UnityEngine.TextCore.Text;

public enum PlayerType
{
    Red,
    Blue
}

public enum ActionType
{
    ShootSelf = 1,
    ShootOther = 2,
    Drink = 3,
    MagGlass = 4,
    Cigar = 5,
    Knife = 6,
    Handcuffs = 7
}

public class GameManager : MonoBehaviour
{
    [Header("Socket")]
    private const string host = "127.0.0.1"; // localhost
    private const int port = 12345;
    private const int connectionTimeout = 5000; // 5 seconds
    private const int receiveTimeout = 10000; // 10 seconds
    TcpClient client;
    NetworkStream stream;
    private Thread receiveThread;
    private bool isRunning = true;
    private bool isConnected = false;
    private float reconnectDelay = 2f; // seconds
    private float lastReconnectAttempt = 0f;
    static GameManager instance;
    public bool play; //determines whether the ais can play; adds pauses
    public UnityMainThreadDispatcher umtd;

    public bool redCuff;
    public bool blueCuff;

    [Header("Gameplay")]
    public string turn; //"r" "b"
    public Stack<string> rounds = new Stack<string>();
    public int redLives = 4;
    public int blueLives = 4;
    public GameObject[] items;
    public List<GameObject> redItems = new List<GameObject>(); //items: 1: drink (unload gun 1) 2: mag. glass (view barrel) 3: cig (heal +1) 4: knife (2 dmg)
    public List<GameObject> blueItems = new List<GameObject>();
    public int totalReal;
    public int totalEmpty;
    public GameObject bluePlayer;
    public GameObject redPlayer;
    public GameObject Gun;
    public GameObject[] redBoard;
    public GameObject[] blueBoard;
    public int gunDamage;

    public int knowledge;
    [Header("Debug Information")]
    public TextMesh blueHPShow;
    public TextMesh redHPShow;
    public TextMeshProUGUI action;
    public TextMeshProUGUI nextBullet;
    public int scalar = 0;
    //AI PLANNING:
    //INPUTS:  1) num bullets | 2) num real | 3) num fake | 4) red lives | 5) blue lives | 6) red items (list) | 7) blue items (list) | 8) gun damage | 9) next bullet (-1 if not aviable, 0 for fake, 1 for real)
    //OUTPUTS: 1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife | 7) cuffs
    private void Awake()
    {
        Application.targetFrameRate = 50;
        Time.timeScale = 3;
        newRound();
        if (instance == null)
        {
            instance = this;
            DontDestroyOnLoad(gameObject);
            ConnectToServer();

        }
        else
        {
            Destroy(gameObject);
        }
    }

    void OnDestroy()
    {
        Application.targetFrameRate = -1;
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

    void OnApplicationQuit()
    {
        isRunning = false;
        DisconnectFromServer();
    }

    public string playStep(string toPlay)
    {
        string toSend = "";
        if(turn == "r")
        {
            toSend += redMove(int.Parse(toPlay)).ToString();
            toSend += ":";
            if(turn == "b") { toSend += "True"; } else { toSend += "False"; }
        }
        else
        {
            toSend += blueMove(int.Parse(toPlay)).ToString();
            toSend += ":";
            if (turn == "r") { toSend += "True"; } else { toSend += "False"; }
        }

        return toSend;
    }

    IEnumerator playAnimation(Animator anim, string animName)
    {
        anim.Play(animName);
        yield return null;
    }

    public int getItems(string team, string item)
    {
        int count = 0;
        if (team == "r")
        {
            for (int i = 0; i < redBoard.Length; i++)
            {
                if (redBoard[i].GetComponent<ItemSlot>().takenByName == item)
                {
                    count++;
                }
            }
            return count;
        }
        else
        {
            for (int i = 0; i < blueBoard.Length; i++)
            {
                if (blueBoard[i].GetComponent<ItemSlot>().takenByName == item)
                {
                    count++;
                }
            }
            return count;
        }
    }

    // 플레이어 타입에 따른 데이터를 반환하는 헬퍼 메서드
    private PlayerType GetPlayerTypeFromString(string team)
    {
        return team == "r" ? PlayerType.Red : PlayerType.Blue;
    }

    private string GetTeamCode(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? "r" : "b";
    }

    private GameObject[] GetPlayerBoard(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? redBoard : blueBoard;
    }

    private ref int GetPlayerLives(PlayerType playerType)
    {
        if (playerType == PlayerType.Red)
            return ref redLives;
        else
            return ref blueLives;
    }

    private ref bool GetPlayerCuff(PlayerType playerType)
    {
        if (playerType == PlayerType.Red)
            return ref redCuff;
        else
            return ref blueCuff;
    }

    private string GetAnimColorName(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? "Red" : "Blue";
    }

    private float GetInvalidActionPenalty(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? 10f : 50f;
    }

    private string GetShootSelfAnimName(PlayerType playerType, int damage)
    {
        string playerName = playerType == PlayerType.Red ? "Red" : "Blue";
        return $"{playerName}Shoot{playerName}-{damage}DMG";
    }

    private string GetShootOtherAnimName(PlayerType playerType, int damage)
    {
        string playerName = playerType == PlayerType.Red ? "Red" : "Blue";
        string otherName = playerType == PlayerType.Red ? "Blue" : "Red";
        return $"{playerName}Shoot{otherName}-{damage}DMG";
    }

    private string GetKnifeAnimName(PlayerType playerType)
    {
        string playerName = playerType == PlayerType.Red ? "Red" : "Blue";
        return $"{playerName}Knife";
    }

    // 통합된 Move 메서드
    public float ExecuteMove(PlayerType playerType, ActionType action)
    {
        float reward = 0;
        string teamCode = GetTeamCode(playerType);
        GameObject[] board = GetPlayerBoard(playerType);
        ref int lives = ref GetPlayerLives(playerType);
        ref bool cuff = ref GetPlayerCuff(playerType);
        string animColor = GetAnimColorName(playerType);
        float penalty = GetInvalidActionPenalty(playerType);
        int actionInt = (int)action;

        if (action == ActionType.ShootSelf)
        {
            Gun.GetComponent<Animator>().StopPlayback();
            Gun.GetComponent<Animator>().Rebind();

            string animName = GetShootSelfAnimName(playerType, gunDamage);
            umtd.Enqueue(playAnimation(Gun.GetComponent<Animator>(), animName));
            Gun.GetComponent<Animator>().Play(animName);
            reward += ExecuteShoot(playerType, true);
        }
        else if (action == ActionType.ShootOther)
        {
            Gun.GetComponent<Animator>().StopPlayback();
            Gun.GetComponent<Animator>().Rebind();

            string animName = GetShootOtherAnimName(playerType, gunDamage);
            umtd.Enqueue(playAnimation(Gun.GetComponent<Animator>(), animName));
            Gun.GetComponent<Animator>().Play(animName);
            reward += ExecuteShoot(playerType, false);
        }
        else
        {
            // 아이템 사용 검증
            string itemCode = "";
            if (action == ActionType.Drink) itemCode = "ED";
            else if (action == ActionType.MagGlass) itemCode = "MG";
            else if (action == ActionType.Cigar) itemCode = "C";
            else if (action == ActionType.Knife) itemCode = "K";
            else if (action == ActionType.Handcuffs) itemCode = "HC";

            if (!string.IsNullOrEmpty(itemCode) && getItems(teamCode, itemCode) == 0)
            {
                reward -= penalty + scalar;
                scalar++;
            }
            else
            {
                scalar = 0;
            }

            // 아이템 사용 처리
            for (int i = 0; i < board.Length; i++)
            {
                ItemSlot slot = board[i].GetComponent<ItemSlot>();
                if (slot.takenByName == itemCode && actionInt == (int)action)
                {
                    reward += ProcessItemUsage(playerType, action, board[i], ref lives, ref cuff, animColor);
                    break;
                }
            }
        }

        newRound();
        return reward;
    }

    private float ProcessItemUsage(PlayerType playerType, ActionType action, GameObject itemSlot, ref int lives, ref bool cuff, string animColor)
    {
        float reward = 0;
        ItemSlot slot = itemSlot.GetComponent<ItemSlot>();
        string teamCode = GetTeamCode(playerType);

        if (action == ActionType.Drink)
        {
            Debug.Log("Energy Drink Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            slot.takenBy.GetComponent<Animator>().Play(animColor);
            StartCoroutine(itemUsage(6, itemSlot));
            rounds.Pop();
            if (knowledge != 2)
            {
                knowledge = 2;
            }
        }
        else if (action == ActionType.MagGlass)
        {
            Debug.Log("Mag Glass Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            slot.takenBy.GetComponent<Animator>().Play(animColor);
            StartCoroutine(itemUsage(6, itemSlot));

            if (rounds.Peek() == "real")
            {
                knowledge = 1;
            }
            else if (rounds.Peek() == "empty")
            {
                knowledge = 0;
            }
            else
            {
                knowledge = 2;
            }

            if (rounds.Count == 1 || totalEmpty == 0 || totalReal == 0 || knowledge != 2)
            {
                reward -= 1;
            }
            else
            {
                reward += 1;
            }
        }
        else if (action == ActionType.Cigar)
        {
            Debug.Log("Cigar Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            slot.takenBy.GetComponent<Animator>().Play(animColor);
            StartCoroutine(itemUsage(6, itemSlot));
            if (lives == 4)
            {
                reward -= 1;
            }
            else
            {
                reward += 0.5f;
                lives++;
            }
        }
        else if (action == ActionType.Knife)
        {
            Debug.Log("Knife Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            slot.takenBy.GetComponent<Animator>().Play(animColor);
            StartCoroutine(itemUsage(6, itemSlot));
            gunDamage = 2;
            Gun.GetComponent<Animator>().Play(GetKnifeAnimName(playerType));
            if (knowledge == 0 || gunDamage == 2 || totalReal == 0)
            {
                reward -= 1f;
            }
            else if (knowledge == 1)
            {
                reward += 2f;
            }
        }
        else if (action == ActionType.Handcuffs)
        {
            Debug.Log("Cuffs Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            // Note: Blue uses "Red" animation for cuffs, Red uses "Red" - keeping original behavior
            string cuffAnimColor = playerType == PlayerType.Blue ? "Red" : animColor;
            slot.takenBy.GetComponent<Animator>().Play(cuffAnimColor);
            StartCoroutine(itemUsage(6, itemSlot));
            if (cuff)
            {
                reward -= 0.5f;
            }
            else
            {
                reward += 1;
            }
            cuff = true;
        }

        return reward;
    }

    public float blueMove(int action) //OUTPUTS: 1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife
    {
        return ExecuteMove(PlayerType.Blue, (ActionType)action);
    }

    // 통합된 Shoot 메서드
    public float ExecuteShoot(PlayerType playerType, bool self)
    {
        float reward = 0;
        knowledge = 2;
        string teamCode = GetTeamCode(playerType);
        ref int playerLives = ref GetPlayerLives(playerType);
        ref int opponentLives = ref GetPlayerLives(playerType == PlayerType.Red ? PlayerType.Blue : PlayerType.Red);
        ref bool playerCuff = ref GetPlayerCuff(playerType);
        string nextTurn = playerType == PlayerType.Red ? "b" : "r";
        string selfTurn = teamCode;

        Debug.Log($"{playerType} Shooting");

        if (rounds.Peek() == "real" && self)
        {
            reward -= 3f;
            playerLives -= gunDamage;
            if (gunDamage == 2)
            {
                reward -= 2f;
                StartCoroutine(regrow());
            }
            gunDamage = 1;
            turn = nextTurn;
            if (playerType == PlayerType.Red)
            {
                totalReal--;
            }
        }
        else if (rounds.Peek() == "real" && !self)
        {
            reward += 5;
            opponentLives -= gunDamage;
            if (gunDamage == 2)
            {
                reward += 10;
                StartCoroutine(regrow());
            }
            gunDamage = 1;
            turn = playerType == PlayerType.Red ? "r" : "b";
            if (playerType == PlayerType.Red)
            {
                totalReal--;
            }
        }
        else if (rounds.Peek() == "empty")
        {
            if (gunDamage == 2)
            {
                StartCoroutine(regrow());
                gunDamage = 1;
            }
            if (self)
            {
                turn = selfTurn;
                reward += 3;
            }
            else
            {
                turn = nextTurn;
                reward -= 3;
            }
            totalEmpty--;
        }
        rounds.Pop();

        if (playerCuff)
        {
            playerCuff = false;
            turn = selfTurn;
        }

        if (blueLives < 0)
        {
            blueLives = 0;
        }

        if (redLives < 0)
        {
            redLives = 0;
        }

        return reward;
    }

    IEnumerator regrow()
    {
        yield return new WaitForSeconds(5);
        Gun.GetComponent<Animator>().Play("BarrelRegrow");
    }
    public float blueShoot(bool self)
    {
        return ExecuteShoot(PlayerType.Blue, self);
    }
    public float redMove(int action) //OUTPUTS: 1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife
    {
        return ExecuteMove(PlayerType.Red, (ActionType)action);
    }
    public float redShoot(bool self)
    {
        return ExecuteShoot(PlayerType.Red, self);
    }
    // 사용자 입력을 처리하는 메서드
    public void HandlePlayerAction(int action)
    {
        if (turn == "r" && play)
        {
            showMove(action, turn);
            string result = playStep(action.ToString());
            // 턴이 바뀌었으므로 블루 플레이어 턴 시작
            if (turn == "b" && isConnected)
            {
                // AI에 상태 요청
                SendToAI("get_state");
            }
        }
    }

    public void randomAction()
    {
        int move = UnityEngine.Random.Range(1, 8);
        if (turn == "r")
        {
            redMove(move);
            if (turn == "b") { Debug.Log("True"); } else { Debug.Log("FALSE"); }
        }
        else
        {
            blueMove(move);
            if (turn == "r") { Debug.Log("True"); } else { Debug.Log("FALSE"); }
        }
        showMove(move, turn);
        Debug.Log($"{rounds.Peek()} is the next bullet");
    }
    IEnumerator itemUsage(int seconds, GameObject item)
    {
        yield return new WaitForSeconds(seconds);
        umtd.Enqueue(() =>
        {
            if (item.GetComponent<ItemSlot>().takenBy)
            {
                Destroy(item.GetComponent<ItemSlot>().takenBy.gameObject);
                item.GetComponent<ItemSlot>().takenBy = null;
                item.GetComponent<ItemSlot>().takenByName = null;
            }
        });

    }
    public void newRound()
    {
        if (rounds.Count != 0)
        {
            return;
        }
        int numReal = UnityEngine.Random.Range(1, 5);
        int numEmpty = UnityEngine.Random.Range(1, 5);
        int totalRounds = numReal + numEmpty;
        totalEmpty = numEmpty;
        totalReal = numReal;


        for (int i = 0; i < totalRounds; i++)
        {
            int which = UnityEngine.Random.Range(0, 2);
            string toAdd;

            if (numReal == 0)
            {
                toAdd = "empty";
                numEmpty--;
            }
            else if (numEmpty == 0)
            {
                toAdd = "real";
                numReal--;
            }
            else if (which == 1)
            {
                toAdd = "real";
                numReal--;
            }
            else
            {
                toAdd = "empty";
                numEmpty--;
            }
            rounds.Push(toAdd);
        }
        int itemsToGive = UnityEngine.Random.Range(2, 5);
        addItems(redItems, itemsToGive, "r");
        addItems(blueItems, itemsToGive, "b");
    }
    private void Update()
    {
        blueHPShow.text = blueLives.ToString();
        redHPShow.text = redLives.ToString();

        if (blueLives == 0 || redLives == 0) {
            blueLives = 4;
            redLives = 4;
            for (int i = 0; i < redBoard.Length; i++)
            {
                itemUsage(0, redBoard[i]);
                itemUsage(0, blueBoard[i]);
            }
        }

        // Auto-reconnect logic
        if (!isConnected && isRunning && Time.time - lastReconnectAttempt > reconnectDelay)
        {
            lastReconnectAttempt = Time.time;
            ConnectToServer();
        }

        // 빨간 플레이어 턴이 시작되면 play를 true로 설정
        if (turn == "r" && !play)
        {
            play = true;
        }

        // 블루 플레이어 턴이 시작되면 AI에 상태 요청
        if (turn == "b" && play && isConnected)
        {
            SendToAI("get_state");
            // 한 번만 요청하도록 play를 false로 설정 (다음 턴까지 대기)
            play = false;
        }
    }
    public void addItems(List<GameObject> itemsList, int itemsToGive, string player)
    {

        for (int i = 0; i < itemsToGive; i++)
        {
            if (itemsList.Count == 8)
            {
                return;
            }
            int item = UnityEngine.Random.Range(0, 5);

            if (player == "r")
            {
                Debug.Log("New Items");
                for (int j = 0; j < redBoard.Length; j++)
                {
                    if (redBoard[j] != null && redBoard[j].GetComponent<ItemSlot>().takenBy == null)
                    {
                        Debug.Log(items[item]);
                        GameObject newItem = Instantiate(items[item], getSlot(item, redBoard[j]).position, items[item].transform.rotation);
                        ItemSlot n = redBoard[j].GetComponent<ItemSlot>();
                        n.takenBy = newItem;
                        n.takenByName = getName(item);
                        break;
                    }
                }
            }

            if (player == "b")
            {

                for (int k = 0; k < redBoard.Length; k++)
                {
                    if (blueBoard[k] != null && blueBoard[k].GetComponent<ItemSlot>().takenBy == null)
                    {
                        Debug.Log(items[item]);
                        GameObject newItem = Instantiate(items[item], getSlot(item, blueBoard[k]).position, items[item].transform.rotation);
                        blueBoard[k].GetComponent<ItemSlot>().takenBy = newItem;
                        ItemSlot n = blueBoard[k].GetComponent<ItemSlot>();
                        n.takenBy = newItem;
                        n.takenByName = getName(item);
                        break;
                    }
                }
            }

        }
    } //adds 4 random times to the items list til 8
    public Transform getSlot(int item, GameObject toSpawnAt)
    {
        string[] spawnNames = {
            "Energy Drink Spawn",
            "Maglifying Glass Spawn",
            "Cigar Spawn",
            "Knife Spawn",
            "Handcuffs Spawn"
        };

        Transform spawnPoint = toSpawnAt.transform.Find(spawnNames[item]);
        if (spawnPoint == null) {
            Debug.LogWarning($"Spawn point '{spawnNames[item]}' not found, using slot position");
            return toSpawnAt.transform;  // 슬롯의 기본 위치 사용
        }
        return spawnPoint;
    }
    public void showMove(int numAction, string player)
    {
        if (player == "r") //1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife
        {
            action.text = "Red: ";
        }
        else
        {
            action.text = "Blue: ";
        }

        if (numAction == 1)
        {
            action.text += "Shoot Self";
        }
        if (numAction == 2)
        {
            action.text += "Shoot Other";
        }
        if (numAction == 3)
        {
            action.text += "Drink";
        }
        if (numAction == 4)
        {
            action.text += "Mag. Glass";
        }
        if (numAction == 5)
        {
            action.text += "Cigar";
        }
        if (numAction == 6)
        {
            action.text += "Knife";
        }
        if (numAction == 7)
        {
            action.text += "Handcuffs";
        }
        nextBullet.text = $"Next Bullet: {rounds.Peek()}";
    }
    public string getName(int item)
    {
        if (item == 0)
        {
            return "ED";
        }
        else if (item == 1)
        {
            return "MG";
        }
        else if (item == 2)
        {
            return "C";
        }
        else if (item == 3)
        {
            return "K";
        }
        else
        {
            return "HC";
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
    void ReceiveData()
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
                    ProcessMessage(message);
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

    private void ProcessMessage(string message)
    {
        try
        {
            if (message == "get_state")
            {
                // 블루 플레이어의 턴일 때만 AI에 상태 전송
                if (turn == "b")
                {
                    umtd.Enqueue(() => {
                        try
                        {
                            string toSend = sendInput();
                            Debug.Log($"Sending state to AI: {toSend}");
                            SendToAI(toSend);
                        }
                        catch (Exception e)
                        {
                            Debug.LogError($"Error processing get_state: {e.Message}");
                        }
                    });
                }
            }
            else if (message.StartsWith("play_step:"))
            {
                // 블루 플레이어의 턴일 때만 AI 행동 처리
                if (turn == "b")
                {
                    string[] parts = message.Split(new[] { ':' }, 2);
                    if (parts.Length >= 2 && int.TryParse(parts[1], out int action))
                    {
                        umtd.Enqueue(() => {
                            try
                            {
                                string stateData = sendInput();
                                int playstep = action + 1; // Convert from 0-based to 1-based
                                showMove(playstep, turn);
                                string result = playStep(playstep.ToString());
                                string toSend = $"{stateData}:{result}";
                                Debug.Log($"Sending play_step result to AI: {toSend}");
                                SendToAI(toSend);
                            }
                            catch (Exception e)
                            {
                                Debug.LogError($"Error processing play_step: {e.Message}");
                            }
                        });
                    }
                    else
                    {
                        Debug.LogWarning($"Invalid play_step message format: {message}");
                    }
                }
            }
            else if (message == "reset")
            {
                umtd.Enqueue(() => {
                    try
                    {
                        for (int i = 0; i < redBoard.Length; i++)
                        {
                            itemUsage(0, redBoard[i]);
                            itemUsage(0, blueBoard[i]);
                        }
                        newRound();
                        Debug.Log("Game reset requested by AI");
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"Error processing reset: {e.Message}");
                    }
                });
            }
            else
            {
                Debug.LogWarning($"Unknown message from AI: {message}");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error processing message: {e.Message}");
        }
    }

    private void SendToAI(string message)
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

    public int boolToInt(bool b)
    {
        return b ? 1 : 0;
    }
    public string sendInput() //1) num bullets | 2) num real | 3) num fake | 4) red lives |
                              //5) blue lives | 6) red items (list) | 7) blue items (list) |
                              //8) gun damage | 9) next bullet (-1 if not aviable, 0 for fake, 1 for real)
    {

        string connected = "";
        List<string> saved = new List<string>();
        if (turn == "r")
        {
            saved.Add("1");
        }
        else
        {
            saved.Add("0");
        }
        saved.Add(rounds.Count.ToString());
        saved.Add(totalReal.ToString());
        saved.Add(totalEmpty.ToString());
        saved.Add(redLives.ToString());
        saved.Add(blueLives.ToString());
        saved.Add(getItems("r", "ED").ToString());
        saved.Add(getItems("r", "MG").ToString());
        saved.Add(getItems("r", "C").ToString());
        saved.Add(getItems("r", "K").ToString());
        saved.Add(getItems("r", "HC").ToString());
        saved.Add(getItems("b", "ED").ToString());
        saved.Add(getItems("b", "MG").ToString());
        saved.Add(getItems("b", "C").ToString());
        saved.Add(getItems("b", "K").ToString());
        saved.Add(getItems("b", "HC").ToString());
        saved.Add(gunDamage.ToString());
        saved.Add(knowledge.ToString());
        saved.Add(boolToInt(blueCuff).ToString());
        saved.Add(boolToInt(redCuff).ToString());
        for (int i = 0; i < saved.Count - 1; i++)
        {
            connected += saved[i] + ",";
        }
        connected += saved[saved.Count - 1];
        return connected;
    }


}
