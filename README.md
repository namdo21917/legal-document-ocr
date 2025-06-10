# Legal Document OCR

## Cấu Trúc Dự Án
legal_document_ocr/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Cấu hình ứng dụng
│   │   └── security.py        # Xử lý authentication/authorization
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── documents.py    # API xử lý documents
│   │   │   │   └── pages.py        # API xử lý pages
│   │   │   └── router.py
│   │   └── dependencies.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py     # Xử lý OCR
│   │   ├── document_parser.py  # Phân tích tài liệu
│   │   └── storage_service.py  # Quản lý lưu trữ file
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py        # SQLAlchemy model cho Documents
│   │   └── page.py           # SQLAlchemy model cho Pages
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── document.py       # Pydantic schemas cho Documents
│   │   └── page.py          # Pydantic schemas cho Pages
│   │
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py          # Base CRUD operations
│   │   ├── document.py      # CRUD cho Documents
│   │   └── page.py         # CRUD cho Pages
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_handlers.py  # Xử lý file
│       └── validators.py     # Validation helpers
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   │   ├── test_documents.py
│   │   └── test_pages.py
│   └── test_services/
│       ├── test_ocr.py
│       └── test_document_parser.py
│
├── alembic/
│   ├── versions/
│   └── alembic.ini
│
├── static/
│   └── uploads/             # Thư mục lưu file tạm
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md


### Mô tả :
   Client đẩy tệp (pdf, ảnh) lên hệ thống. Hệ thống sẽ OCR sau đó trả về kết quả dữ liệu dạng json. Thông tin của từng trang, document sau khi OCR sẽ được lưu vào database. Đối với các trang có bảng, hệ thống sẽ trích xuất ra các ô và nội dung của ô đó. Ngoài ra, PDF có nhiều trang thì sẽ trả ra các trang riêng biệt.

## Chi Tiết Các Logic business
### 1. image_preprocessing.py
- Xử lý tiền xử lý ảnh
- Chuyển đổi màu sắc và format
- Tăng cường chất lượng ảnh
- Xoay ảnh tự động
- Chuyển đổi PDF sang ảnh

### 2. region_segmentation.py
- Phân tích và phân đoạn vùng văn bản
- Phát hiện contours
- Lọc và sắp xếp vùng văn bản
- Vẽ khung đánh dấu vùng

### 3. ocr_module.py
- Xử lý OCR đa luồng
- Tích hợp Tesseract OCR
- Quản lý cache kết quả
- Tối ưu hiệu suất xử lý

### 4. table_detector.py
- Phát hiện cấu trúc bảng
- Phân tích đường kẻ và ô
- Trích xuất nội dung từng ô
- Vẽ khung bảng

### 5. information_extraction.py
- Trích xuất thông tin theo mẫu
- Xử lý regex patterns
- Phân loại thông tin
- Định dạng kết quả

### 6. cache_manager.py
- Quản lý bộ nhớ cache
- Lưu và đọc kết quả OCR
- Tự động dọn dẹp cache cũ
- Tối ưu hiệu suất truy xuất

### 7. validation.py
- Kiểm tra tính hợp lệ đầu vào
- Validate file và format
- Kiểm tra cấu hình
- Báo lỗi chi tiết

### 8. exceptions.py
- Định nghĩa các loại exception
- Quản lý thông tin lỗi
- Phân loại lỗi theo module
- Hỗ trợ debug

### 9. logger.py
- Quản lý logging hệ thống
- Ghi log theo cấp độ
- Lưu log vào file
- Hiển thị log console

### 10. run_ocr.py
- Script chạy chính
- Xử lý tham số dòng lệnh
- Kiểm tra môi trường
- Hiển thị kết quả

### 11. Lưu vào database

### 12. config.json
- Cấu hình cho các module
- Tham số xử lý ảnh
- Pattern trích xuất thông tin:
- Cấu hình cache và logging

### 13. requirements.txt
opencv-python-headless==4.8.1.78
tesserocr==2.6.0
pdf2image==1.16.3
pillow==10.0.0
numpy==1.24.3
hashlib==20.3.0
pickle5==0.0.12


## Luồng Xử Lý

1. **Đầu vào**
   - File PDF hoặc ảnh
   - Kiểm tra tính hợp lệ
   - Chuyển đổi format

2. **Tiền xử lý**
   - Xử lý ảnh
   - Xoay tự động
   - Tăng cường chất lượng

3. **Phân đoạn**
   - Tìm vùng văn bản
   - Phát hiện bảng
   - Đánh dấu vùng

4. **OCR**
   - Xử lý song song
   - Cache kết quả
   - Nhận dạng text

5. **Trích xuất**
   - Phân tích nội dung
   - Trích xuất thông tin
   - Xử lý bảng

6. **Đầu ra**
   - Ảnh đã xử lý
   - Text OCR
   - JSON kết quả
   - Log chi tiết

## Cải Tiến

1. **Hiệu suất**
   - Xử lý song song
   - Cache thông minh
   - Tối ưu bộ nhớ

2. **Độ chính xác**
   - Xoay ảnh tự động
   - Tăng cường chất lượng
   - Xử lý bảng thông minh

3. **Bảo trì**
   - Logging chi tiết
   - Xử lý lỗi rõ ràng
   - Cấu trúc module hóa

4. **Mở rộng**
   - Dễ thêm tính năng
   - Cấu hình linh hoạt
   - API rõ ràng

## Yêu Cầu Hệ Thống

- Python 3.7+
- Tesseract OCR
- RAM: 4GB+
- Disk: 1GB+
- OS: Windows/Linux/MacOS