"""
Core routing algorithm for Qilbee Mycelial Network.

Implements gradient-based routing with embedding similarity,
edge weight reinforcement, and MMR diversity selection.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


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
    THRESHOLD_CAPABILITY_BOOST = 0.1  # Boost if capabilities match
    TOP_K = 3  # Default number of neighbors to route to

    # MMR diversity parameter
    LAMBDA_DIVERSITY = 0.5  # 0=pure relevance, 1=pure diversity

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
    def calculate_demand_overlap(
        nutrient_tasks: List[str],
        neighbor_tasks: List[str],
        time_decay_hours: float = 24.0,
    ) -> float:
        """
        Calculate recent task demand overlap.

        Measures how often the neighbor has worked on similar tasks recently.

        Args:
            nutrient_tasks: Task types/tags from nutrient
            neighbor_tasks: Recent tasks completed by neighbor
            time_decay_hours: Time window for relevance

        Returns:
            Overlap score (0.0 to 1.0)
        """
        if not nutrient_tasks or not neighbor_tasks:
            return 0.0

        # Simple overlap ratio
        overlap = len(set(nutrient_tasks) & set(neighbor_tasks))
        total = len(set(nutrient_tasks))

        if total == 0:
            return 0.0

        return float(overlap / total)

    @staticmethod
    def calculate_routing_score(
        nutrient_embedding: np.ndarray,
        nutrient_tool_hints: List[str],
        neighbor: Neighbor,
    ) -> RoutingScore:
        """
        Calculate routing score for a neighbor.

        Combines similarity, edge weight, and demand signals.

        Args:
            nutrient_embedding: Nutrient embedding vector
            nutrient_tool_hints: Tool hints from nutrient
            neighbor: Neighbor agent data

        Returns:
            RoutingScore with breakdown
        """
        # 1. Semantic similarity
        similarity = RoutingAlgorithm.cosine_similarity(
            nutrient_embedding,
            neighbor.profile_embedding,
        )

        # 2. Recent task overlap (using tool hints as proxy for tasks)
        demand_overlap = RoutingAlgorithm.calculate_demand_overlap(
            nutrient_tool_hints,
            neighbor.recent_tasks,
        )

        # 3. Capability matching
        capability_match = any(
            tool in neighbor.capabilities for tool in nutrient_tool_hints
        )

        # 4. Combined score
        # Formula: similarity * edge_weight * (0.5 + 0.5 * demand)
        base_score = similarity * neighbor.edge_weight * (0.5 + 0.5 * demand_overlap)

        # Boost if capabilities match
        if capability_match:
            base_score += RoutingAlgorithm.THRESHOLD_CAPABILITY_BOOST

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

        selected: List[Tuple[Neighbor, RoutingScore]] = []
        candidates = scored_neighbors.copy()

        # Select first (highest scored)
        candidates.sort(key=lambda x: x[1].total_score, reverse=True)
        selected.append(candidates.pop(0))

        # Select remaining k-1 with MMR
        while len(selected) < k and candidates:
            mmr_scores = []

            for neighbor, score in candidates:
                # Relevance component
                relevance = score.total_score

                # Diversity component: min similarity to already selected
                min_sim = min(
                    RoutingAlgorithm.cosine_similarity(
                        neighbor.profile_embedding,
                        s[0].profile_embedding,
                    )
                    for s in selected
                )

                # MMR formula
                mmr = lambda_diversity * relevance - (1 - lambda_diversity) * min_sim
                mmr_scores.append((neighbor, score, mmr))

            # Select highest MMR
            mmr_scores.sort(key=lambda x: x[2], reverse=True)
            best = mmr_scores[0]
            selected.append((best[0], best[1]))

            # Remove from candidates
            candidates = [(n, s) for n, s in candidates if n.id != best[0].id]

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
    ) -> List[Tuple[Neighbor, RoutingScore]]:
        """
        Route nutrient to best neighbors.

        Main routing function that scores all neighbors and selects top-K
        with optional diversity.

        Args:
            nutrient_embedding: Nutrient embedding vector (1536-dim)
            nutrient_tool_hints: Tool hints from nutrient
            neighbors: Available neighbors
            top_k: Number of neighbors to select (default: TOP_K)
            diversify: Apply MMR diversity selection
            threshold: Minimum score threshold (default: THRESHOLD_MIN)

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

        if len(nutrient_embedding) != 1536:
            raise ValueError(
                f"Nutrient embedding must be 1536-dimensional, got {len(nutrient_embedding)}"
            )

        # Score all neighbors
        scored: List[Tuple[Neighbor, RoutingScore]] = []

        for neighbor in neighbors:
            score = cls.calculate_routing_score(
                nutrient_embedding=nutrient_embedding,
                nutrient_tool_hints=nutrient_tool_hints,
                neighbor=neighbor,
            )

            # Only include if above threshold
            if score.total_score >= threshold:
                scored.append((neighbor, score))

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
