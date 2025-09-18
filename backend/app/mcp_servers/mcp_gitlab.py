import gitlab
from typing import Dict, Any, List
from app.config import settings
from app.core.audit_logger import AuditLogger
import logging

logger = logging.getLogger(__name__)

class MCPGitLab:
    """MCP GitLab server for typed MR creation and pipeline management"""

    def __init__(self, token: str = None, allowed_repos: List[str] = None, audit_logger: AuditLogger = None):
        self.token = token or settings.MCP_GITLAB_TOKEN
        self.client = gitlab.Gitlab('https://gitlab.com', private_token=self.token) if self.token else None
        self.allowed_repos = allowed_repos or settings.ALLOWED_REPOS
        self.audit_logger = audit_logger

        if not self.client:
            logger.warning("GitLab MCP server initialized without token - limited functionality")

    def validate_repo(self, repo_url: str) -> bool:
        """Check if repo is allow-listed"""
        if not self.allowed_repos:
            logger.warning("No allow-listed repos configured - allowing all")
            return True

        is_allowed = any(allowed in repo_url for allowed in self.allowed_repos)
        if not is_allowed:
            logger.error(f"Repository not allow-listed: {repo_url}")
            raise ValueError(f"Repository not allow-listed: {repo_url}")

        return True

    def create_mr(self, params: Dict[str, Any]) -> str:
        """Create GitLab MR with typed interface"""
        if not self.client:
            raise ValueError("GitLab token not configured")

        self.validate_repo(params['repo_url'])

        try:
            # Get project
            project_id = params['project_id']
            project = self.client.projects.get(project_id)

            # Create branch
            branch_name = params['branch_name']
            base_branch = params.get('base_branch', 'main')

            try:
                branch = project.branches.create({
                    'branch': branch_name,
                    'ref': base_branch
                })
                logger.info(f"Created branch: {branch_name}")
            except gitlab.exceptions.GitlabCreateError as e:
                if "already exists" in str(e):
                    logger.warning(f"Branch {branch_name} already exists")
                else:
                    raise

            # Add/update files
            for file_path, content in params['files'].items():
                try:
                    # Try to get existing file
                    existing_file = project.files.get(file_path=file_path, ref=branch_name)
                    existing_file.content = content
                    existing_file.save(branch=branch_name, commit_message=f"Update {file_path}")
                    logger.info(f"Updated file: {file_path}")
                except gitlab.exceptions.GitlabGetError:
                    # Create new file
                    project.files.create({
                        'file_path': file_path,
                        'branch': branch_name,
                        'content': content,
                        'commit_message': f"Add {file_path}"
                    })
                    logger.info(f"Created file: {file_path}")

            # Create MR
            mr = project.mergerequests.create({
                'source_branch': branch_name,
                'target_branch': base_branch,
                'title': params['title'],
                'description': params['body']
            })

            mr_url = mr.web_url
            logger.info(f"MR created: {mr_url}")

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_pr_creation(
                    repo_url=params['repo_url'],
                    pr_url=mr_url,
                    agent="mcp_gitlab",
                    files=params['files']
                )

            return mr_url

        except Exception as e:
            logger.error(f"Failed to create MR: {e}")
            raise

    def attach_artifacts(self, mr_url: str, artifacts: Dict[str, Any]) -> bool:
        """Attach dry-run/plan artifacts to MR as note"""
        if not self.client:
            raise ValueError("GitLab token not configured")

        try:
            # Parse MR URL to get project and MR IID
            import re
            match = re.search(r'gitlab\.com/([^/]+)/([^/]+)/-/merge_requests/(\d+)', mr_url)
            if not match:
                raise ValueError("Invalid GitLab MR URL")

            owner, repo_name, mr_iid = match.groups()
            project = self.client.projects.get(f"{owner}/{repo_name}")
            mr = project.mergerequests.get(int(mr_iid))

            # Format artifacts as markdown note
            note_body = "## F-Ops Dry-Run Artifacts\n\n"

            for artifact_type, content in artifacts.items():
                note_body += f"### {artifact_type.title()}\n\n"
                note_body += "```\n"
                note_body += str(content)
                note_body += "\n```\n\n"

            note_body += "---\n*Generated by F-Ops Pipeline Agent*"

            # Add note to MR
            mr.notes.create({'body': note_body})
            logger.info(f"Artifacts attached to MR: {mr_url}")

            return True

        except Exception as e:
            logger.error(f"Failed to attach artifacts to MR {mr_url}: {e}")
            raise

    def get_pipeline_logs(self, project_id: str, pipeline_id: int) -> str:
        """Fetch pipeline logs for debugging"""
        if not self.client:
            raise ValueError("GitLab token not configured")

        try:
            project = self.client.projects.get(project_id)
            pipeline = project.pipelines.get(pipeline_id)

            # Get pipeline info
            pipeline_info = {
                "pipeline_id": pipeline_id,
                "status": pipeline.status,
                "ref": pipeline.ref,
                "web_url": pipeline.web_url,
                "created_at": pipeline.created_at
            }

            return f"Pipeline Info: {pipeline_info}"

        except Exception as e:
            logger.error(f"Failed to get pipeline logs: {e}")
            raise

    def check_project_access(self, project_path: str) -> Dict[str, Any]:
        """Check if we have access to project"""
        if not self.client:
            return {"access": False, "reason": "No GitLab token configured"}

        try:
            project = self.client.projects.get(project_path)

            return {
                "access": True,
                "project": project_path,
                "permissions": {
                    "access_level": project.permissions.get('project_access', {}).get('access_level', 0),
                    "can_push": project.permissions.get('project_access', {}).get('access_level', 0) >= 30
                },
                "visibility": project.visibility
            }

        except Exception as e:
            return {
                "access": False,
                "project": project_path,
                "reason": str(e)
            }