"""
Workspace Protocol Validation Test Suite

This package provides comprehensive testing utilities and test cases
for validating that all Genie Hive agents properly implement the
standardized workspace interaction protocol.

Test Categories:
- Context File Ingestion: Validate @filepath pattern handling
- Artifact Lifecycle: Test /genie/ideas/ → /genie/wishes/ → DELETE progression
- JSON Response Format: Ensure structured response compliance
- Technical Standards: Validate enforcement of development standards
- Cross-Agent Coordination: Test protocol consistency across agents

Usage:
    # Run all workspace protocol tests
    uv run pytest tests/workspace_protocol/ -v

    # Run specific test category
    uv run pytest tests/workspace_protocol/test_context_ingestion.py -v

    # Run comprehensive validation script
    uv run python tests/workspace_protocol/test_execution_script.py

Components:
- test_context_ingestion.py: Context file processing validation
- test_artifact_lifecycle.py: Artifact lifecycle management validation
- utils/agent_tester.py: Agent testing utilities
- utils/protocol_validator.py: Protocol compliance validation
- test_execution_script.py: Comprehensive validation orchestrator
"""

__version__ = "1.0.0"
__author__ = "GENIE TESTING MAKER"

# Import main testing utilities for easy access
from .utils.agent_tester import AgentTester
from .utils.protocol_validator import ProtocolValidator

__all__ = ["AgentTester", "ProtocolValidator"]
