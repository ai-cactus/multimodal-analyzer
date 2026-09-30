"""
Prometheus Metrics for Production Monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# LLM metrics
llm_calls_total = Counter(
    'llm_calls_total',
    'Total LLM API calls',
    ['model', 'status']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens consumed',
    ['model', 'type']  # type: input or output
)

llm_latency_seconds = Histogram(
    'llm_latency_seconds',
    'LLM API call latency',
    ['model']
)

# Analysis metrics
consensus_confidence_score = Gauge(
    'consensus_confidence_score',
    'Latest consensus confidence score'
)

documents_processed_total = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['status']  # status: completed, failed
)

active_workflows = Gauge(
    'active_workflows',
    'Number of active analysis workflows'
)

# Phase-specific metrics
phase_duration_seconds = Histogram(
    'phase_duration_seconds',
    'Duration of each analysis phase',
    ['phase']  # extraction, analysis, consensus, synthesis
)

findings_count = Histogram(
    'findings_count',
    'Number of findings per document',
    ['confidence_level']  # high, medium, low
)


class MetricsCollector:
    """
    Metrics collection helper
    """
    
    @staticmethod
    def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    @staticmethod
    def record_llm_call(model: str, status: str, tokens_input: int, tokens_output: int, latency: float):
        """Record LLM call metrics"""
        llm_calls_total.labels(model=model, status=status).inc()
        llm_tokens_total.labels(model=model, type="input").inc(tokens_input)
        llm_tokens_total.labels(model=model, type="output").inc(tokens_output)
        llm_latency_seconds.labels(model=model).observe(latency)
    
    @staticmethod
    def record_consensus_score(score: float):
        """Record consensus confidence score"""
        consensus_confidence_score.set(score)
    
    @staticmethod
    def record_document_completion(status: str):
        """Record document processing completion"""
        documents_processed_total.labels(status=status).inc()
    
    @staticmethod
    def increment_active_workflows():
        """Increment active workflows counter"""
        active_workflows.inc()
    
    @staticmethod
    def decrement_active_workflows():
        """Decrement active workflows counter"""
        active_workflows.dec()
    
    @staticmethod
    def record_phase_duration(phase: str, duration: float):
        """Record phase duration"""
        phase_duration_seconds.labels(phase=phase).observe(duration)
    
    @staticmethod
    def record_findings(high_count: int, medium_count: int, low_count: int):
        """Record findings counts"""
        findings_count.labels(confidence_level="high").observe(high_count)
        findings_count.labels(confidence_level="medium").observe(medium_count)
        findings_count.labels(confidence_level="low").observe(low_count)


def get_metrics_collector() -> MetricsCollector:
    """Get MetricsCollector instance"""
    return MetricsCollector()


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
