# Phase 1: Core & Knowledge Base Implementation

## Duration: Week 1 (5 days)

## Objectives
- Set up core infrastructure and FastAPI backend
- Implement Chroma vector database for knowledge management
- Create basic CLI with essential commands
- Establish MCP pack foundations
- Integrate prompt engineering templates

## Day-by-Day Breakdown

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
   │   │   ├── core/
   │   │   │   ├── agent.py
   │   │   │   ├── planner.py
   │   │   │   └── executor.py
   │   │   ├── api/
   │   │   │   ├── routes/
   │   │   │   └── dependencies.py
   │   │   ├── models/
   │   │   ├── schemas/
   │   │   └── utils/
   │   ├── requirements.txt
   │   └── Dockerfile
   ├── cli/
   │   ├── fops/
   │   │   ├── __init__.py
   │   │   ├── cli.py
   │   │   ├── commands/
   │   │   └── utils/
   │   ├── setup.py
   │   └── requirements.txt
   ├── mcp_packs/
   │   ├── github/
   │   ├── kubernetes/
   │   └── base/
   ├── knowledge_base/
   │   ├── connectors/
   │   ├── templates/
   │   └── prompts/
   ├── tests/
   ├── docker-compose.yml
   └── .env.example
   ```

2. **Dependencies Installation**
   ```python
   # backend/requirements.txt
   fastapi==0.104.0
   uvicorn==0.24.0
   langchain==0.0.350
   langgraph==0.0.20
   chromadb==0.4.15
   sqlalchemy==2.0.23
   pydantic==2.5.0
   python-multipart==0.0.6
   httpx==0.25.0
   openai==1.3.0
   anthropic==0.8.0
   prometheus-client==0.19.0
   opentelemetry-api==1.21.0
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4
   ```

3. **FastAPI Application Setup**
   ```python
   # backend/app/main.py
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from app.api.routes import kb, onboard, deploy
   from app.core.config import settings
   
   app = FastAPI(
       title="F-Ops DevOps AI Agent",
       version="0.1.0",
       description="AI-powered DevOps automation platform"
   )
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_ORIGINS,
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   
   app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])
   app.include_router(onboard.router, prefix="/api/onboard", tags=["onboarding"])
   app.include_router(deploy.router, prefix="/api/deploy", tags=["deployment"])
   ```

#### Afternoon (4 hours)
1. **Configuration Management**
   ```python
   # backend/app/config.py
   from pydantic_settings import BaseSettings
   
   class Settings(BaseSettings):
       # API Settings
       API_V1_STR: str = "/api/v1"
       PROJECT_NAME: str = "F-Ops"
       
       # Database
       SQLITE_URL: str = "sqlite:///./fops.db"
       CHROMA_PERSIST_DIR: str = "./chroma_db"
       
       # AI/ML
       OPENAI_API_KEY: str = ""
       ANTHROPIC_API_KEY: str = ""
       DEFAULT_MODEL: str = "gpt-4"
       
       # Security
       SECRET_KEY: str = ""
       ALGORITHM: str = "HS256"
       ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
       
       class Config:
           env_file = ".env"
   ```

2. **Database Models Setup**
   ```python
   # backend/app/models/base.py
   from sqlalchemy import create_engine
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy.orm import sessionmaker
   
   Base = declarative_base()
   
   # backend/app/models/deployment.py
   class Deployment(Base):
       __tablename__ = "deployments"
       
       id = Column(Integer, primary_key=True)
       service_name = Column(String)
       environment = Column(String)
       status = Column(String)
       created_at = Column(DateTime)
       approved_by = Column(String)
       dry_run_results = Column(JSON)
   ```

### Day 2: Chroma Vector Database & Knowledge Base

#### Morning (4 hours)
1. **Chroma Client Setup**
   ```python
   # backend/app/core/knowledge_base.py
   import chromadb
   from chromadb.config import Settings as ChromaSettings
   from typing import List, Dict, Any
   
   class KnowledgeBase:
       def __init__(self, persist_directory: str):
           self.client = chromadb.PersistentClient(
               path=persist_directory,
               settings=ChromaSettings(
                   anonymized_telemetry=False,
                   allow_reset=True
               )
           )
           self.init_collections()
       
       def init_collections(self):
           self.collections = {
               'docs': self.client.get_or_create_collection("kb_docs"),
               'pipelines': self.client.get_or_create_collection("kb_pipelines"),
               'iac': self.client.get_or_create_collection("kb_iac"),
               'incidents': self.client.get_or_create_collection("kb_incidents"),
               'prompts': self.client.get_or_create_collection("kb_prompts")
           }
       
       def add_document(self, collection: str, document: Dict[str, Any]):
           # Implementation for adding documents
           pass
       
       def search(self, collection: str, query: str, k: int = 5):
           # Implementation for semantic search
           pass
   ```

2. **Knowledge Connectors**
   ```python
   # backend/app/core/connectors/github.py
   class GitHubConnector:
       def __init__(self, token: str):
           self.token = token
           self.client = Github(token)
       
       def fetch_repository_docs(self, repo_url: str):
           # Fetch README, docs/, wiki
           pass
       
       def fetch_ci_cd_configs(self, repo_url: str):
           # Fetch .github/workflows, .gitlab-ci.yml, etc.
           pass
   
   # backend/app/core/connectors/confluence.py
   class ConfluenceConnector:
       def __init__(self, url: str, token: str):
           self.url = url
           self.token = token
       
       def fetch_space_content(self, space_key: str):
           # Fetch Confluence pages
           pass
   ```

#### Afternoon (4 hours)
1. **Prompt Templates Integration**
   ```python
   # knowledge_base/prompts/devops_prompts.py
   PROMPT_TEMPLATES = {
       "zero_to_deploy": """
       Analyze the repository at {repo_url} and create a complete deployment pipeline.
       
       Stack detected: {stack}
       Target environment: {environment}
       Deployment target: {target}
       
       Generate:
       1. CI/CD pipeline configuration
       2. Infrastructure as Code templates
       3. Deployment scripts
       4. Environment-specific configurations
       5. Security policies
       
       Requirements:
       - Use best practices for {stack}
       - Include security scanning
       - Implement proper secret management
       - Add health checks and monitoring
       """,
       
       "incident_analysis": """
       Analyze the incident for service: {service_name}
       
       Current symptoms:
       {symptoms}
       
       Recent changes:
       {recent_changes}
       
       Metrics data:
       {metrics}
       
       Provide:
       1. Root cause analysis
       2. Immediate mitigation steps
       3. Long-term fix recommendations
       4. Prevention strategies
       """,
       
       "infrastructure_optimization": """
       Review the current infrastructure and suggest optimizations.
       
       Current setup:
       {infrastructure_details}
       
       Usage patterns:
       {usage_metrics}
       
       Cost data:
       {cost_breakdown}
       
       Recommend:
       1. Cost optimization strategies
       2. Performance improvements
       3. Scaling recommendations
       4. Security enhancements
       """
   }
   ```

2. **Document Processing Pipeline**
   ```python
   # backend/app/core/document_processor.py
   from langchain.text_splitter import RecursiveCharacterTextSplitter
   from langchain.embeddings import OpenAIEmbeddings
   
   class DocumentProcessor:
       def __init__(self):
           self.text_splitter = RecursiveCharacterTextSplitter(
               chunk_size=1000,
               chunk_overlap=100
           )
           self.embeddings = OpenAIEmbeddings()
       
       def process_document(self, content: str, metadata: Dict):
           chunks = self.text_splitter.split_text(content)
           embeddings = self.embeddings.embed_documents(chunks)
           
           return [
               {
                   "text": chunk,
                   "embedding": embedding,
                   "metadata": metadata
               }
               for chunk, embedding in zip(chunks, embeddings)
           ]
   ```

### Day 3: CLI Implementation & Basic Commands

#### Morning (4 hours)
1. **CLI Framework Setup**
   ```python
   # cli/fops/cli.py
   import typer
   from typing import Optional
   from fops.commands import onboard, deploy, kb, incident
   
   app = typer.Typer(
       name="fops",
       help="F-Ops: AI-powered DevOps automation CLI"
   )
   
   app.add_typer(onboard.app, name="onboard")
   app.add_typer(deploy.app, name="deploy")
   app.add_typer(kb.app, name="kb")
   app.add_typer(incident.app, name="incident")
   
   @app.callback()
   def main(
       dry_run: bool = typer.Option(False, "--dry-run", help="Run in dry-run mode"),
       config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
       verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
   ):
       """F-Ops CLI - AI-powered DevOps automation"""
       # Set global options
       pass
   ```

2. **Onboard Command Implementation**
   ```python
   # cli/fops/commands/onboard.py
   import typer
   from typing import List
   from enum import Enum
   
   app = typer.Typer()
   
   class DeploymentTarget(str, Enum):
       k8s = "k8s"
       serverless = "serverless"
       static = "static"
   
   @app.command()
   def repo(
       repo_url: str = typer.Argument(..., help="Repository URL"),
       target: DeploymentTarget = typer.Option(DeploymentTarget.k8s, "--target", "-t"),
       environments: List[str] = typer.Option(["staging", "prod"], "--env", "-e"),
       auto_detect: bool = typer.Option(True, "--auto-detect", help="Auto-detect stack")
   ):
       """Onboard a new repository with zero-to-deploy setup"""
       typer.echo(f"🚀 Onboarding repository: {repo_url}")
       
       # 1. Clone and analyze repository
       # 2. Detect technology stack
       # 3. Generate CI/CD pipeline
       # 4. Create IaC templates
       # 5. Setup environments
       # 6. Create PR with changes
       
       typer.echo("✅ Onboarding complete! PR created: #123")
   ```

#### Afternoon (4 hours)
1. **Knowledge Base Commands**
   ```python
   # cli/fops/commands/kb.py
   import typer
   from typing import Optional
   
   app = typer.Typer()
   
   @app.command()
   def connect(
       uri: str = typer.Argument(..., help="Source URI (GitHub, Confluence, etc.)"),
       connector_type: Optional[str] = typer.Option(None, "--type", "-t"),
       sync: bool = typer.Option(False, "--sync", help="Enable auto-sync")
   ):
       """Connect a knowledge source"""
       typer.echo(f"📚 Connecting to knowledge source: {uri}")
       # Implementation
   
   @app.command()
   def search(
       query: str = typer.Argument(..., help="Search query"),
       collection: Optional[str] = typer.Option(None, "--collection", "-c"),
       limit: int = typer.Option(5, "--limit", "-l")
   ):
       """Search the knowledge base"""
       typer.echo(f"🔍 Searching for: {query}")
       # Implementation
   
   @app.command()
   def sync():
       """Sync all connected knowledge sources"""
       typer.echo("🔄 Syncing knowledge sources...")
       # Implementation
   ```

2. **Deploy Command Implementation**
   ```python
   # cli/fops/commands/deploy.py
   import typer
   from typing import Optional
   
   app = typer.Typer()
   
   @app.command()
   def service(
       service_name: str = typer.Argument(..., help="Service name"),
       environment: str = typer.Option("staging", "--env", "-e"),
       version: Optional[str] = typer.Option(None, "--version", "-v"),
       approve: bool = typer.Option(False, "--approve", help="Auto-approve")
   ):
       """Deploy a service to an environment"""
       typer.echo(f"🚀 Deploying {service_name} to {environment}")
       
       # 1. Validate deployment
       # 2. Run policy checks
       # 3. Execute dry-run
       # 4. Show dry-run results
       # 5. Wait for approval (if not auto-approved)
       # 6. Execute deployment
       # 7. Monitor deployment
       
       typer.echo("✅ Deployment successful!")
   ```

### Day 4: MCP Pack Foundations

#### Morning (4 hours)
1. **Base MCP Pack Structure**
   ```python
   # mcp_packs/base/mcp_pack.py
   from abc import ABC, abstractmethod
   from typing import Dict, Any, List
   
   class MCPPack(ABC):
       def __init__(self, config: Dict[str, Any]):
           self.config = config
           self.validate_config()
       
       @abstractmethod
       def validate_config(self):
           """Validate pack configuration"""
           pass
       
       @abstractmethod
       def execute_action(self, action: str, params: Dict[str, Any]):
           """Execute a pack action"""
           pass
       
       @abstractmethod
       def get_available_actions(self) -> List[str]:
           """Return list of available actions"""
           pass
   ```

2. **GitHub MCP Pack**
   ```python
   # mcp_packs/github/github_pack.py
   from github import Github
   from mcp_packs.base import MCPPack
   
   class GitHubPack(MCPPack):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           self.client = Github(config['token'])
       
       def validate_config(self):
           if 'token' not in self.config:
               raise ValueError("GitHub token required")
       
       def execute_action(self, action: str, params: Dict[str, Any]):
           actions = {
               'create_pr': self.create_pr,
               'get_workflows': self.get_workflows,
               'trigger_workflow': self.trigger_workflow,
               'get_repository_info': self.get_repository_info
           }
           
           if action not in actions:
               raise ValueError(f"Unknown action: {action}")
           
           return actions[action](params)
       
       def create_pr(self, params: Dict[str, Any]):
           # Create pull request implementation
           pass
       
       def get_workflows(self, params: Dict[str, Any]):
           # Get GitHub Actions workflows
           pass
   ```

#### Afternoon (4 hours)
1. **Kubernetes MCP Pack**
   ```python
   # mcp_packs/kubernetes/k8s_pack.py
   from kubernetes import client, config
   from mcp_packs.base import MCPPack
   
   class KubernetesPack(MCPPack):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           self.setup_k8s_client()
       
       def setup_k8s_client(self):
           if self.config.get('in_cluster'):
               config.load_incluster_config()
           else:
               config.load_kube_config(
                   config_file=self.config.get('kubeconfig')
               )
           
           self.v1 = client.CoreV1Api()
           self.apps_v1 = client.AppsV1Api()
       
       def execute_action(self, action: str, params: Dict[str, Any]):
           actions = {
               'deploy': self.deploy_application,
               'scale': self.scale_deployment,
               'rollback': self.rollback_deployment,
               'get_pods': self.get_pods,
               'get_logs': self.get_pod_logs
           }
           
           return actions[action](params)
       
       def deploy_application(self, params: Dict[str, Any]):
           # Deploy application to Kubernetes
           pass
   ```

2. **AWS MCP Pack**
   ```python
   # mcp_packs/aws/aws_pack.py
   import boto3
   from mcp_packs.base import MCPPack
   
   class AWSPack(MCPPack):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           self.setup_aws_clients()
       
       def setup_aws_clients(self):
           session = boto3.Session(
               aws_access_key_id=self.config.get('access_key'),
               aws_secret_access_key=self.config.get('secret_key'),
               region_name=self.config.get('region', 'us-east-1')
           )
           
           self.ec2 = session.client('ec2')
           self.ecs = session.client('ecs')
           self.lambda_client = session.client('lambda')
           self.cloudformation = session.client('cloudformation')
       
       def execute_action(self, action: str, params: Dict[str, Any]):
           actions = {
               'deploy_lambda': self.deploy_lambda,
               'update_ecs_service': self.update_ecs_service,
               'create_stack': self.create_cloudformation_stack
           }
           
           return actions[action](params)
   ```

### Day 5: Integration & Testing

#### Morning (4 hours)
1. **Agent Core Integration**
   ```python
   # backend/app/core/agent.py
   from langchain.agents import initialize_agent, Tool
   from langchain.llms import OpenAI
   from app.core.knowledge_base import KnowledgeBase
   from mcp_packs import GitHubPack, KubernetesPack, AWSPack
   
   class DevOpsAgent:
       def __init__(self):
           self.llm = OpenAI(temperature=0)
           self.kb = KnowledgeBase("./chroma_db")
           self.setup_tools()
           self.setup_agent()
       
       def setup_tools(self):
           self.tools = [
               Tool(
                   name="Knowledge Search",
                   func=self.kb.search,
                   description="Search the knowledge base"
               ),
               Tool(
                   name="GitHub Operations",
                   func=self.github_operations,
                   description="Perform GitHub operations"
               ),
               Tool(
                   name="Kubernetes Operations",
                   func=self.k8s_operations,
                   description="Perform Kubernetes operations"
               )
           ]
       
       def setup_agent(self):
           self.agent = initialize_agent(
               self.tools,
               self.llm,
               agent="zero-shot-react-description",
               verbose=True
           )
       
       def process_request(self, request: str):
           return self.agent.run(request)
   ```

2. **JSONL Audit Logger**
   ```python
   # backend/app/core/audit.py
   import json
   from datetime import datetime
   from pathlib import Path
   
   class AuditLogger:
       def __init__(self, log_dir: str = "./audit_logs"):
           self.log_dir = Path(log_dir)
           self.log_dir.mkdir(exist_ok=True)
           self.current_log = self.log_dir / f"audit_{datetime.now():%Y%m%d}.jsonl"
       
       def log_action(self, action: str, user: str, details: Dict[str, Any]):
           entry = {
               "timestamp": datetime.now().isoformat(),
               "action": action,
               "user": user,
               "details": details
           }
           
           with open(self.current_log, 'a') as f:
               f.write(json.dumps(entry) + '\n')
       
       def get_audit_trail(self, start_date=None, end_date=None, action=None):
           # Query audit logs
           pass
   ```

#### Afternoon (4 hours)
1. **End-to-End Testing**
   ```python
   # tests/test_e2e.py
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app
   
   client = TestClient(app)
   
   def test_onboarding_flow():
       # Test complete onboarding flow
       response = client.post("/api/onboard/repo", json={
           "repo_url": "https://github.com/test/repo",
           "target": "k8s",
           "environments": ["staging", "prod"]
       })
       assert response.status_code == 200
       assert "pr_url" in response.json()
   
   def test_knowledge_base_operations():
       # Test KB connect and search
       response = client.post("/api/kb/connect", json={
           "uri": "https://github.com/test/docs",
           "type": "github"
       })
       assert response.status_code == 200
       
       response = client.get("/api/kb/search?q=deployment")
       assert response.status_code == 200
       assert len(response.json()["results"]) > 0
   ```

2. **Performance Testing**
   ```python
   # tests/test_performance.py
   import time
   import concurrent.futures
   
   def test_knowledge_base_performance():
       start_time = time.time()
       
       # Test concurrent searches
       with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
           futures = [
               executor.submit(kb.search, "deployment", query)
               for query in ["k8s", "docker", "terraform", "helm"]
           ]
           results = [f.result() for f in futures]
       
       elapsed_time = time.time() - start_time
       assert elapsed_time < 2.0  # Should complete in under 2 seconds
   ```

## Deliverables

### By End of Week 1:
1. ✅ Core FastAPI backend running
2. ✅ Chroma vector database configured
3. ✅ Basic CLI with 4 commands (onboard, deploy, kb, incident)
4. ✅ 3 MCP packs implemented (GitHub, Kubernetes, AWS)
5. ✅ 10+ prompt templates integrated
6. ✅ JSONL audit logging functional
7. ✅ SQLite state management ready
8. ✅ Basic authentication and authorization
9. ✅ Docker containerization
10. ✅ Initial test suite

## Success Criteria

### Technical Metrics:
- API response time < 500ms for 95% of requests
- Knowledge base search accuracy > 80%
- CLI command execution < 2 seconds
- Test coverage > 70%
- Zero critical security vulnerabilities

### Functional Metrics:
- Successfully onboard a sample repository
- Execute a dry-run deployment
- Connect and search knowledge base
- Generate audit logs for all actions

## Known Risks & Mitigations

### Risk 1: LLM API Rate Limits
- **Mitigation**: Implement caching, rate limiting, and fallback to local models

### Risk 2: Vector Search Performance
- **Mitigation**: Optimize chunk sizes, implement pagination, use metadata filtering

### Risk 3: MCP Pack Integration Complexity
- **Mitigation**: Start with mock implementations, gradual integration

## Next Phase Preview

Phase 2 will focus on:
- Web UI implementation with React
- Advanced deployment workflows
- Real-time monitoring integration
- Enhanced security features
- User management system

## Team Assignments

### Backend Developer:
- FastAPI setup
- Database models
- API endpoints
- MCP pack integration

### AI/ML Engineer:
- LangChain integration
- Prompt engineering
- Knowledge base implementation
- Vector search optimization

### DevOps Engineer:
- Docker setup
- CI/CD pipeline
- Infrastructure setup
- Monitoring integration

### CLI Developer:
- Typer implementation
- Command structure
- Testing
- Documentation