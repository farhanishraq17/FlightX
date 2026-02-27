"""
Behavioral Cloning Module for FlightX
======================================
Records human play as (state, action) pairs, trains a PyTorch neural network
to imitate the human's behavior, and provides a model for AI playback.
"""

import json
import os
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data Recorder  – captures (state, action) pairs during human PvC play
# ---------------------------------------------------------------------------
class DataRecorder:
    """Records (vision_state, action) pairs from human play for training."""

    SAVE_FILE = 'bc_training_data.json'

    def __init__(self):
        self.data = []          # list of {"state": [...], "action": int}
        self.recording = False

    def start(self):
        self.recording = True
        self.data = []
        print("[BC] Recording started.")

    def stop(self):
        self.recording = False
        print(f"[BC] Recording stopped. {len(self.data)} samples captured.")

    def capture(self, state, action):
        """
        Call every frame while recording.
        state:  list of 4 floats (same vision vector as NEAT)
        action: 1 = flap, 0 = glide, -1 = drop
        """
        if not self.recording:
            return
        self.data.append({
            'state': [float(s) for s in state],
            'action': int(action)
        })

    def save(self):
        with open(self.SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)
        print(f"[BC] Saved {len(self.data)} samples to {self.SAVE_FILE}")
        return len(self.data)

    def load(self):
        if not os.path.exists(self.SAVE_FILE):
            print("[BC] No training data file found.")
            return False
        with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        print(f"[BC] Loaded {len(self.data)} samples.")
        return len(self.data) > 0


# ---------------------------------------------------------------------------
# Neural Network Model
# ---------------------------------------------------------------------------
if TORCH_AVAILABLE:
    class BCModel(nn.Module):
        """Small MLP: 4 inputs → 64 → 32 → 3 action classes."""

        def __init__(self, input_size=4, hidden1=64, hidden2=32, num_actions=3):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_size, hidden1),
                nn.ReLU(),
                nn.Linear(hidden1, hidden2),
                nn.ReLU(),
                nn.Linear(hidden2, num_actions),
            )

        def forward(self, x):
            return self.net(x)

        def predict_action(self, state_list):
            """Given a list of 4 floats, return action int: 1, 0, or -1."""
            self.eval()
            with torch.no_grad():
                x = torch.tensor([state_list], dtype=torch.float32)
                logits = self.forward(x)
                idx = torch.argmax(logits, dim=1).item()
            # Map index to action: 0 → flap(1), 1 → glide(0), 2 → drop(-1)
            return [1, 0, -1][idx]
else:
    # Fallback stub so the file can be imported without torch
    class BCModel:
        def __init__(self, *a, **kw):
            raise RuntimeError("PyTorch is not installed. Run: pip install torch")
        def predict_action(self, state_list):
            raise RuntimeError("PyTorch is not installed.")


# ---------------------------------------------------------------------------
# Trainer
# ---------------------------------------------------------------------------
class BCTrainer:
    """Trains a BCModel from recorded (state, action) data."""

    MODEL_FILE = 'bc_model.pth'

    def __init__(self):
        self.recorder = DataRecorder()
        self.model = None

    def train(self, epochs=80, lr=0.003, batch_size=64):
        """
        Load saved data, train the model, save it.
        Returns (accuracy, num_samples) or (None, 0) on failure.
        """
        if not TORCH_AVAILABLE:
            print("[BC] PyTorch not available.")
            return None, 0

        if not self.recorder.load():
            print("[BC] No training data found.")
            return None, 0

        # Prepare tensors
        states = [d['state'] for d in self.recorder.data]
        actions = [d['action'] for d in self.recorder.data]

        # Map actions: 1 → 0, 0 → 1, -1 → 2  (class indices)
        action_map = {1: 0, 0: 1, -1: 2}
        labels = [action_map.get(a, 1) for a in actions]

        X = torch.tensor(states, dtype=torch.float32)
        y = torch.tensor(labels, dtype=torch.long)

        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model = BCModel()
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)

        # Train
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            correct = 0
            total = 0
            for xb, yb in loader:
                optimizer.zero_grad()
                out = self.model(xb)
                loss = criterion(out, yb)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * xb.size(0)
                correct += (out.argmax(1) == yb).sum().item()
                total += xb.size(0)

            if (epoch + 1) % 20 == 0 or epoch == 0:
                acc = correct / total * 100
                avg_loss = total_loss / total
                print(f"[BC] Epoch {epoch+1}/{epochs}  Loss={avg_loss:.4f}  Acc={acc:.1f}%")

        # Final accuracy
        self.model.eval()
        with torch.no_grad():
            out = self.model(X)
            final_acc = (out.argmax(1) == y).sum().item() / len(y) * 100

        # Save
        torch.save(self.model.state_dict(), self.MODEL_FILE)
        print(f"[BC] Model saved to {self.MODEL_FILE}  Accuracy={final_acc:.1f}%")
        return final_acc, len(states)

    @staticmethod
    def load_model():
        """Load a trained BCModel from disk. Returns model or None."""
        if not TORCH_AVAILABLE:
            print("[BC] PyTorch not available.")
            return None
        if not os.path.exists(BCTrainer.MODEL_FILE):
            print("[BC] No trained model found.")
            return None
        model = BCModel()
        model.load_state_dict(torch.load(BCTrainer.MODEL_FILE, weights_only=True))
        model.eval()
        print("[BC] Loaded trained model.")
        return model
