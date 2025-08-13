"""
DARKBO Tools Framework

This module provides a framework for external tools that can be used
by the AI worker to enhance query responses with real-time data.
"""

from .base import BaseTool, ToolResult
from .datetime_tool import DateTimeTool
from .web_search_tool import WebSearchTool
from .manager import ToolManager

__all__ = ['BaseTool', 'ToolResult', 'DateTimeTool', 'WebSearchTool', 'ToolManager']