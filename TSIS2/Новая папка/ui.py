"""
User Interface components for Paint Application
"""

import pygame
from tools import BRUSH_SIZES

# Brush size presets (3.2)
BRUSH_LABELS = ["S", "M", "L"]

# Tool buttons: (label, mode)
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


class IconDrawer:
    """Utility class to draw simple icons for tools"""
    
    @staticmethod
    def draw_pencil(surface, rect, color):
        """Draw pencil icon"""
        x, y = rect.centerx, rect.centery
        # Pencil shaft (diagonal line)
        pygame.draw.line(surface, color, (x - 6, y + 6), (x + 6, y - 6), 2)
        # Pencil tip (triangle)
        pygame.draw.polygon(surface, (255, 215, 0), [(x + 6, y - 6), (x + 8, y - 4), (x + 4, y - 8)])
    
    @staticmethod
    def draw_line(surface, rect, color):
        """Draw line icon"""
        x, y = rect.centerx, rect.centery
        pygame.draw.line(surface, color, (x - 8, y - 8), (x + 8, y + 8), 2)
    
    @staticmethod
    def draw_rect(surface, rect, color):
        """Draw rectangle icon"""
        x, y = rect.centerx, rect.centery
        pygame.draw.rect(surface, color, (x - 8, y - 6, 16, 12), 2)
    
    @staticmethod
    def draw_circle(surface, rect, color):
        """Draw circle icon"""
        x, y = rect.centerx, rect.centery
        pygame.draw.circle(surface, color, (x, y), 8, 2)
    
    @staticmethod
    def draw_eraser(surface, rect, color):
        """Draw eraser icon"""
        x, y = rect.centerx, rect.centery
        pygame.draw.rect(surface, (200, 200, 200), (x - 7, y - 6, 14, 12), 2)
        pygame.draw.line(surface, color, (x + 7, y - 6), (x - 7, y + 6), 1)
    
    @staticmethod
    def draw_fill(surface, rect, color):
        """Draw fill bucket icon"""
        x, y = rect.centerx, rect.centery
        # Bucket
        pygame.draw.polygon(surface, color, [(x - 6, y - 4), (x - 6, y + 6), (x + 6, y + 6), (x + 6, y - 4)])
        # Handle
        pygame.draw.line(surface, color, (x + 6, y - 4), (x + 8, y - 8), 2)
    
    @staticmethod
    def draw_text(surface, rect, color):
        """Draw text icon"""
        x, y = rect.centerx, rect.centery
        # Draw 'A'
        pygame.draw.line(surface, color, (x - 4, y + 6), (x, y - 6), 2)
        pygame.draw.line(surface, color, (x + 4, y + 6), (x, y - 6), 2)
        pygame.draw.line(surface, color, (x - 2, y), (x + 2, y), 2)
    
    @staticmethod
    def draw_square(surface, rect, color):
        """Draw square icon"""
        x, y = rect.centerx, rect.centery
        pygame.draw.rect(surface, color, (x - 7, y - 7, 14, 14), 2)
    
    @staticmethod
    def draw_right_triangle(surface, rect, color):
        """Draw right triangle icon"""
        x, y = rect.centerx, rect.centery
        points = [(x - 8, y + 6), (x + 8, y + 6), (x + 8, y - 6)]
        pygame.draw.polygon(surface, color, points, 2)
    
    @staticmethod
    def draw_equilateral_triangle(surface, rect, color):
        """Draw equilateral triangle icon"""
        x, y = rect.centerx, rect.centery
        points = [(x, y - 8), (x - 8, y + 6), (x + 8, y + 6)]
        pygame.draw.polygon(surface, color, points, 2)
    
    @staticmethod
    def draw_rhombus(surface, rect, color):
        """Draw rhombus icon"""
        x, y = rect.centerx, rect.centery
        points = [(x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)]
        pygame.draw.polygon(surface, color, points, 2)


class UI:
    """User interface manager"""

    def __init__(self, screen_width, screen_height):
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self.ui_height     = 115
        self.font       = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font  = pygame.font.Font(None, 16)

        # Tool button rects (top row)
        self._tool_btn_rects = []
        btn_w, btn_h = 68, 24
        gap = 3
        start_x, start_y = 5, 5
        for i, (label, mode) in enumerate(TOOL_BUTTONS):
            rect = pygame.Rect(start_x + i * (btn_w + gap), start_y, btn_w, btn_h)
            self._tool_btn_rects.append((rect, mode))

        # Brush-size button rects
        self._brush_btn_rects = []
        btn_w2, btn_h2 = 28, 22
        base_x, base_y = 5, 88
        for i in range(3):
            self._brush_btn_rects.append(
                pygame.Rect(base_x + i * (btn_w2 + 4), base_y, btn_w2, btn_h2)
            )

        # Color swatch rects (filled in draw_color_palette)
        self._color_rects = []
        
        # Icon drawer
        self.icon_drawer = IconDrawer()
        
        # Icon mapping
        self.icon_map = {
            "draw": self.icon_drawer.draw_pencil,
            "line": self.icon_drawer.draw_line,
            "rect": self.icon_drawer.draw_rect,
            "circle": self.icon_drawer.draw_circle,
            "eraser": self.icon_drawer.draw_eraser,
            "fill": self.icon_drawer.draw_fill,
            "text": self.icon_drawer.draw_text,
            "square": self.icon_drawer.draw_square,
            "right_triangle": self.icon_drawer.draw_right_triangle,
            "equilateral": self.icon_drawer.draw_equilateral_triangle,
            "rhombus": self.icon_drawer.draw_rhombus,
        }

    # ── drawing ──────────────────────────────────────────────────────────

    def draw_tool_buttons(self, screen, current_mode):
        """Draw clickable tool buttons with icons."""
        for rect, mode in self._tool_btn_rects:
            is_active = (mode == current_mode)
            bg     = (70, 120, 200)  if is_active else (210, 210, 215)
            fg     = (255, 255, 255) if is_active else (20,  20,  20)
            border = (40,  90,  170) if is_active else (150, 150, 155)
            pygame.draw.rect(screen, bg,     rect, border_radius=5)
            pygame.draw.rect(screen, border, rect, 1, border_radius=5)
            
            # Draw icon
            if mode in self.icon_map:
                self.icon_map[mode](screen, rect, fg)

    def draw_text(self, screen, mode, color, thickness):
        """Draw the UI bar background and status lines."""
        pygame.draw.rect(screen, (240, 240, 240), (0, 0, self.screen_width, self.ui_height))
        pygame.draw.line(screen, (180, 180, 180),
                         (0, self.ui_height), (self.screen_width, self.ui_height), 1)

        # Status line
        text1 = self.small_font.render(
            f"Mode: {mode}   Color: {color}   Size: {thickness}px"
            "   |  C - clear   Ctrl+S - save",
            True, (50, 50, 50)
        )
        screen.blit(text1, (5, 34))

        # Keyboard hint
        text2 = self.tiny_font.render(
            "Hotkeys: 1-11 tools  |  R G B Y P O K - colors  |  F1/F2/F3 - brush size",
            True, (130, 130, 130)
        )
        screen.blit(text2, (5, 54))

        # Brush label
        brush_lbl = self.tiny_font.render("Brush:", True, (60, 60, 60))
        screen.blit(brush_lbl, (5, 72))

    def draw_brush_buttons(self, screen, current_thickness):
        """Draw S / M / L brush-size buttons."""
        btn_w, btn_h = 28, 22
        for i, rect in enumerate(self._brush_btn_rects):
            size_val  = BRUSH_SIZES[i]
            is_active = (current_thickness == size_val)
            bg = (90, 130, 200)  if is_active else (210, 210, 210)
            fg = (255, 255, 255) if is_active else (20,  20,  20)
            pygame.draw.rect(screen, bg,          rect, border_radius=4)
            pygame.draw.rect(screen, (120,120,120), rect, 1, border_radius=4)
            label = self.tiny_font.render(BRUSH_LABELS[i], True, fg)
            lx = rect.x + (btn_w - label.get_width())  // 2
            ly = rect.y + (btn_h - label.get_height()) // 2
            screen.blit(label, (lx, ly))

    def draw_color_palette(self, screen, colors, current_color):
        """Draw colour swatches and cache their rects."""
        box_size = 22
        spacing  = 3
        palette_x = 5 + 3 * (28 + 4) + 18   # right of brush buttons
        palette_y = 88

        self._color_rects = []
        for i, color in enumerate(colors):
            x    = palette_x + (box_size + spacing) * i
            rect = pygame.Rect(x, palette_y, box_size, box_size)
            self._color_rects.append((rect, color))

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
            if color == current_color:
                pygame.draw.rect(screen, (255, 255, 255),
                                 (x - 2, palette_y - 2, box_size + 4, box_size + 4), 2)
                pygame.draw.rect(screen, (0, 0, 0),
                                 (x - 3, palette_y - 3, box_size + 6, box_size + 6), 1)

    # ── hit-testing ──────────────────────────────────────────────────────

    def tool_button_at(self, pos):
        """Return tool mode if pos hits a tool button, else None."""
        for rect, mode in self._tool_btn_rects:
            if rect.collidepoint(pos):
                return mode
        return None

    def brush_button_at(self, pos):
        """Return brush size if pos hits a brush button, else None."""
        for i, rect in enumerate(self._brush_btn_rects):
            if rect.collidepoint(pos):
                return BRUSH_SIZES[i]
        return None

    def color_swatch_at(self, pos):
        """Return color tuple if pos hits a color swatch, else None."""
        for rect, color in self._color_rects:
            if rect.collidepoint(pos):
                return color
        return None
