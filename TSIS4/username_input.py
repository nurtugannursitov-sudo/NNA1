"""
Enter player name before starting
"""

import pygame
from utils import WIDTH, HEIGHT
from main_menu import Button

class UsernameInput:
    """Username input screen with improved UI"""
    
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.title_font = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 28)
        
        self.username = ""
        self.active = True
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Buttons
        self.continue_button = Button(
            self.width // 2 - 100, self.height // 2 + 100, 200, 45,
            "CONTINUE", (0, 100, 0), (0, 150, 0)
        )
        
        self.quit_button = Button(
            self.width // 2 - 100, self.height // 2 + 160, 200, 45,
            "QUIT", (100, 0, 0), (150, 0, 0)
        )
    
    def handle_event(self, event):
        """Handle keyboard input for username"""
        # Handle button clicks
        if self.continue_button.handle_event(event) and len(self.username) >= 3:
            return True
        
        if self.quit_button.handle_event(event):
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and len(self.username) >= 3:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            elif event.key == pygame.K_ESCAPE:
                return False
            else:
                if len(self.username) < 20 and event.unicode.isprintable():
                    self.username += event.unicode
        return None
    
    def update_cursor(self, dt):
        """Update cursor blinking"""
        self.cursor_timer += dt
        if self.cursor_timer >= 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self):
        """Draw username input screen"""
        self.screen.fill((0, 0, 0))
        
        # Draw decorative background
        self.draw_background()
        
        # Title
        title = self.title_font.render("WELCOME TO SNAKE GAME", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Instructions
        inst1 = self.font.render("Enter your username:", True, (255, 255, 255))
        inst1_rect = inst1.get_rect(center=(self.width // 2, 230))
        self.screen.blit(inst1, inst1_rect)
        
        # Input box
        box_rect = pygame.Rect(self.width // 2 - 200, 300, 400, 60)
        pygame.draw.rect(self.screen, (30, 30, 40), box_rect)
        pygame.draw.rect(self.screen, (255, 215, 0), box_rect, 3)
        
        # Username text with cursor
        display_text = self.username
        if self.active and self.cursor_visible:
            display_text += "|"
        
        text_surface = self.font.render(display_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=box_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        # Character count
        count_text = self.small_font.render(f"{len(self.username)}/20 characters", True, (150, 150, 150))
        count_rect = count_text.get_rect(center=(self.width // 2, 380))
        self.screen.blit(count_text, count_rect)
        
        # Warning for short username
        if len(self.username) < 3 and self.username:
            warning = self.small_font.render("Username must be at least 3 characters", True, (255, 0, 0))
            warning_rect = warning.get_rect(center=(self.width // 2, 420))
            self.screen.blit(warning, warning_rect)
        
        # Draw buttons
        self.continue_button.draw(self.screen)
        self.quit_button.draw(self.screen)
        
        # Highlight continue button if username valid
        if len(self.username) >= 3:
            pygame.draw.rect(self.screen, (0, 255, 0), self.continue_button.rect, 3)
    
    def draw_background(self):
        """Draw decorative background"""
        # Draw snake pattern
        for i in range(0, self.width, 40):
            for j in range(0, self.height, 40):
                if (i // 40 + j // 40) % 2 == 0:
                    pygame.draw.rect(self.screen, (10, 20, 10), (i, j, 38, 38), 1)