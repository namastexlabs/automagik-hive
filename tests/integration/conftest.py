"""
Integration test fixtures for real API testing.

No mocks - real execution only.
"""

import asyncio
import os
import time

import pytest
import yaml
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat


@pytest.fixture(scope="session")
def verify_api_keys():
    """Verify required API keys are present."""
    missing_keys = []

    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing_keys.append("ANTHROPIC_API_KEY")

    if missing_keys:
        pytest.skip(f"Missing required API keys: {', '.join(missing_keys)}")

    return True


@pytest.fixture
def openai_model():
    """Get OpenAI model instance."""
    return OpenAIChat(id="gpt-4o-mini")


@pytest.fixture
def anthropic_model():
    """Get Anthropic model instance."""
    return Claude(id="claude-3-5-haiku-20241022")


@pytest.fixture
def retry_config() -> dict[str, int | float]:
    """Configuration for retry logic."""
    return {"max_attempts": 3, "initial_delay": 1.0, "max_delay": 10.0, "backoff_factor": 2.0}


@pytest.fixture
async def async_retry_executor(retry_config):
    """Execute async function with exponential backoff."""

    async def execute(func, *args, **kwargs):
        delay = retry_config["initial_delay"]

        for attempt in range(retry_config["max_attempts"]):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == retry_config["max_attempts"] - 1:
                    raise

                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * retry_config["backoff_factor"], retry_config["max_delay"])

    return execute


@pytest.fixture
def measure_response_time():
    """Measure and validate response times."""
    times: list[float] = []

    class ResponseTimer:
        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, *args):
            duration = time.time() - self.start
            times.append(duration)
            self.duration = duration

        @property
        def average(self):
            return sum(times) / len(times) if times else 0

        @property
        def all_times(self):
            return times.copy()

    return ResponseTimer


@pytest.fixture
def test_agent_configs():
    """Standard test agent configurations."""
    return {
        "openai_simple": {
            "agent": {"name": "OpenAI Test Agent", "agent_id": "openai-test", "version": 1},
            "model": {"provider": "openai", "id": "gpt-4o-mini", "temperature": 0.7},
            "instructions": "You are a helpful assistant. Answer questions clearly and concisely.",
        },
        "anthropic_simple": {
            "agent": {"name": "Anthropic Test Agent", "agent_id": "anthropic-test", "version": 1},
            "model": {"provider": "anthropic", "id": "claude-3-5-haiku-20241022", "temperature": 0.7},
            "instructions": "You are a helpful assistant. Answer questions clearly and concisely.",
        },
        "math_specialist": {
            "agent": {"name": "Math Specialist", "agent_id": "math-specialist", "version": 1},
            "model": {"provider": "openai", "id": "gpt-4o-mini", "temperature": 0.0},
            "instructions": """You are a math specialist.
Solve mathematical problems step by step.
Show your work clearly.
Provide the final answer in this format: ANSWER: [number]""",
        },
        "creative_writer": {
            "agent": {"name": "Creative Writer", "agent_id": "creative-writer", "version": 1},
            "model": {"provider": "anthropic", "id": "claude-3-5-haiku-20241022", "temperature": 0.9},
            "instructions": """You are a creative writing assistant.
Generate engaging, original content.
Be creative but stay on topic.""",
        },
    }


@pytest.fixture
def test_queries():
    """Standard test queries with expected behaviors."""
    return {
        "simple_greeting": {
            "query": "Hello! How are you?",
            "min_length": 10,
            "should_contain": ["hello", "hi", "greet"],
            "timeout": 10.0,
        },
        "math_question": {
            "query": "What is 17 * 23? Show your work.",
            "min_length": 20,
            "should_contain": ["391", "answer"],
            "timeout": 15.0,
        },
        "factual_question": {
            "query": "What is the capital of France?",
            "min_length": 5,
            "should_contain": ["Paris"],
            "timeout": 10.0,
        },
        "creative_prompt": {
            "query": "Write a two-sentence story about a robot.",
            "min_length": 30,
            "should_contain": ["robot"],
            "timeout": 20.0,
        },
        "multi_step": {
            "query": "List three primary colors and explain why they're called primary.",
            "min_length": 50,
            "should_contain": ["red", "blue", "yellow", "primary"],
            "timeout": 20.0,
        },
    }


@pytest.fixture
def quality_validator():
    """Validate response quality."""

    class QualityValidator:
        @staticmethod
        def validate_response(response: str, criteria: dict) -> dict[str, bool]:
            """Validate response against criteria."""
            results = {
                "has_content": bool(response and response.strip()),
                "min_length": len(response) >= criteria.get("min_length", 0),
                "contains_keywords": False,
                "not_error": "error" not in response.lower() or "exception" not in response.lower(),
            }

            # Check if any required keywords present
            keywords = criteria.get("should_contain", [])
            if keywords:
                results["contains_keywords"] = any(kw.lower() in response.lower() for kw in keywords)
            else:
                results["contains_keywords"] = True

            return results

        @staticmethod
        def calculate_quality_score(results: dict[str, bool]) -> float:
            """Calculate quality score (0.0 - 1.0)."""
            return sum(results.values()) / len(results)

    return QualityValidator()


@pytest.fixture
def create_test_agent(tmp_path):
    """Factory to create test agents from configs."""

    def _create_agent(config: dict, model_override=None) -> Agent:
        """Create agent from config dict."""
        from agno.models.anthropic import Claude
        from agno.models.openai import OpenAIChat

        # Resolve model
        if model_override:
            model = model_override
        else:
            model_config = config.get("model", {})
            provider = model_config.get("provider", "openai")
            model_id = model_config.get("id", "gpt-4o-mini")
            temperature = model_config.get("temperature", 0.7)

            if provider == "openai":
                model = OpenAIChat(id=model_id, temperature=temperature)
            elif provider == "anthropic":
                model = Claude(id=model_id, temperature=temperature)
            else:
                raise ValueError(f"Unknown provider: {provider}")

        # Create agent
        agent_config = config.get("agent", {})
        agent = Agent(
            name=agent_config.get("name", "Test Agent"),
            model=model,
            instructions=config.get("instructions", "You are a helpful assistant."),
            markdown=True,
        )

        # Set agent_id if provided
        if "agent_id" in agent_config:
            agent.id = agent_config["agent_id"]  # type: ignore[attr-defined]

        return agent

    return _create_agent


@pytest.fixture
def test_results_logger(tmp_path):
    """Log test results for analysis."""
    results_file = tmp_path / "integration_test_results.yaml"
    results = {"test_runs": [], "summary": {"total_tests": 0, "passed": 0, "failed": 0, "avg_response_time": 0.0}}

    class ResultsLogger:
        def log_test(self, test_name: str, success: bool, duration: float, details: dict | None = None):
            results["test_runs"].append(
                {"test": test_name, "success": success, "duration": duration, "details": details or {}}
            )
            results["summary"]["total_tests"] += 1
            if success:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1

        def save(self):
            # Calculate average response time
            times = [r["duration"] for r in results["test_runs"]]
            if times:
                results["summary"]["avg_response_time"] = sum(times) / len(times)

            with open(results_file, "w") as f:
                yaml.dump(results, f, default_flow_style=False)

            return results_file

    yield ResultsLogger()
