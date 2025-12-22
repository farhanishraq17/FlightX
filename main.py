import pygame
from sys import exit
import config
import components
import population

pygame.init()
clock = pygame.time.Clock()
pygame.display.set_caption('AviationX - Simulator')
config.create_window()
pygame.display.set_icon(pygame.image.load('Assets/aeroplane.jpg'))
config.reset_ground()

background_top = pygame.image.load('Assets/sky1.jpg').convert()
background_bottom = pygame.image.load('Assets/sky2.jpg').convert()
main_menu_bg = pygame.image.load('Assets/mainmenu.png').convert_alpha()

population_manager = population.Population(100)


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
    top_scaled = pygame.transform.smoothscale(background_top, (config.win_width, config.win_height // 2))
    bottom_scaled = pygame.transform.smoothscale(
        background_bottom, (config.win_width, config.win_height - config.win_height // 2))
    config.window.blit(top_scaled, (0, 0))
    config.window.blit(bottom_scaled, (0, config.win_height // 2))


def handle_common_events(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit()
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_f:
            config.toggle_fullscreen()
        if event.key == pygame.K_m:
            config.mute = not config.mute
    if event.type == pygame.VIDEORESIZE:
        config.resize(event.w, event.h)


def main_menu():
    show_instructions = False
    while True:
        buttons = []
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return
            handle_common_events(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for label, rect, action in buttons:
                    if rect.collidepoint(mouse_pos):
                        if action == 'start':
                            return
                        if action == 'instructions':
                            show_instructions = not show_instructions
                        if action == 'audio':
                            config.mute = not config.mute
                        if action == 'exit':
                            pygame.quit()
                            exit()

        title_font, menu_font, author_font = get_fonts()
        min_side = min(config.win_width, config.win_height)
        padding = max(10, int(min_side * 0.02))
        gap = max(10, int(min_side * 0.015))

        config.window.fill((0, 0, 0))

        bg_scaled = pygame.transform.smoothscale(main_menu_bg, (config.win_width, config.win_height))
        bg_scaled.set_alpha(153)
        config.window.blit(bg_scaled, (0, 0))

        title_surf = title_font.render('A v i a t i o n X', True, (255, 255, 255))
        start_surf = menu_font.render('Start Game', True, (0, 0, 0))
        instruction_surf = menu_font.render('Instruction Manual', True, (0, 0, 0))
        mute_surf = menu_font.render(f'Audio: {"Off" if config.mute else "On"}', True, (0, 0, 0))
        exit_surf = menu_font.render('Exit', True, (0, 0, 0))
        author_surf = author_font.render('Author : Farhan Ishraq', True, (255, 255, 255))

        title_rect = title_surf.get_rect(center=(config.win_width // 2, int(config.win_height * 0.28)))

        option_y_start = int(config.win_height * 0.48)
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

        buttons = []
        mouse_pos = pygame.mouse.get_pos()

        config.window.blit(title_surf, title_rect)

        for surf, center, action in zip(option_surfaces, option_centers, option_actions):
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

        config.window.blit(fs_box, fs_box_rect)
        config.window.blit(fs_button_surf, fs_text_rect)
        config.window.blit(author_surf, author_rect)

        if show_instructions:
            info_lines = [
                'Controls:',
                'Enter - Start, F - Fullscreen, M - Mute, Click buttons to navigate.'
            ]
            info_height = len(info_lines) * (menu_font.get_height() + padding) + padding
            info_width = max(menu_font.size(line)[0] for line in info_lines) + padding * 2
            info_box = pygame.Surface((info_width, info_height), pygame.SRCALPHA)
            info_box.fill((0, 0, 0, 180))
            box_rect_info = info_box.get_rect(center=(config.win_width // 2, int(config.win_height * 0.78)))
            config.window.blit(info_box, box_rect_info)
            for idx, line in enumerate(info_lines):
                line_surf = menu_font.render(line, True, (255, 255, 255))
                line_rect = line_surf.get_rect(
                    center=(box_rect_info.centerx, box_rect_info.top + padding + idx * (menu_font.get_height() + padding))
                )
                config.window.blit(line_surf, line_rect)

        pygame.display.flip()
        clock.tick(60)


def run_game():
    pipes_spawn_time = 10

    while True:
        for event in pygame.event.get():
            handle_common_events(event)

        draw_background()

        # Spawn Ground
        config.ground.draw(config.window)

        # Spawn Pipes
        if pipes_spawn_time <= 0:
            generate_pipes()
            pipes_spawn_time = 200
        pipes_spawn_time -= 1

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

        clock.tick(60)
        pygame.display.flip()


def main():
    main_menu()
    run_game()


main()