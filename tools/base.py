"""
Base classes for the DARKBO tools framework
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result returned by a tool execution"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time
        }


class BaseTool(ABC):
    """Abstract base class for all DARKBO tools"""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "parameters_schema": self.get_parameters_schema()
        }
    
    def is_enabled(self) -> bool:
        """Check if tool is enabled"""
        return self.enabled
    
    def enable(self):
        """Enable the tool"""
        self.enabled = True
    
    def disable(self):
        """Disable the tool"""
        self.enabled = False