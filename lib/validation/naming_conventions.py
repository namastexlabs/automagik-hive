"""
Naming Convention Validation System

CRITICAL PREVENTION: Zero tolerance for forbidden naming patterns that violate codebase standards.
USER FEEDBACK: "its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, enhanced, etc"

This module provides comprehensive validation to prevent naming convention violations before they occur.
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class NamingViolation:
    """Represents a naming convention violation with details for correction."""
    violation_type: str
    forbidden_pattern: str
    suggested_alternative: str
    severity: str = "CRITICAL"


class NamingConventionValidator:
    """
    Comprehensive naming convention validator to prevent forbidden patterns.
    
    Enforces zero tolerance policy for modification-status naming patterns
    across all file names, function names, class names, and variable names.
    """
    
    # Absolutely forbidden patterns from behavioral learning
    FORBIDDEN_PATTERNS = {
        # Modification/improvement patterns (CRITICAL violations)
        r'fix(ed)?': "Remove 'fix' - describe what it actually does",
        r'enhanced?': "Remove 'enhanced' - describe the specific enhancement", 
        r'improved?': "Remove 'improved' - describe the actual improvement",
        r'updated?': "Remove 'updated' - describe what changed",
        r'better': "Remove 'better' - describe the specific improvement",
        r'new': "Remove 'new' - everything starts new, describe its purpose",
        r'v\d+': "Remove version suffixes - use proper versioning systems",
        r'_fix(ed)?': "Remove '_fix' suffix - describe the actual function",
        r'_enhanced?': "Remove '_enhanced' suffix - describe the enhancement",
        r'_improved?': "Remove '_improved' suffix - describe the improvement",
        r'_updated?': "Remove '_updated' suffix - describe what changed",
        r'_better': "Remove '_better' suffix - describe the improvement",
        r'_new': "Remove '_new' suffix - describe the purpose",
        r'_v\d+': "Remove version suffixes - use proper versioning",
        
        # Optimization patterns (violation risk)
        r'optimized?': "Consider: describe the specific optimization",
        r'refactored?': "Consider: describe the structural change",
        r'cleaned?': "Consider: describe what was cleaned",
        
        # Quality patterns (violation risk)  
        r'polished?': "Consider: describe the specific polish",
        r'refined?': "Consider: describe the refinement",
        r'streamlined?': "Consider: describe the streamlining"
    }
    
    # Historical violation patterns from behavioral learning
    HISTORICAL_VIOLATIONS = {
        "test_makefile_uninstall_enhanced.py": "test_makefile_uninstall_comprehensive.py",
        "test_makefile_uninstall_new.py": "test_makefile_uninstall_validation.py",
        "test_makefile_uninstall_fixed.py": "test_makefile_uninstall_verification.py",
        "test_makefile_uninstall_improved.py": "test_makefile_uninstall_advanced.py"
    }
    
    def validate_name(self, name: str, name_type: str = "general") -> Tuple[bool, List[NamingViolation]]:
        """
        Validate a name against forbidden patterns.
        
        Args:
            name: The name to validate (file, function, class, variable)
            name_type: Type of name being validated for context
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        name_lower = name.lower()
        
        # Check against forbidden patterns
        for pattern, suggestion in self.FORBIDDEN_PATTERNS.items():
            if re.search(pattern, name_lower, re.IGNORECASE):
                violations.append(NamingViolation(
                    violation_type=f"FORBIDDEN_PATTERN_{name_type.upper()}",
                    forbidden_pattern=pattern,
                    suggested_alternative=suggestion,
                    severity="CRITICAL"
                ))
        
        # Check against historical violations
        if name in self.HISTORICAL_VIOLATIONS:
            violations.append(NamingViolation(
                violation_type=f"HISTORICAL_VIOLATION_{name_type.upper()}",
                forbidden_pattern=name,
                suggested_alternative=self.HISTORICAL_VIOLATIONS[name],
                severity="CRITICAL"
            ))
        
        return len(violations) == 0, violations
    
    def validate_file_path(self, file_path: str) -> Tuple[bool, List[NamingViolation]]:
        """
        Validate a file path for naming convention compliance.
        
        Args:
            file_path: Full or relative file path to validate
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        path = Path(file_path)
        return self.validate_name(path.name, "file")
    
    def validate_function_name(self, function_name: str) -> Tuple[bool, List[NamingViolation]]:
        """Validate a function name for naming convention compliance."""
        return self.validate_name(function_name, "function")
    
    def validate_class_name(self, class_name: str) -> Tuple[bool, List[NamingViolation]]:
        """Validate a class name for naming convention compliance."""
        return self.validate_name(class_name, "class")
    
    def validate_variable_name(self, variable_name: str) -> Tuple[bool, List[NamingViolation]]:
        """Validate a variable name for naming convention compliance."""
        return self.validate_name(variable_name, "variable")
    
    def generate_purpose_based_alternative(self, problematic_name: str, context: str = "") -> str:
        """
        Generate a purpose-based alternative name suggestion.
        
        Args:
            problematic_name: The name containing forbidden patterns
            context: Additional context about the purpose
            
        Returns:
            Suggested alternative name focusing on purpose
        """
        # Remove forbidden patterns and suggest purpose-based alternatives
        clean_name = problematic_name.lower()
        
        # Remove common forbidden suffixes/prefixes and patterns
        forbidden_removals = [
            '_fixed', '_enhanced', '_improved', '_updated', '_better', '_new', '_v2', '_v3',
            'fixed_', 'enhanced_', 'improved_', 'updated_', 'better_', 'new_', 'v2_', 'v3_',
            'fixed', 'enhanced', 'improved', 'updated', 'better', 'new', 'v2', 'v3'
        ]
        
        for removal in forbidden_removals:
            clean_name = clean_name.replace(removal, '')
        
        # Clean up multiple underscores and dots
        clean_name = re.sub(r'_+', '_', clean_name).strip('_.')
        
        # Suggest purpose-based patterns
        if 'test' in clean_name:
            if 'makefile' in clean_name:
                return "test_makefile_comprehensive.py"
            else:
                base = clean_name.replace('test_', '').replace('.py', '')
                return f"test_{base}_validation.py"
        elif 'util' in clean_name or 'helper' in clean_name:
            base = clean_name.replace('.py', '')
            return f"{base}_operations.py"
        elif 'service' in clean_name:
            base = clean_name.replace('.py', '')
            return f"{base}_implementation.py"
        elif 'config' in clean_name:
            base = clean_name.replace('.py', '')
            return f"{base}_settings.py"
        else:
            base = clean_name.replace('.py', '')
            if base:
                return f"{base}_implementation.py"
            else:
                return "implementation.py"
    
    def get_violation_report(self, violations: List[NamingViolation], name: str) -> str:
        """
        Generate a detailed violation report for behavioral learning.
        
        Args:
            violations: List of violations found
            name: The problematic name
            
        Returns:
            Formatted violation report
        """
        if not violations:
            return f"✅ NAMING VALIDATION PASSED: '{name}'"
        
        report = [f"🚨 NAMING CONVENTION VIOLATION: '{name}'"]
        report.append("=" * 60)
        
        for violation in violations:
            report.append(f"VIOLATION TYPE: {violation.violation_type}")
            report.append(f"PATTERN: {violation.forbidden_pattern}")
            report.append(f"SUGGESTION: {violation.suggested_alternative}")
            report.append(f"SEVERITY: {violation.severity}")
            report.append("-" * 40)
        
        report.append("\n🎯 PURPOSE-BASED ALTERNATIVE:")
        report.append(f"   {self.generate_purpose_based_alternative(name)}")
        
        report.append("\n📚 NAMING PRINCIPLE:")
        report.append("   Clean, descriptive names that reflect PURPOSE, not modification status")
        
        return "\n".join(report)


# Global validator instance for easy access
naming_validator = NamingConventionValidator()


def validate_before_creation(name: str, name_type: str = "file") -> None:
    """
    Validation hook to be called before any file/function creation.
    
    Args:
        name: Name to validate
        name_type: Type of name (file, function, class, variable)
        
    Raises:
        ValueError: If naming convention violations are found
    """
    is_valid, violations = naming_validator.validate_name(name, name_type)
    
    if not is_valid:
        violation_report = naming_validator.get_violation_report(violations, name)
        raise ValueError(
            f"NAMING CONVENTION VIOLATION PREVENTED\n\n{violation_report}\n\n"
            f"USER FEEDBACK: 'its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, enhanced, etc'\n\n"
            f"BEHAVIORAL LEARNING: Zero tolerance for modification-status naming patterns"
        )


def validate_file_creation(file_path: str) -> None:
    """
    Pre-creation validation hook for file operations.
    
    Args:
        file_path: Path of file to be created
        
    Raises:
        ValueError: If file name violates naming conventions
    """
    path = Path(file_path)
    validate_before_creation(path.name, "file")


def validate_function_creation(function_name: str) -> None:
    """
    Pre-creation validation hook for function definitions.
    
    Args:
        function_name: Name of function to be created
        
    Raises:
        ValueError: If function name violates naming conventions
    """
    validate_before_creation(function_name, "function")


def validate_class_creation(class_name: str) -> None:
    """
    Pre-creation validation hook for class definitions.
    
    Args:
        class_name: Name of class to be created
        
    Raises:
        ValueError: If class name violates naming conventions
    """
    validate_before_creation(class_name, "class")


def log_violation_prevention(name: str, name_type: str, violations: List[NamingViolation]) -> None:
    """
    Log prevented violations for behavioral learning and system improvement.
    
    Args:
        name: The problematic name that was prevented
        name_type: Type of name (file, function, class, variable)
        violations: List of violations that were prevented
    """
    # This would integrate with the behavioral learning system
    # For now, we'll use simple logging
    print(f"🛡️ VIOLATION PREVENTED: {name_type} '{name}' - {len(violations)} violations blocked")
    for violation in violations:
        print(f"   - {violation.violation_type}: {violation.forbidden_pattern}")