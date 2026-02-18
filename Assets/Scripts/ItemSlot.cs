using UnityEngine;
using System.Collections.Generic;

public class ItemSlot : MonoBehaviour
{
    public GameObject takenBy;
    public string takenByName;
    
    [Header("Settings")]
    [Tooltip("이 슬롯의 소유자 (r = Red 플레이어, b = Blue AI)")]
    public string owner = "r";
    
    private GameManager gameManager;
    
    // 아이템 코드를 ActionType으로 변환하는 딕셔너리
    private static readonly Dictionary<string, ActionType> ItemCodeToAction = new Dictionary<string, ActionType>
    {
        { ItemCode.EnergyDrink, ActionType.Drink },
        { ItemCode.MagnifyingGlass, ActionType.MagGlass },
        { ItemCode.Cigar, ActionType.Cigar },
        { ItemCode.Knife, ActionType.Knife },
        { ItemCode.Handcuffs, ActionType.Handcuffs }
    };
    
    void Start()
    {
        gameManager = FindFirstObjectByType<GameManager>();
    }
    
    void OnMouseDown()
    {
        UseItem();
    }
    
    /// <summary>
    /// 슬롯의 아이템을 사용합니다.
    /// </summary>
    public void UseItem()
    {
        // GameManager가 없으면 찾기
        if (gameManager == null)
        {
            gameManager = FindFirstObjectByType<GameManager>();
            if (gameManager == null)
            {
                Debug.LogWarning("GameManager not found!");
                return;
            }
        }
        
        // Red 플레이어의 슬롯만 클릭 가능
        if (owner != "r")
        {
            Debug.Log("Blue 플레이어의 아이템은 직접 사용할 수 없습니다.");
            return;
        }
        
        // 아이템이 없으면 무시
        if (takenBy == null || string.IsNullOrEmpty(takenByName))
        {
            Debug.Log("이 슬롯에 아이템이 없습니다.");
            return;
        }
        
        // 아이템 코드를 ActionType으로 변환
        if (!ItemCodeToAction.TryGetValue(takenByName, out ActionType action))
        {
            Debug.LogWarning($"알 수 없는 아이템: {takenByName}");
            return;
        }
        
        // GameManager를 통해 아이템 사용
        int actionInt = (int)action;
        Debug.Log($"아이템 사용: {takenByName} -> ActionType: {action} ({actionInt})");
        gameManager.HandlePlayerAction(actionInt);
    }
}
