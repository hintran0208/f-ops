from typing import Dict, Any, List, Optional
import subprocess
import tempfile
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPTerraform:
    """MCP Server for Terraform operations with typed interfaces"""

    def __init__(self, allowed_workspaces: List[str], allowed_providers: List[str] = None):
        self.allowed_workspaces = allowed_workspaces or ["staging", "prod", "dev"]
        self.allowed_providers = allowed_providers or ["aws", "azure", "gcp"]

    def plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run terraform plan with typed interface"""
        try:
            # Validate parameters
            workspace = params.get('workspace', 'default')
            self.validate_workspace(workspace)

            config = params.get('config', {})
            variables = params.get('variables', {})
            backend_config = params.get('backend_config', {})

            if not config:
                raise ValueError("Terraform configuration is required")

            with tempfile.TemporaryDirectory() as tmpdir:
                # Write configuration files
                for path, content in config.items():
                    file_path = os.path.join(tmpdir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                # Write variables file if provided
                if variables:
                    vars_file = os.path.join(tmpdir, 'terraform.tfvars.json')
                    with open(vars_file, 'w') as f:
                        json.dump(variables, f, indent=2)

                # Write backend configuration if provided
                if backend_config:
                    backend_file = os.path.join(tmpdir, 'backend.tf')
                    with open(backend_file, 'w') as f:
                        f.write(self._generate_backend_config(backend_config))

                # Initialize terraform
                init_result = self._run_terraform_init(tmpdir, backend_config)
                if init_result['status'] != 'success':
                    return init_result

                # Run terraform plan
                plan_result = self._run_terraform_plan(tmpdir, workspace)

                return plan_result

        except Exception as e:
            logger.error(f"Terraform plan failed: {e}")
            return {
                "status": "failed",
                "stage": "validation",
                "error": str(e),
                "plan": None,
                "summary": self._empty_summary()
            }

    def validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate terraform configuration"""
        try:
            config = params.get('config', {})
            if not config:
                raise ValueError("Terraform configuration is required")

            with tempfile.TemporaryDirectory() as tmpdir:
                # Write configuration files
                for path, content in config.items():
                    file_path = os.path.join(tmpdir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                # Run terraform validate
                validate_result = subprocess.run(
                    ['terraform', 'validate', '-json'],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if validate_result.returncode == 0:
                    return {
                        "status": "valid",
                        "output": validate_result.stdout,
                        "errors": []
                    }
                else:
                    try:
                        error_data = json.loads(validate_result.stdout)
                        return {
                            "status": "invalid",
                            "output": validate_result.stdout,
                            "errors": error_data.get('diagnostics', [])
                        }
                    except json.JSONDecodeError:
                        return {
                            "status": "invalid",
                            "output": validate_result.stdout,
                            "errors": [{"summary": validate_result.stderr}]
                        }

        except Exception as e:
            logger.error(f"Terraform validation failed: {e}")
            return {
                "status": "error",
                "output": "",
                "errors": [{"summary": str(e)}]
            }

    def format_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Format terraform configuration"""
        try:
            config = params.get('config', {})
            if not config:
                raise ValueError("Terraform configuration is required")

            formatted_config = {}

            with tempfile.TemporaryDirectory() as tmpdir:
                for path, content in config.items():
                    file_path = os.path.join(tmpdir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # Write original content
                    with open(file_path, 'w') as f:
                        f.write(content)

                    # Run terraform fmt
                    fmt_result = subprocess.run(
                        ['terraform', 'fmt', '-'],
                        input=content,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if fmt_result.returncode == 0:
                        formatted_config[path] = fmt_result.stdout
                    else:
                        # If formatting fails, return original content
                        formatted_config[path] = content

            return {
                "status": "success",
                "formatted_config": formatted_config
            }

        except Exception as e:
            logger.error(f"Terraform formatting failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "formatted_config": params.get('config', {})
            }

    def get_providers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get required providers from configuration"""
        try:
            config = params.get('config', {})
            providers = set()

            # Parse terraform configuration to extract providers
            for path, content in config.items():
                if path.endswith('.tf'):
                    # Simple regex-based provider extraction
                    import re
                    provider_matches = re.findall(r'provider\s+"([^"]+)"', content)
                    providers.update(provider_matches)

                    # Also check for required_providers
                    required_matches = re.findall(r'(\w+)\s*=\s*{[^}]*source\s*=\s*"([^"]+)"', content)
                    for match in required_matches:
                        providers.add(match[0])

            return {
                "status": "success",
                "providers": list(providers),
                "supported": [p for p in providers if p in self.allowed_providers]
            }

        except Exception as e:
            logger.error(f"Provider extraction failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "providers": [],
                "supported": []
            }

    def validate_workspace(self, workspace: str):
        """Validate workspace is allowed"""
        if workspace not in self.allowed_workspaces:
            raise ValueError(f"Workspace not allowed: {workspace}. Allowed: {self.allowed_workspaces}")

    def _run_terraform_init(self, working_dir: str, backend_config: Dict = None) -> Dict[str, Any]:
        """Run terraform init"""
        try:
            cmd = ['terraform', 'init']

            # Add backend configuration if provided
            if not backend_config:
                cmd.append('-backend=false')

            init_result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if init_result.returncode == 0:
                return {
                    "status": "success",
                    "stage": "init",
                    "output": init_result.stdout
                }
            else:
                return {
                    "status": "failed",
                    "stage": "init",
                    "error": init_result.stderr,
                    "output": init_result.stdout
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "stage": "init",
                "error": "Terraform init timed out"
            }
        except Exception as e:
            return {
                "status": "failed",
                "stage": "init",
                "error": str(e)
            }

    def _run_terraform_plan(self, working_dir: str, workspace: str = None) -> Dict[str, Any]:
        """Run terraform plan"""
        try:
            cmd = ['terraform', 'plan', '-json', '-detailed-exitcode']

            plan_result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse JSON output
            plan_json = self._parse_json_output(plan_result.stdout)
            summary = self._generate_plan_summary(plan_json)

            # Exit code 0: no changes, 1: error, 2: changes
            if plan_result.returncode == 0:
                status = "no_changes"
            elif plan_result.returncode == 2:
                status = "changes_required"
            else:
                status = "failed"

            return {
                "status": status,
                "plan": plan_json,
                "summary": summary,
                "raw_output": plan_result.stdout,
                "errors": plan_result.stderr,
                "exit_code": plan_result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "stage": "plan",
                "error": "Terraform plan timed out",
                "plan": [],
                "summary": self._empty_summary()
            }
        except Exception as e:
            return {
                "status": "failed",
                "stage": "plan",
                "error": str(e),
                "plan": [],
                "summary": self._empty_summary()
            }

    def _parse_json_output(self, output: str) -> List[Dict]:
        """Parse terraform JSON output"""
        plans = []
        for line in output.split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    plans.append(data)
                except json.JSONDecodeError:
                    continue
        return plans

    def _generate_plan_summary(self, plan_json: List[Dict]) -> Dict[str, Any]:
        """Generate human-readable plan summary"""
        summary = {
            "add": 0,
            "change": 0,
            "destroy": 0,
            "resources": [],
            "drift": [],
            "errors": []
        }

        for item in plan_json:
            msg_type = item.get('@level')

            if msg_type == 'error':
                summary['errors'].append({
                    "message": item.get('@message', ''),
                    "diagnostic": item.get('diagnostic', {})
                })

            elif item.get('type') == 'planned_change':
                change = item.get('change', {})
                action = change.get('action')
                resource = change.get('resource', {})

                if action == 'create':
                    summary['add'] += 1
                elif action == 'update':
                    summary['change'] += 1
                elif action == 'delete':
                    summary['destroy'] += 1

                summary['resources'].append({
                    'type': resource.get('resource_type', 'unknown'),
                    'name': resource.get('resource_name', 'unknown'),
                    'action': action or 'unknown',
                    'provider': resource.get('provider_name', ''),
                    'addr': resource.get('resource', '')
                })

            elif item.get('type') == 'resource_drift':
                drift_change = item.get('change', {})
                drift_resource = drift_change.get('resource', {})

                summary['drift'].append({
                    'type': drift_resource.get('resource_type', 'unknown'),
                    'name': drift_resource.get('resource_name', 'unknown'),
                    'action': drift_change.get('action', 'unknown')
                })

        return summary

    def _generate_backend_config(self, backend_config: Dict[str, Any]) -> str:
        """Generate backend configuration"""
        backend_type = backend_config.get('type', 's3')

        if backend_type == 's3':
            return f'''terraform {{
  backend "s3" {{
    bucket = "{backend_config.get('bucket', 'terraform-state')}"
    key    = "{backend_config.get('key', 'terraform.tfstate')}"
    region = "{backend_config.get('region', 'us-east-1')}"
    {f'dynamodb_table = "{backend_config["dynamodb_table"]}"' if backend_config.get('dynamodb_table') else ''}
    {f'encrypt = {str(backend_config.get("encrypt", True)).lower()}' if backend_config.get('encrypt') is not None else ''}
  }}
}}'''

        elif backend_type == 'local':
            return f'''terraform {{
  backend "local" {{
    path = "{backend_config.get('path', 'terraform.tfstate')}"
  }}
}}'''

        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure"""
        return {
            "add": 0,
            "change": 0,
            "destroy": 0,
            "resources": [],
            "drift": [],
            "errors": []
        }

    def get_state_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get terraform state information"""
        try:
            workspace = params.get('workspace', 'default')
            self.validate_workspace(workspace)

            # For security, we only return basic state info, not the actual state
            return {
                "status": "success",
                "workspace": workspace,
                "state_exists": True,  # This would be determined by actual state check
                "last_modified": None,  # Would get from actual state
                "resources_count": 0,   # Would count from actual state
                "terraform_version": None  # Would get from state metadata
            }

        except Exception as e:
            logger.error(f"State info retrieval failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def list_workspaces(self) -> Dict[str, Any]:
        """List available workspaces"""
        return {
            "status": "success",
            "workspaces": self.allowed_workspaces,
            "current": "default"
        }

    def get_version(self) -> Dict[str, Any]:
        """Get terraform version"""
        try:
            version_result = subprocess.run(
                ['terraform', 'version', '-json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if version_result.returncode == 0:
                version_data = json.loads(version_result.stdout)
                return {
                    "status": "success",
                    "terraform_version": version_data.get('terraform_version'),
                    "provider_versions": version_data.get('provider_selections', {}),
                    "outdated": version_data.get('terraform_outdated', False)
                }
            else:
                return {
                    "status": "failed",
                    "error": version_result.stderr
                }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

# Factory function for creating MCP Terraform server
def create_mcp_terraform_server(config: Dict[str, Any] = None) -> MCPTerraform:
    """Create MCP Terraform server with configuration"""
    config = config or {}

    return MCPTerraform(
        allowed_workspaces=config.get('allowed_workspaces', ['dev', 'staging', 'prod']),
        allowed_providers=config.get('allowed_providers', ['aws', 'azure', 'gcp', 'kubernetes'])
    )