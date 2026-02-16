# VPP Master API - Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for common issues encountered when running the VPP Master API. It includes debugging procedures, log analysis, and solutions for various failure scenarios.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [API Issues](#api-issues)
3. [Database Issues](#database-issues)
4. [Authentication Issues](#authentication-issues)
5. [Performance Issues](#performance-issues)
6. [Deployment Issues](#deployment-issues)
7. [Protocol Conversion Issues](#protocol-conversion-issues)
8. [Analysis Issues](#analysis-issues)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Advanced Debugging](#advanced-debugging)

## Quick Diagnostics

### Health Check

Start with the health endpoint to verify system status:

```bash
# Check API health
curl -v http://localhost:8080/health

# Expected response (200 OK):
{
  "status": "healthy",
  "timestamp": "2026-02-16T10:30:00Z",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### System Status

```bash
# Check all services
docker-compose ps

# Expected output:
# NAME                COMMAND             STATUS
# vpp-api             python3 app.py      Up 2 hours
# postgres            postgres            Up 2 hours
# redis               redis-server        Up 2 hours
# prometheus          prometheus          Up 2 hours
```

### Quick Verification

```bash
# 1. Check API is responding
curl http://localhost:8080/health

# 2. Check database connection
docker-compose exec postgres pg_isready -U vpp_user

# 3. Check Redis connection
docker-compose exec redis redis-cli ping

# 4. Check logs for errors
docker-compose logs --tail=50 | grep -i error
```

## API Issues

### 401 Unauthorized

**Symptom:** All API requests return 401 Unauthorized

**Diagnosis:**
```bash
# Test without authentication
curl http://localhost:8080/api/v1/devices

# Test with API key
curl -H "X-API-Key: your-key" http://localhost:8080/api/v1/devices

# Check API key in environment
docker-compose exec vpp-api env | grep API_KEY
```

**Solutions:**

1. **Verify API key is set:**
```bash
# Check .env file
cat .env | grep API_KEY

# If not set, add to .env
echo "API_KEY=your-secure-key-here" >> .env

# Restart service
docker-compose restart vpp-api
```

2. **Verify API key format:**
```bash
# API key should be 32+ characters
# Test with correct format
curl -H "X-API-Key: abc123def456ghi789jkl012mno345pqr" \
  http://localhost:8080/api/v1/devices
```

3. **Check authentication middleware:**
```bash
# View logs for auth errors
docker-compose logs vpp-api | grep -i "auth\|unauthorized"

# Enable debug logging
docker-compose exec vpp-api env | grep LOG_LEVEL
# If not DEBUG, set it:
# LOG_LEVEL=DEBUG in .env
```

### 400 Bad Request

**Symptom:** API requests return 400 Bad Request with validation errors

**Diagnosis:**
```bash
# Test with invalid JSON
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{invalid json}'

# Check error response
# Should show specific validation errors
```

**Solutions:**

1. **Validate JSON:**
```bash
# Use jq to validate JSON
echo '{"id":"test"}' | jq .

# Pretty print error response
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"invalid":"data"}' | jq .
```

2. **Check required fields:**
```bash
# Device registration requires: id, device_type, location, capabilities
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "id": "device-001",
    "device_type": "solar",
    "location": "Building A",
    "capabilities": {"max_power": 10000}
  }'
```

3. **Verify data types:**
```bash
# Check OpenAPI spec for expected types
curl http://localhost:8080/api/openapi.json | jq '.components.schemas.Device'

# Ensure all fields match expected types
# Strings: "value"
# Numbers: 123 or 123.45
# Booleans: true or false
# Objects: {}
# Arrays: []
```

### 404 Not Found

**Symptom:** Resource not found errors

**Diagnosis:**
```bash
# List all devices to verify ID exists
curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | jq '.data[].id'

# Try to get specific device
curl http://localhost:8080/api/v1/devices/device-id \
  -H "X-API-Key: your-key"
```

**Solutions:**

1. **Verify resource exists:**
```bash
# List all devices
curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | jq .

# Check if device_id is in the list
# If not, create it first
```

2. **Check for typos:**
```bash
# Device IDs are case-sensitive
# Verify exact spelling and case
curl http://localhost:8080/api/v1/devices/device-solar-001 \
  -H "X-API-Key: your-key"
```

### 429 Rate Limited

**Symptom:** Getting 429 Too Many Requests

**Diagnosis:**
```bash
# Check rate limit headers
curl -i http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | grep X-RateLimit

# Check remaining requests
curl -i http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | grep X-RateLimit-Remaining
```

**Solutions:**

1. **Reduce request frequency:**
```bash
# Wait before making more requests
sleep 60

# Then retry
curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key"
```

2. **Implement exponential backoff:**
```python
import time
import requests

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        
        if response.status_code == 429:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

3. **Batch requests:**
```bash
# Instead of multiple requests, batch operations
# Get all devices in one request
curl "http://localhost:8080/api/v1/devices?page_size=100" \
  -H "X-API-Key: your-key"
```

### 500 Internal Server Error

**Symptom:** API returns 500 Internal Server Error

**Diagnosis:**
```bash
# Check application logs
docker-compose logs vpp-api --tail=100

# Look for stack traces and error messages
docker-compose logs vpp-api | grep -i "error\|exception\|traceback"

# Check error ID from response
curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | jq '.error.details.error_id'
```

**Solutions:**

1. **Check database connection:**
```bash
# Verify database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres pg_isready -U vpp_user
```

2. **Check application logs:**
```bash
# View full logs with timestamps
docker-compose logs --timestamps vpp-api

# Follow logs in real-time
docker-compose logs -f vpp-api

# Search for specific error
docker-compose logs vpp-api | grep "error_id"
```

3. **Restart services:**
```bash
# Restart API service
docker-compose restart vpp-api

# If that doesn't work, restart all services
docker-compose restart

# Check if issue persists
curl http://localhost:8080/health
```

## Database Issues

### Database Connection Failed

**Symptom:** "Cannot connect to database" errors

**Diagnosis:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c "SELECT 1"
```

**Solutions:**

1. **Start database:**
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for it to be ready
sleep 10

# Verify connection
docker-compose exec postgres pg_isready -U vpp_user
```

2. **Check credentials:**
```bash
# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Format should be:
# postgresql://username:password@host:port/database

# Test connection with correct credentials
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c "SELECT 1"
```

3. **Check database exists:**
```bash
# List databases
docker-compose exec postgres psql -U postgres -l

# If vpp_prod doesn't exist, create it
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE vpp_prod OWNER vpp_user;"
```

### Slow Database Queries

**Symptom:** API responses are slow, database queries taking too long

**Diagnosis:**
```bash
# Check slow query log
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check query execution plan
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "EXPLAIN ANALYZE SELECT * FROM devices WHERE status = 'online';"
```

**Solutions:**

1. **Create indexes:**
```bash
# Create indexes for frequently queried fields
docker-compose exec postgres psql -U vpp_user -d vpp_prod << EOF
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_created_at ON devices(created_at);
CREATE INDEX idx_dispatches_device_id ON dispatches(device_id);
CREATE INDEX idx_dispatches_status ON dispatches(status);
EOF
```

2. **Analyze tables:**
```bash
# Update table statistics
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "ANALYZE devices; ANALYZE dispatches;"
```

3. **Check connection pool:**
```bash
# View current connections
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "SELECT count(*) FROM pg_stat_activity;"

# If too many connections, increase pool size in .env
# DB_POOL_SIZE=30
```

### Database Disk Space

**Symptom:** "No space left on device" errors

**Diagnosis:**
```bash
# Check disk usage
docker-compose exec postgres df -h

# Check database size
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "SELECT pg_size_pretty(pg_database_size('vpp_prod'));"
```

**Solutions:**

1. **Clean up old data:**
```bash
# Delete old dispatch records (older than 90 days)
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "DELETE FROM dispatches WHERE created_at < NOW() - INTERVAL '90 days';"

# Vacuum database
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c "VACUUM ANALYZE;"
```

2. **Increase disk space:**
```bash
# For Docker volumes, increase Docker disk allocation
# Edit Docker Desktop settings or docker daemon.json

# For mounted volumes, add more disk space to the host
```

## Authentication Issues

### JWT Token Expired

**Symptom:** "Token expired" errors

**Diagnosis:**
```bash
# Decode JWT token to check expiration
# Use jwt.io or:
python3 -c "import jwt; print(jwt.decode('token', options={'verify_signature': False}))"

# Check token expiration time
curl -H "Authorization: Bearer token" http://localhost:8080/api/v1/devices | jq '.error'
```

**Solutions:**

1. **Get new token:**
```bash
# Request new token from auth endpoint
curl -X POST http://localhost:8080/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Use new token in requests
curl -H "Authorization: Bearer new-token" http://localhost:8080/api/v1/devices
```

2. **Increase token expiration:**
```bash
# In .env, increase JWT_EXPIRATION (in seconds)
JWT_EXPIRATION=604800  # 7 days instead of 24 hours

# Restart service
docker-compose restart vpp-api
```

### Insufficient Permissions

**Symptom:** "Insufficient permissions" or 403 Forbidden errors

**Diagnosis:**
```bash
# Check user roles
curl -H "Authorization: Bearer token" http://localhost:8080/api/v1/user/profile | jq '.data.roles'

# Check required permissions for endpoint
curl http://localhost:8080/api/openapi.json | jq '.paths["/api/v1/dispatch"].post.security'
```

**Solutions:**

1. **Grant required role:**
```bash
# Update user role in database
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "UPDATE users SET roles = '{admin,operator}' WHERE id = 'user-id';"
```

2. **Use different user:**
```bash
# Try with admin user
curl -H "Authorization: Bearer admin-token" http://localhost:8080/api/v1/dispatch
```

## Performance Issues

### High CPU Usage

**Symptom:** API server using excessive CPU

**Diagnosis:**
```bash
# Check CPU usage
docker stats vpp-api

# Check which process is using CPU
docker-compose exec vpp-api top -b -n 1 | head -20

# Check for infinite loops in logs
docker-compose logs vpp-api | grep -i "loop\|hang\|stuck"
```

**Solutions:**

1. **Identify slow operations:**
```bash
# Enable profiling
# Add to app.py:
# from werkzeug.middleware.profiler import ProfilerMiddleware
# app = ProfilerMiddleware(app)

# Check profiling output
docker-compose logs vpp-api | grep "profile"
```

2. **Optimize code:**
```bash
# Review slow functions
# Use caching for expensive operations
# Implement pagination for large queries
```

3. **Restart service:**
```bash
# Restart API service
docker-compose restart vpp-api

# Monitor CPU after restart
docker stats vpp-api
```

### High Memory Usage

**Symptom:** API server using excessive memory

**Diagnosis:**
```bash
# Check memory usage
docker stats vpp-api

# Check memory usage over time
docker stats --no-stream vpp-api

# Check for memory leaks in logs
docker-compose logs vpp-api | grep -i "memory\|leak"
```

**Solutions:**

1. **Reduce cache size:**
```bash
# In .env, reduce cache settings
CACHE_SIZE=100  # Reduce from default

# Restart service
docker-compose restart vpp-api
```

2. **Increase container memory:**
```bash
# In docker-compose.yml, add memory limit
services:
  vpp-api:
    mem_limit: 2g
    memswap_limit: 2g

# Restart service
docker-compose restart vpp-api
```

3. **Monitor memory:**
```bash
# Watch memory usage
watch -n 1 'docker stats vpp-api --no-stream'
```

### Slow Response Times

**Symptom:** API responses are slow (>1 second)

**Diagnosis:**
```bash
# Measure response time
time curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key"

# Check response time in headers
curl -i http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | grep -i "time"

# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=vpp_api_request_duration_seconds
```

**Solutions:**

1. **Check database performance:**
```bash
# Identify slow queries
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Create indexes for slow queries
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "CREATE INDEX idx_devices_status ON devices(status);"
```

2. **Enable caching:**
```bash
# Check Redis is running
docker-compose ps redis

# Verify Redis connection
docker-compose exec redis redis-cli ping

# Check cache hit ratio
docker-compose exec redis redis-cli INFO stats
```

3. **Optimize queries:**
```bash
# Use pagination for large result sets
curl "http://localhost:8080/api/v1/devices?page_size=50" \
  -H "X-API-Key: your-key"

# Use filters to reduce result set
curl "http://localhost:8080/api/v1/dispatch/history?status=completed" \
  -H "X-API-Key: your-key"
```

## Deployment Issues

### Container Won't Start

**Symptom:** Docker container exits immediately

**Diagnosis:**
```bash
# Check container logs
docker-compose logs vpp-api

# Check container status
docker-compose ps vpp-api

# Try to run container manually
docker-compose run --rm vpp-api python3 app.py
```

**Solutions:**

1. **Check for startup errors:**
```bash
# View full logs
docker-compose logs vpp-api --tail=100

# Look for import errors, syntax errors, etc.
```

2. **Verify dependencies:**
```bash
# Check if all dependencies are installed
docker-compose exec vpp-api pip list

# Reinstall dependencies
docker-compose exec vpp-api pip install -r requirements.txt
```

3. **Check environment variables:**
```bash
# Verify all required env vars are set
docker-compose exec vpp-api env | grep -E "DATABASE_URL|API_KEY|LOG_LEVEL"

# If missing, add to .env and restart
docker-compose restart vpp-api
```

### Port Already in Use

**Symptom:** "Address already in use" error

**Diagnosis:**
```bash
# Find process using port 8080
lsof -i :8080

# Or on Windows
netstat -ano | findstr :8080
```

**Solutions:**

1. **Kill existing process:**
```bash
# Kill process using port
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8081:8080"
```

2. **Use different port:**
```bash
# Edit docker-compose.yml
ports:
  - "8081:8080"

# Restart services
docker-compose restart vpp-api

# Access on new port
curl http://localhost:8081/health
```

## Protocol Conversion Issues

### IEC 104 Parsing Fails

**Symptom:** "Invalid IEC 104 message" errors

**Diagnosis:**
```bash
# Test protocol parsing
curl -X POST http://localhost:8080/api/v1/protocol/parse \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"protocol":"IEC104","data":"invalid-data"}'

# Check error response
# Should show specific parsing error
```

**Solutions:**

1. **Verify message format:**
```bash
# IEC 104 message should be base64 encoded
# Verify encoding
echo "message-data" | base64

# Use encoded data in request
curl -X POST http://localhost:8080/api/v1/protocol/parse \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"protocol":"IEC104","data":"bWVzc2FnZS1kYXRh"}'
```

2. **Check protocol adapter:**
```bash
# View protocol adapter logs
docker-compose logs vpp-api | grep -i "protocol\|iec104"

# Check if adapter is loaded
docker-compose exec vpp-api python3 -c "from services.protocol_converter import IEC104Adapter; print('OK')"
```

### MQTT Encoding Fails

**Symptom:** "Cannot encode to MQTT" errors

**Diagnosis:**
```bash
# Test MQTT encoding
curl -X POST http://localhost:8080/api/v1/protocol/encode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"protocol":"MQTT","data":{"invalid":"structure"}}'

# Check error response
```

**Solutions:**

1. **Verify data structure:**
```bash
# Check expected MQTT data format
curl http://localhost:8080/api/openapi.json | jq '.paths["/api/v1/protocol/encode"]'

# Ensure data matches expected schema
curl -X POST http://localhost:8080/api/v1/protocol/encode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "protocol":"MQTT",
    "data":{"device_id":"device-001","power":5000},
    "qos":1
  }'
```

## Analysis Issues

### Power Flow Analysis Fails to Converge

**Symptom:** "Analysis failed to converge" errors

**Diagnosis:**
```bash
# Test power flow analysis
curl -X POST http://localhost:8080/api/v1/analysis/power-flow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"system_state":{"buses":[],"generators":[],"loads":[]}}'

# Check error response for convergence details
```

**Solutions:**

1. **Verify system state:**
```bash
# Ensure system state is valid
# Check for:
# - At least one slack bus
# - Balanced power (generation = load + loss)
# - Valid bus voltages (0.9 - 1.1 pu)

# Provide valid system state
curl -X POST http://localhost:8080/api/v1/analysis/power-flow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "system_state":{
      "buses":[{"bus_id":1,"voltage":1.0,"angle":0,"type":"slack"}],
      "generators":[{"gen_id":1,"bus":1,"p":100,"q":0}],
      "loads":[{"load_id":1,"bus":1,"p":100,"q":0}]
    }
  }'
```

2. **Check pandapower installation:**
```bash
# Verify pandapower is installed
docker-compose exec vpp-api python3 -c "import pandapower; print(pandapower.__version__)"

# If not installed, install it
docker-compose exec vpp-api pip install pandapower
```

### Analysis Takes Too Long

**Symptom:** Analysis requests timeout (>5 seconds)

**Diagnosis:**
```bash
# Measure analysis time
time curl -X POST http://localhost:8080/api/v1/analysis/power-flow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"system_state":{...}}'

# Check if system is large
# Large systems (>1000 buses) may take longer
```

**Solutions:**

1. **Reduce system size:**
```bash
# Use smaller system for testing
# Reduce number of buses, generators, loads
```

2. **Increase timeout:**
```bash
# In .env, increase analysis timeout
ANALYSIS_TIMEOUT=30  # seconds

# Restart service
docker-compose restart vpp-api
```

## Monitoring and Logging

### Enable Debug Logging

```bash
# Set LOG_LEVEL to DEBUG in .env
LOG_LEVEL=DEBUG

# Restart service
docker-compose restart vpp-api

# View debug logs
docker-compose logs -f vpp-api
```

### View Structured Logs

```bash
# Logs are in JSON format
docker-compose logs vpp-api | jq .

# Filter by log level
docker-compose logs vpp-api | jq 'select(.level=="ERROR")'

# Filter by component
docker-compose logs vpp-api | jq 'select(.logger | contains("device_manager"))'

# Filter by request ID
docker-compose logs vpp-api | jq 'select(.request_id=="req-abc123")'
```

### Monitor Metrics

```bash
# Query Prometheus for metrics
curl 'http://localhost:9090/api/v1/query?query=vpp_api_requests_total'

# Get request rate
curl 'http://localhost:9090/api/v1/query?query=rate(vpp_api_requests_total[5m])'

# Get error rate
curl 'http://localhost:9090/api/v1/query?query=rate(vpp_api_errors_total[5m])'

# Get response time p95
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,vpp_api_request_duration_seconds)'
```

## Advanced Debugging

### Enable Profiling

```bash
# Add profiling middleware to app.py
from werkzeug.middleware.profiler import ProfilerMiddleware
app = ProfilerMiddleware(app, restrictions=[30])

# Restart service
docker-compose restart vpp-api

# Make request and check profiling output
curl http://localhost:8080/api/v1/devices -H "X-API-Key: your-key"

# View profiling results in logs
docker-compose logs vpp-api | grep "profile"
```

### Database Query Debugging

```bash
# Enable query logging in PostgreSQL
docker-compose exec postgres psql -U vpp_user -d vpp_prod -c \
  "ALTER SYSTEM SET log_statement = 'all';"

# Reload configuration
docker-compose exec postgres psql -U postgres -c "SELECT pg_reload_conf();"

# View query logs
docker-compose exec postgres tail -f /var/log/postgresql/postgresql.log
```

### Network Debugging

```bash
# Check network connectivity
docker-compose exec vpp-api ping postgres

# Check DNS resolution
docker-compose exec vpp-api nslookup postgres

# Check port connectivity
docker-compose exec vpp-api nc -zv postgres 5432

# Check network interfaces
docker-compose exec vpp-api ip addr
```

### Container Inspection

```bash
# Inspect container configuration
docker inspect vpp-api

# Check environment variables
docker inspect vpp-api | jq '.[0].Config.Env'

# Check mounted volumes
docker inspect vpp-api | jq '.[0].Mounts'

# Check network settings
docker inspect vpp-api | jq '.[0].NetworkSettings'
```

### Log Aggregation

```bash
# Export logs to file
docker-compose logs > all-logs.txt

# Export specific service logs
docker-compose logs vpp-api > api-logs.txt

# Export with timestamps
docker-compose logs --timestamps > logs-with-timestamps.txt

# Follow logs in real-time
docker-compose logs -f --tail=100
```

## Getting Help

If you're unable to resolve an issue:

1. **Collect diagnostic information:**
```bash
# Create diagnostic bundle
mkdir diagnostics
docker-compose ps > diagnostics/services.txt
docker-compose logs > diagnostics/logs.txt
curl http://localhost:8080/health > diagnostics/health.json
curl http://localhost:8080/api/openapi.json > diagnostics/openapi.json
docker stats --no-stream > diagnostics/stats.txt
```

2. **Review logs carefully:**
   - Look for error messages and stack traces
   - Note timestamps of errors
   - Check for patterns in error messages

3. **Test in isolation:**
   - Test individual components separately
   - Use curl to test API endpoints directly
   - Test database connection separately

4. **Contact support with:**
   - Diagnostic bundle
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
