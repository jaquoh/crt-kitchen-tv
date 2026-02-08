import os
import time
from pathlib import Path

import pygame
import yaml

from ui.hw.leds_apa102 import Apa102Leds
from player import play as player

CONFIG_PATH = os.environ.get("CRT_CONFIG", "/etc/crt-kitchen-tv/config.yaml")
BUTTON_GPIO = 17
REFRESH_SECONDS = 10
VIDEO_EXTS = {".mp4", ".mkv", ".mov"}

# Favor framebuffer output for pygame menu.
os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
os.environ.setdefault("SDL_NOMOUSE", "1")

try:
    from gpiozero import Button
except ImportError:
    Button = None


class ButtonInput:
    def __init__(self, gpio_pin=BUTTON_GPIO):
        self.last_event = None
        self._enabled = Button is not None
        self._press_time = None
        self.button = None
        if self._enabled:
            try:
                self.button = Button(gpio_pin, pull_up=True, bounce_time=0.05)
                self.button.when_pressed = self._on_press
                self.button.when_released = self._on_release
            except Exception:
                self._enabled = False
                self.button = None

    def _on_press(self):
        self._press_time = time.time()

    def _on_release(self):
        if self._press_time is None:
            return
        self.last_event = "back" if (time.time() - self._press_time) >= 1.0 else "select"
        self._press_time = None

    def poll(self):
        event_name = self.last_event
        self.last_event = None
        return event_name


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        cfg = {}
    cfg.setdefault("news_streams", [])
    cfg.setdefault("movies_dir", "/home/pi/Videos")
    cfg.setdefault("media_root", "/var/lib/crt-kitchen-tv/media")
    cfg.setdefault("collections", ["Inbox", "News", "Movies"])
    cfg.setdefault("library_sort", "newest")
    cfg.setdefault("font_size", 48)
    cfg.setdefault("leds_enabled", True)
    return cfg


def list_video_files(folder, sort_mode):
    path = Path(folder)
    if not path.exists() or not path.is_dir():
        return None, f"Missing folder: {folder}"
    files = [f for f in path.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTS]
    if sort_mode == "alpha":
        files.sort(key=lambda p: p.name.lower())
    else:
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(f) for f in files], None


def draw_list(screen, font, title, items, selected, subtitle=""):
    screen.fill((0, 0, 0))
    title_surf = font.render(title, True, (255, 255, 0))
    screen.blit(title_surf, (40, 25))
    if subtitle:
        sub = font.render(subtitle, True, (120, 180, 255))
        screen.blit(sub, (40, 80))
    y = 145
    visible = items[:8]
    for idx, text in enumerate(visible):
        color = (0, 255, 0) if idx == selected else (220, 220, 220)
        line = font.render(text, True, color)
        screen.blit(line, (60, y))
        y += font.get_linesize() + 8
    pygame.display.flip()


def draw_message(screen, font, message, hint="Backspace to return"):
    screen.fill((0, 0, 0))
    msg = font.render(message, True, (255, 120, 120))
    screen.blit(msg, (40, 180))
    hint_surf = font.render(hint, True, (200, 200, 200))
    screen.blit(hint_surf, (40, 250))
    pygame.display.flip()


def play_news(cfg, leds):
    streams = cfg.get("news_streams", [])
    if not streams:
        return
    leds.set_all(0, 0, 64)
    player.play_media(streams[0], cfg)
    leds.off()


def main():
    cfg = load_config()
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    font = pygame.font.SysFont("dejavusans", int(cfg.get("font_size", 48)))
    clock = pygame.time.Clock()

    leds = Apa102Leds(enabled=cfg.get("leds_enabled", True))
    button = ButtonInput()

    menu_items = ["News", "Movies", "Library"]
    menu_idx = 0
    mode = "menu"

    movies = []
    movies_idx = 0

    collection_idx = 0
    file_idx = 0
    active_collection = None
    collection_files = []
    collection_error = None
    last_scan_ts = 0.0

    def refresh_movies():
        nonlocal movies, movies_idx
        files, err = list_video_files(cfg.get("movies_dir", "/home/pi/Videos"), cfg.get("library_sort", "newest"))
        movies = files or []
        movies_idx = min(movies_idx, max(0, len(movies) - 1))
        return err

    def enter_collection(name):
        nonlocal mode, active_collection, collection_files, collection_error, file_idx, last_scan_ts
        active_collection = name
        target = str(Path(cfg.get("media_root", "/var/lib/crt-kitchen-tv/media")) / name)
        collection_files, collection_error = list_video_files(target, cfg.get("library_sort", "newest"))
        collection_files = collection_files or []
        file_idx = 0
        last_scan_ts = time.time()
        mode = "library_files"

    draw_list(screen, font, "CRT Kitchen TV", menu_items, menu_idx)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_UP:
                if mode == "menu":
                    menu_idx = (menu_idx - 1) % len(menu_items)
                elif mode == "movies" and movies:
                    movies_idx = (movies_idx - 1) % len(movies)
                elif mode == "library_collections":
                    collection_idx = (collection_idx - 1) % len(cfg.get("collections", []))
                elif mode == "library_files" and collection_files:
                    file_idx = (file_idx - 1) % len(collection_files)
            elif event.key == pygame.K_DOWN:
                if mode == "menu":
                    menu_idx = (menu_idx + 1) % len(menu_items)
                elif mode == "movies" and movies:
                    movies_idx = (movies_idx + 1) % len(movies)
                elif mode == "library_collections":
                    collection_idx = (collection_idx + 1) % len(cfg.get("collections", []))
                elif mode == "library_files" and collection_files:
                    file_idx = (file_idx + 1) % len(collection_files)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if mode == "menu":
                    selected = menu_items[menu_idx]
                    if selected == "News":
                        draw_list(screen, font, "News", ["Loading stream..."], 0)
                        play_news(cfg, leds)
                    elif selected == "Movies":
                        mode = "movies"
                        err = refresh_movies()
                        if err:
                            draw_message(screen, font, err)
                    else:
                        mode = "library_collections"
                elif mode == "movies" and movies:
                    leds.set_all(64, 0, 0)
                    player.play_media(movies[movies_idx], cfg)
                    leds.off()
                elif mode == "library_collections":
                    collections = cfg.get("collections", [])
                    if collections:
                        enter_collection(collections[collection_idx])
                elif mode == "library_files" and collection_files and not collection_error:
                    leds.set_all(64, 0, 0)
                    player.play_media(collection_files[file_idx], cfg)
                    leds.off()
            elif event.key == pygame.K_BACKSPACE:
                if mode == "menu":
                    running = False
                elif mode == "library_files":
                    mode = "library_collections"
                else:
                    mode = "menu"

        btn_event = button.poll()
        if btn_event == "select":
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        elif btn_event == "back":
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))

        # Refresh file list periodically while browsing a collection.
        if mode == "library_files" and active_collection and (time.time() - last_scan_ts) >= REFRESH_SECONDS:
            target = str(Path(cfg.get("media_root", "/var/lib/crt-kitchen-tv/media")) / active_collection)
            collection_files, collection_error = list_video_files(target, cfg.get("library_sort", "newest"))
            collection_files = collection_files or []
            file_idx = min(file_idx, max(0, len(collection_files) - 1))
            last_scan_ts = time.time()

        if mode == "menu":
            draw_list(screen, font, "CRT Kitchen TV", menu_items, menu_idx)
        elif mode == "movies":
            items = [Path(p).name for p in movies] if movies else ["No files found"]
            draw_list(screen, font, "Movies", items, movies_idx)
        elif mode == "library_collections":
            collections = cfg.get("collections", [])
            items = collections if collections else ["No collections configured"]
            draw_list(screen, font, "Library", items, collection_idx, subtitle=cfg.get("media_root", ""))
        elif mode == "library_files":
            if collection_error:
                draw_message(screen, font, collection_error)
            else:
                items = [Path(p).name for p in collection_files] if collection_files else ["No files found"]
                draw_list(
                    screen,
                    font,
                    active_collection or "Library",
                    items,
                    file_idx,
                    subtitle=f"Sort: {cfg.get('library_sort', 'newest')}",
                )

        clock.tick(30)

    leds.off()
    leds.close()
    pygame.quit()


if __name__ == "__main__":
    main()
