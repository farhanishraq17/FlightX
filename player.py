import pygame
import random
import math
import brain
import config


class Player:
    def __init__(self, is_human=False):
        self.is_human = is_human
        # Bird
        self.x, self.y = 50, 200
        self.hk_run = pygame.transform.smoothscale(
            pygame.image.load('Assets/plane1.png').convert_alpha(), (40, 40)
        )
        self.hk_air = pygame.transform.smoothscale(
            pygame.image.load('Assets/plane1.png').convert_alpha(), (40, 40)
        )

        self.rect = self.hk_run.get_rect(topleft=(self.x, self.y)).inflate(-12, -12)

        self.vel = 0
        self.alive = True
        self.on_ground = False
        self.lifespan = 0
        self.vision = [0, 0, 0, 0]
        self.fitness = 0
        self.score = 0
        self.inputs = 4

        self.brain = brain.Brain(self.inputs, hidden_layers=[6])
        self.brain.generate_net()
    # ---------------- Utility ----------------
    def clamp(self, v, lo=-1, hi=1):
        return max(lo, min(hi, v))

    # ---------------- Game Logic ----------------
    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        
        # Draw human player with a different color/tint or marker
        if self.is_human:
             # Just a simple indicator for now, maybe a circle around it
             pygame.draw.circle(window, (50, 255, 50), self.rect.center, 25, 2)
             
        window.blit(sprite, self.rect)

    def ground_collision(self, ground):
        return self.rect.colliderect(ground)

    def sky_collision(self):
        return self.rect.top < 0

    def pipe_collision(self):
        p = self.closest_pipe()
        if p:
            # MultiHolePipes has multiple wall segments — check all of them
            if hasattr(p, 'wall_rects'):
                for wr in p.wall_rects:
                    if self.rect.colliderect(wr):
                        return True
                return False
            return self.rect.colliderect(p.top_rect) or self.rect.colliderect(p.bottom_rect)
        return False

    def update(self, ground):
        if not (self.ground_collision(ground) or self.pipe_collision()):
            self.vel += 0.25
            self.vel = min(self.vel, 5)
            self.rect.y += self.vel
            self.lifespan += 1
        else:
            self.alive = False
            self.vel = 0

    def bird_flap(self, generation=1):
        if not self.sky_collision():
            if self.is_human:
                impulse = 7.5 * config.jump_scale
                ceiling = -17.0 * config.jump_scale
            else:
                impulse = 3.8 * config.jump_scale
                ceiling = -6.0 * config.jump_scale
            self.vel = max(self.vel - impulse, ceiling)

    def bird_drop(self):
        # Allow intentional faster descent
        self.vel = min(self.vel + 0.9, 6)

    @staticmethod
    def closest_pipe():
        for p in config.pipes:
            if not p.passed:
                return p
        return None

    # ---------------- AI ----------------
    def look(self):
        p = self.closest_pipe()
        if not p:
            self.vision = [0, 0, 0, 0]
            return

        # Distances derived only from the closest pipe
        gap = (p.top_rect.bottom + p.bottom_rect.top) / 2
        self.vision[0] = self.clamp((self.rect.centery - gap) / 250)  # vertical offset to gap
        self.vision[1] = self.clamp((p.x - self.rect.centerx) / 400)   # horizontal distance to pipe
        self.vision[2] = self.clamp(p.opening / 150)                   # gap size (normalized)
        self.vision[3] = self.clamp(self.vel / 10)                    # current vertical speed

        if config.show_lines:
            pygame.draw.line(config.window, (255, 255, 255), self.rect.center, (self.rect.centerx, gap))
            pygame.draw.line(config.window, (255, 255, 255), self.rect.center, (p.x, self.rect.centery))

    def think(self, generation=1):
        if self.is_human:
            return

        # Before the first pipe is in range, hover near screen center
        first_pipe = self.closest_pipe()
        if not first_pipe:
            target_y = config.win_height * 0.45
            if self.rect.centery > target_y + 10:
                self.bird_flap(generation)
            return

        decision = self.brain.feed_forward(self.vision)

        # Light exploration noise that anneals over generations
        noise_scale = max(0.01, 0.08 * math.exp(-0.08 * generation))
        noisy_decision = decision + random.gauss(0, noise_scale)

        # >0.5  → flap, ≤0.5 → glide/drop
        if noisy_decision > 0.5:
            self.bird_flap(generation)

    def calculate_fitness(self):
        # Reward: surviving longer + passing pipes + being near the gap center
        gap_bonus = max(0, 1.0 - abs(self.vision[0])) * 100
        self.fitness = (self.lifespan * 2) + (self.score * 1000) + gap_bonus

    def clone(self):
        clone = Player()
        clone.brain = self.brain.clone()
        return clone

    def handle_event(self, event):
        if not self.is_human:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                self.bird_flap()
            if event.key == pygame.K_DOWN:
                self.bird_drop()


class BCPlayer(Player):
    """AI player controlled by a trained Behavioral Cloning model."""

    def __init__(self):
        super().__init__(is_human=False)
        self._bc_model = None
        # Tint sprite blue for visual distinction
        self.hk_run = self._tint_sprite(self.hk_run, (100, 150, 255))
        self.hk_air = self._tint_sprite(self.hk_air, (100, 150, 255))

    @staticmethod
    def _tint_sprite(surface, color):
        tinted = surface.copy()
        tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        return tinted

    def load_model(self):
        from behavioral_cloning import BCTrainer
        self._bc_model = BCTrainer.load_model()
        return self._bc_model is not None

    def think(self, generation=1):
        if self._bc_model is None:
            return
        self.look()
        action = self._bc_model.predict_action(self.vision)
        if action == 1:
            self.bird_flap(generation)
        elif action == -1:
            self.bird_drop()

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class DQNPlayer(Player):
    """AI player controlled by a trained DQN model."""

    def __init__(self):
        super().__init__(is_human=False)
        self._dqn_model = None
        # Tint sprite orange for visual distinction
        self.hk_run = self._tint_sprite(self.hk_run, (255, 180, 80))
        self.hk_air = self._tint_sprite(self.hk_air, (255, 180, 80))

    @staticmethod
    def _tint_sprite(surface, color):
        tinted = surface.copy()
        tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        return tinted

    def load_model(self):
        from dqn_agent import DQNAgent
        self._dqn_model = DQNAgent.load_model()
        return self._dqn_model is not None

    def think(self, generation=1):
        if self._dqn_model is None:
            return
        self.look()
        from dqn_agent import DQNAgent
        action = DQNAgent.predict_action(self._dqn_model, self.vision)
        if action == 1:
            self.bird_flap(generation)
        elif action == -1:
            self.bird_drop()

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class HeuristicPlayer(Player):
    """Mathematical AI that plays perfectly by targeting gap center."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((0, 255, 255), special_flags=pygame.BLEND_RGB_MULT) # Cyan
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((0, 255, 255), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if not p:
            if self.rect.centery > config.win_height * 0.45:
                self.bird_flap(generation)
            return
        
        gap_y = (p.top_rect.bottom + p.bottom_rect.top) / 2
        # Target exact center
        if self.rect.centery > gap_y + 15 and self.vel >= -2:
            self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class CautiousPlayer(Player):
    """Mathematical AI that prefers gliding low beneath the upper pipe."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((255, 50, 255), special_flags=pygame.BLEND_RGB_MULT) # Magenta
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((255, 50, 255), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if not p:
            if self.rect.centery > config.win_height * 0.55:
                self.bird_flap(generation)
            return
        
        # Target lower half of the gap
        safe_y = p.bottom_rect.top - 40
        if self.rect.centery > safe_y and self.vel >= -2:
            self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class AggressivePlayer(Player):
    """Mathematical AI that hugs the top pipe."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((255, 255, 50), special_flags=pygame.BLEND_RGB_MULT) # Yellow
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((255, 255, 50), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if not p:
            if self.rect.centery > config.win_height * 0.35:
                self.bird_flap(generation)
            return
        
        # Target upper half of the gap
        safe_y = p.top_rect.bottom + 40
        if self.rect.centery > safe_y and self.vel >= -2:
            self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class RandomPlayer(Player):
    """Flaps randomly."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_MULT)
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        if random.random() < 0.05:
            self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class LazyPlayer(Player):
    """Waits until the last moment to flap."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((100, 255, 100), special_flags=pygame.BLEND_RGB_MULT)
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((100, 255, 100), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if not p:
            if self.rect.centery > config.win_height * 0.8:
                self.bird_flap(generation)
            return
        
        # Target bottom of gap but wait until we are really dropping
        safe_y = p.bottom_rect.top - 20
        if self.rect.centery > safe_y and self.vel >= 3:
            self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class PanickyPlayer(Player):
    """Overcorrects frequently."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((255, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((255, 100, 100), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if not p:
            if self.rect.centery > config.win_height * 0.5:
                self.bird_flap(generation)
            return
        
        safe_y = p.top_rect.bottom + 60
        if self.rect.centery > safe_y and random.random() < 0.6:
            self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class CenterPlayer(Player):
    """Maintains center of screen until pipe is close."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MULT)
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if p and (p.x - self.rect.centerx) < 300:
            gap_y = (p.top_rect.bottom + p.bottom_rect.top) / 2
            if self.rect.centery > gap_y + 10 and self.vel >= -1:
                self.bird_flap(generation)
        else:
            if self.rect.centery > config.win_height * 0.5 and self.vel >= 0:
                self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)


class HighFlyerPlayer(Player):
    """Stays high and dives in."""
    def __init__(self):
        super().__init__(is_human=False)
        self.hk_run = self.hk_run.copy()
        self.hk_run.fill((255, 192, 203), special_flags=pygame.BLEND_RGB_MULT) # Pink
        self.hk_air = self.hk_air.copy()
        self.hk_air.fill((255, 192, 203), special_flags=pygame.BLEND_RGB_MULT)

    def think(self, generation=1):
        p = self.closest_pipe()
        if not p:
            if self.rect.centery > config.win_height * 0.2:
                self.bird_flap(generation)
            return
        
        if (p.x - self.rect.centerx) < 150:
            safe_y = p.bottom_rect.top - 60
            if self.rect.centery > safe_y and self.vel >= -2:
                self.bird_flap(generation)
        else:
            if self.rect.centery > config.win_height * 0.2 and self.vel >= 0:
                self.bird_flap(generation)

    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)
