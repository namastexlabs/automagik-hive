"""
Project Orchestration Agent Tools - Project Lifecycle and Multi-Agent Coordination

Extracted and adapted from Serena's project management and orchestration capabilities.
Focuses on project lifecycle, memory management, and workflow coordination.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from agno.tools import tool


@tool
def onboarding(project_type: str | None = None, force_refresh: bool = False) -> str:
    """
    Perform comprehensive project onboarding to understand structure and setup development context.

    Args:
        project_type: Optional project type hint (python, javascript, java, etc.)
        force_refresh: Whether to force refresh onboarding even if already performed

    Returns:
        Onboarding instructions and project analysis results
    """
    try:
        project_root = Path(os.getcwd())

        # Check if onboarding was already performed
        if not force_refresh:
            onboarding_status = check_onboarding_performed()
            if "already performed" in onboarding_status:
                return (
                    onboarding_status
                    + "\n\nUse force_refresh=True to re-run onboarding."
                )

        # Initialize onboarding analysis
        analysis_results = {
            "project_root": str(project_root),
            "timestamp": datetime.now().isoformat(),
            "project_structure": {},
            "languages_detected": [],
            "build_systems": [],
            "key_files": [],
            "dependencies": {},
            "testing_setup": {},
            "recommendations": [],
        }

        # Analyze project structure
        structure_analysis = _analyze_project_structure(project_root)
        analysis_results["project_structure"] = structure_analysis

        # Detect programming languages
        languages = _detect_programming_languages(project_root)
        analysis_results["languages_detected"] = languages

        # Detect build systems and configuration files
        build_systems = _detect_build_systems(project_root)
        analysis_results["build_systems"] = build_systems

        # Identify key files
        key_files = _identify_key_files(project_root)
        analysis_results["key_files"] = key_files

        # Analyze dependencies
        dependencies = _analyze_dependencies(project_root)
        analysis_results["dependencies"] = dependencies

        # Analyze testing setup
        testing_setup = _analyze_testing_setup(project_root)
        analysis_results["testing_setup"] = testing_setup

        # Generate recommendations
        recommendations = _generate_recommendations(analysis_results)
        analysis_results["recommendations"] = recommendations

        # Store onboarding results in memory
        memory_content = _format_onboarding_memory(analysis_results)
        write_memory("project_onboarding", memory_content)

        # Generate onboarding report
        report = _format_onboarding_report(analysis_results)

        return f"✅ Project onboarding completed successfully!\n\n{report}"

    except Exception as e:
        return f"Error during project onboarding: {e!s}"


@tool
def check_onboarding_performed() -> str:
    """
    Check whether project onboarding was already performed.

    Returns:
        Status of project onboarding with summary if available
    """
    try:
        # Check if onboarding memory exists
        memories = list_memories()

        if "project_onboarding" in memories:
            onboarding_memory = read_memory("project_onboarding")

            # Extract timestamp and basic info
            try:
                if "Onboarding Date:" in onboarding_memory:
                    timestamp_line = [
                        line
                        for line in onboarding_memory.split("\n")
                        if "Onboarding Date:" in line
                    ][0]
                    timestamp = timestamp_line.split("Onboarding Date:")[1].strip()

                    summary = f"✅ Onboarding already performed on {timestamp}\n\n"
                    summary += "Available project memories:\n"

                    for memory_name in memories:
                        summary += f"  📝 {memory_name}\n"

                    summary += "\n💡 You can read specific memories or use existing project context."
                    return summary
            except:
                pass

            return "✅ Onboarding already performed. Project memories are available."

        return "❌ Onboarding not performed yet. Run the 'onboarding' tool to analyze the project."

    except Exception as e:
        return f"Error checking onboarding status: {e!s}"


@tool
def activate_project(
    project_path: str | None = None, project_name: str | None = None
) -> str:
    """
    Activate a project for development work.

    Args:
        project_path: Optional path to project directory
        project_name: Optional project name for identification

    Returns:
        Project activation status and configuration summary
    """
    try:
        if project_path:
            target_path = Path(project_path).resolve()
            if not target_path.exists():
                return f"Error: Project path '{project_path}' does not exist"
            os.chdir(target_path)
        else:
            target_path = Path(os.getcwd())

        project_name = project_name or target_path.name

        # Check if project has configuration files
        config_files = []
        for config_file in [
            "package.json",
            "requirements.txt",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "pyproject.toml",
        ]:
            if (target_path / config_file).exists():
                config_files.append(config_file)

        # Create project activation record
        activation_info = {
            "project_name": project_name,
            "project_path": str(target_path),
            "activated_at": datetime.now().isoformat(),
            "config_files": config_files,
            "git_repository": (target_path / ".git").exists(),
        }

        # Store activation info in memory
        activation_memory = f"""# Project Activation - {project_name}

**Activation Date:** {activation_info["activated_at"]}
**Project Path:** {activation_info["project_path"]}
**Git Repository:** {"Yes" if activation_info["git_repository"] else "No"}

## Configuration Files Found:
{chr(10).join(f"- {cf}" for cf in config_files) if config_files else "- No standard config files found"}

## Project Status:
- Project successfully activated for development
- Working directory set to: {target_path}
- Ready for development operations

## Next Steps:
1. Run onboarding if not already performed
2. Analyze project structure and dependencies
3. Set up development workflow as needed
"""

        write_memory(f"project_activation_{project_name.lower()}", activation_memory)

        result = f"✅ Project '{project_name}' activated successfully!\n"
        result += f"📁 Working directory: {target_path}\n"

        if config_files:
            result += f"📋 Configuration files: {', '.join(config_files)}\n"

        if activation_info["git_repository"]:
            result += "📦 Git repository detected\n"

        result += "\n💡 Project is ready for development. Consider running onboarding for detailed analysis."

        return result

    except Exception as e:
        return f"Error activating project: {e!s}"


@tool
def get_current_config() -> str:
    """
    Get current project configuration and agent status.

    Returns:
        Comprehensive configuration overview including project state and available capabilities
    """
    try:
        project_root = Path(os.getcwd())

        # Gather configuration information
        config_info = {
            "project_root": str(project_root),
            "timestamp": datetime.now().isoformat(),
            "memories_available": [],
            "project_structure": {},
            "git_status": {},
            "agent_capabilities": {},
        }

        # Get available memories
        try:
            memories = list_memories()
            config_info["memories_available"] = memories
        except:
            config_info["memories_available"] = []

        # Analyze current project structure
        structure = {
            "total_files": 0,
            "directories": [],
            "key_files": [],
            "languages_detected": [],
        }

        for item in project_root.rglob("*"):
            if item.is_file():
                structure["total_files"] += 1
                if item.suffix in [
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".cpp",
                    ".c",
                    ".h",
                    ".rb",
                    ".go",
                    ".rs",
                ]:
                    structure["languages_detected"].append(item.suffix)
                if item.name in [
                    "README.md",
                    "package.json",
                    "requirements.txt",
                    "Cargo.toml",
                    "pom.xml",
                ]:
                    structure["key_files"].append(str(item.relative_to(project_root)))
            elif item.is_dir() and not any(
                skip in item.parts for skip in [".git", "node_modules", "__pycache__"]
            ):
                if len(structure["directories"]) < 10:  # Limit output
                    structure["directories"].append(str(item.relative_to(project_root)))

        # Remove duplicates and sort
        structure["languages_detected"] = sorted(
            list(set(structure["languages_detected"]))
        )
        config_info["project_structure"] = structure

        # Get Git status if available
        git_dir = project_root / ".git"
        if git_dir.exists():
            config_info["git_status"] = {
                "repository": True,
                "git_directory": str(git_dir),
            }
        else:
            config_info["git_status"] = {"repository": False}

        # Agent capabilities summary
        config_info["agent_capabilities"] = {
            "project_management": [
                "onboarding",
                "activation",
                "configuration",
                "memory_management",
            ],
            "available_agents": [
                "code-understanding-agent",
                "file-management-agent",
                "code-editing-agent",
            ],
            "coordination_modes": [
                "workflow_orchestration",
                "task_delegation",
                "result_synthesis",
            ],
        }

        # Format output
        output = [f"📊 Current Project Configuration - {project_root.name}\n"]
        output.append(f"📅 Generated: {config_info['timestamp']}")
        output.append(f"📁 Project Root: {config_info['project_root']}")

        # Project structure
        output.append("\n🏗️  Project Structure:")
        output.append(f"   📄 Total Files: {structure['total_files']}")
        output.append(f"   🗂️  Key Directories: {len(structure['directories'])}")
        if structure["key_files"]:
            output.append(f"   🔑 Key Files: {', '.join(structure['key_files'])}")
        if structure["languages_detected"]:
            output.append(
                f"   💻 Languages: {', '.join(structure['languages_detected'])}"
            )

        # Git status
        output.append(
            f"\n📦 Git Repository: {'Yes' if config_info['git_status']['repository'] else 'No'}"
        )

        # Available memories
        output.append(
            f"\n🧠 Available Memories ({len(config_info['memories_available'])}):"
        )
        if config_info["memories_available"]:
            for memory in config_info["memories_available"]:
                output.append(f"   📝 {memory}")
        else:
            output.append("   (No memories stored yet)")

        # Agent capabilities
        output.append("\n🤖 Agent Coordination Capabilities:")
        output.append(
            f"   🔄 Available Agents: {len(config_info['agent_capabilities']['available_agents'])}"
        )
        for agent in config_info["agent_capabilities"]["available_agents"]:
            output.append(f"      - {agent}")

        output.append("\n⚙️  Coordination Modes:")
        for mode in config_info["agent_capabilities"]["coordination_modes"]:
            output.append(f"   - {mode.replace('_', ' ').title()}")

        return "\n".join(output)

    except Exception as e:
        return f"Error getting current configuration: {e!s}"


@tool
def read_memory(memory_name: str) -> str:
    """
    Read a named memory from the project memory store.

    Args:
        memory_name: Name of the memory to read

    Returns:
        Memory content or error message
    """
    try:
        project_root = Path(os.getcwd())
        memory_dir = project_root / ".serena_memories"

        if not memory_dir.exists():
            return "Memory store not initialized. No memories available."

        memory_file = memory_dir / f"{memory_name}.md"

        if not memory_file.exists():
            available_memories = [f.stem for f in memory_dir.glob("*.md")]
            available_list = (
                ", ".join(available_memories) if available_memories else "none"
            )
            return f"Memory '{memory_name}' not found. Available memories: {available_list}"

        content = memory_file.read_text(encoding="utf-8")

        # Add metadata header
        stat = memory_file.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        header = f"📝 Memory: {memory_name}\n"
        header += f"📅 Last Modified: {modified_time}\n"
        header += f"📊 Size: {len(content)} characters\n\n"

        return header + content

    except Exception as e:
        return f"Error reading memory '{memory_name}': {e!s}"


@tool
def write_memory(memory_name: str, content: str) -> str:
    """
    Write a named memory to the project memory store.

    Args:
        memory_name: Name of the memory to write
        content: Content to store in memory

    Returns:
        Success message or error details
    """
    try:
        project_root = Path(os.getcwd())
        memory_dir = project_root / ".serena_memories"

        # Create memory directory if it doesn't exist
        memory_dir.mkdir(exist_ok=True)

        # Sanitize memory name
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_" for c in memory_name
        )
        memory_file = memory_dir / f"{safe_name}.md"

        # Add metadata header to content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_content = f"# {memory_name}\n\n"
        formatted_content += f"*Created/Updated: {timestamp}*\n\n"
        formatted_content += content

        # Write memory file
        memory_file.write_text(formatted_content, encoding="utf-8")

        # Add to gitignore if not already there
        _ensure_memory_gitignore(project_root)

        result = f"✅ Memory '{memory_name}' written successfully"
        result += f"\n📊 Stored {len(content)} characters"
        result += f"\n📁 Location: {memory_file.relative_to(project_root)}"

        return result

    except Exception as e:
        return f"Error writing memory '{memory_name}': {e!s}"


@tool
def list_memories() -> str:
    """
    List all available memories in the project memory store.

    Returns:
        List of available memory names with metadata
    """
    try:
        project_root = Path(os.getcwd())
        memory_dir = project_root / ".serena_memories"

        if not memory_dir.exists():
            return "No memory store found. Use 'write_memory' to create memories."

        memory_files = list(memory_dir.glob("*.md"))

        if not memory_files:
            return "Memory store exists but no memories found."

        memories = []
        for memory_file in sorted(
            memory_files, key=lambda f: f.stat().st_mtime, reverse=True
        ):
            stat = memory_file.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            memories.append(
                {
                    "name": memory_file.stem,
                    "size": size,
                    "modified": modified,
                    "file": memory_file.name,
                }
            )

        # Format output
        output = [f"🧠 Project Memories ({len(memories)} found):\n"]

        for memory in memories:
            size_str = _format_size(memory["size"])
            output.append(f"📝 {memory['name']}")
            output.append(f"   📅 Modified: {memory['modified']}")
            output.append(f"   📊 Size: {size_str}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Error listing memories: {e!s}"


@tool
def delete_memory(memory_name: str) -> str:
    """
    Delete a named memory from the project memory store.

    Args:
        memory_name: Name of the memory to delete

    Returns:
        Success message or error details
    """
    try:
        project_root = Path(os.getcwd())
        memory_dir = project_root / ".serena_memories"

        if not memory_dir.exists():
            return "Memory store not found. No memories to delete."

        # Find the memory file (handle sanitized names)
        memory_file = None
        for candidate in memory_dir.glob("*.md"):
            if candidate.stem == memory_name:
                memory_file = candidate
                break

        if not memory_file:
            available_memories = [f.stem for f in memory_dir.glob("*.md")]
            available_list = (
                ", ".join(available_memories) if available_memories else "none"
            )
            return f"Memory '{memory_name}' not found. Available memories: {available_list}"

        # Get file info before deletion
        size = memory_file.stat().st_size

        # Delete the memory file
        memory_file.unlink()

        result = f"✅ Memory '{memory_name}' deleted successfully"
        result += f"\n📊 Freed {_format_size(size)} of storage"

        return result

    except Exception as e:
        return f"Error deleting memory '{memory_name}': {e!s}"


# Helper functions


def _analyze_project_structure(project_root: Path) -> dict[str, Any]:
    """Analyze the project directory structure"""
    structure = {"root_files": [], "directories": [], "total_files": 0, "total_dirs": 0}

    try:
        for item in project_root.iterdir():
            if item.is_file():
                structure["root_files"].append(item.name)
                structure["total_files"] += 1
            elif item.is_dir() and not item.name.startswith("."):
                structure["directories"].append(item.name)
                structure["total_dirs"] += 1

                # Count files in subdirectories
                try:
                    for sub_item in item.rglob("*"):
                        if sub_item.is_file():
                            structure["total_files"] += 1
                        elif sub_item.is_dir():
                            structure["total_dirs"] += 1
                except:
                    pass
    except:
        pass

    return structure


def _detect_programming_languages(project_root: Path) -> list[str]:
    """Detect programming languages used in the project"""
    language_extensions = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".rb": "Ruby",
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
    }

    detected = set()

    try:
        for item in project_root.rglob("*"):
            if item.is_file() and item.suffix in language_extensions:
                detected.add(language_extensions[item.suffix])
    except:
        pass

    return sorted(list(detected))


def _detect_build_systems(project_root: Path) -> list[str]:
    """Detect build systems and frameworks"""
    build_files = {
        "package.json": "npm/Node.js",
        "requirements.txt": "pip/Python",
        "Pipfile": "pipenv/Python",
        "pyproject.toml": "Python (pyproject)",
        "setup.py": "setuptools/Python",
        "Cargo.toml": "Cargo/Rust",
        "pom.xml": "Maven/Java",
        "build.gradle": "Gradle/Java",
        "Makefile": "Make",
        "CMakeLists.txt": "CMake",
        "composer.json": "Composer/PHP",
        "Gemfile": "Bundler/Ruby",
    }

    detected = []

    for file_name, system in build_files.items():
        if (project_root / file_name).exists():
            detected.append(system)

    return detected


def _identify_key_files(project_root: Path) -> list[str]:
    """Identify important project files"""
    key_files = []
    important_files = [
        "README.md",
        "README.rst",
        "README.txt",
        "LICENSE",
        "LICENSE.txt",
        "LICENSE.md",
        "CHANGELOG.md",
        "CHANGES.txt",
        ".gitignore",
        ".gitattributes",
        "Dockerfile",
        "docker-compose.yml",
        "main.py",
        "index.js",
        "app.py",
        "manage.py",
        "server.js",
    ]

    for file_name in important_files:
        file_path = project_root / file_name
        if file_path.exists():
            key_files.append(str(file_path.relative_to(project_root)))

    return key_files


def _analyze_dependencies(project_root: Path) -> dict[str, Any]:
    """Analyze project dependencies"""
    dependencies = {}

    # Python dependencies
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        try:
            content = req_file.read_text()
            deps = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]
            dependencies["python"] = {"count": len(deps), "file": "requirements.txt"}
        except:
            pass

    # Node.js dependencies
    package_file = project_root / "package.json"
    if package_file.exists():
        try:
            import json

            content = json.loads(package_file.read_text())
            dep_count = len(content.get("dependencies", {})) + len(
                content.get("devDependencies", {})
            )
            dependencies["nodejs"] = {"count": dep_count, "file": "package.json"}
        except:
            pass

    return dependencies


def _analyze_testing_setup(project_root: Path) -> dict[str, Any]:
    """Analyze testing configuration"""
    testing = {}

    # Check for test directories
    test_dirs = ["test", "tests", "__tests__", "spec"]
    found_dirs = []
    for dir_name in test_dirs:
        if (project_root / dir_name).exists():
            found_dirs.append(dir_name)

    if found_dirs:
        testing["test_directories"] = found_dirs

    # Check for test configuration files
    test_configs = [
        "pytest.ini",
        "tox.ini",
        "jest.config.js",
        "karma.conf.js",
        "mocha.opts",
    ]
    found_configs = []
    for config_file in test_configs:
        if (project_root / config_file).exists():
            found_configs.append(config_file)

    if found_configs:
        testing["config_files"] = found_configs

    return testing


def _generate_recommendations(analysis: dict[str, Any]) -> list[str]:
    """Generate setup and development recommendations"""
    recommendations = []

    # Language-specific recommendations
    if "Python" in analysis["languages_detected"]:
        if not any("Python" in bs for bs in analysis["build_systems"]):
            recommendations.append(
                "Consider adding requirements.txt or pyproject.toml for dependency management"
            )
        if not analysis["testing_setup"]:
            recommendations.append("Consider setting up pytest or unittest for testing")

    if (
        "JavaScript" in analysis["languages_detected"]
        or "TypeScript" in analysis["languages_detected"]
    ):
        if "npm/Node.js" not in analysis["build_systems"]:
            recommendations.append(
                "Consider initializing with 'npm init' for dependency management"
            )

    # General recommendations
    if "README.md" not in str(analysis["key_files"]):
        recommendations.append(
            "Consider adding a README.md file to document the project"
        )

    if not analysis["testing_setup"]:
        recommendations.append(
            "Consider setting up automated testing for better code quality"
        )

    return recommendations


def _format_onboarding_memory(analysis: dict[str, Any]) -> str:
    """Format analysis results into memory content"""
    memory = f"""# Project Onboarding Analysis

**Onboarding Date:** {analysis["timestamp"]}
**Project Root:** {analysis["project_root"]}

## Project Structure
- **Total Files:** {analysis["project_structure"]["total_files"]}
- **Total Directories:** {analysis["project_structure"]["total_dirs"]}
- **Root Files:** {", ".join(analysis["project_structure"]["root_files"])}
- **Main Directories:** {", ".join(analysis["project_structure"]["directories"])}

## Programming Languages
{
        ", ".join(analysis["languages_detected"])
        if analysis["languages_detected"]
        else "None detected"
    }

## Build Systems & Frameworks
{
        chr(10).join(f"- {bs}" for bs in analysis["build_systems"])
        if analysis["build_systems"]
        else "- None detected"
    }

## Key Files Identified
{
        chr(10).join(f"- {kf}" for kf in analysis["key_files"])
        if analysis["key_files"]
        else "- None found"
    }

## Dependencies Analysis
{
        chr(10).join(
            f"- {lang}: {info['count']} dependencies ({info['file']})"
            for lang, info in analysis["dependencies"].items()
        )
        if analysis["dependencies"]
        else "- No dependency files found"
    }

## Testing Setup
{
        chr(10).join(
            f"- Test directories: {', '.join(analysis['testing_setup'].get('test_directories', []))}"
             f"- Config files: {', '.join(analysis['testing_setup'].get('config_files', []))}"
            if analysis["testing_setup"]
            else "- No testing setup detected"
        )
    }

## Recommendations
{
        chr(10).join(f"- {rec}" for rec in analysis["recommendations"])
        if analysis["recommendations"]
        else "- Project setup looks good"
    }

## Development Notes
- Onboarding completed successfully
- Project is ready for development activities
- Use specialized agents for code analysis, file operations, and modifications
"""

    return memory


def _format_onboarding_report(analysis: dict[str, Any]) -> str:
    """Format analysis results into user-friendly report"""
    report = "📊 Project Analysis Report\n"
    report += f"📁 Project: {Path(analysis['project_root']).name}\n\n"

    # Structure summary
    report += f"🏗️  Structure: {analysis['project_structure']['total_files']} files, {analysis['project_structure']['total_dirs']} directories\n"

    # Languages
    if analysis["languages_detected"]:
        report += f"💻 Languages: {', '.join(analysis['languages_detected'])}\n"

    # Build systems
    if analysis["build_systems"]:
        report += f"🔧 Build Systems: {', '.join(analysis['build_systems'])}\n"

    # Dependencies
    if analysis["dependencies"]:
        dep_summary = []
        for lang, info in analysis["dependencies"].items():
            dep_summary.append(f"{info['count']} {lang}")
        report += f"📦 Dependencies: {', '.join(dep_summary)}\n"

    # Testing
    if analysis["testing_setup"]:
        report += "🧪 Testing: Configuration detected\n"

    # Recommendations
    if analysis["recommendations"]:
        report += f"\n💡 Recommendations ({len(analysis['recommendations'])}):\n"
        for rec in analysis["recommendations"]:
            report += f"   • {rec}\n"

    report += "\n✨ Project is now ready for multi-agent development workflows!"

    return report


def _ensure_memory_gitignore(project_root: Path):
    """Ensure memory directory is in .gitignore"""
    gitignore_file = project_root / ".gitignore"
    memory_pattern = ".serena_memories/"

    try:
        if gitignore_file.exists():
            content = gitignore_file.read_text()
            if memory_pattern not in content:
                with open(gitignore_file, "a") as f:
                    f.write(f"\n# Serena agent memories\n{memory_pattern}\n")
        else:
            gitignore_file.write_text(f"# Serena agent memories\n{memory_pattern}\n")
    except:
        pass  # Skip if we can't modify .gitignore


def _format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"
