import pygame

class Slider:
    def __init__(self, x, y, width, height, min_val=0.0, max_val=1.0, initial_val=0.5, label="Slider"):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.active = False
        self.slider_width = 10
        self.slider_color = (100, 200, 100)
        self.track_color = (80, 80, 80)
    
    def draw(self, surface, font):
        pygame.draw.rect(surface, self.track_color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 1)
        
        slider_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * (self.rect.width - self.slider_width))
        slider_rect = pygame.Rect(slider_x, self.rect.y, self.slider_width, self.rect.height)
        pygame.draw.rect(surface, self.slider_color, slider_rect)
        
        label_text = font.render(f"{self.label}: {self.value:.2f}", True, (220, 220, 220))
        surface.blit(label_text, (self.rect.x, self.rect.y - 20))
    
    def update(self, mouse_pos, mouse_pressed):
        if mouse_pressed[0]:
            if self.rect.collidepoint(mouse_pos):
                self.active = True
        else:
            self.active = False
            
        if self.active:
            rel_x = max(0, min(mouse_pos[0] - self.rect.x, self.rect.width - self.slider_width))
            self.value = self.min_val + (rel_x / (self.rect.width - self.slider_width)) * (self.max_val - self.min_val)
            return True
        return False
