"""
Unit tests for routing algorithm.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

from shared.routing import (
    RoutingAlgorithm,
    Neighbor,
    RoutingScore,
    QuotaChecker,
    TTLChecker,
)


class TestRoutingAlgorithm:
    """Test routing algorithm."""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])

        similarity = RoutingAlgorithm.cosine_similarity(a, b)

        # Identical vectors should have similarity ~1.0
        assert 0.99 <= similarity <= 1.0

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity with orthogonal vectors."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])

        similarity = RoutingAlgorithm.cosine_similarity(a, b)

        # Orthogonal vectors should have similarity ~0.5 (normalized to [0,1])
        assert 0.4 <= similarity <= 0.6

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity with opposite vectors."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])

        similarity = RoutingAlgorithm.cosine_similarity(a, b)

        # Opposite vectors should have similarity ~0.0
        assert 0.0 <= similarity <= 0.1

    def test_demand_overlap(self):
        """Test demand overlap calculation."""
        nutrient_tasks = ["db.optimize", "sql.analyze"]
        neighbor_tasks = ["db.optimize", "cache.clear", "monitor.check"]

        overlap = RoutingAlgorithm.calculate_demand_overlap(
            nutrient_tasks,
            neighbor_tasks,
        )

        # 1 out of 2 tasks overlap
        assert overlap == 0.5

    def test_demand_overlap_no_match(self):
        """Test demand overlap with no matches."""
        nutrient_tasks = ["db.optimize"]
        neighbor_tasks = ["cache.clear"]

        overlap = RoutingAlgorithm.calculate_demand_overlap(
            nutrient_tasks,
            neighbor_tasks,
        )

        assert overlap == 0.0

    def test_demand_overlap_empty(self):
        """Test demand overlap with empty lists."""
        overlap = RoutingAlgorithm.calculate_demand_overlap([], [])

        assert overlap == 0.0

    def test_calculate_routing_score(self):
        """Test routing score calculation."""
        nutrient_embedding = np.random.rand(1536)
        neighbor_embedding = np.random.rand(1536)

        neighbor = Neighbor(
            id="agent-1",
            profile_embedding=neighbor_embedding,
            edge_weight=0.8,
            base_similarity=0.7,
            recent_tasks=["db.optimize"],
            capabilities=["db.analyze", "sql.optimize"],
            last_update=datetime.utcnow(),
        )

        score = RoutingAlgorithm.calculate_routing_score(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=["db.optimize"],
            neighbor=neighbor,
        )

        assert isinstance(score, RoutingScore)
        assert score.neighbor_id == "agent-1"
        assert 0.0 <= score.total_score <= 2.0
        assert 0.0 <= score.similarity <= 1.0
        assert score.edge_weight == 0.8

    def test_routing_score_capability_boost(self):
        """Test that capability match adds boost."""
        nutrient_embedding = np.ones(1536) * 0.5
        neighbor_embedding = np.ones(1536) * 0.5

        neighbor = Neighbor(
            id="agent-1",
            profile_embedding=neighbor_embedding,
            edge_weight=0.5,
            base_similarity=0.5,
            recent_tasks=[],
            capabilities=["db.analyze"],
            last_update=datetime.utcnow(),
        )

        # With capability match
        score_with = RoutingAlgorithm.calculate_routing_score(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=["db.analyze"],
            neighbor=neighbor,
        )

        # Without capability match
        score_without = RoutingAlgorithm.calculate_routing_score(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=["other.tool"],
            neighbor=neighbor,
        )

        assert score_with.capability_match is True
        assert score_without.capability_match is False
        assert score_with.total_score > score_without.total_score

    def test_route_nutrient(self):
        """Test routing nutrient to neighbors."""
        nutrient_embedding = np.random.rand(1536)

        neighbors = [
            Neighbor(
                id=f"agent-{i}",
                profile_embedding=np.random.rand(1536),
                edge_weight=0.5 + (i * 0.1),
                base_similarity=0.5,
                recent_tasks=["task.common"],
                capabilities=["cap.test"],
                last_update=datetime.utcnow(),
            )
            for i in range(10)
        ]

        selected = RoutingAlgorithm.route_nutrient(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=["task.common"],
            neighbors=neighbors,
            top_k=3,
            diversify=False,
        )

        # Should select top 3
        assert len(selected) <= 3

        # Results should be (Neighbor, RoutingScore) tuples
        for neighbor, score in selected:
            assert isinstance(neighbor, Neighbor)
            assert isinstance(score, RoutingScore)

    def test_route_nutrient_with_diversity(self):
        """Test routing with MMR diversity."""
        nutrient_embedding = np.random.rand(1536)

        # Create similar neighbors (clustering)
        base_embedding = np.random.rand(1536)
        neighbors = [
            Neighbor(
                id=f"agent-{i}",
                profile_embedding=base_embedding + np.random.rand(1536) * 0.1,
                edge_weight=0.8,
                base_similarity=0.7,
                recent_tasks=[],
                capabilities=[],
                last_update=datetime.utcnow(),
            )
            for i in range(10)
        ]

        selected = RoutingAlgorithm.route_nutrient(
            nutrient_embedding=nutrient_embedding,
            nutrient_tool_hints=[],
            neighbors=neighbors,
            top_k=5,
            diversify=True,
        )

        assert len(selected) <= 5

    def test_mmr_select(self):
        """Test MMR diversity selection."""
        # Create embeddings with varying similarity
        embeddings = [
            np.array([1.0, 0.0, 0.0] + [0.0] * 1533),
            np.array([0.9, 0.1, 0.0] + [0.0] * 1533),  # Very similar to first
            np.array([0.0, 1.0, 0.0] + [0.0] * 1533),  # Diverse
            np.array([0.0, 0.0, 1.0] + [0.0] * 1533),  # Diverse
        ]

        neighbors = [
            Neighbor(
                id=f"agent-{i}",
                profile_embedding=emb,
                edge_weight=0.8,
                base_similarity=0.5,
                recent_tasks=[],
                capabilities=[],
                last_update=datetime.utcnow(),
            )
            for i, emb in enumerate(embeddings)
        ]

        # Create scores (all high relevance)
        scored = [
            (n, RoutingScore(
                neighbor_id=n.id,
                total_score=0.9,
                similarity=0.9,
                edge_weight=0.8,
                demand_overlap=0.5,
                capability_match=False,
            ))
            for n in neighbors
        ]

        selected = RoutingAlgorithm.mmr_select(
            scored_neighbors=scored,
            k=2,
            lambda_diversity=0.5,
        )

        # Should select diverse neighbors
        assert len(selected) == 2


class TestQuotaChecker:
    """Test quota checking."""

    def test_within_quota(self):
        """Test quota checking when within limits."""
        result = QuotaChecker.within_quota(
            nutrient_cost=5,
            neighbor_quota={"kb_hour": 1000, "msg_min": 10},
            current_usage={"kb_hour": 100, "msg_min": 2},
        )

        assert result is True

    def test_exceeds_quota(self):
        """Test quota checking when exceeds limits."""
        result = QuotaChecker.within_quota(
            nutrient_cost=500,
            neighbor_quota={"kb_hour": 1000, "msg_min": 10},
            current_usage={"kb_hour": 600, "msg_min": 2},
        )

        assert result is False

    def test_no_quota_limits(self):
        """Test when no quota limits set."""
        result = QuotaChecker.within_quota(
            nutrient_cost=5,
            neighbor_quota={},
            current_usage={},
        )

        assert result is True


class TestTTLChecker:
    """Test TTL checking."""

    def test_can_forward_valid(self):
        """Test can forward when valid."""
        result = TTLChecker.can_forward(
            nutrient_created_at=datetime.utcnow(),
            nutrient_ttl_sec=300,
            nutrient_max_hops=3,
        )

        assert result is True

    def test_can_forward_expired(self):
        """Test cannot forward when expired."""
        result = TTLChecker.can_forward(
            nutrient_created_at=datetime.utcnow() - timedelta(seconds=400),
            nutrient_ttl_sec=300,
            nutrient_max_hops=3,
        )

        assert result is False

    def test_can_forward_no_hops(self):
        """Test cannot forward with no hops remaining."""
        result = TTLChecker.can_forward(
            nutrient_created_at=datetime.utcnow(),
            nutrient_ttl_sec=300,
            nutrient_max_hops=0,
        )

        assert result is False
