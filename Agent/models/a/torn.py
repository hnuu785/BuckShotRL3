import numpy as np
import os
import torch
import random
from model import Agent
from BuckshotEnv import BuckshotEnv

SELECTED_FIGHTERS = [
    # 예시 경로 (실제 파일명에 맞춰 수정 필요)
    "models/Scenario_Balanced/ep_18000.pth",
    "models/Scenario_Aggressive/ep_15000.pth",
    "models/Scenario_Defensive/ep_20000.pth",
    "models/Scenario_Sparse/ep_12000.pth",
    "models/Scenario_RoundFocus/ep_19000.pth",
    "models/Scenario_ItemStrict/ep_16000.pth",
    "models/Scenario_Berserker/ep_10000.pth",
    "models/Scenario_Sniper/ep_14000.pth",
    "models/Scenario_Cautious/ep_19500.pth",
    "models/Scenario_Healer/ep_17000.pth",
    "models/Scenario_Gambler/ep_20000.pth",
    "models/Scenario_Survivor/ep_18000.pth",
    "models/Scenario_Executioner/ep_15000.pth",
    "models/Scenario_Strategist/ep_16000.pth",
    "models/Scenario_Vampire/ep_13000.pth",
    "models/Scenario_GlassCannon/ep_11000.pth"
]

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

def load_agent(path, name):
    agent = Agent(gamma=0.99, epsilon=0, lr=0, input_dims=[20], n_actions=7, 
                  mem_size=1, batch_size=1, checkpoint_dir='models', name=name)
    try:
        agent.load_state_dict(torch.load(path, map_location=agent.device))
    except FileNotFoundError:
        print(f"Error: Model file not found at {path}")
        return None
    return agent

def play_match(p1_path, p2_path):
    p1_name = p1_path.split('/')[-2] + "_" + p1_path.split('/')[-1].replace('.pth','')
    p2_name = p2_path.split('/')[-2] + "_" + p2_path.split('/')[-1].replace('.pth','')
    
    agent1 = load_agent(p1_path, "P1")
    agent2 = load_agent(p2_path, "P2")
    
    if agent1 is None or agent2 is None:
        return None

    print(f"\n⚔️ MATCH START: {p1_name} vs {p2_name}")
    
    env = BuckshotEnv()
    p1_wins = 0
    p2_wins = 0
    total_games = 200

    for _ in range(total_games):
        obs = env.reset()
        done = False
        while not done:
            turn = env.turn
            curr_agent = agent1 if turn == 0 else agent2
            
            view = preprocess_state(obs)
            action, _ = curr_agent.choose_action(view)
            next_obs, _, done = env.step(action)
            obs = next_obs
        
        if env.blue_lives > 0: p1_wins += 1
        else: p2_wins += 1
    
    print(f"   Result: {p1_name} ({p1_wins}) vs {p2_name} ({p2_wins})")
    
    if p1_wins >= p2_wins:
        print(f"   🎉 Winner: {p1_name}")
        return p1_path
    else:
        print(f"   🎉 Winner: {p2_name}")
        return p2_path

def run_bracket(fighter_paths):
    round_num = 1
    current_round = fighter_paths[:]
    
    random.shuffle(current_round)

    while len(current_round) > 1:
        print(f"\n============= ROUND {round_num} ({len(current_round)} Fighters) =============")
        next_round = []
        
        for i in range(0, len(current_round), 2):
            if i + 1 >= len(current_round):
                print(f"   -> {current_round[i]} gets a BYE (Automatic Advance)")
                next_round.append(current_round[i])
                break
                
            p1 = current_round[i]
            p2 = current_round[i+1]
            winner = play_match(p1, p2)
            if winner:
                next_round.append(winner)
        
        current_round = next_round
        round_num += 1

    print(f"\n🏆🏆 ULTIMATE CHAMPION: {current_round[0]} 🏆🏆")

if __name__ == "__main__":
    if len(SELECTED_FIGHTERS) < 2:
        print("Need at least 2 fighters for a tournament.")
    else:
        run_bracket(SELECTED_FIGHTERS)