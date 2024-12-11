import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

import pytesseract
from PIL import Image

from app.utils.cache_manager import CacheManager
from app.utils.logger import Logger
from app.core.config import settings


class OCRModule:
    def __init__(self):
        self.logger = Logger(__name__).logger
        try:
            # Sử dụng đường dẫn từ cấu hình
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            self.logger.info("Khởi tạo Tesseract thành công")

            # Khởi tạo cache manager
            self.cache = CacheManager()
            self.logger.info("Khởi tạo Cache Manager thành công")

            # Số luồng xử lý tối đa
            self.max_workers = multiprocessing.cpu_count()
            self.logger.debug(f"Số luồng xử lý tối đa: {self.max_workers}")
        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo OCR Module: {str(e)}")
            raise

    def recognize_regions(self, region_images):
        """
        Thực hiện OCR trên nhiều vùng ảnh song song
        Args:
            region_images: List các ảnh vùng cần nhận dạng
        Returns:
            list: Danh sách kết quả OCR cho từng vùng
        """
        self.logger.info(f"Bắt đầu nhận dạng {len(region_images)} vùng văn bản")
        results = []

        try:
            # Xử lý song song với ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit các công việc
                future_to_image = {
                    executor.submit(self._process_single_region, image): i
                    for i, image in enumerate(region_images)
                }

                # Thu thập kết quả theo thứ tự hoàn thành
                completed_results = [None] * len(region_images)
                for future in as_completed(future_to_image):
                    index = future_to_image[future]
                    try:
                        result = future.result()
                        completed_results[index] = result
                        self.logger.debug(f"Hoàn thành OCR vùng {index} với độ tin cậy {result['confidence']}%")
                    except Exception as e:
                        self.logger.error(f"Lỗi xử lý vùng {index}: {str(e)}")
                        completed_results[index] = {
                            'text': '',
                            'confidence': 0
                        }

                results = completed_results

        except Exception as e:
            self.logger.error(f"Lỗi xử lý song song: {str(e)}")
            # Fallback về xử lý tuần tự nếu có lỗi
            self.logger.info("Chuyển sang xử lý tuần tự")
            results = [self._process_single_region(image) for image in region_images]

        self.logger.info(f"Hoàn thành nhận dạng {len(results)} vùng văn bản")
        return results

    def _process_single_region(self, image):
        """
        Xử lý OCR cho một vùng ảnh
        Args:
            image: Ảnh cần nhận dạng (PIL Image)
        Returns:
            dict: Kết quả OCR bao gồm text và confidence
        """
        try:
            # Kiểm tra cache trước
            cache_key = self.cache.generate_key(image)
            if cache_key:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    self.logger.debug(f"Sử dụng kết quả từ cache: {cache_key}")
                    return cached_result

            # Nếu không có trong cache, thực hiện OCR
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)

            # Thực hiện OCR với Tesseract
            text = pytesseract.image_to_string(image, lang='vie')
            data = pytesseract.image_to_data(image, lang='vie', output_type=pytesseract.Output.DICT)

            # Tính toán độ tin cậy trung bình
            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
            confidence = sum(confidences) / len(confidences) if confidences else 0

            result = {
                'text': text.strip(),
                'confidence': confidence
            }

            # Lưu kết quả vào cache
            if cache_key:
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Lỗi xử lý OCR: {str(e)}")
            return {
                'text': '',
                'confidence': 0
            }

    # def recognize_text(self, image):
    #     """
    #     Thực hiện OCR trên một ảnh đơn
    #     Args:
    #         image: Ảnh cần nhận dạng
    #     Returns:
    #         tuple: (văn bản nhận dạng được, độ tin cậy)
    #     """
    #     try:
    #         if not isinstance(image, Image.Image):
    #             image = Image.fromarray(image)
    #
    #         text = pytesseract.image_to_string(image, lang='vie')
    #         data = pytesseract.image_to_data(image, lang='vie', output_type=pytesseract.Output.DICT)
    #
    #         # Tính toán độ tin cậy trung bình
    #         confidences = [float(conf) for conf in data['conf'] if conf != '-1']
    #         confidence = sum(confidences) / len(confidences) if confidences else 0
    #
    #         self.logger.debug(f"Nhận dạng văn bản: độ tin cậy {confidence}%")
    #         return text.strip(), confidence
    #     except Exception as e:
    #         self.logger.error(f"Lỗi nhận dạng văn bản: {str(e)}")
    #         return "", 0
