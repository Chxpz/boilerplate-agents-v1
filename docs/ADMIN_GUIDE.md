# Admin Guide

Complete guide for deploying, monitoring, and maintaining the AI Agent in production.

## Table of Contents
1. [Production Deployment](#production-deployment)
2. [Monitoring & Observability](#monitoring--observability)
3. [Scaling](#scaling)
4. [Security](#security)
5. [Backup & Recovery](#backup--recovery)
6. [Maintenance](#maintenance)
7. [Troubleshooting](#troubleshooting)

## Production Deployment

### Prerequisites

- Docker & Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt recommended)
- Monitoring tools (Prometheus, Grafana)

### Deployment Steps

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/agent
cd /opt/agent
```

#### 2. Configure Environment

```bash
# Copy production environment template
cp .env.example .env.production

# Edit with production values
nano .env.production
```

**Production Environment**:
```bash
# OpenAI
OPENAI_API_KEY=sk-prod-your-key

# Supabase
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-anon-key

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_ENABLED=true

# API
API_HOST=0.0.0.0
API_PORT=8000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
```

#### 3. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: agent-redis-prod
    restart: always
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - agent-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: agent-api-prod
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env.production
    environment:
      - REDIS_HOST=redis
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/v1/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - agent-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  nginx:
    image: nginx:alpine
    container_name: agent-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - agent
    networks:
      - agent-network

volumes:
  redis-data:

networks:
  agent-network:
    driver: bridge
```

#### 4. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream agent_backend {
        server agent:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://agent_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /api/v1/chat/stream {
            proxy_pass http://agent_backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_buffering off;
            proxy_cache off;
            chunked_transfer_encoding on;
        }
    }
}
```

#### 5. Deploy

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up --build -d

# Verify
docker-compose -f docker-compose.prod.yml ps
curl https://your-domain.com/api/v1/health
```

### SSL Certificate Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring & Observability

### Logging

#### Application Logs

```bash
# View logs
docker-compose logs -f agent

# Tail specific number of lines
docker-compose logs --tail=100 agent

# Filter by level
docker-compose logs agent | grep ERROR
```

#### Log Rotation

Create `/etc/logrotate.d/agent`:

```
/opt/agent/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose -f /opt/agent/docker-compose.prod.yml restart agent
    endscript
}
```

### Metrics

#### Health Check Monitoring

```bash
# Create health check script
cat > /opt/agent/health-check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8000/api/v1/health"
RESPONSE=$(curl -s $HEALTH_URL)
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "ALERT: Agent unhealthy - $RESPONSE"
    # Send alert (email, Slack, PagerDuty, etc.)
fi
EOF

chmod +x /opt/agent/health-check.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /opt/agent/health-check.sh
```

#### Prometheus Integration

Add to `docker-compose.prod.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - agent-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - agent-network
```

### Alerting

#### Slack Webhook

```python
# Add to core/alerts.py
import requests

def send_alert(message, level="warning"):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    color = {"info": "#36a64f", "warning": "#ff9900", "error": "#ff0000"}
    
    payload = {
        "attachments": [{
            "color": color.get(level, "#808080"),
            "title": f"Agent Alert - {level.upper()}",
            "text": message,
            "ts": int(time.time())
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

## Scaling

### Horizontal Scaling

#### Load Balancer Setup

```yaml
# docker-compose.scale.yml
services:
  agent:
    deploy:
      replicas: 3
    # ... rest of config

  nginx:
    # Update upstream in nginx.conf
    # upstream agent_backend {
    #     server agent:8000;
    #     server agent:8001;
    #     server agent:8002;
    # }
```

#### Redis Cluster

For high availability:

```yaml
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes

  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379

  redis-replica-2:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379
```

### Vertical Scaling

Adjust resource limits in `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      cpus: '2'
      memory: 4G
```

### Auto-Scaling

Use Kubernetes for auto-scaling:

```yaml
# deployment.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Security

### Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Rotate keys regularly

2. **Network Security**
   - Use private networks for internal communication
   - Implement firewall rules
   - Enable SSL/TLS everywhere

3. **Access Control**
   - Implement API authentication
   - Use rate limiting
   - Monitor for suspicious activity

4. **Database Security**
   - Enable RLS policies in Supabase
   - Use read-only credentials where possible
   - Regular security audits

### Authentication Implementation

```python
# Add to api/auth.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    # Verify token with your auth provider
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Use in routes
@router.post("/chat")
async def chat(request: ChatRequest, token: str = Depends(verify_token)):
    # ...
```

## Backup & Recovery

### Database Backups

```bash
# Supabase automatic backups (configured in dashboard)
# Manual backup
pg_dump -h db.xxx.supabase.co -U postgres -d postgres > backup.sql

# Restore
psql -h db.xxx.supabase.co -U postgres -d postgres < backup.sql
```

### Redis Backups

```bash
# Manual backup
docker exec agent-redis redis-cli BGSAVE

# Copy RDB file
docker cp agent-redis:/data/dump.rdb ./backups/

# Restore
docker cp ./backups/dump.rdb agent-redis:/data/
docker-compose restart redis
```

### Vector Store Backups

```bash
# Backup ChromaDB
tar -czf chromadb-backup.tar.gz ./data/vectorstore/

# Restore
tar -xzf chromadb-backup.tar.gz -C ./data/
```

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/agent"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup Redis
docker exec agent-redis redis-cli BGSAVE
sleep 5
docker cp agent-redis:/data/dump.rdb $BACKUP_DIR/$DATE/

# Backup vector store
tar -czf $BACKUP_DIR/$DATE/vectorstore.tar.gz /opt/agent/data/vectorstore/

# Backup logs
tar -czf $BACKUP_DIR/$DATE/logs.tar.gz /opt/agent/logs/

# Remove old backups (keep 30 days)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

## Maintenance

### Regular Tasks

#### Daily
- Check health endpoints
- Review error logs
- Monitor resource usage

#### Weekly
- Review performance metrics
- Check disk space
- Update dependencies (if needed)

#### Monthly
- Security updates
- Backup verification
- Performance optimization
- Cost analysis

### Update Procedure

```bash
# 1. Backup current state
./backup.sh

# 2. Pull latest changes
git pull origin main

# 3. Build new image
docker-compose -f docker-compose.prod.yml build

# 4. Test in staging
docker-compose -f docker-compose.staging.yml up -d

# 5. Run tests
pytest tests/

# 6. Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# 7. Verify
curl https://your-domain.com/api/v1/health

# 8. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Rollback Procedure

```bash
# 1. Stop current version
docker-compose -f docker-compose.prod.yml down

# 2. Restore previous image
docker tag agent:previous agent:latest

# 3. Restore data if needed
./restore.sh <backup-date>

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
curl https://your-domain.com/api/v1/health
```

## Troubleshooting

### Common Production Issues

#### 1. High Memory Usage

**Symptoms**:
- OOM kills
- Slow responses
- Container restarts

**Solutions**:
```bash
# Check memory usage
docker stats agent-api-prod

# Increase memory limit
# In docker-compose.prod.yml:
deploy:
  resources:
    limits:
      memory: 8G

# Optimize Redis
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 2. High CPU Usage

**Symptoms**:
- Slow responses
- Request timeouts
- High load average

**Solutions**:
```bash
# Check CPU usage
docker stats agent-api-prod

# Scale horizontally
docker-compose -f docker-compose.prod.yml up -d --scale agent=3

# Optimize queries
# - Add caching
# - Reduce context window
# - Use faster models
```

#### 3. Database Connection Issues

**Symptoms**:
- Connection timeouts
- "Too many connections" errors

**Solutions**:
```bash
# Check connections
# In Supabase dashboard: Database > Connection pooling

# Increase pool size
# In settings.py:
SUPABASE_POOL_SIZE=20

# Use connection pooling (pgBouncer)
```

#### 4. Redis Connection Issues

**Symptoms**:
- Cache misses
- Session loss
- Connection errors

**Solutions**:
```bash
# Check Redis
docker exec agent-redis redis-cli ping

# Check connections
docker exec agent-redis redis-cli CLIENT LIST

# Restart Redis
docker-compose -f docker-compose.prod.yml restart redis
```

### Performance Optimization

1. **Enable Response Caching**
   ```python
   # Increase cache TTL
   await cache_manager.set(key, value, ttl=7200)  # 2 hours
   ```

2. **Optimize Vector Search**
   ```python
   # Reduce k value
   docs = rag_manager.similarity_search(query, k=3)  # Instead of 4
   ```

3. **Use Smaller Models**
   ```bash
   # In .env
   MODEL_NAME=gpt-3.5-turbo  # Faster, cheaper
   ```

4. **Implement Request Queuing**
   ```python
   # Use Celery for background tasks
   from celery import Celery
   
   @celery.task
   def process_request(message, session_id):
       return agent_executor.execute(message, session_id)
   ```

## Next Steps

- [Development Guide](DEVELOPMENT.md) - Extend functionality
- [API Reference](API_REFERENCE.md) - Complete API docs
- [Event Architecture](EVENT_ARCHITECTURE.md) - Inter-service communication

---

**Need help?** Contact the development team or open an issue.
