import cv2
import numpy as np

class TableDetector:
    def __init__(self, config):
        self.min_line_length = config['table_detection']['min_line_length']
        self.line_thickness = config['table_detection']['line_thickness']
        self.min_cell_area = config['table_detection']['min_cell_area']

    def detect_tables(self, image):
        """Phát hiện bảng trong ảnh"""
        # Phát hiện đường kẻ ngang và dọc
        horizontal_lines = self._detect_horizontal_lines(image)
        vertical_lines = self._detect_vertical_lines(image)
        
        # Tìm giao điểm của các đường
        intersections = cv2.bitwise_and(horizontal_lines, vertical_lines)
        
        # Phát hiện ô trong bảng
        cells = self._detect_cells(intersections)
        
        return cells

    def extract_table_content(self, image, cells):
        """Trích xuất nội dung từ các ô trong bảng"""
        table_data = []
        for cell in cells:
            x, y, w, h = cell
            cell_image = image[y:y+h, x:x+w]
            # OCR cho từng ô
            cell_content = self._ocr_cell(cell_image)
            table_data.append(cell_content)
        return table_data 