"""
종합 검증 스크립트 - 모든 주요 컴포넌트가 올바르게 작동하는지 확인
"""
import os
import sys

def check_imports():
    """모든 import가 정상적으로 작동하는지 확인"""
    print("=" * 60)
    print("1. Import 검증")
    print("=" * 60)
    
    issues = []
    
    # 상위 디렉토리를 경로에 추가
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from model import Agent
        print("✓ model.Agent import 성공")
    except Exception as e:
        issues.append(f"model.Agent import 실패: {e}")
        print(f"✗ model.Agent import 실패: {e}")
    
    try:
        from utils import plotLearning
        print("✓ utils.plotLearning import 성공")
    except Exception as e:
        issues.append(f"utils.plotLearning import 실패: {e}")
        print(f"✗ utils.plotLearning import 실패: {e}")
    
    try:
        from game_env import GameEnvironment, Player, ActionType
        print("✓ game_env import 성공")
    except Exception as e:
        issues.append(f"game_env import 실패: {e}")
        print(f"✗ game_env import 실패: {e}")
    
    return len(issues) == 0, issues

def check_agent_initialization():
    """Agent 초기화가 정상적으로 작동하는지 확인"""
    print("\n" + "=" * 60)
    print("2. Agent 초기화 검증")
    print("=" * 60)
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from model import Agent
        
        # Agents 디렉토리 경로
        agents_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Agents')
        
        agent = Agent(
            gamma=0.99,
            epsilon=1.0,
            lr=4e-4,
            input_dims=[20],
            n_actions=7,
            mem_size=1000,  # 테스트용 작은 크기
            batch_size=64,
            eps_min=0.01,
            eps_dec=2e-5,
            replace=100,
            checkpoint_dir=agents_dir
        )
        
        print("✓ Agent 초기화 성공")
        print(f"  - input_dims: {agent.input_dims}")
        print(f"  - n_actions: {agent.n_actions}")
        print(f"  - epsilon: {agent.epsilon}")
        print(f"  - gamma: {agent.gamma}")
        print(f"  - checkpoint_dir: {agent.checkpoint_dir}")
        
        # q_eval과 q_next가 제대로 생성되었는지 확인
        if hasattr(agent, 'q_eval') and hasattr(agent, 'q_next'):
            print("✓ q_eval과 q_next 네트워크 생성 확인")
        else:
            print("✗ q_eval 또는 q_next 네트워크가 생성되지 않았습니다")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Agent 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_game_environment():
    """게임 환경이 정상적으로 작동하는지 확인"""
    print("\n" + "=" * 60)
    print("3. 게임 환경 검증")
    print("=" * 60)
    
    try:
        from game_env import GameEnvironment, Player, ActionType
        
        env = GameEnvironment(max_hp=4)
        state = env.get_state()
        
        print(f"✓ GameEnvironment 초기화 성공")
        print(f"  - 상태 벡터 차원: {len(state)} (예상: 20)")
        print(f"  - Red HP: {env.red_lives}")
        print(f"  - Blue HP: {env.blue_lives}")
        print(f"  - 현재 턴: {'Red' if env.current_turn == Player.RED else 'Blue'}")
        
        if len(state) != 20:
            print(f"✗ 상태 벡터 차원이 잘못되었습니다 (예상: 20, 실제: {len(state)})")
            return False
        
        # 간단한 액션 테스트
        state, reward, done, info = env.step(ActionType.MagGlass)
        print(f"✓ 액션 실행 성공 (Magnifying Glass)")
        print(f"  - 보상: {reward:.2f}")
        print(f"  - 게임 종료: {done}")
        
        return True
    except Exception as e:
        print(f"✗ 게임 환경 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_checkpoint_files():
    """체크포인트 파일이 존재하는지 확인"""
    print("\n" + "=" * 60)
    print("4. 체크포인트 파일 검증")
    print("=" * 60)
    
    agents_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Agents')
    
    eval_file = os.path.join(agents_dir, 'buckshot_eval')
    next_file = os.path.join(agents_dir, 'buckshot_next')
    
    print(f"체크포인트 디렉토리: {agents_dir}")
    
    if os.path.exists(eval_file):
        size = os.path.getsize(eval_file)
        print(f"✓ buckshot_eval 파일 존재 ({size:,} bytes)")
    else:
        print(f"⚠ buckshot_eval 파일 없음 (새로 학습 시작)")
    
    if os.path.exists(next_file):
        size = os.path.getsize(next_file)
        print(f"✓ buckshot_next 파일 존재 ({size:,} bytes)")
    else:
        print(f"⚠ buckshot_next 파일 없음 (새로 학습 시작)")
    
    return True

def check_self_play_integration():
    """셀프 플레이 통합 테스트"""
    print("\n" + "=" * 60)
    print("5. 셀프 플레이 통합 검증")
    print("=" * 60)
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from model import Agent
        from game_env import GameEnvironment, Player
        
        agents_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Agents')
        
        # 두 에이전트 생성
        agent_red = Agent(
            gamma=0.99,
            epsilon=1.0,
            lr=4e-4,
            input_dims=[20],
            n_actions=7,
            mem_size=1000,
            batch_size=64,
            eps_min=0.01,
            eps_dec=2e-5,
            replace=100,
            checkpoint_dir=agents_dir
        )
        
        agent_blue = Agent(
            gamma=0.99,
            epsilon=1.0,
            lr=4e-4,
            input_dims=[20],
            n_actions=7,
            mem_size=1000,
            batch_size=64,
            eps_min=0.01,
            eps_dec=2e-5,
            replace=100,
            checkpoint_dir=agents_dir
        )
        
        print("✓ 두 에이전트 생성 성공")
        
        # 게임 환경 생성
        env = GameEnvironment(max_hp=4)
        state = env.reset()
        
        print("✓ 게임 환경 생성 및 초기화 성공")
        
        # 간단한 게임 플레이 테스트 (5스텝만)
        for step in range(5):
            current_player = Player.RED if env.current_turn == Player.RED else Player.BLUE
            agent = agent_red if current_player == Player.RED else agent_blue
            
            action, _ = agent.choose_action(state)
            next_state, reward, done, info = env.step(action)
            
            agent.store_transition(state, action, reward, next_state, int(done))
            
            if done:
                break
            
            state = next_state
        
        print("✓ 게임 플레이 테스트 성공 (5스텝)")
        
        # 학습 테스트 (메모리가 충분할 때)
        if agent_red.memory.mem_cntr >= agent_red.batch_size:
            agent_red.learn()
            print("✓ 학습 함수 실행 성공")
        else:
            print(f"⚠ 메모리 부족으로 학습 스킵 (현재: {agent_red.memory.mem_cntr}/{agent_red.batch_size})")
        
        return True
    except Exception as e:
        print(f"✗ 셀프 플레이 통합 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """모든 검증 실행"""
    print("\n" + "=" * 60)
    print("종합 검증 시작")
    print("=" * 60)
    
    results = []
    
    # 1. Import 검증
    success, issues = check_imports()
    results.append(("Import", success))
    if issues:
        print(f"\n⚠ Import 문제: {issues}")
    
    # 2. Agent 초기화 검증
    results.append(("Agent 초기화", check_agent_initialization()))
    
    # 3. 게임 환경 검증
    results.append(("게임 환경", check_game_environment()))
    
    # 4. 체크포인트 파일 검증
    results.append(("체크포인트 파일", check_checkpoint_files()))
    
    # 5. 셀프 플레이 통합 검증
    results.append(("셀프 플레이 통합", check_self_play_integration()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 모든 검증을 통과했습니다!")
        print("✓ 학습을 시작할 수 있습니다!")
    else:
        print("⚠ 일부 검증에서 문제가 발견되었습니다.")
        print("⚠ 위의 오류 메시지를 확인하고 수정하세요.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()
