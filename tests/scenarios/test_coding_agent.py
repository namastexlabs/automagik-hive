#!/usr/bin/env python3
"""
Simple Agent Test Example

This matches the user's pseudocode request for testing agents directly.
"""

import os
import sys
import asyncio
import pytest
import scenario
from agno.agent.agent import Agent
from lib.utils.version_factory import create_agent

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  dotenv not available, using system environment")

scenario.configure(default_model="anthropic/claude-sonnet-4-20250514")


class AgnoAgent(scenario.AgentAdapter):
    def __init__(self, agent: Agent):
        self.agent = agent

    async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
        result = self.agent.run(
            input.last_new_user_message_str(), session_id=input.thread_id
        )
        return str(result.content)


@pytest.mark.asyncio
async def test_coding_agent_can_do_hello_worlds():
    result = await scenario.run(
        name="hello world",
        description="""
            The user is a developer and wants to write a hello world program in 3 different programming languages.
        """,
        agents=[
            AgnoAgent(await create_agent("code-editing-agent")),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                criteria=[
                    "Agent should be succint and generate just the hello world code not a whole application",
                    "Hello world should contain code comments",
                ]
            ),
        ],
        script=[
            scenario.user("how do to a hello world in python?"),
            scenario.agent(),
            scenario.user("how do to a hello world in typescript?"),
            scenario.agent(),
            scenario.user(),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success
