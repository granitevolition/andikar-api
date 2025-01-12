from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import document, auth
from app.api.routes import document
from app.core.config import settings

app = FastAPI(
    title="Document Processing API",
    description="API for processing and rewriting documents using AI",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(document.router, prefix="/api/v1/documents", tags=["documents"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

