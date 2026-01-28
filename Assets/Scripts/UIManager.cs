using UnityEngine;
using TMPro;

public class UIManager : MonoBehaviour
{
    [Header("Debug Information")]
    public TextMeshProUGUI bullets;

    [Header("Health (Canvas)")]
    public TextMeshProUGUI healthRedText;   // 왼쪽 상단 RED 체력
    public TextMeshProUGUI healthBlueText; // 오른쪽 상단 BLUE 체력

    [Header("Start Screen")]
    public GameObject startPanel;

    private GameManager gameManager;
    private RoundManager roundManager;

    private void Awake()
    {
        // GameManager 찾기 (같은 GameObject 또는 씬에서)
        gameManager = GetComponent<GameManager>();
        if (gameManager == null)
        {
            gameManager = FindFirstObjectByType<GameManager>();
        }
    }

    private void Start()
    {
        // Start에서 RoundManager 초기화 (GameManager의 Awake가 완료된 후)
        if (gameManager != null)
        {
            roundManager = gameManager.GetComponent<RoundManager>();
        }
        
    }

    // GameManager에서 직접 설정할 수 있는 메서드
    public void Initialize(GameManager gm)
    {
        gameManager = gm;
        if (gameManager != null)
        {
            roundManager = gameManager.GetComponent<RoundManager>();
            if (roundManager == null)
            {
                Debug.LogWarning("UIManager: RoundManager를 찾을 수 없습니다.");
            }
        }
        else
        {
            Debug.LogError("UIManager: GameManager가 null입니다.");
        }
    }

    public void UpdateUI()
    {
        if (gameManager == null) return;

        // 총알 정보 업데이트
        UpdateBulletsUI();
        
        // 체력 정보 업데이트
        UpdateHealthUI();
    }
    
    public void UpdateHealthUI()
    {
        if (gameManager == null) return;

        if (healthRedText != null)
            healthRedText.text = $"RED: {gameManager.RedPlayerState.Lives}";

        if (healthBlueText != null)
            healthBlueText.text = $"BLUE: {gameManager.BluePlayerState.Lives}";
    }

    public void UpdateBulletsUI()
    {
        if (bullets == null || roundManager == null) return;
        
        int total = roundManager.GetRoundCount();
        bullets.text = $"Bullets: {total} (Real: {roundManager.TotalReal}, Fake: {roundManager.TotalEmpty})";
    }

    /// <summary>
    /// Start 버튼 클릭 시 호출. StartPanel을 끄고 게임 UI를 보이게 합니다.
    /// Inspector에서 Start 버튼의 OnClick 이벤트에 연결하세요.
    /// </summary>
    public void StartGameUI()
    {
        if (startPanel != null)
        {
            startPanel.SetActive(false);
        }
        // 스타트 버튼으로 게임/라운드 시작 (GameManager 대기 해제)
        if (gameManager != null)
            gameManager.StartRound();
    }
}
