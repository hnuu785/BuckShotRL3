import numpy as np
from game_env import Player, ActionType, RoundType


# ==============================================================================
# [선생님 AI] GameEnvironment 전용 Rule-Based 로직
# ==============================================================================
def get_opponent_action(state, difficulty=4):
    """
    제공된 레벨 테이블 이미지 로직 반영:
    - Lv.0: 사격/아이템 모두 랜덤
    - Lv.1: 실탄 비율 사격, 아이템 사용 X
    - Lv.2: 랜덤 사격, 담배/수갑/돋보기 사용
    - Lv.3: 확인된 탄 정보 위주 사격, 담배/수갑/돋보기 사용
    - Lv.4: 실탄 비율/정보 사격, 모든 아이템 우선 사용
    """
    # 상태 벡터 인덱스 추출 (20차원 기준)
    turn = state[0]
    num_real = state[2]
    num_empty = state[3]
    knowledge = state[17]  # -1: 모름, 0: 빈탄, 1: 실탄
    
    is_red = (turn == 1.0)
    my_items = state[6:11] if is_red else state[11:16]
    # 상대 수갑: Red 턴이면 상대=Blue → state[18], Blue 턴이면 상대=Red → state[19]
    opp_cuffed = state[18] if is_red else state[19]
    my_hp = state[4] if is_red else state[5]

    # -------------------------------------------------------
    # 1. 아이템 사용 로직 (레벨별 분기)
    # -------------------------------------------------------
    if difficulty == 0:
        # Lv.0: 아이템 사용도 랜덤 (운 좋으면 사용)
        if np.random.random() < 0.3:
            return np.random.randint(2, 7)

    elif difficulty == 1:
        # Lv.1: 아이템 사용 X (바로 사격 단계로 진행)
        pass

    elif difficulty in [2, 3]:
        # Lv.2, Lv.3: 담배(4), 수갑(6), 돋보기(3) 사용
        if my_hp < 4 and my_items[2] > 0: return 4  # 담배 (Cigar)
        if not opp_cuffed and my_items[4] > 0: return 6  # 수갑 (Handcuffs)
        if knowledge == -1 and my_items[1] > 0: return 3  # 돋보기 (MagGlass)

    elif difficulty == 4:
        # Lv.4: 모든 아이템 우선적으로 사용
        if my_hp < 4 and my_items[2] > 0: return 4  # 담배
        if knowledge == -1 and my_items[1] > 0: return 3  # 돋보기
        if not opp_cuffed and my_items[4] > 0: return 6  # 수갑
        if my_items[0] > 0: return 2  # 맥주 (Drink)
        if my_items[3] > 0 and state[16] == 1.0: return 5  # 칼 (Knife)

    # -------------------------------------------------------
    # 2. 사격 로직 (레벨별 분기)
    # -------------------------------------------------------
    # [Lv.0, Lv.2]: 사격 random
    if difficulty in [0, 2]:
        return np.random.choice([0, 1])

    # [Lv.1]: 실탄 비율 확인해서 유리한 쪽으로 사격
    elif difficulty == 1:
        return 1 if num_real >= num_empty else 0

    # [Lv.3]: 총탄 종류 확인되면 그에 맞춰 사격 (기본은 random)
    elif difficulty == 3:
        if knowledge == 1.0: return 1  # 실탄 확인됨 -> 상대 사격
        if knowledge == 0.0: return 0  # 빈탄 확인됨 -> 자신 사격
        return np.random.choice([0, 1])  # 모르면 랜덤

    # [Lv.4]: 확인되면 맞춤 사격, 모르면 실탄 비율로 사격
    elif difficulty == 4:
        if knowledge == 1.0: return 1
        if knowledge == 0.0: return 0
        return 1 if num_real >= num_empty else 0

    return 1 # 기본값 (상대 사격)