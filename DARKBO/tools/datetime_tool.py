"""
Date and Time Tool for DARKBO
Provides current date, time, and timezone information
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .base import BaseTool, ToolResult


class DateTimeTool(BaseTool):
    """Tool for getting current date and time information"""
    
    def __init__(self):
        super().__init__(
            name="datetime",
            description="Get current date, time, and timezone information",
            version="1.0.0"
        )
    
    async def execute(self, 
                     format: Optional[str] = None, 
                     timezone_name: Optional[str] = None,
                     **kwargs) -> ToolResult:
        """
        Execute the datetime tool
        
        Args:
            format: Optional datetime format string (default: ISO format)
            timezone_name: Optional timezone name (default: UTC)
            **kwargs: Additional parameters (ignored)
        
        Returns:
            ToolResult with datetime information
        """
        start_time = time.time()
        
        try:
            # Get current datetime
            if timezone_name:
                # For simplicity, just support UTC for now
                # In a full implementation, you'd use pytz or zoneinfo
                if timezone_name.upper() == 'UTC':
                    now = datetime.now(timezone.utc)
                else:
                    # Fallback to UTC if unsupported timezone
                    now = datetime.now(timezone.utc)
            else:
                now = datetime.now(timezone.utc)
            
            # Format datetime
            if format:
                try:
                    formatted_time = now.strftime(format)
                except ValueError as e:
                    return ToolResult(
                        success=False,
                        error=f"Invalid datetime format: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            else:
                formatted_time = now.isoformat()
            
            # Prepare result data
            result_data = {
                "current_datetime": formatted_time,
                "iso_format": now.isoformat(),
                "timestamp": now.timestamp(),
                "timezone": str(now.tzinfo),
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "weekday": now.strftime("%A"),
                "format_used": format or "ISO",
                "timezone_requested": timezone_name or "UTC"
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"DateTime tool error: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for datetime tool parameters"""
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Optional datetime format string (e.g., '%Y-%m-%d %H:%M:%S')",
                    "examples": ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%B %d, %Y"]
                },
                "timezone_name": {
                    "type": "string", 
                    "description": "Optional timezone name (currently supports 'UTC')",
                    "examples": ["UTC"]
                }
            },
            "additionalProperties": False
        }