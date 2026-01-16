import numpy as np
import random

# ==========================================
# [행동 인덱스 정의]
# ==========================================
ACTION_SELF = 0   # 자신에게 발사
ACTION_OPP = 1    # 상대에게 발사
ITEM_BEER = 2     # 맥주 (탄 제거)
ITEM_LENS = 3     # 돋보기 (탄 확인)
ITEM_CIG = 4      # 담배 (체력 회복)
ITEM_KNIFE = 5    # 칼 (데미지 2배)
ITEM_CUFF = 6     # 수갑 (턴 스킵)
# ==========================================

class BuckshotEnv:
    def __init__(self, reward_config=None):
        default_rewards = {
            "final_win": 1.2, "round_win": 0.3, "dmg_dealt": 0.1, 
            "dmg_taken": -0.1, "heal": 0.05, "item_bad": -2, "lose": -2.4
        }
        self.rewards = default_rewards if reward_config is None else reward_config
        self.reset()

    def reset(self):
        self.round = 1
        self.max_rounds = 3
        self.red_lives = 4
        self.blue_lives = 4

        self.red_items = [0] * 5
        self.blue_items = [0] * 5
        self.shells = []
        self.damage = 1
        self.knowledge = 2
        self.red_cuffed = False
        self.blue_cuffed = False
        self.turn = random.randint(0, 1)
        self._new_round_setup()
        return self.get_state()

    def _new_round_setup(self):
        num_real = random.randint(1, 5)
        num_empty = random.randint(1, 5)
        self.shells = [1]*num_real + [0]*num_empty
        random.shuffle(self.shells)
        self._add_items(self.red_items)
        self._add_items(self.blue_items)
        self.damage = 1
        self.knowledge = 2
        self.red_cuffed = False
        self.blue_cuffed = False

    def _add_items(self, items):
        count = 4
        for _ in range(count):
            if sum(items) >= 8: break
            items[random.randint(0, 4)] += 1

    def get_state(self):
        state = [
            self.turn, len(self.shells), self.shells.count(1), self.shells.count(0),
            self.red_lives, self.blue_lives,
            *self.red_items, *self.blue_items,
            self.damage, self.knowledge,
            int(self.blue_cuffed), int(self.red_cuffed)
        ]
        return np.array(state, dtype=np.float32)

    def step(self, action):
        is_red = (self.turn == 1)
        if is_red: my_items = self.red_items
        else: my_items = self.blue_items
        
        reward = 0
        done = False
        turn_end = False
        R = self.rewards

        if action == ACTION_SELF:
            if not self.shells: self._new_round_setup()
            shell = self.shells.pop(0)
            if shell == 1:
                self._apply_damage(is_red, self_hit=True)
                reward = R["dmg_taken"]
                turn_end = True
            else:
                reward = R["dmg_dealt"] * 0.5
                turn_end = False
            self._reset_modifiers()

        elif action == ACTION_OPP:
            if not self.shells: self._new_round_setup()
            shell = self.shells.pop(0)
            if shell == 1:
                self._apply_damage(is_red, self_hit=False)
                reward = R["dmg_dealt"]
            else:
                reward = 0
            turn_end = True
            self._reset_modifiers()

        elif action >= ITEM_BEER: 
            idx = action - 2 
            
            if my_items[idx] > 0:
                my_items[idx] -= 1
                self._use_item(idx, is_red)
                if idx == (ITEM_CIG - 2): reward = R["heal"]
                turn_end = False # 아이템 쓰면 턴 유지 (정상)
            else:
                reward = R["item_bad"]
                turn_end = True # <--- 🔥 [여기가 핵심 수정] 강제 턴 종료! 🔥

        if turn_end:
            opp_cuffed = self.blue_cuffed if is_red else self.red_cuffed
            if opp_cuffed:
                if is_red: self.blue_cuffed = False
                else: self.red_cuffed = False
            else:
                self.turn = 1 - self.turn

        if not self.shells: self._new_round_setup()

        winner = self._check_round_end()
        if winner is not None:
            if self.round >= self.max_rounds:
                done = True
                if is_red == (winner == 1): reward = R["final_win"]
                else: reward = R["lose"]
            else:
                self.round += 1
                self._new_round_setup()
                self.red_lives = 4; self.blue_lives = 4
                if is_red == (winner == 1): reward = R["round_win"]
                else: reward = R["lose"] * 0.5

        return self.get_state(), reward, done

    def _apply_damage(self, is_attacker_red, self_hit):
        dmg = self.damage
        target_is_red = is_attacker_red if self_hit else not is_attacker_red
        if target_is_red: self.red_lives -= dmg
        else: self.blue_lives -= dmg

    def _reset_modifiers(self):
        self.damage = 1
        self.knowledge = 2

    def _use_item(self, idx, is_red):
        if idx == 0 and self.shells: self.shells.pop(0)
        elif idx == 1 and self.shells: self.knowledge = self.shells[0]
        elif idx == 2:
            if is_red: self.red_lives = min(4, self.red_lives + 1)
            else: self.blue_lives = min(4, self.blue_lives + 1)
        elif idx == 3: self.damage = 2
        elif idx == 4:
            if is_red: self.blue_cuffed = True
            else: self.red_cuffed = True

    def _check_round_end(self):
        if self.red_lives <= 0: return 0 
        if self.blue_lives <= 0: return 1 
        return None