import re
from datetime import datetime
import json
import os
from PIL import Image, ImageDraw
import numpy as np

from app.services.information_extraction_service import InformationExtractor
from app.utils.logger import Logger

class DocumentMerger:
    def __init__(self, config):
        self.logger = Logger(__name__).logger
        self.extractor = InformationExtractor(config)
        self.doc_patterns = config['document_patterns']
        self.all_pages = []


    def _merge_pages_content(self, pages):
        """
        Gộp nội dung của các trang thành một văn bản hoàn chỉnh
        """
        full_text = []
        for page in pages:
            if page.get('ocr_text'):
                full_text.append(page['ocr_text'])
        return '\n\n'.join(full_text)

    def _is_same_document(self, page1, page2):
        """
        Kiểm tra xem hai trang có thuộc cùng một văn bản không
        """
        try:
            # Kiểm tra số văn bản
            num1 = self._normalize_text(page1['extracted_info'].get('document_number', ''))
            num2 = self._normalize_text(page2['extracted_info'].get('document_number', ''))
            if num1 and num2 and num1 == num2:
                return True

            # Kiểm tra nội dung tiếp nối
            text1 = page1['ocr_text'].strip()
            text2 = page2['ocr_text'].strip()
            
            # Kiểm tra câu cuối của trang 1 và câu đầu của trang 2
            last_sentence = text1.split('.')[-1].strip()
            first_sentence = text2.split('.')[0].strip()
            
            # Nếu có sự tiếp nối của từ
            if last_sentence and first_sentence:
                words1 = set(last_sentence.lower().split())
                words2 = set(first_sentence.lower().split())
                if len(words1.intersection(words2)) >= 2:  # Ít nhất 2 từ trùng nhau
                    return True

            # Kiểm tra các trường thông tin khác
            matching_fields = ['document_type', 'issuing_agency', 'issue_date']
            matches = 0
            for field in matching_fields:
                val1 = self._normalize_text(page1['extracted_info'].get(field, ''))
                val2 = self._normalize_text(page2['extracted_info'].get(field, ''))
                if val1 and val2 and val1 == val2:
                    matches += 1
            if matches >= 2:  # Ít nhất 2 trường thông tin trùng khớp
                return True

            return False
        except Exception as e:
            self.logger.error(f"Lỗi kiểm tra văn bản cùng loại: {str(e)}")
            return False

    def _is_empty_page(self, page_data):
        """
        Kiểm tra trang trống
        """
        # Kiểm tra nội dung OCR
        if not page_data.get('ocr_text', '').strip():
            return True
            
        # Kiểm tra thông tin trích xuất
        extracted_info = page_data.get('extracted_info', {})
        if not any(extracted_info.values()):
            return True
            
        # Kiểm tra regions
        if not page_data.get('regions', []):
            return True
            
        return False

    def _normalize_text(self, text):
        """
        Chuẩn hóa text để so sánh
        """
        if not text:
            return ""
        # Loại bỏ dấu câu và khoảng trắng thừa
        text = re.sub(r'[^\w\s-]', '', text)
        # Chuyển về chữ thường
        return text.lower().strip()

    def _convert_to_serializable(self, obj):
        """
        Chuyển đổi object thành dạng có thể serialize JSON
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        return obj

    def _extract_document_info(self, pages):
        """
        Trích xuất thông tin văn bản từ các trang
        """
        # Lấy text từ tất cả các trang
        full_text = '\n\n'.join(page['ocr_text'] for page in pages)
        
        # Trích xuất các trường thông tin
        info = {
            'document_type': None,
            'document_number': None,
            'issue_location': None,
            'issue_date': None,
            'issuing_agency': None,
            'recipients': None,
            'recipient_address': None,
            'signer': None,
            'position': None,
            'subject': None,
            'content': full_text,
            'page_numbers': [page['page_number'] for page in pages]
        }

        # Trích xuất từ trang đầu tiên
        first_page = pages[0]['extracted_info']
        
        # Loại văn bản và số
        info['document_type'] = first_page.get('document_type')
        doc_number = first_page.get('document_number')
        if doc_number:
            # Tìm số đầy đủ (ví dụ: 391-TTr/VTCCB-TH)
            full_number = re.search(r'[Ss]ố\s*:?\s*([\w-]+/[\w-]+)', full_text)
            if full_number:
                info['document_number'] = full_number.group(1)
            else:
                info['document_number'] = doc_number

        # Địa điểm
        location_match = re.search(r'(?i),?\s*(Hà\s*Nội)\s*,\s*ngày', full_text)
        if location_match:
            info['issue_location'] = location_match.group(1)

        # Ngày tháng
        info['issue_date'] = first_page.get('issue_date')

        # Cơ quan ban hành (2 dòng đầu)
        agency_match = re.search(r'^([^\n]+\n[^\n]+)', full_text)
        if agency_match:
            info['issuing_agency'] = agency_match.group(1).strip()

        # Người nhận
        recipient_match = re.search(r'Kính\s+gửi\s*:?\s*([^\n]+(?:\n[^\n]+)?)', full_text)
        if recipient_match:
            info['recipients'] = recipient_match.group(1).strip()

        # Nơi nhận
        address_match = re.search(r'Nơi\s+nhận\s*:([^\n]+(?:\n-[^\n]+)*)', full_text)
        if address_match:
            info['recipient_address'] = address_match.group(1).strip()

        # Người ký (ở cuối văn bản)
        signer_match = re.search(r'\n([A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰÝỶỸỴ\s]+)$', full_text)
        if signer_match:
            info['signer'] = signer_match.group(1).strip()

        # Chức vụ
        position_match = re.search(r'K/T.*?\n([A-Z\s]+)', full_text)
        if position_match:
            info['position'] = position_match.group(1).strip()

        # Trích yếu
        subject_match = re.search(r'V/v\s+([^\n]+(?:\n[^\n]+)?)', full_text)
        if subject_match:
            info['subject'] = subject_match.group(1).strip()

        return info

    def merge_documents(self, page_results):
        """
        Gộp các trang thành văn bản hoàn chỉnh
        """
        try:
            self.logger.info("Bắt đầu gộp văn bản")
            self.all_pages = []
            documents = []
            current_doc = None
            
            # Lọc bỏ các trang trống nhưng vẫn giữ lại trong all_pages
            self.all_pages = page_results
            valid_pages = [p for p in page_results if not self._is_empty_page(p)]
            
            for i, page in enumerate(valid_pages):
                page['page_number'] = i + 1
                
                # Kiểm tra xem có thuộc văn bản hiện tại không
                if current_doc and self._is_same_document(current_doc['pages'][-1], page):
                    current_doc['pages'].append(page)
                else:
                    # Lưu văn bản hiện tại nếu có
                    if current_doc:
                        documents.append(current_doc)
                    
                    # Tạo văn bản mới
                    current_doc = {'pages': [page]}

            # Thêm văn bản cuối cùng
            if current_doc:
                documents.append(current_doc)

            # Xử lý từng văn bản
            processed_docs = []
            for i, doc in enumerate(documents, 1):
                # Trích xuất thông tin từ các trang
                doc_info = self._extract_document_info(doc['pages'])
                
                processed_doc = {
                    'metadata': {
                        'document_id': str(i),
                        'extraction_time': datetime.now().isoformat(),
                        'version': '1.0'
                    },
                    'document_info': doc_info
                }
                processed_docs.append(processed_doc)

            self.logger.info(f"Đã gộp thành {len(processed_docs)} văn bản")
            return processed_docs

        except Exception as e:
            self.logger.error(f"Lỗi gộp văn bản: {str(e)}")
            return []

    def save_merged_documents(self, documents, output_dir, base_name):
        """
        Lưu các văn bản đã gộp theo cấu trúc thư mục chuẩn
        """
        try:
            # Tạo cấu trúc thư mục
            date_dir = datetime.now().strftime('%Y%m%d')
            base_dir = os.path.join(output_dir, date_dir, base_name)
            pages_dir = os.path.join(base_dir, 'pages')
            docs_dir = os.path.join(base_dir, 'documents')
            
            # Tạo các thư mục
            os.makedirs(base_dir, exist_ok=True)
            os.makedirs(pages_dir, exist_ok=True)
            os.makedirs(docs_dir, exist_ok=True)

            # Lưu từng trang
            for page_data in self.all_pages:
                page_num = page_data['page_number']
                page_dir = os.path.join(pages_dir, f'page_{str(page_num).zfill(3)}')
                os.makedirs(page_dir, exist_ok=True)

                # Lưu ảnh gốc
                if 'processed_image' in page_data:
                    page_data['processed_image'].save(os.path.join(page_dir, 'image.png'))

                # Tạo và lưu ảnh regions
                if 'regions' in page_data and 'processed_image' in page_data:
                    regions_image = page_data['processed_image'].copy()
                    draw = ImageDraw.Draw(regions_image)
                    for region in page_data['regions']:
                        if isinstance(region, np.ndarray):
                            region = region.tolist()
                        x, y, w, h = region
                        draw.rectangle([x, y, x+w, y+h], outline='red', width=2)
                    regions_image.save(os.path.join(page_dir, 'regions.png'))

                # Lưu text OCR
                with open(os.path.join(page_dir, 'full_text.txt'), 'w', encoding='utf-8') as f:
                    f.write(page_data['ocr_text'])

                # Chuẩn bị và lưu thông tin trang
                page_info = {
                    'metadata': {
                        'page_number': page_num,
                        'extraction_time': datetime.now().isoformat(),
                        'version': '1.0'
                    },
                    'page_info': {
                        'text_regions': self._convert_to_serializable(page_data.get('regions', [])),
                        'tables': self._convert_to_serializable(page_data.get('tables', [])),
                        'extracted_info': page_data.get('extracted_info', {})
                    }
                }
                with open(os.path.join(page_dir, 'info.json'), 'w', encoding='utf-8') as f:
                    json.dump(page_info, f, ensure_ascii=False, indent=2)

            # Lưu từng văn bản
            for doc in documents:
                doc_id = doc['metadata']['document_id']
                doc_dir = os.path.join(docs_dir, f'document_{doc_id.zfill(3)}')
                os.makedirs(doc_dir, exist_ok=True)

                # Chuẩn bị và lưu thông tin văn bản
                doc_info = self._convert_to_serializable(doc)
                with open(os.path.join(doc_dir, 'info.json'), 'w', encoding='utf-8') as f:
                    json.dump(doc_info, f, ensure_ascii=False, indent=2)

                # Lưu nội dung đầy đủ
                with open(os.path.join(doc_dir, 'full_text.txt'), 'w', encoding='utf-8') as f:
                    f.write(doc['document_info']['content'])

            # Lưu file tổng hợp
            serializable_docs = self._convert_to_serializable(documents)
            with open(os.path.join(base_dir, 'documents.json'), 'w', encoding='utf-8') as f:
                json.dump(serializable_docs, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Đã lưu {len(documents)} văn bản")
            self.logger.info(f"Kết quả được lưu tại: {base_dir}")
            
        except Exception as e:
            self.logger.error(f"Lỗi lưu văn bản: {str(e)}")
            raise