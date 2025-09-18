# F-Ops: AI-Powered DevOps Automation Platform

F-Ops is an enterprise-grade DevOps AI Agent that combines intelligent automation, knowledge-driven operations, and safe deployment practices. It enables teams to achieve zero-to-deploy for new repositories in under 30 minutes with enterprise-grade safety and governance.

## 🚀 Features

### Core Capabilities
- **Zero-to-Deploy Automation**: Onboard new repositories with complete CI/CD, IaC, and monitoring setup
- **AI-Powered Incident Response**: Automatic root cause analysis and remediation suggestions
- **Knowledge-Driven Operations**: Semantic search across documentation, runbooks, and best practices
- **Safe Deployments**: Dry-run by default, policy enforcement, two-key approvals
- **Multi-Environment Support**: Manage deployments across dev, staging, and production

### Key Components
- **CLI**: Command-line interface for all operations
- **Web UI**: React-based dashboard (Phase 2)
- **Agent Core**: LangChain/LangGraph orchestration
- **MCP Packs**: Modular connectors for GitHub, Kubernetes, AWS
- **Knowledge Base**: Chroma vector database for semantic search
- **Audit System**: Immutable JSONL audit logs

## 📦 Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Kubernetes cluster (optional)
- OpenAI or Anthropic API key

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/f-ops.git
cd f-ops
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Start the backend with Docker:**
```bash
docker-compose up -d
```

4. **Install the CLI:**
```bash
cd cli
pip install -e .
```

5. **Initialize F-Ops:**
```bash
fops init
```

## 🎯 Usage

### CLI Commands

#### Onboarding
```bash
# Onboard a new repository
fops onboard repo https://github.com/user/repo --target k8s --env staging,prod

# Check onboarding status
fops onboard status https://github.com/user/repo

# List onboarded repositories
fops onboard list
```

#### Deployments
```bash
# Deploy a service
fops deploy service my-app --env staging --version v1.2.3

# Check deployment status
fops deploy status my-app --env staging

# Rollback a deployment
fops deploy rollback my-app --env staging

# View deployment history
fops deploy history my-app --limit 10
```

#### Knowledge Base
```bash
# Connect a knowledge source
fops kb connect https://github.com/user/docs --sync

# Search the knowledge base
fops kb search "kubernetes deployment best practices"

# List connected sources
fops kb list

# Sync knowledge sources
fops kb sync
```

#### Incident Management
```bash
# Create an incident
fops incident create api-gateway --severity high --title "High latency observed"

# Investigate an incident
fops incident investigate INC-2024-0142

# Get incident playbook
fops incident playbook high-latency

# Resolve an incident
fops incident resolve INC-2024-0142 --action 1
```

### API Endpoints

The FastAPI backend provides RESTful endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/onboard/repo` - Onboard repository
- `POST /api/deploy/service` - Deploy service
- `POST /api/kb/search` - Search knowledge base
- `POST /api/incident/create` - Create incident

Full API documentation available at `http://localhost:8000/docs`

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interfaces                       │
├──────────────┬──────────────┬──────────────┬────────────────┤
│     CLI      │   Web UI     │  Slack/Teams │  VS Code/MCP   │
└──────────────┴──────────────┴──────────────┴────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      Agent Core (FastAPI)                     │
├───────────────────────────────────────────────────────────────┤
│  • LangGraph/LangChain Orchestration                         │
│  • Prompt Engineering Engine                                 │
│  • Policy Enforcement (OPA)                                  │
└───────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                         MCP Packs                             │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   GitHub     │  Kubernetes  │     AWS      │  Observability │
└──────────────┴──────────────┴──────────────┴────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      Data & Storage Layer                     │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Chroma     │   SQLite     │    JSONL     │   File System  │
│  (Vectors)   │   (State)    │   (Audit)    │   (Configs)    │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## 🔧 Configuration

### Environment Variables
Key environment variables in `.env`:
- `OPENAI_API_KEY` - OpenAI API key for LLM operations
- `GITHUB_TOKEN` - GitHub personal access token
- `KUBECONFIG_PATH` - Path to Kubernetes config
- `CHROMA_PERSIST_DIR` - Directory for vector database

### MCP Pack Configuration
Each MCP pack can be configured independently:
```python
# GitHub Pack
github_config = {
    "token": "ghp_xxxxx"
}

# Kubernetes Pack
k8s_config = {
    "kubeconfig": "~/.kube/config",
    "in_cluster": False
}
```

## 🧪 Testing

Run the test suite:
```bash
# Run unit tests
pytest tests/

# Run end-to-end tests
python tests/test_e2e.py

# Run with coverage
pytest --cov=backend tests/
```

## 📊 Monitoring

F-Ops includes Prometheus and Grafana for monitoring:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)

## 🛡️ Security

- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control (RBAC)
- **Audit Logging**: Immutable JSONL audit trail
- **Policy Enforcement**: OPA integration for guardrails
- **Secret Management**: Environment variables and K8s secrets

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [CLI Reference](docs/cli-reference.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](docs/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

### Phase 1 (Current) ✅
- Core FastAPI backend
- CLI with essential commands
- Chroma knowledge base
- Basic MCP packs

### Phase 2 (Next)
- React Web UI
- Advanced deployment workflows
- Real-time monitoring
- Enhanced security features

### Phase 3 (Future)
- Slack/Teams integration
- VS Code extension
- Claude Code MCP
- Multi-tenancy support

## 💬 Support

- GitHub Issues: [Report bugs or request features](https://github.com/your-org/f-ops/issues)
- Documentation: [Read the docs](https://docs.f-ops.io)
- Community: [Join our Discord](https://discord.gg/f-ops)

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://langchain.com/)
- [Chroma](https://www.trychroma.com/)
- [Typer](https://typer.tiangolo.com/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)

---

**F-Ops**: Transform DevOps with AI-powered automation 🚀