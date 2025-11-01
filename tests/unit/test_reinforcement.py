"""Unit tests for reinforcement learning engine."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/data_plane/reinforcement'))

# Import after path modification
from main import calculate_weight_delta, clamp_weight, ALPHA_POS, ALPHA_NEG, LAMBDA_DECAY, MIN_WEIGHT, MAX_WEIGHT


class TestReinforcementLearning:
    """Test reinforcement learning calculations."""

    def test_calculate_weight_delta_success(self):
        """Test weight delta calculation for successful outcome."""
        outcome_score = 1.0  # Complete success
        current_weight = 0.5

        delta = calculate_weight_delta(outcome_score, current_weight)

        # δ = 0.08 × 1.0 - 0.04 × 0.0 - 0.002 = 0.078
        expected = ALPHA_POS * 1.0 - ALPHA_NEG * 0.0 - LAMBDA_DECAY
        assert abs(delta - expected) < 0.001

    def test_calculate_weight_delta_failure(self):
        """Test weight delta calculation for failed outcome."""
        outcome_score = 0.0  # Complete failure
        current_weight = 0.5

        delta = calculate_weight_delta(outcome_score, current_weight)

        # δ = 0.08 × 0.0 - 0.04 × 1.0 - 0.002 = -0.042
        expected = ALPHA_POS * 0.0 - ALPHA_NEG * 1.0 - LAMBDA_DECAY
        assert abs(delta - expected) < 0.001
        assert delta < 0  # Should be negative for failure

    def test_calculate_weight_delta_partial(self):
        """Test weight delta for partial success."""
        outcome_score = 0.5  # 50% success
        current_weight = 0.5

        delta = calculate_weight_delta(outcome_score, current_weight)

        # δ = 0.08 × 0.5 - 0.04 × 0.5 - 0.002 = 0.018
        expected = ALPHA_POS * 0.5 - ALPHA_NEG * 0.5 - LAMBDA_DECAY
        assert abs(delta - expected) < 0.001

    def test_weight_strengthening(self):
        """Test that successful outcomes strengthen weights."""
        initial_weight = 0.5
        outcome_score = 0.9  # High success

        delta = calculate_weight_delta(outcome_score, initial_weight)

        assert delta > 0  # Should increase weight

    def test_weight_weakening(self):
        """Test that failed outcomes weaken weights."""
        initial_weight = 0.5
        outcome_score = 0.1  # Low success

        delta = calculate_weight_delta(outcome_score, initial_weight)

        assert delta < 0  # Should decrease weight

    def test_clamp_weight_min(self):
        """Test weight clamping at minimum."""
        assert clamp_weight(0.005) == MIN_WEIGHT
        assert clamp_weight(-0.1) == MIN_WEIGHT

    def test_clamp_weight_max(self):
        """Test weight clamping at maximum."""
        assert clamp_weight(2.0) == MAX_WEIGHT
        assert clamp_weight(5.0) == MAX_WEIGHT

    def test_clamp_weight_normal(self):
        """Test weight clamping for normal values."""
        assert clamp_weight(0.5) == 0.5
        assert clamp_weight(1.0) == 1.0

    def test_weight_evolution_series(self):
        """Test weight evolution over series of outcomes."""
        initial_weight = 0.5
        weight = initial_weight

        # Series of successes should strengthen
        for _ in range(5):
            delta = calculate_weight_delta(0.9, weight)
            weight = clamp_weight(weight + delta)

        assert weight > initial_weight  # Weight increased

        # Series of failures should weaken from current weight
        weight_after_success = weight
        for _ in range(10):
            delta = calculate_weight_delta(0.1, weight)
            weight = clamp_weight(weight + delta)

        assert weight < weight_after_success  # Weight decreased from peak

    def test_natural_decay(self):
        """Test that natural decay is always applied."""
        # Even with perfect success, decay is applied
        outcome_score = 1.0
        weight = 0.5

        delta = calculate_weight_delta(outcome_score, weight)

        # Delta should be slightly less than pure positive reinforcement
        pure_positive = ALPHA_POS * outcome_score
        assert delta < pure_positive
        assert delta == (pure_positive - LAMBDA_DECAY)
