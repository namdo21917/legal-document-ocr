import cv2
import numpy as np
from PIL import Image
import math
import pytesseract
from pdf2image import convert_from_path
import os
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.utils.logger import Logger
from app.core.config import settings


class ImagePreprocessor:
    def __init__(self, config):
        self.logger = Logger(__name__).logger
        self.config = config['preprocessing']
        self.logger.debug("Khởi tạo ImagePreprocessor với cấu hình: " +
                          str(self.config))
        # Sử dụng đường dẫn từ cấu hình
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        self.logger.debug("Khởi tạo Tesseract thành công")

    def create_pdf_from_text(self, input_path, output_pdf_path=None):
        try:
            if output_pdf_path is None:
                output_pdf_path = os.path.splitext(input_path)[0] + "_converted.pdf"

            # Đọc nội dung file
            with open(input_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Tạo PDF
            c = canvas.Canvas(output_pdf_path, pagesize=letter)
            # Thiết lập font và cỡ chữ
            c.setFont("Helvetica", 12)

            # Viết nội dung vào PDF
            y = 750  # Vị trí bắt đầu từ trên xuống
            for line in content.split('\n'):
                if y < 50:  # Nếu hết trang
                    c.showPage()
                    y = 750
                c.drawString(50, y, line)
                y -= 15  # Khoảng cách giữa các dòng

            c.save()
            self.logger.info(f"Đã tạo file PDF: {output_pdf_path}")
            return output_pdf_path

        except Exception as e:
            self.logger.error(f"Lỗi tạo PDF: {str(e)}")
            return None

    def convert_from_pdf(self, pdf_path):
        try:
            self.logger.debug(f"Bắt đầu chuyển đổi PDF: {pdf_path}")

            # Kiểm tra file có tồn tại
            if not os.path.exists(pdf_path):
                self.logger.error(f"File không tồn tại: {pdf_path}")
                return None

            # Thử tạo PDF nếu file gốc không phải PDF hợp lệ
            try:
                pdf = PdfReader(pdf_path)
                num_pages = len(pdf.pages)
                if num_pages == 0:
                    raise Exception("PDF không có trang nào")
                self.logger.info(f"PDF có {num_pages} trang")
            except Exception as e:
                self.logger.warning(f"File không phải PDF hợp lệ, thử chuyển đổi: {str(e)}")
                converted_pdf = self.create_pdf_from_text(pdf_path)
                if converted_pdf:
                    pdf_path = converted_pdf
                else:
                    return None

            # Chuyển đổi tất cả các trang PDF sang ảnh
            # Thử nhiều cách để tìm poppler
            poppler_paths_to_try = [
                None,  # Để pdf2image tự tìm
                settings.POPPLER_PATH,
                '/usr/bin',
                '/usr/local/bin',
            ]

            images = None
            last_error = None

            for poppler_path in poppler_paths_to_try:
                try:
                    self.logger.debug(f"Thử poppler_path: {poppler_path}")
                    if poppler_path:
                        images = convert_from_path(pdf_path, poppler_path=poppler_path)
                    else:
                        images = convert_from_path(pdf_path)

                    if images:
                        self.logger.info(f"Thành công với poppler_path: {poppler_path}")
                        break

                except Exception as e:
                    last_error = str(e)
                    self.logger.debug(f"Thất bại với poppler_path {poppler_path}: {str(e)}")
                    continue

            if not images and last_error:
                raise Exception(f"Không thể chuyển đổi PDF với tất cả poppler paths. Lỗi cuối: {last_error}")

            if images:
                self.logger.info(f"Chuyển đổi thành công {len(images)} trang PDF")
                return images
            else:
                self.logger.error(f"Không thể chuyển đổi PDF: {pdf_path}")
                return None

        except Exception as e:
            self.logger.error(f"Lỗi chuyển đổi PDF: {str(e)}")
            return None

    def preprocess(self, image):
        try:
            self.logger.debug("Bắt đầu tiền xử lý ảnh")

            # Chuyển đổi sang OpenCV format nếu cần
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Chuyển sang ảnh xám
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Áp dụng CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(
                clipLimit=self.config['clahe_clip_limit'],
                tileGridSize=(self.config['clahe_grid_size'], self.config['clahe_grid_size'])
            )
            clahe_img = clahe.apply(gray)

            # Áp dụng Gaussian Blur
            blurred = cv2.GaussianBlur(
                clahe_img,
                tuple(self.config['gaussian_kernel_size']),
                self.config['gaussian_sigma']
            )

            # Áp dụng Morphological Closing
            kernel = np.ones(tuple(self.config['morph_kernel_size']), np.uint8)
            closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

            # Áp dụng Adaptive Thresholding
            binary = cv2.adaptiveThreshold(
                closed,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.config['adaptive_block_size'],
                self.config['adaptive_c']
            )

            self.logger.debug("Hoàn thành tiền xử lý ảnh")
            return binary

        except Exception as e:
            self.logger.error(f"Lỗi tiền xử lý ảnh: {str(e)}")
            raise
