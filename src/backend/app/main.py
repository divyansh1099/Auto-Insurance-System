"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import structlog
from sqlalchemy import text
import traceback

from app.config import get_settings
from app.routers import drivers, telematics, risk, pricing, analytics, auth, admin, simulator, rewards, data_generator, realtime
from app.utils.metrics import PrometheusMiddleware, get_metrics
from app.utils.exceptions import BaseAPIException
from app.models.database import SessionLocal
from app.services.redis_client import get_redis_client

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

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)


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
    
    # Start Redis subscriber for real-time pub/sub updates (replaces polling)
    try:
        from app.services.redis_subscriber import start_redis_subscriber
        await start_redis_subscriber()
        logger.info("redis_subscriber_started")
    except Exception as e:
        logger.warning("redis_subscriber_start_failed", error=str(e))
        # Fallback to polling if pub/sub fails
        try:
            from app.services.realtime_poller import start_realtime_poller
            await start_realtime_poller()
            logger.info("realtime_poller_started_as_fallback")
        except Exception as poller_error:
            logger.warning("realtime_poller_fallback_failed", error=str(poller_error))


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
    """Enhanced health check endpoint."""
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "checks": {}
    }
    
    # Check database connection
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
        logger.warning("health_check_database_failed", error=str(e))
    
    # Check Redis connection
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        else:
            health_status["checks"]["redis"] = "unavailable"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
        logger.warning("health_check_redis_failed", error=str(e))
    
    # Check Kafka consumer status
    try:
        from app.services.kafka_consumer import get_consumer
        consumer = get_consumer()
        if consumer and consumer.running:
            health_status["checks"]["kafka"] = "healthy"
        else:
            health_status["checks"]["kafka"] = "not_running"
    except Exception as e:
        health_status["checks"]["kafka"] = f"error: {str(e)}"
        logger.warning("health_check_kafka_failed", error=str(e))
    
    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics()


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint (for Kubernetes)."""
    try:
        # Check database
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check Redis (optional)
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
        
        return {"status": "ready"}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


@app.get("/live")
async def liveness_check():
    """Liveness check endpoint (for Kubernetes)."""
    return {"status": "alive"}


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(drivers.router, prefix=f"{settings.API_V1_PREFIX}/drivers", tags=["Drivers"])
app.include_router(telematics.router, prefix=f"{settings.API_V1_PREFIX}/telematics", tags=["Telematics"])
app.include_router(risk.router, prefix=f"{settings.API_V1_PREFIX}/risk", tags=["Risk Scoring"])
app.include_router(pricing.router, prefix=f"{settings.API_V1_PREFIX}/pricing", tags=["Pricing"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin"])
app.include_router(simulator.router, prefix=f"{settings.API_V1_PREFIX}/simulator", tags=["Drive Simulator"])
app.include_router(rewards.router, prefix=f"{settings.API_V1_PREFIX}/rewards", tags=["Rewards"])
app.include_router(data_generator.router, prefix=f"{settings.API_V1_PREFIX}/data-generator", tags=["Data Generator"])
app.include_router(realtime.router, prefix=f"{settings.API_V1_PREFIX}/realtime", tags=["Real-Time"])


# Exception handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions."""
    logger.warning(
        "api_exception",
        error_code=exc.error_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "path": request.url.path
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    logger.warning(
        "validation_error",
        errors=error_details,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": error_details,
            "path": request.url.path
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    logger.error(
        "database_integrity_error",
        error=error_msg,
        path=request.url.path,
        method=request.method
    )
    
    # Check for common integrity errors
    if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Resource already exists",
                "error_code": "DUPLICATE_RESOURCE",
                "path": request.url.path
            }
        )
    elif "foreign key" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid reference to related resource",
                "error_code": "INVALID_REFERENCE",
                "path": request.url.path
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database integrity error",
            "error_code": "DATABASE_ERROR",
            "path": request.url.path
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(
        "database_error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database operation failed",
            "error_code": "DATABASE_ERROR",
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    error_traceback = traceback.format_exc()
    
    logger.error(
        "unhandled_exception",
        exception=str(exc),
        exception_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        traceback=error_traceback
    )
    
    # In production, don't expose internal errors
    if settings.DEBUG:
        detail = f"Internal server error: {str(exc)}"
    else:
        detail = "Internal server error. Please contact support if this persists."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "error_code": "INTERNAL_SERVER_ERROR",
            "path": request.url.path
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
