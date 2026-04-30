# constants.py — Константы, цвета и настройки игры

import pygame
import os
import json
from datetime import datetime

# --- РАЗМЕРЫ ЭКРАНА ---
WIDTH, HEIGHT = 800, 600
LEFT_BOUNDARY = 100
RIGHT_BOUNDARY = WIDTH - 145

# --- ЦВЕТА ---
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
GRAY        = (50, 50, 50)
LIGHT_GRAY  = (80, 80, 80)
DARK_GRAY   = (30, 30, 30)
RED         = (255, 0, 0)
BLUE        = (0, 0, 255)
GREEN       = (0, 255, 0)
YELLOW      = (255, 255, 0)
ORANGE      = (255, 165, 0)
PURPLE      = (128, 0, 128)
GOLD        = (255, 215, 0)
BRONZE      = (205, 127, 50)
SILVER      = (192, 192, 192)
DARK_BROWN  = (101, 67, 33)
CYAN        = (0, 255, 255)
DARK_RED    = (139, 0, 0)
MAGENTA     = (255, 0, 255)
LIME_GREEN  = (50, 205, 50)
PINK        = (255, 192, 203)

# Цвета power-ups
NITRO_COLOR  = (0, 255, 255)
SHIELD_COLOR = (0, 100, 255)
REPAIR_COLOR = (50, 205, 50)

# Цвета машин игрока
CAR_COLORS = {
    'Red':    (255, 0, 0),
    'Blue':   (0, 0, 255),
    'Green':  (0, 255, 0),
    'Yellow': (255, 255, 0),
    'Purple': (128, 0, 128),
    'Orange': (255, 165, 0),
    'White':  (255, 255, 255),
    'Black':  (0, 0, 0)
}

# Цвета трафика
TRAFFIC_COLORS = [
    (255, 255, 0),
    (0, 200, 0),
    (0, 100, 255),
    (255, 100, 0),
    (200, 0, 200),
    (255, 200, 0),
    (100, 100, 100),
    (200, 200, 200)
]

# --- ОЧКИ ---
POINTS_PER_COIN  = 10
POINTS_PER_METER = 1
NITRO_BONUS      = 50
SHIELD_BONUS     = 30
REPAIR_BONUS     = 20
FINISH_DISTANCE  = 1000

# --- ФАЙЛЫ ---
LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"

# --- НАСТРОЙКИ ПО УМОЛЧАНИЮ ---
DEFAULT_SETTINGS = {
    'sound':       True,
    'car_color':   'Red',
    'difficulty':  'Normal',
    'player_name': 'Player'
}

# --- ИНИЦИАЛИЗАЦИЯ PYGAME ---
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racer Game - Complete Edition")
clock = pygame.time.Clock()

# Шрифты
tiny_font  = pygame.font.Font(None, 16)
small_font = pygame.font.Font(None, 20)
font       = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 48)
huge_font  = pygame.font.Font(None, 72)

# --- РАБОТА С ФАЙЛАМИ ---

def load_settings():
    """Загрузка настроек из файла"""
    settings = dict(DEFAULT_SETTINGS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                settings.update(saved)
        except Exception:
            pass
    # Гарантируем что car_color — это имя, а не RGB-кортеж
    if not isinstance(settings.get('car_color'), str):
        settings['car_color'] = 'Red'
    return settings

def save_settings(settings):
    """Сохранение настроек в файл"""
    # Гарантируем что сохраняем имя цвета, а не RGB
    to_save = dict(settings)
    if not isinstance(to_save.get('car_color'), str):
        to_save['car_color'] = 'Red'
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_leaderboard():
    """Загрузка таблицы лидеров из файла"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_leaderboard(leaderboard):
    """Сохранение таблицы лидеров"""
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

def add_score_to_leaderboard(name, score, distance, coins, level):
    """Добавление результата в таблицу лидеров"""
    leaderboard = load_leaderboard()
    entry = {
        "name":     name,
        "score":    score,
        "distance": distance,
        "coins":    coins,
        "level":    level,
        "date":     datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    leaderboard.append(entry)
    leaderboard.sort(key=lambda x: x.get("score", 0), reverse=True)
    leaderboard = leaderboard[:10]
    save_leaderboard(leaderboard)
    return leaderboard
