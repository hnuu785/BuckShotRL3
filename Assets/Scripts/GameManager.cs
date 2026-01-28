using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;

public class GameManager : MonoBehaviour
{
    static GameManager instance;
    public bool play; //determines whether the ais can play; adds pauses
    public bool waitingForRoundStart; // 라운드 시작 대기 상태
    public bool isGameOver; // 게임 종료 상태
    public UnityMainThreadDispatcher umtd;
    private ItemManager itemManager;
    private RoundManager roundManager;
    private RewardManager rewardManager;
    private SocketClient socketClient;
    [Header("UI Manager")]
    public UIManager uiManager;

    // ActionType을 아이템 코드로 매핑하는 딕셔너리
    private static readonly Dictionary<ActionType, string> ActionToItemCode = new Dictionary<ActionType, string>
    {
        { ActionType.Drink, ItemCode.EnergyDrink },
        { ActionType.MagGlass, ItemCode.MagnifyingGlass },
        { ActionType.Cigar, ItemCode.Cigar },
        { ActionType.Knife, ItemCode.Knife },
        { ActionType.Handcuffs, ItemCode.Handcuffs }
    };

    // 플레이어 상태 관리
    private PlayerState redPlayerState;
    private PlayerState bluePlayerState;
    
    // 외부 접근을 위한 프로퍼티
    public PlayerState RedPlayerState => redPlayerState;
    public PlayerState BluePlayerState => bluePlayerState;

    [Header("Gameplay")]
    public PlayerType? turn; // Red or Blue player's turn
    public GameObject[] items;
    public List<GameObject> redItems = new List<GameObject>(); //items: 1: drink (unload gun 1) 2: mag. glass (view barrel) 3: cig (heal +1) 4: knife (2 dmg)
    public List<GameObject> blueItems = new List<GameObject>();
    public GameObject bluePlayer;
    public GameObject redPlayer;
    public GameObject Gun;
    public GameObject[] redBoard;
    public GameObject[] blueBoard;
    public int gunDamage;
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
        
        // RoundManager 초기화
        roundManager = gameObject.AddComponent<RoundManager>();
        
        // RewardManager 초기화
        rewardManager = gameObject.AddComponent<RewardManager>();
        
        // SocketClient 초기화
        socketClient = gameObject.AddComponent<SocketClient>();
        socketClient.OnMessageReceived += ProcessMessage;
        
        // UIManager 초기화 (Inspector에서 할당되지 않았으면 자동으로 찾거나 생성)
        if (uiManager == null)
        {
            uiManager = GetComponent<UIManager>();
            if (uiManager == null)
            {
                uiManager = FindFirstObjectByType<UIManager>();
                if (uiManager == null)
                {
                    uiManager = gameObject.AddComponent<UIManager>();
                }
            }
        }
        
        // UIManager에 GameManager 참조 전달
        if (uiManager != null)
        {
            uiManager.Initialize(this);
        }
        
        // 플레이어 상태 초기화
        redPlayerState = new PlayerState(4, 4);
        bluePlayerState = new PlayerState(4, 4);
        
        // 게임 초기화
        isGameOver = false;
        turn = PlayerType.Red; // 첫 게임 시작 시 빨간 플레이어부터 시작
        
        // 첫 라운드 준비 후 스타트 화면부터 보이도록 대기
        newRound();
        waitingForRoundStart = true;
        play = false;
        
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
        if (socketClient != null)
        {
            socketClient.OnMessageReceived -= ProcessMessage;
        }
    }

    public string playStep(string toPlay)
    {
        string toSend = "";
        if(turn == PlayerType.Red)
        {
            toSend += redMove(int.Parse(toPlay)).ToString();
            toSend += ":";
            // 게임 종료 상태를 반환 (Python이 기대하는 done 값)
            toSend += isGameOver.ToString();
        }
        else if(turn == PlayerType.Blue)
        {
            toSend += blueMove(int.Parse(toPlay)).ToString();
            toSend += ":";
            // 게임 종료 상태를 반환 (Python이 기대하는 done 값)
            toSend += isGameOver.ToString();
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

    /// <summary>
    /// 플레이어 타입에 해당하는 PlayerState를 반환합니다.
    /// </summary>
    private PlayerState GetPlayerState(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? redPlayerState : bluePlayerState;
    }

    private string GetAnimColorName(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? "Red" : "Blue";
    }

    private float GetInvalidActionPenalty(PlayerType playerType)
    {
        return playerType == PlayerType.Red ? 10f : 50f;
    }

    // ActionType을 아이템 코드로 변환하는 헬퍼 메서드
    private string GetItemCodeFromAction(ActionType action)
    {
        return ActionToItemCode.TryGetValue(action, out string itemCode) ? itemCode : "";
    }

    // 체력을 0 이상으로 보정하는 메서드 (PlayerState에서 자동 처리되므로 제거 가능하지만 호환성을 위해 유지)
    private void ClampLives()
    {
        // PlayerState의 Lives 프로퍼티가 자동으로 Clamp를 처리하므로 별도 작업 불필요
        // 하지만 기존 코드와의 호환성을 위해 메서드는 유지
    }

    // 게임 종료 조건을 체크하고 처리하는 메서드
    // 반환값: 게임이 종료되었으면 true, 아니면 false
    private bool CheckAndHandleGameOver()
    {
        if (redPlayerState.IsDead() || bluePlayerState.IsDead())
        {
            // 게임 종료 (라운드 종료가 아님)
            isGameOver = true;
            roundManager.ClearRounds();
            play = false;
            return true;
        }
        return false;
    }

    // 라운드 종료 조건을 체크하고 처리하는 메서드
    private void CheckAndHandleRoundEnd()
    {
        if (roundManager.IsEmpty())
        {
            // 새 라운드 시작 (체력은 리셋되지 않음)
            newRound();
        }
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
        PlayerState playerState = GetPlayerState(playerType);
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
            string itemCode = GetItemCodeFromAction(action);

            if (!string.IsNullOrEmpty(itemCode) && itemManager.GetItems(teamCode, itemCode) == 0)
            {
                reward += rewardManager.CalculateInvalidActionPenalty();
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
                    reward += ProcessItemUsage(playerType, action, board[i], playerState, animColor);
                    break;
                }
            }
        }

        // 게임 종료 조건 체크: 체력이 0이 되었을 때
        if (CheckAndHandleGameOver())
        {
            return reward;
        }
        
        // 게임 종료 상태가 아니면 라운드 종료 조건 체크: 총알이 다 떨어졌을 때
        if (!isGameOver)
        {
            CheckAndHandleRoundEnd();
        }
        
        return reward;
    }

    private float ProcessItemUsage(PlayerType playerType, ActionType action, GameObject itemSlot, PlayerState playerState, string animColor)
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
            if (roundManager.GetRoundCount() > 0)
            {
                bool isReal = roundManager.IsNextRoundReal();
                reward += rewardManager.CalculateBeerReward(isReal);
            }
            
            roundManager.PopRound();
            if (roundManager.Knowledge != 2)
            {
                roundManager.Knowledge = 2;
            }
        }
        else if (action == ActionType.MagGlass)
        {
            Debug.Log("Mag Glass Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            slot.takenBy.GetComponent<Animator>().Play(animColor);
            StartCoroutine(itemUsage(6, itemSlot));

            if (roundManager.IsNextRoundReal())
            {
                roundManager.Knowledge = 1;
            }
            else if (roundManager.IsNextRoundEmpty())
            {
                roundManager.Knowledge = 0;
            }
            else
            {
                roundManager.Knowledge = 2;
            }

            reward += rewardManager.CalculateMagGlassReward(
                roundManager.GetRoundCount(),
                roundManager.TotalEmpty,
                roundManager.TotalReal,
                roundManager.Knowledge
            );
        }
        else if (action == ActionType.Cigar)
        {
            Debug.Log("Cigar Used");
            umtd.Enqueue(playAnimation(slot.takenBy.GetComponent<Animator>(), animColor));
            umtd.Enqueue(itemUsage(6, itemSlot));
            slot.takenBy.GetComponent<Animator>().Play(animColor);
            StartCoroutine(itemUsage(6, itemSlot));
            
            // Cigar 보상 계산
            float cigarReward = rewardManager.CalculateCigarReward(playerState.Lives, playerState.MaxLives);
            reward += cigarReward;
            
            // 체력 회복 (최대 체력 초과 불가)
            playerState.Heal(1);
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
            roundManager.Knowledge = 2; // Knife 사용 시 knowledge 초기화
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
            PlayerState opponentState = GetPlayerState(opponentType);
            
            reward += rewardManager.CalculateHandcuffsReward(opponentState.IsHandcuffed);
            opponentState.IsHandcuffed = true; // 상대방의 수갑 상태를 true로 설정
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
        roundManager.Knowledge = 2;
        string teamCode = GetTeamCode(playerType);
        PlayerState playerState = GetPlayerState(playerType);
        PlayerState opponentState = GetPlayerState(playerType == PlayerType.Red ? PlayerType.Blue : PlayerType.Red);
        PlayerType nextTurn = playerType == PlayerType.Red ? PlayerType.Blue : PlayerType.Red;
        PlayerType selfTurn = playerType;

        Debug.Log($"{playerType} Shooting");

        bool knifeUsed = (gunDamage == 2);
        
        bool isReal = roundManager.IsNextRoundReal();
        
        if (isReal && self)
        {
            playerState.TakeDamage(gunDamage);
            reward += rewardManager.CalculateShootReward(true, true, gunDamage, knifeUsed, playerState.Lives, opponentState.Lives);
            
            if (knifeUsed)
            {
                StartCoroutine(regrow());
            }
            
            gunDamage = 1;
            // 수갑 로직: 상대방이 수갑에 걸려있으면 상대방 턴 스킵하고 자신의 턴 유지
            if (opponentState.IsHandcuffed)
            {
                opponentState.IsHandcuffed = false;
                turn = selfTurn;
            }
            else
            {
                turn = nextTurn;
            }
            roundManager.PopRound();
        }
        else if (isReal && !self)
        {
            opponentState.TakeDamage(gunDamage);
            reward += rewardManager.CalculateShootReward(true, false, gunDamage, knifeUsed, playerState.Lives, opponentState.Lives);
            
            if (knifeUsed)
            {
                StartCoroutine(regrow());
            }
            
            gunDamage = 1;
            // 수갑 로직: 상대방이 수갑에 걸려있으면 상대방 턴 스킵하고 자신의 턴 유지
            if (opponentState.IsHandcuffed)
            {
                opponentState.IsHandcuffed = false;
                turn = selfTurn; // 상대방 턴 스킵하고 자신의 턴 유지
            }
            else
            {
                turn = nextTurn; // 상대방을 쐈을 때는 턴이 상대방으로 넘어가야 함
            }
            roundManager.PopRound();
        }
        else if (roundManager.IsNextRoundEmpty())
        {
            reward += rewardManager.CalculateShootReward(false, self, gunDamage, knifeUsed, playerState.Lives, opponentState.Lives);
            
            if (knifeUsed)
            {
                StartCoroutine(regrow());
                gunDamage = 1;
            }
            
            if (self)
            {
                turn = selfTurn;
            }
            else
            {
                // 수갑 로직: 상대방이 수갑에 걸려있으면 상대방 턴 스킵하고 자신의 턴 유지
                if (opponentState.IsHandcuffed)
                {
                    opponentState.IsHandcuffed = false;
                    turn = selfTurn; // 상대방 턴 스킵하고 자신의 턴 유지
                }
                else
                {
                    turn = nextTurn;
                }
            }
            roundManager.PopRound();
        }

        // 체력을 0 이상으로 보정
        ClampLives();
        
        // 체력이 0이 되었으면 게임 종료
        CheckAndHandleGameOver();

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
        if (turn == PlayerType.Red && play)
        {
            showMove(action, turn);
            string result = playStep(action.ToString());
            // 턴이 바뀌었으므로 블루 플레이어 턴 시작
            if (turn == PlayerType.Blue && socketClient != null && socketClient.IsConnected)
            {
                // AI에 상태 요청
                socketClient.SendToAI("get_state");
            }
        }
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
        if (!roundManager.IsEmpty())
        {
            return;
        }
        
        // 게임이 종료된 상태면 새 라운드를 시작하지 않음
        if (isGameOver)
        {
            return;
        }
        
        // 중요: 체력은 리셋하지 않음 (게임 시작 시에만 초기화됨)
        // 중요: 아이템은 제거하지 않음 (라운드 간 아이템 유지)
        
        // 새 총알 세트 생성 (RoundManager에서 처리)
        roundManager.GenerateNewRound();
        
        // 아이템 추가
        int itemsToGive = UnityEngine.Random.Range(2, 5);
        addItems(redItems, itemsToGive, GetTeamCode(PlayerType.Red));
        addItems(blueItems, itemsToGive, GetTeamCode(PlayerType.Blue));
        
        // 라운드 자동 시작 (게임 종료 후가 아닌 경우)
        // 중요: 턴은 초기화하지 않음 (이전 라운드의 턴 유지)
        waitingForRoundStart = false;
        // turn은 변경하지 않음 - 현재 턴 유지
        play = true;
    }
    
    // 시작 버튼을 눌렀을 때 호출되는 메서드
    public void StartRound()
    {
        // 게임 종료 상태에서 START 버튼을 누르면 새 게임 시작
        if (isGameOver)
        {
            ResetGame();
            newRound();
            waitingForRoundStart = false;
            turn = PlayerType.Red; // 빨간 플레이어부터 시작
            play = true;
            return;
        }
        
        // 라운드 시작 대기 중이면 라운드 시작
        if (waitingForRoundStart)
        {
            waitingForRoundStart = false;
            turn = PlayerType.Red; // 빨간 플레이어부터 시작
            play = true;
        }
    }
    
    // 게임 완전 리셋 메서드
    public void ResetGame()
    {
        isGameOver = false;
        redPlayerState.Reset();
        bluePlayerState.Reset();
        roundManager.ClearRounds();
        gunDamage = 1;
        
        // 아이템 제거
        for (int i = 0; i < redBoard.Length; i++)
        {
            itemUsage(0, redBoard[i]);
            itemUsage(0, blueBoard[i]);
        }
    }
    private void Update()
    {
        // UI 업데이트
        if (uiManager != null)
        {
            uiManager.UpdateUI();
        }

        // 게임이 종료된 상태면 더 이상 진행하지 않음
        if (isGameOver)
        {
            return;
        }

        // 라운드 시작 대기 중이면 게임 진행을 막음
        if (waitingForRoundStart)
        {
            return;
        }

        // 게임 종료 조건 체크: 체력이 0이 되었을 때
        if (CheckAndHandleGameOver())
        {
            return;
        }

        // 게임 종료 상태가 아니면 라운드 종료 조건 체크: 총알이 다 떨어졌을 때
        if (!isGameOver)
        {
            CheckAndHandleRoundEnd();
        }

        // 게임 종료 상태면 더 이상 진행하지 않음
        if (isGameOver)
        {
            return;
        }

        // 빨간 플레이어 턴이 시작되면 play를 true로 설정
        if (turn == PlayerType.Red && !play)
        {
            play = true;
        }

        // 블루 플레이어 턴이 시작되면 AI에 상태 요청
        if (turn == PlayerType.Blue && play && socketClient != null && socketClient.IsConnected)
        {
            socketClient.SendToAI("get_state");
            // 한 번만 요청하도록 play를 false로 설정 (다음 턴까지 대기)
            play = false;
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
    public void showMove(int numAction, PlayerType? player)
    {
        // 액션 표시 UI 제거됨
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
                // 게임 종료 상태면 AI에 상태를 전송하지 않음
                if (isGameOver)
                {
                    Debug.LogWarning("Game is over. Ignoring get_state message from AI.");
                    return;
                }
                
                // 블루 플레이어의 턴일 때만 AI에 상태 전송
                if (turn == PlayerType.Blue)
                {
                    umtd.Enqueue(() => {
                        try
                        {
                            // 게임 종료 상태 재확인 (비동기 처리 중 게임이 종료되었을 수 있음)
                            if (isGameOver)
                            {
                                Debug.LogWarning("Game ended during get_state processing. Not sending state to AI.");
                                return;
                            }
                            
                            string toSend = sendInput();
                            Debug.Log($"Sending state to AI: {toSend}");
                            if (socketClient != null)
                            {
                                socketClient.SendToAI(toSend);
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
                // 게임 종료 상태면 AI 행동을 처리하지 않음
                if (isGameOver)
                {
                    Debug.LogWarning("Game is over. Ignoring play_step message from AI.");
                    return;
                }
                
                // 블루 플레이어의 턴일 때만 AI 행동 처리
                if (turn == PlayerType.Blue)
                {
                    string[] parts = message.Split(new[] { ':' }, 2);
                    if (parts.Length >= 2 && int.TryParse(parts[1], out int action))
                    {
                        umtd.Enqueue(() => {
                            try
                            {
                                // 게임 종료 상태 재확인 (비동기 처리 중 게임이 종료되었을 수 있음)
                                if (isGameOver)
                                {
                                    Debug.LogWarning("Game ended during play_step processing. Ignoring action.");
                                    return;
                                }
                                
                                string stateData = sendInput();
                                int playstep = action + 1; // Convert from 0-based to 1-based
                                showMove(playstep, turn);
                                string result = playStep(playstep.ToString());
                                
                                // 게임 종료 후에는 AI에 결과를 전송하지 않음
                                if (isGameOver)
                                {
                                    Debug.Log("Game ended after play_step. Not sending result to AI.");
                                    return;
                                }
                                
                                string toSend = $"{stateData}:{result}";
                                Debug.Log($"Sending play_step result to AI: {toSend}");
                                if (socketClient != null)
                                {
                                    socketClient.SendToAI(toSend);
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
                        // reset은 게임 종료 상태에서만 처리 (의도치 않은 reset 방지)
                        if (isGameOver)
                        {
                            ResetGame();
                            newRound();
                            Debug.Log("Game reset requested by AI");
                        }
                        else
                        {
                            Debug.LogWarning("Reset message received but game is not over. Ignoring reset request.");
                        }
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
        if (turn == PlayerType.Red)
        {
            saved.Add("1");
        }
        else if (turn == PlayerType.Blue)
        {
            saved.Add("0");
        }
        else
        {
            saved.Add("0"); // null인 경우 기본값
        }
        saved.Add(roundManager.GetRoundCount().ToString());
        saved.Add(roundManager.TotalReal.ToString());
        saved.Add(roundManager.TotalEmpty.ToString());
        saved.Add(redPlayerState.Lives.ToString());
        saved.Add(bluePlayerState.Lives.ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Red), ItemCode.EnergyDrink).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Red), ItemCode.MagnifyingGlass).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Red), ItemCode.Cigar).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Red), ItemCode.Knife).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Red), ItemCode.Handcuffs).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Blue), ItemCode.EnergyDrink).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Blue), ItemCode.MagnifyingGlass).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Blue), ItemCode.Cigar).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Blue), ItemCode.Knife).ToString());
        saved.Add(itemManager.GetItems(GetTeamCode(PlayerType.Blue), ItemCode.Handcuffs).ToString());
        saved.Add(gunDamage.ToString());
        saved.Add(roundManager.Knowledge.ToString());
        saved.Add(boolToInt(bluePlayerState.IsHandcuffed).ToString());
        saved.Add(boolToInt(redPlayerState.IsHandcuffed).ToString());
        for (int i = 0; i < saved.Count - 1; i++)
        {
            connected += saved[i] + ",";
        }
        connected += saved[saved.Count - 1];
        return connected;
    }
}