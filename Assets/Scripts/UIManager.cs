using UnityEngine;
using TMPro;

public class UIManager : MonoBehaviour
{
    [Header("Debug Information")]
    public TextMeshProUGUI bullets;

    [Header("Start Screen")]
    public GameObject startPanel;

    private GameManager gameManager;
    private RoundManager roundManager;
    
    // HealthRed와 HealthBlue TextMesh 참조
    private TextMesh healthRedText;
    private TextMesh healthBlueText;

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
        
        // HealthRed와 HealthBlue TextMesh 찾기
        FindHealthTextMeshes();
    }
    
    private void FindHealthTextMeshes()
    {
        // HealthRed GameObject 찾기
        GameObject healthRedObj = GameObject.Find("HealthRed");
        if (healthRedObj != null)
        {
            healthRedText = healthRedObj.GetComponent<TextMesh>();
            if (healthRedText == null)
            {
                Debug.LogWarning("UIManager: HealthRed GameObject에 TextMesh 컴포넌트가 없습니다.");
            }
        }
        else
        {
            Debug.LogWarning("UIManager: HealthRed GameObject를 찾을 수 없습니다.");
        }
        
        // HealthBlue GameObject 찾기
        GameObject healthBlueObj = GameObject.Find("HealthBlue");
        if (healthBlueObj != null)
        {
            healthBlueText = healthBlueObj.GetComponent<TextMesh>();
            if (healthBlueText == null)
            {
                Debug.LogWarning("UIManager: HealthBlue GameObject에 TextMesh 컴포넌트가 없습니다.");
            }
        }
        else
        {
            Debug.LogWarning("UIManager: HealthBlue GameObject를 찾을 수 없습니다.");
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
        
        // HealthRed와 HealthBlue TextMesh 찾기
        FindHealthTextMeshes();
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
        
        // HealthRed와 HealthBlue가 아직 찾지 못했다면 다시 시도
        if (healthRedText == null || healthBlueText == null)
        {
            FindHealthTextMeshes();
        }
        
        // HealthRed 업데이트
        if (healthRedText != null)
        {
            healthRedText.text = gameManager.RedPlayerState.Lives.ToString();
        }
        
        // HealthBlue 업데이트
        if (healthBlueText != null)
        {
            healthBlueText.text = gameManager.BluePlayerState.Lives.ToString();
        }
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
