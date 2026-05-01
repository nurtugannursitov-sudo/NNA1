# game.py
import pygame
from entities import Snake, Food, ObstacleManager

WIDTH = 600
HEIGHT = 600

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.snake = Snake()
        self.food = Food(self.snake.body)
        self.obstacles = ObstacleManager()

        self.running = True

    def update(self):
        self.snake.move()

        if self.snake.body[0] == self.food.position:
            self.snake.grow = True
            self.food = Food(self.snake.body)

    def draw(self):
        self.screen.fill((0,0,0))

        for s in self.snake.body:
            pygame.draw.rect(self.screen, (0,255,0), (*s,20,20))

        pygame.draw.rect(self.screen, (255,0,0), (*self.food.position,20,20))

        pygame.display.flip()

    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False

            self.update()
            self.draw()
            self.clock.tick(10)