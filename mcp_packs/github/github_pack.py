from github import Github
from github.GithubException import GithubException
from mcp_packs.base.mcp_pack import MCPPack
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class GitHubPack(MCPPack):
    """GitHub MCP Pack for repository and CI/CD operations"""

    def validate_config(self):
        """Validate GitHub configuration"""
        if 'token' not in self.config:
            raise ValueError("GitHub token is required in configuration")

        if not self.config['token']:
            raise ValueError("GitHub token cannot be empty")

    def initialize(self):
        """Initialize GitHub client"""
        try:
            self.client = Github(self.config['token'])
            # Test connection
            self.user = self.client.get_user()
            self.audit_logger = self.config.get('audit_logger')
            self.allowed_repos = self.config.get('allowed_repos', [])
            logger.info(f"GitHub Pack initialized for user: {self.user.login}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise
    
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GitHub action"""
        actions = {
            'create_pr': self.create_pr,
            'get_workflows': self.get_workflows,
            'trigger_workflow': self.trigger_workflow,
            'get_repository_info': self.get_repository_info,
            'get_branches': self.get_branches,
            'get_commits': self.get_commits,
            'create_issue': self.create_issue,
            'get_pull_requests': self.get_pull_requests,
            'merge_pr': self.merge_pr,
            'create_release': self.create_release,
            'attach_artifacts': self.attach_artifacts
        }
        
        if action not in actions:
            raise ValueError(f"Unknown action: {action}")
        
        return actions[action](params)
    
    def get_available_actions(self) -> List[str]:
        """Return list of available GitHub actions"""
        return [
            'create_pr',
            'get_workflows',
            'trigger_workflow',
            'get_repository_info',
            'get_branches',
            'get_commits',
            'create_issue',
            'get_pull_requests',
            'merge_pr',
            'create_release',
            'attach_artifacts'
        ]
    
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

    def create_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request"""
        try:
            # Validate repository if repo_url is provided
            if 'repo_url' in params:
                self.validate_repo(params['repo_url'])

            # Support both repository name and repo_url
            repo_name = params.get('repository') or params.get('repo_name')
            if not repo_name:
                raise ValueError("Either 'repository' or 'repo_name' parameter is required")

            repo = self.client.get_repo(repo_name)

            # Create branch if branch_name is provided
            if 'branch_name' in params:
                try:
                    base_branch = repo.get_branch(params.get('base_branch', 'main'))
                    repo.create_git_ref(
                        ref=f"refs/heads/{params['branch_name']}",
                        sha=base_branch.commit.sha
                    )
                except GithubException:
                    # Branch might already exist
                    pass

                # Add files if provided
                if 'files' in params:
                    for file_path, content in params['files'].items():
                        try:
                            # Try to get existing file
                            existing_file = repo.get_contents(file_path, ref=params['branch_name'])
                            repo.update_file(
                                path=file_path,
                                message=f"Update {file_path}",
                                content=content,
                                sha=existing_file.sha,
                                branch=params['branch_name']
                            )
                        except GithubException:
                            # Create new file
                            repo.create_file(
                                path=file_path,
                                message=f"Add {file_path}",
                                content=content,
                                branch=params['branch_name']
                            )

            # Create PR
            head_branch = params.get('branch_name') or params.get('head_branch')
            if not head_branch:
                raise ValueError("Either 'branch_name' or 'head_branch' parameter is required")

            pr = repo.create_pull(
                title=params['title'],
                body=params.get('body', ''),
                head=head_branch,
                base=params.get('base_branch', 'main'),
                draft=params.get('draft', False)
            )

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_pr_creation(
                    repo_url=params.get('repo_url', f"https://github.com/{repo_name}"),
                    pr_url=pr.html_url,
                    agent="mcp_github",
                    files=params.get('files', {})
                )

            return {
                'success': True,
                'pr_number': pr.number,
                'pr_url': pr.html_url,
                'state': pr.state
            }
        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_workflows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get GitHub Actions workflows for a repository"""
        try:
            repo = self.client.get_repo(params['repository'])
            workflows = repo.get_workflows()
            
            workflow_list = []
            for workflow in workflows:
                workflow_list.append({
                    'id': workflow.id,
                    'name': workflow.name,
                    'path': workflow.path,
                    'state': workflow.state
                })
            
            return {
                'success': True,
                'workflows': workflow_list
            }
        except GithubException as e:
            logger.error(f"Failed to get workflows: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow"""
        try:
            repo = self.client.get_repo(params['repository'])
            workflow = repo.get_workflow(params['workflow_id'])
            
            # Create workflow dispatch event
            success = workflow.create_dispatch(
                ref=params.get('ref', 'main'),
                inputs=params.get('inputs', {})
            )
            
            return {
                'success': success,
                'workflow_name': workflow.name,
                'message': 'Workflow triggered successfully' if success else 'Failed to trigger workflow'
            }
        except GithubException as e:
            logger.error(f"Failed to trigger workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_repository_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository information"""
        try:
            repo = self.client.get_repo(params['repository'])
            
            return {
                'success': True,
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'default_branch': repo.default_branch,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat(),
                'topics': repo.get_topics()
            }
        except GithubException as e:
            logger.error(f"Failed to get repository info: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_branches(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository branches"""
        try:
            repo = self.client.get_repo(params['repository'])
            branches = repo.get_branches()
            
            branch_list = []
            for branch in branches:
                branch_list.append({
                    'name': branch.name,
                    'commit_sha': branch.commit.sha,
                    'protected': branch.protected
                })
            
            return {
                'success': True,
                'branches': branch_list,
                'default_branch': repo.default_branch
            }
        except GithubException as e:
            logger.error(f"Failed to get branches: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_commits(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository commits"""
        try:
            repo = self.client.get_repo(params['repository'])
            commits = repo.get_commits(
                sha=params.get('branch', repo.default_branch)
            )[:params.get('limit', 10)]
            
            commit_list = []
            for commit in commits:
                commit_list.append({
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date.isoformat()
                })
            
            return {
                'success': True,
                'commits': commit_list
            }
        except GithubException as e:
            logger.error(f"Failed to get commits: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue"""
        try:
            repo = self.client.get_repo(params['repository'])
            
            issue = repo.create_issue(
                title=params['title'],
                body=params.get('body', ''),
                labels=params.get('labels', []),
                assignees=params.get('assignees', [])
            )
            
            return {
                'success': True,
                'issue_number': issue.number,
                'issue_url': issue.html_url,
                'state': issue.state
            }
        except GithubException as e:
            logger.error(f"Failed to create issue: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pull_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get pull requests for a repository"""
        try:
            repo = self.client.get_repo(params['repository'])
            state = params.get('state', 'open')
            prs = repo.get_pulls(state=state)[:params.get('limit', 10)]
            
            pr_list = []
            for pr in prs:
                pr_list.append({
                    'number': pr.number,
                    'title': pr.title,
                    'state': pr.state,
                    'author': pr.user.login,
                    'created_at': pr.created_at.isoformat(),
                    'html_url': pr.html_url
                })
            
            return {
                'success': True,
                'pull_requests': pr_list
            }
        except GithubException as e:
            logger.error(f"Failed to get pull requests: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def merge_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a pull request"""
        try:
            repo = self.client.get_repo(params['repository'])
            pr = repo.get_pull(params['pr_number'])
            
            if not pr.mergeable:
                return {
                    'success': False,
                    'error': 'Pull request is not mergeable'
                }
            
            merge_result = pr.merge(
                commit_message=params.get('commit_message', f"Merge PR #{pr.number}"),
                merge_method=params.get('merge_method', 'merge')  # merge, squash, or rebase
            )
            
            return {
                'success': merge_result.merged,
                'message': merge_result.message,
                'sha': merge_result.sha if merge_result.merged else None
            }
        except GithubException as e:
            logger.error(f"Failed to merge PR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_release(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub release"""
        try:
            repo = self.client.get_repo(params['repository'])
            
            release = repo.create_git_release(
                tag=params['tag'],
                name=params.get('name', params['tag']),
                message=params.get('body', ''),
                draft=params.get('draft', False),
                prerelease=params.get('prerelease', False),
                target_commitish=params.get('target_commitish', repo.default_branch)
            )
            
            return {
                'success': True,
                'release_id': release.id,
                'tag_name': release.tag_name,
                'html_url': release.html_url,
                'created_at': release.created_at.isoformat()
            }
        except GithubException as e:
            logger.error(f"Failed to create release: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check GitHub connection health"""
        try:
            # Try to get user info as health check
            user = self.client.get_user()
            rate_limit = self.client.get_rate_limit()
            
            return {
                'name': self.name,
                'status': 'healthy',
                'user': user.login,
                'rate_limit': {
                    'remaining': rate_limit.core.remaining,
                    'limit': rate_limit.core.limit,
                    'reset': rate_limit.core.reset.isoformat()
                }
            }
        except Exception as e:
            return {
                'name': self.name,
                'status': 'unhealthy',
                'error': str(e)
            }

    def attach_artifacts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Attach dry-run/plan artifacts to PR as comment"""
        try:
            pr_url = params['pr_url']
            artifacts = params['artifacts']

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

            return {
                'success': True,
                'message': 'Artifacts attached successfully'
            }

        except Exception as e:
            logger.error(f"Failed to attach artifacts to PR: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def check_repo_access(self, repo_path: str) -> Dict[str, Any]:
        """Check if we have access to repository"""
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