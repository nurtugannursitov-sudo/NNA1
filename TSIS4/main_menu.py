"""
Main Menu Screen - Navigation hub for the game (Task 3.6)
"""

import pygame
from utils import WIDTH, HEIGHT

class Button:
    """Simple button class for UI elements"""
    
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
    
    def draw(self, screen):
        """Draw the button"""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        """Handle mouse events for the button"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class MainMenu:
    """Main menu screen with navigation buttons"""
    
    def __init__(self, screen):
        self.screen = screen
        self.width = WIDTH
        self.height = HEIGHT
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 36)
        
        # Button dimensions
        button_width = 200
        button_height = 50
        button_x = self.width // 2 - button_width // 2
        start_y = self.height // 2 - 80
        
        # Create buttons
        self.play_button = Button(
            button_x, start_y, button_width, button_height,
            "PLAY", (0, 100, 0), (0, 150, 0)
        )
        
        self.leaderboard_button = Button(
            button_x, start_y + 70, button_width, button_height,
            "LEADERBOARD", (0, 0, 100), (0, 0, 150)
        )
        
        self.settings_button = Button(
            button_x, start_y + 140, button_width, button_height,
            "SETTINGS", (100, 100, 0), (150, 150, 0)
        )
        
        self.quit_button = Button(
            button_x, start_y + 210, button_width, button_height,
            "QUIT", (100, 0, 0), (150, 0, 0)
        )
        
        self.buttons = [
            self.play_button,
            self.leaderboard_button,
            self.settings_button,
            self.quit_button
        ]
    
    def draw(self):
        """Draw the main menu screen"""
        # Background
        self.screen.fill((0, 0, 0))
        
        # Draw animated snake pattern in background (optional)
        self.draw_background_pattern()
        
        # Title with gradient effect
        title_text = self.title_font.render("SNAKE GAME", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        
        # Draw shadow
        shadow_text = self.title_font.render("SNAKE GAME", True, (50, 50, 0))
        shadow_rect = shadow_text.get_rect(center=(self.width // 2 + 3, 103))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle = self.subtitle_font.render("Press 'S' for Settings at any time", True, (150, 150, 150))
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 160))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw decorative line
        pygame.draw.line(self.screen, (255, 215, 0), 
                        (self.width // 2 - 150, 180), 
                        (self.width // 2 + 150, 180), 2)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
        
        # Draw version info
        version_font = pygame.font.Font(None, 18)
        version_text = version_font.render("v2.0 - With Power-ups & Obstacles", True, (80, 80, 80))
        version_rect = version_text.get_rect(bottomright=(self.width - 10, self.height - 10))
        self.screen.blit(version_text, version_rect)
    
    def draw_background_pattern(self):
        """Draw subtle background pattern"""
        for i in range(0, self.width, 40):
            for j in range(0, self.height, 40):
                pygame.draw.rect(self.screen, (10, 10, 10), (i, j, 38, 38), 1)
    
    def handle_event(self, event):
        """Handle events and return selected action"""
        for button in self.buttons:
            if button.handle_event(event):
                if button == self.play_button:
                    return "play"
                elif button == self.leaderboard_button:
                    return "leaderboard"
                elif button == self.settings_button:
                    return "settings"
                elif button == self.quit_button:
                    return "quit"
        return None