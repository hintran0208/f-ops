# F-Ops Development Commands

## Environment Setup

### Initial Setup
```bash
# Clone and setup project
git clone <repo-url>
cd f-ops
cp .env.example .env
# Edit .env with your API keys

# Run automated setup script
./setup.sh
```

### Manual Setup (Alternative)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install CLI (TypeScript)
cd cli
npm install
npm run build
cd ..
```

## Running the Application

### Backend Server
```bash
# Option 1: Direct Python execution (recommended for development)
python run_backend.py

# Option 2: Direct uvicorn (from backend directory)
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

# Option 3: Using Docker Compose
docker-compose up -d

# Option 4: Background process with custom Python path
PYTHONPATH=/Users/hintran0208/Desktop/f-ops:$PYTHONPATH python -m uvicorn backend.app.main:app --reload --port 8002
```

### CLI Commands
```bash
# Install CLI in development mode
cd cli
npm run build

# Basic CLI commands
fops --help
fops status
fops --version

# Onboard new repository
fops onboard --repo https://github.com/user/repo --target k8s --env staging,prod

# Knowledge base operations
fops kb connect --uri https://docs.company.com/devops-guides
fops kb search "kubernetes deployment best practices"
```

## Development Workflow

### Backend Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
python run_backend.py

# Check API documentation
open http://localhost:8002/docs
```

### CLI Development
```bash
cd cli

# Development mode with auto-compilation
npm run dev

# Build for production
npm run build

# Test CLI locally
npm run start -- --help
```

## Testing

### Backend Tests
```bash
# Run E2E tests
python tests/test_e2e.py

# Manual pytest (if pytest installed)
pytest tests/
```

### API Testing
```bash
# Check health endpoint
curl http://localhost:8002/health

# Test root endpoint
curl http://localhost:8002/
```

## Database and Storage

### Chroma Database
- Location: `./chroma_db/` (local persistence)
- No manual setup required - auto-created

### SQLite Database
- Location: `./fops.db` (or configured path in .env)
- Auto-created on first run

### Audit Logs
- Location: `./audit_logs/` directory
- JSONL format for immutable logging

## System Utilities (macOS/Darwin)

### File Operations
```bash
ls          # List files
find .      # Search files (prefer mcp_serena tools over raw find)
grep        # Search in files (prefer mcp_serena tools over raw grep)
cd          # Change directory
pwd         # Print working directory
```

### Process Management
```bash
# Check running processes
ps aux | grep python
ps aux | grep node

# Kill processes
kill <pid>
killall python
killall node
```

### Git Operations
```bash
git status
git add .
git commit -m "message"
git push
git pull
```

## Docker Operations

### Development with Docker
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build
```

## Environment Management

### Python Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate
deactivate

# Check Python version
python --version

# Install new packages
pip install <package>
pip freeze > requirements.txt
```

### Node.js Environment
```bash
# Check versions
node --version
npm --version

# Install dependencies
npm install

# Update dependencies
npm update
```

## Configuration Files

### Key Configuration Files
- `.env` - Environment variables and API keys
- `backend/app/config.py` - Application settings
- `cli/package.json` - CLI dependencies and scripts
- `backend/requirements.txt` - Python dependencies
- `docker-compose.yml` - Container orchestration