# Synthetic Worker - Mycelial Network Integration Blueprint

## Executive Summary

The **Qilbee Synthetic Worker** is a **production-ready, RabbitMQ-based distributed AI worker system** perfectly designed for integration with the Qilbee Mycelial Network. It provides:

- Standardized queue-based communication (RabbitMQ with 5 distinct queues)
- Multi-agent coordination capabilities (parallel, sequential, conditional execution)
- Enterprise-grade authentication (Qube API + JWT)
- Distributed task processing (Celery + RabbitMQ)
- Real-time communication (WebSocket + REST APIs)
- Comprehensive monitoring (Prometheus metrics + structured logging)
- AI-powered execution (Claude API with 6 specialized tools)

## Key Strengths for Mycelial Network

### 1. Queue-Based Architecture (Mycelial Network Native)
- **5 Durable Queues** ready for multi-node orchestration:
  - `qilbee.agent_tasks` - Task distribution
  - `qilbee.agent_responses` - Response collection
  - `qilbee.system_events` - Event broadcasting
  - `qilbee.user_notifications` - User-specific messages
  - `qilbee.agent_coordination` - Inter-agent communication

- **Standardized Message Format**:
  ```json
  {
    "id": "uuid",
    "timestamp": "ISO8601",
    "routing_key": "task.created|task.completed|task.failed",
    "payload": { /* task-specific data */ },
    "source": "qilbee-corporate"
  }
  ```

### 2. Multi-Agent Coordination Out-of-Box
The Agent Coordinator (`agent_coordinator.py`) already supports:
- **Parallel Execution** - Distribute tasks across multiple agents
- **Sequential Execution** - Chain tasks with dependency management
- **Conditional Execution** - Execute based on time, thresholds, agent status
- **Health Monitoring** - Track agent status and error rates
- **Configuration Sync** - Keep all agents in sync via Qube API

### 3. Distributed Task Processing
- **Celery Integration** - Task routing to specialized queues
- **Beat Scheduler** - Periodic task execution (health checks, cleanup)
- **Task Routing** - Route tasks to specific worker types:
  - `task_processing` - General tasks
  - `llm_processing` - LLM-specific processing
  - `system_monitoring` - Health and metrics
- **Result Persistence** - Redis-backed result storage
- **Task Tracking** - Full lifecycle monitoring and audit

### 4. Enterprise-Grade Security
- **Qube Platform Integration**:
  - Remote configuration loading (encrypted, HTTPS)
  - Subscription status validation per task
  - JWT token authentication
  - OAuth2 support via Qube API
  
- **Audit Logging**:
  - Structured JSON logs with full context
  - Tool usage audit trails
  - Screenshot/action logs for automation tasks
  - Metrics for compliance reporting

### 5. Real-Time Capabilities
- **WebSocket Streaming**:
  - Bidirectional communication
  - Tool output streaming callbacks
  - Real-time status updates
  - Session-based history tracking

- **REST API**:
  - Synchronous task creation
  - Status polling endpoints
  - Batch operations support
  - Health/metrics endpoints

## Integration Patterns with Mycelial Network

### Pattern 1: Simple Task Distribution
```
Mycelial Controller
    |
    v
RabbitMQ: task.created (routing_key) → qilbee.agent_tasks
    |
    v
Synthetic Worker (subscribed to queue)
    |
    v
RabbitMQ: task.completed → qilbee.agent_responses
    |
    v
Mycelial Controller (polls responses)
```

### Pattern 2: Multi-Worker Coordination
```
Mycelial Controller
    |
    +-- Create parallel tasks
    |
    v
RabbitMQ: agent.coordination
    |
    v
Agent Coordinator (matches workers by capability)
    |
    +-- Route to Worker 1
    +-- Route to Worker 2
    +-- Route to Worker 3
    |
    v
RabbitMQ: task.completed (from all workers)
    |
    v
Mycelial Controller (aggregates results)
```

### Pattern 3: Event-Driven Automation
```
External System (via Qube API)
    |
    v
Mycelial Orchestrator
    |
    v
RabbitMQ: system.alert (broadcast event)
    |
    v
Synthetic Workers (all subscribed)
    |
    v
Conditional execution based on event type/data
```

## Technical Integration Checklist

### Prerequisites
- [ ] RabbitMQ 3.12+ running (can be shared cluster)
- [ ] Redis 7.0+ for Celery backend
- [ ] Anthropic API key (Claude access)
- [ ] Qube Platform credentials (API key + Agent ID)
- [ ] Python 3.11+ environment

### Configuration for Network Integration
```python
# app/core/config.py - Key settings

# Queue Coordination
RABBITMQ_EXCHANGE = "qilbee"              # Shared exchange
RABBITMQ_QUEUE_PREFIX = "qilbee"          # Queue naming
RABBITMQ_CONNECTION_TIMEOUT = 10          # Network resilience

# Scaling
CELERY_WORKER_CONCURRENCY = 4             # Per-worker threads
MAX_AGENT_SESSIONS = 100                  # Concurrent sessions
CONNECTION_POOL_SIZE = 20                 # DB connections

# Monitoring
METRICS_ENABLED = True                    # For network visibility
TRACING_ENABLED = True                    # Distributed tracing

# Swarm Mode (for network-coordinated operation)
SWARM_MODE = True                         # Process queue only
```

### API Integration Points
```
Network Orchestrator Integration:

1. Health Check
   GET /health → Service status
   GET /ready → Readiness probe
   
2. Configuration
   GET /api/v1/agents → List available agents
   POST /api/v1/agents/{id}/config → Update config
   
3. Task Management
   POST /api/v1/tasks → Submit task
   GET /api/v1/tasks/{id} → Get status
   GET /api/v1/tasks/{id}/result → Get result
   
4. Monitoring
   GET /metrics → Prometheus format
   WebSocket /ws/chat → Real-time monitoring
```

## Message Flow Examples for Mycelial Network

### Example 1: Code Analysis Task via Network
```json
{
  "id": "task-123",
  "timestamp": "2024-11-01T10:00:00Z",
  "routing_key": "task.created",
  "payload": {
    "task_id": "task-123",
    "type": "code_analysis",
    "code": "python code snippet...",
    "language": "python",
    "analysis_type": "security",
    "agent_id": "computer-specialist-01"
  },
  "source": "mycelial-network"
}
```

Response arrives on `qilbee.agent_responses`:
```json
{
  "task_id": "task-123",
  "type": "code_analysis_result",
  "status": "completed",
  "analysis_type": "security",
  "response": [
    {"type": "text", "text": "Security analysis results..."},
    {"type": "tool_use", "name": "code_analyzer", "results": {...}}
  ],
  "timestamp": "2024-11-01T10:00:30Z"
}
```

### Example 2: Multi-Agent Orchestration via Network
```json
{
  "id": "coord-456",
  "routing_key": "agent.coordination",
  "payload": {
    "coordination_id": "coord-456",
    "type": "parallel_execution",
    "agents": ["code-developer", "security-analyst", "performance-expert"],
    "tasks": [
      {"id": "task-1", "prompt": "Review code quality..."},
      {"id": "task-2", "prompt": "Check security..."},
      {"id": "task-3", "prompt": "Optimize performance..."}
    ]
  }
}
```

Workers process in parallel and report status to:
- `qilbee.agent_coordination` - Coordination events
- `qilbee.agent_responses` - Individual task results

## Performance Considerations for Network Scale

### Throughput Expectations
- **Single Worker**: 10-50 tasks/minute (depending on complexity)
- **Prefetch Queue**: 10 messages per worker
- **Task TTL**: 3600 seconds (1 hour)
- **Max Queue Length**: 10,000 messages

### Scaling Strategy
```
Network Load → RabbitMQ → [Worker Pool]
                           ├── Worker 1 (4 concurrent)
                           ├── Worker 2 (4 concurrent)
                           ├── Worker 3 (4 concurrent)
                           └── Worker N

Total capacity = N workers × 4 concurrency × task_rate
```

### Monitoring for Network Health
```
Prometheus Metrics Available:
- qilbee_requests_total (by endpoint, method, status)
- qilbee_request_duration_seconds (histogram)
- qilbee_active_agents (gauge)
- celery_task_total (by status)
- rabbitmq_connection_health (bool)
- redis_cache_hits/misses
```

## Migration Path from Standalone to Network

### Phase 1: Enable Queue Mode
```bash
# Start existing system with SWARM_MODE=true
# This makes it queue-driven instead of direct API
docker-compose up -e SWARM_MODE=true
```

### Phase 2: Connect to Shared RabbitMQ
```bash
# Update configuration to point to network RabbitMQ
RABBITMQ_HOST=network-rabbitmq.internal
RABBITMQ_PORT=5672
RABBITMQ_VHOST=/network-segment
```

### Phase 3: Register with Mycelial Orchestrator
```bash
# Via Qube API configuration
MYCELIAL_NETWORK_ID=network-001
MYCELIAL_CONTROLLER_URL=https://controller.mycelial.local
MYCELIAL_DISCOVERY_ENABLED=true
```

### Phase 4: Enable Distributed Tracing
```bash
TRACING_ENABLED=true
JAEGER_ENDPOINT=https://jaeger.mycelial.local
```

## Known Limitations & Considerations

1. **Single LLM Provider**: Currently hardcoded to Anthropic Claude
   - Could extend with factory pattern for multi-provider support
   
2. **Qube API Dependency**: Requires Qube Platform for configuration
   - Could make optional with fallback to environment variables
   
3. **Session State**: Stored locally in each worker
   - For true multi-worker sessions, needs shared storage (Redis)
   - Already implemented via `chat_session_manager`

4. **Tool Execution**: Runs on worker hardware
   - Suitable for sandboxed environments
   - VNC server included for GUI automation
   - May need resource limits in shared network

## Recommended Network Architecture

```
┌─────────────────────────────────────────────────────┐
│         MYCELIAL NETWORK ORCHESTRATOR               │
│  (Qilbee Mycelial Network Controller/Coordinator)  │
└────────────────┬────────────────────────────────────┘
                 │
       ┌─────────┼─────────┐
       │         │         │
       v         v         v
  ┌─────────┐ ┌─────────┐ ┌─────────┐
  │Worker 1 │ │Worker 2 │ │Worker N │
  │(Synthetic)│(Synthetic) │(Synthetic)
  └────┬────┘ └────┬────┘ └────┬────┘
       │         │         │
       └─────────┼─────────┘
               │
               v
  ┌─────────────────────────────┐
  │  Shared RabbitMQ Cluster    │
  │  ├─ qilbee.agent_tasks      │
  │  ├─ qilbee.agent_responses  │
  │  ├─ qilbee.system_events    │
  │  ├─ qilbee.notifications    │
  │  └─ qilbee.coordination     │
  └────────────────┬────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        v                     v
  ┌──────────────┐      ┌──────────────┐
  │ Redis Cluster│      │ Prometheus   │
  │ (Sessions)   │      │ (Metrics)    │
  └──────────────┘      └──────────────┘
```

## Testing Integration

### Unit Tests
```bash
cd synthetic_worker/backend
pytest tests/

# Key test areas:
# - Message broker publish/consume
# - Agent coordinator logic
# - Task processor routing
# - Qube API integration
```

### Integration Tests
```bash
# Test with actual RabbitMQ
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:latest

# Submit test tasks
python -m pytest tests/integration/ -v

# Test real Claude API (requires ANTHROPIC_API_KEY)
pytest tests/llm_integration/ --api-key=$ANTHROPIC_API_KEY
```

### Network Simulation
```bash
# Run multiple workers against single RabbitMQ
docker-compose scale worker=3

# Monitor queue distribution
curl http://localhost:15672/api/queues -u guest:guest | jq
```

## Next Steps for Mycelial Network Team

1. **Architecture Review**
   - Review this document with network architects
   - Identify any protocol differences
   - Plan adapter/bridge code if needed

2. **Configuration Standardization**
   - Define network-wide settings
   - Create configuration management system
   - Set up CI/CD for deploying to network

3. **Testing & Validation**
   - Build integration test suite
   - Performance testing under load
   - Chaos engineering (network failures)

4. **Documentation & Training**
   - Create operational runbooks
   - Document troubleshooting procedures
   - Build runbooks for common tasks

5. **Production Deployment**
   - Security hardening review
   - Load testing & capacity planning
   - Gradual rollout strategy

---

## Summary

The Synthetic Worker is **production-ready** for Mycelial Network integration with:
- Minimal configuration changes needed
- Standardized RabbitMQ-based communication
- Built-in multi-agent coordination
- Enterprise-grade monitoring and logging
- Proven scalability and reliability

**Perfect fit as a standardized worker node for the Qilbee Mycelial Network.**
