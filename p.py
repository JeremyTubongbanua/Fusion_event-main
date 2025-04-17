import os
import json
import glob
import pygame
import sys

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, label, color=(200, 200, 200)):
        self.x = x
        self.y = y
        self.width = width
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.color = color
        self.grabbed = False
        self.knob_radius = 10
        
        # Calculate knob position
        self.update_knob_pos()
    
    def update_knob_pos(self):
        val_range = self.max_val - self.min_val
        val_percent = (self.value - self.min_val) / val_range
        self.knob_pos = self.x + int(val_percent * self.width)
    
    def draw(self, screen, font):
        # Draw slider track
        pygame.draw.line(screen, self.color, (self.x, self.y), (self.x + self.width, self.y), 3)
        
        # Draw knob
        pygame.draw.circle(screen, self.color, (self.knob_pos, self.y), self.knob_radius)
        
        # Draw label and value
        text = font.render(f"{self.label}: {self.value:.2f}", True, self.color)
        screen.blit(text, (self.x, self.y - 30))
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Check if knob is clicked
            knob_rect = pygame.Rect(self.knob_pos - self.knob_radius, self.y - self.knob_radius, 
                                   self.knob_radius * 2, self.knob_radius * 2)
            if knob_rect.collidepoint(mouse_pos):
                self.grabbed = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False
        
        elif event.type == pygame.MOUSEMOTION and self.grabbed:
            mouse_x = event.pos[0]
            # Constrain to slider bounds
            if mouse_x < self.x:
                mouse_x = self.x
            elif mouse_x > self.x + self.width:
                mouse_x = self.x + self.width
            
            # Update knob position
            self.knob_pos = mouse_x
            
            # Update value based on position
            pos_percent = (self.knob_pos - self.x) / self.width
            self.value = self.min_val + pos_percent * (self.max_val - self.min_val)
            
            return True  # Value changed
        
        return False  # Value not changed

def read_all_json_files(directory_path):
    all_data = {}
    json_pattern = os.path.join(directory_path, "*.json")
    json_files = glob.glob(json_pattern)
    
    for file_path in json_files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                all_data[file_name] = data
                print(f"Successfully read {file_name}")
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
    
    return all_data

def visualize_car_locations(all_json_data):
    pygame.init()
    
    # Load the background image
    background_image_path = "./images/scene.png"
    background = pygame.image.load(background_image_path)
    
    # Set up the screen
    screen_width, screen_height = background.get_size()
    screen_height += 200  # Extra space for sliders
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Car Locations with Adjustment Controls")
    
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
    ]
    
    font_color = (255, 255, 255)  # White
    font = pygame.font.Font(None, 20)
    
    # Initial parameters
    scale_factor = 5.0
    offset_x = screen_width // 2
    offset_y = screen_height // 2 - 100  # Adjusted for slider area
    
    # Create sliders
    sliders = [
        Slider(50, screen_height - 150, 300, 0.1, 100.0, scale_factor, "Scale Factor"),
        Slider(50, screen_height - 100, 300, 0, 10000, offset_x, "X Offset"),
        Slider(50, screen_height - 50, 300, 0, screen_height - 200, offset_y, "Y Offset")
    ]
    
    running = True
    show_labels = True
    
    clock = pygame.time.Clock()
    
    while running:
        need_update = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    show_labels = not show_labels
            
            # Handle slider events
            for slider in sliders:
                if slider.handle_event(event):
                    need_update = True
        
        # Get current values from sliders
        scale_factor = sliders[0].value
        offset_x = sliders[1].value
        offset_y = sliders[2].value
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw background
        screen.blit(background, (0, 0))
        
        # Process all JSON files and draw dots
        for file_name, data in all_json_data.items():
            for key, value in data.items():
                if "Location" in key:
                    car_id = key.split("_")[0]
                    location = value
                    dot_x = int(offset_x + location[0] * scale_factor)
                    dot_y = int(offset_y - location[1] * scale_factor)
                    
                    # Get color index based on combination of file_name and car_id
                    color_index = (hash(file_name + car_id)) % len(colors)
                    
                    # Draw dot
                    pygame.draw.circle(screen, colors[color_index], (dot_x, dot_y), 6)
                    
                    # Draw label if enabled
                    if show_labels:
                        label = f"{car_id} ({location[0]:.1f}, {location[1]:.1f})"
                        text = font.render(label, True, font_color)
                        screen.blit(text, (dot_x + 8, dot_y - 8))
        
        # Draw control panel background
        pygame.draw.rect(screen, (40, 40, 40), (0, screen_height - 200, screen_width, 200))
        
        # Draw controls title
        title_font = pygame.font.Font(None, 30)
        title_text = title_font.render("Adjustment Controls (Press SPACE to toggle labels)", True, (200, 200, 200))
        screen.blit(title_text, (50, screen_height - 190))
        
        # Draw current parameter values
        param_text = font.render(
            f"Current Settings - Scale: {scale_factor:.2f}, X Offset: {offset_x:.1f}, Y Offset: {offset_y:.1f}", 
            True, (200, 200, 200)
        )
        screen.blit(param_text, (400, screen_height - 190))
        
        # Draw sliders
        for slider in sliders:
            slider.draw(screen, font)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    input_directory = "./data/input"
    all_json_data = read_all_json_files(input_directory)
    
    print(f"Found {len(all_json_data)} JSON files")
    
    if all_json_data:
        visualize_car_locations(all_json_data)
    else:
        print("No JSON data found to visualize.")