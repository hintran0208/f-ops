# F-Ops Development Guidelines

## Architecture Principles

### Proposal-Only Design
- **Core Principle**: F-Ops never executes infrastructure changes directly
- **All Operations**: Generate Pull/Merge Requests with dry-run artifacts
- **Safety First**: Human review required before any infrastructure changes
- **Audit Trail**: Immutable JSONL logs for all operations and decisions

### Three-Agent Architecture
- **Separation of Concerns**: Each agent handles specific domain (Pipeline, Infrastructure, Monitoring)
- **Knowledge Integration**: All agents use Chroma KB for template retrieval and citations
- **AI-Powered**: LangGraph orchestration with OpenAI/Anthropic integration
- **MCP Integration**: Typed interfaces to external tools through MCP servers

## Design Patterns

### Agent Pattern
```python
class SomeAgent:
    def __init__(self, kb, citation_engine, audit_logger, ai_service):
        # Dependency injection pattern
        self.kb = kb
        self.citation_engine = citation_engine
        self.audit_logger = audit_logger
        self.ai_service = ai_service
    
    def perform_operation(self, params) -> Dict[str, Any]:
        # Always log decisions with reasoning
        self.audit_logger.log_agent_decision("agent_name", {
            "action": "operation_name",
            "params": params,
            "reasoning": "Why this decision was made"
        })
```

### Configuration Pattern
```python
# Use Pydantic BaseSettings for all configuration
class Settings(BaseSettings):
    # Type all fields with defaults
    PROJECT_NAME: str = "F-Ops"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }
```

### Error Handling Pattern
```python
try:
    # Attempt AI-powered operation
    result = self.ai_service.analyze(data)
except Exception as e:
    logger.error(f"AI operation failed: {e}")
    # Always provide fallback strategy
    result = self._fallback_analysis(data)
    # Log the fallback decision
    self.audit_logger.log_agent_decision("agent", {
        "action": "fallback_used",
        "error": str(e),
        "reasoning": "AI service unavailable, using heuristics"
    })
```

## Code Organization Guidelines

### Backend Structure
- **Agents**: Pure business logic, no direct API dependencies
- **API Routes**: Thin controllers that orchestrate agents
- **Core Services**: Reusable services (AI, KB, audit, citation)
- **MCP Servers**: External tool integrations with typed interfaces
- **Schemas**: Pydantic models for request/response validation

### CLI Structure
- **Commands**: Single-purpose command files using Commander.js
- **Services**: API client abstraction for backend communication
- **Utils**: Reusable utilities for file operations, Git, project scanning

### Dependency Flow
```
CLI Commands → API Routes → Agents → Core Services → MCP Servers → External Tools
```

## Security Guidelines

### Token Management
- **Principle of Least Privilege**: Minimal required permissions per integration
- **Environment Variables**: Store all secrets in .env files
- **Allow Lists**: Configure allowed repositories and namespaces
- **No Hardcoded Secrets**: Never commit API keys or tokens

### Audit and Compliance
- **Immutable Logs**: All decisions logged in JSONL format
- **Decision Reasoning**: Every agent decision includes explanation
- **Error Context**: Failures logged with full context for debugging
- **Access Control**: Repository and namespace restrictions enforced

## Performance Guidelines

### Response Time Targets
- **Basic API**: <500ms for health/status endpoints
- **Agent Operations**: <30 seconds for repository analysis
- **KB Search**: <2 seconds for knowledge base queries
- **Complete Onboarding**: <30 minutes for full workflow

### Resource Management
- **Local Storage**: SQLite for metadata, Chroma for vectors
- **Memory Usage**: Reasonable limits for development environment
- **Async Operations**: Use async/await for I/O bound operations
- **Caching**: Cache knowledge base results and AI responses when appropriate

## Testing Guidelines

### Test Categories
- **Unit Tests**: Test individual agent methods and core services
- **Integration Tests**: Test API endpoints and CLI-backend communication
- **E2E Tests**: Complete workflows from CLI to PR generation
- **Error Tests**: Test fallback behavior and error recovery

### Test Data
- **Mock AI Responses**: Use mock data for AI services in tests
- **Sample Repositories**: Test with representative repository structures
- **Error Scenarios**: Test network failures, API unavailability, invalid inputs

## Documentation Standards

### Code Documentation
- **Docstrings**: Basic descriptions for all public methods
- **Type Hints**: Complete type annotations for all function signatures
- **Comments**: Explain complex business logic and AI decision reasoning
- **API Docs**: Auto-generated FastAPI documentation at /docs

### Architecture Documentation
- **Memory Files**: Maintain Serena memory files for project knowledge
- **README**: Keep main README current with setup and usage
- **Configuration**: Document all environment variables in .env.example

## Development Workflow

### Local Development
1. **Environment Setup**: Use `setup.sh` for automated setup
2. **Backend Development**: Run `python run_backend.py` for auto-reload
3. **CLI Development**: Use `npm run dev` in cli directory
4. **Testing**: Run `python tests/test_e2e.py` before commits

### Quality Checks
- **Type Safety**: Ensure TypeScript and Python type checking passes
- **API Health**: Verify health endpoints respond correctly
- **CLI Functionality**: Test basic CLI commands work
- **Integration**: Verify CLI-backend communication

### Git Workflow
- **Feature Branches**: Use descriptive branch names
- **Commit Messages**: Clear, concise commit descriptions
- **PR Reviews**: Include dry-run artifacts and test results
- **Documentation**: Update relevant docs with changes

## Framework-Specific Guidelines

### FastAPI Best Practices
- **Router Organization**: Group related endpoints in separate router files
- **Dependency Injection**: Use FastAPI dependencies for service injection
- **Error Handling**: Use HTTPException for API errors
- **CORS Configuration**: Configure for local development needs

### LangGraph Integration
- **Agent State**: Maintain clear state through agent workflows
- **Error Recovery**: Handle AI service failures gracefully
- **Reasoning Chains**: Log intermediate steps in complex workflows
- **Citation Tracking**: Maintain source attribution through workflows

### Chroma Vector DB
- **Collection Organization**: Separate collections by data type
- **Metadata**: Include rich metadata for filtering and retrieval
- **Chunking Strategy**: Optimal chunk sizes for different content types
- **Embedding Models**: Consistent embedding model across collections