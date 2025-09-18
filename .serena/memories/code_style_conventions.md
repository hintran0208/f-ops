# Code Style and Conventions

## Python Code Style
- **Python Version**: 3.11+ (project uses pyenv with version "dev01")
- **Type Hints**: Using Pydantic for data validation and type hints
- **Async/Await**: FastAPI routes use async functions
- **Import Style**: Absolute imports from package root (e.g., `from backend.app.config import settings`)

## Naming Conventions
- **Files**: lowercase with underscores (e.g., `knowledge_base.py`)
- **Classes**: PascalCase (e.g., `OnboardRequest`, `AuditLogger`)
- **Functions/Methods**: snake_case (e.g., `onboard_repository`, `get_onboarding_status`)
- **Constants**: UPPERCASE with underscores (e.g., `API_V1_STR`, `OPENAI_API_KEY`)
- **Routers**: Lowercase module names with descriptive tags

## Project Patterns
- **FastAPI Routers**: Separate router files per domain in `backend/app/api/routes/`
- **Dependency Injection**: Using FastAPI's dependency system
- **Configuration**: Pydantic Settings with `.env` file support
- **Error Handling**: Using logging module with structured logging
- **API Versioning**: API paths prefixed with version (e.g., `/api/v1`)

## Documentation
- **Docstrings**: Use triple quotes for function/class documentation
- **API Documentation**: FastAPI auto-generates OpenAPI docs at `/docs`
- **Comments**: Minimal inline comments, prefer self-documenting code

## File Organization
- **One class/concept per file** where practical
- **Related functionality grouped** in modules
- **Clear separation** between API routes, business logic, and data models
- **Configuration** centralized in `config.py`

## Testing Conventions
- Test files in `tests/` directory
- Test file naming: `test_*.py`
- E2E tests separate from unit tests