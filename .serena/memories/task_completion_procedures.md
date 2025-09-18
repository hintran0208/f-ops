# F-Ops Task Completion Procedures

## When a Development Task is Complete

### 1. Code Quality Checks
Since the project doesn't appear to have explicit linting/formatting tools configured yet, follow these manual checks:

#### Python Code Validation
```bash
# Basic syntax check
python -m py_compile backend/app/main.py

# Import validation
cd backend
python -c "from app.main import app; print('✅ Imports successful')"

# Type checking (if mypy is available)
mypy backend/app/ || echo "⚠️  MyPy not configured"
```

#### API Validation
```bash
# Start the server and test basic endpoints
python run_backend.py &
sleep 3

# Test health endpoint
curl -f http://localhost:8002/health || echo "❌ Health check failed"

# Test root endpoint
curl -f http://localhost:8002/ || echo "❌ Root endpoint failed"

# Stop the server
pkill -f "uvicorn.*8002"
```

### 2. Testing Requirements

#### Manual Testing Checklist
- [ ] Backend server starts without errors
- [ ] Health check endpoint responds
- [ ] API documentation accessible at `/docs`
- [ ] CLI commands execute without import errors
- [ ] No obvious syntax errors in modified files

#### Automated Testing
```bash
# Run existing E2E tests
cd tests
python test_e2e.py

# Test CLI installation
cd cli
pip install -e .
fops --help  # Should display help without errors
```

### 3. Documentation Updates
When making significant changes:
- Update relevant comments in code
- Update API endpoint documentation if endpoints changed
- Update CLI help text if commands changed
- Consider updating CLAUDE.md or README.md for major features

### 4. Environment Verification

#### Backend Dependencies
```bash
# Verify core dependencies can be imported
cd backend
python -c "
import fastapi
import uvicorn
import pydantic
import sqlalchemy
from app.main import app
print('✅ Core dependencies verified')
"
```

#### CLI Dependencies
```bash
# Verify CLI can be imported and run
cd cli
python -c "
import typer
from fops.cli import app
print('✅ CLI dependencies verified')
"
```

### 5. Integration Verification

#### API Integration
```bash
# Start backend
python run_backend.py &
API_PID=$!

# Wait for startup
sleep 3

# Test key endpoints
echo "Testing API endpoints..."
curl -s http://localhost:8002/health | grep -q "healthy" && echo "✅ Health OK"
curl -s http://localhost:8002/ | grep -q "F-Ops" && echo "✅ Root OK"

# Cleanup
kill $API_PID
```

#### CLI-API Integration
```bash
# Test CLI can reach API (if running)
fops status  # Should show system status
```

### 6. Pre-Commit Checklist

#### Code Review
- [ ] Code follows established patterns in the codebase
- [ ] Error handling is consistent with existing patterns
- [ ] Logging is appropriate and follows existing format
- [ ] Type hints are used where appropriate
- [ ] No hardcoded secrets or sensitive information

#### Functional Review
- [ ] Changes work as intended
- [ ] No breaking changes to existing functionality
- [ ] API responses maintain expected format
- [ ] CLI commands maintain expected interface

### 7. Deployment Readiness

#### Docker Verification (if using containers)
```bash
# Test Docker build
docker-compose build backend

# Test container startup
docker-compose up -d backend
sleep 5
docker-compose logs backend  # Check for errors
docker-compose down
```

#### Environment Configuration
- [ ] `.env.example` is updated if new environment variables added
- [ ] Required API keys and tokens are documented
- [ ] Configuration validation works properly

### 8. Performance Considerations
- [ ] No obvious performance regressions
- [ ] Database queries are efficient (if database changes made)
- [ ] API response times are reasonable
- [ ] Memory usage appears normal

## Notes for Different Task Types

### Backend API Changes
- Test all modified endpoints manually
- Verify API documentation is generated correctly
- Check that error responses follow established patterns

### CLI Changes
- Test all modified commands
- Verify help text is accurate and helpful
- Check that global options work correctly

### Database/Storage Changes
- Verify migrations work (if applicable)
- Test data persistence
- Check for data corruption or loss

### Configuration Changes
- Test with different configuration values
- Verify defaults work properly
- Check environment variable precedence

## Common Issues to Check
1. **Import Path Issues**: Python path problems are common - verify imports work
2. **Port Conflicts**: Check that default ports (8002) are available
3. **Environment Variables**: Ensure required environment variables are set
4. **File Permissions**: Check that files have correct permissions
5. **Database Initialization**: Verify SQLite database and Chroma DB initialize properly