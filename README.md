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

