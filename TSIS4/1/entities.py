# entities.py
import pygame
import random
import time
import math

WIDTH = 600
HEIGHT = 600
CELL_SIZE = 20

# цвета (оставь нужные)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)
BRIGHT_GREEN = (50, 255, 100)
GOLD = (255, 215, 0)
BLUE = (0, 0, 255)
DARK_RED = (139, 0, 0)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
SHIELD_COLOR = (0, 255, 128)
GRAY = (100, 100, 100)
WHITE = (255,255,255)

# ==== Snake ====
class Snake:
    def __init__(self, colors=None):
        self.HEAD_COLOR, self.BODY_COLOR, self.DARK_BODY_COLOR = colors or (
            BRIGHT_GREEN, GREEN, DARK_GREEN
        )

        cx, cy = WIDTH // 2, HEIGHT // 2
        self.body = [[cx, cy], [cx-20, cy], [cx-40, cy]]
        self.direction = "RIGHT"
        self.grow = False

    def move(self):
        head = self.body[0].copy()
        if self.direction == "RIGHT": head[0] += CELL_SIZE
        elif self.direction == "LEFT": head[0] -= CELL_SIZE
        elif self.direction == "UP": head[1] -= CELL_SIZE
        elif self.direction == "DOWN": head[1] += CELL_SIZE

        self.body.insert(0, head)
        if not self.grow:
            self.body.pop()
        self.grow = False

# ==== Food ====
class Food:
    def __init__(self, snake_body):
        self.position = [0,0]
        self.randomize(snake_body)

    def randomize(self, snake_body):
        while True:
            x = random.randint(0,29)*20
            y = random.randint(0,29)*20
            if [x,y] not in snake_body:
                self.position = [x,y]
                break

# ==== ObstacleManager ====
class ObstacleManager:
    def __init__(self):
        self.obstacles = []

    def generate(self, level):
        self.obstacles = []
        for _ in range(level):
            x = random.randint(0,29)*20
            y = random.randint(0,29)*20
            self.obstacles.append([x,y])