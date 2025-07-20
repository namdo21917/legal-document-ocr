# Legal Document OCR

A comprehensive OCR (Optical Character Recognition) system for processing legal documents with advanced table detection and information extraction capabilities.

##  Overview

This system allows clients to upload files (PDF, images) and receive OCR results in JSON format. The system processes each page and document, storing the results in a database. For pages containing tables, the system extracts individual cells and their content. Multi-page PDFs are processed as separate pages.

##  Project Structure

```
legal_document_ocr/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Application configuration
│   │   └── security.py        # Authentication/authorization handling
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── documents.py    # Document API endpoints
│   │   │   │   └── pages.py        # Page API endpoints
│   │   │   └── router.py
│   │   └── dependencies.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py     # OCR processing service
│   │   ├── document_parser.py  # Document analysis service
│   │   └── storage_service.py  # File storage management
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py        # SQLAlchemy model for Documents
│   │   └── page.py           # SQLAlchemy model for Pages
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── document.py       # Pydantic schemas for Documents
│   │   └── page.py          # Pydantic schemas for Pages
│   │
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py          # Base CRUD operations
│   │   ├── document.py      # CRUD for Documents
│   │   └── page.py         # CRUD for Pages
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_handlers.py  # File processing utilities
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
│   └── uploads/             # Temporary file storage
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

##  Core Business Logic Components

### 1. image_preprocessing.py
- Image preprocessing operations
- Color space and format conversion
- Image quality enhancement
- Automatic image rotation
- PDF to image conversion

### 2. region_segmentation.py
- Text region analysis and segmentation
- Contour detection
- Text region filtering and sorting
- Region boundary marking

### 3. ocr_module.py
- Multi-threaded OCR processing
- Tesseract OCR integration
- Result caching management
- Performance optimization

### 4. table_detector.py
- Table structure detection
- Line and cell analysis
- Individual cell content extraction
- Table boundary visualization

### 5. information_extraction.py
- Template-based information extraction
- Regex pattern processing
- Information classification
- Result formatting

### 6. cache_manager.py
- Memory cache management
- OCR result storage and retrieval
- Automatic cache cleanup
- Access performance optimization

### 7. validation.py
- Input validation
- File and format validation
- Configuration validation
- Detailed error reporting

### 8. exceptions.py
- Custom exception definitions
- Error information management
- Module-specific error classification
- Debug support

### 9. logger.py
- System logging management
- Level-based logging
- File logging
- Console output

### 10. run_ocr.py
- Main execution script
- Command-line parameter handling
- Environment validation
- Result display

### 11. Database Storage
- Processed document and page information storage

### 12. config.json
- Module configuration
- Image processing parameters
- Information extraction patterns
- Cache and logging configuration

##  Dependencies

```txt
opencv-python-headless==4.8.1.78
tesserocr==2.6.0
pdf2image==1.16.3
pillow==10.0.0
numpy==1.24.3
hashlib==20.3.0
pickle5==0.0.12
```

##  Processing Workflow

### 1. Input Stage
- PDF or image file upload
- File validation
- Format conversion

### 2. Preprocessing
- Image processing
- Automatic rotation
- Quality enhancement

### 3. Segmentation
- Text region detection
- Table detection
- Region marking

### 4. OCR Processing
- Parallel processing
- Result caching
- Text recognition

### 5. Information Extraction
- Content analysis
- Information extraction
- Table processing

### 6. Output Generation
- Processed images
- OCR text
- JSON results
- Detailed logs

##  Key Features & Improvements

###  Performance
- Parallel processing
- Intelligent caching
- Memory optimization

### Accuracy
- Automatic image rotation
- Quality enhancement
- Smart table processing

###  Maintainability
- Detailed logging
- Clear error handling
- Modular architecture

###  Scalability
- Easy feature addition
- Flexible configuration
- Clear API design

##  System Requirements

- **Python**: 3.7+
- **OCR Engine**: Tesseract OCR
- **RAM**: 4GB minimum
- **Storage**: 1GB minimum
- **OS**: Windows/Linux/MacOS

##  Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd legal-document-ocr
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python app/main.py
   ```

##  API Documentation

The system provides RESTful APIs for document processing:

- `POST /api/v1/documents/` - Upload and process documents
- `GET /api/v1/documents/{id}` - Retrieve document information
- `GET /api/v1/pages/{id}` - Retrieve page information

##  Testing

Run the test suite:
```bash
pytest tests/
```

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request