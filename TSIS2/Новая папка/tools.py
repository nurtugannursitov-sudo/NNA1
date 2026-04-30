"""
Drawing tools for Paint Application - Extended
"""

import pygame
import math
import os
from collections import deque
from shapes import Rectangle, Square, Circle, RightTriangle, EquilateralTriangle, Rhombus

BRUSH_SIZES = [2, 5, 10]


class Tool:
    def __init__(self, name, cursor_size=5):
        self.name = name
        self.cursor_size = cursor_size

    def on_mouse_down(self, pos):
        pass

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        pass

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        pass


class DrawTool(Tool):
    def __init__(self):
        super().__init__("draw", 5)

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        if last_pos is None or current_pos is None:
            return current_pos
        self.draw_line(screen, last_pos, current_pos, color, thickness)
        return current_pos

    def draw_line(self, screen, p1, p2, color, thickness):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = max(abs(dx), abs(dy))
        if dist == 0:
            pygame.draw.circle(screen, color, p1, thickness)
            return
        for i in range(dist + 1):
            t = i / dist
            x = int(p1[0] + dx * t)
            y = int(p1[1] + dy * t)
            pygame.draw.circle(screen, color, (x, y), thickness)


class LineTool(Tool):
    def __init__(self):
        super().__init__("line", 2)

    def on_mouse_down(self, pos):
        pass

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        return current_pos

    def draw_preview(self, screen, start_pos, current_pos, color, thickness, canvas_snapshot):
        if canvas_snapshot is None or start_pos is None:
            return
        screen.blit(canvas_snapshot, (0, 0))
        pygame.draw.line(screen, color, start_pos, current_pos, max(1, thickness * 2))

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        pygame.draw.line(screen, color, start_pos, pos, max(1, thickness * 2))


class EraserTool(Tool):
    def __init__(self):
        super().__init__("eraser", 10)

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        if last_pos is None or current_pos is None:
            return current_pos
        DrawTool().draw_line(screen, last_pos, current_pos, (255, 255, 255), thickness)
        return current_pos


class RectangleTool(Tool):
    def __init__(self):
        super().__init__("rect", 2)

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        Rectangle(color, thickness).draw(screen, start_pos, pos)


class SquareTool(Tool):
    def __init__(self):
        super().__init__("square", 2)

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        Square(color, thickness).draw(screen, start_pos, pos)


class CircleTool(Tool):
    def __init__(self):
        super().__init__("circle", 2)

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        Circle(color, thickness).draw(screen, start_pos, pos)


class RightTriangleTool(Tool):
    def __init__(self):
        super().__init__("right_triangle", 2)

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        RightTriangle(color, thickness).draw(screen, start_pos, pos)


class EquilateralTriangleTool(Tool):
    def __init__(self):
        super().__init__("equilateral", 2)

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        EquilateralTriangle(color, thickness).draw(screen, start_pos, pos)


class RhombusTool(Tool):
    def __init__(self):
        super().__init__("rhombus", 2)

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        Rhombus(color, thickness).draw(screen, start_pos, pos)


class FillTool(Tool):
    def __init__(self):
        super().__init__("fill", 0)

    def flood_fill(self, screen, pos, fill_color):
        x, y = int(pos[0]), int(pos[1])
        w, h = screen.get_width(), screen.get_height()
        target_color = screen.get_at((x, y))[:3]
        fill_rgb = fill_color[:3] if len(fill_color) == 4 else fill_color
        if target_color == fill_rgb:
            return
        visited = set()
        queue = deque()
        queue.append((x, y))
        visited.add((x, y))
        while queue:
            cx, cy = queue.popleft()
            if cx < 0 or cx >= w or cy < 0 or cy >= h:
                continue
            if screen.get_at((cx, cy))[:3] != target_color:
                continue
            screen.set_at((cx, cy), fill_rgb)
            for nx, ny in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))


def _make_cyrillic_font(size=24):
    """
    Load a font that supports Cyrillic on Windows.
    Tries direct .ttf paths first, then SysFont fallback.
    """
    # Windows font directory
    win_fonts = os.environ.get("WINDIR", "C:\\Windows") + "\\Fonts\\"

    candidates = [
        win_fonts + "arial.ttf",
        win_fonts + "arialbd.ttf",
        win_fonts + "tahoma.ttf",
        win_fonts + "tahomabd.ttf",
        win_fonts + "segoeui.ttf",
        win_fonts + "calibri.ttf",
        win_fonts + "verdana.ttf",
        win_fonts + "times.ttf",
        win_fonts + "cour.ttf",
    ]

    for path in candidates:
        if os.path.isfile(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue

    # Fallback: SysFont
    for name in ["arial", "tahoma", "segoeui", "calibri", "verdana"]:
        try:
            return pygame.font.SysFont(name, size)
        except Exception:
            continue

    return pygame.font.Font(None, size + 4)


class TextTool(Tool):
    """Click to place cursor, type characters, Enter to commit, Escape to cancel."""

    def __init__(self):
        super().__init__("text", 0)
        self.active     = False
        self.cursor_pos = (0, 0)
        self.buffer     = ""
        self.font       = None

    def _get_font(self, size=24):
        if self.font is None:
            self.font = _make_cyrillic_font(size)
        return self.font

    def on_mouse_down(self, pos):
        self.active     = True
        self.cursor_pos = pos
        self.buffer     = ""

    def handle_keydown(self, event, screen, color):
        if not self.active:
            return False

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._commit(screen, color)
            return True

        if event.key == pygame.K_ESCAPE:
            self.active = False
            self.buffer = ""
            return True

        if event.key == pygame.K_BACKSPACE:
            # Correctly remove last character (works with multi-byte Unicode too)
            self.buffer = self.buffer[:-1]
            return True

        # event.unicode handles ALL printable chars including Cyrillic
        if event.unicode and event.unicode.isprintable():
            self.buffer += event.unicode
            return True

        return False

    def _commit(self, screen, color):
        if self.buffer:
            font = self._get_font()
            surf = font.render(self.buffer, True, color)
            screen.blit(surf, self.cursor_pos)
        self.active = False
        self.buffer = ""

    def draw_preview(self, screen, color, ui_height):
        if not self.active:
            return
        font = self._get_font()
        preview = self.buffer + "|"
        surf = font.render(preview, True, color)
        x, y = self.cursor_pos
        if y < ui_height:
            return
        screen.blit(surf, (x, y))