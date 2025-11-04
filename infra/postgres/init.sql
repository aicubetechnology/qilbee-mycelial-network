-- ================================================================
-- QMN (Qilbee Mycelial Network) - PostgreSQL Initialization
-- PostgreSQL 16 + pgvector
-- ================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- TABLE 1: TENANTS
-- ================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    plan_tier VARCHAR(50) DEFAULT 'free',
    status VARCHAR(50) DEFAULT 'active',
    kms_key_id VARCHAR(255),
    region_preference VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_tenants_status ON tenants(status);

-- ================================================================
-- TABLE 2: API_KEYS
-- ================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    scopes TEXT[] DEFAULT ARRAY['*'],
    rate_limit_per_minute INTEGER DEFAULT 1000,
    status VARCHAR(50) DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_api_keys_tenant_id ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- ================================================================
-- TABLE 3: HYPHAE_EDGES
-- ================================================================
CREATE TABLE IF NOT EXISTS hyphae_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_agent_id VARCHAR(255) NOT NULL,
    target_agent_id VARCHAR(255) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    interaction_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, source_agent_id, target_agent_id)
);
CREATE INDEX idx_hyphae_edges_tenant_id ON hyphae_edges(tenant_id);
CREATE INDEX idx_hyphae_edges_source ON hyphae_edges(source_agent_id);
CREATE INDEX idx_hyphae_edges_weight ON hyphae_edges(weight DESC);

-- ================================================================
-- TABLE 4: HYPHAL_MEMORY (with pgvector)
-- ================================================================
CREATE TABLE IF NOT EXISTS hyphal_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    trace_id UUID NOT NULL,
    kind VARCHAR(50),
    summary TEXT NOT NULL,
    content TEXT,
    embedding vector(1536) NOT NULL,
    quality_score FLOAT DEFAULT 0.5,
    sensitivity VARCHAR(50) DEFAULT 'internal',
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_hyphal_memory_tenant_id ON hyphal_memory(tenant_id);
CREATE INDEX idx_hyphal_memory_agent_id ON hyphal_memory(agent_id);
CREATE INDEX idx_hyphal_memory_embedding ON hyphal_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ================================================================
-- TABLE 5: NUTRIENTS_ACTIVE (with pgvector)
-- ================================================================
CREATE TABLE IF NOT EXISTS nutrients_active (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    trace_id UUID NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    snippets JSONB DEFAULT '[]'::jsonb,
    tool_hints TEXT[] DEFAULT ARRAY[]::TEXT[],
    ttl_seconds INTEGER DEFAULT 300,
    max_hops INTEGER DEFAULT 5,
    sensitivity VARCHAR(50) DEFAULT 'internal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '300 seconds')
);
CREATE INDEX idx_nutrients_active_tenant_id ON nutrients_active(tenant_id);
CREATE INDEX idx_nutrients_active_expires_at ON nutrients_active(expires_at);
CREATE INDEX idx_nutrients_active_embedding ON nutrients_active USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- ================================================================
-- TABLE 6: NUTRIENT_ROUTES
-- ================================================================
CREATE TABLE IF NOT EXISTS nutrient_routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    trace_id UUID NOT NULL,
    nutrient_id UUID NOT NULL,
    source_agent_id VARCHAR(255) NOT NULL,
    target_agent_id VARCHAR(255) NOT NULL,
    similarity_score FLOAT,
    edge_weight FLOAT,
    selected BOOLEAN DEFAULT FALSE,
    outcome_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_nutrient_routes_tenant_id ON nutrient_routes(tenant_id);
CREATE INDEX idx_nutrient_routes_trace_id ON nutrient_routes(trace_id);

-- ================================================================
-- TABLE 7: AUDIT_EVENTS
-- ================================================================
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_audit_events_tenant_id ON audit_events(tenant_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at DESC);

-- ================================================================
-- TABLE 8: QUOTA_CONFIGS
-- ================================================================
CREATE TABLE IF NOT EXISTS quota_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE UNIQUE,
    nutrients_per_hour INTEGER DEFAULT 10000,
    contexts_per_hour INTEGER DEFAULT 5000,
    memory_searches_per_hour INTEGER DEFAULT 20000,
    storage_mb INTEGER DEFAULT 10240,
    max_agents INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_quota_configs_tenant_id ON quota_configs(tenant_id);

-- ================================================================
-- TABLE 9: USAGE_METRICS
-- ================================================================
CREATE TABLE IF NOT EXISTS usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    nutrients_sent INTEGER DEFAULT 0,
    contexts_collected INTEGER DEFAULT 0,
    memory_searches INTEGER DEFAULT 0,
    storage_used_mb FLOAT DEFAULT 0.0,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_usage_metrics_tenant_id ON usage_metrics(tenant_id);
CREATE INDEX idx_usage_metrics_window_start ON usage_metrics(window_start DESC);

-- ================================================================
-- INITIAL DATA
-- ================================================================

-- Insert default tenant
INSERT INTO tenants (id, name, plan_tier, status)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Default Tenant',
    'enterprise',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Insert default quota config
INSERT INTO quota_configs (tenant_id, nutrients_per_hour, contexts_per_hour, memory_searches_per_hour, storage_mb, max_agents)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    10000,
    5000,
    20000,
    10240,
    100
) ON CONFLICT (tenant_id) DO NOTHING;

-- ================================================================
-- COMPLETION
-- ================================================================
SELECT 'QMN PostgreSQL initialization completed successfully!' AS status;
SELECT COUNT(*) AS tenant_count FROM tenants;
SELECT COUNT(*) AS quota_count FROM quota_configs;
