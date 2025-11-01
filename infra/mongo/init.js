// Qilbee Mycelial Network - MongoDB Schema
// Collections for agents, policies, and events

// Switch to QMN database
db = db.getSiblingDB('qmn');

// ============================================================================
// COLLECTION: agents
// Agent profiles with capabilities, embeddings, and neighbor relationships
// ============================================================================

db.createCollection('agents', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['_id', 'tenant_id', 'capabilities', 'profile'],
      properties: {
        _id: {
          bsonType: 'string',
          description: 'Unique agent identifier (e.g., agent:juridico-1)'
        },
        tenant_id: {
          bsonType: 'string',
          description: 'Tenant organization ID'
        },
        name: {
          bsonType: 'string',
          description: 'Human-readable agent name'
        },
        capabilities: {
          bsonType: 'array',
          items: { bsonType: 'string' },
          description: 'List of agent capabilities/skills'
        },
        tools: {
          bsonType: 'array',
          items: { bsonType: 'string' },
          description: 'Available tools for this agent'
        },
        profile: {
          bsonType: 'object',
          required: ['embedding'],
          properties: {
            embedding: {
              bsonType: 'array',
              items: { bsonType: 'double' },
              description: '1536-dimensional profile embedding'
            },
            skills: {
              bsonType: 'array',
              items: { bsonType: 'string' }
            },
            description: { bsonType: 'string' }
          }
        },
        metrics: {
          bsonType: 'object',
          properties: {
            tasks_completed_30d: { bsonType: 'int' },
            tasks_completed_all_time: { bsonType: 'int' },
            avg_success: { bsonType: 'double' },
            last_active: { bsonType: 'date' }
          }
        },
        neighbors: {
          bsonType: 'array',
          items: {
            bsonType: 'object',
            required: ['id', 'w', 'sim'],
            properties: {
              id: { bsonType: 'string' },
              w: { bsonType: 'double', minimum: 0.01, maximum: 1.5 },
              sim: { bsonType: 'double', minimum: 0.0, maximum: 1.0 },
              last: { bsonType: 'date' }
            }
          },
          description: 'Direct neighbor connections with weights'
        },
        quota: {
          bsonType: 'object',
          properties: {
            kb_hour: { bsonType: 'int' },
            msg_min: { bsonType: 'int' }
          }
        },
        status: {
          enum: ['active', 'idle', 'suspended'],
          description: 'Current agent status'
        },
        region: {
          bsonType: 'string',
          description: 'Deployment region'
        },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Indices for agents collection
db.agents.createIndex({ tenant_id: 1, status: 1 });
db.agents.createIndex({ tenant_id: 1, 'capabilities': 1 });
db.agents.createIndex({ tenant_id: 1, 'tools': 1 });
db.agents.createIndex({ 'metrics.avg_success': -1 });
db.agents.createIndex({ 'metrics.last_active': -1 });
db.agents.createIndex({ updated_at: -1 });

// ============================================================================
// COLLECTION: policies
// DLP, RBAC, and ABAC policy configurations
// ============================================================================

db.createCollection('policies', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['_id', 'tenant_id', 'policy_type'],
      properties: {
        _id: {
          bsonType: 'string',
          description: 'Policy identifier (e.g., policy:acme:dlp)'
        },
        tenant_id: { bsonType: 'string' },
        policy_type: {
          enum: ['dlp', 'rbac', 'abac', 'rate_limit', 'content_filter'],
          description: 'Type of policy'
        },
        name: { bsonType: 'string' },
        description: { bsonType: 'string' },
        enabled: {
          bsonType: 'bool',
          description: 'Whether policy is active'
        },
        sensitivity_rules: {
          bsonType: 'object',
          description: 'DLP sensitivity classification rules',
          properties: {
            public: { bsonType: 'object' },
            internal: { bsonType: 'object' },
            confidential: { bsonType: 'object' },
            secret: { bsonType: 'object' }
          }
        },
        rbac_roles: {
          bsonType: 'object',
          description: 'Role-based access control definitions',
          additionalProperties: {
            bsonType: 'object',
            properties: {
              permissions: { bsonType: 'array', items: { bsonType: 'string' } },
              scopes: { bsonType: 'array', items: { bsonType: 'string' } }
            }
          }
        },
        capability_matrix: {
          bsonType: 'object',
          description: 'Capability-based access matrix'
        },
        conditions: {
          bsonType: 'array',
          items: { bsonType: 'object' },
          description: 'ABAC conditional rules'
        },
        actions: {
          bsonType: 'object',
          properties: {
            allow: { bsonType: 'array', items: { bsonType: 'string' } },
            deny: { bsonType: 'array', items: { bsonType: 'string' } },
            log: { bsonType: 'bool' },
            alert: { bsonType: 'bool' }
          }
        },
        version: { bsonType: 'int' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Indices for policies collection
db.policies.createIndex({ tenant_id: 1, policy_type: 1, enabled: 1 });
db.policies.createIndex({ tenant_id: 1, enabled: 1 });
db.policies.createIndex({ version: -1 });

// ============================================================================
// COLLECTION: events
// Real-time events and audit trail with signatures
// ============================================================================

db.createCollection('events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['tenant_id', 'trace_id', 'type', 'timestamp'],
      properties: {
        tenant_id: { bsonType: 'string' },
        trace_id: { bsonType: 'string' },
        nutrient_id: { bsonType: 'string' },
        type: {
          enum: [
            'nutrient_broadcast',
            'nutrient_routed',
            'nutrient_received',
            'nutrient_expired',
            'context_collected',
            'outcome_recorded',
            'policy_checked',
            'policy_blocked',
            'agent_registered',
            'agent_deactivated'
          ],
          description: 'Event type'
        },
        outcome: {
          enum: ['allowed', 'denied', 'error'],
          description: 'Event outcome'
        },
        agent_id: { bsonType: 'string' },
        source_agent: { bsonType: 'string' },
        target_agent: { bsonType: 'string' },
        policy_checks: {
          bsonType: 'object',
          description: 'Policy evaluation results'
        },
        details: {
          bsonType: 'object',
          description: 'Event-specific details'
        },
        signature: {
          bsonType: 'string',
          description: 'Ed25519 cryptographic signature'
        },
        ip_address: { bsonType: 'string' },
        region: { bsonType: 'string' },
        timestamp: { bsonType: 'date' }
      }
    }
  },
  timeseries: {
    timeField: 'timestamp',
    metaField: 'tenant_id',
    granularity: 'seconds'
  }
});

// Indices for events collection
db.events.createIndex({ tenant_id: 1, timestamp: -1 });
db.events.createIndex({ trace_id: 1 });
db.events.createIndex({ type: 1, timestamp: -1 });
db.events.createIndex({ outcome: 1, timestamp: -1 });
db.events.createIndex({ agent_id: 1, timestamp: -1 });

// TTL index for automatic event cleanup (90 days)
db.events.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 });

// ============================================================================
// COLLECTION: tasks
// Task tracking and context for reinforcement learning
// ============================================================================

db.createCollection('tasks', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['_id', 'tenant_id', 'status'],
      properties: {
        _id: { bsonType: 'string' },
        tenant_id: { bsonType: 'string' },
        trace_id: { bsonType: 'string' },
        agent_id: { bsonType: 'string' },
        status: {
          enum: ['pending', 'in_progress', 'completed', 'failed'],
          description: 'Task status'
        },
        task_type: { bsonType: 'string' },
        description: { bsonType: 'string' },
        nutrients_broadcast: {
          bsonType: 'array',
          items: { bsonType: 'string' },
          description: 'Nutrient IDs sent for this task'
        },
        contexts_collected: {
          bsonType: 'array',
          items: { bsonType: 'object' },
          description: 'Contexts collected from network'
        },
        outcome: {
          bsonType: 'object',
          properties: {
            score: { bsonType: 'double', minimum: 0.0, maximum: 1.0 },
            feedback: { bsonType: 'string' },
            metadata: { bsonType: 'object' }
          }
        },
        duration_ms: { bsonType: 'int' },
        created_at: { bsonType: 'date' },
        completed_at: { bsonType: 'date' }
      }
    }
  }
});

// Indices for tasks collection
db.tasks.createIndex({ tenant_id: 1, status: 1, created_at: -1 });
db.tasks.createIndex({ trace_id: 1 });
db.tasks.createIndex({ agent_id: 1, created_at: -1 });
db.tasks.createIndex({ 'outcome.score': -1 });

// ============================================================================
// COLLECTION: regional_state
// Regional node state for gossip protocol
// ============================================================================

db.createCollection('regional_state', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['_id', 'region', 'status'],
      properties: {
        _id: {
          bsonType: 'string',
          description: 'Region identifier (e.g., region:us-east-1)'
        },
        region: { bsonType: 'string' },
        status: {
          enum: ['healthy', 'degraded', 'unavailable'],
          description: 'Region health status'
        },
        active_agents: { bsonType: 'int' },
        active_tenants: { bsonType: 'int' },
        capacity: {
          bsonType: 'object',
          properties: {
            cpu_percent: { bsonType: 'double' },
            memory_percent: { bsonType: 'double' },
            requests_per_sec: { bsonType: 'int' }
          }
        },
        neighbors: {
          bsonType: 'array',
          items: {
            bsonType: 'object',
            properties: {
              region: { bsonType: 'string' },
              latency_ms: { bsonType: 'int' },
              last_sync: { bsonType: 'date' }
            }
          }
        },
        version: { bsonType: 'int' },
        last_heartbeat: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Indices for regional_state collection
db.regional_state.createIndex({ status: 1 });
db.regional_state.createIndex({ last_heartbeat: -1 });

// ============================================================================
// SAMPLE DATA for Development
// ============================================================================

// Sample agent
db.agents.insertOne({
  _id: 'agent:dev-1',
  tenant_id: 'dev-tenant',
  name: 'Development Agent 1',
  capabilities: ['code_review', 'testing', 'documentation'],
  tools: ['git.analyze', 'test.run', 'docs.generate'],
  profile: {
    embedding: Array(1536).fill(0.1),
    skills: ['python', 'javascript', 'devops'],
    description: 'General purpose development agent'
  },
  metrics: {
    tasks_completed_30d: 150,
    tasks_completed_all_time: 500,
    avg_success: 0.87,
    last_active: new Date()
  },
  neighbors: [],
  quota: {
    kb_hour: 2000,
    msg_min: 10
  },
  status: 'active',
  region: 'us-east-1',
  created_at: new Date(),
  updated_at: new Date()
});

// Sample DLP policy
db.policies.insertOne({
  _id: 'policy:dev-tenant:dlp',
  tenant_id: 'dev-tenant',
  policy_type: 'dlp',
  name: 'Default DLP Policy',
  description: 'Data loss prevention rules',
  enabled: true,
  sensitivity_rules: {
    public: {
      allowed_agents: ['*'],
      allowed_tools: ['*']
    },
    internal: {
      allowed_agents: ['*'],
      allowed_tools: ['*'],
      require_audit: true
    },
    confidential: {
      allowed_agents: ['finance.*', 'legal.*'],
      allowed_tools: ['secure.*'],
      require_audit: true,
      require_encryption: true
    },
    secret: {
      allowed_agents: ['security.*'],
      allowed_tools: ['vault.*'],
      require_audit: true,
      require_encryption: true,
      require_approval: true
    }
  },
  actions: {
    allow: ['log'],
    deny: ['log', 'alert'],
    log: true,
    alert: true
  },
  version: 1,
  created_at: new Date(),
  updated_at: new Date()
});

// Sample regional state
db.regional_state.insertOne({
  _id: 'region:us-east-1',
  region: 'us-east-1',
  status: 'healthy',
  active_agents: 10,
  active_tenants: 5,
  capacity: {
    cpu_percent: 45.2,
    memory_percent: 62.1,
    requests_per_sec: 1250
  },
  neighbors: [
    { region: 'us-west-1', latency_ms: 65, last_sync: new Date() },
    { region: 'eu-west-1', latency_ms: 95, last_sync: new Date() }
  ],
  version: 1,
  last_heartbeat: new Date(),
  updated_at: new Date()
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

print('QMN MongoDB schema initialized successfully');
print('Collections created: agents, policies, events, tasks, regional_state');
print('Sample data inserted for development');
