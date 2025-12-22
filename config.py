import pygame
import components

win_height = 720
win_width = 900
window = None
fullscreen = False
mute = False

ground = None
pipes = []


def create_window():
    global window
    flags = pygame.RESIZABLE
    if fullscreen:
        flags |= pygame.FULLSCREEN
    window = pygame.display.set_mode((win_width, win_height), flags)
    return window


def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    create_window()
    reset_ground()


def resize(width, height):
    global win_width, win_height
    win_width = max(480, width)
    win_height = max(360, height)
    create_window()
    reset_ground()


def reset_ground():
    global ground
    ground = components.Ground(win_width, win_height)