# AUTOMAGIK HIVE MODULAR DEPLOYMENT ARCHITECTURE

**The Future Command Structure & Unified Workflow**

---

## 🚀 **UNIFIED INSTALLATION & WORKSPACE WORKFLOW**

### **🎯 CORE WORKFLOW PHILOSOPHY:**

**The Golden Path:** `install → start → health → workspace`

1. **Install Infrastructure** - Get Docker services ready (agent/genie only)
2. **Start Services** - Boot Docker services in background, workspace locally  
3. **Health Check** - Verify all systems operational
4. **Workspace Setup** - Initialize or select workspace for development

---

## 🎛️ **SIMPLIFIED COMMAND STRUCTURE**

### **Core Commands:**
```bash
# INSTALLATION & SETUP
uvx automagik-hive --install [all|workspace|agent|genie]    # Install + start + health (default: all)
uvx automagik-hive --init [workspace-name]             # Initialize workspace only (prompts for name if not provided)

# WORKSPACE MANAGEMENT
uvx automagik-hive /path/to/workspace                  # Start workspace server (auto-detects dependencies)

# SERVICE MANAGEMENT  
uvx automagik-hive --start [all|workspace|agent|genie]      # Start services (default: all)
uvx automagik-hive --stop [all|workspace|agent|genie]       # Stop services (default: all)  
uvx automagik-hive --restart [all|workspace|agent|genie]    # Restart services (default: all)
uvx automagik-hive --status [all|workspace|agent|genie]     # Show service status (default: all)

# MAINTENANCE
uvx automagik-hive --health [all|workspace|agent|genie]     # Health check (default: all)
uvx automagik-hive --logs [all|workspace|agent|genie] [lines]  # Show logs (default: all, 50 lines)
uvx automagik-hive --uninstall [all|workspace|agent|genie]  # Remove components (default: all)
```

### **Examples:**
```bash
# Default behavior (everything)
uvx automagik-hive --install          # Install all + workflow
uvx automagik-hive --start            # Start all services
uvx automagik-hive --stop             # Stop all services
uvx automagik-hive --restart          # Restart all services

# Specific components
uvx automagik-hive --install workspace     # Start workspace uvx locally
uvx automagik-hive --install agent    # Start agent Docker services
uvx automagik-hive --install genie    # Start genie Docker services

uvx automagik-hive --start agent      # Start only agent services
uvx automagik-hive --logs genie 100   # Show only genie logs (100 lines)
uvx automagik-hive --health workspace      # Check only workspace health

# Workspace operations
uvx automagik-hive --init             # Prompts for workspace name, creates it
uvx automagik-hive --init my-project  # Creates "my-project" workspace directly
uvx automagik-hive ./my-project       # Start server from existing workspace
```

---

## 📋 **DETAILED UNIFIED WORKFLOW STEPS**

### **Step 1: Install Infrastructure**
```bash
uvx automagik-hive --install [component]
```
**Actions:**
1. 📦 Pull/build required Docker images (agent/genie only)
2. 🏗️ Create Docker networks and volumes  
3. ⚙️ Generate configuration files (.env, docker-compose.yml)
4. 🚀 **AUTO-START**: Launch Docker containers (agent/genie) or workspace uvx
5. ⏳ **AUTO-HEALTH**: Wait for services to be healthy
6. ✅ **AGENT-MODE**: Skip workspace prompts for agent/genie installs

### **Step 2: Health Verification (Automatic)**
```bash
# Happens automatically during --install, but can be run manually:
uvx automagik-hive --health
```
**Health Checks:**
- 🗄️ Database connectivity (ports 35532, 48532) 
- 🌐 API endpoints responding (ports 38886, 48886)
- 🏠 Workspace local uvx process
- 🔗 Service interdependencies working
- 📊 Resource usage validation

### **Step 3: Workspace Initialization (Interactive)**
```bash
# Happens automatically after health checks during --install
# Manual workspace initialization:
uvx automagik-hive --init [workspace-name]
```
**Interactive Flow (during --install):**
```
🧞 All services are healthy! 

Choose workspace option:
1. 📁 Initialize new workspace
2. 📂 Select existing workspace  
3. ⏭️  Skip workspace setup (use --init later)

Enter choice (1-3): 
```

### **Option 1: Initialize New Workspace**
```
📁 Initialize New Workspace
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workspace name: my-ai-project
📍 Location: ./my-ai-project

✅ Creating workspace structure...
✅ Configuring MCP integration...  
✅ Setting up agent templates...
✅ Workspace ready!

🚀 Next: cd my-ai-project
```

### **Option 2: Select Existing Workspace**
```
📂 Select Existing Workspace  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workspace path: ./my-existing-project

🔍 Checking workspace...
❌ Invalid workspace (missing .env or docker-compose.yml)

Would you like to initialize this folder as a workspace? (y/N): y
✅ Initializing existing folder as workspace...
✅ Workspace ready!
```

### **Option 3: Skip (Manual Later)**
```
⏭️ Skip Workspace Setup
━━━━━━━━━━━━━━━━━━━━━━━━
Services are running and ready.

Initialize workspace later with:
  uvx automagik-hive --init [workspace-name]
```

---

## 🏗️ **DOCKER COMPOSE PROFILES ARCHITECTURE**

### **Profile-Based Service Groups:**
```yaml
# docker-compose.unified.yml
services:
  # Agent Stack
  hive-agent-postgres:
    profiles: ["agent", "all"]
  hive-agent-api:
    profiles: ["agent", "all"]
    depends_on: ["hive-agent-postgres"]
    
  # Genie Stack
  hive-genie-postgres: 
    profiles: ["genie", "all"]
  hive-genie-api:
    profiles: ["genie", "all"] 
    depends_on: ["hive-genie-postgres"]
```

### **Profile Activation:**
```bash
uvx automagik-hive --install all         # Start agent + genie Docker services, then workspace uvx
uvx automagik-hive --install workspace # Start workspace uvx only
uvx automagik-hive --install agent     # Start agent Docker services only  
uvx automagik-hive --install genie     # Start genie Docker services only
```

---

## 🎯 **IMPLEMENTATION BLUEPRINT**

### **A. CLI Command Classes:**

```python
# cli/commands/unified_installer.py
class UnifiedInstaller:
    def install_with_workflow(self, component: str = "all") -> bool:
        """Execute full install → start → health → workspace workflow.
        
        Agent/genie installs skip workspace prompts for automation-friendly operation."""
        
    def health_check(self, component: str = "all") -> dict[str, bool]:
        """Health check for specified components."""
        
    def interactive_workspace_setup(self, component: str = "all") -> bool:
        """Interactive workspace initialization/selection.
        
        Skips prompts for agent/genie components (automation-friendly)."""
```

```python  
# cli/commands/service_manager.py
class ServiceManager:
    def start_services(self, component: str = "all") -> bool:
        """Start specified services."""
        
    def stop_services(self, component: str = "all") -> bool:
        """Stop specified services."""
        
    def restart_services(self, component: str = "all") -> bool:
        """Restart specified services."""
        
    def get_status(self, component: str = "all") -> dict[str, str]:
        """Get status of specified services."""
        
    def show_logs(self, component: str = "all", lines: int = 50) -> bool:
        """Show logs for specified services with configurable line count."""
        
    def uninstall(self, component: str = "all") -> bool:
        """Uninstall specified components."""
```

```python  
# cli/commands/workspace_manager.py
class WorkspaceManager:
    def prompt_workspace_choice(self) -> tuple[str, str]:
        """Return (action, path) - ('new', name) or ('existing', path) or ('skip', '')"""
        
    def initialize_workspace(self, name: str | None = None) -> bool:
        """Initialize workspace (prompts for name if None)."""
        
    def start_workspace_server(self, workspace_path: str) -> bool:
        """Start server from existing workspace.
        
        Auto-detects missing dependencies (genie, agent, database) and prompts to install."""
        
    def validate_existing_workspace(self, path: str) -> bool:
        """Check if path is valid workspace."""
        
    def initialize_existing_folder(self, path: str) -> bool:
        """Convert existing folder to workspace."""
```

### **B. Main CLI Logic:**

```python
# cli/main.py

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="automagik-hive")
    
    # Core commands with optional component parameter
    parser.add_argument("--install", nargs="?", const="all", 
                       choices=["all", "workspace", "agent", "genie"],
                       help="Install + start + health workflow (default: all)")
    
    parser.add_argument("--init", nargs="?", const=None,
                       help="Initialize workspace (prompts for name if not provided)")
    
    parser.add_argument("--start", nargs="?", const="all",
                       choices=["all", "workspace", "agent", "genie"], 
                       help="Start services (default: all)")
                       
    parser.add_argument("--stop", nargs="?", const="all",
                       choices=["all", "workspace", "agent", "genie"],
                       help="Stop services (default: all)")
                       
    parser.add_argument("--restart", nargs="?", const="all", 
                       choices=["all", "workspace", "agent", "genie"],
                       help="Restart services (default: all)")
                       
    parser.add_argument("--status", nargs="?", const="all",
                       choices=["all", "workspace", "agent", "genie"],
                       help="Show service status (default: all)")
                       
    parser.add_argument("--health", nargs="?", const="all",
                       choices=["all", "workspace", "agent", "genie"],
                       help="Health check services (default: all)")
                       
    parser.add_argument("--logs", nargs="*", default=None,
                       help="Show service logs: --logs [component] [lines] (default: all, 50 lines)")
                       
    parser.add_argument("--uninstall", nargs="?", const="all",
                       choices=["all", "workspace", "agent", "genie"],
                       help="Uninstall components (default: all)")
    
    # Positional argument for workspace path
    parser.add_argument("workspace", nargs="?", default=None,
                       help="Path to workspace directory (for starting workspace server)")
    
    return parser

def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    
    commands = LazyCommandLoader()
    
    # Handle workspace path (positional argument)
    if args.workspace and not any([args.install, args.init, args.start, args.stop, 
                                   args.restart, args.status, args.health, args.logs, args.uninstall]):
        # This is a workspace startup command: uvx automagik-hive /path/to/workspace
        # Auto-detects dependencies and prompts to install if missing
        success = commands.workspace_manager.start_workspace_server(args.workspace)
        return 0 if success else 1
    
    elif args.install:
        success = commands.unified_installer.install_with_workflow(args.install)
        return 0 if success else 1
        
    elif args.init:
        # --init command: uvx automagik-hive --init [workspace-name]
        success = commands.workspace_manager.initialize_workspace(args.init)
        return 0 if success else 1
        
    elif args.start:
        success = commands.service_manager.start_services(args.start)
        return 0 if success else 1
        
    elif args.stop:
        success = commands.service_manager.stop_services(args.stop)
        return 0 if success else 1
        
    elif args.restart:
        success = commands.service_manager.restart_services(args.restart)
        return 0 if success else 1
        
    elif args.status:
        status = commands.service_manager.get_status(args.status)
        return 0 if all(v == "healthy" for v in status.values()) else 1
        
    elif args.health:
        health = commands.unified_installer.health_check(args.health)
        return 0 if all(health.values()) else 1
        
    elif args.logs is not None:
        # Parse --logs [component] [lines]
        component = args.logs[0] if args.logs else "all"
        lines = int(args.logs[1]) if len(args.logs) > 1 and args.logs[1].isdigit() else 50
        success = commands.service_manager.show_logs(component, lines)
        return 0 if success else 1
        
    elif args.uninstall:
        success = commands.service_manager.uninstall(args.uninstall)
        return 0 if success else 1
        
    else:
        parser.print_help()
        return 0
```

---

## 🎯 **DEPLOYMENT SCENARIOS**

### **The Golden Path (Recommended):**
```bash
# ONE COMMAND - EVERYTHING AUTOMATED
uvx automagik-hive --install
```
**What happens:**
1. 📦 Installs agent + genie Docker services
2. 🚀 Starts Docker services in background, workspace uvx locally  
3. ⏳ Health checks everything
4. 💬 Prompts for workspace setup (all component only):
   ```
   🧞 All services healthy! Choose workspace:
   1. 📁 Initialize new workspace  
   2. 📂 Select existing workspace
   3. ⏭️  Skip (setup later)
   ```

### **Targeted Development:**
```bash  
# Workspace-only development
uvx automagik-hive --install workspace
# Start workspace uvx app with logs

# Agent development focus
uvx automagik-hive --install agent  
# Start agent Docker services in background (no prompts)

# Genie development focus
uvx automagik-hive --install genie
# Start genie Docker services in background (no prompts)
```

### **Service Management:**
```bash
# Start/stop specific components
uvx automagik-hive --start agent      # Start agent services only
uvx automagik-hive --stop genie       # Stop genie services only
uvx automagik-hive --restart workspace     # Restart workspace only

# Monitor specific components  
uvx automagik-hive --status agent     # Check agent status only
uvx automagik-hive --health genie     # Health check genie only
uvx automagik-hive --logs workspace 200   # Show workspace logs only (200 lines)
```

### **Workspace Scenarios:**

**Scenario 1: New Project**
```bash
uvx automagik-hive --install
# Choose: "1. Initialize new workspace"
# Enter: "my-ai-chatbot"  
# Result: ./my-ai-chatbot/ created and configured
```

**Scenario 2: Direct Workspace Creation**
```bash
uvx automagik-hive --init my-awesome-project
# Result: ./my-awesome-project/ created directly
```

**Scenario 3: Workspace Creation with Prompt**
```bash
uvx automagik-hive --init
# Prompts: "Workspace name: " 
# Enter: "my-project"
# Result: ./my-project/ created
```

**Scenario 4: Start Existing Workspace**
```bash
uvx automagik-hive ./my-existing-workspace
# Result: Auto-detects missing dependencies, prompts to install if needed, then starts server
```

---

## ✨ **BENEFITS**

### **User Experience:**
- **Ultra Simple**: Only 8 commands total, all with sensible defaults
- **One Command Setup**: `--install` does everything automatically
- **Smart Workspace Management**: Auto-detects and fixes invalid workspaces
- **Flexible Components**: Choose only what you need
- **Consistent Interface**: Same pattern for all operations

### **Technical Benefits:**
- **Profile-Based**: Docker Compose native profile system
- **Dependency Management**: Proper service startup ordering  
- **Health Checks**: Built-in service health monitoring
- **State Management**: Track installation progress
- **Resource Efficient**: Don't run unused services

### **Operational Benefits:**
- **Unified Workflow**: Single command from zero to running workspace
- **Component Control**: Start/stop individual service groups
- **Troubleshooting**: Easy logs and status per component
- **Clean Maintenance**: Simple uninstall per component

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Phase 1: Core Infrastructure**
1. ✅ Create unified docker-compose.yml with profiles
2. ✅ Implement UnifiedInstaller and ServiceManager classes  
3. ✅ Add component parameter support to all commands

### **Phase 2: Workflow Integration**
1. ✅ Implement install → start → health → workspace flow
2. ✅ Add interactive workspace selection logic
3. ✅ Create comprehensive health checking per component

### **Phase 3: Finalization**
1. ✅ Remove all complex command variations
2. ✅ Implement consistent component parameter handling
3. ✅ Test all component combinations (all, workspace, agent, genie)

This simplified architecture provides maximum power with minimum complexity - just 8 commands that handle everything! 🚀