import numpy as np
import os
import sys
import random
import torch as T
import pandas as pd

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
    best_avg_score = float('-inf')  # 최고 평균 점수 추적

    print(f"🚀 순수 Self-Play 학습 시작 (총 {num_games} 게임)")

    for game_num in range(1, num_games + 1):
        obs = env.reset() #
        done = False
        score = 0
        
        while not done:
            # 현재 턴인 플레이어의 관점으로 시점 변환
            view = env.preprocess_state(obs)
            
            # 메인 에이전트의 현재 지능으로 액션 선택 (BLUE/RED 공통)
            action, _ = main_agent.choose_action(view)
            
            if env.current_turn == Player.BLUE:
                # BLUE(0번) 턴: 실제 학습용 데이터를 쌓음
                next_obs, reward, done, _ = env.step(action)
                
                # 다음 상태도 BLUE 관점으로 변환하여 저장
                next_view = env.preprocess_state(next_obs)
                main_agent.store_transition(view, action, reward, next_view, int(done))
                main_agent.learn()
                
                score += reward
                obs = next_obs
            else:
                # RED(1번) 턴: 액션만 수행 (학습 데이터는 쌓지 않음)
                # 이미 위에서 main_agent의 action을 뽑았으므로 그대로 실행
                obs, _, done, _ = env.step(action)

        scores_history.append(score)
        eps_history.append(main_agent.epsilon)

        # 주기적으로 성능 체크 및 고점일 때만 저장
        if game_num % checkpoint_interval == 0:
            avg_score = np.mean(scores_history[-checkpoint_interval:])
            
            if avg_score > best_avg_score:
                best_avg_score = avg_score
                main_agent.save_models()
                print(f"Ep {game_num} | Avg Score: {avg_score:.1f} | Eps: {main_agent.epsilon:.4f} | 🏆 NEW BEST! 모델 저장")
            else:
                print(f"Ep {game_num} | Avg Score: {avg_score:.1f} | Eps: {main_agent.epsilon:.4f} | Best: {best_avg_score:.1f}")

    # --- 학습 종료 후 그래프 생성 ---
    print(">>> 학습 종료. 그래프 생성 중...")
    x = [i+1 for i in range(len(scores_history))]
    graph_filename = 'pure_self_play_results.png'
    plotLearning(x, scores_history, eps_history, graph_filename)
    print(f"✅ 그래프 저장 완료: {graph_filename}")
    
    # --- 엑셀 파일로 결과 저장 ---
    print(">>> 엑셀 파일 생성 중...")
    df = pd.DataFrame({
        'Episode': x,
        'Score': scores_history,
        'Epsilon': eps_history
    })
    
    # 이동 평균 추가 (100 에피소드 기준)
    df['Avg_Score_100'] = df['Score'].rolling(window=100, min_periods=1).mean()
    
    excel_filename = 'pure_self_play_results.xlsx'
    df.to_excel(excel_filename, index=False, sheet_name='Training Results')
    print(f"✅ 엑셀 저장 완료: {excel_filename}")

if __name__ == "__main__":
    train_pure_self_play()