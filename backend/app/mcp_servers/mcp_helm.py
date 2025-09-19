from typing import Dict, Any, List, Optional
import subprocess
import tempfile
import yaml
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPHelm:
    """MCP Server for Helm operations with typed interfaces"""

    def __init__(self, allowed_namespaces: List[str], allowed_repositories: List[str] = None):
        self.allowed_namespaces = allowed_namespaces or ["default", "staging", "prod"]
        self.allowed_repositories = allowed_repositories or ["stable", "bitnami", "prometheus-community"]

    def dry_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run helm install --dry-run"""
        try:
            # Validate parameters
            namespace = params.get('namespace', 'default')
            self.validate_namespace(namespace)

            chart = params.get('chart', {})
            release_name = params.get('release_name', 'test-release')
            values = params.get('values', {})

            if not chart:
                raise ValueError("Helm chart configuration is required")

            if not release_name:
                raise ValueError("Release name is required")

            with tempfile.TemporaryDirectory() as tmpdir:
                chart_dir = os.path.join(tmpdir, 'chart')
                os.makedirs(chart_dir)

                # Write chart files
                for path, content in chart.items():
                    file_path = os.path.join(chart_dir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                # Write custom values if provided
                values_file = None
                if values:
                    values_file = os.path.join(tmpdir, 'custom-values.yaml')
                    with open(values_file, 'w') as f:
                        yaml.dump(values, f)

                # Run helm lint first
                lint_result = self._run_helm_lint(chart_dir)

                # Run helm dry-run
                dry_run_result = self._run_helm_dry_run(
                    chart_dir, release_name, namespace, values_file
                )

                # Extract and parse manifests
                manifests = self._extract_manifests(dry_run_result.get('raw_output', ''))
                manifest_summary = self._analyze_manifests(manifests)

                return {
                    "status": dry_run_result['status'],
                    "lint": lint_result,
                    "manifests": manifests,
                    "manifest_summary": manifest_summary,
                    "notes": self._extract_notes(dry_run_result.get('raw_output', '')),
                    "raw_output": dry_run_result.get('raw_output', ''),
                    "errors": dry_run_result.get('errors', ''),
                    "release_name": release_name,
                    "namespace": namespace
                }

        except Exception as e:
            logger.error(f"Helm dry-run failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "lint": {"passed": False, "output": "", "errors": str(e)},
                "manifests": [],
                "manifest_summary": {},
                "notes": "",
                "raw_output": "",
                "errors": str(e)
            }

    def lint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run helm lint on chart"""
        try:
            chart = params.get('chart', {})
            if not chart:
                raise ValueError("Helm chart configuration is required")

            with tempfile.TemporaryDirectory() as tmpdir:
                chart_dir = os.path.join(tmpdir, 'chart')
                os.makedirs(chart_dir)

                # Write chart files
                for path, content in chart.items():
                    file_path = os.path.join(chart_dir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                return self._run_helm_lint(chart_dir)

        except Exception as e:
            logger.error(f"Helm lint failed: {e}")
            return {
                "passed": False,
                "output": "",
                "errors": str(e),
                "warnings": [],
                "info": []
            }

    def template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run helm template to render manifests"""
        try:
            chart = params.get('chart', {})
            release_name = params.get('release_name', 'test-release')
            values = params.get('values', {})

            if not chart:
                raise ValueError("Helm chart configuration is required")

            with tempfile.TemporaryDirectory() as tmpdir:
                chart_dir = os.path.join(tmpdir, 'chart')
                os.makedirs(chart_dir)

                # Write chart files
                for path, content in chart.items():
                    file_path = os.path.join(chart_dir, path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)

                # Write custom values if provided
                cmd = ['helm', 'template', release_name, chart_dir]

                if values:
                    values_file = os.path.join(tmpdir, 'custom-values.yaml')
                    with open(values_file, 'w') as f:
                        yaml.dump(values, f)
                    cmd.extend(['-f', values_file])

                # Run helm template
                template_result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if template_result.returncode == 0:
                    manifests = self._extract_manifests(template_result.stdout)
                    return {
                        "status": "success",
                        "manifests": manifests,
                        "manifest_summary": self._analyze_manifests(manifests),
                        "raw_output": template_result.stdout
                    }
                else:
                    return {
                        "status": "failed",
                        "error": template_result.stderr,
                        "raw_output": template_result.stdout
                    }

        except Exception as e:
            logger.error(f"Helm template failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "manifests": [],
                "manifest_summary": {}
            }

    def validate_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate helm chart structure and dependencies"""
        try:
            chart = params.get('chart', {})
            if not chart:
                raise ValueError("Helm chart configuration is required")

            validation_results = {
                "status": "valid",
                "errors": [],
                "warnings": [],
                "chart_info": {},
                "dependencies": []
            }

            # Check required files
            required_files = ['Chart.yaml', 'values.yaml']
            missing_files = [f for f in required_files if f not in chart]

            if missing_files:
                validation_results["errors"].extend([
                    f"Missing required file: {f}" for f in missing_files
                ])
                validation_results["status"] = "invalid"

            # Validate Chart.yaml
            if 'Chart.yaml' in chart:
                try:
                    chart_yaml = yaml.safe_load(chart['Chart.yaml'])
                    validation_results["chart_info"] = {
                        "name": chart_yaml.get('name'),
                        "version": chart_yaml.get('version'),
                        "app_version": chart_yaml.get('appVersion'),
                        "description": chart_yaml.get('description'),
                        "type": chart_yaml.get('type', 'application')
                    }

                    # Check for required fields
                    required_chart_fields = ['name', 'version']
                    for field in required_chart_fields:
                        if not chart_yaml.get(field):
                            validation_results["errors"].append(
                                f"Chart.yaml missing required field: {field}"
                            )
                            validation_results["status"] = "invalid"

                    # Extract dependencies
                    if 'dependencies' in chart_yaml:
                        validation_results["dependencies"] = chart_yaml['dependencies']

                except yaml.YAMLError as e:
                    validation_results["errors"].append(f"Invalid Chart.yaml: {e}")
                    validation_results["status"] = "invalid"

            # Validate values.yaml
            if 'values.yaml' in chart:
                try:
                    yaml.safe_load(chart['values.yaml'])
                except yaml.YAMLError as e:
                    validation_results["errors"].append(f"Invalid values.yaml: {e}")
                    validation_results["status"] = "invalid"

            # Check template files
            template_files = [path for path in chart.keys() if path.startswith('templates/')]
            if not template_files:
                validation_results["warnings"].append("No template files found")

            # Validate template syntax
            for template_path in template_files:
                if template_path.endswith('.yaml') or template_path.endswith('.yml'):
                    content = chart[template_path]
                    if content.strip():  # Only validate non-empty files
                        try:
                            # Basic YAML structure validation
                            # Note: This won't catch Helm template syntax errors
                            yaml.safe_load(content)
                        except yaml.YAMLError as e:
                            validation_results["warnings"].append(
                                f"Template {template_path} may have YAML issues: {e}"
                            )

            return validation_results

        except Exception as e:
            logger.error(f"Chart validation failed: {e}")
            return {
                "status": "error",
                "errors": [str(e)],
                "warnings": [],
                "chart_info": {},
                "dependencies": []
            }

    def get_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get values from helm chart"""
        try:
            chart = params.get('chart', {})
            if not chart or 'values.yaml' not in chart:
                return {
                    "status": "failed",
                    "error": "No values.yaml found in chart"
                }

            values = yaml.safe_load(chart['values.yaml'])
            return {
                "status": "success",
                "values": values,
                "schema": self._analyze_values_schema(values)
            }

        except Exception as e:
            logger.error(f"Get values failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def validate_namespace(self, namespace: str):
        """Validate namespace is allowed"""
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace not allowed: {namespace}. Allowed: {self.allowed_namespaces}")

    def _run_helm_lint(self, chart_dir: str) -> Dict[str, Any]:
        """Run helm lint on chart directory"""
        try:
            lint_result = subprocess.run(
                ['helm', 'lint', chart_dir],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse lint output
            lint_info = self._parse_lint_output(lint_result.stdout)

            return {
                "passed": lint_result.returncode == 0,
                "output": lint_result.stdout,
                "errors": lint_result.stderr,
                "warnings": lint_info.get('warnings', []),
                "info": lint_info.get('info', []),
                "error_count": lint_info.get('error_count', 0),
                "warning_count": lint_info.get('warning_count', 0)
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "",
                "errors": "Helm lint timed out",
                "warnings": [],
                "info": [],
                "error_count": 1,
                "warning_count": 0
            }
        except Exception as e:
            return {
                "passed": False,
                "output": "",
                "errors": str(e),
                "warnings": [],
                "info": [],
                "error_count": 1,
                "warning_count": 0
            }

    def _run_helm_dry_run(self, chart_dir: str, release_name: str,
                         namespace: str, values_file: str = None) -> Dict[str, Any]:
        """Run helm install --dry-run"""
        try:
            cmd = [
                'helm', 'install', release_name, chart_dir,
                '--dry-run', '--debug', '--namespace', namespace
            ]

            if values_file:
                cmd.extend(['-f', values_file])

            dry_run_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "status": "success" if dry_run_result.returncode == 0 else "failed",
                "raw_output": dry_run_result.stdout,
                "errors": dry_run_result.stderr,
                "exit_code": dry_run_result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "raw_output": "",
                "errors": "Helm dry-run timed out",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "status": "failed",
                "raw_output": "",
                "errors": str(e),
                "exit_code": -1
            }

    def _extract_manifests(self, output: str) -> List[Dict]:
        """Extract Kubernetes manifests from dry-run output"""
        manifests = []
        current_manifest = []
        in_manifest = False

        for line in output.split('\n'):
            if line.startswith('---') and not line.startswith('---#'):
                if current_manifest:
                    manifest_text = '\n'.join(current_manifest)
                    try:
                        manifest = yaml.safe_load(manifest_text)
                        if manifest and isinstance(manifest, dict) and manifest.get('kind'):
                            manifests.append(manifest)
                    except yaml.YAMLError:
                        pass
                    current_manifest = []
                in_manifest = True
            elif in_manifest and line.strip() and not line.startswith('#'):
                current_manifest.append(line)

        # Process last manifest
        if current_manifest:
            manifest_text = '\n'.join(current_manifest)
            try:
                manifest = yaml.safe_load(manifest_text)
                if manifest and isinstance(manifest, dict) and manifest.get('kind'):
                    manifests.append(manifest)
            except yaml.YAMLError:
                pass

        return manifests

    def _extract_notes(self, output: str) -> str:
        """Extract NOTES section from helm output"""
        lines = output.split('\n')
        notes_start = -1

        for i, line in enumerate(lines):
            if 'NOTES:' in line:
                notes_start = i + 1
                break

        if notes_start >= 0:
            notes_lines = []
            for line in lines[notes_start:]:
                if line.startswith('---') or line.startswith('apiVersion:'):
                    break
                notes_lines.append(line)
            return '\n'.join(notes_lines).strip()

        return ""

    def _analyze_manifests(self, manifests: List[Dict]) -> Dict[str, Any]:
        """Analyze generated manifests"""
        summary = {
            "total_count": len(manifests),
            "by_kind": {},
            "by_namespace": {},
            "resource_names": [],
            "has_secrets": False,
            "has_configmaps": False,
            "has_services": False,
            "has_ingress": False
        }

        for manifest in manifests:
            kind = manifest.get('kind', 'Unknown')
            namespace = manifest.get('metadata', {}).get('namespace', 'default')
            name = manifest.get('metadata', {}).get('name', 'unknown')

            # Count by kind
            summary["by_kind"][kind] = summary["by_kind"].get(kind, 0) + 1

            # Count by namespace
            summary["by_namespace"][namespace] = summary["by_namespace"].get(namespace, 0) + 1

            # Collect resource names
            summary["resource_names"].append(f"{kind}/{name}")

            # Set flags for common resource types
            if kind == 'Secret':
                summary["has_secrets"] = True
            elif kind == 'ConfigMap':
                summary["has_configmaps"] = True
            elif kind == 'Service':
                summary["has_services"] = True
            elif kind == 'Ingress':
                summary["has_ingress"] = True

        return summary

    def _parse_lint_output(self, output: str) -> Dict[str, Any]:
        """Parse helm lint output"""
        info = {
            "warnings": [],
            "info": [],
            "error_count": 0,
            "warning_count": 0
        }

        for line in output.split('\n'):
            line = line.strip()
            if '[WARNING]' in line:
                info["warnings"].append(line.replace('[WARNING]', '').strip())
                info["warning_count"] += 1
            elif '[INFO]' in line:
                info["info"].append(line.replace('[INFO]', '').strip())
            elif '[ERROR]' in line:
                info["error_count"] += 1

        return info

    def _analyze_values_schema(self, values: Any, path: str = "") -> Dict[str, Any]:
        """Analyze values.yaml schema"""
        if isinstance(values, dict):
            schema = {
                "type": "object",
                "properties": {}
            }
            for key, value in values.items():
                schema["properties"][key] = self._analyze_values_schema(
                    value, f"{path}.{key}" if path else key
                )
            return schema
        elif isinstance(values, list):
            return {
                "type": "array",
                "items": self._analyze_values_schema(values[0] if values else {}, path)
            }
        elif isinstance(values, str):
            return {"type": "string", "example": values}
        elif isinstance(values, bool):
            return {"type": "boolean", "example": values}
        elif isinstance(values, (int, float)):
            return {"type": "number", "example": values}
        else:
            return {"type": "unknown", "example": str(values)}

    def list_namespaces(self) -> Dict[str, Any]:
        """List allowed namespaces"""
        return {
            "status": "success",
            "namespaces": self.allowed_namespaces
        }

    def get_version(self) -> Dict[str, Any]:
        """Get helm version"""
        try:
            version_result = subprocess.run(
                ['helm', 'version', '--short'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if version_result.returncode == 0:
                return {
                    "status": "success",
                    "version": version_result.stdout.strip()
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

# Factory function for creating MCP Helm server
def create_mcp_helm_server(config: Dict[str, Any] = None) -> MCPHelm:
    """Create MCP Helm server with configuration"""
    config = config or {}

    return MCPHelm(
        allowed_namespaces=config.get('allowed_namespaces', ['default', 'staging', 'prod']),
        allowed_repositories=config.get('allowed_repositories', ['stable', 'bitnami', 'prometheus-community'])
    )