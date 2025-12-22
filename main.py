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
background_bottom = pygame.image.load('Assets/dark1.jpg').convert()
main_menu_bg = pygame.image.load('Assets/mainmenu.png').convert_alpha()

population_manager = population.Population(100)
game_state = {'pipes_spawn_time': 10, 'score': 0, 'high_score': 0}
ui_state = {
    'simulation_speed': 0.0,
    'slider_dragging': False,
    'is_paused': False,
}

MENU_MAIN = 'main'
MENU_INSTRUCTIONS = 'instructions'
MENU_GAME = 'game'


def get_fonts():
    base = min(config.win_width, config.win_height)
    title_size = max(64, int(base * 0.3))
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


def restart_simulation():
    global population_manager
    population_manager = population.Population(100)
    population_manager.generation = 0
    config.pipes.clear()
    game_state['pipes_spawn_time'] = 10
    game_state['score'] = 0
    game_state['high_score'] = 0
    ui_state['is_paused'] = False


def update_slider_from_mouse(x_pos, track_rect):
    ratio = max(0.0, min(1.0, (x_pos - track_rect.left) / track_rect.width))
    ui_state['simulation_speed'] = round(ratio * 10.0, 2)


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

    def simulation_tick():
        if game_state['pipes_spawn_time'] <= 0:
            generate_pipes()
            game_state['pipes_spawn_time'] = 200
        game_state['pipes_spawn_time'] -= 1

        for p in list(config.pipes):
            p.update()
            if p.passed and not p.counted:
                game_state['score'] += 1
                if game_state['score'] > game_state['high_score']:
                    game_state['high_score'] = game_state['score']
                p.counted = True
            if p.off_screen:
                config.pipes.remove(p)

        if not population_manager.extinct():
            population_manager.update_live_players()
        else:
            config.pipes.clear()
            population_manager.natural_selection()
            game_state['score'] = 0

    if not ui_state['is_paused']:
        ticks = max(1, int(round(ui_state['simulation_speed'])))
        for _ in range(ticks):
            simulation_tick()

    for p in list(config.pipes):
        p.draw(config.window)
    for pl in population_manager.players:
        if pl.alive:
            pl.draw(config.window)


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


def draw_control_panel(menu_font):
    ground_y = components.Ground.ground_level
    ground_h = getattr(config.ground, 'rect', pygame.Rect(0, 0, 0, 8)).height if config.ground else 8
    panel_y = ground_y + ground_h
    panel_rect = pygame.Rect(0, panel_y, config.win_width, max(60, config.win_height - panel_y))
    pygame.draw.rect(config.window, (0, 0, 0), panel_rect)

    padding = max(12, int(config.win_width * 0.01))
    white = (255, 255, 255)
    dark = (20, 20, 20)
    grey = (180, 180, 180)

    # Iteration counter top-right
    iter_font = pygame.font.Font('font/Pixeltype.ttf', max(22, int(menu_font.get_height() * 0.95)))
    iter_text = iter_font.render(f'Number of Iterations: {population_manager.generation}', True, white)
    iter_rect = iter_text.get_rect(topright=(panel_rect.right - padding, panel_rect.top + padding))
    config.window.blit(iter_text, iter_rect)

    score_text = iter_font.render(f'Score: {game_state["score"]}', True, white)
    score_rect = score_text.get_rect(topright=(panel_rect.right - padding, iter_rect.bottom + 8))

    high_text = iter_font.render(f'Max Score: {game_state["high_score"]}', True, white)
    high_rect = high_text.get_rect(topright=(score_rect.left - padding, score_rect.top))

    config.window.blit(high_text, high_rect)
    config.window.blit(score_text, score_rect)

    # Simulation speed slider top-left
    slider_width = max(180, int(config.win_width * 0.22))
    slider_track = pygame.Rect(panel_rect.left + padding, panel_rect.top + padding, slider_width, 12)
    pygame.draw.rect(config.window, grey, slider_track, border_radius=6)
    knob_x = slider_track.left + (ui_state['simulation_speed'] / 10.0) * slider_track.width
    knob_rect = pygame.Rect(0, 0, 18, 24)
    knob_rect.center = (knob_x, slider_track.centery)
    pygame.draw.rect(config.window, white, knob_rect, border_radius=6)
    speed_label = menu_font.render(f'Speed: {ui_state["simulation_speed"]:.1f}', True, white)
    speed_rect = speed_label.get_rect(left=slider_track.left, top=slider_track.bottom + 6)
    config.window.blit(speed_label, speed_rect)

    # Lines toggle
    toggle_w = max(180, int(config.win_width * 0.22))
    toggle_h = max(36, int(menu_font.get_height() * 1.2))
    toggle_rect = pygame.Rect(slider_track.left, speed_rect.bottom + max(12, int(menu_font.get_height() * 0.5)), toggle_w, toggle_h)
    pygame.draw.rect(config.window, white, toggle_rect, border_radius=6)
    toggle_label = menu_font.render(f'Lines: {"ON" if config.show_lines else "OFF"}', True, dark)
    config.window.blit(toggle_label, toggle_label.get_rect(center=toggle_rect.center))

    # Pause / Restart center
    center_x = panel_rect.centerx
    btn_w = max(160, int(config.win_width * 0.18))
    btn_h = max(44, int(menu_font.get_height() * 1.6))
    pause_rect = pygame.Rect(0, 0, btn_w, btn_h)
    vertical_offset = max(8, int(panel_rect.height * 0.04))
    pause_rect.center = (center_x, panel_rect.top + panel_rect.height * 0.32)
    restart_rect = pygame.Rect(0, 0, btn_w, btn_h)
    restart_rect.center = (center_x, pause_rect.bottom + vertical_offset + restart_rect.height // 2)
    pygame.draw.rect(config.window, white, pause_rect, border_radius=6)
    pygame.draw.rect(config.window, white, restart_rect, border_radius=6)
    pause_label = menu_font.render('Pause' if not ui_state['is_paused'] else 'Resume', True, dark)
    restart_label = menu_font.render('Restart', True, dark)
    config.window.blit(pause_label, pause_label.get_rect(center=pause_rect.center))
    config.window.blit(restart_label, restart_label.get_rect(center=restart_rect.center))

    # Back to menu bottom-right
    back_rect = pygame.Rect(0, 0, max(260, int(config.win_width * 0.24)), max(48, int(menu_font.get_height() * 1.6)))
    back_rect.bottomright = (panel_rect.right - padding, panel_rect.bottom - padding)
    pygame.draw.rect(config.window, white, back_rect, border_radius=6)
    back_label = menu_font.render('Back to Menu', True, dark)
    config.window.blit(back_label, back_label.get_rect(center=back_rect.center))

    return {
        'slider_track': slider_track,
        'slider_knob': knob_rect,
        'lines_toggle': toggle_rect,
        'pause': pause_rect,
        'restart': restart_rect,
        'back': back_rect,
    }


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
            control_rects = draw_control_panel(menu_font)

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
                                game_state['score'] = 0
                                game_state['high_score'] = 0
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
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if control_rects['slider_track'].collidepoint(event.pos) or control_rects['slider_knob'].collidepoint(event.pos):
                        ui_state['slider_dragging'] = True
                        update_slider_from_mouse(event.pos[0], control_rects['slider_track'])
                    elif control_rects['lines_toggle'].collidepoint(event.pos):
                        config.show_lines = not config.show_lines
                    elif control_rects['pause'].collidepoint(event.pos):
                        ui_state['is_paused'] = not ui_state['is_paused']
                    elif control_rects['restart'].collidepoint(event.pos):
                        restart_simulation()
                    elif control_rects['back'].collidepoint(event.pos):
                        state = MENU_MAIN
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    ui_state['slider_dragging'] = False
                if event.type == pygame.MOUSEMOTION and ui_state['slider_dragging']:
                    update_slider_from_mouse(event.pos[0], control_rects['slider_track'])
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU_MAIN

        pygame.display.flip()
        clock.tick(60)


main()