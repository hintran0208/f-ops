import gitlab
from gitlab.exceptions import GitlabError
from mcp_packs.base.mcp_pack import MCPPack
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class GitLabPack(MCPPack):
    """GitLab MCP Pack for repository and CI/CD operations"""

    def validate_config(self):
        """Validate GitLab configuration"""
        if 'token' not in self.config:
            raise ValueError("GitLab token is required in configuration")

        if not self.config['token']:
            raise ValueError("GitLab token cannot be empty")

    def initialize(self):
        """Initialize GitLab client"""
        try:
            self.client = gitlab.Gitlab('https://gitlab.com', private_token=self.config['token'])
            self.client.auth()
            self.user = self.client.user
            self.audit_logger = self.config.get('audit_logger')
            self.allowed_repos = self.config.get('allowed_repos', [])
            logger.info(f"GitLab Pack initialized for user: {self.user.username}")
        except Exception as e:
            logger.error(f"Failed to initialize GitLab client: {e}")
            raise

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GitLab action"""
        actions = {
            'create_mr': self.create_mr,
            'get_pipelines': self.get_pipelines,
            'trigger_pipeline': self.trigger_pipeline,
            'get_project_info': self.get_project_info,
            'get_branches': self.get_branches,
            'get_commits': self.get_commits,
            'create_issue': self.create_issue,
            'get_merge_requests': self.get_merge_requests,
            'merge_mr': self.merge_mr,
            'create_release': self.create_release,
            'attach_artifacts': self.attach_artifacts
        }

        if action not in actions:
            raise ValueError(f"Unknown action: {action}")

        return actions[action](params)

    def get_available_actions(self) -> List[str]:
        """Return list of available GitLab actions"""
        return [
            'create_mr',
            'get_pipelines',
            'trigger_pipeline',
            'get_project_info',
            'get_branches',
            'get_commits',
            'create_issue',
            'get_merge_requests',
            'merge_mr',
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

    def create_mr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a merge request"""
        try:
            self.validate_repo(params['repo_url'])

            project_path = params['project_id']
            project = self.client.projects.get(project_path, lazy=True)

            # Create branch
            branch_data = {
                'branch': params['branch_name'],
                'ref': params.get('base_branch', 'main')
            }
            branch = project.branches.create(branch_data)

            # Add/update files
            for file_path, content in params['files'].items():
                try:
                    # Try to get existing file
                    existing_file = project.files.get(file_path, ref=params['branch_name'])
                    existing_file.content = content
                    existing_file.save(branch=params['branch_name'], commit_message=f"Update {file_path}")
                except GitlabError:
                    # Create new file
                    file_data = {
                        'file_path': file_path,
                        'branch': params['branch_name'],
                        'content': content,
                        'commit_message': f"Add {file_path}"
                    }
                    project.files.create(file_data)

            # Create MR
            mr_data = {
                'source_branch': params['branch_name'],
                'target_branch': params.get('base_branch', 'main'),
                'title': params['title'],
                'description': params.get('body', '')
            }
            mr = project.mergerequests.create(mr_data)

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_pr_creation(
                    repo_url=params['repo_url'],
                    pr_url=mr.web_url,
                    agent="mcp_gitlab",
                    files=params['files']
                )

            return {
                'success': True,
                'mr_iid': mr.iid,
                'mr_url': mr.web_url,
                'state': mr.state
            }

        except GitlabError as e:
            logger.error(f"Failed to create MR: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_pipelines(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get GitLab CI pipelines for a project"""
        try:
            project = self.client.projects.get(params['project_id'])
            pipelines = project.pipelines.list(per_page=params.get('limit', 10))

            pipeline_list = []
            for pipeline in pipelines:
                pipeline_list.append({
                    'id': pipeline.id,
                    'status': pipeline.status,
                    'ref': pipeline.ref,
                    'sha': pipeline.sha,
                    'created_at': pipeline.created_at,
                    'web_url': pipeline.web_url
                })

            return {
                'success': True,
                'pipelines': pipeline_list
            }

        except GitlabError as e:
            logger.error(f"Failed to get pipelines: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def trigger_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a GitLab CI pipeline"""
        try:
            project = self.client.projects.get(params['project_id'])

            pipeline_data = {
                'ref': params.get('ref', 'main'),
                'variables': params.get('variables', [])
            }
            pipeline = project.pipelines.create(pipeline_data)

            return {
                'success': True,
                'pipeline_id': pipeline.id,
                'pipeline_url': pipeline.web_url,
                'status': pipeline.status
            }

        except GitlabError as e:
            logger.error(f"Failed to trigger pipeline: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_project_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get project information"""
        try:
            project = self.client.projects.get(params['project_id'])

            return {
                'success': True,
                'name': project.name,
                'path_with_namespace': project.path_with_namespace,
                'description': project.description,
                'default_branch': project.default_branch,
                'stars': project.star_count,
                'forks': project.forks_count,
                'issues_enabled': project.issues_enabled,
                'created_at': project.created_at,
                'last_activity_at': project.last_activity_at,
                'web_url': project.web_url
            }

        except GitlabError as e:
            logger.error(f"Failed to get project info: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_branches(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get project branches"""
        try:
            project = self.client.projects.get(params['project_id'])
            branches = project.branches.list(per_page=params.get('limit', 20))

            branch_list = []
            for branch in branches:
                branch_list.append({
                    'name': branch.name,
                    'commit_id': branch.commit['id'],
                    'protected': branch.protected,
                    'merged': getattr(branch, 'merged', False)
                })

            return {
                'success': True,
                'branches': branch_list,
                'default_branch': project.default_branch
            }

        except GitlabError as e:
            logger.error(f"Failed to get branches: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_commits(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get project commits"""
        try:
            project = self.client.projects.get(params['project_id'])
            commits = project.commits.list(
                ref_name=params.get('branch', project.default_branch),
                per_page=params.get('limit', 10)
            )

            commit_list = []
            for commit in commits:
                commit_list.append({
                    'id': commit.id,
                    'short_id': commit.short_id,
                    'message': commit.message,
                    'author_name': commit.author_name,
                    'created_at': commit.created_at
                })

            return {
                'success': True,
                'commits': commit_list
            }

        except GitlabError as e:
            logger.error(f"Failed to get commits: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitLab issue"""
        try:
            project = self.client.projects.get(params['project_id'])

            issue_data = {
                'title': params['title'],
                'description': params.get('description', ''),
                'labels': params.get('labels', []),
                'assignee_ids': params.get('assignee_ids', [])
            }
            issue = project.issues.create(issue_data)

            return {
                'success': True,
                'issue_iid': issue.iid,
                'issue_url': issue.web_url,
                'state': issue.state
            }

        except GitlabError as e:
            logger.error(f"Failed to create issue: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_merge_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get merge requests for a project"""
        try:
            project = self.client.projects.get(params['project_id'])
            state = params.get('state', 'opened')
            mrs = project.mergerequests.list(
                state=state,
                per_page=params.get('limit', 10)
            )

            mr_list = []
            for mr in mrs:
                mr_list.append({
                    'iid': mr.iid,
                    'title': mr.title,
                    'state': mr.state,
                    'author': mr.author['name'],
                    'created_at': mr.created_at,
                    'web_url': mr.web_url
                })

            return {
                'success': True,
                'merge_requests': mr_list
            }

        except GitlabError as e:
            logger.error(f"Failed to get merge requests: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def merge_mr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a merge request"""
        try:
            project = self.client.projects.get(params['project_id'])
            mr = project.mergerequests.get(params['mr_iid'])

            if mr.merge_status != 'can_be_merged':
                return {
                    'success': False,
                    'error': f'MR cannot be merged: {mr.merge_status}'
                }

            merge_result = mr.merge(
                merge_commit_message=params.get('merge_commit_message', f"Merge MR !{mr.iid}"),
                should_remove_source_branch=params.get('remove_source_branch', False)
            )

            return {
                'success': True,
                'merged': True,
                'merge_commit_sha': merge_result.get('sha'),
                'message': 'Merge request merged successfully'
            }

        except GitlabError as e:
            logger.error(f"Failed to merge MR: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_release(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitLab release"""
        try:
            project = self.client.projects.get(params['project_id'])

            release_data = {
                'tag_name': params['tag_name'],
                'name': params.get('name', params['tag_name']),
                'description': params.get('description', ''),
                'ref': params.get('ref', project.default_branch)
            }
            release = project.releases.create(release_data)

            return {
                'success': True,
                'tag_name': release.tag_name,
                'name': release.name,
                'created_at': release.created_at,
                '_links': release._links
            }

        except GitlabError as e:
            logger.error(f"Failed to create release: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def attach_artifacts(self, pr_url: str, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """Attach dry-run/plan artifacts to MR as note"""
        try:
            # Parse MR URL to get project and MR IID
            import re
            match = re.search(r'gitlab\.com/([^/]+/[^/]+)/-/merge_requests/(\d+)', pr_url)
            if not match:
                raise ValueError("Invalid GitLab MR URL")

            project_path, mr_iid = match.groups()
            project = self.client.projects.get(project_path, lazy=True)
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
            note_data = {'body': note_body}
            mr.notes.create(note_data)

            logger.info(f"Artifacts attached to MR: {pr_url}")

            return {
                'success': True,
                'message': 'Artifacts attached successfully'
            }

        except Exception as e:
            logger.error(f"Failed to attach artifacts to MR {pr_url}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def check_project_access(self, project_path: str) -> Dict[str, Any]:
        """Check if we have access to project"""
        try:
            project = self.client.projects.get(project_path)

            return {
                "access": True,
                "project": project_path,
                "permissions": {
                    "guest": project.permissions.get('project_access', {}).get('access_level', 0) >= 10,
                    "developer": project.permissions.get('project_access', {}).get('access_level', 0) >= 30,
                    "maintainer": project.permissions.get('project_access', {}).get('access_level', 0) >= 40
                },
                "visibility": project.visibility
            }

        except Exception as e:
            return {
                "access": False,
                "project": project_path,
                "reason": str(e)
            }

    def health_check(self) -> Dict[str, Any]:
        """Check GitLab connection health"""
        try:
            # Try to get user info as health check
            user = self.client.user
            projects = self.client.projects.list(owned=True, per_page=1)

            return {
                'name': self.name,
                'status': 'healthy',
                'user': user.username,
                'user_id': user.id,
                'projects_accessible': len(projects)
            }
        except Exception as e:
            return {
                'name': self.name,
                'status': 'unhealthy',
                'error': str(e)
            }