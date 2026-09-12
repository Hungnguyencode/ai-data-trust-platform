from __future__ import annotations

from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "ai_data_trust_http_requests_total",
    "Total number of HTTP requests handled by the API.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ai_data_trust_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
    ),
)


def observe_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        path=path,
    ).observe(duration_seconds)