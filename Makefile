# ===========================================
# 🏦 PagBank Multi-Agent System - Simplified Makefile
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
MAGIC := 🏦

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
PB_AGENTS_PORT := $(shell grep -E '^PB_AGENTS_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
ifeq ($(PB_AGENTS_PORT),)
    PB_AGENTS_PORT := 7777
endif

# ===========================================
# 🛠️ Utility Functions
# ===========================================
define print_status
    echo -e "$(FONT_PURPLE)🏦 $(1)$(FONT_RESET)"
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

define show_pagbank_logo
    if [ -z "$${PAGBANK_QUIET_LOGO}" ]; then \
        echo ""; \
        echo -e "$(FONT_PURPLE)           @@@@@]^^}@@@@@@                                                                                                                        $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)       @@@*++++++++++++)@@@                                                                                                                      $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    @@@@+++++++++++++++++*@@@                                                                                                                    $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)   @@@++++++++++++++++++++++@@@                                                                                                                  $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)  @@@++++****^>>****+++++++++@@@                                                                               @@@@                              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE) @@@++**>@@@%()(%@@@#**++++++*@@%         @%%@%@@@@                         @%%%%%%@@@                         @@@@                              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)#@@^+*%@(...........(@@*++++++@@@        %@@@%%@@@@@     @%%%@      @@#@@   @@@@  %@@@      @%%%@       @#@   @@@@                               $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)@@@**@................(@@<^*+=#@@@       @@@@   %@@% @@@@@%@@@@  %@@@@%@@%  @@@  @@@@@  @@@@@%@@@@ @@@%@@@@@  @@@@ %@@%%                         $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)@@@>@..............@@>**+++*@@@@@@      @@@@@@@@@@@ @@@@@  @@@ @@@@%  %@@% %@@@%@@@@%  @@@@@  @@% @@@@@  @@@  @@@%@@@@                           $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)@@@@..............@>*+++++*+++@@@@      @@@@@@@@%  %@@@   @@@% @@@@   @@@  @@@   @@@@ @@@@   @@@% @@@%  @@@@ #@@@@@@                             $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)@@@=.............@>**++++++++++@@%      @@@        @@@%  %@@@ @@@@  @@@@@ @@@@   @@@@ @@@%  %@@@  @@@   @@@% @@@@@@@@                            $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)#@@..............@**+++++++++++#@      %@@@        %@@@%@@@@@  @@@@@@@@@@ @@@@@@@@@@@ %@@@%@@@@@ @@@@   @@@ @@@@  @@@@                           $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE) @@@.............@>**++++++++++@@      @%%@         @%%@  %#@   @%%@@@@@  @%%%%%%@     @%%@  %%@ @#%@   #%@ @##@   @%#                           $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)  @@..............@>*+++++*+++@@                              @@@@@@@@@                                                                          $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)   @@..............@@>*++++~@@@                               %@@@@@@@                                                                           $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    @@@..............+%@@@@@@                                                                                                                    $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)      @@@=.........^%@@@@@@                                                                                                                      $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)         @@@@@@@@@@@@@@@                                                                                                                         $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                                                                                                                                                  $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                    Multi-Agent AI System                                                                                                         $(FONT_RESET)"; \
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
help: ## 🏦 Show this help message
	@$(call show_pagbank_logo)
	@echo -e "$(FONT_BOLD)$(FONT_CYAN)PagBank Multi-Agent System$(FONT_RESET) - $(FONT_GRAY)AI Customer Service Agents$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_PURPLE)🏦 Simple & Powerful - From Development to Production$(FONT_RESET)"
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
.PHONY: install
install: ## 🛠️ Install development environment
	@$(call print_status,Installing development environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@$(call show_pagbank_logo)
	@$(call print_success,Development environment ready!)
	@echo -e "$(FONT_CYAN)💡 Run 'make dev' to start development server$(FONT_RESET)"

# ===========================================
# 🎛️ Service Management
# ===========================================
.PHONY: dev
dev: ## 🛠️ Start development server with hot reload )
	@$(call show_pagbank_logo)
	@$(call print_status,Starting PagBank development server...)
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
	@$(call show_pagbank_logo)
	@$(call print_success,Production stack started!)
	@echo -e "$(FONT_CYAN)💡 API available at http://localhost:$(PB_AGENTS_PORT)$(FONT_RESET)"
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
	@if docker ps --filter "name=pagbank-agents" --format "{{.Names}}" | grep -q pagbank-agents; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"pagbank-agents" "running" "$(PB_AGENTS_PORT)" "$(shell docker ps --filter 'name=pagbank-agents' --format '{{.ID}}' | head -c 6)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"pagbank-agents" "stopped" "-" "-"; \
	fi
	@if docker ps --filter "name=pagbank-pgvector" --format "{{.Names}}" | grep -q pagbank-pgvector; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"pagbank-pgvector" "running" "5432" "$(shell docker ps --filter 'name=pagbank-pgvector' --format '{{.ID}}' | head -c 6)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"pagbank-pgvector" "stopped" "-" "-"; \
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
	@echo -e "$(FONT_PURPLE)🏦 Application Logs$(FONT_RESET)"
	@if docker ps --filter "name=pagbank-agents" --format "{{.Names}}" | grep -q pagbank-agents; then \
		echo -e "$(FONT_CYAN)=== PagBank Agents Container Logs ====$(FONT_RESET)"; \
		docker logs --tail=50 pagbank-agents; \
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
	@echo -e "$(FONT_PURPLE)🏦 Live Application Logs$(FONT_RESET)"
	@if docker ps --filter "name=pagbank-agents" --format "{{.Names}}" | grep -q pagbank-agents; then \
		echo -e "$(FONT_CYAN)=== Following PagBank Agents Container Logs ====$(FONT_RESET)"; \
		echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
		docker logs -f pagbank-agents; \
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
	@if docker ps --filter "name=pagbank-agents" --format "{{.Names}}" | grep -q pagbank-agents; then \
		if curl -s http://localhost:$(PB_AGENTS_PORT)/health >/dev/null 2>&1; then \
			echo -e "$(FONT_GREEN)$(CHECKMARK) API health check: passed$(FONT_RESET)"; \
		else \
			echo -e "$(FONT_YELLOW)$(WARNING) API health check: failed$(FONT_RESET)"; \
		fi; \
	else \
		echo -e "$(FONT_YELLOW)$(WARNING) Docker containers not running$(FONT_RESET)"; \
	fi
	@if curl -s http://localhost:$(PB_AGENTS_PORT)/health >/dev/null 2>&1; then \
		echo -e "$(FONT_GREEN)$(CHECKMARK) Development server: healthy$(FONT_RESET)"; \
	elif pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then \
		echo -e "$(FONT_YELLOW)$(WARNING) Development server running but health check failed$(FONT_RESET)"; \
	fi

# ===========================================
# 🔄 Maintenance
# ===========================================
.PHONY: clean
clean: ## 🧹 Clean temporary files
	@$(call print_status,Cleaning temporary files...)
	@rm -rf logs/ 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -type f -delete 2>/dev/null || true
	@find . -name "*.pyo" -type f -delete 2>/dev/null || true
	@$(call print_success,Cleanup complete!)

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
.PHONY: help install dev prod stop status logs logs-live health clean test
