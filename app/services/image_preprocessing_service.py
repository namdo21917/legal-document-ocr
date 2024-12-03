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


class ImagePreprocessor:
    def __init__(self, config):
        self.logger = Logger(__name__).logger
        self.config = config['preprocessing']
        self.logger.debug("Khởi tạo ImagePreprocessor với cấu hình: " +
                          str(self.config))
        # Chỉ định đường dẫn Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'E:\OCR_Resources\Tessaract_OCR\tesseract.exe'
        self.logger.debug("Khởi tạo Tesseract thành công")

    def create_pdf_from_text(self, input_path, output_pdf_path=None):
        """
        Tạo file PDF từ file text
        Args:
            input_path: Đường dẫn file đầu vào
            output_pdf_path: Đường dẫn file PDF đầu ra (tùy chọn)
        Returns:
            str: Đường dẫn đến file PDF đã tạo
        """
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
        """
        Chuyển đổi tất cả các trang PDF sang ảnh
        Args:
            pdf_path: Đường dẫn đến file PDF
        Returns:
            list: Danh sách các ảnh từ các trang PDF
        """
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
            poppler_path = r"E:\OCR_Resources\poppler\poppler-24.08.0\Library\bin"
            images = convert_from_path(
                pdf_path,
                poppler_path=poppler_path
            )

            if images:
                self.logger.info(f"Chuyển đổi thành công {len(images)} trang PDF")
                return images
            else:
                self.logger.error(f"Không thể chuyển đổi PDF: {pdf_path}")
                return None

        except Exception as e:
            self.logger.error(f"Lỗi chuyển đổi PDF: {str(e)}")
            return None

    # def _evaluate_rotation(self, image, angle):
    #     """
    #     Đánh giá chất lượng xoay ảnh bằng OCR
    #     """
    #     try:
    #         if not isinstance(image, Image.Image):
    #             image = Image.fromarray(image)
    #
    #         data = pytesseract.image_to_data(image, lang='vie', output_type=pytesseract.Output.DICT)
    #         confidence = float(sum(int(x) for x in data['conf'] if x != '-1')) / len(data['conf'])
    #         self.logger.debug(f"Độ tin cậy OCR tại góc {angle:.2f}: {confidence}%")
    #         return confidence
    #     except Exception as e:
    #         self.logger.error(f"Lỗi đánh giá xoay: {str(e)}")
    #         return 0

    def preprocess(self, image):
        """
        Tiền xử lý ảnh để cải thiện kết quả OCR
        Args:
            image: Ảnh đầu vào (PIL Image hoặc numpy array)
        Returns:
            numpy.ndarray: Ảnh nhị phân đã xử lý
        """
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
