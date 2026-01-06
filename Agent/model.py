import torch as T
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import os

class ReplayBuffer():
    def __init__(self, max_size, input_shape):
        self.mem_size = max_size
        self.mem_cntr = 0
        self.state_mem = np.zeros((self.mem_size, *input_shape), dtype=np.float32)
        self.new_state_mem = np.zeros((self.mem_size, *input_shape), dtype=np.float32)
        self.action_mem = np.zeros(self.mem_size, dtype=np.int64)
        self.reward_mem = np.zeros(self.mem_size, dtype=np.float32)
        self.terminal_mem = np.zeros(self.mem_size, dtype=np.uint8)

    def store_transition(self, state, action, reward, state_, done):
        index = self.mem_cntr % self.mem_size
        self.state_mem[index] = state
        self.new_state_mem[index] = state_
        self.action_mem[index] = action
        self.reward_mem[index] = reward
        self.terminal_mem[index] = done
        self.mem_cntr += 1 
        #long ass "fake" deque

    def sample_buffer(self, batch_size):
        max_mem = min(self.mem_cntr, self.mem_size)
        batch = np.random.choice(max_mem, batch_size, replace=False)

        states = self.state_mem[batch]
        states_ = self.new_state_mem[batch]
        actions = self.action_mem[batch]
        rewards = self.reward_mem[batch]
        terminal = self.terminal_mem[batch]

        return states, actions, rewards, states_, terminal
        #TODO: 
        #Priotetitized experosnance replay
class DuelingDeepQNetwork(nn.Module):
    def __init__(self, lr, input_dims, n_actions, checkpoint_dir, name):
        super(DuelingDeepQNetwork, self).__init__()
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file = os.path.join(self.checkpoint_dir, name)

        self.input_dims = input_dims
        self.n_actions = n_actions
        
        self.fc1 = nn.Linear(*self.input_dims, 512)
        self.V = nn.Linear(512, 1)
        self.A = nn.Linear(512, self.n_actions)

        self.optimizer = optim.Adam(self.parameters(), lr=lr)
        self.loss = nn.MSELoss()
        self.device = "cpu"
        self.to(self.device)

    def forward(self, state):
        flat1 = F.relu(self.fc1(state))
        V = self.V(flat1)
        A = self.A(flat1)

        return V,A
    
    def save_checkpoint(self):
        print("-- saving checkpoint --")
        T.save(self.state_dict(), self.checkpoint_file)

    def load_checkpoint(self):
        print("-- loading checkpoint --")
        self.load_state_dict(T.load(self.checkpoint_file))


class Agent():
    def __init__(self, gamma, epsilon, lr, n_actions, input_dims, mem_size, batch_size, eps_min = 0.01, eps_dec=5e-7, replace=1000, checkpoint_dir='Agents'):
        self.gamma = gamma
        self.epsilon = epsilon
        self.lr = lr
        self.n_actions = n_actions
        self.input_dims = input_dims
        self.mem_size = mem_size
        self.batch_size = batch_size
        self.eps_min = eps_min
        self.eps_dec = eps_dec
        self.replace_target_count = replace
        self.checkpoint_dir = checkpoint_dir
        self.learn_step_counter = 0
        self.action_space = [i for i in range(self.n_actions)]

        self.memory = ReplayBuffer(mem_size, input_dims)
        self.q_eval = DuelingDeepQNetwork(self.lr, input_dims=self.input_dims, n_actions=self.n_actions, checkpoint_dir=self.checkpoint_dir, name="buckshot_eval")
        self.q_next = DuelingDeepQNetwork(self.lr, input_dims=self.input_dims, n_actions=self.n_actions, checkpoint_dir=self.checkpoint_dir, name="buckshot_next")

    def choose_action(self, observation):
        if(np.random.random() > self.epsilon):
            state = T.tensor([observation], dtype=T.float).to(self.q_eval.device)
            _, advantage = self.q_eval.forward(state)
            action = T.argmax(advantage).item()
            randomness = "AI"
        else:
            action = np.random.choice(self.action_space)
            randomness = "Epsilon"

        return action, randomness
    
    def store_transition(self, state, action, reward, state_, done):
        self.memory.store_transition(state, action, reward, state_, done)

    def replace_target_network(self):
        if self.learn_step_counter % self.replace_target_count == 0:
            self.q_next.load_state_dict(self.q_eval.state_dict())

    def decrease_epsilon(self):
        self.epsilon = self.epsilon - self.eps_dec \
            if self.epsilon > self.eps_min else self.eps_min

    def save_models(self):
        self.q_eval.save_checkpoint()
        self.q_next.save_checkpoint()

    def load_models(self):
        self.q_eval.load_checkpoint()
        self.q_next.load_checkpoint()

    def learn(self):
        if self.memory.mem_cntr < self.batch_size:
            return

        self.q_eval.optimizer.zero_grad()
        self.replace_target_network()

        state, action, reward, new_state, done = \
            self.memory.sample_buffer(self.batch_size)

        states = T.tensor(state).to(self.q_eval.device)
        actions = T.tensor(action).to(self.q_eval.device)
        rewards = T.tensor(reward).to(self.q_eval.device)
        states_ = T.tensor(new_state).to(self.q_eval.device)
        dones = T.tensor(done).to(self.q_eval.device)  # Convert dones to T.bool

        indices = np.arange(self.batch_size)

        V_s, A_s = self.q_eval.forward(states)
        V_s_, A_s_ = self.q_next.forward(states_)

        V_s_eval, A_s_eval = self.q_eval.forward(states_)

        q_pred = T.add(V_s, (A_s - A_s.mean(dim=1, keepdim=True)))[indices, actions]
        q_next = T.add(V_s_, (A_s_ - A_s_.mean(dim=1, keepdim=True)))
        q_eval = T.add(V_s_eval, (A_s_eval - A_s_eval.mean(dim=1, keepdim=True)))

        max_actions = T.argmax(q_eval, dim=1)

        q_next[dones] = 0.0  # Reset the q_next for dones to 0.0
        q_target = rewards + self.gamma * q_next[indices, max_actions]

        loss = self.q_eval.loss(q_target, q_pred).to(self.q_eval.device)
        loss.backward()
        self.q_eval.optimizer.step()
        self.learn_step_counter += 1

        self.decrease_epsilon()
