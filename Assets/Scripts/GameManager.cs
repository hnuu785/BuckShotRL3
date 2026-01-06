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
    public float blueMove(int action) //OUTPUTS: 1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife
    {
        float reward = 0;
        if (action == 1)
        {
            Gun.GetComponent<Animator>().StopPlayback();
            Gun.GetComponent<Animator>().Rebind();

            if (gunDamage == 2)
            {
                umtd.Enqueue(playAnimation(Gun.GetComponent<Animator>(), "BlueShootBlue-2DMG"));
                Gun.GetComponent<Animator>().Play("BlueShootBlue-2DMG");
            }
            else
            {
                umtd.Enqueue(playAnimation(Gun.GetComponent<Animator>(), "BlueShootBlue-1DMG"));
                Gun.GetComponent<Animator>().Play("BlueShootBlue-1DMG");
            }
            reward += blueShoot(true);
        }
        else if (action == 2)
        {
            Gun.GetComponent<Animator>().StopPlayback();
            Gun.GetComponent<Animator>().Rebind();
            if (gunDamage == 2)
            {
                umtd.Enqueue(playAnimation(Gun.GetComponent<Animator>(), "BlueShootRed-2DMG"));
                Gun.GetComponent<Animator>().Play("BlueShootRed-2DMG");
            }
            else
            {
                umtd.Enqueue(playAnimation(Gun.GetComponent<Animator>(), "BlueShootRed-1DMG"));
                Gun.GetComponent<Animator>().Play("BlueShootRed-1DMG");
            }
            reward += blueShoot(true);
        }
        //tell AI that it's blue's move
        else
        {
            if (action == 3 && getItems("b", "ED") == 0)
            {
                reward -= 50f + scalar;
                scalar++;
            }
            else if (action == 4 && getItems("b", "MG") == 0)
            {
                reward -= 50f + scalar;
                scalar++;
            }
            else if (action == 5 && getItems("b", "C") == 0)
            {
                reward -= 50f + scalar;
                scalar++;
            }
            else if (action == 6 && getItems("b", "K") == 0)
            {
                reward -= 50f + scalar;
                scalar++;
            }
            else if (action == 7 && getItems("b", "HC") == 0)
            {
                reward -= 50f + scalar;
                scalar++;
            }
            else
            {
                scalar = 0;
            }
            for (int i = 0; i < blueBoard.Length; i++)
            {
                if (blueBoard[i].GetComponent<ItemSlot>().takenByName == "ED" && action == 3)
                {
                    Debug.Log("Energy Drink Used");

                    umtd.Enqueue(playAnimation(blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Blue"));
                    umtd.Enqueue(itemUsage(6, blueBoard[i]));
                    blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Blue");
                    StartCoroutine(itemUsage(6, blueBoard[i]));
                    rounds.Pop();
                    if (knowledge != 2)
                    {
                        knowledge = 2;
                    }
                    break;
                }
                else if (blueBoard[i].GetComponent<ItemSlot>().takenByName == "MG" && action == 4)
                {
                    Debug.Log("Mag Glass Used");

                    umtd.Enqueue(playAnimation(blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Blue"));
                    umtd.Enqueue(itemUsage(6, blueBoard[i]));
                    blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Blue");
                    StartCoroutine(itemUsage(6, blueBoard[i]));

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
                        reward++;
                    }
                    break;
                }
                else if (blueBoard[i].GetComponent<ItemSlot>().takenByName == "C" && action == 5)
                {
                    Debug.Log("Cigar Used");

                    umtd.Enqueue(playAnimation(blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Blue"));
                    umtd.Enqueue(itemUsage(6, blueBoard[i]));
                    blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Blue");
                    StartCoroutine(itemUsage(6, blueBoard[i]));
                    if (blueLives == 4)
                    {
                        reward -= 1;
                        break;
                        //penalize for using
                    }
                    else
                    {
                        reward += 0.5f;
                        blueLives++;
                    }
                    break;
                }
                else if (blueBoard[i].GetComponent<ItemSlot>().takenByName == "K" && action == 6)
                {
                    Debug.Log("Knife Used");

                    umtd.Enqueue(playAnimation(blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Blue"));
                    umtd.Enqueue(itemUsage(6, blueBoard[i]));
                    blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Blue");
                    StartCoroutine(itemUsage(6, blueBoard[i]));
                    gunDamage = 2;
                    Gun.GetComponent<Animator>().Play("BlueKnife");
                    if (knowledge == 0 || gunDamage == 2 || totalReal == 0)
                    {
                        reward -= 1f;
                    }
                    else if(knowledge == 1)
                    {
                        reward += 2f;
                    }
                    break;
                }
                else if (blueBoard[i].GetComponent<ItemSlot>().takenByName == "HC" && action == 7)
                {
                    Debug.Log("Cuffs Used");

                    umtd.Enqueue(playAnimation(blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Blue"));
                    umtd.Enqueue(itemUsage(6, blueBoard[i]));
                    blueBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Red");
                    StartCoroutine(itemUsage(6, blueBoard[i]));
                    if (blueCuff)
                    {
                        reward -= 0.5f;
                    }
                    else
                    {
                        reward += 1;
                    }
                    blueCuff = true;
                    break;
                }
            }
        }

        newRound();
        return reward;
    }

    IEnumerator regrow()
    {
        yield return new WaitForSeconds(5);
        Gun.GetComponent<Animator>().Play("BarrelRegrow");
    }
    public float blueShoot(bool self)
    {
        float reward = 0;
        knowledge = 2;
        Debug.Log("Blue Shooting");
        if (rounds.Peek() == "real" && self)
        {
            reward -= 3f;
            blueLives -= gunDamage;
            if (gunDamage == 2)
            {
                reward -= 2;
                StartCoroutine(regrow());
            }
            gunDamage = 1;
            turn = "r";
        }
        else if (rounds.Peek() == "real" && !self)
        {
            reward += 5;
            redLives -= gunDamage;
            if (gunDamage == 2)
            {
                reward += 10;
                StartCoroutine(regrow());
            }
            gunDamage = 1;
            turn = "b";
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
                turn = "b";
                reward += 3;
            }
            else
            {
                turn = "r";
                reward -= 3;
            }
            totalEmpty--;
        }
        rounds.Pop();

        if (blueCuff)
        {
            blueCuff = false;
            turn = "b";
        }

        if(blueLives < 0)
        {
            blueLives = 0;
        }

        if(redLives < 0)
        {
            redLives = 0;
        }

        return reward;
    }
    public float redMove(int action) //OUTPUTS: 1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife
    {
        float reward = 0;
        if (action == 1)
        {
            Gun.GetComponent<Animator>().StopPlayback();
            Gun.GetComponent<Animator>().Rebind();
            reward += redShoot(true);
            if (gunDamage == 2)
            {
                Gun.GetComponent<Animator>().Play("RedShootRed-2DMG");
            }
            else
            {
                Gun.GetComponent<Animator>().Play("RedShootRed-1DMG");
            }
        }
        else if (action == 2)
        {
            Gun.GetComponent<Animator>().StopPlayback();
            Gun.GetComponent<Animator>().Rebind();
            reward += redShoot(false);
            if (gunDamage == 2)
            {
                Gun.GetComponent<Animator>().Play("RedShootBlue-2DMG");
            }
            else
            {
                Gun.GetComponent<Animator>().Play("RedShootBlue-1DMG");
            }
        }
        else
        {
            if(action == 3 && getItems("r","ED") == 0)
            {
                reward -= 10f + scalar;
                scalar++;
            }
            else if (action == 4 && getItems("r", "MG") == 0)
            {
                reward -= 10f + scalar;
                scalar++;
            }
            else if (action == 5 && getItems("r", "C") == 0)
            {
                reward -= 10f + scalar;
                scalar++;
            }
            else if (action == 6 && getItems("r", "K") == 0)
            {
                reward -= 10f + scalar;
                scalar++;
            }
            else if (action == 7 && getItems("r", "HC") == 0)
            {
                reward -= 10f + scalar;
                scalar++;
            }
            else
            {
                scalar = 0;
            }
            for (int i = 0; i < redBoard.Length; i++)
            {
                if (redBoard[i].GetComponent<ItemSlot>().takenByName == "ED" && action == 3)
                {
                    umtd.Enqueue(playAnimation(redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Red"));
                    umtd.Enqueue(itemUsage(6, redBoard[i]));
                    redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Red");
                    StartCoroutine(itemUsage(6, redBoard[i]));
                    rounds.Pop();

                    if(knowledge != 2)
                    {
                        knowledge = 2;
                    }
                    break;
                }
                else if (redBoard[i].GetComponent<ItemSlot>().takenByName == "MG" && action == 4)
                {
                    umtd.Enqueue(playAnimation(redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Red"));
                    umtd.Enqueue(itemUsage(6, redBoard[i]));
                    redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Red");
                    StartCoroutine(itemUsage(6, redBoard[i]));
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

                    if(rounds.Count == 1 || totalEmpty == 0 || totalReal == 0 || knowledge != 2)
                    {
                        reward -= 1;
                    }
                    else
                    {
                        reward += 1;
                    }

                    break;
                }
                else if (redBoard[i].GetComponent<ItemSlot>().takenByName == "C" && action == 5)
                {
                    umtd.Enqueue(playAnimation(redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Red"));
                    umtd.Enqueue(itemUsage(6, redBoard[i]));
                    redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Red");
                    StartCoroutine(itemUsage(6, redBoard[i]));
                    if (redLives == 4)
                    {
                        reward -= 1;
                        break;
                    }
                    else
                    {
                        redLives++;
                        reward += 0.5f;
                    }
                    break;
                }
                else if (redBoard[i].GetComponent<ItemSlot>().takenByName == "K" && action == 6)
                {
                    umtd.Enqueue(playAnimation(redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Red"));
                    umtd.Enqueue(itemUsage(6, redBoard[i]));
                    redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Red");
                    Gun.GetComponent<Animator>().Play("RedKnife");
                    if (knowledge == 0 || gunDamage == 2 || totalReal == 0)
                    {
                        reward -= 1f;
                    }
                    else if (knowledge == 1)
                    {
                        reward += 2f;
                    }
                    gunDamage = 2;

                    StartCoroutine(itemUsage(6, redBoard[i]));


                    break;
                }
                else if (redBoard[i].GetComponent<ItemSlot>().takenByName == "HC" && action == 7)
                {
                    umtd.Enqueue(playAnimation(redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>(), "Red"));
                    umtd.Enqueue(itemUsage(6, redBoard[i]));
                    redBoard[i].GetComponent<ItemSlot>().takenBy.GetComponent<Animator>().Play("Red");
                    StartCoroutine(itemUsage(6, redBoard[i]));
                    if (redCuff)
                    {
                        reward -= 0.5f;
                    }
                    else
                    {
                        reward += 1;
                    }
                    redCuff = true;
                    break;
                }
            }
        }

        newRound();
        return reward;
    }
    public float redShoot(bool self)
    {
        knowledge = 2;
        float reward = 0;
        if (rounds.Peek() == "real" && self)
        {
            reward -= 3f;
            redLives -= gunDamage;
            if (gunDamage == 2)
            {
                StartCoroutine(regrow());
                reward -= 2f;
            }
            gunDamage = 1;
            turn = "b";
            totalReal--;
        }
        else if (rounds.Peek() == "real" && !self)
        {
            blueLives -= gunDamage;
            reward += 5;
            if (gunDamage == 2)
            {
                StartCoroutine(regrow());
                reward += 10;
            }
            gunDamage = 1;
            turn = "r";
            totalReal--;
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
                turn = "r";
                reward += 3;
            }
            else
            {
                turn = "b";
                reward -= 3;
            }
            totalEmpty--;
        }
        rounds.Pop();

        if (redCuff)
        {
            redCuff = false;
            turn = "r";
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
