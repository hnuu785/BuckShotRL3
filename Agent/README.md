# 프메 7팀 - 성재네 초밥집

# 모델 Dueling DQN

# 상태 (Input)
상태 벡터 구성 (총 20차원)

1. 턴 정보 (1차원)
- 0: Blue 턴, 1: Red 턴
2. 총알 정보 (3차원)
- 총 총알 개수 (rounds.Count)
- 실탄 개수 (totalReal)
- 빈 총알 개수 (totalEmpty)
3. 생명력 (2차원)
- Red 생명력 (redLives)
- Blue 생명력 (blueLives)
4. Red 아이템 (5차원)
- Energy Drink (ED)
- Magnifying Glass (MG)
- Cigar (C)
- Knife (K)
- Handcuffs (HC)
5. Blue 아이템 (5차원)
- Energy Drink (ED)
- Magnifying Glass (MG)
- Cigar (C)
- Knife (K)
- Handcuffs (HC)
6. 총 상태 (2차원)
- 총 데미지 (gunDamage: 1 또는 2)
- 다음 총알 정보 (knowledge: -1=알 수 없음, 0=빈 총알, 1=실탄, 2=미확인)
7. 수갑 상태 (2차원)
- Blue 수갑 상태 (blueCuff: 0 또는 1)
- Red 수갑 상태 (redCuff: 0 또는 1)

총 20차원 벡터로, Unity에서 쉼표로 구분된 문자열로 전송되고 Python에서 파싱해 사용합니다.

# 행동 (Output)
## 유니티
public enum ActionType
{
    ShootSelf = 1,
    ShootOther = 2,
    Drink = 3,
    MagGlass = 4,
    Cigar = 5,
    Knife = 6,
    Handcuffs = 7
}

## 파이썬
인덱스 액션 이름 설명
0	ShootSelf	자신에게 쏘기
1	ShootOther	상대에게 쏘기
2	Drink	Energy Drink 사용 (총알 제거)
3	MagGlass	Magnifying Glass 사용 (다음 총알 확인)
4	Cigar	Cigar 사용 (체력 회복)
5	Knife	Knife 사용 (데미지 2배)
6	Handcuffs	Handcuffs 사용 (상대 턴 스킵)

# 보상
1. 총 쏘기 보상 요약:
상황	보상	추가 조건
자신에게 실탄 쏘기	-3	데미지 2배면 -2 추가 (총 -5)
상대에게 실탄 쏘기	+5	데미지 2배면 +10 추가 (총 +15)
자신에게 빈 총알 쏘기	+3	턴 유지 (전략적 이점)
상대에게 빈 총알 쏘기	-3	턴 넘김 (불리함)

2. 아이템 사용 보상:
아이템	보상 조건	보상 값
Energy Drink	사용 시	0 (보상 없음, 총알 제거 효과만)
Magnifying Glass	유용한 정보 획득	+1
쓸모없는 상황 (마지막 총알, 이미 알고 있음 등)	-1
Cigar	체력이 4일 때 (최대)	-1
체력 회복 시	+0.5
Knife	실탄을 알고 있을 때 사용	+2
빈 총알이거나 이미 사용 중	-1
Handcuffs	정상 사용	+1
이미 수갑이 걸려있을 때	-0.5

3. 잘못된 액션 패널티
보유하지 않은 아이템 사용 시 패널티
Blue 플레이어: -50 (기본) + scalar (반복 시 증가)
Red 플레이어: -10 (기본) + scalar

보상 범위 요약
최대 보상: +15 (상대에게 데미지 2배 실탄)
최소 보상: -50 이상 (잘못된 아이템 사용, 반복 시 더 감소)
보상은 즉시 보상(immediate reward) 방식으로, 각 액션 후 즉시 계산되어 에이전트에 전달됩니다.

# 셀프 플레이 (Self-Play)

셀프 플레이는 Unity 환경 없이 파이썬으로만 게임을 시뮬레이션하여 두 에이전트가 서로 게임을 하며 학습하는 방식입니다.

## 파일 구조

- `game_env.py`: 게임 환경 클래스 (게임 로직, 상태 관리, 보상 계산)
- `self_play.py`: 셀프 플레이 메인 스크립트
- `test_game_env.py`: 게임 환경 테스트 스크립트

## 사용법

### 기본 사용

```bash
python self_play.py
```

### 옵션 설정

```bash
python self_play.py --num-games 10000 --checkpoint-interval 100 --save-dir Agents
```

### 주요 옵션

- `--num-games`: 학습할 게임 수 (기본값: 10000)
- `--checkpoint-interval`: 체크포인트 저장 간격 (기본값: 100)
- `--save-dir`: 모델 저장 디렉토리 (기본값: Agents)
- `--no-load`: 체크포인트를 로드하지 않음
- `--epsilon`: 초기 엡실론 값 (기본값: 1.0)
- `--lr`: 학습률 (기본값: 4e-4)
- `--max-hp`: 최대 HP (기본값: 4)

### 예제

```bash
# 5000게임 학습, 50게임마다 체크포인트 저장
python self_play.py --num-games 5000 --checkpoint-interval 50

# 체크포인트 없이 처음부터 시작
python self_play.py --num-games 10000 --no-load

# 커스텀 학습률과 엡실론
python self_play.py --num-games 10000 --lr 1e-4 --epsilon 0.5
```

## 게임 환경 테스트

게임 환경이 제대로 작동하는지 테스트:

```bash
python test_game_env.py
```

## 체크포인트

체크포인트는 지정된 간격마다 자동으로 저장됩니다:
- 모델 파일: `Agents/buckshot_eval`, `Agents/buckshot_next`
- 통계 파일: `Agents/training_stats.npz`
- 학습 그래프: `Agents/self_play_red_learning.png`, `Agents/self_play_blue_learning.png`

## 보상 시스템

셀프 플레이에서 사용하는 보상 시스템은 `train_env.mdc` 규칙을 따릅니다:

### 기본 보상
- 승리: +50.0
- 패배: -50.0

### 사격 보상
- 상대에게 실탄 적중: +(데미지 × 10), Knife 사용 시 추가 +5.0
- 상대에게 빈 총알: -5.0, Knife 사용 시 추가 -5.0
- 자신에게 실탄 적중: -(데미지 × 15), Knife 사용 시 추가 +5.0
- 자신에게 빈 총알: +15.0, Knife 사용 시 -5.0 (총 10.0)

### 아이템 보상
- Energy Drink (실탄 배출): +5.0
- Energy Drink (빈 총알 배출): +1.0
- Cigar (체력 회복): +5.0
- Cigar (체력 최대): -2.0
- Handcuffs (정상 사용): +7.0
- Handcuffs (이미 걸려있음): -10.0
- Magnifying Glass: +3.0

### 페널티
- 잘못된 액션 (아이템 없음, 총알 없음 등): -50.0
