import os
import sys
import time
import threading
import pygame
import yaml
from pathlib import Path

from ui.hw.device import has_respeaker_hat
from ui.hw.leds_apa102 import Apa102Leds
from ui.hw import audio
from player import play as player

CONFIG_PATH = os.environ.get("CRT_CONFIG", "/etc/crt-kitchen-tv/config.yaml")
BUTTON_GPIO = 17

# Favor framebuffer output
# os.environ.setdefault("SDL_VIDEODRIVER", "fbcon")
os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
os.environ.setdefault("SDL_NOMOUSE", "1")

try:
    from gpiozero import Button
except ImportError:  # dev host
    Button = None


class ButtonInput:
    def __init__(self, gpio_pin=BUTTON_GPIO):
        self.gpio_pin = gpio_pin
        self.last_event = None
        self._enabled = Button is not None
        if self._enabled:
            try:
                self.button = Button(gpio_pin, pull_up=True, bounce_time=0.05)
                self.button.when_pressed = self._on_press
                self.button.when_released = self._on_release
                self._press_time = None
            except Exception:
                self._enabled = False
                self.button = None
        else:
            self.button = None

    def _on_press(self):
        self._press_time = time.time()

    def _on_release(self):
        if self._press_time is None:
            return
        duration = time.time() - self._press_time
        if duration >= 1.0:
            self.last_event = "back"
        else:
            self.last_event = "select"
        self._press_time = None

    def poll(self):
        ev = self.last_event
        self.last_event = None
        return ev


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def list_movies(path):
    p = Path(path)
    if not p.exists():
        return []
    exts = {".mp4", ".mkv", ".avi", ".mov"}
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts])


def draw_menu(screen, font, items, selected, title="CRT Kitchen TV"):
    screen.fill((0, 0, 0))
    title_surf = font.render(title, True, (255, 255, 0))
    screen.blit(title_surf, (40, 30))
    y = 140
    for idx, item in enumerate(items):
        color = (0, 255, 0) if idx == selected else (200, 200, 200)
        surf = font.render(item, True, color)
        screen.blit(surf, (60, y))
        y += font.get_linesize() + 10
    pygame.display.flip()


def draw_message(screen, font, message):
    screen.fill((0, 0, 0))
    surf = font.render(message, True, (255, 255, 255))
    screen.blit(surf, (40, 200))
    pygame.display.flip()


def play_news(cfg, leds):
    streams = cfg.get("news_streams", [])
    if not streams:
        return
    leds.set_all(0, 0, 64)
    player.play_media(streams[0], cfg)
    leds.off()


def play_movie(path, cfg, leds):
    leds.set_all(64, 0, 0)
    player.play_media(path, cfg)
    leds.off()


def main():
    cfg = load_config()
    font_size = int(cfg.get("font_size", 48))
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    font = pygame.font.SysFont("dejavusans", font_size)

    leds = Apa102Leds(enabled=cfg.get("leds_enabled", True))
    button = ButtonInput()

    menu_items = ["News", "Movies"]
    selected = 0
    mode = "menu"  # or "movies"
    movies = list_movies(cfg.get("movies_dir", "/home/pi/Videos"))
    movie_idx = 0

    clock = pygame.time.Clock()
    draw_menu(screen, font, menu_items, selected)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    if mode == "menu":
                        selected = (selected - 1) % len(menu_items)
                        draw_menu(screen, font, menu_items, selected)
                    elif mode == "movies" and movies:
                        movie_idx = (movie_idx - 1) % len(movies)
                elif event.key == pygame.K_DOWN:
                    if mode == "menu":
                        selected = (selected + 1) % len(menu_items)
                        draw_menu(screen, font, menu_items, selected)
                    elif mode == "movies" and movies:
                        movie_idx = (movie_idx + 1) % len(movies)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if mode == "menu":
                        if menu_items[selected] == "News":
                            draw_message(screen, font, "Loading news...")
                            play_news(cfg, leds)
                            draw_menu(screen, font, menu_items, selected)
                        else:
                            mode = "movies"
                            draw_message(screen, font, "Movies")
                    elif mode == "movies" and movies:
                        draw_message(screen, font, Path(movies[movie_idx]).name)
                        play_movie(movies[movie_idx], cfg, leds)
                        draw_message(screen, font, "Movies")
                elif event.key == pygame.K_BACKSPACE:
                    if mode == "movies":
                        mode = "menu"
                        draw_menu(screen, font, menu_items, selected)

        btn_event = button.poll()
        if btn_event == "select":
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        elif btn_event == "back":
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))

        if mode == "movies" and movies:
            screen.fill((0, 0, 0))
            title = font.render("Movies", True, (255, 255, 0))
            screen.blit(title, (40, 30))
            start_y = 140
            for idx, path in enumerate(movies[:8]):
                color = (0, 255, 0) if idx == movie_idx else (200, 200, 200)
                surf = font.render(Path(path).name, True, color)
                screen.blit(surf, (60, start_y))
                start_y += font.get_linesize() + 8
            pygame.display.flip()

        clock.tick(30)

    leds.off()
    leds.close()
    pygame.quit()


if __name__ == "__main__":
    main()
