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

    // 아이템을 플레이어에게 추가
    public void AddItems(List<GameObject> itemsList, int itemsToGive, string player)
    {
        GameObject[] board = player == "r" ? redBoard : blueBoard;

        for (int i = 0; i < itemsToGive; i++)
        {
            if (itemsList.Count == 8)
            {
                return;
            }
            int item = UnityEngine.Random.Range(0, 5);

            Debug.Log("New Items");
            for (int j = 0; j < board.Length; j++)
            {
                if (board[j] != null && board[j].GetComponent<ItemSlot>().takenBy == null)
                {
                    Debug.Log(items[item]);
                    GameObject newItem = Instantiate(items[item], GetSlot(item, board[j]).position, items[item].transform.rotation);
                    ItemSlot slot = board[j].GetComponent<ItemSlot>();
                    slot.takenBy = newItem;
                    slot.takenByName = GetItemName(item);
                    break;
                }
            }
        }
    }

    // 아이템 인덱스에 따른 이름 반환
    public string GetItemName(int item)
    {
        switch (item)
        {
            case 0:
                return "ED";
            case 1:
                return "MG";
            case 2:
                return "C";
            case 3:
                return "K";
            case 4:
                return "HC";
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
