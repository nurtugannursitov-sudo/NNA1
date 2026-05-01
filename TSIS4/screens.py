"""
 UI Screens
Contains: Button, MainMenu, UsernameScreen, LeaderboardScreen, SettingsScreen, GameOverScreen
"""

import pygame

from constants import (
    WIDTH, HEIGHT,
    BLACK, WHITE, RED, GREEN, BLUE, GOLD, DARK_RED, DARK_GREEN,
    CYAN, YELLOW, SHIELD_COLOR, GRAY
)


# ========== BUTTON CLASS ==========
class Button:
    def __init__(self, x, y, w, h, text, color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        self.font = pygame.font.Font(None, 36)

    def draw(self, screen):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_surf = self.font.render(self.text, True, WHITE)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            return True
        return False


# ========== MAIN MENU ==========
class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width = WIDTH
        self.height = HEIGHT
        bw, bh = 200, 50
        bx = self.width // 2 - bw // 2
        y_start = self.height // 2 - 100

        self.play_btn = Button(bx, y_start, bw, bh, "PLAY", (0, 100, 0), (0, 150, 0))
        self.leaderboard_btn = Button(bx, y_start + 70, bw, bh, "LEADERBOARD", (0, 0, 100), (0, 0, 150))
        self.settings_btn = Button(bx, y_start + 140, bw, bh, "SETTINGS", (100, 100, 0), (150, 150, 0))
        self.quit_btn = Button(bx, y_start + 210, bw, bh, "QUIT", (100, 0, 0), (150, 0, 0))
        self.buttons = [self.play_btn, self.leaderboard_btn, self.settings_btn, self.quit_btn]

    def draw(self):
        self.screen.fill(BLACK)
        for i in range(0, self.width, 40):
            for j in range(0, self.height, 40):
                pygame.draw.rect(self.screen, (10, 10, 10), (i, j, 38, 38), 1)

        font_big = pygame.font.Font(None, 72)
        title = font_big.render("SNAKE GAME", True, GOLD)
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)

        for btn in self.buttons:
            btn.draw(self.screen)
        pygame.display.flip()

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                if btn == self.play_btn:
                    return "play"
                elif btn == self.leaderboard_btn:
                    return "leaderboard"
                elif btn == self.settings_btn:
                    return "settings"
                elif btn == self.quit_btn:
                    return "quit"
        return None


# ========== USERNAME INPUT SCREEN ==========
class UsernameScreen:
    def __init__(self, screen):
        self.screen = screen
        self.username = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 28)

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and len(self.username) >= 3:
                return self.username
            elif event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            elif event.key == pygame.K_ESCAPE:
                return "quit"
            elif len(self.username) < 20 and event.unicode.isprintable():
                self.username += event.unicode
        return None

    def draw(self):
        self.screen.fill(BLACK)
        font_big = pygame.font.Font(None, 64)
        title = font_big.render("SNAKE GAME", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 100)))

        prompt = self.font.render("Enter your username:", True, WHITE)
        self.screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, 230)))

        box = pygame.Rect(WIDTH // 2 - 200, 300, 400, 60)
        pygame.draw.rect(self.screen, (30, 30, 40), box)
        pygame.draw.rect(self.screen, GOLD, box, 3)

        display = self.username + ("|" if self.cursor_visible else "")
        text = self.font.render(display, True, WHITE)
        self.screen.blit(text, text.get_rect(center=box.center))

        if len(self.username) < 3 and self.username:
            warn = self.small_font.render("Minimum 3 characters", True, RED)
            self.screen.blit(warn, warn.get_rect(center=(WIDTH // 2, 390)))

        pygame.display.flip()


# ========== LEADERBOARD SCREEN ==========
class LeaderboardScreen:
    def __init__(self, screen, db):
        self.screen = screen
        self.db = db
        self.scores = []
        self.username = ""
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 56)
        self.back_btn = Button(WIDTH // 2 - 80, HEIGHT - 70, 160, 40, "BACK", GRAY, (120, 120, 120))

    def load_data(self, username):
        self.username = username
        self.scores = self.db.get_top_scores(10)

    def draw(self):
        self.screen.fill(BLACK)
        title = self.title_font.render("LEADERBOARD", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        best = self.db.get_personal_best(self.username)
        pb_text = self.font.render(f"Your Best: {best}", True, GREEN if best > 0 else WHITE)
        self.screen.blit(pb_text, pb_text.get_rect(center=(WIDTH // 2, 110)))

        headers = ["#", "PLAYER", "SCORE", "LEVEL"]
        x_pos = [50, 150, 400, 500]
        for i, h in enumerate(headers):
            self.screen.blit(self.font.render(h, True, GOLD), (x_pos[i], 150))

        pygame.draw.line(self.screen, GRAY, (30, 175), (WIDTH - 30, 175), 2)

        y = 190
        for i, score in enumerate(self.scores[:8]):
            color = GOLD if score["username"] == self.username else WHITE
            rank = i + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            self.screen.blit(self.font.render(medal, True, GOLD if rank <= 3 else WHITE), (x_pos[0], y))
            self.screen.blit(self.font.render(score["username"][:12], True, color), (x_pos[1], y))
            self.screen.blit(self.font.render(str(score["score"]), True, color), (x_pos[2], y))
            self.screen.blit(self.font.render(str(score["level"]), True, color), (x_pos[3], y))
            y += 35

        self.back_btn.draw(self.screen)
        pygame.display.flip()

    def handle_event(self, event):
        if self.back_btn.handle_event(event):
            return "back"
        return None


# ========== SETTINGS SCREEN ==========
class SettingsScreen:
    def __init__(self, screen, settings):
        self.screen = screen
        self.s = settings
        self.selected_color = None
        self.rgb = [0, 0, 0]
        self.dragging_channel = None

        self.grid_rect = pygame.Rect(WIDTH // 2 - 150, 160, 25, 25)
        self.sound_rect = pygame.Rect(WIDTH // 2 - 150, 220, 25, 25)
        self.head_rect = pygame.Rect(WIDTH // 2 + 100, 290, 50, 50)
        self.body_rect = pygame.Rect(WIDTH // 2 + 100, 355, 50, 50)
        self.dark_rect = pygame.Rect(WIDTH // 2 + 100, 420, 50, 50)
        self.save_btn = Button(WIDTH // 2 - 100, HEIGHT - 80, 200, 45, "SAVE & BACK", (0, 100, 0), (0, 150, 0))

    def draw_checkbox(self, rect, checked):
        pygame.draw.rect(self.screen, GRAY, rect, 2)
        if checked:
            pygame.draw.line(self.screen, GREEN,
                             (rect.x + 5, rect.y + rect.height // 2),
                             (rect.x + rect.width // 2, rect.y + rect.height - 8), 3)
            pygame.draw.line(self.screen, GREEN,
                             (rect.x + rect.width // 2, rect.y + rect.height - 8),
                             (rect.x + rect.width - 8, rect.y + 5), 3)

    def draw_color_picker(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 150, 500, 300)
        pygame.draw.rect(self.screen, (40, 40, 50), panel)
        pygame.draw.rect(self.screen, GOLD, panel, 2)

        font = pygame.font.Font(None, 32)
        title = font.render(f"Pick {self.selected_color} Color", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110))
        self.screen.blit(title, title_rect)

        preview = pygame.Rect(WIDTH // 2 + 150, HEIGHT // 2 - 80, 70, 70)
        pygame.draw.rect(self.screen, self.rgb, preview)
        pygame.draw.rect(self.screen, WHITE, preview, 2)

        colors = {'R': RED, 'G': GREEN, 'B': BLUE}
        y = HEIGHT // 2 - 30
        for i, (ch, color) in enumerate(colors.items()):
            slider_bg = pygame.Rect(WIDTH // 2 - 130, y + i * 50, 200, 10)
            fill = pygame.Rect(WIDTH // 2 - 130, y + i * 50, int(200 * self.rgb[i] / 255), 10)
            pygame.draw.rect(self.screen, (30, 30, 30), slider_bg)
            pygame.draw.rect(self.screen, color, fill)

            label = font.render(f"{ch}: {self.rgb[i]}", True, color)
            self.screen.blit(label, (WIDTH // 2 - 200, y + i * 50 - 5))

        ok_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 + 100, 70, 35)
        cancel_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 100, 70, 35)
        pygame.draw.rect(self.screen, GREEN, ok_rect)
        pygame.draw.rect(self.screen, RED, cancel_rect)

        ok_text = font.render("OK", True, WHITE)
        cancel_text = font.render("Cancel", True, WHITE)
        self.screen.blit(ok_text, ok_text.get_rect(center=ok_rect.center))
        self.screen.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

        return ok_rect, cancel_rect

    def draw(self):
        self.screen.fill(BLACK)
        font = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 32)

        title = font.render("SETTINGS", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

        self.screen.blit(font_small.render("Grid Overlay:", True, WHITE), (WIDTH // 2 - 250, 165))
        self.draw_checkbox(self.grid_rect, self.s.get_grid_overlay())

        self.screen.blit(font_small.render("Sound:", True, WHITE), (WIDTH // 2 - 250, 225))
        self.draw_checkbox(self.sound_rect, self.s.get_sound())

        self.screen.blit(font_small.render("SNAKE COLORS", True, GOLD), (WIDTH // 2 - 250, 280))
        self.screen.blit(font_small.render("Head:", True, WHITE), (WIDTH // 2 - 250, 305))
        self.screen.blit(font_small.render("Body:", True, WHITE), (WIDTH // 2 - 250, 370))
        self.screen.blit(font_small.render("Dark Body:", True, WHITE), (WIDTH // 2 - 250, 435))

        colors = self.s.get_snake_colors()
        pygame.draw.rect(self.screen, colors[0], self.head_rect)
        pygame.draw.rect(self.screen, colors[1], self.body_rect)
        pygame.draw.rect(self.screen, colors[2], self.dark_rect)
        pygame.draw.rect(self.screen, WHITE, self.head_rect, 2)
        pygame.draw.rect(self.screen, WHITE, self.body_rect, 2)
        pygame.draw.rect(self.screen, WHITE, self.dark_rect, 2)

        self.save_btn.draw(self.screen)

        if self.selected_color:
            self.draw_color_picker()

        pygame.display.flip()

    def _get_slider_rects(self):
        y = HEIGHT // 2 - 30
        return [
            pygame.Rect(WIDTH // 2 - 130, y + i * 50, 200, 10)
            for i in range(3)
        ]

    def _update_rgb_from_mouse(self, mx):
        if self.dragging_channel is not None:
            slider_x = WIDTH // 2 - 130
            val = int((mx - slider_x) / 200 * 255)
            self.rgb[self.dragging_channel] = max(0, min(255, val))

    def _get_picker_rects(self):
        ok_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 + 100, 70, 35)
        cancel_rect = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 100, 70, 35)
        return ok_rect, cancel_rect

    def handle_event(self, event):
        if self.selected_color:
            ok_rect, cancel_rect = self._get_picker_rects()
            slider_rects = self._get_slider_rects()

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(slider_rects):
                    hit_area = pygame.Rect(rect.x, rect.y - 8, rect.width, rect.height + 16)
                    if hit_area.collidepoint(event.pos):
                        self.dragging_channel = i
                        self._update_rgb_from_mouse(event.pos[0])
                        return None

                if ok_rect.collidepoint(event.pos):
                    if self.selected_color == "Head":
                        self.s.set_snake_color("head", *self.rgb)
                    elif self.selected_color == "Body":
                        self.s.set_snake_color("body", *self.rgb)
                    else:
                        self.s.set_snake_color("dark_body", *self.rgb)
                    self.selected_color = None
                elif cancel_rect.collidepoint(event.pos):
                    self.selected_color = None

            elif event.type == pygame.MOUSEMOTION:
                if hasattr(self, 'dragging_channel') and self.dragging_channel is not None:
                    if event.buttons[0]:
                        self._update_rgb_from_mouse(event.pos[0])
                    else:
                        self.dragging_channel = None

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_channel = None

            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.grid_rect.collidepoint(event.pos):
                self.s.set_grid_overlay(not self.s.get_grid_overlay())
            elif self.sound_rect.collidepoint(event.pos):
                self.s.set_sound(not self.s.get_sound())
            elif self.head_rect.collidepoint(event.pos):
                self.selected_color = "Head"
                self.rgb = list(self.s.get_snake_colors()[0])
            elif self.body_rect.collidepoint(event.pos):
                self.selected_color = "Body"
                self.rgb = list(self.s.get_snake_colors()[1])
            elif self.dark_rect.collidepoint(event.pos):
                self.selected_color = "Dark Body"
                self.rgb = list(self.s.get_snake_colors()[2])

        if self.save_btn.handle_event(event):
            return "save"
        return None


# ========== GAME OVER SCREEN ==========
class GameOverScreen:
    def __init__(self, screen):
        self.screen = screen
        self.score = 0
        self.level = 0
        self.best = 0
        self.retry_btn = Button(WIDTH // 2 - 200, HEIGHT // 2 + 100, 120, 45, "RETRY", (0, 100, 0), (0, 150, 0))
        self.menu_btn = Button(WIDTH // 2 - 60, HEIGHT // 2 + 100, 120, 45, "MENU", (100, 0, 0), (150, 0, 0))
        self.quit_btn = Button(WIDTH // 2 + 80, HEIGHT // 2 + 100, 120, 45, "QUIT", (80, 80, 80), (120, 120, 120))

    def set_stats(self, score, level, best):
        self.score = score
        self.level = level
        self.best = best

    def draw(self):
        self.screen.fill(BLACK)
        for i in range(HEIGHT):
            intensity = int(255 * (1 - i / HEIGHT))
            pygame.draw.line(self.screen, (intensity // 8, 0, 0), (0, i), (WIDTH, i))

        font_big = pygame.font.Font(None, 64)
        font = pygame.font.Font(None, 36)

        game_over = font_big.render("GAME OVER", True, RED)
        self.screen.blit(game_over, game_over.get_rect(center=(WIDTH // 2, 80)))

        new_record = self.score >= self.best and self.score > 0
        if new_record:
            record = font.render("NEW RECORD!", True, GOLD)
            self.screen.blit(record, record.get_rect(center=(WIDTH // 2, 140)))

        stats = [
            (f"Score: {self.score}", WHITE),
            (f"Level: {self.level}", WHITE),
            (f"Best: {self.best}", GREEN if new_record else WHITE)
        ]
        y = 200
        for text, color in stats:
            surf = font.render(text, True, color)
            self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))
            y += 40

        self.retry_btn.draw(self.screen)
        self.menu_btn.draw(self.screen)
        self.quit_btn.draw(self.screen)
        pygame.display.flip()

    def handle_event(self, event):
        if self.retry_btn.handle_event(event):
            return "retry"
        if self.menu_btn.handle_event(event):
            return "menu"
        if self.quit_btn.handle_event(event):
            return "quit"
        return None
