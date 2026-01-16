import numpy as np
import os
import time
from model import Agent
from BuckshotEnv import BuckshotEnv, ACTION_OPP, ACTION_SELF

def rule_based_ai(state):
    # state 정보 분해
    turn = state[0]
    is_red = (turn == 1)
    
    # 탄환 정보
    num_total = state[1]
    num_real = state[2]
    num_empty = state[3]
    
    knowledge = state[17] # 0:공포탄, 1:실탄, 2:모름
    
    # 내 정보 (체력, 아이템)
    my_hp = state[4] if is_red else state[5]
    # 아이템 인덱스: 0:맥주, 1:돋보기, 2:담배, 3:칼, 4:수갑
    my_items = state[6:11] if is_red else state[11:16]
    
    # 상대 정보 (수갑 여부)
    opp_cuffed = state[18] if is_red else state[19] # 내가 레드면 파랑수갑 확인

    # --- 1. 확실한 정보(Knowledge)가 있을 때 최우선 행동 ---
    if knowledge == 1: return ACTION_OPP # 실탄이면 쏜다
    if knowledge == 0: return ACTION_SELF # 공포탄이면 나를 쏴서 턴 유지

    # --- 2. 생존 및 정보 확보 (아이템) ---
    # 체력이 없고 담배가 있으면 사용 (담배: Action 4)
    if my_hp < 4 and my_items[2] > 0: 
        return 4 
    
    # 탄을 모르고 돋보기가 있으면 사용 (돋보기: Action 3)
    if knowledge == 2 and my_items[1] > 0: 
        return 3

    # --- 3. 전략적 아이템 사용 ---
    # 상대가 수갑을 안 찼고, 내 수갑이 있으면 사용 (수갑: Action 6)
    # (턴을 뺏어와서 연속 공격 가능성을 높임)
    if not opp_cuffed and my_items[4] > 0:
        return 6
    
    # 실탄 비율이 높으면 칼을 써서 데미지 2배 (칼: Action 5)
    # 조건: 실탄이 공포탄보다 많거나 같을 때
    if my_items[3] > 0 and num_real >= num_empty:
        return 5

    # --- 4. 확률 기반 사격 (Probability Logic) ---
    # 실탄이 공포탄보다 많거나 같으면 -> 상대를 쏜다 (맞을 확률 높음)
    if num_real >= num_empty:
        return ACTION_OPP
    
    # 공포탄이 더 많으면 -> 나를 쏜다 (공포탄일 확률 높음 -> 턴 유지 노림)
    else:
        return ACTION_SELF

if __name__ == "__main__":
    if not os.path.exists('models'): os.makedirs('models')
    if not os.path.exists('plots'): os.makedirs('plots')

    print(">>> Initializing Environment...")
    env = BuckshotEnv()
    agent_name = "Ref_Agent"
    
    agent = Agent(gamma=0.99, epsilon=1.0, lr=1e-4, input_dims=[20], n_actions=7, 
                  mem_size=50000, batch_size=64, replace=1000, 
                  eps_dec=2e-6, eps_min=0.01,
                  checkpoint_dir='models', name=agent_name)

    scores, eps_history = [], []
    num_games = 20000 

    print(f"\n=== Phase 1: Training {agent_name} vs Smart Rule-Based AI (20k Episodes) ===")
    print(">>> Training Started! (Logs will appear shortly)")

    start_time = time.time()

    for i in range(num_games):
        obs = env.reset()
        done = False
        score = 0
        
        while not done:
            if env.turn == 0: 
                action, _ = agent.choose_action(obs)
                next_obs, reward, done = env.step(action)
                agent.store_transition(obs, action, reward, next_obs, int(done))
                agent.learn()
                score += reward
                obs = next_obs
            else: 
                action = rule_based_ai(obs)
                next_obs, _, done = env.step(action)
                obs = next_obs

        scores.append(score)
        eps_history.append(agent.epsilon)

        if (i+1) <= 100:
            if (i+1) % 10 == 0:
                print(f"[Warm-up] Ep {i+1} | Score: {score:.1f} | Eps: {agent.epsilon:.2f}")
        elif (i+1) % 500 == 0:
            avg_score = np.mean(scores[-100:])
            elapsed = time.time() - start_time
            print(f"Episode {i+1} | Avg Score (100): {avg_score:.2f} | Epsilon: {agent.epsilon:.2f} | Time: {elapsed:.1f}s")

        if (i+1) % 1000 == 0:
            save_name_base = f"{agent_name}_ep{i+1}"
            
            agent.q_eval.checkpoint_file = os.path.join(agent.checkpoint_dir, save_name_base + "_eval")
            agent.q_next.checkpoint_file = os.path.join(agent.checkpoint_dir, save_name_base + "_next")
            
            agent.save_checkpoint()
            print(f">>> Checkpoint saved: models/{save_name_base}_eval")

    from utils import plotLearning
    x = [j+1 for j in range(num_games)]
    plotLearning(x, scores, eps_history, "plots/Phase1_Learning_Curve_20k.png")
    
    print(f"'models/' 폴더를 확인해보세요. 파일들이 생성되었습니다.")