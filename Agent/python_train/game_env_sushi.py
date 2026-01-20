import numpy as np
import random
from enum import IntEnum
from typing import Tuple, Optional

class ActionType(IntEnum):
    EatSelf = 0      # 내가 먹기 (ShootSelf)
    EatOther = 1     # 상대 먹이기 (ShootOther)
    DrinkTea = 2     # 녹차/콜라 마시고 스시 버리기 (Drink/Beer)
    Chopsticks = 3   # 젓가락으로 와사비 확인 (MagGlass)
    Pickle = 4       # 단무지/초생강 먹고 체력 회복 (Cigar)
    DivideSushi = 5  # 스시를 칼로 나눠 두 조각 만들기 (Knife/Saw)
    TakeSoySauce = 6 # 간장종지 압수해서 턴 스킵 (Handcuffs)

class RoundType(IntEnum):
    WASABI = 1  # 실탄 (LIVE)
    NORMAL = 0  # 빈 총알 (BLANK)

class Player(IntEnum):
    RED = 1
    BLUE = 0

class GameEnvironment:
    def __init__(self, max_hp: int = 4):
        self.max_hp = max_hp
        self.reset()
    
    def reset(self):
        """게임 초기화: 배고픔(HP) 및 새 판 시작"""
        self.red_lives = self.max_hp
        self.blue_lives = self.max_hp
        self._start_new_round()
        self.current_turn = Player.BLUE
        self.sushi_damage = 1  # 기본 와사비 데미지
        self.is_divided = False # 스시 분할 여부
        self.red_soy_confiscated = False # 간장 압수 상태
        self.blue_soy_confiscated = False
        self.sushi_knowledge = -1 # 젓가락으로 확인한 정보
        
        return self.get_state()
    
    def _start_new_round(self):
        """새 라운드: 스시 접시 세팅 및 아이템 배분"""
        num_wasabi = random.randint(1, 4)
        num_normal = random.randint(1, 4)
        
        # 스시 접시 구성 및 셔플
        self.rounds = [RoundType.WASABI] * num_wasabi + [RoundType.NORMAL] * num_normal
        random.shuffle(self.rounds)
        
        # 아이템(반찬) 배분
        self.red_items = self._generate_items(random.randint(2, 4))
        self.blue_items = self._generate_items(random.randint(2, 4))
        
        self.sushi_damage = 1
        self.is_divided = False
        self.sushi_knowledge = -1
    
    def _generate_items(self, count: int) -> dict:
        items = {
            'Tea': 0,        # 녹차
            'Chopsticks': 0, # 젓가락
            'Pickle': 0,     # 단무지
            'Knife': 0,      # 칼(스시 분할)
            'SoySauce': 0    # 간장(압수용)
        }
        item_types = ['Tea', 'Chopsticks', 'Pickle', 'Knife', 'SoySauce']
        for _ in range(count):
            item = random.choice(item_types)
            items[item] += 1
        return items
    
    def get_state(self) -> np.ndarray:
        """현재 상태 벡터 (20차원 - 기존과 동일)"""
        state = []
        state.append(float(self.current_turn)) # 1
        total = len(self.rounds)
        wasabi = sum(1 for r in self.rounds if r == RoundType.WASABI)
        normal = total - wasabi
        state.extend([float(total), float(wasabi), float(normal)]) # 3
        state.extend([float(self.red_lives), float(self.blue_lives)]) # 2
        
        # Red 아이템 (5차원)
        state.extend([
            float(self.red_items['Tea']), float(self.red_items['Chopsticks']),
            float(self.red_items['Pickle']), float(self.red_items['Knife']),
            float(self.red_items['SoySauce'])
        ])
        # Blue 아이템 (5차원)
        state.extend([
            float(self.blue_items['Tea']), float(self.blue_items['Chopsticks']),
            float(self.blue_items['Pickle']), float(self.blue_items['Knife']),
            float(self.blue_items['SoySauce'])
        ])
        
        state.extend([float(self.sushi_damage), float(self.sushi_knowledge)]) # 2
        state.extend([float(1 if self.blue_soy_confiscated else 0), float(1 if self.red_soy_confiscated else 0)]) # 2
        
        return np.array(state, dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        reward = 0.0
        done = False
        info = {}
        turn_continues = False
        
        # 간장종지 압수(수갑) 체크
        is_confiscated = self.red_soy_confiscated if self.current_turn == Player.RED else self.blue_soy_confiscated
        if is_confiscated:
            if self.current_turn == Player.RED: self.red_soy_confiscated = False
            else: self.blue_soy_confiscated = False
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            return self.get_state(), 0.0, done, info

        act = ActionType(action)
        
        if act == ActionType.EatSelf:
            reward, turn_continues = self._eat_self()
        elif act == ActionType.EatOther:
            reward = self._eat_other()
        elif act == ActionType.DrinkTea:
            reward = self._use_tea()
        elif act == ActionType.Chopsticks:
            reward = self._use_chopsticks()
            turn_continues = True
        elif act == ActionType.Pickle:
            reward = self._use_pickle()
        elif act == ActionType.DivideSushi:
            reward = self._use_knife()
        elif act == ActionType.TakeSoySauce:
            reward = self._use_soy_sauce()
        else:
            reward = -50.0
        
        # 승패 체크 (기존 리워드 +50/-50 유지)
        if self.red_lives <= 0:
            done = True
            reward += 50.0 if self.current_turn == Player.BLUE else -50.0
        elif self.blue_lives <= 0:
            done = True
            reward += 50.0 if self.current_turn == Player.RED else -50.0
            
        if len(self.rounds) == 0 and not done: self._start_new_round()
        
        if not turn_continues and not done:
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            # 다음 플레이어 간장 압수 확인
            if self.current_turn == Player.RED and self.red_soy_confiscated:
                self.red_soy_confiscated = False
                self.current_turn = Player.BLUE
            elif self.current_turn == Player.BLUE and self.blue_soy_confiscated:
                self.blue_soy_confiscated = False
                self.current_turn = Player.RED
        
        # 사격(식사) 후 칼 효과 리셋
        if act in [ActionType.EatSelf, ActionType.EatOther, ActionType.DrinkTea]:
            self.is_divided = False
            self.sushi_damage = 1
            
        return self.get_state(), reward, done, info

    def _eat_self(self) -> Tuple[float, bool]:
        if not self.rounds: return -50.0, False
        sushi = self.rounds.pop(0)
        self.sushi_knowledge = -1
        was_divided = self.is_divided
        
        if sushi == RoundType.WASABI:
            dmg = self.sushi_damage
            if self.current_turn == Player.RED: self.red_lives -= dmg
            else: self.blue_lives -= dmg
            reward = -(dmg * 15.0) + (5.0 if was_divided else 0.0)
            return reward, False
        else:
            reward = 15.0 - (5.0 if was_divided else 0.0)
            return reward, True

    def _eat_other(self) -> float:
        if not self.rounds: return -50.0
        sushi = self.rounds.pop(0)
        self.sushi_knowledge = -1
        was_divided = self.is_divided
        
        if sushi == RoundType.WASABI:
            dmg = self.sushi_damage
            if self.current_turn == Player.RED: self.blue_lives -= dmg
            else: self.red_lives -= dmg
            return (dmg * 10.0) + (5.0 if was_divided else 0.0)
        else:
            return -5.0 - (5.0 if was_divided else 0.0)

    def _use_tea(self) -> float:
        items = self.red_items if self.current_turn == Player.RED else self.blue_items
        if items['Tea'] <= 0 or not self.rounds: return -50.0
        items['Tea'] -= 1
        sushi = self.rounds.pop(0)
        self.sushi_knowledge = -1
        return 5.0 if sushi == RoundType.WASABI else 1.0

    def _use_chopsticks(self) -> float:
        items = self.red_items if self.current_turn == Player.RED else self.blue_items
        if items['Chopsticks'] <= 0 or not self.rounds: return -50.0
        items['Chopsticks'] -= 1
        self.sushi_knowledge = int(self.rounds[0])
        return 3.0

    def _use_pickle(self) -> float:
        items = self.red_items if self.current_turn == Player.RED else self.blue_items
        if items['Pickle'] <= 0: return -50.0
        items['Pickle'] -= 1
        hp = self.red_lives if self.current_turn == Player.RED else self.blue_lives
        if hp < self.max_hp:
            if self.current_turn == Player.RED: self.red_lives += 1
            else: self.blue_lives += 1
            return 5.0
        return -2.0

    def _use_knife(self) -> float:
        items = self.red_items if self.current_turn == Player.RED else self.blue_items
        if items['Knife'] <= 0 or self.is_divided: return -50.0
        items['Knife'] -= 1
        self.is_divided = True
        self.sushi_damage = 2
        return 0.0

    def _use_soy_sauce(self) -> float:
        items = self.red_items if self.current_turn == Player.RED else self.blue_items
        if items['SoySauce'] <= 0: return -50.0
        items['SoySauce'] -= 1
        if self.current_turn == Player.RED:
            if self.blue_soy_confiscated: return -10.0
            self.blue_soy_confiscated = True
        else:
            if self.red_soy_confiscated: return -10.0
            self.red_soy_confiscated = True
        return 7.0

    def preprocess_state(self, state):
        if state[0] == 1.0: # RED 관점일 때 BLUE 관점으로 반전
            flipped = np.copy(state)
            flipped[0] = 0.0
            flipped[4], flipped[5] = state[5], state[4] # HP 스왑
            flipped[6:11], flipped[11:16] = state[11:16], state[6:11] # 아이템 스왑
            flipped[18], flipped[19] = state[19], state[18] # 압수 상태 스왑
            return flipped
        return state
