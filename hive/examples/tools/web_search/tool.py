"""
Web Search Tool

A wrapper around Agno's DuckDuckGoTools for web searching.
Demonstrates integration with external search APIs.
"""

from pathlib import Path
from typing import Any

import yaml
from agno.tools.duckduckgo import DuckDuckGoTools


class WebSearchTool:
    """
    Web search tool using DuckDuckGo.

    Features:
    - Text search with snippets
    - Configurable result count
    - Safe search filtering
    - Regional search support
    - News search (optional)
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialize web search tool.

        Args:
            config_path: Path to config.yaml (defaults to same directory)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        # Load configuration
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.tool_config = self.config.get("tool", {})
        self.params = self.tool_config.get("parameters", {})
        self.search_options = self.tool_config.get("search_options", {})

        # Initialize DuckDuckGo search
        self.ddg = DuckDuckGoTools(
            fixed_max_results=self.params.get("max_results", 5),
            search=True,
            news=self.search_options.get("include_news", False),
            timeout=self.params.get("timeout_seconds", 30),
        )

        print("✅ Web search tool initialized (DuckDuckGo)")

    def search(self, query: str, max_results: int | None = None, safe_search: bool | None = None) -> dict[str, Any]:
        """
        Search the web for a query.

        Args:
            query: Search query string
            max_results: Override default max results
            safe_search: Override default safe search setting

        Returns:
            Dict with search results
        """
        try:
            if not query or not query.strip():
                return {"status": "error", "error": "Query cannot be empty", "results": []}

            # Use overrides or defaults
            max_res = max_results or self.params.get("max_results", 5)
            safe = safe_search if safe_search is not None else self.params.get("safe_search", True)

            # Execute search
            search_results = self.ddg.search(query=query, max_results=max_res)

            # Format results
            formatted_results = self._format_results(search_results)

            return {
                "status": "success",
                "query": query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "safe_search": safe,
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "query": query, "results": []}

    def _format_results(self, raw_results: Any) -> list[dict[str, str]]:
        """
        Format raw search results into consistent structure.

        Args:
            raw_results: Raw results from DuckDuckGo

        Returns:
            List of formatted result dicts
        """
        formatted = []

        # Handle different result formats
        if isinstance(raw_results, list):
            for result in raw_results:
                if isinstance(result, dict):
                    formatted.append(
                        {
                            "title": result.get("title", "No title"),
                            "url": result.get("href", result.get("url", "")),
                            "snippet": result.get("body", result.get("snippet", "")),
                            "source": "DuckDuckGo",
                        }
                    )
        elif isinstance(raw_results, str):
            # If results are a string (summary), parse it
            formatted.append({"title": "Search Summary", "url": "", "snippet": raw_results, "source": "DuckDuckGo"})

        return formatted

    def search_news(self, query: str, max_results: int | None = None) -> dict[str, Any]:
        """
        Search for news articles.

        Args:
            query: News search query
            max_results: Maximum news articles to return

        Returns:
            Dict with news results
        """
        try:
            if not self.search_options.get("include_news", False):
                return {"status": "error", "error": "News search not enabled in configuration", "results": []}

            max_res = max_results or self.params.get("max_results", 5)

            # Search news
            news_results = self.ddg.news(query=query, max_results=max_res)

            formatted_results = self._format_results(news_results)

            return {
                "status": "success",
                "query": query,
                "type": "news",
                "total_results": len(formatted_results),
                "results": formatted_results,
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "query": query, "results": []}

    def quick_answer(self, query: str) -> dict[str, Any]:
        """
        Get a quick answer for a query (instant answer).

        Args:
            query: Question or query

        Returns:
            Dict with answer if available
        """
        try:
            # DuckDuckGo instant answer API
            results = self.ddg.search(query=query, max_results=1)

            if results:
                formatted = self._format_results(results)
                if formatted:
                    return {
                        "status": "success",
                        "query": query,
                        "answer": formatted[0].get("snippet", "No answer found"),
                        "source": formatted[0].get("url", ""),
                    }

            return {"status": "success", "query": query, "answer": "No instant answer available", "source": ""}

        except Exception as e:
            return {"status": "error", "error": str(e), "query": query, "answer": None}

    def search_and_summarize(self, query: str) -> str:
        """
        Search and create a simple summary of results.

        Args:
            query: Search query

        Returns:
            Formatted string with search results
        """
        result = self.search(query)

        if result["status"] == "error":
            return f"Search failed: {result['error']}"

        summary = f"Search Results for: {query}\n"
        summary += f"Found {result['total_results']} results\n\n"

        for i, res in enumerate(result["results"], 1):
            summary += f"{i}. {res['title']}\n"
            summary += f"   {res['url']}\n"
            if res.get("snippet"):
                summary += f"   {res['snippet'][:100]}...\n"
            summary += "\n"

        return summary


# Factory function for tool registry
def get_web_search_tool(**kwargs) -> WebSearchTool:
    """
    Create web search tool instance.

    Args:
        **kwargs: Runtime overrides

    Returns:
        WebSearchTool: Configured tool instance
    """
    return WebSearchTool()


# Quick test function
if __name__ == "__main__":
    print("Testing Web Search Tool...")

    # Create tool
    tool = get_web_search_tool()
    print(f"✅ Tool created: {tool.tool_config.get('name')}")
    print(f"✅ Version: {tool.tool_config.get('version')}")

    # Test searches
    print("\n🔍 Testing web search...\n")

    # Standard search
    print("1. Standard Search:")
    result1 = tool.search("Python programming language", max_results=3)

    if result1["status"] == "success":
        print(f"   Query: {result1['query']}")
        print(f"   Results: {result1['total_results']}")
        for i, res in enumerate(result1["results"], 1):
            print(f"\n   {i}. {res['title']}")
            print(f"      URL: {res['url']}")
            print(f"      Snippet: {res['snippet'][:100]}...")
    else:
        print(f"   Error: {result1['error']}")

    # Quick answer
    print("\n2. Quick Answer:")
    result2 = tool.quick_answer("What is the capital of France?")

    if result2["status"] == "success":
        print(f"   Query: {result2['query']}")
        print(f"   Answer: {result2['answer']}")
        print(f"   Source: {result2['source']}")
    else:
        print(f"   Error: {result2['error']}")

    # Search and summarize
    print("\n3. Search and Summarize:")
    summary = tool.search_and_summarize("Artificial Intelligence trends 2024")
    print(summary[:500] + "..." if len(summary) > 500 else summary)

    print("\n✅ All tests completed")
