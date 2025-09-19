# F-Ops Codebase Structure

## Top-Level Organization

```
f-ops/
├── backend/                 # Python FastAPI backend
├── cli/                    # TypeScript CLI interface
├── tests/                  # End-to-end tests
├── mcp_packs/             # MCP server pack manager
├── knowledge_base/        # KB storage and configs
├── .github/               # GitHub workflows and configs
├── docker-compose.yml     # Container orchestration
├── setup.sh              # Automated setup script
├── run_backend.py         # Backend runner script
├── .env.example          # Environment template
└── README.md             # Project documentation
```

## Backend Structure (Python)

```
backend/
├── app/
│   ├── agents/            # AI agent implementations
│   │   ├── __init__.py
│   │   └── pipeline_agent.py    # Pipeline generation agent
│   ├── api/               # FastAPI routes
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py      # Pipeline API endpoints
│   │   │   └── kb.py           # Knowledge base endpoints
│   │   └── __init__.py
│   ├── core/              # Core services
│   │   ├── ai_service.py        # AI/LLM integration
│   │   ├── audit.py            # Audit logging
│   │   ├── audit_logger.py     # Audit logger implementation
│   │   ├── citation_engine.py  # Citation and reference engine
│   │   ├── database.py         # Database setup
│   │   ├── kb_manager.py       # Knowledge base management
│   │   ├── knowledge_base.py   # KB operations
│   │   └── pr_orchestrator.py  # PR/MR creation
│   ├── mcp_servers/       # MCP server implementations
│   │   ├── __init__.py
│   │   ├── mcp_github.py       # GitHub MCP server
│   │   ├── mcp_gitlab.py       # GitLab MCP server
│   │   └── mcp_kb.py          # Knowledge base MCP server
│   ├── schemas/           # Pydantic data models
│   │   ├── __init__.py
│   │   └── pipeline.py         # Pipeline-related schemas
│   ├── config.py          # Application configuration
│   ├── main.py           # FastAPI application
│   └── __init__.py
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
└── setup_path.py        # Python path setup
```

## CLI Structure (TypeScript)

```
cli/
├── src/
│   ├── commands/          # CLI command implementations
│   │   ├── onboard.ts          # Repository onboarding
│   │   └── kb.ts              # Knowledge base commands
│   ├── services/          # External service clients
│   │   └── apiClient.ts        # Backend API client
│   ├── utils/             # Utility functions
│   │   ├── fileOperations.ts   # File system operations
│   │   ├── gitUtils.ts         # Git operations
│   │   ├── projectScanner.ts   # Project analysis
│   │   └── workflowGenerator.ts # Workflow generation
│   └── index.ts           # CLI entry point
├── package.json           # Node.js dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── dist/                 # Compiled JavaScript (generated)
```

## Core Components by Function

### Agent System
- **Pipeline Agent** (`backend/app/agents/pipeline_agent.py`)
  - Repository analysis and stack detection
  - CI/CD workflow generation (GitHub Actions, GitLab CI)
  - Security and SLO gate integration
  - YAML validation and syntax checking

### Knowledge Base
- **KB Manager** (`backend/app/core/kb_manager.py`)
  - Document ingestion and chunking
  - Vector embedding and storage
  - Semantic search and retrieval
  - Citation tracking and references

### MCP Integration
- **MCP Servers** (`backend/app/mcp_servers/`)
  - GitHub API integration for PR creation
  - GitLab API integration for MR creation
  - Knowledge base search and retrieval
  - Typed interfaces for external tools

### API Layer
- **Routes** (`backend/app/api/routes/`)
  - RESTful endpoints for agents
  - Knowledge base operations
  - Health and status monitoring
  - CORS configuration for local development

## Data Flow Architecture

### Onboarding Flow
1. **CLI** (`cli/src/commands/onboard.ts`) → **API** (`backend/app/api/routes/pipeline.py`)
2. **Pipeline Agent** (`backend/app/agents/pipeline_agent.py`) → **AI Service** (`backend/app/core/ai_service.py`)
3. **Knowledge Base** (`backend/app/core/knowledge_base.py`) → **Citation Engine** (`backend/app/core/citation_engine.py`)
4. **PR Orchestrator** (`backend/app/core/pr_orchestrator.py`) → **MCP Servers** (`backend/app/mcp_servers/`)

### Knowledge Base Flow
1. **CLI** (`cli/src/commands/kb.ts`) → **API** (`backend/app/api/routes/kb.py`)
2. **KB Manager** (`backend/app/core/kb_manager.py`) → **Chroma Vector DB**
3. **Document Processing** → **Embedding Generation** → **Storage**

## Storage and Persistence

### File System Layout
```
f-ops/
├── chroma_db/             # Chroma vector database (auto-created)
├── audit_logs/            # JSONL audit trail (auto-created)
├── data/                  # SQLite database location
└── venv/                  # Python virtual environment
```

### Database Schema
- **SQLite**: Minimal metadata (agent runs, status, timestamps)
- **Chroma**: Vector embeddings (documents, code examples, templates)
- **JSONL**: Immutable audit logs (decisions, errors, reasoning)

## External Dependencies

### Required External Tools
- **Git**: Repository operations and cloning
- **Docker**: Container runtime (optional)
- **Node.js**: CLI runtime and TypeScript compilation
- **Python 3.11+**: Backend runtime and package management

### Optional External Integrations
- **Terraform**: Infrastructure planning (external binary)
- **Helm**: Kubernetes deployment validation (external binary)
- **kubectl**: Kubernetes cluster operations (external binary)
- **Prometheus/Grafana**: Monitoring stack (external services)