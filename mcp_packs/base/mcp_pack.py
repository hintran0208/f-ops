from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class MCPPack(ABC):
    """Base class for all MCP (Model Context Protocol) packs"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP Pack with configuration
        
        Args:
            config: Configuration dictionary for the pack
        """
        self.config = config
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        self.initialized = False
        
        try:
            self.validate_config()
            self.initialize()
            self.initialized = True
        except Exception as e:
            self.logger.warning(f"Pack {self.name} initialization deferred: {e}")
            # Pack can still be used but may have limited functionality
    
    @abstractmethod
    def validate_config(self):
        """
        Validate pack configuration
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def initialize(self):
        """Initialize pack resources and connections"""
        pass
    
    @abstractmethod
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a pack action
        
        Args:
            action: Action name to execute
            params: Parameters for the action
            
        Returns:
            Dict containing action results
            
        Raises:
            ValueError: If action is not supported
        """
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """
        Return list of available actions
        
        Returns:
            List of action names
        """
        pass
    
    def get_action_schema(self, action: str) -> Optional[Dict[str, Any]]:
        """
        Get schema/documentation for a specific action
        
        Args:
            action: Action name
            
        Returns:
            Schema dictionary or None if not available
        """
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the pack
        
        Returns:
            Health status dictionary
        """
        return {
            "name": self.name,
            "status": "healthy",
            "message": "Pack is operational"
        }
    
    def cleanup(self):
        """Cleanup resources when pack is destroyed"""
        pass
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error during {self.name} cleanup: {e}")