import pygame
import brain
import config


class Player:
    def __init__(self):
        # Bird
        self.x, self.y = 50, 200
        self.hk_run = pygame.transform.smoothscale(
            pygame.image.load('Assets/hk_1.png').convert_alpha(), (40, 40)
        )
        self.hk_air = pygame.transform.smoothscale(
            pygame.image.load('Assets/hk_2.png').convert_alpha(), (40, 40)
        )

        self.rect = self.hk_run.get_rect(topleft=(self.x, self.y)).inflate(-12, -12)

        self.vel = 0
        self.alive = True
        self.on_ground = False
        self.lifespan = 0
        self.vision = [0, 0, 0, 0]
        self.fitness = 0
        self.inputs = 4

        self.brain = brain.Brain(self.inputs)
        self.brain.generate_net()
    # ---------------- Utility ----------------
    def clamp(self, v, lo=-1, hi=1):
        return max(lo, min(hi, v))

    # ---------------- Game Logic ----------------
    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
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

    def bird_flap(self):
        # Small impulse; allow repeated taps without locking out
        if not self.sky_collision():
            self.vel = max(self.vel - 2.2, -5)

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
        self.vision[2] = 0                                            # unused slot reserved
        self.vision[3] = self.clamp(self.vel / 10)                    # current vertical speed

    def think(self):
        decision = self.brain.feed_forward(self.vision)
        # >0.55: small flap up; <0.45: nudge downward; middle: glide
        if decision > 0.55:
            self.bird_flap()
        elif decision < 0.45:
            self.bird_drop()

    def calculate_fitness(self):
        center_penalty = abs(self.vision[0])
        self.fitness = self.lifespan * 1.5 - center_penalty * 100

    def clone(self):
        clone = Player()
        clone.brain = self.brain.clone()
        return clone
