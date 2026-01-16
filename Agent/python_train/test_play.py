"""
체크포인트를 사용한 테스트 플레이 스크립트
buckshot_eval과 buckshot_next 체크포인트를 로드하여 게임을 플레이합니다.
"""
import numpy as np
import os
import sys

# 상위 디렉토리를 경로에 추가하여 model, utils를 import할 수 있도록 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Agent
from game_env import GameEnvironment, Player, ActionType

def test_play(
    num_games: int = 10,
    checkpoint_dir: str = None,
    max_hp: int = 4,
    verbose: bool = True
):
    """
    체크포인트를 사용한 테스트 플레이
    
    Args:
        num_games: 플레이할 게임 수
        checkpoint_dir: 체크포인트 디렉토리 (None이면 상위 디렉토리의 Agents 사용)
        max_hp: 최대 HP
        verbose: 상세 출력 여부
    """
    # checkpoint_dir이 None이면 상위 디렉토리의 Agents 사용
    if checkpoint_dir is None:
        checkpoint_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Agents')
    
    print("=" * 70)
    print("Buckshot Roulette Test Play")
    print("=" * 70)
    print(f"Checkpoint directory: {checkpoint_dir}")
    print(f"Number of games: {num_games}")
    print(f"Max HP: {max_hp}")
    print("=" * 70)
    
    # 두 에이전트 생성 (epsilon=0으로 설정하여 탐험 없이 플레이)
    agent_red = Agent(
        gamma=0.99,
        epsilon=0.0,  # 탐험 없이 플레이
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
    
    agent_blue = Agent(
        gamma=0.99,
        epsilon=0.0,  # 탐험 없이 플레이
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
        print("\nLoading checkpoints...")
        agent_red.load_models()
        agent_blue.load_models()
        print("✓ Checkpoints loaded successfully")
    except Exception as e:
        print(f"✗ Error loading checkpoints: {e}")
        print("Please make sure buckshot_eval and buckshot_next files exist in the checkpoint directory.")
        return
    
    # 게임 환경 생성
    env = GameEnvironment(max_hp=max_hp)
    
    # 통계 추적
    red_wins = 0
    blue_wins = 0
    red_scores = []
    blue_scores = []
    game_lengths = []
    
    action_names = [action.name for action in ActionType]
    
    print("\n" + "=" * 70)
    print("Starting test play...")
    print("=" * 70)
    
    for game_num in range(num_games):
        # 게임 초기화
        state = env.reset()
        done = False
        
        red_score = 0.0
        blue_score = 0.0
        step_count = 0
        max_steps = 1000  # 무한 루프 방지
        
        if verbose:
            print(f"\n--- Game {game_num + 1}/{num_games} ---")
            print(f"Initial state:")
            print(f"  Red HP: {env.red_lives}, Blue HP: {env.blue_lives}")
            print(f"  Total rounds: {len(env.rounds)}")
            print(f"  Live rounds: {sum(1 for r in env.rounds if r.value == 1)}")
            print(f"  Blank rounds: {sum(1 for r in env.rounds if r.value == 0)}")
            print(f"  Current turn: {'Red' if env.current_turn == Player.RED else 'Blue'}")
        
        while not done and step_count < max_steps:
            step_count += 1
            
            # 현재 플레이어 결정
            current_player = Player.RED if env.current_turn == Player.RED else Player.BLUE
            agent = agent_red if current_player == Player.RED else agent_blue
            
            # 액션 선택 (학습 없이)
            action, was_random = agent.choose_action(state)
            
            if verbose and step_count <= 20:  # 처음 20스텝만 상세 출력
                print(f"\nStep {step_count}: {'Red' if current_player == Player.RED else 'Blue'} turn")
                print(f"  Action: {action_names[action]} ({action})")
                print(f"  Decision: {was_random}")
            
            # 액션 실행
            next_state, reward, done, info = env.step(action)
            
            # 보상 기록
            if current_player == Player.RED:
                red_score += reward
            else:
                blue_score += reward
            
            if verbose and step_count <= 20:
                print(f"  Reward: {reward:.2f}")
                print(f"  Red HP: {env.red_lives}, Blue HP: {env.blue_lives}")
                print(f"  Remaining rounds: {len(env.rounds)}")
            
            state = next_state
            
            # 게임 종료 체크
            if done:
                # 승리자 결정
                if env.red_lives <= 0:
                    blue_wins += 1
                    winner = "Blue"
                elif env.blue_lives <= 0:
                    red_wins += 1
                    winner = "Red"
                else:
                    winner = "Draw"
                
                if verbose:
                    print(f"\n  Game Over! Winner: {winner}")
                    print(f"  Final Red HP: {env.red_lives}, Blue HP: {env.blue_lives}")
                    print(f"  Total steps: {step_count}")
                    print(f"  Red Score: {red_score:.2f}, Blue Score: {blue_score:.2f}")
                
                break
        
        # 게임 종료 후 통계 업데이트
        red_scores.append(red_score)
        blue_scores.append(blue_score)
        game_lengths.append(step_count)
        
        if step_count >= max_steps:
            print(f"\n  Warning: Game {game_num + 1} reached max steps ({max_steps})")
    
    # 최종 통계 출력
    print("\n" + "=" * 70)
    print("Test Play Results")
    print("=" * 70)
    print(f"Total games: {num_games}")
    print(f"Red wins: {red_wins} ({red_wins/num_games*100:.1f}%)")
    print(f"Blue wins: {blue_wins} ({blue_wins/num_games*100:.1f}%)")
    print(f"Draws: {num_games - red_wins - blue_wins}")
    print(f"\nAverage game length: {np.mean(game_lengths):.1f} steps")
    print(f"Average Red score: {np.mean(red_scores):.2f}")
    print(f"Average Blue score: {np.mean(blue_scores):.2f}")
    print(f"Red score std: {np.std(red_scores):.2f}")
    print(f"Blue score std: {np.std(blue_scores):.2f}")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test play with loaded checkpoints')
    parser.add_argument('--num-games', type=int, default=10, help='Number of games to play')
    parser.add_argument('--checkpoint-dir', type=str, default=None, help='Checkpoint directory (default: ../Agents)')
    parser.add_argument('--max-hp', type=int, default=4, help='Maximum HP')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode (less verbose output)')
    
    args = parser.parse_args()
    
    test_play(
        num_games=args.num_games,
        checkpoint_dir=args.checkpoint_dir,
        max_hp=args.max_hp,
        verbose=not args.quiet
    )
