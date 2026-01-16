import numpy as np
import random
from enum import IntEnum
from typing import Tuple, Optional

class ActionType(IntEnum):
    ShootSelf = 0
    ShootOther = 1
    Drink = 2  # Energy Drink
    MagGlass = 3  # Magnifying Glass
    Cigar = 4
    Knife = 5
    Handcuffs = 6

class RoundType(IntEnum):
    LIVE = 1
    BLANK = 0

class Player(IntEnum):
    RED = 1
    BLUE = 0

class GameEnvironment:
    def __init__(self, max_hp: int = 4):
        self.max_hp = max_hp
        self.reset()
    
    def reset(self):
        """게임 초기화 및 새 라운드 시작"""
        # HP 초기화
        self.red_lives = self.max_hp
        self.blue_lives = self.max_hp
        
        # 새 라운드 시작
        self._start_new_round()
        
        # 턴 정보 (0: Blue, 1: Red)
        self.current_turn = Player.BLUE
        
        # 총 상태
        self.gun_damage = 1  # 기본 데미지
        self.is_sawed = False  # Knife 사용 여부
        
        # 수갑 상태
        self.red_handcuffed = False
        self.blue_handcuffed = False
        
        # Magnifying Glass로 확인한 총알 정보 (-1: 알 수 없음, 0: 빈 총알, 1: 실탄)
        self.bullet_knowledge = -1
        
        return self.get_state()
    
    def _start_new_round(self):
        """새 라운드 시작: 총알 생성 및 아이템 배분"""
        # 총알 생성: 1-4개의 실탄과 1-4개의 빈 총알
        num_live = random.randint(1, 4)
        num_blank = random.randint(1, 4)
        
        # 총알 리스트 생성 및 셔플
        self.rounds = [RoundType.LIVE] * num_live + [RoundType.BLANK] * num_blank
        random.shuffle(self.rounds)
        
        # 아이템 배분 (각 플레이어에게 2-4개)
        self.red_items = self._generate_items(random.randint(2, 4))
        self.blue_items = self._generate_items(random.randint(2, 4))
        
        # 총 상태 초기화
        self.gun_damage = 1
        self.is_sawed = False
        self.bullet_knowledge = -1
    
    def _generate_items(self, count: int) -> dict:
        """랜덤 아이템 생성"""
        items = {
            'Drink': 0,  # Energy Drink
            'MagGlass': 0,  # Magnifying Glass
            'Cigar': 0,
            'Knife': 0,
            'Handcuffs': 0
        }
        
        item_types = ['Drink', 'MagGlass', 'Cigar', 'Knife', 'Handcuffs']
        for _ in range(count):
            item = random.choice(item_types)
            items[item] += 1
        
        return items
    
    def get_state(self) -> np.ndarray:
        """현재 상태 벡터 반환 (20차원)"""
        state = []
        
        # 1. 턴 정보 (1차원)
        state.append(float(self.current_turn))
        
        # 2. 총알 정보 (3차원)
        total_rounds = len(self.rounds)
        total_live = sum(1 for r in self.rounds if r == RoundType.LIVE)
        total_blank = sum(1 for r in self.rounds if r == RoundType.BLANK)
        state.extend([float(total_rounds), float(total_live), float(total_blank)])
        
        # 3. 생명력 (2차원)
        state.extend([float(self.red_lives), float(self.blue_lives)])
        
        # 4. Red 아이템 (5차원)
        state.extend([
            float(self.red_items['Drink']),
            float(self.red_items['MagGlass']),
            float(self.red_items['Cigar']),
            float(self.red_items['Knife']),
            float(self.red_items['Handcuffs'])
        ])
        
        # 5. Blue 아이템 (5차원)
        state.extend([
            float(self.blue_items['Drink']),
            float(self.blue_items['MagGlass']),
            float(self.blue_items['Cigar']),
            float(self.blue_items['Knife']),
            float(self.blue_items['Handcuffs'])
        ])
        
        # 6. 총 상태 (2차원)
        state.extend([float(self.gun_damage), float(self.bullet_knowledge)])
        
        # 7. 수갑 상태 (2차원)
        state.extend([float(1 if self.blue_handcuffed else 0), float(1 if self.red_handcuffed else 0)])
        
        return np.array(state, dtype=np.float32)
    
    def _get_current_player_items(self) -> dict:
        """현재 플레이어의 아이템 반환"""
        return self.red_items if self.current_turn == Player.RED else self.blue_items
    
    def _use_item(self, item_name: str) -> bool:
        """아이템 사용 (보유 여부 확인 및 소모)"""
        items = self._get_current_player_items()
        if items[item_name] > 0:
            items[item_name] -= 1
            return True
        return False
    
    def _is_handcuffed(self) -> bool:
        """현재 플레이어가 수갑에 걸려있는지 확인"""
        return self.red_handcuffed if self.current_turn == Player.RED else self.blue_handcuffed
    
    def _skip_turn(self):
        """상대 턴 스킵 (수갑 효과)"""
        if self.current_turn == Player.RED:
            self.blue_handcuffed = False
        else:
            self.red_handcuffed = False
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        액션 실행
        Returns: (next_state, reward, done, info)
        """
        reward = 0.0
        done = False
        info = {}
        turn_continues = False  # 턴이 계속되는지 (빈 총알로 자신에게 쏠 때)
        
        # 수갑 체크: 수갑에 걸려있으면 턴 스킵
        if self._is_handcuffed():
            if self.current_turn == Player.RED:
                self.red_handcuffed = False
            else:
                self.blue_handcuffed = False
            # 턴 변경 (스킵)
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            # 스킵된 턴에서는 보상 없음
            return self.get_state(), 0.0, done, info
        
        action_type = ActionType(action)
        
        # 총알이 없으면 게임 종료
        if len(self.rounds) == 0:
            self._start_new_round()
            return self.get_state(), 0.0, done, info
        
        # 액션 처리
        if action_type == ActionType.ShootSelf:
            reward, turn_continues = self._shoot_self()
        elif action_type == ActionType.ShootOther:
            reward = self._shoot_other()
            turn_continues = False
        elif action_type == ActionType.Drink:
            reward = self._use_drink()
            turn_continues = False
        elif action_type == ActionType.MagGlass:
            reward = self._use_mag_glass()
            turn_continues = True  # Magnifying Glass는 턴을 끝내지 않음
        elif action_type == ActionType.Cigar:
            reward = self._use_cigar()
            turn_continues = False
        elif action_type == ActionType.Knife:
            reward = self._use_knife()
            turn_continues = False
        elif action_type == ActionType.Handcuffs:
            reward = self._use_handcuffs()
            turn_continues = False
        else:
            reward = -50.0  # Invalid action
            turn_continues = False
        
        # 게임 종료 체크 (액션 실행 후 HP 확인)
        if self.red_lives <= 0:
            done = True
            # Blue 승리
            if self.current_turn == Player.BLUE:
                # Blue가 상대를 죽여서 승리한 경우: Blue에게 +50
                reward += 50.0
            else:
                # Red가 자해로 죽은 경우: Red에게 -50 (패배)
                reward -= 50.0
        elif self.blue_lives <= 0:
            done = True
            # Red 승리
            if self.current_turn == Player.RED:
                # Red가 상대를 죽여서 승리한 경우: Red에게 +50
                reward += 50.0
            else:
                # Blue가 자해로 죽은 경우: Blue에게 -50 (패배)
                reward -= 50.0
        
        # 총알이 없으면 새 라운드 시작
        if len(self.rounds) == 0 and not done:
            self._start_new_round()
        
        # 턴 관리
        if not turn_continues and not done:
            # 턴 변경
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            
            # 수갑 체크: 변경된 턴의 플레이어가 수갑에 걸려있으면 스킵
            if self.current_turn == Player.RED and self.red_handcuffed:
                self.red_handcuffed = False
                # 다시 턴 변경 (스킵)
                self.current_turn = Player.BLUE
            elif self.current_turn == Player.BLUE and self.blue_handcuffed:
                self.blue_handcuffed = False
                # 다시 턴 변경 (스킵)
                self.current_turn = Player.RED
        
        # Knife 효과 초기화 (총알이 발사되거나 배출된 후)
        if action_type in [ActionType.ShootSelf, ActionType.ShootOther, ActionType.Drink]:
            if self.is_sawed and action_type == ActionType.Drink:
                self.is_sawed = False
                self.gun_damage = 1
            elif self.is_sawed and action_type in [ActionType.ShootSelf, ActionType.ShootOther]:
                self.is_sawed = False
                self.gun_damage = 1
        
        return self.get_state(), reward, done, info
    
    def _shoot_self(self) -> Tuple[float, bool]:
        """자신에게 쏘기"""
        if len(self.rounds) == 0:
            return -50.0, False
        
        bullet = self.rounds.pop(0)
        self.bullet_knowledge = -1  # 총알 사용 후 정보 초기화
        
        # Knife 사용 여부 확인 (사격 후 초기화되므로 미리 저장)
        knife_used = self.is_sawed
        
        if bullet == RoundType.LIVE:
            # 실탄: 데미지 받음
            damage = self.gun_damage
            if self.current_turn == Player.RED:
                self.red_lives -= damage
            else:
                self.blue_lives -= damage
            
            # 보상: -(데미지 × 15)
            reward = -(damage * 15.0)
            
            # Knife 사용 후 적중 시 추가 보상 (+5.0)
            if knife_used:
                reward += 5.0
            
            return reward, False
        else:
            # 빈 총알: 턴 유지
            # 보상: +15.0
            
            # Knife 사용 후 빗나감 시 페널티 (-5.0)
            if knife_used:
                reward = 15.0 - 5.0  # 총 10.0
            else:
                reward = 15.0
            
            return reward, True
    
    def _shoot_other(self) -> float:
        """상대에게 쏘기"""
        if len(self.rounds) == 0:
            return -50.0
        
        bullet = self.rounds.pop(0)
        self.bullet_knowledge = -1  # 총알 사용 후 정보 초기화
        
        # Knife 사용 여부 확인 (사격 후 초기화되므로 미리 저장)
        knife_used = self.is_sawed
        
        if bullet == RoundType.LIVE:
            # 실탄: 상대 데미지
            damage = self.gun_damage
            if self.current_turn == Player.RED:
                self.blue_lives -= damage
            else:
                self.red_lives -= damage
            
            # 보상: +(데미지 × 10)
            reward = damage * 10.0
            
            # Knife 사용 후 적중 시 추가 보상 (+5.0)
            if knife_used:
                reward += 5.0
            
            return reward
        else:
            # 빈 총알: 턴 넘김
            # 보상: -5.0
            
            # Knife 사용 후 빗나감 시 페널티 (-5.0)
            if knife_used:
                reward = -5.0 - 5.0  # 총 -10.0
            else:
                reward = -5.0
            
            return reward
    
    def _use_drink(self) -> float:
        """Energy Drink 사용 (총알 제거)"""
        if not self._use_item('Drink'):
            return -50.0
        
        if len(self.rounds) == 0:
            return -50.0
        
        bullet = self.rounds.pop(0)
        self.bullet_knowledge = -1
        
        # Knife 효과 초기화
        if self.is_sawed:
            self.is_sawed = False
            self.gun_damage = 1
        
        # 보상: 실탄 배출 시 +5.0, 빈 총알 배출 시 +1.0
        if bullet == RoundType.LIVE:
            return 5.0
        else:
            return 1.0
    
    def _use_mag_glass(self) -> float:
        """Magnifying Glass 사용 (다음 총알 확인) - 턴을 끝내지 않음"""
        if not self._use_item('MagGlass'):
            return -50.0
        
        if len(self.rounds) == 0:
            return -50.0
        
        bullet = self.rounds[0]
        self.bullet_knowledge = int(bullet)
        
        # 보상: +3.0 (정보 획득)
        # 턴을 끝내지 않으므로 turn_continues 플래그는 step에서 처리
        return 3.0
    
    def _use_cigar(self) -> float:
        """Cigar 사용 (체력 회복)"""
        if not self._use_item('Cigar'):
            return -50.0
        
        if self.current_turn == Player.RED:
            if self.red_lives < self.max_hp:
                self.red_lives = min(self.red_lives + 1, self.max_hp)
                return 5.0  # 유효한 회복
            else:
                return -2.0  # 아이템 낭비
        else:
            if self.blue_lives < self.max_hp:
                self.blue_lives = min(self.blue_lives + 1, self.max_hp)
                return 5.0  # 유효한 회복
            else:
                return -2.0  # 아이템 낭비
    
    def _use_knife(self) -> float:
        """Knife 사용 (데미지 2배)"""
        if not self._use_item('Knife'):
            return -50.0
        
        if self.is_sawed:
            return -50.0  # 이미 사용 중
        
        self.is_sawed = True
        self.gun_damage = 2
        
        # Knife 사용 자체에는 보상 없음 (실제 사격 시 보상 계산)
        return 0.0
    
    def _use_handcuffs(self) -> float:
        """Handcuffs 사용 (상대 턴 스킵)"""
        if not self._use_item('Handcuffs'):
            return -50.0
        
        if self.current_turn == Player.RED:
            if self.blue_handcuffed:
                return -10.0  # 이미 걸려있음
            self.blue_handcuffed = True
        else:
            if self.red_handcuffed:
                return -10.0  # 이미 걸려있음
            self.red_handcuffed = True
        
        return 7.0  # 정상 사용
    
