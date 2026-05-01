#Игровые объекты: Player, TrafficCar, RoadObstacle, Coin, PowerUp

import pygame
import random
import math

from constants import (
    screen,
    WIDTH, HEIGHT, LEFT_BOUNDARY, RIGHT_BOUNDARY,
    BLACK, WHITE, GRAY, LIGHT_GRAY, YELLOW, ORANGE, CYAN,
    GOLD, BRONZE, SILVER, RED,
    NITRO_COLOR, SHIELD_COLOR, REPAIR_COLOR,
    TRAFFIC_COLORS,
    font
)


# Вспомогательные функции

def draw_road():
    """Отрисовка дороги и разметки"""
    pygame.draw.rect(screen, GRAY,       (80,          0, WIDTH - 160, HEIGHT))
    pygame.draw.rect(screen, LIGHT_GRAY, (0,           0, 80,          HEIGHT))
    pygame.draw.rect(screen, LIGHT_GRAY, (WIDTH - 80,  0, 80,          HEIGHT))

    for y in range(0, HEIGHT, 50):
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 5, y, 10, 30))

    pygame.draw.line(screen, WHITE, (80,         0), (80,         HEIGHT), 3)
    pygame.draw.line(screen, WHITE, (WIDTH - 80, 0), (WIDTH - 80, HEIGHT), 3)


def is_safe_spawn(x, y, width, height, player):
    """Проверка безопасного спавна относительно игрока"""
    if player is None:
        return True
    safe_zone = player.get_rect().inflate(200, 300)
    return not safe_zone.colliderect(pygame.Rect(x, y, width, height))


def check_overlap(new_rect, existing_objects, min_distance=50):
    """Проверка перекрытия с существующими объектами"""
    for obj in existing_objects:
        if hasattr(obj, 'get_rect'):
            if new_rect.colliderect(obj.get_rect().inflate(min_distance, min_distance)):
                return True
    return False



# Power-Up

class PowerUp:
    """Усиления: Nitro, Shield, Repair"""
    COLORS = {'nitro': NITRO_COLOR, 'shield': SHIELD_COLOR, 'repair': REPAIR_COLOR}

    def __init__(self, player=None, existing_objects=None):
        self.type     = random.choice(['nitro', 'shield', 'repair'])
        self.color    = self.COLORS[self.type]
        self.size     = 30
        self.speed    = 3
        self.lifetime = 600
        self._safe_spawn(player, existing_objects or [])

    def _safe_spawn(self, player, existing_objects):
        for attempt in range(15):
            self.x = random.randint(LEFT_BOUNDARY + 10, RIGHT_BOUNDARY - self.size - 10)
            self.y = random.randint(-400, -100)
            if not is_safe_spawn(self.x, self.y, self.size, self.size, player):
                self.y -= 150
                continue
            if check_overlap(self.get_rect(), existing_objects, 40):
                if attempt < 14:
                    continue
                self.y -= 200
            break

    def move(self):
        self.y        += self.speed
        self.lifetime -= 1

    def draw(self):
        if not (self.y + self.size > 0 and self.y < HEIGHT):
            return

        # Свечение
        alpha    = int(100 + 55 * math.sin(pygame.time.get_ticks() * 0.005))
        glow     = pygame.Surface((self.size + 12, self.size + 12), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, alpha // 2),
                           (self.size // 2 + 6, self.size // 2 + 6), self.size // 2 + 6)
        screen.blit(glow, (self.x - 6, self.y - 6))

        cx, cy = self.x + self.size // 2, self.y + self.size // 2
        pygame.draw.circle(screen, self.color, (cx, cy), self.size // 2)
        pygame.draw.circle(screen, WHITE,      (cx, cy), self.size // 2, 2)

        letter   = self.type[0].upper()
        txt      = font.render(letter, True, WHITE)
        screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

        # Мигание при истечении
        if self.lifetime < 120 and (pygame.time.get_ticks() // 200) % 2 == 0:
            warn = pygame.Surface((self.size + 4, self.size + 4), pygame.SRCALPHA)
            pygame.draw.circle(warn, (255, 0, 0, 100),
                               (self.size // 2 + 2, self.size // 2 + 2), self.size // 2 + 2)
            screen.blit(warn, (self.x - 2, self.y - 2))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def off_screen(self):
        return self.y > HEIGHT + 50 or self.lifetime <= 0


# Player

class Player:
    def __init__(self, car_color=RED):
        self.width, self.height = 45, 70
        self.x         = WIDTH // 2 - self.width // 2
        self.y         = HEIGHT - 100
        self.base_speed = 6
        self.speed      = 6
        self.car_color  = car_color  # RGB-кортеж

        # Усиления
        self.active_power_up  = None
        self.power_up_timer   = 0
        self.power_up_duration = 0

        # Эффекты
        self.slowed       = False
        self.slow_timer   = 0
        self.boosted      = False
        self.boost_timer  = 0
        self.shield_active = False
        self.repair_ready  = False

        # Статистика
        self.nitro_collected  = 0
        self.shield_collected = 0
        self.repair_collected = 0

    def activate_power_up(self, power_up_type):
        if self.active_power_up:
            self.deactivate_current_power_up()

        self.active_power_up = power_up_type

        if power_up_type == 'nitro':
            self.power_up_duration = random.randint(180, 300)
            self.boosted     = True
            self.boost_timer = self.power_up_duration
            self.speed       = int(self.base_speed * 1.8)
            self.nitro_collected += 1

        elif power_up_type == 'shield':
            self.power_up_duration = -1
            self.shield_active     = True
            self.shield_collected  += 1

        elif power_up_type == 'repair':
            self.repair_collected += 1
            self.slowed    = False
            self.slow_timer = 0
            self.active_power_up = None  # repair мгновенный

    def deactivate_current_power_up(self):
        if self.active_power_up == 'nitro':
            self.boosted     = False
            self.boost_timer = 0
            self.speed       = self.base_speed
        elif self.active_power_up == 'shield':
            self.shield_active = False

        self.active_power_up  = None
        self.power_up_timer   = 0
        self.power_up_duration = 0

    def use_shield_or_repair(self):
        if self.shield_active:
            self.deactivate_current_power_up()
            return True
        return False

    def move(self, keys):
        if self.slowed:
            spd = max(1, self.speed // 2)
        elif self.boosted:
            spd = int(self.speed * 1.2)
        else:
            spd = self.speed

        if keys[pygame.K_LEFT]  and self.x > LEFT_BOUNDARY:
            self.x -= spd
        if keys[pygame.K_RIGHT] and self.x < RIGHT_BOUNDARY:
            self.x += spd
        if keys[pygame.K_UP]   and self.y > 50:
            self.y -= spd
        if keys[pygame.K_DOWN] and self.y < HEIGHT - self.height:
            self.y += spd

    def update_effects(self):
        if self.active_power_up == 'nitro':
            self.power_up_timer += 1
            if self.power_up_timer >= self.power_up_duration:
                self.deactivate_current_power_up()

        if self.slowed:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.slowed = False

        if self.boosted and self.active_power_up != 'nitro':
            self.boost_timer -= 1
            if self.boost_timer <= 0:
                self.boosted = False
                self.speed   = self.base_speed

    def draw(self):
        # Аура усиления
        if self.active_power_up:
            aura_colors = {'nitro': NITRO_COLOR, 'shield': SHIELD_COLOR, 'repair': REPAIR_COLOR}
            color       = aura_colors.get(self.active_power_up, WHITE)
            alpha       = int(80 + 40 * math.sin(pygame.time.get_ticks() * 0.01))
            aura        = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(aura, (*color, alpha), (0, 0, self.width + 20, self.height + 20), 3)
            screen.blit(aura, (self.x - 10, self.y - 10))

        # Щит
        if self.shield_active:
            alpha  = int(128 + 64 * math.sin(pygame.time.get_ticks() * 0.01))
            shield = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(shield, (0, 255, 255, alpha),
                                (0, 0, self.width + 20, self.height + 20), 3)
            screen.blit(shield, (self.x - 10, self.y - 10))

        # Частицы ускорения
        if self.boosted:
            for _ in range(5):
                px = self.x + random.randint(5, self.width - 5)
                py = self.y + self.height + random.randint(0, 15)
                pygame.draw.circle(screen, CYAN, (px, py), random.randint(2, 4))

        # Кузов машины — используем self.car_color (RGB)
        pygame.draw.rect(screen, self.car_color,
                         (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK,
                         (self.x, self.y, self.width, self.height), 2)

        # Окна
        window = (100, 100, 200)
        pygame.draw.rect(screen, window, (self.x + 5, self.y + 5,  self.width - 10, 20))
        pygame.draw.rect(screen, window, (self.x + 5, self.y + 45, self.width - 10, 15))

        # Фары
        pygame.draw.circle(screen, YELLOW, (self.x + 8,              self.y + self.height - 5), 5)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width - 8, self.y + self.height - 5), 5)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)



# TrafficCar

class TrafficCar:
    def __init__(self, speed_multiplier=1.0, player=None, existing_objects=None):
        self.width, self.height = 40, 65
        self.color = random.choice(TRAFFIC_COLORS)
        self._safe_spawn(player, existing_objects or [])
        self.speed = random.uniform(2.0, 4.0) * speed_multiplier

    def _safe_spawn(self, player, existing_objects):
        for attempt in range(20):
            self.x = random.randint(LEFT_BOUNDARY + 5, RIGHT_BOUNDARY - self.width - 5)
            self.y = random.randint(-300, -self.height)
            if player and not is_safe_spawn(self.x, self.y, self.width, self.height, player):
                continue
            if check_overlap(self.get_rect(), existing_objects, 80):
                if attempt < 19:
                    self.y -= 100
                    continue
            break

    def move(self):
        self.y += self.speed

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK,      (self.x, self.y, self.width, self.height), 2)
        win = (150, 200, 255)
        pygame.draw.rect(screen, win, (self.x + 5, self.y + 5,  self.width - 10, 15))
        pygame.draw.rect(screen, win, (self.x + 5, self.y + 35, self.width - 10, 15))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def off_screen(self):
        return self.y > HEIGHT + 50


# RoadObstacle


class RoadObstacle:
    _TYPES = {
        'barrier':   {'size': (40, 15), 'color': ORANGE,     'effect': 'block'},
        'oil_spill': {'size': None,     'color': (30, 30, 30), 'effect': 'slip'},
        'pothole':   {'size': None,     'color': (20, 20, 20), 'effect': 'damage'},
        'cone':      {'size': (20, 30), 'color': ORANGE,     'effect': 'block'},
    }

    def __init__(self, player=None, existing_objects=None):
        self.type = random.choice(list(self._TYPES.keys()))
        cfg       = self._TYPES[self.type]

        if cfg['size']:
            self.width, self.height = cfg['size']
        else:
            size = random.randint(30, 50)
            self.width = self.height = size

        self.color  = cfg['color']
        self.effect = cfg['effect']
        self.speed  = 3
        self._safe_spawn(player, existing_objects or [])

    def _safe_spawn(self, player, existing_objects):
        for attempt in range(15):
            self.x = random.randint(LEFT_BOUNDARY + 10, RIGHT_BOUNDARY - self.width - 10)
            self.y = random.randint(-400, -100)
            if not is_safe_spawn(self.x, self.y, self.width, self.height, player):
                self.y -= 150
                continue
            if check_overlap(self.get_rect(), existing_objects, 50):
                if attempt < 14:
                    continue
                self.y -= 200
            break

    def move(self):
        self.y += self.speed

    def draw(self):
        if not (self.y + self.height > 0 and self.y < HEIGHT):
            return
        if self.type == 'barrier':
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            for i in range(0, self.width, 8):
                pygame.draw.rect(screen, BLACK, (self.x + i, self.y, 4, self.height))
        elif self.type in ('oil_spill', 'pothole'):
            pygame.draw.ellipse(screen, self.color, (self.x, self.y, self.width, self.height))
            if self.type == 'pothole':
                pygame.draw.ellipse(screen, (10, 10, 10),
                                    (self.x + 3, self.y + 3, self.width - 6, self.height - 6))
        elif self.type == 'cone':
            pygame.draw.polygon(screen, self.color, [
                (self.x + self.width // 2, self.y),
                (self.x,                  self.y + self.height),
                (self.x + self.width,     self.y + self.height),
            ])

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def off_screen(self):
        return self.y > HEIGHT + 50



# Coin


class Coin:
    def __init__(self, player=None, existing_objects=None):
        self.size  = 25
        self.speed = 4
        r = random.random()
        if r < 0.6:
            self.weight, self.color = 1, BRONZE
        elif r < 0.85:
            self.weight, self.color = 2, SILVER
        else:
            self.weight, self.color = 3, GOLD
        self._safe_spawn(player, existing_objects or [])

    def _safe_spawn(self, player, existing_objects):
        for attempt in range(10):
            self.x = random.randint(LEFT_BOUNDARY + 10, RIGHT_BOUNDARY - self.size - 10)
            self.y = random.randint(-200, -50)
            if not is_safe_spawn(self.x, self.y, self.size, self.size, player):
                continue
            if check_overlap(self.get_rect(), existing_objects, 30):
                if attempt < 9:
                    self.y -= 100
                continue
            break

    def move(self):
        self.y += self.speed

    def draw(self):
        if not (self.y + self.size > 0 and self.y < HEIGHT):
            return
        cx, cy = self.x + self.size // 2, self.y + self.size // 2
        pygame.draw.circle(screen, self.color, (cx, cy), self.size // 2)
        pygame.draw.circle(screen, BLACK,      (cx, cy), self.size // 2, 2)
        txt = font.render(str(self.weight), True, BLACK)
        screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def off_screen(self):
        return self.y > HEIGHT + 50
