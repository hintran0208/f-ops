# F-Ops Code Style and Conventions

## Python Code Style

### General Conventions
- **Type Hints**: Full type annotations using modern Python typing
  - Function parameters and return types always annotated
  - Use `Optional[T]` for nullable types, `Dict[str, Any]` for flexible dicts
  - Import types from `typing` module
- **Naming**: snake_case for variables, functions, and modules
- **Classes**: PascalCase for class names (e.g., `PipelineAgent`, `Settings`)
- **Private Methods**: Use single underscore prefix (e.g., `_generate_github_actions`)

### Docstrings
- Use simple docstrings with basic descriptions
- Example: `"""Detect stack and frameworks from repository using AI"""`
- No complex docstring formats like Sphinx or Google style observed

### Configuration
- **Settings**: Use Pydantic BaseSettings for configuration
- **Environment**: pydantic-settings with .env file support
- **Type Safety**: All config fields properly typed with defaults
- **Case Sensitivity**: `case_sensitive: True` in model config

### Error Handling
- Use try/except blocks with specific logging
- Fallback strategies when AI services fail
- Log errors with context before returning fallback values

### Logging
- Use standard Python logging with descriptive messages
- Include structured data in audit logs
- Log agent decisions with reasoning and context

### Code Organization
- **Agents**: Separate classes for each agent type
- **Dependencies**: Inject services (kb, citation_engine, audit_logger, ai_service) via constructor
- **Methods**: Public methods for main operations, private methods with underscore prefix

## TypeScript Code Style

### General Conventions
- **Strict Mode**: TypeScript strict mode enabled
- **Target**: ES2020 with CommonJS modules
- **Imports**: ES6 import syntax
- **Exports**: Named exports preferred
- **Error Handling**: Try/catch with proper error typing

### File Organization
- **Entry Point**: Single index.ts file
- **Commands**: Separate files in commands/ directory
- **Services**: Separate files in services/ directory
- **Utils**: Utility functions in utils/ directory

### CLI Structure
- **Framework**: Commander.js for command structure
- **Commands**: Modular command files (onboard.ts, kb.ts)
- **User Interaction**: Chalk for colors, Inquirer for prompts

## Project Structure Conventions

### Directory Layout
```
backend/
  app/
    agents/          # AI agent implementations
    api/routes/      # FastAPI route handlers
    core/           # Core services (KB, audit, AI)
    mcp_servers/    # MCP server implementations
    schemas/        # Pydantic models
cli/
  src/
    commands/       # CLI command implementations
    services/       # API client and services
    utils/          # Utility functions
tests/              # Test files
mcp_packs/          # MCP server pack manager
```

### Import Patterns
- **Relative Imports**: Use relative imports within app modules
- **Absolute Imports**: Set up proper Python path for cross-module imports
- **Type Imports**: Import types explicitly when needed

### Configuration Files
- **Environment**: .env files for local configuration
- **Docker**: docker-compose.yml for local development
- **TypeScript**: tsconfig.json with strict settings
- **Python**: No pyproject.toml, using requirements.txt

## Security Conventions
- **Proposal-Only**: Never execute commands directly, only generate PRs
- **Token Scoping**: Minimal required permissions per MCP server
- **Allow Lists**: Configured allowed repos and namespaces
- **Audit Trail**: Immutable JSONL logs for all operations