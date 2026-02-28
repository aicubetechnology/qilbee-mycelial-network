"""
Prometheus metrics for QMN services.

Provides custom business metrics counters, histograms, and gauges.
"""

from prometheus_client import Counter, Histogram, Gauge

# Business counters
nutrients_broadcast_total = Counter(
    "qmn_nutrients_broadcast_total",
    "Total number of nutrients broadcast",
    ["tenant_id"],
)

contexts_collected_total = Counter(
    "qmn_contexts_collected_total",
    "Total number of context collection requests",
    ["tenant_id"],
)

outcomes_recorded_total = Counter(
    "qmn_outcomes_recorded_total",
    "Total number of outcomes recorded",
    ["tenant_id"],
)

edges_updated_total = Counter(
    "qmn_edges_updated_total",
    "Total number of edge weight updates",
    ["tenant_id"],
)

# Latency histograms
routing_latency = Histogram(
    "qmn_routing_latency_seconds",
    "Time spent routing nutrients",
    ["tenant_id"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

vector_search_latency = Histogram(
    "qmn_vector_search_latency_seconds",
    "Time spent on vector similarity search",
    ["tenant_id"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Gauges
active_agents = Gauge(
    "qmn_active_agents",
    "Number of active agents",
    ["tenant_id"],
)

active_nutrients = Gauge(
    "qmn_active_nutrients",
    "Number of active nutrients in transit",
    ["tenant_id"],
)
