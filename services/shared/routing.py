"""
Core routing algorithm for Qilbee Mycelial Network.

Implements gradient-based routing with embedding similarity,
edge weight reinforcement, MMR diversity selection,
epsilon-greedy exploration, and semantic demand matching.
"""

import numpy as np
import random
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher


@dataclass
class Neighbor:
    """Represents a network neighbor with routing metadata."""

    id: str
    profile_embedding: np.ndarray  # 1536-dim
    edge_weight: float  # 0.01 to 1.5
    base_similarity: float  # 0.0 to 1.0
    recent_tasks: List[str]
    capabilities: List[str]
    last_update: datetime


@dataclass
class RoutingScore:
    """Routing score with breakdown for debugging."""

    neighbor_id: str
    total_score: float
    similarity: float
    edge_weight: float
    demand_overlap: float
    capability_match: bool


class RoutingAlgorithm:
    """
    Core routing algorithm for nutrient propagation.

    Combines multiple signals:
    1. Cosine similarity between nutrient and agent embeddings
    2. Learned edge weights from reinforcement
    3. Recent task demand overlap
    4. Capability matching
    """

    # Routing thresholds
    THRESHOLD_MIN = 0.15  # Minimum score to consider routing
    CAPABILITY_BOOST_PER_MATCH = 0.05  # Boost per matching capability
    CAPABILITY_BOOST_MAX_MATCHES = 4  # Maximum matches counted for boost
    TOP_K = 3  # Default number of neighbors to route to

    # MMR diversity parameter
    LAMBDA_DIVERSITY = 0.5  # 0=pure relevance, 1=pure diversity

    # Exploration-Exploitation (epsilon-greedy)
    EPSILON_EXPLORE = 0.1  # Probability of random exploration

    # Semantic demand matching
    FUZZY_MATCH_THRESHOLD = 0.7  # Levenshtein ratio threshold for fuzzy matching

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity (-1 to 1, normalized to 0 to 1)
        """
        if len(a) != len(b):
            raise ValueError(f"Vector dimensions must match: {len(a)} != {len(b)}")

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        # Normalize from [-1, 1] to [0, 1]
        similarity = (dot_product / (norm_a * norm_b) + 1.0) / 2.0
        return float(np.clip(similarity, 0.0, 1.0))

    @staticmethod
    def _fuzzy_match(a: str, b: str) -> float:
        """
        Calculate fuzzy string similarity using SequenceMatcher.

        Args:
            a: First string
            b: Second string

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @classmethod
    def calculate_demand_overlap(
        cls,
        nutrient_tasks: List[str],
        neighbor_tasks: List[str],
        time_decay_hours: float = 24.0,
    ) -> float:
        """
        Calculate recent task demand overlap with semantic matching.

        Uses exact match first, then falls back to fuzzy string matching
        (Levenshtein ratio > 0.7) to catch semantically similar tasks
        like "db.optimize" vs "database.optimize".

        Args:
            nutrient_tasks: Task types/tags from nutrient
            neighbor_tasks: Recent tasks completed by neighbor
            time_decay_hours: Time window for relevance

        Returns:
            Overlap score (0.0 to 1.0)
        """
        if not nutrient_tasks or not neighbor_tasks:
            return 0.0

        nutrient_set = set(nutrient_tasks)
        total = len(nutrient_set)

        if total == 0:
            return 0.0

        # Count matches: exact first, then fuzzy
        matched = 0
        for n_task in nutrient_set:
            if n_task in neighbor_tasks:
                matched += 1
                continue
            # Fuzzy matching fallback
            for nb_task in neighbor_tasks:
                if cls._fuzzy_match(n_task, nb_task) >= cls.FUZZY_MATCH_THRESHOLD:
                    matched += 1
                    break

        return float(matched / total)

    @classmethod
    def calculate_routing_score(
        cls,
        nutrient_embedding: np.ndarray,
        nutrient_tool_hints: List[str],
        neighbor: Neighbor,
    ) -> RoutingScore:
        """
        Calculate routing score for a neighbor.

        Combines similarity, edge weight, demand signals, and proportional
        capability boost.

        Args:
            nutrient_embedding: Nutrient embedding vector
            nutrient_tool_hints: Tool hints from nutrient
            neighbor: Neighbor agent data

        Returns:
            RoutingScore with breakdown
        """
        # 1. Semantic similarity
        similarity = cls.cosine_similarity(
            nutrient_embedding,
            neighbor.profile_embedding,
        )

        # 2. Recent task overlap with semantic matching
        demand_overlap = cls.calculate_demand_overlap(
            nutrient_tool_hints,
            neighbor.recent_tasks,
        )

        # 3. Proportional capability matching
        matching_count = sum(
            1 for tool in nutrient_tool_hints
            if tool in neighbor.capabilities
        )
        capability_match = matching_count > 0

        # Proportional boost: 0.05 per match, max 4 matches = max 0.20
        capability_boost = cls.CAPABILITY_BOOST_PER_MATCH * min(
            matching_count, cls.CAPABILITY_BOOST_MAX_MATCHES
        )

        # 4. Combined score
        # Formula: similarity * edge_weight * (0.5 + 0.5 * demand) + capability_boost
        base_score = similarity * neighbor.edge_weight * (0.5 + 0.5 * demand_overlap)
        base_score += capability_boost

        total_score = float(np.clip(base_score, 0.0, 2.0))

        return RoutingScore(
            neighbor_id=neighbor.id,
            total_score=total_score,
            similarity=similarity,
            edge_weight=neighbor.edge_weight,
            demand_overlap=demand_overlap,
            capability_match=capability_match,
        )

    @staticmethod
    def mmr_select(
        scored_neighbors: List[Tuple[Neighbor, RoutingScore]],
        k: int,
        lambda_diversity: float = 0.5,
    ) -> List[Tuple[Neighbor, RoutingScore]]:
        """
        Maximum Marginal Relevance selection for diversity.

        Selects k neighbors balancing relevance and diversity.
        Pre-computes pairwise similarity matrix to avoid redundant calculations.

        Args:
            scored_neighbors: List of (neighbor, score) tuples
            k: Number of neighbors to select
            lambda_diversity: Diversity parameter (0=relevance, 1=diversity)

        Returns:
            Selected neighbors with scores
        """
        if len(scored_neighbors) <= k:
            return scored_neighbors

        if k <= 0:
            return []

        n = len(scored_neighbors)

        # Pre-compute pairwise similarity matrix (Phase 3.3 optimization)
        embeddings = np.array([nb.profile_embedding for nb, _ in scored_neighbors])
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = embeddings / norms
        sim_matrix = (normalized @ normalized.T + 1.0) / 2.0
        np.clip(sim_matrix, 0.0, 1.0, out=sim_matrix)

        # Build index mapping
        id_to_idx = {scored_neighbors[i][0].id: i for i in range(n)}

        selected: List[Tuple[Neighbor, RoutingScore]] = []
        selected_indices: List[int] = []
        candidates = list(range(n))

        # Select first (highest scored)
        candidates.sort(key=lambda i: scored_neighbors[i][1].total_score, reverse=True)
        first_idx = candidates.pop(0)
        selected.append(scored_neighbors[first_idx])
        selected_indices.append(first_idx)

        # Select remaining k-1 with MMR using cached similarity matrix
        while len(selected) < k and candidates:
            best_mmr = float('-inf')
            best_candidate_pos = 0

            for pos, c_idx in enumerate(candidates):
                relevance = scored_neighbors[c_idx][1].total_score
                min_sim = min(sim_matrix[c_idx, s_idx] for s_idx in selected_indices)
                mmr = lambda_diversity * relevance - (1 - lambda_diversity) * min_sim

                if mmr > best_mmr:
                    best_mmr = mmr
                    best_candidate_pos = pos

            best_idx = candidates.pop(best_candidate_pos)
            selected.append(scored_neighbors[best_idx])
            selected_indices.append(best_idx)

        return selected

    @classmethod
    def route_nutrient(
        cls,
        nutrient_embedding: np.ndarray,
        nutrient_tool_hints: List[str],
        neighbors: List[Neighbor],
        top_k: Optional[int] = None,
        diversify: bool = True,
        threshold: Optional[float] = None,
        epsilon: Optional[float] = None,
    ) -> List[Tuple[Neighbor, RoutingScore]]:
        """
        Route nutrient to best neighbors with epsilon-greedy exploration.

        Main routing function that scores all neighbors and selects top-K
        with optional diversity. Implements epsilon-greedy exploration to
        prevent getting stuck in local optima and allow new agents to
        receive traffic.

        Args:
            nutrient_embedding: Nutrient embedding vector (1536-dim)
            nutrient_tool_hints: Tool hints from nutrient
            neighbors: Available neighbors
            top_k: Number of neighbors to select (default: TOP_K)
            diversify: Apply MMR diversity selection
            threshold: Minimum score threshold (default: THRESHOLD_MIN)
            epsilon: Exploration probability (default: EPSILON_EXPLORE)

        Returns:
            List of selected (neighbor, score) tuples

        Example:
            ```python
            selected = RoutingAlgorithm.route_nutrient(
                nutrient_embedding=embedding,
                nutrient_tool_hints=["db.optimize", "sql.analyze"],
                neighbors=available_neighbors,
                top_k=3,
                diversify=True
            )

            for neighbor, score in selected:
                print(f"Route to {neighbor.id}: score={score.total_score:.3f}")
            ```
        """
        if top_k is None:
            top_k = cls.TOP_K

        if threshold is None:
            threshold = cls.THRESHOLD_MIN

        if epsilon is None:
            epsilon = cls.EPSILON_EXPLORE

        if len(nutrient_embedding) != 1536:
            raise ValueError(
                f"Nutrient embedding must be 1536-dimensional, got {len(nutrient_embedding)}"
            )

        # Score all neighbors
        scored: List[Tuple[Neighbor, RoutingScore]] = []
        below_threshold: List[Tuple[Neighbor, RoutingScore]] = []

        for neighbor in neighbors:
            score = cls.calculate_routing_score(
                nutrient_embedding=nutrient_embedding,
                nutrient_tool_hints=nutrient_tool_hints,
                neighbor=neighbor,
            )

            if score.total_score >= threshold:
                scored.append((neighbor, score))
            else:
                below_threshold.append((neighbor, score))

        # Sort by score
        scored.sort(key=lambda x: x[1].total_score, reverse=True)

        # Apply MMR diversity if requested
        if diversify and len(scored) > top_k:
            selected = cls.mmr_select(
                scored_neighbors=scored,
                k=top_k,
                lambda_diversity=cls.LAMBDA_DIVERSITY,
            )
        else:
            selected = scored[:top_k]

        # Epsilon-greedy exploration: replace one selection with random neighbor
        if (epsilon > 0 and random.random() < epsilon
                and len(selected) > 0 and len(below_threshold) > 0):
            # Pick a random below-threshold neighbor for exploration
            explore_choice = random.choice(below_threshold)
            # Replace the lowest-scored member of the selection
            selected[-1] = explore_choice

        return selected


class QuotaChecker:
    """Check quota constraints for routing."""

    @staticmethod
    def within_quota(
        nutrient_cost: int,
        neighbor_quota: Dict[str, int],
        current_usage: Dict[str, int],
    ) -> bool:
        """
        Check if routing is within quota limits.

        Args:
            nutrient_cost: Cost of this nutrient
            neighbor_quota: Quota limits for neighbor
            current_usage: Current usage counters

        Returns:
            True if within quota
        """
        kb_limit = neighbor_quota.get("kb_hour", float("inf"))
        msg_limit = neighbor_quota.get("msg_min", float("inf"))

        kb_used = current_usage.get("kb_hour", 0)
        msg_used = current_usage.get("msg_min", 0)

        return kb_used + nutrient_cost <= kb_limit and msg_used + 1 <= msg_limit


class TTLChecker:
    """Check TTL constraints for routing."""

    @staticmethod
    def can_forward(
        nutrient_created_at: datetime,
        nutrient_ttl_sec: int,
        nutrient_max_hops: int,
    ) -> bool:
        """
        Check if nutrient can still be forwarded.

        Args:
            nutrient_created_at: When nutrient was created
            nutrient_ttl_sec: Time-to-live in seconds
            nutrient_max_hops: Maximum hops remaining

        Returns:
            True if can forward
        """
        # Check TTL
        age = (datetime.utcnow() - nutrient_created_at).total_seconds()
        if age >= nutrient_ttl_sec:
            return False

        # Check hops
        if nutrient_max_hops <= 0:
            return False

        return True
