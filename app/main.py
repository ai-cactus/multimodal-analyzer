"""
Multi-LLM RAG Analysis Service - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db, close_db
from app.api import regulations, documents
from app.utils.logger import setup_logger
from app.config import get_settings

settings = get_settings()
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting Multi-LLM RAG Analysis Service...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-LLM RAG Analysis Service...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Multi-LLM RAG Analysis Service",
    description="AI-powered compliance analysis using multi-model consensus",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(regulations.router, prefix="/api/regulations", tags=["Regulations"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])


# Add metrics endpoint for Prometheus
from app.monitoring.metrics import metrics_endpoint

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Multi-LLM RAG Analysis Service starting...")
    logger.info(f"GCP Project: {settings.gcp_project_id}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    
    # Create upload directory
    import os
    os.makedirs(settings.upload_dir, exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Multi-LLM RAG Analysis Service shutting down...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Multi-LLM RAG Analysis Service",
        "version": "1.0.0",
        "status": "operational",
        "phase": "Phase 1: Infrastructure & Extraction",
        "endpoints": {
            "regulations": "/api/regulations",
            "documents": "/api/documents",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Multi-LLM RAG Analysis Service"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
