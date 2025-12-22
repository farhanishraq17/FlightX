import pygame

# Colors
BG_COLOR = (15, 18, 24)
BTN_COLOR = (235, 235, 235)
BTN_HOVER = (245, 245, 245)
TEXT_COLOR = (20, 22, 26)
SHADOW_COLOR = (0, 0, 0, 70)


def get_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.SysFont("Consolas", size)
    except Exception:
        return pygame.font.SysFont("Arial", size)


class Button:
    def __init__(self, text: str, center: tuple[int, int], size: tuple[int, int], font: pygame.font.Font):
        self.text = text
        self.center = center
        self.size = size
        self.font = font
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.corner_radius = 12
        self.shadow_offset = (0, 4)

    def draw(self, surface: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        hovering = self.rect.collidepoint(mouse_pos)

        # Shadow
        shadow_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            SHADOW_COLOR,
            shadow_surf.get_rect(),
            border_radius=self.corner_radius,
        )
        surface.blit(shadow_surf, (self.rect.x + self.shadow_offset[0], self.rect.y + self.shadow_offset[1]))

        # Button face
        face_color = BTN_HOVER if hovering else BTN_COLOR
        pygame.draw.rect(surface, face_color, self.rect, border_radius=self.corner_radius)

        # Text
        label = self.font.render(self.text, True, TEXT_COLOR)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("FlightX - Menu Buttons Demo")

    font = get_font(32)
    labels = ["Start Game", "Instruction Manual", "Audio : On", "Exit"]

    # Layout: center column with even spacing
    col_x = screen.get_width() // 2
    top_y = screen.get_height() // 2 - 120
    vertical_spacing = 80
    btn_size = (320, 64)

    buttons = []
    for i, label in enumerate(labels):
        center = (col_x, top_y + i * vertical_spacing)
        buttons.append(Button(label, center, btn_size, font))

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for btn in buttons:
                if btn.is_clicked(event):
                    print(f"Clicked: {btn.text}")

        screen.fill(BG_COLOR)
        for btn in buttons:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
