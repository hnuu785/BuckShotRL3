"""
게임 환경 테스트 스크립트
"""
import numpy as np
from game_env import GameEnvironment, ActionType, Player

def test_game_environment():
    """게임 환경 기본 테스트"""
    print("=" * 50)
    print("게임 환경 테스트 시작")
    print("=" * 50)
    
    env = GameEnvironment(max_hp=4)
    
    # 초기 상태 확인
    state = env.get_state()
    print(f"\n초기 상태 벡터 크기: {len(state)} (예상: 20)")
    print(f"초기 상태: {state}")
    print(f"Red HP: {env.red_lives}, Blue HP: {env.blue_lives}")
    print(f"현재 턴: {'Red' if env.current_turn == Player.RED else 'Blue'}")
    print(f"총알 개수: {len(env.rounds)}")
    print(f"Red 아이템: {env.red_items}")
    print(f"Blue 아이템: {env.blue_items}")
    
    # 몇 가지 액션 테스트
    print("\n" + "=" * 50)
    print("액션 테스트")
    print("=" * 50)
    
    for i in range(10):
        current_turn = 'Red' if env.current_turn == Player.RED else 'Blue'
        print(f"\n턴 {i+1}: {current_turn} 플레이어")
        
        # 랜덤 액션 선택
        action = np.random.randint(0, 7)
        action_name = ActionType(action).name
        
        print(f"  액션: {action_name} ({action})")
        
        state, reward, done, info = env.step(action)
        
        print(f"  보상: {reward:.2f}")
        print(f"  Red HP: {env.red_lives}, Blue HP: {env.blue_lives}")
        print(f"  남은 총알: {len(env.rounds)}")
        
        if done:
            print(f"\n게임 종료!")
            if env.red_lives <= 0:
                print("Blue 승리!")
            elif env.blue_lives <= 0:
                print("Red 승리!")
            break
        
        # 새 라운드 시작 확인
        if len(env.rounds) == 0:
            print("  새 라운드 시작!")
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)

def test_specific_actions():
    """특정 액션 테스트"""
    print("\n" + "=" * 50)
    print("특정 액션 테스트")
    print("=" * 50)
    
    env = GameEnvironment(max_hp=4)
    state = env.get_state()
    
    # Magnifying Glass 테스트 (턴을 끝내지 않아야 함)
    print("\n1. Magnifying Glass 테스트")
    print(f"   현재 턴: {'Red' if env.current_turn == Player.RED else 'Blue'}")
    state, reward, done, _ = env.step(ActionType.MagGlass)
    print(f"   보상: {reward:.2f}")
    print(f"   다음 총알 정보: {env.bullet_knowledge} (-1: 알 수 없음, 0: 빈 총알, 1: 실탄)")
    print(f"   턴 변경 여부: {'변경됨' if env.current_turn != Player.RED else '유지됨'}")
    
    # Cigar 테스트
    print("\n2. Cigar 테스트")
    print(f"   현재 HP: Red={env.red_lives}, Blue={env.blue_lives}")
    if env.current_turn == Player.RED and env.red_items['Cigar'] > 0:
        state, reward, done, _ = env.step(ActionType.Cigar)
        print(f"   보상: {reward:.2f}")
        print(f"   HP 변경: Red={env.red_lives}")
    
    # Handcuffs 테스트
    print("\n3. Handcuffs 테스트")
    if env.current_turn == Player.RED and env.red_items['Handcuffs'] > 0:
        state, reward, done, _ = env.step(ActionType.Handcuffs)
        print(f"   보상: {reward:.2f}")
        print(f"   Blue 수갑 상태: {env.blue_handcuffed}")
    
    print("\n테스트 완료")

if __name__ == "__main__":
    test_game_environment()
    test_specific_actions()
