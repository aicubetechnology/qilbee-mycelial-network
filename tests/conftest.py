"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
import sys
import os

# Add SDK and services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../sdk'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services'))


@pytest.fixture
def sample_embedding():
    """Generate a sample 1536-dim embedding."""
    import numpy as np
    return np.random.rand(1536).tolist()


@pytest.fixture
def sample_embedding_array():
    """Generate a sample embedding as numpy array."""
    import numpy as np
    return np.random.rand(1536)


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
