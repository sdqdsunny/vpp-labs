# VPP Phase 2 Simulation Framework - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the VPP Phase 2 Simulation Framework in development and production environments.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Production Environment Setup](#production-environment-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup and Migration](#database-setup-and-migration)
5. [Running Tests](#running-tests)
6. [Monitoring and Logging Setup](#monitoring-and-logging-setup)
7. [Troubleshooting Guide](#troubleshooting-guide)

## Development Environment Setup

### Prerequisites

- Docker and Docker Compose installed
- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### Quick Start with Docker Compose

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd vpp-phase2-simulation
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Start services with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

   This will start:
   - VPP Phase 2 Simulation API (port 8080)
   - PostgreSQL database (port 5432)
   - Redis cache (port 6379)
   - Prometheus metrics (port 9090)
   - Grafana dashboard (port 3000)

4. **Verify services are running**:
   ```bash
   curl http://localhost:8080/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "0.1.0",
     "environment": "development"
   }
   ```

5. **Access API documentation**:
   - Swagger UI: http://localhost:8080/api/docs
   - OpenAPI spec: http://localhost:8080/api/openapi.json

### Local Development Setup (Without Docker)

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**:
   ```bash
   # Create database
   createdb vpp_phase2_sim
   
   # Create user
   createuser vpp_user
   psql -c "ALTER USER vpp_user WITH PASSWORD 'vpp_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE vpp_phase2_sim TO vpp_user;"
   ```

3. **Setup Redis**:
   ```bash
   # Start Redis server
   redis-server
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Initialize database**:
   ```bash
   python -c "from utils.database import init_db; init_db()"
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

## Production Environment Setup

### Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3+ (optional)

#### Deployment Steps

1. **Create namespace**:
   ```bash
   kubectl create namespace vpp-phase2
   ```

2. **Create secrets**:
   ```bash
   kubectl create secret generic vpp-secrets \
     --from-literal=db-password=<secure-password> \
     --from-literal=redis-password=<secure-password> \
     -n vpp-phase2
   ```

3. **Deploy PostgreSQL StatefulSet**:
   ```bash
   kubectl apply -f k8s/postgres-statefulset.yaml -n vpp-phase2
   ```

4. **Deploy Redis cluster**:
   ```bash
   kubectl apply -f k8s/redis-deployment.yaml -n vpp-phase2
   ```

5. **Deploy VPP Phase 2 Simulation**:
   ```bash
   kubectl apply -f k8s/vpp-deployment.yaml -n vpp-phase2
   ```

6. **Deploy Prometheus and Grafana**:
   ```bash
   kubectl apply -f k8s/prometheus-deployment.yaml -n vpp-phase2
   kubectl apply -f k8s/grafana-deployment.yaml -n vpp-phase2
   ```

7. **Setup Ingress**:
   ```bash
   kubectl apply -f k8s/ingress.yaml -n vpp-phase2
   ```

8. **Verify deployment**:
   ```bash
   kubectl get pods -n vpp-phase2
   kubectl get svc -n vpp-phase2
   ```

### Scaling Considerations

- **Horizontal Scaling**: Deploy multiple replicas of the VPP simulation service
- **Database Scaling**: Use PostgreSQL read replicas for query scaling
- **Caching**: Redis cluster for distributed caching
- **Load Balancing**: Use Kubernetes Service with load balancer

## Environment Configuration

### Environment Variables

Create `.env` file with the following variables:

```bash
# Application
ENV=development
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8080
API_WORKERS=4

# Database
DATABASE_URL=postgresql://vpp_user:vpp_password@localhost:5432/vpp_phase2_sim
DATABASE_POOL_SIZE=20
DATABASE_POOL_RECYCLE=3600

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/vpp_phase2_sim.log
LOG_FORMAT=json

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8081

# Security
SECRET_KEY=your-secret-key-here
CORS_ENABLED=true
CORS_ORIGINS=*

# Features
ENABLE_POWER_FLOW=true
ENABLE_METRICS=true
ENABLE_VISUALIZATION=true
```

### Production Environment Variables

For production, use secure values:

```bash
ENV=production
DEBUG=false
API_WORKERS=8
DATABASE_POOL_SIZE=50
LOG_LEVEL=WARNING
CORS_ORIGINS=https://your-domain.com
```

## Database Setup and Migration

### Initial Database Setup

1. **Create database schema**:
   ```bash
   python -c "from utils.database import init_db; init_db()"
   ```

2. **Verify schema**:
   ```bash
   psql -U vpp_user -d vpp_phase2_sim -c "\dt"
   ```

### Database Backup

1. **Create backup**:
   ```bash
   pg_dump -U vpp_user vpp_phase2_sim > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Restore from backup**:
   ```bash
   psql -U vpp_user vpp_phase2_sim < backup_20260216_100000.sql
   ```

### Database Maintenance

1. **Vacuum database**:
   ```bash
   psql -U vpp_user -d vpp_phase2_sim -c "VACUUM ANALYZE;"
   ```

2. **Check database size**:
   ```bash
   psql -U vpp_user -d vpp_phase2_sim -c "SELECT pg_size_pretty(pg_database_size('vpp_phase2_sim'));"
   ```

## Running Tests

### Unit Tests

1. **Run all unit tests**:
   ```bash
   pytest tests/ -v
   ```

2. **Run specific test file**:
   ```bash
   pytest tests/test_device_api.py -v
   ```

3. **Run with coverage**:
   ```bash
   pytest tests/ --cov=. --cov-report=html
   ```

### Property-Based Tests

1. **Run property tests**:
   ```bash
   pytest tests/ -k "property" -v
   ```

2. **Run with specific number of examples**:
   ```bash
   pytest tests/ -k "property" --hypothesis-seed=12345 -v
   ```

### Integration Tests

1. **Run integration tests**:
   ```bash
   pytest tests/test_integration_suite.py -v
   ```

2. **Run end-to-end tests**:
   ```bash
   pytest tests/test_e2e_scenarios.py -v
   ```

## Monitoring and Logging Setup

### Prometheus Metrics

1. **Access Prometheus**:
   - URL: http://localhost:9090
   - Metrics endpoint: http://localhost:8080/metrics

2. **Key metrics to monitor**:
   - `vpp_sim_device_count` - Number of active devices
   - `vpp_sim_power_output_watts` - Power output by device type
   - `vpp_sim_scenario_execution_time_seconds` - Scenario execution time
   - `vpp_sim_power_flow_calculation_time_ms` - Power flow calculation time

### Grafana Dashboards

1. **Access Grafana**:
   - URL: http://localhost:3000
   - Default credentials: admin/admin

2. **Import dashboards**:
   - Navigate to Dashboards > Import
   - Upload dashboard JSON files from `k8s/grafana-dashboards/`

3. **Create alerts**:
   - Setup alert rules for critical metrics
   - Configure notification channels (email, Slack, etc.)

### Structured Logging

Logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2026-02-16T10:30:00Z",
  "level": "INFO",
  "logger": "vpp.services.scenario_engine",
  "message": "Scenario execution started",
  "request_id": "req-abc123def456",
  "scenario_id": "scenario-123",
  "device_count": 1000,
  "duration_ms": 45
}
```

### Log Aggregation

1. **Setup ELK Stack** (optional):
   ```bash
   docker-compose -f docker-compose.elk.yml up -d
   ```

2. **Access Kibana**:
   - URL: http://localhost:5601

## Troubleshooting Guide

### Common Issues

#### 1. Database Connection Failed

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check database credentials
psql -U vpp_user -d vpp_phase2_sim -c "SELECT 1"

# Check connection string in .env
cat .env | grep DATABASE_URL
```

#### 2. Redis Connection Failed

**Error**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solution**:
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli ping

# Check Redis configuration
redis-cli CONFIG GET "*"
```

#### 3. API Not Responding

**Error**: `Connection refused` or `timeout`

**Solution**:
```bash
# Check if API is running
curl http://localhost:8080/health

# Check logs
docker logs vpp-phase2-simulation

# Check port is not in use
lsof -i :8080

# Restart service
docker-compose restart vpp-phase2-simulation
```

#### 4. High Memory Usage

**Error**: `Out of memory` or service crashes

**Solution**:
```bash
# Check memory usage
docker stats vpp-phase2-simulation

# Increase memory limit in docker-compose.yml
# Restart with new limits
docker-compose up -d

# Check for memory leaks in logs
grep -i "memory" logs/vpp_phase2_sim.log
```

#### 5. Slow Query Performance

**Error**: Queries taking >500ms

**Solution**:
```bash
# Enable query logging
psql -U vpp_user -d vpp_phase2_sim -c "SET log_min_duration_statement = 500;"

# Check slow query log
tail -f logs/postgresql.log | grep "duration:"

# Analyze query plan
EXPLAIN ANALYZE SELECT * FROM scenarios WHERE status = 'completed';

# Create indexes if needed
CREATE INDEX idx_scenarios_status ON scenarios(status);
```

#### 6. Metrics Not Appearing

**Error**: Prometheus shows no data

**Solution**:
```bash
# Check metrics endpoint
curl http://localhost:8080/metrics

# Check Prometheus configuration
cat k8s/prometheus-config.yaml

# Verify metrics are being recorded
grep "vpp_sim_" logs/vpp_phase2_sim.log

# Restart Prometheus
docker-compose restart prometheus
```

### Performance Tuning

#### Database Optimization

1. **Connection pooling**:
   ```bash
   # Increase pool size in .env
   DATABASE_POOL_SIZE=50
   ```

2. **Query optimization**:
   ```bash
   # Enable query logging
   psql -U vpp_user -d vpp_phase2_sim -c "SET log_statement = 'all';"
   ```

3. **Index creation**:
   ```bash
   # Create indexes for frequently queried columns
   CREATE INDEX idx_scenarios_created_at ON scenarios(created_at);
   CREATE INDEX idx_metrics_scenario_id ON metrics(scenario_id);
   ```

#### Application Optimization

1. **Increase workers**:
   ```bash
   # In .env
   API_WORKERS=8
   ```

2. **Enable caching**:
   ```bash
   # In .env
   REDIS_ENABLED=true
   CACHE_TTL=3600
   ```

3. **Optimize logging**:
   ```bash
   # In .env
   LOG_LEVEL=WARNING  # Reduce logging overhead
   ```

### Health Checks

1. **API health**:
   ```bash
   curl http://localhost:8080/health
   ```

2. **Readiness check**:
   ```bash
   curl http://localhost:8080/ready
   ```

3. **Database health**:
   ```bash
   psql -U vpp_user -d vpp_phase2_sim -c "SELECT 1"
   ```

4. **Redis health**:
   ```bash
   redis-cli ping
   ```

## Support and Documentation

- **API Documentation**: http://localhost:8080/api/docs
- **OpenAPI Spec**: http://localhost:8080/api/openapi.json
- **GitHub Issues**: <repository-issues-url>
- **Documentation**: <documentation-url>
