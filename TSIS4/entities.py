"""
SNAKE GAME - Game Entities
Contains: Snake, Food, PowerUp, ObstacleManager, EffectManager
"""

import pygame
import random
import time
import math

from constants import (
    WIDTH, HEIGHT, CELL_SIZE,
    BLACK, WHITE, RED, GREEN, BLUE, GOLD, DARK_RED, DARK_GREEN,
    BRIGHT_GREEN, CYAN, YELLOW, SHIELD_COLOR, GRAY
)


# ========== SNAKE CLASS ==========
class Snake:
    def __init__(self, colors=None):
        if colors:
            self.HEAD_COLOR = colors[0]
            self.BODY_COLOR = colors[1]
            self.DARK_BODY_COLOR = colors[2]
        else:
            self.HEAD_COLOR = BRIGHT_GREEN
            self.BODY_COLOR = GREEN
            self.DARK_BODY_COLOR = DARK_GREEN

        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        self.body = [
            [center_x, center_y],
            [center_x - CELL_SIZE, center_y],
            [center_x - CELL_SIZE * 2, center_y]
        ]
        self.direction = "RIGHT"
        self.grow = False
        self.poison_effect_timer = 0

    def move(self):
        head = self.body[0].copy()
        if self.direction == "RIGHT":
            head[0] += CELL_SIZE
        elif self.direction == "LEFT":
            head[0] -= CELL_SIZE
        elif self.direction == "UP":
            head[1] -= CELL_SIZE
        elif self.direction == "DOWN":
            head[1] += CELL_SIZE

        self.body.insert(0, head)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False

    def change_direction(self, new_dir):
        opposites = {"RIGHT": "LEFT", "LEFT": "RIGHT", "UP": "DOWN", "DOWN": "UP"}
        if new_dir != opposites.get(self.direction):
            self.direction = new_dir

    def check_self_collision(self):
        return self.body[0] in self.body[1:]

    def check_wall_collision(self):
        head = self.body[0]
        return head[0] < 0 or head[0] >= WIDTH or head[1] < 0 or head[1] >= HEIGHT

    def eat_food(self, food_pos):
        if self.body[0] == food_pos:
            self.grow = True
            return True
        return False

    def shorten_snake(self, segments=2):
        for _ in range(segments):
            if len(self.body) > 1:
                self.body.pop()
        return len(self.body) > 1

    def poison_effect(self):
        self.poison_effect_timer = 10

    def draw(self, screen):
        for i, segment in enumerate(self.body):
            if i == 0:
                if self.poison_effect_timer > 0:
                    color = DARK_RED
                    self.poison_effect_timer -= 1
                else:
                    color = self.HEAD_COLOR
            else:
                color = self.BODY_COLOR if i % 2 == 0 else self.DARK_BODY_COLOR

            pygame.draw.rect(screen, color, (segment[0], segment[1], CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (0, 100, 0), (segment[0], segment[1], CELL_SIZE, CELL_SIZE), 1)

            if i == 0:
                eye_size = 2
                if self.direction == "RIGHT":
                    pygame.draw.circle(screen, WHITE, (segment[0] + CELL_SIZE - 4, segment[1] + 4), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] + CELL_SIZE - 4, segment[1] + CELL_SIZE - 5), eye_size)
                elif self.direction == "LEFT":
                    pygame.draw.circle(screen, WHITE, (segment[0] + 3, segment[1] + 4), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] + 3, segment[1] + CELL_SIZE - 5), eye_size)
                elif self.direction == "UP":
                    pygame.draw.circle(screen, WHITE, (segment[0] + 4, segment[1] + 3), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] + CELL_SIZE - 5, segment[1] + 3), eye_size)
                else:
                    pygame.draw.circle(screen, WHITE, (segment[0] + 4, segment[1] + CELL_SIZE - 4), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] + CELL_SIZE - 5, segment[1] + CELL_SIZE - 4), eye_size)


# ========== FOOD CLASS ==========
class Food:
    def __init__(self, snake_body, obstacles=None):
        self.type = None
        self.position = [0, 0]
        self.weight = 0
        self.spawn_time = None
        self.lifetime = None
        self.randomize_food(snake_body, obstacles)

    def randomize_food(self, snake_body, obstacles=None):
        rand = random.random()
        if rand < 0.5:
            self.type = "normal"
            self.weight = 1
            self.lifetime = None
        elif rand < 0.7:
            self.type = "gold"
            self.weight = 3
            self.lifetime = None
        elif rand < 0.85:
            self.type = "timed"
            self.weight = 2
            self.lifetime = 3
            self.spawn_time = time.time()
        else:
            self.type = "poison"
            self.weight = -1
            self.lifetime = None

        max_attempts = 1000
        for _ in range(max_attempts):
            x = random.randint(0, (WIDTH // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, (HEIGHT // CELL_SIZE) - 1) * CELL_SIZE
            new_pos = [x, y]
            if new_pos not in snake_body and (obstacles is None or new_pos not in obstacles):
                self.position = new_pos
                return

        for _ in range(max_attempts):
            x = random.randint(0, (WIDTH // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, (HEIGHT // CELL_SIZE) - 1) * CELL_SIZE
            if [x, y] not in snake_body:
                self.position = [x, y]
                return

    def is_expired(self):
        if self.lifetime is None:
            return False
        return time.time() - self.spawn_time >= self.lifetime

    def draw(self, screen):
        if self.type == "normal":
            pygame.draw.rect(screen, RED, (self.position[0], self.position[1], CELL_SIZE, CELL_SIZE))
        elif self.type == "gold":
            pygame.draw.rect(screen, GOLD, (self.position[0], self.position[1], CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (255, 255, 150), (self.position[0] + 2, self.position[1] + 2, CELL_SIZE - 4, CELL_SIZE - 4))
        elif self.type == "timed":
            pygame.draw.rect(screen, BLUE, (self.position[0], self.position[1], CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (0, 0, 200), (self.position[0], self.position[1], CELL_SIZE, CELL_SIZE), 2)
        elif self.type == "poison":
            pygame.draw.rect(screen, DARK_RED, (self.position[0], self.position[1], CELL_SIZE, CELL_SIZE))
            cx, cy = self.position[0] + CELL_SIZE // 2, self.position[1] + CELL_SIZE // 2
            pygame.draw.circle(screen, BLACK, (cx - 5, cy - 3), 2)
            pygame.draw.circle(screen, BLACK, (cx + 5, cy - 3), 2)
            pygame.draw.line(screen, BLACK, (cx - 6, cy + 3), (cx + 6, cy + 8), 2)
            pygame.draw.line(screen, BLACK, (cx + 6, cy + 3), (cx - 6, cy + 8), 2)

    def get_weight(self):
        return self.weight

    def get_type(self):
        return self.type


# ========== OBSTACLE MANAGER ==========
class ObstacleManager:
    def __init__(self):
        self.obstacles = []

    def generate_obstacles(self, level, snake_body, food_pos=None, powerup_pos=None):
        if level < 3:
            self.obstacles = []
            return

        num_obstacles = min(5 + (level - 3) * 2, 25)
        self.obstacles = []

        forbidden = {tuple(pos) for pos in snake_body}
        if food_pos:
            forbidden.add(tuple(food_pos))
        if powerup_pos:
            forbidden.add(tuple(powerup_pos))

        head = snake_body[0]
        head_cell = (head[0] // CELL_SIZE, head[1] // CELL_SIZE)

        for _ in range(1000):
            if len(self.obstacles) >= num_obstacles:
                break
            x = random.randint(0, (WIDTH // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, (HEIGHT // CELL_SIZE) - 1) * CELL_SIZE
            pos = (x, y)
            pos_cell = (x // CELL_SIZE, y // CELL_SIZE)

            if abs(pos_cell[0] - head_cell[0]) <= 2 and abs(pos_cell[1] - head_cell[1]) <= 2:
                continue

            if pos not in forbidden and [x, y] not in self.obstacles:
                self.obstacles.append([x, y])
                forbidden.add(pos)

    def check_collision(self, head_pos):
        return head_pos in self.obstacles

    def is_position_free(self, pos, snake_body, food_pos=None, powerup_pos=None):
        if pos in self.obstacles:
            return False
        if pos in snake_body:
            return False
        if food_pos and pos == food_pos:
            return False
        if powerup_pos and pos == powerup_pos:
            return False
        return True

    def draw(self, screen):
        for obs in self.obstacles:
            pygame.draw.rect(screen, GRAY, (obs[0], obs[1], CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (60, 60, 60), (obs[0], obs[1], CELL_SIZE, CELL_SIZE), 2)
            pygame.draw.line(screen, (120, 120, 120), (obs[0] + 3, obs[1] + CELL_SIZE // 2),
                             (obs[0] + CELL_SIZE - 3, obs[1] + CELL_SIZE // 2), 1)
            pygame.draw.line(screen, (120, 120, 120), (obs[0] + CELL_SIZE // 2, obs[1] + 3),
                             (obs[0] + CELL_SIZE // 2, obs[1] + CELL_SIZE - 3), 1)

    def get_obstacles(self):
        return self.obstacles

    def get_obstacle_count(self):
        return len(self.obstacles)


# ========== POWER-UP CLASS ==========
class PowerUp:
    def __init__(self, snake_body, obstacles=None):
        self.type = random.choice(["speed", "slow", "shield"])
        self.position = [0, 0]
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 8000
        self.effect_duration = 5000
        self.find_position(snake_body, obstacles)

    def find_position(self, snake_body, obstacles=None):
        for _ in range(1000):
            x = random.randint(0, (WIDTH // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, (HEIGHT // CELL_SIZE) - 1) * CELL_SIZE
            pos = [x, y]
            if pos not in snake_body and (obstacles is None or pos not in obstacles):
                self.position = pos
                return
        self.position = [CELL_SIZE, CELL_SIZE]

    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time >= self.lifetime

    def get_remaining_time(self):
        remaining = max(0, self.lifetime - (pygame.time.get_ticks() - self.spawn_time))
        return remaining / 1000.0

    def get_effect_duration(self):
        return self.effect_duration

    def get_type(self):
        return self.type

    def draw(self, screen):
        if self.type == "speed":
            color = CYAN
            bright = (100, 255, 255)
        elif self.type == "slow":
            color = YELLOW
            bright = (255, 255, 100)
        else:
            color = SHIELD_COLOR
            bright = (100, 255, 200)

        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        size = int(CELL_SIZE * (0.7 + pulse * 0.3))
        offset = (CELL_SIZE - size) // 2

        pygame.draw.rect(screen, bright, (self.position[0] + offset - 2, self.position[1] + offset - 2, size + 4, size + 4), border_radius=5)
        pygame.draw.rect(screen, color, (self.position[0] + offset, self.position[1] + offset, size, size), border_radius=5)

        cx, cy = self.position[0] + CELL_SIZE // 2, self.position[1] + CELL_SIZE // 2
        if self.type == "speed":
            pygame.draw.polygon(screen, WHITE, [(cx - 4, cy - 3), (cx + 3, cy), (cx, cy), (cx + 4, cy + 3), (cx - 3, cy), (cx, cy)])
        elif self.type == "slow":
            pygame.draw.circle(screen, WHITE, (cx, cy), 4)
            pygame.draw.line(screen, BLACK, (cx - 2, cy), (cx + 2, cy), 1)
            pygame.draw.line(screen, BLACK, (cx, cy - 2), (cx, cy + 2), 1)
        else:
            points = [(cx, cy - 5), (cx + 5, cy - 2), (cx + 5, cy + 3), (cx, cy + 5), (cx - 5, cy + 3), (cx - 5, cy - 2)]
            pygame.draw.polygon(screen, WHITE, points, 2)

        ratio = self.get_remaining_time() / 8.0
        pygame.draw.rect(screen, (50, 50, 50), (self.position[0], self.position[1] + CELL_SIZE, CELL_SIZE, 3))
        pygame.draw.rect(screen, color, (self.position[0], self.position[1] + CELL_SIZE, int(CELL_SIZE * ratio), 3))


# ========== EFFECT MANAGER ==========
class EffectManager:
    def __init__(self):
        self.active_effects = {}
        self.shield_available = True

    def activate_effect(self, effect_type, duration_ms):
        self.active_effects[effect_type] = pygame.time.get_ticks() + duration_ms
        if effect_type == "shield":
            self.shield_available = True

    def is_effect_active(self, effect_type):
        if effect_type not in self.active_effects:
            return False
        if pygame.time.get_ticks() >= self.active_effects[effect_type]:
            if effect_type == "shield":
                self.shield_available = False
            del self.active_effects[effect_type]
            return False
        return True

    def use_shield(self):
        if self.is_effect_active("shield") and self.shield_available:
            self.shield_available = False
            del self.active_effects["shield"]
            return True
        return False

    def get_remaining_time(self, effect_type):
        if effect_type not in self.active_effects:
            return 0
        remaining = max(0, self.active_effects[effect_type] - pygame.time.get_ticks())
        return remaining / 1000.0

    def clear_all_effects(self):
        self.active_effects.clear()
        self.shield_available = True
