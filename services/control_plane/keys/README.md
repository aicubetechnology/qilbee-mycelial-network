# Hyphal Keys Service

API key management service for Qilbee Mycelial Network.

## Features

- API key creation and validation
- Tenant-based key isolation
- Scoped permissions
- Rate limiting configuration
- Key expiration management
- Bootstrap endpoint for initial admin key creation

## Endpoints

- `POST /keys/v1/keys` - Create new API key
- `POST /keys/v1/keys:validate` - Validate API key
- `POST /keys/v1/bootstrap` - Bootstrap initial admin key (⚠️ see security notes)

## TODO

### Security Enhancement: Restrict Bootstrap Endpoint by Domain

**Context:**
- Public domain: `qilbee.io` (accessible from internet)
- Internal domain: `prod.qilbee.io` (accessible only via VPN)

**Problem:**
Currently, the `/keys/v1/bootstrap` endpoint is publicly accessible via `qilbee.io`, allowing anyone to create admin keys without authentication.

**Proposed Solution:**
Configure ingress to block access to `/bootstrap` endpoint when accessed via public domain but allow it via VPN-protected domain.

**Implementation Steps:**

#### 1. Update Ingress Configuration

Add host-based routing rules to restrict bootstrap endpoint:

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: qmn-keys-ingress
  annotations:
    nginx.ingress.kubernetes.io/server-snippet: |
      # Block bootstrap on public domain
      if ($host = "qilbee.io") {
        set $block_bootstrap A;
      }
      if ($request_uri ~ "^/keys/v1/bootstrap") {
        set $block_bootstrap "${block_bootstrap}B";
      }
      if ($block_bootstrap = AB) {
        return 403;
      }
spec:
  rules:
  - host: qilbee.io
    http:
      paths:
      - path: /keys/v1
        pathType: Prefix
        backend:
          service:
            name: hyphal-keys
            port:
              number: 8000
  - host: prod.qilbee.io
    http:
      paths:
      - path: /keys/v1
        pathType: Prefix
        backend:
          service:
            name: hyphal-keys
            port:
              number: 8000
```

#### 2. Alternative: Application-Level Check

Add middleware to check request host header:

```python
# main.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class BootstrapDomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/keys/v1/bootstrap":
            host = request.headers.get("host", "")
            # Only allow bootstrap on internal domain
            if not host.startswith("prod.qilbee.io"):
                raise HTTPException(
                    status_code=403,
                    detail="Bootstrap endpoint only accessible via internal domain"
                )
        response = await call_next(request)
        return response

# Add to app
app.add_middleware(BootstrapDomainMiddleware)
```

#### 3. Additional Security Measures

Consider implementing one or more:

1. **Secret Token for Bootstrap:**
   ```python
   @app.post("/keys/v1/bootstrap")
   async def bootstrap(bootstrap_token: str = Header(None)):
       if bootstrap_token != os.getenv("BOOTSTRAP_SECRET_TOKEN"):
           raise HTTPException(403, "Invalid bootstrap token")
       # ... existing logic
   ```

2. **One-Time Bootstrap:**
   ```python
   # Only allow bootstrap if no admin keys exist
   existing_admin_keys = await db.fetch_one(
       "SELECT COUNT(*) FROM api_keys WHERE 'admin:*' = ANY(scopes)"
   )
   if existing_admin_keys > 0:
       raise HTTPException(403, "Bootstrap already completed")
   ```

3. **IP Whitelist:**
   ```python
   ALLOWED_BOOTSTRAP_IPS = ["10.0.0.0/8", "172.16.0.0/12"]
   
   def is_ip_allowed(ip: str) -> bool:
       client_ip = ipaddress.ip_address(ip)
       return any(
           client_ip in ipaddress.ip_network(network)
           for network in ALLOWED_BOOTSTRAP_IPS
       )
   ```

#### 4. Monitoring & Alerting

Add logging and alerting for bootstrap attempts:

```python
@app.post("/keys/v1/bootstrap")
async def bootstrap(request: Request):
    logger.warning(
        "Bootstrap endpoint accessed",
        extra={
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "host": request.headers.get("host"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    # Send alert to monitoring system
    await alert_security_team("Bootstrap endpoint accessed")
    # ... existing logic
```

#### 5. Testing

```bash
# Should fail (public domain)
curl -X POST https://qilbee.io/keys/v1/bootstrap
# Expected: 403 Forbidden

# Should succeed (internal domain via VPN)
curl -X POST https://prod.qilbee.io/keys/v1/bootstrap
# Expected: 200 + admin key response
```

**Priority:** HIGH  
**Estimated Effort:** 2-4 hours  
**Security Impact:** Critical - prevents unauthorized admin key creation

