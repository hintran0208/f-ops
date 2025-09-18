# Phase 3: Incidents & Advanced Knowledge Base Implementation

## Duration: Week 3 (5 days)

## Objectives
- Build comprehensive incident management dashboard
- Implement advanced knowledge base features with RAG
- Create learning path integration
- Establish observability integration
- Add career development features

## Prerequisites from Phase 2
- ✅ Web UI operational
- ✅ Deployment workflows complete
- ✅ Basic knowledge base functional
- ✅ Authentication and authorization ready
- ✅ WebSocket infrastructure established

## Day-by-Day Breakdown

### Day 11: Incident Management Core

#### Morning (4 hours)
1. **Incident Detection System**
   ```python
   # backend/app/core/incident_detector.py
   from typing import Dict, Any, List, Optional
   from datetime import datetime, timedelta
   import asyncio
   from app.core.knowledge_base import KnowledgeBase
   from app.models.incident import Incident, IncidentSeverity
   
   class IncidentDetector:
       def __init__(self):
           self.kb = KnowledgeBase()
           self.thresholds = self.load_thresholds()
           self.detectors = [
               self.detect_error_spike,
               self.detect_performance_degradation,
               self.detect_availability_issues,
               self.detect_security_anomalies
           ]
       
       async def run_detection_cycle(self):
           """Run all detection algorithms"""
           incidents = []
           
           for detector in self.detectors:
               detected = await detector()
               if detected:
                   incidents.extend(detected)
           
           # Correlate and deduplicate incidents
           correlated = self.correlate_incidents(incidents)
           
           # Enrich with knowledge base
           enriched = await self.enrich_incidents(correlated)
           
           return enriched
       
       async def detect_error_spike(self) -> List[Incident]:
           """Detect error rate spikes using statistical analysis"""
           incidents = []
           
           # Get error metrics from monitoring systems
           metrics = await self.get_error_metrics()
           
           for service, data in metrics.items():
               baseline = data['baseline']
               current = data['current']
               
               if current > baseline * self.thresholds['error_spike_multiplier']:
                   incident = Incident(
                       title=f"Error spike detected in {service}",
                       severity=self.calculate_severity(current, baseline),
                       service=service,
                       detected_at=datetime.utcnow(),
                       metrics={
                           'error_rate': current,
                           'baseline': baseline,
                           'spike_ratio': current / baseline
                       }
                   )
                   incidents.append(incident)
           
           return incidents
       
       async def detect_performance_degradation(self) -> List[Incident]:
           """Detect performance issues using percentile analysis"""
           incidents = []
           
           # Get performance metrics
           metrics = await self.get_performance_metrics()
           
           for service, data in metrics.items():
               p95 = data['p95_latency']
               threshold = self.thresholds['p95_latency_threshold']
               
               if p95 > threshold:
                   incident = Incident(
                       title=f"Performance degradation in {service}",
                       severity=IncidentSeverity.MEDIUM,
                       service=service,
                       detected_at=datetime.utcnow(),
                       metrics={
                           'p95_latency': p95,
                           'p99_latency': data['p99_latency'],
                           'threshold': threshold
                       }
                   )
                   incidents.append(incident)
           
           return incidents
       
       def correlate_incidents(self, incidents: List[Incident]) -> List[Incident]:
           """Correlate related incidents to reduce noise"""
           correlated = []
           processed = set()
           
           for i, incident in enumerate(incidents):
               if i in processed:
                   continue
               
               # Find related incidents
               related = []
               for j, other in enumerate(incidents[i+1:], i+1):
                   if self.are_related(incident, other):
                       related.append(other)
                       processed.add(j)
               
               if related:
                   # Merge related incidents
                   incident = self.merge_incidents(incident, related)
               
               correlated.append(incident)
           
           return correlated
       
       async def enrich_incidents(self, incidents: List[Incident]) -> List[Incident]:
           """Enrich incidents with knowledge base information"""
           for incident in incidents:
               # Search for similar past incidents
               similar = await self.kb.search(
                   collection='incidents',
                   query=incident.title,
                   k=3
               )
               
               if similar:
                   incident.similar_incidents = similar
                   incident.suggested_actions = self.extract_actions(similar)
                   incident.estimated_mttr = self.estimate_mttr(similar)
           
           return incidents
   ```

2. **Root Cause Analysis Engine**
   ```python
   # backend/app/core/rca_engine.py
   from typing import Dict, Any, List, Optional
   import networkx as nx
   from langchain import LLMChain, PromptTemplate
   
   class RCAEngine:
       def __init__(self):
           self.dependency_graph = self.build_dependency_graph()
           self.llm_chain = self.setup_llm_chain()
       
       def build_dependency_graph(self) -> nx.DiGraph:
           """Build service dependency graph"""
           G = nx.DiGraph()
           
           # Add nodes (services)
           services = self.get_services()
           for service in services:
               G.add_node(service['name'], **service)
           
           # Add edges (dependencies)
           dependencies = self.get_dependencies()
           for dep in dependencies:
               G.add_edge(dep['from'], dep['to'], **dep)
           
           return G
       
       async def analyze_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
           """Perform root cause analysis for an incident"""
           
           # Step 1: Trace through dependency graph
           affected_services = self.trace_dependencies(incident['service'])
           
           # Step 2: Collect metrics and logs
           evidence = await self.collect_evidence(
               incident['service'],
               incident['detected_at'],
               affected_services
           )
           
           # Step 3: Analyze patterns
           patterns = self.analyze_patterns(evidence)
           
           # Step 4: Use LLM for intelligent analysis
           llm_analysis = await self.llm_analysis(incident, evidence, patterns)
           
           # Step 5: Generate RCA report
           rca_report = {
               'incident_id': incident['id'],
               'root_causes': llm_analysis['root_causes'],
               'contributing_factors': patterns['anomalies'],
               'affected_services': affected_services,
               'timeline': self.build_timeline(evidence),
               'recommendations': llm_analysis['recommendations'],
               'evidence': evidence,
               'confidence_score': llm_analysis['confidence']
           }
           
           return rca_report
       
       def trace_dependencies(self, service: str) -> List[str]:
           """Trace service dependencies using graph traversal"""
           affected = set()
           
           # Upstream dependencies (services this depends on)
           upstream = nx.ancestors(self.dependency_graph, service)
           affected.update(upstream)
           
           # Downstream dependencies (services depending on this)
           downstream = nx.descendants(self.dependency_graph, service)
           affected.update(downstream)
           
           return list(affected)
       
       async def collect_evidence(
           self,
           service: str,
           incident_time: datetime,
           related_services: List[str]
       ) -> Dict[str, Any]:
           """Collect evidence from multiple sources"""
           
           evidence = {
               'logs': await self.get_logs(service, incident_time),
               'metrics': await self.get_metrics(service, incident_time),
               'traces': await self.get_traces(service, incident_time),
               'events': await self.get_events(service, incident_time),
               'changes': await self.get_recent_changes(service, incident_time)
           }
           
           # Collect evidence for related services
           for related_service in related_services:
               evidence[f'{related_service}_logs'] = await self.get_logs(
                   related_service, incident_time
               )
               evidence[f'{related_service}_metrics'] = await self.get_metrics(
                   related_service, incident_time
               )
           
           return evidence
       
       def setup_llm_chain(self) -> LLMChain:
           """Setup LLM for intelligent RCA"""
           prompt = PromptTemplate(
               input_variables=["incident", "evidence", "patterns"],
               template="""
               Analyze the following incident and provide root cause analysis:
               
               Incident: {incident}
               
               Evidence collected:
               {evidence}
               
               Patterns detected:
               {patterns}
               
               Provide:
               1. Most likely root causes (with confidence scores)
               2. Contributing factors
               3. Recommended immediate actions
               4. Long-term prevention strategies
               5. Similar past incidents and their resolutions
               
               Format the response as JSON.
               """
           )
           
           return LLMChain(llm=self.llm, prompt=prompt)
   ```

#### Afternoon (4 hours)
1. **Incident Dashboard UI**
   ```typescript
   // src/pages/Incidents.tsx
   import { useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import IncidentList from '../components/incidents/IncidentList';
   import IncidentDetails from '../components/incidents/IncidentDetails';
   import RCAView from '../components/incidents/RCAView';
   import IncidentTimeline from '../components/incidents/IncidentTimeline';
   import api from '../services/api';
   
   export default function Incidents() {
     const [selectedIncident, setSelectedIncident] = useState(null);
     const [view, setView] = useState<'details' | 'rca' | 'timeline'>('details');
     
     const { data: incidents, isLoading } = useQuery({
       queryKey: ['incidents'],
       queryFn: () => api.get('/incidents'),
       refetchInterval: 30000, // Refresh every 30 seconds
     });
     
     const getSeverityColor = (severity: string) => {
       switch (severity) {
         case 'critical': return 'bg-red-100 text-red-800 border-red-200';
         case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
         case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
         case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
         default: return 'bg-gray-100 text-gray-800 border-gray-200';
       }
     };
     
     return (
       <div className="container mx-auto px-4 py-8">
         <div className="flex justify-between items-center mb-6">
           <h1 className="text-2xl font-bold">Incident Management</h1>
           <div className="flex space-x-2">
             <button className="px-4 py-2 bg-primary-600 text-white rounded-md">
               Create Incident
             </button>
             <button className="px-4 py-2 border border-gray-300 rounded-md">
               Export Report
             </button>
           </div>
         </div>
         
         {/* Summary Cards */}
         <div className="grid grid-cols-4 gap-4 mb-6">
           <div className="bg-white rounded-lg shadow p-4">
             <div className="flex items-center justify-between">
               <div>
                 <p className="text-sm text-gray-500">Active Incidents</p>
                 <p className="text-2xl font-bold">{incidents?.data?.active || 0}</p>
               </div>
               <div className="p-3 bg-red-100 rounded-full">
                 <AlertIcon className="h-6 w-6 text-red-600" />
               </div>
             </div>
           </div>
           
           <div className="bg-white rounded-lg shadow p-4">
             <div className="flex items-center justify-between">
               <div>
                 <p className="text-sm text-gray-500">Avg MTTR</p>
                 <p className="text-2xl font-bold">{incidents?.data?.avgMttr || '0'}m</p>
               </div>
               <div className="p-3 bg-blue-100 rounded-full">
                 <ClockIcon className="h-6 w-6 text-blue-600" />
               </div>
             </div>
           </div>
           
           <div className="bg-white rounded-lg shadow p-4">
             <div className="flex items-center justify-between">
               <div>
                 <p className="text-sm text-gray-500">Resolved Today</p>
                 <p className="text-2xl font-bold">{incidents?.data?.resolvedToday || 0}</p>
               </div>
               <div className="p-3 bg-green-100 rounded-full">
                 <CheckIcon className="h-6 w-6 text-green-600" />
               </div>
             </div>
           </div>
           
           <div className="bg-white rounded-lg shadow p-4">
             <div className="flex items-center justify-between">
               <div>
                 <p className="text-sm text-gray-500">On-Call</p>
                 <p className="text-lg font-bold">{incidents?.data?.onCall || 'Team A'}</p>
               </div>
               <div className="p-3 bg-purple-100 rounded-full">
                 <UserIcon className="h-6 w-6 text-purple-600" />
               </div>
             </div>
           </div>
         </div>
         
         {/* Main Content */}
         <div className="grid grid-cols-12 gap-6">
           <div className="col-span-4">
             <IncidentList
               incidents={incidents?.data?.list || []}
               selectedId={selectedIncident?.id}
               onSelect={setSelectedIncident}
               getSeverityColor={getSeverityColor}
               isLoading={isLoading}
             />
           </div>
           
           <div className="col-span-8">
             {selectedIncident ? (
               <div className="bg-white rounded-lg shadow">
                 <div className="border-b">
                   <div className="flex">
                     <button
                       onClick={() => setView('details')}
                       className={`px-4 py-3 font-medium ${
                         view === 'details'
                           ? 'border-b-2 border-primary-600 text-primary-600'
                           : 'text-gray-500'
                       }`}
                     >
                       Details
                     </button>
                     <button
                       onClick={() => setView('rca')}
                       className={`px-4 py-3 font-medium ${
                         view === 'rca'
                           ? 'border-b-2 border-primary-600 text-primary-600'
                           : 'text-gray-500'
                       }`}
                     >
                       Root Cause Analysis
                     </button>
                     <button
                       onClick={() => setView('timeline')}
                       className={`px-4 py-3 font-medium ${
                         view === 'timeline'
                           ? 'border-b-2 border-primary-600 text-primary-600'
                           : 'text-gray-500'
                       }`}
                     >
                       Timeline
                     </button>
                   </div>
                 </div>
                 
                 <div className="p-6">
                   {view === 'details' && (
                     <IncidentDetails incident={selectedIncident} />
                   )}
                   {view === 'rca' && (
                     <RCAView incidentId={selectedIncident.id} />
                   )}
                   {view === 'timeline' && (
                     <IncidentTimeline incidentId={selectedIncident.id} />
                   )}
                 </div>
               </div>
             ) : (
               <div className="bg-gray-50 rounded-lg p-12 text-center text-gray-500">
                 Select an incident to view details
               </div>
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

2. **RCA View Component**
   ```typescript
   // src/components/incidents/RCAView.tsx
   import { useQuery } from '@tanstack/react-query';
   import { useState } from 'react';
   import ReactFlow, { Node, Edge } from 'reactflow';
   import api from '../../services/api';
   
   export default function RCAView({ incidentId }) {
     const [selectedCause, setSelectedCause] = useState(null);
     
     const { data: rca, isLoading } = useQuery({
       queryKey: ['rca', incidentId],
       queryFn: () => api.get(`/incidents/${incidentId}/rca`),
     });
     
     if (isLoading) {
       return (
         <div className="flex items-center justify-center h-64">
           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
           <span className="ml-3">Analyzing incident...</span>
         </div>
       );
     }
     
     const { root_causes, contributing_factors, recommendations, timeline } = rca?.data || {};
     
     return (
       <div className="space-y-6">
         {/* Root Causes */}
         <div>
           <h3 className="text-lg font-medium mb-3">Root Causes</h3>
           <div className="space-y-3">
             {root_causes?.map((cause, index) => (
               <div
                 key={index}
                 className="bg-red-50 border border-red-200 rounded-lg p-4"
               >
                 <div className="flex justify-between items-start">
                   <div>
                     <h4 className="font-medium text-red-900">{cause.title}</h4>
                     <p className="text-sm text-red-700 mt-1">{cause.description}</p>
                   </div>
                   <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                     {cause.confidence}% confidence
                   </span>
                 </div>
                 
                 {cause.evidence && (
                   <div className="mt-3">
                     <p className="text-xs font-medium text-red-700">Evidence:</p>
                     <ul className="mt-1 space-y-1">
                       {cause.evidence.map((item, i) => (
                         <li key={i} className="text-xs text-red-600">• {item}</li>
                       ))}
                     </ul>
                   </div>
                 )}
               </div>
             ))}
           </div>
         </div>
         
         {/* Contributing Factors */}
         <div>
           <h3 className="text-lg font-medium mb-3">Contributing Factors</h3>
           <div className="grid grid-cols-2 gap-3">
             {contributing_factors?.map((factor, index) => (
               <div
                 key={index}
                 className="bg-yellow-50 border border-yellow-200 rounded-lg p-3"
               >
                 <h4 className="font-medium text-yellow-900 text-sm">{factor.title}</h4>
                 <p className="text-xs text-yellow-700 mt-1">{factor.impact}</p>
               </div>
             ))}
           </div>
         </div>
         
         {/* Service Dependency Graph */}
         <div>
           <h3 className="text-lg font-medium mb-3">Service Impact Analysis</h3>
           <div className="bg-gray-50 rounded-lg p-4 h-64">
             <ReactFlow
               nodes={rca?.data?.dependency_nodes || []}
               edges={rca?.data?.dependency_edges || []}
               fitView
             />
           </div>
         </div>
         
         {/* Recommendations */}
         <div>
           <h3 className="text-lg font-medium mb-3">Recommendations</h3>
           <div className="space-y-3">
             {recommendations?.map((rec, index) => (
               <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                 <div className="flex items-start">
                   <div className={`px-2 py-1 rounded text-xs font-medium mr-3 ${
                     rec.priority === 'immediate' ? 'bg-red-100 text-red-800' :
                     rec.priority === 'short-term' ? 'bg-yellow-100 text-yellow-800' :
                     'bg-green-100 text-green-800'
                   }`}>
                     {rec.priority}
                   </div>
                   <div className="flex-1">
                     <h4 className="font-medium text-blue-900">{rec.title}</h4>
                     <p className="text-sm text-blue-700 mt-1">{rec.description}</p>
                     
                     {rec.actions && (
                       <div className="mt-3">
                         <p className="text-xs font-medium text-blue-700">Actions:</p>
                         <ol className="mt-1 space-y-1">
                           {rec.actions.map((action, i) => (
                             <li key={i} className="text-xs text-blue-600">
                               {i + 1}. {action}
                             </li>
                           ))}
                         </ol>
                       </div>
                     )}
                     
                     <button className="mt-3 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700">
                       Execute Action
                     </button>
                   </div>
                 </div>
               </div>
             ))}
           </div>
         </div>
         
         {/* Similar Past Incidents */}
         <div>
           <h3 className="text-lg font-medium mb-3">Similar Past Incidents</h3>
           <div className="space-y-2">
             {rca?.data?.similar_incidents?.map((incident, index) => (
               <div key={index} className="bg-gray-50 rounded-lg p-3">
                 <div className="flex justify-between items-start">
                   <div>
                     <h4 className="font-medium text-sm">{incident.title}</h4>
                     <p className="text-xs text-gray-600 mt-1">
                       {incident.date} • Resolved in {incident.mttr}
                     </p>
                   </div>
                   <span className="text-xs text-gray-500">{incident.similarity}% similar</span>
                 </div>
                 {incident.resolution && (
                   <p className="text-xs text-gray-700 mt-2">
                     <strong>Resolution:</strong> {incident.resolution}
                   </p>
                 )}
               </div>
             ))}
           </div>
         </div>
       </div>
     );
   }
   ```

### Day 12: Advanced Knowledge Base with RAG

#### Morning (4 hours)
1. **RAG Planner Implementation**
   ```python
   # backend/app/core/rag_planner.py
   from typing import Dict, Any, List, Optional
   from langchain import LLMChain, PromptTemplate
   from langchain.memory import ConversationBufferMemory
   from app.core.knowledge_base import KnowledgeBase
   import json
   
   class RAGPlanner:
       def __init__(self):
           self.kb = KnowledgeBase()
           self.memory = ConversationBufferMemory()
           self.setup_chains()
       
       def setup_chains(self):
           """Setup LangChain components for RAG"""
           
           # Context detection chain
           self.context_chain = LLMChain(
               llm=self.llm,
               prompt=PromptTemplate(
                   input_variables=["request"],
                   template="""
                   Analyze the following request and extract:
                   1. Technology stack
                   2. Environment (dev/staging/prod)
                   3. Intent (deploy/troubleshoot/optimize/etc)
                   4. Constraints or requirements
                   
                   Request: {request}
                   
                   Return as JSON.
                   """
               )
           )
           
           # Plan generation chain
           self.plan_chain = LLMChain(
               llm=self.llm,
               prompt=PromptTemplate(
                   input_variables=["context", "retrieved_docs", "request"],
                   template="""
                   Create a detailed plan based on:
                   
                   Context: {context}
                   Request: {request}
                   
                   Retrieved Knowledge:
                   {retrieved_docs}
                   
                   Generate a step-by-step plan that:
                   1. Addresses all requirements
                   2. Follows best practices from the knowledge base
                   3. Includes specific commands and configurations
                   4. Cites sources for each recommendation
                   5. Provides alternative approaches if applicable
                   
                   Format as JSON with steps, commands, and citations.
                   """
               )
           )
       
       async def generate_plan(self, request: str) -> Dict[str, Any]:
           """Generate a plan using RAG"""
           
           # Step 1: Detect context
           context = await self.detect_context(request)
           
           # Step 2: Query knowledge base
           retrieved_docs = await self.retrieve_relevant_docs(request, context)
           
           # Step 3: Generate plan with citations
           plan = await self.create_plan(request, context, retrieved_docs)
           
           # Step 4: Validate plan
           validated_plan = await self.validate_plan(plan)
           
           # Step 5: Add dry-run commands
           final_plan = self.add_dry_run_steps(validated_plan)
           
           return {
               'plan': final_plan,
               'context': context,
               'sources': self.extract_sources(retrieved_docs),
               'confidence': self.calculate_confidence(final_plan, retrieved_docs)
           }
       
       async def retrieve_relevant_docs(
           self,
           request: str,
           context: Dict[str, Any]
       ) -> List[Dict[str, Any]]:
           """Retrieve relevant documents from knowledge base"""
           
           docs = []
           
           # Query different collections based on context
           if context['intent'] == 'deploy':
               pipeline_docs = await self.kb.search('pipelines', request, k=5)
               iac_docs = await self.kb.search('iac', request, k=3)
               docs.extend(pipeline_docs + iac_docs)
           
           elif context['intent'] == 'troubleshoot':
               incident_docs = await self.kb.search('incidents', request, k=5)
               slo_docs = await self.kb.search('slo', request, k=2)
               docs.extend(incident_docs + slo_docs)
           
           # Always include relevant documentation
           general_docs = await self.kb.search('docs', request, k=3)
           docs.extend(general_docs)
           
           # Rerank based on relevance and recency
           ranked_docs = self.rerank_documents(docs, context)
           
           return ranked_docs[:10]  # Return top 10 most relevant
       
       def rerank_documents(
           self,
           docs: List[Dict[str, Any]],
           context: Dict[str, Any]
       ) -> List[Dict[str, Any]]:
           """Rerank documents based on relevance and quality"""
           
           for doc in docs:
               score = doc.get('similarity_score', 0)
               
               # Boost score for exact stack match
               if context['stack'] in doc.get('metadata', {}).get('stack', ''):
                   score *= 1.5
               
               # Boost for environment match
               if context['environment'] == doc.get('metadata', {}).get('environment'):
                   score *= 1.2
               
               # Boost for recency
               age_days = (datetime.now() - doc.get('created_at', datetime.now())).days
               recency_factor = max(0.5, 1 - (age_days / 365))
               score *= recency_factor
               
               # Boost for success rate
               success_rate = doc.get('metadata', {}).get('success_rate', 0.5)
               score *= (1 + success_rate)
               
               doc['final_score'] = score
           
           return sorted(docs, key=lambda x: x['final_score'], reverse=True)
   ```

2. **Knowledge Ingestion Pipeline**
   ```python
   # backend/app/core/knowledge_ingestion.py
   from typing import Dict, Any, List
   import asyncio
   from urllib.parse import urlparse
   from app.core.connectors import GitHubConnector, ConfluenceConnector, NotionConnector
   from app.core.document_processor import DocumentProcessor
   from app.core.knowledge_base import KnowledgeBase
   
   class KnowledgeIngestionPipeline:
       def __init__(self):
           self.kb = KnowledgeBase()
           self.processor = DocumentProcessor()
           self.connectors = {
               'github': GitHubConnector,
               'confluence': ConfluenceConnector,
               'notion': NotionConnector,
               'gitlab': GitLabConnector,
               'docs': DocsConnector
           }
       
       async def ingest_source(self, uri: str, options: Dict[str, Any] = {}) -> Dict[str, Any]:
           """Ingest knowledge from a source"""
           
           # Detect source type
           source_type = self.detect_source_type(uri)
           
           if source_type not in self.connectors:
               raise ValueError(f"Unsupported source type: {source_type}")
           
           # Initialize connector
           connector = self.connectors[source_type](uri, options)
           
           # Fetch content
           raw_content = await connector.fetch_content()
           
           # Process and chunk content
           processed_content = await self.process_content(raw_content, source_type)
           
           # Generate embeddings and store
           stored_count = await self.store_content(processed_content)
           
           # Create sync schedule if requested
           if options.get('sync', False):
               await self.setup_sync(uri, options.get('sync_interval', '1h'))
           
           return {
               'source': uri,
               'type': source_type,
               'documents_processed': len(raw_content),
               'chunks_stored': stored_count,
               'sync_enabled': options.get('sync', False)
           }
       
       async def process_content(
           self,
           content: List[Dict[str, Any]],
           source_type: str
       ) -> List[Dict[str, Any]]:
           """Process raw content into chunks with metadata"""
           
           processed = []
           
           for item in content:
               # Extract metadata based on source type
               metadata = self.extract_metadata(item, source_type)
               
               # Clean and normalize text
               cleaned_text = self.clean_text(item['content'])
               
               # Chunk text
               chunks = self.processor.chunk_text(cleaned_text)
               
               # Add metadata to each chunk
               for chunk in chunks:
                   processed.append({
                       'text': chunk,
                       'metadata': {
                           **metadata,
                           'source_type': source_type,
                           'ingested_at': datetime.utcnow()
                       }
                   })
           
           return processed
       
       def extract_metadata(self, item: Dict[str, Any], source_type: str) -> Dict[str, Any]:
           """Extract relevant metadata from content"""
           
           metadata = {
               'title': item.get('title', ''),
               'url': item.get('url', ''),
               'author': item.get('author', ''),
               'created_at': item.get('created_at'),
               'updated_at': item.get('updated_at')
           }
           
           # Source-specific metadata extraction
           if source_type == 'github':
               metadata.update({
                   'repository': item.get('repository'),
                   'branch': item.get('branch'),
                   'file_path': item.get('file_path'),
                   'language': item.get('language')
               })
           elif source_type == 'confluence':
               metadata.update({
                   'space': item.get('space'),
                   'labels': item.get('labels', []),
                   'version': item.get('version')
               })
           
           return metadata
   ```

#### Afternoon (4 hours)
1. **Knowledge Search UI**
   ```typescript
   // src/pages/KnowledgeBase.tsx
   import { useState } from 'react';
   import { useQuery, useMutation } from '@tanstack/react-query';
   import KnowledgeSearch from '../components/knowledge/KnowledgeSearch';
   import SourceConnector from '../components/knowledge/SourceConnector';
   import KnowledgeGraph from '../components/knowledge/KnowledgeGraph';
   import api from '../services/api';
   
   export default function KnowledgeBase() {
     const [activeTab, setActiveTab] = useState<'search' | 'sources' | 'graph'>('search');
     const [searchQuery, setSearchQuery] = useState('');
     const [selectedCollection, setSelectedCollection] = useState('all');
     
     const { data: stats } = useQuery({
       queryKey: ['kb-stats'],
       queryFn: () => api.get('/kb/stats'),
     });
     
     const { data: sources } = useQuery({
       queryKey: ['kb-sources'],
       queryFn: () => api.get('/kb/sources'),
     });
     
     return (
       <div className="container mx-auto px-4 py-8">
         <div className="flex justify-between items-center mb-6">
           <h1 className="text-2xl font-bold">Knowledge Base</h1>
           <button className="px-4 py-2 bg-primary-600 text-white rounded-md">
             Connect Source
           </button>
         </div>
         
         {/* Stats Cards */}
         <div className="grid grid-cols-4 gap-4 mb-6">
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Total Documents</p>
             <p className="text-2xl font-bold">{stats?.data?.totalDocuments || 0}</p>
           </div>
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Connected Sources</p>
             <p className="text-2xl font-bold">{stats?.data?.connectedSources || 0}</p>
           </div>
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Collections</p>
             <p className="text-2xl font-bold">{stats?.data?.collections || 0}</p>
           </div>
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Last Sync</p>
             <p className="text-lg font-bold">{stats?.data?.lastSync || 'Never'}</p>
           </div>
         </div>
         
         {/* Tab Navigation */}
         <div className="bg-white rounded-lg shadow">
           <div className="border-b">
             <div className="flex">
               <button
                 onClick={() => setActiveTab('search')}
                 className={`px-6 py-3 font-medium ${
                   activeTab === 'search'
                     ? 'border-b-2 border-primary-600 text-primary-600'
                     : 'text-gray-500'
                 }`}
               >
                 Search
               </button>
               <button
                 onClick={() => setActiveTab('sources')}
                 className={`px-6 py-3 font-medium ${
                   activeTab === 'sources'
                     ? 'border-b-2 border-primary-600 text-primary-600'
                     : 'text-gray-500'
                 }`}
               >
                 Sources
               </button>
               <button
                 onClick={() => setActiveTab('graph')}
                 className={`px-6 py-3 font-medium ${
                   activeTab === 'graph'
                     ? 'border-b-2 border-primary-600 text-primary-600'
                     : 'text-gray-500'
                 }`}
               >
                 Knowledge Graph
               </button>
             </div>
           </div>
           
           <div className="p-6">
             {activeTab === 'search' && (
               <KnowledgeSearch
                 searchQuery={searchQuery}
                 setSearchQuery={setSearchQuery}
                 selectedCollection={selectedCollection}
                 setSelectedCollection={setSelectedCollection}
               />
             )}
             
             {activeTab === 'sources' && (
               <div className="space-y-4">
                 <h3 className="text-lg font-medium">Connected Sources</h3>
                 <div className="grid grid-cols-2 gap-4">
                   {sources?.data?.map((source) => (
                     <div key={source.id} className="bg-gray-50 rounded-lg p-4">
                       <div className="flex items-start justify-between">
                         <div>
                           <h4 className="font-medium">{source.name}</h4>
                           <p className="text-sm text-gray-500">{source.type}</p>
                           <p className="text-xs text-gray-400 mt-1">
                             {source.documentsCount} documents
                           </p>
                         </div>
                         <div className="flex items-center space-x-2">
                           {source.syncEnabled && (
                             <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                               Auto-sync
                             </span>
                           )}
                           <button className="text-gray-400 hover:text-gray-600">
                             <RefreshIcon className="h-4 w-4" />
                           </button>
                         </div>
                       </div>
                       
                       <div className="mt-3 pt-3 border-t">
                         <div className="flex justify-between text-xs">
                           <span className="text-gray-500">
                             Last synced: {source.lastSyncTime}
                           </span>
                           <button className="text-primary-600 hover:text-primary-700">
                             View Details
                           </button>
                         </div>
                       </div>
                     </div>
                   ))}
                 </div>
                 
                 <SourceConnector />
               </div>
             )}
             
             {activeTab === 'graph' && (
               <KnowledgeGraph />
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

2. **Semantic Search Component**
   ```typescript
   // src/components/knowledge/KnowledgeSearch.tsx
   import { useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import ReactMarkdown from 'react-markdown';
   import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
   import api from '../../services/api';
   
   export default function KnowledgeSearch({
     searchQuery,
     setSearchQuery,
     selectedCollection,
     setSelectedCollection
   }) {
     const [selectedResult, setSelectedResult] = useState(null);
     
     const { data: searchResults, isLoading } = useQuery({
       queryKey: ['kb-search', searchQuery, selectedCollection],
       queryFn: () => api.post('/kb/search', {
         query: searchQuery,
         collection: selectedCollection,
         k: 10
       }),
       enabled: searchQuery.length > 2,
     });
     
     const { data: collections } = useQuery({
       queryKey: ['kb-collections'],
       queryFn: () => api.get('/kb/collections'),
     });
     
     return (
       <div className="space-y-4">
         {/* Search Bar */}
         <div className="flex space-x-4">
           <div className="flex-1">
             <input
               type="text"
               value={searchQuery}
               onChange={(e) => setSearchQuery(e.target.value)}
               placeholder="Search knowledge base..."
               className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600"
             />
           </div>
           <select
             value={selectedCollection}
             onChange={(e) => setSelectedCollection(e.target.value)}
             className="px-4 py-2 border rounded-lg"
           >
             <option value="all">All Collections</option>
             {collections?.data?.map((collection) => (
               <option key={collection.name} value={collection.name}>
                 {collection.displayName} ({collection.count})
               </option>
             ))}
           </select>
         </div>
         
         {/* Search Results */}
         {isLoading ? (
           <div className="flex justify-center py-8">
             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
           </div>
         ) : searchResults?.data?.length > 0 ? (
           <div className="grid grid-cols-12 gap-6">
             <div className="col-span-5">
               <h3 className="font-medium mb-3">Results ({searchResults.data.length})</h3>
               <div className="space-y-2">
                 {searchResults.data.map((result, index) => (
                   <div
                     key={index}
                     onClick={() => setSelectedResult(result)}
                     className={`p-3 rounded-lg cursor-pointer transition ${
                       selectedResult?.id === result.id
                         ? 'bg-primary-50 border border-primary-200'
                         : 'bg-gray-50 hover:bg-gray-100'
                     }`}
                   >
                     <div className="flex justify-between items-start">
                       <h4 className="font-medium text-sm">{result.title}</h4>
                       <span className="text-xs text-gray-500">
                         {Math.round(result.similarity * 100)}%
                       </span>
                     </div>
                     <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                       {result.excerpt}
                     </p>
                     <div className="flex items-center mt-2 space-x-2">
                       <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                         {result.collection}
                       </span>
                       <span className="text-xs text-gray-400">
                         {result.source}
                       </span>
                     </div>
                   </div>
                 ))}
               </div>
             </div>
             
             <div className="col-span-7">
               {selectedResult ? (
                 <div className="bg-white border rounded-lg p-6">
                   <div className="mb-4">
                     <h3 className="text-lg font-medium">{selectedResult.title}</h3>
                     <div className="flex items-center mt-2 space-x-4 text-sm text-gray-500">
                       <span>Source: {selectedResult.source}</span>
                       <span>•</span>
                       <span>Updated: {selectedResult.updated_at}</span>
                     </div>
                   </div>
                   
                   <div className="prose prose-sm max-w-none">
                     <ReactMarkdown
                       components={{
                         code({ node, inline, className, children, ...props }) {
                           const match = /language-(\w+)/.exec(className || '');
                           return !inline && match ? (
                             <SyntaxHighlighter
                               language={match[1]}
                               PreTag="div"
                               {...props}
                             >
                               {String(children).replace(/\n$/, '')}
                             </SyntaxHighlighter>
                           ) : (
                             <code className={className} {...props}>
                               {children}
                             </code>
                           );
                         }
                       }}
                     >
                       {selectedResult.content}
                     </ReactMarkdown>
                   </div>
                   
                   {selectedResult.citations && (
                     <div className="mt-6 pt-4 border-t">
                       <h4 className="font-medium text-sm mb-2">Citations</h4>
                       <ul className="space-y-1">
                         {selectedResult.citations.map((citation, index) => (
                           <li key={index} className="text-xs text-gray-600">
                             [{index + 1}] {citation.title} - {citation.url}
                           </li>
                         ))}
                       </ul>
                     </div>
                   )}
                   
                   <div className="mt-6 flex space-x-3">
                     <button className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700">
                       Apply as Pipeline
                     </button>
                     <button className="px-3 py-1 border border-gray-300 text-sm rounded hover:bg-gray-50">
                       Copy to Clipboard
                     </button>
                     <button className="px-3 py-1 border border-gray-300 text-sm rounded hover:bg-gray-50">
                       View Source
                     </button>
                   </div>
                 </div>
               ) : (
                 <div className="bg-gray-50 rounded-lg p-12 text-center text-gray-500">
                   Select a result to view details
                 </div>
               )}
             </div>
           </div>
         ) : searchQuery.length > 2 ? (
           <div className="text-center py-8 text-gray-500">
             No results found for "{searchQuery}"
           </div>
         ) : null}
       </div>
     );
   }
   ```

### Day 13: Learning Path & Career Development

#### Morning (4 hours)
1. **Learning Path Backend**
   ```python
   # backend/app/core/learning_path.py
   from typing import Dict, Any, List, Optional
   from datetime import datetime, timedelta
   from app.models.learning import LearningPath, Skill, Progress
   
   class LearningPathManager:
       def __init__(self):
           self.paths = self.load_learning_paths()
           self.skill_tree = self.build_skill_tree()
       
       def load_learning_paths(self) -> Dict[str, LearningPath]:
           """Load predefined learning paths"""
           return {
               'devops_to_ai': LearningPath(
                   id='devops_to_ai',
                   title='DevOps to AI Infrastructure Architect',
                   duration='18 months',
                   difficulty='Advanced',
                   stages=[
                       {
                           'title': 'Foundation (Months 1-3)',
                           'skills': ['python', 'docker', 'kubernetes', 'ci_cd'],
                           'resources': [
                               {'type': 'course', 'title': 'Python for DevOps', 'url': '...'},
                               {'type': 'lab', 'title': 'Kubernetes Hands-on', 'url': '...'},
                               {'type': 'project', 'title': 'Build CI/CD Pipeline', 'url': '...'}
                           ]
                       },
                       {
                           'title': 'AI Fundamentals (Months 4-6)',
                           'skills': ['ml_basics', 'langchain', 'vector_db', 'prompt_engineering'],
                           'resources': [
                               {'type': 'course', 'title': 'ML for Engineers', 'url': '...'},
                               {'type': 'tutorial', 'title': 'LangChain Development', 'url': '...'},
                               {'type': 'project', 'title': 'Build AI Agent', 'url': '...'}
                           ]
                       },
                       {
                           'title': 'Advanced Integration (Months 7-12)',
                           'skills': ['mlops', 'ai_infrastructure', 'optimization', 'monitoring'],
                           'resources': [
                               {'type': 'course', 'title': 'MLOps Best Practices', 'url': '...'},
                               {'type': 'certification', 'title': 'AWS ML Specialty', 'url': '...'}
                           ]
                       },
                       {
                           'title': 'Architecture & Leadership (Months 13-18)',
                           'skills': ['system_design', 'team_leadership', 'strategy', 'innovation'],
                           'resources': [
                               {'type': 'mentorship', 'title': 'Architecture Reviews', 'url': '...'},
                               {'type': 'project', 'title': 'Lead AI Transformation', 'url': '...'}
                           ]
                       }
                   ]
               ),
               'junior_to_senior': LearningPath(
                   id='junior_to_senior',
                   title='Junior to Senior DevOps Engineer',
                   duration='24 months',
                   difficulty='Intermediate'
                   # ... stages
               ),
               'aws_certification': LearningPath(
                   id='aws_certification',
                   title='AWS Certification Path',
                   duration='6 months',
                   difficulty='Intermediate'
                   # ... stages
               )
           }
       
       def get_personalized_path(self, user_profile: Dict[str, Any]) -> LearningPath:
           """Generate personalized learning path based on user profile"""
           
           current_skills = user_profile.get('skills', [])
           career_goal = user_profile.get('career_goal')
           available_time = user_profile.get('available_time_per_week')
           
           # Find best matching base path
           base_path = self.find_best_path(career_goal, current_skills)
           
           # Customize based on existing skills
           personalized_path = self.customize_path(base_path, current_skills)
           
           # Adjust timeline based on available time
           personalized_path = self.adjust_timeline(personalized_path, available_time)
           
           # Add supplementary resources
           personalized_path = self.add_resources(personalized_path, user_profile)
           
           return personalized_path
       
       def track_progress(self, user_id: str, skill: str, completed_item: Dict[str, Any]):
           """Track user progress on learning path"""
           
           progress = Progress(
               user_id=user_id,
               skill=skill,
               item_id=completed_item['id'],
               item_type=completed_item['type'],
               completed_at=datetime.utcnow(),
               score=completed_item.get('score'),
               time_spent=completed_item.get('time_spent')
           )
           
           # Update skill level
           self.update_skill_level(user_id, skill, progress)
           
           # Check for achievements
           achievements = self.check_achievements(user_id, skill, progress)
           
           # Generate next recommendations
           next_items = self.get_next_recommendations(user_id)
           
           return {
               'progress': progress,
               'achievements': achievements,
               'next_recommendations': next_items
           }
   ```

2. **AI-Powered Career Assistant**
   ```python
   # backend/app/core/career_assistant.py
   from typing import Dict, Any, List
   from langchain import LLMChain, PromptTemplate
   
   class CareerAssistant:
       def __init__(self):
           self.setup_chains()
           self.interview_questions = self.load_interview_questions()
           self.prompt_templates = self.load_prompt_templates()
       
       def setup_chains(self):
           """Setup LLM chains for career assistance"""
           
           # Interview preparation chain
           self.interview_chain = LLMChain(
               llm=self.llm,
               prompt=PromptTemplate(
                   input_variables=["role", "level", "company", "technologies"],
                   template="""
                   Prepare interview questions and answers for:
                   Role: {role}
                   Level: {level}
                   Company: {company}
                   Technologies: {technologies}
                   
                   Generate:
                   1. 10 technical questions with detailed answers
                   2. 5 behavioral questions with STAR format answers
                   3. 5 system design questions with solutions
                   4. Key talking points for the role
                   5. Questions to ask the interviewer
                   """
               )
           )
           
           # Resume optimization chain
           self.resume_chain = LLMChain(
               llm=self.llm,
               prompt=PromptTemplate(
                   input_variables=["current_resume", "target_role", "job_description"],
                   template="""
                   Optimize this resume for the target role:
                   
                   Current Resume: {current_resume}
                   Target Role: {target_role}
                   Job Description: {job_description}
                   
                   Provide:
                   1. Optimized summary/objective
                   2. Reworded experience bullets focusing on achievements
                   3. Skills to highlight
                   4. Keywords to include for ATS
                   5. Sections to add or remove
                   """
               )
           )
       
       def get_devops_prompts(self) -> List[Dict[str, str]]:
           """Get 10 essential AI prompts for DevOps productivity"""
           return [
               {
                   'title': 'Kubernetes Troubleshooting',
                   'prompt': 'Debug this Kubernetes deployment issue: {error_log}. Provide step-by-step troubleshooting with kubectl commands.',
                   'category': 'troubleshooting'
               },
               {
                   'title': 'Terraform Code Generation',
                   'prompt': 'Generate Terraform code for: {infrastructure_requirements}. Include best practices and security considerations.',
                   'category': 'iac'
               },
               {
                   'title': 'CI/CD Pipeline Optimization',
                   'prompt': 'Optimize this CI/CD pipeline: {pipeline_config}. Focus on speed, reliability, and cost.',
                   'category': 'cicd'
               },
               {
                   'title': 'Security Vulnerability Fix',
                   'prompt': 'Fix this security vulnerability: {vulnerability_report}. Provide remediation steps and preventive measures.',
                   'category': 'security'
               },
               {
                   'title': 'Performance Optimization',
                   'prompt': 'Optimize performance for: {performance_metrics}. Suggest specific improvements with expected impact.',
                   'category': 'performance'
               },
               {
                   'title': 'Incident Post-Mortem',
                   'prompt': 'Create post-mortem for: {incident_details}. Include root cause, timeline, and prevention strategies.',
                   'category': 'incident'
               },
               {
                   'title': 'Documentation Generation',
                   'prompt': 'Generate documentation for: {code_or_system}. Include architecture, setup, and troubleshooting sections.',
                   'category': 'documentation'
               },
               {
                   'title': 'Cost Optimization',
                   'prompt': 'Analyze and optimize cloud costs: {cost_report}. Provide specific recommendations with ROI.',
                   'category': 'cost'
               },
               {
                   'title': 'Migration Planning',
                   'prompt': 'Plan migration from {source} to {target}. Include timeline, risks, and rollback strategy.',
                   'category': 'migration'
               },
               {
                   'title': 'Monitoring Setup',
                   'prompt': 'Setup monitoring for: {application_stack}. Include metrics, alerts, and dashboards.',
                   'category': 'monitoring'
               }
           ]
       
       async def prepare_for_interview(
           self,
           role: str,
           company: str,
           level: str
       ) -> Dict[str, Any]:
           """Prepare comprehensive interview materials"""
           
           # Generate questions and answers
           interview_prep = await self.interview_chain.arun(
               role=role,
               level=level,
               company=company,
               technologies=self.get_role_technologies(role)
           )
           
           # Get company-specific insights
           company_insights = await self.get_company_insights(company)
           
           # Generate practice scenarios
           practice_scenarios = self.generate_practice_scenarios(role, level)
           
           return {
               'interview_prep': interview_prep,
               'company_insights': company_insights,
               'practice_scenarios': practice_scenarios,
               'estimated_prep_time': self.estimate_prep_time(level)
           }
   ```

#### Afternoon (4 hours)
1. **Learning Path UI Component**
   ```typescript
   // src/components/learning/LearningPathView.tsx
   import { useState } from 'react';
   import { useQuery, useMutation } from '@tanstack/react-query';
   import { CheckCircleIcon, LockClosedIcon, PlayIcon } from '@heroicons/react/24/outline';
   import api from '../../services/api';
   
   export default function LearningPathView() {
     const [selectedPath, setSelectedPath] = useState(null);
     const [expandedStage, setExpandedStage] = useState(0);
     
     const { data: paths } = useQuery({
       queryKey: ['learning-paths'],
       queryFn: () => api.get('/learning/paths'),
     });
     
     const { data: userProgress } = useQuery({
       queryKey: ['user-progress'],
       queryFn: () => api.get('/learning/progress'),
     });
     
     const startPath = useMutation({
       mutationFn: (pathId: string) => api.post(`/learning/paths/${pathId}/start`),
     });
     
     return (
       <div className="max-w-6xl mx-auto">
         <h2 className="text-2xl font-bold mb-6">Learning Paths</h2>
         
         {/* Path Selection */}
         <div className="grid grid-cols-3 gap-6 mb-8">
           {paths?.data?.map((path) => (
             <div
               key={path.id}
               onClick={() => setSelectedPath(path)}
               className={`bg-white rounded-lg shadow-lg p-6 cursor-pointer transition ${
                 selectedPath?.id === path.id
                   ? 'ring-2 ring-primary-600'
                   : 'hover:shadow-xl'
               }`}
             >
               <div className="flex items-start justify-between mb-4">
                 <div className="p-3 bg-primary-100 rounded-lg">
                   <PathIcon className="h-6 w-6 text-primary-600" />
                 </div>
                 <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                   {path.duration}
                 </span>
               </div>
               
               <h3 className="font-bold text-lg mb-2">{path.title}</h3>
               <p className="text-sm text-gray-600 mb-4">{path.description}</p>
               
               <div className="flex items-center justify-between">
                 <span className={`px-2 py-1 rounded text-xs ${
                   path.difficulty === 'Beginner' ? 'bg-green-100 text-green-800' :
                   path.difficulty === 'Intermediate' ? 'bg-yellow-100 text-yellow-800' :
                   'bg-red-100 text-red-800'
                 }`}>
                   {path.difficulty}
                 </span>
                 
                 {userProgress?.data?.[path.id] ? (
                   <div className="flex items-center">
                     <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                       <div
                         className="bg-primary-600 h-2 rounded-full"
                         style={{ width: `${userProgress.data[path.id].percentage}%` }}
                       />
                     </div>
                     <span className="text-xs text-gray-600">
                       {userProgress.data[path.id].percentage}%
                     </span>
                   </div>
                 ) : (
                   <button
                     onClick={(e) => {
                       e.stopPropagation();
                       startPath.mutate(path.id);
                     }}
                     className="px-3 py-1 bg-primary-600 text-white text-xs rounded hover:bg-primary-700"
                   >
                     Start
                   </button>
                 )}
               </div>
             </div>
           ))}
         </div>
         
         {/* Selected Path Details */}
         {selectedPath && (
           <div className="bg-white rounded-lg shadow-lg p-8">
             <h3 className="text-xl font-bold mb-6">{selectedPath.title}</h3>
             
             {/* Timeline */}
             <div className="relative">
               {selectedPath.stages.map((stage, index) => {
                 const isCompleted = userProgress?.data?.[selectedPath.id]?.completedStages?.includes(index);
                 const isActive = userProgress?.data?.[selectedPath.id]?.currentStage === index;
                 const isLocked = !isCompleted && !isActive && index > 0;
                 
                 return (
                   <div key={index} className="mb-8 last:mb-0">
                     <div className="flex items-start">
                       <div className="flex flex-col items-center mr-4">
                         <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                           isCompleted ? 'bg-green-500' :
                           isActive ? 'bg-primary-600' :
                           'bg-gray-300'
                         }`}>
                           {isCompleted ? (
                             <CheckCircleIcon className="h-6 w-6 text-white" />
                           ) : isLocked ? (
                             <LockClosedIcon className="h-5 w-5 text-white" />
                           ) : (
                             <span className="text-white font-medium">{index + 1}</span>
                           )}
                         </div>
                         {index < selectedPath.stages.length - 1 && (
                           <div className={`w-0.5 h-24 ${
                             isCompleted ? 'bg-green-500' : 'bg-gray-300'
                           }`} />
                         )}
                       </div>
                       
                       <div className="flex-1">
                         <div
                           onClick={() => !isLocked && setExpandedStage(index)}
                           className={`cursor-pointer ${isLocked ? 'opacity-50' : ''}`}
                         >
                           <h4 className="font-bold text-lg">{stage.title}</h4>
                           <p className="text-sm text-gray-600 mb-2">{stage.duration}</p>
                           
                           {/* Skills */}
                           <div className="flex flex-wrap gap-2 mb-3">
                             {stage.skills.map((skill) => (
                               <span
                                 key={skill}
                                 className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                               >
                                 {skill}
                               </span>
                             ))}
                           </div>
                           
                           {/* Resources (expanded) */}
                           {expandedStage === index && !isLocked && (
                             <div className="mt-4 space-y-3">
                               {stage.resources.map((resource, rIndex) => (
                                 <div
                                   key={rIndex}
                                   className="bg-gray-50 rounded-lg p-4 flex items-center justify-between"
                                 >
                                   <div className="flex items-center">
                                     <ResourceIcon type={resource.type} />
                                     <div className="ml-3">
                                       <h5 className="font-medium text-sm">{resource.title}</h5>
                                       <p className="text-xs text-gray-500">
                                         {resource.duration} • {resource.type}
                                       </p>
                                     </div>
                                   </div>
                                   
                                   <button className="px-3 py-1 bg-primary-600 text-white text-xs rounded flex items-center hover:bg-primary-700">
                                     <PlayIcon className="h-3 w-3 mr-1" />
                                     Start
                                   </button>
                                 </div>
                               ))}
                             </div>
                           )}
                         </div>
                       </div>
                     </div>
                   </div>
                 );
               })}
             </div>
           </div>
         )}
       </div>
     );
   }
   ```

2. **Career Development Dashboard**
   ```typescript
   // src/components/career/CareerDashboard.tsx
   import { useState } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import SkillRadar from './SkillRadar';
   import InterviewPrep from './InterviewPrep';
   import PromptLibrary from './PromptLibrary';
   import api from '../../services/api';
   
   export default function CareerDashboard() {
     const [activeSection, setActiveSection] = useState<'skills' | 'interview' | 'prompts'>('skills');
     
     const { data: profile } = useQuery({
       queryKey: ['career-profile'],
       queryFn: () => api.get('/career/profile'),
     });
     
     const { data: recommendations } = useQuery({
       queryKey: ['career-recommendations'],
       queryFn: () => api.get('/career/recommendations'),
     });
     
     return (
       <div className="max-w-6xl mx-auto">
         <h2 className="text-2xl font-bold mb-6">Career Development</h2>
         
         {/* Career Stats */}
         <div className="grid grid-cols-4 gap-4 mb-8">
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Current Level</p>
             <p className="text-xl font-bold">{profile?.data?.level || 'Mid-Level'}</p>
           </div>
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Skills Mastered</p>
             <p className="text-xl font-bold">{profile?.data?.skillsMastered || 0}/50</p>
           </div>
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Certifications</p>
             <p className="text-xl font-bold">{profile?.data?.certifications || 0}</p>
           </div>
           <div className="bg-white rounded-lg shadow p-4">
             <p className="text-sm text-gray-500">Next Milestone</p>
             <p className="text-lg font-bold">{profile?.data?.nextMilestone || 'Senior Level'}</p>
           </div>
         </div>
         
         {/* Navigation Tabs */}
         <div className="bg-white rounded-lg shadow mb-6">
           <div className="border-b">
             <div className="flex">
               <button
                 onClick={() => setActiveSection('skills')}
                 className={`px-6 py-3 font-medium ${
                   activeSection === 'skills'
                     ? 'border-b-2 border-primary-600 text-primary-600'
                     : 'text-gray-500'
                 }`}
               >
                 Skills Assessment
               </button>
               <button
                 onClick={() => setActiveSection('interview')}
                 className={`px-6 py-3 font-medium ${
                   activeSection === 'interview'
                     ? 'border-b-2 border-primary-600 text-primary-600'
                     : 'text-gray-500'
                 }`}
               >
                 Interview Prep
               </button>
               <button
                 onClick={() => setActiveSection('prompts')}
                 className={`px-6 py-3 font-medium ${
                   activeSection === 'prompts'
                     ? 'border-b-2 border-primary-600 text-primary-600'
                     : 'text-gray-500'
                 }`}
               >
                 AI Prompts
               </button>
             </div>
           </div>
           
           <div className="p-6">
             {activeSection === 'skills' && (
               <div className="grid grid-cols-2 gap-8">
                 <div>
                   <h3 className="font-bold mb-4">Skills Radar</h3>
                   <SkillRadar skills={profile?.data?.skills} />
                 </div>
                 
                 <div>
                   <h3 className="font-bold mb-4">Recommended Skills</h3>
                   <div className="space-y-3">
                     {recommendations?.data?.skills?.map((skill) => (
                       <div key={skill.name} className="bg-gray-50 rounded-lg p-4">
                         <div className="flex justify-between items-start">
                           <div>
                             <h4 className="font-medium">{skill.name}</h4>
                             <p className="text-sm text-gray-600">{skill.reason}</p>
                           </div>
                           <span className="px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded">
                             +{skill.salaryImpact}%
                           </span>
                         </div>
                         <button className="mt-3 text-sm text-primary-600 hover:text-primary-700">
                           Start Learning →
                         </button>
                       </div>
                     ))}
                   </div>
                 </div>
               </div>
             )}
             
             {activeSection === 'interview' && (
               <InterviewPrep />
             )}
             
             {activeSection === 'prompts' && (
               <PromptLibrary />
             )}
           </div>
         </div>
       </div>
     );
   }
   ```

### Day 14: Observability Integration

#### Morning (4 hours)
1. **Prometheus Integration**
   ```python
   # backend/app/core/observability/prometheus_client.py
   from typing import Dict, Any, List
   import aiohttp
   from datetime import datetime, timedelta
   
   class PrometheusClient:
       def __init__(self, base_url: str):
           self.base_url = base_url
           self.session = None
       
       async def __aenter__(self):
           self.session = aiohttp.ClientSession()
           return self
       
       async def __aexit__(self, exc_type, exc_val, exc_tb):
           await self.session.close()
       
       async def query(self, promql: str, time: Optional[datetime] = None) -> Dict[str, Any]:
           """Execute instant query"""
           params = {'query': promql}
           if time:
               params['time'] = time.timestamp()
           
           async with self.session.get(
               f"{self.base_url}/api/v1/query",
               params=params
           ) as response:
               return await response.json()
       
       async def query_range(
           self,
           promql: str,
           start: datetime,
           end: datetime,
           step: str = '15s'
       ) -> Dict[str, Any]:
           """Execute range query"""
           params = {
               'query': promql,
               'start': start.timestamp(),
               'end': end.timestamp(),
               'step': step
           }
           
           async with self.session.get(
               f"{self.base_url}/api/v1/query_range",
               params=params
           ) as response:
               return await response.json()
       
       async def get_service_metrics(self, service: str) -> Dict[str, Any]:
           """Get comprehensive metrics for a service"""
           
           now = datetime.utcnow()
           hour_ago = now - timedelta(hours=1)
           
           metrics = {}
           
           # Error rate
           error_query = f'rate(http_requests_total{{service="{service}",status=~"5.."}}[5m])'
           metrics['error_rate'] = await self.query(error_query)
           
           # Request rate
           request_query = f'rate(http_requests_total{{service="{service}"}}[5m])'
           metrics['request_rate'] = await self.query(request_query)
           
           # P95 latency
           latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m]))'
           metrics['p95_latency'] = await self.query(latency_query)
           
           # CPU usage
           cpu_query = f'rate(container_cpu_usage_seconds_total{{pod=~"{service}-.*"}}[5m])'
           metrics['cpu_usage'] = await self.query(cpu_query)
           
           # Memory usage
           memory_query = f'container_memory_usage_bytes{{pod=~"{service}-.*"}}'
           metrics['memory_usage'] = await self.query(memory_query)
           
           # Historical data for graphs
           metrics['history'] = {
               'error_rate': await self.query_range(error_query, hour_ago, now),
               'request_rate': await self.query_range(request_query, hour_ago, now),
               'latency': await self.query_range(latency_query, hour_ago, now)
           }
           
           return metrics
   ```

2. **Grafana Dashboard Generator**
   ```python
   # backend/app/core/observability/grafana_manager.py
   import json
   from typing import Dict, Any, List
   import aiohttp
   
   class GrafanaManager:
       def __init__(self, base_url: str, api_key: str):
           self.base_url = base_url
           self.headers = {'Authorization': f'Bearer {api_key}'}
       
       async def create_dashboard(
           self,
           service_name: str,
           metrics: List[str]
       ) -> Dict[str, Any]:
           """Generate and create Grafana dashboard for a service"""
           
           dashboard = self.generate_dashboard_json(service_name, metrics)
           
           async with aiohttp.ClientSession() as session:
               async with session.post(
                   f"{self.base_url}/api/dashboards/db",
                   headers=self.headers,
                   json={'dashboard': dashboard, 'overwrite': True}
               ) as response:
                   return await response.json()
       
       def generate_dashboard_json(
           self,
           service_name: str,
           metrics: List[str]
       ) -> Dict[str, Any]:
           """Generate dashboard JSON configuration"""
           
           panels = []
           panel_id = 1
           
           # Add panels for each metric type
           for metric in metrics:
               if 'error' in metric.lower():
                   panel = self.create_error_panel(panel_id, service_name)
               elif 'latency' in metric.lower():
                   panel = self.create_latency_panel(panel_id, service_name)
               elif 'cpu' in metric.lower():
                   panel = self.create_cpu_panel(panel_id, service_name)
               elif 'memory' in metric.lower():
                   panel = self.create_memory_panel(panel_id, service_name)
               else:
                   panel = self.create_generic_panel(panel_id, service_name, metric)
               
               panels.append(panel)
               panel_id += 1
           
           return {
               'title': f'{service_name} Dashboard',
               'tags': ['auto-generated', 'f-ops', service_name],
               'timezone': 'utc',
               'panels': panels,
               'refresh': '10s',
               'time': {'from': 'now-1h', 'to': 'now'},
               'templating': {
                   'list': [
                       {
                           'name': 'service',
                           'type': 'constant',
                           'value': service_name
                       }
                   ]
               }
           }
       
       def create_error_panel(self, panel_id: int, service: str) -> Dict[str, Any]:
           return {
               'id': panel_id,
               'title': 'Error Rate',
               'type': 'graph',
               'gridPos': {'x': 0, 'y': 0, 'w': 12, 'h': 8},
               'targets': [
                   {
                       'expr': f'rate(http_requests_total{{service="{service}",status=~"5.."}}[5m])',
                       'legendFormat': '5xx Errors'
                   },
                   {
                       'expr': f'rate(http_requests_total{{service="{service}",status=~"4.."}}[5m])',
                       'legendFormat': '4xx Errors'
                   }
               ],
               'yaxes': [
                   {'format': 'ops', 'show': True},
                   {'show': False}
               ]
           }
   ```

#### Afternoon (4 hours)
1. **Observability Dashboard UI**
   ```typescript
   // src/components/observability/MetricsDashboard.tsx
   import { useState, useEffect } from 'react';
   import { useQuery } from '@tanstack/react-query';
   import {
       LineChart,
       Line,
       AreaChart,
       Area,
       BarChart,
       Bar,
       XAxis,
       YAxis,
       CartesianGrid,
       Tooltip,
       Legend,
       ResponsiveContainer
   } from 'recharts';
   import api from '../../services/api';
   
   export default function MetricsDashboard({ serviceId }) {
     const [timeRange, setTimeRange] = useState('1h');
     const [autoRefresh, setAutoRefresh] = useState(true);
     
     const { data: metrics, isLoading } = useQuery({
       queryKey: ['metrics', serviceId, timeRange],
       queryFn: () => api.get(`/metrics/${serviceId}?range=${timeRange}`),
       refetchInterval: autoRefresh ? 10000 : false,
     });
     
     const { data: alerts } = useQuery({
       queryKey: ['alerts', serviceId],
       queryFn: () => api.get(`/alerts/${serviceId}`),
       refetchInterval: 30000,
     });
     
     return (
       <div className="space-y-6">
         {/* Controls */}
         <div className="flex justify-between items-center">
           <div className="flex space-x-2">
             {['1h', '6h', '24h', '7d', '30d'].map((range) => (
               <button
                 key={range}
                 onClick={() => setTimeRange(range)}
                 className={`px-3 py-1 rounded ${
                   timeRange === range
                     ? 'bg-primary-600 text-white'
                     : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                 }`}
               >
                 {range}
               </button>
             ))}
           </div>
           
           <div className="flex items-center space-x-4">
             <label className="flex items-center">
               <input
                 type="checkbox"
                 checked={autoRefresh}
                 onChange={(e) => setAutoRefresh(e.target.checked)}
                 className="mr-2"
               />
               <span className="text-sm">Auto-refresh</span>
             </label>
             
             <button className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">
               Export
             </button>
           </div>
         </div>
         
         {/* Active Alerts */}
         {alerts?.data?.length > 0 && (
           <div className="bg-red-50 border border-red-200 rounded-lg p-4">
             <h3 className="font-medium text-red-900 mb-2">Active Alerts</h3>
             <div className="space-y-2">
               {alerts.data.map((alert) => (
                 <div key={alert.id} className="flex items-center justify-between">
                   <div>
                     <span className="font-medium text-red-800">{alert.name}</span>
                     <span className="ml-2 text-sm text-red-600">{alert.message}</span>
                   </div>
                   <span className="text-xs text-red-500">{alert.duration}</span>
                 </div>
               ))}
             </div>
           </div>
         )}
         
         {/* Metrics Grid */}
         <div className="grid grid-cols-2 gap-6">
           {/* Request Rate */}
           <div className="bg-white rounded-lg shadow p-6">
             <h3 className="font-medium mb-4">Request Rate</h3>
             <ResponsiveContainer width="100%" height={200}>
               <AreaChart data={metrics?.data?.requestRate || []}>
                 <CartesianGrid strokeDasharray="3 3" />
                 <XAxis dataKey="time" />
                 <YAxis />
                 <Tooltip />
                 <Area
                   type="monotone"
                   dataKey="value"
                   stroke="#3b82f6"
                   fill="#93bbfc"
                 />
               </AreaChart>
             </ResponsiveContainer>
           </div>
           
           {/* Error Rate */}
           <div className="bg-white rounded-lg shadow p-6">
             <h3 className="font-medium mb-4">Error Rate</h3>
             <ResponsiveContainer width="100%" height={200}>
               <LineChart data={metrics?.data?.errorRate || []}>
                 <CartesianGrid strokeDasharray="3 3" />
                 <XAxis dataKey="time" />
                 <YAxis />
                 <Tooltip />
                 <Legend />
                 <Line
                   type="monotone"
                   dataKey="5xx"
                   stroke="#ef4444"
                   name="5xx Errors"
                 />
                 <Line
                   type="monotone"
                   dataKey="4xx"
                   stroke="#f59e0b"
                   name="4xx Errors"
                 />
               </LineChart>
             </ResponsiveContainer>
           </div>
           
           {/* Latency */}
           <div className="bg-white rounded-lg shadow p-6">
             <h3 className="font-medium mb-4">Latency (ms)</h3>
             <ResponsiveContainer width="100%" height={200}>
               <LineChart data={metrics?.data?.latency || []}>
                 <CartesianGrid strokeDasharray="3 3" />
                 <XAxis dataKey="time" />
                 <YAxis />
                 <Tooltip />
                 <Legend />
                 <Line
                   type="monotone"
                   dataKey="p50"
                   stroke="#10b981"
                   name="P50"
                 />
                 <Line
                   type="monotone"
                   dataKey="p95"
                   stroke="#3b82f6"
                   name="P95"
                 />
                 <Line
                   type="monotone"
                   dataKey="p99"
                   stroke="#8b5cf6"
                   name="P99"
                 />
               </LineChart>
             </ResponsiveContainer>
           </div>
           
           {/* Resource Usage */}
           <div className="bg-white rounded-lg shadow p-6">
             <h3 className="font-medium mb-4">Resource Usage</h3>
             <ResponsiveContainer width="100%" height={200}>
               <AreaChart data={metrics?.data?.resources || []}>
                 <CartesianGrid strokeDasharray="3 3" />
                 <XAxis dataKey="time" />
                 <YAxis />
                 <Tooltip />
                 <Legend />
                 <Area
                   type="monotone"
                   dataKey="cpu"
                   stackId="1"
                   stroke="#3b82f6"
                   fill="#93bbfc"
                   name="CPU %"
                 />
                 <Area
                   type="monotone"
                   dataKey="memory"
                   stackId="2"
                   stroke="#10b981"
                   fill="#86efac"
                   name="Memory %"
                 />
               </AreaChart>
             </ResponsiveContainer>
           </div>
         </div>
         
         {/* Service Dependencies */}
         <div className="bg-white rounded-lg shadow p-6">
           <h3 className="font-medium mb-4">Service Dependencies</h3>
           <div className="grid grid-cols-4 gap-4">
             {metrics?.data?.dependencies?.map((dep) => (
               <div key={dep.name} className="bg-gray-50 rounded-lg p-4">
                 <div className="flex items-center justify-between mb-2">
                   <span className="font-medium">{dep.name}</span>
                   <span className={`w-2 h-2 rounded-full ${
                     dep.status === 'healthy' ? 'bg-green-500' :
                     dep.status === 'degraded' ? 'bg-yellow-500' :
                     'bg-red-500'
                   }`} />
                 </div>
                 <div className="text-xs text-gray-600">
                   <p>Latency: {dep.latency}ms</p>
                   <p>Success: {dep.successRate}%</p>
                 </div>
               </div>
             ))}
           </div>
         </div>
       </div>
     );
   }
   ```

### Day 15: Testing & Integration

#### Morning (4 hours)
1. **Integration Testing**
   ```python
   # tests/integration/test_incident_flow.py
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app
   
   @pytest.fixture
   def client():
       return TestClient(app)
   
   @pytest.fixture
   def auth_headers(client):
       response = client.post("/api/auth/login", json={
           "username": "admin",
           "password": "password"
       })
       token = response.json()["token"]
       return {"Authorization": f"Bearer {token}"}
   
   def test_incident_detection_and_rca(client, auth_headers):
       # Simulate incident creation
       response = client.post(
           "/api/incidents",
           headers=auth_headers,
           json={
               "title": "High error rate in API service",
               "severity": "high",
               "service": "api-gateway",
               "metrics": {
                   "error_rate": 0.15,
                   "p95_latency": 2500
               }
           }
       )
       assert response.status_code == 201
       incident_id = response.json()["id"]
       
       # Trigger RCA
       response = client.post(
           f"/api/incidents/{incident_id}/analyze",
           headers=auth_headers
       )
       assert response.status_code == 200
       rca = response.json()
       
       assert "root_causes" in rca
       assert "recommendations" in rca
       assert len(rca["root_causes"]) > 0
       
       # Get suggested actions
       response = client.get(
           f"/api/incidents/{incident_id}/actions",
           headers=auth_headers
       )
       assert response.status_code == 200
       actions = response.json()
       
       assert len(actions) > 0
       assert all("title" in action for action in actions)
       
       # Execute an action
       response = client.post(
           f"/api/incidents/{incident_id}/actions/{actions[0]['id']}/execute",
           headers=auth_headers
       )
       assert response.status_code == 200
       
       # Verify incident status updated
       response = client.get(
           f"/api/incidents/{incident_id}",
           headers=auth_headers
       )
       assert response.json()["status"] == "resolving"
   
   def test_knowledge_base_rag_planning(client, auth_headers):
       # Connect a knowledge source
       response = client.post(
           "/api/kb/connect",
           headers=auth_headers,
           json={
               "uri": "https://github.com/example/devops-docs",
               "type": "github",
               "sync": True
           }
       )
       assert response.status_code == 200
       
       # Wait for initial sync
       import time
       time.sleep(5)
       
       # Search knowledge base
       response = client.post(
           "/api/kb/search",
           headers=auth_headers,
           json={
               "query": "kubernetes deployment best practices",
               "collection": "docs",
               "k": 5
           }
       )
       assert response.status_code == 200
       results = response.json()
       
       assert len(results) > 0
       assert all("similarity" in r for r in results)
       
       # Generate plan using RAG
       response = client.post(
           "/api/planner/generate",
           headers=auth_headers,
           json={
               "request": "Deploy Node.js application to Kubernetes with monitoring",
               "environment": "production",
               "use_rag": True
           }
       )
       assert response.status_code == 200
       plan = response.json()
       
       assert "steps" in plan
       assert "sources" in plan
       assert len(plan["steps"]) > 0
       assert all("citation" in step for step in plan["steps"])
   ```

2. **Performance Testing**
   ```python
   # tests/performance/test_load.py
   import asyncio
   import aiohttp
   import time
   from statistics import mean, stdev
   
   async def make_request(session, url, headers):
       start = time.time()
       async with session.get(url, headers=headers) as response:
           await response.text()
           return time.time() - start
   
   async def load_test(endpoint, concurrent_users=10, requests_per_user=100):
       """Load test an endpoint"""
       url = f"http://localhost:8000{endpoint}"
       headers = {"Authorization": "Bearer test_token"}
       
       async with aiohttp.ClientSession() as session:
           tasks = []
           for _ in range(concurrent_users):
               for _ in range(requests_per_user):
                   tasks.append(make_request(session, url, headers))
           
           start_time = time.time()
           response_times = await asyncio.gather(*tasks)
           total_time = time.time() - start_time
       
       return {
           "total_requests": len(response_times),
           "total_time": total_time,
           "requests_per_second": len(response_times) / total_time,
           "avg_response_time": mean(response_times),
           "std_dev": stdev(response_times),
           "min_response_time": min(response_times),
           "max_response_time": max(response_times),
           "p95": sorted(response_times)[int(len(response_times) * 0.95)],
           "p99": sorted(response_times)[int(len(response_times) * 0.99)]
       }
   
   async def test_api_performance():
       endpoints = [
           "/api/deployments",
           "/api/incidents",
           "/api/kb/search",
           "/api/metrics/service-1"
       ]
       
       results = {}
       for endpoint in endpoints:
           print(f"Testing {endpoint}...")
           results[endpoint] = await load_test(endpoint)
       
       # Assert performance requirements
       for endpoint, metrics in results.items():
           assert metrics["avg_response_time"] < 0.5, f"{endpoint} avg response > 500ms"
           assert metrics["p95"] < 1.0, f"{endpoint} p95 > 1s"
           assert metrics["requests_per_second"] > 100, f"{endpoint} RPS < 100"
       
       return results
   ```

#### Afternoon (4 hours)
1. **End-to-End UI Testing**
   ```typescript
   // tests/e2e/incident-management.test.ts
   import { test, expect } from '@playwright/test';
   
   test.describe('Incident Management E2E', () => {
     test.beforeEach(async ({ page }) => {
       // Login
       await page.goto('http://localhost:3000/login');
       await page.fill('input[name="username"]', 'admin');
       await page.fill('input[name="password"]', 'password');
       await page.click('button[type="submit"]');
       await page.waitForURL('**/dashboard');
     });
     
     test('should detect incident and perform RCA', async ({ page }) => {
       // Navigate to incidents
       await page.goto('http://localhost:3000/incidents');
       
       // Verify incident appears
       await page.waitForSelector('text=High error rate detected');
       
       // Click on incident
       await page.click('text=High error rate detected');
       
       // Switch to RCA tab
       await page.click('text=Root Cause Analysis');
       
       // Wait for RCA to complete
       await page.waitForSelector('text=Root Causes', { timeout: 30000 });
       
       // Verify RCA results
       await expect(page.locator('text=Database connection pool exhausted')).toBeVisible();
       
       // Execute recommended action
       await page.click('button:has-text("Execute Action")');
       
       // Confirm action
       await page.click('button:has-text("Confirm")');
       
       // Verify status update
       await expect(page.locator('text=Resolving')).toBeVisible();
     });
     
     test('should search knowledge base and apply solution', async ({ page }) => {
       // Navigate to knowledge base
       await page.goto('http://localhost:3000/knowledge');
       
       // Search for solution
       await page.fill('input[placeholder="Search knowledge base..."]', 'kubernetes scaling');
       await page.waitForTimeout(1000); // Debounce
       
       // Verify results
       await expect(page.locator('text=Horizontal Pod Autoscaler')).toBeVisible();
       
       // Click on result
       await page.click('text=Horizontal Pod Autoscaler');
       
       // Apply as pipeline
       await page.click('button:has-text("Apply as Pipeline")');
       
       // Verify pipeline creation
       await expect(page.locator('text=Pipeline created successfully')).toBeVisible();
     });
     
     test('should track learning progress', async ({ page }) => {
       // Navigate to career development
       await page.goto('http://localhost:3000/career');
       
       // Select learning path
       await page.click('text=DevOps to AI Infrastructure Architect');
       
       // Start a module
       await page.click('button:has-text("Start")').first();
       
       // Complete a lesson
       await page.click('text=Python for DevOps');
       await page.click('button:has-text("Mark Complete")');
       
       // Verify progress update
       await expect(page.locator('text=5% Complete')).toBeVisible();
       
       // Check skill radar update
       await page.click('text=Skills Assessment');
       await expect(page.locator('canvas')).toBeVisible(); // Skill radar chart
     });
   });
   ```

2. **Documentation & Demo Scripts**
   ```markdown
   # Phase 3 Demo Script
   
   ## 1. Incident Management Demo
   
   ### Setup
   ```bash
   # Simulate high error rate
   curl -X POST http://localhost:8000/api/test/simulate-incident \
     -H "Content-Type: application/json" \
     -d '{"type": "error_spike", "service": "api-gateway"}'
   ```
   
   ### Demo Flow
   1. Show incident appearing in dashboard
   2. Click into incident details
   3. Demonstrate RCA analysis
   4. Show service dependency graph
   5. Execute recommended action
   6. Show metrics returning to normal
   
   ## 2. Knowledge Base RAG Demo
   
   ### Setup
   ```bash
   # Connect GitHub repository
   curl -X POST http://localhost:8000/api/kb/connect \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"uri": "https://github.com/kubernetes/examples"}'
   ```
   
   ### Demo Flow
   1. Search for "stateful application deployment"
   2. Show semantic search results with relevance scores
   3. Generate deployment plan using RAG
   4. Show citations in generated plan
   5. Apply plan to create PR
   
   ## 3. Learning Path Demo
   
   ### Demo Flow
   1. Show career dashboard
   2. Select "DevOps to AI" learning path
   3. Show skill assessment radar chart
   4. Start a learning module
   5. Complete a lesson and show progress
   6. Demonstrate interview prep feature
   7. Show AI prompt library
   
   ## 4. Observability Integration Demo
   
   ### Demo Flow
   1. Show service metrics dashboard
   2. Demonstrate auto-refresh
   3. Show alert correlation with incidents
   4. Generate Grafana dashboard
   5. Show service dependency visualization
   ```

## Deliverables

### By End of Week 3:
1. ✅ Incident detection and management system
2. ✅ Root Cause Analysis with AI
3. ✅ Advanced Knowledge Base with RAG
4. ✅ Semantic search with citations
5. ✅ Learning paths and career development
6. ✅ AI prompt library for DevOps
7. ✅ Interview preparation tools
8. ✅ Prometheus/Grafana integration
9. ✅ Service dependency mapping
10. ✅ Comprehensive testing suite

## Success Criteria

### Technical Metrics:
- Incident detection accuracy > 90%
- RCA confidence score > 80%
- Knowledge search relevance > 85%
- RAG plan quality score > 4/5
- Observability data latency < 30s

### Functional Metrics:
- End-to-end incident resolution working
- Knowledge base with 100+ documents
- Learning paths fully functional
- Career tracking operational
- Metrics dashboards auto-updating

## Next Phase Preview

Phase 4 will focus on:
- Multi-tenancy implementation
- Enterprise security features
- Performance optimization
- Production hardening
- Advanced AI features