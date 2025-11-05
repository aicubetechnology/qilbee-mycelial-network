# 🐛 BUG REPORT: Metadata JSON Parsing Issue in Identity Service

**Date**: 2025-11-05
**Severity**: HIGH
**Service**: Identity Service (`services/control_plane/identity/main.py`)
**Status**: CONFIRMED ✅

---

## 📋 Summary

The Identity Service has inconsistent JSON parsing for the `metadata` field. The **CREATE** endpoint correctly parses JSONB from PostgreSQL, but **GET**, **UPDATE**, and **LIST** endpoints return raw JSON strings instead of dict objects, causing type mismatches.

---

## 🔍 Root Cause Analysis

### Database Schema
PostgreSQL stores `metadata` as **JSONB** type (line 84 in `infra/postgres/init.sql`):
```sql
metadata JSONB DEFAULT '{}'
```

### asyncpg Behavior
When reading JSONB columns, `asyncpg` returns:
- **Python string** containing JSON (e.g., `'{"key": "value"}'`)
- NOT a Python dict

### Current Code Issues

#### ✅ POST `/v1/tenants` (Line 184) - **CORRECT**
```python
metadata_dict = json_lib.loads(result["metadata"]) if result["metadata"] else {}
```
**Status**: Parses JSON string to dict ✅

#### ❌ GET `/v1/tenants/{tenant_id}` (Line 247) - **INCORRECT**
```python
metadata=result["metadata"] or {},
```
**Status**: Returns JSON string, not dict ❌

#### ❌ PUT `/v1/tenants/{tenant_id}` (Line 341) - **INCORRECT**
```python
metadata=result["metadata"] or {},
```
**Status**: Returns JSON string, not dict ❌

#### ❌ GET `/v1/tenants` (Line 399) - **INCORRECT**
```python
metadata=row["metadata"] or {},
```
**Status**: Returns JSON string, not dict ❌

---

## 🧪 Why Tests Didn't Catch This

### Test Gap Analysis

**File**: `tests/integration/test_services.py`

1. **test_create_tenant** (line 88)
   - Only tests CREATE endpoint
   - Doesn't validate GET after creation
   - ❌ Missing assertion for metadata type

2. **No dedicated tests for**:
   - GET `/v1/tenants/{tenant_id}`
   - PUT `/v1/tenants/{tenant_id}`
   - GET `/v1/tenants` (list)

3. **E2E tests** (`tests/e2e/test_live_agents.py`, `test_5_agent_collaboration.py`)
   - Focus on Router and Memory services
   - Don't test Identity service GET/UPDATE operations

### Why It Worked Initially
- Tests only call **POST** (create), which has correct parsing
- Tests don't retrieve and validate metadata afterward
- Production usage revealed the bug when Aicube tenant was accessed

---

## 💥 Impact

### Observed Behavior
```bash
# Production error when accessing Aicube tenant
GET https://qmn.qube.aicube.ca/identity/v1/tenants/4b374062-0494-4aad-8b3f-de40f820f1c4
Response: 500 Internal Server Error
```

### Type Mismatch
```python
# Expected
TenantResponse.metadata: Dict[str, Any]  # Python dict

# Actual (from buggy endpoints)
result["metadata"]: str  # JSON string like '{"company": "Aicube Technology LLC"}'
```

### Pydantic Validation
Pydantic's `TenantResponse` model may coerce string to dict in some cases, but this is:
- Unreliable
- Not guaranteed
- Can cause serialization issues

---

## 🔧 Fix Required

Add `json.loads()` to 3 locations:

### 1. GET `/v1/tenants/{tenant_id}` (Line 247)

**Before**:
```python
metadata=result["metadata"] or {},
```

**After**:
```python
import json as json_lib  # Add at top if not present

# In the return statement
metadata=json_lib.loads(result["metadata"]) if result["metadata"] else {},
```

### 2. PUT `/v1/tenants/{tenant_id}` (Line 341)

**Before**:
```python
metadata=result["metadata"] or {},
```

**After**:
```python
metadata=json_lib.loads(result["metadata"]) if result["metadata"] else {},
```

### 3. GET `/v1/tenants` (Line 399)

**Before**:
```python
metadata=row["metadata"] or {},
```

**After**:
```python
metadata=json_lib.loads(row["metadata"]) if row["metadata"] else {},
```

---

## ✅ Testing Plan

### 1. Unit Tests to Add
```python
@pytest.mark.asyncio
async def test_get_tenant_returns_dict_metadata():
    """Ensure GET returns metadata as dict, not string."""
    # Create tenant with metadata
    # GET tenant
    # Assert isinstance(response.json()["metadata"], dict)
    # Assert response.json()["metadata"]["company"] == "Test Company"

@pytest.mark.asyncio
async def test_update_tenant_preserves_metadata_type():
    """Ensure UPDATE returns metadata as dict."""
    # Create tenant
    # Update tenant
    # Assert metadata is dict

@pytest.mark.asyncio
async def test_list_tenants_returns_dict_metadata():
    """Ensure LIST returns metadata as dict for all tenants."""
    # Create multiple tenants with metadata
    # List tenants
    # Assert all metadata fields are dicts
```

### 2. Integration Test
- Create tenant with metadata via POST
- Retrieve via GET and validate metadata is dict
- Update via PUT and validate metadata is dict
- List via GET /tenants and validate metadata is dict

### 3. Production Validation
```bash
# After fix is deployed
curl -X GET https://qmn.qube.aicube.ca/identity/v1/tenants/4b374062-0494-4aad-8b3f-de40f820f1c4
# Should return 200 with proper JSON metadata
```

---

## 📝 Checklist

- [x] Bug confirmed
- [x] Root cause identified
- [x] Fix documented
- [ ] Fix applied to code
- [ ] Tests added
- [ ] Local testing completed
- [ ] Code committed
- [ ] Deployed to production
- [ ] Production validation

---

## 🚀 Deployment Steps

1. Apply fixes to `services/control_plane/identity/main.py`
2. Add unit tests
3. Run local tests: `pytest tests/integration/test_services.py -v`
4. Commit changes
5. Rebuild Docker image: `docker-compose build identity`
6. Deploy: `docker-compose up -d identity`
7. Validate: Test Aicube tenant GET endpoint

---

## 📚 References

- **File**: `services/control_plane/identity/main.py`
- **Lines**: 247, 341, 399
- **Related**: PostgreSQL JSONB type behavior with asyncpg
- **Tenant**: Aicube Technology LLC (`4b374062-0494-4aad-8b3f-de40f820f1c4`)
