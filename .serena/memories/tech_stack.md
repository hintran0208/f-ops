# F-Ops Tech Stack

## Core Technologies

### Backend (Python)
- **FastAPI** (0.115.5) - API framework
- **Uvicorn** (0.32.1) - ASGI server
- **Pydantic** (2.10.4) - Data validation and settings
- **SQLAlchemy** (2.0.36) - Database ORM
- **SQLite** - Minimal state storage

### AI/ML Stack
- **LangChain** (0.2.16) - LLM framework
- **LangGraph** (0.2.0) - Agent orchestration
- **OpenAI** (1.58.1) - LLM API client
- **Anthropic** (0.40.0) - Claude API client
- **ChromaDB** (0.5.0) - Vector database for RAG

### CLI
- **Typer** - CLI framework (from setup.py)
- **Rich** - Terminal formatting and display

### DevOps Integrations
- **PyGithub** (2.1.1) - GitHub API
- **Kubernetes** (28.1.0) - K8s client
- **Boto3** (1.29.0) - AWS SDK
- **python-jose** (3.3.0) - JWT handling

### Monitoring
- **Prometheus Client** (0.19.0) - Metrics
- **OpenTelemetry** (1.21.0) - Observability

### Development Tools
- **Docker & Docker Compose** - Containerization
- **HTTPX** (0.25.0) - HTTP client
- **python-dotenv** (1.0.0) - Environment management
- **aiofiles** (23.2.1) - Async file operations

## Architecture Components

### Storage
- **Chroma**: Vector embeddings for knowledge base
- **SQLite**: Minimal state (approvals index, run metadata)
- **JSONL**: Immutable audit logs
- **File System**: Generated configs and templates

### External Integrations
- **GitHub/GitLab**: PR/MR creation and management
- **Terraform**: Infrastructure planning
- **Helm**: Kubernetes deployment validation
- **Prometheus/Grafana**: Monitoring validation

### Python Version
- **Python 3.11+** (as specified in README)
- Uses pyenv for version management