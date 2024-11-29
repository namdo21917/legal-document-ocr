import re
from datetime import datetime

class InformationExtractor:
    def __init__(self):
        self.patterns = {
            'document_number': r'Số:\s*(\d+\/[^\s]+)',
            'issue_date': r'ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})',
            'signer': r'Người ký:\s*([^\n]+)',
            'position': r'Chức vụ:\s*([^\n]+)'
        }

    def extract_metadata(self, text):
        """Trích xuất metadata từ văn bản"""
        metadata = {}
        
        # Trích xuất số văn bản
        doc_num_match = re.search(self.patterns['document_number'], text)
        if doc_num_match:
            metadata['document_number'] = doc_num_match.group(1)

        # Trích xuất ngày tháng
        date_match = re.search(self.patterns['issue_date'], text)
        if date_match:
            day, month, year = map(int, date_match.groups())
            metadata['issue_date'] = datetime(year, month, day)

        return metadata

    def extract_content_structure(self, text):
        """Phân tích cấu trúc nội dung văn bản"""
        sections = {
            'header': self._extract_header(text),
            'body': self._extract_body(text),
            'footer': self._extract_footer(text)
        }
        return sections 