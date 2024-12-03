# legal-document-ocr

Tôi sẽ hướng dẫn chi tiết các bước chạy dự án trên Windows:
Cài đặt Python 3.10.0:
# Tải Python 3.10.0 từ
https://www.python.org/downloads/release/python-3100/
# Chọn Windows installer (64-bit)
# Trong quá trình cài đặt:
- ✓ Add Python 3.10 to PATH
- ✓ Install for all users

Cài đặt Tesseract OCR:
# Tải Tesseract installer từ:
Home
# Chọn: tesseract-ocr-w64-setup-v5.3.1.20230401.exe
# Trong quá trình cài đặt:
- Chọn "Additional language data"
- ✓ Vietnamese language data
- Ghi nhớ đường dẫn: C:\Program Files\Tesseract-OCR

Cài đặt Poppler:
# Tải từ GitHub:
GitHub - oschwartz10612/poppler-windows: Download Poppler binaries packaged for Windows with dependereleases
# Tải file: Release-24.02.0-0.zip
# Giải nén và cài đặt:
- Tạo thư mục: C:\Program Files\poppler
- Copy nội dung từ zip vào thư mục vừa tạo

Thêm biến môi trường:
# Mở System Properties:
Windows + R -> sysdm.cpl -> Advanced -> Environment Variables
# Trong System Variables -> Path, thêm:
C:\Program Files\Tesseract-OCR
C:\Program Files\poppler\Library\bin

Tạo và thiết lập dự án:
# Tạo thư mục dự án
cd C:\Users\YourUsername\Documents
mkdir legal_document_ocr
cd legal_document_ocr
# Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate
# Cài đặt dependencies
pip install -r requirements.txt

Tạo cấu trúc thư mục:
# Trong thư mục dự án, tạo các thư mục:
mkdir logs
mkdir cache
mkdir output

Kiểm tra cài đặt:
# Tạo file test_env.py:
import sys
import cv2
import numpy
import tesserocr
from PIL import Image
from pdf2image import convert_from_path
print(f"Python version: {sys.version}")
print(f"Tesseract version: {tesserocr.get_version()}")
print(f"OpenCV version: {cv2.__version__}")
print(f"Numpy version: {numpy.__version__}")
print(f"Pillow version: {Image.__version__}")
# Chạy test:
python test_env.py

Chạy ứng dụng:
# Đặt file PDF cần xử lý vào thư mục dự án
# Ví dụ: document.pdf
# Chạy OCR:
python run_ocr.py document.pdf

Kiểm tra kết quả:
# Kết quả sẽ được lưu trong thư mục output:
- document_processed.png  # Ảnh đã xử lý
- document_ocr.txt       # Văn bản OCR
- document_info.json     # Thông tin trích xuất
# Log được lưu trong thư mục logs

Xử lý lỗi thường gặp:
Lỗi Tesseract không tìm thấy:
# Kiểm tra biến môi trường
echo %PATH%
# Hoặc thêm trực tiếp trong code:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

Lỗi pdf2image:
# Kiểm tra Poppler trong PATH
where pdftoppm
# Khởi động lại Command Prompt sau khi thêm PATH

Lỗi permission:
# Chạy Command Prompt với quyền Administrator
# Kiểm tra quyền truy cập thư mục