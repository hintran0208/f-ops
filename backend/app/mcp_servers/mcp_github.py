from github import Github
from typing import Dict, Any, List
from app.config import settings
from app.core.audit_logger import AuditLogger
import logging

logger = logging.getLogger(__name__)

class MCPGitHub:
    """MCP GitHub server for typed PR creation and workflow management"""

    def __init__(self, token: str = None, allowed_repos: List[str] = None, audit_logger: AuditLogger = None):
        self.token = token or settings.MCP_GITHUB_TOKEN
        self.client = Github(self.token) if self.token else None
        self.allowed_repos = allowed_repos or settings.ALLOWED_REPOS
        self.audit_logger = audit_logger

        if not self.client:
            logger.warning("GitHub MCP server initialized without token - limited functionality")

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

    def create_pr(self, params: Dict[str, Any]) -> str:
        """Create PR with typed interface (no shell execution)"""
        if not self.client:
            raise ValueError("GitHub token not configured")

        self.validate_repo(params['repo_url'])

        try:
            # Parse repo info
            repo_path = params['repo_name']  # format: "owner/repo"
            repo = self.client.get_repo(repo_path)

            # Create branch
            base_branch = repo.get_branch(params.get('base_branch', 'main'))
            branch_name = params['branch_name']

            # Check if branch already exists
            try:
                repo.get_branch(branch_name)
                logger.warning(f"Branch {branch_name} already exists")
            except:
                # Create new branch
                repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=base_branch.commit.sha
                )
                logger.info(f"Created branch: {branch_name}")

            # Add/update files
            for file_path, content in params['files'].items():
                try:
                    # Try to get existing file
                    existing_file = repo.get_contents(file_path, ref=branch_name)
                    repo.update_file(
                        path=file_path,
                        message=f"Update {file_path}",
                        content=content,
                        sha=existing_file.sha,
                        branch=branch_name
                    )
                    logger.info(f"Updated file: {file_path}")
                except:
                    # Create new file
                    repo.create_file(
                        path=file_path,
                        message=f"Add {file_path}",
                        content=content,
                        branch=branch_name
                    )
                    logger.info(f"Created file: {file_path}")

            # Create PR
            pr = repo.create_pull(
                title=params['title'],
                body=params['body'],
                head=branch_name,
                base=params.get('base_branch', 'main')
            )

            pr_url = pr.html_url
            logger.info(f"PR created: {pr_url}")

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_pr_creation(
                    repo_url=params['repo_url'],
                    pr_url=pr_url,
                    agent="mcp_github",
                    files=params['files']
                )

            return pr_url

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            raise

    def attach_artifacts(self, pr_url: str, artifacts: Dict[str, Any]) -> bool:
        """Attach dry-run/plan artifacts to PR as comment"""
        if not self.client:
            raise ValueError("GitHub token not configured")

        try:
            # Parse PR URL to get repo and PR number
            import re
            match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
            if not match:
                raise ValueError("Invalid GitHub PR URL")

            owner, repo_name, pr_number = match.groups()
            repo = self.client.get_repo(f"{owner}/{repo_name}")
            pr = repo.get_pull(int(pr_number))

            # Format artifacts as markdown comment
            comment_body = "## F-Ops Dry-Run Artifacts\n\n"

            for artifact_type, content in artifacts.items():
                comment_body += f"### {artifact_type.title()}\n\n"
                comment_body += "```\n"
                comment_body += str(content)
                comment_body += "\n```\n\n"

            comment_body += "---\n*Generated by F-Ops Pipeline Agent*"

            # Add comment to PR
            pr.create_issue_comment(comment_body)
            logger.info(f"Artifacts attached to PR: {pr_url}")

            return True

        except Exception as e:
            logger.error(f"Failed to attach artifacts to PR {pr_url}: {e}")
            raise

    def get_workflow_logs(self, repo_path: str, workflow_run_id: int) -> str:
        """Fetch workflow logs for debugging"""
        if not self.client:
            raise ValueError("GitHub token not configured")

        try:
            repo = self.client.get_repo(repo_path)
            workflow_run = repo.get_workflow_run(workflow_run_id)

            # Get logs URL (this would require additional API calls for full implementation)
            logs_info = {
                "workflow_run_id": workflow_run_id,
                "status": workflow_run.status,
                "conclusion": workflow_run.conclusion,
                "url": workflow_run.html_url,
                "created_at": workflow_run.created_at.isoformat()
            }

            return f"Workflow Run Info: {logs_info}"

        except Exception as e:
            logger.error(f"Failed to get workflow logs: {e}")
            raise

    def check_repo_access(self, repo_path: str) -> Dict[str, Any]:
        """Check if we have access to repository"""
        if not self.client:
            return {"access": False, "reason": "No GitHub token configured"}

        try:
            repo = self.client.get_repo(repo_path)
            permissions = repo.permissions

            return {
                "access": True,
                "repo": repo_path,
                "permissions": {
                    "admin": permissions.admin,
                    "push": permissions.push,
                    "pull": permissions.pull
                },
                "private": repo.private
            }

        except Exception as e:
            return {
                "access": False,
                "repo": repo_path,
                "reason": str(e)
            }