"""Tool recommendation system for agent generation.

Maps use case requirements to appropriate Agno builtin tools.
Minimalist approach: only recommend what's truly needed.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolRecommendation:
    """Tool recommendation with configuration."""

    tool_name: str
    tool_class: str  # Python import path
    reasoning: str
    required: bool  # True if essential, False if optional
    config_hints: Optional[dict] = None  # Optional configuration parameters


@dataclass
class ToolCatalogEntry:
    """Tool catalog entry with metadata."""

    name: str
    class_path: str
    description: str
    use_cases: list[str]  # Keywords for matching
    keywords: list[str]  # Additional matching terms
    required_for: list[str]  # Use cases where this is required
    conflicts_with: list[str]  # Tools that shouldn't be used together
    config_params: Optional[dict] = None


class ToolRecommender:
    """Intelligent tool recommendation based on use case analysis.

    Usage:
        recommender = ToolRecommender()
        tools = recommender.recommend(
            description="Build a customer support bot with web search"
        )
    """

    # Builtin tools catalog (Agno native tools)
    BUILTIN_TOOLS = {
        # Web and search tools
        "DuckDuckGoTools": ToolCatalogEntry(
            name="DuckDuckGoTools",
            class_path="agno.tools.duckduckgo",
            description="Web search using DuckDuckGo (privacy-focused)",
            use_cases=["search", "research", "web", "lookup", "information"],
            keywords=["internet", "online", "query", "find"],
            required_for=["web_search", "research_agent", "information_retrieval"],
            conflicts_with=["TavilyTools"],  # Similar purpose
        ),
        "TavilyTools": ToolCatalogEntry(
            name="TavilyTools",
            class_path="agno.tools.tavily",
            description="AI-optimized search engine (requires API key)",
            use_cases=["search", "research", "web", "ai_search"],
            keywords=["internet", "online", "semantic"],
            required_for=["semantic_search"],
            conflicts_with=["DuckDuckGoTools"],
            config_params={"api_key": "TAVILY_API_KEY"},
        ),
        # Code execution
        "PythonTools": ToolCatalogEntry(
            name="PythonTools",
            class_path="agno.tools.python",
            description="Execute Python code in sandboxed environment",
            use_cases=["code", "calculation", "data_analysis", "compute"],
            keywords=["python", "execute", "run", "script"],
            required_for=["code_execution", "data_analysis", "calculations"],
            conflicts_with=[],
        ),
        "ShellTools": ToolCatalogEntry(
            name="ShellTools",
            class_path="agno.tools.shell",
            description="Execute shell commands (use cautiously)",
            use_cases=["shell", "command", "system", "devops"],
            keywords=["bash", "terminal", "cli", "system"],
            required_for=["system_automation", "devops"],
            conflicts_with=[],
            config_params={"restricted_commands": ["rm -rf", "mkfs"]},
        ),
        # File operations
        "FileTools": ToolCatalogEntry(
            name="FileTools",
            class_path="agno.tools.file",
            description="Read and write files",
            use_cases=["file", "read", "write", "storage"],
            keywords=["document", "text", "save", "load"],
            required_for=["file_processing", "document_handling"],
            conflicts_with=[],
        ),
        "CSVTools": ToolCatalogEntry(
            name="CSVTools",
            class_path="agno.tools.csv",
            description="CSV file operations and analysis",
            use_cases=["csv", "data", "spreadsheet", "table"],
            keywords=["excel", "tabular", "rows", "columns"],
            required_for=["csv_analysis", "data_processing"],
            conflicts_with=[],
        ),
        # Web scraping and APIs
        "WebpageTools": ToolCatalogEntry(
            name="WebpageTools",
            class_path="agno.tools.webpage",
            description="Fetch and parse web pages",
            use_cases=["scrape", "webpage", "html", "fetch"],
            keywords=["website", "page", "content", "extract"],
            required_for=["web_scraping", "content_extraction"],
            conflicts_with=[],
        ),
        "YouTubeTools": ToolCatalogEntry(
            name="YouTubeTools",
            class_path="agno.tools.youtube",
            description="YouTube video information and transcripts",
            use_cases=["youtube", "video", "transcript", "media"],
            keywords=["yt", "captions", "subtitles"],
            required_for=["youtube_analysis"],
            conflicts_with=[],
        ),
        # Data and calculation
        "PandasTools": ToolCatalogEntry(
            name="PandasTools",
            class_path="agno.tools.pandas",
            description="Data manipulation with pandas",
            use_cases=["data", "analysis", "dataframe", "statistics"],
            keywords=["pandas", "df", "manipulation", "transform"],
            required_for=["data_analysis", "statistics"],
            conflicts_with=[],
        ),
        "CalculatorTools": ToolCatalogEntry(
            name="CalculatorTools",
            class_path="agno.tools.calculator",
            description="Basic mathematical calculations",
            use_cases=["math", "calculate", "arithmetic", "numbers"],
            keywords=["calculator", "compute", "formula"],
            required_for=["calculations"],
            conflicts_with=["PythonTools"],  # Python can do calculations too
        ),
        # Database
        "PostgresTools": ToolCatalogEntry(
            name="PostgresTools",
            class_path="agno.tools.postgres",
            description="PostgreSQL database operations",
            use_cases=["database", "sql", "postgres", "query"],
            keywords=["db", "postgresql", "data"],
            required_for=["database_operations"],
            conflicts_with=[],
            config_params={"connection_string": "DATABASE_URL"},
        ),
        # Email and communication
        "EmailTools": ToolCatalogEntry(
            name="EmailTools",
            class_path="agno.tools.email",
            description="Send emails",
            use_cases=["email", "send", "notification", "message"],
            keywords=["mail", "smtp", "notify"],
            required_for=["email_sending"],
            conflicts_with=[],
            config_params={"smtp_config": "required"},
        ),
        # API integrations
        "SlackTools": ToolCatalogEntry(
            name="SlackTools",
            class_path="agno.tools.slack",
            description="Slack workspace integration",
            use_cases=["slack", "message", "channel", "workspace"],
            keywords=["chat", "team", "notification"],
            required_for=["slack_integration"],
            conflicts_with=[],
            config_params={"bot_token": "SLACK_BOT_TOKEN"},
        ),
        "GitHubTools": ToolCatalogEntry(
            name="GitHubTools",
            class_path="agno.tools.github",
            description="GitHub repository operations",
            use_cases=["github", "git", "repository", "code"],
            keywords=["repo", "commit", "pr", "issue"],
            required_for=["github_integration"],
            conflicts_with=[],
            config_params={"access_token": "GITHUB_TOKEN"},
        ),
        "JiraTools": ToolCatalogEntry(
            name="JiraTools",
            class_path="agno.tools.jira",
            description="Jira issue tracking integration",
            use_cases=["jira", "issue", "ticket", "tracking"],
            keywords=["project", "task", "bug"],
            required_for=["jira_integration"],
            conflicts_with=[],
            config_params={"api_token": "JIRA_API_TOKEN"},
        ),
    }

    def recommend(
        self, description: str, include_optional: bool = True, max_tools: int = 5
    ) -> list[ToolRecommendation]:
        """Recommend tools based on use case description.

        Args:
            description: Natural language description of agent requirements
            include_optional: Include optional (nice-to-have) tools
            max_tools: Maximum number of tools to recommend

        Returns:
            List of ToolRecommendation sorted by relevance
        """
        description_lower = description.lower()

        # Score all tools
        scored_tools = []
        for tool_name, catalog_entry in self.BUILTIN_TOOLS.items():
            score, required = self._score_tool(catalog_entry, description_lower)
            if score > 0:
                scored_tools.append((score, required, tool_name, catalog_entry))

        # Sort by score (required first, then by score)
        scored_tools.sort(reverse=True, key=lambda x: (x[1], x[0]))

        # Build recommendations
        recommendations = []
        required_count = 0

        for score, required, tool_name, catalog_entry in scored_tools:
            # Stop if we hit max tools (but always include required)
            if not required and len(recommendations) >= max_tools:
                break

            # Skip optional if requested
            if not include_optional and not required:
                continue

            # Check for conflicts with already selected tools
            conflicts = any(rec.tool_name in catalog_entry.conflicts_with for rec in recommendations)
            if conflicts:
                continue

            reasoning = self._build_tool_reasoning(catalog_entry, description_lower, required, score)

            recommendations.append(
                ToolRecommendation(
                    tool_name=tool_name,
                    tool_class=catalog_entry.class_path,
                    reasoning=reasoning,
                    required=required,
                    config_hints=catalog_entry.config_params,
                )
            )

            if required:
                required_count += 1

        return recommendations

    def _score_tool(self, catalog_entry: ToolCatalogEntry, description: str) -> tuple[float, bool]:
        """Score a tool based on description match (0-100).

        Returns:
            (score, is_required) tuple
        """
        score = 0.0
        required = False

        # Check if required for any matching use cases
        for req_case in catalog_entry.required_for:
            if req_case.replace("_", " ") in description:
                required = True
                score += 50  # Base score for required tools

        # Match use cases (30 points)
        for use_case in catalog_entry.use_cases:
            if use_case in description:
                score += 10

        # Match keywords (20 points)
        for keyword in catalog_entry.keywords:
            if keyword in description:
                score += 5

        return score, required

    def _build_tool_reasoning(
        self, catalog_entry: ToolCatalogEntry, description: str, required: bool, score: float
    ) -> str:
        """Build human-readable reasoning for tool recommendation."""
        if required:
            reasons = [f"REQUIRED: {catalog_entry.description}"]
            matched_cases = [case for case in catalog_entry.required_for if case.replace("_", " ") in description]
            if matched_cases:
                reasons.append(f"Essential for: {', '.join(matched_cases)}")
        else:
            reasons = [f"OPTIONAL: {catalog_entry.description}"]
            matched = [uc for uc in catalog_entry.use_cases if uc in description]
            if matched:
                reasons.append(f"Useful for: {', '.join(matched)}")

        if catalog_entry.config_params:
            param_list = ", ".join(catalog_entry.config_params.keys())
            reasons.append(f"Configuration needed: {param_list}")

        return "\n".join(reasons)

    def get_tool_info(self, tool_name: str) -> Optional[ToolCatalogEntry]:
        """Get detailed information about a specific tool."""
        return self.BUILTIN_TOOLS.get(tool_name)

    def list_tools_by_category(self) -> dict[str, list[str]]:
        """List tools organized by category."""
        categories = {
            "Web & Search": ["DuckDuckGoTools", "TavilyTools", "WebpageTools", "YouTubeTools"],
            "Code Execution": ["PythonTools", "ShellTools"],
            "File Operations": ["FileTools", "CSVTools"],
            "Data & Analysis": ["PandasTools", "CalculatorTools"],
            "Database": ["PostgresTools"],
            "Communication": ["EmailTools", "SlackTools"],
            "Integrations": ["GitHubTools", "JiraTools"],
        }
        return categories

    def recommend_minimal(self, description: str) -> list[ToolRecommendation]:
        """Recommend only essential tools (minimalist approach).

        Returns only required tools, no optional suggestions.
        """
        return self.recommend(description, include_optional=False, max_tools=3)

    def validate_tool_combination(self, tool_names: list[str]) -> tuple[bool, list[str]]:
        """Check if a combination of tools is valid (no conflicts).

        Args:
            tool_names: List of tool names to validate

        Returns:
            (is_valid, list_of_conflicts) tuple
        """
        conflicts = []
        for i, tool_a in enumerate(tool_names):
            entry_a = self.BUILTIN_TOOLS.get(tool_a)
            if not entry_a:
                continue

            for tool_b in tool_names[i + 1 :]:
                if tool_b in entry_a.conflicts_with:
                    conflicts.append(f"{tool_a} conflicts with {tool_b}")

        return len(conflicts) == 0, conflicts
