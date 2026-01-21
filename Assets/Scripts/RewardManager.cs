using UnityEngine;

public class RewardManager : MonoBehaviour
{
    // 보상 상수 정의
    private const float WIN_REWARD = 50.0f;
    private const float LOSS_PENALTY = -50.0f;
    private const float INVALID_ACTION_PENALTY = -50.0f;
    
    // 사격 보상
    private const float HIT_OPPONENT_MULTIPLIER = 10.0f;
    private const float HIT_SELF_MULTIPLIER = -15.0f;
    private const float MISS_OPPONENT_PENALTY = -5.0f;
    private const float MISS_SELF_REWARD = 15.0f;
    
    // 아이템 보상
    private const float BEER_REAL_REWARD = 5.0f;
    private const float BEER_EMPTY_REWARD = 1.0f;
    private const float CIGAR_HEAL_REWARD = 5.0f;
    private const float CIGAR_WASTE_PENALTY = -2.0f;
    private const float HANDCUFFS_SUCCESS_REWARD = 7.0f;
    private const float HANDCUFFS_FAIL_PENALTY = -10.0f;
    private const float KNIFE_HIT_REWARD = 5.0f;
    private const float KNIFE_MISS_PENALTY = -5.0f;
    private const float MAGGLASS_REWARD = 3.0f;

    /// <summary>
    /// 사격 보상 계산
    /// </summary>
    /// <param name="isReal">실탄인지 여부</param>
    /// <param name="isSelf">자신에게 쏘는지 여부</param>
    /// <param name="damage">데미지</param>
    /// <param name="knifeUsed">칼 사용 여부</param>
    /// <param name="playerLives">플레이어 생명력 (자신에게 쏠 때)</param>
    /// <param name="opponentLives">상대 생명력 (상대에게 쏠 때)</param>
    /// <returns>보상 값</returns>
    public float CalculateShootReward(bool isReal, bool isSelf, int damage, bool knifeUsed, int playerLives, int opponentLives)
    {
        float reward = 0f;

        if (isReal && isSelf)
        {
            // 나에게 실탄 적중: -(데미지 × 15)
            reward += damage * HIT_SELF_MULTIPLIER;
            
            // 칼 사용 후 적중: +5.0
            if (knifeUsed)
            {
                reward += KNIFE_HIT_REWARD;
            }
            
            // 자신의 체력이 0 이하가 되었을 때 패배 보상
            if (playerLives <= 0)
            {
                reward += LOSS_PENALTY;
            }
        }
        else if (isReal && !isSelf)
        {
            // 상대에게 실탄 적중: +(데미지 × 10)
            reward += damage * HIT_OPPONENT_MULTIPLIER;
            
            // 칼 사용 후 적중: +5.0
            if (knifeUsed)
            {
                reward += KNIFE_HIT_REWARD;
            }
            
            // 상대방 체력이 0 이하가 되었을 때 승리 보상
            if (opponentLives <= 0)
            {
                reward += WIN_REWARD;
            }
        }
        else if (!isReal)
        {
            // 빈 총알
            if (knifeUsed && !isSelf)
            {
                // 칼 사용 후 빗나감: -5.0 (상대에게 쏠 때만)
                reward += KNIFE_MISS_PENALTY;
            }
            
            if (isSelf)
            {
                // 나에게 빈 총알: +15.0 (턴 유지)
                reward += MISS_SELF_REWARD;
            }
            else
            {
                // 상대에게 빈 총알: -5.0 (턴 넘김)
                reward += MISS_OPPONENT_PENALTY;
            }
        }

        return reward;
    }

    /// <summary>
    /// Energy Drink (Beer) 보상 계산
    /// </summary>
    /// <param name="isReal">배출된 총알이 실탄인지 여부</param>
    /// <returns>보상 값</returns>
    public float CalculateBeerReward(bool isReal)
    {
        if (isReal)
        {
            return BEER_REAL_REWARD; // +5.0
        }
        else
        {
            return BEER_EMPTY_REWARD; // +1.0
        }
    }

    /// <summary>
    /// Magnifying Glass 보상 계산
    /// </summary>
    /// <param name="roundCount">남은 총알 개수</param>
    /// <param name="totalEmpty">남은 빈 총알 개수</param>
    /// <param name="totalReal">남은 실탄 개수</param>
    /// <param name="knowledge">다음 총알 정보 (0=빈 총알, 1=실탄, 2=미확인)</param>
    /// <returns>보상 값</returns>
    public float CalculateMagGlassReward(int roundCount, int totalEmpty, int totalReal, int knowledge)
    {
        // 쓸모없는 상황: 총알이 1개 남았거나, 빈 총알/실탄이 0개이거나, 이미 확인된 경우
        if (roundCount == 1 || totalEmpty == 0 || totalReal == 0 || knowledge != 2)
        {
            return 0f; // 보상 없음
        }
        else
        {
            return MAGGLASS_REWARD; // +3.0
        }
    }

    /// <summary>
    /// Cigar 보상 계산
    /// </summary>
    /// <param name="currentLives">현재 생명력</param>
    /// <param name="maxLives">최대 생명력</param>
    /// <returns>보상 값</returns>
    public float CalculateCigarReward(int currentLives, int maxLives)
    {
        if (currentLives >= maxLives)
        {
            return CIGAR_WASTE_PENALTY; // -2.0 (아이템 낭비)
        }
        else
        {
            return CIGAR_HEAL_REWARD; // +5.0 (유효한 회복)
        }
    }

    /// <summary>
    /// Handcuffs 보상 계산
    /// </summary>
    /// <param name="opponentAlreadyCuffed">상대가 이미 수갑에 걸려있는지 여부</param>
    /// <returns>보상 값</returns>
    public float CalculateHandcuffsReward(bool opponentAlreadyCuffed)
    {
        if (opponentAlreadyCuffed)
        {
            return HANDCUFFS_FAIL_PENALTY; // -10.0 (무효 행동)
        }
        else
        {
            return HANDCUFFS_SUCCESS_REWARD; // +7.0 (성공)
        }
    }

    /// <summary>
    /// 무효 행동 페널티 계산
    /// </summary>
    /// <returns>페널티 값 (-50.0)</returns>
    public float CalculateInvalidActionPenalty()
    {
        return INVALID_ACTION_PENALTY;
    }

    /// <summary>
    /// 승리 보상
    /// </summary>
    /// <returns>보상 값 (+50.0)</returns>
    public float GetWinReward()
    {
        return WIN_REWARD;
    }

    /// <summary>
    /// 패배 페널티
    /// </summary>
    /// <returns>페널티 값 (-50.0)</returns>
    public float GetLossPenalty()
    {
        return LOSS_PENALTY;
    }
}
