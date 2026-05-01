# ui.py
import pygame

WHITE = (255,255,255)

class Button:
    def __init__(self, x,y,w,h,text,color,hover):
        self.rect = pygame.Rect(x,y,w,h)
        self.text = text
        self.color = color
        self.hover = hover
        self.font = pygame.font.Font(None,36)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text = self.font.render(self.text, True, WHITE)
        screen.blit(text, text.get_rect(center=self.rect.center))