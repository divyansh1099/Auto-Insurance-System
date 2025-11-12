"""
Prometheus metrics for monitoring.

Comprehensive metrics collection for:
- HTTP requests and response times
- Database queries and connection pool
- Cache hit/miss rates
- Kafka consumer lag and throughput
- ML model inference performance
- Business metrics (active drivers, trips, risk scores)
"""
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import structlog

logger = structlog.get_logger()

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

# ============================================================================
# ENHANCED METRICS - Added for comprehensive monitoring
# ============================================================================

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type', 'cache_key_pattern']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type', 'cache_key_pattern']
)

cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation', 'cache_type']
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Total cache size in bytes',
    ['cache_type']
)

cache_evictions_total = Counter(
    'cache_evictions_total',
    'Total cache evictions',
    ['cache_type', 'reason']
)

# Database Connection Pool Metrics
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Current database connection pool size'
)

db_connection_pool_checked_out = Gauge(
    'db_connection_pool_checked_out',
    'Number of connections checked out from pool'
)

db_connection_pool_overflow = Gauge(
    'db_connection_pool_overflow',
    'Number of connections in overflow'
)

db_connection_pool_checked_in = Gauge(
    'db_connection_pool_checked_in',
    'Number of connections checked into pool'
)

db_connection_errors_total = Counter(
    'db_connection_errors_total',
    'Total database connection errors',
    ['error_type']
)

db_transaction_duration_seconds = Histogram(
    'db_transaction_duration_seconds',
    'Database transaction duration in seconds',
    ['operation']
)

# Enhanced Kafka Metrics
kafka_consumer_lag_messages = Gauge(
    'kafka_consumer_lag_messages',
    'Kafka consumer lag in number of messages',
    ['topic', 'partition', 'consumer_group']
)

kafka_messages_produced_total = Counter(
    'kafka_messages_produced_total',
    'Total Kafka messages produced',
    ['topic', 'status']
)

kafka_message_size_bytes = Histogram(
    'kafka_message_size_bytes',
    'Kafka message size in bytes',
    ['topic']
)

kafka_consumer_errors_total = Counter(
    'kafka_consumer_errors_total',
    'Total Kafka consumer errors',
    ['topic', 'error_type']
)

kafka_processing_errors_total = Counter(
    'kafka_processing_errors_total',
    'Total errors during message processing',
    ['topic', 'error_type']
)

# ML Model Metrics
ml_inference_duration_seconds = Histogram(
    'ml_inference_duration_seconds',
    'ML model inference duration in seconds',
    ['model_name', 'model_version']
)

ml_inference_total = Counter(
    'ml_inference_total',
    'Total ML model inferences',
    ['model_name', 'status']
)

ml_batch_size = Histogram(
    'ml_batch_size',
    'ML inference batch size',
    ['model_name']
)

ml_model_load_duration_seconds = Histogram(
    'ml_model_load_duration_seconds',
    'ML model load duration in seconds',
    ['model_name']
)

ml_feature_extraction_duration_seconds = Histogram(
    'ml_feature_extraction_duration_seconds',
    'Feature extraction duration in seconds'
)

ml_cache_hits_total = Counter(
    'ml_cache_hits_total',
    'ML prediction cache hits',
    ['model_name']
)

ml_cache_misses_total = Counter(
    'ml_cache_misses_total',
    'ML prediction cache misses',
    ['model_name']
)

# Business Metrics
active_drivers_total = Gauge(
    'active_drivers_total',
    'Number of active drivers'
)

active_trips_total = Gauge(
    'active_trips_total',
    'Number of active trips (trips without end_time)'
)

completed_trips_total = Counter(
    'completed_trips_total',
    'Total completed trips',
    ['risk_level']
)

events_per_second = Gauge(
    'events_per_second',
    'Telematics events processed per second'
)

average_risk_score = Gauge(
    'average_risk_score',
    'Average risk score across all drivers'
)

high_risk_drivers_total = Gauge(
    'high_risk_drivers_total',
    'Number of high-risk drivers'
)

medium_risk_drivers_total = Gauge(
    'medium_risk_drivers_total',
    'Number of medium-risk drivers'
)

low_risk_drivers_total = Gauge(
    'low_risk_drivers_total',
    'Number of low-risk drivers'
)

active_policies_total = Gauge(
    'active_policies_total',
    'Number of active insurance policies'
)

total_premiums_monthly = Gauge(
    'total_premiums_monthly',
    'Total monthly premiums across all policies'
)

average_premium_monthly = Gauge(
    'average_premium_monthly',
    'Average monthly premium per policy'
)

# WebSocket Metrics
websocket_connections_total = Gauge(
    'websocket_connections_total',
    'Number of active WebSocket connections'
)

websocket_messages_sent_total = Counter(
    'websocket_messages_sent_total',
    'Total WebSocket messages sent',
    ['message_type']
)

websocket_messages_failed_total = Counter(
    'websocket_messages_failed_total',
    'Total failed WebSocket message deliveries',
    ['message_type']
)

# API Error Metrics
api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type', 'status_code']
)

api_validation_errors_total = Counter(
    'api_validation_errors_total',
    'Total API validation errors',
    ['endpoint', 'field']
)

# Performance Metrics
slow_queries_total = Counter(
    'slow_queries_total',
    'Total slow database queries (>1s)',
    ['table', 'operation']
)

large_response_payloads_total = Counter(
    'large_response_payloads_total',
    'Total large response payloads (>1MB)',
    ['endpoint']
)

response_size_bytes = Histogram(
    'response_size_bytes',
    'Response payload size in bytes',
    ['endpoint']
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

