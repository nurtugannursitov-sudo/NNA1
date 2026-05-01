"""
Settings Screen - Customize game preferences with improved UI (Task 3.6)
"""

import pygame
from utils import WIDTH, HEIGHT
from main_menu import Button

class SettingsScreen:
    """Enhanced settings screen with better UI"""
    
    def __init__(self, screen, settings_manager):
        self.screen = screen
        self.settings = settings_manager
        self.width = WIDTH
        self.height = HEIGHT
        
        # Fonts
        self.title_font = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # Color selection state
        self.selected_color = None
        self.color_picker_active = False
        self.rgb_values = [0, 0, 0]
        
        # UI elements positions
        self.grid_checkbox_rect = pygame.Rect(self.width // 2 - 150, 160, 25, 25)
        self.sound_checkbox_rect = pygame.Rect(self.width // 2 - 150, 220, 25, 25)
        
        # Color preview rectangles
        self.head_preview = pygame.Rect(self.width // 2 + 100, 290, 50, 50)
        self.body_preview = pygame.Rect(self.width // 2 + 100, 355, 50, 50)
        self.dark_body_preview = pygame.Rect(self.width // 2 + 100, 420, 50, 50)
        
        # Buttons
        self.save_button = Button(
            self.width // 2 - 100, self.height - 80, 200, 45,
            "SAVE & BACK", (0, 100, 0), (0, 150, 0)
        )
        
        # Color picker buttons
        self.picker_confirm = None
        self.picker_cancel = None
        
        # Dragging state
        self.dragging_slider = None
        self.color_sliders = {}
    
    def draw(self):
        """Draw the settings screen"""
        self.screen.fill((0, 0, 0))
        
        # Title
        title = self.title_font.render("SETTINGS", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Draw settings panel
        panel_rect = pygame.Rect(50, 100, self.width - 100, self.height - 200)
        pygame.draw.rect(self.screen, (20, 20, 30), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)
        
        # Grid Overlay setting
        grid_text = self.font.render("Show Grid Overlay:", True, (255, 255, 255))
        self.screen.blit(grid_text, (self.width // 2 - 350, 165))
        self.draw_checkbox(self.grid_checkbox_rect, self.settings.get_grid_overlay())
        
        # Sound setting
        sound_text = self.font.render("Enable Sound:", True, (255, 255, 255))
        self.screen.blit(sound_text, (self.width // 2 - 350, 225))
        self.draw_checkbox(self.sound_checkbox_rect, self.settings.get_sound())
        
        # Snake Colors section
        color_title = self.font.render("SNAKE COLORS", True, (255, 215, 0))
        self.screen.blit(color_title, (self.width // 2 - 350, 290))
        
        # Divider line
        pygame.draw.line(self.screen, (100, 100, 100), 
                        (self.width // 2 - 350, 310), 
                        (self.width // 2 + 300, 310), 1)
        
        # Head color
        head_text = self.font.render("Head Color:", True, (255, 255, 255))
        self.screen.blit(head_text, (self.width // 2 - 350, 330))
        head_color = self.settings.get_setting("snake_color", "head")
        pygame.draw.rect(self.screen, tuple(head_color), self.head_preview)
        pygame.draw.rect(self.screen, (255, 255, 255), self.head_preview, 2)
        
        # Body color
        body_text = self.font.render("Body Color:", True, (255, 255, 255))
        self.screen.blit(body_text, (self.width // 2 - 350, 395))
        body_color = self.settings.get_setting("snake_color", "body")
        pygame.draw.rect(self.screen, tuple(body_color), self.body_preview)
        pygame.draw.rect(self.screen, (255, 255, 255), self.body_preview, 2)
        
        # Dark body color
        dark_body_text = self.font.render("Dark Body Color:", True, (255, 255, 255))
        self.screen.blit(dark_body_text, (self.width // 2 - 350, 460))
        dark_body_color = self.settings.get_setting("snake_color", "dark_body")
        pygame.draw.rect(self.screen, tuple(dark_body_color), self.dark_body_preview)
        pygame.draw.rect(self.screen, (255, 255, 255), self.dark_body_preview, 2)
        
        # Instruction text
        inst_text = self.small_font.render("Click on color boxes to customize", True, (150, 150, 150))
        self.screen.blit(inst_text, (self.width // 2 - 350, 520))
        
        # Draw save button
        self.save_button.draw(self.screen)
        
        # Draw color picker if active
        if self.color_picker_active:
            self.draw_color_picker()
    
    def draw_checkbox(self, rect, checked):
        """Draw a checkbox"""
        pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
        if checked:
            pygame.draw.line(self.screen, (0, 255, 0), 
                           (rect.x + 5, rect.y + rect.height // 2),
                           (rect.x + rect.width // 2, rect.y + rect.height - 8), 3)
            pygame.draw.line(self.screen, (0, 255, 0),
                           (rect.x + rect.width // 2, rect.y + rect.height - 8),
                           (rect.x + rect.width - 8, rect.y + 5), 3)
    
    def draw_color_picker(self):
        """Draw the color picker interface"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Color picker panel
        panel_rect = pygame.Rect(self.width // 2 - 250, self.height // 2 - 180, 500, 360)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect)
        pygame.draw.rect(self.screen, (255, 215, 0), panel_rect, 2)
        
        # Title
        title = self.font.render(f"Pick {self.selected_color.upper()} Color", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 140))
        self.screen.blit(title, title_rect)
        
        # Color preview
        preview_rect = pygame.Rect(self.width // 2 + 150, self.height // 2 - 110, 80, 80)
        pygame.draw.rect(self.screen, self.rgb_values, preview_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), preview_rect, 2)
        
        # RGB Sliders
        colors = {'R': (255, 0, 0), 'G': (0, 255, 0), 'B': (0, 0, 255)}
        y_offset = self.height // 2 - 60
        
        for i, (channel, color) in enumerate(colors.items()):
            y = y_offset + i * 55
            
            # Label
            label = self.font.render(f"{channel}:", True, color)
            self.screen.blit(label, (self.width // 2 - 200, y))
            
            # Value
            value_text = self.font.render(str(self.rgb_values[i]), True, (255, 255, 255))
            self.screen.blit(value_text, (self.width // 2 + 50, y))
            
            # Slider background
            slider_bg = pygame.Rect(self.width // 2 - 130, y + 10, 160, 12)
            pygame.draw.rect(self.screen, (30, 30, 30), slider_bg)
            
            # Slider fill
            fill_width = int(160 * self.rgb_values[i] / 255)
            slider_fill = pygame.Rect(self.width // 2 - 130, y + 10, fill_width, 12)
            pygame.draw.rect(self.screen, color, slider_fill)
            
            # Slider handle
            handle_x = self.width // 2 - 130 + fill_width - 6
            handle_rect = pygame.Rect(handle_x, y + 5, 12, 22)
            pygame.draw.rect(self.screen, (255, 255, 255), handle_rect)
            
            # Store slider data
            self.color_sliders[channel] = {'rect': slider_bg, 'value': self.rgb_values[i]}
        
        # Buttons
        confirm_rect = pygame.Rect(self.width // 2 - 100, self.height // 2 + 100, 90, 35)
        cancel_rect = pygame.Rect(self.width // 2 + 10, self.height // 2 + 100, 90, 35)
        
        pygame.draw.rect(self.screen, (0, 150, 0), confirm_rect)
        pygame.draw.rect(self.screen, (150, 0, 0), cancel_rect)
        
        confirm_text = self.small_font.render("OK", True, (255, 255, 255))
        cancel_text = self.small_font.render("Cancel", True, (255, 255, 255))
        
        confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
        cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
        
        self.screen.blit(confirm_text, confirm_text_rect)
        self.screen.blit(cancel_text, cancel_text_rect)
        
        self.picker_confirm = confirm_rect
        self.picker_cancel = cancel_rect
    
    def handle_event(self, event):
        """Handle events on settings screen"""
        # Handle color picker if active
        if self.color_picker_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                
                # Check confirm button
                if self.picker_confirm and self.picker_confirm.collidepoint(pos):
                    if self.selected_color == 'head':
                        self.settings.set_snake_color('head', *self.rgb_values)
                    elif self.selected_color == 'body':
                        self.settings.set_snake_color('body', *self.rgb_values)
                    elif self.selected_color == 'dark_body':
                        self.settings.set_snake_color('dark_body', *self.rgb_values)
                    self.color_picker_active = False
                    self.selected_color = None
                    return None
                
                # Check cancel button
                if self.picker_cancel and self.picker_cancel.collidepoint(pos):
                    self.color_picker_active = False
                    self.selected_color = None
                    return None
                
                # Check sliders
                for channel, slider_data in self.color_sliders.items():
                    if slider_data['rect'].collidepoint(pos):
                        self.dragging_slider = channel
                        return None
            
            elif event.type == pygame.MOUSEMOTION and self.dragging_slider:
                # Update slider value
                slider_rect = self.color_sliders[self.dragging_slider]['rect']
                relative_x = max(0, min(slider_rect.width, event.pos[0] - slider_rect.x))
                value = int((relative_x / slider_rect.width) * 255)
                
                if self.dragging_slider == 'R':
                    self.rgb_values[0] = value
                elif self.dragging_slider == 'G':
                    self.rgb_values[1] = value
                elif self.dragging_slider == 'B':
                    self.rgb_values[2] = value
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_slider = None
            
            return None
        
        # Handle main settings screen interactions
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            # Check grid checkbox
            if self.grid_checkbox_rect.collidepoint(pos):
                new_value = not self.settings.get_grid_overlay()
                self.settings.set_grid_overlay(new_value)
                return None
            
            # Check sound checkbox
            if self.sound_checkbox_rect.collidepoint(pos):
                new_value = not self.settings.get_sound()
                self.settings.set_sound(new_value)
                return None
            
            # Check color preview boxes
            if self.head_preview.collidepoint(pos):
                self.selected_color = 'head'
                self.rgb_values = self.settings.get_setting("snake_color", "head").copy()
                self.color_picker_active = True
                return None
            
            if self.body_preview.collidepoint(pos):
                self.selected_color = 'body'
                self.rgb_values = self.settings.get_setting("snake_color", "body").copy()
                self.color_picker_active = True
                return None
            
            if self.dark_body_preview.collidepoint(pos):
                self.selected_color = 'dark_body'
                self.rgb_values = self.settings.get_setting("snake_color", "dark_body").copy()
                self.color_picker_active = True
                return None
        
        # Check save button
        if self.save_button.handle_event(event):
            return "save"
        
        return None