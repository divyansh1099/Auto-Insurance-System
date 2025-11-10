"""
Prometheus metrics for monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database Metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

# Kafka Metrics
kafka_messages_consumed_total = Counter(
    'kafka_messages_consumed_total',
    'Total Kafka messages consumed',
    ['topic']
)

kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag',
    ['topic']
)

kafka_processing_duration_seconds = Histogram(
    'kafka_processing_duration_seconds',
    'Kafka message processing duration',
    ['topic']
)

# Risk Scoring Metrics
risk_score_calculations_total = Counter(
    'risk_score_calculations_total',
    'Total risk score calculations',
    ['driver_id']
)

risk_score_duration_seconds = Histogram(
    'risk_score_duration_seconds',
    'Risk score calculation duration in seconds'
)

# Redis Metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation']
)

# System Metrics
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

events_processed_total = Counter(
    'events_processed_total',
    'Total telematics events processed',
    ['event_type', 'status']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP requests with Prometheus."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get endpoint path (remove query params)
        endpoint = request.url.path
        
        # Skip metrics endpoint
        if endpoint == "/metrics":
            return await call_next(request)
        
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response


def get_metrics():
    """Get Prometheus metrics."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

