import cv2
import numpy as np
from PIL import Image, ImageDraw

class RegionSegmenter:
    def __init__(self, config):
        self.config = config['segmentation']
    
    def find_text_regions(self, binary_image):
        """
        Tìm các vùng văn bản trong ảnh nhị phân sử dụng phát hiện contour
        Args:
            binary_image: Ảnh nhị phân đầu vào
        Returns:
            list: Danh sách các vùng văn bản (x, y, w, h)
        """
        # Tìm contour
        contours, _ = cv2.findContours(
            binary_image,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Lọc và sắp xếp các vùng văn bản
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / float(h)
            
            # Lọc dựa trên diện tích và tỷ lệ khung
            if (area >= self.config['min_contour_area'] and
                self.config['min_aspect_ratio'] <= aspect_ratio <= self.config['max_aspect_ratio']):
                text_regions.append((x, y, w, h))
        
        # Sắp xếp các vùng từ trên xuống dưới
        text_regions.sort(key=lambda r: r[1])
        
        return text_regions
    
    def draw_regions(self, image, regions):
        """
        Draw bounding boxes around detected text regions
        """
        # Convert to PIL Image if necessary
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Create a copy for drawing
        draw_image = image.copy()
        draw = ImageDraw.Draw(draw_image)
        
        # Draw rectangles around text regions
        for x, y, w, h in regions:
            draw.rectangle(
                [(x, y), (x + w, y + h)],
                outline='red',
                width=2
            )
        
        return draw_image
    
    def extract_regions(self, image, regions):
        """
        Extract individual region images from the original image
        """
        # Convert to PIL Image if necessary
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        region_images = []
        for x, y, w, h in regions:
            region = image.crop((x, y, x + w, y + h))
            region_images.append(region)
        
        return region_images 