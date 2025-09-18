# Week 2: Infrastructure Agent & Web UI

## Duration: Week 2 (5 days)

## Objectives
- Build **Infrastructure Agent** for Terraform modules and Helm charts
- Implement `terraform plan` and `helm --dry-run` validation
- Create Web UI modules for Pipeline and Infrastructure agents
- Implement PR/MR creation with attached dry-run artifacts
- Build `mcp-terraform` and `mcp-helm` servers

## Prerequisites
- Week 1 completed (Core Foundation & Pipeline Agent)
- FastAPI backend running with Pipeline Agent
- Chroma database with KB collections operational
- MCP servers (`mcp-kb`, `mcp-github`, `mcp-gitlab`) functional
- JSONL audit logging active

## Day-by-Day Implementation

### Day 6: Infrastructure Agent Core

#### Morning (4 hours)
1. **Infrastructure Agent Implementation**
   ```python
   # backend/app/agents/infrastructure_agent.py
   from typing import Dict, Any, List, Optional
   import subprocess
   import tempfile
   import yaml
   import json
   from app.core.kb_manager import KnowledgeBaseManager
   from app.core.citation_engine import CitationEngine

   class InfrastructureAgent:
       def __init__(self, kb_manager: KnowledgeBaseManager):
           self.kb = kb_manager
           self.citation_engine = CitationEngine(kb_manager)

       def generate_infrastructure(self,
                                  target: str,
                                  environments: List[str],
                                  domain: str,
                                  registry: str,
                                  secrets_strategy: str) -> Dict[str, Any]:
           """Generate Terraform and Helm configs with validation"""

           # 1. Search KB for similar infrastructure patterns
           similar_infra = self.kb.search(
               collection='iac',
               query=f"{target} infrastructure terraform helm",
               k=5
           )

           # 2. Generate Terraform modules
           terraform_config = self._generate_terraform(
               target, environments, domain, registry
           )

           # 3. Generate Helm charts (if k8s)
           helm_chart = None
           if target == "k8s":
               helm_chart = self._generate_helm_chart(
                   environments, domain, registry
               )

           # 4. Run terraform plan (dry-run)
           terraform_plan = self._run_terraform_plan(terraform_config)

           # 5. Run helm --dry-run (if k8s)
           helm_dry_run = None
           if helm_chart:
               helm_dry_run = self._run_helm_dry_run(helm_chart)

           # 6. Add citations
           result_with_citations = self.citation_engine.generate_citations(
               json.dumps({
                   "terraform": terraform_config,
                   "helm": helm_chart
               }),
               similar_infra
           )

           return {
               "terraform": terraform_config,
               "helm": helm_chart,
               "terraform_plan": terraform_plan,
               "helm_dry_run": helm_dry_run,
               "citations": [s['citation'] for s in similar_infra]
           }

       def _generate_terraform(self, target: str, envs: List[str],
                              domain: str, registry: str) -> Dict[str, str]:
           """Generate Terraform modules"""
           files = {}

           # Main configuration
           files['main.tf'] = f"""
           terraform {{
               required_version = ">= 1.0"
               required_providers {{
                   aws = {{
                       source  = "hashicorp/aws"
                       version = "~> 5.0"
                   }}
               }}
           }}

           provider "aws" {{
               region = var.aws_region
           }}
           """

           # Network module
           files['modules/network/main.tf'] = self._generate_network_module()

           # Registry module
           files['modules/registry/main.tf'] = self._generate_registry_module(registry)

           # DNS module
           files['modules/dns/main.tf'] = self._generate_dns_module(domain)

           # Secrets module
           files['modules/secrets/main.tf'] = self._generate_secrets_module()

           # Environment-specific configs
           for env in envs:
               files[f'environments/{env}/terraform.tfvars'] = self._generate_env_vars(env)

           return files

       def _run_terraform_plan(self, config: Dict[str, str]) -> Dict[str, Any]:
           """Execute terraform plan and capture output"""
           with tempfile.TemporaryDirectory() as tmpdir:
               # Write terraform files
               for path, content in config.items():
                   file_path = f"{tmpdir}/{path}"
                   # Create directories
                   os.makedirs(os.path.dirname(file_path), exist_ok=True)
                   with open(file_path, 'w') as f:
                       f.write(content)

               # Run terraform init
               init_result = subprocess.run(
                   ['terraform', 'init'],
                   cwd=tmpdir,
                   capture_output=True,
                   text=True
               )

               # Run terraform plan
               plan_result = subprocess.run(
                   ['terraform', 'plan', '-json'],
                   cwd=tmpdir,
                   capture_output=True,
                   text=True
               )

               return {
                   "status": "success" if plan_result.returncode == 0 else "failed",
                   "output": plan_result.stdout,
                   "errors": plan_result.stderr,
                   "summary": self._parse_terraform_plan(plan_result.stdout)
               }
   ```

2. **Helm Chart Generation**
   ```python
   # backend/app/agents/infrastructure_agent.py (continued)
   def _generate_helm_chart(self, environments: List[str],
                            domain: str, registry: str) -> Dict[str, str]:
       """Generate Helm chart skeleton"""
       files = {}

       # Chart.yaml
       files['Chart.yaml'] = """
       apiVersion: v2
       name: f-ops-app
       description: A Helm chart for F-Ops application
       type: application
       version: 0.1.0
       appVersion: "1.0"
       """

       # values.yaml
       files['values.yaml'] = f"""
       replicaCount: 2

       image:
         repository: {registry}/f-ops-app
         pullPolicy: IfNotPresent
         tag: ""

       service:
         type: ClusterIP
         port: 80

       ingress:
         enabled: true
         className: nginx
         annotations: {{}}
         hosts:
           - host: {domain}
             paths:
               - path: /
                 pathType: Prefix

       resources:
         limits:
           cpu: 500m
           memory: 512Mi
         requests:
           cpu: 250m
           memory: 256Mi

       autoscaling:
         enabled: true
         minReplicas: 2
         maxReplicas: 10
         targetCPUUtilizationPercentage: 80
       """

       # Deployment template
       files['templates/deployment.yaml'] = self._generate_deployment_template()

       # Service template
       files['templates/service.yaml'] = self._generate_service_template()

       # Ingress template
       files['templates/ingress.yaml'] = self._generate_ingress_template()

       # Environment-specific values
       for env in environments:
           files[f'values-{env}.yaml'] = self._generate_env_values(env)

       return files

   def _run_helm_dry_run(self, chart: Dict[str, str]) -> Dict[str, Any]:
       """Execute helm --dry-run and capture output"""
       with tempfile.TemporaryDirectory() as tmpdir:
           chart_dir = f"{tmpdir}/chart"
           os.makedirs(chart_dir)

           # Write helm files
           for path, content in chart.items():
               file_path = f"{chart_dir}/{path}"
               os.makedirs(os.path.dirname(file_path), exist_ok=True)
               with open(file_path, 'w') as f:
                   f.write(content)

           # Run helm lint
           lint_result = subprocess.run(
               ['helm', 'lint', chart_dir],
               capture_output=True,
               text=True
           )

           # Run helm install --dry-run
           dry_run_result = subprocess.run(
               ['helm', 'install', 'test-release', chart_dir, '--dry-run', '--debug'],
               capture_output=True,
               text=True
           )

           return {
               "status": "success" if dry_run_result.returncode == 0 else "failed",
               "lint_output": lint_result.stdout,
               "dry_run_output": dry_run_result.stdout,
               "errors": dry_run_result.stderr,
               "manifests": self._extract_manifests(dry_run_result.stdout)
           }
   ```

#### Afternoon (4 hours)
1. **MCP Terraform Server**
   ```python
   # backend/app/mcp_servers/mcp_terraform.py
   from typing import Dict, Any, List
   import subprocess
   import tempfile
   import os
   import json

   class MCPTerraform:
       def __init__(self, allowed_workspaces: List[str]):
           self.allowed_workspaces = allowed_workspaces

       def plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
           """Run terraform plan with typed interface"""
           self.validate_workspace(params['workspace'])

           config = params['config']
           variables = params.get('variables', {})

           with tempfile.TemporaryDirectory() as tmpdir:
               # Write configuration
               for path, content in config.items():
                   file_path = os.path.join(tmpdir, path)
                   os.makedirs(os.path.dirname(file_path), exist_ok=True)
                   with open(file_path, 'w') as f:
                       f.write(content)

               # Write variables
               if variables:
                   with open(os.path.join(tmpdir, 'terraform.tfvars.json'), 'w') as f:
                       json.dump(variables, f)

               # Initialize terraform
               init_result = subprocess.run(
                   ['terraform', 'init', '-backend=false'],
                   cwd=tmpdir,
                   capture_output=True,
                   text=True,
                   timeout=60
               )

               if init_result.returncode != 0:
                   return {
                       "status": "failed",
                       "stage": "init",
                       "error": init_result.stderr
                   }

               # Run plan
               plan_result = subprocess.run(
                   ['terraform', 'plan', '-out=tfplan', '-json'],
                   cwd=tmpdir,
                   capture_output=True,
                   text=True,
                   timeout=120
               )

               # Parse JSON output
               plan_json = self._parse_json_output(plan_result.stdout)

               return {
                   "status": "success" if plan_result.returncode == 0 else "failed",
                   "plan": plan_json,
                   "summary": self._generate_plan_summary(plan_json),
                   "raw_output": plan_result.stdout,
                   "errors": plan_result.stderr
               }

       def validate_workspace(self, workspace: str):
           """Validate workspace is allowed"""
           if workspace not in self.allowed_workspaces:
               raise ValueError(f"Workspace not allowed: {workspace}")

       def _parse_json_output(self, output: str) -> List[Dict]:
           """Parse terraform JSON output"""
           plans = []
           for line in output.split('\n'):
               if line.strip():
                   try:
                       plans.append(json.loads(line))
                   except json.JSONDecodeError:
                       continue
           return plans

       def _generate_plan_summary(self, plan_json: List[Dict]) -> Dict:
           """Generate human-readable plan summary"""
           summary = {
               "add": 0,
               "change": 0,
               "destroy": 0,
               "resources": []
           }

           for item in plan_json:
               if item.get('@level') == 'info' and 'change' in item:
                   change = item['change']
                   action = change.get('action')
                   if action == 'create':
                       summary['add'] += 1
                   elif action == 'update':
                       summary['change'] += 1
                   elif action == 'delete':
                       summary['destroy'] += 1

                   summary['resources'].append({
                       'type': change.get('resource', {}).get('type'),
                       'name': change.get('resource', {}).get('name'),
                       'action': action
                   })

           return summary
   ```

2. **MCP Helm Server**
   ```python
   # backend/app/mcp_servers/mcp_helm.py
   from typing import Dict, Any, List
   import subprocess
   import tempfile
   import yaml
   import os

   class MCPHelm:
       def __init__(self, allowed_namespaces: List[str]):
           self.allowed_namespaces = allowed_namespaces

       def dry_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
           """Run helm install --dry-run"""
           self.validate_namespace(params.get('namespace', 'default'))

           chart = params['chart']
           release_name = params['release_name']
           values = params.get('values', {})

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
               lint_result = subprocess.run(
                   ['helm', 'lint', chart_dir],
                   capture_output=True,
                   text=True
               )

               # Prepare dry-run command
               cmd = [
                   'helm', 'install', release_name, chart_dir,
                   '--dry-run', '--debug'
               ]

               if values_file:
                   cmd.extend(['-f', values_file])

               if params.get('namespace'):
                   cmd.extend(['--namespace', params['namespace']])

               # Run dry-run
               dry_run_result = subprocess.run(
                   cmd,
                   capture_output=True,
                   text=True,
                   timeout=60
               )

               return {
                   "status": "success" if dry_run_result.returncode == 0 else "failed",
                   "lint": {
                       "passed": lint_result.returncode == 0,
                       "output": lint_result.stdout,
                       "errors": lint_result.stderr
                   },
                   "manifests": self._extract_manifests(dry_run_result.stdout),
                   "notes": self._extract_notes(dry_run_result.stdout),
                   "raw_output": dry_run_result.stdout,
                   "errors": dry_run_result.stderr
               }

       def validate_namespace(self, namespace: str):
           """Validate namespace is allowed"""
           if namespace not in self.allowed_namespaces:
               raise ValueError(f"Namespace not allowed: {namespace}")

       def _extract_manifests(self, output: str) -> List[Dict]:
           """Extract Kubernetes manifests from dry-run output"""
           manifests = []
           current_manifest = []
           in_manifest = False

           for line in output.split('\n'):
               if line.startswith('---'):
                   if current_manifest:
                       manifest_text = '\n'.join(current_manifest)
                       try:
                           manifests.append(yaml.safe_load(manifest_text))
                       except yaml.YAMLError:
                           pass
                       current_manifest = []
                   in_manifest = True
               elif in_manifest and line.strip():
                   current_manifest.append(line)

           # Process last manifest
           if current_manifest:
               manifest_text = '\n'.join(current_manifest)
               try:
                   manifests.append(yaml.safe_load(manifest_text))
               except yaml.YAMLError:
                   pass

           return manifests
   ```

### Day 7: Web UI Setup & Pipeline Module

#### Morning (4 hours)
1. **React Project Setup**
   ```bash
   # Create frontend directory
   cd frontend
   npm create vite@latest f-ops-ui -- --template react-ts
   cd f-ops-ui
   npm install
   ```

2. **Core Dependencies**
   ```json
   {
     "dependencies": {
       "react": "^18.2.0",
       "react-dom": "^18.2.0",
       "react-router-dom": "^6.20.0",
       "@reduxjs/toolkit": "^2.0.0",
       "react-redux": "^9.0.0",
       "axios": "^1.6.0",
       "@tanstack/react-query": "^5.0.0",
       "react-hook-form": "^7.48.0",
       "tailwindcss": "^3.3.0",
       "@headlessui/react": "^1.7.0",
       "@heroicons/react": "^2.0.0",
       "react-syntax-highlighter": "^15.5.0",
       "react-diff-viewer": "^3.1.1"
     }
   }
   ```

3. **App Structure**
   ```typescript
   // src/App.tsx
   import { BrowserRouter, Routes, Route } from 'react-router-dom';
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
   import Layout from './components/Layout';
   import PipelineModule from './modules/PipelineModule';
   import InfrastructureModule from './modules/InfrastructureModule';
   import MonitoringModule from './modules/MonitoringModule';
   import KBConnectModule from './modules/KBConnectModule';

   const queryClient = new QueryClient();

   function App() {
     return (
       <QueryClientProvider client={queryClient}>
         <BrowserRouter>
           <Layout>
             <Routes>
               <Route path="/" element={<PipelineModule />} />
               <Route path="/pipeline" element={<PipelineModule />} />
               <Route path="/infrastructure" element={<InfrastructureModule />} />
               <Route path="/monitoring" element={<MonitoringModule />} />
               <Route path="/kb" element={<KBConnectModule />} />
             </Routes>
           </Layout>
         </BrowserRouter>
       </QueryClientProvider>
     );
   }
   ```

#### Afternoon (4 hours)
1. **Pipeline Agent Module**
   ```typescript
   // src/modules/PipelineModule.tsx
   import { useState } from 'react';
   import { useForm } from 'react-hook-form';
   import { useMutation } from '@tanstack/react-query';
   import api from '../services/api';
   import PreviewPanel from '../components/PreviewPanel';
   import CitationList from '../components/CitationList';

   export default function PipelineModule() {
     const [preview, setPreview] = useState(null);
     const [prUrl, setPrUrl] = useState(null);

     const { register, handleSubmit, formState: { errors } } = useForm();

     const generateMutation = useMutation({
       mutationFn: (data) => api.post('/api/pipeline/generate', data),
       onSuccess: (response) => {
         setPreview(response.data);
       }
     });

     const createPrMutation = useMutation({
       mutationFn: (data) => api.post('/api/pipeline/create-pr', data),
       onSuccess: (response) => {
         setPrUrl(response.data.pr_url);
       }
     });

     const onSubmit = (data) => {
       generateMutation.mutate(data);
     };

     const handleCreatePr = () => {
       createPrMutation.mutate({
         ...preview,
         repo_url: formData.repo_url
       });
     };

     return (
       <div className="container mx-auto p-6">
         <h1 className="text-2xl font-bold mb-6">Pipeline Agent</h1>
         <p className="text-gray-600 mb-8">
           Generate CI/CD pipelines for new or existing projects
         </p>

         <div className="grid grid-cols-2 gap-6">
           {/* Input Form */}
           <div className="bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-semibold mb-4">Repository Configuration</h2>

             <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
               <div>
                 <label className="block text-sm font-medium mb-2">
                   Repository URL
                 </label>
                 <input
                   type="url"
                   {...register('repo_url', { required: 'Repository URL is required' })}
                   className="w-full border rounded-md px-3 py-2"
                   placeholder="https://github.com/org/repo"
                 />
                 {errors.repo_url && (
                   <p className="text-red-500 text-sm mt-1">{errors.repo_url.message}</p>
                 )}
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Target Platform
                 </label>
                 <select
                   {...register('target', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="k8s">Kubernetes</option>
                   <option value="serverless">Serverless</option>
                   <option value="static">Static Site</option>
                 </select>
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Environments
                 </label>
                 <div className="space-y-2">
                   {['staging', 'prod'].map(env => (
                     <label key={env} className="flex items-center">
                       <input
                         type="checkbox"
                         value={env}
                         {...register('environments')}
                         className="mr-2"
                       />
                       <span className="text-sm">{env}</span>
                     </label>
                   ))}
                 </div>
               </div>

               <button
                 type="submit"
                 disabled={generateMutation.isPending}
                 className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
               >
                 {generateMutation.isPending ? 'Generating...' : 'Generate Pipeline'}
               </button>
             </form>
           </div>

           {/* Preview Panel */}
           <div className="bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-semibold mb-4">Generated Pipeline Preview</h2>

             {preview ? (
               <div>
                 <PreviewPanel
                   content={preview.pipeline}
                   language="yaml"
                   filename=".github/workflows/pipeline.yml"
                 />

                 <div className="mt-4">
                   <h3 className="font-medium mb-2">KB Citations ({preview.citations.length})</h3>
                   <CitationList citations={preview.citations} />
                 </div>

                 <div className="mt-4 flex gap-2">
                   <button
                     onClick={handleCreatePr}
                     disabled={createPrMutation.isPending}
                     className="flex-1 bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
                   >
                     {createPrMutation.isPending ? 'Creating PR...' : 'Create PR'}
                   </button>
                 </div>

                 {prUrl && (
                   <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                     <p className="text-green-800">
                       ✅ PR created successfully:
                       <a href={prUrl} target="_blank" className="ml-2 underline">
                         {prUrl}
                       </a>
                     </p>
                   </div>
                 )}
               </div>
             ) : (
               <div className="text-center text-gray-500 py-12">
                 Generate a pipeline to see preview
               </div>
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

### Day 8: Infrastructure Module & Dry-Run Display

#### Morning (4 hours)
1. **Infrastructure Module UI**
   ```typescript
   // src/modules/InfrastructureModule.tsx
   import { useState } from 'react';
   import { useForm } from 'react-hook-form';
   import { useMutation } from '@tanstack/react-query';
   import api from '../services/api';
   import DryRunViewer from '../components/DryRunViewer';
   import TerraformPlanViewer from '../components/TerraformPlanViewer';
   import HelmDryRunViewer from '../components/HelmDryRunViewer';

   export default function InfrastructureModule() {
     const [result, setResult] = useState(null);
     const { register, handleSubmit } = useForm();

     const generateMutation = useMutation({
       mutationFn: (data) => api.post('/api/infrastructure/generate', data),
       onSuccess: (response) => {
         setResult(response.data);
       }
     });

     const createPrMutation = useMutation({
       mutationFn: (data) => api.post('/api/infrastructure/create-pr', data),
       onSuccess: (response) => {
         setResult(prev => ({
           ...prev,
           pr_url: response.data.pr_url
         }));
       }
     });

     return (
       <div className="container mx-auto p-6">
         <h1 className="text-2xl font-bold mb-6">Infrastructure Agent</h1>
         <p className="text-gray-600 mb-8">
           Generate Terraform modules and Helm charts with validation
         </p>

         <div className="grid grid-cols-12 gap-6">
           {/* Configuration Form */}
           <div className="col-span-4 bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-semibold mb-4">Infrastructure Configuration</h2>

             <form onSubmit={handleSubmit(generateMutation.mutate)} className="space-y-4">
               <div>
                 <label className="block text-sm font-medium mb-2">
                   Target Platform
                 </label>
                 <select
                   {...register('target', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="k8s">Kubernetes</option>
                   <option value="serverless">Serverless (AWS Lambda)</option>
                   <option value="static">Static Site (S3 + CloudFront)</option>
                 </select>
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Environments
                 </label>
                 <div className="space-y-2">
                   {['staging', 'prod'].map(env => (
                     <label key={env} className="flex items-center">
                       <input
                         type="checkbox"
                         value={env}
                         {...register('environments')}
                         className="mr-2"
                       />
                       <span className="text-sm">{env}</span>
                     </label>
                   ))}
                 </div>
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Domain
                 </label>
                 <input
                   type="text"
                   {...register('domain')}
                   className="w-full border rounded-md px-3 py-2"
                   placeholder="app.example.com"
                 />
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Container Registry
                 </label>
                 <input
                   type="text"
                   {...register('registry')}
                   className="w-full border rounded-md px-3 py-2"
                   placeholder="docker.io/myorg"
                 />
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Secrets Strategy
                 </label>
                 <select
                   {...register('secrets_strategy')}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="aws-secrets-manager">AWS Secrets Manager</option>
                   <option value="k8s-secrets">Kubernetes Secrets</option>
                   <option value="vault">HashiCorp Vault</option>
                 </select>
               </div>

               <button
                 type="submit"
                 disabled={generateMutation.isPending}
                 className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
               >
                 {generateMutation.isPending ? 'Generating...' : 'Generate Infrastructure'}
               </button>
             </form>
           </div>

           {/* Results Panel */}
           <div className="col-span-8">
             {result && (
               <div className="space-y-6">
                 {/* Terraform Plan Results */}
                 <div className="bg-white rounded-lg shadow p-6">
                   <h2 className="text-lg font-semibold mb-4">Terraform Plan</h2>
                   <TerraformPlanViewer plan={result.terraform_plan} />

                   {result.terraform_plan?.summary && (
                     <div className="mt-4 p-3 bg-gray-50 rounded">
                       <h3 className="font-medium mb-2">Plan Summary</h3>
                       <div className="flex gap-4 text-sm">
                         <span className="text-green-600">
                           + {result.terraform_plan.summary.add} to add
                         </span>
                         <span className="text-yellow-600">
                           ~ {result.terraform_plan.summary.change} to change
                         </span>
                         <span className="text-red-600">
                           - {result.terraform_plan.summary.destroy} to destroy
                         </span>
                       </div>
                     </div>
                   )}
                 </div>

                 {/* Helm Dry-Run Results */}
                 {result.helm_dry_run && (
                   <div className="bg-white rounded-lg shadow p-6">
                     <h2 className="text-lg font-semibold mb-4">Helm Dry-Run</h2>
                     <HelmDryRunViewer dryRun={result.helm_dry_run} />
                   </div>
                 )}

                 {/* Citations */}
                 <div className="bg-white rounded-lg shadow p-6">
                   <h3 className="font-medium mb-2">KB Citations</h3>
                   <ul className="space-y-1 text-sm">
                     {result.citations.map((citation, idx) => (
                       <li key={idx} className="text-gray-600">
                         • {citation}
                       </li>
                     ))}
                   </ul>
                 </div>

                 {/* Action Buttons */}
                 <div className="bg-white rounded-lg shadow p-6">
                   {!result.pr_url ? (
                     <button
                       onClick={() => createPrMutation.mutate(result)}
                       disabled={createPrMutation.isPending}
                       className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
                     >
                       {createPrMutation.isPending ? 'Creating PR...' : 'Create PR with Artifacts'}
                     </button>
                   ) : (
                     <div className="p-3 bg-green-50 border border-green-200 rounded">
                       <p className="text-green-800">
                         ✅ PR created with dry-run artifacts:
                         <a href={result.pr_url} target="_blank" className="ml-2 underline">
                           {result.pr_url}
                         </a>
                       </p>
                     </div>
                   )}
                 </div>
               </div>
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

2. **Dry-Run Viewer Components**
   ```typescript
   // src/components/TerraformPlanViewer.tsx
   import { useState } from 'react';
   import SyntaxHighlighter from 'react-syntax-highlighter';
   import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

   export default function TerraformPlanViewer({ plan }) {
     const [view, setView] = useState<'summary' | 'raw'>('summary');

     if (!plan) return null;

     return (
       <div>
         <div className="flex gap-2 mb-4">
           <button
             onClick={() => setView('summary')}
             className={`px-3 py-1 rounded ${
               view === 'summary' ? 'bg-blue-600 text-white' : 'bg-gray-200'
             }`}
           >
             Summary
           </button>
           <button
             onClick={() => setView('raw')}
             className={`px-3 py-1 rounded ${
               view === 'raw' ? 'bg-blue-600 text-white' : 'bg-gray-200'
             }`}
           >
             Raw Output
           </button>
         </div>

         {view === 'summary' ? (
           <div>
             <div className={`p-3 rounded mb-2 ${
               plan.status === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
             }`}>
               Status: {plan.status}
             </div>

             {plan.summary?.resources && (
               <div>
                 <h4 className="font-medium mb-2">Resources to be modified:</h4>
                 <ul className="space-y-2">
                   {plan.summary.resources.map((resource, idx) => (
                     <li key={idx} className="flex items-center gap-2">
                       <span className={`px-2 py-1 text-xs rounded ${
                         resource.action === 'create' ? 'bg-green-100 text-green-800' :
                         resource.action === 'update' ? 'bg-yellow-100 text-yellow-800' :
                         'bg-red-100 text-red-800'
                       }`}>
                         {resource.action}
                       </span>
                       <span className="font-mono text-sm">
                         {resource.type}.{resource.name}
                       </span>
                     </li>
                   ))}
                 </ul>
               </div>
             )}
           </div>
         ) : (
           <div className="max-h-96 overflow-y-auto">
             <SyntaxHighlighter
               language="hcl"
               style={atomOneDark}
               customStyle={{ padding: '1rem', borderRadius: '0.5rem' }}
             >
               {plan.raw_output || plan.output}
             </SyntaxHighlighter>
           </div>
         )}
       </div>
     );
   }
   ```

### Day 9: PR/MR Artifact Attachment

#### Morning (4 hours)
1. **PR Creation with Artifacts**
   ```python
   # backend/app/core/pr_orchestrator_v2.py
   from github import Github
   import gitlab
   from typing import Dict, Any, List
   import base64
   import json

   class PROrchestrator:
       def __init__(self, github_token: str, gitlab_token: str):
           self.github = Github(github_token)
           self.gitlab = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_token)

       def create_pr_with_artifacts(self,
                                   repo_url: str,
                                   files: Dict[str, str],
                                   title: str,
                                   body: str,
                                   artifacts: Dict[str, Any]) -> str:
           """Create PR/MR with dry-run artifacts attached"""

           if "github.com" in repo_url:
               return self._create_github_pr_with_artifacts(
                   repo_url, files, title, body, artifacts
               )
           else:
               return self._create_gitlab_mr_with_artifacts(
                   repo_url, files, title, body, artifacts
               )

       def _create_github_pr_with_artifacts(self,
                                           repo_url: str,
                                           files: Dict[str, str],
                                           title: str,
                                           body: str,
                                           artifacts: Dict[str, Any]) -> str:
           """Create GitHub PR with artifacts as comments"""

           # Parse repo from URL
           repo_parts = repo_url.replace('https://github.com/', '').split('/')
           repo = self.github.get_repo(f"{repo_parts[0]}/{repo_parts[1]}")

           # Create branch
           main_branch = repo.get_branch('main')
           branch_name = f"f-ops/{title.lower().replace(' ', '-')[:30]}"
           repo.create_git_ref(
               ref=f"refs/heads/{branch_name}",
               sha=main_branch.commit.sha
           )

           # Add files to branch
           for path, content in files.items():
               repo.create_file(
                   path=path,
                   message=f"Add {path}",
                   content=content,
                   branch=branch_name
               )

           # Create PR
           pr = repo.create_pull(
               title=f"[F-Ops] {title}",
               body=body,
               head=branch_name,
               base='main'
           )

           # Add artifacts as comments
           self._add_artifacts_to_github_pr(pr, artifacts)

           return pr.html_url

       def _add_artifacts_to_github_pr(self, pr, artifacts: Dict[str, Any]):
           """Add dry-run artifacts as formatted PR comments"""

           # Format Terraform plan
           if artifacts.get('terraform_plan'):
               terraform_comment = self._format_terraform_plan_comment(
                   artifacts['terraform_plan']
               )
               pr.create_issue_comment(terraform_comment)

           # Format Helm dry-run
           if artifacts.get('helm_dry_run'):
               helm_comment = self._format_helm_dry_run_comment(
                   artifacts['helm_dry_run']
               )
               pr.create_issue_comment(helm_comment)

           # Add citations
           if artifacts.get('citations'):
               citations_comment = self._format_citations_comment(
                   artifacts['citations']
               )
               pr.create_issue_comment(citations_comment)

       def _format_terraform_plan_comment(self, plan: Dict) -> str:
           """Format Terraform plan as markdown comment"""
           comment = "## 📋 Terraform Plan Results\n\n"

           if plan['status'] == 'success':
               comment += "✅ **Plan executed successfully**\n\n"

               if plan.get('summary'):
                   comment += "### Summary\n"
                   comment += f"- 🟢 **{plan['summary']['add']}** resources to add\n"
                   comment += f"- 🟡 **{plan['summary']['change']}** resources to change\n"
                   comment += f"- 🔴 **{plan['summary']['destroy']}** resources to destroy\n\n"

                   if plan['summary'].get('resources'):
                       comment += "### Resources\n"
                       comment += "| Action | Type | Name |\n"
                       comment += "|--------|------|------|\n"
                       for resource in plan['summary']['resources']:
                           emoji = {'create': '➕', 'update': '♻️', 'delete': '➖'}.get(
                               resource['action'], '❓'
                           )
                           comment += f"| {emoji} {resource['action']} | `{resource['type']}` | `{resource['name']}` |\n"
           else:
               comment += "❌ **Plan failed**\n\n"
               comment += f"```\n{plan.get('errors', 'Unknown error')}\n```\n"

           # Add collapsible raw output
           comment += "\n<details>\n<summary>View raw terraform plan output</summary>\n\n"
           comment += f"```hcl\n{plan.get('raw_output', '')[:5000]}\n```\n"
           comment += "</details>\n"

           return comment

       def _format_helm_dry_run_comment(self, dry_run: Dict) -> str:
           """Format Helm dry-run as markdown comment"""
           comment = "## ⎈ Helm Dry-Run Results\n\n"

           # Lint results
           if dry_run.get('lint'):
               if dry_run['lint']['passed']:
                   comment += "✅ **Helm lint passed**\n\n"
               else:
                   comment += "⚠️ **Helm lint warnings**\n"
                   comment += f"```\n{dry_run['lint']['output']}\n```\n\n"

           # Dry-run status
           if dry_run['status'] == 'success':
               comment += "✅ **Dry-run successful**\n\n"

               # Show generated manifests summary
               if dry_run.get('manifests'):
                   comment += "### Generated Kubernetes Resources\n"
                   manifest_types = {}
                   for manifest in dry_run['manifests']:
                       kind = manifest.get('kind', 'Unknown')
                       manifest_types[kind] = manifest_types.get(kind, 0) + 1

                   for kind, count in manifest_types.items():
                       comment += f"- {count} {kind}(s)\n"
           else:
               comment += "❌ **Dry-run failed**\n\n"
               comment += f"```\n{dry_run.get('errors', 'Unknown error')}\n```\n"

           # Add collapsible manifests
           if dry_run.get('manifests'):
               comment += "\n<details>\n<summary>View generated manifests</summary>\n\n"
               comment += "```yaml\n"
               for manifest in dry_run['manifests'][:10]:  # Limit to first 10
                   comment += f"---\n{yaml.dump(manifest)}\n"
               comment += "```\n</details>\n"

           return comment

       def _format_citations_comment(self, citations: List[str]) -> str:
           """Format KB citations as markdown comment"""
           comment = "## 📚 Knowledge Base Citations\n\n"
           comment += "This configuration was generated using the following KB sources:\n\n"

           for citation in citations:
               comment += f"- {citation}\n"

           comment += "\n*These citations help track the patterns and best practices used in generation.*"

           return comment
   ```

### Day 10: Testing & Integration

#### Morning (4 hours)
1. **API Integration Tests**
   ```python
   # tests/test_infrastructure_agent.py
   import pytest
   from app.agents.infrastructure_agent import InfrastructureAgent
   from app.core.kb_manager import KnowledgeBaseManager

   @pytest.fixture
   def infra_agent():
       kb = KnowledgeBaseManager("./test_chroma")
       return InfrastructureAgent(kb)

   def test_terraform_generation(infra_agent):
       """Test Terraform module generation"""
       result = infra_agent.generate_infrastructure(
           target="k8s",
           environments=["staging", "prod"],
           domain="app.example.com",
           registry="docker.io/myorg",
           secrets_strategy="aws-secrets-manager"
       )

       assert "terraform" in result
       assert "terraform_plan" in result
       assert result["terraform_plan"]["status"] in ["success", "failed"]
       assert len(result["citations"]) > 0

   def test_helm_generation(infra_agent):
       """Test Helm chart generation"""
       result = infra_agent.generate_infrastructure(
           target="k8s",
           environments=["staging"],
           domain="app.example.com",
           registry="docker.io/myorg",
           secrets_strategy="k8s-secrets"
       )

       assert "helm" in result
       assert "helm_dry_run" in result
       assert result["helm_dry_run"]["status"] in ["success", "failed"]

       # Check for required Helm files
       helm_files = result["helm"]
       assert "Chart.yaml" in helm_files
       assert "values.yaml" in helm_files
       assert "templates/deployment.yaml" in helm_files
   ```

2. **E2E Web UI Test**
   ```typescript
   // tests/e2e/infrastructure.test.ts
   import { test, expect } from '@playwright/test';

   test.describe('Infrastructure Module', () => {
     test('should generate infrastructure with dry-run', async ({ page }) => {
       await page.goto('http://localhost:3000/infrastructure');

       // Fill form
       await page.selectOption('select[name="target"]', 'k8s');
       await page.check('input[value="staging"]');
       await page.fill('input[name="domain"]', 'app.example.com');
       await page.fill('input[name="registry"]', 'docker.io/myorg');

       // Generate
       await page.click('button:has-text("Generate Infrastructure")');

       // Wait for results
       await page.waitForSelector('text=Terraform Plan', { timeout: 30000 });

       // Verify terraform plan displayed
       await expect(page.locator('text=Plan Summary')).toBeVisible();

       // Verify helm dry-run displayed
       await expect(page.locator('text=Helm Dry-Run Results')).toBeVisible();

       // Create PR
       await page.click('button:has-text("Create PR with Artifacts")');

       // Verify PR created
       await page.waitForSelector('text=PR created with dry-run artifacts');
     });
   });
   ```

#### Afternoon (4 hours)
1. **Docker Compose Update**
   ```yaml
   # docker-compose.yml
   version: '3.8'

   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       volumes:
         - ./chroma_db:/app/chroma_db
         - ./audit_logs:/app/audit_logs
         - ./fops.db:/app/fops.db
       environment:
         - CHROMA_PERSIST_DIR=/app/chroma_db
         - AUDIT_LOG_DIR=/app/audit_logs
         - SQLITE_URL=sqlite:////app/fops.db
         - MCP_GITHUB_TOKEN=${MCP_GITHUB_TOKEN}
         - MCP_GITLAB_TOKEN=${MCP_GITLAB_TOKEN}
       command: uvicorn app.main:app --host 0.0.0.0 --reload

     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       environment:
         - VITE_API_URL=http://localhost:8000
       command: npm run dev

     terraform:
       image: hashicorp/terraform:latest
       volumes:
         - ./terraform:/workspace
       working_dir: /workspace

     helm:
       image: alpine/helm:latest
       volumes:
         - ./helm:/apps
       working_dir: /apps
   ```

2. **Documentation**
   ```markdown
   # Week 2 Deliverables

   ## Completed Features

   ### Infrastructure Agent
   - ✅ Terraform module generation for multiple targets (k8s, serverless, static)
   - ✅ Helm chart generation for Kubernetes deployments
   - ✅ `terraform plan` execution and validation
   - ✅ `helm --dry-run` execution and validation
   - ✅ KB integration with citation generation

   ### Web UI Modules
   - ✅ Pipeline Agent module with preview and PR creation
   - ✅ Infrastructure Agent module with dry-run displays
   - ✅ Citation display for all generated configs
   - ✅ Responsive design with Tailwind CSS

   ### MCP Servers
   - ✅ `mcp-terraform`: Typed interface for Terraform operations
   - ✅ `mcp-helm`: Typed interface for Helm operations
   - ✅ No raw shell execution - all typed MCP calls

   ### PR/MR Enhancements
   - ✅ Attach Terraform plan results as PR comments
   - ✅ Attach Helm dry-run results as PR comments
   - ✅ Format artifacts as readable markdown
   - ✅ Include citations in PR description

   ## Success Metrics
   - Valid Terraform plans generated: 95%+
   - Helm charts pass dry-run: 100%
   - PR creation with artifacts: 100%
   - KB citations per file: 3-5 average
   - Web UI response time: <2 seconds

   ## Example Output

   ```bash
   $ fops onboard https://github.com/acme/api --target k8s --env staging --env prod

   🚀 Onboarding repository: https://github.com/acme/api
      Target: k8s
      Environments: staging, prod

   ✅ Pipeline generated with 5 KB citations
   ✅ Infrastructure generated with 7 KB citations
   📋 Terraform plan: 12 resources to add, 0 to change, 0 to destroy
   ⎈ Helm dry-run: Passed with 5 Kubernetes resources

   📝 PR created: https://github.com/acme/api/pull/42

   PR contains:
   - .github/workflows/pipeline.yml (Pipeline Agent)
   - infra/* (Terraform modules)
   - deploy/chart/* (Helm chart)
   - Attached artifacts: terraform plan, helm dry-run results
   - Citations: [iac:terraform-k8s-001], [iac:helm-best-practices-003], ...
   ```
   ```

## Deliverables for Week 2

### Completed Components
1. ✅ **Infrastructure Agent** generating Terraform + Helm
2. ✅ `terraform plan` integration with validation
3. ✅ `helm --dry-run` execution with manifest extraction
4. ✅ Web UI: Pipeline Agent module
5. ✅ Web UI: Infrastructure Agent module
6. ✅ MCP servers: `mcp-terraform`, `mcp-helm`
7. ✅ PR/MR with attached dry-run artifacts
8. ✅ Citations for all generated configs

### Success Criteria Met
- ✅ Valid Terraform plans attached to PRs
- ✅ Helm charts pass dry-run validation
- ✅ Web UI generates PRs with complete artifacts
- ✅ All operations use typed MCP interfaces (no shell)

## Next Week Preview (Week 3)
- **Monitoring Agent**: Prometheus rules + Grafana dashboards
- Web UI: Monitoring Agent module
- Web UI: KB Connect module for documentation ingestion
- Advanced RAG pipeline with relevance scoring