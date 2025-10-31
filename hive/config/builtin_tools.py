"""Builtin tools catalog for Automagik Hive.

Curated, production-ready tools from Agno framework.
Makes it dead simple to add powerful capabilities to agents.

12-year-old friendly: Pick tools like ordering from a menu!
"""

from typing import Any

# ============================================================
# BUILTIN TOOLS CATALOG
# ============================================================
# All tools are from the Agno framework.
# No custom code needed - just reference by name!
# ============================================================

BUILTIN_TOOLS = {
    # ===== PYTHON EXECUTION =====
    "python_executor": {
        "description": "Execute Python code safely in sandbox",
        "import_path": "agno.tools.python.PythonTools",
        "use_cases": ["data analysis", "calculations", "scripting"],
        "example": """
            tools: ["python_executor"]
            # Agent can now run Python code!
        """,
    },
    # ===== WEB OPERATIONS =====
    "web_search": {
        "description": "Search the web using DuckDuckGo",
        "import_path": "agno.tools.duckduckgo.DuckDuckGoTools",
        "use_cases": ["research", "fact-checking", "current events"],
        "example": """
            tools: ["web_search"]
            # Agent can now search the web!
        """,
    },
    "web_scraper": {
        "description": "Scrape web pages and extract content",
        "import_path": "agno.tools.website.WebsiteTools",
        "use_cases": ["data extraction", "monitoring", "content aggregation"],
        "example": """
            tools: ["web_scraper"]
            # Agent can now scrape websites!
        """,
    },
    # ===== FILE OPERATIONS =====
    "file_reader": {
        "description": "Read and parse files (txt, csv, json, yaml)",
        "import_path": "agno.tools.file.FileTools",
        "use_cases": ["data loading", "config reading", "log analysis"],
        "example": """
            tools: ["file_reader"]
            # Agent can now read files!
        """,
    },
    "csv_tools": {
        "description": "Advanced CSV file operations and analysis",
        "import_path": "agno.tools.csv.CSVTools",
        "use_cases": ["data processing", "CSV analysis", "report generation"],
        "example": """
            tools: ["csv_tools"]
            # Agent can now work with CSV files!
        """,
    },
    # ===== DATABASE =====
    "sql_query": {
        "description": "Execute SQL queries safely",
        "import_path": "agno.tools.sql.SQLTools",
        "use_cases": ["data queries", "reporting", "analytics"],
        "example": """
            tools: ["sql_query"]
            # Agent can now query databases!
        """,
    },
    # ===== API INTEGRATIONS =====
    "github_api": {
        "description": "Interact with GitHub (PRs, issues, repos)",
        "import_path": "agno.tools.github.GithubTools",
        "use_cases": ["code review", "issue management", "repo operations"],
        "example": """
            tools: ["github_api"]
            # Agent can now work with GitHub!
        """,
    },
    "slack_api": {
        "description": "Send Slack messages and notifications",
        "import_path": "agno.tools.slack.SlackTools",
        "use_cases": ["notifications", "team communication", "alerts"],
        "example": """
            tools: ["slack_api"]
            # Agent can now send Slack messages!
        """,
    },
    # ===== SPECIALIZED TOOLS =====
    "calculator": {
        "description": "Perform mathematical calculations",
        "import_path": "agno.tools.calculator.CalculatorTools",
        "use_cases": ["math", "statistics", "financial calculations"],
        "example": """
            tools: ["calculator"]
            # Agent can now do math!
        """,
    },
    "shell_tools": {
        "description": "Execute shell commands safely",
        "import_path": "agno.tools.shell.ShellTools",
        "use_cases": ["system operations", "automation", "deployment"],
        "example": """
            tools: ["shell_tools"]
            # Agent can now run shell commands!
        """,
    },
    "email_tools": {
        "description": "Send and manage emails",
        "import_path": "agno.tools.email.EmailTools",
        "use_cases": ["notifications", "reports", "communication"],
        "example": """
            tools: ["email_tools"]
            # Agent can now send emails!
        """,
    },
    "youtube_tools": {
        "description": "Search and analyze YouTube videos",
        "import_path": "agno.tools.youtube.YouTubeTools",
        "use_cases": ["video research", "content analysis", "transcripts"],
        "example": """
            tools: ["youtube_tools"]
            # Agent can now search YouTube!
        """,
    },
}


# ============================================================
# TOOL CATEGORIES
# ============================================================
# Organize tools by category for easier discovery
# ============================================================

TOOL_CATEGORIES = {
    "execution": ["python_executor", "shell_tools"],
    "web": ["web_search", "web_scraper", "youtube_tools"],
    "files": ["file_reader", "csv_tools"],
    "database": ["sql_query"],
    "api": ["github_api", "slack_api", "email_tools"],
    "computation": ["calculator"],
}


# ============================================================
# TOOL LOADING FUNCTIONS
# ============================================================


def load_builtin_tool(tool_name: str) -> Any | None:
    """Load a builtin tool by name.

    Args:
        tool_name: Name of the builtin tool

    Returns:
        Tool instance or None if not found

    Example:
        >>> tool = load_builtin_tool("web_search")
        >>> result = tool.run("Python tutorials")
    """
    if tool_name not in BUILTIN_TOOLS:
        return None

    tool_config = BUILTIN_TOOLS[tool_name]
    import_path: str = tool_config["import_path"]  # type: ignore[assignment]

    try:
        # Dynamic import
        module_path, class_name = import_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        tool_class = getattr(module, class_name)

        # Instantiate tool
        return tool_class()
    except Exception as e:
        print(f"❌ Failed to load tool '{tool_name}': {e}")
        return None


def get_tool_info(tool_name: str) -> dict[str, Any] | None:
    """Get information about a builtin tool.

    Args:
        tool_name: Name of the builtin tool

    Returns:
        Tool configuration dictionary or None

    Example:
        >>> info = get_tool_info("web_search")
        >>> print(info["description"])
        Search the web using DuckDuckGo
    """
    return BUILTIN_TOOLS.get(tool_name)


def list_builtin_tools(category: str | None = None) -> list[str]:
    """List available builtin tools.

    Args:
        category: Optional category filter

    Returns:
        List of tool names

    Example:
        >>> tools = list_builtin_tools()
        >>> print(tools)
        ['python_executor', 'web_search', ...]

        >>> web_tools = list_builtin_tools(category="web")
        >>> print(web_tools)
        ['web_search', 'web_scraper', 'youtube_tools']
    """
    if category:
        return TOOL_CATEGORIES.get(category, [])
    return list(BUILTIN_TOOLS.keys())


def get_tools_by_category() -> dict[str, list[str]]:
    """Get all tools organized by category.

    Returns:
        Dictionary mapping categories to tool names

    Example:
        >>> by_category = get_tools_by_category()
        >>> print(by_category["web"])
        ['web_search', 'web_scraper', 'youtube_tools']
    """
    return TOOL_CATEGORIES.copy()


def search_tools(query: str) -> list[dict[str, Any]]:
    """Search for tools by description or use case.

    Args:
        query: Search query string

    Returns:
        List of matching tool configurations

    Example:
        >>> results = search_tools("github")
        >>> print(results[0]["description"])
        Interact with GitHub (PRs, issues, repos)
    """
    query_lower = query.lower()
    results = []

    for tool_name, tool_config in BUILTIN_TOOLS.items():
        # Search in description
        description: str = tool_config["description"]  # type: ignore[assignment]
        if query_lower in description.lower():
            results.append({"name": tool_name, **tool_config})
            continue

        # Search in use cases
        use_cases_list: list[str] = tool_config["use_cases"]  # type: ignore[assignment]
        use_cases = " ".join(use_cases_list)
        if query_lower in use_cases.lower():
            results.append({"name": tool_name, **tool_config})

    return results


def print_tool_catalog():
    """Print a formatted catalog of all builtin tools.

    Example:
        >>> print_tool_catalog()
        # Prints nicely formatted tool catalog
    """
    print("\n" + "=" * 60)
    print("BUILTIN TOOLS CATALOG")
    print("=" * 60 + "\n")

    for category, tool_names in TOOL_CATEGORIES.items():
        print(f"\n📦 {category.upper()}")
        print("-" * 60)

        for tool_name in tool_names:
            tool_config = BUILTIN_TOOLS[tool_name]
            print(f"\n  🔧 {tool_name}")
            print(f"     {tool_config['description']}")
            print(f"     Use for: {', '.join(tool_config['use_cases'])}")

    print("\n" + "=" * 60)
    print(f"Total tools: {len(BUILTIN_TOOLS)}")
    print("=" * 60 + "\n")


# ============================================================
# TOOL RECOMMENDATIONS
# ============================================================


def recommend_tools_for_task(task_description: str) -> list[dict[str, Any]]:
    """Recommend tools based on task description.

    Args:
        task_description: Description of the task

    Returns:
        List of recommended tools with explanations

    Example:
        >>> recommendations = recommend_tools_for_task(
        ...     "Build a web scraper that saves data to CSV"
        ... )
        >>> for rec in recommendations:
        ...     print(f"{rec['name']}: {rec['reason']}")
        web_scraper: For extracting web content
        csv_tools: For saving data to CSV files
    """
    task_lower = task_description.lower()
    recommendations = []

    # Keyword-based recommendations
    tool_keywords = {
        "web_search": ["search", "research", "find information", "google"],
        "web_scraper": ["scrape", "extract", "crawl", "website"],
        "file_reader": ["read file", "load file", "parse file"],
        "csv_tools": ["csv", "spreadsheet", "tabular data"],
        "python_executor": ["code", "script", "calculate", "process"],
        "sql_query": ["database", "sql", "query", "data"],
        "github_api": ["github", "repository", "pull request", "issue"],
        "slack_api": ["slack", "notify", "message", "team"],
        "calculator": ["math", "calculate", "sum", "statistics"],
        "shell_tools": ["command", "shell", "bash", "terminal"],
        "email_tools": ["email", "send mail", "notification"],
        "youtube_tools": ["youtube", "video", "transcript"],
    }

    for tool_name, keywords in tool_keywords.items():
        for keyword in keywords:
            if keyword in task_lower:
                tool_config = BUILTIN_TOOLS[tool_name]
                recommendations.append(
                    {
                        "name": tool_name,
                        "description": tool_config["description"],
                        "reason": f"Task mentions '{keyword}'",
                    }
                )
                break  # Only add each tool once

    return recommendations


# ============================================================
# USAGE EXAMPLES
# ============================================================

if __name__ == "__main__":
    # Print full catalog
    print_tool_catalog()

    # Search for tools
    print("\n\n🔍 SEARCH EXAMPLES\n")
    print("Search for 'github':")
    results = search_tools("github")
    for result in results:
        print(f"  - {result['name']}: {result['description']}")

    # Get recommendations
    print("\n\n💡 RECOMMENDATION EXAMPLES\n")
    task = "Build a bot that searches the web and sends Slack notifications"
    print(f"Task: {task}")
    print("\nRecommended tools:")
    recommendations = recommend_tools_for_task(task)
    for rec in recommendations:
        print(f"  - {rec['name']}: {rec['reason']}")
