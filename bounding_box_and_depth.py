import os
import sys
import numpy as np
import cv2
import pygame
import torch
from pygame.locals import *
import glob
import time

class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), hover_color=(150, 150, 150)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, surface, font):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
    
    def check_click(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click

class ImageAnalyzerApp:
    def __init__(self):
        pygame.init()
        self.screen_width = 1400
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Image Analyzer - YOLO Detection & Depth Mapping")
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.status_font = pygame.font.SysFont('Arial', 16)
        self.bg_color = (30, 30, 30)
        self.panel_color = (50, 50, 50)
        self.text_color = (220, 220, 220)
        self.status_message = "Ready. Please select an image."
        self.current_image = None
        self.detection_image = None
        self.depth_image = None
        self.current_image_path = None
        self.load_models()
        self.scan_image_folders()
        self.setup_ui()
        self.running = True
    
    def load_models(self):
        try:
            self.yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.has_yolo = True
        except Exception as e:
            self.has_yolo = False
        try:
            self.depth_model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            self.depth_model.to('cuda' if torch.cuda.is_available() else 'cpu')
            self.depth_model.eval()
            self.midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.transform = self.midas_transforms.small_transform
            self.has_depth = True
        except Exception as e:
            self.has_depth = False
    
    def scan_image_folders(self):
        camera_a_path = "./data/CameraA"
        camera_b_path = "./data/CameraB"
        self.camera_a_images = []
        self.camera_b_images = []
        try:
            self.camera_a_images = glob.glob(os.path.join(camera_a_path, "*.png"))
            self.camera_a_images.extend(glob.glob(os.path.join(camera_a_path, "*.jpg")))
            self.camera_b_images = glob.glob(os.path.join(camera_b_path, "*.png"))
            self.camera_b_images.extend(glob.glob(os.path.join(camera_b_path, "*.jpg")))
            self.status_message = f"Found {len(self.camera_a_images)} images in Camera A and {len(self.camera_b_images)} images in Camera B."
        except Exception as e:
            self.status_message = f"Error scanning image folders: {e}"
    
    def setup_ui(self):
        self.tab_a_button = Button(20, 10, 150, 30, "Camera A")
        self.tab_b_button = Button(180, 10, 150, 30, "Camera B")
        self.active_tab = "A"
        self.scroll_y = 0
        self.max_scroll = 0
        self.image_buttons = []
        self.create_image_buttons()
    
    def create_image_buttons(self):
        self.image_buttons = []
        images = self.camera_a_images if self.active_tab == "A" else self.camera_b_images
        button_y = 50
        for img_path in images:
            img_name = os.path.basename(img_path)
            button = Button(40, button_y, 280, 30, img_name)
            self.image_buttons.append((button, img_path))
            button_y += 35
        self.max_scroll = max(0, button_y - self.screen_height + 50)
    
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                if event.type == MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.tab_a_button.check_click(mouse_pos, True):
                        self.active_tab = "A"
                        self.scroll_y = 0
                        self.create_image_buttons()
                    elif self.tab_b_button.check_click(mouse_pos, True):
                        self.active_tab = "B"
                        self.scroll_y = 0
                        self.create_image_buttons()
                    for button, img_path in self.image_buttons:
                        adjusted_button = button.rect.copy()
                        adjusted_button.y -= self.scroll_y
                        if adjusted_button.collidepoint(mouse_pos):
                            self.process_image(img_path)
                            break
                if event.type == MOUSEWHEEL:
                    self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 20))
            mouse_pos = pygame.mouse.get_pos()
            self.tab_a_button.check_hover(mouse_pos)
            self.tab_b_button.check_hover(mouse_pos)
            for button, _ in self.image_buttons:
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
        left_panel = pygame.Rect(10, 10, 340, self.screen_height - 20)
        pygame.draw.rect(self.screen, self.panel_color, left_panel)
        self.tab_a_button.draw(self.screen, self.font)
        self.tab_b_button.draw(self.screen, self.font)
        scroll_rect = pygame.Rect(20, 50, 320, self.screen_height - 70)
        self.screen.set_clip(scroll_rect)
        for button, _ in self.image_buttons:
            adjusted_button = button.rect.copy()
            adjusted_button.y -= self.scroll_y
            if scroll_rect.colliderect(adjusted_button):
                pygame.draw.rect(self.screen, button.hover_color if button.is_hovered else button.color, adjusted_button)
                pygame.draw.rect(self.screen, (200, 200, 200), adjusted_button, 2)
                text_surf = self.font.render(button.text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=adjusted_button.center)
                self.screen.blit(text_surf, text_rect)
        self.screen.set_clip(None)
        if self.max_scroll > 0:
            if self.scroll_y > 0:
                pygame.draw.polygon(self.screen, (200, 200, 200), 
                                    [(320, 55), (330, 65), (310, 65)])
            if self.scroll_y < self.max_scroll:
                pygame.draw.polygon(self.screen, (200, 200, 200), 
                                    [(320, self.screen_height - 35), (330, self.screen_height - 45), (310, self.screen_height - 45)])
        orig_panel = pygame.Rect(360, 10, (self.screen_width - 380) // 2, (self.screen_height - 30) // 2)
        pygame.draw.rect(self.screen, self.panel_color, orig_panel)
        self.draw_panel_title(orig_panel, "Original Image")
        yolo_panel = pygame.Rect(370 + (self.screen_width - 380) // 2, 10, 
                                 (self.screen_width - 380) // 2, (self.screen_height - 30) // 2)
        pygame.draw.rect(self.screen, self.panel_color, yolo_panel)
        self.draw_panel_title(yolo_panel, "Person Detection (YOLO)")
        depth_panel = pygame.Rect(360, 20 + (self.screen_height - 30) // 2, 
                                  self.screen_width - 380, (self.screen_height - 30) // 2)
        pygame.draw.rect(self.screen, self.panel_color, depth_panel)
        self.draw_panel_title(depth_panel, "Depth Map")
        if self.current_image is not None:
            self.draw_image_in_panel(self.current_image, orig_panel)
        if self.detection_image is not None:
            self.draw_image_in_panel(self.detection_image, yolo_panel)
        if self.depth_image is not None:
            self.draw_image_in_panel(self.depth_image, depth_panel)
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
    
    def process_image(self, img_path):
        try:
            self.status_message = f"Processing {os.path.basename(img_path)}..."
            self.current_image_path = img_path
            img = cv2.imread(img_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.current_image = self.numpy_to_pygame(img_rgb)
            if self.has_yolo:
                self.run_yolo_detection(img_rgb.copy())
            if self.has_depth:
                self.generate_depth_map(img_rgb.copy())
            self.status_message = f"Processed {os.path.basename(img_path)}"
        except Exception as e:
            self.status_message = f"Error processing image: {e}"
    
    def numpy_to_pygame(self, img_array):
        img_array = np.flip(img_array, axis=2)
        img_surface = pygame.surfarray.make_surface(np.transpose(img_array, (1, 0, 2)))
        return img_surface
    
    def run_yolo_detection(self, img):
        results = self.yolo_model(img)
        persons = results.pandas().xyxy[0]
        persons = persons[persons['class'] == 0]
        for idx, row in persons.iterrows():
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            conf = row['confidence']
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"Person: {conf:.2f}"
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        self.detection_image = self.numpy_to_pygame(img)
        num_persons = len(persons)
        self.status_message = f"Detected {num_persons} persons in {os.path.basename(self.current_image_path)}"
    
    def generate_depth_map(self, img):
        input_batch = self.transform(img).to('cuda' if torch.cuda.is_available() else 'cpu')
        with torch.no_grad():
            prediction = self.depth_model(input_batch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        depth_map = prediction.cpu().numpy()
        depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
        depth_colored = cv2.applyColorMap((depth_map * 255).astype(np.uint8), cv2.COLORMAP_PLASMA)
        self.depth_image = self.numpy_to_pygame(depth_colored)

if __name__ == "__main__":
    app = ImageAnalyzerApp()
    app.run()
