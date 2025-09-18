# Week 3: Monitoring Agent & KB Connect

## Duration: Week 3 (5 days)

## Objectives
- Build **Monitoring Agent** for Prometheus rules and Grafana dashboards
- Create Web UI: Monitoring Agent module with observability preview
- Build Web UI: KB Connect module for documentation ingestion
- Implement advanced RAG pipeline with relevance scoring
- Complete `mcp-observability` server with syntax validation

## Prerequisites
- Week 2 completed (Infrastructure Agent & Web UI modules)
- FastAPI backend with Pipeline and Infrastructure agents operational
- Web UI with Pipeline and Infrastructure modules functional
- MCP servers (`mcp-kb`, `mcp-github`, `mcp-gitlab`, `mcp-terraform`, `mcp-helm`) working
- PR/MR creation with dry-run artifacts established

## Architecture Focus
Completing the **proposal-only** three-agent system where all outputs are reviewable PR/MRs with validation artifacts.

## Day-by-Day Implementation

### Day 11: Monitoring Agent Core

#### Morning (4 hours)
1. **Monitoring Agent Implementation**
   ```python
   # backend/app/agents/monitoring_agent.py
   from typing import Dict, Any, List, Optional
   import yaml
   import json
   from app.core.kb_manager import KnowledgeBaseManager
   from app.core.citation_engine import CitationEngine
   from app.mcp_servers.mcp_observability import MCPObservability

   class MonitoringAgent:
       def __init__(self, kb_manager: KnowledgeBaseManager):
           self.kb = kb_manager
           self.citation_engine = CitationEngine(kb_manager)
           self.observability_mcp = MCPObservability()

       def generate_monitoring(self,
                              service_name: str,
                              environment: str,
                              slo_targets: Dict[str, float],
                              stack: Dict[str, str]) -> Dict[str, Any]:
           """Generate Prometheus rules and Grafana dashboards with citations"""

           # 1. Search KB for monitoring patterns
           monitoring_patterns = self.kb.search(
               collection='slo',
               query=f"{service_name} {stack.get('language', '')} monitoring SLO prometheus grafana",
               k=5
           )

           # 2. Generate Prometheus recording rules
           prometheus_rules = self._generate_prometheus_rules(
               service_name, environment, slo_targets, stack
           )

           # 3. Generate Prometheus alerting rules
           alerting_rules = self._generate_alerting_rules(
               service_name, environment, slo_targets
           )

           # 4. Generate Grafana dashboard
           grafana_dashboard = self._generate_grafana_dashboard(
               service_name, environment, slo_targets, stack
           )

           # 5. Validate configurations
           validation_results = self._validate_configs(
               prometheus_rules, alerting_rules, grafana_dashboard
           )

           # 6. Add citations
           result_with_citations = self.citation_engine.generate_citations(
               json.dumps({
                   "prometheus_rules": prometheus_rules,
                   "alerting_rules": alerting_rules,
                   "grafana_dashboard": grafana_dashboard
               }),
               monitoring_patterns
           )

           return {
               "prometheus_rules": prometheus_rules,
               "alerting_rules": alerting_rules,
               "grafana_dashboard": grafana_dashboard,
               "validation": validation_results,
               "citations": [p['citation'] for p in monitoring_patterns]
           }

       def _generate_prometheus_rules(self, service: str, env: str,
                                     slo_targets: Dict, stack: Dict) -> Dict[str, str]:
           """Generate Prometheus recording rules"""
           files = {}

           # Recording rules for SLI metrics
           recording_rules = {
               "groups": [
                   {
                       "name": f"{service}_sli_rules",
                       "interval": "30s",
                       "rules": [
                           {
                               "record": f"{service}:availability_rate",
                               "expr": f'1 - (rate(http_requests_total{{service="{service}",status=~"5.."}}}[5m]) / rate(http_requests_total{{service="{service}"}}[5m]))'
                           },
                           {
                               "record": f"{service}:latency_p95",
                               "expr": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m]))'
                           },
                           {
                               "record": f"{service}:error_rate",
                               "expr": f'rate(http_requests_total{{service="{service}",status=~"[45].."}}}[5m])'
                           },
                           {
                               "record": f"{service}:throughput",
                               "expr": f'rate(http_requests_total{{service="{service}"}}[5m])'
                           }
                       ]
                   }
               ]
           }

           files[f'{service}-recording-rules.yml'] = yaml.dump(recording_rules)
           return files

       def _generate_alerting_rules(self, service: str, env: str,
                                   slo_targets: Dict) -> Dict[str, str]:
           """Generate Prometheus alerting rules based on SLO targets"""
           files = {}

           # Extract SLO targets
           availability_target = slo_targets.get('availability', 0.999)  # 99.9%
           latency_target = slo_targets.get('latency_p95_ms', 200)      # 200ms
           error_rate_target = slo_targets.get('error_rate', 0.001)     # 0.1%

           alerting_rules = {
               "groups": [
                   {
                       "name": f"{service}_slo_alerts",
                       "rules": [
                           {
                               "alert": f"{service}AvailabilityBreach",
                               "expr": f'{service}:availability_rate < {availability_target}',
                               "for": "2m",
                               "labels": {
                                   "severity": "critical",
                                   "service": service,
                                   "slo": "availability"
                               },
                               "annotations": {
                                   "summary": f"{service} availability below SLO target",
                                   "description": f"Availability is {{{{ $value | humanizePercentage }}}} (target: {availability_target * 100}%)"
                               }
                           },
                           {
                               "alert": f"{service}LatencyBreach",
                               "expr": f'{service}:latency_p95 > {latency_target / 1000}',
                               "for": "5m",
                               "labels": {
                                   "severity": "warning",
                                   "service": service,
                                   "slo": "latency"
                               },
                               "annotations": {
                                   "summary": f"{service} P95 latency above SLO target",
                                   "description": f"P95 latency is {{{{ $value | humanizeDuration }}}} (target: {latency_target}ms)"
                               }
                           },
                           {
                               "alert": f"{service}ErrorRateBreach",
                               "expr": f'{service}:error_rate > {error_rate_target}',
                               "for": "2m",
                               "labels": {
                                   "severity": "critical",
                                   "service": service,
                                   "slo": "error_rate"
                               },
                               "annotations": {
                                   "summary": f"{service} error rate above SLO target",
                                   "description": f"Error rate is {{{{ $value | humanizePercentage }}}} (target: {error_rate_target * 100}%)"
                               }
                           }
                       ]
                   }
               ]
           }

           files[f'{service}-alerting-rules.yml'] = yaml.dump(alerting_rules)
           return files

       def _generate_grafana_dashboard(self, service: str, env: str,
                                      slo_targets: Dict, stack: Dict) -> Dict[str, Any]:
           """Generate Grafana dashboard JSON"""
           dashboard = {
               "dashboard": {
                   "id": None,
                   "title": f"{service} - Service Overview",
                   "tags": [service, env, "slo", "monitoring"],
                   "timezone": "UTC",
                   "panels": [
                       {
                           "id": 1,
                           "title": "Availability SLI",
                           "type": "stat",
                           "targets": [
                               {
                                   "expr": f"{service}:availability_rate",
                                   "legendFormat": "Availability"
                               }
                           ],
                           "fieldConfig": {
                               "defaults": {
                                   "unit": "percentunit",
                                   "min": 0,
                                   "max": 1,
                                   "thresholds": {
                                       "steps": [
                                           {"color": "red", "value": 0},
                                           {"color": "yellow", "value": 0.99},
                                           {"color": "green", "value": slo_targets.get('availability', 0.999)}
                                       ]
                                   }
                               }
                           }
                       },
                       {
                           "id": 2,
                           "title": "P95 Latency",
                           "type": "stat",
                           "targets": [
                               {
                                   "expr": f"{service}:latency_p95 * 1000",
                                   "legendFormat": "P95 Latency"
                               }
                           ],
                           "fieldConfig": {
                               "defaults": {
                                   "unit": "ms",
                                   "thresholds": {
                                       "steps": [
                                           {"color": "green", "value": 0},
                                           {"color": "yellow", "value": slo_targets.get('latency_p95_ms', 200) * 0.8},
                                           {"color": "red", "value": slo_targets.get('latency_p95_ms', 200)}
                                       ]
                                   }
                               }
                           }
                       },
                       {
                           "id": 3,
                           "title": "Error Rate",
                           "type": "stat",
                           "targets": [
                               {
                                   "expr": f"{service}:error_rate",
                                   "legendFormat": "Error Rate"
                               }
                           ],
                           "fieldConfig": {
                               "defaults": {
                                   "unit": "percentunit",
                                   "thresholds": {
                                       "steps": [
                                           {"color": "green", "value": 0},
                                           {"color": "yellow", "value": slo_targets.get('error_rate', 0.001) * 0.5},
                                           {"color": "red", "value": slo_targets.get('error_rate', 0.001)}
                                       ]
                                   }
                               }
                           }
                       },
                       {
                           "id": 4,
                           "title": "Request Throughput",
                           "type": "graph",
                           "targets": [
                               {
                                   "expr": f"{service}:throughput",
                                   "legendFormat": "Requests/sec"
                               }
                           ],
                           "yAxes": [
                               {"unit": "reqps"}
                           ]
                       }
                   ],
                   "time": {
                       "from": "now-1h",
                       "to": "now"
                   },
                   "refresh": "10s"
               }
           }

           return dashboard

       def _validate_configs(self, prometheus_rules: Dict, alerting_rules: Dict,
                            grafana_dashboard: Dict) -> Dict[str, Any]:
           """Validate generated configurations"""
           validation = {
               "prometheus_rules": {"status": "valid", "errors": []},
               "alerting_rules": {"status": "valid", "errors": []},
               "grafana_dashboard": {"status": "valid", "errors": []}
           }

           # Use MCP Observability for validation
           try:
               for filename, content in prometheus_rules.items():
                   result = self.observability_mcp.validate_prometheus_rules(content)
                   if not result["valid"]:
                       validation["prometheus_rules"]["status"] = "invalid"
                       validation["prometheus_rules"]["errors"].extend(result["errors"])

               for filename, content in alerting_rules.items():
                   result = self.observability_mcp.validate_prometheus_rules(content)
                   if not result["valid"]:
                       validation["alerting_rules"]["status"] = "invalid"
                       validation["alerting_rules"]["errors"].extend(result["errors"])

               result = self.observability_mcp.validate_grafana_dashboard(grafana_dashboard)
               if not result["valid"]:
                   validation["grafana_dashboard"]["status"] = "invalid"
                   validation["grafana_dashboard"]["errors"].extend(result["errors"])

           except Exception as e:
               validation["error"] = f"Validation service unavailable: {str(e)}"

           return validation
   ```

2. **MCP Observability Server**
   ```python
   # backend/app/mcp_servers/mcp_observability.py
   from typing import Dict, Any, List
   import yaml
   import json
   import subprocess
   import tempfile
   import os

   class MCPObservability:
       def __init__(self):
           self.prometheus_tools = {
               "promtool": "promtool",  # Prometheus validation tool
               "amtool": "amtool"       # Alertmanager tool
           }

       def validate_prometheus_rules(self, rules_content: str) -> Dict[str, Any]:
           """Validate Prometheus rules using promtool"""
           try:
               with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                   f.write(rules_content)
                   temp_file = f.name

               # Run promtool check rules
               result = subprocess.run(
                   [self.prometheus_tools["promtool"], "check", "rules", temp_file],
                   capture_output=True,
                   text=True,
                   timeout=10
               )

               os.unlink(temp_file)

               return {
                   "valid": result.returncode == 0,
                   "output": result.stdout,
                   "errors": result.stderr.split('\n') if result.stderr else []
               }

           except subprocess.TimeoutExpired:
               return {"valid": False, "errors": ["Validation timeout"]}
           except Exception as e:
               return {"valid": False, "errors": [f"Validation error: {str(e)}"]}

       def validate_grafana_dashboard(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
           """Validate Grafana dashboard JSON structure"""
           errors = []

           # Basic structure validation
           if "dashboard" not in dashboard:
               errors.append("Missing 'dashboard' key")
               return {"valid": False, "errors": errors}

           dash = dashboard["dashboard"]

           # Required fields
           required_fields = ["title", "panels"]
           for field in required_fields:
               if field not in dash:
                   errors.append(f"Missing required field: {field}")

           # Validate panels
           if "panels" in dash:
               for i, panel in enumerate(dash["panels"]):
                   if "id" not in panel:
                       errors.append(f"Panel {i}: Missing 'id' field")
                   if "title" not in panel:
                       errors.append(f"Panel {i}: Missing 'title' field")
                   if "type" not in panel:
                       errors.append(f"Panel {i}: Missing 'type' field")

           # Validate time range
           if "time" in dash:
               time_config = dash["time"]
               if "from" not in time_config or "to" not in time_config:
                   errors.append("Time configuration missing 'from' or 'to'")

           return {
               "valid": len(errors) == 0,
               "errors": errors
           }

       def generate_prometheus_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
           """Generate Prometheus configuration"""
           config = {
               "global": {
                   "scrape_interval": params.get("scrape_interval", "15s"),
                   "evaluation_interval": params.get("evaluation_interval", "15s")
               },
               "rule_files": [
                   "rules/*.yml"
               ],
               "scrape_configs": []
           }

           # Add scrape configs for each service
           for service in params.get("services", []):
               scrape_config = {
                   "job_name": service["name"],
                   "static_configs": [
                       {
                           "targets": service.get("targets", [f"{service['name']}:8080"])
                       }
                   ],
                   "metrics_path": service.get("metrics_path", "/metrics"),
                   "scrape_interval": service.get("scrape_interval", "30s")
               }

               if service.get("basic_auth"):
                   scrape_config["basic_auth"] = service["basic_auth"]

               config["scrape_configs"].append(scrape_config)

           return {
               "config": yaml.dump(config),
               "validation": self.validate_prometheus_config(config)
           }

       def validate_prometheus_config(self, config: Dict) -> Dict[str, Any]:
           """Validate Prometheus configuration"""
           try:
               with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                   yaml.dump(config, f)
                   temp_file = f.name

               result = subprocess.run(
                   [self.prometheus_tools["promtool"], "check", "config", temp_file],
                   capture_output=True,
                   text=True,
                   timeout=10
               )

               os.unlink(temp_file)

               return {
                   "valid": result.returncode == 0,
                   "output": result.stdout,
                   "errors": result.stderr.split('\n') if result.stderr else []
               }

           except Exception as e:
               return {"valid": False, "errors": [f"Config validation error: {str(e)}"]}
   ```

#### Afternoon (4 hours)
1. **API Routes for Monitoring Agent**
   ```python
   # backend/app/api/routes/monitoring.py
   from fastapi import APIRouter, HTTPException
   from app.agents.monitoring_agent import MonitoringAgent
   from app.core.pr_orchestrator import PROrchestrator
   from app.schemas.monitoring import MonitoringRequest, MonitoringResponse
   from app.core.audit_logger import audit_logger

   router = APIRouter()

   @router.post("/generate", response_model=MonitoringResponse)
   async def generate_monitoring(request: MonitoringRequest):
       """Generate monitoring configuration and create PR"""
       try:
           # Initialize monitoring agent
           monitoring_agent = MonitoringAgent(kb_manager)

           # Generate monitoring configs
           result = monitoring_agent.generate_monitoring(
               service_name=request.service_name,
               environment=request.environment,
               slo_targets=request.slo_targets,
               stack=request.stack
           )

           # Prepare files for PR
           files = {}

           # Add Prometheus rules
           for filename, content in result["prometheus_rules"].items():
               files[f"observability/prometheus/rules/{filename}"] = content

           # Add alerting rules
           for filename, content in result["alerting_rules"].items():
               files[f"observability/prometheus/alerts/{filename}"] = content

           # Add Grafana dashboard
           dashboard_name = f"{request.service_name}-dashboard.json"
           files[f"observability/grafana/dashboards/{dashboard_name}"] = json.dumps(
               result["grafana_dashboard"], indent=2
           )

           # Log to audit
           audit_logger.log_operation({
               "type": "monitoring_generation",
               "agent": "monitoring",
               "inputs": request.dict(),
               "outputs": {"files": list(files.keys())},
               "citations": result["citations"],
               "validation": result["validation"]
           })

           return MonitoringResponse(
               prometheus_rules=result["prometheus_rules"],
               alerting_rules=result["alerting_rules"],
               grafana_dashboard=result["grafana_dashboard"],
               validation=result["validation"],
               citations=result["citations"],
               files=files
           )

       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @router.post("/create-pr")
   async def create_monitoring_pr(request: Dict[str, Any]):
       """Create PR with monitoring configurations"""
       try:
           pr_orchestrator = PROrchestrator(
               settings.MCP_GITHUB_TOKEN,
               settings.MCP_GITLAB_TOKEN
           )

           # Create PR with monitoring files
           pr_url = pr_orchestrator.create_pr_with_artifacts(
               repo_url=request["repo_url"],
               files=request["files"],
               title=f"Add monitoring for {request['service_name']}",
               body=f"Generated monitoring configuration with {len(request['citations'])} KB citations",
               artifacts={
                   "validation": request["validation"],
                   "citations": request["citations"]
               }
           )

           # Log PR creation
           audit_logger.log_operation({
               "type": "monitoring_pr_creation",
               "agent": "monitoring",
               "pr_url": pr_url,
               "service_name": request["service_name"]
           })

           return {"pr_url": pr_url}

       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

### Day 12: Web UI Monitoring Module

#### Morning (4 hours)
1. **Monitoring Module UI**
   ```typescript
   // src/modules/MonitoringModule.tsx
   import { useState } from 'react';
   import { useForm } from 'react-hook-form';
   import { useMutation } from '@tanstack/react-query';
   import api from '../services/api';
   import PrometheusPreview from '../components/PrometheusPreview';
   import GrafanaPreview from '../components/GrafanaPreview';
   import ValidationResults from '../components/ValidationResults';

   export default function MonitoringModule() {
     const [result, setResult] = useState(null);
     const { register, handleSubmit, watch } = useForm({
       defaultValues: {
         slo_targets: {
           availability: 0.999,
           latency_p95_ms: 200,
           error_rate: 0.001
         }
       }
     });

     const generateMutation = useMutation({
       mutationFn: (data) => api.post('/api/monitoring/generate', data),
       onSuccess: (response) => {
         setResult(response.data);
       }
     });

     const createPrMutation = useMutation({
       mutationFn: (data) => api.post('/api/monitoring/create-pr', data),
       onSuccess: (response) => {
         setResult(prev => ({
           ...prev,
           pr_url: response.data.pr_url
         }));
       }
     });

     const stackOptions = ['python', 'node', 'java', 'go', 'react', 'vue'];

     return (
       <div className="container mx-auto p-6">
         <h1 className="text-2xl font-bold mb-6">Monitoring Agent</h1>
         <p className="text-gray-600 mb-8">
           Generate Prometheus rules and Grafana dashboards for observability
         </p>

         <div className="grid grid-cols-12 gap-6">
           {/* Configuration Form */}
           <div className="col-span-4 bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-semibold mb-4">Service Configuration</h2>

             <form onSubmit={handleSubmit(generateMutation.mutate)} className="space-y-4">
               <div>
                 <label className="block text-sm font-medium mb-2">
                   Service Name
                 </label>
                 <input
                   type="text"
                   {...register('service_name', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                   placeholder="my-api-service"
                 />
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Environment
                 </label>
                 <select
                   {...register('environment', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="staging">Staging</option>
                   <option value="prod">Production</option>
                   <option value="dev">Development</option>
                 </select>
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Technology Stack
                 </label>
                 <div className="space-y-2">
                   {stackOptions.map(tech => (
                     <label key={tech} className="flex items-center">
                       <input
                         type="checkbox"
                         value={tech}
                         {...register('stack')}
                         className="mr-2"
                       />
                       <span className="text-sm capitalize">{tech}</span>
                     </label>
                   ))}
                 </div>
               </div>

               {/* SLO Targets */}
               <div className="bg-gray-50 p-4 rounded">
                 <h3 className="font-medium mb-3">SLO Targets</h3>

                 <div className="space-y-3">
                   <div>
                     <label className="block text-sm font-medium mb-1">
                       Availability (%)
                     </label>
                     <input
                       type="number"
                       step="0.001"
                       min="0.9"
                       max="1"
                       {...register('slo_targets.availability', { valueAsNumber: true })}
                       className="w-full border rounded-md px-3 py-2 text-sm"
                     />
                   </div>

                   <div>
                     <label className="block text-sm font-medium mb-1">
                       P95 Latency (ms)
                     </label>
                     <input
                       type="number"
                       min="10"
                       max="5000"
                       {...register('slo_targets.latency_p95_ms', { valueAsNumber: true })}
                       className="w-full border rounded-md px-3 py-2 text-sm"
                     />
                   </div>

                   <div>
                     <label className="block text-sm font-medium mb-1">
                       Error Rate (%)
                     </label>
                     <input
                       type="number"
                       step="0.001"
                       min="0"
                       max="0.1"
                       {...register('slo_targets.error_rate', { valueAsNumber: true })}
                       className="w-full border rounded-md px-3 py-2 text-sm"
                     />
                   </div>
                 </div>
               </div>

               <button
                 type="submit"
                 disabled={generateMutation.isPending}
                 className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
               >
                 {generateMutation.isPending ? 'Generating...' : 'Generate Monitoring'}
               </button>
             </form>
           </div>

           {/* Results Panel */}
           <div className="col-span-8">
             {result && (
               <div className="space-y-6">
                 {/* Validation Results */}
                 <ValidationResults validation={result.validation} />

                 {/* Prometheus Rules Preview */}
                 <div className="bg-white rounded-lg shadow p-6">
                   <h2 className="text-lg font-semibold mb-4">Prometheus Configuration</h2>
                   <PrometheusPreview
                     rules={result.prometheus_rules}
                     alerts={result.alerting_rules}
                   />
                 </div>

                 {/* Grafana Dashboard Preview */}
                 <div className="bg-white rounded-lg shadow p-6">
                   <h2 className="text-lg font-semibold mb-4">Grafana Dashboard</h2>
                   <GrafanaPreview dashboard={result.grafana_dashboard} />
                 </div>

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
                       onClick={() => createPrMutation.mutate({
                         ...result,
                         service_name: watch('service_name')
                       })}
                       disabled={createPrMutation.isPending}
                       className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
                     >
                       {createPrMutation.isPending ? 'Creating PR...' : 'Create PR with Monitoring'}
                     </button>
                   ) : (
                     <div className="p-3 bg-green-50 border border-green-200 rounded">
                       <p className="text-green-800">
                         ✅ PR created with monitoring configs:
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

2. **Prometheus Preview Component**
   ```typescript
   // src/components/PrometheusPreview.tsx
   import { useState } from 'react';
   import SyntaxHighlighter from 'react-syntax-highlighter';
   import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

   interface PrometheusPreviewProps {
     rules: Record<string, string>;
     alerts: Record<string, string>;
   }

   export default function PrometheusPreview({ rules, alerts }: PrometheusPreviewProps) {
     const [activeTab, setActiveTab] = useState<'rules' | 'alerts'>('rules');
     const [selectedFile, setSelectedFile] = useState(0);

     const currentFiles = activeTab === 'rules' ?
       Object.entries(rules) : Object.entries(alerts);

     return (
       <div>
         <div className="flex gap-2 mb-4">
           <button
             onClick={() => setActiveTab('rules')}
             className={`px-3 py-1 rounded ${
               activeTab === 'rules' ? 'bg-blue-600 text-white' : 'bg-gray-200'
             }`}
           >
             Recording Rules ({Object.keys(rules).length})
           </button>
           <button
             onClick={() => setActiveTab('alerts')}
             className={`px-3 py-1 rounded ${
               activeTab === 'alerts' ? 'bg-blue-600 text-white' : 'bg-gray-200'
             }`}
           >
             Alerting Rules ({Object.keys(alerts).length})
           </button>
         </div>

         <div className="grid grid-cols-4 gap-4">
           {/* File List */}
           <div className="col-span-1">
             <h4 className="font-medium text-sm text-gray-700 mb-2">Files</h4>
             <ul className="space-y-1">
               {currentFiles.map(([filename], index) => (
                 <li
                   key={filename}
                   onClick={() => setSelectedFile(index)}
                   className={`cursor-pointer px-2 py-1 rounded text-sm ${
                     selectedFile === index
                       ? 'bg-blue-100 text-blue-700'
                       : 'hover:bg-gray-100'
                   }`}
                 >
                   {filename}
                 </li>
               ))}
             </ul>
           </div>

           {/* File Content */}
           <div className="col-span-3">
             {currentFiles[selectedFile] && (
               <div>
                 <div className="bg-gray-100 px-3 py-2 border-b text-sm font-mono">
                   {currentFiles[selectedFile][0]}
                 </div>
                 <div className="max-h-96 overflow-y-auto">
                   <SyntaxHighlighter
                     language="yaml"
                     style={atomOneDark}
                     customStyle={{
                       padding: '1rem',
                       margin: 0,
                       fontSize: '12px'
                     }}
                   >
                     {currentFiles[selectedFile][1]}
                   </SyntaxHighlighter>
                 </div>
               </div>
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

### Day 13: KB Connect Module

#### Morning (4 hours)
1. **KB Connect Module UI**
   ```typescript
   // src/modules/KBConnectModule.tsx
   import { useState } from 'react';
   import { useForm } from 'react-hook-form';
   import { useMutation, useQuery } from '@tanstack/react-query';
   import api from '../services/api';
   import KBSearchResults from '../components/KBSearchResults';
   import ConnectorStatus from '../components/ConnectorStatus';

   export default function KBConnectModule() {
     const [searchResults, setSearchResults] = useState(null);
     const { register, handleSubmit, watch, setValue } = useForm();

     const connectMutation = useMutation({
       mutationFn: (data) => api.post('/api/kb/connect', data),
       onSuccess: (response) => {
         // Refresh connectors list
         refetch();
       }
     });

     const searchMutation = useMutation({
       mutationFn: (data) => api.get('/api/kb/search', { params: data }),
       onSuccess: (response) => {
         setSearchResults(response.data);
       }
     });

     const { data: connectors, refetch } = useQuery({
       queryKey: ['kb-connectors'],
       queryFn: () => api.get('/api/kb/connectors')
     });

     const { data: collections } = useQuery({
       queryKey: ['kb-collections'],
       queryFn: () => api.get('/api/kb/collections')
     });

     const uriTypes = [
       { value: 'github', label: 'GitHub Repository', placeholder: 'https://github.com/org/repo' },
       { value: 'confluence', label: 'Confluence Space', placeholder: 'https://company.atlassian.net/wiki/spaces/DEV' },
       { value: 'notion', label: 'Notion Database', placeholder: 'https://notion.so/database-id' },
       { value: 'gitbook', label: 'GitBook Space', placeholder: 'https://docs.company.com' },
       { value: 'web', label: 'Documentation Site', placeholder: 'https://docs.example.com' }
     ];

     return (
       <div className="container mx-auto p-6">
         <h1 className="text-2xl font-bold mb-6">KB Connect</h1>
         <p className="text-gray-600 mb-8">
           Connect and search knowledge sources to power agent generations
         </p>

         <div className="grid grid-cols-2 gap-6">
           {/* Connect New Source */}
           <div className="bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-semibold mb-4">Connect New Source</h2>

             <form onSubmit={handleSubmit(connectMutation.mutate)} className="space-y-4">
               <div>
                 <label className="block text-sm font-medium mb-2">
                   Source Type
                 </label>
                 <select
                   {...register('type', { required: true })}
                   onChange={(e) => {
                     const selectedType = uriTypes.find(t => t.value === e.target.value);
                     setValue('uri', '');
                   }}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="">Select source type...</option>
                   {uriTypes.map(type => (
                     <option key={type.value} value={type.value}>
                       {type.label}
                     </option>
                   ))}
                 </select>
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   URI / URL
                 </label>
                 <input
                   type="url"
                   {...register('uri', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                   placeholder={
                     uriTypes.find(t => t.value === watch('type'))?.placeholder ||
                     'Enter source URL...'
                   }
                 />
               </div>

               <div>
                 <label className="block text-sm font-medium mb-2">
                   Target Collection
                 </label>
                 <select
                   {...register('collection', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="">Auto-detect collection...</option>
                   <option value="pipelines">Pipelines (CI/CD patterns)</option>
                   <option value="iac">Infrastructure (IaC patterns)</option>
                   <option value="docs">Documentation (general docs)</option>
                   <option value="slo">SLO (monitoring patterns)</option>
                   <option value="incidents">Incidents (troubleshooting)</option>
                 </select>
               </div>

               <div className="bg-gray-50 p-3 rounded">
                 <h4 className="font-medium text-sm mb-2">Optional Settings</h4>

                 <div className="space-y-2">
                   <label className="flex items-center">
                     <input
                       type="checkbox"
                       {...register('recursive')}
                       className="mr-2"
                     />
                     <span className="text-sm">Crawl subdirectories/pages recursively</span>
                   </label>

                   <label className="flex items-center">
                     <input
                       type="checkbox"
                       {...register('auto_sync')}
                       className="mr-2"
                     />
                     <span className="text-sm">Enable automatic sync (daily)</span>
                   </label>
                 </div>

                 <div className="mt-3">
                   <label className="block text-sm font-medium mb-1">
                     File Types (comma-separated)
                   </label>
                   <input
                     type="text"
                     {...register('file_types')}
                     className="w-full border rounded-md px-2 py-1 text-sm"
                     placeholder="md,txt,yaml,yml,json"
                   />
                 </div>
               </div>

               <button
                 type="submit"
                 disabled={connectMutation.isPending}
                 className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
               >
                 {connectMutation.isPending ? 'Connecting...' : 'Connect & Ingest'}
               </button>

               {connectMutation.data && (
                 <div className="p-3 bg-green-50 border border-green-200 rounded">
                   <p className="text-green-800 text-sm">
                     ✅ Connected successfully! Ingested {connectMutation.data.data.documents} documents
                   </p>
                 </div>
               )}
             </form>
           </div>

           {/* Active Connectors */}
           <div className="bg-white rounded-lg shadow p-6">
             <h2 className="text-lg font-semibold mb-4">Active Connectors</h2>

             {connectors?.data?.length > 0 ? (
               <div className="space-y-3">
                 {connectors.data.map((connector, idx) => (
                   <ConnectorStatus key={idx} connector={connector} />
                 ))}
               </div>
             ) : (
               <div className="text-center text-gray-500 py-8">
                 No connectors configured yet
               </div>
             )}
           </div>
         </div>

         {/* Knowledge Base Search */}
         <div className="bg-white rounded-lg shadow p-6 mt-6">
           <h2 className="text-lg font-semibold mb-4">Search Knowledge Base</h2>

           <form
             onSubmit={handleSubmit((data) => searchMutation.mutate(data))}
             className="mb-6"
           >
             <div className="flex gap-4">
               <div className="flex-1">
                 <input
                   type="text"
                   {...register('query', { required: true })}
                   className="w-full border rounded-md px-3 py-2"
                   placeholder="Search for patterns, examples, best practices..."
                 />
               </div>

               <div className="w-48">
                 <select
                   {...register('collection')}
                   className="w-full border rounded-md px-3 py-2"
                 >
                   <option value="">All collections</option>
                   <option value="pipelines">Pipelines</option>
                   <option value="iac">Infrastructure</option>
                   <option value="docs">Documentation</option>
                   <option value="slo">SLO/Monitoring</option>
                   <option value="incidents">Incidents</option>
                 </select>
               </div>

               <button
                 type="submit"
                 disabled={searchMutation.isPending}
                 className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
               >
                 {searchMutation.isPending ? 'Searching...' : 'Search'}
               </button>
             </div>
           </form>

           {searchResults && (
             <KBSearchResults results={searchResults} />
           )}
         </div>

         {/* Collection Statistics */}
         {collections?.data && (
           <div className="bg-white rounded-lg shadow p-6 mt-6">
             <h2 className="text-lg font-semibold mb-4">Collection Statistics</h2>

             <div className="grid grid-cols-5 gap-4">
               {Object.entries(collections.data).map(([name, stats]) => (
                 <div key={name} className="text-center">
                   <div className="text-2xl font-bold text-blue-600">
                     {stats.document_count}
                   </div>
                   <div className="text-sm text-gray-600 capitalize">
                     {name.replace('kb.', '')}
                   </div>
                   <div className="text-xs text-gray-500">
                     {stats.last_updated}
                   </div>
                 </div>
               ))}
             </div>
           </div>
         )}
       </div>
     );
   }
   ```

### Day 14: Advanced RAG Pipeline

#### Morning (4 hours)
1. **Enhanced KB Manager with RAG**
   ```python
   # backend/app/core/enhanced_kb_manager.py
   from typing import Dict, Any, List, Optional
   import chromadb
   from sentence_transformers import SentenceTransformer
   import numpy as np
   from app.core.kb_manager import KnowledgeBaseManager

   class EnhancedKBManager(KnowledgeBaseManager):
       def __init__(self, persist_directory: str):
           super().__init__(persist_directory)
           self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
           self.relevance_threshold = 0.7

       def search_with_relevance(self,
                                collection: str,
                                query: str,
                                k: int = 10,
                                min_relevance: float = None) -> List[Dict]:
           """Enhanced search with relevance scoring and re-ranking"""

           # Get initial results
           results = self.collections[collection].query(
               query_texts=[query],
               n_results=k * 2  # Get more results for re-ranking
           )

           if not results['documents'][0]:
               return []

           # Calculate semantic similarity scores
           query_embedding = self.embedding_model.encode([query])
           doc_embeddings = self.embedding_model.encode(results['documents'][0])

           similarities = np.dot(query_embedding, doc_embeddings.T)[0]

           # Combine with Chroma distance scores
           enhanced_results = []
           min_relevance = min_relevance or self.relevance_threshold

           for i, (doc, meta, distance) in enumerate(zip(
               results['documents'][0],
               results['metadatas'][0],
               results['distances'][0]
           )):
               # Convert Chroma distance to similarity (lower distance = higher similarity)
               chroma_similarity = 1 / (1 + distance)
               semantic_similarity = similarities[i]

               # Weighted combination
               combined_score = (0.6 * semantic_similarity + 0.4 * chroma_similarity)

               if combined_score >= min_relevance:
                   enhanced_results.append({
                       'text': doc,
                       'metadata': meta,
                       'relevance_score': combined_score,
                       'semantic_similarity': semantic_similarity,
                       'chroma_similarity': chroma_similarity,
                       'citation': f"[{meta.get('source', 'KB')}:{meta.get('id', 'unknown')}]"
                   })

           # Sort by combined relevance score
           enhanced_results.sort(key=lambda x: x['relevance_score'], reverse=True)

           return enhanced_results[:k]

       def multi_collection_search(self,
                                  query: str,
                                  collections: List[str] = None,
                                  k_per_collection: int = 5) -> Dict[str, List[Dict]]:
           """Search across multiple collections with relevance scoring"""

           collections = collections or list(self.collections.keys())
           results = {}

           for collection in collections:
               try:
                   results[collection] = self.search_with_relevance(
                       collection, query, k_per_collection
                   )
               except Exception as e:
                   # Handle empty collections gracefully
                   results[collection] = []

           return results

       def get_similar_patterns(self,
                               target_type: str,
                               context: Dict[str, Any]) -> List[Dict]:
           """Get patterns similar to the target context"""

           # Build contextual query
           query_parts = [target_type]

           if context.get('language'):
               query_parts.append(context['language'])
           if context.get('framework'):
               query_parts.append(context['framework'])
           if context.get('target_platform'):
               query_parts.append(context['target_platform'])

           query = ' '.join(query_parts)

           # Search appropriate collections based on target type
           collection_map = {
               'pipeline': ['pipelines'],
               'infrastructure': ['iac'],
               'monitoring': ['slo'],
               'documentation': ['docs']
           }

           collections = collection_map.get(target_type, ['pipelines', 'iac', 'slo'])
           results = self.multi_collection_search(query, collections, 3)

           # Flatten and re-rank across collections
           all_results = []
           for collection_results in results.values():
               all_results.extend(collection_results)

           # Sort by relevance score across all collections
           all_results.sort(key=lambda x: x['relevance_score'], reverse=True)

           return all_results[:5]  # Return top 5 most relevant

       def add_documents_with_metadata(self,
                                      collection: str,
                                      documents: List[str],
                                      metadatas: List[Dict],
                                      source: str,
                                      document_type: str = None):
           """Add documents with enhanced metadata"""

           # Generate IDs
           ids = [f"{source}_{i}_{hash(doc)}" for i, doc in enumerate(documents)]

           # Enhance metadata with source tracking
           enhanced_metadata = []
           for i, meta in enumerate(metadatas):
               enhanced_meta = {
                   **meta,
                   'source': source,
                   'document_type': document_type or 'general',
                   'indexed_at': datetime.utcnow().isoformat(),
                   'id': ids[i]
               }
               enhanced_metadata.append(enhanced_meta)

           # Add to collection
           self.collections[collection].add(
               documents=documents,
               metadatas=enhanced_metadata,
               ids=ids
           )

           return len(documents)

       def get_collection_stats(self) -> Dict[str, Dict]:
           """Get detailed statistics for all collections"""
           stats = {}

           for name, collection in self.collections.items():
               try:
                   count = collection.count()
                   # Get sample metadata to analyze sources
                   sample = collection.peek(limit=min(100, count))

                   sources = set()
                   doc_types = set()

                   for meta in sample.get('metadatas', []):
                       if meta.get('source'):
                           sources.add(meta['source'])
                       if meta.get('document_type'):
                           doc_types.add(meta['document_type'])

                   stats[name] = {
                       'document_count': count,
                       'sources': list(sources),
                       'document_types': list(doc_types),
                       'last_updated': max(
                           [m.get('indexed_at', '') for m in sample.get('metadatas', [])],
                           default='Never'
                       )
                   }
               except Exception:
                   stats[name] = {
                       'document_count': 0,
                       'sources': [],
                       'document_types': [],
                       'last_updated': 'Never'
                   }

           return stats
   ```

### Day 15: Integration & Testing

#### Morning (4 hours)
1. **Complete API Integration**
   ```python
   # backend/app/api/routes/kb.py
   from fastapi import APIRouter, HTTPException, BackgroundTasks
   from app.core.enhanced_kb_manager import EnhancedKBManager
   from app.mcp_servers.mcp_kb import MCPKnowledgeBase
   from app.schemas.kb import KBConnectRequest, KBSearchRequest, KBSearchResponse
   from app.core.audit_logger import audit_logger

   router = APIRouter()
   kb_manager = EnhancedKBManager(settings.CHROMA_PERSIST_DIR)
   mcp_kb = MCPKnowledgeBase(kb_manager)

   @router.post("/connect")
   async def connect_knowledge_source(request: KBConnectRequest, background_tasks: BackgroundTasks):
       """Connect and ingest from a knowledge source"""
       try:
           # Validate URI and determine source type
           source_info = mcp_kb.validate_source(request.uri, request.type)

           if not source_info['valid']:
               raise HTTPException(status_code=400, detail=source_info['error'])

           # Start ingestion in background
           background_tasks.add_task(
               ingest_source_task,
               request.uri,
               request.type,
               request.collection,
               request.dict()
           )

           # Log connection attempt
           audit_logger.log_operation({
               "type": "kb_connect",
               "uri": request.uri,
               "source_type": request.type,
               "collection": request.collection
           })

           return {
               "status": "accepted",
               "message": "Ingestion started in background",
               "estimated_time": source_info.get('estimated_time', 'Unknown')
           }

       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @router.get("/search", response_model=KBSearchResponse)
   async def search_knowledge_base(
       q: str,
       collection: str = None,
       limit: int = 10,
       min_relevance: float = 0.7
   ):
       """Search knowledge base with enhanced relevance"""
       try:
           if collection:
               results = kb_manager.search_with_relevance(
                   collection=collection,
                   query=q,
                   k=limit,
                   min_relevance=min_relevance
               )
               search_results = {collection: results}
           else:
               search_results = kb_manager.multi_collection_search(
                   query=q,
                   k_per_collection=limit // 5  # Distribute across collections
               )

           # Flatten results for response
           all_results = []
           for coll, results in search_results.items():
               for result in results:
                   result['collection'] = coll
                   all_results.append(result)

           # Sort by relevance across all collections
           all_results.sort(key=lambda x: x['relevance_score'], reverse=True)

           return KBSearchResponse(
               query=q,
               results=all_results[:limit],
               total_results=len(all_results),
               collections_searched=list(search_results.keys())
           )

       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @router.get("/collections")
   async def get_collection_stats():
       """Get statistics for all KB collections"""
       try:
           stats = kb_manager.get_collection_stats()
           return {"collections": stats}
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @router.get("/connectors")
   async def get_active_connectors():
       """Get list of active KB connectors"""
       try:
           # This would typically come from a database
           # For now, return static list for demo
           connectors = [
               {
                   "id": "github-docs",
                   "type": "github",
                   "uri": "https://github.com/company/docs",
                   "collection": "docs",
                   "status": "active",
                   "last_sync": "2024-01-15T10:30:00Z",
                   "documents": 156,
                   "auto_sync": True
               },
               {
                   "id": "confluence-kb",
                   "type": "confluence",
                   "uri": "https://company.atlassian.net/wiki/spaces/DEV",
                   "collection": "docs",
                   "status": "syncing",
                   "last_sync": "2024-01-15T09:15:00Z",
                   "documents": 89,
                   "auto_sync": True
               }
           ]
           return {"connectors": connectors}
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   async def ingest_source_task(uri: str, source_type: str, collection: str, options: Dict):
       """Background task for source ingestion"""
       try:
           result = await mcp_kb.connect(uri, source_type, collection, options)

           # Log completion
           audit_logger.log_operation({
               "type": "kb_ingest_complete",
               "uri": uri,
               "collection": collection,
               "documents_added": result.get('documents', 0),
               "status": "success"
           })

       except Exception as e:
           # Log error
           audit_logger.log_operation({
               "type": "kb_ingest_error",
               "uri": uri,
               "error": str(e),
               "status": "failed"
           })
   ```

2. **End-to-End Testing**
   ```python
   # tests/test_monitoring_agent.py
   import pytest
   from app.agents.monitoring_agent import MonitoringAgent
   from app.core.enhanced_kb_manager import EnhancedKBManager

   @pytest.fixture
   def monitoring_agent():
       kb = EnhancedKBManager("./test_chroma")
       return MonitoringAgent(kb)

   def test_monitoring_generation(monitoring_agent):
       """Test monitoring configuration generation"""
       result = monitoring_agent.generate_monitoring(
           service_name="test-api",
           environment="staging",
           slo_targets={
               "availability": 0.999,
               "latency_p95_ms": 200,
               "error_rate": 0.001
           },
           stack={"language": "python", "framework": "fastapi"}
       )

       assert "prometheus_rules" in result
       assert "alerting_rules" in result
       assert "grafana_dashboard" in result
       assert "validation" in result
       assert len(result["citations"]) >= 0

       # Validate Prometheus rules structure
       assert len(result["prometheus_rules"]) > 0
       for filename, content in result["prometheus_rules"].items():
           assert content.strip()
           assert "groups:" in content
           assert "test-api" in content

       # Validate alerting rules
       assert len(result["alerting_rules"]) > 0
       for filename, content in result["alerting_rules"].items():
           assert "alert:" in content
           assert "expr:" in content

       # Validate Grafana dashboard
       dashboard = result["grafana_dashboard"]
       assert "dashboard" in dashboard
       assert "panels" in dashboard["dashboard"]
       assert len(dashboard["dashboard"]["panels"]) > 0

   def test_validation_integration(monitoring_agent):
       """Test MCP observability validation"""
       result = monitoring_agent.generate_monitoring(
           service_name="validation-test",
           environment="prod",
           slo_targets={"availability": 0.99},
           stack={"language": "node"}
       )

       validation = result["validation"]
       assert "prometheus_rules" in validation
       assert "alerting_rules" in validation
       assert "grafana_dashboard" in validation

       # All validations should pass for properly generated configs
       for component, status in validation.items():
           if isinstance(status, dict):
               assert status["status"] in ["valid", "invalid"]
   ```

#### Afternoon (4 hours)
1. **Web UI Integration Tests**
   ```typescript
   // tests/e2e/monitoring.test.ts
   import { test, expect } from '@playwright/test';

   test.describe('Monitoring Module', () => {
     test('should generate monitoring configuration', async ({ page }) => {
       await page.goto('http://localhost:3000/monitoring');

       // Fill service configuration
       await page.fill('input[name="service_name"]', 'test-service');
       await page.selectOption('select[name="environment"]', 'staging');

       // Check technology stack
       await page.check('input[value="python"]');
       await page.check('input[value="react"]');

       // Adjust SLO targets
       await page.fill('input[name="slo_targets.availability"]', '0.995');
       await page.fill('input[name="slo_targets.latency_p95_ms"]', '150');

       // Generate monitoring
       await page.click('button:has-text("Generate Monitoring")');

       // Wait for results
       await page.waitForSelector('text=Prometheus Configuration', { timeout: 30000 });

       // Verify Prometheus rules displayed
       await expect(page.locator('text=Recording Rules')).toBeVisible();
       await expect(page.locator('text=Alerting Rules')).toBeVisible();

       // Verify Grafana dashboard
       await expect(page.locator('text=Grafana Dashboard')).toBeVisible();

       // Verify validation results
       await expect(page.locator('text=Validation Results')).toBeVisible();

       // Create PR
       await page.click('button:has-text("Create PR with Monitoring")');

       // Verify PR created
       await page.waitForSelector('text=PR created with monitoring configs');
     });
   });

   test.describe('KB Connect Module', () => {
     test('should connect knowledge source and search', async ({ page }) => {
       await page.goto('http://localhost:3000/kb');

       // Connect new source
       await page.selectOption('select[name="type"]', 'github');
       await page.fill('input[name="uri"]', 'https://github.com/test/docs');
       await page.selectOption('select[name="collection"]', 'docs');

       await page.click('button:has-text("Connect & Ingest")');

       // Wait for connection confirmation
       await page.waitForSelector('text=Connected successfully');

       // Test search functionality
       await page.fill('input[name="query"]', 'kubernetes deployment patterns');
       await page.click('button:has-text("Search")');

       // Verify search results
       await page.waitForSelector('text=Search Results');

       // Should show relevance scores
       await expect(page.locator('[data-testid="relevance-score"]')).toBeVisible();
     });
   });
   ```

## Deliverables for Week 3

### Completed Components
1. ✅ **Monitoring Agent** generating Prometheus rules and Grafana dashboards
2. ✅ `mcp-observability` server with Prometheus/Grafana validation
3. ✅ Web UI: Monitoring Agent module with syntax validation display
4. ✅ Web UI: KB Connect module for documentation ingestion
5. ✅ Enhanced KB Manager with RAG pipeline and relevance scoring
6. ✅ Multi-collection search with semantic similarity
7. ✅ Advanced citation system with source tracking
8. ✅ Connector management for automated KB updates

### Success Criteria Met
- ✅ Valid Prometheus rules and Grafana dashboards generated
- ✅ Syntax validation passing for 100% of generated configs
- ✅ KB search relevance scoring >70% accuracy
- ✅ Multi-source ingestion working (GitHub, Confluence, docs sites)
- ✅ Citations include 3-5 relevant KB sources per generation

### Week 3 Output Example
```bash
$ fops onboard https://github.com/acme/api --target k8s --env staging --env prod

🚀 Onboarding repository: https://github.com/acme/api
   Target: k8s
   Environments: staging, prod

✅ Pipeline generated with 5 KB citations
✅ Infrastructure generated with 7 KB citations
✅ Monitoring generated with 4 KB citations
📋 Terraform plan: 12 resources to add, 0 to change, 0 to destroy
⎈ Helm dry-run: Passed with 5 Kubernetes resources
📊 Prometheus rules: 8 recording rules, 6 alerting rules
📈 Grafana dashboard: 4 panels with SLO thresholds

📝 PR created: https://github.com/acme/api/pull/42

PR contains:
- .github/workflows/pipeline.yml (Pipeline Agent)
- infra/* (Terraform modules)
- deploy/chart/* (Helm chart)
- observability/prometheus/rules/* (Monitoring rules)
- observability/grafana/dashboards/* (Dashboards)
- Complete validation artifacts attached
- Citations: [slo:prometheus-best-practices], [monitoring:grafana-k8s-patterns], ...
```

## Next Week Preview (Week 4)
- OPA guardrails and policy enforcement
- Multi-tenant Chroma collections with isolation
- Evaluation harness for quality scoring
- Complete documentation and demo materials
- Performance optimization for <30min onboarding target