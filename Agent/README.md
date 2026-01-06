# Buckshot AI Agent - Unity 6.3 LTS

This directory contains the Python-based AI agent for the Buckshot game, optimized for Unity 6.3 LTS.

## Improvements for Unity 6.3 LTS

### 1. Enhanced Error Handling
- Added connection timeout handling
- Improved error messages and logging
- Graceful disconnection handling

### 2. Performance Optimizations
- Increased buffer size from 1024 to 4096 bytes
- Added socket timeouts for better responsiveness
- Improved data parsing efficiency

### 3. Connection Reliability
- Automatic reconnection logic in Unity
- Connection state monitoring
- Better handling of network interruptions

### 4. Cross-Platform Compatibility
- Works on Windows, macOS, and Linux
- Standard TCP socket implementation
- No platform-specific dependencies

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install torch numpy matplotlib
```

3. Run the agent:
```bash
python agent.py
```

## Communication Protocol

The agent communicates with Unity via TCP sockets on `localhost:12345`.

### Commands:
- `get_state` - Request current game state
- `play_step:<action>` - Execute an action (0-6)
- `reset` - Reset the game

### State Format:
Comma-separated values representing:
1. Turn (1=red, 0=blue)
2. Number of bullets
3. Number of real bullets
4. Number of empty bullets
5. Red lives
6. Blue lives
7-11. Red items (ED, MG, C, K, HC)
12-16. Blue items (ED, MG, C, K, HC)
17. Gun damage
18. Knowledge state
19. Blue cuffed (0/1)
20. Red cuffed (0/1)

## Notes

- The agent uses Dueling DQN (Double Deep Q-Network) for reinforcement learning
- Model checkpoints are saved in the `Agents/` folder
- Training progress is logged and visualized

