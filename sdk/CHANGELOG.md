# Changelog

All notable changes to the Qilbee Mycelial Network SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-11-05

### Fixed
- **API endpoint paths**: Corrected all endpoint paths to match production OpenAPI specifications
  - `/router/v1/contexts:collect` (was `/contexts:collect`)
  - `/keys/v1/keys:rotate` (was `/keys:rotate`)
  - `/reinforcement/v1/outcomes:record` (was `/outcomes:record`)

### Changed
- **Health check endpoint**: Now accepts optional `service` parameter to check specific services (router, memory, identity, keys)
- **Usage endpoint**: Temporarily disabled with NotImplementedError until production deployment

### Verified
- All paths tested against production environment at https://qmn.qube.aicube.ca
- Validated with OpenAPI specs from:
  - `/router/openapi.json`
  - `/memory/openapi.json`
  - `/identity/openapi.json`
  - `/keys/openapi.json`
- Successfully tested with 14-operation banking project simulation (0 errors)

## [0.1.1] - 2025-11-05

### Added
- **Multi-tenant support**: Added `tenant_id` parameter to settings and authentication
- **Hyphal memory storage**: New `hyphal_store()` method for persisting knowledge
- **Production endpoints**: Updated default API base URL to production environment
- **Environment variable**: Added `QMN_TENANT_ID` support

### Changed
- **Authentication headers**: Updated to use `X-API-Key` and `X-Tenant-ID` headers
- **API endpoints**: Updated paths to match production routing:
  - `/router/v1/nutrients:broadcast`
  - `/memory/v1/hyphal:search`
  - `/memory/v1/hyphal:store`
- **Default API URL**: Changed from `https://api.qilbee.network` to `https://qmn.qube.aicube.ca`
- **Timeout configuration**: Fixed httpx.Timeout to include all required parameters

### Fixed
- HTTP client timeout configuration for better compatibility with httpx
- API URL construction (removed version prefix)
- Bearer token format (now uses direct API key)

### Documentation
- Added SDK usage example in `tests/scenarios/banking_project_sdk_version.py`
- Demonstrates best practices for enterprise deployment

## [0.1.0] - 2025-11-01

### Added
- Initial release of Qilbee Mycelial Network Python SDK
- Core client (`MycelialClient`) with async support
- Nutrient broadcasting for knowledge sharing
- Context collection with semantic search
- Hyphal memory search with vector similarity
- Outcome recording for reinforcement learning
- Automatic retry logic with exponential backoff
- Comprehensive error handling
- Type hints throughout
- Environment variable configuration
- Settings validation
- Health check endpoints
- Usage metrics API

### Features
- **Transport protocols**: HTTP, gRPC (optional), QUIC (optional)
- **Security**: TLS 1.3, API key authentication
- **Observability**: OpenTelemetry integration (optional)
- **Multi-region**: Regional routing support
- **Configurability**: Extensive settings via environment or code

### Documentation
- Complete README with examples
- API documentation
- Architecture overview
- Quick start guide
- Advanced usage patterns

---

## Release Notes

### v0.1.1 - Production Ready Update

This release makes the SDK production-ready with multi-tenant support and proper endpoint configuration for the Aicube Technology LLC production environment.

**Breaking Changes**: None (fully backward compatible)

**Migration Guide**:
- If you were using custom endpoints, update them to include service prefixes (`/router`, `/memory`)
- Set `QMN_TENANT_ID` environment variable for multi-tenant deployments
- No code changes required for single-tenant usage

**Tested Against**:
- Production QMN system at `https://qmn.qube.aicube.ca`
- Python 3.9, 3.10, 3.11, 3.12, 3.13
- Enterprise banking project simulation (100+ agents)
