# QMN Comprehensive Improvement Plan - TODO Tracker

## Phase 1: Routing Intelligence & RL Core
- [x] 1.1 Time-Based Edge Decay Background Task
- [x] 1.2 Probabilistic Routing (Epsilon-Greedy Exploration)
- [x] 1.3 Semantic Demand Overlap (fuzzy matching)
- [x] 1.4 Proportional Capability Boost
- [x] 1.5 TTL Enforcement in Router
- [x] 1.6 Per-Hop Outcome Support

## Phase 2: Production Hardening
- [x] 2.1 Real Encryption (AES-256-GCM)
- [x] 2.2 Rate Limiting Middleware
- [x] 2.3 Quota Enforcement
- [x] 2.4 Proper Audit Signing (Ed25519)
- [x] 2.5 SQL Injection Hardening

## Phase 3: Performance at Scale
- [x] 3.1 Fix N+1 Query in Neighbor Loading
- [x] 3.2 Batch Edge Weight Updates
- [x] 3.3 Cache Similarity Matrix in MMR
- [x] 3.4 Add Missing Database Index
- [x] 3.5 Dynamic Neighbor Limit

## Phase 4: Observability & Monitoring
- [x] 4.1 Prometheus Metrics Endpoints
- [x] 4.2 Custom Business Metrics
- [x] 4.3 Structured Logging
- [x] 4.4 Alerting Rules

## Phase 5: SDK Completeness
- [x] 5.1 Control Plane SDK Methods
- [x] 5.2 Implement get_usage()
- [x] 5.3 SDK Models for New Features

## Phase 6: Test Coverage 85%+
- [x] 6.1 Control Plane Unit Tests (test_auth.py, test_auth_middleware.py)
- [x] 6.2 Security Tests (test_rate_limiter.py, test_error_handling.py)
- [x] 6.3 Routing & RL Enhancement Tests (test_phase1_routing.py)
- [x] 6.4 Error Case Tests (test_error_handling.py, test_retry.py)
- [x] 6.5 SDK Client Tests (test_client.py)
- [x] 6.6 Database Manager Tests (test_database.py)
- [x] 6.7 Startup Tests (test_startup.py)

## Summary
- All 6 phases complete
- 312 tests passing, 2 pre-existing failures (settings URL mismatch)
- Coverage: 98% (target was 85%)
