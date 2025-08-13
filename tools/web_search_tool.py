"""
Web Search Tool for DARKBO
Provides web search capabilities using the public Searx instance
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
import requests
from urllib.parse import quote_plus

from .base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Tool for performing web searches"""

    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for current information using Searx",
            version="1.0.0"
        )
        self.base_url = "https://searx.be/search"

    async def execute(self,
                     query: str,
                     max_results: Optional[int] = 5,
                     safe_search: Optional[str] = "moderate",
                     **kwargs) -> ToolResult:
        """Execute the web search tool"""
        start_time = time.time()

        if not query or not query.strip():
            return ToolResult(
                success=False,
                error="Search query cannot be empty",
                execution_time=time.time() - start_time
            )

        try:
            search_results = await self._search_searx(query, max_results, safe_search)

            result_data = {
                "query": query,
                "results": search_results,
                "total_results": len(search_results),
                "max_results_requested": max_results,
                "safe_search": safe_search,
                "search_engine": "Searx"
            }

            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Web search error: {str(e)}",
                execution_time=time.time() - start_time
            )

    async def _search_searx(self, query: str, max_results: int, safe_search: str) -> List[Dict[str, Any]]:
        """
        Perform search using a public Searx instance.

        Note: This is a simplified implementation. For production use, consider:
        - Using official search APIs (Google Custom Search, Bing Search API)
        - Implementing proper rate limiting
        - Adding caching mechanisms
        - Better error handling and retries
        """

        try:
            safesearch_map = {
                "off": 0,
                "moderate": 1,
                "strict": 2,
            }

            params = {
                "q": query,
                "format": "json",
                "language": "en",
                "safesearch": safesearch_map.get(safe_search.lower(), 1),
            }

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/117.0 Safari/537.36"
                )
            }

            loop = asyncio.get_event_loop()
            response = None
            for attempt in range(3):
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(
                        self.base_url,
                        params=params,
                        headers=headers,
                        timeout=10,
                    ),
                )

                if response.status_code == 200:
                    break
                if response.status_code == 202:
                    await asyncio.sleep(1 + attempt)
                    continue
                return [{
                    "title": "Search Error",
                    "snippet": f"Search service returned status code {response.status_code}",
                    "url": "",
                    "source": "error",
                }]

            if response is None or response.status_code != 200:
                return [{
                    "title": "Search Error",
                    "snippet": f"Search service returned status code {response.status_code if response else 'N/A'}",
                    "url": "",
                    "source": "error",
                }]

            data = response.json()
            results = []

            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", ""),
                    "source": ", ".join(item.get("engines", [])) or "searx",
                })

                if len(results) >= max_results:
                    break

            if len(results) == 0:
                results.append({
                    "title": f"Search for: {query}",
                    "snippet": f"No results found. Try searching for '{query}' on a search engine for more detailed results.",
                    "url": f"https://searx.be/search?q={quote_plus(query)}",
                    "source": "Searx Search Link",
                })

            return results[:max_results]

        except requests.exceptions.RequestException:
            return [{
                "title": "Search Service Unavailable",
                "snippet": f"Web search is currently unavailable due to network restrictions. For information about '{query}', please check your local knowledge base or contact support directly.",
                "url": "",
                "source": "error",
            }]
        except Exception as e:
            return [{
                "title": "Search Error",
                "snippet": f"An error occurred while searching: {str(e)}",
                "url": "",
                "source": "error",
            }]

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for web search tool parameters"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string",
                    "minLength": 1,
                    "examples": ["current weather in New York", "latest Python version", "how to install Docker"]
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5
                },
                "safe_search": {
                    "type": "string",
                    "description": "Safe search setting",
                    "enum": ["strict", "moderate", "off"],
                    "default": "moderate",
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }

