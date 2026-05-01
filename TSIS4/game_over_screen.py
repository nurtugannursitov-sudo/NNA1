"""
Game Over Screen - Shows final stats and provides retry options (Task 3.6)
"""

import pygame
from utils import WIDTH, HEIGHT
from main_menu import Button

class GameOverScreen:
    """Game over screen with final scores and navigation buttons"""
    
    def __init__(self, screen):
        self.screen = screen
        self.width = WIDTH
        self.height = HEIGHT
        
        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.big_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Buttons
        button_width = 180
        button_height = 50
        button_x = self.width // 2 - button_width - 20
        start_y = self.height // 2 + 100
        
        self.retry_button = Button(
            button_x, start_y, button_width, button_height,
            "RETRY", (0, 100, 0), (0, 150, 0)
        )
        
        self.menu_button = Button(
            button_x + button_width + 40, start_y, button_width, button_height,
            "MAIN MENU", (100, 0, 0), (150, 0, 0)
        )
        
        self.quit_button = Button(
            button_x + (button_width + 40) * 2, start_y, button_width, button_height,
            "QUIT", (80, 80, 80), (120, 120, 120)
        )
        
        self.buttons = [self.retry_button, self.menu_button, self.quit_button]
        
        # Game stats
        self.score = 0
        self.level = 0
        self.personal_best = 0
        self.obstacles_avoided = 0
        self.powerups_collected = 0
    
    def set_stats(self, score, level, personal_best, obstacles_avoided=0, powerups_collected=0):
        """Set the game statistics to display"""
        self.score = score
        self.level = level
        self.personal_best = personal_best
        self.obstacles_avoided = obstacles_avoided
        self.powerups_collected = powerups_collected
    
    def draw(self):
        """Draw the game over screen"""
        self.screen.fill((0, 0, 0))
        
        # Draw dramatic background effect
        self.draw_dramatic_effect()
        
        # Game Over title
        title_text = self.title_font.render("GAME OVER", True, (255, 0, 0))
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)
        
        # Draw skull icon (ASCII art style)
        self.draw_skull_icon()
        
        # Stats panel
        panel_rect = pygame.Rect(self.width // 2 - 250, 140, 500, 200)
        pygame.draw.rect(self.screen, (20, 20, 30), panel_rect)
        pygame.draw.rect(self.screen, (255, 215, 0), panel_rect, 2)
        
        # Stats text
        stats = [
            (f"Final Score: {self.score}", (255, 255, 255)),
            (f"Level Reached: {self.level}", (255, 255, 255)),
            (f"Personal Best: {self.personal_best}", (0, 255, 0) if self.score >= self.personal_best else (255, 255, 0)),
            (f"Obstacles Avoided: {self.obstacles_avoided}", (150, 150, 150)),
            (f"Power-ups Collected: {self.powerups_collected}", (150, 150, 150))
        ]
        
        y_offset = 170
        for text, color in stats:
            stat_text = self.font.render(text, True, color)
            stat_rect = stat_text.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(stat_text, stat_rect)
            y_offset += 35
        
        # New record message
        if self.score >= self.personal_best and self.score > 0:
            record_text = self.big_font.render("NEW RECORD!", True, (255, 215, 0))
            record_rect = record_text.get_rect(center=(self.width // 2, 310))
            # Pulsing effect
            pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500
            record_rect.y = 310 - int(pulse * 5)
            self.screen.blit(record_text, record_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
        
        # Instructions
        inst_font = pygame.font.Font(None, 20)
        inst_text = inst_font.render("Press ESC to quit at any time", True, (80, 80, 80))
        inst_rect = inst_text.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(inst_text, inst_rect)
    
    def draw_dramatic_effect(self):
        """Draw dramatic background effect"""
        # Create gradient effect
        for i in range(HEIGHT):
            intensity = int(255 * (1 - i / HEIGHT))
            color = (intensity // 8, 0, 0)
            pygame.draw.line(self.screen, color, (0, i), (WIDTH, i))
    
    def draw_skull_icon(self):
        """Draw a skull icon for game over screen"""
        center_x = self.width // 2
        center_y = 95
        
        # Draw skull (simple shape)
        skull_rect = pygame.Rect(center_x - 20, center_y - 20, 40, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), skull_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), skull_rect, 2)
        
        # Eyes
        pygame.draw.circle(self.screen, (0, 0, 0), (center_x - 10, center_y - 5), 5)
        pygame.draw.circle(self.screen, (0, 0, 0), (center_x + 10, center_y - 5), 5)
        
        # Mouth
        pygame.draw.arc(self.screen, (0, 0, 0), 
                       (center_x - 10, center_y + 5, 20, 15), 
                       3.14, 6.28, 2)
    
    def handle_event(self, event):
        """Handle events and return selected action"""
        for button in self.buttons:
            if button.handle_event(event):
                if button == self.retry_button:
                    return "retry"
                elif button == self.menu_button:
                    return "menu"
                elif button == self.quit_button:
                    return "quit"
        return None