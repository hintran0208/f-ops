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
            'create_release': self.create_release
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
            'create_release'
        ]
    
    def create_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request"""
        try:
            repo = self.client.get_repo(params['repository'])
            
            pr = repo.create_pull(
                title=params['title'],
                body=params.get('body', ''),
                head=params['head_branch'],
                base=params.get('base_branch', 'main'),
                draft=params.get('draft', False)
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