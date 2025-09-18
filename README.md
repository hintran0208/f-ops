# F-Ops — Three-Agent DevOps Assistant (Python + Chroma)

F-Ops is a local-first DevOps assistant that combines **AI-powered automation** with **proposal-only safety**. Three specialized agents (**Pipeline**, **Infrastructure**, **Monitoring**) generate complete DevOps setups through **reviewable PRs** with **dry-run validation**—never executing directly.

## 🎯 Core Concept

**Proposal-Only Architecture**: F-Ops generates CI/CD pipelines, infrastructure configs, and monitoring setups as **Pull/Merge Requests** with attached dry-run artifacts. All changes are reviewable before execution.

### Three-Agent System
- **Pipeline Agent**: Generates CI/CD workflows (GitHub Actions/GitLab CI) with security scans and SLO gates
- **Infrastructure Agent**: Creates Terraform modules and Helm charts with `terraform plan` and `helm --dry-run` validation
- **Monitoring Agent**: Produces Prometheus rules and Grafana dashboards for observability

### MCP Server Integration
Custom **MCP (Model Context Protocol) server packs** provide typed interfaces to:
- **SCM & CI**: GitHub/GitLab for PR creation, Jenkins for pipeline management
- **Infra & Cluster**: Terraform for IaC planning, Kubernetes/Helm for deployment validation
- **Observability**: Prometheus rule generation, Grafana dashboard provisioning
- **Knowledge**: Chroma vector database for RAG-powered template retrieval

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- OpenAI or Anthropic API key
- GitHub/GitLab token for PR creation

### Installation

1. **Clone and setup:**
```bash
git clone https://github.com/your-org/f-ops.git
cd f-ops
cp .env.example .env
# Edit .env with your API keys
```

2. **Start with Docker:**
```bash
docker-compose up -d
```

3. **Install CLI:**
```bash
cd cli
pip install -e .
fops --help
```

## 🎯 Usage

### CLI Commands (Proposal-Only)

#### Onboard New Repository
```bash
# Generate complete DevOps setup as PRs
fops onboard --repo https://github.com/user/repo \
             --target k8s \
             --env staging,prod

# Output: 3 PRs opened with CI/CD + IaC + Monitoring + dry-run artifacts
```

#### Knowledge Base Operations
```bash
# Ingest documentation for RAG templates
fops kb connect --uri https://docs.company.com/devops-guides

# Search for relevant patterns
fops kb search "kubernetes deployment best practices"
```

### Web UI Modules

Access at `http://localhost:3000` (after Week 2):

- **Pipeline Agent Module**: Form-driven CI/CD generation with preview
- **Infrastructure Agent Module**: IaC template generation with plan validation
- **Monitoring Agent Module**: Observability config generation
- **KB Connect Module**: Documentation ingestion and search

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Interfaces                               │
├──────────────┬──────────────┬──────────────┬────────────────┤
│     CLI      │   Web UI     │    API       │   MCP Servers  │
│  (Typer)     │  (React)     │  (FastAPI)   │   (Local)      │
└──────────────┴──────────────┴──────────────┴────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                  Three-Agent Core                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Pipeline   │Infrastructure│  Monitoring  │   Knowledge    │
│    Agent     │    Agent     │    Agent     │      Base      │
│ (LangGraph)  │ (LangGraph)  │ (LangGraph)  │   (Chroma)     │
└──────────────┴──────────────┴──────────────┴────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server Packs                       │
├──────────────┬──────────────┬──────────────┬────────────────┤
│     SCM      │     Infra    │      Obs     │       KB       │
│  GitHub/GL   │   TF/K8s/Helm│   Prom/Graf  │    Search      │
└──────────────┴──────────────┴──────────────┴────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                   Storage & State                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│    Chroma    │    SQLite    │     JSONL    │   File System  │
│  (Vectors)   │   (State)    │   (Audit)    │   (Configs)    │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## 📅 Development Timeline (4 Weeks)

### Week 1: Core Agents & CLI ⚡
- **Pipeline Agent**: GitHub Actions/GitLab CI generation with security scans
- **Knowledge Base**: Chroma setup with embedding pipeline for documentation
- **CLI Foundation**: `fops onboard` and `fops kb` commands
- **MCP Integration**: Basic GitHub/GitLab MCP servers for PR creation

### Week 2: Infrastructure Agent & Web UI 🏗️
- **Infrastructure Agent**: Terraform plan and Helm dry-run generation
- **Web UI Foundation**: React frontend with Pipeline and Infrastructure modules
- **PR Orchestration**: Automated PR creation with plan artifacts attached
- **Validation Pipeline**: Syntax validation and dry-run execution

### Week 3: Monitoring Agent & Advanced KB 📊
- **Monitoring Agent**: Prometheus rules and Grafana dashboard generation
- **Advanced RAG**: Enhanced knowledge retrieval with relevance scoring
- **KB Connect Module**: Web UI for documentation ingestion
- **Observability MCP**: Prometheus/Grafana validation servers

### Week 4: Enterprise Readiness 🛡️
- **OPA Guardrails**: Policy enforcement and security compliance
- **Multi-Tenant**: Isolated Chroma collections per organization
- **Evaluation Harness**: Quality metrics and success rate monitoring
- **Performance**: <30min onboarding target optimization

## 🎯 Success Metrics

- **Onboarding Speed**: New repo → Complete PR set in **≤30 minutes**
- **Review Quality**: **100%** of outputs delivered as reviewable PRs with dry-run artifacts
- **Knowledge Utility**: **≥80%** of generated configs include KB citations
- **Adoption Rate**: **≥50%** usage via Web UI after Week 3
- **Safety**: **Zero** direct execution—all changes through PR review

## 🛡️ Safety & Security

### Proposal-Only Design
- **No Direct Execution**: All operations generate PR/MR proposals only
- **Dry-Run Validation**: Every generated config includes validation artifacts
- **Review Gates**: Human approval required before any infrastructure changes
- **Audit Trail**: Immutable JSONL logs for all operations

### Enterprise Features
- **OPA Policies**: Configurable guardrails for compliance requirements
- **Token Scoping**: Minimal required permissions per MCP server
- **Multi-Tenant**: Isolated knowledge bases per organization
- **RBAC Integration**: Role-based access control for sensitive operations

## 📦 Core Technologies

- **Backend**: FastAPI with LangGraph agent orchestration
- **Frontend**: React with Tailwind CSS and TypeScript
- **Vector DB**: Chroma for semantic search and RAG
- **State**: SQLite for minimal metadata, JSONL for audit
- **MCP**: Custom Model Context Protocol servers for tool integration
- **Validation**: OPA for policy enforcement, native tools for syntax checking

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas:
- **MCP Server Development**: Add new tool integrations
- **Agent Enhancement**: Improve generation quality and citation accuracy
- **Template Library**: Contribute high-quality DevOps templates
- **Policy Packs**: Create OPA policies for different compliance frameworks

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) for the agent core
- [LangGraph](https://langchain.com/langgraph) for agent orchestration
- [Chroma](https://www.trychroma.com/) for vector storage and RAG
- [React](https://react.dev/) for the Web UI
- [Typer](https://typer.tiangolo.com/) for CLI development

---

**F-Ops**: Safe, fast, reviewable DevOps automation through AI-powered proposal generation 🚀