"""
Unit tests for scope-based authorization on the hyphal_memory store_memory
endpoint.

Verifies that storing kind='skill' or kind='guardrail' requires the API key
to carry the 'memory:write:privileged' scope (or be admin/wildcard), while
all other kinds remain unrestricted for any authenticated tenant. This is
the architectural safeguard preventing an agent from arbitrarily storing
privileged memory kinds even if it were instructed to via prompt injection
or a misbehaving system prompt (see GUARD_RAILS_PROTOCOL memory).
"""

import importlib.util
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services"))

from shared.auth import TenantContext  # noqa: E402

# NOTE: Load hyphal_memory's main.py under a unique module name
# ("hyphal_memory_main") instead of `import main` / sys.path-hacking into
# services/data_plane/hyphal_memory. Several sibling test files (e.g.
# test_reinforcement.py, test_phase1_routing.py) also rely on a bare
# `from main import ...`, and a generic `sys.modules["main"]` entry would
# get cached and silently shadow/collide with theirs depending on test
# collection order, causing spurious ImportErrors in unrelated suites.
_HYPHAL_MEMORY_MAIN_PATH = os.path.join(
    os.path.dirname(__file__), "../../services/data_plane/hyphal_memory/main.py"
)
_spec = importlib.util.spec_from_file_location(
    "hyphal_memory_main", _HYPHAL_MEMORY_MAIN_PATH
)
hyphal_memory_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hyphal_memory_main)


def _make_request_payload(kind: str) -> dict:
    return {
        "agent_id": "test-agent",
        "kind": kind,
        "content": {"foo": "bar"},
        "embedding": [0.1] * 1536,
    }


@pytest.fixture
def client():
    """TestClient with postgres dependency overridden to avoid real DB."""
    mock_postgres = MagicMock()
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "id": "11111111-1111-1111-1111-111111111111",
            "agent_id": "test-agent",
            "kind": "memory",
            "content": '{"foo": "bar"}',
            "quality": 0.5,
            "sensitivity": "internal",
            "created_at": __import__("datetime").datetime.utcnow(),
            "expires_at": None,
        }
    )

    hyphal_memory_main.app.dependency_overrides[hyphal_memory_main.get_postgres] = (
        lambda: mock_postgres
    )

    yield TestClient(hyphal_memory_main.app)

    hyphal_memory_main.app.dependency_overrides.clear()


def _override_ctx(ctx: TenantContext):
    hyphal_memory_main.app.dependency_overrides[
        hyphal_memory_main.get_tenant_context
    ] = lambda: ctx


class TestPrivilegedKindEnforcement:
    """kind='skill'/'guardrail' requires memory:write:privileged scope."""

    @pytest.mark.parametrize("kind", ["skill", "guardrail"])
    def test_privileged_kind_without_scope_returns_403(self, client, kind):
        _override_ctx(
            TenantContext(tenant_id="tenant-a", scopes=["read", "write"], is_admin=False)
        )
        resp = client.post(
            "/v1/hyphal:store",
            json=_make_request_payload(kind),
            headers={"X-API-Key": "irrelevant-mocked"},
        )
        assert resp.status_code == 403
        assert "memory:write:privileged" in resp.json()["detail"]

    @pytest.mark.parametrize("kind", ["skill", "guardrail"])
    def test_privileged_kind_with_scope_succeeds(self, client, kind):
        _override_ctx(
            TenantContext(
                tenant_id="tenant-a",
                scopes=["memory:write:privileged"],
                is_admin=False,
            )
        )
        resp = client.post(
            "/v1/hyphal:store",
            json=_make_request_payload(kind),
            headers={"X-API-Key": "irrelevant-mocked"},
        )
        assert resp.status_code == 201

    @pytest.mark.parametrize("kind", ["skill", "guardrail"])
    def test_privileged_kind_with_admin_succeeds(self, client, kind):
        _override_ctx(TenantContext(tenant_id="tenant-a", scopes=[], is_admin=True))
        resp = client.post(
            "/v1/hyphal:store",
            json=_make_request_payload(kind),
            headers={"X-API-Key": "irrelevant-mocked"},
        )
        assert resp.status_code == 201

    @pytest.mark.parametrize("kind", ["skill", "guardrail"])
    def test_privileged_kind_with_wildcard_scope_succeeds(self, client, kind):
        _override_ctx(
            TenantContext(tenant_id="tenant-a", scopes=["*"], is_admin=False)
        )
        resp = client.post(
            "/v1/hyphal:store",
            json=_make_request_payload(kind),
            headers={"X-API-Key": "irrelevant-mocked"},
        )
        assert resp.status_code == 201

    def test_privileged_kind_case_insensitive(self, client):
        """kind='Skill' (mixed case) is still gated (kind is lowercased)."""
        _override_ctx(
            TenantContext(tenant_id="tenant-a", scopes=["read"], is_admin=False)
        )
        resp = client.post(
            "/v1/hyphal:store",
            json=_make_request_payload("Skill"),
            headers={"X-API-Key": "irrelevant-mocked"},
        )
        assert resp.status_code == 403


class TestNonPrivilegedKindUnrestricted:
    """Non-privileged kinds remain unrestricted for any authenticated tenant."""

    @pytest.mark.parametrize(
        "kind",
        ["memory", "insight", "snippet", "context", "task", "outcome"],
    )
    def test_non_privileged_kind_without_scope_succeeds(self, client, kind):
        _override_ctx(
            TenantContext(tenant_id="tenant-a", scopes=[], is_admin=False)
        )
        resp = client.post(
            "/v1/hyphal:store",
            json=_make_request_payload(kind),
            headers={"X-API-Key": "irrelevant-mocked"},
        )
        assert resp.status_code == 201
