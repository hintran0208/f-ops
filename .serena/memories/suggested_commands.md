# Suggested Commands for F-Ops Development

## Running the Application

### Backend Server
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or run directly with Python
cd backend
uvicorn app.main:app --reload --port 8000

# For development with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### CLI
```bash
# Install CLI in development mode
cd cli
pip install -e .

# Use CLI
fops --help
fops onboard --repo <url> --target k8s --env staging,prod
fops deploy --service <name> --env <env>
fops kb search "<query>"
fops incident --service <name>
```

## Development Setup
```bash
# Initial setup (run from project root)
./setup.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install -e cli/
```

## Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=backend tests/

# Run end-to-end tests
python tests/test_e2e.py
```

## Code Quality
```bash
# Format code with ruff (available on system)
ruff format backend/ cli/

# Lint code
ruff check backend/ cli/

# Type checking (if mypy installed)
mypy backend/
```

## Docker Operations
```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

## Git Operations
```bash
# Check status
git status

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add knowledge base search functionality"

# Push to remote
git push origin main
```

## System Utilities (macOS/Darwin)
```bash
# List files (macOS ls)
ls -la

# Find files
find . -name "*.py" -type f

# Search in files (using ripgrep if available, otherwise grep)
rg "pattern" --type py
grep -r "pattern" --include="*.py" .

# Check Python environment
python --version
which python
pyenv versions

# Environment variables
export FOPS_API_URL=http://localhost:8000
source .env
```

## API Testing
```bash
# Health check
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Test onboarding endpoint
curl -X POST http://localhost:8000/api/onboard/repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "target": "k8s"}'
```

## Monitoring
```bash
# Access Prometheus
open http://localhost:9090

# Access Grafana (admin/admin)
open http://localhost:3000
```