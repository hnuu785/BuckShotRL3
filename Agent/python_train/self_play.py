import numpy as np
import os
import sys
import random
import torch as T

# 상위 디렉토리 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import Agent
from utils import plotLearning
from game_env import GameEnvironment, Player

def train_pure_self_play(
    num_games: int = 10000,
    checkpoint_interval: int = 300,
    save_dir: str = 'Agents',
    load_checkpoint: bool = True,
    max_hp: int = 4
):
    # 디렉토리 생성
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    
    # 메인 학습 에이전트 하나만 사용
    main_agent = Agent(gamma=0.99, epsilon=0.1, lr=5e-5, 
                       input_dims=[20], n_actions=7, mem_size=100000, 
                       batch_size=64, eps_min=0.01, eps_dec=1e-6, replace=100, 
                       checkpoint_dir=save_dir)

    if load_checkpoint:
        try:
            main_agent.load_models()
            print(">>> 기존 buckshot_eval 모델 로드 완료.")
        except:
            print(">>> 기존 모델이 없습니다. 처음부터 학습합니다.")

    env = GameEnvironment(max_hp=max_hp)
    
    scores_history = []
    eps_history = []

    print(f"🚀 순수 Self-Play 학습 시작 (총 {num_games} 게임)")

    for game_num in range(1, num_games + 1):
        obs = env.reset() #
        done = False
        score = 0
        
        while not done:
            # 현재 턴인 플레이어의 관점으로 시점 변환
            view = env.preprocess_state(obs)
            mask = env.get_action_mask()
            # 메인 에이전트의 현재 지능으로 액션 선택 (BLUE/RED 공통, action masking 적용)
            action, _ = main_agent.choose_action(view, action_mask=mask)
            
            if env.current_turn == Player.BLUE:
                # BLUE(0번) 턴: 학습용 데이터 저장 (BLUE 관점 보상 그대로)
                next_obs, reward, done, _ = env.step(action)
                next_view = env.preprocess_state(next_obs)
                main_agent.store_transition(view, action, reward, next_view, int(done))
                main_agent.learn()
                score += reward
                obs = next_obs
            else:
                # RED(1번) 턴: RED 경험도 BLUE 관점으로 저장 후 학습
                # RED가 얻은 보상 = BLUE 입장에선 손해이므로 -reward 로 저장
                next_obs, reward, done, _ = env.step(action)
                next_view = env.preprocess_state(next_obs)
                main_agent.store_transition(view, action, -reward, next_view, int(done))
                main_agent.learn()
                obs = next_obs

        scores_history.append(score)
        eps_history.append(main_agent.epsilon)

        # 주기적으로 모델 업데이트 출력 및 저장
        if game_num % 10 == 0:
            main_agent.save_models()
            
        if game_num % checkpoint_interval == 0:
            avg_score = np.mean(scores_history[-checkpoint_interval:])
            print(f"Ep {game_num} | Avg Score: {avg_score:.1f} | Eps: {main_agent.epsilon:.4f}")

    # --- 학습 종료 후 그래프 생성 ---
    print(">>> 학습 종료. 그래프 생성 중...")
    x = [i+1 for i in range(len(scores_history))]
    graph_filename = 'pure_self_play_results.png'
    plotLearning(x, scores_history, eps_history, graph_filename)
    print(f"✅ 그래프 저장 완료: {graph_filename}")

if __name__ == "__main__":
    train_pure_self_play()