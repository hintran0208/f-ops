# F-Ops Project Overview

## Purpose
F-Ops is a **local-first DevOps assistant** that provides AI-powered automation through **proposal-only safety**. It combines three specialized agents (Pipeline, Infrastructure, Monitoring) that generate complete DevOps setups through **reviewable PRs** with **dry-run validation**—never executing directly.

## Core Concept
**Proposal-Only Architecture**: F-Ops generates CI/CD pipelines, infrastructure configs, and monitoring setups as **Pull/Merge Requests** with attached dry-run artifacts. All changes are reviewable before execution.

## Three-Agent System
- **Pipeline Agent**: Generates CI/CD workflows (GitHub Actions/GitLab CI) with security scans and SLO gates
- **Infrastructure Agent**: Creates Terraform modules and Helm charts with `terraform plan` and `helm --dry-run` validation
- **Monitoring Agent**: Produces Prometheus rules and Grafana dashboards for observability

## Key Features
- **Safety First**: No direct execution - all operations generate PR/MR proposals only
- **Dry-Run Validation**: Every generated config includes validation artifacts
- **Knowledge Base**: Chroma vector database for RAG-powered template retrieval
- **MCP Integration**: Custom Model Context Protocol servers for tool integration
- **Multi-Interface**: CLI and Web UI access

## Target Workflows
1. `fops onboard --repo <url> --target k8s --env staging,prod` → Generates complete DevOps setup as 3 PRs
2. `fops kb connect --uri <link>` / `fops kb search "<query>"` → Knowledge management
3. Web UI modules for form-driven generation with preview

## Architecture
- **Backend**: FastAPI with LangGraph agent orchestration
- **Vector DB**: Chroma for semantic search and RAG
- **State**: SQLite for minimal metadata, JSONL for audit
- **Validation**: Native tools for syntax checking, dry-run execution
- **Security**: Proposal-only, scoped tokens, allow-listed repos