# F-Ops Project Overview

## Purpose
F-Ops is a local-first DevOps assistant that combines AI-powered automation with proposal-only safety. It features three specialized agents that generate complete DevOps setups through reviewable Pull/Merge Requests with dry-run validation—never executing directly.

## Core Concept
**Proposal-Only Architecture**: F-Ops generates CI/CD pipelines, infrastructure configs, and monitoring setups as Pull/Merge Requests with attached dry-run artifacts. All changes are reviewable before execution.

## Three-Agent System
- **Pipeline Agent**: Generates CI/CD workflows (GitHub Actions/GitLab CI) with security scans and SLO gates
- **Infrastructure Agent**: Creates Terraform modules and Helm charts with `terraform plan` and `helm --dry-run` validation  
- **Monitoring Agent**: Produces Prometheus rules and Grafana dashboards for observability

## Key Features
- **Safety First**: Zero direct execution—all changes through PR review
- **AI-Powered**: Uses OpenAI/Anthropic APIs for intelligent analysis
- **Knowledge Base**: Chroma vector database for RAG-powered template retrieval
- **MCP Integration**: Custom Model Context Protocol server packs for tool integration
- **Local-First**: No external dependencies for core functionality

## Success Metrics
- Onboarding Speed: New repo → Complete PR set in ≤30 minutes
- Review Quality: 100% of outputs delivered as reviewable PRs with dry-run artifacts
- Knowledge Utility: ≥80% of generated configs include KB citations
- Safety: Zero direct execution—all changes through PR review

## Main Interfaces
- **CLI**: `fops onboard` and `fops kb` commands for proposal generation
- **Web UI**: React frontend with four modules (planned for Week 2+)
- **API**: FastAPI backend with agent orchestration