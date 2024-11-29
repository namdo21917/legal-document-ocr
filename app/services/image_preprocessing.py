import cv2
import numpy as np
from pdf2image import convert_from_path

class ImagePreprocessor:
    def __init__(self):
        self.config = self._load_config()

    def preprocess(self, image):
        """Tiền xử lý ảnh"""
        # Chuyển sang grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Khử nhiễu
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Tăng độ tương phản
        enhanced = cv2.equalizeHist(denoised)
        
        # Phát hiện và xoay ảnh tự động
        angle = self._detect_orientation(enhanced)
        if angle != 0:
            enhanced = self._rotate_image(enhanced, angle)
            
        return enhanced

    def pdf_to_images(self, pdf_path):
        """Chuyển PDF thành list các ảnh"""
        return convert_from_path(pdf_path)

    def _detect_orientation(self, image):
        # TODO: Implement orientation detection
        pass

    def _rotate_image(self, image, angle):
        # TODO: Implement image rotation
        pass 