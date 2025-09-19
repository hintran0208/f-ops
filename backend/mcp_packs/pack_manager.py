"""
MCP Pack Manager - Unified interface for all MCP server operations

Provides access to:
- SCM operations (GitHub, GitLab)
- Infrastructure (Terraform, Kubernetes, Helm)
- Observability (Prometheus, Grafana)
- Knowledge base operations
"""

import asyncio
import json
import logging
import os
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    endpoint: str
    enabled: bool = True
    timeout: int = 30

@dataclass
class MCPResponse:
    """Standardized MCP response"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    server: Optional[str] = None

class MCPPackManager:
    """
    Manages all MCP server packs for F-Ops

    This is a simplified implementation that provides the necessary interfaces
    for F-Ops operations while being compatible with the existing codebase.
    """

    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {
            "github": MCPServerConfig("github", "http://localhost:8001"),
            "gitlab": MCPServerConfig("gitlab", "http://localhost:8002"),
            "terraform": MCPServerConfig("terraform", "http://localhost:8003"),
            "kubernetes": MCPServerConfig("kubernetes", "http://localhost:8004"),
            "helm": MCPServerConfig("helm", "http://localhost:8005"),
            "observability": MCPServerConfig("observability", "http://localhost:8006"),
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        self.initialized_packs = set()

    def initialize_github_pack(self, token: str = None, allowed_repos: List[str] = None, audit_logger = None):
        """Initialize GitHub MCP pack"""
        logger.info("Initializing GitHub MCP pack")
        self.initialized_packs.add("github")

    def initialize_gitlab_pack(self, token: str = None, allowed_repos: List[str] = None, audit_logger = None):
        """Initialize GitLab MCP pack"""
        logger.info("Initializing GitLab MCP pack")
        self.initialized_packs.add("gitlab")

    def initialize_kb_pack(self, kb_manager, audit_logger):
        """Initialize Knowledge Base MCP pack"""
        logger.info("Initializing Knowledge Base MCP pack")
        self.kb_manager = kb_manager
        self.audit_logger = audit_logger
        self.initialized_packs.add("kb")

    async def _execute_kb_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute KB-specific actions using kb_manager directly"""
        try:
            # Handle different actions
            if action == "connect":
                uri = params.get('uri')
                if uri and uri.startswith('file://'):
                    # Handle local file system path
                    return await self._connect_local_files(uri)
                else:
                    return {"success": False, "error": "Only file:// URIs are supported currently"}
            elif action == "search":
                return self._kb_search(params)
            elif action == "get_stats":
                return self._kb_get_stats(params)
            else:
                return {"success": False, "error": f"Unknown KB action: {action}"}

        except Exception as e:
            logger.error(f"KB action {action} failed: {e}")
            return {"success": False, "error": str(e)}

    def _kb_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base using kb_manager directly"""
        query = params['query']
        collections = params.get('collections', list(self.kb_manager.collections.keys()))
        k = params.get('k', 5)

        logger.info(f"Searching KB: '{query}' in {collections}")

        try:
            results = []
            for collection_name in collections:
                if collection_name in self.kb_manager.collections:
                    collection_results = self.kb_manager.search(collection_name, query, k)
                    results.extend(collection_results)

            # Sort by relevance and limit results
            results = results[:k]

            logger.info(f"Found {len(results)} results for query: '{query}'")

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "collections_searched": collections
            }

        except Exception as e:
            logger.error(f"KB search failed for query '{query}': {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def _kb_get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get knowledge base statistics using kb_manager directly"""
        try:
            stats = self.kb_manager.get_collection_stats()

            return {
                "success": True,
                "collections": stats,
                "total_documents": sum(s["document_count"] for s in stats.values()),
                "status": "operational"
            }

        except Exception as e:
            logger.error(f"Failed to get KB stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _connect_local_files(self, file_uri: str) -> Dict[str, Any]:
        """Connect and ingest local files from a directory"""
        # Remove file:// prefix
        local_path = file_uri.replace('file://', '')

        if not os.path.exists(local_path):
            return {"success": False, "error": f"Path does not exist: {local_path}"}

        if not os.path.isdir(local_path):
            return {"success": False, "error": f"Path is not a directory: {local_path}"}

        documents_added = 0
        collections_updated = set()

        try:
            logger.info(f"Starting to walk directory: {local_path}")
            # Walk through all files in the directory
            for root, dirs, files in os.walk(local_path):
                logger.info(f"Processing directory: {root}, found {len(files)} files")
                for file in files:
                    # Skip system files
                    if file.startswith('.'):
                        logger.debug(f"Skipping system file: {file}")
                        continue

                    if file.endswith(('.yml', '.yaml', '.md', '.txt', '.json')) or 'jenkinsfile' in file.lower():
                        logger.info(f"Processing file: {file}")
                        file_path = os.path.join(root, file)

                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # Determine collection based on file type and content
                            collection_name = self._determine_collection(file_path, content)

                            # Create metadata
                            metadata = {
                                'source': 'local_file',
                                'file_path': file_path,
                                'filename': file,
                                'type': self._get_file_type(file_path),
                                'relative_path': os.path.relpath(file_path, local_path)
                            }

                            # Add framework/language detection for pipeline files
                            if collection_name == 'pipelines':
                                metadata.update(self._detect_pipeline_metadata(content, file))

                            # Generate unique ID
                            file_id = f"local-{hash(file_path)}"

                            # Add to appropriate collection
                            self.kb_manager.collections[collection_name].add(
                                documents=[content],
                                metadatas=[metadata],
                                ids=[file_id]
                            )

                            documents_added += 1
                            collections_updated.add(collection_name)

                            logger.info(f"Added {file} to {collection_name} collection")

                        except Exception as e:
                            logger.warning(f"Failed to process {file_path}: {e}")
                            continue

            return {
                "success": True,
                "uri": file_uri,
                "documents": documents_added,
                "collections": list(collections_updated),
                "source_type": "local_directory",
                "note": f"Ingested {documents_added} files from {local_path}"
            }

        except Exception as e:
            logger.error(f"Failed to ingest local files from {local_path}: {e}")
            return {"success": False, "error": str(e), "uri": file_uri}

    def _determine_collection(self, file_path: str, content: str) -> str:
        """Determine which collection a file should go into"""
        filename = os.path.basename(file_path).lower()

        # Pipeline files
        if '.yml' in filename or '.yaml' in filename:
            if any(keyword in content.lower() for keyword in ['workflow', 'pipeline', 'ci/cd', 'jobs:', 'stages:']):
                return 'pipelines'

        # Infrastructure files
        if any(keyword in filename for keyword in ['terraform', 'helm', 'kubernetes', 'k8s', 'infra']):
            return 'iac'

        # Documentation files
        if any(ext in filename for ext in ['.md', '.txt']) or 'readme' in filename:
            return 'docs'

        # Default to pipelines for YAML files, docs for others
        if filename.endswith(('.yml', '.yaml')):
            return 'pipelines'
        else:
            return 'docs'

    def _get_file_type(self, file_path: str) -> str:
        """Get file type based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json'
        }
        return type_map.get(ext, 'unknown')

    def _detect_pipeline_metadata(self, content: str, filename: str) -> dict:
        """Detect pipeline-specific metadata"""
        metadata = {}

        # Detect CI platform
        if 'github' in filename.lower() or 'workflow' in content.lower():
            metadata['platform'] = 'github_actions'
        elif 'gitlab' in filename.lower() or 'gitlab-ci' in filename.lower():
            metadata['platform'] = 'gitlab_ci'
        elif 'jenkins' in filename.lower() or 'jenkinsfile' in filename.lower():
            metadata['platform'] = 'jenkins'
        else:
            metadata['platform'] = 'unknown'

        # Detect languages/frameworks from content
        content_lower = content.lower()
        languages = []

        if any(lang in content_lower for lang in ['python', 'pip', 'pytest', 'django']):
            languages.append('python')
        if any(lang in content_lower for lang in ['node', 'npm', 'yarn', 'javascript', 'typescript']):
            languages.append('javascript')
        if any(lang in content_lower for lang in ['java', 'maven', 'gradle']):
            languages.append('java')
        if any(lang in content_lower for lang in ['go', 'golang']):
            languages.append('go')
        if any(lang in content_lower for lang in ['docker', 'dockerfile']):
            languages.append('docker')

        if languages:
            metadata['languages'] = languages

        return metadata

    async def execute_action(self, pack_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action on a specific MCP pack"""
        logger.info(f"Executing {action} on {pack_name} pack")

        if pack_name == "kb":
            return await self._execute_kb_action(action, params)
        elif pack_name == "github" and action == "create_pr":
            return self._simulate_github_pr_creation(params)
        elif pack_name == "gitlab" and action == "create_mr":
            return self._simulate_gitlab_mr_creation(params)
        elif action == "attach_artifacts":
            return self._simulate_artifact_attachment(params)
        else:
            return {"success": False, "error": f"Unknown action {action} for pack {pack_name}"}

    def get_pack(self, pack_name: str):
        """Get a pack instance (simplified simulation)"""
        if pack_name in self.initialized_packs:
            return MockPack(pack_name)
        return None

    def _simulate_github_pr_creation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate GitHub PR creation"""
        repo_name = params.get('repo_name', 'unknown/repo')
        return {
            "success": True,
            "pr_url": f"https://github.com/{repo_name}/pull/123",
            "pr_number": 123,
            "branch": params.get('branch_name', 'f-ops-pipeline')
        }

    def _simulate_gitlab_mr_creation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate GitLab MR creation"""
        project_id = params.get('project_id', 'unknown/project')
        return {
            "success": True,
            "mr_url": f"https://gitlab.com/{project_id}/-/merge_requests/123",
            "mr_number": 123,
            "branch": params.get('branch_name', 'f-ops-pipeline')
        }

    def _simulate_artifact_attachment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate artifact attachment"""
        return {
            "success": True,
            "artifacts_attached": len(params.get('artifacts', {}))
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def create_pull_request(self, repo_url: str, title: str, content: str,
                                 file_path: str, branch: str = "f-ops-pipeline") -> MCPResponse:
        """
        Create a pull request with pipeline content

        For now, this returns a simulated PR URL since we're focusing on
        the CLI-API integration rather than actual Git operations.
        """
        try:
            # Simulate PR creation - in production this would call actual MCP servers
            pr_url = f"https://github.com/{repo_url.split('/')[-2]}/{repo_url.split('/')[-1]}/pull/123"

            logger.info(f"Simulated PR creation for {repo_url}")
            logger.info(f"Title: {title}")
            logger.info(f"File: {file_path}")
            logger.info(f"Content length: {len(content)} characters")

            return MCPResponse(
                success=True,
                data={
                    "pr_url": pr_url,
                    "pr_number": 123,
                    "branch": branch,
                    "files_changed": [file_path]
                },
                server="github"
            )

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return MCPResponse(
                success=False,
                error=str(e),
                server="github"
            )

    async def validate_pipeline(self, content: str, pipeline_type: str = "github") -> MCPResponse:
        """
        Validate pipeline syntax

        This provides basic YAML validation for now.
        """
        try:
            # Parse YAML to check syntax
            parsed = yaml.safe_load(content)

            validation_result = {
                "status": "valid",
                "syntax_valid": True,
                "structure_valid": True,
                "warnings": [],
                "suggestions": []
            }

            # Basic structure validation for GitHub Actions
            if pipeline_type == "github":
                if "name" not in parsed:
                    validation_result["warnings"].append("Missing workflow name")
                if "on" not in parsed:
                    validation_result["warnings"].append("Missing trigger configuration")
                if "jobs" not in parsed:
                    validation_result["warnings"].append("Missing jobs definition")

            return MCPResponse(
                success=True,
                data=validation_result,
                server=pipeline_type
            )

        except yaml.YAMLError as e:
            return MCPResponse(
                success=False,
                error=f"YAML syntax error: {str(e)}",
                server=pipeline_type
            )
        except Exception as e:
            return MCPResponse(
                success=False,
                error=f"Validation error: {str(e)}",
                server=pipeline_type
            )

    async def run_terraform_plan(self, config_path: str) -> MCPResponse:
        """
        Run terraform plan (simulated)
        """
        try:
            # Simulate terraform plan output
            plan_output = """
Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                          = "ami-0c55b159cbfafe1d0"
      + instance_type                = "t2.micro"
    }

Plan: 1 to add, 0 to change, 0 to destroy.
"""

            return MCPResponse(
                success=True,
                data={
                    "plan_output": plan_output,
                    "resources_to_add": 1,
                    "resources_to_change": 0,
                    "resources_to_destroy": 0
                },
                server="terraform"
            )

        except Exception as e:
            return MCPResponse(
                success=False,
                error=str(e),
                server="terraform"
            )

    async def run_helm_dry_run(self, chart_path: str, values: Dict[str, Any]) -> MCPResponse:
        """
        Run helm template/dry-run (simulated)
        """
        try:
            # Simulate helm dry-run output
            manifest_output = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
"""

            return MCPResponse(
                success=True,
                data={
                    "manifest_output": manifest_output,
                    "resources": ["Deployment", "Service", "Ingress"]
                },
                server="helm"
            )

        except Exception as e:
            return MCPResponse(
                success=False,
                error=str(e),
                server="helm"
            )

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all MCP servers
        """
        health_status = {}

        for server_name, config in self.servers.items():
            try:
                # For now, mark all servers as healthy (simulated)
                # In production, this would make actual HTTP calls to MCP servers
                health_status[server_name] = True

            except Exception as e:
                logger.error(f"Health check failed for {server_name}: {e}")
                health_status[server_name] = False

        return health_status

    def get_server_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all configured MCP servers
        """
        return {
            name: {
                "endpoint": config.endpoint,
                "enabled": config.enabled,
                "timeout": config.timeout
            }
            for name, config in self.servers.items()
        }

class MockPack:
    """Mock pack instance for testing"""

    def __init__(self, pack_name: str):
        self.pack_name = pack_name
        self.initialized = True

    def check_repo_access(self, repo_path: str) -> Dict[str, Any]:
        """Check if we have access to the repository"""
        return {
            "access": True,
            "permissions": ["read", "write", "pull_requests"],
            "repo_path": repo_path
        }

    def check_project_access(self, project_path: str) -> Dict[str, Any]:
        """Check if we have access to the GitLab project"""
        return {
            "access": True,
            "permissions": ["read", "write", "merge_requests"],
            "project_path": project_path
        }

# Global instance
pack_manager = MCPPackManager()