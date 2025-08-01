"""
Docker Compose Management for Automagik Hive.

This module provides Docker Compose orchestration capabilities,
specifically optimized for PostgreSQL and multi-service container management.
"""

import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ServiceStatus(Enum):
    """Docker Compose service status states"""
    RUNNING = "running"
    STOPPED = "stopped" 
    RESTARTING = "restarting"
    PAUSED = "paused"
    EXITED = "exited"
    DEAD = "dead"
    NOT_EXISTS = "not_exists"


@dataclass
class ServiceInfo:
    """Docker Compose service information"""
    name: str
    status: ServiceStatus
    ports: List[str]
    image: str
    container_name: Optional[str] = None


class DockerComposeManager:
    """
    Docker Compose orchestration for multi-service container management.
    
    Provides high-level operations for managing PostgreSQL and other services
    using existing docker-compose.yml files as foundation.
    """
    
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        
    def start_service(self, service: str, workspace_path: str = ".") -> bool:
        """
        Start specific service from docker-compose.yml.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if started successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                print(f"❌ {self.compose_file} not found in {workspace_path}")
                return False
                
            print(f"🚀 Starting {service} service...")
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "up", "-d", service
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {service} service started successfully")
                return True
            else:
                print(f"❌ Failed to start {service} service: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"❌ Error starting {service} service: {e}")
            return False
            
    def stop_service(self, service: str, workspace_path: str = ".") -> bool:
        """
        Stop specific service from docker-compose.yml.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                print(f"❌ {self.compose_file} not found in {workspace_path}")
                return False
                
            print(f"🛑 Stopping {service} service...")
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "stop", service
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ {service} service stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop {service} service: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"❌ Error stopping {service} service: {e}")
            return False
            
    def restart_service(self, service: str, workspace_path: str = ".") -> bool:
        """
        Restart specific service from docker-compose.yml.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if restarted successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                print(f"❌ {self.compose_file} not found in {workspace_path}")
                return False
                
            print(f"🔄 Restarting {service} service...")
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "restart", service
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {service} service restarted successfully")
                return True
            else:
                print(f"❌ Failed to restart {service} service: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"❌ Error restarting {service} service: {e}")
            return False
            
    def get_service_logs(self, service: str, tail: int = 50, workspace_path: str = ".") -> Optional[str]:
        """
        Get logs for specific service.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            tail: Number of lines to retrieve
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            Service logs as string, None if error
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return None
                
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), 
                "logs", "--tail", str(tail), service
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None
            
    def stream_service_logs(self, service: str, workspace_path: str = ".") -> bool:
        """
        Stream logs for specific service (non-blocking).
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if streaming started successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                print(f"❌ {self.compose_file} not found in {workspace_path}")
                return False
                
            print(f"📡 Streaming {service} logs (Ctrl+C to stop)...")
            subprocess.run([
                "docker-compose", "-f", str(compose_file_path), 
                "logs", "-f", service
            ], timeout=None)  # No timeout for streaming
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n🛑 Stopped streaming {service} logs")
            return True
        except subprocess.SubprocessError as e:
            print(f"❌ Error streaming {service} logs: {e}")
            return False
            
    def get_service_status(self, service: str, workspace_path: str = ".") -> ServiceStatus:
        """
        Get status of specific service.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            ServiceStatus indicating current state
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return ServiceStatus.NOT_EXISTS
                
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "ps", service
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return ServiceStatus.NOT_EXISTS
                
            output = result.stdout.strip()
            if not output or "No containers found" in output:
                return ServiceStatus.NOT_EXISTS
                
            # Parse docker-compose ps output
            lines = output.split('\n')
            if len(lines) < 2:  # Header + at least one service line
                return ServiceStatus.NOT_EXISTS
                
            # Look for service status in output
            service_line = None
            for line in lines[1:]:  # Skip header
                if service in line:
                    service_line = line
                    break
                    
            if not service_line:
                return ServiceStatus.NOT_EXISTS
                
            # Parse status from the line
            if "Up" in service_line:
                return ServiceStatus.RUNNING
            elif "Exit" in service_line:
                return ServiceStatus.EXITED
            elif "Restarting" in service_line:
                return ServiceStatus.RESTARTING
            elif "Paused" in service_line:
                return ServiceStatus.PAUSED
            else:
                return ServiceStatus.STOPPED
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return ServiceStatus.NOT_EXISTS
            
    def get_all_services_status(self, workspace_path: str = ".") -> Dict[str, ServiceInfo]:
        """
        Get status of all services in docker-compose.yml.
        
        Args:
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            Dict mapping service names to ServiceInfo
        """
        services = {}
        
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return services
                
            # Parse docker-compose.yml to get service names
            with open(compose_file_path, 'r') as f:
                compose_config = yaml.safe_load(f)
                
            if 'services' not in compose_config:
                return services
                
            # Get status for each service
            for service_name in compose_config['services']:
                status = self.get_service_status(service_name, workspace_path)
                service_config = compose_config['services'][service_name]
                
                # Extract service information
                ports = []
                if 'ports' in service_config:
                    ports = service_config['ports']
                    
                image = service_config.get('image', 'unknown')
                if 'build' in service_config:
                    image = f"built:{service_name}"
                    
                container_name = service_config.get('container_name')
                
                services[service_name] = ServiceInfo(
                    name=service_name,
                    status=status,
                    ports=ports,
                    image=image,
                    container_name=container_name
                )
                
        except Exception as e:
            print(f"⚠️ Warning: Could not get all services status: {e}")
            
        return services
        
    def start_all_services(self, workspace_path: str = ".") -> bool:
        """
        Start all services from docker-compose.yml.
        
        Args:
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if all services started successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                print(f"❌ {self.compose_file} not found in {workspace_path}")
                return False
                
            print("🚀 Starting all services...")
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "up", "-d"
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print("✅ All services started successfully")
                return True
            else:
                print(f"❌ Failed to start services: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"❌ Error starting all services: {e}")
            return False
            
    def stop_all_services(self, workspace_path: str = ".") -> bool:
        """
        Stop all services from docker-compose.yml.
        
        Args:
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if all services stopped successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                print(f"❌ {self.compose_file} not found in {workspace_path}")
                return False
                
            print("🛑 Stopping all services...")
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "down"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ All services stopped successfully")
                return True
            else:
                print(f"❌ Failed to stop services: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"❌ Error stopping all services: {e}")
            return False
            
    def validate_compose_file(self, workspace_path: str = ".") -> bool:
        """
        Validate docker-compose.yml file syntax and structure.
        
        Args:
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            True if valid, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False
                
            # Validate syntax with docker-compose config
            result = subprocess.run([
                "docker-compose", "-f", str(compose_file_path), "config"
            ], capture_output=True, text=True, timeout=30)
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
            
    def get_compose_services(self, workspace_path: str = ".") -> List[str]:
        """
        Get list of service names from docker-compose.yml.
        
        Args:
            workspace_path: Path to workspace with docker-compose.yml
            
        Returns:
            List of service names
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return []
                
            with open(compose_file_path, 'r') as f:
                compose_config = yaml.safe_load(f)
                
            if 'services' not in compose_config:
                return []
                
            return list(compose_config['services'].keys())
            
        except Exception:
            return []