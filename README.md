<div align="center">

# 🎰 Buckshot Roulette AI Agent

**프메 7팀 · 성재네 초밥집**

*Unity 6.3 LTS · Dueling DQN · 강화학습*

[📌 프로젝트 판넬 보러가기](https://prometheus-ai.net/project/57) · [프로메테우스](https://prometheus-ai.net)

---

</div>

## 📋 목차

- [개요](#-개요)
- [팀 문서](#-팀-문서)
- [모델](#-모델)
- [상태 (Input)](#-상태-input)
- [행동 (Output)](#-행동-output)
- [보상 체계](#-보상-체계)
- [설정 및 실행](#-설정-및-실행)
- [통신 프로토콜](#-통신-프로토콜)
- [참고 사항](#-참고-사항)

---

## 🎯 개요

이 프로젝트는 **Buckshot Roulette** 게임용 Python 기반 AI 에이전트입니다.  
Unity 6.3 LTS 환경과 TCP 소켓으로 연동하며, **Dueling DQN**으로 학습합니다.

| 항목 | 설명 |
|------|------|
| **플랫폼** | Unity 6.3 LTS |
| **에이전트** | Python (PyTorch) |
| **연결** | TCP `localhost:12345` |

---

## 📄 팀 문서

- **PDF**: README에서는 PDF를 화면 안에 임베드할 수 없고, **링크**만 걸 수 있습니다. 클릭 시 새 탭에서 열리거나 다운로드됩니다.  
  → PDF를 저장소에 두었다면: `[팀7 문서 보기](팀7.pdf)` 처럼 링크 추가.
- **이미지**: 내용을 README에 바로 보이게 하려면 PDF 대신 **PNG/JPG로 변환**해 넣는 게 좋습니다.  
  → 예: `![팀7 자료](docs/팀7.png)` (필요한 페이지만 이미지로 저장 후 `docs/` 등에 두기)

<!-- PDF 링크 예시 (파일 추가 후 경로 수정):
[📎 팀7 문서 (PDF)](팀7.pdf)
-->

<!-- 이미지로 넣을 경우 예시:
![팀7 자료](docs/팀7.png)
-->

---

## 🧠 모델

**Dueling DQN** (Double Deep Q-Network)  
상태 벡터를 입력받아 7가지 행동 중 Q값이 최대인 액션을 선택합니다.

---

## 📥 상태 (Input)

총 **20차원** 벡터. Unity에서 쉼표로 구분된 문자열로 전송되고, Python에서 파싱해 사용합니다.

| 구분 | 차원 | 설명 |
|------|------|------|
| **1. 턴** | 1 | `0` = Blue 턴, `1` = Red 턴 |
| **2. 총알** | 3 | 총 개수 (`rounds.Count`), 실탄(`totalReal`), 빈 총알(`totalEmpty`) |
| **3. 생명력** | 2 | Red 생명력, Blue 생명력 |
| **4. Red 아이템** | 5 | ED, MG, C, K, HC |
| **5. Blue 아이템** | 5 | ED, MG, C, K, HC |
| **6. 총 상태** | 2 | 데미지(1/2), 다음 총알 정보(`knowledge`: -1/0/1/2) |
| **7. 수갑** | 2 | Blue 수갑(0/1), Red 수갑(0/1) |

- **아이템 약어**: ED=Energy Drink, MG=Magnifying Glass, C=Cigar, K=Knife, HC=Handcuffs  
- **knowledge**: `-1`=알 수 없음, `0`=빈 총알, `1`=실탄, `2`=미확인

---

## 📤 행동 (Output)

### Unity (C#)

```csharp
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
```

### Python 인덱스 매핑

| 인덱스 | 액션 | 설명 |
|--------|------|------|
| 0 | ShootSelf | 자신에게 쏘기 |
| 1 | ShootOther | 상대에게 쏘기 |
| 2 | Drink | Energy Drink (총알 제거) |
| 3 | MagGlass | Magnifying Glass (다음 총알 확인) |
| 4 | Cigar | Cigar (체력 회복) |
| 5 | Knife | Knife (데미지 2배) |
| 6 | Handcuffs | Handcuffs (상대 턴 스킵) |

---

## 🏆 보상 체계

보상은 **즉시 보상(immediate reward)** 방식으로, 각 액션 직후 계산되어 에이전트에 전달됩니다.

### 1. 사격 보상

| 상황 | 보상 | 비고 |
|------|------|------|
| 자신에게 실탄 | -3 | 데미지 2배면 -2 추가 (총 -5) |
| 상대에게 실탄 | +5 | 데미지 2배면 +10 추가 (총 +15) |
| 자신에게 빈 총알 | +3 | 턴 유지 (전략적 이점) |
| 상대에게 빈 총알 | -3 | 턴 넘김 (불리함) |

### 2. 아이템 사용 보상

| 아이템 | 조건 | 보상 |
|--------|------|------|
| Energy Drink | 사용 시 | 0 (총알 제거만) |
| Magnifying Glass | 유용한 정보 획득 | +1 |
| Magnifying Glass | 쓸모없는 상황 | -1 |
| Cigar | 체력 최대(4)일 때 | -1 |
| Cigar | 체력 회복 시 | +0.5 |
| Knife | 실탄 알 때 사용 | +2 |
| Knife | 빈 총알/이미 사용 중 | -1 |
| Handcuffs | 정상 사용 | +1 |
| Handcuffs | 이미 수갑 걸림 | -0.5 |

### 3. 잘못된 액션 패널티

| 대상 | 기본 패널티 | 비고 |
|------|-------------|------|
| Blue 플레이어 | -50 | 반복 시 scalar 추가 |
| Red 플레이어 | -10 | 반복 시 scalar 추가 |

**보상 범위**: 최대 +15 (상대에게 2배 실탄) ~ 최소 -50 이하 (무효 액션 반복 시 더 감소)

---

## ⚙️ 설정 및 실행

### 1. 가상 환경

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install torch numpy matplotlib
```

### 3. 에이전트 실행

```bash
python agent.py
```

### Unity 6.3 LTS 관련

| 항목 | 내용 |
|------|------|
| **오류 처리** | 연결 타임아웃, 개선된 로깅, 우아한 연결 해제 |
| **성능** | 버퍼 4096 바이트, 소켓 타임아웃, 파싱 효율 개선 |
| **연결** | 자동 재연결, 연결 상태 모니터링 |
| **호환성** | Windows, macOS, Linux · 표준 TCP |

---

## 🔌 통신 프로토콜

**주소**: `localhost:12345` (TCP)

### 명령어

| 명령 | 설명 |
|------|------|
| `get_state` | 현재 게임 상태 요청 |
| `play_step:<action>` | 액션 실행 (action: 0~6) |
| `reset` | 게임 리셋 |

### 상태 문자열 형식 (쉼표 구분)

| 순서 | 의미 |
|------|------|
| 1 | 턴 (0=파랑, 1=빨강) |
| 2–4 | 총알 개수, 실탄, 빈 총알 |
| 5–6 | 빨강 생명력, 파랑 생명력 |
| 7–11 | 빨강 아이템 (ED, MG, C, K, HC) |
| 12–16 | 파랑 아이템 (ED, MG, C, K, HC) |
| 17 | 총 데미지 |
| 18 | 지식 상태 |
| 19–20 | 파랑 수갑, 빨강 수갑 (0/1) |

---

## 📌 참고 사항

- 모델 체크포인트: `Agents/` 폴더에 저장
- 훈련 진행 상황: 로깅 및 시각화 지원
- 게임 규칙 및 상세 스펙: `.cursor/rules/` 내 규칙 파일 참고

---

<div align="center">

*Buckshot Roulette AI · Dueling DQN · Unity 6.3 LTS*

</div>
