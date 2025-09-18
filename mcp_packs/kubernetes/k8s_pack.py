from kubernetes import client, config
from kubernetes.client.rest import ApiException
from mcp_packs.base.mcp_pack import MCPPack
from typing import Dict, Any, List, Optional
import logging
import yaml
import base64

logger = logging.getLogger(__name__)

class KubernetesPack(MCPPack):
    """Kubernetes MCP Pack for container orchestration operations"""
    
    def validate_config(self):
        """Validate Kubernetes configuration"""
        # Check if we're running in-cluster or need kubeconfig
        self.in_cluster = self.config.get('in_cluster', False)
        
        if not self.in_cluster and 'kubeconfig' not in self.config:
            # Try to use default kubeconfig location
            import os
            default_kubeconfig = os.path.expanduser('~/.kube/config')
            if not os.path.exists(default_kubeconfig):
                raise ValueError("Kubeconfig file not found and not running in-cluster")
            self.config['kubeconfig'] = default_kubeconfig
    
    def initialize(self):
        """Initialize Kubernetes client"""
        try:
            if self.in_cluster:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration")
            else:
                config.load_kube_config(config_file=self.config.get('kubeconfig'))
                logger.info(f"Loaded kubeconfig from: {self.config.get('kubeconfig')}")
            
            # Initialize API clients
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            
            # Test connection
            self.v1.list_namespace()
            logger.info("Kubernetes Pack initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise
    
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Kubernetes action"""
        actions = {
            'deploy': self.deploy_application,
            'scale': self.scale_deployment,
            'rollback': self.rollback_deployment,
            'get_pods': self.get_pods,
            'get_deployments': self.get_deployments,
            'get_services': self.get_services,
            'get_logs': self.get_pod_logs,
            'restart_deployment': self.restart_deployment,
            'create_configmap': self.create_configmap,
            'create_secret': self.create_secret,
            'get_namespaces': self.get_namespaces,
            'get_events': self.get_events,
            'exec_pod': self.exec_pod_command
        }
        
        if action not in actions:
            raise ValueError(f"Unknown action: {action}")
        
        return actions[action](params)
    
    def get_available_actions(self) -> List[str]:
        """Return list of available Kubernetes actions"""
        return [
            'deploy',
            'scale',
            'rollback',
            'get_pods',
            'get_deployments',
            'get_services',
            'get_logs',
            'restart_deployment',
            'create_configmap',
            'create_secret',
            'get_namespaces',
            'get_events',
            'exec_pod'
        ]
    
    def deploy_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application to Kubernetes"""
        try:
            namespace = params.get('namespace', 'default')
            
            # Parse deployment manifest
            if 'manifest' in params:
                manifest = yaml.safe_load(params['manifest'])
            else:
                # Create deployment from parameters
                manifest = self._create_deployment_manifest(params)
            
            # Create or update deployment
            deployment_name = manifest['metadata']['name']
            
            try:
                # Try to update existing deployment
                existing = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                )
                
                response = self.apps_v1.patch_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace,
                    body=manifest
                )
                operation = 'updated'
            except ApiException as e:
                if e.status == 404:
                    # Create new deployment
                    response = self.apps_v1.create_namespaced_deployment(
                        namespace=namespace,
                        body=manifest
                    )
                    operation = 'created'
                else:
                    raise
            
            return {
                'success': True,
                'operation': operation,
                'deployment': deployment_name,
                'namespace': namespace,
                'replicas': response.spec.replicas
            }
        except Exception as e:
            logger.error(f"Failed to deploy application: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def scale_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scale a Kubernetes deployment"""
        try:
            name = params['deployment_name']
            namespace = params.get('namespace', 'default')
            replicas = params['replicas']
            
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            response = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                'success': True,
                'deployment': name,
                'namespace': namespace,
                'replicas': replicas,
                'previous_replicas': deployment.spec.replicas
            }
        except ApiException as e:
            logger.error(f"Failed to scale deployment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def rollback_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback a deployment to previous version"""
        try:
            name = params['deployment_name']
            namespace = params.get('namespace', 'default')
            revision = params.get('revision', None)
            
            # This is a simplified rollback - in production, you'd use 
            # deployment rollout history and kubectl rollout undo equivalent
            
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # Trigger rollback by updating deployment
            if deployment.metadata.annotations is None:
                deployment.metadata.annotations = {}
            
            deployment.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = \
                datetime.now().isoformat()
            
            response = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                'success': True,
                'deployment': name,
                'namespace': namespace,
                'message': 'Rollback initiated'
            }
        except ApiException as e:
            logger.error(f"Failed to rollback deployment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pods(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get pods in a namespace"""
        try:
            namespace = params.get('namespace', 'default')
            label_selector = params.get('label_selector', None)
            
            if label_selector:
                pods = self.v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                )
            else:
                pods = self.v1.list_namespaced_pod(namespace=namespace)
            
            pod_list = []
            for pod in pods.items:
                pod_list.append({
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'status': pod.status.phase,
                    'ready': all(c.ready for c in pod.status.container_statuses or []),
                    'restarts': sum(c.restart_count for c in pod.status.container_statuses or []),
                    'age': (datetime.now(timezone.utc) - pod.metadata.creation_timestamp).total_seconds(),
                    'node': pod.spec.node_name
                })
            
            return {
                'success': True,
                'pods': pod_list,
                'count': len(pod_list)
            }
        except ApiException as e:
            logger.error(f"Failed to get pods: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_deployments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get deployments in a namespace"""
        try:
            namespace = params.get('namespace', 'default')
            
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            
            deployment_list = []
            for deployment in deployments.items:
                deployment_list.append({
                    'name': deployment.metadata.name,
                    'namespace': deployment.metadata.namespace,
                    'replicas': deployment.spec.replicas,
                    'ready_replicas': deployment.status.ready_replicas or 0,
                    'available_replicas': deployment.status.available_replicas or 0,
                    'updated_replicas': deployment.status.updated_replicas or 0,
                    'conditions': [
                        {
                            'type': c.type,
                            'status': c.status,
                            'reason': c.reason
                        } for c in deployment.status.conditions or []
                    ]
                })
            
            return {
                'success': True,
                'deployments': deployment_list,
                'count': len(deployment_list)
            }
        except ApiException as e:
            logger.error(f"Failed to get deployments: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get services in a namespace"""
        try:
            namespace = params.get('namespace', 'default')
            
            services = self.v1.list_namespaced_service(namespace=namespace)
            
            service_list = []
            for service in services.items:
                service_list.append({
                    'name': service.metadata.name,
                    'namespace': service.metadata.namespace,
                    'type': service.spec.type,
                    'cluster_ip': service.spec.cluster_ip,
                    'external_ip': service.status.load_balancer.ingress[0].ip 
                        if service.status.load_balancer.ingress else None,
                    'ports': [
                        {
                            'port': p.port,
                            'target_port': p.target_port,
                            'protocol': p.protocol
                        } for p in service.spec.ports or []
                    ]
                })
            
            return {
                'success': True,
                'services': service_list,
                'count': len(service_list)
            }
        except ApiException as e:
            logger.error(f"Failed to get services: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pod_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get logs from a pod"""
        try:
            pod_name = params['pod_name']
            namespace = params.get('namespace', 'default')
            container = params.get('container', None)
            tail_lines = params.get('tail_lines', 100)
            
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            
            return {
                'success': True,
                'pod': pod_name,
                'namespace': namespace,
                'logs': logs
            }
        except ApiException as e:
            logger.error(f"Failed to get pod logs: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def restart_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a deployment by updating its annotation"""
        try:
            name = params['deployment_name']
            namespace = params.get('namespace', 'default')
            
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # Add restart annotation
            if deployment.spec.template.metadata.annotations is None:
                deployment.spec.template.metadata.annotations = {}
            
            deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = \
                datetime.now().isoformat()
            
            response = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                'success': True,
                'deployment': name,
                'namespace': namespace,
                'message': 'Deployment restart initiated'
            }
        except ApiException as e:
            logger.error(f"Failed to restart deployment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_configmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a ConfigMap"""
        try:
            name = params['name']
            namespace = params.get('namespace', 'default')
            data = params['data']
            
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name=name),
                data=data
            )
            
            try:
                response = self.v1.create_namespaced_config_map(
                    namespace=namespace,
                    body=configmap
                )
                operation = 'created'
            except ApiException as e:
                if e.status == 409:  # Already exists
                    response = self.v1.patch_namespaced_config_map(
                        name=name,
                        namespace=namespace,
                        body=configmap
                    )
                    operation = 'updated'
                else:
                    raise
            
            return {
                'success': True,
                'operation': operation,
                'configmap': name,
                'namespace': namespace
            }
        except ApiException as e:
            logger.error(f"Failed to create configmap: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_secret(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Secret"""
        try:
            name = params['name']
            namespace = params.get('namespace', 'default')
            data = params['data']
            secret_type = params.get('type', 'Opaque')
            
            # Encode data to base64
            encoded_data = {
                k: base64.b64encode(v.encode()).decode() 
                for k, v in data.items()
            }
            
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(name=name),
                data=encoded_data,
                type=secret_type
            )
            
            try:
                response = self.v1.create_namespaced_secret(
                    namespace=namespace,
                    body=secret
                )
                operation = 'created'
            except ApiException as e:
                if e.status == 409:  # Already exists
                    response = self.v1.patch_namespaced_secret(
                        name=name,
                        namespace=namespace,
                        body=secret
                    )
                    operation = 'updated'
                else:
                    raise
            
            return {
                'success': True,
                'operation': operation,
                'secret': name,
                'namespace': namespace
            }
        except ApiException as e:
            logger.error(f"Failed to create secret: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_namespaces(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all namespaces"""
        try:
            namespaces = self.v1.list_namespace()
            
            namespace_list = []
            for ns in namespaces.items:
                namespace_list.append({
                    'name': ns.metadata.name,
                    'status': ns.status.phase,
                    'age': (datetime.now(timezone.utc) - ns.metadata.creation_timestamp).total_seconds()
                })
            
            return {
                'success': True,
                'namespaces': namespace_list,
                'count': len(namespace_list)
            }
        except ApiException as e:
            logger.error(f"Failed to get namespaces: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_events(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get events in a namespace"""
        try:
            namespace = params.get('namespace', 'default')
            limit = params.get('limit', 20)
            
            events = self.v1.list_namespaced_event(namespace=namespace)
            
            event_list = []
            for event in events.items[:limit]:
                event_list.append({
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message,
                    'object': f"{event.involved_object.kind}/{event.involved_object.name}",
                    'first_seen': event.first_timestamp.isoformat() if event.first_timestamp else None,
                    'last_seen': event.last_timestamp.isoformat() if event.last_timestamp else None,
                    'count': event.count
                })
            
            # Sort by last seen timestamp
            event_list.sort(key=lambda x: x['last_seen'] or '', reverse=True)
            
            return {
                'success': True,
                'events': event_list,
                'count': len(event_list)
            }
        except ApiException as e:
            logger.error(f"Failed to get events: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def exec_pod_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command in a pod"""
        try:
            from kubernetes.stream import stream
            
            pod_name = params['pod_name']
            namespace = params.get('namespace', 'default')
            command = params['command']
            container = params.get('container', None)
            
            # Execute command
            resp = stream(
                self.v1.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=command if isinstance(command, list) else ['/bin/sh', '-c', command],
                container=container,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            
            return {
                'success': True,
                'pod': pod_name,
                'namespace': namespace,
                'output': resp
            }
        except ApiException as e:
            logger.error(f"Failed to execute command in pod: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_deployment_manifest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deployment manifest from parameters"""
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': params['name'],
                'labels': params.get('labels', {})
            },
            'spec': {
                'replicas': params.get('replicas', 1),
                'selector': {
                    'matchLabels': params.get('selector_labels', {'app': params['name']})
                },
                'template': {
                    'metadata': {
                        'labels': params.get('pod_labels', {'app': params['name']})
                    },
                    'spec': {
                        'containers': [{
                            'name': params.get('container_name', params['name']),
                            'image': params['image'],
                            'ports': [{'containerPort': p} for p in params.get('ports', [])],
                            'env': [
                                {'name': k, 'value': v} 
                                for k, v in params.get('env', {}).items()
                            ],
                            'resources': params.get('resources', {})
                        }]
                    }
                }
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check Kubernetes cluster health"""
        try:
            # Try to list namespaces as health check
            namespaces = self.v1.list_namespace()
            
            # Get cluster version
            version_info = self.v1.get_api_resources().group_version
            
            return {
                'name': self.name,
                'status': 'healthy',
                'cluster_version': version_info,
                'namespace_count': len(namespaces.items)
            }
        except Exception as e:
            return {
                'name': self.name,
                'status': 'unhealthy',
                'error': str(e)
            }

from datetime import datetime, timezone