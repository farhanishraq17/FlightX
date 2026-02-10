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

        self.brain = brain.Brain(self.inputs)
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
        # Small impulse; allow repeated taps without locking out
        if not self.sky_collision():
            boost_factor = 1.02 if generation % 10 == 0 else 1.0
            # Human players get much stronger jump
            human_multiplier = 3.5 if self.is_human else 1.0
            impulse = 2.2 * boost_factor * config.jump_scale * human_multiplier
            ceiling = -5 * boost_factor * config.jump_scale * human_multiplier
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
            target_y = config.win_height * 0.5
            if self.rect.centery < target_y - 5:
                self.bird_drop()
            elif self.rect.centery > target_y + 5:
                self.bird_flap(generation)
            return

        decision = self.brain.feed_forward(self.vision)

        # Anneal exploratory noise: higher early generations, near-zero after ~25
        fail_prob = max(0.02, 0.85 * math.exp(-0.12 * max(0, generation - 1)))
        if random.random() < fail_prob:
            return  # deliberately skip action to allow early failures

        noisy_decision = decision + random.uniform(-0.1, 0.1) * fail_prob

        # >0.55: small flap up; <0.45: nudge downward; middle: glide
        if noisy_decision > 0.55:
            self.bird_flap(generation)
        elif noisy_decision < 0.45:
            self.bird_drop()

    def calculate_fitness(self):
        center_penalty = abs(self.vision[0])
        self.fitness = self.lifespan + (self.score * 500) - (center_penalty * 50)

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
