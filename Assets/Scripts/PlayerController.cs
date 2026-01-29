using UnityEngine;
using UnityEngine.UI;

public class PlayerController : MonoBehaviour
{
    public GameManager gameManager;
    public GameObject actionPanel; // 액션 선택 패널
    public Button[] actionButtons; // 액션 버튼들 (2개: shoot self, shoot other) - 아이템은 ItemSlot 클릭으로 사용
    public Button startRoundButton; // 라운드 시작 버튼
    public GameObject startRoundPanel; // 라운드 시작 패널

    void Start()
    {
        gameManager = FindFirstObjectByType<GameManager>();
        HideActionPanel();
        // 맨 처음에는 스타트 패널 표시, 대기 중이 아니면 숨김
        if (gameManager != null && gameManager.waitingForRoundStart)
            ShowStartRoundPanel();
        else
            HideStartRoundPanel();

        // 버튼 이벤트 연결 (Shoot Self = 1, Shoot Other = 2)
        for (int i = 0; i < actionButtons.Length; i++)
        {
            int actionIndex = i + 1; // 1-based indexing (1: ShootSelf, 2: ShootOther)
            actionButtons[i].onClick.AddListener(() => OnActionSelected(actionIndex));
        }
        
        // 시작 버튼 이벤트 연결
        if (startRoundButton != null)
        {
            startRoundButton.onClick.AddListener(OnStartRoundClicked);
        }
    }

    void Update()
    {
        // 게임 종료 상태면 시작 버튼 패널 표시
        if (gameManager.isGameOver)
        {
            ShowStartRoundPanel();
            HideActionPanel();
            return;
        }
        
        // 라운드 시작 대기 중이면 시작 버튼 패널 표시
        if (gameManager.waitingForRoundStart)
        {
            ShowStartRoundPanel();
            HideActionPanel();
            return;
        }
        
        if (gameManager.turn == PlayerType.Red && gameManager.play)
        {
            HideStartRoundPanel();
            ShowActionPanel();
        }
        else if (gameManager.turn == PlayerType.Blue)
        {
            HideStartRoundPanel();
            HideActionPanel();
        }
        else
        {
            HideStartRoundPanel();
            HideActionPanel();
        }
    }

    void ShowActionPanel()
    {
        actionPanel.SetActive(true);
        UpdateButtonStates();
    }

    void HideActionPanel()
    {
        actionPanel.SetActive(false);
    }

    void UpdateButtonStates()
    {
        // Shoot Self, Shoot Other 버튼은 항상 활성화
        // (아이템은 ItemSlot 직접 클릭으로 사용)
        for (int i = 0; i < actionButtons.Length; i++)
        {
            actionButtons[i].interactable = true;
        }
    }

    void OnActionSelected(int action)
    {
        gameManager.HandlePlayerAction(action);
    }
    
    void OnStartRoundClicked()
    {
        gameManager.StartRound();
    }
    
    void ShowStartRoundPanel()
    {
        if (startRoundPanel != null)
        {
            startRoundPanel.SetActive(true);
        }
    }
    
    void HideStartRoundPanel()
    {
        if (startRoundPanel != null)
        {
            startRoundPanel.SetActive(false);
        }
    }
}
