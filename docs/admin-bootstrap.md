# QMN Admin Bootstrap Guide

## Overview

The Qilbee Mycelial Network (QMN) uses a secure bootstrap process to generate the initial admin API key. This key belongs to **AIcube Technology LLC**, the global administrator tenant with full system access.

## Security Design

- **No automatic key generation**: The admin API key is NOT created automatically on startup
- **No disk storage**: The API key is NEVER saved to any file on the server
- **No logging**: The full API key is NEVER written to logs (only the prefix is logged)
- **One-time bootstrap**: The bootstrap endpoint only works ONCE - it's disabled after the first key is created

## Fresh Startup Process

### Step 1: Start the Services

```bash
docker-compose up -d
```

### Step 2: Check the Logs

On fresh startup, you'll see this message in the logs:

```bash
docker-compose logs identity
```

```
INFO:shared.startup:FRESH STARTUP DETECTED
INFO:shared.startup:To generate admin API key, run:
INFO:shared.startup:  curl -X POST http://localhost:8022/keys/v1/bootstrap
```

### Step 3: Generate the Admin API Key

Run the bootstrap command:

```bash
curl -X POST http://localhost:8022/keys/v1/bootstrap
```

**Response:**

```json
{
  "success": true,
  "tenant_id": "00000000-0000-0000-0000-000000000001",
  "tenant_name": "AIcube Technology LLC",
  "api_key": "qmn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "message": "Admin API key created. Save this key - it will NOT be shown again!"
}
```

### Step 4: Save the API Key

**IMPORTANT**: Copy and securely store the `api_key` value immediately. This is the ONLY time it will be shown.

Recommended storage:
- Password manager (1Password, Bitwarden, etc.)
- Encrypted secrets vault (HashiCorp Vault, AWS Secrets Manager)
- Secure offline storage for disaster recovery

## Using the Admin API Key

### List All Tenants

```bash
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
  http://localhost:8022/identity/v1/tenants
```

### Create a New Tenant

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -d '{"id":"my-company","name":"My Company Inc","plan_tier":"pro"}' \
  http://localhost:8022/identity/v1/tenants
```

### Create API Key for a Tenant

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -d '{"tenant_id":"my-company","name":"production-key","scopes":["*"]}' \
  http://localhost:8022/keys/v1/keys
```

### List API Keys for a Tenant

```bash
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
  http://localhost:8022/keys/v1/keys/my-company
```

### Revoke an API Key

```bash
curl -X DELETE \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  http://localhost:8022/keys/v1/keys/KEY_ID
```

## Admin-Only Endpoints

These endpoints require the AIcube Technology LLC admin API key:

| Service | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Identity | `/v1/tenants` | GET | List all tenants |
| Identity | `/v1/tenants` | POST | Create tenant |
| Identity | `/v1/tenants/{id}` | GET | Get tenant |
| Identity | `/v1/tenants/{id}` | PUT | Update tenant |
| Identity | `/v1/tenants/{id}` | DELETE | Delete tenant |
| Keys | `/v1/keys` | POST | Create API key |
| Keys | `/v1/keys/{tenant_id}` | GET | List tenant's keys |
| Keys | `/v1/keys:rotate` | POST | Rotate API key |
| Keys | `/v1/keys/{key_id}` | DELETE | Revoke API key |
| Memory | `/v1/hyphal:cleanup` | POST | Cleanup expired data |

## Troubleshooting

### Bootstrap Returns 403

```json
{"detail": "Bootstrap disabled: Admin API key already exists."}
```

**Cause**: An admin API key has already been created.

**Solutions**:
1. Use the existing admin key
2. If lost, revoke all admin keys via direct database access, then bootstrap again:

```sql
-- Connect to PostgreSQL
UPDATE api_keys SET status = 'revoked'
WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
```

Then run bootstrap again.

### Lost Admin API Key

If you've lost the admin API key and need to recover:

1. Access the database directly:
```bash
docker exec -it qmn-postgres psql -U postgres -d qmn
```

2. Revoke existing admin keys:
```sql
UPDATE api_keys SET status = 'revoked'
WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
```

3. Run bootstrap again:
```bash
curl -X POST http://localhost:8022/keys/v1/bootstrap
```

## Admin Tenant Details

| Property | Value |
|----------|-------|
| Tenant ID | `00000000-0000-0000-0000-000000000001` |
| Tenant Name | AIcube Technology LLC |
| Plan Tier | Enterprise |
| Scopes | `admin:*`, `*` |
| Rate Limit | 10,000 requests/minute |
| Key Expiration | 10 years |

## Best Practices

1. **Rotate keys regularly**: Use `/v1/keys:rotate` to rotate admin keys periodically
2. **Use separate keys**: Create separate API keys for different environments (dev, staging, prod)
3. **Monitor usage**: Check `last_used_at` on API keys to detect unauthorized access
4. **Principle of least privilege**: Create tenant-specific keys with limited scopes when possible
