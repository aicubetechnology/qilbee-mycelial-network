-- Qilbee Mycelial Network Database Schema
-- PostgreSQL 16+ with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- ============================================================================
-- TABLES: Core Network Topology
-- ============================================================================

-- Hyphae edges representing connections between agents
CREATE TABLE hyphae_edges (
    tenant_id TEXT NOT NULL,
    src TEXT NOT NULL,                    -- Source agent ID
    dst TEXT NOT NULL,                    -- Destination agent ID
    w REAL DEFAULT 0.1 CHECK (w >= 0.01 AND w <= 1.5),  -- Edge weight/strength
    sim REAL DEFAULT 0.0 CHECK (sim >= 0.0 AND sim <= 1.0),  -- Base similarity
    r_success REAL DEFAULT 0.0,           -- Cumulative success reinforcement
    r_decay REAL DEFAULT 0.0,             -- Cumulative decay
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    PRIMARY KEY (tenant_id, src, dst)
);

-- Indices for edge queries
CREATE INDEX idx_edges_tenant_src ON hyphae_edges(tenant_id, src, last_update DESC);
CREATE INDEX idx_edges_tenant_dst ON hyphae_edges(tenant_id, dst, last_update DESC);
CREATE INDEX idx_edges_weight ON hyphae_edges(tenant_id, w DESC);

-- ============================================================================
-- TABLES: Hyphal Memory (Vector Store)
-- ============================================================================

-- Distributed memory storage with embeddings
CREATE TABLE hyphal_memory (
    tenant_id TEXT NOT NULL,
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT NOT NULL,
    task_id TEXT,
    trace_id TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('insight', 'snippet', 'tool_hint', 'plan', 'outcome')),
    content JSONB NOT NULL,
    embedding VECTOR(1536) NOT NULL,      -- OpenAI ada-002 / text-embedding-3 dimensions
    quality REAL DEFAULT 0.0 CHECK (quality >= 0.0 AND quality <= 1.0),
    sensitivity TEXT DEFAULT 'internal' CHECK (sensitivity IN ('public', 'internal', 'confidential', 'secret')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Vector similarity index (IVFFlat for large-scale)
CREATE INDEX hyphal_memory_vec_idx
ON hyphal_memory
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Traditional indices
CREATE INDEX idx_memory_tenant_created ON hyphal_memory(tenant_id, created_at DESC);
CREATE INDEX idx_memory_tenant_agent ON hyphal_memory(tenant_id, agent_id);
CREATE INDEX idx_memory_kind ON hyphal_memory(tenant_id, kind);
CREATE INDEX idx_memory_quality ON hyphal_memory(tenant_id, quality DESC);
CREATE INDEX idx_memory_trace ON hyphal_memory(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_memory_expiration ON hyphal_memory(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- TABLES: Tenants & Identity
-- ============================================================================

-- Tenant organizations
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plan_tier TEXT DEFAULT 'free' CHECK (plan_tier IN ('free', 'pro', 'enterprise')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    kms_key_id TEXT,                      -- Customer-managed encryption key
    region_preference TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_plan ON tenants(plan_tier);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE,        -- SHA-256 hash of API key
    key_prefix TEXT NOT NULL,             -- First 8 chars for identification
    name TEXT,
    scopes JSONB DEFAULT '["*"]',         -- API scopes
    rate_limit_per_minute INTEGER DEFAULT 1000,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired')),
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_keys_status ON api_keys(status);

-- ============================================================================
-- TABLES: Usage & Quotas
-- ============================================================================

-- Usage metrics (time-series like)
CREATE TABLE usage_metrics (
    tenant_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,           -- 'nutrients_sent', 'contexts_collected', etc.
    value BIGINT NOT NULL DEFAULT 0,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    region TEXT,
    metadata JSONB DEFAULT '{}',

    PRIMARY KEY (tenant_id, metric_type, window_start)
);

CREATE INDEX idx_usage_tenant_window ON usage_metrics(tenant_id, window_start DESC);
CREATE INDEX idx_usage_metric_type ON usage_metrics(metric_type, window_start DESC);

-- Quota configurations
CREATE TABLE quota_configs (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    nutrients_per_hour INTEGER DEFAULT 10000,
    contexts_per_hour INTEGER DEFAULT 5000,
    memory_searches_per_hour INTEGER DEFAULT 20000,
    storage_mb INTEGER DEFAULT 10240,       -- 10 GB default
    max_agents INTEGER DEFAULT 100,
    custom_limits JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLES: Audit & Compliance
-- ============================================================================

-- Audit events with cryptographic signatures
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor_id TEXT,                        -- Agent or user ID
    resource_type TEXT,
    resource_id TEXT,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'failure', 'denied')),
    details JSONB DEFAULT '{}',
    signature TEXT,                       -- Ed25519 signature
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant_created ON audit_events(tenant_id, created_at DESC);
CREATE INDEX idx_audit_type ON audit_events(event_type, created_at DESC);
CREATE INDEX idx_audit_actor ON audit_events(actor_id, created_at DESC);
CREATE INDEX idx_audit_outcome ON audit_events(outcome, created_at DESC);

-- Data retention policies
CREATE TABLE retention_policies (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    ephemeral_data_hours INTEGER DEFAULT 24,
    operational_data_days INTEGER DEFAULT 90,
    audit_data_years INTEGER DEFAULT 1,
    compliance_data_years INTEGER DEFAULT 5,
    auto_delete BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLES: Nutrient Flow Tracking
-- ============================================================================

-- Active nutrients in transit
CREATE TABLE nutrients_active (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    snippets JSONB DEFAULT '[]',
    tool_hints JSONB DEFAULT '[]',
    sensitivity TEXT NOT NULL CHECK (sensitivity IN ('public', 'internal', 'confidential', 'secret')),
    current_hop INTEGER DEFAULT 0,
    max_hops INTEGER NOT NULL,
    ttl_sec INTEGER NOT NULL,
    quota_cost INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_nutrients_tenant ON nutrients_active(tenant_id, expires_at);
CREATE INDEX idx_nutrients_trace ON nutrients_active(trace_id);
CREATE INDEX idx_nutrients_expiration ON nutrients_active(expires_at);

-- Nutrient routing history (for reinforcement learning)
CREATE TABLE nutrient_routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL,
    nutrient_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    src_agent TEXT NOT NULL,
    dst_agent TEXT NOT NULL,
    hop_number INTEGER NOT NULL,
    routing_score REAL,
    routed_at TIMESTAMP DEFAULT NOW(),
    outcome_score REAL,                   -- Set when outcome recorded
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_routes_trace ON nutrient_routes(trace_id);
CREATE INDEX idx_routes_tenant_time ON nutrient_routes(tenant_id, routed_at DESC);
CREATE INDEX idx_routes_edge ON nutrient_routes(tenant_id, src_agent, dst_agent);

-- ============================================================================
-- FUNCTIONS: Maintenance & Utilities
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER trigger_update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_update_hyphal_memory_updated_at
    BEFORE UPDATE ON hyphal_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Cleanup expired nutrients
CREATE OR REPLACE FUNCTION cleanup_expired_nutrients()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM nutrients_active WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Cleanup expired memory based on retention policies
CREATE OR REPLACE FUNCTION cleanup_expired_memory()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM hyphal_memory WHERE expires_at IS NOT NULL AND expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Vector similarity search helper
CREATE OR REPLACE FUNCTION search_similar_memories(
    p_tenant_id TEXT,
    p_embedding VECTOR(1536),
    p_top_k INTEGER DEFAULT 10,
    p_min_quality REAL DEFAULT 0.0
)
RETURNS TABLE (
    id UUID,
    agent_id TEXT,
    kind TEXT,
    content JSONB,
    similarity REAL,
    quality REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        hm.id,
        hm.agent_id,
        hm.kind,
        hm.content,
        1 - (hm.embedding <=> p_embedding) AS similarity,
        hm.quality
    FROM hyphal_memory hm
    WHERE hm.tenant_id = p_tenant_id
      AND hm.quality >= p_min_quality
      AND (hm.expires_at IS NULL OR hm.expires_at > NOW())
    ORDER BY hm.embedding <=> p_embedding
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROW LEVEL SECURITY (Multi-Tenant Isolation)
-- ============================================================================

-- Enable RLS on critical tables
ALTER TABLE hyphae_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE hyphal_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrients_active ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies (example - requires app to set current tenant)
CREATE POLICY tenant_isolation_edges ON hyphae_edges
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', TRUE));

CREATE POLICY tenant_isolation_memory ON hyphal_memory
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', TRUE));

CREATE POLICY tenant_isolation_nutrients ON nutrients_active
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', TRUE));

CREATE POLICY tenant_isolation_audit ON audit_events
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', TRUE));

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Default tenant for development
INSERT INTO tenants (id, name, plan_tier, status)
VALUES ('dev-tenant', 'Development Tenant', 'enterprise', 'active')
ON CONFLICT (id) DO NOTHING;

-- Default quota config
INSERT INTO quota_configs (tenant_id)
VALUES ('dev-tenant')
ON CONFLICT (tenant_id) DO NOTHING;

-- Default retention policy
INSERT INTO retention_policies (tenant_id)
VALUES ('dev-tenant')
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE hyphae_edges IS 'Network topology edges with reinforcement learning weights';
COMMENT ON TABLE hyphal_memory IS 'Distributed vector memory for agent knowledge';
COMMENT ON TABLE tenants IS 'Tenant organizations with plan and encryption settings';
COMMENT ON TABLE api_keys IS 'API authentication keys with scopes and rate limits';
COMMENT ON TABLE audit_events IS 'Cryptographically signed audit trail';
COMMENT ON TABLE nutrients_active IS 'Currently propagating nutrients through network';
COMMENT ON TABLE nutrient_routes IS 'Historical routing decisions for reinforcement learning';

-- ============================================================================
-- PERFORMANCE TUNING
-- ============================================================================

-- Autovacuum settings for high-write tables
ALTER TABLE nutrient_routes SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE usage_metrics SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Statistics for query planning
ALTER TABLE hyphal_memory ALTER COLUMN embedding SET STATISTICS 1000;
ALTER TABLE hyphae_edges ALTER COLUMN w SET STATISTICS 500;
