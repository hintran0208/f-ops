# F-Ops — Master Implementation Plan

## Overview
F-Ops is a local-first DevOps assistant that generates **proposal-only** CI/CD pipelines, infrastructure configs, and monitoring setups through intelligent agents. All operations result in reviewable PR/MRs with dry-run artifacts - no direct execution.

## Vision
Enable teams to achieve zero-to-deploy readiness for new repositories in **≤ 30 minutes** through AI-powered generation of CI/CD, IaC, and observability configs - all delivered as reviewable pull requests with validation artifacts.

## Core Architecture

### Three-Agent System
1. **Pipeline Agent**: CI/CD pipeline generation with security scans and SLO gates
2. **Infrastructure Agent**: Terraform modules and Helm charts with plan/dry-run outputs
3. **Monitoring Agent**: Prometheus rules and Grafana dashboards for observability

### Interfaces
- **CLI**: Onboarding and knowledge management commands
- **Web UI**: Four modules for agent interactions and KB management
- **MCP Server Packs**: Tool integration layer (GitHub/GitLab/Jenkins/K8s/Terraform/Helm/Observability/KB)

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
├─────────────────────────┬────────────────────────────────────┤
│         CLI             │            Web UI                  │
│   (Typer/Click)         │      (React + FastAPI)            │
│                         │                                    │
│  • fops onboard         │  Modules:                         │
│  • fops kb connect      │  • Pipeline Agent                 │
│  • fops kb search       │  • Infrastructure Agent           │
│                         │  • Monitoring Agent               │
│                         │  • KB Connect                     │
└─────────────────────────┴────────────────────────────────────┘
                               │
┌──────────────────────────────────────────────────────────────┐
│                   Agent Core (FastAPI)                       │
├──────────────────────────────────────────────────────────────┤
│  • Planning Engine (LangGraph/LangChain)                     │
│  • RAG Pipeline (Chroma integration)                         │
│  • Policy Enforcement (OPA guardrails)                       │
│  • PR/MR Orchestration                                       │
│  • Dry-run Execution & Validation                           │
│  • Citation Generation                                       │
└──────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────────────────────────────────────┐
│                      MCP Server Packs                        │
├────────────────┬────────────────┬────────────────────────────┤
│   SCM & CI     │   Infra & K8s   │   Observability & KB      │
├────────────────┼────────────────┼────────────────────────────┤
│ • mcp-github   │ • mcp-terraform │ • mcp-observability       │
│ • mcp-gitlab   │ • mcp-kubernetes│ • mcp-kb                  │
│ • mcp-jenkins  │ • mcp-helm      │   - connect               │
│                │                 │   - sync                  │
│                │                 │   - search                │
│                │                 │   - compose               │
└────────────────┴────────────────┴────────────────────────────┘
                               │
┌──────────────────────────────────────────────────────────────┐
│                    Data & Storage Layer                      │
├────────────────┬────────────────┬────────────────────────────┤
│    Chroma      │     SQLite      │         JSONL             │
│  (Embeddings)  │ (Minimal State) │   (Immutable Audit)       │
│                │                 │                           │
│ Collections:   │ • Approvals     │ • All operations         │
│ • kb.pipelines │ • Run metadata  │ • Agent decisions        │
│ • kb.iac       │ • Session state │ • Citations              │
│ • kb.docs      │                 │ • Dry-run results        │
│ • kb.slo       │                 │                           │
│ • kb.incidents │                 │                           │
└────────────────┴────────────────┴────────────────────────────┘
```

## 4-Week Delivery Timeline

### Week 1: Core Foundation & Pipeline Agent
**Goal**: FastAPI core, Chroma integration, Pipeline Agent MVP

**Deliverables**:
- FastAPI application structure with agent orchestration
- Chroma client and KB collections setup
- `mcp-kb` implementation (connect/search functionality)
- **Pipeline Agent**: GitHub/GitLab CI/CD generation
- CLI commands: `fops onboard` (basic), `fops kb connect/search`
- JSONL audit logging system
- SQLite for minimal state management

**Success Criteria**:
- Generate valid GitHub Actions/GitLab CI pipelines
- KB search returns relevant snippets with citations
- Audit trail captures all operations

### Week 2: Infrastructure Agent & Web UI
**Goal**: IaC generation with validation, Web UI for Pipeline+Infrastructure

**Deliverables**:
- **Infrastructure Agent**: Terraform modules + Helm charts
- `terraform plan` integration for validation
- `helm --dry-run` execution and output capture
- Web UI: Pipeline Agent module (preview & PR generation)
- Web UI: Infrastructure Agent module (preview with plan outputs)
- PR/MR creation with attached dry-run artifacts
- `mcp-terraform` and `mcp-helm` implementations

**Success Criteria**:
- Valid Terraform plans generated and attached to PRs
- Helm charts pass dry-run validation
- Web UI generates PRs with complete artifacts

### Week 3: Monitoring Agent & KB Connect
**Goal**: Complete observability configs, full KB management

**Deliverables**:
- **Monitoring Agent**: Prometheus rules + Grafana provisioning
- Web UI: Monitoring Agent module
- Web UI: KB Connect module (crawl, embed, search)
- `mcp-observability` implementation
- KB connectors for GitHub/Confluence/Notion
- Citation system for all generated configs
- Advanced RAG pipeline with relevance scoring

**Success Criteria**:
- Valid Prometheus/Grafana configs with syntax validation
- ≥80% of generated files include KB citations
- KB Connect successfully ingests external documentation

### Week 4: Guardrails & Enterprise Readiness
**Goal**: Security, multi-tenancy, evaluation, documentation

**Deliverables**:
- OPA policy guardrails implementation
- Multi-tenant Chroma collections with isolation
- Scoped MCP tokens and credential rotation
- Evaluation harness:
  - Retrieval hit-rate metrics
  - Plan quality scoring
  - Syntax validation suite
- Complete documentation and demo materials
- Performance optimization (target: <30min onboarding)

**Success Criteria**:
- All operations pass OPA policy checks
- 100% of changes delivered as reviewable PR/MRs
- Complete zero-to-deploy in ≤30 minutes
- ≥50% adoption via Web UI after launch

## Tech Stack

### Core
- **Language**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **AI/ML**: LangGraph, LangChain
- **Vector DB**: Chroma (no Postgres)
- **State**: SQLite (minimal)
- **Audit**: JSONL (immutable)
- **Policy**: OPA

### Frontend
- **Framework**: React 18+
- **Styling**: Tailwind CSS
- **State**: Redux Toolkit or Zustand
- **Build**: Vite

### MCP Integration
- Custom MCP server implementations
- Typed interfaces for all tools
- No raw shell execution - only typed MCP calls

## Key Design Principles

### 1. Proposal-Only Operations
- All outputs are PR/MRs for review
- No direct apply/execute/deploy
- Dry-run validations attached as artifacts
- Human approval required for all changes

### 2. Knowledge-Driven Generation
- RAG pipeline queries Chroma for patterns
- All generated configs cite KB sources
- Continuous KB updates via connectors
- Semantic search for relevant examples

### 3. Safety & Compliance
- OPA policy enforcement on all operations
- Allow-listed repos and namespaces
- Scoped credentials per MCP server
- Immutable audit trail in JSONL

### 4. Local-First Architecture
- No external service dependencies for core ops
- MCP servers run locally
- Chroma runs locally
- SQLite for state (no Postgres)

## Agent Specifications

### Pipeline Agent
**Inputs**: repo URL, stack, target, environments
**Process**:
1. Stack detection (language, frameworks)
2. KB retrieval of similar pipelines
3. Pipeline composition with security/SLO gates
4. Citation generation from KB sources
5. PR/MR creation with validated YAML

**Outputs**: `.github/workflows/*.yml` or `.gitlab-ci.yml`

### Infrastructure Agent
**Inputs**: target (k8s/serverless/static), environments, domain
**Process**:
1. Terraform module selection
2. Helm chart skeleton (if k8s)
3. Configuration generation
4. `terraform plan` execution
5. `helm --dry-run` validation
6. PR/MR with plan artifacts

**Outputs**: `infra/*` and `deploy/chart/*` with validation results

### Monitoring Agent
**Inputs**: service name, SLO targets, stack
**Process**:
1. Prometheus rule generation
2. Grafana dashboard creation
3. KB pattern matching
4. Syntax validation
5. PR/MR with provisioning files

**Outputs**: `observability/*` configs with citations

## Success Metrics

### Delivery Metrics
- **Onboarding Speed**: New repo → PR in ≤30 minutes
- **Review Quality**: 100% PRs include dry-run artifacts
- **KB Utilization**: ≥80% configs include citations
- **UI Adoption**: ≥50% usage via Web UI by Week 3

### Quality Metrics
- **Syntax Validity**: 100% generated configs parse correctly
- **Plan Success**: ≥95% Terraform plans execute successfully
- **Helm Validation**: 100% charts pass dry-run
- **Citation Coverage**: ≥3 KB citations per generated file

## Risk Mitigation

### Technical Risks
- **Config Drift**: Proposal-only prevents drift
- **Invalid Configs**: Dry-run validation before PR
- **KB Quality**: Continuous validation and curation
- **Performance**: Caching and optimization for <30min target

### Security Risks
- **Credential Exposure**: Scoped tokens, rotation policies
- **Unauthorized Access**: Allow-lists, OPA policies
- **Audit Gaps**: Immutable JSONL for all operations
- **Shell Injection**: No raw shell - only typed MCP calls

## Next Steps

1. **Immediate** (Day 1-2):
   - Set up project structure
   - Initialize FastAPI application
   - Configure Chroma database
   - Implement basic MCP server framework

2. **Week 1 Sprint**:
   - Complete Pipeline Agent
   - Implement KB connect/search
   - Basic CLI commands
   - JSONL audit system

3. **Ongoing**:
   - Daily progress tracking against timeline
   - Weekly demos of completed features
   - Continuous documentation updates
   - Regular security reviews