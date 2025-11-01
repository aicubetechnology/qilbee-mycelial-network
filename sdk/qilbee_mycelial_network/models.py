"""
Core data models for QMN SDK.

Defines Nutrient, Outcome, Sensitivity, and Context models for agent communication.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Sensitivity(str, Enum):
    """Data classification levels for DLP enforcement."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dataclass
class Nutrient:
    """
    A nutrient is a package of context/knowledge broadcast through the network.

    Contains embeddings and distilled context that can be routed between agents
    based on semantic similarity and relevance.
    """

    summary: str
    embedding: List[float]  # 1536-dim vector
    snippets: List[str] = field(default_factory=list)
    tool_hints: List[str] = field(default_factory=list)
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    ttl_sec: int = 180
    max_hops: int = 3
    quota_cost: int = 1
    trace_task_id: Optional[str] = None

    # Internal fields (set by system)
    id: str = field(default_factory=lambda: f"nutr-{uuid.uuid4().hex[:12]}")
    trace_id: str = field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:16]}")
    created_at: datetime = field(default_factory=datetime.utcnow)
    current_hop: int = 0

    @classmethod
    def seed(
        cls,
        summary: str,
        embedding: List[float],
        snippets: Optional[List[str]] = None,
        tool_hints: Optional[List[str]] = None,
        sensitivity: Sensitivity = Sensitivity.INTERNAL,
        ttl_sec: int = 180,
        max_hops: int = 3,
        quota_cost: int = 1,
        trace_task_id: Optional[str] = None,
    ) -> "Nutrient":
        """Create a new nutrient for broadcasting."""
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must be 1536-dimensional, got {len(embedding)}")

        return cls(
            summary=summary,
            embedding=embedding,
            snippets=snippets or [],
            tool_hints=tool_hints or [],
            sensitivity=sensitivity,
            ttl_sec=ttl_sec,
            max_hops=max_hops,
            quota_cost=quota_cost,
            trace_task_id=trace_task_id,
        )

    def decrement_hop(self) -> "Nutrient":
        """Create a copy with decremented hop count for forwarding."""
        return Nutrient(
            id=self.id,
            trace_id=self.trace_id,
            summary=self.summary,
            embedding=self.embedding,
            snippets=self.snippets,
            tool_hints=self.tool_hints,
            sensitivity=self.sensitivity,
            ttl_sec=self.ttl_sec,
            max_hops=self.max_hops - 1,
            quota_cost=self.quota_cost,
            trace_task_id=self.trace_task_id,
            created_at=self.created_at,
            current_hop=self.current_hop + 1,
        )

    def is_expired(self) -> bool:
        """Check if nutrient has exceeded TTL."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_sec

    def can_forward(self) -> bool:
        """Check if nutrient can be forwarded."""
        return self.max_hops > 0 and not self.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API transport."""
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "summary": self.summary,
            "embedding": self.embedding,
            "snippets": self.snippets,
            "tool_hints": self.tool_hints,
            "sensitivity": self.sensitivity.value,
            "ttl_sec": self.ttl_sec,
            "max_hops": self.max_hops,
            "quota_cost": self.quota_cost,
            "trace_task_id": self.trace_task_id,
            "created_at": self.created_at.isoformat(),
            "current_hop": self.current_hop,
        }


@dataclass
class Context:
    """
    Enriched context collected from the network.

    Represents aggregated knowledge from multiple agents that responded
    to a collect() request.
    """

    trace_id: str
    contents: List[Dict[str, Any]]
    source_agents: List[str]
    quality_scores: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        """Create Context from API response."""
        return cls(
            trace_id=data["trace_id"],
            contents=data["contents"],
            source_agents=data["source_agents"],
            quality_scores=data["quality_scores"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class Outcome:
    """
    Task outcome for reinforcement learning.

    Used to update edge weights based on whether a collected context
    led to successful task completion.
    """

    score: float  # 0.0 to 1.0 (0=failure, 1=success)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def with_score(cls, score: float, **metadata) -> "Outcome":
        """Create outcome with validation."""
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {score}")
        return cls(score=score, metadata=metadata)

    @classmethod
    def success(cls, **metadata) -> "Outcome":
        """Create success outcome (score=1.0)."""
        return cls(score=1.0, metadata=metadata)

    @classmethod
    def failure(cls, **metadata) -> "Outcome":
        """Create failure outcome (score=0.0)."""
        return cls(score=0.0, metadata=metadata)

    @classmethod
    def partial(cls, score: float = 0.5, **metadata) -> "Outcome":
        """Create partial success outcome."""
        return cls.with_score(score, **metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API transport."""
        return {
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class SearchRequest:
    """Request for hyphal memory vector search."""

    embedding: List[float]
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API transport."""
        return {
            "embedding": self.embedding,
            "top_k": self.top_k,
            "filters": self.filters or {},
        }


@dataclass
class SearchResult:
    """Result from hyphal memory search."""

    id: str
    content: Dict[str, Any]
    similarity: float
    agent_id: str
    kind: str
    created_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create SearchResult from API response."""
        return cls(
            id=data["id"],
            content=data["content"],
            similarity=data["similarity"],
            agent_id=data["agent_id"],
            kind=data["kind"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
