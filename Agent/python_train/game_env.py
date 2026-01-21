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
        
        # 아이템 초기화 (게임 시작 시에만 새로 생성)
        # 빈 딕셔너리로 시작하여 _start_new_round()에서 새로 생성되도록 함
        self.red_items = {
            'Drink': 0,
            'MagGlass': 0,
            'Cigar': 0,
            'Knife': 0,
            'Handcuffs': 0
        }
        self.blue_items = {
            'Drink': 0,
            'MagGlass': 0,
            'Cigar': 0,
            'Knife': 0,
            'Handcuffs': 0
        }
        
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
        """
        새 라운드 시작: 총알 생성 및 아이템 배분
        주의: 
        - 체력(HP)은 회복되지 않으며 유지됩니다. 체력은 게임 시작 시에만 초기화됩니다.
        - 수갑(Handcuffs) 상태는 유지됩니다. 턴 변경 시 자동으로 체크되어 상대의 첫 턴이 스킵됩니다.
        - 아이템은 이전 라운드에서 유지되며, 새 라운드 시작 시 2-4개가 추가됩니다.
        """
        # 총알 생성: 1-4개의 실탄과 1-4개의 빈 총알
        num_live = random.randint(1, 4)
        num_blank = random.randint(1, 4)
        
        # 총알 리스트 생성 및 셔플
        self.rounds = [RoundType.LIVE] * num_live + [RoundType.BLANK] * num_blank
        random.shuffle(self.rounds)
        
        # 아이템 배분 (각 플레이어에게 2-4개 추가, 인벤토리 제한: 최대 8개)
        # 이전 라운드의 아이템은 유지되고, 새로운 아이템만 추가됩니다
        self.red_items = self._add_items_to_inventory(self.red_items, random.randint(2, 4))
        self.blue_items = self._add_items_to_inventory(self.blue_items, random.randint(2, 4))
        
        # 총 상태 초기화
        self.gun_damage = 1
        self.is_sawed = False
        self.bullet_knowledge = -1
    
    def _get_total_item_count(self, items: dict) -> int:
        """아이템 딕셔너리의 총 아이템 개수 반환"""
        return sum(items.values())
    
    def _generate_items(self, count: int) -> dict:
        """
        랜덤 아이템 생성 (인벤토리 제한: 최대 8개)
        게임 초기화 시에만 사용됩니다.
        """
        INVENTORY_LIMIT = 8
        
        items = {
            'Drink': 0,  # Energy Drink
            'MagGlass': 0,  # Magnifying Glass
            'Cigar': 0,
            'Knife': 0,
            'Handcuffs': 0
        }
        
        # 요청된 개수가 인벤토리 제한을 초과하면 제한으로 조정
        count = min(count, INVENTORY_LIMIT)
        
        item_types = ['Drink', 'MagGlass', 'Cigar', 'Knife', 'Handcuffs']
        for _ in range(count):
            # 인벤토리가 가득 찬 경우 중단
            if self._get_total_item_count(items) >= INVENTORY_LIMIT:
                break
            item = random.choice(item_types)
            items[item] += 1
        
        return items
    
    def _add_items_to_inventory(self, existing_items: dict, count: int) -> dict:
        """
        기존 아이템에 새 아이템 추가 (인벤토리 제한: 최대 8개)
        이전 라운드의 아이템은 유지되고, 새로운 아이템만 추가됩니다.
        만약 기존 아이템이 없으면(게임 시작 시) 새로 생성합니다.
        """
        INVENTORY_LIMIT = 8
        
        # 기존 아이템 복사
        items = existing_items.copy()
        
        # 현재 아이템 개수 확인
        current_count = self._get_total_item_count(items)
        
        # 게임 시작 시 (아이템이 없을 때) 새로 생성
        if current_count == 0:
            return self._generate_items(count)
        
        # 추가 가능한 아이템 개수 계산
        available_slots = INVENTORY_LIMIT - current_count
        
        # 추가할 아이템 개수 결정
        items_to_add = min(count, available_slots)
        
        # 아이템 추가
        item_types = ['Drink', 'MagGlass', 'Cigar', 'Knife', 'Handcuffs']
        for _ in range(items_to_add):
            # 인벤토리가 가득 찬 경우 중단
            if self._get_total_item_count(items) >= INVENTORY_LIMIT:
                break
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
        
        # 액션 처리
        if action_type == ActionType.ShootSelf:
            reward, turn_continues = self._shoot_self()
        elif action_type == ActionType.ShootOther:
            reward = self._shoot_other()
            turn_continues = False
        elif action_type == ActionType.Drink:
            reward = self._use_drink()
            turn_continues = True  # Energy Drink는 턴을 끝내지 않음
        elif action_type == ActionType.MagGlass:
            reward = self._use_mag_glass()
            turn_continues = True  # Magnifying Glass는 턴을 끝내지 않음
        elif action_type == ActionType.Cigar:
            reward = self._use_cigar()
            turn_continues = True  # Cigar는 턴을 끝내지 않음
        elif action_type == ActionType.Knife:
            reward = self._use_knife()
            turn_continues = True   # Knife는 턴을 끝내지 않음
        elif action_type == ActionType.Handcuffs:
            reward = self._use_handcuffs()
            turn_continues = True  # Handcuffs는 턴을 끝내지 않음
        else:
            reward = -50.0  # Invalid action
            turn_continues = True  # Invalid action does not end turn
        
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
        # 기본 규칙: 상대의 다음 턴이 실제로 스킵될 때만 수갑을 해제
        # 이 로직 하나로 모든 Handcuffs 케이스를 처리:
        # - Shoot Self (Live) + Handcuffs: 턴 변경 → 상대 턴 스킵 → 다시 자신 턴으로 돌아옴
        # - Shoot Self (Blank) + Handcuffs: 턴 변경 없음 → 수갑 상태 유지
        # - Magazine Empty + Handcuffs: 새 라운드 후 첫 턴 변경 시 자동 처리
        if not turn_continues and not done:
            # 턴 변경
            self.current_turn = Player.BLUE if self.current_turn == Player.RED else Player.RED
            
            # 수갑 체크: 변경된 턴의 플레이어가 수갑에 걸려있으면 스킵
            if self.current_turn == Player.RED and self.red_handcuffed:
                self.red_handcuffed = False  # 수갑 해제 (상대 턴이 스킵되었으므로)
                # 다시 턴 변경 (스킵)
                self.current_turn = Player.BLUE
            elif self.current_turn == Player.BLUE and self.blue_handcuffed:
                self.blue_handcuffed = False  # 수갑 해제 (상대 턴이 스킵되었으므로)
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
        """
        자신에게 쏘기
        Returns: (reward, turn_continues)
        
        기본 규칙:
        - 실탄: 데미지 받음, 턴 종료
        - 빈 총알: 턴 유지 (상대 턴으로 넘어가지 않음)
        
        Handcuffs는 턴 변경 시 자동으로 처리됨:
        - 실탄으로 쏘면 턴이 끝나고 상대 턴으로 넘어감 → 상대가 수갑에 걸려있으면 스킵 → 다시 자신 턴으로 돌아옴
        - 빈 총알로 쏘면 턴이 유지됨 → 턴 변경이 없으므로 수갑 상태도 유지됨
        """
        if len(self.rounds) == 0:
            return -50.0, False
        
        bullet = self.rounds.pop(0)
        self.bullet_knowledge = -1  # 총알 사용 후 정보 초기화
        
        # Knife 사용 여부 확인 (사격 후 초기화되므로 미리 저장)
        knife_used = self.is_sawed
        
        if bullet == RoundType.LIVE:
            # 실탄: 데미지 받음, 턴 종료
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
            
            # 턴 종료 (상대 턴으로 넘어감, 턴 변경 시 수갑 체크가 자동으로 처리됨)
            return reward, False
        else:
            # 빈 총알: 턴 유지
            # 보상: +15.0
            
            # Knife 사용 후 빗나감 시 페널티 (-5.0)
            # 규칙: 빈 총알이면 is_sawed 효과는 소모되고 초기화됨
            if knife_used:
                self.is_sawed = False
                self.gun_damage = 1
                reward = 15.0 - 5.0  # 총 10.0
            else:
                reward = 15.0
            
            # 턴 유지 (상대 턴으로 넘어가지 않으므로 수갑 상태도 유지됨)
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
    
        # ==============================================================================
    # [유틸리티] 상태 전처리: 모든 상황을 BLUE(0.0) 관점으로 통일
    # ==============================================================================
    def preprocess_state(self, state):
        """
        현재 턴이 RED(1.0)일 경우 BLUE(0.0) 관점으로 데이터를 반전시킵니다.
        에이전트는 항상 '내가 BLUE(0번 플레이어)'라고 생각하고 학습할 수 있습니다.
        """
        state = self.get_state()

        if state[0] == 1.0: # RED 플레이어 턴인 경우
            flipped = np.copy(state)
            flipped[0] = 0.0                                  # 턴 주체를 나(0.0)로 설정
            flipped[4], flipped[5] = state[5], state[4]       # HP 스왑 (내 HP <-> 상대 HP)
            flipped[6:11], flipped[11:16] = state[11:16], state[6:11] # 아이템 스왑
            flipped[18], flipped[19] = state[19], state[18]   # 수갑 상태 스왑
            return flipped
        return state
    
