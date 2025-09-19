# F-Ops Task Completion Requirements

## Development Standards

### Code Quality Requirements
- **Type Safety**: All Python code must include proper type hints
- **Error Handling**: Implement try/catch blocks with appropriate logging
- **Documentation**: Include basic docstrings for all public methods
- **Security**: Follow proposal-only architecture - never execute commands directly
- **Logging**: Use structured logging with audit trail for agent decisions

### Testing Requirements
- **Functional Testing**: Test core API endpoints with `python tests/test_e2e.py`
- **Integration Testing**: Verify backend-CLI communication
- **API Validation**: Test health endpoints at `http://localhost:8002/health`
- **Error Cases**: Test fallback behavior when AI services are unavailable

## Pre-Completion Checklist

### Backend Changes
1. **Validate Code**: Ensure type hints and proper error handling
2. **Test API**: Run `python tests/test_e2e.py` to verify endpoints
3. **Check Health**: Verify `http://localhost:8002/health` responds correctly
4. **Audit Logging**: Confirm audit logs are written to JSONL format
5. **Configuration**: Update .env.example if new environment variables added

### CLI Changes
1. **Build Check**: Run `npm run build` in cli/ directory
2. **Command Testing**: Test CLI commands with `fops --help` and `fops status`
3. **Type Safety**: Ensure TypeScript compilation succeeds without errors
4. **Integration**: Verify CLI can communicate with backend API

### Database/Storage
1. **Migration**: Ensure SQLite schema changes are backwards compatible
2. **Chroma DB**: Verify vector database operations work correctly
3. **File Permissions**: Check that log and data directories are writable

## Quality Gates

### Code Review Standards
- **Security Review**: No direct command execution, only PR/MR generation
- **Performance**: API response times under reasonable limits
- **Error Handling**: Graceful degradation when external services fail
- **Documentation**: Clear comments explaining AI agent decision logic

### Integration Validation
- **Backend-CLI**: CLI can successfully communicate with backend
- **Agent Workflow**: Complete onboarding flow generates proper proposals
- **Knowledge Base**: KB operations (connect, search) function correctly
- **MCP Servers**: External integrations (GitHub, GitLab) work as expected

## Deployment Validation

### Local Development
1. **Environment Setup**: `.env` file configured with necessary API keys
2. **Service Health**: Backend runs successfully on port 8002
3. **CLI Functionality**: `fops` command available and responsive
4. **Database Connection**: SQLite and Chroma databases initialize correctly

### Docker Environment
1. **Container Build**: `docker-compose up -d` succeeds
2. **Service Communication**: All services can communicate internally
3. **Volume Mounts**: Persistent data volumes work correctly
4. **Port Mapping**: Services accessible on expected ports

## Performance Standards

### Response Time Requirements
- **API Endpoints**: Basic endpoints respond within 500ms
- **Agent Operations**: Repository analysis completes within 30 seconds
- **Knowledge Base**: Search queries return results within 2 seconds
- **PR Generation**: Complete onboarding workflow under 30 minutes

### Resource Usage
- **Memory**: Backend process uses reasonable memory (under 1GB for development)
- **Storage**: Database files grow reasonably with usage
- **CPU**: No excessive CPU usage during normal operations

## Security Verification

### Proposal-Only Architecture
- **No Direct Execution**: Verify no commands are executed directly
- **PR/MR Creation**: All changes result in reviewable pull/merge requests
- **Dry-Run Validation**: Infrastructure changes include dry-run artifacts
- **Audit Trail**: All operations logged with reasoning and context

### Token Security
- **Scoped Permissions**: API tokens have minimal required permissions
- **Environment Variables**: Sensitive data stored in .env files
- **Allow Lists**: Repository and namespace restrictions enforced
- **No Hardcoded Secrets**: No API keys or tokens in source code

## Final Validation Steps

### End-to-End Testing
1. **Onboarding Flow**: Complete repository onboarding with PR generation
2. **Knowledge Base**: Connect to documentation source and perform searches
3. **Agent Decisions**: Verify audit logs contain proper reasoning
4. **Error Recovery**: Test behavior when external services are unavailable

### Documentation Updates
1. **README**: Update if new features or requirements added
2. **Configuration**: Update .env.example with new variables
3. **Memory Files**: Update Serena memory files if architecture changes
4. **API Docs**: FastAPI documentation auto-generated and accessible

### Production Readiness
1. **Environment Isolation**: Development and production configs separated
2. **Scaling Considerations**: Architecture supports reasonable load
3. **Monitoring**: Health endpoints provide meaningful status information
4. **Backup Strategy**: Important data (audit logs, KB) can be backed up