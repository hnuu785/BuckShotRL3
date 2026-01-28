import numpy as np
from model import Agent
from utils import plotLearning
import data
import time



if(__name__ == "__main__"):
    load_checkpoint = True

    agent = Agent(gamma=0.99,epsilon=0,lr=4e-4, input_dims=[20],n_actions=7, mem_size=1_000_000, eps_min=0, batch_size=64,eps_dec=4e-4,replace=100)

    if load_checkpoint:
        agent.load_models()

    filename = 'BuckshotRoulette-DDDQN-Adam-lr5e4-replace100-1.png'
    scores, eps_history = [],[]
    num_games = 5000

    def get_action_mask_from_state(state):
        # state는 Unity에서 받은 1차원 배열 (리스트 또는 numpy array)
        # Action Mask 초기화 (0: 불가, 1: 가능)
        mask = np.zeros(7)
        
        # 상태 인덱스 파싱 (GameManager.cs의 sendInput 순서 기준)
        # [0]: Turn (0=Blue, 1=Red)
        # [1]: Total Rounds (총알 수)
        # [16]: Gun Damage (1=기본, 2=톱질됨)
        # [18]: Blue Handcuffed
        # [19]: Red Handcuffed
        
        current_turn = state[0] # 0.0 or 1.0
        has_rounds = (state[1] > 0)
        gun_damage = state[16]
        is_sawed = (gun_damage > 1.5) # 데미지가 2면 톱질된 상태
        
        # 아이템 인덱스 시작점 설정
        # Red(1.0)인 경우 index 6부터, Blue(0.0)인 경우 index 11부터
        if current_turn > 0.5: # Red Turn
            base_idx = 6
            opponent_handcuffed = (state[18] > 0.5) # Blue가 수갑 찼는지
        else: # Blue Turn
            base_idx = 11
            opponent_handcuffed = (state[19] > 0.5) # Red가 수갑 찼는지
            
        # 아이템 개수 확인
        n_drink = state[base_idx + 0]
        n_mag = state[base_idx + 1]
        n_cigar = state[base_idx + 2]
        n_knife = state[base_idx + 3]
        n_cuffs = state[base_idx + 4]
        
        # 마스크 설정
        if has_rounds:
            mask[0] = 1.0 # Shoot Self
            mask[1] = 1.0 # Shoot Other
            if n_drink > 0: mask[2] = 1.0 # Drink
            if n_mag > 0: mask[3] = 1.0 # Mag Glass
        
        if n_cigar > 0: mask[4] = 1.0 # Cigar (총알 없어도 사용 가능 여부는 게임 룰에 따라 다름, 보통 상관없음)
        
        if n_knife > 0 and not is_sawed and has_rounds: mask[5] = 1.0 # Knife (이미 톱질 안했고 총알 있을 때)
        
        if n_cuffs > 0 and not opponent_handcuffed: mask[6] = 1.0 # Handcuffs (상대가 안 묶여있을 때)

        return mask


    def on_connection_established(client_socket):
        print("Connection established")

        for i in range(num_games):
            done = False
            score = 0
            

            while not done:
                observation = data.get_state()
                time.sleep(6 / 3) #6 seconds between  actions
                action_mask = get_action_mask_from_state(observation)
                action, was_random = agent.choose_action(observation, action_mask=action_mask)
                observation_, reward, done = data.play_step(action)
                print(f"{was_random} Action {action}: Reward {reward}")
                score += reward

            data.reset()
            scores.append(score)
            avg_score = np.mean(scores[-100:])
            print('episode', i, 'score %.lf' % score, 'average score %.lf ' % avg_score, 'epsilon %.2f ' % agent.epsilon)

        print("- training process over -")
        print("- creating model graph -")
        x = [i+1 for i in range(num_games)]
        plotLearning(x,scores,eps_history,filename)

    
            

    data.create_host(on_connection_established)