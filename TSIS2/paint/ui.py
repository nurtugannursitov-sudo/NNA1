"""
User Interface components for Paint Application
"""

import pygame
from tools import BRUSH_SIZES

# Brush size presets (3.2)
BRUSH_LABELS = ["S", "M", "L"]


class UI:
    """User interface manager"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui_height = 85                          # Height of UI area
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 16)

        # Brush-size button rects (built once, reused every frame)
        self._brush_btn_rects = []
        btn_w, btn_h = 28, 22
        base_x, base_y = 10, 60
        for i in range(3):
            self._brush_btn_rects.append(
                pygame.Rect(base_x + i * (btn_w + 4), base_y, btn_w, btn_h)
            )

    # ── drawing ────────────────────────────────────────────────────────────

    def draw_text(self, screen, mode, color, thickness):
        """Draw the top info bar."""
        pygame.draw.rect(screen, (240, 240, 240), (0, 0, self.screen_width, self.ui_height))
        pygame.draw.line(screen, (180, 180, 180), (0, self.ui_height), (self.screen_width, self.ui_height), 1)

        # Line 1: mode / color / size
        text1 = self.font.render(f"Mode: {mode}   Color: {color}   Size: {thickness}px", True, (0, 0, 0))
        screen.blit(text1, (10, 8))

        # Line 2: tool shortcuts
        text2 = self.small_font.render(
            "1-pencil  2-line  3-rect  4-circle  5-eraser  6-fill  7-text  "
            "8-sq  9-rtri  0-etri  =-rhomb",
            True, (50, 50, 50)
        )
        screen.blit(text2, (10, 32))

        # Line 3: colour shortcuts + save
        text3 = self.small_font.render(
            "R/G/B/Y/P/O/K colours  |  C-clear  |  Ctrl+S save",
            True, (50, 50, 50)
        )
        screen.blit(text3, (10, 48))

    def draw_brush_buttons(self, screen, current_thickness):
        """Draw S / M / L brush-size buttons (3.2)."""
        btn_w, btn_h = 28, 22
        for i, rect in enumerate(self._brush_btn_rects):
            size_val = BRUSH_SIZES[i]
            is_active = (current_thickness == size_val)
            bg = (90, 130, 200) if is_active else (210, 210, 210)
            fg = (255, 255, 255) if is_active else (20, 20, 20)
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, (120, 120, 120), rect, 1, border_radius=4)
            label = self.tiny_font.render(BRUSH_LABELS[i], True, fg)
            lx = rect.x + (btn_w - label.get_width()) // 2
            ly = rect.y + (btn_h - label.get_height()) // 2
            screen.blit(label, (lx, ly))

    def draw_color_palette(self, screen, colors, current_color):
        """Draw colour swatches."""
        palette_x = self.screen_width - 220
        palette_y = 10
        box_size = 28
        spacing = 4
        for i, color in enumerate(colors):
            x = palette_x + (box_size + spacing) * i
            y = palette_y
            pygame.draw.rect(screen, color, (x, y, box_size, box_size))
            pygame.draw.rect(screen, (0, 0, 0), (x, y, box_size, box_size), 1)
            if color == current_color:
                pygame.draw.rect(screen, (255, 255, 255), (x - 2, y - 2, box_size + 4, box_size + 4), 2)
                pygame.draw.rect(screen, (0, 0, 0), (x - 3, y - 3, box_size + 6, box_size + 6), 1)

    # ── hit-testing ────────────────────────────────────────────────────────

    def brush_button_at(self, pos):
        """Return the brush size for the button at pos, or None."""
        for i, rect in enumerate(self._brush_btn_rects):
            if rect.collidepoint(pos):
                return BRUSH_SIZES[i]
        return None
