"""
Pre-train script for FlightX ML models
========================================
Generates expert play data using a rule-based agent, then trains
both the Behavioral Cloning model and the DQN model so they work
immediately without any manual training.

Usage:
    python pretrain_models.py
"""

import json
import os
import random
import numpy as np

from flightx_env import FlightXEnv

# ─── Generate expert demonstration data ─────────────────────────────────
def expert_action(state):
    """
    Rule-based expert: simple but effective.
    state = [y_offset_to_gap, x_distance, gap_size_norm, velocity_norm]
    y_offset > 0 means we're BELOW the gap → flap
    y_offset < 0 means we're ABOVE → glide or drop
    """
    y_off = state[0]   # positive = below gap
    vel   = state[3]   # positive = falling, negative = rising

    if y_off > 0.08:
        return 0  # flap (below gap)
    elif y_off < -0.08:
        if vel < -0.15:
            return 2  # drop (rising too fast while above gap)
        return 1  # glide
    else:
        # Near center — manage velocity
        if vel > 0.15:
            return 0  # flap to slow descent
        elif vel < -0.15:
            return 1  # glide to slow ascent
        return 1  # glide


def generate_expert_data(num_episodes=200, max_steps=5000):
    """Run the expert agent and collect (state, action) pairs."""
    env = FlightXEnv()
    data = []
    total_score = 0

    for ep in range(num_episodes):
        state = env.reset()
        for _ in range(max_steps):
            action = expert_action(state)
            # Map env action (0=flap,1=glide,2=drop) to BC action (1=flap,0=glide,-1=drop)
            bc_action = {0: 1, 1: 0, 2: -1}[action]
            data.append({'state': [float(s) for s in state], 'action': bc_action})

            next_state, reward, done, info = env.step(action)
            state = next_state
            if done:
                break
        total_score += info.get('score', 0)

    avg = total_score / num_episodes
    print(f'[Expert] Generated {len(data)} samples over {num_episodes} episodes, avg score={avg:.1f}')
    return data


# ─── Train BC model ─────────────────────────────────────────────────────
def train_bc_model(data):
    """Train behavioral cloning model from expert data."""
    from behavioral_cloning import BCTrainer, DataRecorder

    # Save data to file
    recorder = DataRecorder()
    recorder.data = data
    recorder.save()

    # Train
    trainer = BCTrainer()
    acc, n = trainer.train(epochs=100, lr=0.003, batch_size=128)
    print(f'[BC] Training complete: accuracy={acc:.1f}%, samples={n}')
    return acc


# ─── Train DQN model ────────────────────────────────────────────────────
def train_dqn_model():
    """Train DQN agent headlessly."""
    from dqn_agent import DQNAgent

    agent = DQNAgent(
        lr=1e-3,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995,
        batch_size=64,
        target_update=500,
        buffer_capacity=50000,
    )

    def progress(ep, total, reward, score, eps):
        if ep % 25 == 0 or ep == 1:
            print(f'  [DQN] Ep {ep}/{total}  Reward={reward:.0f}  Score={score}  ε={eps:.3f}')

    print('[DQN] Starting training (300 episodes)...')
    agent.train(num_episodes=300, max_steps=3000, progress_callback=progress)
    print('[DQN] Training complete!')


# ─── Main ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('='*50)
    print('  FlightX Model Pre-Training')
    print('='*50)

    # Step 1: Generate expert data
    print('\n[Step 1] Generating expert play data...')
    expert_data = generate_expert_data(num_episodes=200, max_steps=5000)

    # Step 2: Train BC model
    print('\n[Step 2] Training Behavioral Cloning model...')
    train_bc_model(expert_data)

    # Step 3: Train DQN model
    print('\n[Step 3] Training DQN agent...')
    train_dqn_model()

    print('\n' + '='*50)
    print('  All models pre-trained successfully!')
    print(f'  - bc_model.pth  : {"exists" if os.path.exists("bc_model.pth") else "MISSING"}')
    print(f'  - dqn_model.pth : {"exists" if os.path.exists("dqn_model.pth") else "MISSING"}')
    print('='*50)
