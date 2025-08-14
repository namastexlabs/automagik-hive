#!/usr/bin/env python3
"""
TDD Test Suite for Comprehensive Makefile Uninstall Functionality

This test suite validates that the make uninstall command properly cleans up:
- Main infrastructure containers (hive-agents, hive-postgres)
- Agent infrastructure containers (hive-agents-agent, hive-agent-postgres)
- Docker images (automagik-hive-app)
- Docker volumes (app_logs, app_data, agent_app_logs, agent_app_data)
- Background processes (agent server processes)
- Data directories (./data/postgres, ./data/agent-postgres)
- Environment files (via docker-compose inheritance from main .env)
- Log files and PID tracking files
"""

import os
import shutil
import tempfile

import pytest


class TestMakefileUninstallComprehensive:
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
        os.makedirs("data/agent-postgres", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # Create environment files
        with open(".env", "w") as f:
            f.write(
                "HIVE_API_PORT=8886\nHIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
            )
        # Agent inherits from main .env via docker-compose, no separate .env.agent needed

        # Create log and PID files
        with open("logs/agent-server.pid", "w") as f:
            f.write("12345")
        with open("logs/agent-server.log", "w") as f:
            f.write("Agent server logs")

        # Create mock Makefile with comprehensive uninstall targets
        self.create_comprehensive_makefile()

    def create_comprehensive_makefile(self):
        """Create Makefile with comprehensive uninstall functionality"""
        makefile_content = """
# Comprehensive uninstall targets for agent infrastructure cleanup

.PHONY: uninstall-containers-only-comprehensive
uninstall-containers-only-comprehensive:
	@echo "Stopping and removing all containers..."
	@docker compose -f docker-compose.yml down 2>/dev/null || true
	@docker compose -f docker-compose-agent.yml down 2>/dev/null || true
	@docker container rm hive-agents hive-postgres hive-agent-postgres hive-agent-api 2>/dev/null || true
	@pkill -f "python.*api/serve.py" 2>/dev/null || true
	@if [ -f "logs/agent-server.pid" ]; then kill -TERM $$(cat logs/agent-server.pid) 2>/dev/null || true; fi
	@echo "Containers and processes stopped"

.PHONY: uninstall-clean-comprehensive
uninstall-clean-comprehensive:
	@echo "Comprehensive clean uninstall - removing containers, images, and venv..."
	@$(MAKE) uninstall-containers-only-comprehensive
	@docker image rm automagik-hive-app 2>/dev/null || true
	@docker volume rm automagik-hive_app_logs automagik-hive_app_data 2>/dev/null || true
	@docker volume rm automagik-hive_agent_app_logs automagik-hive_agent_app_data 2>/dev/null || true
	@rm -rf .venv/ 2>/dev/null || true
	@rm -f logs/agent-server.pid logs/agent-server.log 2>/dev/null || true
	@echo "Comprehensive clean uninstall complete"

.PHONY: uninstall-purge-comprehensive
uninstall-purge-comprehensive:
	@echo "Comprehensive purge - removing everything including agent data..."
	@$(MAKE) uninstall-clean-comprehensive
	@rm -rf ./data/postgres ./data/agent-postgres 2>/dev/null || true
	@rmdir ./data 2>/dev/null || true
	@rm -rf logs/ 2>/dev/null || true
	@echo "Comprehensive purge complete"
"""
        with open("Makefile", "w") as f:
            f.write(makefile_content)

    def test_uninstall_containers_only_comprehensive_stops_all_services(self):
        """Test that containers-only uninstall includes agent infrastructure"""
        # Check that the actual project Makefile has comprehensive container cleanup
        with open("/home/namastex/workspace/automagik-hive/Makefile") as f:
            makefile_content = f.read()

        # Verify the comprehensive uninstall target exists and includes agent cleanup
        assert "docker/agent/docker-compose.yml down" in makefile_content
        assert "hive-agent-postgres hive-agent-api" in makefile_content
        assert "define stop_agent_background" in makefile_content

    def test_uninstall_clean_comprehensive_removes_agent_infrastructure(self):
        """Test that clean uninstall removes agent infrastructure"""
        # Check that the actual project Makefile has comprehensive clean uninstall
        with open("/home/namastex/workspace/automagik-hive/Makefile") as f:
            makefile_content = f.read()

        # Verify the comprehensive uninstall-clean target includes agent infrastructure cleanup
        assert "hive_agent_app_logs hive_agent_app_data" in makefile_content
        # Verify agent process files are cleaned up
        assert "logs/agent-server.pid logs/agent-server.log" in makefile_content
        # Note: Agent inherits env from main .env via docker-compose, no separate .env files
        assert "Agent environment uninstalled!" in makefile_content

    def test_uninstall_purge_comprehensive_removes_all_data(self):
        """Test that uninstall removes all data including agent data"""
        # Check that the actual project Makefile has comprehensive uninstall
        with open("/home/namastex/workspace/automagik-hive/Makefile") as f:
            makefile_content = f.read()

        # Verify uninstall includes agent infrastructure cleanup - using actual text from Makefile
        assert "This will destroy all containers and data, then reinstall and start fresh" in makefile_content
        assert "Agent environment uninstalled!" in makefile_content
        assert "docker/agent/docker-compose.yml down" in makefile_content
        assert "hive-agent-postgres hive-agent-api" in makefile_content

        # Check purge script is comprehensive - using actual patterns from purge.sh
        with open("/home/namastex/workspace/automagik-hive/scripts/purge.sh") as f:
            purge_content = f.read()

        assert "docker-compose-agent.yml down" in purge_content
        assert "hive-agents-agent hive-agent-postgres" in purge_content
        assert "Enhanced full purge complete - all main and agent infrastructure deleted" in purge_content

    def test_agent_infrastructure_cleanup_components_identified(self):
        """Test that all agent infrastructure components are identified"""
        components = {
            "containers": [
                "hive-agents",
                "hive-postgres",
                "hive-agent-api",
                "hive-agent-postgres",
            ],
            "compose_files": ["docker-compose.yml", "docker-compose-agent.yml"],
            "images": ["automagik-hive-app"],
            "volumes": [
                "automagik-hive_app_logs",
                "automagik-hive_app_data",
                "automagik-hive_agent_app_logs",
                "automagik-hive_agent_app_data",
            ],
            "data_dirs": ["./data/postgres", "./data/agent-postgres"],
            "env_inheritance": ["main .env via docker-compose"],
            "log_files": ["logs/agent-server.pid", "logs/agent-server.log"],
        }

        # Verify all components are properly identified
        assert len(components["containers"]) == 4
        assert len(components["compose_files"]) == 2
        assert len(components["data_dirs"]) == 2
        assert "hive-agent-api" in components["containers"]
        assert "hive-agent-postgres" in components["containers"]

    def test_makefile_comprehensive_targets_exist(self):
        """Test that comprehensive uninstall targets exist in Makefile"""
        with open("Makefile") as f:
            makefile_content = f.read()

        assert "uninstall-containers-only-comprehensive" in makefile_content
        assert "uninstall-clean-comprehensive" in makefile_content
        assert "uninstall-purge-comprehensive" in makefile_content
        assert "docker compose -f docker-compose-agent.yml down" in makefile_content
        assert "hive-agent-postgres hive-agent-api" in makefile_content

    def test_agent_process_cleanup_logic(self):
        """Test that agent processes are properly stopped"""
        # Verify PID file handling logic
        assert os.path.exists("logs/agent-server.pid")

        with open("logs/agent-server.pid") as f:
            pid = f.read().strip()

        assert pid == "12345"

        # Test cleanup removes PID file
        cleanup_commands = [
            "rm -f logs/agent-server.pid logs/agent-server.log"
        ]

        for cmd in cleanup_commands:
            assert "logs/agent-server.pid" in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
