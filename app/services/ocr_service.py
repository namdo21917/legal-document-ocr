import json
import multiprocessing
import os

from PIL import Image

from app.services.document_merger import DocumentMerger
from app.services.image_preprocessing import ImagePreprocessor
from app.services.information_extraction import InformationExtractor
from app.services.ocr import OCRModule
from app.services.region_segmentation import RegionSegmenter
from app.services.table_detector import TableDetector
from app.utils.cache_manager import CacheManager
from app.utils.exceptions import FileError, OCRProcessError
from app.utils.validation import Validator


class OCRService:
    def __init__(self, config_path='config.json'):
        self.cache = CacheManager()
        self.validator = Validator()
        self.num_threads = multiprocessing.cpu_count()

        try:
            # Đọc và kiểm tra cấu hình
            if not self.validator.validate_file(config_path):
                raise ValueError(f"File cấu hình không hợp lệ: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            if not self.validator.validate_config(self.config):
                raise ValueError("Cấu hình không hợp lệ")

            # Khởi tạo các module
            self.preprocessor = ImagePreprocessor(self.config)
            self.segmenter = RegionSegmenter(self.config)
            self.ocr = OCRModule()
            self.extractor = InformationExtractor(self.config)
            self.table_detector = TableDetector(self.config)
            self.document_merger = DocumentMerger(self.config)

            self.logger.info("Khởi tạo các module thành công")

        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo hệ thống: {str(e)}")
            raise

    def process_document(self, input_path):
        """
        Xử lý văn bản từ file PDF
        Args:
            input_path: Đường dẫn đến file đầu vào
        Returns:
            dict: Kết quả xử lý
        """
        self.logger.info(f"Bắt đầu xử lý tài liệu: {input_path}")
        try:
            # Tạo thư mục output
            output_dir = 'output'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            base_name = os.path.splitext(os.path.basename(input_path))[0]

            # Kiểm tra file đầu vào
            if not self.validator.validate_file_path(input_path, ['.pdf', '.png', '.jpg', '.jpeg']):
                raise FileError(f"File đầu vào không hợp lệ: {input_path}", input_path)

            # Đọc và xử lý ảnh
            try:
                if input_path.lower().endswith('.pdf'):
                    images = self.preprocessor.convert_from_pdf(input_path)
                    if not images:
                        raise FileError("Không thể chuyển đổi PDF", input_path)
                else:
                    images = [Image.open(input_path)]
            except Exception as e:
                raise FileError(f"Lỗi đọc file: {str(e)}", input_path)

            all_results = []
            # Xử lý từng trang
            for page_num, image in enumerate(images, 1):
                self.logger.info(f"Xử lý trang {page_num}/{len(images)}")

                try:
                    # Tiền xử lý ảnh
                    binary_image = self.preprocessor.preprocess(image)

                    # Tìm các vùng văn bản
                    regions = self.segmenter.find_text_regions(binary_image)
                    if not regions:
                        self.logger.warning(f"Không tìm thấy vùng văn bản nào trong trang {page_num}")
                        continue

                    # Vẽ khung vùng văn bản
                    marked_image = self.segmenter.draw_regions(image, regions)

                    # Trích xuất và OCR các vùng
                    region_images = self.segmenter.extract_regions(image, regions)
                    ocr_results = self.ocr.recognize_regions(region_images)

                    # Kết hợp kết quả OCR
                    full_text = '\n'.join([result['text'] for result in ocr_results])

                    # Trích xuất thông tin
                    extracted_info = self.extractor.extract_information(full_text)['document_info']

                    # Phát hiện bảng
                    tables = self.table_detector.detect_tables(binary_image)
                    if tables:
                        self.logger.info(f"Đã phát hiện {len(tables)} bảng trong trang {page_num}")
                        for table in tables:
                            marked_image = self.table_detector.draw_table_boundaries(marked_image, table)

                    # Lưu kết quả trang
                    page_result = {
                        'page_number': page_num,
                        'processed_image': marked_image,
                        'ocr_text': full_text,
                        'extracted_info': extracted_info,
                        'regions': regions,
                        'tables': tables if tables else []
                    }
                    all_results.append(page_result)

                except Exception as e:
                    self.logger.error(f"Lỗi xử lý trang {page_num}: {str(e)}")
                    continue

            if not all_results:
                raise OCRProcessError("Không xử lý được trang nào")

            # Gộp các văn bản liên quan
            merged_docs = self.document_merger.merge_documents(all_results)

            # Lưu kết quả đã gộp
            self.document_merger.save_merged_documents(
                merged_docs,
                output_dir,
                base_name
            )

            self.logger.info(f"Xử lý thành công {len(all_results)} trang")
            return {
                'success': True,
                'num_pages': len(all_results),
                'num_documents': len(merged_docs),
                'documents': merged_docs  # Trả về danh sách văn bản đã gộp
            }

        except Exception as e:
            self.logger.error(f"Lỗi xử lý tài liệu: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
