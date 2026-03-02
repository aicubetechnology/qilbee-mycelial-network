# 🚀 QMN ArgoCD Apps - Plano de Deployment

**Data:** 2026-03-02  
**Fonte:** `~/repos/qilbee-mycelial-network/docker-compose.yml`  
**Objetivo:** Converter stack QMN do docker-compose para apps ArgoCD

---

## 📊 ANÁLISE DO DOCKER-COMPOSE

### Serviços Identificados (Total: 9)

#### **INFRAESTRUTURA (2 - NÃO converter):**
1. `postgres` - Banco de dados com pgvector
2. `redis` - Cache e message broker

#### **CONTROL PLANE (2 - converter):**
3. `qmn-identity` - Gerenciamento de identidade e autenticação
4. `qmn-keys` - Gerenciamento de chaves criptográficas

#### **DATA PLANE (3 - converter):**
5. `qmn-router` - Roteamento de mensagens
6. `qmn-hyphal-memory` - Memória distribuída (pgvector)
7. `qmn-reinforcement` - Aprendizado por reforço

#### **GATEWAY (1 - converter):**
8. `qmn-gateway` - Nginx reverse proxy (CRÍTICO)

#### **OBSERVABILITY (1 - converter):**
9. `grafana` - Dashboards e métricas

---

## 🎯 APPS ARGOCD A CRIAR (6 apps)

### 1. **qmn-identity** (Control Plane)
**Tipo:** Deployment + Service  
**Porta:** 8100  
**Imagem:** `qmn-identity:latest`  
**Dependências:** postgres, redis  

**Variáveis de ambiente:**
- POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- REDIS_HOST, REDIS_PORT
- JWT_SECRET_KEY, JWT_ALGORITHM
- UVICORN_HOST, UVICORN_PORT

**Health check:** `http://localhost:8100/health`

**Dockerfile:** `/services/control_plane/identity/Dockerfile`

---

### 2. **qmn-keys** (Control Plane)
**Tipo:** Deployment + Service  
**Porta:** 8101  
**Imagem:** `qmn-keys:latest`  
**Dependências:** postgres, redis  

**Variáveis de ambiente:**
- POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- REDIS_HOST, REDIS_PORT
- IDENTITY_SERVICE_URL (http://qmn-identity:8100)
- KEY_ROTATION_INTERVAL_HOURS

**Health check:** `http://localhost:8101/health`

**Dockerfile:** `/services/control_plane/keys/Dockerfile`

---

### 3. **qmn-router** (Data Plane)
**Tipo:** Deployment + Service  
**Porta:** 8200  
**Imagem:** `qmn-router:latest`  
**Dependências:** postgres, redis, qmn-identity  

**Variáveis de ambiente:**
- POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- REDIS_HOST, REDIS_PORT
- IDENTITY_SERVICE_URL
- MAX_HOPS, DEFAULT_TTL, ENABLE_ROUTING_METRICS

**Health check:** `http://localhost:8200/health`

**Dockerfile:** `/services/data_plane/router/Dockerfile`

---

### 4. **qmn-hyphal-memory** (Data Plane)
**Tipo:** Deployment + Service  
**Porta:** 8201  
**Imagem:** `qmn-hyphal-memory:latest`  
**Dependências:** postgres (pgvector), redis, qmn-identity  

**Variáveis de ambiente:**
- POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- REDIS_HOST, REDIS_PORT
- IDENTITY_SERVICE_URL
- EMBEDDING_DIMENSIONS (1536)
- MAX_MEMORY_AGE_DAYS
- ENABLE_QUALITY_SCORING

**Health check:** `http://localhost:8201/health`

**Dockerfile:** `/services/data_plane/hyphal_memory/Dockerfile`

**⚠️ CRÍTICO:** Requer pgvector extension no Postgres

---

### 5. **qmn-reinforcement** (Data Plane)
**Tipo:** Deployment + Service  
**Porta:** 8202  
**Imagem:** `qmn-reinforcement:latest`  
**Dependências:** postgres, redis, qmn-identity  

**Variáveis de ambiente:**
- POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- REDIS_HOST, REDIS_PORT
- IDENTITY_SERVICE_URL
- LEARNING_RATE
- DISCOUNT_FACTOR
- ENABLE_REAL_TIME_LEARNING

**Health check:** `http://localhost:8202/health`

**Dockerfile:** `/services/data_plane/reinforcement/Dockerfile`

---

### 6. **qmn-gateway** (Gateway - CRÍTICO)
**Tipo:** Deployment + Service + Ingress  
**Porta:** 80  
**Imagem:** `nginx:alpine`  
**Dependências:** Todos os serviços acima  

**ConfigMap:** `nginx.conf` (configuração do reverse proxy)

**Rotas expostas:**
```nginx
/identity/*      → qmn-identity:8100
/keys/*          → qmn-keys:8101
/router/*        → qmn-router:8200
/memory/*        → qmn-hyphal-memory:8201
/reinforcement/* → qmn-reinforcement:8202
/health          → health check aggregado
```

**Ingress:**
- Host: `qmn.dev.qilbee.io` ✅ (CORRIGIDO)
- TLS: letsencrypt-production
- Annotations: nginx ingress controller

**ConfigMap:** `/infra/nginx/nginx.conf`

---

### 7. **qmn-grafana** (Observability - OPCIONAL)
**Tipo:** Deployment + Service + Ingress  
**Porta:** 3000 → 3021 (remapeado)  
**Imagem:** `grafana/grafana:latest`  
**Dependências:** prometheus (se houver)  

**Variáveis de ambiente:**
- GF_SECURITY_ADMIN_USER
- GF_SECURITY_ADMIN_PASSWORD
- GF_SERVER_ROOT_URL

**Persistent Volume:** Para dashboards e configurações

**Ingress:**
- Host: `qmn-grafana.dev.qilbee.io`

---

## 🗄️ BANCOS DE DADOS (NÃO converter - usar RDS/Externo)

### **PostgreSQL com pgvector**
**Não criar app ArgoCD**, usar:
- **Opção A:** AWS RDS Postgres 15+ com pgvector extension
- **Opção B:** Pod StatefulSet (não recomendado para prod)

**Database:** `qmn`  
**Extensions:** `vector`, `uuid-ossp`  
**Port:** 5432  

**Tabelas principais:**
- `agents` - Registro de agents
- `agent_knowledge` - Knowledge base
- `hyphal_memories` - Memórias distribuídas (com embeddings)
- `routing_metrics` - Métricas de roteamento
- `reinforcement_data` - Dados de aprendizado

### **Redis**
**Não criar app ArgoCD**, usar:
- **Opção A:** AWS ElastiCache Redis
- **Opção B:** Helm chart redis (bitnami)

**Port:** 6379  
**Uso:** Cache, pub/sub, session storage

---

## 📦 ESTRUTURA DE APPS NO ARGOCD

### Organização Recomendada:

```
argocd/
├── qmn-infrastructure/          # App-of-Apps
│   ├── postgres-external.yaml   # External service (RDS)
│   └── redis-external.yaml      # External service (ElastiCache)
│
├── qmn-control-plane/           # App-of-Apps
│   ├── qmn-identity.yaml
│   └── qmn-keys.yaml
│
├── qmn-data-plane/              # App-of-Apps
│   ├── qmn-router.yaml
│   ├── qmn-hyphal-memory.yaml
│   └── qmn-reinforcement.yaml
│
├── qmn-gateway/                 # Standalone app (CRÍTICO)
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap-nginx.yaml
│   └── ingress.yaml
│
└── qmn-observability/           # Standalone app (OPCIONAL)
    └── grafana.yaml
```

---

## 🔗 DEPENDÊNCIAS ENTRE APPS

```
Ordem de deployment:

1. ✅ Infraestrutura (externa)
   ├─ RDS Postgres (pgvector)
   └─ ElastiCache Redis

2. ✅ Control Plane
   ├─ qmn-identity (primeiro)
   └─ qmn-keys (após identity)

3. ✅ Data Plane
   ├─ qmn-router
   ├─ qmn-hyphal-memory (requer pgvector)
   └─ qmn-reinforcement

4. ✅ Gateway (após todos os serviços)
   └─ qmn-gateway

5. ⏳ Observability (opcional)
   └─ grafana
```

**ArgoCD Sync Waves:**
- Wave 0: External services
- Wave 1: qmn-identity
- Wave 2: qmn-keys
- Wave 3: Data plane services
- Wave 4: qmn-gateway
- Wave 5: grafana

---

## 🔐 SECRETS NECESSÁRIOS

### 1. **qmn-postgres-credentials**
```yaml
POSTGRES_HOST: <RDS_ENDPOINT>
POSTGRES_DB: qmn
POSTGRES_USER: qmn_user
POSTGRES_PASSWORD: <SECRET>
```

### 2. **qmn-redis-credentials**
```yaml
REDIS_HOST: <ELASTICACHE_ENDPOINT>
REDIS_PORT: 6379
REDIS_PASSWORD: <SECRET>
```

### 3. **qmn-jwt-secret**
```yaml
JWT_SECRET_KEY: <RANDOM_SECRET>
JWT_ALGORITHM: HS256
```

### 4. **qmn-grafana-admin**
```yaml
GF_SECURITY_ADMIN_USER: admin
GF_SECURITY_ADMIN_PASSWORD: <SECRET>
```

---

## 🌐 INGRESS E DNS

### Domínios Necessários:

1. **qmn.dev.qilbee.io** ✅
   - Gateway principal
   - Roteamento para todos os serviços

2. **qmn-grafana.dev.qilbee.io** (opcional)
   - Dashboards de observability

### Certificados SSL:
- Issuer: letsencrypt-production
- Secret: qmn-tls

---

## 🚀 CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Preparação (Pré-requisitos)
- [ ] Provisionar RDS Postgres 15+ com pgvector
- [ ] Provisionar ElastiCache Redis
- [ ] Criar database `qmn` e executar migrations
- [ ] Criar secrets no Kubernetes
- [ ] Configurar DNS (qmn.dev.qilbee.io → LoadBalancer)

### Fase 2: Build de Imagens
- [ ] Build qmn-identity → Push para ECR
- [ ] Build qmn-keys → Push para ECR
- [ ] Build qmn-router → Push para ECR
- [ ] Build qmn-hyphal-memory → Push para ECR
- [ ] Build qmn-reinforcement → Push para ECR

### Fase 3: Criar Manifests Kubernetes
- [ ] Criar Deployments para cada serviço
- [ ] Criar Services (ClusterIP)
- [ ] Criar ConfigMap para nginx
- [ ] Criar Deployment e Service do gateway
- [ ] Criar Ingress para qmn.dev.qilbee.io

### Fase 4: ArgoCD Apps
- [ ] Criar app qmn-identity
- [ ] Criar app qmn-keys
- [ ] Criar app qmn-router
- [ ] Criar app qmn-hyphal-memory
- [ ] Criar app qmn-reinforcement
- [ ] Criar app qmn-gateway (CRÍTICO)
- [ ] Criar app qmn-grafana (opcional)

### Fase 5: Validação
- [ ] Verificar health de todos os serviços
- [ ] Testar https://qmn.dev.qilbee.io/health
- [ ] Testar rotas do gateway
- [ ] Verificar conectividade com RDS/Redis
- [ ] Validar logs de inicialização

### Fase 6: Integração com Agents
- [ ] Atualizar agent manifest: QMN_API_BASE_URL=https://qmn.dev.qilbee.io
- [ ] Gerar QMN_API_KEY real (substituir "pending")
- [ ] Recriar pod do agent
- [ ] Testar registro do agent no QMN
- [ ] Verificar logs: "Mycelial client initialized successfully"

---

## 📊 RESUMO

### Total de Apps ArgoCD: 6-7

**Essenciais (6):**
1. qmn-identity
2. qmn-keys
3. qmn-router
4. qmn-hyphal-memory
5. qmn-reinforcement
6. qmn-gateway ⭐ CRÍTICO

**Opcional (1):**
7. qmn-grafana

### Infraestrutura Externa (NÃO apps):
- PostgreSQL (RDS)
- Redis (ElastiCache)

### URL Final:
✅ **https://qmn.dev.qilbee.io** (corrigido de qmn.qube.aicube.ca)

---

## 🔗 REFERÊNCIAS

- Docker Compose: `~/repos/qilbee-mycelial-network/docker-compose.yml`
- Nginx Config: `~/repos/qilbee-mycelial-network/infra/nginx/nginx.conf`
- Dockerfiles: `~/repos/qilbee-mycelial-network/services/*/Dockerfile`
- Agent config: `~/repos/kubernetes-manifest/qube-agents/dev/curl-test-1770647379.yaml`

---

**Próxima ação recomendada:** Criar estrutura de manifests Kubernetes para cada app
