# Unified All-in-One Container Architecture - Detailed Design Document (DDD)

## Document Metadata
- **TSD Reference**: Docker Architecture Mismatch Analysis
- **Created By**: genie-dev-designer
- **Version**: 1.0
- **Architecture Pattern**: Clean Architecture + Unified Container Pattern
- **Creation Date**: 2025-08-01

## Executive Summary

Transform the current failing separate PostgreSQL + FastAPI container architecture into unified all-in-one containers for Genie and Agent services. This addresses the critical "Container hive-postgres-agent is unhealthy" issue by eliminating inter-container dependencies while maintaining the UVX master plan specification for T1.8 and T1.9.

## System Architecture

### Current Architecture Issues
```
FAILING: Separate Containers (Current)
├── app-agent (FastAPI container)
│   └── depends_on: postgres-agent (service_healthy) ❌ FAILS
└── postgres-agent (PostgreSQL container) ❌ UNHEALTHY

FAILING: Separate Containers (Current)  
├── genie-server (FastAPI container)
│   └── depends_on: genie-postgres (service_healthy) ❌ DEPENDENCY
└── genie-postgres (PostgreSQL container) ❌ SEPARATE
```

### Target Architecture (UVX Master Plan Compliant)
```
UNIFIED: All-in-One Containers (Target)
├── Genie All-in-One Container (Port 48886)
│   ├── Internal PostgreSQL (localhost:5432)
│   ├── FastAPI Application (0.0.0.0:48886)
│   ├── Supervisord Process Manager
│   └── Self-contained Health Checks ✅
│
├── Agent All-in-One Container (Port 38886)
│   ├── Internal PostgreSQL (localhost:5432)
│   ├── FastAPI Application (0.0.0.0:38886)
│   ├── Supervisord Process Manager
│   └── Self-contained Health Checks ✅
│
└── Main Workspace (Keep Current - Port 8886)
    ├── App Container (FastAPI)
    └── PostgreSQL Container (Separate) ✅ WORKING
```

## Clean Architecture Layers

### Presentation Layer
**Container API Endpoints**
- **Genie Container**: External port 48886 → Internal FastAPI
- **Agent Container**: External port 38886 → Internal FastAPI
- **Health Endpoints**: `/api/v1/health` for both containers
- **Container Management**: Docker Compose orchestration

### Application Layer
**Container Orchestration Services**
- **GenieContainerManager**: Unified Genie container lifecycle
- **AgentContainerManager**: Unified Agent container lifecycle
- **ProcessCoordinator**: Supervisord process management
- **HealthMonitor**: Internal service health validation

### Domain Layer
**Core Business Entities**
```python
# Domain Entities
class UnifiedContainer:
    container_id: str
    service_type: ContainerType  # GENIE | AGENT
    internal_database: PostgreSQLInstance
    application_service: FastAPIInstance
    process_manager: SupervisordManager
    health_status: HealthStatus

class ContainerType(Enum):
    GENIE = "genie"
    AGENT = "agent"
    WORKSPACE = "workspace"  # Keep separate containers

class ProcessManager:
    postgresql_process: Process
    fastapi_process: Process
    health_monitor: Process
    
class HealthStatus(Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
```

### Infrastructure Layer
**Container Implementation**
- **Docker Engine**: Container runtime management
- **Supervisord**: Multi-process coordination within containers
- **PostgreSQL**: Embedded database with pgvector
- **FastAPI**: Python web application framework
- **Volume Management**: Data persistence strategies

## Component Design

### Genie Unified Container Module
```
docker/genie/
├── Dockerfile.genie                    # Multi-stage unified build
├── supervisord.conf                    # Process management config
├── postgresql.conf                     # PostgreSQL optimization
├── pg_hba.conf                        # Database authentication
├── health-monitor.sh                  # Health check script
└── docker-compose.yml                # Container orchestration
```

### Agent Unified Container Module
```
docker/agent/
├── Dockerfile.agent                   # Multi-stage unified build
├── supervisord.conf                   # Process management config
├── postgresql.conf                    # PostgreSQL optimization
├── pg_hba.conf                       # Database authentication
├── health-monitor.sh                 # Health check script
└── docker-compose.yml               # Container orchestration
```

### Container Management Module
```
cli/infrastructure/
├── container_manager.py              # Base container management
├── genie_container.py                # Genie-specific operations
├── agent_container.py                # Agent-specific operations
└── health_monitor.py                 # Health checking service
```

## Data Architecture

### Database Schema Strategy
```sql
-- Genie Container Database: hive_genie
CREATE DATABASE hive_genie OWNER hive;
CREATE EXTENSION vector;

-- Genie-specific tables
CREATE TABLE genie_sessions (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    session_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Container Database: hive_agent  
CREATE DATABASE hive_agent OWNER agent;
CREATE EXTENSION vector;

-- Agent-specific tables
CREATE TABLE agent_deployments (
    id UUID PRIMARY KEY,
    agent_config JSONB,
    deployment_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Data Persistence Strategy
```yaml
# Volume Mounting Strategy
volumes:
  # Genie data persistence
  - ./data/postgres-genie:/var/lib/postgresql/data
  - ./logs/genie:/var/log/hive
  
  # Agent data persistence  
  - ./data/postgres-agent:/var/lib/postgresql/data
  - ./logs/agent:/var/log/hive
```

## Process Architecture

### Supervisord Process Hierarchy
```
Container Process Tree:
├── supervisord (PID 1)
│   ├── postgresql (Priority 100)
│   │   └── postgres: hive_genie/hive_agent database
│   ├── hive-service (Priority 200)
│   │   └── uvicorn: FastAPI application server
│   └── health-monitor (Priority 300)
│       └── Health check monitoring script
```

### Process Communication
```
Internal Container Communication:
┌─────────────────────────────────┐
│         Container Boundary       │
│  ┌─────────────┐  ┌─────────────┐│
│  │ PostgreSQL  │  │   FastAPI   ││
│  │ port: 5432  │◄─┤ port: 48886 ││
│  │ localhost   │  │ 0.0.0.0     ││
│  └─────────────┘  └─────────────┘│
│           ▲                      │
│  ┌─────────────┐                 │
│  │ Supervisord │                 │
│  │ Process Mgr │                 │
│  └─────────────┘                 │
└─────────────────────────────────┘
```

## Interface Definitions

### Container Manager Interface
```python
class IContainerManager(ABC):
    """Abstract base class for container management"""
    
    @abstractmethod
    async def start_container(self) -> ContainerStatus:
        """Start the unified container with all services"""
        pass
    
    @abstractmethod
    async def stop_container(self) -> ContainerStatus:
        """Stop the unified container gracefully"""
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check health of all internal services"""
        pass
    
    @abstractmethod
    async def get_logs(self, service: str = None) -> List[str]:
        """Retrieve logs from container services"""
        pass

class GenieContainerManager(IContainerManager):
    """Genie-specific unified container management"""
    
    async def start_container(self) -> ContainerStatus:
        """Start Genie container on port 48886"""
        return await self._docker_compose_up("genie")
    
    async def health_check(self) -> HealthStatus:
        """Check Genie PostgreSQL + FastAPI health"""
        postgres_ok = await self._check_postgres("hive_genie")
        api_ok = await self._check_api("http://localhost:48886/api/v1/health")
        return HealthStatus.HEALTHY if postgres_ok and api_ok else HealthStatus.UNHEALTHY

class AgentContainerManager(IContainerManager):
    """Agent-specific unified container management"""
    
    async def start_container(self) -> ContainerStatus:
        """Start Agent container on port 38886"""
        return await self._docker_compose_up("agent")
```

### Health Check Interface
```python
class IHealthMonitor(ABC):
    """Health monitoring interface for unified containers"""
    
    @abstractmethod
    async def check_postgresql_health(self, database: str) -> bool:
        """Verify PostgreSQL is running and accessible"""
        pass
    
    @abstractmethod
    async def check_api_health(self, endpoint: str) -> bool:
        """Verify FastAPI is responding to requests"""
        pass
    
    @abstractmethod
    async def get_service_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all managed services"""
        pass

class SupervisordHealthMonitor(IHealthMonitor):
    """Supervisord-based health monitoring implementation"""
    
    async def check_postgresql_health(self, database: str) -> bool:
        result = await run_command(["pg_isready", "-d", database])
        return result.returncode == 0
    
    async def check_api_health(self, endpoint: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    return response.status == 200
        except:
            return False
```

## Implementation Blueprint

### File Structure
```
automagik-hive/
├── docker/
│   ├── genie/
│   │   ├── Dockerfile.genie           # Unified Genie container
│   │   ├── supervisord.conf           # Process management
│   │   ├── postgresql.conf            # Database config
│   │   ├── pg_hba.conf               # Auth config
│   │   ├── health-monitor.sh         # Health script
│   │   └── docker-compose.yml        # Orchestration
│   ├── agent/
│   │   ├── Dockerfile.agent          # Unified Agent container
│   │   ├── supervisord.conf          # Process management
│   │   ├── postgresql.conf           # Database config
│   │   ├── pg_hba.conf              # Auth config
│   │   ├── health-monitor.sh        # Health script
│   │   └── docker-compose.yml       # Orchestration
│   └── templates/
│       ├── agent.yml                 # Updated unified template
│       └── genie.yml                 # Updated unified template
├── cli/
│   └── infrastructure/
│       ├── container_manager.py      # Base container management
│       ├── genie_container.py        # Genie operations
│       ├── agent_container.py        # Agent operations
│       └── health_monitor.py         # Health monitoring
└── lib/
    └── docker/
        ├── unified_container.py       # Unified container abstraction
        └── supervisord_manager.py     # Process management
```

### Key Implementation Files

#### Dockerfile.genie (Multi-stage Build)
```dockerfile
# Stage 1: Dependencies
FROM python:3.12-slim as builder
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: PostgreSQL Base
FROM agnohq/pgvector:16 as postgres-base

# Stage 3: Unified Container
FROM ubuntu:22.04 as genie-production
# Install PostgreSQL + Python + Supervisord
# Configure processes and permissions
# Copy application code and dependencies
EXPOSE 48886
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### supervisord.conf (Process Management)
```ini
[supervisord]
nodaemon=true
user=hive

[program:postgresql]
command=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data/pgdata
priority=100
autostart=true
autorestart=true

[program:hive-genie]
command=python -m uvicorn api.serve:app --host 0.0.0.0 --port 48886
directory=/app
priority=200
environment=HIVE_DATABASE_URL="postgresql+psycopg://hive:password@localhost:5432/hive_genie"
```

#### GenieContainerManager Implementation
```python
class GenieContainerManager:
    def __init__(self):
        self.compose_file = "docker/genie/docker-compose.yml"
        self.container_name = "hive-genie-unified"
        self.api_port = 48886
    
    async def start(self) -> bool:
        """Start unified Genie container"""
        try:
            await run_command([
                "docker-compose", "-f", self.compose_file, 
                "up", "-d", "--build"
            ])
            return await self._wait_for_health()
        except Exception as e:
            logger.error(f"Failed to start Genie container: {e}")
            return False
    
    async def _wait_for_health(self, timeout: int = 120) -> bool:
        """Wait for container to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await self.health_check():
                return True
            await asyncio.sleep(5)
        return False
```

## Quality Gates

### Clean Architecture Validation
- ✅ **Layer Separation**: Clear boundaries between presentation, application, domain, and infrastructure
- ✅ **Dependency Direction**: Outer layers depend on inner layers only
- ✅ **Domain Independence**: Core business logic isolated from external concerns
- ✅ **Interface Abstractions**: Abstract interfaces defined for all external dependencies

### Scalability Gate
- ✅ **Horizontal Scaling**: Each container can run independently on different hosts
- ✅ **Resource Isolation**: CPU and memory limits configurable per container
- ✅ **Network Isolation**: Dedicated networks prevent cross-container interference
- ✅ **Data Isolation**: Separate databases and persistent volumes per container

### Maintainability Gate
- ✅ **Modular Structure**: Clear separation of Genie and Agent containers
- ✅ **Configuration Management**: External config files for all services
- ✅ **Logging Strategy**: Comprehensive logging for debugging and monitoring
- ✅ **Health Monitoring**: Built-in health checks and status reporting

### Reliability Gate
- ✅ **Process Management**: Supervisord ensures service restart on failure
- ✅ **Health Checks**: Multi-level health validation (PostgreSQL + API)
- ✅ **Data Persistence**: Volume mounting ensures data survives container restarts
- ✅ **Graceful Shutdown**: Proper signal handling for clean shutdowns

### Integration Gate
- ✅ **UVX Compatibility**: Aligned with master plan T1.8 and T1.9 specifications
- ✅ **Existing API Compatibility**: Maintains existing FastAPI server patterns
- ✅ **CLI Integration**: Ready for UVX CLI command integration
- ✅ **Backward Compatibility**: Migration path from current separate containers

## Security Architecture

### Container Security
```yaml
# Non-root user execution
user: "1000:1000"

# File system permissions
volumes:
  - type: bind
    source: ./data/postgres-genie
    target: /var/lib/postgresql/data
    bind:
      create_host_path: true
      selinux: Z
```

### Database Security
```sql
-- Dedicated database users per container
CREATE USER hive WITH PASSWORD 'genie_secure_password';
CREATE USER agent WITH PASSWORD 'agent_secure_password';

-- Database access restrictions
GRANT ALL PRIVILEGES ON DATABASE hive_genie TO hive;
GRANT ALL PRIVILEGES ON DATABASE hive_agent TO agent;
```

### Network Security
```yaml
# Isolated networks per container
networks:
  genie_network:
    driver: bridge
    name: hive_genie_network
  agent_network:
    driver: bridge  
    name: hive_agent_network
```

## Performance Optimization

### Container Optimization
- **Multi-stage builds** reduce final image size
- **UV package manager** for fast dependency resolution
- **Layer caching** optimizes build times
- **Resource limits** prevent container resource exhaustion

### Database Optimization
```ini
# PostgreSQL performance tuning
shared_buffers = 128MB
effective_cache_size = 512MB
work_mem = 4MB
max_connections = 100
```

### Application Optimization
```python
# FastAPI optimization
app = FastAPI(
    workers=2,  # Multiple workers for better throughput
    timeout_keep_alive=30,
    timeout_graceful_shutdown=30
)
```

## Monitoring and Observability

### Health Check Strategy
```bash
# Multi-service health validation
#!/bin/bash
# Health check script combines PostgreSQL and API checks
pg_isready -h localhost -p 5432 -U hive -d hive_genie && \
curl -f http://localhost:48886/api/v1/health
```

### Logging Architecture
```
Container Logging Strategy:
├── /var/log/supervisor/         # Supervisord logs
├── /var/log/postgresql/         # PostgreSQL logs  
├── /var/log/hive/              # Application logs
└── Docker logs                 # Container stdout/stderr
```

### Monitoring Integration
```yaml
# Prometheus metrics exposure (future)
- "9090:9090"  # Metrics endpoint

# Health check endpoints
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:48886/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Deployment Strategy

### Development Deployment
```bash
# Local development with unified containers
docker-compose -f docker/genie/docker-compose.yml up -d
docker-compose -f docker/agent/docker-compose.yml up -d
```

### Production Deployment
```bash
# Production deployment with resource limits
docker-compose -f docker/genie/docker-compose.prod.yml up -d
# Includes CPU/memory limits, health checks, restart policies
```

### Container Updates
```bash
# Zero-downtime updates
docker-compose -f docker/genie/docker-compose.yml pull
docker-compose -f docker/genie/docker-compose.yml up -d --no-deps genie-all-in-one
```

## Testing Strategy

### Unit Testing
- Container manager classes with mocked Docker operations
- Health monitoring logic with simulated service states
- Configuration validation with various input scenarios

### Integration Testing
- End-to-end container startup and health validation
- PostgreSQL connectivity and pgvector functionality
- FastAPI endpoint accessibility and response validation

### Performance Testing
- Container startup time measurement
- API response time under load
- Database query performance validation
- Resource usage monitoring

## Migration Execution Plan

### Pre-Migration Checklist
- [ ] Backup existing PostgreSQL data
- [ ] Validate Docker and Docker Compose versions
- [ ] Test unified containers in development environment
- [ ] Prepare rollback procedures

### Migration Steps
1. **Build unified container images**
2. **Stop current failing containers**
3. **Deploy unified containers with existing data**
4. **Validate health checks and API endpoints**
5. **Update CLI commands and documentation**
6. **Monitor performance and stability**

### Post-Migration Validation
- [ ] All containers start without health check failures
- [ ] API endpoints respond correctly
- [ ] Database queries execute successfully
- [ ] Data persistence works across restarts
- [ ] Performance meets acceptable thresholds

## Success Metrics

### Functional Success Criteria
- ✅ **Container Startup**: Both Genie and Agent containers start without "unhealthy" errors
- ✅ **API Access**: All endpoints accessible on configured ports (48886, 38886)
- ✅ **Database Functionality**: PostgreSQL with pgvector working in both containers
- ✅ **Health Checks**: Self-contained health validation without external dependencies

### Performance Success Criteria
- ✅ **Startup Time**: Containers ready within 60 seconds
- ✅ **API Response**: Health endpoints respond within 1 second
- ✅ **Database Performance**: Query response times under 100ms
- ✅ **Resource Usage**: Memory usage under 512MB per container

### Operational Success Criteria
- ✅ **Reliability**: 99.9% uptime during testing period
- ✅ **Data Persistence**: No data loss during container restarts
- ✅ **Monitoring**: Comprehensive logs available for debugging
- ✅ **Maintainability**: Clear procedures for updates and configuration changes

## Conclusion

This Detailed Design Document provides a comprehensive blueprint for transforming the current failing separate container architecture into a unified all-in-one container system. The design addresses the root cause of the "Container hive-postgres-agent is unhealthy" issue by eliminating inter-container dependencies while maintaining full compliance with the UVX master plan specifications T1.8 and T1.9.

The unified architecture provides improved reliability, simplified operations, and better alignment with the intended system design, setting the foundation for successful agent development and Genie consultation services.

---

**Implementation Ready**: This DDD provides complete architectural specification and implementation blueprint for immediate development execution.