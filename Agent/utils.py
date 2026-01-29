import matplotlib.pyplot as plt
import numpy as np

def plotLearning(x, scores, epsilons, filename):
    fig, (ax_score, ax_eps) = plt.subplots(2, 1, figsize=(12, 8))
    
    # --- 상단: Score 그래프 ---
    N = len(scores)
    running_avg = np.empty(N)
    for t in range(N):
        running_avg[t] = np.mean(scores[max(0, t-100):(t+1)])  # 100 에피소드 이동 평균
    
    ax_score.plot(x, scores, alpha=0.3, color="C1", label='Raw Score')
    ax_score.plot(x, running_avg, color="C3", linewidth=2, label='Avg (100 ep)')
    ax_score.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax_score.set_xlabel("Game")
    ax_score.set_ylabel("Score")
    ax_score.set_title("Training Score")
    ax_score.legend(loc='upper left')
    ax_score.set_yscale('symlog', linthresh=10)  # 대칭 로그 스케일 (±10 근처는 선형)
    ax_score.grid(True, alpha=0.3)
    
    # --- 하단: Epsilon 그래프 ---
    ax_eps.plot(x, epsilons, color="C0")
    ax_eps.set_xlabel("Game")
    ax_eps.set_ylabel("Epsilon")
    ax_eps.set_title("Exploration Rate")
    ax_eps.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
