# VPP Traffic Visualization Engine - Quick Start with Docker

## 5-Minute Setup

### Step 1: Prerequisites

Ensure you have Docker and Docker Compose installed:

```bash
docker --version
docker-compose --version
```

### Step 2: Navigate to Project Directory

```bash
cd vpp-traffic-visualization
```

### Step 3: Start the Application

Using the deployment script (recommended):

```bash
chmod +x deploy.sh
./deploy.sh start
```

Or using Docker Compose directly:

```bash
docker-compose up -d
```

### Step 4: Wait for Service to Start

The service typically starts within 10-15 seconds. Check status:

```bash
docker-compose ps
```

### Step 5: Access the Application

Open your browser and navigate to:

- **Frontend Dashboard**: http://localhost
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f nginx
```

### Stop Application

```bash
./deploy.sh stop
# or
docker-compose down
```

### Restart Application

```bash
./deploy.sh restart
# or
docker-compose restart
```

### Check Service Status

```bash
./deploy.sh status
# or
docker-compose ps
```

## Troubleshooting

### Port Already in Use

If port 80 or 5000 is already in use:

1. Find the process using the port:
```bash
lsof -i :80
lsof -i :5000
```

2. Either stop that process or change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:80"    # Change 80 to 8080
```

### Container Won't Start

Check the logs:

```bash
docker-compose logs backend
```

Common issues:
- Port already in use
- Insufficient disk space
- Docker daemon not running

### WebSocket Connection Failed

1. Verify nginx is running:
```bash
docker-compose logs nginx
```

2. Check nginx configuration:
```bash
docker-compose exec nginx nginx -t
```

3. Verify backend is accessible:
```bash
curl http://localhost:5000/api/health
```

## Next Steps

1. **Explore the Dashboard**: Open http://localhost and interact with the visualization
2. **Check API Documentation**: Review the API endpoints at http://localhost:5000/api/
3. **View Logs**: Monitor application logs with `docker-compose logs -f`
4. **Configure**: Edit `docker-compose.yml` for custom settings

## File Structure

```
vpp-traffic-visualization/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── nginx.conf             # Nginx reverse proxy configuration
├── deploy.sh              # Deployment script
├── verify-docker.sh       # Verification script
├── backend/               # Flask backend application
│   ├── app.py            # Main Flask app
│   ├── requirements.txt   # Python dependencies
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── routes/           # API routes
│   └── tests/            # Unit tests
└── frontend/             # Web frontend
    ├── index.html        # Main HTML page
    ├── css/              # Stylesheets
    └── js/               # JavaScript modules
```

## Performance Tips

1. **Allocate sufficient resources** to Docker:
   - Minimum: 2GB RAM
   - Recommended: 4GB RAM

2. **Monitor resource usage**:
```bash
docker stats
```

3. **Optimize for high traffic**:
   - Increase worker processes in nginx.conf
   - Adjust Flask worker count
   - Enable caching

## Security Notes

For production deployment:

1. **Enable HTTPS**:
   - Generate SSL certificates
   - Place in `ssl/` directory
   - Update nginx.conf

2. **Change default ports**:
   - Don't expose on port 80/443 directly
   - Use firewall rules
   - Consider reverse proxy

3. **Secure the API**:
   - Add authentication
   - Implement rate limiting
   - Validate all inputs

## Support

For detailed information, see:
- `DOCKER_DEPLOYMENT.md` - Comprehensive deployment guide
- `README.md` - Project overview
- Backend logs: `docker-compose logs backend`
- Nginx logs: `docker-compose logs nginx`

## Clean Up

To remove all containers and volumes:

```bash
./deploy.sh clean
# or
docker-compose down -v
```

This will remove:
- All containers
- All volumes
- Network configuration

Data will be lost unless backed up first.
