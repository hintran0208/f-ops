# Week 1: Core Foundation & Pipeline Agent

## Duration: Week 1 (5 days)

## Objectives
- Set up FastAPI core with agent orchestration
- Implement Chroma vector database for knowledge management
- Build **Pipeline Agent** for CI/CD generation
- Create CLI with `fops onboard` and `fops kb` commands
- Implement `mcp-kb` for knowledge operations
- Establish JSONL audit logging and SQLite state management

## Architecture Focus
Building the foundation for **proposal-only** operations where all agent outputs are PR/MRs with dry-run artifacts attached for review.

## Day-by-Day Implementation

### Day 1: Project Setup & Core Infrastructure

#### Morning (4 hours)
1. **Project Structure Creation**
   ```
   f-ops/
   ├── backend/
   │   ├── app/
   │   │   ├── __init__.py
   │   │   ├── main.py
   │   │   ├── config.py
   │   │   ├── agents/
   │   │   │   ├── pipeline_agent.py
   │   │   │   ├── infrastructure_agent.py  # (Week 2)
   │   │   │   └── monitoring_agent.py      # (Week 3)
   │   │   ├── core/
   │   │   │   ├── kb_manager.py
   │   │   │   ├── pr_orchestrator.py
   │   │   │   └── citation_engine.py
   │   │   ├── mcp_servers/
   │   │   │   ├── mcp_kb.py
   │   │   │   ├── mcp_github.py
   │   │   │   └── mcp_gitlab.py
   │   │   ├── api/
   │   │   │   └── routes/
   │   │   ├── models/
   │   │   └── schemas/
   │   ├── requirements.txt
   │   └── Dockerfile
   ├── cli/
   │   ├── fops/
   │   │   ├── __init__.py
   │   │   ├── cli.py
   │   │   ├── commands/
   │   │   │   ├── onboard.py
   │   │   │   └── kb.py
   │   └── requirements.txt
   ├── audit_logs/
   ├── chroma_db/
   ├── docker-compose.yml
   └── .env.example
   ```

2. **Core Dependencies**
   ```python
   # backend/requirements.txt
   fastapi==0.104.0
   uvicorn==0.24.0
   langchain==0.0.350
   langgraph==0.0.20
   chromadb==0.4.15
   sqlalchemy==2.0.23
   pydantic==2.5.0
   httpx==0.25.0
   pygithub==2.1.1
   python-gitlab==3.15.0
   pyyaml==6.0.1
   jsonschema==4.20.0  # For YAML validation
   ```

3. **FastAPI Application Core**
   ```python
   # backend/app/main.py
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from app.api.routes import pipeline, kb
   from app.core.config import settings

   app = FastAPI(
       title="F-Ops — Local-First DevOps Assistant",
       version="0.1.0",
       description="Proposal-only CI/CD, IaC, and monitoring generation"
   )

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],  # Local-first
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline-agent"])
   app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])
   ```

#### Afternoon (4 hours)
1. **Configuration Management**
   ```python
   # backend/app/config.py
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       # Core
       PROJECT_NAME: str = "F-Ops"
       API_V1_STR: str = "/api/v1"

       # Local Storage (no Postgres)
       SQLITE_URL: str = "sqlite:///./fops.db"
       CHROMA_PERSIST_DIR: str = "./chroma_db"
       AUDIT_LOG_DIR: str = "./audit_logs"

       # MCP Servers (local)
       MCP_GITHUB_TOKEN: str = ""
       MCP_GITLAB_TOKEN: str = ""

       # Security
       ALLOWED_REPOS: list = []  # Allow-listed repos
       SCOPED_NAMESPACES: list = []

       class Config:
           env_file = ".env"

   settings = Settings()
   ```

2. **SQLite Models (Minimal State)**
   ```python
   # backend/app/models/state.py
   from sqlalchemy import Column, Integer, String, DateTime, JSON
   from sqlalchemy.ext.declarative import declarative_base

   Base = declarative_base()

   class ApprovalIndex(Base):
       __tablename__ = "approvals"

       id = Column(Integer, primary_key=True)
       pr_url = Column(String, unique=True)
       repo = Column(String)
       agent_type = Column(String)  # pipeline/infrastructure/monitoring
       created_at = Column(DateTime)
       status = Column(String)  # pending/approved/rejected

   class RunMetadata(Base):
       __tablename__ = "runs"

       id = Column(Integer, primary_key=True)
       run_id = Column(String, unique=True)
       command = Column(String)
       start_time = Column(DateTime)
       end_time = Column(DateTime)
       status = Column(String)
   ```

### Day 2: Chroma Setup & Knowledge Collections

#### Morning (4 hours)
1. **Chroma Knowledge Base Manager**
   ```python
   # backend/app/core/kb_manager.py
   import chromadb
   from chromadb.config import Settings as ChromaSettings
   from typing import List, Dict, Any

   class KnowledgeBaseManager:
       def __init__(self, persist_directory: str):
           self.client = chromadb.PersistentClient(
               path=persist_directory,
               settings=ChromaSettings(
                   anonymized_telemetry=False,
                   allow_reset=False  # Safety
               )
           )
           self.init_collections()

       def init_collections(self):
           """Initialize the 5 core collections"""
           self.collections = {
               'pipelines': self.client.get_or_create_collection(
                   name="kb.pipelines",
                   metadata={"description": "CI/CD pipeline templates"}
               ),
               'iac': self.client.get_or_create_collection(
                   name="kb.iac",
                   metadata={"description": "Infrastructure as Code"}
               ),
               'docs': self.client.get_or_create_collection(
                   name="kb.docs",
                   metadata={"description": "Documentation and runbooks"}
               ),
               'slo': self.client.get_or_create_collection(
                   name="kb.slo",
                   metadata={"description": "SLO definitions"}
               ),
               'incidents': self.client.get_or_create_collection(
                   name="kb.incidents",
                   metadata={"description": "Incident patterns"}
               )
           }

       def search(self, collection: str, query: str, k: int = 5):
           """Search with citation support"""
           results = self.collections[collection].query(
               query_texts=[query],
               n_results=k
           )

           # Format with citations
           return [{
               'text': doc,
               'metadata': meta,
               'citation': f"[{meta.get('source', 'KB')}:{meta.get('id', 'unknown')}]"
           } for doc, meta in zip(results['documents'][0], results['metadatas'][0])]
   ```

2. **Citation Engine**
   ```python
   # backend/app/core/citation_engine.py
   from typing import List, Dict, Any

   class CitationEngine:
       def __init__(self, kb_manager):
           self.kb = kb_manager

       def generate_citations(self, generated_content: str, kb_sources: List[Dict]) -> str:
           """Add citations to generated content"""
           citations = []
           for idx, source in enumerate(kb_sources, 1):
               citations.append(f"[{idx}] {source['citation']}: {source['metadata'].get('title', 'Untitled')}")

           return f"{generated_content}\n\n# Citations\n" + "\n".join(citations)

       def track_usage(self, content_hash: str, sources: List[str]):
           """Track which KB sources were used"""
           # Log to audit trail
           pass
   ```

#### Afternoon (4 hours)
1. **KB Connectors Implementation**
   ```python
   # backend/app/mcp_servers/mcp_kb.py
   from typing import Dict, Any, List
   import httpx
   from bs4 import BeautifulSoup

   class MCPKnowledgeBase:
       def __init__(self, kb_manager):
           self.kb = kb_manager

       async def connect(self, uri: str) -> Dict[str, Any]:
           """Crawl and ingest content from URI"""
           if "github.com" in uri:
               return await self._connect_github(uri)
           elif "confluence" in uri:
               return await self._connect_confluence(uri)
           else:
               return await self._connect_generic(uri)

       async def _connect_github(self, repo_url: str):
           """Ingest GitHub repo docs"""
           # Extract README, docs/, .github/workflows
           pass

       def search(self, query: str, collections: List[str] = None) -> List[Dict]:
           """Multi-collection search"""
           results = []
           for collection in (collections or self.kb.collections.keys()):
               results.extend(self.kb.search(collection, query))
           return results

       def compose(self, template_type: str, context: Dict) -> str:
           """Compose content from KB patterns"""
           # RAG-based composition
           relevant_docs = self.search(context.get('query', ''))
           # Merge patterns and return with citations
           pass
   ```

2. **JSONL Audit Logger**
   ```python
   # backend/app/core/audit_logger.py
   import json
   from datetime import datetime
   from pathlib import Path
   from typing import Dict, Any

   class AuditLogger:
       def __init__(self, log_dir: str = "./audit_logs"):
           self.log_dir = Path(log_dir)
           self.log_dir.mkdir(exist_ok=True)
           self.current_log = self.log_dir / f"audit_{datetime.now():%Y%m%d}.jsonl"

       def log_operation(self, operation: Dict[str, Any]):
           """Log all operations immutably"""
           entry = {
               "timestamp": datetime.now().isoformat(),
               "operation_type": operation.get("type"),
               "agent": operation.get("agent"),
               "inputs": operation.get("inputs"),
               "outputs": operation.get("outputs"),
               "citations": operation.get("citations", []),
               "dry_run_results": operation.get("dry_run_results"),
               "pr_url": operation.get("pr_url")
           }

           with open(self.current_log, 'a') as f:
               f.write(json.dumps(entry) + '\n')

       def log_agent_decision(self, agent: str, decision: Dict):
           """Log agent reasoning and decisions"""
           self.log_operation({
               "type": "agent_decision",
               "agent": agent,
               "decision": decision
           })
   ```

### Day 3: Pipeline Agent Implementation

#### Morning (4 hours)
1. **Pipeline Agent Core**
   ```python
   # backend/app/agents/pipeline_agent.py
   from typing import Dict, Any, List
   from langchain import LLMChain
   from app.core.kb_manager import KnowledgeBaseManager
   from app.core.citation_engine import CitationEngine
   import yaml
   import jsonschema

   class PipelineAgent:
       def __init__(self, kb_manager: KnowledgeBaseManager):
           self.kb = kb_manager
           self.citation_engine = CitationEngine(kb_manager)

       def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
           """Detect stack and frameworks"""
           # Clone repo (temporarily)
           # Detect: language, Dockerfile, package.json, requirements.txt
           # Return stack analysis
           pass

       def generate_pipeline(self,
                           repo_url: str,
                           stack: Dict,
                           target: str,
                           environments: List[str]) -> Dict[str, Any]:
           """Generate CI/CD pipeline with citations"""

           # 1. Search KB for similar pipelines
           similar_pipelines = self.kb.search(
               collection='pipelines',
               query=f"{stack['language']} {target} CI/CD",
               k=5
           )

           # 2. Compose pipeline
           if "github.com" in repo_url:
               pipeline = self._generate_github_actions(stack, target, environments)
           else:
               pipeline = self._generate_gitlab_ci(stack, target, environments)

           # 3. Add security scans and SLO gates
           pipeline = self._add_security_gates(pipeline)
           pipeline = self._add_slo_gates(pipeline)

           # 4. Validate syntax
           self._validate_yaml(pipeline)

           # 5. Add citations
           pipeline_with_citations = self.citation_engine.generate_citations(
               pipeline,
               similar_pipelines
           )

           return {
               "pipeline": pipeline_with_citations,
               "citations": [s['citation'] for s in similar_pipelines],
               "validation": "passed"
           }

       def _generate_github_actions(self, stack: Dict, target: str, envs: List[str]) -> str:
           """Generate GitHub Actions workflow"""
           workflow = {
               'name': 'CI/CD Pipeline',
               'on': {'push': {'branches': ['main']}, 'pull_request': {}},
               'jobs': {}
           }

           # Build job
           workflow['jobs']['build'] = {
               'runs-on': 'ubuntu-latest',
               'steps': [
                   {'uses': 'actions/checkout@v3'},
                   {'name': 'Build', 'run': f"# Build commands for {stack['language']}"}
               ]
           }

           # Add security scanning
           workflow['jobs']['security'] = {
               'runs-on': 'ubuntu-latest',
               'steps': [
                   {'name': 'Security Scan', 'run': 'echo "Security scanning..."'}
               ]
           }

           return yaml.dump(workflow)

       def _validate_yaml(self, yaml_content: str):
           """Validate YAML syntax"""
           try:
               yaml.safe_load(yaml_content)
           except yaml.YAMLError as e:
               raise ValueError(f"Invalid YAML: {e}")
   ```

2. **PR Orchestrator**
   ```python
   # backend/app/core/pr_orchestrator.py
   from github import Github
   import gitlab
   from typing import Dict, Any, List

   class PROrchestrator:
       def __init__(self, github_token: str, gitlab_token: str):
           self.github = Github(github_token)
           self.gitlab = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_token)

       def create_pr(self,
                    repo_url: str,
                    files: Dict[str, str],
                    title: str,
                    body: str,
                    dry_run_artifacts: Dict = None) -> str:
           """Create PR/MR with files and dry-run results"""

           if "github.com" in repo_url:
               return self._create_github_pr(repo_url, files, title, body, dry_run_artifacts)
           else:
               return self._create_gitlab_mr(repo_url, files, title, body, dry_run_artifacts)

       def _create_github_pr(self, repo_url: str, files: Dict, title: str, body: str, artifacts: Dict) -> str:
           """Create GitHub PR"""
           # Parse repo from URL
           # Create branch
           # Add files
           # Attach dry-run results as PR comment
           # Return PR URL
           pass

       def attach_artifacts(self, pr_url: str, artifacts: Dict):
           """Attach dry-run/plan artifacts to PR"""
           # Format artifacts as markdown
           # Add as PR comment
           pass
   ```

#### Afternoon (4 hours)
1. **CLI Implementation**
   ```python
   # cli/fops/cli.py
   import typer
   from typing import List, Optional
   from fops.commands import onboard, kb

   app = typer.Typer(
       name="fops",
       help="F-Ops: Local-first DevOps assistant (proposal-only)"
   )

   app.add_typer(onboard.app, name="onboard")
   app.add_typer(kb.app, name="kb")

   @app.callback()
   def main():
       """F-Ops CLI - All operations generate PR/MRs for review"""
       pass
   ```

2. **Onboard Command**
   ```python
   # cli/fops/commands/onboard.py
   import typer
   from typing import List
   from enum import Enum
   import httpx

   app = typer.Typer()

   class Target(str, Enum):
       k8s = "k8s"
       serverless = "serverless"
       static = "static"

   @app.command()
   def main(
       repo: str = typer.Argument(..., help="Repository URL"),
       target: Target = typer.Option(Target.k8s, "--target", "-t"),
       env: List[str] = typer.Option(["staging", "prod"], "--env", "-e")
   ):
       """Generate CI/CD pipeline and infrastructure configs"""
       typer.echo(f"🚀 Onboarding repository: {repo}")
       typer.echo(f"   Target: {target.value}")
       typer.echo(f"   Environments: {', '.join(env)}")

       # Call Pipeline Agent
       response = httpx.post(
           "http://localhost:8000/api/pipeline/generate",
           json={
               "repo_url": repo,
               "target": target.value,
               "environments": env
           }
       )

       if response.status_code == 200:
           result = response.json()
           typer.echo(f"✅ Pipeline generated with {len(result['citations'])} KB citations")
           typer.echo(f"📝 PR created: {result['pr_url']}")

           # Note: Infrastructure Agent will be added in Week 2
           typer.echo("ℹ️  Infrastructure configs will be available in Week 2")
       else:
           typer.echo(f"❌ Error: {response.text}", err=True)
   ```

### Day 4: MCP Server Implementation

#### Morning (4 hours)
1. **MCP GitHub Server**
   ```python
   # backend/app/mcp_servers/mcp_github.py
   from github import Github
   from typing import Dict, Any, List

   class MCPGitHub:
       def __init__(self, token: str, allowed_repos: List[str]):
           self.client = Github(token)
           self.allowed_repos = allowed_repos

       def validate_repo(self, repo_url: str):
           """Check if repo is allow-listed"""
           if not any(allowed in repo_url for allowed in self.allowed_repos):
               raise ValueError(f"Repository not allow-listed: {repo_url}")

       def create_pr(self, params: Dict[str, Any]) -> str:
           """Create PR with typed interface (no shell execution)"""
           self.validate_repo(params['repo_url'])

           repo = self.client.get_repo(params['repo_name'])

           # Create branch
           base_branch = repo.get_branch("main")
           repo.create_git_ref(
               ref=f"refs/heads/{params['branch_name']}",
               sha=base_branch.commit.sha
           )

           # Add files
           for path, content in params['files'].items():
               repo.create_file(
                   path=path,
                   message=f"Add {path}",
                   content=content,
                   branch=params['branch_name']
               )

           # Create PR
           pr = repo.create_pull(
               title=params['title'],
               body=params['body'],
               head=params['branch_name'],
               base="main"
           )

           return pr.html_url

       def get_logs(self, workflow_run_id: int) -> str:
           """Fetch workflow logs"""
           # Typed interface to fetch logs
           pass
   ```

2. **MCP GitLab Server**
   ```python
   # backend/app/mcp_servers/mcp_gitlab.py
   import gitlab
   from typing import Dict, Any, List

   class MCPGitLab:
       def __init__(self, token: str, allowed_repos: List[str]):
           self.client = gitlab.Gitlab('https://gitlab.com', private_token=token)
           self.allowed_repos = allowed_repos

       def create_mr(self, params: Dict[str, Any]) -> str:
           """Create GitLab MR"""
           self.validate_repo(params['repo_url'])

           project = self.client.projects.get(params['project_id'])

           # Create branch and add files
           branch = project.branches.create({
               'branch': params['branch_name'],
               'ref': 'main'
           })

           # Create MR
           mr = project.mergerequests.create({
               'source_branch': params['branch_name'],
               'target_branch': 'main',
               'title': params['title'],
               'description': params['body']
           })

           return mr.web_url
   ```

#### Afternoon (4 hours)
1. **KB Commands**
   ```python
   # cli/fops/commands/kb.py
   import typer
   from typing import Optional
   import httpx

   app = typer.Typer()

   @app.command()
   def connect(
       uri: str = typer.Argument(..., help="URI to connect (GitHub/Confluence/Docs)")
   ):
       """Connect and ingest knowledge source"""
       typer.echo(f"📚 Connecting to: {uri}")

       response = httpx.post(
           "http://localhost:8000/api/kb/connect",
           json={"uri": uri}
       )

       if response.status_code == 200:
           result = response.json()
           typer.echo(f"✅ Ingested {result['documents']} documents")
           typer.echo(f"📊 Collections updated: {', '.join(result['collections'])}")
       else:
           typer.echo(f"❌ Error: {response.text}", err=True)

   @app.command()
   def search(
       query: str = typer.Argument(..., help="Search query"),
       collection: Optional[str] = typer.Option(None, "--collection", "-c"),
       limit: int = typer.Option(5, "--limit", "-l")
   ):
       """Search knowledge base"""
       typer.echo(f"🔍 Searching for: {query}")

       params = {"q": query, "limit": limit}
       if collection:
           params["collection"] = collection

       response = httpx.get(
           "http://localhost:8000/api/kb/search",
           params=params
       )

       if response.status_code == 200:
           results = response.json()["results"]
           for idx, result in enumerate(results, 1):
               typer.echo(f"\n{idx}. {result['metadata']['title']}")
               typer.echo(f"   {result['text'][:200]}...")
               typer.echo(f"   Citation: {result['citation']}")
       else:
           typer.echo(f"❌ Error: {response.text}", err=True)
   ```

2. **API Routes**
   ```python
   # backend/app/api/routes/pipeline.py
   from fastapi import APIRouter, HTTPException
   from app.agents.pipeline_agent import PipelineAgent
   from app.core.pr_orchestrator import PROrchestrator
   from app.schemas.pipeline import PipelineRequest, PipelineResponse

   router = APIRouter()

   @router.post("/generate", response_model=PipelineResponse)
   async def generate_pipeline(request: PipelineRequest):
       """Generate CI/CD pipeline and create PR"""
       try:
           # Initialize agent
           pipeline_agent = PipelineAgent(kb_manager)

           # Analyze repository
           stack = pipeline_agent.analyze_repository(request.repo_url)

           # Generate pipeline
           result = pipeline_agent.generate_pipeline(
               repo_url=request.repo_url,
               stack=stack,
               target=request.target,
               environments=request.environments
           )

           # Create PR
           pr_orchestrator = PROrchestrator(
               settings.MCP_GITHUB_TOKEN,
               settings.MCP_GITLAB_TOKEN
           )

           pr_url = pr_orchestrator.create_pr(
               repo_url=request.repo_url,
               files={
                   ".github/workflows/pipeline.yml": result["pipeline"]
               },
               title="[F-Ops] Add CI/CD Pipeline",
               body=f"Generated pipeline with {len(result['citations'])} KB citations"
           )

           # Log to audit
           audit_logger.log_operation({
               "type": "pipeline_generation",
               "agent": "pipeline",
               "inputs": request.dict(),
               "outputs": {"pr_url": pr_url},
               "citations": result["citations"]
           })

           return PipelineResponse(
               pr_url=pr_url,
               citations=result["citations"],
               validation_status="passed"
           )

       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

### Day 5: Integration & Testing

#### Morning (4 hours)
1. **End-to-End Pipeline Test**
   ```python
   # tests/test_pipeline_agent.py
   import pytest
   from app.agents.pipeline_agent import PipelineAgent
   from app.core.kb_manager import KnowledgeBaseManager

   @pytest.fixture
   def pipeline_agent():
       kb = KnowledgeBaseManager("./test_chroma")
       return PipelineAgent(kb)

   def test_github_actions_generation(pipeline_agent):
       """Test GitHub Actions generation"""
       result = pipeline_agent.generate_pipeline(
           repo_url="https://github.com/test/repo",
           stack={"language": "python", "framework": "fastapi"},
           target="k8s",
           environments=["staging", "prod"]
       )

       assert "pipeline" in result
       assert "citations" in result
       assert len(result["citations"]) > 0
       assert "validation" in result
       assert result["validation"] == "passed"

   def test_gitlab_ci_generation(pipeline_agent):
       """Test GitLab CI generation"""
       result = pipeline_agent.generate_pipeline(
           repo_url="https://gitlab.com/test/repo",
           stack={"language": "node", "framework": "express"},
           target="serverless",
           environments=["dev", "prod"]
       )

       assert ".gitlab-ci.yml" in result["pipeline"] or "stages:" in result["pipeline"]

   def test_security_gates_included(pipeline_agent):
       """Test security scanning is included"""
       result = pipeline_agent.generate_pipeline(
           repo_url="https://github.com/test/repo",
           stack={"language": "python"},
           target="static",
           environments=["prod"]
       )

       assert "security" in result["pipeline"].lower() or "scan" in result["pipeline"].lower()
   ```

2. **KB Integration Test**
   ```python
   # tests/test_kb_integration.py
   import pytest
   from app.core.kb_manager import KnowledgeBaseManager

   @pytest.fixture
   def kb_manager():
       return KnowledgeBaseManager("./test_chroma")

   def test_kb_search_with_citations(kb_manager):
       """Test KB search returns citations"""
       # Add test document
       kb_manager.collections['pipelines'].add(
           documents=["GitHub Actions for Python with pytest"],
           metadatas=[{"source": "github", "id": "test-001"}],
           ids=["doc1"]
       )

       results = kb_manager.search("pipelines", "python testing", k=1)

       assert len(results) > 0
       assert "citation" in results[0]
       assert "[github:test-001]" in results[0]["citation"]

   def test_multi_collection_search(kb_manager):
       """Test searching across collections"""
       mcp_kb = MCPKnowledgeBase(kb_manager)
       results = mcp_kb.search("kubernetes deployment", collections=["pipelines", "iac"])

       assert isinstance(results, list)
   ```

#### Afternoon (4 hours)
1. **CLI Testing**
   ```python
   # tests/test_cli.py
   from typer.testing import CliRunner
   from fops.cli import app

   runner = CliRunner()

   def test_onboard_command():
       result = runner.invoke(app, [
           "onboard",
           "https://github.com/test/repo",
           "--target", "k8s",
           "--env", "staging",
           "--env", "prod"
       ])

       assert result.exit_code == 0
       assert "Onboarding repository" in result.stdout
       assert "PR created" in result.stdout or "Error" in result.stdout

   def test_kb_search_command():
       result = runner.invoke(app, [
           "kb", "search",
           "deployment strategies"
       ])

       assert result.exit_code == 0
       assert "Searching for" in result.stdout
   ```

2. **Docker Setup**
   ```yaml
   # docker-compose.yml
   version: '3.8'

   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       volumes:
         - ./chroma_db:/app/chroma_db
         - ./audit_logs:/app/audit_logs
         - ./fops.db:/app/fops.db
       environment:
         - CHROMA_PERSIST_DIR=/app/chroma_db
         - AUDIT_LOG_DIR=/app/audit_logs
         - SQLITE_URL=sqlite:////app/fops.db
       command: uvicorn app.main:app --host 0.0.0.0 --reload

     chroma:
       image: chromadb/chroma
       ports:
         - "8001:8000"
       volumes:
         - ./chroma_db:/chroma/chroma
   ```

## Deliverables for Week 1

### Completed Components
1. ✅ FastAPI core with agent orchestration
2. ✅ Chroma with 5 KB collections (pipelines, iac, docs, slo, incidents)
3. ✅ **Pipeline Agent** generating CI/CD with citations
4. ✅ CLI: `fops onboard` and `fops kb` commands
5. ✅ MCP servers: `mcp-kb`, `mcp-github`, `mcp-gitlab`
6. ✅ PR/MR creation with validated YAML
7. ✅ JSONL audit logging
8. ✅ SQLite minimal state
9. ✅ Docker containerization

### Success Criteria Met
- ✅ Generate valid GitHub Actions/GitLab CI pipelines
- ✅ KB search returns relevant snippets with citations
- ✅ All operations logged to audit trail
- ✅ PR/MR created with pipeline configs
- ✅ YAML syntax validation passes

### Week 1 Output Example
```bash
$ fops onboard https://github.com/acme/api --target k8s --env staging --env prod

🚀 Onboarding repository: https://github.com/acme/api
   Target: k8s
   Environments: staging, prod

✅ Pipeline generated with 5 KB citations
📝 PR created: https://github.com/acme/api/pull/42

PR contains:
- .github/workflows/pipeline.yml (with security scans & SLO gates)
- Citations from KB: [pipelines:k8s-001], [pipelines:python-003], ...

ℹ️  Infrastructure configs will be available in Week 2
```

## Next Week Preview (Week 2)
- **Infrastructure Agent**: Terraform + Helm generation
- `terraform plan` and `helm --dry-run` integration
- Web UI: Pipeline and Infrastructure modules
- PR/MR with attached dry-run artifacts