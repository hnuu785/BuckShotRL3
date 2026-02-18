/// <summary>
/// 게임에서 사용되는 공통 타입과 상수 정의
/// </summary>

public enum PlayerType
{
    Red,
    Blue
}

public enum ActionType
{
    ShootSelf = 1,
    ShootOther = 2,
    Drink = 3,
    MagGlass = 4,
    Cigar = 5,
    Knife = 6,
    Handcuffs = 7
}

/// <summary>
/// 아이템 코드 상수 클래스
/// </summary>
public static class ItemCode
{
    public const string EnergyDrink = "ED";
    public const string MagnifyingGlass = "MG";
    public const string Cigar = "C";
    public const string Knife = "K";
    public const string Handcuffs = "HC";
}
