# CLI Command Comparison: Current vs Proposed

## CURRENT STRUCTURE (What Exists Now)

### Core Commands (`--` style)
| Command | Parameters | Description |
|---------|------------|-------------|
| `--init [NAME]` | Optional workspace name | Initialize new workspace directory | ## OK, init without a name should initialize in the current . directory.
| `--serve [WORKSPACE]` | Optional workspace path (default: `.`) | Start production server using Docker | ## NO NEED FOR WORKSSPACE, SERVE ALREADY EXPECTES TO RUN THE CURRENT WORKSPACE.. 
| `--dev [WORKSPACE]` | Optional workspace path (default: `.`) | Start development server locally | ## NO NEED FOR WORKSSPACE,  ALREADY EXPECTES TO RUN THE CURRENT WORKSPACE.. 
| `--version` | None | Show version information | 
| `--stop [WORKSPACE]` | Optional workspace path | Stop production environment | ## NO NEED FOR WORKSSPACE,  ALREADY EXPECTES TO RUN THE CURRENT WORKSPACE.. 
| `--restart [WORKSPACE]` | Optional workspace path | Restart production environment | ## NO NEED FOR WORKSSPACE,  ALREADY EXPECTES TO RUN THE CURRENT WORKSPACE.. 
| `--status [WORKSPACE]` | Optional workspace path | Check production environment status | ## NO NEED FOR WORKSSPACE,  ALREADY EXPECTES TO RUN THE CURRENT WORKSPACE.. 
| `--logs [WORKSPACE]` | Optional workspace path + `--tail N` | Show production environment logs | ## NO NEED FOR WORKSSPACE, ALREADY EXPECTES TO RUN THE CURRENT WORKSPACE.. 

### Agent Commands (`--agent-` prefix) ## AGENT DOESNT HAVE WORKSPACE ITS A DOCKER  ONLY INSTANCE FOR THE  CODING AGENT TO TEST DURING  DEVELOPMENT...
| Command | Parameters | Description |
|---------|------------|-------------|
| `--agent-install [WORKSPACE]` | Optional workspace path | Install and start agent services (PostgreSQL on 35532, API on 38886) |
| `--agent-start [WORKSPACE]` | Optional workspace path | Start already installed agent services |
| `--agent-stop [WORKSPACE]` | Optional workspace path | Stop running agent services |
| `--agent-restart [WORKSPACE]` | Optional workspace path | Stop and restart agent services |
| `--agent-status [WORKSPACE]` | Optional workspace path | Check agent service status |
| `--agent-logs [WORKSPACE]` | Optional workspace path + `--tail N` | View agent service logs |
| `--agent-reset [WORKSPACE]` | Optional workspace path | Destroy all, reinstall, and start agent environment |

### Genie Commands (`--genie-` prefix) ## GENIE DOESNT HAVE WORKSPACE ITS A DOCKER  ONLY INSTANCE FOR GETTING HELP FROM GENIE DURING  DEVELOPMENT...
| Command | Parameters | Description |
|---------|------------|-------------|
| `--genie-install [WORKSPACE]` | Optional workspace path | Install and start genie services (PostgreSQL on 45532, API on 48886) |
| `--genie-start [WORKSPACE]` | Optional workspace path | Start already installed genie services |
| `--genie-stop [WORKSPACE]` | Optional workspace path | Stop running genie services |
| `--genie-restart [WORKSPACE]` | Optional workspace path | Stop and restart genie services |
| `--genie-status [WORKSPACE]` | Optional workspace path | Check genie service status |
| `--genie-logs [WORKSPACE]` | Optional workspace path + `--tail N` | View genie service logs |
| `--genie-reset [WORKSPACE]` | Optional workspace path | Destroy all, reinstall, and start genie environment |

### PostgreSQL Commands (`--postgres-` prefix) ## POSTGRES DOESNT HAVE WORKSPACE, THE MAIN POSTGRES IS USED BY WHATEVER WORKSPACE IS BEING WORKED ON. THERE WONT BE MULTIPLE WORKSPACES AT  THE SAME INSTANCE.
| Command | Parameters | Description |
|---------|------------|-------------|
| `--postgres-status [WORKSPACE]` | Optional workspace path | Check PostgreSQL service status |
| `--postgres-start [WORKSPACE]` | Optional workspace path | Start PostgreSQL service |
| `--postgres-stop [WORKSPACE]` | Optional workspace path | Stop PostgreSQL service |
| `--postgres-restart [WORKSPACE]` | Optional workspace path | Restart PostgreSQL service |
| `--postgres-logs [WORKSPACE]` | Optional workspace path + `--tail N` | Show PostgreSQL logs |
| `--postgres-health [WORKSPACE]` | Optional workspace path | Check PostgreSQL health and connectivity |

### Subcommands (direct command style - inconsistent!)
| Command | Parameters | Description |
|---------|------------|-------------|
| `install [WORKSPACE]` | Optional workspace path | Complete environment setup with .env generation and PostgreSQL | ## this has no workspace... install just installs the automagik-hive ,nothing related to t he workspace
| `uninstall [WORKSPACE]` | Optional workspace path | COMPLETE SYSTEM WIPE - removes all environments | ## this has no workspace... install just installs the automagik-hive ,nothing related to t he workspace
| `genie [ARGS...]` | Optional arguments to pass | Launch claude with GENIE.md as system prompt | ## which args?? detail whatts possible
| `dev [WORKSPACE]` | Optional workspace path | Start development server (alternative syntax) | ## duplicate from  --dev? i  only need dev... and again, no workspace

### Global Flags ## not so global.. not every  command is related to starting a server... or checking logs... --help is global, and should have speciallized help  per subsection like  hive genie --help  will  output help  from genie subcommand.
| Flag | Description |
|------|-------------|
| `--tail N` | Number of log lines to show (default: 50) |
| `--host HOST` | Host to bind server to (default: 0.0.0.0) |
| `--port PORT` | Port to bind server to (default: 8886) |
| `--help` | Show help message |

---

## PROPOSED NEW STRUCTURE (Clean Direct Commands)

### Program Name Change
- **OLD**: `automagik-hive`
- **NEW**: `hive` (shorter, cleaner)

### Direct Command Structure
```bash
hive <command> <subcommand> [options]
```

### Core Commands
| Command | Subcommands | Description |
|---------|------------|-------------|
| `hive init [NAME]` | None | Initialize new workspace |
| `hive serve [WORKSPACE]` | None | Start production server (Docker) |
| `hive dev [WORKSPACE]` | None | Start development server (local) |
| `hive install [WORKSPACE]` | None | Complete environment setup |
| `hive uninstall [WORKSPACE]` | None | Complete system wipe |
| `hive health` | None | System health check |

### Agent Commands
| Command | Description |
|---------|-------------|
| `hive agent install` | Install and start agent services |
| `hive agent start` | Start agent services |
| `hive agent stop` | Stop agent services |
| `hive agent restart` | Restart agent services |
| `hive agent status` | Check agent status |
| `hive agent logs [--tail N]` | View agent logs |
| `hive agent reset` | Reset agent environment |

### Genie Commands
| Command | Description |
|---------|-------------|
| `hive genie install` | Install and start genie services |
| `hive genie start` | Start genie services |
| `hive genie stop` | Stop genie services |
| `hive genie restart` | Restart genie services |
| `hive genie status` | Check genie status |
| `hive genie logs [--tail N]` | View genie logs |
| `hive genie reset` | Reset genie environment |
| `hive genie launch [ARGS]` | Launch claude with GENIE.md |

### PostgreSQL Commands
| Command | Description |
|---------|-------------|
| `hive postgres start` | Start PostgreSQL |
| `hive postgres stop` | Stop PostgreSQL |
| `hive postgres restart` | Restart PostgreSQL |
| `hive postgres status` | Check PostgreSQL status |
| `hive postgres logs [--tail N]` | View PostgreSQL logs |
| `hive postgres health` | Check PostgreSQL health |

### Production Commands
| Command | Description |
|---------|-------------|
| `hive production stop` | Stop production environment |
| `hive production restart` | Restart production environment |
| `hive production status` | Check production status |
| `hive production logs [--tail N]` | View production logs |

### Global Flags (Only Real Flags)
| Flag | Description |
|------|-------------|
| `--help, -h` | Show help message |
| `--version, -v` | Show version |
| `--verbose` | Verbose output |
| `--quiet` | Suppress output |

### Options (Per Command)
| Option | Used With | Description |
|--------|-----------|-------------|
| `--tail N` | Any `logs` command | Number of lines to show |
| `--host HOST` | `serve`, `dev` | Host to bind to |
| `--port PORT` | `serve`, `dev` | Port to bind to |
| `--workspace PATH` | Most commands | Workspace path override |

---

## KEY DIFFERENCES

### 1. Command Style
- **OLD**: Mix of `--command-style`, subcommands, and positional arguments
- **NEW**: Consistent direct command approach like git/docker

### 2. Program Name
- **OLD**: `automagik-hive` (long)
- **NEW**: `hive` (short, memorable)

### 3. No Aliases
- **OLD**: Would have had aliases like `a` for `agent`
- **NEW**: No aliases - explicit commands only

### 4. Consistency
- **OLD**: Inconsistent patterns (some use `--`, some don't)
- **NEW**: All commands follow same pattern

### 5. Workspace Handling
- **OLD**: Workspace as optional parameter everywhere (but ignored!)
- **NEW**: No workspace parameters - commands work where they should

### 6. Examples

**OLD Style (with fake workspace params):**
```bash
automagik-hive --agent-install /path  # path ignored!
automagik-hive --postgres-logs .      # path ignored!
automagik-hive --dev /workspace       # path ignored!
automagik-hive install .              # path ignored!
```

**NEW Style (honest and clean):**
```bash
hive agent install              # Docker containers
hive postgres logs --tail 100   # Single instance
hive dev                        # Current directory
hive install                    # System-wide
```

---

## WHAT EACH COMMAND DOES

### Agent Environment
- **install**: Sets up isolated agent development environment with PostgreSQL (port 35532) and API server (port 38886)
- **start/stop/restart**: Controls the agent services
- **status**: Shows if agent services are running
- **logs**: Shows agent service output for debugging
- **reset**: Complete teardown and fresh reinstall

### Genie Environment
- **install**: Sets up isolated genie environment with PostgreSQL (port 45532) and API server (port 48886)
- **start/stop/restart**: Controls the genie services
- **status**: Shows if genie services are running
- **logs**: Shows genie service output for debugging
- **reset**: Complete teardown and fresh reinstall
- **launch**: Opens Claude AI with GENIE.md as system prompt

### PostgreSQL
- **start/stop/restart**: Controls main PostgreSQL database
- **status**: Shows if PostgreSQL is running
- **health**: Tests database connectivity and health
- **logs**: Shows PostgreSQL output

### Production/Development
- **serve**: Runs production server using Docker
- **dev**: Runs development server locally with hot reload
- **install**: Sets up complete environment with .env file
- **uninstall**: Removes everything (dangerous!)

### Workspace
- **init**: Creates new workspace directory with boilerplate