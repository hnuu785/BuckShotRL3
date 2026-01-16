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

# Buckshot AI Agent - Unity 6.3 LTS

이 디렉토리는 Unity 6.3 LTS에 최적화된 Buckshot 게임용 Python 기반 AI 에이전트를 포함합니다.

## Unity 6.3 LTS 개선 사항

### 1. 향상된 오류 처리
- 연결 타임아웃 처리 추가
- 개선된 오류 메시지 및 로깅
- 우아한 연결 해제 처리

### 2. 성능 최적화
- 버퍼 크기를 1024에서 4096 바이트로 증가
- 더 나은 응답성을 위한 소켓 타임아웃 추가
- 데이터 파싱 효율성 개선

### 3. 연결 안정성
- Unity에서 자동 재연결 로직
- 연결 상태 모니터링
- 네트워크 중단 처리 개선

### 4. 크로스 플랫폼 호환성
- Windows, macOS, Linux에서 작동
- 표준 TCP 소켓 구현
- 플랫폼별 의존성 없음

## 설정

1. Python 가상 환경 생성:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치:
```bash
pip install torch numpy matplotlib
```

3. 에이전트 실행:
```bash
python agent.py
```

## 통신 프로토콜

에이전트는 `localhost:12345`에서 TCP 소켓을 통해 Unity와 통신합니다.

### 명령어:
- `get_state` - 현재 게임 상태 요청
- `play_step:<action>` - 액션 실행 (0-6)
- `reset` - 게임 리셋

### 상태 형식:
쉼표로 구분된 값으로 다음을 나타냅니다:
1. 턴 (1=빨강, 0=파랑)
2. 총알 개수
3. 실탄 개수
4. 빈 총알 개수
5. 빨강 생명력
6. 파랑 생명력
7-11. 빨강 아이템 (ED, MG, C, K, HC)
12-16. 파랑 아이템 (ED, MG, C, K, HC)
17. 총 데미지
18. 지식 상태
19. 파랑 수갑 상태 (0/1)
20. 빨강 수갑 상태 (0/1)

## 참고 사항

- 에이전트는 강화 학습을 위해 Dueling DQN (Double Deep Q-Network)을 사용합니다
- 모델 체크포인트는 `Agents/` 폴더에 저장됩니다
- 훈련 진행 상황이 로깅되고 시각화됩니다

