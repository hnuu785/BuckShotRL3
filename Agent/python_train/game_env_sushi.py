import numpy as np
import random
from enum import IntEnum
from typing import Tuple, Optional

class ActionType(IntEnum):
    EatSelf = 0       # 자신에게 먹기 (ShootSelf)
    EatOther = 1      # 상대에게 먹이기 (ShootOther)
    GreenTea = 2      # 녹차/콜라 (Drink)
    Chopsticks = 3    # 젓가락으로 확인 (MagGlass)
    Pickle = 4        # 단무지/초생강 (Cigar)
    KitchenKnife = 5  # 칼로 나누기 (Knife)
    SoySauce = 6      # 간장종지 압수 (Handcuffs)

class RoundType(IntEnum):
    WASABI = 1        # 와사비 스시 (LIVE)
    NORMAL = 0        # 일반 스시 (BLANK)

class Player(IntEnum):
    RED = 1
    BLUE = 0

class GameEnvironment:
    def __init__(self, max_hp: int = 4):
        self.max_hp = max_hp
        self.reset()
    
    def reset(self):
        """게임 초기화 및 새 접시 시작"""
        # HP 초기화
        self.red_lives = self.max_hp
        self.blue_lives = self.max_hp
        
        # 새 라운드 시작
        self._start_new_round()
        
        # 턴 정보 (0: Blue, 1: Red)
        self.current_turn = Player.BLUE
        
        # 스시 상태
        self.sushi_damage = 1  # 기본 데미지
        self.is_split = False  # KitchenKnife 사용 여부
        
        # 간장종지 압수 상태
        self.red_handcuffed = False
        self.blue_handcuffed = False
        
        # 젓가락으로 확인한 스시 정보 (-1: 알 수 없음, 0: 일반, 1: 와사비)
        self.sushi_knowledge = -1
        
        return self.get_state()
    
    def _start_new_round(self):
        """
        새 접시 시작: 스시 생성 및 아이템 배분
        체력은 유지됩니다.
        """
        # 스시 생성: 1-4개의 와사비와 1-4개의 일반 스시
        num_wasabi = random.randint(1, 4)
        num_normal = random.randint(1, 4)
        
        # 스시 리스트 생성 및 셔플
        self.rounds = [RoundType.WASABI] * num_wasabi + [RoundType.NORMAL] * num_normal
        random.shuffle(self.rounds)
        
        # 아이템 배분 (각 플레이어에게 2-4개)
        self.red_items = self._generate_items(random.randint(2, 4))
        self.blue_items = self._generate_items(random.randint(2, 4))
        
        # 접시 상태 초기화
        self.sushi_damage = 1
        self.is_split = False
        self.sushi_knowledge = -1
    
    def _generate_items(self, count: int) -> dict:
        """랜덤 아이템 생성 (스시 테마)"""
        items = {
            'GreenTea': 0,      # 녹차
            'Chopsticks': 0,    # 젓가락
            'Pickle': 0,        # 단무지
            'KitchenKnife': 0,  # 칼
            'SoySauce': 0       # 간장종지
        }
        
        item_types = ['GreenTea', 'Chopsticks', 'Pickle', 'KitchenKnife', 'SoySauce']
        for _ in range(count):
            item = random.choice(item_types)
            items[item] += 1
        
        return items
    
    def get_state(self) -> np.ndarray:
        """현재 상태 벡터 반환 (20차원)"""
        state = []
        
        # 1. 턴 정보 (1차원)
        state.append(float(self.current_turn))
        
        # 2. 스시 정보 (3차원)
        total_rounds = len(self.rounds)
        total_wasabi = sum(1 for r in self.rounds if r == RoundType.WASABI)
        total_normal = sum(1 for r in self.rounds if r == RoundType.NORMAL)
        state.extend([float(total_rounds), float(total_wasabi), float(total_normal)])
        
        # 3. 생명력 (2차원)
        state.extend([float(self.red_lives), float(self.blue_lives)])
        
        # 4. Red 아이템 (5차원)
        state.extend([
            float(self.red_items['GreenTea']),
            float(self.red_items['Chopsticks']),
            float(self.red_items['Pickle']),
            float(self.red_items['KitchenKnife']),
            float(self.red_items['SoySauce'])
        ])
        
        # 5. Blue 아이템 (5차원)
        state.extend([
            float(self.blue_items['GreenTea']),
            float(self.blue_items['Chopsticks']),
            float(self.blue_items['Pickle']),
            float(self.blue_items['KitchenKnife']),
            float(self.blue_items['SoySauce'])
        ])
        
        # 6. 접시 상태 (2차원)
        state.extend([float(self.sushi_damage), float(self.sushi_knowledge)])
        
        # 7. 간장종지 상태 (2차원)
        state.extend([float(1 if self.blue_handcuffed else 0), float(1 if self.red_handcuffed else 0)])
        
        return np.array(state, dtype=np.float32)
    
    def _get_current_player_items(self) -> dict:
        """현재 플레이어의 아이템 반환"""
        return self.red_items if self.current_turn == Player.RED else self.blue_items
    
    def _use_item(self, item_name: str) -> bool:
        """아이템 사용"""
        items = self._get_current_player_items()
        if items[item_name] > 0:
            items[item_name] -= 1
            return True
        return False
    
    def _is_handcuffed(self) -> bool:
        """간장종지 압수 여부 확인"""
        return self.red_handcuffed if self.current_turn == Player.RED else self.blue_handcuffed
    
    def _skip_turn(self):
        """턴 스킵"""
        if self.current_turn == Player.RED:
            self.blue_handcuffed = False
        else:
            self.red_handcuffed = False
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """액션 실행"""
        reward = 0.0
        done = False
        info = {}
        turn_continues = False 
        
        # 간장종지 체크
        if self._is_handcuffed():
            if self.current_turn == Player.RED:
                self.red_handcuffed = False
            else:
                self.blue_handcuffed = False
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            return self.get_state(), 0.0, done, info
        
        action_type = ActionType(action)
        
        # 액션 처리
        if action_type == ActionType.EatSelf:
            reward, turn_continues = self._eat_self()
        elif action_type == ActionType.EatOther:
            reward = self._eat_other()
            turn_continues = False
        elif action_type == ActionType.GreenTea:
            reward = self._use_greentea()
            turn_continues = False
        elif action_type == ActionType.Chopsticks:
            reward = self._use_chopsticks()
            turn_continues = True
        elif action_type == ActionType.Pickle:
            reward = self._use_pickle()
            turn_continues = False
        elif action_type == ActionType.KitchenKnife:
            reward = self._use_kitchen_knife()
            turn_continues = False
        elif action_type == ActionType.SoySauce:
            reward = self._use_soysauce()
            turn_continues = False
        else:
            reward = -50.0
            turn_continues = False
        
        # 게임 종료 체크
        if self.red_lives <= 0:
            done = True
            if self.current_turn == Player.BLUE:
                reward += 50.0
            else:
                reward -= 50.0
        elif self.blue_lives <= 0:
            done = True
            if self.current_turn == Player.RED:
                reward += 50.0
            else:
                reward -= 50.0
        
        # 스시가 없으면 새 접시 시작
        if len(self.rounds) == 0 and not done:
            self._start_new_round()
        
        # 턴 관리
        if not turn_continues and not done:
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            if self.current_turn == Player.RED and self.red_handcuffed:
                self.red_handcuffed = False
                self.current_turn = Player.BLUE
            elif self.current_turn == Player.BLUE and self.blue_handcuffed:
                self.blue_handcuffed = False
                self.current_turn = Player.RED
        
        # 효과 초기화
        if action_type in [ActionType.EatSelf, ActionType.EatOther, ActionType.GreenTea]:
            if self.is_split:
                self.is_split = False
                self.sushi_damage = 1
        
        return self.get_state(), reward, done, info
    
    def _eat_self(self) -> Tuple[float, bool]:
        """자신이 먹기"""
        if len(self.rounds) == 0:
            return -50.0, False
        
        sushi = self.rounds.pop(0)
        self.sushi_knowledge = -1
        split_used = self.is_split
        
        if sushi == RoundType.WASABI:
            damage = self.sushi_damage
            if self.current_turn == Player.RED:
                self.red_lives -= damage
            else:
                self.blue_lives -= damage
            reward = -(damage * 15.0)
            if split_used: reward += 5.0
            return reward, False
        else:
            reward = 15.0 - (5.0 if split_used else 0.0)
            return reward, True
    
    def _eat_other(self) -> float:
        """상대에게 먹이기"""
        if len(self.rounds) == 0:
            return -50.0
        
        sushi = self.rounds.pop(0)
        self.sushi_knowledge = -1
        split_used = self.is_split
        
        if sushi == RoundType.WASABI:
            damage = self.sushi_damage
            if self.current_turn == Player.RED:
                self.blue_lives -= damage
            else:
                self.red_lives -= damage
            reward = damage * 10.0
            if split_used: reward += 5.0
            return reward
        else:
            reward = -5.0 - (5.0 if split_used else 0.0)
            return reward
    
    def _use_greentea(self) -> float:
        """녹차 사용 (스시 제거)"""
        if not self._use_item('GreenTea'):
            return -50.0
        if len(self.rounds) == 0:
            return -50.0
        
        sushi = self.rounds.pop(0)
        self.sushi_knowledge = -1
        if self.is_split:
            self.is_split = False
            self.sushi_damage = 1
        
        return 5.0 if sushi == RoundType.WASABI else 1.0
    
    def _use_chopsticks(self) -> float:
        """젓가락 사용 (스시 확인)"""
        if not self._use_item('Chopsticks'):
            return -50.0
        if len(self.rounds) == 0:
            return -50.0
        
        self.sushi_knowledge = int(self.rounds[0])
        return 3.0
    
    def _use_pickle(self) -> float:
        """단무지 사용 (회복)"""
        if not self._use_item('Pickle'):
            return -50.0
        
        if self.current_turn == Player.RED:
            if self.red_lives < self.max_hp:
                self.red_lives = min(self.red_lives + 1, self.max_hp)
                return 5.0
            return -2.0
        else:
            if self.blue_lives < self.max_hp:
                self.blue_lives = min(self.blue_lives + 1, self.max_hp)
                return 5.0
            return -2.0
    
    def _use_kitchen_knife(self) -> float:
        """칼 사용 (2배)"""
        if not self._use_item('KitchenKnife'):
            return -50.0
        if self.is_split:
            return -50.0
        
        self.is_split = True
        self.sushi_damage = 2
        return 0.0
    
    def _use_soysauce(self) -> float:
        """간장종지 압수 (스킵)"""
        if not self._use_item('SoySauce'):
            return -50.0
        
        if self.current_turn == Player.RED:
            if self.blue_handcuffed: return -10.0
            self.blue_handcuffed = True
        else:
            if self.red_handcuffed: return -10.0
            self.red_handcuffed = True
        
        return 7.0
    
    def preprocess_state(self, state):
        """BLUE 관점으로 통일"""
        state = self.get_state()
        if state[0] == 1.0: # RED 턴
            flipped = np.copy(state)
            flipped[0] = 0.0
            flipped[4], flipped[5] = state[5], state[4]
            flipped[6:11], flipped[11:16] = state[11:16], state[6:11]
            flipped[18], flipped[19] = state[19], state[18]
            return flipped
        return state
