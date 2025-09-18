from typing import Dict, Any, List, Optional
from mcp_packs.github.github_pack import GitHubPack
from mcp_packs.gitlab.gitlab_pack import GitLabPack
from mcp_packs.kb.kb_pack import KnowledgeBasePack
from mcp_packs.base.mcp_pack import MCPPack
import logging

logger = logging.getLogger(__name__)

class MCPPackManager:
    """Manager for MCP Packs - provides unified interface to all MCP servers"""

    def __init__(self):
        self.packs: Dict[str, MCPPack] = {}

    def register_pack(self, name: str, pack_class: type, config: Dict[str, Any]) -> bool:
        """Register a new MCP pack"""
        try:
            pack = pack_class(config)
            self.packs[name] = pack
            logger.info(f"Registered MCP pack: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register pack {name}: {e}")
            return False

    def initialize_github_pack(self, token: str, allowed_repos: List[str] = None, audit_logger=None) -> bool:
        """Initialize GitHub MCP pack"""
        config = {
            'token': token,
            'allowed_repos': allowed_repos or [],
            'audit_logger': audit_logger
        }
        return self.register_pack('github', GitHubPack, config)

    def initialize_gitlab_pack(self, token: str, allowed_repos: List[str] = None, audit_logger=None) -> bool:
        """Initialize GitLab MCP pack"""
        config = {
            'token': token,
            'allowed_repos': allowed_repos or [],
            'audit_logger': audit_logger
        }
        return self.register_pack('gitlab', GitLabPack, config)

    def initialize_kb_pack(self, kb_manager, audit_logger=None) -> bool:
        """Initialize Knowledge Base MCP pack"""
        config = {
            'kb_manager': kb_manager,
            'audit_logger': audit_logger
        }
        return self.register_pack('kb', KnowledgeBasePack, config)

    def get_pack(self, name: str) -> Optional[MCPPack]:
        """Get a registered pack by name"""
        return self.packs.get(name)

    def execute_action(self, pack_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action on a specific pack"""
        pack = self.get_pack(pack_name)
        if not pack:
            return {
                'success': False,
                'error': f'Pack {pack_name} not found or not initialized'
            }

        if not pack.initialized:
            return {
                'success': False,
                'error': f'Pack {pack_name} not properly initialized'
            }

        try:
            return pack.execute_action(action, params)
        except Exception as e:
            logger.error(f"Error executing {action} on {pack_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_available_actions(self, pack_name: str) -> List[str]:
        """Get available actions for a pack"""
        pack = self.get_pack(pack_name)
        if not pack:
            return []
        return pack.get_available_actions()

    def health_check(self) -> Dict[str, Any]:
        """Health check for all registered packs"""
        status = {
            'overall_status': 'healthy',
            'packs': {}
        }

        unhealthy_packs = 0
        for name, pack in self.packs.items():
            pack_health = pack.health_check()
            status['packs'][name] = pack_health

            if pack_health.get('status') != 'healthy':
                unhealthy_packs += 1

        if unhealthy_packs > 0:
            status['overall_status'] = 'degraded' if unhealthy_packs < len(self.packs) else 'unhealthy'

        status['total_packs'] = len(self.packs)
        status['unhealthy_packs'] = unhealthy_packs

        return status

    def list_packs(self) -> Dict[str, Dict[str, Any]]:
        """List all registered packs with their info"""
        pack_info = {}
        for name, pack in self.packs.items():
            pack_info[name] = {
                'name': pack.name,
                'initialized': pack.initialized,
                'available_actions': pack.get_available_actions(),
                'health': pack.health_check()
            }
        return pack_info

    def cleanup(self):
        """Cleanup all packs"""
        for name, pack in self.packs.items():
            try:
                pack.cleanup()
                logger.info(f"Cleaned up pack: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up pack {name}: {e}")

        self.packs.clear()

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error during pack manager cleanup: {e}")


# Global instance for use across the application
pack_manager = MCPPackManager()