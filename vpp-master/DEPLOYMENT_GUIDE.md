# VPP Master API - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the VPP Master API in development, staging, and production environments. The deployment uses Docker Compose for orchestration and supports both SQLite (development) and PostgreSQL (production) databases.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Environment](#development-environment)
3. [Staging Environment](#staging-environment)
4. [Production Environment](#production-environment)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Scaling and Performance](#scaling-and-performance)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- Memory: 4 GB RAM
- Disk: 20 GB free space
- OS: Linux, macOS, or Windows with WSL2

**Recommended:**
- CPU: 4+ cores
- Memory: 8+ GB RAM
- Disk: 50+ GB free space
- OS: Ubuntu 20.04 LTS or later

### Required Software

- Docker 20.10+
- Docker Compose 1.29+
- Python 3.9+
- Git

**Installation:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3.9 git

# macOS (using Homebrew)
brew install docker docker-compose python@3.9 git

# Verify installations
docker --version
docker-compose --version
python3 --version
git --version
```

### Network Requirements

- Port 8080: API server
- Port 5432: PostgreSQL (production only)
- Port 6379: Redis (optional caching)
- Port 9090: Prometheus (monitoring)
- Port 3000: Grafana (visualization)

## Development Environment

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/vpp-master.git
cd vpp-master
```

2. **Create environment file:**
```bash
cp .env.example .env.dev
```

3. **Start the application:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. **Verify deployment:**
```bash
curl http://localhost:8080/health
```

### Development Docker Compose

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  vpp-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=sqlite:///vpp.db
      - LOG_LEVEL=DEBUG
      - API_KEY=dev-key-12345678901234567890
    volumes:
      - .:/app
      - vpp-data:/data
    command: python3 app.py
    networks:
      - vpp-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    networks:
      - vpp-network

volumes:
  vpp-data:
  prometheus-data:

networks:
  vpp-network:
    driver: bridge
```

### Development Workflow

```bash
# Start services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f vpp-api

# Run tests
docker-compose -f docker-compose.dev.yml exec vpp-api python3 -m pytest

# Stop services
docker-compose -f docker-compose.dev.yml down

# Clean up (remove volumes)
docker-compose -f docker-compose.dev.yml down -v
```

## Staging Environment

### Staging Docker Compose

Create `docker-compose.staging.yml`:

```yaml
version: '3.8'

services:
  vpp-api:
    image: vpp-api:staging
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=staging
      - DATABASE_URL=postgresql://vpp_user:${DB_PASSWORD}@postgres:5432/vpp_staging
      - LOG_LEVEL=INFO
      - API_KEY=${API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - vpp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_USER=vpp_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=vpp_staging
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - vpp-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - vpp-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - vpp-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - vpp-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  vpp-network:
    driver: bridge
```

### Staging Deployment

```bash
# Build image
docker build -t vpp-api:staging .

# Create environment file
cp .env.example .env.staging
# Edit .env.staging with staging values

# Start services
docker-compose -f docker-compose.staging.yml up -d

# Run database migrations
docker-compose -f docker-compose.staging.yml exec vpp-api python3 -m alembic upgrade head

# Verify deployment
curl http://localhost:8080/health
```

## Production Environment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  vpp-api-1:
    image: vpp-api:${VERSION}
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://vpp_user:${DB_PASSWORD}@postgres:5432/vpp_prod
      - LOG_LEVEL=WARN
      - API_KEY=${API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - vpp-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  vpp-api-2:
    image: vpp-api:${VERSION}
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://vpp_user:${DB_PASSWORD}@postgres:5432/vpp_prod
      - LOG_LEVEL=WARN
      - API_KEY=${API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - vpp-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  vpp-api-3:
    image: vpp-api:${VERSION}
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://vpp_user:${DB_PASSWORD}@postgres:5432/vpp_prod
      - LOG_LEVEL=WARN
      - API_KEY=${API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - vpp-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - vpp-api-1
      - vpp-api-2
      - vpp-api-3
    networks:
      - vpp-network
    restart: always

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_USER=vpp_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=vpp_prod
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - vpp-network
    restart: always
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - vpp-network
    restart: always
    command: redis-server --appendonly yes

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - vpp-network
    restart: always

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - vpp-network
    restart: always

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  vpp-network:
    driver: bridge
```

### Production Deployment

```bash
# Build and tag image
docker build -t vpp-api:1.0.0 .
docker tag vpp-api:1.0.0 your-registry/vpp-api:1.0.0
docker push your-registry/vpp-api:1.0.0

# Create environment file
cp .env.example .env.prod
# Edit .env.prod with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec vpp-api-1 python3 -m alembic upgrade head

# Verify deployment
curl https://api.vpp.example.com/health
```

## Environment Configuration

### Environment Variables

Create `.env` file with the following variables:

```bash
# Application
FLASK_ENV=production
LOG_LEVEL=INFO
API_KEY=your-secure-api-key-here

# Database
DATABASE_URL=postgresql://vpp_user:password@postgres:5432/vpp_prod
DB_POOL_SIZE=20
DB_POOL_RECYCLE=3600

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=your-redis-password

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
JWT_EXPIRATION=86400

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=your-grafana-password

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_MINUTE=100

# CORS
CORS_ORIGINS=https://app.vpp.example.com,https://admin.vpp.example.com

# Email (for alerts)
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your-email-password
```

### Configuration Files

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'vpp-api'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

**nginx.conf:**
```nginx
upstream vpp_api {
    server vpp-api-1:8080;
    server vpp-api-2:8080;
    server vpp-api-3:8080;
}

server {
    listen 80;
    server_name api.vpp.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.vpp.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://vpp_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Database Setup

### PostgreSQL Initialization

```bash
# Create database and user
docker-compose exec postgres psql -U postgres -c "CREATE USER vpp_user WITH PASSWORD 'password';"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE vpp_prod OWNER vpp_user;"

# Run migrations
docker-compose exec vpp-api python3 -m alembic upgrade head

# Verify database
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c "\dt"
```

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U vpp_user vpp_prod > backup.sql

# Restore database
docker-compose exec -T postgres psql -U vpp_user vpp_prod < backup.sql

# Automated backup (cron job)
0 2 * * * docker-compose exec postgres pg_dump -U vpp_user vpp_prod > /backups/vpp_$(date +\%Y\%m\%d).sql
```

### Database Optimization

```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_created_at ON devices(created_at);
CREATE INDEX idx_dispatches_device_id ON dispatches(device_id);
CREATE INDEX idx_dispatches_status ON dispatches(status);
CREATE INDEX idx_dispatches_created_at ON dispatches(created_at);

-- Analyze tables
ANALYZE devices;
ANALYZE dispatches;
```

## Monitoring and Observability

### Prometheus Metrics

Access metrics at: http://localhost:9090

Key metrics to monitor:
- `vpp_api_requests_total` - Total API requests
- `vpp_api_request_duration_seconds` - Request duration
- `vpp_api_errors_total` - Total errors
- `vpp_device_count` - Number of devices
- `vpp_dispatch_total` - Total dispatches

### Grafana Dashboards

Access Grafana at: http://localhost:3000

1. Add Prometheus data source
2. Import dashboards from `monitoring/dashboards/`
3. Configure alerts

### Logging

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f vpp-api

# Last 100 lines
docker-compose logs --tail=100 vpp-api
```

## Scaling and Performance

### Horizontal Scaling

Add more API instances in docker-compose.prod.yml:

```yaml
vpp-api-4:
  image: vpp-api:${VERSION}
  # ... same configuration as other instances
```

### Database Connection Pooling

Configure in `.env`:
```bash
DB_POOL_SIZE=20
DB_POOL_RECYCLE=3600
```

### Caching Strategy

Redis is used for caching:
- Device status cache (TTL: 30s)
- Dispatch history cache (TTL: 5m)
- Metrics cache (TTL: 1m)

### Performance Tuning

```bash
# Increase file descriptors
ulimit -n 65536

# Tune kernel parameters
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

## Backup and Recovery

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec postgres pg_dump -U vpp_user vpp_prod > $BACKUP_DIR/db_$DATE.sql

# Backup volumes
docker run --rm -v vpp-master_postgres-data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/data_$DATE.tar.gz -C /data .

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Recovery Procedure

```bash
# Restore database
docker-compose exec -T postgres psql -U vpp_user vpp_prod < backup.sql

# Restore volumes
docker run --rm -v vpp-master_postgres-data:/data -v /backups:/backup \
  alpine tar xzf /backup/data_backup.tar.gz -C /data

# Restart services
docker-compose restart
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>
```

**Database connection failed:**
```bash
# Check database status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**Out of memory:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Edit Docker Desktop settings or docker daemon.json
```

**High CPU usage:**
```bash
# Check which container is using CPU
docker stats

# Check application logs
docker-compose logs vpp-api | grep -i error
```

### Health Checks

```bash
# API health
curl http://localhost:8080/health

# Database health
docker-compose exec postgres pg_isready -U vpp_user

# Redis health
docker-compose exec redis redis-cli ping

# Prometheus health
curl http://localhost:9090/-/healthy
```

### Performance Diagnostics

```bash
# Check slow queries
docker-compose exec postgres psql -U vpp_user vpp_prod -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check connection count
docker-compose exec postgres psql -U vpp_user vpp_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Check cache hit ratio
docker-compose exec redis redis-cli INFO stats
```
