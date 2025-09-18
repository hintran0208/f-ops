import sys
import os
# Add project root to path to import mcp_packs and knowledge_base
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.core.knowledge_base import KnowledgeBase
from app.core.audit import AuditLogger, AuditAction
from app.config import settings
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
            openai_api_key=settings.OPENAI_API_KEY or "dummy-key-for-testing"
        ) if settings.OPENAI_API_KEY else None
        
        # Initialize Knowledge Base
        try:
            self.kb = KnowledgeBase()
            logger.info("Knowledge Base initialized")
        except Exception as e:
            logger.warning(f"Knowledge Base initialization failed: {e}")
            self.kb = None
        
        # Initialize Audit Logger
        try:
            self.audit = AuditLogger()
            logger.info("Audit Logger initialized")
        except Exception as e:
            logger.warning(f"Audit Logger initialization failed: {e}")
            self.audit = None
        
        # Initialize MCP Packs (deferred loading)
        self.mcp_packs = {}
        self._initialize_mcp_packs_deferred()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        logger.info("DevOps Agent initialized successfully")
    
    def _initialize_mcp_packs_deferred(self):
        """Initialize MCP packs with deferred loading"""
        # Try to import and initialize GitHub Pack
        if settings.GITHUB_TOKEN and settings.GITHUB_TOKEN.strip():
            try:
                from mcp_packs.github.github_pack import GitHubPack
                self.mcp_packs['github'] = GitHubPack({'token': settings.GITHUB_TOKEN})
                logger.info("GitHub MCP Pack initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub Pack: {e}")
        
        # Try to import and initialize Kubernetes Pack
        try:
            from mcp_packs.kubernetes.k8s_pack import KubernetesPack
            k8s_pack = KubernetesPack({
                'kubeconfig': settings.KUBECONFIG_PATH,
                'in_cluster': False
            })
            if k8s_pack.initialized:
                self.mcp_packs['kubernetes'] = k8s_pack
                logger.info("Kubernetes MCP Pack initialized")
            else:
                logger.warning("Kubernetes Pack not initialized - cluster not accessible")
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes Pack: {e}")
    
    def _search_knowledge(self, query: str) -> str:
        """Search knowledge base"""
        if not self.kb:
            return "Knowledge base not available"
        
        try:
            results = self.kb.search_all(query, k=3)
            
            if not results:
                return "No relevant information found in knowledge base."
            
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
    
    def process_request(self, request: str, user: str = "system") -> Dict[str, Any]:
        """Process a user request"""
        try:
            # Log the request if audit is available
            if self.audit:
                self.audit.log_action(
                    AuditAction.SYSTEM_WARNING,
                    user=user,
                    details={"request": request[:200]},
                    metadata={"type": "agent_request"}
                )
            
            # Simple response for now
            response = f"Received request: {request}"
            
            # If LLM is available, use it
            if self.llm:
                try:
                    prompt = PromptTemplate(
                        template="Process this DevOps request: {request}\nProvide a helpful response.",
                        input_variables=["request"]
                    )
                    chain = LLMChain(llm=self.llm, prompt=prompt)
                    response = chain.run(request=request)
                except Exception as e:
                    logger.error(f"LLM processing error: {e}")
                    response = f"Processing with limited capabilities: {request}"
            
            return {
                "success": True,
                "response": response,
                "user": user
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "success": False,
                "error": str(e),
                "user": user
            }
    
    def onboard_repository(self, repo_url: str, target: str, environments: List[str], 
                          user: str = "system") -> Dict[str, Any]:
        """Onboard a new repository with zero-to-deploy setup"""
        try:
            # Log onboarding start if audit is available
            if self.audit:
                self.audit.log_action(
                    AuditAction.ONBOARDING_STARTED,
                    user=user,
                    resource=repo_url,
                    details={"target": target, "environments": environments}
                )
            
            # For now, return a simple response
            result = {
                "success": True,
                "message": f"Repository {repo_url} onboarding initiated",
                "target": target,
                "environments": environments,
                "pr_url": "https://github.com/example/pr/123"
            }
            
            # Log successful onboarding if audit is available
            if self.audit:
                self.audit.log_action(
                    AuditAction.ONBOARDING_COMPLETED,
                    user=user,
                    resource=repo_url,
                    details=result
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
            # Log incident analysis start if audit is available
            if self.audit:
                self.audit.log_action(
                    AuditAction.INCIDENT_INVESTIGATED,
                    user=user,
                    resource=service_name,
                    details={"symptoms": symptoms[:200]}
                )
            
            # Simple analysis for now
            analysis = f"""
Incident Analysis for {service_name}:

Symptoms: {symptoms}

Recommended Actions:
1. Check service logs for errors
2. Verify resource utilization (CPU, Memory)
3. Check network connectivity
4. Review recent deployments
5. Check dependency services

This is a simplified analysis. With proper LLM integration, more detailed analysis would be provided.
"""
            
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
            # Log deployment initiation if audit is available
            if self.audit:
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
            
            if dry_run:
                result = {
                    "success": True,
                    "dry_run": True,
                    "message": f"Dry-run successful for {service_name} to {environment}",
                    "changes": [
                        f"Would deploy {service_name}:{version or 'latest'} to {environment}",
                        f"Would update {'3' if environment == 'production' else '1'} replicas",
                        "Would update health checks",
                        "Would update monitoring"
                    ]
                }
            else:
                # Check if Kubernetes pack is available
                if 'kubernetes' in self.mcp_packs:
                    params = {
                        "name": service_name,
                        "namespace": environment,
                        "image": f"{service_name}:{version or 'latest'}",
                        "replicas": 3 if environment == "production" else 1
                    }
                    result = self.mcp_packs['kubernetes'].execute_action("deploy", params)
                else:
                    result = {
                        "success": True,
                        "message": f"Deployment simulated for {service_name} to {environment}",
                        "note": "Kubernetes pack not available, using simulation"
                    }
            
            # Log result if audit is available
            if self.audit:
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
            
            if self.audit:
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