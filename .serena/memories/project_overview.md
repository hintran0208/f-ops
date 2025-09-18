# F-Ops Project Overview

## Purpose
F-Ops is an AI-powered DevOps automation platform that combines intelligent automation, knowledge-driven operations, and safe deployment practices. It enables teams to achieve zero-to-deploy for new repositories in under 30 minutes with enterprise-grade safety and governance.

## Tech Stack
- **Language**: Python 3.11+ (currently using Python 3.13.5 via pyenv)
- **Backend Framework**: FastAPI with Uvicorn ASGI server
- **CLI Framework**: Typer with Rich for CLI interface
- **AI/ML**: 
  - LangChain/LangGraph for orchestration
  - OpenAI/Anthropic APIs for LLM operations
  - Chroma vector database for semantic search
- **Database**: 
  - SQLite for state management
  - JSONL for audit logs
  - Chroma for knowledge base embeddings
- **Infrastructure**:
  - Docker/Docker Compose for containerization
  - Kubernetes Python client for K8s operations
  - PyGithub for GitHub integration
  - Boto3 for AWS operations
- **Monitoring**: Prometheus and Grafana

## Project Structure
```
f-ops/
├── backend/          # FastAPI backend server
│   ├── app/         # Application code
│   │   ├── api/     # API routes
│   │   ├── core/    # Core functionality (agent, KB, audit)
│   │   ├── models/  # Database models
│   │   └── schemas/ # Pydantic schemas
│   ├── audit_logs/  # Audit log storage
│   └── chroma_db/   # Vector database storage
├── cli/             # CLI application
│   └── fops/        # CLI package
│       ├── commands/# Sub-commands
│       └── utils/   # Utilities
├── mcp_packs/       # Model Context Protocol packs
├── knowledge_base/  # KB documents and sources
└── tests/           # Test files

## Architecture
- **Agent Core** (FastAPI): Handles planning, policy checks, approvals, and orchestration
- **MCP Packs**: Modular connectors for GitHub, Kubernetes, AWS, and observability tools
- **Knowledge Layer**: Chroma for semantic search with collections per project/tenant
- **State Management**: SQLite for approvals/runs, JSONL for immutable audit trail

## Development Phases
Currently in Phase 1: Core infrastructure with CLI and basic MCP packs
Next: Phase 2 with React Web UI and advanced deployment workflows