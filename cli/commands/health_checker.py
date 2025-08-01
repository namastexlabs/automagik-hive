"""Comprehensive health checking system for Automagik Hive components.

Provides detailed health validation for:
- Database connectivity (agent: 35532, genie: 48532)
- API endpoint health (agent: 38886, genie: 48886)
- Workspace local uvx process validation
- Service interdependency validation
- Resource usage monitoring and validation
- Detailed health reports with actionable diagnostics
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil
import psycopg
import requests
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    service: str
    component: str
    status: str  # "healthy", "unhealthy", "warning", "unknown"
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    response_time_ms: float | None = None
    remediation: str | None = None


@dataclass
class ResourceUsage:
    """System resource usage metrics."""

    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_connections: int
    docker_containers: int


class HealthChecker:
    """Comprehensive health checking system for all Automagik Hive components."""

    def __init__(self) -> None:
        self.console = Console()
        self.timeout_seconds = 30
        self.retry_attempts = 3
        self.retry_delay = 5

        # Service configuration mapping
        self.service_config = {
            "agent": {
                "database_port": 35532,
                "api_port": 38886,
                "database_name": "hive_agent",
                "container_prefix": "hive-agent",
            },
            "genie": {
                "database_port": 48532,
                "api_port": 48886,
                "database_name": "hive_genie",
                "container_prefix": "hive-genie",
            },
        }

    def comprehensive_health_check(
        self, component: str = "all"
    ) -> dict[str, HealthCheckResult]:
        """Perform comprehensive health check for specified component.

        Args:
            component: Component to check ('all', 'workspace', 'agent', 'genie')

        Returns:
            Dict mapping service names to health check results
        """
        self.console.print(
            Panel.fit(
                f"🏥 [bold]Comprehensive Health Check[/bold]\n"
                f"Component: [cyan]{component}[/cyan]\n"
                f"Timeout: [yellow]{self.timeout_seconds}s[/yellow] | "
                f"Retries: [yellow]{self.retry_attempts}[/yellow]",
                border_style="blue",
            )
        )

        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Determine which services to check
            services_to_check = self._get_services_for_component(component)

            for service_name, check_config in services_to_check.items():
                task = progress.add_task(f"Checking {service_name}...", total=None)

                # Perform health check with retries
                result = self._check_service_with_retries(
                    service_name, check_config, progress, task
                )
                results[service_name] = result

                # Update progress based on result
                status_icon = self._get_status_icon(result.status)
                progress.update(
                    task, description=f"{status_icon} {service_name}: {result.message}"
                )

        # Display comprehensive results
        self._display_health_report(results, component)

        return results

    def database_connectivity_check(self, component: str) -> HealthCheckResult:
        """Check database connectivity for specified component.

        Args:
            component: Component to check ('agent' or 'genie')

        Returns:
            HealthCheckResult with database connectivity status
        """
        if component not in self.service_config:
            return HealthCheckResult(
                service=f"{component}-database",
                component=component,
                status="unknown",
                message=f"Unknown component: {component}",
                remediation="Use 'agent' or 'genie' as component",
            )

        config = self.service_config[component]
        port = config["database_port"]
        db_name = config["database_name"]

        start_time = time.time()

        try:
            # Test database connection
            connection = psycopg.connect(
                host="localhost",
                port=port,
                dbname=db_name,
                user="hive",
                password="hive",
                connect_timeout=self.timeout_seconds,
            )

            # Test basic query
            cursor = connection.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            # Check database size and connections
            cursor.execute("""
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as size,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as connections
            """)
            db_stats = cursor.fetchone()

            cursor.close()
            connection.close()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service=f"{component}-database",
                component=component,
                status="healthy",
                message=f"Connected successfully (port {port})",
                details={
                    "port": port,
                    "database": db_name,
                    "version": version,
                    "size": db_stats[0],
                    "active_connections": db_stats[1],
                },
                response_time_ms=response_time,
            )

        except psycopg.OperationalError as e:
            return HealthCheckResult(
                service=f"{component}-database",
                component=component,
                status="unhealthy",
                message=f"Connection failed: {str(e)[:100]}...",
                details={"port": port, "database": db_name, "error": str(e)},
                remediation=f"Check if {component} database container is running: docker ps | grep {config['container_prefix']}-postgres",
            )
        except Exception as e:
            return HealthCheckResult(
                service=f"{component}-database",
                component=component,
                status="unhealthy",
                message=f"Unexpected error: {str(e)[:100]}...",
                details={"port": port, "database": db_name, "error": str(e)},
                remediation="Check Docker containers and network connectivity",
            )

    def api_endpoint_check(self, component: str) -> HealthCheckResult:
        """Check API endpoint health for specified component.

        Args:
            component: Component to check ('agent' or 'genie')

        Returns:
            HealthCheckResult with API endpoint status
        """
        if component not in self.service_config:
            return HealthCheckResult(
                service=f"{component}-api",
                component=component,
                status="unknown",
                message=f"Unknown component: {component}",
                remediation="Use 'agent' or 'genie' as component",
            )

        config = self.service_config[component]
        port = config["api_port"]
        base_url = f"http://localhost:{port}"

        start_time = time.time()

        try:
            # Test health endpoint
            health_response = requests.get(
                f"{base_url}/health", timeout=self.timeout_seconds
            )

            response_time = (time.time() - start_time) * 1000

            if health_response.status_code == 200:
                health_data = health_response.json() if health_response.content else {}

                # Test additional endpoints
                endpoints_status = {}
                test_endpoints = ["/docs", "/openapi.json", "/v1/"]

                for endpoint in test_endpoints:
                    try:
                        resp = requests.get(f"{base_url}{endpoint}", timeout=5)
                        endpoints_status[endpoint] = resp.status_code
                    except Exception:
                        endpoints_status[endpoint] = 503  # Service Unavailable

                return HealthCheckResult(
                    service=f"{component}-api",
                    component=component,
                    status="healthy",
                    message=f"API responding (port {port})",
                    details={
                        "port": port,
                        "base_url": base_url,
                        "health_data": health_data,
                        "endpoints": endpoints_status,
                    },
                    response_time_ms=response_time,
                )
            return HealthCheckResult(
                service=f"{component}-api",
                component=component,
                status="unhealthy",
                message=f"API returned status {health_response.status_code}",
                details={
                    "port": port,
                    "status_code": health_response.status_code,
                    "response": health_response.text[:200],
                },
                remediation=f"Check {component} API container logs: docker logs {config['container_prefix']}-api",
            )

        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                service=f"{component}-api",
                component=component,
                status="unhealthy",
                message=f"Cannot connect to API (port {port})",
                details={"port": port, "base_url": base_url},
                remediation=f"Check if {component} API container is running: docker ps | grep {config['container_prefix']}-api",
            )
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service=f"{component}-api",
                component=component,
                status="unhealthy",
                message=f"API timeout after {self.timeout_seconds}s",
                details={"port": port, "timeout": self.timeout_seconds},
                remediation="API may be overloaded or starting up - wait and retry",
            )
        except Exception as e:
            return HealthCheckResult(
                service=f"{component}-api",
                component=component,
                status="unhealthy",
                message=f"Unexpected error: {str(e)[:100]}...",
                details={"port": port, "error": str(e)},
                remediation="Check Docker containers and network connectivity",
            )

    def workspace_process_check(self) -> HealthCheckResult:
        """Check workspace local uvx process validation.

        Returns:
            HealthCheckResult with workspace process status
        """
        try:
            # Look for automagik-hive processes
            hive_processes = []
            uvx_processes = []
            python_hive_processes = []

            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "status", "cpu_percent", "memory_info"]
            ):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    name = proc.info["name"] or ""

                    # Look for various forms of automagik-hive processes
                    if "automagik-hive" in cmdline or "automagik_hive" in cmdline:
                        hive_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": name,
                                "cmdline": cmdline,
                                "status": proc.info["status"],
                                "cpu_percent": proc.info["cpu_percent"] or 0,
                                "memory_mb": proc.info["memory_info"].rss
                                // 1024
                                // 1024
                                if proc.info["memory_info"]
                                else 0,
                            }
                        )

                    # Look for Python processes running hive modules
                    if "python" in name and (
                        "api.serve" in cmdline
                        or "api.main" in cmdline
                        or "automagik-hive" in cmdline
                    ):
                        python_hive_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": name,
                                "cmdline": cmdline,
                                "status": proc.info["status"],
                            }
                        )

                    # Look for uvx processes
                    if "uvx" in name or (
                        "uvx" in cmdline and "automagik-hive" in cmdline
                    ):
                        uvx_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": name,
                                "cmdline": cmdline,
                                "status": proc.info["status"],
                            }
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Check if workspace server is running
            workspace_running = False
            workspace_port = None

            # Check for processes listening on common workspace ports
            for port in [8000, 8080, 3000]:
                try:
                    connections = psutil.net_connections(kind="inet")
                    for conn in connections:
                        if conn.laddr.port == port and conn.status == "LISTEN":
                            workspace_running = True
                            workspace_port = port
                            break
                    if workspace_running:
                        break
                except Exception:
                    continue

            # Test workspace connectivity if found
            workspace_accessible = False
            if workspace_running and workspace_port:
                try:
                    response = requests.get(
                        f"http://localhost:{workspace_port}", timeout=5
                    )
                    workspace_accessible = response.status_code < 500
                except Exception:
                    workspace_accessible = False

            # Determine status based on all process types found
            total_processes = (
                len(hive_processes) + len(python_hive_processes) + len(uvx_processes)
            )

            # Determine status and create result
            if workspace_running and workspace_accessible:
                status = "healthy"
                message = f"Workspace accessible on port {workspace_port}"
                remediation = None
            elif workspace_running:
                status = "warning"
                message = f"Workspace process found on port {workspace_port} but not accessible"
                remediation = "Workspace process exists but not responding - check logs or restart"
            elif total_processes > 0:
                status = "warning"
                message = f"Found {total_processes} hive-related processes but no accessible workspace"
                remediation = "Processes found but no accessible service - may be starting up or misconfigured"
            else:
                status = "unhealthy"
                message = "No workspace process detected"
                remediation = "Start workspace with: uvx automagik-hive serve or uvx automagik-hive --install workspace"

            return HealthCheckResult(
                service="workspace",
                component="workspace",
                status=status,
                message=message,
                details={
                    "hive_processes": hive_processes,
                    "python_hive_processes": python_hive_processes,
                    "uvx_processes": uvx_processes[:5],  # Limit output
                    "workspace_port": workspace_port,
                    "workspace_accessible": workspace_accessible,
                    "total_processes": total_processes,
                },
                remediation=remediation,
            )

        except Exception as e:
            return HealthCheckResult(
                service="workspace",
                component="workspace",
                status="unhealthy",
                message=f"Process check failed: {str(e)[:100]}...",
                details={"error": str(e)},
                remediation="Check system process access and psutil installation",
            )

    def service_interdependency_check(
        self, component: str = "all"
    ) -> list[HealthCheckResult]:
        """Check service interdependencies for specified component.

        Args:
            component: Component to check interdependencies for

        Returns:
            List of HealthCheckResult for interdependency checks
        """
        results = []

        try:
            # Get Docker containers
            docker_result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=False,
            )

            containers = []
            if docker_result.returncode == 0:
                for line in docker_result.stdout.strip().split("\n"):
                    if line.strip():
                        try:
                            containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

            # Check Docker network connectivity
            network_result = self._check_docker_network()
            results.append(network_result)

            # Check component-specific interdependencies
            if component in ["all", "agent"]:
                agent_deps = self._check_agent_dependencies(containers)
                results.extend(agent_deps)

            if component in ["all", "genie"]:
                genie_deps = self._check_genie_dependencies(containers)
                results.extend(genie_deps)

            # Check cross-component dependencies if checking all
            if component == "all":
                cross_deps = self._check_cross_component_dependencies(containers)
                results.extend(cross_deps)

        except Exception as e:
            results.append(
                HealthCheckResult(
                    service="interdependency-check",
                    component=component,
                    status="unhealthy",
                    message=f"Interdependency check failed: {str(e)[:100]}...",
                    details={"error": str(e)},
                    remediation="Check Docker installation and network connectivity",
                )
            )

        return results

    def resource_usage_check(self) -> HealthCheckResult:
        """Monitor and validate resource usage.

        Returns:
            HealthCheckResult with resource usage status
        """
        try:
            # Get system resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Get network connections
            connections = len(psutil.net_connections(kind="inet"))

            # Get Docker container count
            docker_result = subprocess.run(
                ["docker", "ps", "-q"], capture_output=True, text=True, check=False
            )
            docker_containers = (
                len(docker_result.stdout.strip().split("\n"))
                if docker_result.returncode == 0 and docker_result.stdout.strip()
                else 0
            )

            # Check Automagik Hive specific resource usage
            hive_memory_mb = 0
            hive_processes = 0

            for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if "automagik-hive" in cmdline or "hive-" in proc.info["name"]:
                        hive_processes += 1
                        if proc.info["memory_info"]:
                            hive_memory_mb += (
                                proc.info["memory_info"].rss // 1024 // 1024
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_connections=connections,
                docker_containers=docker_containers,
            )

            # Determine status based on thresholds
            status = "healthy"
            warnings = []

            if cpu_percent > 90:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")

            if memory.percent > 90:
                status = "warning"
                warnings.append(f"High memory usage: {memory.percent:.1f}%")

            if disk.percent > 90:
                status = "warning"
                warnings.append(f"High disk usage: {disk.percent:.1f}%")

            if docker_containers == 0:
                status = "warning"
                warnings.append("No Docker containers running")

            message = "Resource usage within normal limits"
            if warnings:
                message = f"Resource warnings: {'; '.join(warnings)}"

            remediation = None
            if warnings:
                remediation = (
                    "Consider stopping unused services or upgrading system resources"
                )

            return HealthCheckResult(
                service="resource-usage",
                component="system",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available // 1024 // 1024 // 1024,
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free // 1024 // 1024 // 1024,
                    "network_connections": connections,
                    "docker_containers": docker_containers,
                    "hive_processes": hive_processes,
                    "hive_memory_mb": hive_memory_mb,
                },
                remediation=remediation,
            )

        except Exception as e:
            return HealthCheckResult(
                service="resource-usage",
                component="system",
                status="unhealthy",
                message=f"Resource check failed: {str(e)[:100]}...",
                details={"error": str(e)},
                remediation="Check system monitoring tools and psutil installation",
            )

    def generate_health_report(
        self, results: dict[str, HealthCheckResult], component: str
    ) -> str:
        """Generate detailed health report with actionable diagnostics.

        Args:
            results: Health check results
            component: Component that was checked

        Returns:
            Formatted health report string
        """
        # Count results by status
        status_counts = {"healthy": 0, "unhealthy": 0, "warning": 0, "unknown": 0}
        for result in results.values():
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        total_services = len(results)
        health_score = (
            (status_counts["healthy"] / total_services * 100)
            if total_services > 0
            else 0
        )

        # Generate report
        report_lines = [
            "# AUTOMAGIK HIVE HEALTH REPORT",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Component: {component.upper()}",
            f"Health Score: {health_score:.1f}% ({status_counts['healthy']}/{total_services} services healthy)",
            "",
            "## SUMMARY",
            f"✅ Healthy: {status_counts['healthy']}",
            f"⚠️  Warning: {status_counts['warning']}",
            f"❌ Unhealthy: {status_counts['unhealthy']}",
            f"❓ Unknown: {status_counts['unknown']}",
            "",
            "## DETAILED RESULTS",
        ]

        for service_name, result in results.items():
            icon = self._get_status_icon(result.status)
            report_lines.extend(
                [
                    f"### {icon} {service_name.upper()}",
                    f"Status: {result.status.upper()}",
                    f"Message: {result.message}",
                ]
            )

            if result.response_time_ms:
                report_lines.append(f"Response Time: {result.response_time_ms:.1f}ms")

            if result.details:
                report_lines.append("Details:")
                for key, value in result.details.items():
                    report_lines.append(f"  - {key}: {value}")

            if result.remediation:
                report_lines.extend(["Remediation:", f"  {result.remediation}"])

            report_lines.append("")

        # Add recommendations section
        if status_counts["unhealthy"] > 0 or status_counts["warning"] > 0:
            report_lines.extend(
                [
                    "## RECOMMENDATIONS",
                    "1. Address unhealthy services first (❌)",
                    "2. Monitor warning services closely (⚠️)",
                    "3. Check remediation steps above",
                    "4. Run health check again after fixes",
                    "",
                ]
            )

        report_lines.extend(
            [
                "## NEXT STEPS",
                "- For service issues: Check container logs with `docker logs <container-name>`",
                "- For connectivity issues: Verify Docker network with `docker network ls`",
                "- For resource issues: Monitor with `docker stats` and `htop`",
                "- Re-run health check: `uvx automagik-hive --health`",
            ]
        )

        return "\n".join(report_lines)

    def _get_services_for_component(self, component: str) -> dict[str, dict[str, Any]]:
        """Get services to check for specified component.

        Args:
            component: Component to get services for

        Returns:
            Dict mapping service names to check configurations
        """
        services = {}

        if component in ["all", "workspace"]:
            services["workspace"] = {"type": "workspace"}

        if component in ["all", "agent"]:
            services["agent-database"] = {"type": "database", "component": "agent"}
            services["agent-api"] = {"type": "api", "component": "agent"}

        if component in ["all", "genie"]:
            services["genie-database"] = {"type": "database", "component": "genie"}
            services["genie-api"] = {"type": "api", "component": "genie"}

        if component == "all":
            services["resource-usage"] = {"type": "resources"}
            services["interdependencies"] = {"type": "interdependencies"}

        return services

    def _check_service_with_retries(
        self, service_name: str, config: dict[str, Any], progress: Progress, task: Any
    ) -> HealthCheckResult:
        """Check service with retry logic.

        Args:
            service_name: Name of service to check
            config: Service configuration
            progress: Progress display
            task: Progress task ID

        Returns:
            HealthCheckResult for the service
        """
        last_result = None

        for attempt in range(self.retry_attempts):
            try:
                # Route to appropriate check method
                if config["type"] == "database":
                    result = self.database_connectivity_check(config["component"])
                elif config["type"] == "api":
                    result = self.api_endpoint_check(config["component"])
                elif config["type"] == "workspace":
                    result = self.workspace_process_check()
                elif config["type"] == "resources":
                    result = self.resource_usage_check()
                elif config["type"] == "interdependencies":
                    interdep_results = self.service_interdependency_check("all")
                    # Combine interdependency results into single result
                    healthy_deps = sum(
                        1 for r in interdep_results if r.status == "healthy"
                    )
                    total_deps = len(interdep_results)
                    if healthy_deps == total_deps:
                        result = HealthCheckResult(
                            service="interdependencies",
                            component="all",
                            status="healthy",
                            message=f"All {total_deps} interdependencies healthy",
                        )
                    else:
                        result = HealthCheckResult(
                            service="interdependencies",
                            component="all",
                            status="warning",
                            message=f"{healthy_deps}/{total_deps} interdependencies healthy",
                        )
                else:
                    result = HealthCheckResult(
                        service=service_name,
                        component="unknown",
                        status="unknown",
                        message=f"Unknown service type: {config['type']}",
                    )

                last_result = result

                # If healthy or if this is the last attempt, return result
                if result.status == "healthy" or attempt == self.retry_attempts - 1:
                    return result

                # Update progress for retry
                if attempt < self.retry_attempts - 1:
                    progress.update(
                        task,
                        description=f"⏳ {service_name} retrying... (attempt {attempt + 1})",
                    )
                    time.sleep(self.retry_delay)

            except Exception as e:
                last_result = HealthCheckResult(
                    service=service_name,
                    component=config.get("component", "unknown"),
                    status="unhealthy",
                    message=f"Check failed: {str(e)[:100]}...",
                    details={"error": str(e)},
                    remediation="Check service configuration and connectivity",
                )

                if attempt < self.retry_attempts - 1:
                    progress.update(
                        task, description=f"⏳ {service_name} error, retrying..."
                    )
                    time.sleep(self.retry_delay)

        return last_result or HealthCheckResult(
            service=service_name,
            component="unknown",
            status="unknown",
            message="No result available",
        )

    def _check_docker_network(self) -> HealthCheckResult:
        """Check Docker network connectivity.

        Returns:
            HealthCheckResult for Docker network
        """
        try:
            # Check if hive-network exists
            network_result = subprocess.run(
                [
                    "docker",
                    "network",
                    "ls",
                    "--filter",
                    "name=hive-network",
                    "--format",
                    "{{.Name}}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if (
                network_result.returncode == 0
                and "hive-network" in network_result.stdout
            ):
                return HealthCheckResult(
                    service="docker-network",
                    component="infrastructure",
                    status="healthy",
                    message="Docker network 'hive-network' exists",
                    details={"network": "hive-network"},
                )
            return HealthCheckResult(
                service="docker-network",
                component="infrastructure",
                status="unhealthy",
                message="Docker network 'hive-network' not found",
                remediation="Create network with: docker network create hive-network",
            )

        except Exception as e:
            return HealthCheckResult(
                service="docker-network",
                component="infrastructure",
                status="unhealthy",
                message=f"Network check failed: {str(e)[:100]}...",
                details={"error": str(e)},
                remediation="Check Docker installation and daemon status",
            )

    def _check_agent_dependencies(
        self, containers: list[dict[str, Any]]
    ) -> list[HealthCheckResult]:
        """Check agent component dependencies.

        Args:
            containers: List of Docker container info

        Returns:
            List of HealthCheckResult for agent dependencies
        """
        results = []

        # Check if agent containers exist and are running
        agent_postgres = any(
            "hive-agent-postgres" in container.get("Names", "")
            for container in containers
        )
        agent_api = any(
            "hive-agent-api" in container.get("Names", "") for container in containers
        )

        if agent_postgres:
            results.append(
                HealthCheckResult(
                    service="agent-postgres-container",
                    component="agent",
                    status="healthy",
                    message="Agent PostgreSQL container running",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    service="agent-postgres-container",
                    component="agent",
                    status="unhealthy",
                    message="Agent PostgreSQL container not found",
                    remediation="Start with: docker-compose --profile agent up -d",
                )
            )

        if agent_api:
            results.append(
                HealthCheckResult(
                    service="agent-api-container",
                    component="agent",
                    status="healthy",
                    message="Agent API container running",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    service="agent-api-container",
                    component="agent",
                    status="unhealthy",
                    message="Agent API container not found",
                    remediation="Start with: docker-compose --profile agent up -d",
                )
            )

        return results

    def _check_genie_dependencies(
        self, containers: list[dict[str, Any]]
    ) -> list[HealthCheckResult]:
        """Check genie component dependencies.

        Args:
            containers: List of Docker container info

        Returns:
            List of HealthCheckResult for genie dependencies
        """
        results = []

        # Check if genie containers exist and are running
        genie_postgres = any(
            "hive-genie-postgres" in container.get("Names", "")
            for container in containers
        )
        genie_api = any(
            "hive-genie-api" in container.get("Names", "") for container in containers
        )

        if genie_postgres:
            results.append(
                HealthCheckResult(
                    service="genie-postgres-container",
                    component="genie",
                    status="healthy",
                    message="Genie PostgreSQL container running",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    service="genie-postgres-container",
                    component="genie",
                    status="unhealthy",
                    message="Genie PostgreSQL container not found",
                    remediation="Start with: docker-compose --profile genie up -d",
                )
            )

        if genie_api:
            results.append(
                HealthCheckResult(
                    service="genie-api-container",
                    component="genie",
                    status="healthy",
                    message="Genie API container running",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    service="genie-api-container",
                    component="genie",
                    status="unhealthy",
                    message="Genie API container not found",
                    remediation="Start with: docker-compose --profile genie up -d",
                )
            )

        return results

    def _check_cross_component_dependencies(
        self, containers: list[dict[str, Any]]
    ) -> list[HealthCheckResult]:
        """Check cross-component dependencies.

        Args:
            containers: List of Docker container info

        Returns:
            List of HealthCheckResult for cross-component checks
        """
        results = []

        # Check if both agent and genie can access shared resources
        # This is a placeholder for future cross-component checks
        results.append(
            HealthCheckResult(
                service="cross-component-deps",
                component="all",
                status="healthy",
                message="Cross-component dependencies healthy",
                details={"note": "Placeholder for future cross-component checks"},
            )
        )

        return results

    def _get_status_icon(self, status: str) -> str:
        """Get icon for status.

        Args:
            status: Health status

        Returns:
            Status icon string
        """
        icons = {"healthy": "✅", "unhealthy": "❌", "warning": "⚠️", "unknown": "❓"}
        return icons.get(status, "❓")

    def _display_health_report(
        self, results: dict[str, HealthCheckResult], component: str
    ) -> None:
        """Display comprehensive health report.

        Args:
            results: Health check results
            component: Component that was checked
        """
        # Count results by status
        status_counts = {"healthy": 0, "unhealthy": 0, "warning": 0, "unknown": 0}
        for result in results.values():
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        total_services = len(results)
        health_score = (
            (status_counts["healthy"] / total_services * 100)
            if total_services > 0
            else 0
        )

        # Create summary table
        summary_table = Table(title=f"Health Summary - {component.upper()}")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")

        summary_table.add_row("Health Score", f"{health_score:.1f}%")
        summary_table.add_row("Total Services", str(total_services))
        summary_table.add_row("✅ Healthy", str(status_counts["healthy"]))
        summary_table.add_row("⚠️ Warning", str(status_counts["warning"]))
        summary_table.add_row("❌ Unhealthy", str(status_counts["unhealthy"]))
        summary_table.add_row("❓ Unknown", str(status_counts["unknown"]))

        self.console.print(summary_table)
        self.console.print()

        # Create detailed results table
        details_table = Table(title="Service Details")
        details_table.add_column("Service", style="cyan")
        details_table.add_column("Status", style="bold")
        details_table.add_column("Message", style="white")
        details_table.add_column("Response Time", style="yellow")

        for service_name, result in results.items():
            status_icon = self._get_status_icon(result.status)
            status_text = f"{status_icon} {result.status.upper()}"

            # Color status based on result
            if result.status == "healthy":
                status_style = "green"
            elif result.status == "warning":
                status_style = "yellow"
            elif result.status == "unhealthy":
                status_style = "red"
            else:
                status_style = "white"

            response_time = (
                f"{result.response_time_ms:.1f}ms" if result.response_time_ms else "-"
            )

            details_table.add_row(
                service_name,
                Text(status_text, style=status_style),
                result.message,
                response_time,
            )

        self.console.print(details_table)

        # Show remediation steps for unhealthy services
        unhealthy_services = [
            (name, result)
            for name, result in results.items()
            if result.status in ["unhealthy", "warning"] and result.remediation
        ]

        if unhealthy_services:
            self.console.print()
            self.console.print(
                Panel.fit(
                    "🔧 [bold]Remediation Steps[/bold]\n\n"
                    + "\n".join(
                        [
                            f"• [cyan]{name}[/cyan]: {result.remediation}"
                            for name, result in unhealthy_services
                        ]
                    ),
                    title="Action Required",
                    border_style="yellow",
                )
            )

        # Overall status message
        if health_score == 100:
            self.console.print(
                Panel.fit(
                    "🎉 [bold green]All systems healthy![/bold green]\n"
                    "Your Automagik Hive is running optimally.",
                    border_style="green",
                )
            )
        elif health_score >= 70:
            self.console.print(
                Panel.fit(
                    "⚠️ [bold yellow]System partially healthy[/bold yellow]\n"
                    "Some services need attention - check remediation steps above.",
                    border_style="yellow",
                )
            )
        else:
            self.console.print(
                Panel.fit(
                    "🚨 [bold red]System health critical[/bold red]\n"
                    "Multiple services unhealthy - immediate action required.",
                    border_style="red",
                )
            )

    def run_health_check_cli(
        self, component: str = "all", save_report: bool = False
    ) -> int:
        """Run health check from CLI with proper exit codes.

        Args:
            component: Component to check
            save_report: Whether to save detailed report to file

        Returns:
            int: Exit code (0 = healthy, 1 = issues found)
        """
        try:
            results = self.comprehensive_health_check(component)

            # Save detailed report if requested
            if save_report:
                report = self.generate_health_report(results, component)
                report_file = Path(f"health_report_{component}_{int(time.time())}.md")
                report_file.write_text(report)
                self.console.print(f"\n📄 Detailed report saved to: {report_file}")

            # Determine exit code based on results
            critical_issues = sum(
                1 for result in results.values() if result.status == "unhealthy"
            )

            if critical_issues == 0:
                return 0  # All healthy or just warnings
            return 1  # Critical issues found

        except Exception as e:
            logger.error(f"Health check CLI failed: {e}")
            self.console.print(f"❌ [red]Health check failed:[/red] {e}")
            return 1
