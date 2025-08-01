"""Security utilities for Automagik Hive CLI operations.

This module provides centralized security validation and sanitization
for all CLI operations involving user input, file paths, and subprocess calls.

CRITICAL SECURITY FEATURES:
- Path traversal attack prevention
- Command injection protection
- Input sanitization for subprocess calls
- Workspace path validation
- File system boundary enforcement
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any, List, Optional, Union, Dict


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal attack is detected."""
    pass


class CommandInjectionError(SecurityError):
    """Raised when command injection attempt is detected."""
    pass


class InputValidationError(SecurityError):
    """Raised when input validation fails."""
    pass


class SecurePathValidator:
    """Secure path validation and sanitization utility."""
    
    # Dangerous path patterns that indicate traversal attacks
    DANGEROUS_PATTERNS = [
        r'\.\.',           # Directory traversal
        r'\/\.\.',         # Unix path traversal  
        r'\\\.\.',         # Windows path traversal
        r'~/',             # Home directory access
        r'\/tmp\/',        # Temp directory access
        r'\/etc\/',        # System config access
        r'\/var\/',        # System var access
        r'\/usr\/',        # System usr access
        r'\/root\/',       # Root directory access
        r'\/bin\/',        # Binary directory access
        r'\/sbin\/',       # System binary access
        r'[;&|`$]',        # Command injection chars
        r'\\x[0-9a-fA-F]{2}',  # Hex encoded chars
        r'%[0-9a-fA-F]{2}',    # URL encoded chars
    ]
    
    # Maximum allowed path depth
    MAX_PATH_DEPTH = 10
    
    # Maximum path length
    MAX_PATH_LENGTH = 1000
    
    @classmethod
    def validate_workspace_path(cls, path: Union[str, Path]) -> Path:
        """Validate and sanitize workspace path for security.
        
        Args:
            path: User-provided workspace path
            
        Returns:
            Validated and resolved Path object
            
        Raises:
            PathTraversalError: If path contains traversal attempts
            InputValidationError: If path is invalid
        """
        if not path:
            raise InputValidationError("Path cannot be empty")
            
        path_str = str(path)
        
        # Check path length
        if len(path_str) > cls.MAX_PATH_LENGTH:
            raise InputValidationError(f"Path too long: {len(path_str)} > {cls.MAX_PATH_LENGTH}")
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                raise PathTraversalError(f"Dangerous path pattern detected: {pattern} in {path_str}")
        
        # Convert to Path object for further validation
        try:
            resolved_path = Path(path).resolve()
        except (OSError, ValueError) as e:
            raise InputValidationError(f"Invalid path format: {e}")
        
        # Check path depth
        path_parts = resolved_path.parts
        if len(path_parts) > cls.MAX_PATH_DEPTH:
            raise PathTraversalError(f"Path depth {len(path_parts)} exceeds maximum {cls.MAX_PATH_DEPTH}")
        
        # Ensure path is within allowed boundaries (no access to system directories)
        resolved_str = str(resolved_path)
        system_dirs = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/tmp']
        for sys_dir in system_dirs:
            if resolved_str.startswith(sys_dir):
                raise PathTraversalError(f"Access to system directory denied: {sys_dir}")
        
        return resolved_path
    
    @classmethod
    def validate_file_path(cls, path: Union[str, Path], must_exist: bool = False) -> Path:
        """Validate file path for security.
        
        Args:
            path: File path to validate
            must_exist: Whether file must exist
            
        Returns:
            Validated Path object
            
        Raises:
            PathTraversalError: If path contains traversal attempts
            InputValidationError: If path is invalid
        """
        validated_path = cls.validate_workspace_path(path)
        
        if must_exist and not validated_path.exists():
            raise InputValidationError(f"Required file does not exist: {validated_path}")
        
        return validated_path


class SecureSubprocessExecutor:
    """Secure subprocess execution with command injection prevention."""
    
    # Allowed executables for subprocess calls
    ALLOWED_EXECUTABLES = {
        'docker', 'docker-compose', 'uv', 'python', 'python3',
        'tail', 'head', 'cat', 'ls', 'mkdir', 'rm', 'cp', 'mv',
        'pg_isready', 'psql', 'git', 'chmod', 'chown'
    }
    
    # Dangerous command injection patterns
    INJECTION_PATTERNS = [
        r'[;&|`$()]',      # Command separators and execution
        r'>\s*\/dev',      # Redirection to devices
        r'<\s*\/dev',      # Input from devices  
        r'\|\s*sh',        # Pipe to shell
        r'\|\s*bash',      # Pipe to bash
        r'eval\s*\(',      # Eval execution
        r'exec\s*\(',      # Exec execution
        r'system\s*\(',    # System calls
        r'`[^`]*`',        # Backtick command substitution
        r'\$\([^)]*\)',    # Command substitution
        r'\/:/host',       # Docker volume mount to host root
        r'--rm.*-v.*:',    # Docker dangerous volume mounts
        r'import\s+os',    # Python os module import
        r'\.system\(',     # Python system calls
    ]
    
    @classmethod
    def validate_command_args(cls, args: List[str]) -> List[str]:
        """Validate subprocess command arguments for security.
        
        Args:
            args: List of command arguments
            
        Returns:
            Validated argument list
            
        Raises:
            CommandInjectionError: If injection attempt detected
            InputValidationError: If arguments invalid
        """
        if not args:
            raise InputValidationError("Command arguments cannot be empty")
        
        # Validate executable
        executable = args[0]
        if executable not in cls.ALLOWED_EXECUTABLES:
            raise CommandInjectionError(f"Executable not allowed: {executable}")
        
        # Check each argument for injection patterns
        for i, arg in enumerate(args):
            arg_str = str(arg)
            
            # Check for injection patterns
            for pattern in cls.INJECTION_PATTERNS:
                if re.search(pattern, arg_str, re.IGNORECASE):
                    raise CommandInjectionError(f"Command injection detected in arg[{i}]: {pattern}")
            
            # Validate path arguments
            if i > 0 and ('/' in arg_str or '\\' in arg_str):
                try:
                    # Try to validate as path (may fail for non-path args, that's OK)
                    SecurePathValidator.validate_workspace_path(arg_str)
                except (PathTraversalError, InputValidationError):
                    # For non-path arguments, do basic validation
                    if '..' in arg_str or arg_str.startswith('/etc'):
                        raise CommandInjectionError(f"Suspicious path in arg[{i}]: {arg_str}")
        
        return args
    
    @classmethod
    def safe_subprocess_run(
        cls, 
        args: List[str], 
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """Execute subprocess with security validation.
        
        Args:
            args: Command arguments
            cwd: Working directory 
            env: Environment variables
            **kwargs: Additional subprocess.run arguments
            
        Returns:
            CompletedProcess result
            
        Raises:
            CommandInjectionError: If injection attempt detected
            PathTraversalError: If dangerous path detected
        """
        # Validate command arguments
        validated_args = cls.validate_command_args(args)
        
        # Validate working directory
        validated_cwd = None
        if cwd:
            validated_cwd = SecurePathValidator.validate_workspace_path(cwd)
        
        # Ensure shell=False to prevent shell injection
        kwargs['shell'] = False
        
        # Set secure defaults
        kwargs.setdefault('capture_output', True)
        kwargs.setdefault('text', True)
        kwargs.setdefault('check', False)
        
        # Execute with validated parameters
        return subprocess.run(
            validated_args,
            cwd=str(validated_cwd) if validated_cwd else None,
            env=env,
            **kwargs
        )


class SecureEnvironmentHandler:
    """Secure environment file handling and validation."""
    
    # Allowed environment variable patterns
    ALLOWED_ENV_PATTERNS = [
        r'^[A-Z_][A-Z0-9_]*$',  # Standard env var names
    ]
    
    # Dangerous environment values
    DANGEROUS_ENV_VALUES = [
        r'[;&|`$()]',          # Command injection
        r'eval\s*\(',          # Eval calls
        r'exec\s*\(',          # Exec calls  
        r'system\s*\(',        # System calls
        r'\$\([^)]*\)',        # Command substitution
        r'`[^`]*`',            # Backtick substitution
    ]
    
    @classmethod
    def validate_env_var(cls, key: str, value: str) -> tuple[str, str]:
        """Validate environment variable key and value.
        
        Args:
            key: Environment variable name
            value: Environment variable value
            
        Returns:
            Validated (key, value) tuple
            
        Raises:
            InputValidationError: If key/value invalid
            CommandInjectionError: If injection detected
        """
        # Validate key format
        key_valid = any(re.match(pattern, key) for pattern in cls.ALLOWED_ENV_PATTERNS)
        if not key_valid:
            raise InputValidationError(f"Invalid environment variable name: {key}")
        
        # Check value for dangerous patterns
        for pattern in cls.DANGEROUS_ENV_VALUES:
            if re.search(pattern, value):
                raise CommandInjectionError(f"Dangerous pattern in env value for {key}: {pattern}")
        
        return key, value
    
    @classmethod  
    def safe_env_file_load(cls, env_file: Union[str, Path]) -> Dict[str, str]:
        """Safely load environment file with validation.
        
        Args:
            env_file: Path to environment file
            
        Returns:
            Dictionary of validated environment variables
            
        Raises:
            PathTraversalError: If file path is dangerous
            InputValidationError: If file content invalid
        """
        validated_path = SecurePathValidator.validate_file_path(env_file, must_exist=True)
        
        env_vars = {}
        try:
            with open(validated_path) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    try:
                        validated_key, validated_value = cls.validate_env_var(key, value)
                        env_vars[validated_key] = validated_value
                    except (InputValidationError, CommandInjectionError) as e:
                        raise InputValidationError(f"Line {line_num} in {env_file}: {e}")
                        
        except OSError as e:
            raise InputValidationError(f"Failed to read environment file {env_file}: {e}")
        
        return env_vars


# Convenience functions for common security operations
def secure_resolve_workspace(workspace_path: Optional[Union[str, Path]] = None) -> Path:
    """Securely resolve workspace path with validation.
    
    Args:
        workspace_path: User-provided workspace path (defaults to current directory)
        
    Returns:
        Validated workspace Path object
        
    Raises:
        PathTraversalError: If path contains traversal attempts
        InputValidationError: If path is invalid
    """
    if workspace_path is None:
        workspace_path = Path.cwd()
    
    return SecurePathValidator.validate_workspace_path(workspace_path)


def secure_subprocess_call(args: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Secure wrapper for subprocess calls with validation.
    
    Args:
        args: Command arguments
        **kwargs: Additional subprocess arguments
        
    Returns:
        CompletedProcess result
        
    Raises:
        CommandInjectionError: If injection attempt detected
    """
    return SecureSubprocessExecutor.safe_subprocess_run(args, **kwargs)


def validate_user_input_path(path: Union[str, Path]) -> Path:
    """Validate user-provided path input for security.
    
    Args:
        path: User input path
        
    Returns:
        Validated Path object
        
    Raises:
        PathTraversalError: If path traversal detected
        InputValidationError: If input invalid
    """
    return SecurePathValidator.validate_workspace_path(path)


# Security test functions for penetration testing
def test_path_traversal_protection():
    """Test path traversal attack prevention."""
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/etc/passwd",
        "/tmp/../etc/passwd", 
        "workspace/../../../root/.ssh",
        "~/../../../etc/shadow",
        "./workspace;cat /etc/passwd",
        "workspace`cat /etc/passwd`",
        "workspace$(cat /etc/passwd)",
    ]
    
    for path in malicious_paths:
        try:
            SecurePathValidator.validate_workspace_path(path)
            print(f"❌ SECURITY FAILURE: Path traversal not detected: {path}")
            return False
        except (PathTraversalError, InputValidationError):
            print(f"✅ Path traversal blocked: {path}")
    
    return True


def test_command_injection_protection():
    """Test command injection prevention."""
    malicious_commands = [
        ["tail", "-f", "/var/log/auth.log; cat /etc/passwd"],
        ["docker", "run", "--rm", "-v", "/:/host", "alpine", "cat", "/host/etc/passwd"],
        ["python", "-c", "import os; os.system('cat /etc/passwd')"],
        ["ls", "/tmp", "&&", "cat", "/etc/passwd"],
        ["uv", "run", "`cat /etc/passwd`"],
        ["tail", "/tmp/log", "|", "sh"],
    ]
    
    for cmd in malicious_commands:
        try:
            SecureSubprocessExecutor.validate_command_args(cmd)
            print(f"❌ SECURITY FAILURE: Command injection not detected: {cmd}")
            return False
        except CommandInjectionError:
            print(f"✅ Command injection blocked: {cmd[0]} {' '.join(cmd[1:])}")
    
    return True


def run_security_penetration_tests() -> bool:
    """Run comprehensive security penetration tests.
    
    Returns:
        True if all security tests pass, False if vulnerabilities found
    """
    print("🔐 Running Security Penetration Tests...")
    print("=" * 50)
    
    path_test = test_path_traversal_protection()
    cmd_test = test_command_injection_protection()
    
    if path_test and cmd_test:
        print("=" * 50)
        print("✅ ALL SECURITY TESTS PASSED - System is protected")
        return True
    else:
        print("=" * 50)
        print("❌ SECURITY VULNERABILITIES DETECTED - System is NOT safe")
        return False