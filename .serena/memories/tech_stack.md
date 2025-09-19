# F-Ops Technology Stack

## Backend (Python)
- **Framework**: FastAPI 0.115.5 with Uvicorn
- **Agent Framework**: LangGraph with LangChain for AI orchestration
- **AI/ML**: OpenAI (GPT-4) and Anthropic APIs
- **Vector Database**: Chroma 0.5.0 for semantic search and RAG
- **State Storage**: SQLite for minimal metadata
- **Audit**: JSONL logs for immutable audit trail
- **Data Models**: Pydantic 2.10.4 for validation and settings
- **HTTP Client**: httpx for external API calls

## CLI (TypeScript/Node.js)
- **Framework**: Commander.js for CLI structure
- **Runtime**: Node.js ≥16.0.0, TypeScript 5.1.6
- **UI Components**: Ink for React-based CLI interfaces
- **User Interaction**: Inquirer for prompts, Ora for spinners
- **Build System**: TypeScript compiler with ES2020 target

## Infrastructure & Integration
- **Container**: Docker with docker-compose for local development
- **SCM Integration**: PyGithub and python-gitlab for PR/MR creation
- **Cloud**: boto3 for AWS, kubernetes client for K8s
- **Monitoring**: prometheus-client, OpenTelemetry
- **Security**: python-jose for JWT, passlib for password hashing

## Development Tools
- **Package Managers**: pip (Python), npm (Node.js)
- **Testing**: pytest for Python, no formal test framework for TypeScript CLI
- **Environment**: python-dotenv for configuration
- **File Operations**: aiofiles for async I/O, fs-extra for Node.js

## Database & Storage
- **Primary DB**: SQLite (no PostgreSQL dependency)
- **Vector Store**: Chroma with local persistence
- **File Storage**: Local file system for configs and artifacts
- **Audit Logs**: JSONL format for immutable logging

## External Integrations
- **AI Services**: OpenAI API, Anthropic Claude API
- **Version Control**: GitHub API, GitLab API
- **Infrastructure Tools**: Terraform (external), Helm (external), Kubernetes API
- **Monitoring**: Prometheus, Grafana (external services)