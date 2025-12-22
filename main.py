import pygame
from sys import exit
import config
import components
import population

pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption('FlightX - Simulator')
config.create_window()
pygame.display.set_icon(pygame.image.load('Assets/aeroplane.jpg'))
config.reset_ground()

background_top = pygame.image.load('Assets/sky2.jpg').convert()
background_bottom = pygame.image.load('Assets/soil.jpg').convert()
main_menu_bg = pygame.image.load('Assets/mainmenu.png').convert_alpha()

population_manager = population.Population(100)
game_state = {'pipes_spawn_time': 10}

MENU_MAIN = 'main'
MENU_INSTRUCTIONS = 'instructions'
MENU_GAME = 'game'


def get_fonts():
    base = min(config.win_width, config.win_height)
    title_size = max(64, int(base * 0.2))
    menu_size = max(28, int(base * 0.08))
    author_size = max(32, int(base * 0.1))
    return (
        pygame.font.Font('font/Pixeltype.ttf', title_size),
        pygame.font.Font('font/Pixeltype.ttf', menu_size),
        pygame.font.Font('font/Pixeltype.ttf', author_size),
    )


def generate_pipes():
    config.pipes.append(components.Pipes(config.win_width))


def draw_background():
    ground_y = components.Ground.ground_level
    ground_h = getattr(config.ground, 'rect', pygame.Rect(0, 0, 0, 8)).height if config.ground else 8
    top_h = max(1, ground_y)
    bottom_y = ground_y + ground_h
    bottom_h = max(1, config.win_height - bottom_y)

    top_scaled = pygame.transform.smoothscale(background_top, (config.win_width, top_h))
    bottom_scaled = pygame.transform.smoothscale(background_bottom, (config.win_width, bottom_h))

    config.window.blit(top_scaled, (0, 0))
    config.window.blit(bottom_scaled, (0, bottom_y))


def handle_common_events(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit()
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_f:
            config.toggle_fullscreen()
        if event.key == pygame.K_m:
            config.mute = not config.mute
            if config.mute:
                pygame.mixer.pause()
            else:
                pygame.mixer.unpause()
    if event.type == pygame.VIDEORESIZE:
        config.resize(event.w, event.h)


def layout_main_menu(title_font, menu_font, author_font):
    min_side = min(config.win_width, config.win_height)
    padding = max(10, int(min_side * 0.02))
    gap = max(10, int(min_side * 0.015))

    title_surf = title_font.render('FlightX', True, (255, 255, 255))
    start_surf = menu_font.render('Start Game', True, (0, 0, 0))
    instruction_surf = menu_font.render('Instruction Manual', True, (0, 0, 0))
    mute_surf = menu_font.render(f'Audio: {"Off" if config.mute else "On"}', True, (0, 0, 0))
    exit_surf = menu_font.render('Exit', True, (0, 0, 0))
    author_surf = author_font.render('Author : Farhan Ishraq', True, (255, 255, 255))

    title_rect = title_surf.get_rect(center=(config.win_width // 2, int(config.win_height * 0.28)))

    option_surfaces = [start_surf, instruction_surf, mute_surf, exit_surf]
    option_actions = ['start', 'instructions', 'audio', 'exit']

    btn_height = max(s.get_height() + padding * 2 for s in option_surfaces)
    total_height = btn_height * len(option_surfaces) + gap * (len(option_surfaces) - 1)
    offset_down = max(10, int(min_side * 0.12))
    column_top = config.win_height // 2 - total_height // 2 + offset_down
    option_centers = [
        (config.win_width // 2, column_top + btn_height // 2 + i * (btn_height + gap))
        for i in range(len(option_surfaces))
    ]

    author_rect = author_surf.get_rect(midbottom=(config.win_width // 2, config.win_height - gap))

    fs_button_surf = menu_font.render('Fullscreen [F]', True, (0, 0, 0))
    fs_box = pygame.Surface(
        (fs_button_surf.get_width() + padding * 2, fs_button_surf.get_height() + padding * 2),
        pygame.SRCALPHA,
    )
    fs_box.fill((255, 255, 255, 200))
    fs_box_rect = fs_box.get_rect(topright=(config.win_width - padding, padding))
    fs_text_rect = fs_button_surf.get_rect(center=fs_box_rect.center)

    return {
        'padding': padding,
        'title': (title_surf, title_rect),
        'options': list(zip(option_surfaces, option_centers, option_actions)),
        'author': (author_surf, author_rect),
        'fs': (fs_box, fs_box_rect, fs_button_surf, fs_text_rect),
    }


def draw_main_menu(layout):
    config.window.fill((0, 0, 0))

    bg_scaled = pygame.transform.smoothscale(main_menu_bg, (config.win_width, config.win_height))
    bg_scaled.set_alpha(153)
    config.window.blit(bg_scaled, (0, 0))

    title_surf, title_rect = layout['title']
    config.window.blit(title_surf, title_rect)

    padding = layout['padding']
    mouse_pos = pygame.mouse.get_pos()
    buttons = []
    for surf, center, action in layout['options']:
        box = pygame.Surface(
            (surf.get_width() + padding * 2, surf.get_height() + padding * 2), pygame.SRCALPHA
        )
        box_rect = box.get_rect(center=center)
        text_rect = surf.get_rect(center=box_rect.center)
        hover = box_rect.collidepoint(mouse_pos)
        box.fill((230, 230, 230, 220) if hover else (255, 255, 255, 200))
        if hover:
            pygame.draw.rect(box, (50, 150, 255, 255), box.get_rect(), 2)
        config.window.blit(box, box_rect)
        config.window.blit(surf, text_rect)
        buttons.append((surf, box_rect, action))

    fs_box, fs_box_rect, fs_button_surf, fs_text_rect = layout['fs']
    config.window.blit(fs_box, fs_box_rect)
    config.window.blit(fs_button_surf, fs_text_rect)

    author_surf, author_rect = layout['author']
    config.window.blit(author_surf, author_rect)
    return buttons


def run_game_step():
    draw_background()

    config.ground.draw(config.window)

    if game_state['pipes_spawn_time'] <= 0:
        generate_pipes()
        game_state['pipes_spawn_time'] = 200
    game_state['pipes_spawn_time'] -= 1

    for p in list(config.pipes):
        p.draw(config.window)
        p.update()
        if p.off_screen:
            config.pipes.remove(p)

    if not population_manager.extinct():
        population_manager.update_live_players()
    else:
        config.pipes.clear()
        population_manager.natural_selection()


def render_game_placeholder(title_font):
    config.window.fill((0, 0, 0))
    bg_scaled = pygame.transform.smoothscale(main_menu_bg, (config.win_width, config.win_height))
    bg_scaled.set_alpha(153)
    config.window.blit(bg_scaled, (0, 0))
    text = title_font.render('GAME STARTED', True, (255, 255, 255))
    rect = text.get_rect(center=(config.win_width // 2, config.win_height // 2))
    config.window.blit(text, rect)


def render_instructions(menu_font):
    config.window.fill((0, 0, 0))
    bg_scaled = pygame.transform.smoothscale(main_menu_bg, (config.win_width, config.win_height))
    bg_scaled.set_alpha(153)
    config.window.blit(bg_scaled, (0, 0))

    lorem = (
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '
        'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in '
        'voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    )
    margin = 40
    max_width = config.win_width - margin * 2
    color = (255, 255, 255)

    def wrap_text(text, font, max_w):
        words = text.split(' ')
        lines = []
        current = ''
        for word in words:
            test = (current + ' ' + word).strip()
            if font.size(test)[0] <= max_w:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    lines = wrap_text(lorem, menu_font, max_width)
    y = margin
    for line in lines:
        surf = menu_font.render(line, True, color)
        rect = surf.get_rect(topleft=(margin, y))
        config.window.blit(surf, rect)
        y += surf.get_height() + 8

    back_surf = menu_font.render('Press ESC to return', True, (200, 200, 200))
    back_rect = back_surf.get_rect(bottomright=(config.win_width - margin, config.win_height - margin))
    config.window.blit(back_surf, back_rect)


def main():
    state = MENU_MAIN
    while True:
        title_font, menu_font, author_font = get_fonts()
        events = pygame.event.get()

        if state == MENU_MAIN:
            layout = layout_main_menu(title_font, menu_font, author_font)
            buttons = draw_main_menu(layout)
        elif state == MENU_INSTRUCTIONS:
            buttons = []
            render_instructions(menu_font)
        elif state == MENU_GAME:
            buttons = []
            run_game_step()

        for event in events:
            handle_common_events(event)

            if state == MENU_MAIN:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    for _, rect, action in buttons:
                        if rect.collidepoint(mouse_pos):
                            if action == 'start':
                                state = MENU_GAME
                                config.pipes.clear()
                                game_state['pipes_spawn_time'] = 10
                            elif action == 'instructions':
                                state = MENU_INSTRUCTIONS
                            elif action == 'audio':
                                config.mute = not config.mute
                                if config.mute:
                                    pygame.mixer.pause()
                                else:
                                    pygame.mixer.unpause()
                            elif action == 'exit':
                                pygame.quit()
                                exit()
            elif state == MENU_INSTRUCTIONS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU_MAIN
            elif state == MENU_GAME:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU_MAIN

        pygame.display.flip()
        clock.tick(60)


main()