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
HIVE_PORT := $(shell grep -E '^HIVE_API_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
ifeq ($(HIVE_PORT),)
    HIVE_PORT := 8886
endif

# Load agent port from .env.agent file
AGENT_PORT := $(shell grep -E '^HIVE_API_PORT=' .env.agent 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
ifeq ($(AGENT_PORT),)
    AGENT_PORT := 38886
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
        echo -e "$(FONT_PURPLE)                                                                     $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                                                                     $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████    ████             ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████     ████            ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████      ████      ████ ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████      █████    ████  ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████       ████   ████   ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                 ████    ████        ████  ████   ██████████████    $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                 ████    ████        █████████    ██████████████    $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                 ████    ████         ███████     ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    █████████████████    ████          █████      ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    █████████████████    ████           ████      ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████ ██████████        ░██       ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████ ██████████         █        ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                                                                     $(FONT_RESET)"; \
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
        $(call generate_hive_api_key); \
        echo -e "$(FONT_YELLOW)💡 Edit .env and add your AI provider API keys$(FONT_RESET)"; \
    elif grep -q "HIVE_API_KEY=your-hive-api-key-here" .env; then \
        $(call print_warning,Hive API key needs to be generated); \
        $(call generate_hive_api_key); \
    elif ! grep -q "HIVE_API_KEY=hive_" .env; then \
        $(call print_warning,Hive API key format needs updating to hive_ prefix); \
        $(call generate_hive_api_key); \
    fi
endef

define generate_hive_api_key
    $(call print_status,Generating secure Hive API key...); \
    uv run python -c "from lib.auth.cli import regenerate_key; regenerate_key()"
endef

define generate_agent_hive_api_key
    $(call print_status,Generating secure Agent API key...); \
    API_KEY=$$(uv run python -c "import secrets; print('hive_agent_' + secrets.token_urlsafe(32))"); \
    sed -i "s|^HIVE_API_KEY=.*|HIVE_API_KEY=$$API_KEY|" .env.agent; \
    echo -e "$(FONT_GREEN)🔑 Agent API Key: $$API_KEY$(FONT_RESET)"
endef

define show_api_key_info
    echo ""; \
    CURRENT_KEY=$$(grep "^HIVE_API_KEY=" .env 2>/dev/null | cut -d'=' -f2); \
    if [ -n "$$CURRENT_KEY" ]; then \
        echo -e "$(FONT_GREEN)🔑 YOUR API KEY: $$CURRENT_KEY$(FONT_RESET)"; \
        echo -e "$(FONT_CYAN)   Already saved to .env - use in x-api-key headers$(FONT_RESET)"; \
        echo ""; \
    fi
endef

define generate_postgres_credentials
    $(call print_status,Generating secure PostgreSQL credentials...); \
    POSTGRES_USER=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
    POSTGRES_PASS=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
    POSTGRES_DB="hive"; \
    sed -i "s|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@localhost:5532/$$POSTGRES_DB|" .env; \
    $(call print_success,PostgreSQL credentials generated and saved to .env); \
    echo -e "$(FONT_CYAN)Generated credentials:$(FONT_RESET)"; \
    echo -e "  User: $$POSTGRES_USER"; \
    echo -e "  Password: $$POSTGRES_PASS"; \
    echo -e "  Database: $$POSTGRES_DB"
endef

define generate_agent_postgres_credentials
    $(call print_status,Generating secure Agent PostgreSQL credentials...); \
    POSTGRES_USER=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
    POSTGRES_PASS=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
    POSTGRES_DB="hive_agent"; \
    sed -i "s|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@localhost:35532/$$POSTGRES_DB|" .env.agent; \
    $(call print_success,Agent PostgreSQL credentials generated and saved to .env.agent); \
    echo -e "$(FONT_CYAN)Generated agent credentials:$(FONT_RESET)"; \
    echo -e "  User: $$POSTGRES_USER"; \
    echo -e "  Password: $$POSTGRES_PASS"; \
    echo -e "  Database: $$POSTGRES_DB"
endef

define setup_docker_postgres
    echo ""; \
    echo -e "$(FONT_PURPLE)🐳 Optional Docker PostgreSQL Setup$(FONT_RESET)"; \
    echo -e "$(FONT_CYAN)Would you like to set up Docker PostgreSQL with secure credentials? (Y/n)$(FONT_RESET)"; \
    read -r REPLY </dev/tty; \
    if [ "$$REPLY" != "n" ] && [ "$$REPLY" != "N" ]; then \
        $(call check_docker); \
        $(call generate_postgres_credentials); \
        echo -e "$(FONT_CYAN)🐳 Starting PostgreSQL container...$(FONT_RESET)"; \
        if [ -d "./data/postgres" ]; then \
            if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
                OWNER=$$(stat -c '%U' ./data/postgres 2>/dev/null || stat -f '%Su' ./data/postgres 2>/dev/null || echo "unknown"); \
                if [ "$$OWNER" = "root" ]; then \
                    echo -e "$(FONT_YELLOW)💡 Fixing PostgreSQL data directory permissions...$(FONT_RESET)"; \
                    sudo chown -R $$(id -u):$$(id -g) ./data/postgres 2>/dev/null || true; \
                fi; \
            fi; \
        fi; \
        DB_URL=$$(grep '^HIVE_DATABASE_URL=' .env | cut -d'=' -f2-); \
        WITHOUT_PROTOCOL=$${DB_URL#*://}; \
        CREDENTIALS=$${WITHOUT_PROTOCOL%%@*}; \
        AFTER_AT=$${WITHOUT_PROTOCOL##*@}; \
        export POSTGRES_USER=$${CREDENTIALS%%:*}; \
        export POSTGRES_PASSWORD=$${CREDENTIALS##*:}; \
        export POSTGRES_DB=$${AFTER_AT##*/}; \
        if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
            export POSTGRES_UID=$$(id -u); \
            export POSTGRES_GID=$$(id -g); \
        else \
            export POSTGRES_UID=1000; \
            export POSTGRES_GID=1000; \
        fi; \
        mkdir -p ./data/postgres && chown -R $${POSTGRES_UID}:$${POSTGRES_GID} ./data 2>/dev/null || sudo chown -R $$USER:$$USER ./data; \
        $(DOCKER_COMPOSE) up -d postgres; \
        echo -e "$(FONT_GREEN)$(CHECKMARK) PostgreSQL container started with secure credentials!$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)💡 Run 'make dev' for development or 'make prod' for production stack$(FONT_RESET)"; \
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

define setup_agent_env
    $(call print_status,Creating agent environment...); \
    cp .env.example .env.agent; \
    sed -i 's|HIVE_API_PORT=8886|HIVE_API_PORT=38886|' .env.agent; \
    sed -i 's|localhost:5532|localhost:35532|' .env.agent; \
    sed -i 's|/hive|/hive_agent|' .env.agent; \
    sed -i 's|http://localhost:8886|http://localhost:38886|' .env.agent; \
    $(call print_success,Agent environment file created)
endef

define setup_agent_postgres
    $(call check_docker); \
    $(call generate_agent_postgres_credentials); \
    echo -e "$(FONT_CYAN)🐳 Starting Agent PostgreSQL container...$(FONT_RESET)"; \
    DB_URL=$$(grep '^HIVE_DATABASE_URL=' .env.agent | cut -d'=' -f2-); \
    WITHOUT_PROTOCOL=$${DB_URL#*://}; \
    CREDENTIALS=$${WITHOUT_PROTOCOL%%@*}; \
    AFTER_AT=$${WITHOUT_PROTOCOL##*@}; \
    export POSTGRES_USER=$${CREDENTIALS%%:*}; \
    export POSTGRES_PASSWORD=$${CREDENTIALS##*:}; \
    export POSTGRES_DB=$${AFTER_AT##*/}; \
    if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
        export POSTGRES_UID=$$(id -u); \
        export POSTGRES_GID=$$(id -g); \
    else \
        export POSTGRES_UID=1000; \
        export POSTGRES_GID=1000; \
    fi; \
    mkdir -p ./data/postgres-agent && chown -R $${POSTGRES_UID}:$${POSTGRES_GID} ./data 2>/dev/null || sudo chown -R $$USER:$$USER ./data; \
    $(DOCKER_COMPOSE) -f docker-compose-agent.yml up -d postgres-agent; \
    $(call print_success,Agent PostgreSQL container started on port 35532!)
endef

define cleanup_agent_environment
    $(call print_status,Cleaning up existing agent environment...); \
    pkill -f "python.*api/serve.py.*\.env\.agent" 2>/dev/null || true; \
    $(DOCKER_COMPOSE) -f docker-compose-agent.yml down 2>/dev/null || true; \
    docker container rm hive-agents-agent hive-postgres-agent 2>/dev/null || true; \
    rm -f logs/agent-server.pid logs/agent-server.log 2>/dev/null || true; \
    rm -rf ./data/postgres-agent 2>/dev/null || true; \
    $(call print_success,Agent environment cleaned up)
endef

define start_agent_background
    mkdir -p logs; \
    $(call print_status,Starting agent server in background...); \
    ( \
        set -a; \
        source .env.agent; \
        set +a; \
        nohup uv run python api/serve.py > logs/agent-server.log 2>&1 & echo $$! > logs/agent-server.pid; \
    ); \
    sleep 3; \
    if [ -f logs/agent-server.pid ] && kill -0 $$(cat logs/agent-server.pid) 2>/dev/null; then \
        $(call print_success,Agent server started in background (PID: $$(cat logs/agent-server.pid))); \
        echo -e "$(FONT_CYAN)🌐 Agent API: http://localhost:$(AGENT_PORT)$(FONT_RESET)"; \
        echo -e "$(FONT_CYAN)📋 Logs: make agent-logs$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)--- Startup logs ---$(FONT_RESET)"; \
        head -20 logs/agent-server.log 2>/dev/null || echo "No logs yet"; \
    else \
        $(call print_error,Failed to start agent server); \
        echo -e "$(FONT_YELLOW)Check logs: cat logs/agent-server.log$(FONT_RESET)"; \
        exit 1; \
    fi
endef

define stop_agent_background
    if [ -f logs/agent-server.pid ]; then \
        PID=$$(cat logs/agent-server.pid); \
        if kill -0 $$PID 2>/dev/null; then \
            $(call print_status,Stopping agent server (PID: $$PID)...); \
            kill -TERM $$PID 2>/dev/null; \
            sleep 5; \
            if kill -0 $$PID 2>/dev/null; then \
                kill -KILL $$PID 2>/dev/null; \
            fi; \
            $(call print_success,Agent server stopped); \
        else \
            $(call print_warning,Agent server not running); \
        fi; \
        rm -f logs/agent-server.pid; \
    else \
        $(call print_warning,No agent server PID file found); \
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
	@echo -e "$(FONT_PURPLE)🐝 Usage: make [command]$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_CYAN)🚀 Getting Started:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)install$(FONT_RESET)         Install environment with optional PostgreSQL setup"
	@echo -e "  $(FONT_PURPLE)dev$(FONT_RESET)             Start local development server (with hot-reload)"
	@echo -e "  $(FONT_PURPLE)prod$(FONT_RESET)            Start production stack via Docker"
	@echo ""
	@echo -e "$(FONT_CYAN)🤖 Agent Environment (LLM-Optimized):$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)install-agent$(FONT_RESET)   Silent agent environment setup (ports 38886/35532)"
	@echo -e "  $(FONT_PURPLE)agent$(FONT_RESET)           Start agent server in background (non-blocking)"
	@echo -e "  $(FONT_PURPLE)agent-stop$(FONT_RESET)      Stop agent server cleanly"
	@echo -e "  $(FONT_PURPLE)agent-restart$(FONT_RESET)   Restart agent server"
	@echo -e "  $(FONT_PURPLE)agent-logs$(FONT_RESET)      Show agent logs (non-blocking)"
	@echo -e "  $(FONT_PURPLE)agent-status$(FONT_RESET)    Check agent environment status"
	@echo ""
	@echo -e "$(FONT_CYAN)🎛️ Service Control:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)status$(FONT_RESET)          Show running services status"
	@echo -e "  $(FONT_PURPLE)stop$(FONT_RESET)            Stop application service (keeps database running)"
	@echo -e "  $(FONT_PURPLE)stop-all$(FONT_RESET)       Stop all services (including database)"
	@echo -e "  $(FONT_PURPLE)update$(FONT_RESET)          Fast rebuild of Docker app using cache"
	@echo -e "  $(FONT_PURPLE)rebuild$(FONT_RESET)         Force full rebuild of Docker app (no cache)"
	@echo ""
	@echo -e "$(FONT_CYAN)📋 Monitoring:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)logs$(FONT_RESET)            Show recent service logs"
	@echo -e "  $(FONT_PURPLE)logs-live$(FONT_RESET)       Follow service logs in real-time"
	@echo -e "  $(FONT_PURPLE)health$(FONT_RESET)          Check API health endpoint"
	@echo ""
	@echo -e "$(FONT_CYAN)🔄 Maintenance:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)test$(FONT_RESET)            Run Python test suite"
	@echo -e "  $(FONT_PURPLE)clean$(FONT_RESET)           Clean temporary files (__pycache__, etc.)"
	@echo -e "  $(FONT_PURPLE)uninstall$(FONT_RESET)       Show options to uninstall and purge data"
	@echo ""
	@echo -e "$(FONT_YELLOW)💡 For detailed commands, inspect the Makefile.$(FONT_RESET)"
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
	@$(call show_api_key_info)
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
	@if [ -f .env ]; then \
		DB_URL=$$(grep '^HIVE_DATABASE_URL=' .env | cut -d'=' -f2-); \
		if [ -n "$$DB_URL" ]; then \
			WITHOUT_PROTOCOL=$${DB_URL#*://}; \
			CREDENTIALS=$${WITHOUT_PROTOCOL%%@*}; \
			AFTER_AT=$${WITHOUT_PROTOCOL##*@}; \
			export POSTGRES_USER=$${CREDENTIALS%%:*}; \
			export POSTGRES_PASSWORD=$${CREDENTIALS##*:}; \
			export POSTGRES_DB=$${AFTER_AT##*/}; \
			if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
				export POSTGRES_UID=$$(id -u); \
				export POSTGRES_GID=$$(id -g); \
			else \
				export POSTGRES_UID=1000; \
				export POSTGRES_GID=1000; \
			fi; \
			$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d --build; \
		else \
			echo "Error: Could not extract database URL from .env"; \
			exit 1; \
		fi; \
	else \
		echo "Error: .env file not found"; \
		exit 1; \
	fi
	@$(call show_hive_logo)
	@$(call print_success,Production stack started!)
	@echo -e "$(FONT_CYAN)💡 API available at http://localhost:$(HIVE_PORT)$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Check status with 'make status'$(FONT_RESET)"

.PHONY: stop
stop: ## 🛑 Stop application services (keeps PostgreSQL running)
	@$(call print_status,Stopping application services...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) stop app 2>/dev/null || true
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) rm -f app 2>/dev/null || true
	@pkill -f "python.*api/serve.py" 2>/dev/null || true
	@$(call print_success,Application services stopped! PostgreSQL remains running.)

.PHONY: stop-all
stop-all: ## 🛑 Stop all services including PostgreSQL
	@$(call print_status,Stopping all services...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down 2>/dev/null || true
	@pkill -f "python.*api/serve.py" 2>/dev/null || true
	@$(call print_success,All services stopped!)

.PHONY: update
update: ## 🔄 Fast rebuild using cache (recommended for development)
	@$(call print_status,Fast updating Automagik Hive application...)
	@$(call print_status,Rebuilding with cache optimization...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d --build app
	@$(call print_success,Application updated successfully! PostgreSQL data preserved.)
	@echo -e "$(FONT_CYAN)💡 API available at http://localhost:$(HIVE_PORT)$(FONT_RESET)"

.PHONY: rebuild
rebuild: ## 🔄 Force full rebuild without cache (for clean state)
	@$(call print_status,Force rebuilding Automagik Hive application...)
	@$(call print_status,Stopping application container...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) stop app 2>/dev/null || true
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) rm -f app 2>/dev/null || true
	@$(call print_status,Rebuilding application container (no cache)...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build --no-cache app
	@$(call print_status,Starting updated application...)
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d app
	@$(call print_success,Application rebuilt successfully! PostgreSQL data preserved.)
	@echo -e "$(FONT_CYAN)💡 API available at http://localhost:$(HIVE_PORT)$(FONT_RESET)"

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
	@read -p "Enter choice (1-4): " CHOICE < /dev/tty; \
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
	@if pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then pkill -f "python.*api/serve.py" 2>/dev/null || true; fi
	@$(call print_success,Containers removed)
	@echo -e "$(FONT_GREEN)✓ Kept: Database data (./data/)$(FONT_RESET)"
	@echo -e "$(FONT_GREEN)✓ Kept: Virtual environment (.venv/)$(FONT_RESET)"

.PHONY: uninstall-clean
uninstall-clean: ## 🗑️ Remove containers and venv
	@$(call print_status,Removing containers and virtual environment...)
	@echo -e "$(FONT_YELLOW)This will remove containers and .venv but keep your database data$(FONT_RESET)"
	@read -p "Type 'yes' to confirm: " CONFIRM < /dev/tty; \
	if [ "$$CONFIRM" = "yes" ]; then \
		$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down 2>/dev/null || true; \
		docker container rm hive-agents hive-postgres 2>/dev/null || true; \
		if pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then pkill -f "python.*api/serve.py" 2>/dev/null || true; fi; \
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
	@read -r CONFIRM < /dev/tty; \
	if [ "$$CONFIRM" = "DELETE EVERYTHING" ]; then \
		./scripts/purge.sh; \
	else \
		echo -e "$(FONT_CYAN)Purge cancelled$(FONT_RESET)"; \
	fi

# ===========================================
# 🤖 Agent Environment Commands
# ===========================================
.PHONY: install-agent
install-agent: ## 🤖 Silent agent environment setup (destructive reinstall)
	@$(call print_status,Setting up agent environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@if [ -f ".env.agent" ] || [ -f "logs/agent-server.pid" ] || docker ps --filter "name=hive-postgres-agent" --format "{{.Names}}" | grep -q hive-postgres-agent; then \
		$(call cleanup_agent_environment); \
	fi
	@$(call setup_agent_env)
	@$(call setup_agent_postgres)
	@$(call generate_agent_hive_api_key)
	@$(call print_success,Agent environment ready!)
	@echo -e "$(FONT_CYAN)🌐 Agent API will be available at: http://localhost:$(AGENT_PORT)$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Start with: make agent$(FONT_RESET)"

.PHONY: agent
agent: ## 🤖 Start agent server in background (non-blocking)
	@if [ ! -f ".env.agent" ]; then \
		$(call print_error,Agent environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install-agent' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@if [ ! -d "$(VENV_PATH)" ]; then \
		$(call print_error,Virtual environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install-agent' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@if [ -f "logs/agent-server.pid" ] && kill -0 $$(cat logs/agent-server.pid) 2>/dev/null; then \
		$(call print_warning,Agent server already running (PID: $$(cat logs/agent-server.pid))); \
		echo -e "$(FONT_CYAN)🌐 Agent API: http://localhost:$(AGENT_PORT)$(FONT_RESET)"; \
		exit 0; \
	fi
	@$(call start_agent_background)

.PHONY: agent-stop
agent-stop: ## 🛑 Stop agent server cleanly
	@$(call stop_agent_background)

.PHONY: agent-restart
agent-restart: ## 🔄 Restart agent server
	@$(call stop_agent_background)
	@sleep 2
	@$(MAKE) agent

.PHONY: agent-logs
agent-logs: ## 📄 Show agent logs (non-blocking)
	@echo -e "$(FONT_PURPLE)🤖 Agent Server Logs$(FONT_RESET)"
	@if [ -f "logs/agent-server.log" ]; then \
		echo -e "$(FONT_CYAN)=== Recent Agent Logs (last 50 lines) ====$(FONT_RESET)"; \
		tail -50 logs/agent-server.log; \
	else \
		echo -e "$(FONT_YELLOW)⚠️ No agent log file found$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)💡 Start agent server with 'make agent'$(FONT_RESET)"; \
	fi

.PHONY: agent-status
agent-status: ## 📊 Check agent environment status
	@$(call print_status,Agent Environment Status)
	@echo ""
	@echo -e "$(FONT_PURPLE)┌─────────────────────────┬──────────┬─────────┬──────────┐$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)│ Agent Service           │ Status   │ Port    │ PID      │$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)├─────────────────────────┼──────────┼─────────┼──────────┤$(FONT_RESET)"
	@if [ -f "logs/agent-server.pid" ] && kill -0 $$(cat logs/agent-server.pid) 2>/dev/null; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"agent-server" "running" "$(AGENT_PORT)" "$$(cat logs/agent-server.pid)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"agent-server" "stopped" "-" "-"; \
	fi
	@if docker ps --filter "name=hive-postgres-agent" --format "{{.Names}}" | grep -q hive-postgres-agent; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"agent-postgres" "running" "35532" "$(shell docker ps --filter 'name=hive-postgres-agent' --format '{{.ID}}' | head -c 6)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-8s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET) %-7s $(FONT_PURPLE)│$(FONT_RESET) %-8s $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"agent-postgres" "stopped" "-" "-"; \
	fi
	@echo -e "$(FONT_PURPLE)└─────────────────────────┴──────────┴─────────┴──────────┘$(FONT_RESET)"
	@if [ -f "logs/agent-server.log" ]; then \
		echo ""; \
		echo -e "$(FONT_CYAN)Recent agent activity:$(FONT_RESET)"; \
		tail -5 logs/agent-server.log 2>/dev/null | sed 's/^/  /' || echo -e "$(FONT_GRAY)  No recent activity$(FONT_RESET)"; \
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
.PHONY: help install install-local dev prod stop status logs logs-live health clean test uninstall uninstall-containers-only uninstall-clean uninstall-purge install-agent agent agent-stop agent-restart agent-logs agent-status