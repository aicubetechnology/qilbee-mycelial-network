"""
Unit tests for error handling across the system.

Tests: invalid inputs, malformed requests, edge cases.
"""

import pytest
import numpy as np
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../sdk'))

from shared.routing import RoutingAlgorithm, Neighbor, RoutingScore
from shared.security import EncryptionManager, AuditSigner
from qilbee_mycelial_network.models import Nutrient, Outcome, Sensitivity, SearchRequest


class TestRoutingErrorHandling:
    """Test routing error cases."""

    def test_wrong_embedding_dimension(self):
        """Routing rejects wrong embedding dimensions."""
        with pytest.raises(ValueError, match="1536"):
            RoutingAlgorithm.route_nutrient(
                nutrient_embedding=np.random.rand(512),
                nutrient_tool_hints=[],
                neighbors=[],
            )

    def test_cosine_similarity_dimension_mismatch(self):
        """Cosine similarity rejects mismatched dimensions."""
        with pytest.raises(ValueError, match="dimensions must match"):
            RoutingAlgorithm.cosine_similarity(
                np.array([1.0, 0.0]),
                np.array([1.0, 0.0, 0.0]),
            )

    def test_cosine_similarity_zero_vectors(self):
        """Zero vectors return 0 similarity."""
        result = RoutingAlgorithm.cosine_similarity(
            np.zeros(3),
            np.zeros(3),
        )
        assert result == 0.0

    def test_empty_neighbors(self):
        """Routing with no neighbors returns empty."""
        selected = RoutingAlgorithm.route_nutrient(
            nutrient_embedding=np.random.rand(1536),
            nutrient_tool_hints=["test"],
            neighbors=[],
        )
        assert selected == []

    def test_mmr_empty_k(self):
        """MMR with k=0 returns empty."""
        result = RoutingAlgorithm.mmr_select([], k=0)
        assert result == []

    def test_routing_high_threshold_filters_all(self):
        """Very high threshold filters all neighbors."""
        neighbors = [
            Neighbor(
                id="agent-1",
                profile_embedding=np.random.rand(1536),
                edge_weight=0.1,
                base_similarity=0.1,
                recent_tasks=[],
                capabilities=[],
                last_update=datetime.utcnow(),
            )
        ]
        selected = RoutingAlgorithm.route_nutrient(
            nutrient_embedding=np.random.rand(1536),
            nutrient_tool_hints=[],
            neighbors=neighbors,
            threshold=100.0,  # Very high threshold
        )
        assert len(selected) == 0


class TestNutrientValidation:
    """Test Nutrient model validation."""

    def test_wrong_embedding_dimension(self):
        """Nutrient rejects wrong embedding size."""
        with pytest.raises(ValueError, match="1536"):
            Nutrient.seed(
                summary="test",
                embedding=[0.1] * 100,
            )

    def test_nutrient_expiration(self):
        """Nutrient TTL expiration detection."""
        n = Nutrient.seed(
            summary="test",
            embedding=[0.1] * 1536,
            ttl_sec=0,
        )
        # With 0 TTL, should be expired almost immediately
        import time
        time.sleep(0.01)
        assert n.is_expired() is True

    def test_nutrient_can_forward(self):
        """Nutrient forwarding check."""
        n = Nutrient.seed(
            summary="test",
            embedding=[0.1] * 1536,
            max_hops=3,
            ttl_sec=300,
        )
        assert n.can_forward() is True

    def test_nutrient_no_hops_cannot_forward(self):
        """Nutrient with 0 hops cannot forward."""
        n = Nutrient.seed(
            summary="test",
            embedding=[0.1] * 1536,
            max_hops=0,
        )
        assert n.can_forward() is False

    def test_nutrient_decrement_hop(self):
        """Decrementing hops works correctly."""
        n = Nutrient.seed(
            summary="test",
            embedding=[0.1] * 1536,
            max_hops=3,
        )
        forwarded = n.decrement_hop()
        assert forwarded.max_hops == 2
        assert forwarded.current_hop == 1
        assert forwarded.id == n.id


class TestOutcomeValidation:
    """Test Outcome model validation."""

    def test_score_below_zero(self):
        """Score below 0 raises ValueError."""
        with pytest.raises(ValueError):
            Outcome.with_score(-0.1)

    def test_score_above_one(self):
        """Score above 1 raises ValueError."""
        with pytest.raises(ValueError):
            Outcome.with_score(1.1)

    def test_success_score(self):
        """Success has score 1.0."""
        assert Outcome.success().score == 1.0

    def test_failure_score(self):
        """Failure has score 0.0."""
        assert Outcome.failure().score == 0.0

    def test_partial_default(self):
        """Partial default is 0.5."""
        assert Outcome.partial().score == 0.5

    def test_outcome_with_metadata(self):
        """Outcome can carry metadata."""
        o = Outcome.with_score(0.7, reason="good performance")
        assert o.metadata["reason"] == "good performance"


class TestEncryptionErrorHandling:
    """Test encryption error cases."""

    def test_decrypt_empty_data(self):
        """Decrypting too-short data raises ValueError."""
        mgr = EncryptionManager()
        with pytest.raises(ValueError, match="too short"):
            mgr.decrypt(b"")

    def test_decrypt_random_data(self):
        """Decrypting random data fails gracefully."""
        mgr = EncryptionManager()
        with pytest.raises(Exception):
            mgr.decrypt(os.urandom(100))

    def test_encrypt_empty_string(self):
        """Encrypting empty bytes works."""
        mgr = EncryptionManager()
        encrypted = mgr.encrypt(b"")
        assert mgr.decrypt(encrypted) == b""


class TestSearchRequestValidation:
    """Test SearchRequest model."""

    def test_to_dict(self):
        """SearchRequest serialization."""
        req = SearchRequest(
            embedding=[0.1] * 1536,
            top_k=5,
            filters={"kind": "insight"},
        )
        d = req.to_dict()
        assert d["top_k"] == 5
        assert d["filters"]["kind"] == "insight"
        assert len(d["embedding"]) == 1536

    def test_defaults(self):
        """Default values."""
        req = SearchRequest(embedding=[0.1] * 1536)
        assert req.top_k == 10
        assert req.filters is None
