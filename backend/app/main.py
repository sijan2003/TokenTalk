"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.routes import auth, documents, youtube, webpage
import os

# Create FastAPI app instance
# title/version are used for the auto-generated Swagger documentation at /docs
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configure CORS (Cross-Origin Resource Sharing)
# This middleware allows our frontend (HTML/JS) to make requests to this backend.
# NOTE: allow_origins=["*"] allows any domain/IP to connect during development.
# allow_credentials=False is required when using the "*" wildcard to avoid browser errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registration: Breaking the app into modules (auth, docs, youtube, web)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(youtube.router)
app.include_router(webpage.router)

# Ensure required local directories exist for file uploads and AI indices
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """
    Runs once when the server starts.
    Initializes the SQLite database tables based on our Python models.
    """
    init_db()
    print(f"✅ {settings.APP_NAME} started successfully!")
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    print(f"🗄️ Vector store directory: {settings.VECTOR_STORE_DIR}")

@app.get("/")
async def root():
    """Simple health check and welcome message"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Standard health check endpoint for monitoring tools"""
    return {"status": "healthy"}
