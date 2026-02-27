import pygame
import random
import math


class Ground:
    ground_level = 500

    def __init__(self, win_width, win_height):
        Ground.ground_level = int(win_height * 0.8)
        self.x, self.y = 0, Ground.ground_level
        self.rect = pygame.Rect(self.x, self.y, win_width, 8)

    def draw(self, window):
        pygame.draw.rect(window, (255, 255, 255), self.rect)


class Pipes:
    width = 15

    def __init__(self, win_width):
        self.opening = random.randint(90, 130)
        self.x = win_width
        self.bottom_height = random.randint(10, 300)
        self.top_height = Ground.ground_level - self.bottom_height - self.opening
        self.bottom_rect, self.top_rect = pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0)
        self.passed = False
        self.counted = False
        self.off_screen = False

    def draw(self, window):
        self.bottom_rect = pygame.Rect(self.x, Ground.ground_level - self.bottom_height, self.width, self.bottom_height)
        pygame.draw.rect(window, (255, 255, 255), self.bottom_rect)

        self.top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        pygame.draw.rect(window, (255, 255, 255), self.top_rect)

    def update(self):
        self.x -= 1
        if self.x + Pipes.width <= 50:
            self.passed = True
        if self.x <= -self.width:
            self.off_screen = True


# ═══════════════════════════════════════════════════════════════
#  NEW OBSTACLES
# ═══════════════════════════════════════════════════════════════

class MovingPipes(Pipes):
    """Pipes that oscillate vertically, making the gap a moving target."""

    def __init__(self, win_width):
        super().__init__(win_width)
        self.base_bottom_height = self.bottom_height
        self.base_top_height = self.top_height
        self.amplitude = random.randint(20, 50)   # pixels of oscillation
        self.frequency = random.uniform(0.02, 0.05)  # speed of oscillation
        self.phase = random.uniform(0, 2 * math.pi)
        self.tick = 0

    def update(self):
        super().update()
        self.tick += 1
        shift = int(self.amplitude * math.sin(self.frequency * self.tick + self.phase))
        self.bottom_height = max(10, self.base_bottom_height + shift)
        self.top_height = max(10, Ground.ground_level - self.bottom_height - self.opening)

    def draw(self, window):
        # Draw with a distinct color (cyan) so player can see they're special
        self.bottom_rect = pygame.Rect(
            self.x, Ground.ground_level - self.bottom_height,
            self.width, self.bottom_height
        )
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)

        pygame.draw.rect(window, (0, 220, 220), self.bottom_rect)
        pygame.draw.rect(window, (0, 220, 220), self.top_rect)


class WindZone:
    """
    A transparent zone that applies a vertical force to any player passing
    through it.  Positive strength = upward push, negative = downward push.
    """
    WIDTH = 60

    def __init__(self, win_width):
        self.x = win_width
        self.y = random.randint(50, Ground.ground_level - 120)
        self.height = random.randint(80, 160)
        self.strength = random.choice([-0.35, -0.25, 0.25, 0.35])
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.height)
        self.off_screen = False
        # Visual
        self.alpha_tick = 0

    def update(self):
        self.x -= 1
        self.rect.x = self.x
        self.alpha_tick += 1
        if self.x <= -self.WIDTH:
            self.off_screen = True

    def draw(self, window):
        # Semi-transparent colored rectangle
        alpha = int(80 + 40 * math.sin(self.alpha_tick * 0.08))
        surf = pygame.Surface((self.WIDTH, self.height), pygame.SRCALPHA)
        if self.strength > 0:
            surf.fill((80, 255, 80, alpha))   # green = upward
        else:
            surf.fill((255, 80, 80, alpha))   # red = downward
        window.blit(surf, self.rect)

        # Arrow indicators
        arrow_color = (120, 255, 120) if self.strength > 0 else (255, 120, 120)
        cx = self.x + self.WIDTH // 2
        for ay in range(self.y + 15, self.y + self.height - 10, 30):
            if self.strength > 0:  # up arrow
                pygame.draw.polygon(window, arrow_color, [
                    (cx, ay - 8), (cx - 6, ay + 4), (cx + 6, ay + 4)
                ])
            else:  # down arrow
                pygame.draw.polygon(window, arrow_color, [
                    (cx - 6, ay - 4), (cx + 6, ay - 4), (cx, ay + 8)
                ])

    def affects(self, player_rect):
        """Check if a player rect is inside this wind zone."""
        return self.rect.colliderect(player_rect)

    def apply_force(self, player):
        """Apply wind force to a player if they're inside the zone."""
        if self.affects(player.rect):
            player.vel -= self.strength  # negative strength pushes down


class Coin:
    """
    Collectible coin placed in the middle between two pipes, centered at the gap.
    Awards bonus score when collected.
    """
    RADIUS = 8
    BONUS = 3

    def __init__(self, pipe_x, gap_y=None):
        """
        pipe_x: x position of the pipe that just spawned.
        gap_y:  vertical center of the pipe's gap (if available).
        """
        # Place coin midway between the pipe and the previous one (~100px before)
        self.x = pipe_x + 100
        # Vertically center at the gap if provided, else random safe position
        if gap_y is not None:
            self.y = gap_y
        else:
            self.y = random.randint(60, Ground.ground_level - 60)
        self.collected = False
        self.off_screen = False
        self.bob_tick = random.uniform(0, 2 * math.pi)

    def update(self):
        self.x -= 1
        self.bob_tick += 0.06
        if self.x <= -self.RADIUS:
            self.off_screen = True

    def draw(self, window):
        if self.collected:
            return
        bob_y = self.y + int(4 * math.sin(self.bob_tick))
        # Gold coin with glow
        glow_radius = self.RADIUS + 3 + int(2 * math.sin(self.bob_tick * 2))
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, 60), (glow_radius, glow_radius), glow_radius)
        window.blit(glow_surf, (self.x - glow_radius, bob_y - glow_radius))
        pygame.draw.circle(window, (255, 215, 0), (self.x, bob_y), self.RADIUS)
        pygame.draw.circle(window, (255, 255, 150), (self.x, bob_y), self.RADIUS, 2)

    def check_collect(self, player_rect):
        """Return True if collected by this player."""
        if self.collected:
            return False
        bob_y = self.y + int(4 * math.sin(self.bob_tick))
        coin_rect = pygame.Rect(self.x - self.RADIUS, bob_y - self.RADIUS,
                                self.RADIUS * 2, self.RADIUS * 2)
        if coin_rect.colliderect(player_rect):
            self.collected = True
            return True
        return False


class FlyingBlock:
    """
    A bird/block that flies horizontally at a random height.
    Unlocked at score >= 20.  Kills on contact.
    """
    SIZE = 18

    def __init__(self, win_width):
        self.x = win_width + random.randint(0, 100)
        self.y = random.randint(40, Ground.ground_level - 40)
        self.speed = random.uniform(1.5, 3.0)
        self.rect = pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)
        self.off_screen = False
        self.wing_tick = 0
        # Slight vertical wobble
        self.base_y = self.y
        self.wobble_amp = random.randint(5, 15)
        self.wobble_freq = random.uniform(0.03, 0.07)

    def update(self):
        self.x -= self.speed
        self.wing_tick += 1
        self.y = self.base_y + int(self.wobble_amp * math.sin(self.wobble_freq * self.wing_tick))
        self.rect.x = int(self.x)
        self.rect.y = self.y
        if self.x <= -self.SIZE:
            self.off_screen = True

    def draw(self, window):
        # Body (dark red)
        pygame.draw.rect(window, (200, 50, 50), self.rect)
        # "Wings" that flap
        wing_offset = int(4 * math.sin(self.wing_tick * 0.15))
        left_wing = pygame.Rect(self.rect.x - 5, self.rect.y + 4 + wing_offset, 5, 8)
        right_wing = pygame.Rect(self.rect.right, self.rect.y + 4 - wing_offset, 5, 8)
        pygame.draw.rect(window, (220, 80, 80), left_wing)
        pygame.draw.rect(window, (220, 80, 80), right_wing)
        # Eye
        pygame.draw.circle(window, (255, 255, 255),
                           (self.rect.right - 4, self.rect.y + 5), 3)
        pygame.draw.circle(window, (0, 0, 0),
                           (self.rect.right - 3, self.rect.y + 5), 1)

    def check_collision(self, player_rect):
        return self.rect.colliderect(player_rect)


class FallingObstacle:
    """
    An obstacle that falls vertically from the top of the screen.
    Unlocked at score >= 15.  Kills on contact.
    """
    WIDTH = 16
    HEIGHT = 16

    def __init__(self, win_width):
        self.x = random.randint(50, win_width - 50)
        self.y = -self.HEIGHT  # start above screen
        self.fall_speed = random.uniform(1.5, 3.5)
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        self.off_screen = False
        self.rotation = 0
        self.rot_speed = random.uniform(2.0, 6.0)

    def update(self):
        self.y += self.fall_speed
        self.rotation += self.rot_speed
        self.rect.y = int(self.y)
        if self.y > Ground.ground_level + 20:
            self.off_screen = True

    def draw(self, window):
        # Rotating spiky rock
        cx = self.x + self.WIDTH // 2
        cy = int(self.y) + self.HEIGHT // 2
        r = self.WIDTH // 2
        # Draw as a rotating diamond/spike shape
        angle_rad = math.radians(self.rotation)
        points = []
        for i in range(4):
            a = angle_rad + math.pi / 2 * i
            spike_r = r + 4 if i % 2 == 0 else r - 2
            px = cx + int(spike_r * math.cos(a))
            py = cy + int(spike_r * math.sin(a))
            points.append((px, py))
        pygame.draw.polygon(window, (180, 100, 0), points)
        pygame.draw.polygon(window, (255, 150, 50), points, 2)
        # Warning indicator line from top
        if self.y < 50:
            pygame.draw.line(window, (255, 150, 50, 120), (cx, 0), (cx, int(self.y)), 1)

    def check_collision(self, player_rect):
        return self.rect.colliderect(player_rect)


class MultiHolePipes:
    """
    Pipes with 2-3 gaps instead of 1.  Only one gap is the real safe
    passage (widest); the others are decoy narrow gaps.
    Unlocked at score >= 30.
    """
    width = 15

    def __init__(self, win_width):
        self.x = win_width
        self.passed = False
        self.counted = False
        self.off_screen = False

        num_holes = random.choice([2, 2, 3])
        total = Ground.ground_level
        min_gap = 60
        real_gap = random.randint(85, 115)

        # Generate segment boundaries
        segments = []
        remaining = total
        gaps = []
        for i in range(num_holes):
            gap = real_gap if i == 0 else random.randint(min_gap, min_gap + 15)
            gaps.append(gap)
        total_gap = sum(gaps)
        total_wall = remaining - total_gap
        if total_wall < num_holes + 1:
            total_wall = num_holes + 1

        # Distribute wall sections
        walls = []
        for i in range(num_holes + 1):
            w = random.randint(15, max(20, total_wall // (num_holes + 1) + 10))
            walls.append(w)
        # Scale walls to fit
        wall_sum = sum(walls)
        scale = total_wall / max(wall_sum, 1)
        walls = [max(8, int(w * scale)) for w in walls]

        # Build rects: wall, gap, wall, gap, wall, ...
        self.wall_rects = []
        self.gap_positions = []
        y = 0
        for i in range(num_holes):
            wall_h = walls[i]
            self.wall_rects.append(pygame.Rect(self.x, y, self.width, wall_h))
            y += wall_h
            self.gap_positions.append((y, gaps[i]))
            y += gaps[i]
        # Final wall
        final_h = Ground.ground_level - y
        if final_h > 0:
            self.wall_rects.append(pygame.Rect(self.x, y, self.width, final_h))

        # For collision compatibility
        self.bottom_rect = self.wall_rects[-1] if self.wall_rects else pygame.Rect(0, 0, 0, 0)
        self.top_rect = self.wall_rects[0] if self.wall_rects else pygame.Rect(0, 0, 0, 0)
        # Opening — use the largest gap
        self.opening = max(gaps)
        self.bottom_height = self.bottom_rect.height if self.wall_rects else 0
        self.top_height = self.top_rect.height if self.wall_rects else 0

    def update(self):
        self.x -= 1
        for r in self.wall_rects:
            r.x = self.x
        self.bottom_rect.x = self.x
        self.top_rect.x = self.x
        if self.x + self.width <= 50:
            self.passed = True
        if self.x <= -self.width:
            self.off_screen = True

    def draw(self, window):
        for r in self.wall_rects:
            pygame.draw.rect(window, (255, 160, 0), r)  # Orange for multi-hole






