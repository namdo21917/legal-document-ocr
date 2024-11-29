
1. **Documents**: Lưu trữ thông tin về các tài liệu đã xử lý.
   - `id`: Khóa chính.
   - `document_id`: ID của tài liệu (chuỗi).
   - `extraction_time`: Thời gian trích xuất thông tin.
   - `version`: Phiên bản của thông tin trích xuất.
   - `document_type`: Loại tài liệu.
   - `document_number`: Số hiệu tài liệu.
   - `issue_location`: Nơi cấp.
   - `issue_date`: Ngày cấp.
   - `issuing_agency`: Cơ quan cấp.
   - `recipients`: Người nhận.
   - `recipient_address`: Địa chỉ người nhận.
   - `signer`: Người ký.
   - `position`: Chức vụ của người ký.
   - `subject`: Chủ đề của tài liệu.
   - `content`: Nội dung của tài liệu.
   - `page_numbers`: Danh sách số trang (có thể lưu dưới dạng chuỗi JSON nếu cần).

2. **Pages**: Lưu trữ thông tin và hình ảnh của các trang trong tài liệu.
   - `id`: Khóa chính.
   - `document_id`: Khóa ngoại tham chiếu đến bảng Documents.
   - `page_number`: Số thứ tự trang.
   - `ocr_text`: Văn bản OCR của trang.
   - `image_data`: Dữ liệu nhị phân của hình ảnh (BLOB) hoặc đường dẫn đến hình ảnh gốc.
