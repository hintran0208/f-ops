# F-Ops Development Commands

## Quick Start (Recommended)

### 1. Initial Setup
```bash
# Clone and setup environment
cp .env.example .env
# Edit .env with your API keys

# Run setup script
./setup.sh
```

### 2. Running the Backend Server
```bash
# Option 1: Simple Python script (recommended for development)
python run_backend.py

# Option 2: Direct uvicorn command
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

# Option 3: Using Docker Compose
docker-compose up -d
```

### 3. Install CLI
```bash
cd cli
pip install -e .
fops --help
```

## Development Commands

### Backend Development
```bash
# Start development server with hot reload
cd backend
uvicorn app.main:app --reload --port 8002

# Alternative simplified server
uvicorn app.main_simple:app --reload --port 8002

# Run with custom Python path (if needed)
PYTHONPATH=/path/to/f-ops:$PYTHONPATH uvicorn app.main:app --reload --port 8002
```

### CLI Development & Testing
```bash
# Install CLI in development mode
cd cli
pip install -e .

# Test CLI commands
fops --help
fops version
fops status
fops init

# Test onboarding (primary workflow)
fops onboard --repo https://github.com/user/repo --target k8s --env staging,prod

# Test knowledge base
fops kb search "kubernetes deployment"
fops kb connect --uri https://docs.example.com
```

### Docker Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild after changes
docker-compose build backend
docker-compose up -d backend

# Stop all services
docker-compose down
```

## Testing

### Basic Testing
```bash
# Run E2E tests
python tests/test_e2e.py

# Test API endpoints manually
curl http://localhost:8002/health
curl http://localhost:8002/
```

### API Testing
```bash
# Check API status
curl http://localhost:8002/health

# Test onboarding endpoint
curl -X POST http://localhost:8002/api/onboard/repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/test/repo", "target": "k8s"}'
```

## Useful System Commands (macOS/Darwin)

### File Operations
```bash
# List files (macOS)
ls -la
find . -name "*.py" -type f
grep -r "pattern" . --include="*.py"

# Git operations
git status
git add .
git commit -m "message"
git push
```

### Process Management
```bash
# Find running processes
ps aux | grep uvicorn
lsof -i :8002

# Kill processes on port
lsof -ti:8002 | xargs kill -9
```

### Environment Management
```bash
# Python virtual environment
python3 -m venv venv
source venv/bin/activate
deactivate

# Check Python version
python3 --version
which python3
```

## Project Structure Navigation
```bash
# Key directories to know
backend/app/           # FastAPI application
backend/app/core/      # Core business logic
backend/app/api/routes/ # API endpoints
cli/fops/commands/     # CLI command implementations
mcp_packs/            # MCP server integrations
knowledge_base/       # Chroma DB and knowledge management
tests/                # Test files
```

## Configuration
```bash
# Environment setup
cp .env.example .env
# Edit .env file with your API keys and settings

# CLI configuration
fops init  # Interactive configuration setup
```

## API Documentation
- **Development**: http://localhost:8002/docs (FastAPI auto-docs)
- **Health Check**: http://localhost:8002/health
- **API Root**: http://localhost:8002/