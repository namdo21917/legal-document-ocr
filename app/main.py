from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import engine

app = FastAPI(
    title="Legal Document OCR API",
    description="API for OCR processing of legal documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

origins = [
    settings.CLIENT_ORIGIN,
    'http://127.0.0.1:5173'
]


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router, 
    prefix="/api/v1",
    tags=["OCR API"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to Legal Document OCR API"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Legal Document OCR API",
        version="1.0.0",
        description="API for OCR processing of legal documents",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
