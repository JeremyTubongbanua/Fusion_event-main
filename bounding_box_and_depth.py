import os
import sys
import numpy as np
import cv2
import pygame
import torch
from pygame.locals import *
import glob
import time
import json
from ui.button import Button
from ui.slider import Slider

class MapView:
    def __init__(self, x, y, width, height, parent):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.parent = parent
        self.scale_x = 5.0
        self.scale_y = 5.0
        self.offset_x = width // 2
        self.offset_y = height // 2
        self.offset_adjust_x = 200  # Additional offset adjustment
        self.offset_adjust_y = 150  # Additional offset adjustment
        self.background = None
        self.load_background()
        
        # Create sliders for controlling the map view
        slider_width = 180
        self.scale_x_slider = Slider(x + 10, y + height - 110, slider_width, 15, 
                                     min_val=0.5, max_val=20.0, initial_val=self.scale_x,
                                     label="Scale X")
        self.scale_y_slider = Slider(x + 10, y + height - 80, slider_width, 15, 
                                     min_val=0.5, max_val=20.0, initial_val=self.scale_y,
                                     label="Scale Y")
        self.offset_x_slider = Slider(x + width - slider_width - 10, y + height - 110, 
                                     slider_width, 15, min_val=0, max_val=width,
                                     initial_val=self.offset_x, label="Offset X")
        self.offset_y_slider = Slider(x + width - slider_width - 10, y + height - 80, 
                                     slider_width, 15, min_val=0, max_val=height,
                                     initial_val=self.offset_y, label="Offset Y")
        
    def load_background(self):
        bg_path = "./images/scene.png"
        try:
            self.background = pygame.image.load(bg_path)
            orig_w, orig_h = self.background.get_size()
            scale = min(self.width / orig_w, self.height / orig_h) * 0.8  # Scale to 80% to leave room for controls
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            self.background = pygame.transform.scale(self.background, (new_w, new_h))
        except pygame.error:
            self.background = pygame.Surface((self.width, self.height))
            self.background.fill((20, 20, 20))
            font = pygame.font.SysFont('Arial', 16)
            text = font.render("Background image not found at ./images/scene.png", True, (200, 200, 200))
            self.background.blit(text, (10, self.height//2 - 8))
    
    def update_sliders(self, mouse_pos, mouse_pressed):
        # Update sliders and return if any slider was changed
        changed = False
        
        if self.scale_x_slider.update(mouse_pos, mouse_pressed):
            self.scale_x = self.scale_x_slider.value
            changed = True
            
        if self.scale_y_slider.update(mouse_pos, mouse_pressed):
            self.scale_y = self.scale_y_slider.value
            changed = True
            
        if self.offset_x_slider.update(mouse_pos, mouse_pressed):
            self.offset_x = self.offset_x_slider.value
            changed = True
            
        if self.offset_y_slider.update(mouse_pos, mouse_pressed):
            self.offset_y = self.offset_y_slider.value
            changed = True
            
        return changed
    
    def draw(self, surface):
        # Draw map background panel
        map_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (50, 50, 50), map_rect)
        pygame.draw.rect(surface, (100, 100, 100), map_rect, 1)
        
        # Draw map title
        title_font = pygame.font.SysFont('Arial', 18, bold=True)
        title_text = title_font.render("Scene Map View", True, (220, 220, 220))
        surface.blit(title_text, (self.x + 10, self.y + 5))
        
        # Draw background image
        bg_x = self.x + (self.width - self.background.get_width()) // 2
        bg_y = self.y + 30
        surface.blit(self.background, (bg_x, bg_y))
        
        # Draw car positions if scene data is available
        if self.parent.scene_data:
            car_colors = [(255, 0, 0), (0, 255, 0)]  # Red for Car A, Green for Car B
            
            for i, car_id in enumerate(["CarA", "CarB"]):
                location_key = f"{car_id}_Location"
                if location_key in self.parent.scene_data:
                    location = self.parent.scene_data[location_key]
                    dot_x = int(self.x + self.offset_x + location[0] * self.scale_x) + self.offset_adjust_x
                    dot_y = int(self.y + self.offset_y - location[1] * self.scale_y * 1.5) + self.offset_adjust_y
                    
                    car_color = car_colors[i]
                    
                    # Draw car position with a more prominent marker
                    pygame.draw.circle(surface, car_color, (dot_x, dot_y), 8)
                    pygame.draw.circle(surface, (255, 255, 255), (dot_x, dot_y), 9, 1)
                    
                    # Draw label with background for better visibility
                    font = pygame.font.SysFont('Arial', 14)
                    label = f"{car_id} ({location[0]:.1f}, {location[1]:.1f})"
                    text = font.render(label, True, (240, 240, 240))
                    text_bg = pygame.Rect(dot_x + 10, dot_y - 10, text.get_width() + 6, text.get_height() + 4)
                    pygame.draw.rect(surface, (40, 40, 40, 180), text_bg)
                    pygame.draw.rect(surface, car_color, text_bg, 1)
                    surface.blit(text, (dot_x + 13, dot_y - 8))
                    
                    # If we have rotation data, draw a direction indicator
                    rotation_key = f"{car_id}_Rotation"
                    if rotation_key in self.parent.scene_data:
                        angle = self.parent.scene_data[rotation_key]
                        rad_angle = np.radians(angle)
                        end_x = dot_x + int(20 * np.cos(rad_angle))
                        end_y = dot_y - int(20 * np.sin(rad_angle))
                        pygame.draw.line(surface, car_color, (dot_x, dot_y), (end_x, end_y), 3)
                        # Draw arrowhead
                        arrow_angle1 = rad_angle + np.radians(150)
                        arrow_angle2 = rad_angle - np.radians(150)
                        arrow_x1 = end_x + int(8 * np.cos(arrow_angle1))
                        arrow_y1 = end_y - int(8 * np.sin(arrow_angle1))
                        arrow_x2 = end_x + int(8 * np.cos(arrow_angle2))
                        arrow_y2 = end_y - int(8 * np.sin(arrow_angle2))
                        pygame.draw.polygon(surface, car_color, [(end_x, end_y), (arrow_x1, arrow_y1), (arrow_x2, arrow_y2)])
        
        # Draw data parameters
        font = pygame.font.SysFont('Arial', 14)
        param_text = font.render(f"Position Controls:", True, (220, 220, 220))
        surface.blit(param_text, (self.x + 10, self.y + self.height - 140))
        
        # Draw sliders
        self.scale_x_slider.draw(surface, font)
        self.scale_y_slider.draw(surface, font)
        self.offset_x_slider.draw(surface, font)
        self.offset_y_slider.draw(surface, font)
        
        # Draw center button
        center_button = pygame.Rect(self.x + (self.width // 2) - 40, self.y + self.height - 45, 80, 25)
        pygame.draw.rect(surface, (80, 80, 80), center_button)
        pygame.draw.rect(surface, (160, 160, 160), center_button, 1)
        center_text = font.render("Reset View", True, (220, 220, 220))
        text_rect = center_text.get_rect(center=center_button.center)
        surface.blit(center_text, text_rect)
        
        # Return interactive elements
        return [center_button]
    
    def handle_center_click(self):
        # Reset view to default values
        self.scale_x = 1.3
        self.scale_y = 3.14
        self.offset_x = 378
        self.offset_y = 107
        
        # Update slider values to match
        self.scale_x_slider.value = self.scale_x
        self.scale_y_slider.value = self.scale_y
        self.offset_x_slider.value = self.offset_x
        self.offset_y_slider.value = self.offset_y
    
    def handle_drag(self, rel_x, rel_y):
        # Update offset values based on drag
        self.offset_x += rel_x
        self.offset_y += rel_y
        
        # Update slider values to match
        self.offset_x_slider.value = self.offset_x
        self.offset_y_slider.value = self.offset_y

class SceneAnalyzer:
    def __init__(self):
        pygame.init()
        self.screen_width = 1400
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Multi-Vehicle Scene Analyzer")
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.status_font = pygame.font.SysFont('Arial', 16)
        self.bg_color = (30, 30, 30)
        self.panel_color = (50, 50, 50)
        self.text_color = (220, 220, 220)
        self.status_message = "Ready. Please select a scene file."
        
        self.current_scene = None
        self.scene_data = None
        
        self.car_a_image = None
        self.car_a_detection = None
        self.car_a_depth = None
        self.car_a_depth_map = None
        
        self.car_b_image = None
        self.car_b_detection = None
        self.car_b_depth = None
        self.car_b_depth_map = None
        
        self.detected_persons_a = []
        self.detected_persons_b = []
        self.confidence_threshold = 0.5
        
        self.load_models()
        self.scan_scene_files()
        self.setup_ui()
        self.running = True
        
        # Create map view with appropriate dimensions
        map_height = 350  # Increased height to accommodate sliders
        self.map_view = MapView(360, 10, self.screen_width - 380, map_height, self)
        self.map_buttons = []
        self.dragging_map = False
    
    def load_models(self):
        try:
            self.yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.has_yolo = True
        except Exception as e:
            self.has_yolo = False
            self.status_message = f"Failed to load YOLO: {e}"
        
        try:
            self.depth_model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            self.depth_model.to('cuda' if torch.cuda.is_available() else 'cpu')
            self.depth_model.eval()
            self.midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.transform = self.midas_transforms.small_transform
            self.has_depth = True
        except Exception as e:
            self.has_depth = False
            self.status_message = f"Failed to load depth model: {e}"
    
    def scan_scene_files(self):
        scene_path = "./data/input"
        self.scene_files = []
        try:
            self.scene_files = glob.glob(os.path.join(scene_path, "scene_*.json"))
            self.status_message = f"Found {len(self.scene_files)} scene files."
        except Exception as e:
            self.status_message = f"Error scanning scene files: {e}"
    
    def setup_ui(self):
        self.scene_list_button = Button(20, 10, 150, 30, "Scene Files")
        self.confidence_slider = Slider(20, self.screen_height - 180, 320, 20, 
                                      min_val=0.1, max_val=0.9, initial_val=0.5, 
                                      label="Confidence Threshold")
        self.scroll_y = 0
        self.max_scroll = 0
        self.scene_buttons = []
        self.create_scene_buttons()
    
    def create_scene_buttons(self):
        self.scene_buttons = []
        button_y = 50
        for scene_path in self.scene_files:
            scene_name = os.path.basename(scene_path)
            button = Button(40, button_y, 280, 30, scene_name)
            self.scene_buttons.append((button, scene_path))
            button_y += 35
        self.max_scroll = max(0, button_y - self.screen_height + 250)
    
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == MOUSEBUTTONDOWN:
                    # Handle scene buttons
                    for button, scene_path in self.scene_buttons:
                        adjusted_button = button.rect.copy()
                        adjusted_button.y -= self.scroll_y
                        if adjusted_button.collidepoint(mouse_pos):
                            self.process_scene(scene_path)
                            break
                    
                    # Handle map center button
                    for i, button_rect in enumerate(self.map_buttons):
                        if button_rect.collidepoint(mouse_pos):
                            self.map_view.handle_center_click()
                            break
                    
                    # Handle map dragging
                    map_area = pygame.Rect(
                        self.map_view.x, self.map_view.y + 30, 
                        self.map_view.width, self.map_view.height - 150
                    )
                    if map_area.collidepoint(mouse_pos):
                        self.dragging_map = True
                
                elif event.type == MOUSEBUTTONUP:
                    self.dragging_map = False
                
                elif event.type == MOUSEWHEEL:
                    self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 20))
                
                elif event.type == MOUSEMOTION and self.dragging_map:
                    self.map_view.handle_drag(event.rel[0], event.rel[1])
            
            # Update confidence slider
            slider_changed = self.confidence_slider.update(mouse_pos, mouse_pressed)
            if slider_changed and self.current_scene:
                self.confidence_threshold = self.confidence_slider.value
                if self.has_yolo:
                    self.process_scene(self.current_scene, reprocess=True)
            
            # Update map view sliders
            map_sliders_changed = self.map_view.update_sliders(mouse_pos, mouse_pressed)
            
            # Update UI hover states
            self.scene_list_button.check_hover(mouse_pos)
            for button, _ in self.scene_buttons:
                adjusted_button = button.rect.copy()
                adjusted_button.y -= self.scroll_y
                button.is_hovered = adjusted_button.collidepoint(mouse_pos)
            
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()
        sys.exit()
    
    def draw(self):
        self.screen.fill(self.bg_color)
        
        # Draw left panel with scene list
        left_panel = pygame.Rect(10, 10, 340, self.screen_height - 20)
        pygame.draw.rect(self.screen, self.panel_color, left_panel)
        self.scene_list_button.draw(self.screen, self.font)
        
        # Draw scrollable scene list
        scroll_rect = pygame.Rect(20, 50, 320, self.screen_height - 230)
        self.screen.set_clip(scroll_rect)
        for button, _ in self.scene_buttons:
            adjusted_button = button.rect.copy()
            adjusted_button.y -= self.scroll_y
            if scroll_rect.colliderect(adjusted_button):
                pygame.draw.rect(self.screen, button.hover_color if button.is_hovered else button.color, adjusted_button)
                pygame.draw.rect(self.screen, (200, 200, 200), adjusted_button, 2)
                text_surf = self.font.render(button.text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=adjusted_button.center)
                self.screen.blit(text_surf, text_rect)
        self.screen.set_clip(None)
        
        # Draw scroll indicators if needed
        if self.max_scroll > 0:
            if self.scroll_y > 0:
                pygame.draw.polygon(self.screen, (200, 200, 200), 
                                  [(320, 55), (330, 65), (310, 65)])
            if self.scroll_y < self.max_scroll:
                pygame.draw.polygon(self.screen, (200, 200, 200), 
                                  [(320, self.screen_height - 245), (330, self.screen_height - 255), (310, self.screen_height - 255)])
        
        # Draw confidence slider
        self.confidence_slider.draw(self.screen, self.font)
        
        # Draw JSON data panel
        json_panel = pygame.Rect(10, self.screen_height - 140, 340, 100)
        pygame.draw.rect(self.screen, self.panel_color, json_panel)
        pygame.draw.rect(self.screen, (200, 200, 200), json_panel, 2)
        json_title = self.title_font.render("Scene Data", True, self.text_color)
        self.screen.blit(json_title, (json_panel.x + 10, json_panel.y + 5))
        
        # Display scene data if available
        y_offset = json_panel.y + 30
        if self.scene_data:
            try:
                keys_to_show = ['CarA_Location', 'CarA_Rotation', 'CarB_Location', 'CarB_Rotation']
                for key in keys_to_show:
                    if key in self.scene_data:
                        value = str(self.scene_data[key])
                        if len(value) > 30:
                            value = value[:27] + "..."
                        json_text = self.font.render(f"{key}: {value}", True, self.text_color)
                        self.screen.blit(json_text, (json_panel.x + 10, y_offset))
                        y_offset += 18
            except Exception as e:
                error_text = self.font.render(f"Error displaying JSON: {str(e)[:30]}", True, (255, 100, 100))
                self.screen.blit(error_text, (json_panel.x + 10, y_offset))
        else:
            no_data_text = self.font.render("No scene data loaded", True, self.text_color)
            self.screen.blit(no_data_text, (json_panel.x + 10, y_offset))
        
        # Draw map view with interactive elements
        self.map_buttons = self.map_view.draw(self.screen)
        
        # Calculate panel positions based on map height
        map_height = self.map_view.height
        panel_y = 20 + map_height
        panel_height = (self.screen_height - panel_y - 40) // 2
        
        # Draw camera panels - first row (Car A)
        car_a_orig_panel = pygame.Rect(360, panel_y, (self.screen_width - 380) // 3, panel_height)
        pygame.draw.rect(self.screen, self.panel_color, car_a_orig_panel)
        self.draw_panel_title(car_a_orig_panel, "Car A Original")
        
        car_a_yolo_panel = pygame.Rect(370 + (self.screen_width - 380) // 3, panel_y, 
                                     (self.screen_width - 380) // 3, panel_height)
        pygame.draw.rect(self.screen, self.panel_color, car_a_yolo_panel)
        self.draw_panel_title(car_a_yolo_panel, "Car A Detection")
        
        car_a_depth_panel = pygame.Rect(380 + 2 * (self.screen_width - 380) // 3, panel_y, 
                                      (self.screen_width - 380) // 3, panel_height)
        pygame.draw.rect(self.screen, self.panel_color, car_a_depth_panel)
        self.draw_panel_title(car_a_depth_panel, "Car A Depth Map")
        
        # Draw camera panels - second row (Car B)
        car_b_orig_panel = pygame.Rect(360, panel_y + panel_height + 10, 
                                     (self.screen_width - 380) // 3, panel_height)
        pygame.draw.rect(self.screen, self.panel_color, car_b_orig_panel)
        self.draw_panel_title(car_b_orig_panel, "Car B Original")
        
        car_b_yolo_panel = pygame.Rect(370 + (self.screen_width - 380) // 3, panel_y + panel_height + 10, 
                                     (self.screen_width - 380) // 3, panel_height)
        pygame.draw.rect(self.screen, self.panel_color, car_b_yolo_panel)
        self.draw_panel_title(car_b_yolo_panel, "Car B Detection")
        
        car_b_depth_panel = pygame.Rect(380 + 2 * (self.screen_width - 380) // 3, panel_y + panel_height + 10, 
                                      (self.screen_width - 380) // 3, panel_height)
        pygame.draw.rect(self.screen, self.panel_color, car_b_depth_panel)
        self.draw_panel_title(car_b_depth_panel, "Car B Depth Map")
        
        # Draw images if available
        if self.car_a_image is not None:
            self.draw_image_in_panel(self.car_a_image, car_a_orig_panel)
        if self.car_a_detection is not None:
            self.draw_image_in_panel(self.car_a_detection, car_a_yolo_panel)
        if self.car_a_depth is not None:
            self.draw_image_in_panel(self.car_a_depth, car_a_depth_panel)
            
        if self.car_b_image is not None:
            self.draw_image_in_panel(self.car_b_image, car_b_orig_panel)
        if self.car_b_detection is not None:
            self.draw_image_in_panel(self.car_b_detection, car_b_yolo_panel)
        if self.car_b_depth is not None:
            self.draw_image_in_panel(self.car_b_depth, car_b_depth_panel)
        
        # Draw detection count information
        a_person_count = len(self.detected_persons_a) if hasattr(self, 'detected_persons_a') else 0
        b_person_count = len(self.detected_persons_b) if hasattr(self, 'detected_persons_b') else 0
        
        if a_person_count > 0:
            person_info_a = f"Car A: {a_person_count} pedestrians detected"
            info_text_a = self.font.render(person_info_a, True, (220, 220, 220))
            self.screen.blit(info_text_a, (car_a_yolo_panel.x + 10, car_a_yolo_panel.y + car_a_yolo_panel.height - 25))
        
        if b_person_count > 0:
            person_info_b = f"Car B: {b_person_count} pedestrians detected"
            info_text_b = self.font.render(person_info_b, True, (220, 220, 220))
            self.screen.blit(info_text_b, (car_b_yolo_panel.x + 10, car_b_yolo_panel.y + car_b_yolo_panel.height - 25))
        
        # Draw status bar
        status_rect = pygame.Rect(10, self.screen_height - 30, self.screen_width - 20, 20)
        pygame.draw.rect(self.screen, (60, 60, 60), status_rect)
        status_text = self.status_font.render(self.status_message, True, self.text_color)
        self.screen.blit(status_text, (status_rect.x + 10, status_rect.y + 2))
    
    def draw_panel_title(self, panel, title):
        title_text = self.title_font.render(title, True, self.text_color)
        self.screen.blit(title_text, (panel.x + 10, panel.y + 5))
    
    def draw_image_in_panel(self, image, panel):
        content_rect = pygame.Rect(panel.x + 5, panel.y + 30, panel.width - 10, panel.height - 35)
        img_w, img_h = image.get_size()
        scale = min(content_rect.width / img_w, content_rect.height / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        scaled_img = pygame.transform.scale(image, (new_w, new_h))
        img_x = content_rect.x + (content_rect.width - new_w) // 2
        img_y = content_rect.y + (content_rect.height - new_h) // 2
        self.screen.blit(scaled_img, (img_x, img_y))
    
    def process_scene(self, scene_path, reprocess=False):
        try:
            self.status_message = f"Processing scene {os.path.basename(scene_path)}..."
            self.current_scene = scene_path
            
            if not reprocess:
                with open(scene_path, 'r') as f:
                    self.scene_data = json.load(f)
                
                base_data_dir = "./data"
                car_a_camera_path = os.path.join(base_data_dir, self.scene_data.get("CarA_Camera", ""))
                car_b_camera_path = os.path.join(base_data_dir, self.scene_data.get("CarB_Camera", ""))
                
                if os.path.exists(car_a_camera_path):
                    img_a = cv2.imread(car_a_camera_path)
                    img_a_rgb = cv2.cvtColor(img_a, cv2.COLOR_BGR2RGB)
                    self.car_a_image = self.numpy_to_pygame(img_a_rgb)
                    
                    if self.has_depth:
                        self.generate_depth_map_a(img_a_rgb.copy())
                else:
                    self.status_message = f"Error: Car A camera image not found at {car_a_camera_path}"
                    return
                
                if os.path.exists(car_b_camera_path):
                    img_b = cv2.imread(car_b_camera_path)
                    img_b_rgb = cv2.cvtColor(img_b, cv2.COLOR_BGR2RGB)
                    self.car_b_image = self.numpy_to_pygame(img_b_rgb)
                    
                    if self.has_depth:
                        self.generate_depth_map_b(img_b_rgb.copy())
                else:
                    self.status_message = f"Error: Car B camera image not found at {car_b_camera_path}"
                    return
            
            if self.has_yolo:
                if self.car_a_image is not None and self.car_a_depth_map is not None:
                    img_a = cv2.imread(os.path.join("./data", self.scene_data.get("CarA_Camera", "")))
                    img_a_rgb = cv2.cvtColor(img_a, cv2.COLOR_BGR2RGB)
                    self.run_yolo_detection_a(img_a_rgb.copy())
                
                if self.car_b_image is not None and self.car_b_depth_map is not None:
                    img_b = cv2.imread(os.path.join("./data", self.scene_data.get("CarB_Camera", "")))
                    img_b_rgb = cv2.cvtColor(img_b, cv2.COLOR_BGR2RGB)
                    self.run_yolo_detection_b(img_b_rgb.copy())
            
            self.status_message = f"Processed scene {os.path.basename(scene_path)}"
            
        except Exception as e:
            self.status_message = f"Error processing scene: {e}"
    
    def generate_depth_map_a(self, img):
        input_batch = self.transform(img).to('cuda' if torch.cuda.is_available() else 'cpu')
        with torch.no_grad():
            prediction = self.depth_model(input_batch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        
        self.car_a_depth_map = prediction.cpu().numpy()
        normalized_depth = (self.car_a_depth_map - self.car_a_depth_map.min()) / (self.car_a_depth_map.max() - self.car_a_depth_map.min())
        depth_colored = cv2.applyColorMap((normalized_depth * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        self.car_a_depth = self.numpy_to_pygame(depth_colored)
    
    def generate_depth_map_b(self, img):
        input_batch = self.transform(img).to('cuda' if torch.cuda.is_available() else 'cpu')
        with torch.no_grad():
            prediction = self.depth_model(input_batch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        
        self.car_b_depth_map = prediction.cpu().numpy()
        normalized_depth = (self.car_b_depth_map - self.car_b_depth_map.min()) / (self.car_b_depth_map.max() - self.car_b_depth_map.min())
        depth_colored = cv2.applyColorMap((normalized_depth * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        self.car_b_depth = self.numpy_to_pygame(depth_colored)
    
    def run_yolo_detection_a(self, img):
        results = self.yolo_model(img)
        persons = results.pandas().xyxy[0]
        persons = persons[persons['class'] == 0]
        
        filtered_persons = persons[persons['confidence'] >= self.confidence_threshold]
        self.detected_persons_a = []
        
        for idx, row in filtered_persons.iterrows():
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            conf = row['confidence']
            
            distance_str = "N/A"
            distance_val = None
            
            if self.has_depth and self.car_a_depth_map is not None:
                try:
                    roi = self.car_a_depth_map[y1:y2, x1:x2]
                    if roi.size > 0:
                        avg_depth = np.mean(roi)
                        depth_scale = 0.05
                        distance_val = avg_depth * depth_scale
                        distance_str = f"{distance_val:.2f}m"
                except Exception:
                    distance_str = "Error"
            
            self.detected_persons_a.append({
                'id': idx,
                'bbox': (x1, y1, x2, y2),
                'conf': conf,
                'distance': distance_str,
                'distance_val': distance_val
            })
            
            box_color = (0, 255, 0)
            if distance_val is not None:
                if distance_val < 1.5:
                    box_color = (0, 0, 255)
                elif distance_val < 2.5:
                    box_color = (0, 165, 255)
                else:
                    box_color = (0, 255, 0)
            
            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 2)
            
            label = f"{len(self.detected_persons_a)}"
            cv2.putText(img, label, (x1+5, y1+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
        
        self.car_a_detection = self.numpy_to_pygame(img)
        num_persons = len(self.detected_persons_a)
        self.status_message = f"Detected {num_persons} persons in Car A (threshold: {self.confidence_threshold:.2f})"
    
    def run_yolo_detection_b(self, img):
        results = self.yolo_model(img)
        persons = results.pandas().xyxy[0]
        persons = persons[persons['class'] == 0]
        
        filtered_persons = persons[persons['confidence'] >= self.confidence_threshold]
        self.detected_persons_b = []
        
        for idx, row in filtered_persons.iterrows():
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            conf = row['confidence']
            
            distance_str = "N/A"
            distance_val = None
            
            if self.has_depth and self.car_b_depth_map is not None:
                try:
                    roi = self.car_b_depth_map[y1:y2, x1:x2]
                    if roi.size > 0:
                        avg_depth = np.mean(roi)
                        depth_scale = 0.05
                        distance_val = avg_depth * depth_scale
                        distance_str = f"{distance_val:.2f}m"
                except Exception:
                    distance_str = "Error"
            
            self.detected_persons_b.append({
                'id': idx,
                'bbox': (x1, y1, x2, y2),
                'conf': conf,
                'distance': distance_str,
                'distance_val': distance_val
            })
            
            box_color = (0, 255, 0)
            if distance_val is not None:
                if distance_val < 1.5:
                    box_color = (0, 0, 255)
                elif distance_val < 2.5:
                    box_color = (0, 165, 255)
                else:
                    box_color = (0, 255, 0)
            
            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 2)
            label = f"{len(self.detected_persons_b)}"
            cv2.putText(img, label, (x1+5, y1+20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
        
        self.car_b_detection = self.numpy_to_pygame(img)
        total_persons = len(self.detected_persons_a) + len(self.detected_persons_b)
        self.status_message = f"Total: {total_persons} persons detected across both cameras (threshold: {self.confidence_threshold:.2f})"
    
    def numpy_to_pygame(self, img_array):
        img_array = np.flip(img_array, axis=2)
        img_surface = pygame.surfarray.make_surface(np.transpose(img_array, (1, 0, 2)))
        return img_surface

if __name__ == "__main__":
    app = SceneAnalyzer()
    app.run()