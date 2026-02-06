using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ItemManager : MonoBehaviour
{
    private GameObject[] redBoard;
    private GameObject[] blueBoard;
    private GameObject[] items;

    // 초기화 메서드
    public void Initialize(GameObject[] redBoard, GameObject[] blueBoard, GameObject[] items)
    {
        this.redBoard = redBoard;
        this.blueBoard = blueBoard;
        this.items = items;
    }

    // 특정 팀의 특정 아이템 개수를 반환
    public int GetItems(string team, string item)
    {
        int count = 0;
        GameObject[] board = team == "r" ? redBoard : blueBoard;

        for (int i = 0; i < board.Length; i++)
        {
            if (board[i] != null && board[i].GetComponent<ItemSlot>().takenByName == item)
            {
                count++;
            }
        }
        return count;
    }

    // 특정 팀의 현재 인벤토리에 있는 총 아이템 개수를 반환
    public int GetTotalItemCount(string team)
    {
        int count = 0;
        GameObject[] board = team == "r" ? redBoard : blueBoard;

        for (int i = 0; i < board.Length; i++)
        {
            if (board[i] != null && board[i].GetComponent<ItemSlot>().takenBy != null)
            {
                count++;
            }
        }
        return count;
    }

    // 아이템을 플레이어에게 추가 (인벤토리 한도 8슬롯 고려)
    public void AddItems(List<GameObject> itemsList, int itemsToGive, string player)
    {
        GameObject[] board = player == "r" ? redBoard : blueBoard;
        const int INVENTORY_LIMIT = 8;

        // 현재 인벤토리에 있는 아이템 개수 확인
        int currentItemCount = GetTotalItemCount(player);
        
        // 추가할 수 있는 최대 아이템 개수 계산
        int availableSlots = INVENTORY_LIMIT - currentItemCount;
        if (availableSlots <= 0)
        {
            Debug.Log($"{player} inventory is full (8/8). Cannot add more items.");
            return;
        }

        // 추가할 아이템 개수를 인벤토리 한도 내로 제한
        int actualItemsToGive = Mathf.Min(itemsToGive, availableSlots);

        for (int i = 0; i < actualItemsToGive; i++)
        {
            // 인벤토리가 가득 찼는지 다시 확인
            if (GetTotalItemCount(player) >= INVENTORY_LIMIT)
            {
                break;
            }

            int item = UnityEngine.Random.Range(0, 5);

            Debug.Log($"Adding new item to {player}");
            for (int j = 0; j < board.Length; j++)
            {
                if (board[j] != null && board[j].GetComponent<ItemSlot>().takenBy == null)
                {
                    Debug.Log(items[item]);
                    Quaternion rotation = items[item].transform.rotation;
                    // Maglifying Glass(인덱스 1)는 BoardBlue에서 스폰 시 Y 180도 회전
                    if (player == "b" && item == 1)
                        rotation = rotation * Quaternion.Euler(0f, 180f, 0f);
                    GameObject newItem = Instantiate(items[item], GetSlot(item, board[j]).position, rotation);
                    ItemSlot slot = board[j].GetComponent<ItemSlot>();
                    slot.takenBy = newItem;
                    slot.takenByName = GetItemName(item);
                    break;
                }
            }
        }

        if (actualItemsToGive < itemsToGive)
        {
            Debug.Log($"{player} inventory limit reached. Added {actualItemsToGive} items instead of {itemsToGive}.");
        }
    }

    // 아이템 인덱스에 따른 이름 반환
    public string GetItemName(int item)
    {
        switch (item)
        {
            case 0:
                return ItemCode.EnergyDrink;
            case 1:
                return ItemCode.MagnifyingGlass;
            case 2:
                return ItemCode.Cigar;
            case 3:
                return ItemCode.Knife;
            case 4:
                return ItemCode.Handcuffs;
            default:
                return "";
        }
    }

    // 아이템 스폰 위치 반환
    public Transform GetSlot(int item, GameObject toSpawnAt)
    {
        string[] spawnNames = {
            "Energy Drink Spawn",
            "Maglifying Glass Spawn",
            "Cigar Spawn",
            "Knife Spawn",
            "Handcuffs Spawn"
        };

        Transform spawnPoint = toSpawnAt.transform.Find(spawnNames[item]);
        if (spawnPoint == null)
        {
            Debug.LogWarning($"Spawn point '{spawnNames[item]}' not found, using slot position");
            return toSpawnAt.transform;  // 슬롯의 기본 위치 사용
        }
        return spawnPoint;
    }
}
