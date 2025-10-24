from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import settings
from backend.api.models import Base, engine
from backend.api.routes import conversations_router, messages_router, diagrams_router
import os
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


# Rate limiting middleware (simple implementation)
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Clean up old entries
        self.clients = {
            ip: timestamps for ip, timestamps in self.clients.items()
            if any(t > current_time - self.period for t in timestamps)
        }

        # Check rate limit
        if client_ip in self.clients:
            recent_calls = [t for t in self.clients[client_ip] if t > current_time - self.period]
            if len(recent_calls) >= self.calls:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."}
                )
            self.clients[client_ip] = recent_calls + [current_time]
        else:
            self.clients[client_ip] = [current_time]

        return await call_next(request)


# Create FastAPI app
app = FastAPI(
    title="Architecture Diagram Generator API",
    description="AI-powered architecture diagram generator from technical conversations",
    version="1.0.0",
    docs_url="/api/docs" if settings.API_RELOAD else None,  # Disable docs in production
    redoc_url="/api/redoc" if settings.API_RELOAD else None,
    openapi_url="/api/openapi.json" if settings.API_RELOAD else None
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS with more restrictive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add trusted host middleware for production
if not settings.API_RELOAD:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
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
