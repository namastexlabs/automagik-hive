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
DOCKER_COMPOSE_FILE := docker/main/docker-compose.yml

# Docker Compose command detection
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

# UV command
UV := uv

# Load port from .env file
HIVE_PORT := $(shell grep -E '^HIVE_API_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
ifeq ($(HIVE_PORT),)
    HIVE_PORT := 8886
endif

# Load agent port from docker/agent/.env file
AGENT_PORT := $(shell grep -E '^HIVE_API_PORT=' docker/agent/.env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
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
    $(call use_unified_api_key_for_agent); \
    $(call extract_hive_api_key_from_env); \
    if [ -z "$$HIVE_API_KEY" ]; then \
        $(call print_status,Generating secure Agent API key...); \
        API_KEY=$$(uv run python -c "import secrets; print('hive_agent_' + secrets.token_urlsafe(32))"); \
        sed -i "s|^HIVE_API_KEY=.*|HIVE_API_KEY=$$API_KEY|" docker/agent/.env; \
        echo -e "$(FONT_GREEN)🔑 Agent API Key: $$API_KEY$(FONT_RESET)"; \
    fi
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
    $(call extract_postgres_credentials_from_env); \
    if [ -n "$$POSTGRES_USER" ] && [ -n "$$POSTGRES_PASS" ] && \
       [ "$$POSTGRES_PASS" != "your-secure-password-here" ] && \
       [ "$$POSTGRES_USER" != "hive_user" ] && \
       [ "$$POSTGRES_USER" != "your-username-here" ]; then \
        $(call print_status,Using existing PostgreSQL credentials from .env...); \
        echo -e "$(FONT_CYAN)Reusing credentials:$(FONT_RESET)"; \
        echo -e "  User: $$POSTGRES_USER"; \
        echo -e "  Password: $$POSTGRES_PASS"; \
        echo -e "  Database: $$POSTGRES_DB"; \
    else \
        $(call print_status,Generating secure PostgreSQL credentials...); \
        POSTGRES_USER=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
        POSTGRES_PASS=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
        POSTGRES_DB="hive"; \
        sed -i "s|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@localhost:5532/$$POSTGRES_DB|" .env; \
        $(call print_success,PostgreSQL credentials generated and saved to .env); \
        echo -e "$(FONT_CYAN)Generated credentials:$(FONT_RESET)"; \
        echo -e "  User: $$POSTGRES_USER"; \
        echo -e "  Password: $$POSTGRES_PASS"; \
        echo -e "  Database: $$POSTGRES_DB"; \
    fi
endef

define generate_agent_postgres_credentials
    $(call use_unified_credentials_for_agent); \
    $(call extract_postgres_credentials_from_env); \
    if [ -z "$$POSTGRES_USER" ]; then \
        $(call print_status,Generating secure Agent PostgreSQL credentials...); \
        POSTGRES_USER=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
        POSTGRES_PASS=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
        POSTGRES_DB="hive_agent"; \
        $(call print_success,Agent PostgreSQL credentials generated and will be saved to docker/agent/.env); \
        echo -e "$(FONT_CYAN)Generated agent credentials:$(FONT_RESET)"; \
        echo -e "  User: $$POSTGRES_USER"; \
        echo -e "  Password: $$POSTGRES_PASS"; \
        echo -e "  Database: $$POSTGRES_DB"; \
    fi
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
        mkdir -p ./data/postgres; \
        chmod -R 755 ./data/postgres; \
        chown -R $${POSTGRES_UID}:$${POSTGRES_GID} ./data/postgres 2>/dev/null || sudo chown -R $$USER:$$USER ./data/postgres; \
        echo -e "$(FONT_CYAN)📋 Creating Docker environment file for compose...$(FONT_RESET)"; \
        mkdir -p docker/main; \
        echo "POSTGRES_USER=$$POSTGRES_USER" > docker/main/.env; \
        echo "POSTGRES_PASSWORD=$$POSTGRES_PASSWORD" >> docker/main/.env; \
        echo "POSTGRES_DB=$$POSTGRES_DB" >> docker/main/.env; \
        echo "POSTGRES_UID=$$POSTGRES_UID" >> docker/main/.env; \
        echo "POSTGRES_GID=$$POSTGRES_GID" >> docker/main/.env; \
        echo "HIVE_API_PORT=$$(grep '^HIVE_API_PORT=' .env | cut -d'=' -f2 | head -1 || echo '8886')" >> docker/main/.env; \
        $(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d postgres; \
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
    $(call print_status,Creating agent environment from .env.example...); \
    mkdir -p docker/agent; \
    cp .env.example docker/agent/.env; \
    sed -i 's|HIVE_API_PORT=8886|HIVE_API_PORT=38886|' docker/agent/.env; \
    sed -i 's|localhost:5532/hive|localhost:35532/hive_agent|' docker/agent/.env; \
    sed -i 's|http://localhost:8886|http://localhost:38886|' docker/agent/.env; \
    $(call print_success,Agent environment created from unified template)
endef

define setup_agent_postgres
    $(call check_docker); \
    $(call generate_agent_postgres_credentials); \
    echo -e "$(FONT_CYAN)🐳 Starting Agent PostgreSQL container...$(FONT_RESET)"; \
    DB_URL=$$(grep '^HIVE_DATABASE_URL=' docker/agent/.env | cut -d'=' -f2-); \
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
    echo -e "$(FONT_CYAN)📋 Updating Docker agent environment with secure credentials...$(FONT_RESET)"; \
    sed -i "s/POSTGRES_USER=.*/POSTGRES_USER=$$POSTGRES_USER/" docker/agent/.env; \
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$$POSTGRES_PASSWORD/" docker/agent/.env; \
    sed -i "s/POSTGRES_DB=.*/POSTGRES_DB=$$POSTGRES_DB/" docker/agent/.env; \
    $(DOCKER_COMPOSE) -f docker/agent/docker-compose.yml up -d postgres-agent; \
    $(call print_success,Agent PostgreSQL container started on port 35532!)
endef

define cleanup_agent_environment
    $(call print_status,Cleaning up existing agent environment...); \
    $(DOCKER_COMPOSE) -f docker/agent/docker-compose.yml down 2>/dev/null || true; \
    docker container rm hive-agent-dev-server hive-postgres-agent 2>/dev/null || true; \
    rm -f logs/agent-server.pid logs/agent-server.log 2>/dev/null || true; \
    rm -rf ./data/postgres-agent 2>/dev/null || true; \
    rm -f docker/agent/.env 2>/dev/null || true; \
    $(call print_success,Agent environment cleaned up)
endef

define start_agent_background
    $(call print_status,Starting agent server via Docker...); \
    $(DOCKER_COMPOSE) -f docker/agent/docker-compose.yml up -d agent-dev-server; \
    sleep 5; \
    if docker ps --filter "name=hive-agent-dev-server" --format "{{.Names}}" | grep -q hive-agent-dev-server; then \
        $(call print_success,Agent server started via Docker); \
        echo -e "$(FONT_CYAN)🌐 Agent API: http://localhost:$(AGENT_PORT)$(FONT_RESET)"; \
        echo -e "$(FONT_CYAN)📋 Logs: make agent-logs$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)--- Startup logs ---$(FONT_RESET)"; \
        docker logs hive-agent-dev-server 2>/dev/null | head -20 || echo "No logs yet"; \
    else \
        $(call print_error,Failed to start agent server); \
        echo -e "$(FONT_YELLOW)Check logs: docker logs hive-agent-dev-server$(FONT_RESET)"; \
        exit 1; \
    fi
endef

define stop_agent_background
    if docker ps --filter "name=hive-agent-dev-server" --format "{{.Names}}" | grep -q hive-agent-dev-server; then \
        $(call print_status,Stopping agent server via Docker...); \
        $(DOCKER_COMPOSE) -f docker/agent/docker-compose.yml stop agent-dev-server; \
        $(call print_success,Agent server stopped); \
    else \
        $(call print_warning,Agent server not running); \
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
	@echo -e "  $(FONT_PURPLE)uninstall-agent$(FONT_RESET) Remove agent environment (autonomous - no confirmation)"
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
	@echo -e "  $(FONT_PURPLE)uninstall$(FONT_RESET)       Complete uninstall - removes everything"
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
	@$(call sync_mcp_config_with_credentials)


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
			echo -e "$(FONT_CYAN)📋 Creating Docker environment file for compose...$(FONT_RESET)"; \
			mkdir -p docker/main; \
			echo "POSTGRES_USER=$$POSTGRES_USER" > docker/main/.env; \
			echo "POSTGRES_PASSWORD=$$POSTGRES_PASSWORD" >> docker/main/.env; \
			echo "POSTGRES_DB=$$POSTGRES_DB" >> docker/main/.env; \
			echo "POSTGRES_UID=$$POSTGRES_UID" >> docker/main/.env; \
			echo "POSTGRES_GID=$$POSTGRES_GID" >> docker/main/.env; \
			echo "HIVE_API_PORT=$$(grep '^HIVE_API_PORT=' .env | cut -d'=' -f2 | head -1 || echo '8886')" >> docker/main/.env; \
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
uninstall: ## 🗑️ Complete uninstall - removes everything
	@$(call print_status,Complete Automagik Hive Uninstall)
	@echo -e "$(FONT_YELLOW)This will remove ALL containers, images, volumes, data, and environment files$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)🐳 Stopping all services...$(FONT_RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down --remove-orphans 2>/dev/null || true
	@$(DOCKER_COMPOSE) -f docker/agent/docker-compose.yml down --remove-orphans 2>/dev/null || true
	@echo -e "$(FONT_CYAN)🗑️ Removing containers...$(FONT_RESET)"
	@docker container rm hive-agents hive-postgres hive-agents-agent hive-postgres-agent 2>/dev/null || true
	@echo -e "$(FONT_CYAN)🖼️ Removing Docker images...$(FONT_RESET)"
	@docker image rm automagik-hive-app 2>/dev/null || true
	@echo -e "$(FONT_CYAN)💾 Removing Docker volumes...$(FONT_RESET)"
	@docker volume rm automagik-hive_app_logs automagik-hive_app_data 2>/dev/null || true
	@docker volume rm automagik-hive_agent_app_logs automagik-hive_agent_app_data 2>/dev/null || true
	@echo -e "$(FONT_CYAN)📁 Removing files and data...$(FONT_RESET)"
	@rm -rf .venv/ data/ logs/ 2>/dev/null || true
	@$(call print_success,Complete uninstall finished)
	@echo -e "$(FONT_GREEN)✓ Everything removed: containers, images, volumes, data, venv$(FONT_RESET)"


# ===========================================
# 🤖 Agent Environment Commands
# ===========================================
.PHONY: install-agent
install-agent: ## 🤖 Silent agent environment setup (destructive reinstall)
	@$(call print_status,Setting up agent environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@if [ -f "docker/agent/.env" ] || docker ps --filter "name=hive-postgres-agent" --format "{{.Names}}" | grep -q hive-postgres-agent; then \
		$(call cleanup_agent_environment); \
	fi
	@$(call setup_agent_env)
	@$(call setup_agent_postgres)
	@$(call generate_agent_hive_api_key)
	@$(call sync_mcp_config_with_credentials)
	@$(call print_success,Agent environment ready!)
	@echo -e "$(FONT_CYAN)🌐 Agent API will be available at: http://localhost:$(AGENT_PORT)$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Start with: make agent$(FONT_RESET)"

.PHONY: agent
agent: ## 🤖 Start agent server in background (non-blocking)
	@if [ ! -f "docker/agent/.env" ]; then \
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
	@if docker ps --filter "name=hive-agent-dev-server" --format "{{.Names}}" | grep -q hive-agent-dev-server; then \
		echo -e "$(FONT_CYAN)=== Recent Agent Logs (last 50 lines) ====$(FONT_RESET)"; \
		docker logs --tail=50 hive-agent-dev-server; \
	else \
		echo -e "$(FONT_YELLOW)⚠️ Agent server not running$(FONT_RESET)"; \
		echo -e "$(FONT_GRAY)💡 Start agent server with 'make agent'$(FONT_RESET)"; \
	fi

.PHONY: uninstall-agent
uninstall-agent: ## 🗑️ Uninstall agent environment (autonomous - no confirmation)
	@$(call print_status,Uninstalling agent environment...)
	@echo -e "$(FONT_CYAN)🐳 Stopping agent services...$(FONT_RESET)"
	@$(DOCKER_COMPOSE) -f docker/agent/docker-compose.yml down --remove-orphans -v 2>/dev/null || true
	@echo -e "$(FONT_CYAN)🗑️ Removing agent containers and volumes...$(FONT_RESET)"
	@docker container rm hive-postgres-agent hive-agent-dev-server 2>/dev/null || true
	@docker volume rm hive_agent_app_logs hive_agent_app_data hive_agent_supervisor_logs 2>/dev/null || true
	@echo -e "$(FONT_CYAN)🔗 Removing agent network...$(FONT_RESET)"
	@docker network rm hive_agent_network 2>/dev/null || true
	@echo -e "$(FONT_CYAN)📁 Cleaning agent files...$(FONT_RESET)"
	@rm -rf ./data/postgres-agent docker/agent/.env 2>/dev/null || true
	@$(call print_success,Agent environment uninstalled!)

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
	@if docker ps --filter "name=hive-agent-dev-server" --format "{{.Names}}" | grep -q hive-agent-dev-server; then \
		echo ""; \
		echo -e "$(FONT_CYAN)Recent agent activity:$(FONT_RESET)"; \
		docker logs --tail=5 hive-agent-dev-server 2>/dev/null | sed 's/^/  /' || echo -e "$(FONT_GRAY)  No recent activity$(FONT_RESET)"; \
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
# 🔒 Pre-Commit Hook Management
# ===========================================
.PHONY: install-hooks
install-hooks: ## 🔒 Install pre-commit hooks for root-level file validation
	@$(call print_status,Installing pre-commit hooks...)
	@if [ ! -f "scripts/validate_root_files.py" ]; then \
		$(call print_error,Validation script not found: scripts/validate_root_files.py); \
		echo -e "$(FONT_YELLOW)💡 Make sure the pre-commit hook system is properly implemented$(FONT_RESET)"; \
		exit 1; \
	fi
	@if [ ! -f "scripts/pre-commit-hook.sh" ]; then \
		$(call print_error,Pre-commit hook script not found: scripts/pre-commit-hook.sh); \
		echo -e "$(FONT_YELLOW)💡 Make sure the pre-commit hook system is properly implemented$(FONT_RESET)"; \
		exit 1; \
	fi
	@mkdir -p .git/hooks
	@cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@$(call print_success,Pre-commit hooks installed successfully!)
	@echo -e "$(FONT_CYAN)🔍 Hook validates root-level file organization$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)💡 Test with: make test-hooks$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)🚨 Emergency bypass: git commit --no-verify$(FONT_RESET)"

.PHONY: uninstall-hooks
uninstall-hooks: ## 🗑️ Remove pre-commit hooks
	@$(call print_status,Removing pre-commit hooks...)
	@rm -f .git/hooks/pre-commit
	@rm -f .git/hooks/BYPASS_ROOT_VALIDATION
	@rm -f .git/hooks/validation_metrics.json
	@$(call print_success,Pre-commit hooks removed!)

.PHONY: bypass-hooks
bypass-hooks: ## ⚠️ Create bypass flag (emergency use only)
	@$(call print_warning,Creating bypass flag for emergency use...)
	@mkdir -p .git/hooks
	@echo "# Emergency bypass flag - validation temporarily disabled" > .git/hooks/BYPASS_ROOT_VALIDATION
	@echo "# Created: $$(date)" >> .git/hooks/BYPASS_ROOT_VALIDATION
	@echo "# Reason: Emergency bypass via Makefile" >> .git/hooks/BYPASS_ROOT_VALIDATION
	@echo '{"reason": "Emergency bypass via Makefile", "duration_hours": 1, "created_by": "'$$(git config user.name || echo "unknown")'", "created_at": "'$$(date -Iseconds)'", "expires_at": "'$$(date -Iseconds -d '+1 hour' 2>/dev/null || date -Iseconds -v+1H 2>/dev/null || echo "unknown")'"}' >> .git/hooks/BYPASS_ROOT_VALIDATION
	@echo -e "$(FONT_YELLOW)⚠️ BYPASS ACTIVE: Root-level file validation disabled for 1 hour$(FONT_RESET)"
	@echo -e "$(FONT_CYAN)🔄 Restore validation: make restore-hooks$(FONT_RESET)"

.PHONY: restore-hooks
restore-hooks: ## 🔄 Restore hook validation (remove bypass)
	@$(call print_status,Restoring hook validation...)
	@rm -f .git/hooks/BYPASS_ROOT_VALIDATION
	@$(call print_success,Hook validation restored!)
	@echo -e "$(FONT_CYAN)✅ Pre-commit validation is now active$(FONT_RESET)"

.PHONY: test-hooks
test-hooks: ## 🧪 Test pre-commit hook validation system
	@$(call print_status,Testing pre-commit hook validation...)
	@if [ ! -f "scripts/validate_root_files.py" ]; then \
		$(call print_error,Validation script not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install-hooks' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@echo -e "$(FONT_CYAN)🧪 Running validation system test...$(FONT_RESET)"
	@if uv run python scripts/validate_root_files.py --test; then \
		$(call print_success,Pre-commit hook validation system is working correctly!); \
	else \
		$(call print_error,Pre-commit hook validation test failed); \
		echo -e "$(FONT_YELLOW)💡 Check the validation system implementation$(FONT_RESET)"; \
		exit 1; \
	fi
	@echo -e "$(FONT_CYAN)📊 Checking hook installation...$(FONT_RESET)"
	@if [ -f ".git/hooks/pre-commit" ]; then \
		echo -e "$(FONT_GREEN)✅ Pre-commit hook installed$(FONT_RESET)"; \
	else \
		echo -e "$(FONT_YELLOW)⚠️ Pre-commit hook not installed - run 'make install-hooks'$(FONT_RESET)"; \
	fi
	@if [ -f ".git/hooks/BYPASS_ROOT_VALIDATION" ]; then \
		echo -e "$(FONT_YELLOW)⚠️ Bypass flag active - validation will be skipped$(FONT_RESET)"; \
	else \
		echo -e "$(FONT_GREEN)✅ Validation active (no bypass flag)$(FONT_RESET)"; \
	fi

.PHONY: hook-status
hook-status: ## 📊 Show pre-commit hook status and metrics
	@$(call print_status,Pre-Commit Hook Status)
	@echo ""
	@echo -e "$(FONT_PURPLE)┌─────────────────────────┬──────────────────────────────┐$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)│ Hook Component          │ Status                       │$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)├─────────────────────────┼──────────────────────────────┤$(FONT_RESET)"
	@if [ -f ".git/hooks/pre-commit" ]; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Pre-commit hook" "Installed and active"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Pre-commit hook" "Not installed"; \
	fi
	@if [ -f "scripts/validate_root_files.py" ]; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Validation script" "Available"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_RED)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Validation script" "Missing"; \
	fi
	@if [ -f ".git/hooks/BYPASS_ROOT_VALIDATION" ]; then \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_YELLOW)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Bypass flag" "Active (validation disabled)"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GREEN)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Bypass flag" "Not active"; \
	fi
	@if [ -f ".git/hooks/validation_metrics.json" ]; then \
		METRICS_COUNT=$$(wc -l < .git/hooks/validation_metrics.json 2>/dev/null || echo "0"); \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_CYAN)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Validation metrics" "$$METRICS_COUNT records collected"; \
	else \
		printf "$(FONT_PURPLE)│$(FONT_RESET) %-23s $(FONT_PURPLE)│$(FONT_RESET) $(FONT_GRAY)%-28s$(FONT_RESET) $(FONT_PURPLE)│$(FONT_RESET)\n" \
			"Validation metrics" "No data collected yet"; \
	fi
	@echo -e "$(FONT_PURPLE)└─────────────────────────┴──────────────────────────────┘$(FONT_RESET)"
	@if [ -f ".git/hooks/BYPASS_ROOT_VALIDATION" ]; then \
		echo ""; \
		echo -e "$(FONT_YELLOW)⚠️ BYPASS INFORMATION:$(FONT_RESET)"; \
		if command -v python3 >/dev/null 2>&1; then \
			python3 -c "import json; exec('try:\n    with open(\".git/hooks/BYPASS_ROOT_VALIDATION\", \"r\") as f: content = f.read()\n    lines = content.split(\"\\n\")\n    for i, line in enumerate(lines):\n        if line.strip() and not line.startswith(\"#\"):\n            data = json.loads(\"\\n\".join(lines[i:]))\n            print(f\"   Reason: {data.get(\\\"reason\\\", \\\"No reason provided\\\")}\")\n            print(f\"   Created by: {data.get(\\\"created_by\\\", \\\"unknown\\\")}\")\n            print(f\"   Expires: {data.get(\\\"expires_at\\\", \\\"unknown\\\")}\")\n            break\nexcept: print(\"   Unable to read bypass information\")')" 2>/dev/null || echo "   Unable to read bypass information"; \
		fi; \
	fi

# ===========================================
# 🚀 Release & Publishing (Alpha)
# ===========================================
.PHONY: bump
bump: ## 🏷️ Bump alpha version and prepare for release
	@$(call print_status,Bumping alpha version...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	if echo "$$CURRENT_VERSION" | grep -q "a[0-9]*$$"; then \
		ALPHA_NUM=$$(echo "$$CURRENT_VERSION" | grep -o "a[0-9]*$$" | sed 's/a//'); \
		NEW_ALPHA_NUM=$$((ALPHA_NUM + 1)); \
		BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/a[0-9]*$$//'); \
		NEW_VERSION="$${BASE_VERSION}a$${NEW_ALPHA_NUM}"; \
	else \
		$(call print_error,Current version is not an alpha version: $$CURRENT_VERSION); \
		echo -e "$(FONT_YELLOW)💡 Only alpha versions can be bumped with this command$(FONT_RESET)"; \
		exit 1; \
	fi; \
	$(call print_status,Updating version from $$CURRENT_VERSION to $$NEW_VERSION); \
	sed -i "s/^version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	$(call print_success,Version bumped to $$NEW_VERSION); \
	echo -e "$(FONT_CYAN)💡 Next: make publish$(FONT_RESET)"

.PHONY: publish
publish: ## 📦 Build and publish alpha release to PyPI
	@$(call print_status,Publishing alpha release...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	if ! echo "$$CURRENT_VERSION" | grep -q "a[0-9]*$$"; then \
		$(call print_error,Not an alpha version: $$CURRENT_VERSION); \
		echo -e "$(FONT_YELLOW)💡 Only alpha versions can be published with this command$(FONT_RESET)"; \
		exit 1; \
	fi; \
	$(call print_status,Building package for version $$CURRENT_VERSION); \
	rm -rf dist/ build/ *.egg-info/; \
	if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		$(call print_error,uv not found - required for building); \
		exit 1; \
	fi; \
	$(call print_status,Committing version bump...); \
	git add pyproject.toml; \
	git commit -m "bump: alpha version $$CURRENT_VERSION" \
		-m "🏷️ ALPHA RELEASE PREPARATION:" \
		-m "- Bumped version to $$CURRENT_VERSION" \
		-m "- Ready for PyPI publication via 'make publish'" \
		-m "- UVX testing enabled with: uvx automagik-hive@$$CURRENT_VERSION" \
		-m "" \
		-m "🚀 TESTING COMMAND:" \
		-m "uvx automagik-hive@$$CURRENT_VERSION --version" \
		--trailer "Co-Authored-By: Automagik Genie <genie@namastex.ai>"; \
	$(call print_status,Creating and pushing git tag...); \
	git tag "v$$CURRENT_VERSION" -m "Alpha release v$$CURRENT_VERSION"; \
	git push origin dev; \
	git push origin "v$$CURRENT_VERSION"; \
	$(call print_status,Publishing to PyPI...); \
	if [ -f ".env" ]; then \
		PYPI_USERNAME=$$(grep '^PYPI_USERNAME=' .env | cut -d'=' -f2 | tr -d ' '); \
		PYPI_TOKEN=$$(grep '^PYPI_API_KEY=' .env | cut -d'=' -f2 | tr -d ' '); \
		if [ -n "$$PYPI_USERNAME" ] && [ -n "$$PYPI_TOKEN" ] && [ "$$PYPI_TOKEN" != "your-pypi-api-token-here" ]; then \
			$(call print_status,Using PyPI credentials from .env file...); \
			export TWINE_USERNAME="$$PYPI_USERNAME"; \
			export TWINE_PASSWORD="$$PYPI_TOKEN"; \
		else \
			$(call print_warning,PyPI credentials not found in .env - will prompt for input); \
		fi; \
	else \
		$(call print_warning,.env file not found - will prompt for PyPI credentials); \
	fi; \
	if command -v twine >/dev/null 2>&1; then \
		twine upload dist/*; \
	else \
		$(call print_warning,twine not found - installing...); \
		uv add --dev twine; \
		uv run twine upload dist/*; \
	fi; \
	$(call print_success,Alpha release $$CURRENT_VERSION published!); \
	echo -e "$(FONT_CYAN)🚀 Test with: uvx automagik-hive@$$CURRENT_VERSION --version$(FONT_RESET)"; \
	echo -e "$(FONT_CYAN)🧪 UVX Genie commands: uvx automagik-hive@$$CURRENT_VERSION --genie-serve$(FONT_RESET)"; \
	echo -e "$(FONT_YELLOW)💡 Wait 5-10 minutes for PyPI propagation$(FONT_RESET)"

# ===========================================
# 🧹 Phony Targets  
# ===========================================
.PHONY: help install install-local dev prod stop status logs logs-live health clean test uninstall install-agent uninstall-agent agent agent-stop agent-restart agent-logs agent-status install-hooks uninstall-hooks bypass-hooks restore-hooks test-hooks hook-status bump publish
# ===========================================
# 🔑 UNIFIED CREDENTIAL MANAGEMENT SYSTEM
# ===========================================

# Extract PostgreSQL credentials from main .env file
define extract_postgres_credentials_from_env
    if [ -f ".env" ] && grep -q "^HIVE_DATABASE_URL=" .env; then \
        EXISTING_URL=$$(grep "^HIVE_DATABASE_URL=" .env | cut -d'=' -f2); \
        if echo "$$EXISTING_URL" | grep -q "postgresql+psycopg://"; then \
            POSTGRES_USER=$$(echo "$$EXISTING_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p'); \
            POSTGRES_PASS=$$(echo "$$EXISTING_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p'); \
            POSTGRES_DB=$$(echo "$$EXISTING_URL" | sed -n 's|.*/\([^?]*\).*|\1|p'); \
            POSTGRES_HOST=$$(echo "$$EXISTING_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p'); \
            POSTGRES_PORT=$$(echo "$$EXISTING_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p'); \
        fi; \
    fi
endef

# Extract API key from main .env file  
define extract_hive_api_key_from_env
    if [ -f ".env" ] && grep -q "^HIVE_API_KEY=" .env; then \
        HIVE_API_KEY=$$(grep "^HIVE_API_KEY=" .env | cut -d'=' -f2); \
    fi
endef


# Use unified credentials from main .env for agent (shared user/pass, different port/db)
define use_unified_credentials_for_agent
    $(call extract_postgres_credentials_from_env); \
    if [ -n "$$POSTGRES_USER" ] && [ -n "$$POSTGRES_PASS" ]; then \
        $(call print_status,Using unified credentials from main .env for agent...); \
        sed -i "s|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@localhost:35532/hive_agent|" docker/agent/.env; \
        echo -e "$(FONT_CYAN)Unified agent credentials:$(FONT_RESET)"; \
        echo -e "  User: $$POSTGRES_USER (shared)"; \
        echo -e "  Password: $$POSTGRES_PASS (shared)"; \
        echo -e "  Database: hive_agent"; \
        echo -e "  Port: 35532 (agent-specific)"; \
    fi
endef

# Use unified API key from main .env for agent  
define use_unified_api_key_for_agent
    $(call extract_hive_api_key_from_env); \
    if [ -n "$$HIVE_API_KEY" ]; then \
        $(call print_status,Using unified API key from main .env for agent...); \
        sed -i "s|^HIVE_API_KEY=.*|HIVE_API_KEY=$$HIVE_API_KEY|" docker/agent/.env; \
        echo -e "$(FONT_CYAN)Unified agent API key:$(FONT_RESET)"; \
        echo -e "  API Key: $$HIVE_API_KEY (shared)"; \
    fi
endef

# Generate MCP configuration with current credentials
define sync_mcp_config_with_credentials
    $(call extract_postgres_credentials_from_env); \
    $(call extract_hive_api_key_from_env); \
    if [ -n "$$POSTGRES_USER" ] && [ -n "$$POSTGRES_PASS" ] && [ -n "$$HIVE_API_KEY" ]; then \
        $(call print_status,Updating .mcp.json with current credentials...); \
        sed -i "s|postgresql+psycopg://[^@]*@|postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@|g" .mcp.json; \
        sed -i "s|\"HIVE_API_KEY\": \"[^\"]*\"|\"HIVE_API_KEY\": \"$$HIVE_API_KEY\"|g" .mcp.json; \
        $(call print_success,.mcp.json updated with current credentials); \
    else \
        $(call print_warning,Could not update .mcp.json - missing credentials); \
    fi
endef

