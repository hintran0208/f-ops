import sys
import os
# Add project root to path to import mcp_packs and knowledge_base
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain.agents import create_react_agent, Tool, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain import hub
from app.core.knowledge_base import KnowledgeBase
from app.core.audit import AuditLogger, AuditAction
from app.config import settings
from mcp_packs.github.github_pack import GitHubPack
from mcp_packs.kubernetes.k8s_pack import KubernetesPack
from knowledge_base.prompts.devops_prompts import PROMPT_TEMPLATES
from typing import Dict, Any, List, Optional
import logging
import json

logger = logging.getLogger(__name__)

class DevOpsAgent:
    """Main DevOps AI Agent orchestrating all operations"""
    
    def __init__(self):
        """Initialize the DevOps Agent with LLM, tools, and knowledge base"""
        # Initialize LLM
        self.llm = ChatOpenAI(
            temperature=0,
            model_name=settings.DEFAULT_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize Knowledge Base
        self.kb = KnowledgeBase()
        
        # Initialize Audit Logger
        self.audit = AuditLogger()
        
        # Initialize MCP Packs
        self.mcp_packs = self._initialize_mcp_packs()
        
        # Setup tools
        self.tools = self._setup_tools()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Setup agent
        self.agent = self._setup_agent()
        
        logger.info("DevOps Agent initialized successfully")
    
    def _initialize_mcp_packs(self) -> Dict[str, Any]:
        """Initialize MCP packs"""
        packs = {}
        
        # Initialize GitHub Pack if configured
        if settings.GITHUB_TOKEN and settings.GITHUB_TOKEN.strip():
            try:
                packs['github'] = GitHubPack({'token': settings.GITHUB_TOKEN})
                logger.info("GitHub MCP Pack initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub Pack: {e}")
        else:
            logger.info("GitHub Pack skipped - no token configured")
        
        # Initialize Kubernetes Pack
        try:
            packs['kubernetes'] = KubernetesPack({
                'kubeconfig': settings.KUBECONFIG_PATH,
                'in_cluster': False
            })
            logger.info("Kubernetes MCP Pack initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes Pack: {e}")
        
        return packs
    
    def _setup_tools(self) -> List[Tool]:
        """Setup LangChain tools"""
        tools = []
        
        # Knowledge Base Search Tool
        tools.append(Tool(
            name="Knowledge Search",
            func=self._search_knowledge,
            description="Search the knowledge base for documentation, runbooks, and best practices"
        ))
        
        # GitHub Operations Tool
        if 'github' in self.mcp_packs:
            tools.append(Tool(
                name="GitHub Operations",
                func=self._github_operations,
                description="Perform GitHub operations like creating PRs, managing workflows"
            ))
        
        # Kubernetes Operations Tool
        if 'kubernetes' in self.mcp_packs:
            tools.append(Tool(
                name="Kubernetes Operations",
                func=self._k8s_operations,
                description="Perform Kubernetes operations like deployments, scaling, monitoring"
            ))
        
        # Prompt Template Tool
        tools.append(Tool(
            name="Generate DevOps Solution",
            func=self._generate_solution,
            description="Generate DevOps solutions using specialized templates"
        ))
        
        # Incident Analysis Tool
        tools.append(Tool(
            name="Analyze Incident",
            func=self._analyze_incident,
            description="Analyze incidents and provide root cause analysis"
        ))
        
        return tools
    
    def _setup_agent(self):
        """Setup LangChain agent"""
        # Use a simple ReAct prompt for now
        prompt = PromptTemplate.from_template(
            """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def _search_knowledge(self, query: str) -> str:
        """Search knowledge base"""
        try:
            results = self.kb.search_all(query, k=3)
            
            if not results:
                return "No relevant information found in knowledge base."
            
            # Format results
            formatted_results = []
            for collection, items in results.items():
                for item in items:
                    formatted_results.append(
                        f"[{collection}] {item['content'][:200]}..."
                    )
            
            return "\n\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Knowledge search error: {e}")
            return f"Error searching knowledge base: {str(e)}"
    
    def _github_operations(self, operation: str) -> str:
        """Execute GitHub operations"""
        try:
            # Parse operation string (format: "action:params")
            parts = operation.split(":", 1)
            if len(parts) != 2:
                return "Invalid operation format. Use 'action:params'"
            
            action = parts[0]
            params = json.loads(parts[1]) if parts[1] else {}
            
            result = self.mcp_packs['github'].execute_action(action, params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"GitHub operation error: {e}")
            return f"Error executing GitHub operation: {str(e)}"
    
    def _k8s_operations(self, operation: str) -> str:
        """Execute Kubernetes operations"""
        try:
            # Parse operation string
            parts = operation.split(":", 1)
            if len(parts) != 2:
                return "Invalid operation format. Use 'action:params'"
            
            action = parts[0]
            params = json.loads(parts[1]) if parts[1] else {}
            
            result = self.mcp_packs['kubernetes'].execute_action(action, params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Kubernetes operation error: {e}")
            return f"Error executing Kubernetes operation: {str(e)}"
    
    def _generate_solution(self, request: str) -> str:
        """Generate DevOps solution using templates"""
        try:
            # Determine which template to use based on request
            template_key = self._select_template(request)
            
            if template_key not in PROMPT_TEMPLATES:
                return "No suitable template found for this request."
            
            # Create prompt from template
            prompt = PromptTemplate(
                template=PROMPT_TEMPLATES[template_key],
                input_variables=self._get_template_variables(template_key)
            )
            
            # Generate solution
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Extract variables from request (simplified)
            variables = self._extract_variables(request, template_key)
            
            solution = chain.run(**variables)
            return solution
        except Exception as e:
            logger.error(f"Solution generation error: {e}")
            return f"Error generating solution: {str(e)}"
    
    def _analyze_incident(self, incident_data: str) -> str:
        """Analyze incident and provide recommendations"""
        try:
            # Use incident analysis template
            prompt = PromptTemplate(
                template=PROMPT_TEMPLATES["incident_analysis"],
                input_variables=["service_name", "symptoms", "recent_changes", "metrics", "log_samples"]
            )
            
            # Parse incident data
            data = json.loads(incident_data) if incident_data.startswith("{") else {
                "service_name": "unknown",
                "symptoms": incident_data,
                "recent_changes": "Unknown",
                "metrics": "Not available",
                "log_samples": "Not available"
            }
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            analysis = chain.run(**data)
            
            return analysis
        except Exception as e:
            logger.error(f"Incident analysis error: {e}")
            return f"Error analyzing incident: {str(e)}"
    
    def _select_template(self, request: str) -> str:
        """Select appropriate template based on request"""
        request_lower = request.lower()
        
        if "deploy" in request_lower or "pipeline" in request_lower:
            return "zero_to_deploy"
        elif "incident" in request_lower or "outage" in request_lower:
            return "incident_analysis"
        elif "optimize" in request_lower or "cost" in request_lower:
            return "infrastructure_optimization"
        elif "kubernetes" in request_lower or "k8s" in request_lower:
            return "kubernetes_manifest"
        elif "terraform" in request_lower or "infrastructure" in request_lower:
            return "terraform_infrastructure"
        elif "security" in request_lower or "audit" in request_lower:
            return "security_audit"
        elif "performance" in request_lower or "slow" in request_lower:
            return "performance_tuning"
        else:
            return "zero_to_deploy"  # Default
    
    def _get_template_variables(self, template_key: str) -> List[str]:
        """Get required variables for a template"""
        # Extract variables from template
        template = PROMPT_TEMPLATES[template_key]
        import re
        variables = re.findall(r'\{(\w+)\}', template)
        return list(set(variables))
    
    def _extract_variables(self, request: str, template_key: str) -> Dict[str, str]:
        """Extract variables from request for template"""
        # This is a simplified extraction - in production, use NLP or structured input
        variables = {}
        required_vars = self._get_template_variables(template_key)
        
        for var in required_vars:
            # Set default values
            if var == "repo_url":
                variables[var] = "https://github.com/example/repo"
            elif var == "stack":
                variables[var] = "Python/FastAPI"
            elif var == "environment":
                variables[var] = "production"
            elif var == "target":
                variables[var] = "kubernetes"
            else:
                variables[var] = f"[{var} to be specified]"
        
        return variables
    
    def process_request(self, request: str, user: str = "system") -> Dict[str, Any]:
        """Process a user request through the agent"""
        try:
            # Log the request
            self.audit.log_action(
                AuditAction.SYSTEM_WARNING,
                user=user,
                details={"request": request[:200]},
                metadata={"type": "agent_request"}
            )
            
            # Process through agent
            response = self.agent.run(request)
            
            # Log successful processing
            self.audit.log_action(
                AuditAction.SYSTEM_WARNING,
                user=user,
                details={"request": request[:200], "response_length": len(response)},
                metadata={"type": "agent_response"}
            )
            
            return {
                "success": True,
                "response": response,
                "user": user
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            
            # Log error
            self.audit.log_action(
                AuditAction.SYSTEM_ERROR,
                user=user,
                details={"request": request[:200], "error": str(e)},
                metadata={"type": "agent_error"}
            )
            
            return {
                "success": False,
                "error": str(e),
                "user": user
            }
    
    def onboard_repository(self, repo_url: str, target: str, environments: List[str], 
                          user: str = "system") -> Dict[str, Any]:
        """Onboard a new repository with zero-to-deploy setup"""
        try:
            # Log onboarding start
            self.audit.log_action(
                AuditAction.ONBOARDING_STARTED,
                user=user,
                resource=repo_url,
                details={"target": target, "environments": environments}
            )
            
            # Prepare request for agent
            request = f"""
            Create a complete zero-to-deploy setup for repository: {repo_url}
            Deployment target: {target}
            Environments: {', '.join(environments)}
            
            Include CI/CD pipeline, infrastructure templates, and deployment configurations.
            """
            
            # Process through agent
            result = self.process_request(request, user)
            
            if result["success"]:
                # Log successful onboarding
                self.audit.log_action(
                    AuditAction.ONBOARDING_COMPLETED,
                    user=user,
                    resource=repo_url,
                    details={"target": target, "environments": environments}
                )
            else:
                # Log failed onboarding
                self.audit.log_action(
                    AuditAction.ONBOARDING_FAILED,
                    user=user,
                    resource=repo_url,
                    details={"error": result.get("error", "Unknown error")}
                )
            
            return result
        except Exception as e:
            logger.error(f"Onboarding error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_incident(self, service_name: str, symptoms: str, 
                        user: str = "system") -> Dict[str, Any]:
        """Analyze an incident and provide recommendations"""
        try:
            # Log incident analysis start
            self.audit.log_action(
                AuditAction.INCIDENT_INVESTIGATED,
                user=user,
                resource=service_name,
                details={"symptoms": symptoms[:200]}
            )
            
            # Prepare incident data
            incident_data = {
                "service_name": service_name,
                "symptoms": symptoms,
                "recent_changes": "Check deployment history",
                "metrics": "Fetch from monitoring system",
                "log_samples": "Extract from log aggregation"
            }
            
            # Analyze through dedicated function
            analysis = self._analyze_incident(json.dumps(incident_data))
            
            return {
                "success": True,
                "analysis": analysis,
                "service": service_name
            }
        except Exception as e:
            logger.error(f"Incident analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def deploy_service(self, service_name: str, environment: str, version: Optional[str] = None,
                       dry_run: bool = True, user: str = "system") -> Dict[str, Any]:
        """Deploy a service to an environment"""
        try:
            # Log deployment initiation
            self.audit.log_action(
                AuditAction.DEPLOYMENT_INITIATED,
                user=user,
                resource=service_name,
                details={
                    "environment": environment,
                    "version": version,
                    "dry_run": dry_run
                }
            )
            
            if 'kubernetes' not in self.mcp_packs:
                return {
                    "success": False,
                    "error": "Kubernetes pack not available"
                }
            
            # Prepare deployment parameters
            params = {
                "name": service_name,
                "namespace": environment,
                "image": f"{service_name}:{version or 'latest'}",
                "replicas": 3 if environment == "production" else 1
            }
            
            if dry_run:
                # Simulate deployment
                result = {
                    "success": True,
                    "dry_run": True,
                    "message": f"Dry-run successful for {service_name} to {environment}"
                }
            else:
                # Execute actual deployment
                result = self.mcp_packs['kubernetes'].execute_action("deploy", params)
            
            # Log result
            if result.get("success"):
                self.audit.log_action(
                    AuditAction.DEPLOYMENT_COMPLETED,
                    user=user,
                    resource=service_name,
                    details=result
                )
            else:
                self.audit.log_action(
                    AuditAction.DEPLOYMENT_FAILED,
                    user=user,
                    resource=service_name,
                    details=result
                )
            
            return result
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            
            self.audit.log_action(
                AuditAction.DEPLOYMENT_FAILED,
                user=user,
                resource=service_name,
                details={"error": str(e)}
            )
            
            return {
                "success": False,
                "error": str(e)
            }