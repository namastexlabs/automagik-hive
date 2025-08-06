# Health Checker Decomposition Analysis

## Current State: health_checker.py (1,272 lines)

### Core Components Analysis:
1. **Data Models** (lines 31-53):
   - HealthCheckResult dataclass
   - ResourceUsage dataclass

2. **Core Health Check Logic** (lines 55-625):
   - HealthChecker class initialization and core orchestration
   - database_connectivity_check()
   - api_endpoint_check() 
   - workspace_process_check()
   - service_interdependency_check()
   - resource_usage_check()
   - _get_services_for_component()
   - _check_service_with_retries()
   - _check_docker_network()
   - _check_agent_dependencies()
   - _check_genie_dependencies()
   - _check_cross_component_dependencies()

3. **Reporting & Display Logic** (lines 626-1272):
   - generate_health_report()
   - _display_health_report()
   - run_health_check_cli()
   - check_health() (CLI compatibility)
   - display_health() (CLI compatibility)
   - _get_status_icon()

## Decomposition Strategy:

### health.py (<350 lines) - Core Health Checking Logic
- Import statements
- Data models (HealthCheckResult, ResourceUsage)
- HealthChecker class core functionality:
  - __init__()
  - comprehensive_health_check()
  - database_connectivity_check()
  - api_endpoint_check()  
  - workspace_process_check()
  - service_interdependency_check()
  - resource_usage_check()
  - All private helper methods for actual health checking
- CLI compatibility wrapper methods

### health_report.py (<350 lines) - Health Reporting & Display
- Import statements (including from health import HealthCheckResult, HealthChecker)
- HealthReporter class with display functionality:
  - generate_health_report()
  - _display_health_report()
  - run_health_check_cli() 
  - display_health()
  - _get_status_icon()
  - All Rich console formatting logic

## Integration Points:
- health_report.py imports HealthCheckResult and core logic from health.py
- LazyCommandLoader will import from health.py (minimal change needed)
- CLI main.py continues to work with same interface through health.py
- health.py exposes a method to get reporter instance for display needs

## Import Updates Needed:
- cli/commands/__init__.py: Update import to use health.py
- cli/commands/installer.py: Update import to use health.py  
- Any other files importing health_checker