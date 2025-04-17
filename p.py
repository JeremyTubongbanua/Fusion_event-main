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
        
        self.update_knob_pos()
    
    def update_knob_pos(self):
        val_range = self.max_val - self.min_val
        val_percent = (self.value - self.min_val) / val_range
        self.knob_pos = self.x + int(val_percent * self.width)
    
    def draw(self, screen, font):
        pygame.draw.line(screen, self.color, (self.x, self.y), (self.x + self.width, self.y), 3)
        
        pygame.draw.circle(screen, self.color, (self.knob_pos, self.y), self.knob_radius)
        
        text = font.render(f"{self.label}: {self.value:.2f}", True, self.color)
        screen.blit(text, (self.x, self.y - 30))
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            knob_rect = pygame.Rect(self.knob_pos - self.knob_radius, self.y - self.knob_radius, 
                                   self.knob_radius * 2, self.knob_radius * 2)
            if knob_rect.collidepoint(mouse_pos):
                self.grabbed = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False
        
        elif event.type == pygame.MOUSEMOTION and self.grabbed:
            mouse_x = event.pos[0]
            if mouse_x < self.x:
                mouse_x = self.x
            elif mouse_x > self.x + self.width:
                mouse_x = self.x + self.width
            
            self.knob_pos = mouse_x
            
            pos_percent = (self.knob_pos - self.x) / self.width
            self.value = self.min_val + pos_percent * (self.max_val - self.min_val)
            
            return True
        
        return False

class Checkbox:
    def __init__(self, x, y, label, color=(200, 200, 200), checked=True):
        self.x = x
        self.y = y
        self.label = label
        self.color = color
        self.checked = checked
        self.size = 16
        self.rect = pygame.Rect(x, y, self.size, self.size)
    
    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        if self.checked:
            pygame.draw.rect(screen, self.color, 
                            (self.x + 3, self.y + 3, self.size - 6, self.size - 6))
        
        text = font.render(self.label, True, self.color)
        screen.blit(text, (self.x + self.size + 5, self.y))
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True
        return False

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
    
    background_image_path = "./images/scene.png"
    try:
        background = pygame.image.load(background_image_path)
    except pygame.error:
        print(f"Warning: Could not load background image at {background_image_path}")
        background = pygame.Surface((800, 600))
        background.fill((0, 0, 0))
    
    base_width, base_height = background.get_size()
    
    # Calculate required screen width to fit all checkboxes
    screen_width = max(base_width, 1200)  # Ensure minimum width of 1200px for checkboxes
    
    # Add extra height if there are many JSON files to show all checkboxes
    file_count = len(all_json_data)
    extra_height = max(0, (file_count - 8) * 25)  # 25px per extra file beyond 8
    
    screen_height = base_height + 250 + extra_height
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
    
    font_color = (255, 255, 255)
    font = pygame.font.Font(None, 20)
    
    scale_x = 5.0
    scale_y = 5.0
    offset_x = screen_width // 2
    offset_y = screen_height // 2 - 150  
    image_scale_x = 1.0
    image_scale_y = 1.0
    
    sliders = [
        Slider(50, screen_height - 230, 300, 0.1, 100.0, scale_x, "Scale X Factor"),
        Slider(50, screen_height - 180, 300, 0.1, 100.0, scale_y, "Scale Y Factor"),
        Slider(50, screen_height - 130, 300, 0, 10000, offset_x, "X Offset"),
        Slider(50, screen_height - 80, 300, 0, screen_height - 250, offset_y, "Y Offset"),
        Slider(400, screen_height - 230, 300, 0.1, 3.0, image_scale_x, "Image Scale X"),
        Slider(400, screen_height - 180, 300, 0.1, 3.0, image_scale_y, "Image Scale Y")
    ]
    
    file_checkboxes = []
    # Organize checkboxes in columns if there are many files
    checkbox_x = 750
    checkbox_y = screen_height - 230
    line_height = 25
    max_checkboxes_per_column = 10
    column_width = 200
    
    for i, file_name in enumerate(all_json_data.keys()):
        column = i // max_checkboxes_per_column
        row = i % max_checkboxes_per_column
        cb_x = checkbox_x + (column * column_width)
        cb_y = checkbox_y + (row * line_height)
        checkbox = Checkbox(cb_x, cb_y, file_name)
        file_checkboxes.append(checkbox)
    
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
            
            for slider in sliders:
                if slider.handle_event(event):
                    need_update = True
            
            for checkbox in file_checkboxes:
                if checkbox.handle_event(event):
                    need_update = True
        
        scale_x = sliders[0].value
        scale_y = sliders[1].value
        offset_x = sliders[2].value
        offset_y = sliders[3].value
        image_scale_x = sliders[4].value
        image_scale_y = sliders[5].value
        
        screen.fill((0, 0, 0))
        
        scaled_width = int(background.get_width() * image_scale_x)
        scaled_height = int(background.get_height() * image_scale_y)
        scaled_background = pygame.transform.scale(background, (scaled_width, scaled_height))
        
        screen.blit(scaled_background, (0, 0))
        
        visible_files = {checkbox.label: checkbox.checked for checkbox in file_checkboxes}
        
        for file_name, data in all_json_data.items():
            if visible_files.get(file_name, True):
                for key, value in data.items():
                    if "Location" in key:
                        car_id = key.split("_")[0]
                        location = value
                        dot_x = int(offset_x + location[0] * scale_x)
                        dot_y = int(offset_y - location[1] * scale_y)
                        
                        color_index = (hash(file_name + car_id)) % len(colors)
                        
                        pygame.draw.circle(screen, colors[color_index], (dot_x, dot_y), 6)
                        
                        if show_labels:
                            label = f"{car_id} ({location[0]:.1f}, {location[1]:.1f}) - {file_name}"
                            text = font.render(label, True, font_color)
                            screen.blit(text, (dot_x + 8, dot_y - 8))
        
        pygame.draw.rect(screen, (40, 40, 40), (0, screen_height - 250, screen_width, 250))
        
        title_font = pygame.font.Font(None, 30)
        title_text = title_font.render("Adjustment Controls (Press SPACE to toggle labels)", True, (200, 200, 200))
        screen.blit(title_text, (50, screen_height - 250 + 10))
        
        param_text = font.render(
            f"Data: Scale X: {scale_x:.2f}, Scale Y: {scale_y:.2f}, X Offset: {offset_x:.1f}, Y Offset: {offset_y:.1f}", 
            True, (200, 200, 200)
        )
        screen.blit(param_text, (400, screen_height - 250 + 10))
        
        img_param_text = font.render(
            f"Image: Scale X: {image_scale_x:.2f}, Scale Y: {image_scale_y:.2f}", 
            True, (200, 200, 200)
        )
        screen.blit(img_param_text, (400, screen_height - 250 + 35))
        
        files_text = title_font.render("Files:", True, (200, 200, 200))
        screen.blit(files_text, (checkbox_x, checkbox_y - 30))
        
        for slider in sliders:
            slider.draw(screen, font)
        
        for checkbox in file_checkboxes:
            checkbox.draw(screen, font)
        
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