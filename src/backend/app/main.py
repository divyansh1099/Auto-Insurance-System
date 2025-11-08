"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import get_settings
from app.routers import drivers, telematics, risk, pricing, analytics, auth, admin

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Telematics-based auto insurance system with real-time risk scoring and dynamic pricing",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("application_starting", app_name=settings.APP_NAME, version=settings.APP_VERSION)
    
    # Start Kafka consumer in background
    try:
        from app.services.kafka_consumer import start_consumer_background
        start_consumer_background(topic="telematics-events")
        logger.info("kafka_consumer_started")
    except Exception as e:
        logger.warning("kafka_consumer_start_failed", error=str(e))
        # Continue without Kafka consumer if it fails


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("application_shutting_down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Telematics Insurance System API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(drivers.router, prefix=f"{settings.API_V1_PREFIX}/drivers", tags=["Drivers"])
app.include_router(telematics.router, prefix=f"{settings.API_V1_PREFIX}/telematics", tags=["Telematics"])
app.include_router(risk.router, prefix=f"{settings.API_V1_PREFIX}/risk", tags=["Risk Scoring"])
app.include_router(pricing.router, prefix=f"{settings.API_V1_PREFIX}/pricing", tags=["Pricing"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error("unhandled_exception", exception=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
