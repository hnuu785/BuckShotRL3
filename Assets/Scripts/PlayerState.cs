using UnityEngine;

/// <summary>
/// 플레이어의 상태를 관리하는 클래스
/// 체력, 수갑 상태 등의 플레이어 데이터를 구조화하여 관리합니다.
/// </summary>
public class PlayerState
{
    private int lives;
    private bool isHandcuffed;
    private int maxLives;

    /// <summary>
    /// 현재 생명력
    /// </summary>
    public int Lives
    {
        get => lives;
        set => lives = Mathf.Clamp(value, 0, maxLives);
    }

    /// <summary>
    /// 수갑에 걸려있는지 여부
    /// </summary>
    public bool IsHandcuffed
    {
        get => isHandcuffed;
        set => isHandcuffed = value;
    }

    /// <summary>
    /// 최대 생명력
    /// </summary>
    public int MaxLives
    {
        get => maxLives;
        private set => maxLives = value;
    }

    /// <summary>
    /// 생성자
    /// </summary>
    /// <param name="initialLives">초기 생명력</param>
    /// <param name="maxLives">최대 생명력</param>
    public PlayerState(int initialLives = 4, int maxLives = 4)
    {
        this.maxLives = maxLives;
        this.lives = initialLives;
        this.isHandcuffed = false;
    }

    /// <summary>
    /// 생명력을 감소시킵니다.
    /// </summary>
    /// <param name="damage">감소시킬 생명력</param>
    public void TakeDamage(int damage)
    {
        Lives -= damage;
    }

    /// <summary>
    /// 생명력을 회복시킵니다.
    /// </summary>
    /// <param name="amount">회복할 생명력</param>
    public void Heal(int amount)
    {
        Lives += amount;
    }

    /// <summary>
    /// 생명력이 0 이하인지 확인합니다.
    /// </summary>
    /// <returns>생명력이 0 이하면 true</returns>
    public bool IsDead()
    {
        return lives <= 0;
    }

    /// <summary>
    /// 상태를 초기화합니다.
    /// </summary>
    /// <param name="initialLives">초기 생명력 (기본값: 최대 생명력)</param>
    public void Reset(int? initialLives = null)
    {
        lives = initialLives ?? maxLives;
        isHandcuffed = false;
    }

    /// <summary>
    /// 상태를 복사합니다.
    /// </summary>
    /// <returns>현재 상태의 복사본</returns>
    public PlayerState Clone()
    {
        PlayerState clone = new PlayerState(lives, maxLives);
        clone.isHandcuffed = isHandcuffed;
        return clone;
    }
}
