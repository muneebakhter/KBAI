"""
Tool Manager for DARKBO
Manages and executes tools for the AI worker
"""

import asyncio
from typing import Dict, List, Any, Optional
from .base import BaseTool, ToolResult
from .datetime_tool import DateTimeTool
from .web_search_tool import WebSearchTool


class ToolManager:
    """Manages available tools and executes them"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the default tools"""
        self.register_tool(DateTimeTool())
        self.register_tool(WebSearchTool())
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            del self.tools[tool_name]
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [tool.get_info() for tool in self.tools.values() if tool.is_enabled()]
    
    def get_enabled_tools(self) -> Dict[str, BaseTool]:
        """Get all enabled tools"""
        return {name: tool for name, tool in self.tools.items() if tool.is_enabled()}
    
    async def execute_tool(self, tool_name: str, **parameters) -> ToolResult:
        """Execute a tool with given parameters"""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found"
            )
        
        if not tool.is_enabled():
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is disabled"
            )
        
        try:
            return await tool.execute(**parameters)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error executing tool '{tool_name}': {str(e)}"
            )
    
    def should_use_tool(self, query: str) -> List[str]:
        """
        Determine which tools should be used for a given query
        This is a simple keyword-based implementation.
        In a more sophisticated system, you might use NLP or ML models.
        """
        query_lower = query.lower()
        suggested_tools = []
        
        # Check for datetime-related keywords first (higher priority)
        datetime_keywords = [
            'time', 'date', 'when', 'today', 'now', 'current', 
            'year', 'month', 'day', 'hour', 'minute', 'clock',
            'calendar', 'schedule', 'deadline'
        ]
        
        if any(keyword in query_lower for keyword in datetime_keywords):
            if 'datetime' in self.tools and self.tools['datetime'].is_enabled():
                suggested_tools.append('datetime')
        
        # Check for web search keywords
        web_search_keywords = [
            'search', 'find', 'look up', 'what is', 'who is', 
            'latest', 'recent', 'news', 'update',
            'website', 'online', 'internet', 'web', 'google',
            'how to', 'where', 'why'
        ]
        
        # Also trigger web search for questions about things not in KB
        question_indicators = ['what', 'who', 'where', 'why', 'how']
        
        # Don't use web search for datetime queries to avoid conflicts
        datetime_query = any(keyword in query_lower for keyword in datetime_keywords)
        
        if not datetime_query and (any(keyword in query_lower for keyword in web_search_keywords) or 
            any(query_lower.startswith(q) for q in question_indicators)):
            if 'web_search' in self.tools and self.tools['web_search'].is_enabled():
                suggested_tools.append('web_search')
        
        return suggested_tools