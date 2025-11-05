"""
Qilbee Mycelial Network (QMN) - Enterprise SaaS SDK

A fully managed SaaS platform that enables AI agents to form an adaptive,
self-optimizing communication network inspired by biological mycelia.
"""

__version__ = "0.1.2"

from .client import MycelialClient
from .models import Nutrient, Outcome, Sensitivity, Context
from .settings import QMNSettings

__all__ = [
    "MycelialClient",
    "Nutrient",
    "Outcome",
    "Sensitivity",
    "Context",
    "QMNSettings",
]
