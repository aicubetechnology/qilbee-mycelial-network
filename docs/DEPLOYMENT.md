# QMN Deployment Guide

## 📋 Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- kubectl configured
- Docker registry access

## 🚀 Quick Deploy

### Local Development
```bash
# Start with Docker Compose
make up

# Check health
make health

# View logs
make logs
```

### Kubernetes Production

```bash
# Add Helm repository
helm repo add qmn https://charts.qilbee.network
helm repo update

# Install QMN
helm install qmn qmn/qmn \
  --namespace qmn \
  --create-namespace \
  --values production-values.yaml

# Verify deployment
kubectl -n qmn get pods
kubectl -n qmn get svc
```

## 🔧 Configuration

### Environment Variables

**Required:**
- `POSTGRES_URL` - PostgreSQL connection string
- `MONGO_URL` - MongoDB connection string
- `QMN_SIGNING_KEY` - Ed25519 signing key

**Optional:**
- `REDIS_URL` - Redis connection string
- `LOG_LEVEL` - Logging level (default: INFO)
- `REGION` - Deployment region

### Secrets Management

```bash
# Create secrets
kubectl create secret generic qmn-secrets \
  --from-literal=postgres-url="postgresql://..." \
  --from-literal=mongo-url="mongodb://..." \
  --from-literal=signing-key="..." \
  -n qmn
```

## 📊 Monitoring

### Prometheus Metrics
- Available at: `/metrics` on each service
- Grafana dashboards in `infra/grafana/dashboards/`

### Health Checks
```bash
# Check all services
curl http://api.qilbee.network/v1/health
```

## 🔄 Scaling

### Horizontal Scaling
```bash
# Scale router service
kubectl scale deployment qmn-router --replicas=10 -n qmn

# Autoscaling
kubectl autoscale deployment qmn-router \
  --cpu-percent=70 \
  --min=5 --max=20 -n qmn
```

## 🔐 Security

### TLS/SSL
- Cert-manager for automatic certificate management
- Let's Encrypt integration

### Network Policies
```bash
kubectl apply -f deploy/network-policies/
```

## 💾 Backup & Recovery

### Database Backups
```bash
# PostgreSQL backup
kubectl exec -n qmn qmn-postgres-0 -- \
  pg_dump -U postgres qmn > backup.sql

# MongoDB backup
kubectl exec -n qmn qmn-mongo-0 -- \
  mongodump --out=/backup
```

## 📈 Performance Tuning

### PostgreSQL
- Connection pooling: 100 connections
- Shared buffers: 4GB
- Effective cache: 12GB

### MongoDB
- WiredTiger cache: 8GB
- Index optimization enabled

## 🆘 Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n qmn
kubectl logs <pod-name> -n qmn
```

**Database connection issues:**
```bash
kubectl run -it --rm debug --image=postgres:16 \
  --restart=Never -- psql $POSTGRES_URL
```

## 📞 Support

- Documentation: https://docs.qilbee.network
- Issues: https://github.com/qilbee/mycelial-network/issues
- Email: support@qilbee.network
