"""Tests for CLI orchestrator commands."""

import pytest
from pathlib import Path
from cli.commands.orchestrator import WorkflowOrchestrator


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator functionality."""
    
    def test_orchestrator_initialization(self):
        """Test WorkflowOrchestrator initializes correctly."""
        orchestrator = WorkflowOrchestrator()
        assert orchestrator.workspace_path == Path(".")
    
    def test_orchestrator_with_custom_path(self):
        """Test WorkflowOrchestrator with custom workspace path."""
        custom_path = Path("/custom/path")
        orchestrator = WorkflowOrchestrator(custom_path)
        assert orchestrator.workspace_path == custom_path
    
    def test_orchestrate_workflow_default(self):
        """Test orchestrate_workflow with default parameters."""
        orchestrator = WorkflowOrchestrator()
        result = orchestrator.orchestrate_workflow()
        assert result is True
    
    def test_orchestrate_workflow_named(self):
        """Test orchestrate_workflow with named workflow."""
        orchestrator = WorkflowOrchestrator()
        result = orchestrator.orchestrate_workflow("test_workflow")
        assert result is True
    
    def test_execute(self):
        """Test execute method."""
        orchestrator = WorkflowOrchestrator()
        result = orchestrator.execute()
        assert result is True
    
    def test_status(self):
        """Test status method."""
        orchestrator = WorkflowOrchestrator()
        status = orchestrator.status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "healthy" in status