"""Tests for ToolRecommender component."""

import sys
from pathlib import Path

import pytest

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.generators.tool_recommender import ToolRecommender


class TestToolRecommender:
    """Test suite for ToolRecommender."""

    @pytest.fixture
    def recommender(self) -> ToolRecommender:
        """Create ToolRecommender instance."""
        return ToolRecommender()

    def test_recommender_initialization(self, recommender: ToolRecommender) -> None:
        """Test ToolRecommender initializes correctly."""
        assert recommender is not None
        assert len(recommender.BUILTIN_TOOLS) > 0

    def test_web_search_recommendation(self, recommender: ToolRecommender) -> None:
        """Test recommendation for web search use case."""
        recommendations = recommender.recommend("I need an agent that searches the web")

        assert len(recommendations) > 0
        tool_names = [rec.tool_name for rec in recommendations]
        assert "DuckDuckGoTools" in tool_names or "TavilyTools" in tool_names

    def test_code_execution_recommendation(self, recommender: ToolRecommender) -> None:
        """Test recommendation for code execution use case."""
        recommendations = recommender.recommend("I need an agent that executes Python code")

        assert len(recommendations) > 0
        tool_names = [rec.tool_name for rec in recommendations]
        assert "PythonTools" in tool_names

    def test_file_operations_recommendation(self, recommender: ToolRecommender) -> None:
        """Test recommendation for file operations."""
        recommendations = recommender.recommend("I need an agent that reads and writes files")

        assert len(recommendations) > 0
        tool_names = [rec.tool_name for rec in recommendations]
        assert "FileTools" in tool_names

    def test_data_analysis_recommendation(self, recommender: ToolRecommender) -> None:
        """Test recommendation for data analysis use case."""
        recommendations = recommender.recommend("I need an agent that analyzes CSV data")

        assert len(recommendations) > 0
        tool_names = [rec.tool_name for rec in recommendations]
        assert "CSVTools" in tool_names or "PandasTools" in tool_names

    def test_required_vs_optional_tools(self, recommender: ToolRecommender) -> None:
        """Test distinction between required and optional tools."""
        recommendations = recommender.recommend("I need web search capabilities")

        required_tools = [rec for rec in recommendations if rec.required]
        optional_tools = [rec for rec in recommendations if not rec.required]

        # Should have at least one required tool for web search
        assert len(required_tools) > 0

    def test_minimal_recommendations(self, recommender: ToolRecommender) -> None:
        """Test minimal recommendation mode (required only)."""
        all_recs = recommender.recommend("I need web search and file operations")
        minimal_recs = recommender.recommend_minimal("I need web search and file operations")

        assert len(minimal_recs) <= len(all_recs)
        assert all(rec.required for rec in minimal_recs)

    def test_max_tools_limit(self, recommender: ToolRecommender) -> None:
        """Test max tools limit is respected."""
        recommendations = recommender.recommend(
            "I need web search, code execution, file operations, data analysis, and database access",
            max_tools=3,
        )

        # Should respect max_tools (plus any required tools)
        assert len(recommendations) <= 5  # Some buffer for required tools

    def test_conflict_detection(self, recommender: ToolRecommender) -> None:
        """Test conflicting tools are not recommended together."""
        recommendations = recommender.recommend("I need web search capabilities")

        tool_names = [rec.tool_name for rec in recommendations]

        # DuckDuckGo and Tavily should not both be recommended (they conflict)
        has_ddg = "DuckDuckGoTools" in tool_names
        has_tavily = "TavilyTools" in tool_names
        assert not (has_ddg and has_tavily), "Conflicting tools recommended together"

    def test_validate_tool_combination(self, recommender: ToolRecommender) -> None:
        """Test tool combination validation."""
        # Valid combination
        is_valid, conflicts = recommender.validate_tool_combination(["PythonTools", "FileTools", "CSVTools"])
        assert is_valid
        assert len(conflicts) == 0

        # Invalid combination (conflicting tools)
        is_valid, conflicts = recommender.validate_tool_combination(["DuckDuckGoTools", "TavilyTools"])
        assert not is_valid
        assert len(conflicts) > 0

    def test_tool_info_retrieval(self, recommender: ToolRecommender) -> None:
        """Test retrieving tool information."""
        info = recommender.get_tool_info("PythonTools")

        assert info is not None
        assert info.name == "PythonTools"
        assert "code" in info.use_cases
        assert len(info.description) > 0

    def test_list_tools_by_category(self, recommender: ToolRecommender) -> None:
        """Test listing tools by category."""
        categories = recommender.list_tools_by_category()

        assert "Web & Search" in categories
        assert "Code Execution" in categories
        assert len(categories) > 0

    def test_reasoning_generation(self, recommender: ToolRecommender) -> None:
        """Test reasoning text is generated for recommendations."""
        recommendations = recommender.recommend("I need web search")

        for rec in recommendations:
            assert len(rec.reasoning) > 0
            assert "REQUIRED" in rec.reasoning or "OPTIONAL" in rec.reasoning

    def test_config_hints_for_api_tools(self, recommender: ToolRecommender) -> None:
        """Test config hints are provided for tools requiring API keys."""
        recommendations = recommender.recommend("I need Slack integration")

        slack_recs = [rec for rec in recommendations if rec.tool_name == "SlackTools"]
        if slack_recs:
            assert slack_recs[0].config_hints is not None
            assert "bot_token" in slack_recs[0].config_hints

    def test_github_integration_recommendation(self, recommender: ToolRecommender) -> None:
        """Test GitHub integration recommendation."""
        recommendations = recommender.recommend("I need to interact with GitHub repositories")

        tool_names = [rec.tool_name for rec in recommendations]
        assert "GitHubTools" in tool_names

    def test_database_recommendation(self, recommender: ToolRecommender) -> None:
        """Test database tool recommendation."""
        recommendations = recommender.recommend("I need to query a PostgreSQL database")

        tool_names = [rec.tool_name for rec in recommendations]
        assert "PostgresTools" in tool_names

    def test_email_recommendation(self, recommender: ToolRecommender) -> None:
        """Test email tool recommendation."""
        recommendations = recommender.recommend("I need to send email notifications")

        tool_names = [rec.tool_name for rec in recommendations]
        assert "EmailTools" in tool_names

    def test_youtube_recommendation(self, recommender: ToolRecommender) -> None:
        """Test YouTube tool recommendation."""
        recommendations = recommender.recommend("I need to extract YouTube video transcripts")

        tool_names = [rec.tool_name for rec in recommendations]
        assert "YouTubeTools" in tool_names

    def test_empty_description(self, recommender: ToolRecommender) -> None:
        """Test handling of empty description."""
        recommendations = recommender.recommend("")

        # Should return some recommendations even with empty description
        assert isinstance(recommendations, list)

    def test_complex_multi_tool_scenario(self, recommender: ToolRecommender) -> None:
        """Test complex scenario requiring multiple tools."""
        recommendations = recommender.recommend(
            "I need an agent that searches the web, processes CSV files, "
            "executes Python code for analysis, and sends email reports"
        )

        tool_names = [rec.tool_name for rec in recommendations]

        # Should recommend multiple appropriate tools (at least 2)
        assert len(tool_names) >= 2
        # Check that relevant tool categories are covered
        has_relevant_tools = any(
            any(keyword in name.lower() for keyword in ["duckduckgo", "tavily", "csv", "python", "email"])
            for name in tool_names
        )
        assert has_relevant_tools
        assert any("csv" in name.lower() or "file" in name.lower() for name in tool_names)

    def test_include_optional_flag(self, recommender: ToolRecommender) -> None:
        """Test include_optional flag behavior."""
        with_optional = recommender.recommend("web search", include_optional=True)
        without_optional = recommender.recommend("web search", include_optional=False)

        assert len(with_optional) >= len(without_optional)

    def test_all_builtin_tools_have_metadata(self, recommender: ToolRecommender) -> None:
        """Test all builtin tools have complete metadata."""
        for tool_name, catalog_entry in recommender.BUILTIN_TOOLS.items():
            assert catalog_entry.name == tool_name
            assert len(catalog_entry.class_path) > 0
            assert len(catalog_entry.description) > 0
            assert len(catalog_entry.use_cases) > 0
            assert isinstance(catalog_entry.conflicts_with, list)
