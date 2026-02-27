"""
FlightX Headless Environment
=============================
Gym-like wrapper around the FlightX game physics for RL training.
No Pygame rendering — pure numerical simulation.
"""

import random


class FlightXEnv:
    """
    Lightweight, headless FlightX environment for RL training.

    Actions:
        0 = flap (jump up)
        1 = glide (do nothing)
        2 = drop (accelerate down)

    State (4 floats, same as Player.vision):
        [y_offset_to_gap, x_distance_to_pipe, gap_size_norm, velocity_norm]
    """

    # Physics constants (mirror components.py / player.py)
    GRAVITY = 0.25
    MAX_VEL = 5
    FLAP_IMPULSE = 2.2
    FLAP_CEILING = -5.0
    DROP_ACCEL = 0.9
    DROP_MAX = 6.0
    PIPE_SPEED = 1
    PIPE_WIDTH = 15
    SPAWN_INTERVAL = 200

    def __init__(self, win_width=900, win_height=720):
        self.win_width = win_width
        self.win_height = win_height
        self.ground_y = int(win_height * 0.8)
        self.reset()

    def reset(self):
        self.player_x = 50
        self.player_y = 200
        self.player_vel = 0.0
        self.pipes = []
        self.spawn_timer = 10
        self.score = 0
        self.alive = True
        self.steps = 0
        return self._get_state()

    # ---- internal pipe helpers ----
    def _spawn_pipe(self):
        opening = random.randint(90, 130)
        bottom_h = random.randint(10, 300)
        top_h = self.ground_y - bottom_h - opening
        self.pipes.append({
            'x': self.win_width,
            'top_h': top_h,
            'bottom_y': self.ground_y - bottom_h,
            'opening': opening,
            'passed': False,
            'counted': False,
        })

    def _closest_pipe(self):
        for p in self.pipes:
            if not p['passed']:
                return p
        return None

    def _get_state(self):
        p = self._closest_pipe()
        if p is None:
            return [0.0, 0.0, 0.0, self._clamp(self.player_vel / 10)]
        gap_center = (p['top_h'] + p['bottom_y']) / 2
        return [
            self._clamp((self.player_y - gap_center) / 250),
            self._clamp((p['x'] - self.player_x) / 400),
            self._clamp(p['opening'] / 150),
            self._clamp(self.player_vel / 10),
        ]

    @staticmethod
    def _clamp(v, lo=-1, hi=1):
        return max(lo, min(hi, v))

    # ---- collision checks ----
    def _collides(self):
        # Ground / ceiling
        if self.player_y + 14 >= self.ground_y or self.player_y - 14 < 0:
            return True
        # Pipes (simple AABB, half-size 14 matching Player inflate(-12,-12) on 40×40)
        px, py = self.player_x, self.player_y
        half = 14
        for p in self.pipes:
            pipe_left = p['x']
            pipe_right = p['x'] + self.PIPE_WIDTH
            if px + half > pipe_left and px - half < pipe_right:
                # Top pipe
                if py - half < p['top_h']:
                    return True
                # Bottom pipe
                if py + half > p['bottom_y']:
                    return True
        return False

    # ---- step ----
    def step(self, action):
        """
        Execute one frame.
        Returns (state, reward, done, info).
        """
        if not self.alive:
            return self._get_state(), 0.0, True, {'score': self.score}

        # Action
        if action == 0:   # flap
            if self.player_y - 14 > 0:
                self.player_vel = max(self.player_vel - self.FLAP_IMPULSE, self.FLAP_CEILING)
        elif action == 2:  # drop
            self.player_vel = min(self.player_vel + self.DROP_ACCEL, self.DROP_MAX)
        # action == 1 → glide (do nothing)

        # Physics
        self.player_vel += self.GRAVITY
        self.player_vel = min(self.player_vel, self.MAX_VEL)
        self.player_y += self.player_vel
        self.steps += 1

        # Pipes
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self._spawn_pipe()
            self.spawn_timer = self.SPAWN_INTERVAL

        reward = 0.1  # survival reward per frame

        for p in self.pipes:
            p['x'] -= self.PIPE_SPEED
            if p['x'] + self.PIPE_WIDTH <= self.player_x and not p['passed']:
                p['passed'] = True
            if p['passed'] and not p['counted']:
                p['counted'] = True
                self.score += 1
                reward += 10.0  # pipe passed bonus

        # Remove off-screen
        self.pipes = [p for p in self.pipes if p['x'] > -self.PIPE_WIDTH]

        # Collision
        if self._collides():
            self.alive = False
            reward = -100.0

        state = self._get_state()
        return state, reward, not self.alive, {'score': self.score}
