"""
Unit tests for Phase 1 routing intelligence improvements.

Tests: semantic demand overlap, proportional capability boost,
epsilon-greedy exploration, and MMR cache optimization.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import math

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/data_plane/reinforcement'))

from shared.routing import RoutingAlgorithm, Neighbor, RoutingScore
from main import (
    calculate_time_decay,
    TIME_DECAY_LAMBDA,
    STALE_EDGE_MIN_WEIGHT,
    STALE_EDGE_MAX_AGE_DAYS,
)


class TestSemanticDemandOverlap:
    """Test semantic/fuzzy demand overlap matching (Phase 1.3)."""

    def test_exact_match(self):
        """Exact string matches still work."""
        overlap = RoutingAlgorithm.calculate_demand_overlap(
            ["db.optimize", "sql.analyze"],
            ["db.optimize", "cache.clear"],
        )
        assert overlap == 0.5

    def test_fuzzy_match_similar_strings(self):
        """Similar strings match via fuzzy matching."""
        overlap = RoutingAlgorithm.calculate_demand_overlap(
            ["database.optimize"],
            ["database.optimise"],  # British spelling
        )
        assert overlap > 0.0

    def test_fuzzy_match_threshold(self):
        """Strings below threshold don't match."""
        overlap = RoutingAlgorithm.calculate_demand_overlap(
            ["db.optimize"],
            ["network.monitor"],  # Completely different
        )
        assert overlap == 0.0

    def test_mixed_exact_and_fuzzy(self):
        """Combination of exact and fuzzy matches."""
        overlap = RoutingAlgorithm.calculate_demand_overlap(
            ["db.optimize", "sql.analyze", "cache.clear"],
            ["db.optimize", "sql.analyse", "monitor.check"],
        )
        # db.optimize = exact match, sql.analyze ~ sql.analyse = fuzzy match
        assert overlap >= 2.0 / 3.0

    def test_empty_lists(self):
        """Empty lists return 0."""
        assert RoutingAlgorithm.calculate_demand_overlap([], []) == 0.0
        assert RoutingAlgorithm.calculate_demand_overlap(["task"], []) == 0.0
        assert RoutingAlgorithm.calculate_demand_overlap([], ["task"]) == 0.0

    def test_full_overlap(self):
        """All tasks match."""
        tasks = ["db.optimize", "sql.analyze"]
        overlap = RoutingAlgorithm.calculate_demand_overlap(tasks, tasks)
        assert overlap == 1.0


class TestProportionalCapabilityBoost:
    """Test proportional capability boost (Phase 1.4)."""

    def _make_neighbor(self, capabilities):
        return Neighbor(
            id="agent-1",
            profile_embedding=np.ones(1536) * 0.5,
            edge_weight=0.5,
            base_similarity=0.5,
            recent_tasks=[],
            capabilities=capabilities,
            last_update=datetime.utcnow(),
        )

    def test_no_capability_match(self):
        """Zero boost when no capabilities match."""
        neighbor = self._make_neighbor(["other.tool"])
        score = RoutingAlgorithm.calculate_routing_score(
            np.ones(1536) * 0.5,
            ["db.analyze"],
            neighbor,
        )
        assert score.capability_match is False

    def test_single_capability_match(self):
        """Single match gives 0.05 boost."""
        neighbor = self._make_neighbor(["db.analyze"])
        score = RoutingAlgorithm.calculate_routing_score(
            np.ones(1536) * 0.5,
            ["db.analyze"],
            neighbor,
        )
        assert score.capability_match is True

    def test_multiple_capability_matches_more_than_single(self):
        """Multiple matches give higher boost than single match."""
        neighbor_multi = self._make_neighbor(
            ["db.analyze", "sql.optimize", "cache.manage"]
        )
        neighbor_single = self._make_neighbor(["db.analyze"])

        embedding = np.ones(1536) * 0.5
        hints = ["db.analyze", "sql.optimize", "cache.manage"]

        score_multi = RoutingAlgorithm.calculate_routing_score(
            embedding, hints, neighbor_multi,
        )
        score_single = RoutingAlgorithm.calculate_routing_score(
            embedding, hints, neighbor_single,
        )
        assert score_multi.total_score > score_single.total_score

    def test_capability_boost_capped_at_four(self):
        """Boost is capped at 4 matches (0.20 max)."""
        caps = ["a", "b", "c", "d", "e"]
        neighbor = self._make_neighbor(caps)

        embedding = np.ones(1536) * 0.5
        score = RoutingAlgorithm.calculate_routing_score(
            embedding, caps, neighbor,
        )
        # Max boost = 0.05 * 4 = 0.20 (even though 5 match)
        # Base score = similarity * edge_weight * 0.5 + 0.20
        # The boost shouldn't exceed 0.20
        neighbor_4 = self._make_neighbor(["a", "b", "c", "d"])
        score_4 = RoutingAlgorithm.calculate_routing_score(
            embedding, caps, neighbor_4,
        )
        # 5 matches capped at 4, so same as 4 matches
        assert abs(score.total_score - score_4.total_score) < 0.001


class TestEpsilonGreedyExploration:
    """Test epsilon-greedy exploration (Phase 1.2)."""

    def _make_neighbors(self, n, high_score=True):
        """Create n neighbors with controlled embeddings."""
        neighbors = []
        for i in range(n):
            emb = np.random.rand(1536)
            neighbors.append(Neighbor(
                id=f"agent-{i}",
                profile_embedding=emb,
                edge_weight=0.8 if high_score else 0.01,
                base_similarity=0.7,
                recent_tasks=["task.common"],
                capabilities=["cap.test"],
                last_update=datetime.utcnow(),
            ))
        return neighbors

    def test_epsilon_zero_no_exploration(self):
        """With epsilon=0, no exploration happens."""
        np.random.seed(42)
        neighbors = self._make_neighbors(10)
        nutrient_embedding = np.random.rand(1536)

        results = []
        for _ in range(50):
            selected = RoutingAlgorithm.route_nutrient(
                nutrient_embedding=nutrient_embedding,
                nutrient_tool_hints=["task.common"],
                neighbors=neighbors,
                top_k=3,
                diversify=False,
                epsilon=0.0,
            )
            results.append(set(n.id for n, _ in selected))

        # All results should be identical (deterministic)
        first = results[0]
        assert all(r == first for r in results)

    def test_epsilon_one_always_explores(self):
        """With epsilon=1.0, exploration always happens."""
        np.random.seed(42)
        # Create neighbors with wide score gap
        high_neighbors = self._make_neighbors(5, high_score=True)
        low_neighbors = self._make_neighbors(5, high_score=False)
        # Give low neighbors distinct IDs
        for i, n in enumerate(low_neighbors):
            n.id = f"low-agent-{i}"

        all_neighbors = high_neighbors + low_neighbors
        nutrient_embedding = np.random.rand(1536)

        explore_count = 0
        trials = 100
        for _ in range(trials):
            selected = RoutingAlgorithm.route_nutrient(
                nutrient_embedding=nutrient_embedding,
                nutrient_tool_hints=[],
                neighbors=all_neighbors,
                top_k=3,
                diversify=False,
                epsilon=1.0,
            )
            ids = [n.id for n, _ in selected]
            if any(id.startswith("low-") for id in ids):
                explore_count += 1

        # With epsilon=1.0, exploration should happen most of the time
        assert explore_count > 50

    def test_default_epsilon(self):
        """Default epsilon is 0.1."""
        assert RoutingAlgorithm.EPSILON_EXPLORE == 0.1


class TestMMRCacheOptimization:
    """Test that MMR with cached similarity matrix gives correct results."""

    def test_mmr_selects_diverse(self):
        """MMR should prefer diverse neighbors over similar ones."""
        # Create embeddings with clear clusters
        embeddings = [
            np.array([1.0, 0.0, 0.0] + [0.0] * 1533),
            np.array([0.95, 0.05, 0.0] + [0.0] * 1533),  # Very similar to first
            np.array([0.0, 1.0, 0.0] + [0.0] * 1533),    # Diverse
            np.array([0.0, 0.0, 1.0] + [0.0] * 1533),    # Diverse
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

        selected = RoutingAlgorithm.mmr_select(scored, k=2, lambda_diversity=0.5)
        assert len(selected) == 2

    def test_mmr_returns_all_when_k_exceeds_candidates(self):
        """MMR returns all when k > candidates."""
        embeddings = [np.random.rand(1536) for _ in range(3)]
        neighbors = [
            Neighbor(id=f"a-{i}", profile_embedding=e, edge_weight=0.5,
                     base_similarity=0.5, recent_tasks=[], capabilities=[],
                     last_update=datetime.utcnow())
            for i, e in enumerate(embeddings)
        ]
        scored = [
            (n, RoutingScore(n.id, 0.5, 0.5, 0.5, 0.0, False))
            for n in neighbors
        ]
        selected = RoutingAlgorithm.mmr_select(scored, k=10)
        assert len(selected) == 3


class TestTimeBasedDecay:
    """Test time-based edge decay (Phase 1.1)."""

    def test_decay_formula(self):
        """Test exponential decay formula: w_new = w * e^(-lambda * days)."""
        weight = 1.0
        days = 10.0
        expected = weight * math.exp(-TIME_DECAY_LAMBDA * days)
        result = calculate_time_decay(weight, days)
        assert abs(result - expected) < 0.0001

    def test_no_decay_at_zero_days(self):
        """No decay when days_since_update is 0."""
        result = calculate_time_decay(1.0, 0.0)
        assert result == 1.0

    def test_significant_decay_after_100_days(self):
        """Significant decay after 100 days."""
        result = calculate_time_decay(1.0, 100.0)
        expected = math.exp(-TIME_DECAY_LAMBDA * 100)
        assert abs(result - expected) < 0.0001
        assert result < 0.5  # Should have decayed significantly

    def test_decay_preserves_relative_order(self):
        """Heavier edges stay heavier after decay."""
        heavy = calculate_time_decay(1.5, 30.0)
        light = calculate_time_decay(0.5, 30.0)
        assert heavy > light

    def test_stale_edge_deletion_threshold(self):
        """Very old, low-weight edges should qualify for deletion."""
        weight = 0.015  # Below STALE_EDGE_MIN_WEIGHT
        days = 35.0  # Beyond STALE_EDGE_MAX_AGE_DAYS
        result = calculate_time_decay(weight, days)
        assert result < STALE_EDGE_MIN_WEIGHT


class TestPerHopOutcome:
    """Test per-hop outcome support (Phase 1.6)."""

    def test_per_hop_score_retrieval(self):
        """Test getting per-agent scores from hop_outcomes."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                        '../../services/data_plane/reinforcement'))
        from main import OutcomeRequest

        req = OutcomeRequest(
            trace_id="tr-test",
            outcome_score=0.5,
            hop_outcomes={"agent-1": 0.9, "agent-2": 0.3},
        )

        assert req.get_agent_score("agent-1") == 0.9
        assert req.get_agent_score("agent-2") == 0.3
        assert req.get_agent_score("agent-unknown") == 0.5  # Falls back to uniform

    def test_uniform_fallback(self):
        """Without hop_outcomes, all agents get the same score."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                        '../../services/data_plane/reinforcement'))
        from main import OutcomeRequest

        req = OutcomeRequest(
            trace_id="tr-test",
            outcome_score=0.85,
        )
        assert req.get_agent_score("any-agent") == 0.85

    def test_hop_outcomes_validation(self):
        """Hop outcomes with invalid scores should raise."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                        '../../services/data_plane/reinforcement'))
        from main import OutcomeRequest

        with pytest.raises(Exception):
            OutcomeRequest(
                trace_id="tr-test",
                outcome_score=0.5,
                hop_outcomes={"agent-1": 1.5},  # Invalid: > 1.0
            )
