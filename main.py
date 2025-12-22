import os
import pygame
from sys import exit
import config
import components
import population
import matplotlib

try:
    matplotlib.use('TkAgg')
except Exception:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

INTERACTIVE_BACKEND = matplotlib.get_backend().lower() != 'agg'

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
graph_state = {'data': [], 'last_logged_gen': None, 'dirty': False}
ui_state = {
    'simulation_speed': 0.0,
    'slider_dragging': False,
        'jump_dragging': False,
    'is_paused': False,
}

music_tracks = {
    'menu': 'Audio/main_menu.wav',
    'none': None,
}
current_music = None
click_sound = None

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


def load_sounds():
    global click_sound
    try:
        click_sound = pygame.mixer.Sound('Audio/press_button.mp3')
        click_sound.set_volume(0.6)
    except pygame.error:
        click_sound = None


def play_click():
    if click_sound and not config.mute:
        click_sound.play()


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
    graph_state['data'].clear()
    graph_state['last_logged_gen'] = None
    graph_state['dirty'] = False
    load_sounds()


def update_slider_from_mouse(x_pos, track_rect):
    ratio = max(0.0, min(1.0, (x_pos - track_rect.left) / track_rect.width))
    ui_state['simulation_speed'] = round(ratio * 10.0, 2)


def update_jump_from_mouse(x_pos, track_rect):
    ratio = max(0.0, min(1.0, (x_pos - track_rect.left) / track_rect.width))
    # Map to 0.5x - 2.0x
    config.jump_scale = round(0.5 + ratio * 1.5, 2)


def handle_common_events(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit()
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_f:
            config.toggle_fullscreen()
        if event.key == pygame.K_m:
            config.mute = not config.mute
            set_music(current_music or 'menu')
    if event.type == pygame.VIDEORESIZE:
        config.resize(event.w, event.h)


def set_music(track):
    global current_music
    # If muted, pause and zero volume regardless of requested track
    if config.mute:
        pygame.mixer.music.pause()
        pygame.mixer.music.set_volume(0.0)
        return

    # Unmuted path: ensure correct track is playing
    if track is None or music_tracks.get(track) is None:
        pygame.mixer.music.stop()
        current_music = None
        return

    path = music_tracks.get(track)
    if current_music != track:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            current_music = track
        except pygame.error:
            current_music = None
            return

    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.unpause()


def layout_main_menu(title_font, menu_font, author_font):
    min_side = min(config.win_width, config.win_height)
    padding = max(10, int(min_side * 0.02))
    gap = max(10, int(min_side * 0.015))

    title_surf = title_font.render('FlightX', True, (255, 255, 255))
    start_surf = menu_font.render('Start Simulation', True, (0, 0, 0))
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


def update_graph_data():
    # Capture score every 3 iterations (generations)
    current_gen = population_manager.generation
    if current_gen == graph_state['last_logged_gen']:
        return
    graph_state['last_logged_gen'] = current_gen
    if current_gen % 3 != 0:
        return
    graph_state['data'].append((current_gen, game_state['high_score']))
    graph_state['dirty'] = True


def render_graph(save_path=None, show_window=False, force=False):
    if force and not graph_state['data']:
        graph_state['data'].append((population_manager.generation, game_state['high_score']))
    if not graph_state['data']:
        return

    xs, ys = zip(*graph_state['data'])
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(xs, ys, marker='o', linestyle='-', color='skyblue', label='Total Score')

    max_idx = max(range(len(ys)), key=lambda i: ys[i]) if ys else 0
    ax.scatter([xs[max_idx]], [ys[max_idx]], color='crimson', marker='*', s=140, label='Interval High')

    ax.set_xlabel('Iteration (every 3)')
    ax.set_ylabel('Total Score')
    if xs:
        ax.set_xticks(xs)
    y_max = max(ys) if ys else 10
    y_limit = max(10, (int(y_max / 10) + 1) * 10)
    ax.set_yticks(list(range(0, y_limit + 1, 10)))
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)

    if show_window:
        if INTERACTIVE_BACKEND:
            fig.canvas.manager.set_window_title('Score Graph')
            fig.canvas.draw_idle()
            plt.show(block=True)
            plt.close(fig)
        else:
            target = save_path or 'score_graph.png'
            fig.savefig(target)
            try:
                os.startfile(target)
            except Exception:
                pass
            plt.close(fig)
    else:
        plt.close(fig)

    graph_state['dirty'] = False


def generate_graph_image(force=False):
    render_graph(save_path='score_graph.png', show_window=False, force=force)


def show_graph_window():
    render_graph(save_path='score_graph.png', show_window=True, force=True)


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

    instr_font = pygame.font.Font('font/Pixeltype.ttf', max(32, int(menu_font.get_height() * 1.05)))

    lorem = (
        'FlightX Control Panel Guide\n\n'
        'Speed Bar: Drag to adjust simulation speed (0-10).\n\n'
        'Plane Count: Set number of agents (applies after Restart).\n\n'
        'Lines Off: Toggle AI vision lines on/off.\n\n'
        'Stats: View active Jumps, Alive Agents, and Reward.\n\n'
        'Pause: Freeze the simulation.\n\n'
        'Restart: Reset the simulation and apply new settings.\n\n'
        'Back: Return to the Main Menu.\n\n'
        'Generate Graph: Create and view the score graph image.'
    )
    outer_pad = max(32, int(min(config.win_width, config.win_height) * 0.03))
    box_w = min(config.win_width - outer_pad * 2, int(config.win_width * 0.82))
    box_h = min(config.win_height - outer_pad * 2, int(config.win_height * 0.78))
    box_rect = pygame.Rect(0, 0, box_w, box_h)
    box_rect.center = (config.win_width // 2, config.win_height // 2)
    panel = pygame.Surface(box_rect.size, pygame.SRCALPHA)
    panel.fill((50, 50, 50, 210))
    pygame.draw.rect(panel, (220, 220, 220, 230), panel.get_rect(), width=2, border_radius=12)
    config.window.blit(panel, box_rect.topleft)

    inner_pad = max(18, int(instr_font.get_height() * 0.6))
    max_width = box_rect.width - inner_pad * 2
    color = (240, 240, 240)

    def wrap_text(text, font, max_w):
        lines = []
        for block in text.split('\n'):
            if not block:
                lines.append('')
                continue
            words = block.split(' ')
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

    lines = wrap_text(lorem, instr_font, max_width)
    y = box_rect.top + inner_pad
    first_line = True
    for line in lines:
        surf = instr_font.render(line, True, color)
        if first_line and line.strip().startswith('FlightX Control Panel Guide'):
            rect = surf.get_rect(midtop=(box_rect.centerx, y))
        else:
            rect = surf.get_rect(topleft=(box_rect.left + inner_pad, y))
        config.window.blit(surf, rect)
        y += surf.get_height() + 10
        first_line = False

    back_font = pygame.font.Font('font/Pixeltype.ttf', max(20, int(menu_font.get_height() * 0.8)))
    back_surf = back_font.render('Press ESC to return', True, (210, 210, 210))
    back_rect = back_surf.get_rect(bottomright=(box_rect.right - inner_pad, box_rect.bottom - inner_pad))
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

    update_graph_data()
    if graph_state['dirty']:
        generate_graph_image()

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

    # Jump control slider
    jump_track = pygame.Rect(slider_track.left, speed_rect.bottom + max(10, int(menu_font.get_height() * 0.4)), slider_width, 12)
    pygame.draw.rect(config.window, grey, jump_track, border_radius=6)
    jump_ratio = (config.jump_scale - 0.5) / 1.5
    jump_knob_x = jump_track.left + jump_ratio * jump_track.width
    jump_knob = pygame.Rect(0, 0, 18, 24)
    jump_knob.center = (jump_knob_x, jump_track.centery)
    pygame.draw.rect(config.window, white, jump_knob, border_radius=6)
    jump_label = menu_font.render(f'Jump: {config.jump_scale:.2f}x', True, white)
    jump_rect = jump_label.get_rect(left=jump_track.left, top=jump_track.bottom + 6)
    config.window.blit(jump_label, jump_rect)

    # Lines toggle (auto-stacks if narrow)
    toggle_w = max(180, int(config.win_width * 0.22))
    toggle_h = max(36, int(menu_font.get_height() * 1.2))
    toggle_gap = max(12, int(config.win_width * 0.01))
    place_side = (panel_rect.right - padding) - (jump_track.right + toggle_gap) >= toggle_w + 12 and config.win_width >= 900
    if place_side:
        toggle_x = jump_track.right + toggle_gap
        toggle_x = min(toggle_x, panel_rect.right - padding - toggle_w)
        toggle_y = jump_track.top + max(18, int(menu_font.get_height() * 0.4))
    else:
        toggle_w = min(toggle_w, panel_rect.width - padding * 2)
        toggle_x = panel_rect.left + padding
        toggle_y = jump_rect.bottom + max(10, int(menu_font.get_height() * 0.5))
    toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_w, toggle_h)
    pygame.draw.rect(config.window, white, toggle_rect, border_radius=6)
    toggle_label = menu_font.render(f'Lines: {"ON" if config.show_lines else "OFF"}', True, dark)
    config.window.blit(toggle_label, toggle_label.get_rect(center=toggle_rect.center))

    # Pause / Restart shifted right but clamped
    btn_w = max(160, int(config.win_width * 0.18))
    btn_h = max(44, int(menu_font.get_height() * 1.6))
    right_column_left = min(iter_rect.left, score_rect.left, high_rect.left)
    target_x = right_column_left - padding - btn_w // 2
    center_x = min(panel_rect.centerx + max(140, int(config.win_width * 0.12)), target_x)
    if not config.fullscreen:
        center_x -= max(40, int(config.win_width * 0.04))
    center_x = max(center_x, panel_rect.left + padding + btn_w // 2)

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

    # Info box (Reward/Punishment/Jump/Planes) floats between slider and pause/restart, above the lines toggle
    info_font = pygame.font.Font('font/Pixeltype.ttf', max(14, int(menu_font.get_height() * 0.65)))
    alive_count = sum(1 for p in population_manager.players if p.alive)
    jump_factor = 1.02 if population_manager.generation % 10 == 0 else 1.0
    jump_impulse = round(2.2 * jump_factor * config.jump_scale, 2)
    info_items = [
        'Reward: +7',
        'Punishment: -1000',
        f'Jump: {jump_impulse}',
        f'Planes Alive: {alive_count}/{len(population_manager.players)}',
    ]
    line_surfs = [info_font.render(t, True, white) for t in info_items]
    box_padding = max(5, int(config.win_width * 0.0040))
    box_width = max(s.get_width() for s in line_surfs) + box_padding * 2
    box_height = sum(s.get_height() for s in line_surfs) + box_padding * 2 + (len(line_surfs) - 1) * 3

    min_x = slider_track.right + padding
    max_x = pause_rect.left - padding - box_width
    if max_x < min_x:
        box_x = max_x
    else:
        box_x = min_x
    box_x = max(panel_rect.left + padding, min(box_x, panel_rect.right - padding - box_width))

    up_shift = max(4, int(menu_font.get_height() * 0.1))
    desired_y = slider_track.top - up_shift
    limit_y = toggle_rect.top - padding - box_height
    box_y = max(panel_rect.top + padding, min(desired_y, limit_y))

    info_box = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(config.window, (30, 30, 30), info_box, border_radius=6)
    pygame.draw.rect(config.window, white, info_box, width=1, border_radius=6)

    cursor_y = info_box.top + box_padding
    for surf in line_surfs:
        rect = surf.get_rect(left=info_box.left + box_padding, top=cursor_y)
        config.window.blit(surf, rect)
        cursor_y += surf.get_height() + 3

    # Graph box to the right of info box
    box_gap = max(10, int(config.win_width * 0.01))
    graph_x = min(pause_rect.left - padding - box_width, info_box.right + box_gap)
    graph_x = max(panel_rect.left + padding, min(graph_x, panel_rect.right - padding - box_width))
    graph_y = box_y
    graph_box = pygame.Rect(graph_x, graph_y, box_width, box_height)
    pygame.draw.rect(config.window, (30, 30, 30), graph_box, border_radius=6)
    pygame.draw.rect(config.window, white, graph_box, width=1, border_radius=6)
    graph_font = pygame.font.Font('font/Pixeltype.ttf', max(16, int(menu_font.get_height() * 0.8)))
    graph_line1 = graph_font.render('Generate', True, white)
    graph_line2 = graph_font.render('Graph', True, white)
    total_h = graph_line1.get_height() + graph_line2.get_height() + 2
    start_y = graph_box.centery - total_h // 2
    config.window.blit(graph_line1, graph_line1.get_rect(center=(graph_box.centerx, start_y + graph_line1.get_height() // 2)))
    config.window.blit(graph_line2, graph_line2.get_rect(center=(graph_box.centerx, start_y + graph_line1.get_height() + 2 + graph_line2.get_height() // 2)))

    # Back to menu bottom-right
    back_rect = pygame.Rect(0, 0, max(260, int(config.win_width * 0.24)), max(48, int(menu_font.get_height() * 1.6)))
    back_rect.bottomright = (panel_rect.right - padding, panel_rect.bottom - padding)
    pygame.draw.rect(config.window, white, back_rect, border_radius=6)
    back_label = menu_font.render('Back to Menu', True, dark)
    config.window.blit(back_label, back_label.get_rect(center=back_rect.center))

    return {
        'slider_track': slider_track,
        'slider_knob': knob_rect,
        'jump_track': jump_track,
        'jump_knob': jump_knob,
        'lines_toggle': toggle_rect,
        'pause': pause_rect,
        'restart': restart_rect,
        'graph': graph_box,
        'back': back_rect,
    }


def main():
    state = MENU_MAIN
    load_sounds()
    set_music('menu')
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
                                play_click()
                                state = MENU_GAME
                                config.pipes.clear()
                                game_state['pipes_spawn_time'] = 10
                                game_state['score'] = 0
                                game_state['high_score'] = 0
                            elif action == 'instructions':
                                play_click()
                                state = MENU_INSTRUCTIONS
                                set_music('menu')
                            elif action == 'audio':
                                play_click()
                                config.mute = not config.mute
                                set_music('menu')
                            elif action == 'exit':
                                play_click()
                                pygame.quit()
                                exit()
            elif state == MENU_INSTRUCTIONS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU_MAIN
                    set_music('menu')
            elif state == MENU_GAME:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if control_rects['slider_track'].collidepoint(event.pos) or control_rects['slider_knob'].collidepoint(event.pos):
                        ui_state['slider_dragging'] = True
                        update_slider_from_mouse(event.pos[0], control_rects['slider_track'])
                    elif control_rects['jump_track'].collidepoint(event.pos) or control_rects['jump_knob'].collidepoint(event.pos):
                        ui_state['jump_dragging'] = True
                        update_jump_from_mouse(event.pos[0], control_rects['jump_track'])
                    elif control_rects['lines_toggle'].collidepoint(event.pos):
                        play_click()
                        config.show_lines = not config.show_lines
                    elif control_rects['graph'].collidepoint(event.pos):
                        play_click()
                        graph_state['dirty'] = True
                        show_graph_window()
                    elif control_rects['pause'].collidepoint(event.pos):
                        play_click()
                        ui_state['is_paused'] = not ui_state['is_paused']
                    elif control_rects['restart'].collidepoint(event.pos):
                        play_click()
                        restart_simulation()
                    elif control_rects['back'].collidepoint(event.pos):
                        play_click()
                        state = MENU_MAIN
                        set_music('menu')
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    ui_state['slider_dragging'] = False
                    ui_state['jump_dragging'] = False
                if event.type == pygame.MOUSEMOTION and ui_state['slider_dragging']:
                    update_slider_from_mouse(event.pos[0], control_rects['slider_track'])
                if event.type == pygame.MOUSEMOTION and ui_state['jump_dragging']:
                    update_jump_from_mouse(event.pos[0], control_rects['jump_track'])
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU_MAIN
                    set_music('menu')

        pygame.display.flip()
        clock.tick(60)


main()