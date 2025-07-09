#!/usr/bin/env python3
"""
Integration-First Orchestration Patterns
Prevents future dead code generation through integration validation

Based on lessons learned from the 800+ lines of dead code cleanup.
Implements "Integration-First Development" to replace "Build First, Integrate Never" anti-pattern.
"""

import ast
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class IntegrationContract:
    """Contract defining how components should integrate"""
    component_name: str
    required_dependencies: List[str]
    provided_interfaces: List[str]
    usage_requirements: Dict[str, Any]
    integration_tests: List[Callable] = field(default_factory=list)


@dataclass 
class CodeUsageRecord:
    """Record of code usage for tracking"""
    function_name: str
    file_path: str
    caller: str
    usage_count: int = 0
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)


class CodeRegistry:
    """Central registry for tracking all code components and their usage"""
    
    def __init__(self):
        self.registered_functions: Dict[str, CodeUsageRecord] = {}
        self.integration_contracts: Dict[str, IntegrationContract] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger("integration_patterns.registry")
    
    def register_function(self, function_name: str, file_path: str, dependencies: List[str] = None):
        """Register a function for usage tracking"""
        self.registered_functions[function_name] = CodeUsageRecord(
            function_name=function_name,
            file_path=file_path,
            caller="registry",
            dependencies=dependencies or []
        )
        self.logger.info(f"Registered function: {function_name}")
    
    def track_usage(self, function_name: str, caller: str):
        """Track usage of a function"""
        if function_name in self.registered_functions:
            record = self.registered_functions[function_name]
            record.usage_count += 1
            record.caller = caller
            record.last_used = datetime.now()
            if record.first_used is None:
                record.first_used = datetime.now()
    
    def get_unused_functions(self) -> List[str]:
        """Get list of functions that have never been used"""
        return [
            name for name, record in self.registered_functions.items()
            if record.usage_count == 0
        ]
    
    def get_dependency_violations(self) -> List[str]:
        """Get list of dependencies that don't exist"""
        violations = []
        for func_name, record in self.registered_functions.items():
            for dep in record.dependencies:
                if dep not in self.registered_functions:
                    violations.append(f"{func_name} depends on missing {dep}")
        return violations


class IntegrationValidator:
    """Validates integration requirements before code generation"""
    
    def __init__(self, code_registry: CodeRegistry):
        self.registry = code_registry
        self.logger = logging.getLogger("integration_patterns.validator")
    
    def validate_integration_contract(self, contract: IntegrationContract) -> bool:
        """Validate that an integration contract can be fulfilled"""
        self.logger.info(f"Validating contract for {contract.component_name}")
        
        # Check required dependencies exist
        for dependency in contract.required_dependencies:
            if dependency not in self.registry.registered_functions:
                self.logger.error(f"Missing dependency: {dependency}")
                return False
        
        # Run integration tests
        for test in contract.integration_tests:
            try:
                result = test()
                if not result:
                    self.logger.error(f"Integration test failed: {test.__name__}")
                    return False
            except Exception as e:
                self.logger.error(f"Integration test error: {e}")
                return False
        
        self.logger.info(f"Contract validation passed for {contract.component_name}")
        return True
    
    def validate_before_build(self, component_name: str, dependencies: List[str]) -> bool:
        """Validate dependencies exist before building component"""
        missing = []
        for dep in dependencies:
            if dep not in self.registry.registered_functions:
                missing.append(dep)
        
        if missing:
            self.logger.error(f"Cannot build {component_name}: missing {missing}")
            return False
        
        return True


class CodeAnalyzer:
    """Analyzes existing code to identify usage patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger("integration_patterns.analyzer")
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for functions and dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            functions = []
            imports = []
            calls = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{node.module}.{alias.name}")
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
            
            return {
                'functions': functions,
                'imports': imports,
                'calls': calls,
                'file_path': str(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return {}
    
    def find_unused_functions(self, project_path: Path) -> List[str]:
        """Find functions that are defined but never called"""
        defined_functions = set()
        called_functions = set()
        
        # Analyze all Python files
        for py_file in project_path.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            analysis = self.analyze_file(py_file)
            defined_functions.update(analysis.get('functions', []))
            called_functions.update(analysis.get('calls', []))
        
        unused = defined_functions - called_functions
        self.logger.info(f"Found {len(unused)} potentially unused functions")
        return list(unused)


class IntegrationFirstOrchestrator:
    """
    Main orchestrator implementing Integration-First Development pattern
    Prevents dead code generation through proactive integration validation
    """
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.code_registry = CodeRegistry()
        self.validator = IntegrationValidator(self.code_registry)
        self.analyzer = CodeAnalyzer()
        self.logger = logging.getLogger("integration_patterns.orchestrator")
        
        # Initialize with existing codebase analysis
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize registry with existing codebase"""
        self.logger.info("Initializing code registry with existing codebase...")
        
        for py_file in self.project_path.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            analysis = self.analyzer.analyze_file(py_file)
            for func_name in analysis.get('functions', []):
                self.code_registry.register_function(
                    function_name=func_name,
                    file_path=str(py_file),
                    dependencies=analysis.get('calls', [])
                )
    
    def create_integration_contract(self, component_name: str, 
                                  dependencies: List[str],
                                  interfaces: List[str]) -> IntegrationContract:
        """Create an integration contract for a component"""
        return IntegrationContract(
            component_name=component_name,
            required_dependencies=dependencies,
            provided_interfaces=interfaces,
            usage_requirements={}
        )
    
    def validate_before_development(self, contract: IntegrationContract) -> bool:
        """Validate integration contract before starting development"""
        self.logger.info(f"Pre-development validation for {contract.component_name}")
        
        # Check if dependencies exist
        if not self.validator.validate_integration_contract(contract):
            self.logger.error("Integration validation failed - cannot proceed")
            return False
        
        # Register the contract
        self.code_registry.integration_contracts[contract.component_name] = contract
        
        self.logger.info("Pre-development validation passed")
        return True
    
    def track_development_usage(self, function_name: str, caller: str):
        """Track usage during development"""
        self.code_registry.track_usage(function_name, caller)
    
    def validate_integration_points(self) -> Dict[str, Any]:
        """Validate all integration points in the system"""
        self.logger.info("Validating all integration points...")
        
        results = {
            'unused_functions': self.code_registry.get_unused_functions(),
            'dependency_violations': self.code_registry.get_dependency_violations(),
            'integration_status': {},
            'cleanup_recommendations': []
        }
        
        # Validate each contract
        for name, contract in self.code_registry.integration_contracts.items():
            results['integration_status'][name] = self.validator.validate_integration_contract(contract)
        
        # Generate cleanup recommendations
        if results['unused_functions']:
            results['cleanup_recommendations'].append(
                f"Remove {len(results['unused_functions'])} unused functions"
            )
        
        if results['dependency_violations']:
            results['cleanup_recommendations'].append(
                f"Fix {len(results['dependency_violations'])} dependency violations"
            )
        
        return results
    
    def automated_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """Perform automated cleanup of unused code"""
        self.logger.info(f"Starting automated cleanup (dry_run={dry_run})")
        
        cleanup_report = {
            'removed_functions': [],
            'fixed_dependencies': [],
            'files_modified': [],
            'dry_run': dry_run
        }
        
        unused_functions = self.code_registry.get_unused_functions()
        
        if not dry_run:
            # In real implementation, this would modify files
            for func_name in unused_functions:
                record = self.code_registry.registered_functions[func_name]
                # TODO: Implement actual file modification
                cleanup_report['removed_functions'].append(func_name)
                self.logger.info(f"Would remove unused function: {func_name}")
        else:
            cleanup_report['removed_functions'] = unused_functions
            self.logger.info(f"Dry run: would remove {len(unused_functions)} functions")
        
        return cleanup_report
    
    def generate_development_guidelines(self) -> str:
        """Generate development guidelines based on lessons learned"""
        return """
# Integration-First Development Guidelines

## Phase 1: Integration Planning
1. Identify all required integrations BEFORE coding
2. Create integration contracts with dependencies
3. Validate all dependencies exist
4. Write integration tests first

## Phase 2: Coordinated Development  
1. Build with integration points defined upfront
2. Track usage as code is created
3. Monitor dependencies in real-time
4. Prevent orphaned code creation

## Phase 3: Integration Validation
1. Test all integration points continuously
2. Remove unused code immediately
3. Validate cross-component usage
4. Update dependency graphs

## Phase 4: Automated Cleanup
1. Run usage analysis regularly
2. Remove orphaned functions automatically
3. Validate all code is integrated
4. Document integration patterns

## Anti-Patterns to Avoid
- ❌ "Build First, Integrate Never"
- ❌ Creating code without integration plan
- ❌ Ignoring dependency validation
- ❌ Accumulating unused code

## Success Metrics
- ✅ Zero unused functions
- ✅ All dependencies validated
- ✅ Integration tests passing
- ✅ Clean dependency graphs
"""


def create_integration_orchestrator(project_path: Optional[Path] = None) -> IntegrationFirstOrchestrator:
    """Factory function to create integration orchestrator"""
    return IntegrationFirstOrchestrator(project_path)


# Example usage and testing
if __name__ == "__main__":
    # Create orchestrator for current project
    orchestrator = create_integration_orchestrator()
    
    # Validate current integration points
    validation_results = orchestrator.validate_integration_points()
    
    print("🔍 Integration Validation Results:")
    print(f"📊 Unused functions: {len(validation_results['unused_functions'])}")
    print(f"⚠️  Dependency violations: {len(validation_results['dependency_violations'])}")
    print(f"📋 Cleanup recommendations: {validation_results['cleanup_recommendations']}")
    
    # Perform dry run cleanup
    cleanup_report = orchestrator.automated_cleanup(dry_run=True)
    print(f"\n🧹 Cleanup Report (dry run):")
    print(f"Would remove {len(cleanup_report['removed_functions'])} functions")
    
    # Generate guidelines
    guidelines = orchestrator.generate_development_guidelines()
    print(f"\n📖 Development Guidelines Generated")