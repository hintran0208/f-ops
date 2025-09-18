# F-Ops (DevOps AI Agent) — Implementation Plan (Python + Chroma)

**Phase focus:** Implement **CLI** and **Web UI** first. Slack/Teams, VS Code/Copilot, and Claude Code MCP will follow after MVP.

---

## 1) Objectives (Phase 1 = CLI + Web UI)

- **Zero-to-Deploy** for brand-new repos via CLI & Web UI wizard.
- **Operate Safely**: CI/CD orchestration, dry-run by default, approvals in Web UI.
- **Knowledge-Driven**: Chroma vector KB for pipelines/runbooks; plans cite sources.
- **Guardrails**: OPA policy checks, two-key approvals, immutable audit.

---

## 2) Scope & Features (Phase 1)

### A) CLI (Python Typer)

- `fops onboard --repo <url> --target k8s|serverless|static --env staging,prod`
- `fops deploy --service <name> --env <env> --approve`
- `fops incident --service <name>` (summarize logs/metrics; propose actions)
- `fops kb connect --uri <link>` and `fops kb search "<query>"`
- Global flags: `--dry-run`, `--no-apply`, `--policy=<file.rego>`

### B) Web UI (FastAPI backend + React/Tailwind frontend)

- **Onboarding Wizard**: repo URL → detect stack → options → preview PR diffs (CI/CD, IaC/Helm, policies) → **Approve**.
- **Deployments**: service listing, “Deploy now”, live logs, health/SLO status, **Approve** buttons.
- **Incidents**: alert list → RCA view (metrics/logs) → proposed fix actions → approval & execution.
- **Knowledge Base**: “Connect Source” (paste link), KB search with snippet preview & citations, “Apply as pipeline”.
- **Audit & Policy**: timeline of actions; policy viewer (active OPA rules).

---

## 3) Architecture (no Postgres)

- **Agent Core (FastAPI)**: planning (LangGraph/LangChain), policy checks (OPA), approvals, event/webhook handlers.
- **MCP Packs (local)**: `mcp-github`, `mcp-gitlab`, `mcp-jenkins`, `mcp-kubernetes`, `mcp-aws`, `mcp-observability`, `mcp-kb`.
- **Knowledge Layer**: **Chroma** (persistent) for embeddings/semantic search; collections per tenant/project.
- **State & Audit**: **SQLite** (approvals, runs, incidents), **JSONL** append-only audit logs.
- **Observability**: Prometheus/Grafana APIs, optional ELK; OpenTelemetry for agent traces.
- **Security**: OPA guardrails, least-privilege credentials, tenant scoping (per-collection), signed webhooks.

---

## 4) Tech Stack

- **Python 3.11+**, **FastAPI**, **Uvicorn**
- **LangGraph/LangChain** for tool orchestration
- **Chroma** for vector search; **SQLite** + **JSONL** for state/audit
- **Terraform**, **Helm**, **Kubernetes Python client**
- **Prometheus/Grafana** HTTP APIs; **OPA (rego)**
- **React + Tailwind** (Web UI), **Typer** (CLI)
- Packaging: Docker images per MCP & agent; PyPI pkg for CLI

---

## 5) Knowledge & Planning (Phase 1)

- **Chroma collections**: `kb.docs`, `kb.pipelines`, `kb.iac`, `kb.incidents`, `kb.slo`.
- **Connectors**: `kb.connect(uri)` → crawl → clean → chunk → embed; `kb.sync` via webhook/poll.
- **RAG planner**: detect context (stack/env/intent) → query top-K → **merge** retrieved pipeline/IaC steps into a plan → OPA validate → dry-run → create PR with **citations**.

---

## 6) Development Roadmap (front-loaded on CLI + Web UI)

**Week 1 — Core & KB**

- FastAPI skeleton; Chroma client; `kb.connect/search`; JSONL audit; SQLite approvals/runs.
- MCP: GitHub + Kubernetes; **Zero-to-Deploy** scaffold generator (CI/CD, Helm/Terraform, policy files).
- CLI: `onboard`, `kb connect/search`.

**Week 2 — Web UI MVP & Deploy Flow**

- Web UI: auth, Onboarding Wizard, PR preview (diffs), Approve → dry-run deploy to **staging**; Deployments page (live logs).
- CLI: `deploy`, `incident` (summary + suggested actions).
- OPA policy hooks (deny destructive ops; require approval).

**Week 3 — Incidents, KB polish, Approvals UX**

- Web UI: Incident dashboard (RCA view, action proposals, approval buttons), KB search/preview, “Apply as pipeline”.
- Observability MCP (Prometheus/Grafana) for metrics queries.
- RAG planner v1 (citations in PR); service/env filters.

**Week 4 — Hardening & Demo Readiness**

- Multi-tenant collections; token scoping; signed webhooks.
- Evaluation harness (retrieval hit-rate, plan quality, dry-run success).
- Docs: Quickstart (CLI/Web), security policy templates, demo scripts.

> **Post-MVP (later):** Slack/Teams bot, VS Code extension + Copilot prompts, Claude Code MCP wiring, GitLab/Jenkins/AWS breadth.

---

## 7) APIs & CLI↔Web parity (examples)

- **Onboard**:
  - CLI: `fops onboard --repo https://github.com/acme/app --target k8s --env staging,prod`
  - Web: Wizard form → Preview diffs → **Approve** → PR + dry-run → staging live.
- **Deploy**:
  - CLI: `fops deploy --service app --env staging --approve`
  - Web: Service → **Deploy now** → live logs → health/SLO check.
- **Incident**:
  - CLI: `fops incident --service api-gw`
  - Web: Click incident → RCA + actions → **Approve rollback/restart/scale**.
- **Knowledge**:
  - CLI: `fops kb connect --uri <confluence|notion|repo>`; `fops kb search "python helm canary"`
  - Web: “Connect Source” wizard; KB search with citations; **Apply as pipeline**.

---

## 8) Security & Governance

- **OPA guardrails**: change windows, RBAC roles, two-key approvals for prod.
- **Isolation**: per-tenant Chroma collections; credential scoping per MCP pack.
- **Audit**: JSONL timeline + Web UI viewer; export bundle (actions, diffs, approvals, SLO checks).

---

## 9) Success Metrics (Phase 1)

- **Onboarding time**: new repo → staging live **< 30 minutes**.
- **Adoption**: % actions executed from **Web UI** vs CLI (target ≥50% via Web UI).
- **CI/CD health**: dry-run pass rate ≥90%; deploy failure CFR <15%.
- **Incident response**: MTTR **< 1h** for supported classes; ≥60% actions approved from Web UI.

---

## 10) Deliverables (Phase 1)

- **CLI package (PyPI)** with onboard/deploy/incident/KB commands.
- **Web UI** (FastAPI backend + React/Tailwind) with Onboarding, Deployments, Incidents, KB, Approvals, Audit.
- **Agent Core** (FastAPI service) + **MCP packs** (GitHub, Kubernetes, Observability, KB).
- **Chroma KB** persistence + ingestion scripts.
- **SQLite schema + JSONL audit** utilities.
- **Docs**: Quickstart (CLI/Web), security policy templates, demo scenarios.

---

### Bottom Line

We will **ship CLI and Web UI first** with a Python + Chroma core, delivering zero-to-deploy onboarding, safe deployments with approvals, incident triage, and a searchable knowledge base. The same planning and policy engine powers both surfaces; additional surfaces (Slack/Teams, VS Code/Copilot, Claude Code MCP) can plug in later without changing the core.
