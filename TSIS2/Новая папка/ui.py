"""
User Interface components for Paint Application
Icons drawn with pygame primitives (no font/unicode dependency)
"""

import pygame
import math
from tools import BRUSH_SIZES

BRUSH_LABELS = ["S", "M", "L"]

TOOL_BUTTONS = [
    ("Pencil",    "draw"),
    ("Line",      "line"),
    ("Rect",      "rect"),
    ("Circle",    "circle"),
    ("Eraser",    "eraser"),
    ("Fill",      "fill"),
    ("Text",      "text"),
    ("Square",    "square"),
    ("R.Tri",     "right_triangle"),
    ("E.Tri",     "equilateral"),
    ("Rhombus",   "rhombus"),
]


def _draw_icon(surface, mode, rect, color):
    """Draw a tool icon using pygame primitives into the given rect."""
    cx = rect.centerx
    cy = rect.centery
    w  = rect.width
    h  = rect.height
    m  = 5

    if mode == "draw":
        pygame.draw.line(surface, color,
                         (rect.x + m, rect.bottom - m),
                         (rect.right - m, rect.y + m), 2)
        pygame.draw.circle(surface, color, (rect.x + m, rect.bottom - m), 2)

    elif mode == "line":
        pygame.draw.line(surface, color,
                         (rect.x + m, rect.bottom - m),
                         (rect.right - m, rect.y + m), 2)

    elif mode == "rect":
        pygame.draw.rect(surface, color,
                         pygame.Rect(rect.x + m, rect.y + m,
                                     w - m * 2, h - m * 2), 2)

    elif mode == "square":
        side = min(w, h) - m * 2
        sx = cx - side // 2
        sy = cy - side // 2
        pygame.draw.rect(surface, color, pygame.Rect(sx, sy, side, side), 2)

    elif mode == "circle":
        r = min(w, h) // 2 - m
        pygame.draw.circle(surface, color, (cx, cy), max(r, 2), 2)

    elif mode == "eraser":
        er = pygame.Rect(rect.x + m, cy - 4, w - m * 2, 8)
        pygame.draw.rect(surface, color, er, 2)

    elif mode == "fill":
        # Simple bucket: rectangle body + spout line
        bx = rect.x + m + 2
        by = cy - 2
        bw = w - m * 2 - 2
        bh = h // 2 - 2
        pygame.draw.rect(surface, color, pygame.Rect(bx, by, bw, bh), 2)
        pygame.draw.line(surface, color,
                         (bx + bw // 2, rect.y + m),
                         (bx + bw // 2, by), 2)
        # Drop at bottom
        pygame.draw.circle(surface, color, (bx + bw // 2, by + bh + 3), 2)

    elif mode == "text":
        font = pygame.font.Font(None, h + 2)
        t = font.render("T", True, color)
        surface.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))

    elif mode == "right_triangle":
        pts = [
            (rect.x + m, rect.y + m),
            (rect.x + m, rect.bottom - m),
            (rect.right - m, rect.bottom - m),
        ]
        pygame.draw.polygon(surface, color, pts, 2)

    elif mode == "equilateral":
        base = w - m * 2
        hgt  = int(base * math.sqrt(3) / 2)
        bx   = rect.x + m
        by   = cy + hgt // 2
        pts  = [
            (bx, by),
            (bx + base, by),
            (bx + base // 2, by - hgt),
        ]
        pygame.draw.polygon(surface, color, pts, 2)

    elif mode == "rhombus":
        pts = [
            (cx, rect.y + m),
            (rect.right - m, cy),
            (cx, rect.bottom - m),
            (rect.x + m, cy),
        ]
        pygame.draw.polygon(surface, color, pts, 2)


class UI:
    """User interface manager"""

    def __init__(self, screen_width, screen_height):
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self.ui_height     = 120
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font  = pygame.font.Font(None, 16)

        # Tool button rects — bigger to fit icons
        self._tool_btn_rects = []
        btn_w, btn_h = 68, 40
        gap = 3
        start_x, start_y = 5, 5
        for i, (label, mode) in enumerate(TOOL_BUTTONS):
            rect = pygame.Rect(start_x + i * (btn_w + gap), start_y, btn_w, btn_h)
            self._tool_btn_rects.append((rect, mode))

        # Brush-size button rects
        self._brush_btn_rects = []
        btn_w2, btn_h2 = 28, 22
        base_x, base_y = 5, 93
        for i in range(3):
            self._brush_btn_rects.append(
                pygame.Rect(base_x + i * (btn_w2 + 4), base_y, btn_w2, btn_h2)
            )

        self._color_rects = []

    # ── drawing ──────────────────────────────────────────────────────────

    def draw_tool_buttons(self, screen, current_mode):
        for rect, mode in self._tool_btn_rects:
            is_active = (mode == current_mode)
            bg     = (70, 120, 200)  if is_active else (210, 210, 215)
            fg     = (255, 255, 255) if is_active else (30,  30,  30)
            border = (40,  90,  170) if is_active else (150, 150, 155)
            pygame.draw.rect(screen, bg,     rect, border_radius=5)
            pygame.draw.rect(screen, border, rect, 1, border_radius=5)
            _draw_icon(screen, mode, rect, fg)

    def draw_text(self, screen, mode, color, thickness):
        pygame.draw.rect(screen, (240, 240, 240),
                         (0, 0, self.screen_width, self.ui_height))
        pygame.draw.line(screen, (180, 180, 180),
                         (0, self.ui_height), (self.screen_width, self.ui_height), 1)

        text1 = self.small_font.render(
            f"Mode: {mode}   Size: {thickness}px   |  C - clear   Ctrl+S - save",
            True, (50, 50, 50)
        )
        screen.blit(text1, (5, 52))

        text2 = self.tiny_font.render(
            "Hotkeys: 1-0 tools  |  R G B Y P O K - colors  |  F1/F2/F3 - brush size",
            True, (130, 130, 130)
        )
        screen.blit(text2, (5, 68))

        brush_lbl = self.tiny_font.render("Brush:", True, (60, 60, 60))
        screen.blit(brush_lbl, (5, 78))

    def draw_brush_buttons(self, screen, current_thickness):
        btn_w, btn_h = 28, 22
        for i, rect in enumerate(self._brush_btn_rects):
            size_val  = BRUSH_SIZES[i]
            is_active = (current_thickness == size_val)
            bg = (90, 130, 200)  if is_active else (210, 210, 210)
            fg = (255, 255, 255) if is_active else (20,  20,  20)
            pygame.draw.rect(screen, bg,              rect, border_radius=4)
            pygame.draw.rect(screen, (120, 120, 120), rect, 1, border_radius=4)
            label = self.tiny_font.render(BRUSH_LABELS[i], True, fg)
            lx = rect.x + (btn_w - label.get_width())  // 2
            ly = rect.y + (btn_h - label.get_height()) // 2
            screen.blit(label, (lx, ly))

    def draw_color_palette(self, screen, colors, current_color):
        box_size  = 22
        spacing   = 3
        palette_x = 5 + 3 * (28 + 4) + 18
        palette_y = 93

        self._color_rects = []
        for i, color in enumerate(colors):
            x    = palette_x + (box_size + spacing) * i
            rect = pygame.Rect(x, palette_y, box_size, box_size)
            self._color_rects.append((rect, color))
            pygame.draw.rect(screen, color,     rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
            if color == current_color:
                pygame.draw.rect(screen, (255, 255, 255),
                                 (x - 2, palette_y - 2, box_size + 4, box_size + 4), 2)
                pygame.draw.rect(screen, (0, 0, 0),
                                 (x - 3, palette_y - 3, box_size + 6, box_size + 6), 1)

    # ── hit-testing ──────────────────────────────────────────────────────

    def tool_button_at(self, pos):
        for rect, mode in self._tool_btn_rects:
            if rect.collidepoint(pos):
                return mode
        return None

    def brush_button_at(self, pos):
        for i, rect in enumerate(self._brush_btn_rects):
            if rect.collidepoint(pos):
                return BRUSH_SIZES[i]
        return None

    def color_swatch_at(self, pos):
        for rect, color in self._color_rects:
            if rect.collidepoint(pos):
                return color
        return None
