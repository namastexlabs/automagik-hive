# Pre-Commit Hook System - Detailed Design Document (DDD)

## 🎯 System Overview

**Mission**: Enforce root-level file organization through automated pre-commit validation, preventing workspace pollution while maintaining developer productivity.

**Core Principle**: Zero-tolerance for unauthorized root-level file creation with intelligent exception handling and clear developer guidance.

## 🏛️ Clean Architecture Design

### 1. Domain Layer (Core Business Rules)

#### 1.1 Entities

```python
# src/hooks/domain/entities.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class FileOperation(Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"

class ValidationResult(Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    BYPASS = "bypass"

@dataclass
class FileChange:
    """Core entity representing a file system change"""
    path: str
    operation: FileOperation
    is_root_level: bool
    file_extension: Optional[str]
    is_directory: bool
    
    def get_suggested_path(self) -> Optional[str]:
        """Generate suggested alternative path based on file type"""
        if not self.is_root_level:
            return None
            
        if self.file_extension == ".md":
            if "readme" in self.path.lower():
                return None  # README.md is allowed at root
            return f"/genie/docs/{self.path}"
        elif self.is_directory:
            return f"/lib/{self.path}/"
        
        return None

@dataclass
class ValidationRule:
    """Core entity defining validation rules"""
    pattern: str
    rule_type: str  # "allow" or "block"
    description: str
    applies_to: List[FileOperation]
    
@dataclass
class HookValidationResult:
    """Result of hook validation"""
    result: ValidationResult
    blocked_files: List[FileChange]
    allowed_files: List[FileChange]
    bypass_files: List[FileChange]
    error_messages: List[str]
    suggestions: List[str]
```

#### 1.2 Value Objects

```python
# src/hooks/domain/value_objects.py
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class RootWhitelist:
    """Immutable whitelist of allowed root-level patterns"""
    patterns: List[str]
    
    @classmethod
    def default(cls) -> 'RootWhitelist':
        return cls(patterns=[
            "pyproject.toml",
            "README.md",
            "CHANGELOG.md", 
            "LICENSE",
            "Makefile",
            "Dockerfile*",
            "docker-compose*.yml",
            ".env.example",
            ".gitignore",
            ".github/",
            ".claude/",
            "scripts/",
            "templates/",
            "*.sh"  # Build scripts
        ])

@dataclass(frozen=True)
class GenieStructure:
    """Immutable genie workspace structure definition"""
    allowed_paths: List[str]
    
    @classmethod
    def default(cls) -> 'GenieStructure':
        return cls(allowed_paths=[
            "/genie/docs/",
            "/genie/ideas/", 
            "/genie/wishes/",
            "/genie/reports/",
            "/genie/experiments/",
            "/genie/knowledge/"
        ])
```

### 2. Application Layer (Use Cases)

#### 2.1 Use Case: Validate Pre-Commit Changes

```python
# src/hooks/application/validate_precommit.py
from typing import List
from ..domain.entities import FileChange, HookValidationResult, ValidationResult
from ..domain.value_objects import RootWhitelist, GenieStructure

class ValidatePreCommitUseCase:
    """Core use case for pre-commit validation"""
    
    def __init__(self, whitelist: RootWhitelist, genie_structure: GenieStructure):
        self.whitelist = whitelist
        self.genie_structure = genie_structure
        
    def execute(self, file_changes: List[FileChange], bypass_flag: bool = False) -> HookValidationResult:
        """Execute pre-commit validation"""
        if bypass_flag:
            return self._create_bypass_result(file_changes)
            
        blocked_files = []
        allowed_files = []
        error_messages = []
        suggestions = []
        
        for change in file_changes:
            if self._is_root_level_violation(change):
                blocked_files.append(change)
                error_messages.append(self._generate_error_message(change))
                suggestion = change.get_suggested_path()
                if suggestion:
                    suggestions.append(f"Consider moving {change.path} to {suggestion}")
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
    
    def _is_root_level_violation(self, change: FileChange) -> bool:
        """Check if file change violates root-level rules"""
        if not change.is_root_level:
            return False
            
        # Check whitelist
        for pattern in self.whitelist.patterns:
            if self._matches_pattern(change.path, pattern):
                return False
                
        # Special handling for .md files
        if change.file_extension == ".md":
            return not self._is_allowed_root_md(change.path)
            
        return True
    
    def _is_allowed_root_md(self, path: str) -> bool:
        """Check if .md file is allowed at root"""
        allowed_root_md = ["README.md", "CHANGELOG.md", "CLAUDE.md"]
        return path in allowed_root_md
        
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Pattern matching logic"""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
        
    def _generate_error_message(self, change: FileChange) -> str:
        """Generate human-readable error message"""
        if change.file_extension == ".md":
            return f"❌ BLOCKED: {change.path} - All .md files must be created in /genie/ structure (except README.md, CHANGELOG.md, CLAUDE.md)"
        elif change.is_directory:
            return f"❌ BLOCKED: {change.path}/ - New directories should be created in /lib/ or existing structure"
        else:
            return f"❌ BLOCKED: {change.path} - Unauthorized root-level file creation"
            
    def _create_bypass_result(self, file_changes: List[FileChange]) -> HookValidationResult:
        """Create result for bypass scenario"""
        return HookValidationResult(
            result=ValidationResult.BYPASS,
            blocked_files=[],
            allowed_files=[],
            bypass_files=file_changes,
            error_messages=["⚠️ BYPASS ACTIVE: Root-level file restrictions temporarily disabled"],
            suggestions=[]
        )
```

### 3. Infrastructure Layer (External Integrations)

#### 3.1 Git Integration

```python
# src/hooks/infrastructure/git_adapter.py
import subprocess
from typing import List
from ..domain.entities import FileChange, FileOperation

class GitAdapter:
    """Adapter for Git operations"""
    
    def get_staged_changes(self) -> List[FileChange]:
        """Get list of staged file changes"""
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                capture_output=True,
                text=True,
                check=True
            )
            
            changes = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                status, path = line.split('\t', 1)
                operation = self._map_git_status(status)
                
                change = FileChange(
                    path=path,
                    operation=operation,
                    is_root_level=self._is_root_level(path),
                    file_extension=self._get_extension(path),
                    is_directory=self._is_directory(path)
                )
                changes.append(change)
                
            return changes
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e}")
    
    def _map_git_status(self, status: str) -> FileOperation:
        """Map git status to FileOperation"""
        mapping = {
            'A': FileOperation.CREATE,
            'M': FileOperation.MODIFY,
            'D': FileOperation.DELETE,
            'R': FileOperation.RENAME
        }
        return mapping.get(status[0], FileOperation.MODIFY)
    
    def _is_root_level(self, path: str) -> bool:
        """Check if path is at root level"""
        return '/' not in path
    
    def _get_extension(self, path: str) -> str:
        """Get file extension"""
        import os
        return os.path.splitext(path)[1]
    
    def _is_directory(self, path: str) -> bool:
        """Check if path represents a directory"""
        import os
        return os.path.isdir(path) if os.path.exists(path) else path.endswith('/')
```

#### 3.2 File System Adapter

```python
# src/hooks/infrastructure/filesystem_adapter.py
import os
from typing import List

class FileSystemAdapter:
    """Adapter for file system operations"""
    
    def check_bypass_flag(self) -> bool:
        """Check for bypass flag file"""
        return os.path.exists('.git/hooks/BYPASS_ROOT_VALIDATION')
    
    def create_bypass_flag(self, reason: str) -> None:
        """Create bypass flag with reason"""
        with open('.git/hooks/BYPASS_ROOT_VALIDATION', 'w') as f:
            f.write(f"Bypass reason: {reason}\n")
            f.write(f"Created at: {os.popen('date').read().strip()}\n")
    
    def remove_bypass_flag(self) -> None:
        """Remove bypass flag"""
        if self.check_bypass_flag():
            os.remove('.git/hooks/BYPASS_ROOT_VALIDATION')
    
    def get_project_root(self) -> str:
        """Get project root directory"""
        return os.getcwd()
```

### 4. Presentation Layer (CLI Interface)

#### 4.1 Pre-Commit Hook Script

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Pre-Commit Hook - Root-Level File Validation${NC}"

# Check if Python validation script exists
if [ ! -f "scripts/validate_root_files.py" ]; then
    echo -e "${RED}❌ Validation script not found: scripts/validate_root_files.py${NC}"
    exit 1
fi

# Run Python validation
if uv run python scripts/validate_root_files.py; then
    echo -e "${GREEN}✅ Root-level file validation passed${NC}"
    exit 0
else
    echo -e "${RED}❌ Pre-commit validation failed${NC}"
    echo -e "${YELLOW}💡 To bypass this check temporarily (emergency only):${NC}"
    echo -e "${YELLOW}   git commit --no-verify${NC}"
    echo -e "${YELLOW}   Or create bypass flag: touch .git/hooks/BYPASS_ROOT_VALIDATION${NC}"
    exit 1
fi
```

#### 4.2 Python Validation Script

```python
#!/usr/bin/env python3
# scripts/validate_root_files.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.hooks.application.validate_precommit import ValidatePreCommitUseCase
from src.hooks.infrastructure.git_adapter import GitAdapter
from src.hooks.infrastructure.filesystem_adapter import FileSystemAdapter
from src.hooks.domain.value_objects import RootWhitelist, GenieStructure

def main():
    """Main pre-commit validation entry point"""
    try:
        # Initialize components
        git_adapter = GitAdapter()
        fs_adapter = FileSystemAdapter()
        
        # Get file changes
        file_changes = git_adapter.get_staged_changes()
        
        if not file_changes:
            print("ℹ️ No staged changes to validate")
            return 0
        
        # Check bypass flag
        bypass_flag = fs_adapter.check_bypass_flag()
        
        # Initialize use case
        whitelist = RootWhitelist.default()
        genie_structure = GenieStructure.default()
        use_case = ValidatePreCommitUseCase(whitelist, genie_structure)
        
        # Execute validation
        result = use_case.execute(file_changes, bypass_flag)
        
        # Display results
        display_validation_result(result)
        
        # Return appropriate exit code
        if result.result == ValidationResult.BLOCKED:
            return 1
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Pre-commit hook error: {e}")
        return 1

def display_validation_result(result):
    """Display validation results to user"""
    if result.result == ValidationResult.BYPASS:
        print("⚠️ BYPASS MODE ACTIVE - Validation skipped")
        for msg in result.error_messages:
            print(f"  {msg}")
        return
    
    if result.allowed_files:
        print(f"✅ Allowed files ({len(result.allowed_files)}):")
        for file_change in result.allowed_files:
            print(f"  ✓ {file_change.path}")
    
    if result.blocked_files:
        print(f"\n❌ Blocked files ({len(result.blocked_files)}):")
        for i, msg in enumerate(result.error_messages):
            print(f"  {msg}")
    
    if result.suggestions:
        print(f"\n💡 Suggestions:")
        for suggestion in result.suggestions:
            print(f"  {suggestion}")
    
    if result.blocked_files:
        print(f"\n🛠️ Quick fixes:")
        print(f"  • Move .md files to /genie/docs/ or /genie/ideas/")
        print(f"  • Move source code to /lib/ or existing modules")
        print(f"  • Check CLAUDE.md workspace organization rules")

if __name__ == "__main__":
    sys.exit(main())
```

## 🔧 Component Integration

### 5. GitHub Actions Integration

```yaml
# .github/workflows/validate-root-organization.yml
name: Validate Root Organization

on:
  pull_request:
    branches: [ main, dev ]
  push:
    branches: [ main, dev ]

jobs:
  validate-root-files:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run root-level validation
      run: |
        # Get changed files in PR
        if [ "${{ github.event_name }}" = "pull_request" ]; then
          CHANGED_FILES=$(git diff --name-only origin/${{ github.base_ref }}...HEAD)
        else
          CHANGED_FILES=$(git diff --name-only HEAD~1..HEAD)
        fi
        
        echo "Changed files:"
        echo "$CHANGED_FILES"
        
        # Run validation on changed files
        uv run python scripts/validate_root_files_ci.py "$CHANGED_FILES"
    
    - name: Comment PR if validation fails
      if: failure() && github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '❌ **Root-level file organization violation detected**\n\nPlease move files to appropriate directories:\n• `.md` files → `/genie/docs/` or `/genie/ideas/`\n• Source code → `/lib/` or existing modules\n\nSee CLAUDE.md for workspace organization rules.'
          })
```

### 6. Developer Experience Enhancements

#### 6.1 Installation Script

```bash
#!/bin/bash
# scripts/install_pre_commit_hooks.sh

echo "🔧 Installing Pre-Commit Hooks for Root-Level File Validation"

# Make hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy pre-commit hook
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Create validation script if it doesn't exist
if [ ! -f "scripts/validate_root_files.py" ]; then
    echo "📝 Creating validation script..."
    # Script creation logic here
fi

echo "✅ Pre-commit hooks installed successfully"
echo "💡 To bypass validation temporarily: git commit --no-verify"
echo "🚨 Emergency bypass: touch .git/hooks/BYPASS_ROOT_VALIDATION"
```

#### 6.2 Hook Management Commands

```bash
# Makefile additions
.PHONY: install-hooks uninstall-hooks bypass-hooks restore-hooks

install-hooks:
	@echo "🔧 Installing pre-commit hooks..."
	@bash scripts/install_pre_commit_hooks.sh

uninstall-hooks:
	@echo "🗑️ Removing pre-commit hooks..."
	@rm -f .git/hooks/pre-commit
	@rm -f .git/hooks/BYPASS_ROOT_VALIDATION

bypass-hooks:
	@echo "⚠️ Creating bypass flag (emergency use only)..."
	@touch .git/hooks/BYPASS_ROOT_VALIDATION
	@echo "Temporary bypass for critical fix" > .git/hooks/BYPASS_ROOT_VALIDATION

restore-hooks:
	@echo "🔄 Restoring hook validation..."
	@rm -f .git/hooks/BYPASS_ROOT_VALIDATION
	@echo "✅ Hook validation restored"

test-hooks:
	@echo "🧪 Testing pre-commit hook validation..."
	@uv run python scripts/validate_root_files.py --test
```

## 🛡️ Security & Safety Features

### 7. Emergency Bypass System

```python
# src/hooks/domain/bypass_manager.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class BypassRequest:
    reason: str
    duration_hours: int
    created_by: str
    created_at: datetime
    
class BypassManager:
    """Manage emergency bypass functionality"""
    
    def create_bypass(self, reason: str, duration_hours: int = 1) -> bool:
        """Create temporary bypass with expiration"""
        bypass = BypassRequest(
            reason=reason,
            duration_hours=duration_hours,
            created_by=self._get_git_user(),
            created_at=datetime.now()
        )
        
        return self._write_bypass_file(bypass)
    
    def is_bypass_active(self) -> bool:
        """Check if bypass is active and not expired"""
        bypass = self._read_bypass_file()
        if not bypass:
            return False
            
        # Check if expired
        expiry = bypass.created_at + timedelta(hours=bypass.duration_hours)
        if datetime.now() > expiry:
            self._remove_bypass_file()
            return False
            
        return True
    
    def _get_git_user(self) -> str:
        """Get current git user"""
        import subprocess
        try:
            result = subprocess.run(['git', 'config', 'user.name'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
```

## 📊 Testing Strategy

### 8. Comprehensive Test Suite

```python
# tests/hooks/test_validation_use_case.py
import pytest
from src.hooks.application.validate_precommit import ValidatePreCommitUseCase
from src.hooks.domain.entities import FileChange, FileOperation, ValidationResult
from src.hooks.domain.value_objects import RootWhitelist, GenieStructure

class TestValidatePreCommitUseCase:
    
    def setup_method(self):
        self.whitelist = RootWhitelist.default()
        self.genie_structure = GenieStructure.default()
        self.use_case = ValidatePreCommitUseCase(self.whitelist, self.genie_structure)
    
    def test_allowed_root_files(self):
        """Test that whitelisted files are allowed"""
        changes = [
            FileChange("README.md", FileOperation.CREATE, True, ".md", False),
            FileChange("pyproject.toml", FileOperation.MODIFY, True, ".toml", False),
        ]
        
        result = self.use_case.execute(changes)
        
        assert result.result == ValidationResult.ALLOWED
        assert len(result.blocked_files) == 0
        assert len(result.allowed_files) == 2
    
    def test_blocked_root_md_files(self):
        """Test that non-whitelisted .md files are blocked"""
        changes = [
            FileChange("setup.md", FileOperation.CREATE, True, ".md", False),
        ]
        
        result = self.use_case.execute(changes)
        
        assert result.result == ValidationResult.BLOCKED
        assert len(result.blocked_files) == 1
        assert "All .md files must be created in /genie/ structure" in result.error_messages[0]
    
    def test_bypass_mode(self):
        """Test bypass functionality"""
        changes = [
            FileChange("blocked.md", FileOperation.CREATE, True, ".md", False),
        ]
        
        result = self.use_case.execute(changes, bypass_flag=True)
        
        assert result.result == ValidationResult.BYPASS
        assert len(result.bypass_files) == 1
    
    def test_suggestion_generation(self):
        """Test that suggestions are generated for blocked files"""
        changes = [
            FileChange("docs.md", FileOperation.CREATE, True, ".md", False),
        ]
        
        result = self.use_case.execute(changes)
        
        assert len(result.suggestions) > 0
        assert "/genie/docs/" in result.suggestions[0]
```

## 🚀 Deployment & Configuration

### 9. Installation & Setup

```python
# scripts/setup_hook_system.py
#!/usr/bin/env python3

import os
import shutil
import stat
from pathlib import Path

def setup_hook_system():
    """Set up the complete pre-commit hook system"""
    
    print("🚀 Setting up Pre-Commit Hook System for Root-Level File Validation")
    
    # Create necessary directories
    dirs_to_create = [
        "src/hooks/domain",
        "src/hooks/application", 
        "src/hooks/infrastructure",
        "tests/hooks",
        ".git/hooks"
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created directory: {dir_path}")
    
    # Install pre-commit hook
    hook_source = "scripts/pre-commit-hook.sh"
    hook_dest = ".git/hooks/pre-commit"
    
    if Path(hook_source).exists():
        shutil.copy2(hook_source, hook_dest)
        # Make executable
        st = os.stat(hook_dest)
        os.chmod(hook_dest, st.st_mode | stat.S_IEXEC)
        print(f"  ✓ Installed pre-commit hook: {hook_dest}")
    
    # Create validation script
    validation_script = "scripts/validate_root_files.py"
    if not Path(validation_script).exists():
        print(f"  ⚠️ Create validation script manually: {validation_script}")
    
    print("✅ Pre-commit hook system setup complete!")
    print("💡 Test with: make test-hooks")

if __name__ == "__main__":
    setup_hook_system()
```

## 📈 Monitoring & Analytics

### 10. Hook Performance Metrics

```python
# src/hooks/infrastructure/metrics_collector.py
import time
import json
from datetime import datetime
from typing import Dict, Any

class HookMetricsCollector:
    """Collect performance and usage metrics"""
    
    def __init__(self):
        self.metrics_file = ".git/hooks/metrics.json"
    
    def record_validation(self, 
                         duration_ms: float,
                         files_checked: int,
                         blocked_count: int,
                         bypass_used: bool) -> None:
        """Record validation metrics"""
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "files_checked": files_checked,
            "blocked_count": blocked_count,
            "bypass_used": bypass_used,
            "success": blocked_count == 0
        }
        
        self._append_metric(metric)
    
    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of metrics for the last N days"""
        metrics = self._load_metrics()
        
        # Filter by date range
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        recent_metrics = [m for m in metrics 
                         if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff]
        
        if not recent_metrics:
            return {"total_validations": 0}
        
        return {
            "total_validations": len(recent_metrics),
            "success_rate": sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics),
            "avg_duration_ms": sum(m["duration_ms"] for m in recent_metrics) / len(recent_metrics),
            "total_files_checked": sum(m["files_checked"] for m in recent_metrics),
            "total_blocks": sum(m["blocked_count"] for m in recent_metrics),
            "bypass_usage": sum(1 for m in recent_metrics if m["bypass_used"])
        }
```

## 🔄 Integration with Existing Systems

### 11. CLAUDE.md Integration

The hook system enforces the existing CLAUDE.md workspace rules:

```python
# src/hooks/domain/claude_md_rules.py
from typing import List, Dict

class ClaudeMdRulesValidator:
    """Validate against CLAUDE.md workspace organization rules"""
    
    GENIE_STRUCTURE_RULES = {
        "ideas": "Brainstorming and analysis files",
        "wishes": "Execution-ready plans", 
        "docs": "Design documents and architecture",
        "reports": "Completion reports and findings",
        "experiments": "Prototype and test files",
        "knowledge": "Learning and wisdom storage"
    }
    
    ROOT_PROHIBITED_PATTERNS = [
        "*.md",  # Except README.md, CHANGELOG.md, CLAUDE.md
        "temp_*",
        "draft_*",
        "test_*"
    ]
    
    def validate_genie_structure(self, path: str) -> bool:
        """Validate file follows proper /genie/ structure"""
        if not path.startswith("/genie/"):
            return False
            
        path_parts = path.split("/")
        if len(path_parts) < 3:
            return False
            
        genie_folder = path_parts[2]
        return genie_folder in self.GENIE_STRUCTURE_RULES
    
    def get_suggested_genie_path(self, filename: str) -> str:
        """Suggest appropriate /genie/ path based on filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ["plan", "wish", "todo"]):
            return f"/genie/wishes/{filename}"
        elif any(word in filename_lower for word in ["design", "architecture", "ddd"]):
            return f"/genie/docs/{filename}"
        elif any(word in filename_lower for word in ["idea", "analysis", "brain"]):
            return f"/genie/ideas/{filename}"
        elif any(word in filename_lower for word in ["report", "complete", "summary"]):
            return f"/genie/reports/{filename}"
        else:
            return f"/genie/docs/{filename}"
```

## 📋 Implementation Checklist

### Phase 1: Core System (Week 1)
- [ ] Implement domain entities and value objects
- [ ] Create validation use case with comprehensive rules
- [ ] Build Git adapter for staged file detection
- [ ] Create basic pre-commit hook script
- [ ] Write core validation logic

### Phase 2: Developer Experience (Week 2)  
- [ ] Add bypass mechanism with expiration
- [ ] Create installation and setup scripts
- [ ] Implement clear error messages and suggestions
- [ ] Add Makefile commands for hook management
- [ ] Create comprehensive test suite

### Phase 3: CI/CD Integration (Week 3)
- [ ] Implement GitHub Actions validation
- [ ] Add PR comment automation
- [ ] Create metrics collection system
- [ ] Build monitoring dashboard
- [ ] Add performance optimization

### Phase 4: Advanced Features (Week 4)
- [ ] Cross-agent behavioral enforcement integration
- [ ] Advanced pattern matching and rules
- [ ] Integration with existing MCP tools
- [ ] Custom rule configuration support
- [ ] Full documentation and examples

## 🎯 Success Metrics

### Key Performance Indicators
- **Prevention Rate**: 95%+ of unauthorized root-level files blocked
- **Developer Satisfaction**: <30 second resolution time for validation errors
- **Bypass Usage**: <5% of commits require bypass (indicates good UX)
- **False Positive Rate**: <1% of legitimate files blocked
- **Performance**: <500ms validation time for typical commits

### Quality Gates
- [ ] Zero false positives for whitelisted files
- [ ] Clear, actionable error messages for all violations
- [ ] Emergency bypass works reliably under all conditions
- [ ] CI/CD integration prevents bad commits from reaching main
- [ ] Cross-agent learning integration updates rules dynamically

---

## 🏆 Architectural Quality Validation

### Clean Architecture Compliance ✅
- **Domain Layer**: Pure business logic with zero external dependencies
- **Application Layer**: Use cases orchestrate domain entities
- **Infrastructure Layer**: External system adapters (Git, filesystem)
- **Presentation Layer**: CLI interface and hook scripts

### Design Patterns Applied ✅
- **Repository Pattern**: GitAdapter abstracts Git operations
- **Strategy Pattern**: Multiple validation rule strategies
- **Factory Pattern**: Default configurations for value objects
- **Observer Pattern**: Metrics collection during validation
- **Command Pattern**: Bypass operations as discrete commands

### SOLID Principles ✅
- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Rules extensible without modifying core logic
- **Liskov Substitution**: Validation strategies are interchangeable
- **Interface Segregation**: Focused interfaces for each concern
- **Dependency Inversion**: Abstractions don't depend on details

## 📝 Implementation Blueprint

### File Structure
```
src/hooks/
├── domain/
│   ├── entities.py              # Core business entities
│   ├── value_objects.py         # Immutable configuration objects
│   └── claude_md_rules.py       # CLAUDE.md integration rules
├── application/
│   └── validate_precommit.py    # Main validation use case
├── infrastructure/
│   ├── git_adapter.py           # Git operations adapter
│   ├── filesystem_adapter.py    # File system operations
│   └── metrics_collector.py     # Performance metrics
└── presentation/
    └── cli_interface.py         # Command-line interface

scripts/
├── pre-commit-hook.sh           # Bash hook script
├── validate_root_files.py       # Python validation entry point
├── install_pre_commit_hooks.sh  # Installation script
└── setup_hook_system.py        # Complete system setup

tests/hooks/
├── test_validation_use_case.py  # Core logic tests
├── test_git_adapter.py          # Git integration tests
└── test_claude_md_rules.py      # Rule validation tests

.github/workflows/
└── validate-root-organization.yml # CI/CD integration
```

This comprehensive design provides a robust, maintainable solution for enforcing root-level file organization while maintaining excellent developer experience and emergency flexibility.