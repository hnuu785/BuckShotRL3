using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BluePlayer : MonoBehaviour
{
    public GameManager gm;

    private void Awake()
    {
        gm = Object.FindFirstObjectByType<GameManager>();
    }
    void Update()
    {
        if(gm.turn == "b" && gm.play)
        {

        }
    }
}
