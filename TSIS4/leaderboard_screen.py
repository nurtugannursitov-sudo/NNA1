"""
Leaderboard Screen - Displays top scores with table format (Task 3.6)
"""

import pygame
from utils import WIDTH, HEIGHT
from main_menu import Button

class LeaderboardScreen:
    """Enhanced leaderboard screen with table display"""
    
    def __init__(self, screen, db):
        self.screen = screen
        self.db = db
        self.width = WIDTH
        self.height = HEIGHT
        
        # Fonts
        self.title_font = pygame.font.Font(None, 56)
        self.header_font = pygame.font.Font(None, 28)
        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        
        # Button
        self.back_button = Button(
            self.width // 2 - 80, self.height - 60, 160, 40,
            "BACK", (100, 100, 100), (150, 150, 150)
        )
        
        self.refresh_button = Button(
            self.width - 110, 20, 90, 30,
            "REFRESH", (0, 100, 100), (0, 150, 150)
        )
        
        # Data
        self.top_scores = []
        self.username = ""
        self.personal_best = 0
        self.scroll_offset = 0
        self.max_scroll = 0
    
    def load_data(self, username):
        """Load leaderboard data and personal best"""
        self.username = username
        self.top_scores = self.db.get_top_scores(10)
        self.personal_best = self.db.get_personal_best(username)
        self.max_scroll = max(0, len(self.top_scores) - 8)
    
    def draw(self):
        """Draw the leaderboard screen"""
        self.screen.fill((0, 0, 0))
        
        # Draw decorative header
        self.draw_header()
        
        # Title
        title = self.title_font.render("LEADERBOARD", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title, title_rect)
        
        # Personal best section
        pb_text = f"YOUR PERSONAL BEST: {self.personal_best}"
        pb_color = (0, 255, 0) if self.personal_best > 0 else (150, 150, 150)
        pb_surface = self.header_font.render(pb_text, True, pb_color)
        pb_rect = pb_surface.get_rect(center=(self.width // 2, 110))
        self.screen.blit(pb_surface, pb_rect)
        
        # Draw table header
        self.draw_table_header()
        
        # Draw table rows
        self.draw_table_rows()
        
        # Draw buttons
        self.back_button.draw(self.screen)
        self.refresh_button.draw(self.screen)
        
        # Draw scroll indicator if needed
        if self.max_scroll > 0:
            self.draw_scroll_indicator()
    
    def draw_header(self):
        """Draw decorative header"""
        # Gradient bar
        for i in range(5):
            color = (50 + i * 10, 30 + i * 5, 0)
            pygame.draw.rect(self.screen, color, (0, i * 5, self.width, 5))
    
    def draw_table_header(self):
        """Draw table column headers"""
        headers = ["RANK", "PLAYER", "SCORE", "LEVEL", "DATE"]
        header_x = [60, 130, 350, 450, 520]
        header_y = 150
        
        # Draw header background
        header_rect = pygame.Rect(30, header_y - 10, self.width - 60, 35)
        pygame.draw.rect(self.screen, (30, 30, 50), header_rect)
        pygame.draw.rect(self.screen, (255, 215, 0), header_rect, 2)
        
        for i, header in enumerate(headers):
            header_surface = self.header_font.render(header, True, (255, 215, 0))
            self.screen.blit(header_surface, (header_x[i], header_y))
        
        # Separator line
        pygame.draw.line(self.screen, (100, 100, 100), 
                        (30, header_y + 25), (self.width - 30, header_y + 25), 1)
    
    def draw_table_rows(self):
        """Draw leaderboard table rows"""
        y_start = 200
        row_height = 35
        
        # Define column positions
        columns = {
            'rank': 60,
            'username': 130,
            'score': 350,
            'level': 450,
            'date': 520
        }
        
        for i, score_data in enumerate(self.top_scores):
            # Check if within scroll view
            if i < self.scroll_offset:
                continue
            if i >= self.scroll_offset + 8:
                break
            
            y = y_start + (i - self.scroll_offset) * row_height
            
            # Highlight current player's row
            if score_data['username'] == self.username:
                highlight_rect = pygame.Rect(30, y - 5, self.width - 60, row_height)
                pygame.draw.rect(self.screen, (50, 50, 80), highlight_rect)
            
            # Rank with medal colors for top 3
            rank = score_data['rank']
            if rank == 1:
                rank_color = (255, 215, 0)  # Gold
                medal = "🥇"
            elif rank == 2:
                rank_color = (192, 192, 192)  # Silver
                medal = "🥈"
            elif rank == 3:
                rank_color = (205, 127, 50)  # Bronze
                medal = "🥉"
            else:
                rank_color = (255, 255, 255)
                medal = f"#{rank}"
            
            # Draw rank
            rank_text = self.font.render(medal, True, rank_color)
            self.screen.blit(rank_text, (columns['rank'], y))
            
            # Draw username (truncate if too long)
            username = score_data['username'][:15]
            if len(score_data['username']) > 15:
                username += "..."
            username_text = self.font.render(username, True, (255, 255, 255))
            self.screen.blit(username_text, (columns['username'], y))
            
            # Draw score
            score_text = self.font.render(str(score_data['score']), True, (255, 255, 255))
            self.screen.blit(score_text, (columns['score'], y))
            
            # Draw level
            level_text = self.font.render(str(score_data['level']), True, (255, 255, 255))
            self.screen.blit(level_text, (columns['level'], y))
            
            # Draw date (only show date part)
            date_str = score_data['date'][:10]
            date_text = self.small_font.render(date_str, True, (150, 150, 150))
            self.screen.blit(date_text, (columns['date'], y + 5))
            
            # Draw separator line
            pygame.draw.line(self.screen, (40, 40, 40), 
                           (30, y + row_height - 5), (self.width - 30, y + row_height - 5), 1)
        
        # No scores message
        if not self.top_scores:
            no_scores_text = self.font.render("No scores yet. Play a game!", True, (150, 150, 150))
            no_scores_rect = no_scores_text.get_rect(center=(self.width // 2, 300))
            self.screen.blit(no_scores_text, no_scores_rect)
    
    def draw_scroll_indicator(self):
        """Draw scroll indicator if there are more entries"""
        # Scroll bar background
        scroll_bg = pygame.Rect(self.width - 20, 190, 10, 280)
        pygame.draw.rect(self.screen, (40, 40, 40), scroll_bg)
        
        # Scroll bar handle
        total_rows = len(self.top_scores)
        visible_rows = 8
        handle_height = int(280 * (visible_rows / total_rows))
        handle_y = 190 + int(280 * (self.scroll_offset / total_rows))
        scroll_handle = pygame.Rect(self.width - 20, handle_y, 10, handle_height)
        pygame.draw.rect(self.screen, (100, 100, 150), scroll_handle)
        
        # Scroll arrows
        up_arrow = pygame.Rect(self.width - 20, 185, 10, 5)
        down_arrow = pygame.Rect(self.width - 20, 470, 10, 5)
        pygame.draw.polygon(self.screen, (150, 150, 150), 
                           [(up_arrow.x + 5, up_arrow.y), 
                            (up_arrow.x, up_arrow.y + 5), 
                            (up_arrow.x + 10, up_arrow.y + 5)])
        pygame.draw.polygon(self.screen, (150, 150, 150), 
                           [(down_arrow.x + 5, down_arrow.y + 5), 
                            (down_arrow.x, down_arrow.y), 
                            (down_arrow.x + 10, down_arrow.y)])
    
    def handle_event(self, event):
        """Handle events on leaderboard screen"""
        # Handle scroll wheel
        if event.type == pygame.MOUSEWHEEL:
            if event.y < 0 and self.scroll_offset < self.max_scroll:
                self.scroll_offset += 1
            elif event.y > 0 and self.scroll_offset > 0:
                self.scroll_offset -= 1
        
        # Handle button clicks
        if self.back_button.handle_event(event):
            return "back"
        
        if self.refresh_button.handle_event(event):
            self.top_scores = self.db.get_top_scores(10)
            self.personal_best = self.db.get_personal_best(self.username)
            return "refresh"
        
        return None