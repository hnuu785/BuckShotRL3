using System.Collections.Generic;
using UnityEngine;

public class RoundManager : MonoBehaviour
{
    private Stack<string> rounds = new Stack<string>();
    private int totalReal;
    private int totalEmpty;
    private int knowledge = 2; // -1=알 수 없음, 0=빈 총알, 1=실탄, 2=미확인

    // 프로퍼티로 외부 접근 허용
    public Stack<string> Rounds => rounds;
    public int TotalReal => totalReal;
    public int TotalEmpty => totalEmpty;
    public int Knowledge 
    { 
        get => knowledge; 
        set => knowledge = value; 
    }

    // 새 라운드 생성 (총알만 생성, 아이템 추가는 GameManager에서 처리)
    public void GenerateNewRound()
    {
        if (rounds.Count != 0)
        {
            return;
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

        // 다음 총알 정보 초기화 (알 수 없음)
        knowledge = 2;
    }

    // 라운드 클리어
    public void ClearRounds()
    {
        rounds.Clear();
        totalReal = 0;
        totalEmpty = 0;
        knowledge = 2;
    }

    // 다음 총알 확인 (Peek)
    public string PeekRound()
    {
        if (rounds.Count == 0)
        {
            return null;
        }
        return rounds.Peek();
    }

    // 총알 발사 (Pop)
    public string PopRound()
    {
        if (rounds.Count == 0)
        {
            return null;
        }
        
        string round = rounds.Pop();
        
        // 총알 타입에 따라 카운트 감소
        if (round == "real")
        {
            totalReal--;
        }
        else if (round == "empty")
        {
            totalEmpty--;
        }
        
        return round;
    }

    // 총알 개수 반환
    public int GetRoundCount()
    {
        return rounds.Count;
    }

    // 실탄 개수 감소 (수동 조작이 필요한 경우)
    public void DecrementReal()
    {
        if (totalReal > 0)
        {
            totalReal--;
        }
    }

    // 빈 총알 개수 감소 (수동 조작이 필요한 경우)
    public void DecrementEmpty()
    {
        if (totalEmpty > 0)
        {
            totalEmpty--;
        }
    }

    // 라운드가 비어있는지 확인
    public bool IsEmpty()
    {
        return rounds.Count == 0;
    }

    // 다음 총알이 실탄인지 확인
    public bool IsNextRoundReal()
    {
        if (rounds.Count == 0)
        {
            return false;
        }
        return rounds.Peek() == "real";
    }

    // 다음 총알이 빈 총알인지 확인
    public bool IsNextRoundEmpty()
    {
        if (rounds.Count == 0)
        {
            return false;
        }
        return rounds.Peek() == "empty";
    }
}
