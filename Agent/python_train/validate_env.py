"""
게임 환경 검증 스크립트
상태 벡터 차원, 보상 시스템, 게임 로직 등을 검증합니다.
"""
import numpy as np
from game_env import GameEnvironment, ActionType, Player, RoundType

def validate_state_dimension():
    """상태 벡터가 20차원인지 확인"""
    print("=" * 60)
    print("1. 상태 벡터 차원 검증")
    print("=" * 60)
    
    env = GameEnvironment(max_hp=4)
    state = env.get_state()
    
    expected_dim = 20
    actual_dim = len(state)
    
    print(f"예상 차원: {expected_dim}")
    print(f"실제 차원: {actual_dim}")
    
    if actual_dim == expected_dim:
        print("✓ 상태 벡터 차원이 올바릅니다!")
    else:
        print(f"✗ 상태 벡터 차원이 잘못되었습니다! (예상: {expected_dim}, 실제: {actual_dim})")
        return False
    
    # 각 차원 설명
    print("\n상태 벡터 구성:")
    print(f"  1. 턴 정보: 1차원 (현재: {state[0]})")
    print(f"  2. 총알 정보: 3차원 (총: {state[1]}, 실탄: {state[2]}, 빈 총알: {state[3]})")
    print(f"  3. 생명력: 2차원 (Red: {state[4]}, Blue: {state[5]})")
    print(f"  4. Red 아이템: 5차원 (Drink: {state[6]}, MagGlass: {state[7]}, Cigar: {state[8]}, Knife: {state[9]}, Handcuffs: {state[10]})")
    print(f"  5. Blue 아이템: 5차원 (Drink: {state[11]}, MagGlass: {state[12]}, Cigar: {state[13]}, Knife: {state[14]}, Handcuffs: {state[15]})")
    print(f"  6. 총 상태: 2차원 (데미지: {state[16]}, 총알 정보: {state[17]})")
    print(f"  7. 수갑 상태: 2차원 (Blue: {state[18]}, Red: {state[19]})")
    
    return True

def validate_action_indices():
    """액션 인덱스가 올바른지 확인"""
    print("\n" + "=" * 60)
    print("2. 액션 인덱스 검증")
    print("=" * 60)
    
    expected_actions = {
        0: "ShootSelf",
        1: "ShootOther",
        2: "Drink",
        3: "MagGlass",
        4: "Cigar",
        5: "Knife",
        6: "Handcuffs"
    }
    
    all_correct = True
    for idx, name in expected_actions.items():
        actual_name = ActionType(idx).name
        if actual_name == name:
            print(f"✓ 액션 {idx}: {name}")
        else:
            print(f"✗ 액션 {idx}: 예상 {name}, 실제 {actual_name}")
            all_correct = False
    
    return all_correct

def validate_reward_system():
    """보상 시스템 검증"""
    print("\n" + "=" * 60)
    print("3. 보상 시스템 검증")
    print("=" * 60)
    
    env = GameEnvironment(max_hp=4)
    issues = []
    
    # 초기 상태
    state = env.get_state()
    print(f"초기 상태: Red HP={env.red_lives}, Blue HP={env.blue_lives}")
    print(f"현재 턴: {'Red' if env.current_turn == Player.RED else 'Blue'}")
    
    # 테스트 1: 상대에게 실탄 쏘기
    print("\n테스트 1: 상대에게 실탄 쏘기")
    env.reset()
    env.current_turn = Player.RED
    # 실탄이 나오도록 조작 (테스트용)
    if len(env.rounds) > 0:
        # 첫 번째 총알이 실탄인지 확인
        first_bullet = env.rounds[0]
        if first_bullet == RoundType.LIVE:
            state, reward, done, _ = env.step(ActionType.ShootOther)
            print(f"  보상: {reward:.2f} (예상: 10.0 이상)")
            if reward < 10.0:
                issues.append("상대에게 실탄 쏘기 보상이 너무 낮습니다")
        else:
            print("  (첫 번째 총알이 빈 총알이어서 테스트 스킵)")
    
    # 테스트 2: 자신에게 빈 총알 쏘기
    print("\n테스트 2: 자신에게 빈 총알 쏘기")
    env.reset()
    env.current_turn = Player.RED
    # 빈 총알이 나오도록 조작 (테스트용)
    if len(env.rounds) > 0:
        first_bullet = env.rounds[0]
        if first_bullet == RoundType.BLANK:
            state, reward, done, _ = env.step(ActionType.ShootSelf)
            print(f"  보상: {reward:.2f} (예상: 15.0)")
            if abs(reward - 15.0) > 0.1:
                issues.append(f"자신에게 빈 총알 쏘기 보상이 잘못되었습니다 (예상: 15.0, 실제: {reward:.2f})")
        else:
            print("  (첫 번째 총알이 실탄이어서 테스트 스킵)")
    
    # 테스트 3: 게임 종료 보상
    print("\n테스트 3: 게임 종료 보상")
    env.reset()
    env.current_turn = Player.RED
    env.blue_lives = 1  # Blue를 1 HP로 설정
    # 실탄으로 Blue를 죽이기
    if len(env.rounds) > 0:
        # 실탄 찾기
        for i, bullet in enumerate(env.rounds):
            if bullet == RoundType.LIVE:
                # 실탄을 맨 앞으로 이동
                env.rounds.insert(0, env.rounds.pop(i))
                break
        state, reward, done, _ = env.step(ActionType.ShootOther)
        print(f"  Red가 Blue를 죽임: 보상={reward:.2f}, done={done}")
        if done and reward < 50.0:
            issues.append("승리 보상이 제대로 주어지지 않습니다")
    
    if issues:
        print("\n⚠ 발견된 문제:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ 보상 시스템이 올바르게 작동합니다!")
        return True

def validate_game_logic():
    """게임 로직 검증"""
    print("\n" + "=" * 60)
    print("4. 게임 로직 검증")
    print("=" * 60)
    
    env = GameEnvironment(max_hp=4)
    issues = []
    
    # 테스트 1: Magnifying Glass는 턴을 끝내지 않음
    print("\n테스트 1: Magnifying Glass 턴 유지")
    env.reset()
    current_turn_before = env.current_turn
    if env.red_items['MagGlass'] > 0 and env.current_turn == Player.RED:
        state, reward, done, _ = env.step(ActionType.MagGlass)
        if env.current_turn != current_turn_before:
            issues.append("Magnifying Glass 사용 후 턴이 변경되었습니다")
        else:
            print("  ✓ Magnifying Glass 사용 후 턴이 유지됩니다")
    else:
        print("  (테스트 스킵: 아이템이 없거나 Red 턴이 아님)")
    
    # 테스트 2: 자신에게 빈 총알 쏘면 턴 유지
    print("\n테스트 2: 자신에게 빈 총알 쏘기 턴 유지")
    env.reset()
    env.current_turn = Player.RED
    if len(env.rounds) > 0:
        # 빈 총알 찾기
        for i, bullet in enumerate(env.rounds):
            if bullet == RoundType.BLANK:
                env.rounds.insert(0, env.rounds.pop(i))
                break
        current_turn_before = env.current_turn
        state, reward, done, _ = env.step(ActionType.ShootSelf)
        if env.current_turn != current_turn_before:
            issues.append("자신에게 빈 총알 쏘기 후 턴이 변경되었습니다")
        else:
            print("  ✓ 자신에게 빈 총알 쏘기 후 턴이 유지됩니다")
    
    # 테스트 3: 새 라운드 시작 시 아이템 재배분
    print("\n테스트 3: 새 라운드 시작 시 아이템 재배분")
    env.reset()
    initial_red_items = sum(env.red_items.values())
    initial_blue_items = sum(env.blue_items.values())
    
    # 모든 총알 소모
    while len(env.rounds) > 0:
        env.step(ActionType.Drink if env.current_turn == Player.RED and env.red_items['Drink'] > 0 else ActionType.ShootOther)
    
    # 새 라운드 시작 확인
    new_red_items = sum(env.red_items.values())
    new_blue_items = sum(env.blue_items.values())
    
    if new_red_items == 0 or new_blue_items == 0:
        issues.append("새 라운드 시작 시 아이템이 재배분되지 않았습니다")
    else:
        print(f"  ✓ 새 라운드 시작: Red 아이템 {initial_red_items}개 → {new_red_items}개, Blue 아이템 {initial_blue_items}개 → {new_blue_items}개")
    
    if issues:
        print("\n⚠ 발견된 문제:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ 게임 로직이 올바르게 작동합니다!")
        return True

def main():
    """모든 검증 실행"""
    print("\n" + "=" * 60)
    print("게임 환경 검증 시작")
    print("=" * 60)
    
    results = []
    
    results.append(("상태 벡터 차원", validate_state_dimension()))
    results.append(("액션 인덱스", validate_action_indices()))
    results.append(("보상 시스템", validate_reward_system()))
    results.append(("게임 로직", validate_game_logic()))
    
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 모든 검증을 통과했습니다!")
    else:
        print("⚠ 일부 검증에서 문제가 발견되었습니다.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()
