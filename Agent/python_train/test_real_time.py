"""
실시간 턴제 게임: 사용자 vs AI 에이전트
터미널에서 직접 플레이할 수 있는 인터랙티브 게임
"""
import numpy as np
import os
import sys

# 상위 디렉토리를 경로에 추가하여 model, utils를 import할 수 있도록 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Agent
from game_env import GameEnvironment, Player, ActionType, RoundType

def clear_screen():
    """화면 지우기"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_separator():
    """구분선 출력"""
    print("=" * 70)

def display_game_state(env, user_player: Player):
    """게임 상태 표시"""
    clear_screen()
    print_separator()
    print("BUCKSHOT ROULETTE - Real Time Play")
    print_separator()
    
    # 플레이어 정보
    user_name = "YOU" if user_player == Player.RED else "YOU"
    ai_name = "AI" if user_player == Player.BLUE else "AI"
    
    # 현재 턴 표시
    current_turn_name = "YOU" if env.current_turn == user_player else "AI"
    print(f"\n{'>>> YOUR TURN <<<' if env.current_turn == user_player else '>>> AI TURN <<<'}")
    print_separator()
    
    # HP 표시
    if user_player == Player.RED:
        print(f"\n{'YOU (Red)':<20} {'AI (Blue)':<20}")
        print(f"HP: {env.red_lives}/{env.max_hp}{' ' * 10}HP: {env.blue_lives}/{env.max_hp}")
    else:
        print(f"\n{'AI (Red)':<20} {'YOU (Blue)':<20}")
        print(f"HP: {env.red_lives}/{env.max_hp}{' ' * 10}HP: {env.blue_lives}/{env.max_hp}")
    
    # 총알 정보
    total_rounds = len(env.rounds)
    live_rounds = sum(1 for r in env.rounds if r == RoundType.LIVE)
    blank_rounds = sum(1 for r in env.rounds if r == RoundType.BLANK)
    
    print(f"\n총알 정보:")
    print(f"  총 개수: {total_rounds}")
    print(f"  실탄: {live_rounds}개")
    print(f"  빈 총알: {blank_rounds}개")
    
    # 다음 총알 정보 (Magnifying Glass 사용 시)
    if env.bullet_knowledge >= 0:
        bullet_type = "실탄" if env.bullet_knowledge == 1 else "빈 총알"
        print(f"  다음 총알: {bullet_type} (확인됨)")
    else:
        print(f"  다음 총알: 알 수 없음")
    
    # 총 상태
    if env.gun_damage > 1:
        print(f"\n총 상태: 데미지 {env.gun_damage}x (Knife 사용 중)")
    else:
        print(f"\n총 상태: 데미지 1x")
    
    # 수갑 상태
    if user_player == Player.RED:
        if env.red_handcuffed:
            print(f"⚠️  YOU는 수갑에 걸려있습니다!")
        if env.blue_handcuffed:
            print(f"⚠️  AI는 수갑에 걸려있습니다!")
    else:
        if env.blue_handcuffed:
            print(f"⚠️  YOU는 수갑에 걸려있습니다!")
        if env.red_handcuffed:
            print(f"⚠️  AI는 수갑에 걸려있습니다!")
    
    # 아이템 표시
    if env.current_turn == user_player:
        items = env.red_items if user_player == Player.RED else env.blue_items
        print(f"\n보유 아이템:")
        print(f"  Energy Drink (Drink): {items['Drink']}개")
        print(f"  Magnifying Glass (MagGlass): {items['MagGlass']}개")
        print(f"  Cigar: {items['Cigar']}개")
        print(f"  Knife: {items['Knife']}개")
        print(f"  Handcuffs: {items['Handcuffs']}개")
    
    print_separator()

def get_user_action(env, user_player: Player) -> int:
    """사용자로부터 액션 입력 받기"""
    items = env.red_items if user_player == Player.RED else env.blue_items
    
    print("\n액션 선택:")
    print("  0: ShootSelf (자신에게 쏘기)")
    print("  1: ShootOther (상대에게 쏘기)")
    
    if items['Drink'] > 0:
        print(f"  2: Drink (Energy Drink - 총알 제거) [{items['Drink']}개 보유]")
    else:
        print(f"  2: Drink (보유하지 않음)")
    
    if items['MagGlass'] > 0:
        print(f"  3: MagGlass (Magnifying Glass - 다음 총알 확인) [{items['MagGlass']}개 보유]")
    else:
        print(f"  3: MagGlass (보유하지 않음)")
    
    if items['Cigar'] > 0:
        print(f"  4: Cigar (체력 회복) [{items['Cigar']}개 보유]")
    else:
        print(f"  4: Cigar (보유하지 않음)")
    
    if items['Knife'] > 0:
        print(f"  5: Knife (데미지 2배) [{items['Knife']}개 보유]")
    else:
        print(f"  5: Knife (보유하지 않음)")
    
    if items['Handcuffs'] > 0:
        print(f"  6: Handcuffs (상대 턴 스킵) [{items['Handcuffs']}개 보유]")
    else:
        print(f"  6: Handcuffs (보유하지 않음)")
    
    while True:
        try:
            choice = input("\n액션 번호를 입력하세요 (0-6): ").strip()
            action = int(choice)
            
            if action < 0 or action > 6:
                print("❌ 잘못된 번호입니다. 0-6 사이의 숫자를 입력하세요.")
                continue
            
            # 아이템 보유 여부 확인
            if action == 2 and items['Drink'] == 0:
                print("❌ Energy Drink을 보유하지 않습니다.")
                continue
            if action == 3 and items['MagGlass'] == 0:
                print("❌ Magnifying Glass를 보유하지 않습니다.")
                continue
            if action == 4 and items['Cigar'] == 0:
                print("❌ Cigar를 보유하지 않습니다.")
                continue
            if action == 5 and items['Knife'] == 0:
                print("❌ Knife를 보유하지 않습니다.")
                continue
            if action == 6 and items['Handcuffs'] == 0:
                print("❌ Handcuffs를 보유하지 않습니다.")
                continue
            
            return action
            
        except ValueError:
            print("❌ 숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n\n게임을 종료합니다.")
            sys.exit(0)

def print_action_result(action: int, reward: float, env, user_player: Player, action_player: Player):
    """액션 결과 출력"""
    action_names = {
        0: "ShootSelf (자신에게 쏘기)",
        1: "ShootOther (상대에게 쏘기)",
        2: "Drink (Energy Drink)",
        3: "MagGlass (Magnifying Glass)",
        4: "Cigar (체력 회복)",
        5: "Knife (데미지 2배)",
        6: "Handcuffs (상대 턴 스킵)"
    }
    
    # 액션을 실행한 플레이어 확인
    actor = "YOU" if action_player == user_player else "AI"
    print(f"\n{actor}의 액션: {action_names[action]}")
    
    if reward > 0:
        print(f"✅ 결과: 성공 (보상: +{reward:.1f})")
    elif reward < 0:
        if reward <= -10:
            print(f"❌ 결과: 실패 (페널티: {reward:.1f})")
        else:
            print(f"⚠️  결과: 불리함 (보상: {reward:.1f})")
    else:
        print(f"⚪ 결과: 중립")
    
    input("\n계속하려면 Enter를 누르세요...")

def play_game(
    checkpoint_dir: str = None,
    max_hp: int = 4,
    user_player: Player = Player.RED
):
    """
    실시간 게임 플레이
    
    Args:
        checkpoint_dir: 체크포인트 디렉토리
        max_hp: 최대 HP
        user_player: 사용자가 플레이할 플레이어 (RED 또는 BLUE)
    """
    # checkpoint_dir이 None이면 상위 디렉토리의 Agents 사용
    if checkpoint_dir is None:
        checkpoint_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Agents')
    
    # 에이전트 생성 (epsilon=0으로 설정하여 탐험 없이 플레이)
    agent = Agent(
        gamma=0.99,
        epsilon=0.0,
        lr=4e-4,
        input_dims=[20],
        n_actions=7,
        mem_size=1_000_000,
        batch_size=64,
        eps_min=0.0,
        eps_dec=0.0,
        replace=100,
        checkpoint_dir=checkpoint_dir
    )
    
    # 체크포인트 로드
    try:
        print("Loading checkpoint...")
        agent.load_models()
        print("✓ Checkpoint loaded successfully\n")
    except Exception as e:
        print(f"✗ Error loading checkpoint: {e}")
        print("Please make sure buckshot_eval and buckshot_next files exist in the checkpoint directory.")
        return
    
    # 게임 환경 생성
    env = GameEnvironment(max_hp=max_hp)
    state = env.reset()
    
    action_names = [action.name for action in ActionType]
    
    print("\n게임을 시작합니다!")
    print(f"당신은 {'Red' if user_player == Player.RED else 'Blue'} 플레이어입니다.")
    input("시작하려면 Enter를 누르세요...")
    
    done = False
    step_count = 0
    max_steps = 1000
    
    while not done and step_count < max_steps:
        step_count += 1
        
        # 게임 상태 표시
        display_game_state(env, user_player)
        
        # 현재 플레이어 확인
        current_player = env.current_turn
        
        # 액션 실행 전 총알 개수 저장 (라운드 종료 체크용)
        rounds_before_action = len(env.rounds)
        was_last_round = rounds_before_action == 1  # 마지막 총알인지 확인
        
        if current_player == user_player:
            # 사용자 턴
            action = get_user_action(env, user_player)
        else:
            # AI 턴
            print("\nAI가 생각 중...")
            action, was_random = agent.choose_action(state)
            print(f"AI 선택: {action_names[action]}")
            input("\n계속하려면 Enter를 누르세요...")
        
        # 총알을 소모하는 액션인지 확인 (ShootSelf, ShootOther, Drink)
        consumes_round = action in [ActionType.ShootSelf, ActionType.ShootOther, ActionType.Drink]
        
        # 액션 실행
        next_state, reward, done, info = env.step(action)
        
        # 액션 실행 후 총알 개수 확인 (새 라운드가 시작되었는지 확인)
        rounds_after_action = len(env.rounds)
        # 마지막 총알을 사용했고, 새 라운드가 시작되었다면 라운드가 끝난 것
        # (총알을 소모하는 액션이었고, 액션 전에 1개였고, 액션 후에 새 라운드가 시작된 경우)
        rounds_exhausted = consumes_round and was_last_round and rounds_after_action > 0
        
        # 결과 표시 (액션을 실행한 플레이어 정보 전달)
        if current_player == user_player:
            print_action_result(action, reward, env, user_player, current_player)
        else:
            # AI 액션 결과는 간단히 표시
            display_game_state(env, user_player)
            print_action_result(action, reward, env, user_player, current_player)
        
        state = next_state
        
        # 게임 종료 체크
        # 1. 한 플레이어가 죽은 경우
        # 2. 라운드의 총알이 모두 떨어진 경우 (마지막 총알을 사용한 경우)
        
        if done or rounds_exhausted:
            clear_screen()
            print_separator()
            print("게임 종료!")
            print_separator()
            
            if env.red_lives <= 0:
                if user_player == Player.RED:
                    print("\n❌ 패배! AI가 승리했습니다.")
                else:
                    print("\n🎉 승리! 당신이 승리했습니다!")
            elif env.blue_lives <= 0:
                if user_player == Player.BLUE:
                    print("\n❌ 패배! AI가 승리했습니다.")
                else:
                    print("\n🎉 승리! 당신이 승리했습니다!")
            elif rounds_exhausted:
                # 총알이 다 떨어진 경우 - HP가 더 높은 플레이어가 승리
                if env.red_lives > env.blue_lives:
                    if user_player == Player.RED:
                        print("\n🎉 승리! 총알이 모두 소진되었고, 당신의 HP가 더 높습니다!")
                    else:
                        print("\n❌ 패배! 총알이 모두 소진되었고, AI의 HP가 더 높습니다.")
                elif env.blue_lives > env.red_lives:
                    if user_player == Player.BLUE:
                        print("\n🎉 승리! 총알이 모두 소진되었고, 당신의 HP가 더 높습니다!")
                    else:
                        print("\n❌ 패배! 총알이 모두 소진되었고, AI의 HP가 더 높습니다.")
                else:
                    print("\n⚖️  무승부! 총알이 모두 소진되었고, 두 플레이어의 HP가 같습니다.")
            
            print(f"\n최종 HP:")
            print(f"  Red: {env.red_lives}/{env.max_hp}")
            print(f"  Blue: {env.blue_lives}/{env.max_hp}")
            print(f"총 턴 수: {step_count}")
            print_separator()
            break
        
        if step_count >= max_steps:
            print("\n⚠️  최대 턴 수에 도달했습니다. 게임을 종료합니다.")
            break

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time interactive game against AI')
    parser.add_argument('--checkpoint-dir', type=str, default=None, help='Checkpoint directory (default: ../Agents)')
    parser.add_argument('--max-hp', type=int, default=4, help='Maximum HP')
    parser.add_argument('--player', type=str, choices=['red', 'blue'], default='red', 
                       help='Player side (red or blue, default: red)')
    
    args = parser.parse_args()
    
    user_player = Player.RED if args.player.lower() == 'red' else Player.BLUE
    
    try:
        play_game(
            checkpoint_dir=args.checkpoint_dir,
            max_hp=args.max_hp,
            user_player=user_player
        )
    except KeyboardInterrupt:
        print("\n\n게임을 종료합니다.")
        sys.exit(0)
