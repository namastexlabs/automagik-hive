"""Application layer use case for pre-commit validation.

This module contains the core business logic for validating file changes
against root-level organization rules. It orchestrates domain entities
and implements the main validation workflow.
"""


from ..domain.entities import FileChange, HookValidationResult, ValidationResult
from ..domain.value_objects import GenieStructure, RootWhitelist, ValidationConfig


class ValidatePreCommitUseCase:
    """Core use case for pre-commit validation.
    
    This class implements the main business logic for validating file changes
    against organizational rules. It processes file changes and determines
    whether to allow, block, or bypass validation.
    """

    def __init__(
        self,
        whitelist: RootWhitelist,
        genie_structure: GenieStructure,
        config: ValidationConfig = None
    ):
        """Initialize validation use case with configuration.
        
        Args:
            whitelist: Allowed root-level file patterns
            genie_structure: Valid genie workspace structure
            config: Validation configuration, uses default if None
        """
        self.whitelist = whitelist
        self.genie_structure = genie_structure
        self.config = config or ValidationConfig.default()

    def execute(
        self,
        file_changes: list[FileChange],
        bypass_flag: bool = False
    ) -> HookValidationResult:
        """Execute pre-commit validation on file changes.
        
        Args:
            file_changes: List of file changes to validate
            bypass_flag: Whether to bypass validation (emergency mode)
            
        Returns:
            HookValidationResult containing validation outcome and details
        """
        if bypass_flag:
            return self._create_bypass_result(file_changes)

        blocked_files = []
        allowed_files = []
        error_messages = []
        suggestions = []

        for change in file_changes:
            validation_outcome = self._validate_file_change(change)

            if validation_outcome["blocked"]:
                blocked_files.append(change)
                error_messages.append(validation_outcome["error_message"])

                suggestion = change.get_suggested_path()
                if suggestion:
                    suggestions.append(f"📍 Move {change.path} → {suggestion}")

                # Add additional context-specific suggestions
                additional_suggestions = self._get_additional_suggestions(change)
                suggestions.extend(additional_suggestions)
            else:
                allowed_files.append(change)

        result = ValidationResult.BLOCKED if blocked_files else ValidationResult.ALLOWED

        return HookValidationResult(
            result=result,
            blocked_files=blocked_files,
            allowed_files=allowed_files,
            bypass_files=[],
            error_messages=error_messages,
            suggestions=suggestions
        )

    def _validate_file_change(self, change: FileChange) -> dict:
        """Validate a single file change against all rules.
        
        Args:
            change: FileChange to validate
            
        Returns:
            Dictionary with validation result and error message
        """
        # Allow non-root-level files
        if not change.is_root_level:
            return {"blocked": False, "error_message": ""}

        # Check against whitelist patterns
        if self.whitelist.matches_pattern(change.path):
            return {"blocked": False, "error_message": ""}

        # Special handling for .md files
        if change.file_extension == ".md":
            if self.config.is_allowed_root_md(change.path):
                return {"blocked": False, "error_message": ""}
            return {
                "blocked": True,
                "error_message": self._generate_md_error_message(change)
            }

        # Special handling for directories
        if change.is_directory:
            return {
                "blocked": True,
                "error_message": self._generate_directory_error_message(change)
            }

        # Block all other root-level files
        return {
            "blocked": True,
            "error_message": self._generate_generic_error_message(change)
        }

    def _generate_md_error_message(self, change: FileChange) -> str:
        """Generate error message for blocked markdown files.
        
        Args:
            change: FileChange for markdown file
            
        Returns:
            Human-readable error message
        """
        allowed_files = ", ".join(self.config.allow_root_md_files)
        return (
            f"❌ BLOCKED: {change.path}\n"
            f"   📝 Markdown files must be created in /genie/ structure\n"
            f"   ✅ Only {allowed_files} are allowed at root\n"
            f"   💡 Consider /genie/docs/ for documentation or /genie/ideas/ for notes"
        )

    def _generate_directory_error_message(self, change: FileChange) -> str:
        """Generate error message for blocked directories.
        
        Args:
            change: FileChange for directory
            
        Returns:
            Human-readable error message
        """
        return (
            f"❌ BLOCKED: {change.path}/\n"
            f"   📁 New directories should be created in /lib/ or existing structure\n"
            f"   💡 Consider /lib/{change.path}/ for shared libraries"
        )

    def _generate_generic_error_message(self, change: FileChange) -> str:
        """Generate error message for other blocked files.
        
        Args:
            change: FileChange for blocked file
            
        Returns:
            Human-readable error message
        """
        return (
            f"❌ BLOCKED: {change.path}\n"
            f"   🚫 Unauthorized root-level file creation\n"
            f"   📋 Check project whitelist or move to appropriate subdirectory"
        )

    def _get_additional_suggestions(self, change: FileChange) -> list[str]:
        """Get additional context-specific suggestions for blocked files.
        
        Args:
            change: FileChange that was blocked
            
        Returns:
            List of additional suggestion strings
        """
        suggestions = []

        if change.file_extension == ".py":
            suggestions.append("🐍 Python files belong in /lib/, /api/, or /ai/ directories")
        elif change.file_extension in [".yaml", ".yml"]:
            suggestions.append("⚙️ Configuration files should be in appropriate service directories")
        elif change.file_extension == ".json":
            suggestions.append("📄 JSON files should be in /lib/config/ or relevant service directory")
        elif change.file_extension in [".txt", ".log"]:
            suggestions.append("📝 Text files should be in /docs/ or appropriate subdirectory")

        # File-specific suggestions based on name patterns
        filename_lower = change.path.lower()
        if "test" in filename_lower:
            suggestions.append("🧪 Test files belong in /tests/ directory")
        elif "config" in filename_lower:
            suggestions.append("⚙️ Configuration files belong in /lib/config/ or service directories")
        elif "script" in filename_lower:
            suggestions.append("📜 Scripts should be in /scripts/ directory")

        return suggestions

    def _create_bypass_result(self, file_changes: list[FileChange]) -> HookValidationResult:
        """Create validation result for bypass scenario.
        
        Args:
            file_changes: List of file changes being bypassed
            
        Returns:
            HookValidationResult indicating bypass mode
        """
        return HookValidationResult(
            result=ValidationResult.BYPASS,
            blocked_files=[],
            allowed_files=[],
            bypass_files=file_changes,
            error_messages=[
                "⚠️ BYPASS ACTIVE: Root-level file restrictions temporarily disabled",
                f"📊 Processing {len(file_changes)} files without validation"
            ],
            suggestions=[
                "🔧 Remember to remove bypass flag after emergency fix",
                "📋 Review bypassed files for proper organization later"
            ]
        )


class ValidationMetrics:
    """Helper class for collecting validation metrics."""

    def __init__(self):
        self.total_validations = 0
        self.blocked_count = 0
        self.bypassed_count = 0
        self.file_type_stats = {}

    def record_validation(self, result: HookValidationResult):
        """Record metrics from a validation result.
        
        Args:
            result: HookValidationResult to extract metrics from
        """
        self.total_validations += 1

        if result.result == ValidationResult.BLOCKED:
            self.blocked_count += 1
        elif result.result == ValidationResult.BYPASS:
            self.bypassed_count += 1

        # Record file type statistics
        all_files = result.blocked_files + result.allowed_files + result.bypass_files
        for file_change in all_files:
            ext = file_change.file_extension or "no_extension"
            self.file_type_stats[ext] = self.file_type_stats.get(ext, 0) + 1

    def get_summary(self) -> dict:
        """Get summary of collected metrics.
        
        Returns:
            Dictionary containing validation metrics
        """
        return {
            "total_validations": self.total_validations,
            "blocked_count": self.blocked_count,
            "bypassed_count": self.bypassed_count,
            "success_rate": (
                (self.total_validations - self.blocked_count) / self.total_validations
                if self.total_validations > 0 else 1.0
            ),
            "file_type_stats": self.file_type_stats
        }
