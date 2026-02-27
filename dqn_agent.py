"""
Deep Q‑Network (DQN) Agent for FlightX
========================================
Full DQN with experience replay, target network, and epsilon‑greedy
exploration.  Trains headlessly using FlightXEnv.
"""

import os
import random
import json
from collections import deque

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from flightx_env import FlightXEnv


# ---------------------------------------------------------------------------
# Q‑Network
# ---------------------------------------------------------------------------
if TORCH_AVAILABLE:
    class QNetwork(nn.Module):
        """MLP Q‑function: state (4) → Q‑values (3 actions)."""

        def __init__(self, state_dim=4, hidden1=128, hidden2=64, action_dim=3):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(state_dim, hidden1),
                nn.ReLU(),
                nn.Linear(hidden1, hidden2),
                nn.ReLU(),
                nn.Linear(hidden2, action_dim),
            )

        def forward(self, x):
            return self.net(x)
else:
    class QNetwork:
        def __init__(self, *a, **kw):
            raise RuntimeError("PyTorch is required. Run: pip install torch")


# ---------------------------------------------------------------------------
# Replay Buffer
# ---------------------------------------------------------------------------
class ReplayBuffer:
    def __init__(self, capacity=50_000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)


# ---------------------------------------------------------------------------
# DQN Agent
# ---------------------------------------------------------------------------
class DQNAgent:
    """
    DQN agent with target network and ε‑greedy exploration.

    Call `train()` to run headless training.
    Call `load_model()` to load a saved model for inference.
    """

    MODEL_FILE = 'dqn_model.pth'
    LOG_FILE = 'dqn_training_log.json'

    def __init__(
        self,
        state_dim=4,
        action_dim=3,
        lr=1e-3,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995,
        batch_size=64,
        target_update=1000,
        buffer_capacity=50_000,
    ):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required. Run: pip install torch")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update

        self.policy_net = QNetwork(state_dim, action_dim=action_dim)
        self.target_net = QNetwork(state_dim, action_dim=action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.criterion = nn.SmoothL1Loss()  # Huber loss
        self.buffer = ReplayBuffer(buffer_capacity)

        self.steps_done = 0
        self.training_log = []   # list of {"episode", "reward", "score", "epsilon"}

    # ---- action selection ----
    def select_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        with torch.no_grad():
            q = self.policy_net(torch.tensor([state], dtype=torch.float32))
            return q.argmax(1).item()

    # ---- one gradient step ----
    def _learn(self):
        if len(self.buffer) < self.batch_size:
            return

        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)

        s = torch.tensor(states)
        a = torch.tensor(actions).unsqueeze(1)
        r = torch.tensor(rewards).unsqueeze(1)
        ns = torch.tensor(next_states)
        d = torch.tensor(dones).unsqueeze(1)

        q_values = self.policy_net(s).gather(1, a)

        with torch.no_grad():
            next_q = self.target_net(ns).max(1, keepdim=True)[0]
            target = r + self.gamma * next_q * (1 - d)

        loss = self.criterion(q_values, target)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

    # ---- training loop ----
    def train(self, num_episodes=500, max_steps=5000, progress_callback=None):
        """
        Run headless training.
        progress_callback(episode, total, reward, score, epsilon) is called
        each episode for UI updates.
        Returns the training log.
        """
        env = FlightXEnv()

        for ep in range(1, num_episodes + 1):
            state = env.reset()
            total_reward = 0

            for _ in range(max_steps):
                action = self.select_action(state)
                next_state, reward, done, info = env.step(action)
                self.buffer.push(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward
                self.steps_done += 1

                self._learn()

                # Sync target network
                if self.steps_done % self.target_update_freq == 0:
                    self.target_net.load_state_dict(self.policy_net.state_dict())

                if done:
                    break

            # Decay epsilon
            self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

            entry = {
                'episode': ep,
                'reward': round(total_reward, 2),
                'score': info.get('score', 0),
                'epsilon': round(self.epsilon, 4),
            }
            self.training_log.append(entry)

            if ep % 10 == 0 or ep == 1:
                print(
                    f"[DQN] Ep {ep}/{num_episodes}  "
                    f"Reward={total_reward:.1f}  Score={info['score']}  "
                    f"ε={self.epsilon:.3f}"
                )

            if progress_callback:
                progress_callback(ep, num_episodes, total_reward, info['score'], self.epsilon)

        # Save
        self.save_model()
        self._save_log()
        return self.training_log

    def save_model(self):
        torch.save(self.policy_net.state_dict(), self.MODEL_FILE)
        print(f"[DQN] Model saved to {self.MODEL_FILE}")

    def _save_log(self):
        with open(self.LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.training_log, f)
        print(f"[DQN] Training log saved to {self.LOG_FILE}")

    # ---- inference ----
    @staticmethod
    def load_model():
        """Load a trained QNetwork for inference. Returns model or None."""
        if not TORCH_AVAILABLE:
            print("[DQN] PyTorch not available.")
            return None
        if not os.path.exists(DQNAgent.MODEL_FILE):
            print("[DQN] No trained model found.")
            return None
        model = QNetwork()
        model.load_state_dict(torch.load(DQNAgent.MODEL_FILE, weights_only=True))
        model.eval()
        print("[DQN] Loaded trained model.")
        return model

    @staticmethod
    def predict_action(model, state_list):
        """Given a QNetwork and state list, return action int: 1 (flap), 0 (glide), -1 (drop)."""
        with torch.no_grad():
            q = model(torch.tensor([state_list], dtype=torch.float32))
            idx = q.argmax(1).item()
        return [1, 0, -1][idx]

    @staticmethod
    def load_training_log():
        """Load the DQN training log for comparison graphs."""
        if not os.path.exists(DQNAgent.LOG_FILE):
            return None
        with open(DQNAgent.LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
