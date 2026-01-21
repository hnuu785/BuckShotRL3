using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class PlayerController : MonoBehaviour
{
    public GameManager gameManager;
    public GameObject actionPanel; // 액션 선택 패널
    public Button[] actionButtons; // 액션 버튼들 (7개: shoot self, shoot other, drink, mag glass, cigar, knife, handcuffs)
    public TextMeshProUGUI turnIndicator;
    public Button startRoundButton; // 라운드 시작 버튼
    public GameObject startRoundPanel; // 라운드 시작 패널

    void Start()
    {
        gameManager = FindObjectOfType<GameManager>();
        HideActionPanel();
        HideStartRoundPanel();

        // 버튼 이벤트 연결
        for (int i = 0; i < actionButtons.Length; i++)
        {
            int actionIndex = i + 1; // 1-based indexing
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
        // 라운드 시작 대기 중이면 시작 버튼 패널 표시
        if (gameManager.waitingForRoundStart)
        {
            ShowStartRoundPanel();
            HideActionPanel();
            turnIndicator.text = "Press Start to Begin Round";
            return;
        }
        
        if (gameManager.turn == "r" && gameManager.play)
        {
            HideStartRoundPanel();
            ShowActionPanel();
            turnIndicator.text = "Your Turn (Red Player)";
        }
        else if (gameManager.turn == "b")
        {
            HideStartRoundPanel();
            HideActionPanel();
            turnIndicator.text = "AI Turn (Blue Player)";
        }
        else
        {
            HideStartRoundPanel();
            HideActionPanel();
            turnIndicator.text = "Waiting...";
        }
    }

    void ShowActionPanel()
    {
        actionPanel.SetActive(true);
        // 버튼 활성화/비활성화 로직 (아이템 보유 여부에 따라)
        UpdateButtonStates();
    }

    void HideActionPanel()
    {
        actionPanel.SetActive(false);
    }

    void UpdateButtonStates()
    {
        if (actionButtons.Length < 7) return;

        // Shoot Self, Shoot Other는 항상 활성화
        actionButtons[0].interactable = true; // Shoot Self
        actionButtons[1].interactable = true; // Shoot Other

        // 아이템 버튼들은 보유 여부에 따라 활성화
        actionButtons[2].interactable = gameManager.getItems("r", "ED") > 0; // Drink
        actionButtons[3].interactable = gameManager.getItems("r", "MG") > 0; // Mag Glass
        actionButtons[4].interactable = gameManager.getItems("r", "C") > 0;  // Cigar
        actionButtons[5].interactable = gameManager.getItems("r", "K") > 0;  // Knife
        actionButtons[6].interactable = gameManager.getItems("r", "HC") > 0; // Handcuffs
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
