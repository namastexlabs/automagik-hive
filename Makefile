# ===========================================
# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile
# ===========================================

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
FONT_RED := $(shell tput setaf 1)
FONT_GREEN := $(shell tput setaf 2)
FONT_YELLOW := $(shell tput setaf 3)
FONT_BLUE := $(shell tput setaf 4)
FONT_PURPLE := $(shell tput setaf 5)
FONT_CYAN := $(shell tput setaf 6)
FONT_GRAY := $(shell tput setaf 7)
FONT_BLACK := $(shell tput setaf 8)
FONT_BOLD := $(shell tput bold)
FONT_RESET := $(shell tput sgr0)
CHECKMARK := ✅
WARNING := ⚠️
ERROR := ❌
MAGIC := 🐝

# ===========================================
# 📁 Paths & Configuration
# ===========================================
PROJECT_ROOT := $(shell pwd)
VENV_PATH := $(PROJECT_ROOT)/.venv
PYTHON := $(VENV_PATH)/bin/python
DOCKER_COMPOSE_FILE := docker-compose.yml

# Docker Compose command detection
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

# UV command
UV := uv

# Load port from .env file
HIVE_PORT := $(shell grep -E '^HIVE_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
ifeq ($(HIVE_PORT),)
    HIVE_PORT := 7777
endif

# ===========================================
# 🛠️ Utility Functions
# ===========================================
define print_status
    echo -e "$(FONT_PURPLE)🐝 $(1)$(FONT_RESET)"
endef

define print_success
    echo -e "$(FONT_GREEN)$(CHECKMARK) $(1)$(FONT_RESET)"
endef

define print_warning
    echo -e "$(FONT_YELLOW)$(WARNING) $(1)$(FONT_RESET)"
endef

define print_error
    echo -e "$(FONT_RED)$(ERROR) $(1)$(FONT_RESET)"
endef

define show_hive_logo
    if [ -z "$${HIVE_QUIET_LOGO}" ]; then \
        echo ""; \
        echo -e "$(FONT_PURPLE)    ╭─────────────────────────────────────────────────────────╮$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │                                                         │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │  🐝 ⚡ 🤖  AUTOMAGIK HIVE  🤖 ⚡ 🐝                       │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │                                                         │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │        Enterprise Multi-Agent AI Framework             │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │                                                         │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │  • Intelligent Agent Coordination & Routing           │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │  • Real-time Knowledge Base with Hot Reload            │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │  • Enterprise-grade PostgreSQL Memory System           │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │  • WhatsApp Integration via Evolution API              │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │  • Production-ready with Docker & FastAPI              │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    │                                                         │$(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ╰─────────────────────────────────────────────────────────╯$(FONT_RESET)"; \
        echo ""; \
    fi
endef

define check_docker
    if ! command -v docker >/dev/null 2>&1; then \
        $(call print_error,Docker not found); \
        echo -e "$(FONT_YELLOW)💡 Install Docker: https://docs.docker.com/get-docker/$(FONT_RESET)"; \
        exit 1; \
    fi; \
    if ! docker info >/dev/null 2>&1; then \
        $(call print_error,Docker daemon not running); \
        echo -e "$(FONT_YELLOW)💡 Start Docker service$(FONT_RESET)"; \
        exit 1; \
    fi
endef

define check_env_file
    if [ ! -f ".env" ]; then \
        $(call print_warning,.env file not found); \
        echo -e "$(FONT_CYAN)Copying .env.example to .env...$(FONT_RESET)"; \
        cp .env.example .env; \
        $(call print_success,.env created from example); \
        echo -e "$(FONT_YELLOW)💡 Edit .env and add your API keys$(FONT_RESET)"; \
    fi
endef

define generate_postgres_credentials
    $(call print_status,Generating secure PostgreSQL credentials...); \
    POSTGRES_USER=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
    POSTGRES_PASS=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
    POSTGRES_DB="hive"; \
    echo "" >> .env; \
    echo "# PostgreSQL credentials (auto-generated)" >> .env; \
    echo "POSTGRES_USER=$$POSTGRES_USER" >> .env; \
    echo "POSTGRES_PASSWORD=$$POSTGRES_PASS" >> .env; \
    echo "POSTGRES_DB=$$POSTGRES_DB" >> .env; \
    echo "HIVE_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@localhost:5532/$$POSTGRES_DB" >> .env; \
    $(call print_success,PostgreSQL credentials generated and saved to .env); \
    echo -e "$(FONT_CYAN)Generated credentials:$(FONT_RESET)"; \
    echo -e "  User: $$POSTGRES_USER"; \
    echo -e "  Password: $$POSTGRES_PASS"; \
    echo -e "  Database: $$POSTGRES_DB"
endef

define setup_docker_postgres
    echo ""; \
    echo -e "$(FONT_PURPLE)🐳 Optional Docker PostgreSQL Setup$(FONT_RESET)"; \
    echo -e "$(FONT_CYAN)Would you like to set up Docker PostgreSQL with secure credentials? (y/N)$(FONT_RESET)"; \
    read -r REPLY; \
    if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
        $(call check_docker); \
        $(call generate_postgres_credentials); \
        echo -e "$(FONT_CYAN)🐳 Starting PostgreSQL container...$(FONT_RESET)"; \
        $(DOCKER_COMPOSE) up -d postgres; \
        echo -e "$(FONT_GREEN)$(CHECKMARK) PostgreSQL container started with secure credentials!$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)💡 Run 'make prod' to start the full production stack$(FONT_RESET)"; \
    else \
        echo -e "$(FONT_GRAY)Skipping Docker PostgreSQL setup$(FONT_RESET)"; \
    fi
endef

define check_prerequisites
    if ! command -v python3 >/dev/null 2>&1; then \
        $(call print_error,Python 3 not found); \
        exit 1; \
    fi; \
    if ! command -v uv >/dev/null 2>&1; then \
        if [ -f "$HOME/.local/bin/uv" ]; then \
            export PATH="$HOME/.local/bin:$PATH"; \
            $(call print_status,Found uv in $HOME/.local/bin); \
        else \
            $(call print_status,Installing uv...); \
            curl -LsSf https://astral.sh/uv/install.sh | sh; \
            export PATH="$HOME/.local/bin:$PATH"; \
            $(call print_success,uv installed successfully); \
        fi; \
    else \
        $(call print_status,uv is already available in PATH); \
    fi
endef

define setup_python_env
    $(call print_status,Installing dependencies with uv...); \
    if command -v uv >/dev/null 2>&1; then \
        if ! uv sync 2>/dev/null; then \
            $(call print_warning,Installation failed - clearing UV cache and retrying...); \
            uv cache clean; \
            uv sync; \
        fi; \
    elif [ -f "$HOME/.local/bin/uv" ]; then \
        if ! $HOME/.local/bin/uv sync 2>/dev/null; then \
            $(call print_warning,Installation failed - clearing UV cache and retrying...); \
            $HOME/.local/bin/uv cache clean; \
            $HOME/.local/bin/uv sync; \
        fi; \
    else \
        $(call print_error,uv not found - please run 'make install' first); \
        exit 1; \
    fi
endef

# ===========================================
# 📋 Help System
# ===========================================
.PHONY: help
help: ## 🐝 Show this help message
	@$(call show_hive_logo)
	@echo -e "$(FONT_BOLD)$(FONT_CYAN)Automagik Hive Multi-Agent System$(FONT_RESET) - $(FONT_GRAY)Enterprise AI Framework$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_PURPLE)🐝 Simple & Powerful - From Development to Production$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_CYAN)🚀 Quick Start:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)install$(FONT_RESET)         Install development environment (uv sync)"
	@echo -e "  $(FONT_PURPLE)dev$(FONT_RESET)             Start development server"
	@echo -e "  $(FONT_PURPLE)prod$(FONT_RESET)            Start production Docker stack"
	@echo ""
	@echo -e "$(FONT_CYAN)🎛️ Service Management:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)dev$(FONT_RESET)             Development mode with hot reload (uv run)"
	@echo -e "  $(FONT_PURPLE)prod$(FONT_RESET)            Production Docker stack (app + PostgreSQL)"
	@echo -e "  $(FONT_PURPLE)stop$(FONT_RESET)            Stop all services"
	@echo -e "  $(FONT_PURPLE)status$(FONT_RESET)          Show service status"
	@echo ""
	@echo -e "$(FONT_CYAN)📋 Monitoring:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)logs$(FONT_RESET)            Show logs (container or local development)"
	@echo -e "  $(FONT_PURPLE)logs-live$(FONT_RESET)       Follow logs in real-time"
	@echo -e "  $(FONT_PURPLE)health$(FONT_RESET)          Check service health"
	@echo ""
	@echo -e "$(FONT_CYAN)🔄 Maintenance:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)clean$(FONT_RESET)           Clean temporary files"
	@echo -e "  $(FONT_PURPLE)test$(FONT_RESET)            Run test suite"
	@echo ""
	@echo -e "$(FONT_YELLOW)💡Production uses Docker$(FONT_RESET)"
	@echo ""

# ===========================================
# 🚀 Installation
# ===========================================
.PHONY: install-local
install-local: ## 🛠️ Install development environment (local only)
	@$(call print_status,Installing development environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@$(call show_hive_logo)
	@$(call print_success,Development environment ready!)
	@echo -e "$(FONT_CYAN)💡 Run 'make dev' to start development server$(FONT_RESET)"

.PHONY: install
install: ## 🛠️ Install with optional Docker PostgreSQL setup
	@$(MAKE) install-local
	@$(call setup_docker_postgres)

# ===========================================
# 🎛️ Service Management
# ===========================================
.PHONY: dev
dev: ## 🛠️ Start development server with hot reload
	@$(call show_hive_logo)
	@$(call print_status,Starting Automagik Hive development server...)
	@$(call check_env_file)
	@if [ ! -d "$(VENV_PATH)" ]; then \
		$(call print_error,Virtual environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop the server$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)🚀 Starting server...$(FONT_RESET)"
	@uv run python api/serve.py

.PHONY: prod
prod: ## 🏭 Start production Docker stack (app + PostgreSQL)
	@$(call print_status,Starting production Docker stack...)
	@$(call check_docker)
	@$(call check_env_file)
	@echo -e "$(FONT_CYAN)🐳 Building and starting containers...$(FONT_RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d --build
	@$(call show_hive_logo)
	@$(call print_success,Production stack started!)
	@echo -e "$(FONT_CYAN)💡 API available at http://localhost:$(HIVE_PORT)$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Check status with 'make status'$(FONT_RESET)"

.PHONY: stop
stop: ## 🛑 Stop all services
	@$(call print_status,Stopping all services...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down 2>/dev/null || true
	@pkill -f "python.*api/serve.py" 2>/dev/null || true
	@$(call print_success,All services stopped!)

.PHONY: status
status: ## 📊 Show service status
	@$(call print_status,Service Status)
	@echo ""
	@echo -e "$(FONT_PURPLE)┌─────────────────────────┬──────────┬─────────┬──────────┐$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)│ Service                 │ Status   │ Port    │ Container│$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)├─────────────────────────┼──────────┼─────────┼──────────┤$(FONT_RESET)"
	@if docker ps --filter "name=hive-agents" --format "{{.Names}}" | grep -q hive-agents; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"hive-agents" "running" "$(HIVE_PORT)" "$(shell docker ps --filter 'name=hive-agents' --format '{{.ID}}' | head -c 6)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"hive-agents" "stopped" "-" "-"; \
	fi
	@if docker ps --filter "name=hive-postgres" --format "{{.Names}}" | grep -q hive-postgres; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"hive-postgres" "running" "5432" "$(shell docker ps --filter 'name=hive-postgres' --format '{{.ID}}' | head -c 6)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"hive-postgres" "stopped" "-" "-"; \
	fi
	@if pgrep -f "python.*api/serve.py" > /dev/null 2>&1; then \
		pid=$(pgrep -f "python.*api/serve.py"); \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"local-development" "running" "$$pid"; \
	fi
	@echo -e "$(FONT_PURPLE)└─────────────────────────┴──────────┴─────────┴──────────┘$(FONT_RESET)"

# ===========================================
# 📋 Monitoring
# ===========================================
.PHONY: logs
logs: ## 📄 Show logs (container or local development)
	@echo -e "$(FONT_PURPLE)🐝 Application Logs$(FONT_RESET)"
	@if docker ps --filter "name=hive-agents" --format "{{.Names}}" | grep -q hive-agents; then \
		echo -e "$(FONT_CYAN)=== Hive Agents Container Logs ====$(FONT_RESET)"; \
		docker logs --tail=50 hive-agents; \
	elif pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then \
		echo -e "$(FONT_CYAN)=== Local Development Server Logs ====$(FONT_RESET)"; \
		echo -e "$(FONT_YELLOW)💡 Local development server is running (PID: $$(pgrep -f 'python.*api/serve.py'))$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)📋 To see live logs, use: tail -f logs/app.log (if logging to file)$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)📋 Or check the terminal where 'make dev' is running$(FONT_RESET)"; \
		if [ -f "logs/app.log" ]; then \
			echo -e "$(FONT_CYAN)=== Recent Application Logs ====$(FONT_RESET)"; \
			tail -50 logs/app.log 2>/dev/null || echo -e "$(FONT_YELLOW)⚠️ Could not read logs/app.log$(FONT_RESET)"; \
		elif [ -f "app.log" ]; then \
			echo -e "$(FONT_CYAN)=== Recent Application Logs ====$(FONT_RESET)"; \
			tail -50 app.log 2>/dev/null || echo -e "$(FONT_YELLOW)⚠️ Could not read app.log$(FONT_RESET)"; \
		else \
			echo -e "$(FONT_GRAY)📝 No log files found - logs are displayed in the development terminal$(FONT_RESET)"; \
		fi \
	else \
		echo -e "$(FONT_YELLOW)⚠️ No running services found$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)💡 Start services with 'make dev' (local) or 'make prod' (Docker)$(FONT_RESET)"; \
	fi

.PHONY: logs-live
logs-live: ## 📄 Follow logs in real-time
	@echo -e "$(FONT_PURPLE)🐝 Live Application Logs$(FONT_RESET)"
	@if docker ps --filter "name=hive-agents" --format "{{.Names}}" | grep -q hive-agents; then \
		echo -e "$(FONT_CYAN)=== Following Hive Agents Container Logs ====$(FONT_RESET)"; \
		echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
		docker logs -f hive-agents; \
	elif pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then \
		echo -e "$(FONT_CYAN)=== Following Local Development Logs ====$(FONT_RESET)"; \
		if [ -f "logs/app.log" ]; then \
			echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
			tail -f logs/app.log; \
		elif [ -f "app.log" ]; then \
			echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
			tail -f app.log; \
		else \
			echo -e "$(FONT_YELLOW)⚠️ No log files found for local development$(FONT_RESET)"; \
			echo -e "$(FONT_GRAY)📋 Logs are displayed in the terminal where 'make dev' is running$(FONT_RESET)"; \
		fi \
	else \
		echo -e "$(FONT_YELLOW)⚠️ No running services found$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)💡 Start services with 'make dev' (local) or 'make prod' (Docker)$(FONT_RESET)"; \
	fi

.PHONY: health
health: ## 💊 Check service health
	@$(call print_status,Health Check)
	@if docker ps --filter "name=hive-agents" --format "{{.Names}}" | grep -q hive-agents; then \
		if curl -s http://localhost:$(HIVE_PORT)/health >/dev/null 2>&1; then \
			echo -e "$(FONT_GREEN)$(CHECKMARK) API health check: passed$(FONT_RESET)"; \
		else \
			echo -e "$(FONT_YELLOW)$(WARNING) API health check: failed$(FONT_RESET)"; \
		fi; \
	else \
		echo -e "$(FONT_YELLOW)$(WARNING) Docker containers not running$(FONT_RESET)"; \
	fi
	@if curl -s http://localhost:$(HIVE_PORT)/health >/dev/null 2>&1; then \
		echo -e "$(FONT_GREEN)$(CHECKMARK) Development server: healthy$(FONT_RESET)"; \
	elif pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then \
		echo -e "$(FONT_YELLOW)$(WARNING) Development server running but health check failed$(FONT_RESET)"; \
	fi

# ===========================================
# 🔄 Maintenance & Data Management
# ===========================================
.PHONY: clean
clean: ## 🧹 Clean temporary files
	@$(call print_status,Cleaning temporary files...)
	@rm -rf logs/ 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -type f -delete 2>/dev/null || true
	@find . -name "*.pyo" -type f -delete 2>/dev/null || true
	@$(call print_success,Cleanup complete!)


.PHONY: uninstall
uninstall: ## 🗑️ Uninstall with data options
	@$(call print_status,Automagik Hive Uninstall)
	@echo ""
	@echo -e "$(FONT_YELLOW)Choose uninstall option:$(FONT_RESET)"
	@echo -e "  $(FONT_CYAN)1)$(FONT_RESET) Remove containers only (keep data + venv)"
	@echo -e "  $(FONT_CYAN)2)$(FONT_RESET) Remove containers + venv (keep data)"
	@echo -e "  $(FONT_CYAN)3)$(FONT_RESET) Full purge (remove everything including data)"
	@echo -e "  $(FONT_CYAN)4)$(FONT_RESET) Cancel"
	@echo ""
	@if [ -d "./data/postgres" ]; then \
		DATA_SIZE=$$(du -sh ./data/postgres 2>/dev/null | cut -f1 || echo "unknown"); \
		echo -e "$(FONT_PURPLE)Current database size: $$DATA_SIZE$(FONT_RESET)"; \
		echo -e "$(FONT_PURPLE)Database location: ./data/postgres/$(FONT_RESET)"; \
		echo ""; \
	fi
	@read -p "Enter choice (1-4): " CHOICE; \
	case "$$CHOICE" in \
		1) $(MAKE) uninstall-containers-only ;; \
		2) $(MAKE) uninstall-clean ;; \
		3) $(MAKE) uninstall-purge ;; \
		4) echo -e "$(FONT_CYAN)Uninstall cancelled$(FONT_RESET)" ;; \
		*) echo -e "$(FONT_RED)Invalid choice$(FONT_RESET)" ;; \
	esac

.PHONY: uninstall-containers-only
uninstall-containers-only: ## 🗑️ Remove containers only
	@$(call print_status,Removing containers only...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down 2>/dev/null || true
	@docker container rm hive-agents hive-postgres 2>/dev/null || true
	@pkill -f "python.*api/serve.py" 2>/dev/null || true
	@$(call print_success,Containers removed)
	@echo -e "$(FONT_GREEN)✓ Kept: Database data (./data/)$(FONT_RESET)"
	@echo -e "$(FONT_GREEN)✓ Kept: Virtual environment (.venv/)$(FONT_RESET)"

.PHONY: uninstall-clean
uninstall-clean: ## 🗑️ Remove containers and venv
	@$(call print_status,Removing containers and virtual environment...)
	@echo -e "$(FONT_YELLOW)This will remove containers and .venv but keep your database data$(FONT_RESET)"
	@read -p "Type 'yes' to confirm: " CONFIRM; \
	if [ "$$CONFIRM" = "yes" ]; then \
		$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down 2>/dev/null || true; \
		docker container rm hive-agents hive-postgres 2>/dev/null || true; \
		pkill -f "python.*api/serve.py" 2>/dev/null || true; \
		rm -rf .venv/ 2>/dev/null || true; \
		$(call print_success,Clean uninstall complete); \
		echo -e "$(FONT_GREEN)✓ Kept: Database data (./data/)$(FONT_RESET)"; \
		echo -e "$(FONT_RED)✗ Removed: Virtual environment$(FONT_RESET)"; \
	else \
		echo -e "$(FONT_CYAN)Uninstall cancelled$(FONT_RESET)"; \
	fi

.PHONY: uninstall-purge
uninstall-purge: ## 🗑️ Full purge including data
	@$(call print_status,Full purge - DANGER!)
	@echo -e "$(FONT_RED)⚠️  WARNING: This will permanently delete ALL data including databases!$(FONT_RESET)"
	@if [ -d "./data/postgres" ]; then \
		DATA_SIZE=$$(du -sh ./data/postgres 2>/dev/null | cut -f1 || echo "unknown"); \
		echo -e "$(FONT_RED)Database size to be deleted: $$DATA_SIZE$(FONT_RESET)"; \
	fi
	@echo -e "$(FONT_YELLOW)Type 'DELETE EVERYTHING' to confirm full purge:$(FONT_RESET)"
	@read -r CONFIRM; \
	if [ "$$CONFIRM" = "DELETE EVERYTHING" ]; then \
		$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down 2>/dev/null || true; \
		docker container rm hive-agents hive-postgres 2>/dev/null || true; \
		docker volume rm $$(docker volume ls -q | grep -E "(postgres|hive)" 2>/dev/null) 2>/dev/null || true; \
		pkill -f "python.*api/serve.py" 2>/dev/null || true; \
		rm -rf .venv/ ./data/ logs/ 2>/dev/null || true; \
		$(call print_success,Full purge complete - all data deleted); \
	else \
		echo -e "$(FONT_CYAN)Purge cancelled$(FONT_RESET)"; \
	fi

.PHONY: test
test: ## 🧪 Run test suite
	@$(call print_status,Running tests...)
	@if [ ! -d "$(VENV_PATH)" ]; then \
		$(call print_error,Virtual environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@uv run pytest

# ===========================================
# 🧹 Phony Targets
# ===========================================
.PHONY: help install install-local dev prod stop status logs logs-live health clean test uninstall uninstall-containers-only uninstall-clean uninstall-purge