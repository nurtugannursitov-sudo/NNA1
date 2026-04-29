"""
Drawing tools for Paint Application - Extended
"""

import pygame
import math
from collections import deque
from shapes import Rectangle, Square, Circle, RightTriangle, EquilateralTriangle, Rhombus

# Brush size presets (3.2)
BRUSH_SIZES = [2, 5, 10]


class Tool:
    """Base class for all drawing tools"""
    def __init__(self, name, cursor_size=5):
        self.name = name
        self.cursor_size = cursor_size

    def on_mouse_down(self, pos):
        pass

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        pass

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        pass


# ── 3.1 Pencil tool ─────────────────────────────────────────────────────────

class DrawTool(Tool):
    """Free-drawing pencil tool — draws continuously along cursor path"""
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


# ── 3.1 Straight-line tool ───────────────────────────────────────────────────

class LineTool(Tool):
    """Straight-line tool with live preview while dragging"""
    def __init__(self):
        super().__init__("line", 2)
        self._preview_surface = None   # snapshot before preview is drawn
        self._last_preview_end = None  # last endpoint drawn in preview

    def on_mouse_down(self, pos):
        self._preview_surface = None
        self._last_preview_end = None

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        """Draw a live preview line from start_pos to current mouse position."""
        # NOTE: start_pos is not passed here; the app stores it separately.
        # We abuse last_pos == None as a sentinel that this is a shape tool.
        return current_pos   # actual preview is handled in PaintApp

    def draw_preview(self, screen, start_pos, current_pos, color, thickness, canvas_snapshot):
        """Restore canvas and draw preview line — called from PaintApp each frame."""
        if canvas_snapshot is None or start_pos is None:
            return
        screen.blit(canvas_snapshot, (0, 0))   # restore clean canvas
        pygame.draw.line(screen, color, start_pos, current_pos, max(1, thickness * 2))

    def on_mouse_up(self, pos, start_pos, screen, color, thickness):
        if start_pos is None:
            return
        pygame.draw.line(screen, color, start_pos, pos, max(1, thickness * 2))


# ── Eraser ───────────────────────────────────────────────────────────────────

class EraserTool(Tool):
    """Eraser tool"""
    def __init__(self):
        super().__init__("eraser", 10)

    def on_mouse_move(self, current_pos, last_pos, screen, color, thickness):
        if last_pos is None or current_pos is None:
            return current_pos
        draw_tool = DrawTool()
        draw_tool.draw_line(screen, last_pos, current_pos, (255, 255, 255), thickness)
        return current_pos


# ── Shape tools (unchanged API) ───────────────────────────────────────────────

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


# ── 3.3 Flood-Fill tool ──────────────────────────────────────────────────────

class FillTool(Tool):
    """Flood-fill using BFS over canvas pixels"""
    def __init__(self):
        super().__init__("fill", 0)

    def on_mouse_down(self, pos):
        pass   # fill is triggered on mouse_up / click — handled in PaintApp

    def flood_fill(self, screen, pos, fill_color):
        """BFS flood fill starting at pos with fill_color."""
        x, y = int(pos[0]), int(pos[1])
        w, h = screen.get_width(), screen.get_height()

        target_color = screen.get_at((x, y))[:3]   # ignore alpha
        fill_rgb = fill_color[:3] if len(fill_color) == 4 else fill_color

        if target_color == fill_rgb:                # already the right color
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


# ── 3.5 Text tool ────────────────────────────────────────────────────────────

class TextTool(Tool):
    """Click to place cursor, type characters, Enter to commit, Escape to cancel."""
    def __init__(self):
        super().__init__("text", 0)
        self.active = False          # Are we in text-entry mode?
        self.cursor_pos = (0, 0)     # Where the text starts
        self.buffer = ""             # Characters typed so far
        self.font = None             # Lazily initialised

    def _get_font(self, size=24):
        if self.font is None:
            try:
                self.font = pygame.font.SysFont("monospace", size)
            except Exception:
                self.font = pygame.font.Font(None, size + 4)
        return self.font

    def on_mouse_down(self, pos):
        """Place text cursor at clicked position."""
        self.active = True
        self.cursor_pos = pos
        self.buffer = ""

    def handle_keydown(self, event, screen, color):
        """
        Returns True if the event was consumed.
        Call from PaintApp.handle_keyboard when mode == 'text'.
        """
        if not self.active:
            return False

        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            self._commit(screen, color)
            return True

        if event.key == pygame.K_ESCAPE:
            self.active = False
            self.buffer = ""
            return True

        if event.key == pygame.K_BACKSPACE:
            self.buffer = self.buffer[:-1]
            return True

        # Only printable ASCII
        if event.unicode and event.unicode.isprintable():
            self.buffer += event.unicode
            return True

        return False

    def _commit(self, screen, color):
        """Render text permanently onto the canvas."""
        if self.buffer:
            font = self._get_font()
            surf = font.render(self.buffer, True, color)
            screen.blit(surf, self.cursor_pos)
        self.active = False
        self.buffer = ""

    def draw_preview(self, screen, color, ui_height):
        """Draw the live text preview (with blinking cursor indicator)."""
        if not self.active:
            return
        font = self._get_font()
        # Draw typed text
        preview = self.buffer + "|"   # pipe as cursor
        surf = font.render(preview, True, color)
        # Don't draw over UI bar
        x, y = self.cursor_pos
        if y < ui_height:
            return
        screen.blit(surf, (x, y))
