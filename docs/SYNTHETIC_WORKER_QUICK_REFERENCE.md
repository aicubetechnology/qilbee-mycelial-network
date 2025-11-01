# Synthetic Worker - Quick Reference Guide

## What Is It?
Enterprise AI Worker Platform running Claude agents with distributed task processing, GUI automation, code analysis, and multi-agent coordination.

## Key Components at a Glance

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Server** | FastAPI + Uvicorn | REST endpoints + WebSocket real-time communication |
| **Message Queue** | RabbitMQ 3.12+ | Async task distribution and inter-worker communication |
| **Task Scheduler** | Celery 5.3+ | Distributed task processing and beat scheduling |
| **AI Engine** | Claude API (Anthropic) | LLM for reasoning, tool coordination, automation |
| **Cache/Session** | Redis 7.0+ | Session storage, caching, Celery backend |
| **Integration** | Qube API | Authentication, config management, subscription validation |
| **Logging** | structlog + JSON | Structured audit logs, metrics, tracing |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                             │
│  (REST API, WebSocket, Direct Integration)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        v                         v
┌──────────────┐         ┌──────────────────┐
│  FastAPI App │         │   WebSocket      │
│  (Port 8000) │         │   Real-time      │
└──────────────┘         └──────────────────┘
        │                         │
        └────────────┬────────────┘
                     │
                     v
        ┌────────────────────────────┐
        │   RabbitMQ Message Broker   │
        │  (5 Durable Queues)         │
        └──────────┬─────────────────┘
                   │
        ┌──────────┴───────────┬──────────────┐
        │                      │              │
        v                      v              v
   ┌─────────┐          ┌──────────┐    ┌──────────┐
   │ LLM     │          │  Task    │    │  System  │
   │ Worker  │          │ Processor│    │ Monitor  │
   │ (Async) │          │(Celery)  │    │(Periodic)│
   └────┬────┘          └──────────┘    └──────────┘
        │
        v
   ┌─────────────────────┐
   │  Claude API         │
   │  + Tools            │
   │  (Bash, Computer,   │
   │   Edit, Memory,     │
   │   Web Fetch, Code)  │
   └─────────────────────┘
```

## Queue Architecture (RabbitMQ)

```
Exchange Types:
├── qilbee (TOPIC)       - Main event routing
├── qilbee.direct        - Direct agent targeting
└── qilbee.topic         - Pattern-based routing

Queues (5 Total):
├── qilbee.agent_tasks         ← Task creation
├── qilbee.agent_responses     ← Task completion/failure
├── qilbee.system_events       ← System-wide events
├── qilbee.user_notifications  ← User-specific messages
└── qilbee.agent_coordination  ← Agent-to-agent sync

Routing Keys:
├── task.created      → agent_tasks
├── task.completed    → agent_responses
├── task.failed       → agent_responses
├── system.*          → system_events
└── agent.*           → agent_coordination
```

## Task Types Supported

| Type | Handler | Use Case |
|------|---------|----------|
| `llm_request` | Direct Claude call | Questions, analysis, reasoning |
| `code_analysis` | Code review engine | Security, performance, refactoring |
| `chat_message` | Conversational loop | Multi-turn dialogue with history |
| `automation` | Computer use tool | GUI interactions, screenshots, clicks |

## Critical Files Reference

```
/backend/
├── run.py                           → Main app launcher
├── start_rabbitmq_llm_worker.py     → Worker startup
├── app/
│   ├── main.py                      → FastAPI app (startup/shutdown)
│   ├── core/config.py               → All settings + Qube API loader
│   ├── services/
│   │   ├── message_broker.py        → RabbitMQ client singleton
│   │   ├── anthropic_client.py      → Claude API wrapper
│   │   └── qube_client.py           → Qube Platform integration
│   ├── workers/
│   │   ├── rabbitmq_llm_worker.py   → Main consumer (CRITICAL)
│   │   ├── agent_coordinator.py     → Multi-agent orchestration
│   │   └── celery_app.py            → Task queue configuration
│   └── api/
│       ├── websocket.py             → Real-time streaming
│       └── v1/                      → REST endpoints
└── data/
    ├── agent_templates/             → Agent definitions (JSON)
    └── audit/                       → Logs, screenshots, events
```

## Environment Variables (Critical)

```bash
# REQUIRED - Without these, service won't start
QILBEE_AGENT_API_KEY=<qube-api-key>
QILBEE_AGENT_ID=<agent-uuid>
ANTHROPIC_API_KEY=<claude-api-key>

# RabbitMQ Connection
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Qube Platform
QUBE_API_BASE_URL=https://api.qube.aicube.ca
QUBE_API_VERSION=v1

# Mode
SWARM_MODE=true              # Process queue tasks only
ENVIRONMENT=production        # or development
DEBUG=false
```

## API Endpoints Summary

### REST
- `POST /api/v1/tasks` - Create new task
- `GET /api/v1/tasks/{task_id}` - Get task status
- `GET /api/v1/agents` - List all agents
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### WebSocket
- `ws://localhost:8000/ws/chat?session_id=<sid>&token=<jwt>`
  - Stream-based real-time responses
  - Tool use execution with callbacks
  - Session history tracking

## Communication Flow Example

### Task Submission → Completion
```
1. Client: POST /api/v1/tasks
           {"type": "llm_request", "prompt": "..."}

2. API: Publish to RabbitMQ (routing_key: task.created)
        to qilbee.agent_tasks queue

3. Worker: Consume message
           Check subscription status
           Call Claude API with tools

4. Claude: Return text, tools calls, etc.

5. Worker: Publish response (routing_key: task.completed)
           to qilbee.agent_responses queue

6. Client: Poll /api/v1/tasks/{task_id}
           or WebSocket receives async update
```

## Performance Characteristics

| Metric | Setting | Notes |
|--------|---------|-------|
| Max Concurrent Connections | 1000 | WebSocket limit |
| Message Prefetch | 10 | Per worker |
| Request Timeout | 300s | 5 minutes |
| Task TTL | 3600s | 1 hour |
| Max Queue Length | 10,000 | Messages per queue |

## Deployment

### Local Development
```bash
# Terminal 1 - API Server
cd synthetic_worker/backend
python run_dev.py

# Terminal 2 - RabbitMQ Worker
python start_rabbitmq_llm_worker.py
```

### Docker Production
```bash
# From /qilbee_os_linux root
docker-compose up -d qilbee-agent

# Ports exposed:
# 8000 - FastAPI
# 8080 - Nginx proxy
# 5900 - VNC (optional)
# 8001 - Prometheus metrics
```

## Monitoring & Observability

### Endpoints
- **Health**: `GET /health` (check connectivity)
- **Ready**: `GET /ready` (startup probe)
- **Metrics**: `GET /metrics` (Prometheus format)

### Log Format
- Structured JSON logging via structlog
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Audit logs for tool usage stored in `/data/audit/`

### Metrics Tracked
- Request count (by method, endpoint, status)
- Request latency (histogram)
- Active agents count
- Task execution metrics
- Error rates

## Integration Points for Mycelial Network

1. **Task Queue Interface** - RabbitMQ with standardized message format
2. **Configuration Management** - Qube API integration for dynamic config
3. **Authentication** - JWT tokens + Qube API credential validation
4. **Status Reporting** - Periodic health checks and metrics publication
5. **Multi-Worker Scaling** - Celery + RabbitMQ handle distributed processing
6. **Tool Standardization** - Claude tool use protocol for extensibility

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Worker won't start | Missing QILBEE_AGENT_API_KEY | Set env var, verify credentials |
| Tasks not processing | RabbitMQ not running | Start RabbitMQ or update RABBITMQ_HOST |
| WebSocket disconnects | Token expired | Implement token refresh in client |
| Memory growth | Tool caching | Clear /data/analysis_cache periodically |
| Slow responses | High prefetch queue | Reduce CELERY_WORKER_CONCURRENCY |

---

**For detailed information, see:** `/Users/kimera/projects/qilbee-mycelial-network/SYNTHETIC_WORKER_OVERVIEW.md`
