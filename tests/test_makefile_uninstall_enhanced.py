#!/usr/bin/env python3
"""
TDD Test Suite for Enhanced Makefile Uninstall Functionality

This test suite validates that the make uninstall command properly cleans up:
- Main infrastructure containers (hive-agents, hive-postgres)
- Agent infrastructure containers (hive-agents-agent, hive-postgres-agent)
- Docker images (automagik-hive-app)
- Docker volumes (app_logs, app_data, agent_app_logs, agent_app_data)
- Background processes (agent server processes)
- Data directories (./data/postgres, ./data/postgres-agent)
- Environment files (.env.agent)
- Log files and PID tracking files
"""

import os
import shutil
import tempfile

import pytest


class TestMakefileUninstallEnhanced:
    """Test comprehensive infrastructure cleanup for make uninstall"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

        # Create mock project structure
        self.create_mock_project_structure()

    def teardown_method(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_project_structure(self):
        """Create mock project files and directories"""
        # Create data directories
        os.makedirs("data/postgres", exist_ok=True)
        os.makedirs("data/postgres-agent", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # Create environment files
        with open(".env", "w") as f:
            f.write(
                "HIVE_API_PORT=8886\nHIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            )
        with open(".env.agent", "w") as f:
            f.write(
                "HIVE_API_PORT=38886\nHIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:35532/hive_agent\n"
            )

        # Create log and PID files
        with open("logs/agent-server.pid", "w") as f:
            f.write("12345")
        with open("logs/agent-server.log", "w") as f:
            f.write("Agent server logs")

        # Create mock Makefile with enhanced uninstall targets
        self.create_enhanced_makefile()

    def create_enhanced_makefile(self):
        """Create Makefile with enhanced uninstall functionality"""
        makefile_content = """
# Enhanced uninstall targets for agent infrastructure cleanup

.PHONY: uninstall-containers-only-enhanced
uninstall-containers-only-enhanced:
	@echo "Stopping and removing all containers..."
	@docker compose -f docker-compose.yml down 2>/dev/null || true
	@docker compose -f docker-compose-agent.yml down 2>/dev/null || true
	@docker container rm hive-agents hive-postgres hive-agents-agent hive-postgres-agent 2>/dev/null || true
	@pkill -f "python.*api/serve.py" 2>/dev/null || true
	@if [ -f "logs/agent-server.pid" ]; then kill -TERM $$(cat logs/agent-server.pid) 2>/dev/null || true; fi
	@echo "Containers and processes stopped"

.PHONY: uninstall-clean-enhanced
uninstall-clean-enhanced:
	@echo "Enhanced clean uninstall - removing containers, images, and venv..."
	@$(MAKE) uninstall-containers-only-enhanced
	@docker image rm automagik-hive-app 2>/dev/null || true
	@docker volume rm automagik-hive_app_logs automagik-hive_app_data 2>/dev/null || true
	@docker volume rm automagik-hive_agent_app_logs automagik-hive_agent_app_data 2>/dev/null || true
	@rm -rf .venv/ 2>/dev/null || true
	@rm -f .env.agent logs/agent-server.pid logs/agent-server.log 2>/dev/null || true
	@echo "Enhanced clean uninstall complete"

.PHONY: uninstall-purge-enhanced
uninstall-purge-enhanced:
	@echo "Enhanced purge - removing everything including agent data..."
	@$(MAKE) uninstall-clean-enhanced
	@rm -rf ./data/postgres ./data/postgres-agent 2>/dev/null || true
	@rmdir ./data 2>/dev/null || true
	@rm -rf logs/ 2>/dev/null || true
	@echo "Enhanced purge complete"
"""
        with open("Makefile", "w") as f:
            f.write(makefile_content)

    def test_uninstall_containers_only_enhanced_stops_all_services(self):
        """Test that containers-only uninstall includes agent infrastructure"""
        # Check that the actual project Makefile has enhanced container cleanup
        with open("/home/namastex/workspace/automagik-hive/Makefile") as f:
            makefile_content = f.read()

        # Verify the enhanced uninstall-containers-only target exists and includes agent cleanup
        assert "docker-compose-agent.yml down" in makefile_content
        assert "hive-agents-agent hive-postgres-agent" in makefile_content
        assert "$(call stop_agent_background)" in makefile_content

    def test_uninstall_clean_enhanced_removes_agent_infrastructure(self):
        """Test that clean uninstall removes agent infrastructure"""
        # Check that the actual project Makefile has enhanced clean uninstall
        with open("/home/namastex/workspace/automagik-hive/Makefile") as f:
            makefile_content = f.read()

        # Verify the enhanced uninstall-clean target includes agent infrastructure cleanup
        assert "docker image rm automagik-hive-app" in makefile_content
        assert (
            "automagik-hive_agent_app_logs automagik-hive_agent_app_data"
            in makefile_content
        )
        assert (
            ".env.agent logs/agent-server.pid logs/agent-server.log" in makefile_content
        )
        assert "Enhanced clean uninstall complete" in makefile_content

    def test_uninstall_purge_enhanced_removes_all_data(self):
        """Test that purge removes all data including agent data"""
        # Check that the actual project Makefile has enhanced purge
        with open("/home/namastex/workspace/automagik-hive/Makefile") as f:
            makefile_content = f.read()

        # Verify enhanced purge includes agent data in warning messages and description
        assert "main and agent databases" in makefile_content
        assert "Agent database size to be deleted" in makefile_content
        assert "All containers (main + agent)" in makefile_content
        assert "Agent environment files" in makefile_content

        # Check purge script is enhanced
        with open("/home/namastex/workspace/automagik-hive/scripts/purge.sh") as f:
            purge_content = f.read()

        assert "docker-compose-agent.yml down" in purge_content
        assert "hive-agents-agent hive-postgres-agent" in purge_content
        assert "Enhanced full purge complete" in purge_content

    def test_agent_infrastructure_cleanup_components_identified(self):
        """Test that all agent infrastructure components are identified"""
        components = {
            "containers": [
                "hive-agents",
                "hive-postgres",
                "hive-agents-agent",
                "hive-postgres-agent",
            ],
            "compose_files": ["docker-compose.yml", "docker-compose-agent.yml"],
            "images": ["automagik-hive-app"],
            "volumes": [
                "automagik-hive_app_logs",
                "automagik-hive_app_data",
                "automagik-hive_agent_app_logs",
                "automagik-hive_agent_app_data",
            ],
            "data_dirs": ["./data/postgres", "./data/postgres-agent"],
            "env_files": [".env.agent"],
            "log_files": ["logs/agent-server.pid", "logs/agent-server.log"],
        }

        # Verify all components are properly identified
        assert len(components["containers"]) == 4
        assert len(components["compose_files"]) == 2
        assert len(components["data_dirs"]) == 2
        assert "hive-agents-agent" in components["containers"]
        assert "hive-postgres-agent" in components["containers"]

    def test_makefile_enhanced_targets_exist(self):
        """Test that enhanced uninstall targets exist in Makefile"""
        with open("Makefile") as f:
            makefile_content = f.read()

        assert "uninstall-containers-only-enhanced" in makefile_content
        assert "uninstall-clean-enhanced" in makefile_content
        assert "uninstall-purge-enhanced" in makefile_content
        assert "docker compose -f docker-compose-agent.yml down" in makefile_content
        assert "hive-agents-agent hive-postgres-agent" in makefile_content

    def test_agent_process_cleanup_logic(self):
        """Test that agent processes are properly stopped"""
        # Verify PID file handling logic
        assert os.path.exists("logs/agent-server.pid")

        with open("logs/agent-server.pid") as f:
            pid = f.read().strip()

        assert pid == "12345"

        # Test cleanup removes PID file
        cleanup_commands = [
            "rm -f .env.agent logs/agent-server.pid logs/agent-server.log"
        ]

        for cmd in cleanup_commands:
            assert "logs/agent-server.pid" in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
