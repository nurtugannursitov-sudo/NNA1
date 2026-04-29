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

SHAPE_TOOLS = {"rect", "circle", "square", "right_triangle",
               "equilateral", "rhombus", "line"}


class PaintApp:
    def __init__(self):
        pygame.init()
        self.screen_width  = 900
        self.screen_height = 650
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Paint Application — Extended")

        self.clock   = pygame.time.Clock()
        self.running = True

        self.thickness = 5
        self.color     = BLACK
        self.mode      = "draw"
        self.drawing   = False
        self.start_pos = None
        self.last_pos  = None
        self._canvas_snapshot = None

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

        self.ui = UI(self.screen_width, self.screen_height)
        self.screen.fill(WHITE)

    def _canvas_rect(self):
        return pygame.Rect(0, self.ui.ui_height, self.screen_width,
                           self.screen_height - self.ui.ui_height)

    def _in_canvas(self, pos):
        return self._canvas_rect().collidepoint(pos)

    def _snapshot(self):
        return self.screen.copy()

    def save_canvas(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"canvas_{timestamp}.png"
        pygame.image.save(self.screen, filename)
        print(f"[Save] Canvas saved as: {filename}")
        font = pygame.font.Font(None, 28)
        msg  = font.render(f"Saved: {filename}", True, (0, 140, 0))
        self.screen.blit(msg, (self.screen_width // 2 - msg.get_width() // 2, 5))
        pygame.display.flip()
        pygame.time.wait(1200)

    def handle_events(self):
        text_tool = self.tools["text"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # ── TEXTINPUT: правильный способ получить Unicode/кириллицу ──
            elif event.type == pygame.TEXTINPUT:
                if self.mode == "text" and text_tool.active:
                    text_tool.handle_textinput(event.text)
                continue

            elif event.type == pygame.KEYDOWN:
                # Управляющие клавиши текстового инструмента
                if self.mode == "text" and text_tool.active:
                    consumed = text_tool.handle_keydown(event, self.screen, self.color)
                    if consumed:
                        continue
                self.handle_keyboard(event)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                new_tool = self.ui.tool_button_at(pos)
                if new_tool is not None:
                    if self.mode == "text":
                        text_tool.stop()
                    self.mode = new_tool
                    continue

                new_size = self.ui.brush_button_at(pos)
                if new_size is not None:
                    self.thickness = new_size
                    continue

                new_color = self.ui.color_swatch_at(pos)
                if new_color is not None:
                    self.color = new_color
                    continue

                if not self._in_canvas(pos):
                    continue

                if self.mode == "fill":
                    self.tools["fill"].flood_fill(self.screen, pos, self.color)
                    continue

                if self.mode == "text":
                    text_tool.on_mouse_down(pos)
                    continue

                self.drawing   = True
                self.start_pos = pos
                self.last_pos  = pos
                self.tools[self.mode].on_mouse_down(pos)

                if self.mode == "line":
                    self._canvas_snapshot = self._snapshot()

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

            elif event.type == pygame.MOUSEMOTION and self.drawing:
                pos = event.pos
                if self.mode in ("draw", "eraser"):
                    self.last_pos = self.tools[self.mode].on_mouse_move(
                        pos, self.last_pos, self.screen, self.color, self.thickness
                    )

    def handle_keyboard(self, event):
        mods = pygame.key.get_mods()

        if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
            self.save_canvas()
            return

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
        }
        if event.key in key_tool_map:
            new_mode = key_tool_map[event.key]
            if self.mode == "text":
                self.tools["text"].stop()
            self.mode = new_mode
            return

        if event.unicode == '=':
            self.mode = "rhombus"
            return

        if event.key == pygame.K_F1:
            self.thickness = BRUSH_SIZES[0]; return
        if event.key == pygame.K_F2:
            self.thickness = BRUSH_SIZES[1]; return
        if event.key == pygame.K_F3:
            self.thickness = BRUSH_SIZES[2]; return

        if event.unicode == '+':
            self.thickness = min(self.thickness + 1, 50); return
        if event.key == pygame.K_MINUS and (mods & pygame.KMOD_SHIFT):
            self.thickness = max(self.thickness - 1, 1); return

        colour_map = {
            pygame.K_r: RED,   pygame.K_g: GREEN,
            pygame.K_b: BLUE,  pygame.K_y: YELLOW,
            pygame.K_p: PURPLE, pygame.K_o: ORANGE,
            pygame.K_k: BLACK, pygame.K_w: WHITE,
        }
        if event.key in colour_map:
            self.color = colour_map[event.key]; return

        if event.key == pygame.K_c and not (mods & pygame.KMOD_CTRL):
            self.screen.fill(WHITE)

    def run(self):
        while self.running:
            self.handle_events()

            if self.mode == "line" and self.drawing and self._canvas_snapshot:
                mouse_pos = pygame.mouse.get_pos()
                self.tools["line"].draw_preview(
                    self.screen, self.start_pos, mouse_pos,
                    self.color, self.thickness, self._canvas_snapshot
                )

            if self.mode == "text":
                self.tools["text"].draw_preview(self.screen, self.color, self.ui.ui_height)

            # UI — сначала фон, потом кнопки поверх
            self.ui.draw_text(self.screen, self.mode, self.color, self.thickness)
            self.ui.draw_tool_buttons(self.screen, self.mode)
            self.ui.draw_color_palette(self.screen, COLOR_PALETTE, self.color)
            self.ui.draw_brush_buttons(self.screen, self.thickness)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = PaintApp()
    app.run()
