using UnityEngine;
using TMPro;

public class UIManager : MonoBehaviour
{
    [Header("Debug Information")]
    public TextMeshProUGUI action;
    public TextMeshProUGUI nextBullet;
    public TextMeshProUGUI bullets;

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
        UpdateNextBulletUI();
    }

    public void UpdateBulletsUI()
    {
        if (bullets == null || roundManager == null) return;
        
        int total = roundManager.GetRoundCount();
        bullets.text = $"Bullets: {total} (Real: {roundManager.TotalReal}, Fake: {roundManager.TotalEmpty})";
    }

    public void UpdateNextBulletUI()
    {
        if (nextBullet == null || roundManager == null) return;
        
        // 디버그 용도: 실제 총알 정보 표시
        if (roundManager.IsEmpty())
        {
            nextBullet.text = "Next Bullet: None";
        }
        else
        {
            nextBullet.text = $"Next Bullet: {roundManager.PeekRound()}";
        }
    }

    public void ShowMove(int numAction, PlayerType? player)
    {
        if (action == null) return;

        string[] actionNames = { "", "Shoot Self", "Shoot Other", "Drink", "Mag. Glass", "Cigar", "Knife", "Handcuffs" };
        string playerName = player == PlayerType.Red ? "Red" : "Blue";
        
        action.text = $"{playerName}: {(numAction >= 1 && numAction < actionNames.Length ? actionNames[numAction] : "")}";
        UpdateNextBulletUI();
    }
}
