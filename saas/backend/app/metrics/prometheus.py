"""Custom Prometheus metrics labeled by tenant."""

from prometheus_client import Counter, Gauge

TENANT_REQUESTS = Counter(
    "saas_tenant_requests_total",
    "Total requests processed per tenant",
    ["tenant_id", "endpoint", "status_code"],
)

TENANT_QUOTA_REMAINING = Gauge(
    "saas_tenant_quota_remaining",
    "Remaining transfer quota for the tenant",
    ["tenant_id"],
)
