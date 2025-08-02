# Technical Specification Document: UVX Automagik Hive Implementation

## 1. OVERVIEW

**Objective**: Implement the correct UVX (uvx automagik-hive) architecture with **ONLY 2 core commands** that delivers an excellent developer experience through interactive workspace initialization and single-server workspace startup.

**Success Metrics**: 
- Perfect T2.2 Interactive Workspace Initialization (--init) with guided setup
- Seamless ./workspace-path startup with validation and error routing to --init
- <500ms startup time for ./workspace (UVX compatibility)
- Complete Docker auto-installation across Linux/macOS/Windows/WSL
- Single-server approach (NOT 3-container complexity)
- Template-based workspace creation with full Claude Code + MCP integration

**Key Insight**: Current codebase has 8-command CLI but UVX Master Plan requires SIMPLIFIED 2-command approach focused on developer experience excellence.

## 2. FUNCTIONAL REQUIREMENTS

### Core Features

#### **Command 1: Interactive Workspace Initialization (--init)**
- **Requirement 1**: Interactive workspace creation via `uvx automagik-hive --init`
  - **Acceptance Criteria**: 
    - Prompts for workspace path with default `./my-workspace`
    - Collects API keys (OpenAI, Anthropic, Google) with optional skip
    - Auto-detects Docker installation status
    - Offers Docker auto-installation if missing (Linux/macOS/Windows/WSL)
    - Provides PostgreSQL setup choice (Docker built-in vs external)
    - Creates complete workspace structure with templates
    - Generates secure credentials automatically
    - Sets up Claude Code integration with .claude/ folder
    - Configures MCP servers with .mcp.json
    - Success message with next steps

#### **Command 2: Workspace Startup (./path)**
- **Requirement 2**: Start existing workspace server via `uvx automagik-hive ./my-workspace`
  - **Acceptance Criteria**:
    - Validates workspace is properly initialized (.env, PostgreSQL, .claude/)
    - Tests database connection before starting server
    - Routes to --init with clear guidance if not initialized
    - Starts FastAPI server on port 8886
    - <500ms startup time (UVX compatibility requirement)
    - Clear error messages for all failure modes
    - Success confirmation with server status

### User Stories

- **As a developer**, I want to run `uvx automagik-hive --init` and be guided through workspace creation so that I have a fully functional AI development environment in under 5 minutes
- **As a developer**, I want to run `uvx automagik-hive ./my-project` and have the server start immediately so that I can begin development without configuration
- **As a developer**, I want Docker automatically installed if missing so that I don't need manual setup steps
- **As a developer**, I want complete Claude Code integration so that I have access to the full Genie agent ecosystem immediately
- **As a developer**, I want MCP servers pre-configured so that I can use external tools without manual setup

## 3. NON-FUNCTIONAL REQUIREMENTS

### Performance
- **Startup Time**: ./workspace command must start in <500ms (UVX environment compatibility)
- **Interactive Flow**: --init command should complete workspace creation in <5 minutes
- **Docker Operations**: Container startup should complete in <30 seconds

### Security
- **Credential Generation**: Cryptographically secure random generation for PostgreSQL credentials
- **API Key Storage**: Secure storage in workspace .env file with proper permissions
- **File Permissions**: Proper directory and file permissions on workspace creation
- **Input Validation**: All user inputs validated and sanitized

### Reliability  
- **Error Handling**: Graceful handling of all failure modes with actionable error messages
- **Recovery**: Ability to resume interrupted initialization
- **Validation**: Comprehensive dependency validation before operations
- **Cross-Platform**: Consistent behavior across Linux/macOS/Windows/WSL

### Usability
- **Clear Guidance**: Step-by-step instructions with progress indicators
- **Error Messages**: Actionable error messages that guide users to solutions
- **Defaults**: Sensible defaults that work for 90% of users
- **Flexibility**: Support for both Docker built-in and external PostgreSQL

## 4. TECHNICAL ARCHITECTURE

### System Components

#### **Command Router (cli/main.py)**
- **Responsibilities**: Route between --init and ./workspace commands ONLY
- **Interfaces**: Simplified argument parsing for 2-command structure
- **Integration**: Direct integration with InitService and WorkspaceService

#### **Interactive Initialization Service (cli/application/init_service.py)**
- **Responsibilities**: 
  - Interactive workspace path collection and validation
  - Docker installation detection and auto-installation
  - PostgreSQL setup choice and configuration
  - API key collection and validation
  - Template processing and workspace creation
  - Claude Code integration setup
  - MCP server configuration
- **Interfaces**: 
  ```python
  class InitService:
      def initialize_workspace(self, workspace_name: Optional[str]) -> bool
      def collect_workspace_config(self) -> WorkspaceConfig
      def setup_docker_environment(self) -> bool
      def setup_postgresql(self, config: DatabaseConfig) -> bool
      def generate_workspace_templates(self, path: Path, config: WorkspaceConfig) -> bool
  ```

#### **Workspace Startup Service (cli/application/workspace_service.py)**
- **Responsibilities**:
  - Workspace validation (.env, PostgreSQL connection, required files)
  - FastAPI server startup coordination
  - Error routing to --init when appropriate
  - Health checking and status reporting
- **Interfaces**:
  ```python
  class WorkspaceService:
      def start_workspace_server(self, workspace_path: str) -> bool
      def validate_workspace(self, path: Path) -> ValidationResult
      def test_database_connection(self, env_path: Path) -> bool
      def start_fastapi_server(self, workspace_path: Path) -> bool
  ```

#### **Docker Installation Manager (cli/infrastructure/docker_installer.py)**
- **Responsibilities**:
  - Cross-platform Docker detection
  - Automated Docker installation (Linux/macOS/Windows/WSL)
  - Docker daemon health checking
  - PostgreSQL image pre-pulling (agnohq/pgvector:16)
- **Interfaces**:
  ```python
  class DockerInstaller:
      def detect_docker_installation(self) -> DockerStatus
      def install_docker_for_platform(self, platform: Platform) -> bool
      def start_docker_daemon(self) -> bool
      def pull_required_images(self) -> bool
  ```

#### **Template Manager (cli/infrastructure/template_manager.py)**
- **Responsibilities**:
  - .env generation from .env.example template
  - .claude/ folder copying from package
  - .mcp.json generation with workspace-specific URLs
  - ai/ directory structure creation
  - Container configuration generation
- **Interfaces**:
  ```python
  class TemplateManager:
      def generate_env_file(self, path: Path, config: WorkspaceConfig) -> bool
      def copy_claude_integration(self, path: Path) -> bool
      def generate_mcp_config(self, path: Path, config: WorkspaceConfig) -> bool
      def create_ai_structure(self, path: Path) -> bool
  ```

### Data Models

```python
@dataclass
class WorkspaceConfig:
    """Configuration for workspace initialization."""
    path: Path
    api_keys: Dict[str, str]
    database_config: DatabaseConfig
    docker_enabled: bool
    external_postgresql: bool = False

@dataclass  
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str = "localhost"
    port: int = 5532
    database: str = "hive"
    username: str
    password: str
    external: bool = False

@dataclass
class ValidationResult:
    """Workspace validation result."""
    is_valid: bool
    missing_components: List[str]
    error_messages: List[str]
    can_auto_fix: bool
```

### API Contracts

#### **CLI Entry Points**
```python
# Primary entry point (simplified)
def main() -> int:
    """Main CLI with ONLY 2 commands: --init and ./workspace"""
    
# Interactive initialization
def initialize_workspace(workspace_name: Optional[str]) -> bool:
    """Interactive workspace creation with guided setup"""
    
# Workspace startup
def start_workspace_server(workspace_path: str) -> bool:
    """Start existing workspace with validation"""
```

#### **Configuration Generation**
```python
def generate_secure_credentials() -> Dict[str, str]:
    """Generate cryptographically secure PostgreSQL credentials"""
    
def process_env_template(template_path: Path, config: WorkspaceConfig) -> str:
    """Process .env.example template with user configuration"""
    
def generate_mcp_configuration(workspace_config: WorkspaceConfig) -> Dict:
    """Generate .mcp.json with workspace-specific server URLs"""
```

## 5. TEST-DRIVEN DEVELOPMENT STRATEGY

### Red-Green-Refactor Integration

#### **Red Phase: Failing Tests to Write First**
```python
def test_init_command_creates_complete_workspace():
    """Test --init creates all required workspace components"""
    # Should fail until full initialization implemented
    
def test_workspace_startup_validates_dependencies():
    """Test ./workspace validates before starting server"""
    # Should fail until validation logic implemented
    
def test_docker_auto_installation_cross_platform():
    """Test Docker installation across Linux/macOS/Windows"""
    # Should fail until cross-platform installer implemented
    
def test_template_generation_with_secure_credentials():
    """Test template processing generates secure credentials"""
    # Should fail until template manager implemented
```

#### **Green Phase: Minimal Implementation Approach**  
- Implement basic --init command that creates workspace directory
- Add basic ./workspace validation that checks for .env file
- Create simple Docker detection (without installation)
- Implement basic template copying (without processing)

#### **Refactor Phase: Quality Improvement Opportunities**
- Add comprehensive error handling and recovery
- Implement cross-platform Docker installation
- Add advanced template processing with credential generation
- Optimize startup performance for <500ms requirement

### Test Categories

#### **Unit Tests**
- **Template Processing**: Test .env generation, .claude/ copying, .mcp.json creation
- **Docker Management**: Test installation detection, container management
- **Credential Generation**: Test secure random generation, password strength
- **Validation Logic**: Test workspace validation, dependency checking

#### **Integration Tests**  
- **End-to-End Init**: Test complete --init flow from user input to workspace ready
- **Workspace Startup**: Test ./workspace from directory detection to server running
- **Cross-Platform**: Test Docker installation on Linux/macOS/Windows/WSL
- **Template Integration**: Test all templates work together correctly

#### **End-to-End Tests**
- **Complete User Journey**: Test full workflow from `uvx automagik-hive --init` to working development environment
- **Error Recovery**: Test graceful handling of interrupted initialization
- **Multi-Workspace**: Test multiple workspaces don't interfere with each other

## 6. IMPLEMENTATION PHASES

### Phase 1: Core Command Structure (2 weeks)
- **Deliverable 1**: Simplified CLI with ONLY --init and ./workspace commands
  - Remove existing 8-command complexity
  - Implement basic argument parsing for 2 commands
  - Create placeholder command handlers
- **Deliverable 2**: Basic workspace validation framework
  - Directory existence checking
  - .env file validation
  - Database connection testing

### Phase 2: Interactive Initialization (3 weeks)  
- **Deliverable 3**: Complete --init interactive flow
  - Workspace path collection with validation
  - API key collection with optional skip
  - Database setup choice (Docker vs external)
  - Progress indicators and user feedback
- **Deliverable 4**: Docker auto-installation system
  - Cross-platform Docker detection
  - Automated installation for Linux/macOS/Windows/WSL
  - Docker daemon health checking

### Phase 3: Template System Integration (2 weeks)
- **Deliverable 5**: Complete template processing system
  - .env generation from .env.example with secure credentials  
  - .claude/ folder copying from package
  - .mcp.json generation with workspace URLs
  - ai/ directory structure creation
- **Deliverable 6**: Claude Code + MCP integration
  - Pre-configured MCP servers (automagik-hive, postgres, automagik-forge)
  - Complete Genie agent ecosystem access
  - Cursor IDE auto-detection and setup

### Phase 4: Performance & Reliability (2 weeks)
- **Deliverable 7**: <500ms startup optimization
  - Lazy loading for workspace startup
  - Efficient dependency validation
  - Startup time monitoring and optimization
- **Deliverable 8**: Comprehensive error handling
  - Graceful failure recovery
  - Clear error messages with actionable guidance
  - Automatic routing to --init when appropriate

## 7. EDGE CASES & ERROR HANDLING

### Boundary Conditions

#### **Workspace Path Handling**
- **Edge case 1**: Path contains spaces or special characters
  - **Handling strategy**: Proper path quoting and validation
- **Edge case 2**: Path is too long for filesystem
  - **Handling strategy**: Length validation with clear error message
- **Edge case 3**: Parent directory doesn't exist  
  - **Handling strategy**: Recursive directory creation with user consent

#### **Docker Installation Scenarios**
- **Edge case 4**: Docker installed but daemon not running
  - **Handling strategy**: Attempt to start daemon, guide user if fails
- **Edge case 5**: Docker installation fails due to permissions
  - **Handling strategy**: Clear guidance on manual installation with sudo
- **Edge case 6**: WSL2 without Docker Desktop
  - **Handling strategy**: Specific WSL2 Docker installation guidance

### Error Scenarios

#### **Database Connection Failures**
- **Error scenario 1**: PostgreSQL container fails to start
  - **Recovery strategy**: Container recreation with different port if conflict
- **Error scenario 2**: External PostgreSQL connection fails
  - **Recovery strategy**: Connection retry with alternative settings
- **Error scenario 3**: pgvector extension missing
  - **Recovery strategy**: Automatic extension installation with fallback guidance

#### **Template Processing Failures**
- **Error scenario 4**: .env.example template missing from package
  - **Recovery strategy**: Embedded fallback template generation
- **Error scenario 5**: .claude/ folder corrupted or missing
  - **Recovery strategy**: Re-download or regenerate from embedded defaults
- **Error scenario 6**: Insufficient disk space during setup
  - **Recovery strategy**: Space checking with cleanup suggestions

## 8. ACCEPTANCE CRITERIA

### Definition of Done

#### **Interactive Initialization (--init)**
- [ ] Command prompts for workspace path with validation
- [ ] API key collection with optional skip functionality
- [ ] Docker installation detection and auto-installation
- [ ] PostgreSQL setup choice (Docker built-in vs external)
- [ ] Complete workspace structure creation
- [ ] Secure credential generation and .env creation
- [ ] .claude/ folder integration with full agent ecosystem
- [ ] .mcp.json configuration with pre-configured servers
- [ ] Clear success message with next steps
- [ ] Graceful error handling with actionable guidance

#### **Workspace Startup (./path)**
- [ ] Workspace validation before server startup
- [ ] Database connection testing with clear error messages
- [ ] FastAPI server startup on port 8886
- [ ] <500ms startup time (UVX compatibility)
- [ ] Automatic routing to --init when workspace not initialized
- [ ] Health checking and status reporting
- [ ] Cross-platform compatibility (Linux/macOS/Windows/WSL)

#### **Overall Architecture**
- [ ] ONLY 2 commands implemented (--init and ./workspace)
- [ ] Single-server approach (NOT 3-container complexity)
- [ ] Template-based workspace creation
- [ ] Complete Docker auto-installation support
- [ ] Full Claude Code integration
- [ ] Pre-configured MCP servers
- [ ] Comprehensive error handling and recovery
- [ ] Cross-platform Docker installation

### Validation Steps

#### **End-to-End Validation Process**
1. **Fresh Environment Test**: Test complete flow on clean system without Docker
2. **Cross-Platform Validation**: Test on Linux, macOS, Windows/WSL
3. **Error Recovery Testing**: Test interrupted initialization and recovery
4. **Performance Validation**: Verify <500ms startup time requirement
5. **Integration Testing**: Verify Claude Code + MCP integration works
6. **Docker Installation Testing**: Test auto-installation on each platform
7. **Template Processing Testing**: Verify all templates generate correctly
8. **Database Testing**: Test both Docker and external PostgreSQL options

#### **User Acceptance Testing Approach**
1. **Developer Experience Testing**: Have 5-10 developers test complete workflow
2. **Documentation Validation**: Ensure users can succeed with documentation alone
3. **Error Scenario Testing**: Test all identified error scenarios with users
4. **Performance Testing**: Validate startup times meet UVX requirements

#### **Production Readiness Validation**
1. **Security Review**: Validate secure credential generation and storage
2. **Reliability Testing**: Test failure modes and recovery mechanisms
3. **Compatibility Testing**: Validate UVX environment compatibility
4. **Integration Testing**: Test with existing Automagik Hive ecosystem

---

**Implementation Priority**: This specification focuses on the CORRECT UVX architecture with simplified 2-command approach, single-server design, and excellent developer experience through interactive initialization and template-based workspace creation. The current 8-command CLI complexity must be simplified to match the UVX Master Plan requirements for viral developer adoption.