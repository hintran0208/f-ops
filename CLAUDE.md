# F-Ops — Three-Agent Plan (Python + Chroma) — CLI + Web UI

> **Purpose:** A local-first DevOps assistant exposed through **CLI** and **Web UI**.  
> **Agents:** **Pipeline Agent**, **Infrastructure Agent**, **Monitoring Agent**.  
> **Tooling Interface:** custom **MCP server packs** (GitHub/GitLab/Jenkins/Kubernetes/Terraform/Helm/Observability/KB). MCP is our “USB-C” for tools so the same skills work across all surfaces (CLI, Web UI, Slack/Teams, VS Code, Claude Code).

---

## 1) Scope & Boundaries

- **CLI**: supports **onboarding** and **knowledge** commands.
  - `fops onboard --repo <url> --target k8s|serverless|static --env staging,prod` → **Pipeline + Infrastructure** Agents collaborate to generate CI/CD + IaC artifacts and open a **PR/MR**; run **dry-runs** where supported (e.g., `terraform plan`, `helm --dry-run`) and attach results for review.
  - `fops kb connect --uri <link>` / `fops kb search "<q>"` → Knowledge ingestion/search in **Chroma**.
- **Web UI**: provides four modules
  - **Pipeline Agent** (generate/preview CI/CD)
  - **Infrastructure Agent** (generate/preview IaC/Helm)
  - **Monitoring Agent** (generate/preview telemetry configs)
  - **KB Connect** (crawl links → embed into Chroma)

---

## 2) Agents & Outputs

### A) Pipeline Agent

**Goal:** Provide CI/CD pipelines for **new or existing projects without deployments**.  
**Inputs:** repo URL, stack, target (k8s/serverless/static), environments, org standards.  
**Process:**

1. Detect stack (lang, Dockerfile, frameworks).
2. Retrieve similar pipelines/templates from **Chroma** (KB).
3. Compose pipeline (GitHub Actions/GitLab CI/Jenkinsfile) with **security/scans + SLO gates**; cite sources.
4. Open **PR/MR** with `.github/workflows/*.yml` or `.gitlab-ci.yml` (validated syntax).  
   **Output:** A reviewable PR/MR containing CI/CD files + a short plan & citations.

### B) Infrastructure Agent

**Goal:** Provide baseline infrastructure & deployment configs to support that pipeline.  
**Inputs:** target (k8s/serverless/static), envs, domain, registry, secrets strategy.  
**Process:**

1. Propose **Terraform** modules (networking, registry, DNS/secrets) and **Helm** chart skeleton (if k8s).
2. Generate IaC + Helm values; run **`terraform plan`** and **`helm --dry-run`**; attach outputs.
3. Open **PR/MR** with `infra/*` and `deploy/chart/*`.  
   **Output:** A reviewable PR/MR with IaC/Helm + plan/dry-run artifacts.

### C) Monitoring Agent

**Goal:** Provide observability scaffolding (metrics/dashboards/alerts) aligned to the new service.  
**Inputs:** service name, env, SLO targets, stack.  
**Process:**

1. Emit **Prometheus rules** (recording/alerting) and **Grafana** provisioning files; cite KB examples.
2. Open **PR/MR** under `observability/` (provisioning YAML + dashboard JSON).  
   **Output:** Reviewable monitoring configs.

---

## 3) Knowledge Base (Chroma) & Connectors

- **Chroma collections:** `kb.pipelines`, `kb.iac`, `kb.docs/runbooks`, `kb.slo`, `kb.incidents` (text + embeddings + tags).
- **Connectors:** `kb.connect(uri)` crawls GitHub/Confluence/Notion/Docs; cleans, chunks, embeds; `kb.sync` refreshes on webhook/poll.
- **RAG planning:** Agents query top-K relevant snippets, **merge** into proposed CI/CD/IaC/observability templates, and **cite sources** in PRs.
- **Safety:** all plans are **proposal-only**; no apply/execute from CLI/Web UI.

---

## 4) MCP Server Packs (local)

A single pack that exposes multiple custom MCP servers/namespaces:

- **SCM & CI:** `mcp-github`, `mcp-gitlab`, `mcp-jenkins` — open PR/MR, comment, fetch logs.
- **Infra & Cluster:** `mcp-terraform`, `mcp-kubernetes`, `mcp-helm` — produce plans/dry-runs and diffs.
- **Observability:** `mcp-observability` — generate Prometheus rule files & Grafana provisioning; optionally validate syntax.
- **Knowledge:** `mcp-kb` — `connect`, `sync`, `search`, `compose`.

---

## 5) Architecture (Python + Chroma, no Postgres)

- **Agent Core (FastAPI):** planning (LangGraph/LangChain), policy checks (OPA), PR orchestration, event/webhook receivers.
- **State & Audit:** SQLite for minimal state (approvals index, run metadata), JSONL for immutable audit.
- **Security:** OPA guardrails, allow-listed repos/namespaces, scoped tokens per MCP; avoid running arbitrary shell via agent—prefer typed MCP calls.
- **Observability:** Prometheus/Grafana APIs used only for **template validation**.

---

## 6) Web UI Modules

- **Pipeline Agent:** form → repo URL, target, envs → preview generated CI/CD files → open PR/MR.
- **Infrastructure Agent:** form → cloud/K8s settings → preview Terraform/Helm + **plan/dry-run** outputs → open PR/MR.
- **Monitoring Agent:** form → SLO targets/stack → preview Prometheus/Grafana provisioning → open PR/MR.
- **KB Connect:** paste links → crawl & embed into Chroma; search/preview indexed items.

---

## 7) CLI Commands

- `fops onboard …` — **enabled** (proposal + PR; with Terraform/Helm dry-run artifacts).
- `fops kb connect …` / `fops kb search …` — **enabled**.

---

## 8) Delivery Timeline (4 weeks)

- **Week 1** — FastAPI core; Chroma client; `mcp-kb` (connect/search); **Pipeline Agent** GitHub/GitLab scaffolds; JSONL audit; SQLite minimal state.
- **Week 2** — **Infrastructure Agent** (Terraform plan; Helm `--dry-run`); Web UI module for Pipeline+Infra previews & PRs.
- **Week 3** — **Monitoring Agent** (Prometheus rules + Grafana provisioning); Web UI monitoring module; KB Connect module.
- **Week 4** — OPA guardrails; multi-tenant Chroma collections; evaluation harness (retrieval hit-rate, plan quality, syntax validation); docs/demo.

---

## 9) Success Criteria

- **Onboarding speed:** new repo → PR with CI/CD + IaC + monitoring in **≤ 30 min**.
- **Reviewability:** 100% changes land as **PR/MR** with **plan/dry-run** artifacts attached.
- **KB utility:** ≥ 80% of generated files include **citations** to KB sources/snippets.
- **Adoption:** ≥ 50% usage via Web UI modules after Week-3.

---

## 10) Risks & Mitigations

- **Config drift or unsafe ops** → strictly plan/preview/PR-only; no apply.
- **MCP security posture** → scoped creds, allow-lists, no raw shell; central policies; rotate tokens.
- **Pipeline portability** → rely on official provider syntax refs (GitHub Actions/GitLab CI).

---

### Bottom Line

F-Ops centers on **design-time generation and review**: the three agents produce **high-quality PRs** for **Pipelines**, **Infrastructure**, and **Monitoring**, and the **KB Connect** module keeps knowledge fresh in **Chroma**. CLI and Web UI expose only onboarding and knowledge flows—keeping everything proposal-first, reviewable, and safe.
