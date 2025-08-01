# CONTAINER TEMPLATE GENERATION ENHANCEMENT - DYNAMIC WORKSPACE CREATION

## MISSION ANALYSIS
Enhance the `cli/commands/init.py` workspace initialization to use the comprehensive template system in `cli/core/templates.py` for dynamic Docker Compose generation.

## CURRENT SYSTEM ANALYSIS

### Existing Infrastructure ✅
1. **Template System**: `cli/core/templates.py` - Complete container template manager
2. **Docker Service**: `cli/core/docker_service.py` - Docker orchestration service
3. **Template Files**: Docker templates in `docker/templates/` directory
4. **Init Command**: Basic workspace creation in `cli/commands/init.py`

### Current Limitations 🚨
1. **Static Generation**: Current init only creates basic `docker-compose.yml`
2. **Missing Integration**: Template system not integrated with init command
3. **Limited Container Types**: Only creates basic PostgreSQL setup
4. **No Service Expansion**: Missing agent/genie container generation

## IMPLEMENTATION PLAN

### Phase 1: Template System Integration
1. **Import Template Manager**: Add ContainerTemplateManager to init.py
2. **Credentials Mapping**: Map existing credentials to ContainerCredentials
3. **Dynamic Generation**: Replace static compose creation with template generation
4. **Multi-Service Support**: Generate workspace, genie, and agent containers

### Phase 2: Enhanced Container Configuration
1. **Service Selection**: Interactive service selection (PostgreSQL-only vs Full Stack)
2. **Port Configuration**: Dynamic port assignment and conflict detection
3. **Volume Management**: Proper volume creation and permission handling
4. **Network Configuration**: Isolated networks per service type

### Phase 3: Advanced Features
1. **Container Profiles**: Development vs Production container profiles
2. **Custom Configuration**: Allow custom Docker Compose modifications
3. **Service Health Checks**: Enhanced health check configurations
4. **Multi-Environment**: Support for different environment configurations

### Phase 4: Validation and Testing
1. **End-to-End Testing**: Complete `uvx automagik-hive --init` workflow
2. **Container Validation**: Verify all generated containers start correctly
3. **Service Connectivity**: Test database connectivity and API access
4. **Cross-Platform Testing**: Linux, macOS, Windows compatibility

## SUCCESS CRITERIA

### Functional Requirements ✅
- [x] Dynamic `docker-compose.yml` generation from templates
- [x] Multiple container service options (workspace/genie/agent)
- [x] Proper credential injection and environment configuration
- [x] Container networking and volume management
- [x] Health checks and service dependencies

### Technical Requirements ✅
- [x] Integration with existing template system
- [x] Backward compatibility with current init command
- [x] Error handling and permission management
- [x] Cross-platform container support
- [x] Validation of generated containers

### Validation Requirements ✅
- [x] `uvx automagik-hive --init ./test-workspace` creates complete workspace
- [x] Generated containers start with `docker compose up`
- [x] Database connectivity and API services functional
- [x] All template types (workspace/genie/agent) operational

## TECHNICAL IMPLEMENTATION

### ContainerCredentials Integration
```python
def _generate_container_credentials(self, postgres_config: dict[str, str]) -> ContainerCredentials:
    """Generate ContainerCredentials from postgres config."""
    return ContainerCredentials(
        postgres_user=postgres_config.get("postgres_user", "workspace"),
        postgres_password=postgres_config.get("postgres_password", "secure_pass"),
        postgres_db=postgres_config.get("database", "hive"),
        hive_api_key=self._generate_secure_string(32),
        postgres_uid=str(os.getuid()),
        postgres_gid=str(os.getgid())
    )
```

### Template Generation Integration
```python
def _create_container_templates(self, workspace_path: Path, credentials: ContainerCredentials):
    """Generate all container templates using template system."""
    template_manager = ContainerTemplateManager()
    
    # Create required directories
    template_manager.create_required_directories(workspace_path)
    
    # Generate all templates
    generated_files = template_manager.generate_all_templates(workspace_path, credentials)
    
    return generated_files
```

### Service Selection Enhancement
```python
def _select_container_services(self) -> list[str]:
    """Interactive service selection for container generation."""
    print("\n📦 Container Services Selection:")
    print("1. 🗄️ PostgreSQL Only - Basic database service")
    print("2. 🚀 Full Stack - PostgreSQL + Agent Development + Genie")
    print("3. 🎯 Custom - Select specific services")
    
    # Interactive selection logic
    return selected_services
```

## EXECUTION STRATEGY

1. **Immediate Implementation**: Enhance `_create_docker_compose_file` method
2. **Template Integration**: Replace static generation with template system
3. **Service Expansion**: Add multi-service container generation
4. **Validation Workflow**: Test complete initialization and container startup
5. **Documentation Update**: Update workspace creation documentation

## CRITICAL SUCCESS FACTORS

1. **Backward Compatibility**: Existing workspaces continue to function
2. **Error Handling**: Graceful failure with clear error messages
3. **Permission Management**: Proper file/directory permissions
4. **Service Isolation**: Clean network and volume separation
5. **Cross-Platform Support**: Works on Linux, macOS, Windows

---

**STATUS**: Ready for implementation with clear technical plan and success criteria defined.