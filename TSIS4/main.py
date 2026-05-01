"""
SNAKE GAME - Main Game Logic & Entry Point
Contains: Game class, main()

Run this file to start the game:
    python main.py
"""

import pygame
import sys
import random

from constants import (
    WIDTH, HEIGHT, CELL_SIZE,
    BLACK, WHITE, RED, GREEN, BLUE, GOLD, DARK_RED,
    CYAN, YELLOW, SHIELD_COLOR, ORANGE
)
from data import SettingsManager, Database
from entities import Snake, Food, PowerUp, ObstacleManager, EffectManager
from screens import Button, MainMenu, UsernameScreen, LeaderboardScreen, SettingsScreen, GameOverScreen


# MAIN GAME CLASS
class Game:
    def __init__(self, username, settings):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.username = username
        self.settings = settings
        self.db = Database()

        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.reset_game()

    def reset_game(self):
        colors = self.settings.get_snake_colors()
        self.snake = Snake(colors)
        self.obstacles = ObstacleManager()
        self.food = Food(self.snake.body, self.obstacles.get_obstacles())
        self.powerup = None
        self.effects = EffectManager()

        self.score = 0
        self.level = 1
        self.base_speed = 8
        self.speed = 8
        self.game_active = True
        self.last_powerup_spawn = pygame.time.get_ticks()
        self.personal_best = self.db.get_personal_best(self.username)

        self.generate_level_obstacles()

    def generate_level_obstacles(self):
        food_pos = self.food.position if self.food else None
        powerup_pos = self.powerup.position if self.powerup else None
        self.obstacles.generate_obstacles(self.level, self.snake.body, food_pos, powerup_pos)

        if not self.obstacles.is_position_free(self.food.position, self.snake.body):
            self.food = Food(self.snake.body, self.obstacles.get_obstacles())

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.snake.change_direction("RIGHT")
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction("LEFT")
                elif event.key == pygame.K_UP:
                    self.snake.change_direction("UP")
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction("DOWN")
        return True

    def update_powerup(self):
        now = pygame.time.get_ticks()

        if self.powerup is None and now - self.last_powerup_spawn > 10000:
            if random.random() < 0.7:
                self.powerup = PowerUp(self.snake.body, self.obstacles.get_obstacles())
                self.last_powerup_spawn = now

        if self.powerup and self.powerup.is_expired():
            self.powerup = None

        if self.powerup and self.snake.eat_food(self.powerup.position):
            effect = self.powerup.get_type()
            self.effects.activate_effect(effect, self.powerup.get_effect_duration())
            if effect == "speed":
                self.speed = min(self.base_speed + 5, 25)
            elif effect == "slow":
                self.speed = max(self.base_speed - 3, 3)
            self.powerup = None
            self.last_powerup_spawn = now

        if self.effects.is_effect_active("speed"):
            self.speed = min(self.base_speed + 5, 25)
        elif self.effects.is_effect_active("slow"):
            self.speed = max(self.base_speed - 3, 3)
        else:
            self.speed = self.base_speed

    def update(self):
        self.snake.move()

        wall = self.snake.check_wall_collision()
        self_collision = self.snake.check_self_collision()
        obstacle = self.obstacles.check_collision(self.snake.body[0])

        if wall or self_collision or obstacle:
            if self.effects.use_shield():
                pass
            else:
                self.game_active = False
                return

        if self.snake.eat_food(self.food.position):
            points = self.food.get_weight()
            self.score += points

            if self.food.get_type() == "poison":
                if not self.snake.shorten_snake(2):
                    self.game_active = False
                    return
                self.snake.poison_effect()

            self.food = Food(self.snake.body, self.obstacles.get_obstacles())

            if points > 0 and self.score >= self.level * 10:
                self.level += 1
                self.base_speed = min(self.base_speed + 1, 20)
                self.generate_level_obstacles()

        if self.food.is_expired():
            self.food = Food(self.snake.body, self.obstacles.get_obstacles())

        self.update_powerup()

    def draw(self):
        self.screen.fill(BLACK)

        if self.settings.get_grid_overlay():
            for x in range(0, WIDTH, CELL_SIZE):
                pygame.draw.line(self.screen, (30, 30, 40), (x, 0), (x, HEIGHT), 1)
            for y in range(0, HEIGHT, CELL_SIZE):
                pygame.draw.line(self.screen, (30, 30, 40), (0, y), (WIDTH, y), 1)

        self.obstacles.draw(self.screen)
        self.snake.draw(self.screen)
        self.food.draw(self.screen)
        if self.powerup:
            self.powerup.draw(self.screen)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        best_text = self.small_font.render(f"Best: {self.personal_best}", True, GOLD)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(level_text, (WIDTH - 120, 10))
        self.screen.blit(best_text, (10, HEIGHT - 30))

        y = 50
        if self.effects.is_effect_active("speed"):
            self.screen.blit(self.small_font.render(f"SPEED: {self.effects.get_remaining_time('speed'):.1f}s", True, CYAN), (WIDTH - 150, y))
            y += 25
        if self.effects.is_effect_active("slow"):
            self.screen.blit(self.small_font.render(f"SLOW: {self.effects.get_remaining_time('slow'):.1f}s", True, YELLOW), (WIDTH - 150, y))
            y += 25
        if self.effects.is_effect_active("shield"):
            self.screen.blit(self.small_font.render(f"SHIELD: {self.effects.get_remaining_time('shield'):.1f}s", True, SHIELD_COLOR), (WIDTH - 150, y))

        if self.level >= 3:
            warn = self.small_font.render("⚠ OBSTACLES ACTIVE ⚠", True, ORANGE)
            self.screen.blit(warn, (WIDTH // 2 - 80, HEIGHT - 30))

        if self.food.get_type() == "gold":
            info = self.small_font.render("GOLD +3!", True, GOLD)
            self.screen.blit(info, (WIDTH // 2 - 50, 50))
        elif self.food.get_type() == "timed":
            self.screen.blit(self.small_font.render("TIMED +2", True, BLUE), (WIDTH // 2 - 50, 50))
        elif self.food.get_type() == "poison":
            self.screen.blit(self.small_font.render("POISON -2 SEGMENTS!", True, DARK_RED), (WIDTH // 2 - 90, 50))

        pygame.display.flip()

    def run(self):
        while self.game_active:
            if not self.handle_input():
                return False
            self.update()
            self.draw()
            self.clock.tick(self.speed)

        self.db.save_game_result(self.username, self.score, self.level)
        return True


#  MAIN FUNCTION 
def main():
    pygame.init()

    settings = SettingsManager()
    db = Database()

    username = None
    running = True
    screen_state = "username"

    while running:
        if screen_state == "username":
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Snake Game")
            username_screen = UsernameScreen(screen)
            clock = pygame.time.Clock()

            waiting = True
            while waiting:
                dt = clock.tick(60)
                username_screen.update(dt)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    result = username_screen.handle_event(event)
                    if result == "quit":
                        pygame.quit()
                        sys.exit()
                    elif result:
                        username = result
                        waiting = False
                        screen_state = "menu"

                username_screen.draw()

        elif screen_state == "menu":
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Snake Game")
            main_menu = MainMenu(screen)

            in_menu = True
            while in_menu:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    action = main_menu.handle_event(event)
                    if action == "play":
                        in_menu = False
                        screen_state = "game"
                    elif action == "leaderboard":
                        in_menu = False
                        screen_state = "leaderboard"
                    elif action == "settings":
                        in_menu = False
                        screen_state = "settings"
                    elif action == "quit":
                        pygame.quit()
                        sys.exit()

                main_menu.draw()
                pygame.time.Clock().tick(60)

        elif screen_state == "game":
            game = Game(username, settings)
            game.run()
            screen_state = "game_over"

        elif screen_state == "game_over":
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            game_over_screen = GameOverScreen(screen)
            best = db.get_personal_best(username)
            game_over_screen.set_stats(game.score, game.level, best)

            in_game_over = True
            while in_game_over:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    action = game_over_screen.handle_event(event)
                    if action == "retry":
                        in_game_over = False
                        screen_state = "game"
                    elif action == "menu":
                        in_game_over = False
                        screen_state = "menu"
                    elif action == "quit":
                        pygame.quit()
                        sys.exit()

                game_over_screen.draw()
                pygame.time.Clock().tick(60)

        elif screen_state == "leaderboard":
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            leaderboard_screen = LeaderboardScreen(screen, db)
            leaderboard_screen.load_data(username)

            in_leaderboard = True
            while in_leaderboard:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    action = leaderboard_screen.handle_event(event)
                    if action == "back":
                        in_leaderboard = False
                        screen_state = "menu"

                leaderboard_screen.draw()
                pygame.time.Clock().tick(60)

        elif screen_state == "settings":
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            settings_screen = SettingsScreen(screen, settings)

            in_settings = True
            while in_settings:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    action = settings_screen.handle_event(event)
                    if action == "save":
                        in_settings = False
                        screen_state = "menu"

                settings_screen.draw()
                pygame.time.Clock().tick(60)


if __name__ == "__main__":
    main()
