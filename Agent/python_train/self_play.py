import numpy as np
import os
import sys
import time

# 상위 디렉토리를 경로에 추가하여 model, utils를 import할 수 있도록 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Agent
from utils import plotLearning
from game_env import GameEnvironment, Player

def train_self_play(
    num_games: int = 10000,
    checkpoint_interval: int = 100,
    save_dir: str = None,
    load_checkpoint: bool = True,
    gamma: float = 0.99,
    epsilon: float = 1.0,
    lr: float = 4e-4,
    eps_min: float = 0.01,
    eps_dec: float = 2e-5,
    replace: int = 100,
    mem_size: int = 1_000_000,
    batch_size: int = 64,
    max_hp: int = 4
):
    """
    셀프 플레이 학습
    
    Args:
        num_games: 학습할 게임 수
        checkpoint_interval: 체크포인트 저장 간격
        save_dir: 모델 저장 디렉토리 (None이면 상위 디렉토리의 Agents 사용)
        load_checkpoint: 체크포인트 로드 여부
        gamma: 할인율
        epsilon: 초기 엡실론
        lr: 학습률
        eps_min: 최소 엡실론
        eps_dec: 엡실론 감소율
        replace: 타겟 네트워크 업데이트 주기
        mem_size: 리플레이 버퍼 크기
        batch_size: 배치 크기
        max_hp: 최대 HP
    """
    # save_dir가 None이면 상위 디렉토리의 Agents 사용
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Agents')
    
    # 디렉토리가 없으면 생성
    os.makedirs(save_dir, exist_ok=True)
    
    # 두 에이전트 생성 (같은 모델 사용)
    agent_red = Agent(
        gamma=gamma,
        epsilon=epsilon,
        lr=lr,
        input_dims=[20],
        n_actions=7,
        mem_size=mem_size,
        batch_size=batch_size,
        eps_min=eps_min,
        eps_dec=eps_dec,
        replace=replace,
        checkpoint_dir=save_dir
    )
    
    agent_blue = Agent(
        gamma=gamma,
        epsilon=epsilon,
        lr=lr,
        input_dims=[20],
        n_actions=7,
        mem_size=mem_size,
        batch_size=batch_size,
        eps_min=eps_min,
        eps_dec=eps_dec,
        replace=replace,
        checkpoint_dir=save_dir
    )
    
    # 체크포인트 로드
    if load_checkpoint:
        try:
            agent_red.load_models()
            agent_blue.load_models()
            print("Checkpoint loaded successfully")
        except:
            print("No checkpoint found, starting from scratch")
    
    # 게임 환경 생성
    env = GameEnvironment(max_hp=max_hp)
    
    # 통계 추적
    red_scores = []
    blue_scores = []
    eps_history = []
    red_wins = 0
    blue_wins = 0
    
    print("Starting self-play training...")
    print(f"Total games: {num_games}")
    print(f"Checkpoint interval: {checkpoint_interval}")
    print("-" * 50)
    
    for game_num in range(num_games):
        # 게임 초기화
        state = env.reset()
        done = False
        
        red_score = 0.0
        blue_score = 0.0
        step_count = 0
        max_steps = 1000  # 무한 루프 방지
        
        while not done and step_count < max_steps:
            step_count += 1
            
            # 현재 플레이어 결정
            current_player = Player.RED if env.current_turn == Player.RED else Player.BLUE
            agent = agent_red if current_player == Player.RED else agent_blue
            
            # 액션 선택
            action, was_random = agent.choose_action(state)
            
            # 액션 실행
            next_state, reward, done, info = env.step(action)
            
            # 보상 기록
            if current_player == Player.RED:
                red_score += reward
            else:
                blue_score += reward
            
            # 경험 저장 및 학습
            agent.store_transition(state, action, reward, next_state, int(done))
            agent.learn()
            
            state = next_state
            
            # 게임 종료 체크
            if done:
                # 승리자 결정 및 상대방에게도 보상 전달
                if env.red_lives <= 0:
                    # Blue 승리
                    blue_wins += 1
                    # Red에게 패배 보상 전달 (이미 reward에 포함되어 있을 수 있지만 확실히 하기 위해)
                    if current_player == Player.RED:
                        # Red가 마지막 액션을 했고 패배한 경우 (자해로 죽음)
                        # 보상은 이미 계산됨
                        pass
                    else:
                        # Blue가 승리했지만 Red에게도 패배 보상 전달
                        red_final_reward = -50.0
                        red_score += red_final_reward
                        # Red의 마지막 상태로 경험 저장
                        red_state = env.get_state()
                        agent_red.store_transition(red_state, 0, red_final_reward, red_state, 1)
                elif env.blue_lives <= 0:
                    # Red 승리
                    red_wins += 1
                    # Blue에게 패배 보상 전달
                    if current_player == Player.BLUE:
                        # Blue가 마지막 액션을 했고 패배한 경우 (자해로 죽음)
                        # 보상은 이미 계산됨
                        pass
                    else:
                        # Red가 승리했지만 Blue에게도 패배 보상 전달
                        blue_final_reward = -50.0
                        blue_score += blue_final_reward
                        # Blue의 마지막 상태로 경험 저장
                        blue_state = env.get_state()
                        agent_blue.store_transition(blue_state, 0, blue_final_reward, blue_state, 1)
                
                break
        
        # 게임 종료 후 통계 업데이트
        red_scores.append(red_score)
        blue_scores.append(blue_score)
        eps_history.append((agent_red.epsilon + agent_blue.epsilon) / 2)
        
        # 평균 점수 계산
        red_avg = np.mean(red_scores[-100:]) if len(red_scores) >= 100 else np.mean(red_scores)
        blue_avg = np.mean(blue_scores[-100:]) if len(blue_scores) >= 100 else np.mean(blue_scores)
        
        # 진행 상황 출력
        if (game_num + 1) % 10 == 0 or game_num == 0:
            print(f"Game {game_num + 1}/{num_games}")
            print(f"  Red Score: {red_score:.2f} (Avg: {red_avg:.2f}) | Blue Score: {blue_score:.2f} (Avg: {blue_avg:.2f})")
            print(f"  Red Wins: {red_wins} | Blue Wins: {blue_wins}")
            print(f"  Red Epsilon: {agent_red.epsilon:.4f} | Blue Epsilon: {agent_blue.epsilon:.4f}")
            print("-" * 50)
        
        # 체크포인트 저장
        if (game_num + 1) % checkpoint_interval == 0:
            print(f"\nSaving checkpoint at game {game_num + 1}...")
            agent_red.save_models()
            agent_blue.save_models()
            
            # 통계 저장
            stats_file = os.path.join(save_dir, 'training_stats.npz')
            np.savez(
                stats_file,
                red_scores=red_scores,
                blue_scores=blue_scores,
                eps_history=eps_history,
                red_wins=red_wins,
                blue_wins=blue_wins,
                game_num=game_num + 1
            )
            print(f"Checkpoint saved to {save_dir}\n")
    
    # 최종 모델 저장
    print("\nSaving final models...")
    agent_red.save_models()
    agent_blue.save_models()
    
    # 최종 통계 저장
    stats_file = os.path.join(save_dir, 'training_stats.npz')
    np.savez(
        stats_file,
        red_scores=red_scores,
        blue_scores=blue_scores,
        eps_history=eps_history,
        red_wins=red_wins,
        blue_wins=blue_wins,
        game_num=num_games
    )
    
    # 학습 그래프 생성
    print("Creating learning graphs...")
    x = [i + 1 for i in range(num_games)]
    
    # Red 에이전트 그래프
    filename_red = os.path.join(save_dir, 'self_play_red_learning.png')
    plotLearning(x, red_scores, eps_history, filename_red)
    
    # Blue 에이전트 그래프
    filename_blue = os.path.join(save_dir, 'self_play_blue_learning.png')
    plotLearning(x, blue_scores, eps_history, filename_blue)
    
    print("\nTraining completed!")
    print(f"Final stats:")
    print(f"  Red Wins: {red_wins} ({red_wins/num_games*100:.1f}%)")
    print(f"  Blue Wins: {blue_wins} ({blue_wins/num_games*100:.1f}%)")
    print(f"  Draws: {num_games - red_wins - blue_wins}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Self-play training for Buckshot Roulette')
    parser.add_argument('--num-games', type=int, default=10000, help='Number of games to train')
    parser.add_argument('--checkpoint-interval', type=int, default=100, help='Checkpoint save interval')
    parser.add_argument('--save-dir', type=str, default=None, help='Directory to save models (default: ../Agents)')
    parser.add_argument('--no-load', action='store_true', help='Do not load checkpoint')
    parser.add_argument('--gamma', type=float, default=0.99, help='Discount factor')
    parser.add_argument('--epsilon', type=float, default=1.0, help='Initial epsilon')
    parser.add_argument('--lr', type=float, default=4e-4, help='Learning rate')
    parser.add_argument('--eps-min', type=float, default=0.01, help='Minimum epsilon')
    parser.add_argument('--eps-dec', type=float, default=2e-5, help='Epsilon decay')
    parser.add_argument('--replace', type=int, default=100, help='Target network update interval')
    parser.add_argument('--mem-size', type=int, default=1_000_000, help='Replay buffer size')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--max-hp', type=int, default=4, help='Maximum HP')
    
    args = parser.parse_args()
    
    train_self_play(
        num_games=args.num_games,
        checkpoint_interval=args.checkpoint_interval,
        save_dir=args.save_dir,
        load_checkpoint=not args.no_load,
        gamma=args.gamma,
        epsilon=args.epsilon,
        lr=args.lr,
        eps_min=args.eps_min,
        eps_dec=args.eps_dec,
        replace=args.replace,
        mem_size=args.mem_size,
        batch_size=args.batch_size,
        max_hp=args.max_hp
    )
