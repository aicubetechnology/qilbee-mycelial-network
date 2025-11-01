# QILBEE Synthetic Worker - Comprehensive Overview

## 1. PROJECT STRUCTURE

```
synthetic_worker/
├── README.md
└── backend/
    ├── app/
    │   ├── api/
    │   │   ├── v1/
    │   │   │   ├── agents.py       # Agent management endpoints
    │   │   │   ├── tasks.py        # Task creation/management
    │   │   │   ├── chat.py         # Chat session endpoints
    │   │   │   └── router.py       # Main API router
    │   │   ├── dependencies.py     # Auth dependencies
    │   │   └── websocket.py        # WebSocket real-time communication (60KB+)
    │   │
    │   ├── core/
    │   │   ├── config.py           # Pydantic settings, env management
    │   │   ├── logging.py          # Structured logging setup
    │   │   ├── monitoring.py       # Prometheus metrics, health checks
    │   │   └── exceptions.py       # Custom exception classes
    │   │
    │   ├── services/
    │   │   ├── message_broker.py   # RabbitMQ communication (15KB)
    │   │   ├── anthropic_client.py # Claude API integration (33KB)
    │   │   ├── chat_service.py     # Chat history management
    │   │   ├── qube_client.py      # Qube Platform API client (47KB)
    │   │   ├── auth_service.py     # JWT/OAuth authentication
    │   │   ├── notification_service.py # User notifications
    │   │   └── agent_templates.py  # Agent configuration templates
    │   │
    │   ├── tools/
    │   │   ├── bash_tool.py        # Shell command execution
    │   │   ├── computer_tool.py    # Screen capture, mouse/keyboard control
    │   │   ├── edit_tool.py        # File editing capabilities
    │   │   ├── memory_tool.py      # Persistent memory/knowledge storage
    │   │   ├── web_fetch_tool.py   # Web content retrieval
    │   │   └── code_analyzer_tool.py # Code analysis (63KB)
    │   │
    │   ├── workers/
    │   │   ├── celery_app.py       # Celery distributed task queue setup
    │   │   ├── rabbitmq_llm_worker.py # Main RabbitMQ consumer (async)
    │   │   ├── task_processor.py   # Task execution logic
    │   │   ├── llm_task_processor.py # LLM-specific processing
    │   │   ├── agent_coordinator.py # Multi-agent coordination
    │   │   ├── system_monitor.py   # Health/metrics monitoring
    │   │   └── __init__.py
    │   │
    │   ├── utils/
    │   │   └── summarization.py    # Text summarization utilities
    │   │
    │   └── main.py                 # FastAPI app initialization (11KB)
    │
    ├── data/
    │   ├── audit/                  # Audit logs (screenshots, events)
    │   ├── analysis_cache/         # Cached analysis results
    │   ├── agent_templates/        # JSON agent configs
    │   └── logs/                   # Application logs
    │
    ├── requirements.txt            # Python dependencies
    ├── run.py                      # Application launcher
    ├── run_dev.py                  # Development server
    └── start_rabbitmq_llm_worker.py # Worker startup script

```

## 2. WHAT THE PROJECT DOES

**Qilbee Corporate** is an **Enterprise-grade AI Worker Platform** that:

1. **Provides Synthetic Workers** - Autonomous AI agents powered by Claude (Anthropic) that can:
   - Interact via chat (WebSocket real-time + REST API)
   - Execute automation tasks (GUI automation via computer use)
   - Analyze code and perform security reviews
   - Execute shell commands
   - Edit files and manage knowledge

2. **Manages Agent Lifecycle** - Complete agent management including:
   - Agent creation, configuration, and deployment
   - Agent status monitoring and health checks
   - Agent coordination (parallel, sequential, conditional execution)
   - Configuration synchronization with Qube Platform

3. **Processes Tasks at Scale** - Distributed task processing:
   - RabbitMQ-based message queue for asynchronous task handling
   - Celery for distributed task scheduling
   - Multiple queue types (agent tasks, responses, system events, notifications, coordination)
   - Support for multiple task types (llm_request, code_analysis, chat_message, automation)

4. **Integrates with Qube Platform** - Seamless integration with enterprise platform:
   - Authentication via Qube API (JWT + OAuth2)
   - Remote configuration management
   - Subscription status validation
   - Agent registration and lifecycle management

## 3. PROGRAMMING LANGUAGES & TECH STACK

### Backend
- **Python 3.11+** - Primary language
  - FastAPI 0.104+ - Modern async API framework
  - SQLAlchemy 2.0+ - ORM for data persistence
  - Pydantic 2.0+ - Data validation
  - Celery 5.3+ - Distributed task processing
  - aio-pika 9.3+ - Async RabbitMQ client
  - structlog 23.2+ - Structured logging

### Message Queue & Communication
- **RabbitMQ 3.12+** - Primary message broker
  - Topic exchanges for routing
  - Direct exchanges for targeted messages
  - Persistent message storage
  - Queue binding with routing keys

### AI & Tools
- **Anthropic Claude API** - LLM provider (claude-sonnet-4-20250514)
- **pyautogui 0.9.54** - GUI automation
- **Beautiful Soup 4.12.3** - Web scraping
- **PyPDF2 3.0.1** - PDF extraction
- **Pillow 10.1.0** - Image processing
- **NumPy 1.26.2** - Numerical computing

### Infrastructure & Monitoring
- **Redis 7.0+** - Caching and session storage
- **PostgreSQL** (optional) - Database backend
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **OpenTelemetry** - Distributed tracing
- **Jaeger** - Distributed tracing backend

### Deployment
- **Docker** - Container deployment
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy, static file serving
- **Gunicorn** - Production WSGI server
- **Uvicorn** - ASGI application server

## 4. EXISTING AGENT/WORKER ARCHITECTURE

### Agent Types
Located in `/backend/data/agent_templates/`:
- **general-assistant.json** - Multi-purpose assistant
- **computer-specialist.json** - GUI automation expert
- **code-developer.json** - Software development specialist
- **research-analyst.json** - Data research and analysis
- **system-admin.json** - System administration

### Worker Types

1. **RabbitMQ LLM Worker** (`rabbitmq_llm_worker.py`)
   - Main worker consuming from `qilbee.agent_tasks` queue
   - Processes message types:
     - `llm_request` - Direct LLM queries
     - `code_analysis` - Code review/analysis
     - `chat_message` - Conversational chat
     - `automation` - GUI automation tasks
   - Publishes responses to `task.completed` and `task.failed` routing keys
   - Integrates with Qube API for subscription validation
   - Supports streaming output callbacks
   - Loads configuration remotely from Qube API at startup

2. **Celery Task Processor** (`task_processor.py`)
   - Async task queue for background processing
   - Routes to: `task_processing`, `llm_processing`, `system_monitoring` queues
   - Beat scheduler for periodic tasks:
     - System health checks (every 5 minutes)
     - Cleanup of completed tasks (hourly)

3. **Agent Coordinator** (`agent_coordinator.py`)
   - Manages multi-agent interactions
   - Coordination types:
     - Parallel execution
     - Sequential execution
     - Conditional execution (time-based, threshold, status-based)
   - Updates agent status via Qube API
   - Health monitoring for all active agents

4. **System Monitor** (`system_monitor.py`)
   - Periodic health checks
   - Metrics collection and reporting
   - Agent lifecycle monitoring

### Swarm Mode
- Enabled via configuration: `SWARM_MODE: bool`
- When enabled, worker processes queue tasks only
- Individual chat requests are disabled
- Configuration message shown to users

## 5. HOW WORKERS/AGENTS CURRENTLY COMMUNICATE

### Message Flow Architecture

```
User/External System
    |
    v
[FastAPI REST API + WebSocket]
    |
    +----------> [RabbitMQ Message Broker]
    |                    |
    |         +----------+----------+
    |         |                    |
    |    [Task Queue]         [Response Queue]
    |    (agent_tasks)        (agent_responses)
    |         |                    |
    |         v                    v
    |  [RabbitMQ LLM Worker]    [Client Connection]
    |         |
    +---------|
    |         |
    v         v
[Claude API] [Tool Execution]
```

### Queue Architecture

**Queue Names** (configured in `message_broker.py`):
1. `qilbee.agent_tasks` - Incoming task requests
2. `qilbee.agent_responses` - Task responses and completions
3. `qilbee.system_events` - System-level events
4. `qilbee.user_notifications` - User notifications
5. `qilbee.agent_coordination` - Agent-to-agent coordination

**Exchanges**:
- `qilbee` (Topic Exchange) - Main routing
- `qilbee.direct` (Direct Exchange) - Targeted messages
- `qilbee.topic` (Topic Exchange) - Pattern-based routing

**Routing Keys**:
- `task.created` → `qilbee.agent_tasks`
- `task.completed` → `qilbee.agent_responses`
- `task.failed` → `qilbee.agent_responses`
- `system.*` → `qilbee.system_events`
- `agent.*` → `qilbee.agent_coordination`

### Communication Protocols

1. **WebSocket** (Real-time, Bidirectional)
   - Client connects: `ws://localhost:8000/ws/chat?session_id=SESSION&token=JWT_TOKEN`
   - Uses `authenticate_websocket_token()` for authentication
   - Streaming responses sent via WebSocket
   - Supports multiple concurrent connections (max 1000 configurable)

2. **REST API**
   - POST `/api/v1/tasks` - Create task
   - GET `/api/v1/tasks/{task_id}` - Get task status
   - POST `/api/v1/chat/sessions` - Create chat session
   - POST `/api/v1/chat/{session_id}/messages` - Send message
   - GET `/api/v1/agents` - List agents

3. **RabbitMQ Direct Message Passing**
   - Used between workers and coordinator
   - Async message publishing/consuming
   - Manual acknowledgment (ack) for reliability
   - Automatic reconnection on failure

### Message Format

Standard wrapper for all RabbitMQ messages:
```json
{
  "id": "uuid-string",
  "timestamp": "2024-11-01T10:00:00.000Z",
  "routing_key": "task.created",
  "payload": {
    "task_id": "task-uuid",
    "type": "llm_request|code_analysis|chat_message|automation",
    "prompt": "User input",
    "context": [],
    "model": "claude-sonnet-4-20250514",
    "session_id": "optional-session-uuid"
  },
  "source": "qilbee-corporate"
}
```

## 6. KEY ENTRY POINTS & MAIN FILES

### Application Startup
1. **`run.py`** - Main application launcher
   - Starts FastAPI server (Uvicorn/Gunicorn)
   - Initializes RabbitMQ and Qube API connections
   - Sets up monitoring and logging
   - Loads configuration from Qube API (REQUIRED)

2. **`run_dev.py`** - Development server
   - Hot reload enabled
   - Debug logging enabled
   - Local testing without Docker

3. **`start_rabbitmq_llm_worker.py`** - Worker startup
   - Runs as separate process
   - Consumes from `qilbee.agent_tasks`
   - Can be containerized independently

### Main FastAPI Application
- **`app/main.py`** (11KB)
  - Lifespan management (startup/shutdown)
  - CORS, compression, authentication middleware
  - Prometheus metrics endpoints
  - WebSocket endpoint registration
  - Health check endpoints

### Critical Configuration
- **`app/core/config.py`** (360+ lines)
  - Pydantic Settings with environment variable support
  - RabbitMQ, Redis, Celery configuration
  - Qube Platform integration settings
  - Swarm mode configuration
  - Loads remote config from Qube API at startup

### API Routers
- **`app/api/v1/router.py`** - Main router aggregator
- **`app/api/v1/agents.py`** - Agent CRUD operations
- **`app/api/v1/tasks.py`** - Task management
- **`app/api/v1/chat.py`** - Chat sessions
- **`app/api/websocket.py`** (60KB) - WebSocket handler

### Service Layer
- **`app/services/message_broker.py`** (15KB) - RabbitMQ client
- **`app/services/anthropic_client.py`** (33KB) - Claude API wrapper
- **`app/services/chat_service.py`** - Chat history management
- **`app/services/qube_client.py`** (47KB) - Qube Platform API client
- **`app/services/auth_service.py`** - Authentication management

### Worker Implementation
- **`app/workers/rabbitmq_llm_worker.py`** - Main async worker
  - Consumes from RabbitMQ
  - Processes 4 task types
  - Calls `worker_loop()` for Claude API
  - Publishes responses back to queue

## 7. EXISTING MESSAGING/QUEUE SYSTEMS

### RabbitMQ-Based Messaging

**Core Message Broker Class** (`message_broker.py`):
- Singleton instance: `message_broker` (globally accessible)
- Methods:
  - `connect()` - Establish RabbitMQ connection
  - `publish_message(routing_key, message, exchange, priority)` - Send message
  - `consume_queue(queue_name, callback, auto_ack)` - Consume messages
  - `send_task_to_agent(agent_id, task_data)` - High-level task send
  - `send_task_response(task_id, agent_id, result, status)` - Response send
  - `broadcast_system_event(event_type, event_data)` - System event broadcast
  - `notify_user(user_id, notification)` - User notification
  - `coordinate_agents(coordination_message)` - Agent coordination
  - `health_check()` - Connection health verification
  - `get_queue_info(queue_name)` - Queue statistics
  - `purge_queue(queue_name)` - Clear queue messages

**Configuration**:
```python
RABBITMQ_HOST: str = "localhost"
RABBITMQ_PORT: int = 5672
RABBITMQ_USER: str = "guest"
RABBITMQ_PASSWORD: str = "guest"
RABBITMQ_VHOST: str = "/"
RABBITMQ_EXCHANGE: str = "qilbee"
RABBITMQ_QUEUE_PREFIX: str = "qilbee"
RABBITMQ_HEARTBEAT: int = 600
RABBITMQ_CONNECTION_TIMEOUT: int = 10
```

**Prefetch Settings**:
- QoS prefetch_count: 10 messages per worker
- Manual acknowledgment (ack) after processing
- Automatic reconnection on connection failure
- Persistent delivery mode for critical messages

### Celery Task Queue

**Celery Configuration** (`celery_app.py`):
- Broker: RabbitMQ (amqp://)
- Result Backend: Redis
- Task routing to 3 queues:
  - `task_processing` - General task processor
  - `llm_processing` - LLM-specific tasks
  - `system_monitoring` - Monitoring tasks

**Task Types**:
- `update_agent_status()` - Periodic agent status updates
- `coordinate_agent_tasks()` - Multi-agent coordination
- `sync_agent_configurations()` - Configuration sync
- `monitor_agent_health()` - Health monitoring
- `cleanup_completed_tasks()` - Periodic cleanup

**Beat Schedule**:
- System health check: Every 5 minutes
- Cleanup completed tasks: Every 1 hour

### Task Processing Flow

1. **Task Creation**
   - REST API: POST `/api/v1/tasks`
   - WebSocket: Send task message
   - Direct publish to `task.created` routing key

2. **Task Queuing**
   - RabbitMQ receives on `qilbee.agent_tasks` queue
   - Worker pulls task with prefetch_count=10

3. **Task Processing**
   - `rabbitmq_llm_worker.py` consumes message
   - Calls appropriate handler based on task type
   - Executes Claude API with tools
   - Streams responses via callbacks

4. **Response Publishing**
   - Publishes to `task.completed` or `task.failed`
   - WebSocket client receives via subscription
   - REST client polls `/api/v1/tasks/{task_id}`

### Notification System

- Dedicated `qilbee.user_notifications` queue
- Method: `notify_user(user_id, notification)`
- Routing key: `user.{user_id}.notification`
- Direct exchange for targeted delivery

## 8. DEPLOYMENT & DOCKER ARCHITECTURE

### Docker Setup
- **Base Image**: Ubuntu 22.04
- **Components**: 
  - X11 VNC server for GUI display
  - Nginx reverse proxy
  - Firefox, LibreOffice, X11 apps
  - Python 3.11.6 via pyenv
  - Cython compilation for performance

### Docker Compose Services
```yaml
qilbee-agent:
  - FastAPI API: 8000
  - Nginx proxy: 8080
  - VNC: 5900
  - Metrics: 8001
  - Health checks enabled
  - 2GB shared memory for X11
```

### Environment Variables (Key)
- `QILBEE_AGENT_API_KEY` - Qube Platform API key (REQUIRED)
- `QILBEE_AGENT_ID` - Agent identifier (REQUIRED)
- `ANTHROPIC_API_KEY` - Claude API key
- `QUBE_API_BASE_URL` - Qube Platform URL
- `RABBITMQ_HOST/PORT` - RabbitMQ connection
- `REDIS_URL` - Redis connection
- `DEFAULT_MODEL` - Claude model (claude-sonnet-4-20250514)
- `SWARM_MODE` - Enable/disable swarm operation mode

## 9. PERFORMANCE & MONITORING

### Metrics Collection
- Prometheus client integration
- Metrics endpoint: `GET /metrics`
- Tracked metrics:
  - Request count (method, endpoint, status)
  - Request duration (histogram)
  - Active agent count
  - Task execution metrics
  - Error rates

### Health Checks
- `GET /health` - General health
- `GET /ready` - Readiness probe
- RabbitMQ connection test on startup
- Qube API connectivity test on startup

### Logging
- **structlog** for structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log output: File + stdout
- Audit logs for editor/computer tool usage

---

## SUMMARY FOR MYCELIAL NETWORK INTEGRATION

This is a **production-ready, distributed AI worker platform** with:
- **Multi-channel communication** (REST, WebSocket, RabbitMQ)
- **Enterprise authentication** (Qube API integration)
- **Scalable architecture** (RabbitMQ + Celery)
- **AI-powered automation** (Claude API with computer use)
- **Comprehensive monitoring** (Prometheus, structured logging)
- **Multi-agent support** (Agent coordinator for complex workflows)
- **Subscription-aware** (Validates Qube Platform subscription status)

Perfect foundation for Qilbee Mycelial Network integration as a standardized worker node with full queue-based communication support.
