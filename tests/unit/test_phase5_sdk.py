"""
Unit tests for Phase 5 SDK completeness.

Tests: control plane methods, new model fields, get_usage implementation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../sdk'))

from qilbee_mycelial_network.models import (
    Outcome, Nutrient, Sensitivity, SearchRequest, Context,
)
from qilbee_mycelial_network.client import MycelialClient
from qilbee_mycelial_network.settings import QMNSettings


class TestOutcomeHopScores:
    """Test per-hop outcome support in SDK models (Phase 5.3)."""

    def test_outcome_with_hop_scores(self):
        """Create outcome with per-agent hop scores."""
        outcome = Outcome.with_hop_scores(
            score=0.8,
            hop_outcomes={"agent-1": 0.9, "agent-2": 0.6},
        )
        assert outcome.score == 0.8
        assert outcome.hop_outcomes == {"agent-1": 0.9, "agent-2": 0.6}

    def test_outcome_hop_scores_to_dict(self):
        """Hop scores are included in serialized output."""
        outcome = Outcome.with_hop_scores(
            score=0.7,
            hop_outcomes={"agent-1": 0.9},
        )
        d = outcome.to_dict()
        assert "hop_outcomes" in d
        assert d["hop_outcomes"]["agent-1"] == 0.9

    def test_outcome_without_hop_scores(self):
        """Regular outcomes don't include hop_outcomes."""
        outcome = Outcome.success()
        d = outcome.to_dict()
        assert "hop_outcomes" not in d

    def test_outcome_hop_scores_validation(self):
        """Hop scores must be 0.0-1.0."""
        with pytest.raises(ValueError):
            Outcome.with_hop_scores(
                score=0.5,
                hop_outcomes={"agent-1": 1.5},
            )

    def test_backward_compatible_outcome(self):
        """Existing outcome methods still work."""
        assert Outcome.success().score == 1.0
        assert Outcome.failure().score == 0.0
        assert Outcome.partial(0.5).score == 0.5
        assert Outcome.with_score(0.7).score == 0.7


class TestSearchRequestUserFilter:
    """Test user_filter support in SearchRequest (Phase 5.3)."""

    def test_search_request_with_user_filter(self):
        """SearchRequest supports user_filter."""
        req = SearchRequest(
            embedding=[0.1] * 1536,
            top_k=10,
            user_filter={"agent_id": "agent-1", "kind": "insight"},
        )
        d = req.to_dict()
        assert "user_filter" in d
        assert d["user_filter"]["agent_id"] == "agent-1"

    def test_search_request_without_user_filter(self):
        """SearchRequest works without user_filter."""
        req = SearchRequest(embedding=[0.1] * 1536)
        d = req.to_dict()
        assert "user_filter" not in d


class TestSDKControlPlaneMethods:
    """Test that control plane methods exist on MycelialClient (Phase 5.1)."""

    def test_client_has_tenant_methods(self):
        """Client has tenant CRUD methods."""
        assert hasattr(MycelialClient, 'create_tenant')
        assert hasattr(MycelialClient, 'get_tenant')
        assert hasattr(MycelialClient, 'list_tenants')
        assert hasattr(MycelialClient, 'update_tenant')
        assert hasattr(MycelialClient, 'delete_tenant')

    def test_client_has_key_methods(self):
        """Client has key management methods."""
        assert hasattr(MycelialClient, 'create_key')
        assert hasattr(MycelialClient, 'validate_key')
        assert hasattr(MycelialClient, 'list_keys')
        assert hasattr(MycelialClient, 'revoke_key')

    def test_client_has_policy_methods(self):
        """Client has policy management methods."""
        assert hasattr(MycelialClient, 'evaluate_policy')
        assert hasattr(MycelialClient, 'create_policy')
        assert hasattr(MycelialClient, 'list_policies')

    def test_client_has_get_usage(self):
        """Client has get_usage method (no longer raises NotImplementedError)."""
        assert hasattr(MycelialClient, 'get_usage')
        # Verify it's no longer raising NotImplementedError by checking the source
        import inspect
        source = inspect.getsource(MycelialClient.get_usage)
        assert "NotImplementedError" not in source


class TestContextModel:
    """Test Context model."""

    def test_context_from_dict(self):
        """Context can be created from API response."""
        data = {
            "trace_id": "tr-abc123",
            "contents": [{"data": "test"}],
            "source_agents": ["agent-1"],
            "quality_scores": [0.9],
            "metadata": {"diversified": True},
        }
        ctx = Context.from_dict(data)
        assert ctx.trace_id == "tr-abc123"
        assert len(ctx.contents) == 1
        assert ctx.metadata["diversified"] is True


class TestNutrientModel:
    """Test Nutrient model enhancements."""

    def test_nutrient_seed_with_source_agent(self):
        """Nutrient seed supports source_agent_id."""
        n = Nutrient.seed(
            summary="test",
            embedding=[0.1] * 1536,
            source_agent_id="my-agent",
        )
        assert n.source_agent_id == "my-agent"
        d = n.to_dict()
        assert d["source_agent_id"] == "my-agent"
