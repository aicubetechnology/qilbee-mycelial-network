"""
Unit tests for Phase 4 observability & monitoring.

Tests: structured logging, metrics module, alerting rules.
"""

import pytest
import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))


class TestStructuredLogging:
    """Test structured logging configuration."""

    def test_configure_logging_returns_logger(self):
        """Configure logging returns a bound logger."""
        from shared.logging import configure_logging
        logger = configure_logging("test-service")
        assert logger is not None

    def test_bind_and_clear_context(self):
        """Can bind and clear context variables."""
        from shared.logging import bind_context, clear_context
        bind_context(tenant_id="test", trace_id="tr-123")
        clear_context()


class TestMetricsModule:
    """Test Prometheus metrics module."""

    def test_metrics_import(self):
        """All metrics can be imported."""
        from shared.metrics import (
            nutrients_broadcast_total,
            contexts_collected_total,
            outcomes_recorded_total,
            edges_updated_total,
            routing_latency,
            vector_search_latency,
            active_agents,
            active_nutrients,
        )
        assert nutrients_broadcast_total is not None
        assert contexts_collected_total is not None
        assert outcomes_recorded_total is not None
        assert edges_updated_total is not None
        assert routing_latency is not None
        assert vector_search_latency is not None
        assert active_agents is not None
        assert active_nutrients is not None

    def test_counter_increment(self):
        """Counters can be incremented."""
        from shared.metrics import nutrients_broadcast_total
        nutrients_broadcast_total.labels(tenant_id="test").inc()

    def test_histogram_observe(self):
        """Histograms can record observations."""
        from shared.metrics import routing_latency
        routing_latency.labels(tenant_id="test").observe(0.025)

    def test_gauge_set(self):
        """Gauges can be set."""
        from shared.metrics import active_agents
        active_agents.labels(tenant_id="test").set(42)


class TestAlertingRules:
    """Test alerting rules YAML configuration."""

    def test_alerts_file_exists(self):
        """Alert rules file exists."""
        alerts_path = os.path.join(
            os.path.dirname(__file__), '../../infra/prometheus/alerts.yml'
        )
        assert os.path.exists(alerts_path)

    def test_alerts_valid_yaml(self):
        """Alert rules are valid YAML."""
        alerts_path = os.path.join(
            os.path.dirname(__file__), '../../infra/prometheus/alerts.yml'
        )
        with open(alerts_path) as f:
            data = yaml.safe_load(f)
        assert 'groups' in data
        assert len(data['groups']) >= 2

    def test_critical_alerts_defined(self):
        """Critical alerts are defined."""
        alerts_path = os.path.join(
            os.path.dirname(__file__), '../../infra/prometheus/alerts.yml'
        )
        with open(alerts_path) as f:
            data = yaml.safe_load(f)

        alert_names = []
        for group in data['groups']:
            for rule in group['rules']:
                alert_names.append(rule['alert'])

        assert 'HighErrorRate' in alert_names
        assert 'HighLatencyP99' in alert_names
        assert 'ServiceDown' in alert_names

    def test_prometheus_config_references_alerts(self):
        """Prometheus config references alert rules file."""
        config_path = os.path.join(
            os.path.dirname(__file__), '../../infra/prometheus/prometheus.yml'
        )
        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert 'rule_files' in data
        assert 'alerts.yml' in data['rule_files']

    def test_prometheus_scrapes_reinforcement(self):
        """Prometheus config scrapes reinforcement service."""
        config_path = os.path.join(
            os.path.dirname(__file__), '../../infra/prometheus/prometheus.yml'
        )
        with open(config_path) as f:
            data = yaml.safe_load(f)

        job_names = [job['job_name'] for job in data['scrape_configs']]
        assert 'reinforcement' in job_names
        assert 'router' in job_names
