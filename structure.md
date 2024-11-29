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