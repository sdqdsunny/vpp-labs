# VPP Phase 2 Simulation Framework - Quick Start Guide

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 12+ (for production)
- Redis 6+ (for caching)
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/sdqdsunny/power-emulator.git
cd power-emulator
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
cd vpp-phase2-simulation
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database**
```bash
python3 -c "from utils.database import init_db; init_db()"
```

6. **Run tests**
```bash
python3 -m pytest tests/ -v
```

7. **Start application**
```bash
python3 app.py
```

The API will be available at `http://localhost:8001`

## Docker Development

### Using Docker Compose

1. **Start all services**
```bash
docker-compose up -d
```

2. **Check service status**
```bash
docker-compose ps
```

3. **View logs**
```bash
docker-compose logs -f vpp-phase2-sim
```

4. **Stop services**
```bash
docker-compose down
```

### Services Available

- **VPP Phase 2 Simulation**: http://localhost:8001
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## API Endpoints

### Health Check
```bash
curl http://localhost:8001/health
```

### Readiness Check
```bash
curl http://localhost:8001/ready
```

## Project Structure

```
vpp-phase2-simulation/
├── app.py                 # Main application
├── config.py              # Configuration
├── models/                # Database models
├── services/              # Business logic
├── routes/                # API endpoints
├── middleware/            # Middleware
├── utils/                 # Utilities
├── tests/                 # Tests
└── requirements.txt       # Dependencies
```

## Configuration

### Environment Variables

```bash
# Environment
ENV=development
DEBUG=False

# Database
DATABASE_URL=sqlite:///vpp_phase2_sim.db

# Logging
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8001

# Simulation
MAX_DEVICES=10000
MAX_SCENARIOS=100
```

## Testing

### Run all tests
```bash
python3 -m pytest tests/ -v
```

### Run specific test file
```bash
python3 -m pytest tests/test_infrastructure.py -v
```

### Run with coverage
```bash
python3 -m pytest tests/ --cov=. --cov-report=html
```

### Run property-based tests
```bash
python3 -m pytest tests/ -v -k "property"
```

## Development Workflow

1. **Create feature branch**
```bash
git checkout -b feature/my-feature
```

2. **Make changes and test**
```bash
python3 -m pytest tests/ -v
```

3. **Format code**
```bash
black .
flake8 .
```

4. **Commit and push**
```bash
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

5. **Create pull request**

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database credentials

### Port Already in Use
- Change API_PORT in .env
- Or kill process: `lsof -ti:8001 | xargs kill -9`

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check PYTHONPATH

### Test Failures
- Check database is initialized
- Ensure all dependencies installed
- Review test logs for details

## Documentation

- [Architecture Design](../docs/ARCHITECTURE.md)
- [API Documentation](../docs/API.md)
- [Database Schema](../docs/SCHEMA.md)
- [Testing Guide](../docs/TESTING.md)

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review documentation
3. Create new GitHub issue with details

## License

See LICENSE file in repository root.
