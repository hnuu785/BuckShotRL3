import numpy as np
import os
import sys

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

    # epsilon: 게임 수 기준 선형 감소 (num_games 동안 0.1 → 0.01)
    eps_initial, eps_min = 0.1, 0.01
    eps_dec_per_game = (eps_initial - eps_min) / num_games

    # 메인 학습 에이전트 하나만 사용
    main_agent = Agent(gamma=0.99, epsilon=eps_initial, lr=5e-5,
                       input_dims=[20], n_actions=7, mem_size=100000,
                       batch_size=64, eps_min=eps_min, eps_dec=eps_dec_per_game, replace=100,
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
                # BLUE 턴
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
                main_agent.store_transition(view, action, reward, next_view, int(done))
                main_agent.learn()
                obs = next_obs

        scores_history.append(score)
        eps_history.append(main_agent.epsilon)
        main_agent.decrease_epsilon()  # 게임 1회마다 epsilon 1회 감소

        # 주기적으로 모델 저장 (100게임마다)
        if game_num % 100 == 0:
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
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=10000, help="학습할 게임 수 (짧게: 200~500)")
    p.add_argument("--no-load", action="store_true", help="기존 체크포인트 무시하고 처음부터")
    p.add_argument("--save-dir", type=str, default="Agents", help="체크포인트 저장 경로")
    args = p.parse_args()
    train_pure_self_play(
        num_games=args.games,
        load_checkpoint=not args.no_load,
        save_dir=args.save_dir,
    )