# ui.py — UI-элементы и все экраны (меню, настройки, таблица лидеров, game over)

import pygame
from constants import (
    screen, clock, font, small_font, tiny_font, large_font, huge_font,
    WIDTH, HEIGHT,
    BLACK, WHITE, GRAY, LIGHT_GRAY, DARK_GRAY,
    RED, BLUE, GREEN, YELLOW, ORANGE, GOLD, BRONZE, SILVER, CYAN, LIME_GREEN,
    NITRO_COLOR, SHIELD_COLOR, REPAIR_COLOR,
    CAR_COLORS,
    load_settings, save_settings, load_leaderboard, save_leaderboard,
    add_score_to_leaderboard
)


# ─────────────────────────────────────────────
# Базовые виджеты
# ─────────────────────────────────────────────

class Button:
    """Обычная кнопка"""
    def __init__(self, x, y, width, height, text, color, hover_color,
                 text_color=WHITE, font_size=36):
        self.rect        = pygame.Rect(x, y, width, height)
        self.text        = text
        self.color       = color
        self.hover_color = hover_color
        self.text_color  = text_color
        self.font        = pygame.font.Font(None, font_size)
        self.is_hovered  = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered:
            return True
        return False


class ToggleButton:
    """Переключатель ON/OFF"""
    def __init__(self, x, y, width, height, text, initial_state=True):
        self.rect  = pygame.Rect(x, y, width, height)
        self.text  = text
        self.state = initial_state
        self.font  = pygame.font.Font(None, 30)

    def draw(self, surface):
        color = GREEN if self.state else RED
        pygame.draw.rect(surface, color, self.rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=15)
        label = f"{self.text}: {'ON' if self.state else 'OFF'}"
        text_surf = self.font.render(label, True, WHITE)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.state = not self.state
            return True
        return False


class ColorSelector:
    """Выбор цвета машины — квадратики с подписями"""
    def __init__(self, x, y, colors_dict):
        self.x              = x
        self.y              = y
        self.colors         = colors_dict
        self.color_names    = list(colors_dict.keys())
        self.selected_index = 0
        self.color_size     = 40
        self.spacing        = 10

    def draw(self, surface):
        title = small_font.render("Car Color:", True, WHITE)
        surface.blit(title, (self.x, self.y - 30))

        for i, (name, color) in enumerate(self.colors.items()):
            rx   = self.x + i * (self.color_size + self.spacing)
            rect = pygame.Rect(rx, self.y, self.color_size, self.color_size)

            display_color = color if color != (0, 0, 0) else (50, 50, 50)
            pygame.draw.rect(surface, display_color, rect, border_radius=5)

            border_color = YELLOW if i == self.selected_index else WHITE
            border_width = 3     if i == self.selected_index else 1
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=5)

            name_surf = tiny_font.render(name, True, WHITE)
            surface.blit(name_surf, name_surf.get_rect(centerx=rect.centerx,
                                                        top=rect.bottom + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(len(self.color_names)):
                rx   = self.x + i * (self.color_size + self.spacing)
                rect = pygame.Rect(rx, self.y, self.color_size, self.color_size)
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    return True
        return False

    def get_selected_color(self):
        return self.colors[self.color_names[self.selected_index]]

    def get_selected_color_name(self):
        return self.color_names[self.selected_index]

    def set_by_name(self, name):
        """Установить выбранный цвет по имени"""
        if name in self.color_names:
            self.selected_index = self.color_names.index(name)


class DifficultySelector:
    """Выбор сложности — три кнопки"""
    def __init__(self, x, y):
        self.x              = x
        self.y              = y
        self.difficulties   = ['Easy', 'Normal', 'Hard']
        self.selected_index = 1
        self.button_width   = 120
        self.button_height  = 40
        self.spacing        = 20

    def draw(self, surface):
        title = small_font.render("Difficulty:", True, WHITE)
        surface.blit(title, (self.x, self.y - 30))

        for i, diff in enumerate(self.difficulties):
            rx    = self.x + i * (self.button_width + self.spacing)
            rect  = pygame.Rect(rx, self.y, self.button_width, self.button_height)
            color = GREEN if i == self.selected_index else GRAY
            pygame.draw.rect(surface, color, rect, border_radius=10)
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=10)
            text_surf = small_font.render(diff, True, WHITE)
            surface.blit(text_surf, text_surf.get_rect(center=rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(len(self.difficulties)):
                rx   = self.x + i * (self.button_width + self.spacing)
                rect = pygame.Rect(rx, self.y, self.button_width, self.button_height)
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    return True
        return False

    def get_difficulty_multiplier(self):
        multipliers = {'Easy': 0.7, 'Normal': 1.0, 'Hard': 1.5}
        return multipliers[self.difficulties[self.selected_index]]

    def get_selected_difficulty(self):
        return self.difficulties[self.selected_index]

    def set_by_name(self, name):
        if name in self.difficulties:
            self.selected_index = self.difficulties.index(name)


# ─────────────────────────────────────────────
# Экраны
# ─────────────────────────────────────────────

def show_main_menu():
    """Главное меню → возвращает 'play' | 'leaderboard' | 'settings' | 'quit'"""
    bw, bh = 250, 60
    bx     = WIDTH // 2 - bw // 2
    sy     = 200
    sp     = 80

    play_btn   = Button(bx, sy,          bw, bh, "PLAY",        GREEN,  LIME_GREEN)
    lb_btn     = Button(bx, sy + sp,     bw, bh, "LEADERBOARD", BLUE,   (100, 100, 255))
    sets_btn   = Button(bx, sy + sp * 2, bw, bh, "SETTINGS",    ORANGE, (255, 200, 100))
    quit_btn   = Button(bx, sy + sp * 3, bw, bh, "QUIT",        RED,    (255, 100, 100))

    while True:
        screen.fill(BLACK)

        title    = huge_font.render("RACER GAME", True, RED)
        subtitle = font.render("Complete Edition", True, GOLD)
        screen.blit(title,    title.get_rect(centerx=WIDTH // 2, y=50))
        screen.blit(subtitle, subtitle.get_rect(centerx=WIDTH // 2, y=130))

        for btn in [play_btn, lb_btn, sets_btn, quit_btn]:
            btn.draw(screen)

        hint = tiny_font.render("Use mouse to navigate | Arrow keys to play", True, LIGHT_GRAY)
        screen.blit(hint, hint.get_rect(centerx=WIDTH // 2, y=HEIGHT - 30))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if play_btn.handle_event(event):   return "play"
            if lb_btn.handle_event(event):     return "leaderboard"
            if sets_btn.handle_event(event):   return "settings"
            if quit_btn.handle_event(event):   return "quit"


def show_settings_screen():
    """
    Экран настроек.
    Возвращает обновлённый словарь настроек (или None если нажат BACK без сохранения).
    ИСПРАВЛЕНО: цвет машины сохраняется как строка-имя и корректно применяется в игре.
    """
    settings = load_settings()

    sound_toggle       = ToggleButton(WIDTH // 2 - 150, 200, 300, 50, "Sound",
                                      settings['sound'])
    color_selector     = ColorSelector(50, 350, CAR_COLORS)
    difficulty_selector = DifficultySelector(WIDTH // 2 - 200, 480)

    # Восстанавливаем сохранённые значения
    color_selector.set_by_name(settings.get('car_color', 'Red'))
    difficulty_selector.set_by_name(settings.get('difficulty', 'Normal'))

    back_btn = Button(WIDTH // 2 - 75, 550, 150, 40, "BACK", GRAY,  LIGHT_GRAY)
    save_btn = Button(WIDTH // 2 - 75, 500, 150, 40, "SAVE", GREEN, LIME_GREEN)

    message       = ""
    message_timer = 0
    saved_settings = None  # будет заполнен при нажатии SAVE

    while True:
        screen.fill(BLACK)

        title = large_font.render("SETTINGS", True, GOLD)
        screen.blit(title, title.get_rect(centerx=WIDTH // 2, y=50))

        # Имя игрока
        name_label = small_font.render(
            f"Player: {settings.get('player_name', 'Player')}  (edit settings.json to change)",
            True, LIGHT_GRAY)
        screen.blit(name_label, (50, 140))

        sound_toggle.draw(screen)
        color_selector.draw(screen)
        difficulty_selector.draw(screen)
        back_btn.draw(screen)
        save_btn.draw(screen)

        if message and message_timer > 0:
            msg_surf = small_font.render(message, True, GREEN)
            screen.blit(msg_surf, msg_surf.get_rect(centerx=WIDTH // 2, y=160))
            message_timer -= 1

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # При закрытии окна возвращаем последние сохранённые настройки
                return saved_settings

            sound_toggle.handle_event(event)
            color_selector.handle_event(event)
            difficulty_selector.handle_event(event)

            if back_btn.handle_event(event):
                return saved_settings  # None если не было SAVE

            if save_btn.handle_event(event):
                # ИСПРАВЛЕНИЕ: всегда сохраняем имя цвета (строку), не RGB
                saved_settings = {
                    'sound':       sound_toggle.state,
                    'car_color':   color_selector.get_selected_color_name(),
                    'difficulty':  difficulty_selector.get_selected_difficulty(),
                    'player_name': settings.get('player_name', 'Player')
                }
                save_settings(saved_settings)
                message       = "Settings saved!"
                message_timer = 120


def show_leaderboard_screen():
    """Экран таблицы лидеров"""
    leaderboard = load_leaderboard()
    back_btn    = Button(WIDTH // 2 - 75,  HEIGHT - 80, 150, 50, "BACK",  GRAY, LIGHT_GRAY)
    reset_btn   = Button(WIDTH - 200,      HEIGHT - 80, 180, 50, "RESET", RED,  (255, 100, 100),
                         font_size=24)

    while True:
        screen.fill(BLACK)

        title = large_font.render("TOP 10 LEADERBOARD", True, GOLD)
        screen.blit(title, title.get_rect(centerx=WIDTH // 2, y=20))

        headers     = ["RANK", "NAME", "SCORE", "DIST", "COINS", "LVL", "DATE"]
        x_positions = [20, 70, 200, 310, 390, 460, 510]

        pygame.draw.rect(screen, DARK_GRAY, (10, 55, WIDTH - 20, 30))
        for i, header in enumerate(headers):
            h_surf = small_font.render(header, True, CYAN)
            screen.blit(h_surf, (x_positions[i], 60))

        pygame.draw.line(screen, GRAY, (20, 85), (WIDTH - 20, 85), 2)

        if leaderboard:
            for i, entry in enumerate(leaderboard):
                y_pos = 95 + i * 45

                if i % 2 == 0:
                    pygame.draw.rect(screen, DARK_GRAY, (10, y_pos - 5, WIDTH - 20, 40))

                rank_labels = ["👑 1", "🥈 2", "🥉 3"]
                rank_colors = [GOLD, SILVER, BRONZE]
                if i < 3:
                    rank, rank_color = rank_labels[i], rank_colors[i]
                else:
                    rank, rank_color = f"  {i + 1}", WHITE

                screen.blit(small_font.render(rank, True, rank_color), (x_positions[0], y_pos))

                texts = [
                    (entry.get("name",     "Unknown")[:10], WHITE),
                    (str(entry.get("score",    0)),          YELLOW),
                    (f"{entry.get('distance', 0)}m",         WHITE),
                    (str(entry.get("coins",    0)),           GOLD),
                    (str(entry.get("level",    1)),           GREEN),
                    (entry.get("date",    "")[:16],          LIGHT_GRAY),
                ]
                for j, (text, color) in enumerate(texts):
                    surf = small_font.render(text, True, color)
                    screen.blit(surf, (x_positions[j + 1], y_pos))
        else:
            no_scores = font.render("No scores yet!", True, LIGHT_GRAY)
            screen.blit(no_scores, no_scores.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        back_btn.draw(screen)
        reset_btn.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if back_btn.handle_event(event):
                return
            if reset_btn.handle_event(event):
                save_leaderboard([])
                leaderboard = []


def show_game_over_screen(score, distance, coins, level, player_name,
                          obstacles_dodged, nitro_used, shields_used, repairs_used):
    """Экран конца игры → 'retry' | 'menu' | 'quit'"""
    leaderboard = add_score_to_leaderboard(player_name, score, distance, coins, level)

    player_rank = None
    for i, entry in enumerate(leaderboard):
        if entry.get("score") == score and entry.get("name") == player_name:
            player_rank = i + 1
            break

    retry_btn = Button(WIDTH // 2 - 200, HEIGHT - 100, 180, 50, "RETRY",     GREEN, LIME_GREEN)
    menu_btn  = Button(WIDTH // 2 + 20,  HEIGHT - 100, 180, 50, "MAIN MENU", BLUE,  (100, 100, 255))
    lb_btn    = Button(WIDTH // 2 - 90,  HEIGHT - 160, 180, 40, "LEADERBOARD",
                       ORANGE, (255, 200, 100), font_size=24)

    while True:
        screen.fill(BLACK)

        go_surf = huge_font.render("GAME OVER", True, RED)
        screen.blit(go_surf, go_surf.get_rect(centerx=WIDTH // 2, y=20))

        score_surf = large_font.render(f"Score: {score}", True, YELLOW)
        screen.blit(score_surf, score_surf.get_rect(centerx=WIDTH // 2, y=100))

        name_surf = font.render(f"Player: {player_name}", True, CYAN)
        screen.blit(name_surf, name_surf.get_rect(centerx=WIDTH // 2, y=145))

        if player_rank:
            if player_rank == 1:
                rank_text  = "👑 #1 - NEW RECORD! 👑"
                rank_color = GOLD
            elif player_rank <= 3:
                rank_text  = f"🏆 Rank #{player_rank} - TOP 3! 🏆"
                rank_color = GOLD
            else:
                rank_text  = f"Rank #{player_rank} of {len(leaderboard)}"
                rank_color = WHITE
            rank_surf = font.render(rank_text, True, rank_color)
            screen.blit(rank_surf, rank_surf.get_rect(centerx=WIDTH // 2, y=180))

        stats_rect = pygame.Rect(WIDTH // 2 - 200, 220, 400, 220)
        pygame.draw.rect(screen, DARK_GRAY, stats_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE,     stats_rect, 2, border_radius=10)

        title_surf = font.render("STATISTICS", True, GOLD)
        screen.blit(title_surf, title_surf.get_rect(centerx=WIDTH // 2, y=230))

        stats = [
            (f"Distance: {distance} meters",       WHITE),
            (f"Coins Collected: {coins}",           GOLD),
            (f"Level Reached: {level}",             WHITE),
            (f"Obstacles Dodged: {obstacles_dodged}", WHITE),
            (f"Nitro Used: {nitro_used}",           NITRO_COLOR),
            (f"Shields Used: {shields_used}",       SHIELD_COLOR),
            (f"Repairs Used: {repairs_used}",       REPAIR_COLOR),
        ]
        for i, (stat, color) in enumerate(stats):
            stat_surf = small_font.render(stat, True, color)
            screen.blit(stat_surf, (WIDTH // 2 - 180, 265 + i * 25))

        retry_btn.draw(screen)
        menu_btn.draw(screen)
        lb_btn.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if retry_btn.handle_event(event): return "retry"
            if menu_btn.handle_event(event):  return "menu"
            if lb_btn.handle_event(event):    show_leaderboard_screen()
