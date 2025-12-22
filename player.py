import brain
import pygame
import config


class Player:
    def __init__(self):
        # Bird
        self.x, self.y = 50, 200
        self.hk_run = pygame.transform.smoothscale(
            pygame.image.load('Assets/hk_1.png').convert_alpha(), (40, 40))
        self.hk_air = pygame.transform.smoothscale(
            pygame.image.load('Assets/hk_2.png').convert_alpha(), (40, 40))
        self.rect = self.hk_run.get_rect(topleft=(self.x, self.y)).inflate(-12, -12)

        self.vel = 0
        self.flap = False
        self.alive = True
        self.lifespan = 0
        self.on_ground = False

        # AI
        self.decision = None
        self.vision = [0.5, 1, 0.5]
        self.fitness = 0
        self.inputs = 3
        self.brain = brain.Brain(self.inputs)
        self.brain.generate_net()

    # Game related functions
    def draw(self, window):
        sprite = self.hk_air if self.vel < -0.1 else self.hk_run
        window.blit(sprite, self.rect)

    def ground_collision(self, ground):
        return pygame.Rect.colliderect(self.rect, ground)

    def sky_collision(self):
        return self.rect.top < 0


    def pipe_collision(self):
        closest = self.closest_pipe()
        if closest:
            return (
                self.rect.colliderect(closest.top_rect) or
                self.rect.colliderect(closest.bottom_rect)
            )
        return False


    def update(self, ground):
        if not (self.ground_collision(ground) or self.pipe_collision()):
            # Gravity
            self.vel += 0.25
            self.rect.y += self.vel
            if self.vel > 5:
                self.vel = 5
            self.on_ground = False
            # Increment lifespan
            self.lifespan += 1
        else:
            self.on_ground = True
            self.alive = False
            self.flap = False
            self.vel = 0

    def bird_flap(self):
        if not self.flap and not self.sky_collision():
            self.flap = True
            self.vel = -5
        if self.vel >= 3:
            self.flap = False

    @staticmethod
    def closest_pipe():
        for p in config.pipes:
            if not p.passed:
                return p
        return None


    # AI related functions
    def look(self):
        if config.pipes:
            closest = self.closest_pipe()

            # Line to top pipe
            self.vision[0] = max(0, self.rect.center[1] - closest.top_rect.bottom) / 500
            pygame.draw.line(config.window, (255, 255, 255), self.rect.center,
                             (self.rect.center[0], closest.top_rect.bottom))

            # Line to mid pipe
            self.vision[1] = max(0, closest.x - self.rect.center[0]) / 500
            pygame.draw.line(config.window, (255, 255, 255), self.rect.center,
                             (closest.x, self.rect.center[1]))

            # Line to bottom pipe
            self.vision[2] = max(0, closest.bottom_rect.top - self.rect.center[1]) / 500
            pygame.draw.line(config.window, (255, 255, 255), self.rect.center,
                             (self.rect.center[0], closest.bottom_rect.top))

    def think(self):
        self.decision = self.brain.feed_forward(self.vision)
        if self.decision > 0.73:
            self.bird_flap()

    def calculate_fitness(self):
        self.fitness = self.lifespan

    def clone(self):
        clone = Player()
        clone.fitness = self.fitness
        clone.brain = self.brain.clone()
        clone.brain.generate_net()
        return clone