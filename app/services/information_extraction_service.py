import re
import json
from datetime import datetime

from app.utils.logger import Logger


class InformationExtractor:
    def __init__(self, config):
        self.logger = Logger(__name__).logger
        self.patterns = config['extraction_patterns']
        self.logger.debug("Khởi tạo InformationExtractor với các mẫu: " +
                          str(list(self.patterns.keys())))

    def _clean_text(self, text):
        """Làm sạch text và giữ nguyên xuống dòng"""
        if not text:
            return ""
        # Chuẩn hóa xuống dòng thành \r\n
        text = text.replace('\n', '\r\n')
        # Loại bỏ khoảng trắng thừa nhưng giữ xuống dòng
        text = '\r\n'.join(line.strip() for line in text.split('\r\n'))
        return text.strip()

    def _extract_location_date(self, text):
        """Trích xuất địa điểm và ngày ban hành"""
        location_date = {}

        # Tìm địa điểm và ngày
        pattern = r'(?i)(?:tại|,)?\s*([^,\r\n]+?)\s*,\s*ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})'
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            day = match.group(2)
            month = match.group(3)
            year = match.group(4)

            location_date['issue_location'] = location
            location_date['issue_date'] = f"{day}/{month}/{year}"

        return location_date

    def _extract_subject(self, text):
        """Trích xuất trích yếu nội dung"""
        # Tìm trích yếu sau tiêu đề văn bản
        pattern = r'(?i)(?:v/v|về việc)\s+(.*?)(?=\r\n\r\n|\Z)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _extract_agency_info(self, text):
        """Trích xuất thông tin cơ quan ban hành"""
        # Lấy các dòng đầu tiên cho đến khi gặp ngày tháng
        pattern = r'^(.*?)(?=\r\n.*?ngày|\Z)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            agency_text = match.group(1).strip()
            # Loại bỏ các dòng không liên quan
            agency_lines = [line.strip() for line in agency_text.split('\r\n')
                            if line.strip() and not re.match(r'(?i)(số|ngày)', line)]
            return '\r\n'.join(agency_lines)
        return None

    def extract_information(self, text, document_id=None):
        """Trích xuất thông tin theo template"""
        self.logger.info("Bắt đầu trích xuất thông tin")

        # Làm sạch text
        text = self._clean_text(text)

        # Khởi tạo kết quả theo template
        result = {
            "metadata": {
                "document_id": str(document_id) if document_id else "1",
                "extraction_time": datetime.now().isoformat(),
                "version": "1.0"
            },
            "document_info": {
                "document_type": None,
                "document_number": None,
                "issue_location": None,
                "issue_date": None,
                "issuing_agency": None,
                "recipients": None,
                "recipient_address": None,
                "signer": None,
                "position": None,
                "subject": None,
                "content": text,
                "page_numbers": []  # Sẽ được cập nhật bởi DocumentMerger
            }
        }

        try:
            # Trích xuất thông tin cơ bản từ patterns
            for field, pattern_config in self.patterns.items():
                for pattern in pattern_config['patterns']:
                    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                    if match:
                        value = match.group(1) if len(match.groups()) > 0 else match.group(0)
                        result['document_info'][field] = value.strip()
                        break

            # Trích xuất địa điểm và ngày
            location_date = self._extract_location_date(text)
            result['document_info'].update(location_date)

            # Trích xuất trích yếu
            subject = self._extract_subject(text)
            if subject:
                result['document_info']['subject'] = subject

            # Trích xuất cơ quan ban hành
            if not result['document_info']['issuing_agency']:
                agency = self._extract_agency_info(text)
                if agency:
                    result['document_info']['issuing_agency'] = agency

            self.logger.info("Hoàn thành trích xuất thông tin")
            return result

        except Exception as e:
            self.logger.error(f"Lỗi trích xuất thông tin: {str(e)}")
            raise

    def format_output(self, documents):
        """Định dạng danh sách văn bản thành JSON"""
        try:
            return json.dumps(documents, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Lỗi định dạng output: {str(e)}")
            return "[]"