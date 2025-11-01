# Qilbee Mycelial Network (QMN) Integration Guide
## For Qilbee Worker Command Center V2

**Target Audience**: Development team integrating QMN into the React/TypeScript Command Center
**Last Updated**: November 1, 2025
**QMN Version**: 1.0
**Command Center**: React 18 + TypeScript + Vite

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Integration](#architecture-integration)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Service Module Creation](#service-module-creation)
6. [API Client Integration](#api-client-integration)
7. [React Hooks](#react-hooks)
8. [UI Components](#ui-components)
9. [Complete Examples](#complete-examples)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### What is QMN?

The **Qilbee Mycelial Network (QMN)** is a bio-inspired distributed knowledge-sharing system that enables AI agents to:

- **Share knowledge instantly** through ephemeral nutrient broadcasting
- **Store persistent memories** with quality scoring
- **Search semantically** using vector embeddings
- **Collaborate across boundaries** without centralized coordination

### How QMN Integrates with Command Center

Your Command Center currently manages:
- ✅ Agents (creation, monitoring, control)
- ✅ Tasks and workflows
- ✅ Chat sessions
- ✅ User and company management

**QMN adds**:
- ✨ **Agent knowledge sharing** - Agents share insights and findings
- ✨ **Cross-agent memory** - Persistent knowledge base across all agents
- ✨ **Semantic search** - Find relevant knowledge by meaning, not keywords
- ✨ **Real-time collaboration** - Agents broadcast discoveries to the network

---

## Architecture Integration

### Current Command Center Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Center Frontend                   │
│              (React + TypeScript + Vite)                     │
├─────────────────────────────────────────────────────────────┤
│  Components          Services           Pages                │
│  • Agents            • ApiClient        • AgentsPage         │
│  • Tasks             • AuthService      • TasksPage          │
│  • Chat              • AgentService     • ConversationsPage  │
│  • Workflows         • TaskService      • WorkflowPage       │
└────────────────────┬────────────────────────────────────────┘
                      │
                      │ HTTP/WebSocket
                      ▼
           ┌──────────────────────┐
           │   Backend API         │
           │   (Your existing)     │
           └──────────────────────┘
```

### Integrated Architecture with QMN

```
┌──────────────────────────────────────────────────────────────────┐
│                    Command Center Frontend                        │
│                 (React + TypeScript + Vite)                       │
├──────────────────────────────────────────────────────────────────┤
│  Components            Services              Pages                │
│  • Agents              • ApiClient           • AgentsPage         │
│  • Tasks               • AuthService         • TasksPage          │
│  • Chat                • AgentService        • ConversationsPage  │
│  • Workflows           • TaskService         • WorkflowPage       │
│  • KnowledgeShare ✨   • QmnService ✨       • KnowledgePage ✨  │
│  • MemoryBrowser ✨                                               │
└────────────────┬─────────────────────────┬───────────────────────┘
                  │                          │
                  │ HTTP/WebSocket          │ HTTP (QMN API)
                  ▼                          ▼
       ┌──────────────────┐        ┌──────────────────────────┐
       │   Backend API     │        │  QMN Services            │
       │  (Your existing)  │        │  • Identity Service      │
       └──────────────────┘        │  • Router (Broadcast)    │
                                    │  • Hyphal Memory         │
                                    │  • Policies              │
                                    └──────────────────────────┘
```

---

## Prerequisites

### 1. QMN Services Running

Ensure QMN services are deployed and accessible:

```bash
# Navigate to QMN directory
cd /Users/kimera/projects/qilbee-mycelial-network

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check health
curl http://localhost:8001/health  # Identity Service
curl http://localhost:8003/health  # Router Service
curl http://localhost:8004/health  # Hyphal Memory Service
```

### 2. Environment Variables

Add QMN configuration to your Command Center `.env.development`:

```bash
# Qilbee Mycelial Network Configuration
VITE_QMN_BASE_URL=http://localhost:8000  # Adjust for production
VITE_QMN_IDENTITY_URL=http://localhost:8001
VITE_QMN_KEYS_URL=http://localhost:8002
VITE_QMN_ROUTER_URL=http://localhost:8003
VITE_QMN_MEMORY_URL=http://localhost:8004
VITE_QMN_POLICIES_URL=http://localhost:8005

# Your QMN tenant ID (create via Identity Service)
VITE_QMN_TENANT_ID=your-tenant-id-here
```

### 3. Dependencies

QMN uses standard HTTP APIs - no additional npm packages required! Your existing stack works:

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.56.2",  // ✅ Already installed
    "react": "^18.3.1",                   // ✅ Already installed
    "react-router-dom": "^6.26.2"         // ✅ Already installed
  }
}
```

---

## Quick Start

### Step 1: Create QMN Service Module

Create `/src/services/modules/QmnService.ts`:

```typescript
import { HttpClient } from '../core/HttpClient';

export interface TenantCreateRequest {
  id: string;
  name: string;
  plan_tier: 'free' | 'pro' | 'enterprise';
  kms_key_id: string;
  region_preference?: string;
  metadata?: Record<string, any>;
}

export interface BroadcastRequest {
  summary: string;
  embedding: number[];
  snippets: string[];
  tool_hints: string[];
  sensitivity: 'public' | 'internal' | 'confidential';
  max_hops: number;
  ttl_sec: number;
  quota_cost: number;
}

export interface MemoryStoreRequest {
  agent_id: string;
  kind: 'insight' | 'snippet' | 'decision' | 'preference';
  content: Record<string, any>;
  quality: number;
  sensitivity: 'public' | 'internal' | 'confidential';
  metadata?: Record<string, any>;
  embedding: number[];
  expires_at?: string;
}

export interface MemorySearchRequest {
  embedding: number[];
  min_quality?: number;
  limit?: number;
  kind_filter?: string;
}

export class QmnService extends HttpClient {
  private identityBaseUrl: string;
  private routerBaseUrl: string;
  private memoryBaseUrl: string;
  private tenantId: string;

  constructor(
    identityUrl?: string,
    routerUrl?: string,
    memoryUrl?: string,
    tenantId?: string
  ) {
    super(identityUrl);
    this.identityBaseUrl = identityUrl || import.meta.env.VITE_QMN_IDENTITY_URL;
    this.routerBaseUrl = routerUrl || import.meta.env.VITE_QMN_ROUTER_URL;
    this.memoryBaseUrl = memoryUrl || import.meta.env.VITE_QMN_MEMORY_URL;
    this.tenantId = tenantId || import.meta.env.VITE_QMN_TENANT_ID;
  }

  // ===== Tenant Management =====

  async createTenant(request: TenantCreateRequest) {
    return this.request(`${this.identityBaseUrl}/v1/tenants`, {
      method: 'POST',
      body: JSON.stringify(request),
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async getTenant(tenantId?: string) {
    const id = tenantId || this.tenantId;
    return this.request(`${this.identityBaseUrl}/v1/tenants/${id}`, {
      method: 'GET'
    });
  }

  // ===== Knowledge Broadcasting (Ephemeral) =====

  async broadcastKnowledge(
    traceId: string,
    request: BroadcastRequest
  ) {
    return this.request(
      `${this.routerBaseUrl}/v1/broadcast/${this.tenantId}/${traceId}`,
      {
        method: 'POST',
        body: JSON.stringify(request),
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  // ===== Memory Storage (Persistent) =====

  async storeMemory(request: MemoryStoreRequest) {
    return this.request(
      `${this.memoryBaseUrl}/v1/hyphal/${this.tenantId}`,
      {
        method: 'POST',
        body: JSON.stringify(request),
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  async searchMemories(request: MemorySearchRequest) {
    return this.request(
      `${this.memoryBaseUrl}/v1/hyphal:search/${this.tenantId}`,
      {
        method: 'POST',
        body: JSON.stringify(request),
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  // ===== Utility: Generate Embedding =====

  /**
   * Generate a simple hash-based embedding for testing.
   * In production, use a proper embedding model (OpenAI, Cohere, etc.)
   */
  generateTestEmbedding(text: string, dim: number = 1536): number[] {
    const embedding = new Array(dim).fill(0);
    for (let i = 0; i < text.length; i++) {
      const charCode = text.charCodeAt(i);
      embedding[i % dim] += charCode / 1000.0;
    }
    // Normalize
    const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return embedding.map(val => val / magnitude);
  }
}

export const qmnService = new QmnService();
```

---

### Step 2: Integrate into ApiClient

Update `/src/services/apiClient.ts`:

```typescript
import { QmnService } from './modules/QmnService';

class ApiClient extends HttpClient {
  // ... existing services
  qmn: QmnService;  // ✨ Add QMN service

  constructor(baseURL?: string, baseURLV2?: string) {
    super(baseURL);

    // ... existing services initialization
    this.qmn = new QmnService();  // ✨ Initialize QMN
  }

  override saveTokensToStorage(accessToken: string, refreshToken: string) {
    super.saveTokensToStorage(accessToken, refreshToken);
    // ... existing services
    this.qmn.saveTokensToStorage(accessToken, refreshToken);  // ✨ Sync auth
  }

  override clearTokensFromStorage() {
    super.clearTokensFromStorage();
    // ... existing services
    this.qmn.clearTokensFromStorage();  // ✨ Sync auth
  }
}

export const apiClient = new ApiClient(
  import.meta.env.VITE_API_BASE_URL,
  import.meta.env.VITE_API_BASE_URL_V2
);
```

---

### Step 3: Create React Hooks

Create `/src/hooks/useQmn.ts`:

```typescript
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';

/**
 * Hook to broadcast knowledge to the mycelial network
 */
export function useBroadcastKnowledge() {
  return useMutation({
    mutationFn: async ({
      summary,
      snippets,
      agentId
    }: {
      summary: string;
      snippets: string[];
      agentId: string;
    }) => {
      const traceId = `${agentId}-${Date.now()}`;
      const embedding = apiClient.qmn.generateTestEmbedding(summary);

      return apiClient.qmn.broadcastKnowledge(traceId, {
        summary,
        embedding,
        snippets,
        tool_hints: [],
        sensitivity: 'internal',
        max_hops: 3,
        ttl_sec: 300,
        quota_cost: 100
      });
    }
  });
}

/**
 * Hook to store persistent memory
 */
export function useStoreMemory() {
  return useMutation({
    mutationFn: async ({
      agentId,
      content,
      kind,
      quality
    }: {
      agentId: string;
      content: Record<string, any>;
      kind: 'insight' | 'snippet' | 'decision' | 'preference';
      quality: number;
    }) => {
      const contentStr = JSON.stringify(content);
      const embedding = apiClient.qmn.generateTestEmbedding(contentStr);

      return apiClient.qmn.storeMemory({
        agent_id: agentId,
        kind,
        content,
        quality,
        sensitivity: 'internal',
        embedding
      });
    }
  });
}

/**
 * Hook to search memories
 */
export function useSearchMemories(query: string, options?: {
  minQuality?: number;
  limit?: number;
  kind?: string;
}) {
  return useQuery({
    queryKey: ['qmn-memories', query, options],
    queryFn: async () => {
      if (!query) return { results: [] };

      const embedding = apiClient.qmn.generateTestEmbedding(query);

      return apiClient.qmn.searchMemories({
        embedding,
        min_quality: options?.minQuality || 0.5,
        limit: options?.limit || 10,
        kind_filter: options?.kind
      });
    },
    enabled: !!query
  });
}

/**
 * Hook to get current tenant info
 */
export function useTenantInfo(tenantId?: string) {
  return useQuery({
    queryKey: ['qmn-tenant', tenantId],
    queryFn: () => apiClient.qmn.getTenant(tenantId)
  });
}
```

---

### Step 4: Create UI Components

Create `/src/components/qmn/KnowledgeShareCard.tsx`:

```typescript
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useBroadcastKnowledge } from '@/hooks/useQmn';
import { Loader2, Radio } from 'lucide-react';
import { toast } from 'sonner';

interface KnowledgeShareCardProps {
  agentId: string;
  agentName: string;
}

export function KnowledgeShareCard({ agentId, agentName }: KnowledgeShareCardProps) {
  const [knowledge, setKnowledge] = useState('');
  const broadcastMutation = useBroadcastKnowledge();

  const handleShare = async () => {
    if (!knowledge.trim()) {
      toast.error('Please enter knowledge to share');
      return;
    }

    try {
      await broadcastMutation.mutateAsync({
        summary: knowledge,
        snippets: [knowledge],
        agentId
      });

      toast.success('Knowledge shared to mycelial network!');
      setKnowledge('');
    } catch (error) {
      toast.error('Failed to share knowledge');
      console.error(error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-primary" />
          Share Knowledge
        </CardTitle>
        <CardDescription>
          Broadcast insights from {agentName} to the mycelial network
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="knowledge">Knowledge to Share</Label>
          <Textarea
            id="knowledge"
            placeholder="e.g., 'Discovered that users prefer dark mode in the evening...'"
            value={knowledge}
            onChange={(e) => setKnowledge(e.target.value)}
            rows={4}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button
          onClick={handleShare}
          disabled={broadcastMutation.isPending}
          className="w-full"
        >
          {broadcastMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Broadcasting...
            </>
          ) : (
            <>
              <Radio className="mr-2 h-4 w-4" />
              Broadcast to Network
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
```

Create `/src/components/qmn/MemorySearchCard.tsx`:

```typescript
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSearchMemories } from '@/hooks/useQmn';
import { Search, Brain, Loader2 } from 'lucide-react';

export function MemorySearchCard() {
  const [query, setQuery] = useState('');
  const { data, isLoading } = useSearchMemories(query);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          Search Mycelial Memory
        </CardTitle>
        <CardDescription>
          Find relevant knowledge across all agents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="search">Search Query</Label>
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              id="search"
              placeholder="e.g., 'user preferences', 'performance optimization'..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {data?.results && data.results.length > 0 && (
          <div className="space-y-2">
            <Label>Results ({data.results.length})</Label>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {data.results.map((result: any, idx: number) => (
                <div
                  key={idx}
                  className="p-3 border rounded-lg bg-muted/50 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{result.kind}</span>
                    <span className="text-xs text-muted-foreground">
                      Quality: {(result.quality * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {JSON.stringify(result.content)}
                  </p>
                  <div className="text-xs text-muted-foreground">
                    Similarity: {(result.similarity * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {data?.results && data.results.length === 0 && query && (
          <p className="text-sm text-muted-foreground text-center py-8">
            No memories found for "{query}"
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

---

### Step 5: Create Knowledge Page

Create `/src/pages/KnowledgePage.tsx`:

```typescript
import { MainLayout } from "@/components/layouts/MainLayout";
import { KnowledgeShareCard } from "@/components/qmn/KnowledgeShareCard";
import { MemorySearchCard } from "@/components/qmn/MemorySearchCard";
import { useTenantInfo } from "@/hooks/useQmn";
import { Loader2, Network } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function KnowledgePage() {
  const { data: tenantInfo, isLoading } = useTenantInfo();

  return (
    <MainLayout>
      <div className="container mx-auto py-8 space-y-6">
        <div className="flex items-center gap-3">
          <Network className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Mycelial Knowledge Network</h1>
            <p className="text-muted-foreground">
              Share and discover knowledge across all agents
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Tenant Information</CardTitle>
                <CardDescription>Your mycelial network tenant</CardDescription>
              </CardHeader>
              <CardContent>
                <dl className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Name</dt>
                    <dd className="text-sm">{tenantInfo?.name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Plan</dt>
                    <dd className="text-sm capitalize">{tenantInfo?.plan_tier}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Status</dt>
                    <dd className="text-sm capitalize">{tenantInfo?.status}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Region</dt>
                    <dd className="text-sm">{tenantInfo?.region_preference || 'Default'}</dd>
                  </div>
                </dl>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <KnowledgeShareCard
                agentId="agent-demo-001"
                agentName="Demo Agent"
              />
              <MemorySearchCard />
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}
```

---

### Step 6: Add Route

Update `/src/App.tsx`:

```typescript
// Add import
const KnowledgePage = lazy(() => import("./pages/KnowledgePage"));

// Add route
<Route path="/knowledge" element={<ProtectedRoute><KnowledgePage /></ProtectedRoute>} />
```

---

## Complete Examples

### Example 1: Agent Shares Discovery

```typescript
// When an agent makes a discovery, broadcast it
const handleAgentDiscovery = async (agentId: string, discovery: string) => {
  await apiClient.qmn.broadcastKnowledge(`discovery-${Date.now()}`, {
    summary: discovery,
    embedding: apiClient.qmn.generateTestEmbedding(discovery),
    snippets: [discovery],
    tool_hints: ['analysis', 'insight'],
    sensitivity: 'internal',
    max_hops: 3,
    ttl_sec: 600,
    quota_cost: 100
  });

  // Also store in persistent memory for later
  await apiClient.qmn.storeMemory({
    agent_id: agentId,
    kind: 'insight',
    content: { discovery, timestamp: new Date().toISOString() },
    quality: 0.85,
    sensitivity: 'internal',
    embedding: apiClient.qmn.generateTestEmbedding(discovery)
  });
};
```

### Example 2: Search Before Acting

```typescript
// Before executing a task, search for related knowledge
const executeTaskWithKnowledge = async (task: string) => {
  // Search for relevant past knowledge
  const embedding = apiClient.qmn.generateTestEmbedding(task);
  const memories = await apiClient.qmn.searchMemories({
    embedding,
    min_quality: 0.7,
    limit: 5
  });

  console.log(`Found ${memories.results.length} relevant past experiences`);

  // Use knowledge to inform task execution
  const context = memories.results.map(r => r.content);

  // Execute task with context...
};
```

### Example 3: Multi-Agent Collaboration

```typescript
// Agent A shares a problem
await apiClient.qmn.broadcastKnowledge('problem-solve-123', {
  summary: 'Need help optimizing database queries',
  embedding: apiClient.qmn.generateTestEmbedding('database optimization'),
  snippets: ['SELECT * FROM users is slow', 'Need indexing strategy'],
  tool_hints: ['database', 'performance'],
  sensitivity: 'internal',
  max_hops: 5,
  ttl_sec: 3600,
  quota_cost: 200
});

// Agent B searches for related knowledge
const solutions = await apiClient.qmn.searchMemories({
  embedding: apiClient.qmn.generateTestEmbedding('database optimization'),
  min_quality: 0.6,
  limit: 10,
  kind_filter: 'insight'
});

// Agent B shares solution
await apiClient.qmn.storeMemory({
  agent_id: 'agent-b',
  kind: 'insight',
  content: {
    problem: 'database optimization',
    solution: 'Add composite index on (user_id, created_at)',
    performance_gain: '10x faster'
  },
  quality: 0.9,
  sensitivity: 'internal',
  embedding: apiClient.qmn.generateTestEmbedding('database index optimization')
});
```

---

## Testing

### 1. Unit Tests

Create `/src/services/modules/__tests__/QmnService.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { QmnService } from '../QmnService';

describe('QmnService', () => {
  it('should generate deterministic embeddings', () => {
    const qmn = new QmnService();
    const emb1 = qmn.generateTestEmbedding('test');
    const emb2 = qmn.generateTestEmbedding('test');

    expect(emb1).toEqual(emb2);
    expect(emb1.length).toBe(1536);
  });

  it('should normalize embeddings', () => {
    const qmn = new QmnService();
    const emb = qmn.generateTestEmbedding('test');

    const magnitude = Math.sqrt(emb.reduce((sum, val) => sum + val * val, 0));
    expect(magnitude).toBeCloseTo(1.0, 5);
  });
});
```

### 2. Integration Tests

Create `/src/hooks/__tests__/useQmn.test.tsx`:

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBroadcastKnowledge, useSearchMemories } from '../useQmn';

const createWrapper = () => {
  const queryClient = new QueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useQmn hooks', () => {
  it('should broadcast knowledge', async () => {
    const { result } = renderHook(() => useBroadcastKnowledge(), {
      wrapper: createWrapper()
    });

    result.current.mutate({
      summary: 'Test knowledge',
      snippets: ['snippet1'],
      agentId: 'test-agent'
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('should search memories', async () => {
    const { result } = renderHook(
      () => useSearchMemories('test query'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveProperty('results');
  });
});
```

---

## Deployment

### Production Environment Variables

Update your production `.env`:

```bash
# QMN Production URLs
VITE_QMN_IDENTITY_URL=https://qmn-identity.yourcompany.com
VITE_QMN_ROUTER_URL=https://qmn-router.yourcompany.com
VITE_QMN_MEMORY_URL=https://qmn-memory.yourcompany.com
VITE_QMN_TENANT_ID=prod-tenant-abc123
```

### Build for Production

```bash
# Build Command Center with QMN integration
npm run build

# Build optimizes and tree-shakes QMN code
# Output: dist/
```

---

## Troubleshooting

### Common Issues

**Issue**: "QMN services not reachable"
```
Solution: Verify services are running
docker-compose ps
curl http://localhost:8001/health
```

**Issue**: "Tenant not found"
```
Solution: Create tenant first
POST http://localhost:8001/v1/tenants
{
  "id": "my-tenant",
  "name": "My Company",
  "plan_tier": "pro"
}
```

**Issue**: "CORS errors"
```
Solution: QMN services include CORS headers. Verify:
- Services are running on correct ports
- Frontend is using correct URLs
- No proxy/firewall blocking requests
```

---

## Next Steps

1. ✅ **Integrate QMN service** - Complete!
2. ✅ **Create UI components** - Complete!
3. ⏭️ **Replace test embeddings** - Use real embedding API (OpenAI, Cohere)
4. ⏭️ **Add authentication** - Integrate QMN auth with your existing auth
5. ⏭️ **Monitor usage** - Add QMN metrics to your dashboards
6. ⏭️ **Scale** - Deploy QMN services to production infrastructure

---

**Questions?** Refer to:
- [QMN API Reference](./QMN_API_REFERENCE.md)
- [QMN Architecture Guide](./RESEARCH_PAPER.md)
- [Example Applications](./ENTERPRISE_50_WORKERS_KNOW_HOW_SHARING.md)

**Happy integrating!** 🍄✨
