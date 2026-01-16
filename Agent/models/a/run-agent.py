import numpy as np
import os
import torch
import matplotlib.pyplot as plt
from model import Agent
from BuckshotEnv import BuckshotEnv

BOSS_MODEL_NAME = "Ref_Agent_ep28000"
TOTAL_EPISODES = 40000
SAVE_INTERVAL = 20

def preprocess_state(state):
    if state[0] == 1: 
        flipped = np.copy(state)
        flipped[0] = 0
        flipped[4], flipped[5] = state[5], state[4]
        flipped[6:11] = state[11:16]
        flipped[11:16] = state[6:11]
        flipped[18], flipped[19] = state[19], state[18]
        return flipped
    return state

def plot_learning_curve(x, scores, figure_file, title):
    running_avg = np.zeros(len(scores))
    for i in range(len(running_avg)):
        running_avg[i] = np.mean(scores[max(0, i-100):(i+1)])
    plt.figure(figsize=(10, 6))
    plt.plot(x, running_avg)
    plt.title(f'Running average of previous 100 scores - {title}')
    plt.xlabel('Episodes')
    plt.ylabel('Average Score')
    plt.grid(True)
    plt.savefig(figure_file)
    plt.close()

def get_configs():
    base = [
        # --- Group A: 정석 파생형 (User Reference 기반 미세 조정) ---
        
        # 1. Balanced: 작성해주신 기준값 그대로 적용 (표준)
        {"name": "Balanced", "cfg": {"final_win": 1.2, "round_win": 0.3, "dmg_dealt": 0.1, "dmg_taken": -0.1, "heal": 0.05, "item_bad": -2.0, "lose": -2.4}},
        
        # 2. Aggressive: 딜량 보상을 높여 더 공격적인 운영 유도
        {"name": "Aggressive", "cfg": {"final_win": 1.2, "round_win": 0.3, "dmg_dealt": 0.25, "dmg_taken": -0.1, "heal": 0.05, "item_bad": -2.0, "lose": -2.4}},
        
        # 3. Defensive: 맞는 것을 더 싫어하고(-0.2), 회복을 중시(0.15)
        {"name": "Defensive", "cfg": {"final_win": 1.2, "round_win": 0.3, "dmg_dealt": 0.1, "dmg_taken": -0.25, "heal": 0.15, "item_bad": -2.0, "lose": -2.4}},
        
        # 4. ItemStrict: 아이템 실수를 '죄악' 수준으로 설정 (-3.0)
        {"name": "ItemStrict", "cfg": {"final_win": 1.2, "round_win": 0.3, "dmg_dealt": 0.1, "dmg_taken": -0.1, "heal": 0.05, "item_bad": -3.0, "lose": -2.4}},
        
        # 5. RoundFocus: 최종 승리보다 당장 눈앞의 라운드 승리에 더 집착 (스노우볼링)
        {"name": "RoundFocus", "cfg": {"final_win": 1.0, "round_win": 0.6, "dmg_dealt": 0.1, "dmg_taken": -0.1, "heal": 0.05, "item_bad": -2.0, "lose": -2.4}},
        
        # 6. Sniper: 상대에게 딜을 넣는 행위에 큰 가산점, 빗나가는 것(간접적) 싫어함
        {"name": "Sniper", "cfg": {"final_win": 1.2, "round_win": 0.2, "dmg_dealt": 0.3, "dmg_taken": -0.1, "heal": 0.0, "item_bad": -2.0, "lose": -2.4}},
        
        # 7. Executioner: 힐링 페널티(오직 죽이는 것만 생각), 라운드 승리 중시
        {"name": "Executioner", "cfg": {"final_win": 1.2, "round_win": 0.4, "dmg_dealt": 0.2, "dmg_taken": -0.1, "heal": -0.05, "item_bad": -2.0, "lose": -2.4}},
        
        # 8. Cautious: 아이템 실수와 피격 모두 극도로 경계
        {"name": "Cautious", "cfg": {"final_win": 1.2, "round_win": 0.2, "dmg_dealt": 0.1, "dmg_taken": -0.4, "heal": 0.1, "item_bad": -2.5, "lose": -2.4}},
        
        # 9. Strategist: 모든 자잘한 행동 점수를 낮추고, 오직 승/패/실수방지에만 집중
        {"name": "Strategist", "cfg": {"final_win": 1.5, "round_win": 0.2, "dmg_dealt": 0.05, "dmg_taken": -0.05, "heal": 0.05, "item_bad": -3.0, "lose": -3.0}},
        
        # 10. GlassCannon: 내가 아픈 건 상관없고(-0.01), 너만 아프면 됨(0.4)
        {"name": "GlassCannon", "cfg": {"final_win": 1.2, "round_win": 0.3, "dmg_dealt": 0.4, "dmg_taken": -0.01, "heal": 0.0, "item_bad": -2.0, "lose": -2.4}},
        
        # 11. Survivor: 힐 효율을 극대화하여 끈질기게 버티기
        {"name": "Survivor", "cfg": {"final_win": 1.2, "round_win": 0.2, "dmg_dealt": 0.05, "dmg_taken": -0.3, "heal": 0.3, "item_bad": -2.0, "lose": -2.4}},
        
        # 12. Sparse: 행동 보상 거의 없음. 이기는 법을 스스로 깨우쳐야 함
        {"name": "Sparse", "cfg": {"final_win": 2.0, "round_win": 0.5, "dmg_dealt": 0.01, "dmg_taken": -0.01, "heal": 0.01, "item_bad": -2.0, "lose": -3.0}},

        # --- Group B: 방향성 4가지 (Divergent) - 다양성 확보용 ---
        # (여전히 item_bad는 -2.0 이상으로 유지하여 멍청한 짓은 방지)
        
        # 13. Berserker (광전사): 맞는 것을 두려워하지 않음(dmg_taken 0), 오직 딜과 승리
        {"name": "Berserker", "cfg": {"final_win": 1.5, "round_win": 0.2, "dmg_dealt": 0.5, "dmg_taken": 0.0, "heal": -0.1, "item_bad": -2.0, "lose": -2.0}},
        
        # 14. Gambler (도박사): 과정(딜/힐) 다 무시. 이기면 대박(+3), 지면 쪽박(-3).
        {"name": "Gambler", "cfg": {"final_win": 3.0, "round_win": 0.0, "dmg_dealt": 0.0, "dmg_taken": 0.0, "heal": 0.0, "item_bad": -2.0, "lose": -3.0}},
        
        # 15. Vampire (흡혈귀): 딜과 힐에 엄청난 가중치. 오래 살면서 괴롭히는 스타일.
        {"name": "Vampire", "cfg": {"final_win": 1.0, "round_win": 0.1, "dmg_dealt": 0.3, "dmg_taken": -0.1, "heal": 0.4, "item_bad": -2.0, "lose": -2.0}},
        
        # 16. Turtle (철벽): 힐과 방어(피격 패널티)에 몰빵. 이기는 것보다 '안 죽는 것'이 목표.
        {"name": "Turtle", "cfg": {"final_win": 1.0, "round_win": 0.1, "dmg_dealt": 0.0, "dmg_taken": -0.6, "heal": 0.4, "item_bad": -2.0, "lose": -2.0}},
    ]
    return base

def train_scenario(config, boss_agent):
    scenario_name = f"Scenario_{config['name']}"
    save_dir = os.path.join('models', scenario_name)
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"\n>>> Start Training: {scenario_name} (Reward Config: {config['cfg']})")

    env = BuckshotEnv(reward_config=config['cfg'])
    agent = Agent(gamma=0.99, epsilon=1.0, lr=1e-4, input_dims=[20], n_actions=7, 
                  mem_size=50000, batch_size=64, replace=1000, 
                  checkpoint_dir=save_dir, name=scenario_name)
    
    scores = []
    eps_history = []
    
    for i in range(1, TOTAL_EPISODES + 1):
        obs = env.reset()
        done = False
        score = 0
        while not done:
            if env.turn == 0:
                view = preprocess_state(obs)
                action, _ = agent.choose_action(view)
                next_obs, reward, done = env.step(action)
                next_view = preprocess_state(next_obs)
                agent.store_transition(view, action, reward, next_view, int(done))
                agent.learn()
                score += reward
                obs = next_obs
            else:
                view = preprocess_state(obs)
                action, _ = boss_agent.choose_action(view)
                next_obs, _, done = env.step(action)
                obs = next_obs
        
        scores.append(score)
        eps_history.append(i)

        if i % SAVE_INTERVAL == 0:
            file_path = os.path.join(save_dir, f"ep_{i}.pth")
            torch.save(agent.state_dict(), file_path)
            
        if i % 100 == 0:
            avg_score = np.mean(scores[-100:])
            print(f"[{scenario_name}] Ep {i}/{TOTAL_EPISODES} | Avg Score: {avg_score:.2f} | Epsilon: {agent.epsilon:.2f}")

    plot_path = os.path.join(save_dir, f"{scenario_name}_graph.png")
    plot_learning_curve(eps_history, scores, plot_path, scenario_name)
    print(f"Finished {scenario_name}. Graph saved to {plot_path}")

if __name__ == "__main__":
    boss_path = os.path.join('models', BOSS_MODEL_NAME)
    if not os.path.exists(boss_path):
        print("Reference Model Not Found!")
        exit()
        
    boss_agent = Agent(gamma=0.99, epsilon=0, lr=0, input_dims=[20], n_actions=7, 
                       mem_size=1, batch_size=1, checkpoint_dir='models', name="BOSS")
    try:
        boss_agent.load_state_dict(torch.load(boss_path, map_location=boss_agent.device))
    except:
        boss_agent.checkpoint_file = boss_path
        boss_agent.load_checkpoint()
    boss_agent.epsilon = 0

    configs = get_configs()
    for cfg in configs:
        train_scenario(cfg, boss_agent)