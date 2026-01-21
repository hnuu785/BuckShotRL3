using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;

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
    static GameManager instance;
    public bool play; //determines whether the ais can play; adds pauses
    public bool waitingForRoundStart; // 라운드 시작 대기 상태
    public UnityMainThreadDispatcher umtd;
    private ItemManager itemManager;
    private AIClient aiClient;

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
    public TextMeshProUGUI bullets;
    public int scalar = 0;
    //AI PLANNING:
    //INPUTS:  1) num bullets | 2) num real | 3) num fake | 4) red lives | 5) blue lives | 6) red items (list) | 7) blue items (list) | 8) gun damage | 9) next bullet (-1 if not aviable, 0 for fake, 1 for real)
    //OUTPUTS: 1) shoot self | 2) shoot other | 3) drink | 4) mag. glass | 5) cig | 6) knife | 7) cuffs
    private void Awake()
    {
        Application.targetFrameRate = 50;
        Time.timeScale = 3;
        
        // ItemManager 초기화
        itemManager = gameObject.AddComponent<ItemManager>();
        itemManager.Initialize(redBoard, blueBoard, items);
        
        // AIClient 초기화
        aiClient = gameObject.AddComponent<AIClient>();
        aiClient.OnMessageReceived += ProcessMessage;
        
        // 초기 라운드 설정 (첫 라운드는 즉시 시작)
        waitingForRoundStart = false;
        turn = "r";
        play = true;
        newRound();
        // 첫 라운드는 즉시 시작 (newRound()에서 설정한 대기 상태를 해제)
        waitingForRoundStart = false;
        turn = "r";
        play = true;
        
        if (instance == null)
        {
            instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    void OnDestroy()
    {
        Application.targetFrameRate = -1;
        if (aiClient != null)
        {
            aiClient.OnMessageReceived -= ProcessMessage;
        }
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
        return itemManager.GetItems(team, item);
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

            if (!string.IsNullOrEmpty(itemCode) && itemManager.GetItems(teamCode, itemCode) == 0)
            {
                reward -= 50f;
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

        // 라운드 종료 조건 체크: 총알이 비었거나 체력이 0이 되었을 때
        if (rounds.Count == 0 || redLives <= 0 || blueLives <= 0)
        {
            // 체력이 0이 되었으면 라운드 종료
            if (redLives <= 0 || blueLives <= 0)
            {
                rounds.Clear();
                totalReal = 0;
                totalEmpty = 0;
            }
            newRound();
        }
        
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
            
            // Beer 보상: 실탄 배출 +5.0, 빈 총알 배출 +1.0
            if (rounds.Count > 0)
            {
                if (rounds.Peek() == "real")
                {
                    reward += 5f;
                    totalReal--;
                }
                else if (rounds.Peek() == "empty")
                {
                    reward += 1f;
                    totalEmpty--;
                }
            }
            
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
                // 쓸모없는 상황 - 보상 없음 (기존 -1 제거)
            }
            else
            {
                reward += 3f;
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
                reward -= 2f;
            }
            else
            {
                reward += 5f;
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
            // Knife 보상은 ExecuteShoot에서 처리됨
            // 사용 후 적중: +5.0 (데미지 보상과 별도), 사용 후 빗나감: -5.0
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
            
            // 수갑은 상대방의 수갑 상태를 설정해야 함
            PlayerType opponentType = playerType == PlayerType.Red ? PlayerType.Blue : PlayerType.Red;
            ref bool opponentCuff = ref GetPlayerCuff(opponentType);
            
            if (opponentCuff)
            {
                reward -= 10f;
            }
            else
            {
                reward += 7f;
            }
            opponentCuff = true; // 상대방의 수갑 상태를 true로 설정
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
        ref bool opponentCuff = ref GetPlayerCuff(playerType == PlayerType.Red ? PlayerType.Blue : PlayerType.Red);
        string nextTurn = playerType == PlayerType.Red ? "b" : "r";
        string selfTurn = teamCode;

        Debug.Log($"{playerType} Shooting");

        bool knifeUsed = (gunDamage == 2);
        
        if (rounds.Peek() == "real" && self)
        {
            reward -= gunDamage * 15f;
            playerLives -= gunDamage;
            if (knifeUsed)
            {
                StartCoroutine(regrow());
                // Knife 사용 후 적중: +5.0 (데미지 보상과 별도)
                reward += 5f;
            }
            
            // 자신의 체력이 0 이하가 되었을 때 패배 보상
            if (playerLives <= 0)
            {
                reward -= 50f;
            }
            
            gunDamage = 1;
            // 수갑 로직: 상대방이 수갑에 걸려있으면 상대방 턴 스킵하고 자신의 턴 유지
            if (opponentCuff)
            {
                opponentCuff = false;
                turn = selfTurn;
            }
            else
            {
                turn = nextTurn;
            }
            if (playerType == PlayerType.Red)
            {
                totalReal--;
            }
        }
        else if (rounds.Peek() == "real" && !self)
        {
            reward += gunDamage * 10f;
            opponentLives -= gunDamage;
            if (knifeUsed)
            {
                StartCoroutine(regrow());
                // Knife 사용 후 적중: +5.0 (데미지 보상과 별도)
                reward += 5f;
            }
            
            // 상대방 체력이 0 이하가 되었을 때 추가 보상 (라운드 승리)
            if (opponentLives <= 0)
            {
                reward += 50f;
            }
            
            gunDamage = 1;
            // 수갑 로직: 상대방이 수갑에 걸려있으면 상대방 턴 스킵하고 자신의 턴 유지
            if (opponentCuff)
            {
                opponentCuff = false;
                turn = selfTurn; // 상대방 턴 스킵하고 자신의 턴 유지
            }
            else
            {
                turn = nextTurn; // 상대방을 쐈을 때는 턴이 상대방으로 넘어가야 함
            }
            if (playerType == PlayerType.Red)
            {
                totalReal--;
            }
        }
        else if (rounds.Peek() == "empty")
        {
            if (knifeUsed)
            {
                StartCoroutine(regrow());
                gunDamage = 1;
                // Knife 사용 후 빗나감: -5.0 (아이템 낭비) - 상대에게 쏠 때만 적용
                if (!self)
                {
                    reward -= 5f;
                }
            }
            if (self)
            {
                turn = selfTurn;
                reward += 15f;
            }
            else
            {
                // 수갑 로직: 상대방이 수갑에 걸려있으면 상대방 턴 스킵하고 자신의 턴 유지
                if (opponentCuff)
                {
                    opponentCuff = false;
                    turn = selfTurn; // 상대방 턴 스킵하고 자신의 턴 유지
                }
                else
                {
                    turn = nextTurn;
                }
                reward -= 5f;
            }
            totalEmpty--;
        }
        rounds.Pop();

        if (blueLives < 0)
        {
            blueLives = 0;
        }

        if (redLives < 0)
        {
            redLives = 0;
        }
        
        // 체력이 0이 되었으면 라운드 종료를 위해 총알 제거
        if (redLives <= 0 || blueLives <= 0)
        {
            rounds.Clear();
            totalReal = 0;
            totalEmpty = 0;
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
            if (turn == "b" && aiClient != null && aiClient.IsConnected)
            {
                // AI에 상태 요청
                aiClient.SendToAI("get_state");
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
        
        // 라운드 시작 시 체력 리셋
        blueLives = 4;
        redLives = 4;
        
        // 아이템 제거
        for (int i = 0; i < redBoard.Length; i++)
        {
            itemUsage(0, redBoard[i]);
            itemUsage(0, blueBoard[i]);
        }
        
        // 새 총알 세트 생성
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
        
        // 다음 총알 정보 초기화 (알 수 없음)
        knowledge = 2;
        
        // 라운드 시작 대기 상태로 설정
        waitingForRoundStart = true;
        play = false;
        turn = ""; // 턴 초기화
    }
    
    // 시작 버튼을 눌렀을 때 호출되는 메서드
    public void StartRound()
    {
        if (waitingForRoundStart)
        {
            waitingForRoundStart = false;
            turn = "r"; // 빨간 플레이어부터 시작
            play = true;
        }
    }
    private void Update()
    {
        blueHPShow.text = blueLives.ToString();
        redHPShow.text = redLives.ToString();
        UpdateBulletsUI();
        UpdateNextBulletUI();

        // 라운드 시작 대기 중이면 게임 진행을 막음
        if (waitingForRoundStart)
        {
            return;
        }

        // 라운드 종료 조건: 총알이 비었거나 체력이 0이 되었을 때
        if (rounds.Count == 0 || blueLives <= 0 || redLives <= 0) {
            // 체력이 0이 되었으면 총알도 모두 제거
            if (blueLives <= 0 || redLives <= 0)
            {
                rounds.Clear();
                totalReal = 0;
                totalEmpty = 0;
            }
            
            // 새 라운드 시작 (체력 리셋은 newRound()에서 처리)
            newRound();
        }

        // 빨간 플레이어 턴이 시작되면 play를 true로 설정
        if (turn == "r" && !play)
        {
            play = true;
        }

        // 블루 플레이어 턴이 시작되면 AI에 상태 요청
        if (turn == "b" && play && aiClient != null && aiClient.IsConnected)
        {
            aiClient.SendToAI("get_state");
            // 한 번만 요청하도록 play를 false로 설정 (다음 턴까지 대기)
            play = false;
        }
    }

    private void UpdateBulletsUI()
    {
        if (bullets == null) return;
        int total = rounds != null ? rounds.Count : 0;
        bullets.text = $"Bullets: {total} (Real: {totalReal}, Fake: {totalEmpty})";
    }

    private void UpdateNextBulletUI()
    {
        if (nextBullet == null) return;
        
        // 디버그 용도: 실제 총알 정보 표시
        if (rounds == null || rounds.Count == 0)
        {
            nextBullet.text = "Next Bullet: None";
        }
        else
        {
            nextBullet.text = $"Next Bullet: {rounds.Peek()}";
        }
    }
    public void addItems(List<GameObject> itemsList, int itemsToGive, string player)
    {
        itemManager.AddItems(itemsList, itemsToGive, player);
    } //adds 4 random times to the items list til 8
    public Transform getSlot(int item, GameObject toSpawnAt)
    {
        return itemManager.GetSlot(item, toSpawnAt);
    }
    public void showMove(int numAction, string player)
    {
        string[] actionNames = { "", "Shoot Self", "Shoot Other", "Drink", "Mag. Glass", "Cigar", "Knife", "Handcuffs" };
        string playerName = player == "r" ? "Red" : "Blue";
        
        action.text = $"{playerName}: {(numAction >= 1 && numAction < actionNames.Length ? actionNames[numAction] : "")}";
        UpdateNextBulletUI();
    }
    public string getName(int item)
    {
        return itemManager.GetItemName(item);
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
                            if (aiClient != null)
                            {
                                aiClient.SendToAI(toSend);
                            }
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
                                if (aiClient != null)
                                {
                                    aiClient.SendToAI(toSend);
                                }
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
        saved.Add(itemManager.GetItems("r", "ED").ToString());
        saved.Add(itemManager.GetItems("r", "MG").ToString());
        saved.Add(itemManager.GetItems("r", "C").ToString());
        saved.Add(itemManager.GetItems("r", "K").ToString());
        saved.Add(itemManager.GetItems("r", "HC").ToString());
        saved.Add(itemManager.GetItems("b", "ED").ToString());
        saved.Add(itemManager.GetItems("b", "MG").ToString());
        saved.Add(itemManager.GetItems("b", "C").ToString());
        saved.Add(itemManager.GetItems("b", "K").ToString());
        saved.Add(itemManager.GetItems("b", "HC").ToString());
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