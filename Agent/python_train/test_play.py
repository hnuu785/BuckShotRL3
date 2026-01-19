"""
체크포인트를 사용한 테스트 플레이 스크립트
buckshot_eval과 buckshot_next 체크포인트를 로드하여 게임을 플레이합니다.
"""
"""
체크포인트를 사용한 테스트 플레이 스크립트 (시점 변환 수정 버전)
"""
import numpy as np
import os
import sys

# 상위 디렉토리를 경로에 추가하여 model, utils, train_ref를 import할 수 있도록 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Agent
from game_env import GameEnvironment, Player, ActionType
from train_ref import get_opponent_action

def test_play(
    num_games: int = 10,
    checkpoint_dir = "Agents",
    max_hp: int = 4,
    verbose: bool = True
):
    if checkpoint_dir is None:
        checkpoint_dir = "Agents"
    
    print("=" * 70)
    print("Buckshot Roulette Test Play (Invariance Applied)")
    print("=" * 70)
    
    # 두 에이전트 생성 (epsilon=0으로 설정하여 탐험 없이 플레이)
    agent_red = Agent(gamma=0.99, epsilon=0.0, lr=4e-4, input_dims=[20], n_actions=7,
                      mem_size=1000000, batch_size=64, eps_min=0.0, eps_dec=0.0,
                      replace=100, checkpoint_dir=checkpoint_dir)
    
    agent_blue = Agent(gamma=0.99, epsilon=0.0, lr=4e-4, input_dims=[20], n_actions=7,
                       mem_size=1000000, batch_size=64, eps_min=0.0, eps_dec=0.0,
                       replace=100, checkpoint_dir=checkpoint_dir)
    
    # 체크포인트 로드 (buckshot_eval 사용)
    try:
        agent_red.load_models()
        agent_blue.load_models()
        print("✓ Checkpoints loaded successfully")
    except Exception as e:
        print(f"✗ Error loading checkpoints: {e}")
        return
    
    env = GameEnvironment(max_hp=max_hp)
    red_wins, blue_wins = 0, 0
    red_scores, blue_scores, game_lengths = [], [], []
    action_names = [action.name for action in ActionType]
    
    for game_num in range(num_games):
        obs = env.reset() #
        done = False
        red_score, blue_score, step_count = 0.0, 0.0, 0
        
        while not done and step_count < 1000:
            step_count += 1
            current_player = Player.RED if env.current_turn == Player.RED else Player.BLUE
            agent = agent_red if current_player == Player.RED else agent_blue
            
            # [핵심 수정] 에이전트에게 주기 전 시점을 항상 '본인 중심'으로 변환
            # Red(1P)일 때는 데이터를 Swap하여 에이전트가 본인을 Blue(0P)라고 착각하게 만듦
            state_for_agent = env.preprocess_state(obs) 
            
            # 변환된 상태로 액션 결정
            action, _ = agent.choose_action(state_for_agent)
            
            # 실제 환경에 액션 적용 (원본 관측값 기준)
            next_obs, reward, done, info = env.step(action)
            
            if current_player == Player.RED: red_score += reward
            else: blue_score += reward
            
            if verbose and step_count <= 10: # 로그 출력
                p_name = "Red" if current_player == Player.RED else "Blue"
                print(f"Step {step_count} | {p_name} | Action: {action_names[action]} | Reward: {reward:.1f}")
            
            obs = next_obs
            
            if done:
                if env.red_lives <= 0: blue_wins += 1
                elif env.blue_lives <= 0: red_wins += 1
                break
        
        red_scores.append(red_score)
        blue_scores.append(blue_score)
        game_lengths.append(step_count)
    
    # 최종 결과 출력
    print("\n" + "=" * 70)
    print(f"Final Results over {num_games} games")
    print(f"Red Win Rate: {red_wins/num_games*100:.1f}% | Avg Score: {np.mean(red_scores):.2f}")
    print(f"Blue Win Rate: {blue_wins/num_games*100:.1f}% | Avg Score: {np.mean(blue_scores):.2f}")
    print(f"Average Steps: {np.mean(game_lengths):.1f}")
    print("=" * 70)

if __name__ == "__main__":
    test_play(num_games=100)

def test_against_teacher(
    num_games: int = 100,
    checkpoint_dir = "Agents",
    max_hp: int = 4,
    teacher_level: int = 4  # 선생님 난이도 설정
):
    if checkpoint_dir is None:
        checkpoint_dir = "Agents"
    
    # 내 에이전트 생성 (Blue 진영으로 테스트)
    my_agent = Agent(gamma=0.99, epsilon=0.0, lr=0, input_dims=[20], n_actions=7,
                     mem_size=1, batch_size=1, checkpoint_dir=checkpoint_dir)
    
    try:
        my_agent.load_models()
        print(f"✅ 내 에이전트 로드 완료 (Location: {checkpoint_dir})")
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return

    env = GameEnvironment(max_hp=max_hp)
    my_wins, teacher_wins = 0, 0
    my_scores, teacher_scores = [], []

    print("=" * 70)
    print(f"🥊 대결 시작: 내 에이전트 (Blue) vs Level {teacher_level} 선생님 (Red)")
    print("=" * 70)

    for game_num in range(num_games):
        obs = env.reset()
        done = False
        my_score, teacher_score = 0.0, 0.0
        
        while not done:
            if env.current_turn == Player.BLUE:
                # 1. 내 에이전트 턴 (시점 변환 후 액션 결정)
                state_for_agent = env.preprocess_state(obs)
                action, _ = my_agent.choose_action(state_for_agent)
                obs, reward, done, _ = env.step(action)
                my_score += reward
            else:
                # 2. Level 4 선생님 턴 (기존 Rule-based 로직 사용)
                action = get_opponent_action(obs, teacher_level)
                obs, reward, done, _ = env.step(action)
                teacher_score += reward
            
        # 결과 집계
        if env.blue_lives > 0 and env.red_lives <= 0:
            my_wins += 1
        elif env.red_lives > 0 and env.blue_lives <= 0:
            teacher_wins += 1
            
        my_scores.append(my_score)
        teacher_scores.append(teacher_score)

    # 최종 승률 보고
    print("\n" + "=" * 70)
    print(f"📊 최종 성적 ({num_games} 게임)")
    print(f"🏆 내 에이전트 승률: {my_wins/num_games*100:.1f}% (Avg Score: {np.mean(my_scores):.2f})")
    print(f"👨‍🏫 선생님 AI 승률: {teacher_wins/num_games*100:.1f}% (Avg Score: {np.mean(teacher_scores):.2f})")
    print("=" * 70)

if __name__ == "__main__":
    test_against_teacher(num_games=100)