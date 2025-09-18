from mcp_packs.base.mcp_pack import MCPPack
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class KnowledgeBasePack(MCPPack):
    """Knowledge Base MCP Pack for connect, search, and compose operations"""

    def validate_config(self):
        """Validate KB configuration"""
        if 'kb_manager' not in self.config:
            raise ValueError("KnowledgeBaseManager instance is required in configuration")

    def initialize(self):
        """Initialize KB pack"""
        self.kb_manager = self.config['kb_manager']
        self.audit_logger = self.config.get('audit_logger')
        logger.info("Knowledge Base Pack initialized")

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute KB action"""
        actions = {
            'connect': self.connect,
            'search': self.search,
            'compose': self.compose,
            'sync': self.sync,
            'get_stats': self.get_stats
        }

        if action not in actions:
            raise ValueError(f"Unknown action: {action}")

        return actions[action](params)

    def get_available_actions(self) -> List[str]:
        """Return list of available KB actions"""
        return ['connect', 'search', 'compose', 'sync', 'get_stats']

    async def connect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect and ingest content from URI"""
        uri = params['uri']
        logger.info(f"Connecting to knowledge source: {uri}")

        try:
            if "github.com" in uri:
                return await self._connect_github(uri)
            elif "confluence" in uri:
                return await self._connect_confluence(uri)
            elif "notion" in uri:
                return await self._connect_notion(uri)
            else:
                return await self._connect_generic(uri)
        except Exception as e:
            logger.error(f"Failed to connect to {uri}: {e}")
            return {
                "success": False,
                "error": str(e),
                "uri": uri
            }

    async def _connect_github(self, repo_url: str) -> Dict[str, Any]:
        """Ingest GitHub repository documentation"""
        try:
            # Extract owner/repo from URL
            import re
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if not match:
                raise ValueError("Invalid GitHub URL format")

            owner, repo = match.groups()
            repo = repo.rstrip('.git')

            # Fetch repository content via GitHub API
            base_url = f"https://api.github.com/repos/{owner}/{repo}"

            async with httpx.AsyncClient() as client:
                # Get repository info
                repo_response = await client.get(f"{base_url}")
                repo_data = repo_response.json()

                # Get README
                try:
                    readme_response = await client.get(f"{base_url}/readme")
                    readme_data = readme_response.json()
                    readme_content = self._decode_base64_content(readme_data['content'])
                except:
                    readme_content = "No README found"

                # Get workflow files
                workflows = []
                try:
                    workflows_response = await client.get(f"{base_url}/contents/.github/workflows")
                    if workflows_response.status_code == 200:
                        workflows_data = workflows_response.json()
                        for workflow in workflows_data:
                            workflow_response = await client.get(workflow['download_url'])
                            workflows.append({
                                'name': workflow['name'],
                                'content': workflow_response.text
                            })
                except:
                    pass

            # Store in appropriate collections
            documents_added = 0
            collections_updated = []

            # Add README to docs collection
            if readme_content and readme_content != "No README found":
                self.kb_manager.collections['docs'].add(
                    documents=[readme_content],
                    metadatas=[{
                        'source': 'github',
                        'repo': f"{owner}/{repo}",
                        'type': 'readme',
                        'title': f"{owner}/{repo} README"
                    }],
                    ids=[f"github-{owner}-{repo}-readme"]
                )
                documents_added += 1
                collections_updated.append('docs')

            # Add workflows to pipelines collection
            for workflow in workflows:
                self.kb_manager.collections['pipelines'].add(
                    documents=[workflow['content']],
                    metadatas=[{
                        'source': 'github',
                        'repo': f"{owner}/{repo}",
                        'type': 'workflow',
                        'title': f"{workflow['name']} workflow",
                        'filename': workflow['name']
                    }],
                    ids=[f"github-{owner}-{repo}-{workflow['name']}"]
                )
                documents_added += 1
                collections_updated.append('pipelines')

            logger.info(f"Ingested {documents_added} documents from {repo_url}")

            return {
                "success": True,
                "documents": documents_added,
                "collections": list(set(collections_updated)),
                "repo": f"{owner}/{repo}",
                "uri": repo_url
            }

        except Exception as e:
            logger.error(f"Failed to connect to GitHub repo {repo_url}: {e}")
            raise

    async def _connect_confluence(self, confluence_url: str) -> Dict[str, Any]:
        """Ingest Confluence content"""
        # Placeholder for Confluence integration
        logger.warning("Confluence integration not yet implemented")
        return {
            "success": False,
            "error": "Confluence integration not yet implemented",
            "uri": confluence_url
        }

    async def _connect_notion(self, notion_url: str) -> Dict[str, Any]:
        """Ingest Notion content"""
        # Placeholder for Notion integration
        logger.warning("Notion integration not yet implemented")
        return {
            "success": False,
            "error": "Notion integration not yet implemented",
            "uri": notion_url
        }

    async def _connect_generic(self, uri: str) -> Dict[str, Any]:
        """Ingest generic web content"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(uri)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract title and text content
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "Untitled"

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                text_content = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = '\n'.join(chunk for chunk in chunks if chunk)

                # Store in docs collection
                self.kb_manager.collections['docs'].add(
                    documents=[text_content],
                    metadatas=[{
                        'source': 'web',
                        'url': uri,
                        'type': 'webpage',
                        'title': title_text
                    }],
                    ids=[f"web-{hash(uri)}"]
                )

                logger.info(f"Ingested content from {uri}")

                return {
                    "success": True,
                    "documents": 1,
                    "collections": ['docs'],
                    "title": title_text,
                    "uri": uri
                }

        except Exception as e:
            logger.error(f"Failed to connect to generic URI {uri}: {e}")
            raise

    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base"""
        query = params['query']
        collections = params.get('collections', list(self.kb_manager.collections.keys()))
        k = params.get('k', 5)

        logger.info(f"Searching KB: '{query}' in {collections}")

        try:
            results = []
            for collection_name in collections:
                if collection_name in self.kb_manager.collections:
                    collection_results = self.kb_manager.search(collection_name, query, k)
                    results.extend(collection_results)

            # Sort by relevance and limit results
            results = results[:k]

            logger.info(f"Found {len(results)} results for query: '{query}'")

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "collections_searched": collections
            }

        except Exception as e:
            logger.error(f"KB search failed for query '{query}': {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def compose(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compose content from KB patterns"""
        template_type = params['template_type']
        context = params.get('context', {})

        logger.info(f"Composing content: {template_type}")

        try:
            # Search for relevant patterns
            search_query = context.get('query', template_type)
            relevant_docs = self.search({
                'query': search_query,
                'collections': [template_type] if template_type in self.kb_manager.collections else None,
                'k': 3
            })

            if not relevant_docs.get('results'):
                return {
                    "success": False,
                    "error": f"No relevant patterns found for {template_type}",
                    "template_type": template_type
                }

            # Compose content from patterns (simplified)
            patterns = [result['text'] for result in relevant_docs['results']]
            citations = [result['citation'] for result in relevant_docs['results']]

            composed_content = f"# Generated {template_type.title()}\n\n"
            composed_content += "Based on the following patterns:\n\n"

            for i, pattern in enumerate(patterns[:2], 1):
                composed_content += f"## Pattern {i}\n{pattern[:500]}...\n\n"

            composed_content += "\n# Citations\n"
            for i, citation in enumerate(citations, 1):
                composed_content += f"{i}. {citation}\n"

            return {
                "success": True,
                "template_type": template_type,
                "content": composed_content,
                "citations": citations,
                "patterns_used": len(patterns)
            }

        except Exception as e:
            logger.error(f"Composition failed for {template_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "template_type": template_type
            }

    def sync(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync existing knowledge sources"""
        logger.info("Syncing knowledge sources")

        # Placeholder for sync implementation
        return {
            "success": True,
            "message": "Sync functionality not yet implemented",
            "sources_synced": 0
        }

    def get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            stats = self.kb_manager.get_collection_stats()

            return {
                "success": True,
                "collections": stats,
                "total_documents": sum(s["document_count"] for s in stats.values()),
                "status": "operational"
            }

        except Exception as e:
            logger.error(f"Failed to get KB stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _decode_base64_content(self, content: str) -> str:
        """Decode base64 content from GitHub API"""
        import base64
        try:
            decoded_bytes = base64.b64decode(content)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {e}")
            return ""

    def health_check(self) -> Dict[str, Any]:
        """Check KB pack health"""
        try:
            stats = self.kb_manager.get_collection_stats()

            return {
                "name": self.name,
                "status": "healthy",
                "collections_count": len(stats),
                "total_documents": sum(s["document_count"] for s in stats.values()),
                "chroma_status": "connected"
            }
        except Exception as e:
            return {
                "name": self.name,
                "status": "unhealthy",
                "error": str(e)
            }