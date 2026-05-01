import pygame
import sys
import random

from constants import (
    screen, clock,
    WIDTH, HEIGHT, LEFT_BOUNDARY, RIGHT_BOUNDARY,
    BLACK, WHITE, GRAY, LIGHT_GRAY, DARK_GRAY,
    YELLOW, CYAN, GOLD,
    NITRO_COLOR, SHIELD_COLOR, REPAIR_COLOR,
    POINTS_PER_COIN, POINTS_PER_METER, NITRO_BONUS, SHIELD_BONUS, REPAIR_BONUS,
    CAR_COLORS, RED,
    font, small_font, tiny_font,
    load_settings, save_settings
)
from ui import (
    show_main_menu,
    show_settings_screen,
    show_leaderboard_screen,
    show_game_over_screen
)
from game_objects import (
    draw_road,
    Player, TrafficCar, RoadObstacle, Coin, PowerUp
)


class Game:
    """Менеджер одной игровой сессии"""

    def __init__(self, settings):
        self.player_name = settings.get('player_name', 'Player')
        self.difficulty  = settings.get('difficulty', 'Normal')
        self.sound_enabled = settings.get('sound', True)

        # ИСПРАВЛЕНИЕ: car_color всегда строка → ищем RGB в CAR_COLORS
        car_color_name = settings.get('car_color', 'Red')
        if isinstance(car_color_name, str):
            self.car_color = CAR_COLORS.get(car_color_name, RED)
        else:
            # Защита на случай если в файле настроек оказался RGB-кортеж
            self.car_color = car_color_name

        difficulty_multipliers = {'Easy': 0.7, 'Normal': 1.0, 'Hard': 1.5}
        self.difficulty_multiplier = difficulty_multipliers.get(self.difficulty, 1.0)
        self.difficulty_level = 1

        self._start_new_game()

    # Инициализация 

    def _start_new_game(self):
        self.player       = Player(self.car_color)
        self.traffic_cars = []
        self.obstacles    = []
        self.coins        = []
        self.power_ups    = []

        self._spawn_initial_objects()

        self.coins_collected  = 0
        self.distance_traveled = 0
        self.speed_increase   = 0
        self.game_active      = True
        self.score            = 0
        self.obstacles_dodged = 0

        self.traffic_spawn_timer  = 0
        self.obstacle_spawn_timer = 0
        self.coin_spawn_timer     = 0
        self.power_up_spawn_timer = 0

    def _spawn_initial_objects(self):
        for _ in range(2):
            self.traffic_cars.append(
                TrafficCar(self.difficulty_multiplier, self.player, self.traffic_cars))
        for _ in range(3):
            self.obstacles.append(
                RoadObstacle(self.player, self.obstacles))
        for _ in range(5):
            self.coins.append(
                Coin(self.player, self.coins))
        self.power_ups.append(
            PowerUp(self.player, self.power_ups))

    #  Подсчёт очков 

    def _calculate_score(self):
        dist_score   = (self.distance_traveled // 60) * POINTS_PER_METER
        coin_score   = self.coins_collected * POINTS_PER_COIN
        nitro_bonus  = self.player.nitro_collected  * NITRO_BONUS
        shield_bonus = self.player.shield_collected * SHIELD_BONUS
        repair_bonus = self.player.repair_collected * REPAIR_BONUS
        dodge_bonus  = self.obstacles_dodged * 5

        self.score = int(
            (dist_score + coin_score + nitro_bonus + shield_bonus + repair_bonus + dodge_bonus)
            * self.difficulty_multiplier
        )
        return self.score

    #Ввод 

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        self.player.move(pygame.key.get_pressed())
        return True

    #Обновление состояния 

    def _update(self):
        if not self.game_active:
            return

        self.distance_traveled += 1
        self.player.update_effects()
        self._calculate_score()

        self.difficulty_level = min(5, 1 + self.coins_collected // 15)

        spawn_intervals = {
            1: (180, 240, 120, 480),
            2: (150, 200, 100, 420),
            3: (120, 160,  90, 360),
            4: ( 90, 120,  80, 300),
            5: ( 60, 100,  70, 240),
        }
        ti, oi, ci, pi = spawn_intervals.get(self.difficulty_level, spawn_intervals[5])

        # Спавн трафика
        self.traffic_spawn_timer += 1
        if self.traffic_spawn_timer >= ti:
            if len(self.traffic_cars) < 3 + self.difficulty_level * 2:
                all_obj = self.traffic_cars + self.obstacles + self.coins + self.power_ups
                self.traffic_cars.append(
                    TrafficCar(self.difficulty_multiplier, self.player, all_obj))
            self.traffic_spawn_timer = 0

        # Спавн препятствий
        self.obstacle_spawn_timer += 1
        if self.obstacle_spawn_timer >= oi:
            if len(self.obstacles) < 3 + self.difficulty_level:
                all_obj = self.traffic_cars + self.obstacles + self.coins + self.power_ups
                self.obstacles.append(RoadObstacle(self.player, all_obj))
            self.obstacle_spawn_timer = 0

        # Спавн монет
        self.coin_spawn_timer += 1
        if self.coin_spawn_timer >= ci:
            if len(self.coins) < 8:
                all_obj = self.traffic_cars + self.obstacles + self.coins + self.power_ups
                self.coins.append(Coin(self.player, all_obj))
            self.coin_spawn_timer = 0

        # Спавн power-ups
        self.power_up_spawn_timer += 1
        if self.power_up_spawn_timer >= pi:
            if len(self.power_ups) < 2:
                all_obj = self.traffic_cars + self.obstacles + self.coins + self.power_ups
                self.power_ups.append(PowerUp(self.player, all_obj))
            self.power_up_spawn_timer = 0

        self._update_power_ups()
        self._update_traffic()
        self._update_obstacles()
        self._update_coins()

    def _update_power_ups(self):
        for pu in self.power_ups[:]:
            pu.move()
            if self.player.get_rect().colliderect(pu.get_rect()):
                self.player.activate_power_up(pu.type)
                self.power_ups.remove(pu)
            elif pu.off_screen():
                self.power_ups.remove(pu)

    def _update_traffic(self):
        for car in self.traffic_cars[:]:
            car.move()
            if self.player.get_rect().colliderect(car.get_rect()):
                if self.player.use_shield_or_repair():
                    self.traffic_cars.remove(car)
                    self.obstacles_dodged += 1
                else:
                    self.game_active = False
            elif car.off_screen():
                self.traffic_cars.remove(car)
                self.obstacles_dodged += 1

    def _update_obstacles(self):
        for obs in self.obstacles[:]:
            obs.move()
            if self.player.get_rect().colliderect(obs.get_rect()):
                if self.player.use_shield_or_repair():
                    self.obstacles.remove(obs)
                    self.obstacles_dodged += 1
                else:
                    if obs.effect == 'slip':
                        self.player.x += random.choice([-40, 40])
                        self.player.x = max(LEFT_BOUNDARY, min(RIGHT_BOUNDARY, self.player.x))
                    elif obs.effect == 'block':
                        self.player.y = min(HEIGHT - self.player.height, self.player.y + 30)
                    elif obs.effect == 'damage':
                        self.player.slowed     = True
                        self.player.slow_timer = 90
                    self.obstacles.remove(obs)
            elif obs.off_screen():
                self.obstacles.remove(obs)
                self.obstacles_dodged += 1

    def _update_coins(self):
        for coin in self.coins[:]:
            coin.move()
            if self.player.get_rect().colliderect(coin.get_rect()):
                self.coins_collected += coin.weight
                self.coins.remove(coin)
                new_speed = self.coins_collected // 5
                if new_speed > self.speed_increase:
                    self.speed_increase      = new_speed
                    self.player.base_speed   = 6 + self.speed_increase
                    if not self.player.boosted:
                        self.player.speed = self.player.base_speed
            elif coin.off_screen():
                self.coins.remove(coin)

    # Отрисовка 

    def _draw(self):
        draw_road()

        for pu  in self.power_ups:    pu.draw()
        for obs in self.obstacles:   obs.draw()
        for c   in self.coins:         c.draw()
        for car in self.traffic_cars: car.draw()

        self.player.draw()
        self._draw_ui()
        pygame.display.flip()

    def _draw_ui(self):
        # Верхняя панель
        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 50))
        pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, 50), 2)

        info = small_font.render(f"{self.player_name} | {self.difficulty}", True, CYAN)
        screen.blit(info, (10, 15))

        score_surf = font.render(f"Score: {self.score}", True, YELLOW)
        screen.blit(score_surf, score_surf.get_rect(centerx=WIDTH // 2, y=10))

        dist_m    = self.distance_traveled // 60
        dist_surf = small_font.render(f"Distance: {dist_m}m", True, WHITE)
        screen.blit(dist_surf, (WIDTH - 200, 15))

        # Правая панель
        px, py = WIDTH - 180, 55
        pygame.draw.rect(screen, BLACK, (px, py, 175, 150))
        pygame.draw.rect(screen, WHITE, (px, py, 175, 150), 2)

        stats = [
            (f"Level: {self.difficulty_level}",          WHITE),
            (f"Speed: {self.player.speed}",              WHITE),
            (f"Coins: {self.coins_collected}",           GOLD),
            (f"Nitro: {self.player.nitro_collected}",    NITRO_COLOR),
            (f"Shield: {self.player.shield_collected}",  SHIELD_COLOR),
            (f"Repair: {self.player.repair_collected}",  REPAIR_COLOR),
        ]
        for i, (text, color) in enumerate(stats):
            surf = tiny_font.render(text, True, color)
            screen.blit(surf, (px + 10, py + 10 + i * 22))

    # Главный цикл сессии 

    def run(self):
        while self.game_active:
            if not self._handle_input():
                return "quit"
            self._update()
            self._draw()
            clock.tick(60)

        final_score    = self._calculate_score()
        distance_meters = self.distance_traveled // 60

        return show_game_over_screen(
            final_score, distance_meters, self.coins_collected,
            self.difficulty_level, self.player_name, self.obstacles_dodged,
            self.player.nitro_collected, self.player.shield_collected,
            self.player.repair_collected
        )



# Точка входа

def main():
    settings       = load_settings()
    current_screen = "menu"

    while True:
        if current_screen == "menu":
            action = show_main_menu()

            if action == "quit":
                break
            elif action == "play":
                current_screen = "game"
                # Перечитываем настройки — имя могло измениться на экране ввода
                settings = load_settings()
            elif action == "leaderboard":
                show_leaderboard_screen()
            elif action == "settings":
                new_settings = show_settings_screen()
                if new_settings:
                    settings.update(new_settings)
                    # Перечитываем с диска чтобы иметь актуальные данные
                    settings = load_settings()

        elif current_screen == "game":
            game   = Game(settings)
            result = game.run()

            if result == "quit":
                break
            elif result == "menu":
                current_screen = "menu"
            elif result == "retry":
                current_screen = "game"

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
