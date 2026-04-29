import pygame
import sys
from datetime import datetime

from colors import *
from tools import (
    DrawTool, LineTool, EraserTool,
    RectangleTool, SquareTool, CircleTool,
    RightTriangleTool, EquilateralTriangleTool, RhombusTool,
    FillTool, TextTool,
    BRUSH_SIZES,
)
from ui import UI


# Shape tools that finalise on mouse-up (not continuous)
SHAPE_TOOLS = {"rect", "circle", "square", "right_triangle",
               "equilateral", "rhombus", "line"}


class PaintApp:
    """Main paint application class"""

    def __init__(self):
        pygame.init()
        self.screen_width  = 900
        self.screen_height = 650
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Paint Application — Extended")

        self.clock   = pygame.time.Clock()
        self.running = True

        # ── drawing state ──────────────────────────────────────────────────
        self.thickness = 5
        self.color     = BLACK
        self.mode      = "draw"
        self.drawing   = False
        self.start_pos = None
        self.last_pos  = None

        # Snapshot of the canvas before a preview-mode drag starts (line tool)
        self._canvas_snapshot = None

        # ── tools ─────────────────────────────────────────────────────────
        self.tools = {
            "draw":           DrawTool(),
            "line":           LineTool(),
            "rect":           RectangleTool(),
            "circle":         CircleTool(),
            "eraser":         EraserTool(),
            "square":         SquareTool(),
            "right_triangle": RightTriangleTool(),
            "equilateral":    EquilateralTriangleTool(),
            "rhombus":        RhombusTool(),
            "fill":           FillTool(),
            "text":           TextTool(),
        }

        # ── UI ────────────────────────────────────────────────────────────
        self.ui = UI(self.screen_width, self.screen_height)

        # Canvas starts white
        self.screen.fill(WHITE)

    # ── helpers ───────────────────────────────────────────────────────────

    def _canvas_rect(self):
        """Rectangle covering only the drawable area (below UI bar)."""
        return pygame.Rect(0, self.ui.ui_height, self.screen_width,
                           self.screen_height - self.ui.ui_height)

    def _in_canvas(self, pos):
        return self._canvas_rect().collidepoint(pos)

    def _snapshot(self):
        """Return a copy of the current screen (for line-preview restore)."""
        return self.screen.copy()

    # ── save (3.4) ────────────────────────────────────────────────────────

    def save_canvas(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"canvas_{timestamp}.png"
        pygame.image.save(self.screen, filename)
        print(f"[Save] Canvas saved as: {filename}")

        # Brief on-screen notification
        font = pygame.font.Font(None, 28)
        msg  = font.render(f"Saved: {filename}", True, (0, 140, 0))
        self.screen.blit(msg, (self.screen_width // 2 - msg.get_width() // 2, 5))
        pygame.display.flip()
        pygame.time.wait(1200)          # show notification for 1.2 s

    # ── event handling ────────────────────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():

            # ── quit ──────────────────────────────────────────────────────
            if event.type == pygame.QUIT:
                self.running = False

            # ── keyboard ──────────────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                # Let the text tool consume the key first
                text_tool = self.tools["text"]
                if self.mode == "text" and text_tool.active:
                    consumed = text_tool.handle_keydown(event, self.screen, self.color)
                    if consumed:
                        continue
                self.handle_keyboard(event)

            # ── mouse button down ─────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Click on tool buttons
                new_tool = self.ui.tool_button_at(pos)
                if new_tool is not None:
                    if self.mode == "text":
                        self.tools["text"].active = False
                        self.tools["text"].buffer = ""
                    self.mode = new_tool
                    continue

                # Click on brush-size buttons
                new_size = self.ui.brush_button_at(pos)
                if new_size is not None:
                    self.thickness = new_size
                    continue

                # Click on color swatches
                new_color = self.ui.color_swatch_at(pos)
                if new_color is not None:
                    self.color = new_color
                    continue

                if not self._in_canvas(pos):
                    continue

                # ── fill tool (single click) ───────────────────────────────
                if self.mode == "fill":
                    self.tools["fill"].flood_fill(self.screen, pos, self.color)
                    continue

                # ── text tool ─────────────────────────────────────────────
                if self.mode == "text":
                    self.tools["text"].on_mouse_down(pos)
                    continue

                # ── all other tools ────────────────────────────────────────
                self.drawing   = True
                self.start_pos = pos
                self.last_pos  = pos
                self.tools[self.mode].on_mouse_down(pos)

                # Snapshot canvas for line-preview restore
                if self.mode == "line":
                    self._canvas_snapshot = self._snapshot()

            # ── mouse button up ───────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not self.drawing:
                    continue
                self.drawing = False
                pos = event.pos

                if self.mode in SHAPE_TOOLS:
                    self.tools[self.mode].on_mouse_up(
                        pos, self.start_pos, self.screen, self.color, self.thickness
                    )

                self._canvas_snapshot = None
                self.start_pos = None
                self.last_pos  = None

            # ── mouse motion ──────────────────────────────────────────────
            elif event.type == pygame.MOUSEMOTION and self.drawing:
                pos = event.pos

                if self.mode in ("draw", "eraser"):
                    self.last_pos = self.tools[self.mode].on_mouse_move(
                        pos, self.last_pos, self.screen, self.color, self.thickness
                    )
                # Line tool: preview handled in run()

    # ── keyboard shortcuts ────────────────────────────────────────────────

    def handle_keyboard(self, event):
        mods = pygame.key.get_mods()

        # Ctrl+S — save (3.4)
        if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
            self.save_canvas()
            return

        # ── tool selection ────────────────────────────────────────────────
        key_tool_map = {
            pygame.K_1: "draw",
            pygame.K_2: "line",
            pygame.K_3: "rect",
            pygame.K_4: "circle",
            pygame.K_5: "eraser",
            pygame.K_6: "fill",
            pygame.K_7: "text",
            pygame.K_8: "square",
            pygame.K_9: "right_triangle",
            pygame.K_0: "equilateral",
            pygame.K_EQUALS: None,   # handled below for size
        }
        if event.key in key_tool_map and key_tool_map[event.key] is not None:
            new_mode = key_tool_map[event.key]
            # Cancel any active text session when switching away
            if self.mode == "text":
                self.tools["text"].active = False
                self.tools["text"].buffer = ""
            self.mode = new_mode
            return

        if event.key == pygame.K_MINUS and not (mods & pygame.KMOD_CTRL):
            # '-' mapped to rhombus (was K_MINUS in original) — use '=' instead
            pass
        if event.key == ord('=') or (event.key == pygame.K_MINUS and mods == 0):
            # check unicode for '='
            if event.unicode == '=':
                self.mode = "rhombus"
                return

        # ── brush size presets (3.2)  s/m/l keys ──────────────────────────
        if event.key == pygame.K_F1:
            self.thickness = BRUSH_SIZES[0]   # 2
            return
        if event.key == pygame.K_F2:
            self.thickness = BRUSH_SIZES[1]   # 5
            return
        if event.key == pygame.K_F3:
            self.thickness = BRUSH_SIZES[2]   # 10
            return

        # Fine-grain size adjustment with +/-
        if event.key == pygame.K_PLUS or (event.unicode == '+'):
            self.thickness = min(self.thickness + 1, 50)
            return
        if event.key == pygame.K_MINUS and (mods & pygame.KMOD_SHIFT):
            self.thickness = max(self.thickness - 1, 1)
            return

        # ── colour shortcuts ──────────────────────────────────────────────
        colour_map = {
            pygame.K_r: RED,
            pygame.K_g: GREEN,
            pygame.K_b: BLUE,
            pygame.K_y: YELLOW,
            pygame.K_p: PURPLE,
            pygame.K_o: ORANGE,
            pygame.K_k: BLACK,
            pygame.K_w: WHITE,
        }
        if event.key in colour_map:
            self.color = colour_map[event.key]
            return

        # ── clear ─────────────────────────────────────────────────────────
        if event.key == pygame.K_c and not (mods & pygame.KMOD_CTRL):
            self.screen.fill(WHITE)

    # ── main loop ─────────────────────────────────────────────────────────

    def run(self):
        while self.running:
            self.handle_events()

            # Line tool live preview (3.1)
            if self.mode == "line" and self.drawing and self._canvas_snapshot:
                mouse_pos = pygame.mouse.get_pos()
                self.tools["line"].draw_preview(
                    self.screen, self.start_pos, mouse_pos,
                    self.color, self.thickness, self._canvas_snapshot
                )

            # Text tool live preview (3.5)
            if self.mode == "text":
                self.tools["text"].draw_preview(self.screen, self.color, self.ui.ui_height)

            # UI
            self.ui.draw_tool_buttons(self.screen, self.mode)
            self.ui.draw_text(self.screen, self.mode, self.color, self.thickness)
            self.ui.draw_color_palette(self.screen, COLOR_PALETTE, self.color)
            self.ui.draw_brush_buttons(self.screen, self.thickness)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = PaintApp()
    app.run()
