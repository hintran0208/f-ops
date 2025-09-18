from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from app.core.kb_manager import KnowledgeBaseManager
from app.core.audit_logger import AuditLogger
import logging

logger = logging.getLogger(__name__)

class MCPKnowledgeBase:
    """MCP Knowledge Base server for connect, sync, search, compose operations"""

    def __init__(self, kb_manager: KnowledgeBaseManager, audit_logger: AuditLogger):
        self.kb = kb_manager
        self.audit_logger = audit_logger

    async def connect(self, uri: str) -> Dict[str, Any]:
        """Crawl and ingest content from URI"""
        logger.info(f"Connecting to knowledge source: {uri}")

        try:
            if "github.com" in uri:
                result = await self._connect_github(uri)
            elif "confluence" in uri:
                result = await self._connect_confluence(uri)
            elif "notion" in uri:
                result = await self._connect_notion(uri)
            else:
                result = await self._connect_generic(uri)

            # Log the connection
            self.audit_logger.log_operation({
                "type": "kb_connect",
                "agent": "mcp_kb",
                "inputs": {"uri": uri},
                "outputs": result
            })

            return result

        except Exception as e:
            logger.error(f"Failed to connect to {uri}: {e}")
            error_result = {
                "success": False,
                "uri": uri,
                "error": str(e),
                "documents": 0,
                "collections": []
            }

            self.audit_logger.log_operation({
                "type": "kb_connect_error",
                "agent": "mcp_kb",
                "inputs": {"uri": uri},
                "outputs": error_result
            })

            return error_result

    async def _connect_github(self, repo_url: str) -> Dict[str, Any]:
        """Ingest GitHub repo documentation"""
        logger.info(f"Ingesting GitHub repo: {repo_url}")

        # Extract owner/repo from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            raise ValueError("Invalid GitHub URL format")

        owner, repo = match.groups()
        repo = repo.rstrip('.git')

        documents_added = 0
        collections_updated = set()

        # GitHub API URLs
        api_base = f"https://api.github.com/repos/{owner}/{repo}"

        async with httpx.AsyncClient() as client:
            # Get README
            try:
                readme_response = await client.get(f"{api_base}/readme")
                if readme_response.status_code == 200:
                    readme_data = readme_response.json()
                    readme_content = self._decode_base64_content(readme_data['content'])

                    self.kb.add_document(
                        collection='docs',
                        document=readme_content,
                        metadata={
                            'source': 'github',
                            'type': 'readme',
                            'repo': f"{owner}/{repo}",
                            'url': repo_url,
                            'title': f"{repo} README"
                        },
                        doc_id=f"github_{owner}_{repo}_readme"
                    )
                    documents_added += 1
                    collections_updated.add('docs')

            except Exception as e:
                logger.warning(f"Could not fetch README: {e}")

            # Get workflow files
            try:
                workflows_response = await client.get(f"{api_base}/contents/.github/workflows")
                if workflows_response.status_code == 200:
                    workflows = workflows_response.json()
                    for workflow in workflows:
                        if workflow['name'].endswith(('.yml', '.yaml')):
                            workflow_response = await client.get(workflow['download_url'])
                            if workflow_response.status_code == 200:
                                self.kb.add_document(
                                    collection='pipelines',
                                    document=workflow_response.text,
                                    metadata={
                                        'source': 'github',
                                        'type': 'workflow',
                                        'repo': f"{owner}/{repo}",
                                        'filename': workflow['name'],
                                        'title': f"{repo} - {workflow['name']}"
                                    },
                                    doc_id=f"github_{owner}_{repo}_{workflow['name'].replace('.', '_')}"
                                )
                                documents_added += 1
                                collections_updated.add('pipelines')

            except Exception as e:
                logger.warning(f"Could not fetch workflows: {e}")

        return {
            "success": True,
            "uri": repo_url,
            "documents": documents_added,
            "collections": list(collections_updated),
            "source_type": "github"
        }

    async def _connect_confluence(self, confluence_url: str) -> Dict[str, Any]:
        """Ingest Confluence documentation"""
        # Phase 1: Basic implementation
        logger.info(f"Confluence ingestion not fully implemented in Phase 1: {confluence_url}")

        return {
            "success": True,
            "uri": confluence_url,
            "documents": 0,
            "collections": [],
            "source_type": "confluence",
            "note": "Confluence ingestion will be implemented in Phase 2"
        }

    async def _connect_notion(self, notion_url: str) -> Dict[str, Any]:
        """Ingest Notion documentation"""
        # Phase 1: Basic implementation
        logger.info(f"Notion ingestion not fully implemented in Phase 1: {notion_url}")

        return {
            "success": True,
            "uri": notion_url,
            "documents": 0,
            "collections": [],
            "source_type": "notion",
            "note": "Notion ingestion will be implemented in Phase 2"
        }

    async def _connect_generic(self, url: str) -> Dict[str, Any]:
        """Ingest generic web documentation"""
        logger.info(f"Ingesting generic web content: {url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract text content
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)

            # Add to docs collection
            self.kb.add_document(
                collection='docs',
                document=clean_text,
                metadata={
                    'source': 'web',
                    'type': 'documentation',
                    'url': url,
                    'title': soup.title.string if soup.title else "Web Documentation",
                    'domain': urlparse(url).netloc
                },
                doc_id=f"web_{urlparse(url).netloc}_{hash(url) % 10000}"
            )

            return {
                "success": True,
                "uri": url,
                "documents": 1,
                "collections": ['docs'],
                "source_type": "web"
            }

    def search(self, query: str, collections: List[str] = None) -> List[Dict]:
        """Multi-collection search"""
        logger.info(f"Searching KB: '{query}' in collections: {collections}")

        results = []
        search_collections = collections or list(self.kb.collections.keys())

        for collection in search_collections:
            try:
                collection_results = self.kb.search(collection, query, k=3)
                results.extend(collection_results)
            except Exception as e:
                logger.warning(f"Search failed for collection {collection}: {e}")

        # Log search
        self.audit_logger.log_kb_usage(
            query=query,
            collection=",".join(search_collections),
            results_count=len(results),
            citations=[r['citation'] for r in results]
        )

        return results

    def compose(self, template_type: str, context: Dict) -> str:
        """Compose content from KB patterns using RAG"""
        logger.info(f"Composing {template_type} with context: {list(context.keys())}")

        # Search for relevant patterns
        search_query = context.get('query', template_type)
        relevant_docs = self.search(search_query)

        if not relevant_docs:
            return f"# {template_type.title()}\n\nNo relevant patterns found in knowledge base."

        # Simple composition for Phase 1
        composed_content = f"# {template_type.title()}\n\n"
        composed_content += "## Based on Knowledge Base Patterns\n\n"

        for doc in relevant_docs[:3]:  # Use top 3 results
            composed_content += f"- {doc['metadata'].get('title', 'Untitled')}\n"
            composed_content += f"  {doc['text'][:200]}...\n\n"

        # Add citations
        citations = [doc['citation'] for doc in relevant_docs]
        composed_content += "## Citations\n"
        for i, citation in enumerate(citations, 1):
            composed_content += f"{i}. {citation}\n"

        return composed_content

    def sync(self, source_id: str) -> Dict[str, Any]:
        """Sync/refresh knowledge source"""
        # Phase 1: Basic implementation
        logger.info(f"Sync operation requested for: {source_id}")

        return {
            "success": True,
            "source_id": source_id,
            "synchronized": False,
            "note": "Sync functionality will be implemented in Phase 2"
        }

    def _decode_base64_content(self, base64_content: str) -> str:
        """Decode base64 GitHub API content"""
        import base64
        return base64.b64decode(base64_content).decode('utf-8')