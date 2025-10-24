from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from backend.api.models import Base, engine
from backend.api.routes import conversations_router, messages_router, diagrams_router
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Architecture Diagram Generator API",
    description="AI-powered architecture diagram generator from technical conversations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables
@app.on_event("startup")
async def startup():
    """Initialize app on startup"""
    logger.info("Starting Architecture Diagram Generator API")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Ensure diagram storage directory exists
    os.makedirs(settings.DIAGRAM_STORAGE_PATH, exist_ok=True)
    logger.info(f"Diagram storage path: {settings.DIAGRAM_STORAGE_PATH}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down Architecture Diagram Generator API")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


# Include routers
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(diagrams_router, prefix="/api/v1")


# Serve static files for diagrams
if os.path.exists(settings.DIAGRAM_STORAGE_PATH):
    app.mount(
        "/diagrams",
        StaticFiles(directory=settings.DIAGRAM_STORAGE_PATH),
        name="diagrams"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
