"""
Unit tests for SDK models.
"""

import pytest
from datetime import datetime
from qilbee_mycelial_network.models import (
    Nutrient,
    Outcome,
    Sensitivity,
    Context,
    SearchRequest,
)


class TestNutrient:
    """Test Nutrient model."""

    def test_nutrient_creation(self):
        """Test creating a nutrient."""
        embedding = [0.1] * 1536

        nutrient = Nutrient.seed(
            summary="Test nutrient",
            embedding=embedding,
            snippets=["code snippet"],
            tool_hints=["tool.hint"],
            sensitivity=Sensitivity.INTERNAL,
        )

        assert nutrient.summary == "Test nutrient"
        assert len(nutrient.embedding) == 1536
        assert nutrient.sensitivity == Sensitivity.INTERNAL
        assert nutrient.current_hop == 0
        assert nutrient.max_hops == 3
        assert nutrient.id.startswith("nutr-")
        assert nutrient.trace_id.startswith("tr-")

    def test_nutrient_invalid_embedding_size(self):
        """Test that invalid embedding size raises error."""
        embedding = [0.1] * 100  # Wrong size

        with pytest.raises(ValueError, match="must be 1536-dimensional"):
            Nutrient.seed(
                summary="Test",
                embedding=embedding,
            )

    def test_nutrient_decrement_hop(self):
        """Test hop decrement."""
        embedding = [0.1] * 1536
        nutrient = Nutrient.seed(
            summary="Test",
            embedding=embedding,
            max_hops=3,
        )

        decremented = nutrient.decrement_hop()

        assert decremented.max_hops == 2
        assert decremented.current_hop == 1
        assert decremented.id == nutrient.id
        assert decremented.trace_id == nutrient.trace_id

    def test_nutrient_can_forward(self):
        """Test can_forward logic."""
        embedding = [0.1] * 1536
        nutrient = Nutrient.seed(
            summary="Test",
            embedding=embedding,
            max_hops=3,
            ttl_sec=180,
        )

        assert nutrient.can_forward() is True

        # Exhaust hops
        nutrient.max_hops = 0
        assert nutrient.can_forward() is False

    def test_nutrient_to_dict(self):
        """Test serialization to dict."""
        embedding = [0.1] * 1536
        nutrient = Nutrient.seed(
            summary="Test",
            embedding=embedding,
        )

        data = nutrient.to_dict()

        assert data["summary"] == "Test"
        assert data["sensitivity"] == "internal"
        assert len(data["embedding"]) == 1536
        assert "id" in data
        assert "trace_id" in data


class TestOutcome:
    """Test Outcome model."""

    def test_outcome_with_score(self):
        """Test creating outcome with score."""
        outcome = Outcome.with_score(0.85)

        assert outcome.score == 0.85
        assert outcome.metadata == {}

    def test_outcome_success(self):
        """Test success outcome."""
        outcome = Outcome.success()

        assert outcome.score == 1.0

    def test_outcome_failure(self):
        """Test failure outcome."""
        outcome = Outcome.failure()

        assert outcome.score == 0.0

    def test_outcome_partial(self):
        """Test partial outcome."""
        outcome = Outcome.partial(score=0.5)

        assert outcome.score == 0.5

    def test_outcome_invalid_score(self):
        """Test that invalid score raises error."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            Outcome.with_score(1.5)

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            Outcome.with_score(-0.1)

    def test_outcome_with_metadata(self):
        """Test outcome with metadata."""
        outcome = Outcome.with_score(
            0.75,
            task_type="optimization",
            execution_time_ms=1234,
        )

        assert outcome.score == 0.75
        assert outcome.metadata["task_type"] == "optimization"
        assert outcome.metadata["execution_time_ms"] == 1234


class TestContext:
    """Test Context model."""

    def test_context_from_dict(self):
        """Test creating context from dict."""
        data = {
            "trace_id": "tr-123",
            "contents": [{"agent_id": "agent-1", "data": "test"}],
            "source_agents": ["agent-1"],
            "quality_scores": [0.8],
            "metadata": {"window_ms": 300},
        }

        context = Context.from_dict(data)

        assert context.trace_id == "tr-123"
        assert len(context.contents) == 1
        assert len(context.source_agents) == 1
        assert context.metadata["window_ms"] == 300


class TestSearchRequest:
    """Test SearchRequest model."""

    def test_search_request_creation(self):
        """Test creating search request."""
        embedding = [0.1] * 1536

        request = SearchRequest(
            embedding=embedding,
            top_k=10,
            filters={"kind": "insight"},
        )

        assert len(request.embedding) == 1536
        assert request.top_k == 10
        assert request.filters["kind"] == "insight"

    def test_search_request_to_dict(self):
        """Test serialization."""
        embedding = [0.1] * 1536

        request = SearchRequest(
            embedding=embedding,
            top_k=5,
        )

        data = request.to_dict()

        assert len(data["embedding"]) == 1536
        assert data["top_k"] == 5
        assert data["filters"] == {}


class TestSensitivity:
    """Test Sensitivity enum."""

    def test_sensitivity_values(self):
        """Test sensitivity enum values."""
        assert Sensitivity.PUBLIC.value == "public"
        assert Sensitivity.INTERNAL.value == "internal"
        assert Sensitivity.CONFIDENTIAL.value == "confidential"
        assert Sensitivity.SECRET.value == "secret"

    def test_sensitivity_comparison(self):
        """Test sensitivity comparison."""
        assert Sensitivity.PUBLIC != Sensitivity.SECRET
        assert Sensitivity.INTERNAL == Sensitivity.INTERNAL
