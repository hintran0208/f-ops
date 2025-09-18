# F-Ops Code Style and Conventions

## Python Code Style

### General Style
- **PEP 8** compliance expected (standard Python style guide)
- **Type hints**: Used throughout codebase (`from typing import List, Optional`)
- **Pydantic models**: For data validation and API schemas
- **Logging**: Structured logging with `logging.getLogger(__name__)`

### Import Organization
```python
# Standard library first
import os
import sys
import logging

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Local imports last
from app.core.agent_fixed import DevOpsAgent
```

### Naming Conventions
- **Functions/Variables**: `snake_case` (e.g., `onboard_repository`, `get_agent`)
- **Classes**: `PascalCase` (e.g., `OnboardRequest`, `DevOpsAgent`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_V1_STR`)
- **Files/Modules**: `snake_case` (e.g., `main.py`, `agent_fixed.py`)

### API Patterns
- **Request Models**: Pydantic BaseModel classes for API inputs
- **Response Format**: Consistent JSON structure with success/error fields
- **Error Handling**: Try-catch blocks with proper logging and HTTP exceptions
- **Endpoint Naming**: RESTful patterns (`/api/onboard/repo`, `/api/deploy/service`)

### Directory Structure Conventions
```
backend/
├── app/
│   ├── api/routes/         # API route handlers
│   ├── core/              # Core business logic
│   ├── schemas/           # Pydantic models
│   └── utils/             # Utility functions
cli/
├── fops/
│   ├── commands/          # CLI command modules
│   └── utils/             # CLI utilities
```

### Configuration Management
- **Environment Variables**: Using `pydantic-settings` and `.env` files
- **Defaults**: Sensible defaults with environment overrides
- **Validation**: Pydantic for config validation

### Documentation
- **Docstrings**: Used for API endpoints and important functions
- **Type Hints**: Comprehensive type annotations
- **Comments**: Inline comments for complex logic

### Error Handling Patterns
```python
try:
    # Business logic
    result = some_operation()
    return result
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## CLI Conventions
- **Typer framework**: For command-line interface
- **Rich library**: For formatted terminal output
- **Global options**: Dry-run, verbose, config file support
- **Sub-commands**: Organized by domain (onboard, deploy, kb, incident)