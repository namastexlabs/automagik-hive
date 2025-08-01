"""
Comprehensive test suite for lib/logging/batch_logger.py

This module provides exhaustive test coverage for batch logging operations,
log aggregation, performance logging, and batch processing functionality.
Targets 61 uncovered lines for a 0.9% coverage boost.
"""

import os
import time
from io import StringIO
from unittest.mock import patch

import pytest

from lib.logging.batch_logger import (
    BatchLogger,
    log_agent_created,
    log_agent_inheritance,
    log_csv_processing,
    log_model_resolved,
    log_storage_created,
    log_team_member_loaded,
    set_runtime_mode,
    startup_logging,
)


class TestBatchLoggerCore:
    """Test core BatchLogger functionality with comprehensive coverage."""

    @pytest.fixture
    def clean_logger(self):
        """Create a fresh BatchLogger instance for testing."""
        logger_instance = BatchLogger()
        yield logger_instance
        # Clean up after test
        logger_instance.batches.clear()
        logger_instance.seen_messages.clear()

    @pytest.fixture
    def mock_environment_verbose(self):
        """Mock environment for verbose logging tests."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "true", "HIVE_LOG_LEVEL": "INFO"}
        ):
            yield

    @pytest.fixture
    def mock_environment_debug(self):
        """Mock environment for debug logging tests."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "DEBUG"}
        ):
            yield

    @pytest.fixture
    def mock_environment_quiet(self):
        """Mock environment for quiet logging tests."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            yield

    def test_verbose_logging_environment_detection(
        self, clean_logger, mock_environment_verbose
    ):
        """Test verbose logging detection via environment variables."""
        logger_instance = BatchLogger()
        assert logger_instance._should_log_verbose() is True
        assert logger_instance.verbose is True

    def test_debug_logging_environment_detection(
        self, clean_logger, mock_environment_debug
    ):
        """Test debug logging detection via environment variables."""
        logger_instance = BatchLogger()
        assert logger_instance._should_log_verbose() is True
        assert logger_instance.log_level == "DEBUG"

    def test_quiet_logging_environment_detection(
        self, clean_logger, mock_environment_quiet
    ):
        """Test normal logging mode via environment variables."""
        logger_instance = BatchLogger()
        assert logger_instance._should_log_verbose() is False
        assert logger_instance.verbose is False
        assert logger_instance.log_level == "INFO"


class TestBatchLoggerVerboseMode:
    """Test BatchLogger behavior in verbose mode to cover verbose logging paths."""

    @pytest.fixture
    def verbose_logger(self):
        """Create logger in verbose mode."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "true", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()
            yield logger_instance

    @patch("lib.logging.batch_logger.logger")
    def test_log_agent_inheritance_verbose(self, mock_logger, verbose_logger):
        """Test agent inheritance logging in verbose mode (lines 38-39)."""
        verbose_logger.log_agent_inheritance("test_agent_verbose")

        # In verbose mode, should log immediately with debug level
        mock_logger.debug.assert_called_once_with(
            "Applied inheritance to agent test_agent_verbose"
        )

        # Should not batch in verbose mode
        assert "agent_inheritance" not in verbose_logger.batches

    @patch("lib.logging.batch_logger.logger")
    def test_log_model_resolved_verbose(self, mock_logger, verbose_logger):
        """Test model resolution logging in verbose mode (lines 49-52)."""
        verbose_logger.log_model_resolved("test_model", "test_provider")

        # In verbose mode, should log immediately with info level
        mock_logger.info.assert_called_once_with(
            "Model resolved successfully",
            model_id="test_model",
            provider="test_provider",
        )

        # Should not batch in verbose mode
        assert "model_resolved" not in verbose_logger.batches

    @patch("lib.logging.batch_logger.logger")
    def test_log_storage_created_verbose(self, mock_logger, verbose_logger):
        """Test storage creation logging in verbose mode (lines 62-65)."""
        verbose_logger.log_storage_created("vector", "test_component")

        # In verbose mode, should log immediately with info level
        mock_logger.info.assert_called_once_with(
            "Successfully created vector storage for test_component"
        )

        # Should not batch in verbose mode
        assert "storage_created" not in verbose_logger.batches

    @patch("lib.logging.batch_logger.logger")
    def test_log_agent_created_verbose(self, mock_logger, verbose_logger):
        """Test agent creation logging in verbose mode (lines 74-78)."""
        verbose_logger.log_agent_created("test_agent", 42)

        # In verbose mode, should log immediately with info level
        mock_logger.info.assert_called_once_with(
            "🤖 Agent test_agent created with inheritance and 42 available parameters"
        )

        # Should not batch in verbose mode
        assert "agent_created" not in verbose_logger.batches

    @patch("lib.logging.batch_logger.logger")
    def test_log_team_member_loaded_verbose(self, mock_logger, verbose_logger):
        """Test team member loading in verbose mode (lines 87-89)."""
        verbose_logger.log_team_member_loaded("test_member")

        # In verbose mode, should log immediately with info level
        mock_logger.info.assert_called_once_with("🤖 Loaded team member: test_member")

        # Should not batch in verbose mode
        assert "team_members" not in verbose_logger.batches

    @patch("lib.logging.batch_logger.logger")
    def test_log_csv_processing_verbose(self, mock_logger, verbose_logger):
        """Test CSV processing logging in verbose mode (lines 99-101)."""
        verbose_logger.log_csv_processing("test_source.csv", 100)

        # In verbose mode, should log immediately with info level
        mock_logger.info.assert_called_once_with(
            "test_source.csv: 100 documents processed"
        )

        # Should not batch in verbose mode
        assert "csv_processing" not in verbose_logger.batches


class TestBatchLoggerRuntimeMode:
    """Test BatchLogger behavior in runtime mode (non-startup) to cover runtime paths."""

    @pytest.fixture
    def runtime_logger(self):
        """Create logger in runtime mode."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()
            logger_instance.set_runtime_mode()  # Switch to runtime mode
            yield logger_instance

    @patch("lib.logging.batch_logger.logger")
    def test_log_agent_inheritance_runtime(self, mock_logger, runtime_logger):
        """Test agent inheritance logging in runtime mode (line 44)."""
        runtime_logger.log_agent_inheritance("runtime_agent")

        # In runtime mode, should log immediately with debug level
        mock_logger.debug.assert_called_once_with(
            "Applied inheritance to agent runtime_agent"
        )

    @patch("lib.logging.batch_logger.logger")
    def test_log_model_resolved_runtime(self, mock_logger, runtime_logger):
        """Test model resolution logging in runtime mode (line 57)."""
        runtime_logger.log_model_resolved("runtime_model", "runtime_provider")

        # In runtime mode, should log immediately with debug level
        mock_logger.debug.assert_called_once_with("🔧 Model resolved: runtime_model")

    @patch("lib.logging.batch_logger.logger")
    def test_log_storage_created_runtime(self, mock_logger, runtime_logger):
        """Test storage creation logging in runtime mode (line 70)."""
        runtime_logger.log_storage_created("memory", "runtime_component")

        # In runtime mode, should log immediately with debug level
        mock_logger.debug.assert_called_once_with(
            "🔧 Storage created: runtime_component"
        )

    @patch("lib.logging.batch_logger.logger")
    def test_log_agent_created_runtime(self, mock_logger, runtime_logger):
        """Test agent creation logging in runtime mode (line 83)."""
        runtime_logger.log_agent_created("runtime_agent", 24)

        # In runtime mode, should log immediately with info level
        mock_logger.info.assert_called_once_with("🤖 Agent runtime_agent ready")

    @patch("lib.logging.batch_logger.logger")
    def test_log_team_member_loaded_runtime(self, mock_logger, runtime_logger):
        """Test team member loading in runtime mode (line 95)."""
        runtime_logger.log_team_member_loaded("runtime_member")

        # In runtime mode, should log immediately with debug level
        mock_logger.debug.assert_called_once_with("🤖 Member loaded: runtime_member")

    @patch("lib.logging.batch_logger.logger")
    def test_log_csv_processing_runtime(self, mock_logger, runtime_logger):
        """Test CSV processing logging in runtime mode (line 106)."""
        runtime_logger.log_csv_processing("runtime_source.csv", 50)

        # In runtime mode, should log immediately with debug level
        mock_logger.debug.assert_called_once_with("runtime_source.csv: 50 docs")


class TestBatchLoggerAdvancedOperations:
    """Test advanced BatchLogger operations for comprehensive coverage."""

    @pytest.fixture
    def startup_logger(self):
        """Create logger in startup mode for batching tests."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()
            # Ensure we're in startup mode
            logger_instance.startup_mode = True
            yield logger_instance

    @patch("lib.logging.batch_logger.logger")
    def test_log_once_functionality(self, mock_logger, startup_logger):
        """Test log_once deduplication functionality (lines 110-113)."""
        # First call should log
        startup_logger.log_once("Test message", level="info")
        mock_logger.info.assert_called_once_with("Test message")

        # Reset mock for second call
        mock_logger.reset_mock()

        # Second call with same message should not log
        startup_logger.log_once("Test message", level="info")
        mock_logger.info.assert_not_called()

        # Different message should log
        startup_logger.log_once("Different message", level="warning")
        mock_logger.warning.assert_called_once_with("Different message")

    @patch("lib.logging.batch_logger.logger")
    def test_log_once_with_kwargs(self, mock_logger, startup_logger):
        """Test log_once with keyword arguments."""
        startup_logger.log_once(
            "Message with kwargs", level="error", component="test", count=42
        )
        mock_logger.error.assert_called_once_with(
            "Message with kwargs", component="test", count=42
        )

        # Reset and try same message with different kwargs - should log again
        mock_logger.reset_mock()
        startup_logger.log_once(
            "Message with kwargs", level="error", component="different", count=24
        )
        mock_logger.error.assert_called_once_with(
            "Message with kwargs", component="different", count=24
        )

    @patch("lib.logging.batch_logger.logger")
    def test_log_team_member_loaded_with_team_id(self, mock_logger, startup_logger):
        """Test team member loading with specific team ID (lines 92-93)."""
        startup_logger.log_team_member_loaded("team_member_1", "team_alpha")
        startup_logger.log_team_member_loaded("team_member_2", "team_alpha")
        startup_logger.log_team_member_loaded("team_member_3", "team_beta")

        # Check batching with team-specific keys
        assert "team_members_team_alpha" in startup_logger.batches
        assert "team_members_team_beta" in startup_logger.batches
        assert len(startup_logger.batches["team_members_team_alpha"]) == 2
        assert len(startup_logger.batches["team_members_team_beta"]) == 1


class TestBatchLoggerFlushOperations:
    """Test comprehensive batch flushing operations to cover flush logic."""

    @pytest.fixture
    def populated_logger(self):
        """Create logger with populated batches for flush testing."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()
            logger_instance.startup_mode = True

            # Populate with diverse data
            logger_instance.log_agent_inheritance("agent1")
            logger_instance.log_agent_inheritance("agent2")

            logger_instance.log_model_resolved("model1", "provider_a")
            logger_instance.log_model_resolved("model2", "provider_b")
            logger_instance.log_model_resolved("model3", "provider_a")

            logger_instance.log_storage_created("vector", "comp1")
            logger_instance.log_storage_created("memory", "comp2")
            logger_instance.log_storage_created("vector", "comp3")

            logger_instance.log_agent_created("agent_alpha", 10)
            logger_instance.log_agent_created("agent_beta", 20)
            logger_instance.log_agent_created("agent_gamma", 30)

            logger_instance.log_team_member_loaded("member1")
            logger_instance.log_team_member_loaded("member2")
            logger_instance.log_team_member_loaded("member3", "team_x")
            logger_instance.log_team_member_loaded("member4", "team_x")
            logger_instance.log_team_member_loaded("member5", "team_y")

            logger_instance.log_csv_processing("source1.csv", 100)
            logger_instance.log_csv_processing("source2.csv", 200)
            logger_instance.log_csv_processing("source3.csv", 150)

            yield logger_instance

    @patch("lib.logging.batch_logger.logger")
    def test_flush_storage_created_summary(self, mock_logger, populated_logger):
        """Test storage creation summary flushing (lines 137-139)."""
        populated_logger._flush_startup_batches()

        # Verify storage summary was logged
        storage_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Storage initialization:" in str(call)
        ]
        assert len(storage_calls) == 1

        # Should contain Counter dict with storage types
        storage_call = storage_calls[0]
        assert "{'vector': 2, 'memory': 1}" in str(storage_call)

    @patch("lib.logging.batch_logger.logger")
    def test_flush_agent_created_summary(self, mock_logger, populated_logger):
        """Test agent creation summary flushing (lines 143-149)."""
        populated_logger._flush_startup_batches()

        # Verify agent creation summary was logged
        agent_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Created 3 agents:" in str(call)
        ]
        assert len(agent_calls) == 1

        # Should contain agent names and average parameters
        agent_call = agent_calls[0]
        call_str = str(agent_call)
        assert "agent_alpha, agent_beta, agent_gamma" in call_str
        assert "avg 20 params" in call_str  # (10+20+30)/3 = 20

    @patch("lib.logging.batch_logger.logger")
    def test_flush_team_members_generic_summary(self, mock_logger, populated_logger):
        """Test generic team members summary flushing (lines 158-160)."""
        populated_logger._flush_startup_batches()

        # Verify generic team members summary was logged
        team_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Loaded 2 team members:" in str(call)
        ]
        assert len(team_calls) == 1

        # Should contain member names
        team_call = team_calls[0]
        call_str = str(team_call)
        assert "member1, member2" in call_str

    @patch("lib.logging.batch_logger.logger")
    def test_flush_team_members_specific_teams_summary(
        self, mock_logger, populated_logger
    ):
        """Test specific team members summary flushing (lines 162-165)."""
        populated_logger._flush_startup_batches()

        # Verify team-specific summaries were logged
        team_x_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Team team_x: 2 members loaded" in str(call)
        ]
        assert len(team_x_calls) == 1

        team_y_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Team team_y: 1 members loaded" in str(call)
        ]
        assert len(team_y_calls) == 1

        # Check member lists in team summaries
        team_x_call = team_x_calls[0]
        team_y_call = team_y_calls[0]
        assert "member3, member4" in str(team_x_call)
        assert "member5" in str(team_y_call)

    @patch("lib.logging.batch_logger.logger")
    def test_flush_csv_processing_summary(self, mock_logger, populated_logger):
        """Test CSV processing summary flushing (lines 169-174)."""
        populated_logger._flush_startup_batches()

        # Verify CSV processing summary was logged
        csv_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Knowledge base:" in str(call)
        ]
        assert len(csv_calls) == 1

        # Should contain source count and total documents
        csv_call = csv_calls[0]
        call_str = str(csv_call)
        assert "3 sources" in call_str  # 3 different CSV sources
        assert "450 documents loaded" in call_str  # 100+200+150 = 450


class TestBatchLoggerContextManager:
    """Test BatchLogger context manager functionality."""

    @patch("lib.logging.batch_logger.logger")
    def test_startup_context_manager(self, mock_logger):
        """Test startup context manager functionality (lines 182-186)."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()

            # Initially in startup mode
            assert logger_instance.startup_mode is True

            # Use context manager
            with logger_instance.startup_context():
                # Should be in startup mode during context
                assert logger_instance.startup_mode is True

                # Add some batch data
                logger_instance.log_agent_inheritance("context_agent")
                assert "agent_inheritance" in logger_instance.batches

            # After context, should be in runtime mode and batches flushed
            assert logger_instance.startup_mode is False
            assert len(logger_instance.batches) == 0  # Batches should be cleared

            # Verify flush happened
            mock_logger.info.assert_called()

    @patch("lib.logging.batch_logger.logger")
    def test_startup_context_exception_handling(self, mock_logger):
        """Test startup context manager exception handling."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()

            # Test that context manager properly cleans up even with exceptions
            try:
                with logger_instance.startup_context():
                    logger_instance.log_agent_inheritance("exception_agent")
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Should still be in runtime mode and flushed after exception
            assert logger_instance.startup_mode is False


class TestBatchLoggerGlobalFunctions:
    """Test global convenience functions to achieve full coverage."""

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_log_agent_inheritance(self, mock_batch_logger):
        """Test global log_agent_inheritance function (line 199)."""
        log_agent_inheritance("global_agent")
        mock_batch_logger.log_agent_inheritance.assert_called_once_with("global_agent")

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_log_model_resolved(self, mock_batch_logger):
        """Test global log_model_resolved function (line 204)."""
        log_model_resolved("global_model", "global_provider")
        mock_batch_logger.log_model_resolved.assert_called_once_with(
            "global_model", "global_provider"
        )

        # Test with default provider
        mock_batch_logger.reset_mock()
        log_model_resolved("model_only")
        mock_batch_logger.log_model_resolved.assert_called_once_with(
            "model_only", "unknown"
        )

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_log_storage_created(self, mock_batch_logger):
        """Test global log_storage_created function (line 209)."""
        log_storage_created("global_storage", "global_component")
        mock_batch_logger.log_storage_created.assert_called_once_with(
            "global_storage", "global_component"
        )

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_log_agent_created(self, mock_batch_logger):
        """Test global log_agent_created function (line 214)."""
        log_agent_created("global_agent", 42)
        mock_batch_logger.log_agent_created.assert_called_once_with("global_agent", 42)

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_log_team_member_loaded(self, mock_batch_logger):
        """Test global log_team_member_loaded function (line 219)."""
        log_team_member_loaded("global_member", "global_team")
        mock_batch_logger.log_team_member_loaded.assert_called_once_with(
            "global_member", "global_team"
        )

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_log_csv_processing(self, mock_batch_logger):
        """Test global log_csv_processing function (line 224)."""
        log_csv_processing("global_source.csv", 100)
        mock_batch_logger.log_csv_processing.assert_called_once_with(
            "global_source.csv", 100
        )

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_set_runtime_mode(self, mock_batch_logger):
        """Test global set_runtime_mode function (line 229)."""
        set_runtime_mode()
        mock_batch_logger.set_runtime_mode.assert_called_once()

    @patch("lib.logging.batch_logger.batch_logger")
    def test_global_startup_logging(self, mock_batch_logger):
        """Test global startup_logging function (line 234)."""
        context_manager = startup_logging()
        mock_batch_logger.startup_context.assert_called_once()


class TestBatchLoggerEdgeCases:
    """Test edge cases and boundary conditions for comprehensive coverage."""

    @pytest.fixture
    def edge_case_logger(self):
        """Create logger for edge case testing."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()
            yield logger_instance

    @patch("lib.logging.batch_logger.logger")
    def test_flush_empty_batches(self, mock_logger, edge_case_logger):
        """Test flushing when no batches exist."""
        # Ensure batches are empty
        edge_case_logger.batches.clear()

        # Flush should handle empty batches gracefully
        edge_case_logger._flush_startup_batches()

        # No logging should occur for empty batches
        mock_logger.info.assert_not_called()

    @patch("lib.logging.batch_logger.logger")
    def test_force_flush_method(self, mock_logger, edge_case_logger):
        """Test force_flush method specifically (line 190)."""
        # Add some batch data
        edge_case_logger.startup_mode = True
        edge_case_logger.log_agent_inheritance("force_flush_agent")
        edge_case_logger.log_model_resolved("force_flush_model", "force_flush_provider")

        # Verify batches exist
        assert len(edge_case_logger.batches) > 0

        # Use force_flush method specifically
        edge_case_logger.force_flush()

        # Verify batches were cleared and summaries logged
        assert len(edge_case_logger.batches) == 0
        mock_logger.info.assert_called()

    @patch("lib.logging.batch_logger.logger")
    def test_agent_created_with_zero_parameters(self, mock_logger, edge_case_logger):
        """Test agent creation with zero parameters for proper average calculation."""
        edge_case_logger.startup_mode = True

        # Add agents with zero parameters
        edge_case_logger.log_agent_created("zero_param_agent", 0)

        # Flush to test average calculation with zero
        edge_case_logger._flush_startup_batches()

        # Should handle zero parameters correctly
        agent_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Created 1 agents:" in str(call)
        ]
        assert len(agent_calls) == 1
        assert "avg 0 params" in str(agent_calls[0])

    @patch("lib.logging.batch_logger.logger")
    def test_mixed_team_member_scenarios(self, mock_logger, edge_case_logger):
        """Test complex team member scenarios."""
        edge_case_logger.startup_mode = True

        # Mix of team-specific and generic members
        edge_case_logger.log_team_member_loaded("generic1")
        edge_case_logger.log_team_member_loaded("specific1", "team_a")
        edge_case_logger.log_team_member_loaded("generic2")
        edge_case_logger.log_team_member_loaded("specific2", "team_a")
        edge_case_logger.log_team_member_loaded("specific3", "team_b")

        # Flush and verify proper categorization
        edge_case_logger._flush_startup_batches()

        # Should log separate summaries for generic and team-specific members
        team_calls = mock_logger.info.call_args_list
        team_call_strs = [str(call) for call in team_calls]

        # Check for generic team members
        generic_calls = [s for s in team_call_strs if "Loaded 2 team members:" in s]
        assert len(generic_calls) == 1

        # Check for team-specific calls
        team_a_calls = [
            s for s in team_call_strs if "Team team_a: 2 members loaded" in s
        ]
        assert len(team_a_calls) == 1

        team_b_calls = [
            s for s in team_call_strs if "Team team_b: 1 members loaded" in s
        ]
        assert len(team_b_calls) == 1

    def test_environment_variable_edge_cases(self):
        """Test edge cases in environment variable handling."""
        # Test with different case variations
        test_cases = [
            {"HIVE_VERBOSE_LOGS": "TRUE", "expected_verbose": True},
            {"HIVE_VERBOSE_LOGS": "True", "expected_verbose": True},
            {"HIVE_VERBOSE_LOGS": "FALSE", "expected_verbose": False},
            {"HIVE_VERBOSE_LOGS": "false", "expected_verbose": False},
            {"HIVE_VERBOSE_LOGS": "invalid", "expected_verbose": False},
            {"HIVE_LOG_LEVEL": "debug", "expected_debug": True},
            {"HIVE_LOG_LEVEL": "DEBUG", "expected_debug": True},
            {"HIVE_LOG_LEVEL": "info", "expected_debug": False},
        ]

        for test_case in test_cases:
            # Convert boolean values to strings for environment variables
            env_dict = {
                k: str(v) if isinstance(v, bool) else v
                for k, v in test_case.items()
                if not k.startswith("expected_")
            }

            with patch.dict(os.environ, env_dict):
                logger_instance = BatchLogger()

                if "expected_verbose" in test_case:
                    assert logger_instance.verbose == test_case["expected_verbose"]

                if "expected_debug" in test_case:
                    is_debug = logger_instance.log_level == "DEBUG"
                    assert is_debug == test_case["expected_debug"]


class TestBatchLoggerPerformance:
    """Test performance characteristics of batch logging."""

    def test_batch_logging_performance(self):
        """Test batch logging performance with large volumes."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()

            start_time = time.time()

            # Simulate heavy batching
            for i in range(1000):
                logger_instance.log_agent_inheritance(f"agent_{i}")
                if i % 10 == 0:
                    logger_instance.log_model_resolved(f"model_{i}", "provider")
                if i % 20 == 0:
                    logger_instance.log_storage_created("vector", f"comp_{i}")

            batch_time = time.time() - start_time

            # Batching should be very fast (under 1 second for 1000 operations)
            assert batch_time < 1.0

            # Verify data is properly batched
            assert len(logger_instance.batches["agent_inheritance"]) == 1000
            assert len(logger_instance.batches["model_resolved"]) == 100
            assert len(logger_instance.batches["storage_created"]) == 50

    @patch("lib.logging.batch_logger.logger")
    def test_flush_performance(self, mock_logger):
        """Test flush performance with large batches."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            logger_instance = BatchLogger()

            # Create large batches
            for i in range(500):
                logger_instance.log_agent_inheritance(f"agent_{i}")
                logger_instance.log_model_resolved(f"model_{i}", f"provider_{i % 5}")
                logger_instance.log_storage_created(f"type_{i % 3}", f"comp_{i}")
                logger_instance.log_agent_created(f"agent_{i}", i % 50)
                logger_instance.log_team_member_loaded(f"member_{i}", f"team_{i % 10}")
                logger_instance.log_csv_processing(f"source_{i}.csv", i * 10)

            start_time = time.time()
            logger_instance._flush_startup_batches()
            flush_time = time.time() - start_time

            # Flush should complete reasonably quickly (under 2 seconds)
            assert flush_time < 2.0

            # Verify all summaries were logged
            info_calls = len(mock_logger.info.call_args_list)
            assert info_calls >= 6  # At least one summary for each batch type


class TestBatchLoggerIntegration:
    """Integration tests for batch logger with real logging output."""

    def test_full_lifecycle_integration(self):
        """Test full lifecycle from startup to runtime with real logging."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            # Capture log output
            log_capture = StringIO()

            with patch("lib.logging.batch_logger.logger") as mock_logger:
                # Configure mock to capture calls
                mock_logger.info.side_effect = lambda msg, **kwargs: log_capture.write(
                    f"INFO: {msg}\n"
                )
                mock_logger.debug.side_effect = lambda msg, **kwargs: log_capture.write(
                    f"DEBUG: {msg}\n"
                )

                # Create logger and simulate startup sequence
                logger_instance = BatchLogger()

                # Startup phase - should batch
                assert logger_instance.startup_mode is True
                logger_instance.log_agent_inheritance("startup_agent")
                logger_instance.log_model_resolved("startup_model", "startup_provider")
                logger_instance.log_storage_created("vector", "startup_component")
                logger_instance.log_agent_created("startup_agent", 25)
                logger_instance.log_team_member_loaded("startup_member")
                logger_instance.log_csv_processing("startup.csv", 100)

                # No immediate logging during startup
                assert log_capture.getvalue() == ""

                # Switch to runtime mode (triggers flush)
                logger_instance.set_runtime_mode()

                # Should have summary logs now
                log_output = log_capture.getvalue()
                assert "Applied inheritance to 1 agents:" in log_output
                assert "Model resolution: 1 operations" in log_output
                assert "Storage initialization:" in log_output
                assert "Created 1 agents:" in log_output
                assert "Loaded 1 team members:" in log_output
                assert "Knowledge base: 1 sources, 100 documents loaded" in log_output

                # Clear capture for runtime phase
                log_capture.truncate(0)
                log_capture.seek(0)

                # Runtime phase - should log immediately
                assert logger_instance.startup_mode is False
                logger_instance.log_agent_inheritance("runtime_agent")
                logger_instance.log_model_resolved("runtime_model", "runtime_provider")

                # Should have immediate debug logs
                log_output = log_capture.getvalue()
                assert "DEBUG: Applied inheritance to agent runtime_agent" in log_output
                assert "DEBUG: 🔧 Model resolved: runtime_model" in log_output

    def test_context_manager_integration(self):
        """Test context manager integration with real workflow."""
        with patch.dict(
            os.environ, {"HIVE_VERBOSE_LOGS": "false", "HIVE_LOG_LEVEL": "INFO"}
        ):
            log_capture = StringIO()

            with patch("lib.logging.batch_logger.logger") as mock_logger:
                mock_logger.info.side_effect = lambda msg, **kwargs: log_capture.write(
                    f"INFO: {msg}\n"
                )

                logger_instance = BatchLogger()

                # Use context manager
                with logger_instance.startup_context():
                    # Should be in startup mode
                    assert logger_instance.startup_mode is True

                    # Add data during startup
                    logger_instance.log_agent_inheritance("context_agent_1")
                    logger_instance.log_agent_inheritance("context_agent_2")
                    logger_instance.log_model_resolved(
                        "context_model", "context_provider"
                    )

                    # No logging yet
                    assert log_capture.getvalue() == ""

                # After context, should be flushed and in runtime mode
                assert logger_instance.startup_mode is False
                log_output = log_capture.getvalue()
                assert (
                    "Applied inheritance to 2 agents: context_agent_1, context_agent_2"
                    in log_output
                )
                assert "Model resolution: 1 operations across 1 providers" in log_output
