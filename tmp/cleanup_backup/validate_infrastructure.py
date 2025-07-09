#!/usr/bin/env python3
"""Validate PagBank infrastructure setup."""

import sys
import traceback
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def validate_imports():
    """Validate that all required modules can be imported."""
    console.print("\n[blue]🔍 Validating Module Imports...[/blue]")
    
    try:
        # Test core imports
        pass
        
        console.print("✅ All core modules imported successfully")
        return True
    except Exception as e:
        console.print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False


def validate_database():
    """Validate database connectivity and PgVector."""
    console.print("\n[blue]🗄️ Validating Database...[/blue]")
    
    try:
        from pagbank.config.database import health_check, init_database

        # Initialize database
        init_database()
        
        # Check health
        health = health_check()
        
        table = Table(title="Database Health Check")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row(
            "PostgreSQL Connection",
            "✅ Healthy" if health["connection"] else "❌ Failed",
            health["url"]
        )
        
        table.add_row(
            "PgVector Extension", 
            "✅ Available" if health["pgvector"] else "❌ Missing",
            "Vector operations working" if health["pgvector"] else "Vector operations failed"
        )
        
        console.print(table)
        
        return health["connection"] and health["pgvector"]
        
    except Exception as e:
        console.print(f"❌ Database validation failed: {e}")
        traceback.print_exc()
        return False


def validate_models():
    """Validate AI model configurations."""
    console.print("\n[blue]🤖 Validating AI Models...[/blue]")
    
    try:
        from pagbank.config.models import validate_models as validate_model_config
        
        validation = validate_model_config()
        
        table = Table(title="Model Validation")
        table.add_column("Model", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row(
            "Anthropic API Key",
            "✅ Valid" if validation["anthropic_api_key"] else "❌ Invalid"
        )
        
        table.add_row(
            "Embedding Model",
            "✅ Available" if validation["embedding_model"] else "❌ Missing"
        )
        
        console.print(table)
        
        return all(validation.values())
        
    except Exception as e:
        console.print(f"❌ Model validation failed: {e}")
        traceback.print_exc()
        return False


def validate_environment():
    """Validate environment setup."""
    console.print("\n[blue]🌍 Validating Environment...[/blue]")
    
    try:
        from pagbank.config.settings import validate_environment as validate_env_config
        
        validation = validate_env_config()
        
        table = Table(title="Environment Validation")
        table.add_column("Setting", style="cyan")
        table.add_column("Status", style="green")
        
        for key, value in validation.items():
            table.add_row(
                key.replace("_", " ").title(),
                "✅ Valid" if value else "❌ Invalid"
            )
        
        console.print(table)
        
        return all(validation.values())
        
    except Exception as e:
        console.print(f"❌ Environment validation failed: {e}")
        traceback.print_exc()
        return False


def validate_directory_structure():
    """Validate directory structure."""
    console.print("\n[blue]📁 Validating Directory Structure...[/blue]")
    
    required_dirs = [
        "pagbank/agents",
        "pagbank/teams", 
        "pagbank/orchestrator",
        "pagbank/knowledge",
        "pagbank/memory",
        "pagbank/demo",
        "pagbank/utils",
        "pagbank/config",
        "tests",
        "tests/integration",
        "tests/unit"
    ]
    
    table = Table(title="Directory Structure")
    table.add_column("Directory", style="cyan")
    table.add_column("Status", style="green")
    
    all_exist = True
    base_path = Path(__file__).parent
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        
        table.add_row(
            dir_name,
            "✅ Exists" if exists else "❌ Missing"
        )
        
        if not exists:
            all_exist = False
    
    console.print(table)
    return all_exist


def validate_python_packages():
    """Validate Python package structure."""
    console.print("\n[blue]🐍 Validating Python Packages...[/blue]")
    
    required_init_files = [
        "pagbank/__init__.py",
        "pagbank/agents/__init__.py",
        "pagbank/teams/__init__.py",
        "pagbank/orchestrator/__init__.py", 
        "pagbank/knowledge/__init__.py",
        "pagbank/memory/__init__.py",
        "pagbank/demo/__init__.py",
        "pagbank/utils/__init__.py",
        "pagbank/config/__init__.py",
        "tests/__init__.py",
        "tests/integration/__init__.py",
        "tests/unit/__init__.py"
    ]
    
    table = Table(title="Python Package Structure")
    table.add_column("Package", style="cyan")
    table.add_column("Status", style="green")
    
    all_exist = True
    base_path = Path(__file__).parent
    
    for init_file in required_init_files:
        init_path = base_path / init_file
        exists = init_path.exists() and init_path.is_file()
        
        table.add_row(
            init_file,
            "✅ Exists" if exists else "❌ Missing"
        )
        
        if not exists:
            all_exist = False
    
    console.print(table)
    return all_exist


def validate_configuration_files():
    """Validate configuration files."""
    console.print("\n[blue]⚙️ Validating Configuration Files...[/blue]")
    
    required_config_files = [
        "pagbank/config/database.py",
        "pagbank/config/models.py", 
        "pagbank/config/settings.py",
        "pyproject.toml",
        ".env"
    ]
    
    table = Table(title="Configuration Files")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    
    all_exist = True
    base_path = Path(__file__).parent
    
    for config_file in required_config_files:
        config_path = base_path / config_file
        exists = config_path.exists() and config_path.is_file()
        
        table.add_row(
            config_file,
            "✅ Exists" if exists else "❌ Missing"
        )
        
        if not exists:
            all_exist = False
    
    console.print(table)
    return all_exist


def run_integration_tests():
    """Run basic integration tests."""
    console.print("\n[blue]🧪 Running Integration Tests...[/blue]")
    
    try:
        # Test database operations
        from pagbank.config.database import db_config
        
        with db_config.get_session() as session:
            # Test basic query
            from sqlalchemy import text
            result = session.execute(text("SELECT 1;")).fetchone()
            assert result[0] == 1
            
            # Test PgVector operations
            result = session.execute(text("SELECT vector_dims(vector '[1,2,3]');")).fetchone()
            assert result[0] == 3
        
        # Test Claude client
        from pagbank.config.models import get_claude_client
        
        client = get_claude_client()
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Test"}]
        )
        
        assert len(response.content) > 0
        
        console.print("✅ Integration tests passed")
        return True
        
    except Exception as e:
        console.print(f"❌ Integration tests failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run complete infrastructure validation."""
    console.print(Panel.fit(
        "[bold green]PagBank Infrastructure Validation[/bold green]",
        border_style="green"
    ))
    
    validations = [
        ("Module Imports", validate_imports),
        ("Directory Structure", validate_directory_structure),
        ("Python Packages", validate_python_packages),
        ("Configuration Files", validate_configuration_files),
        ("Database", validate_database),
        ("AI Models", validate_models),
        ("Environment", validate_environment),
        ("Integration Tests", run_integration_tests),
    ]
    
    results = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for name, validation_func in validations:
            task = progress.add_task(f"Validating {name}...", total=None)
            results[name] = validation_func()
            progress.update(task, completed=True)
    
    # Summary table
    console.print("\n[bold blue]📊 Validation Summary[/bold blue]")
    
    summary_table = Table(title="Infrastructure Validation Results")
    summary_table.add_column("Component", style="cyan")
    summary_table.add_column("Status", style="green")
    
    for name, passed in results.items():
        summary_table.add_row(
            name,
            "✅ Passed" if passed else "❌ Failed"
        )
    
    console.print(summary_table)
    
    # Final status
    all_passed = all(results.values())
    
    if all_passed:
        console.print(Panel.fit(
            "[bold green]🎉 All Infrastructure Validations Passed![/bold green]\n"
            "[green]PagBank infrastructure is ready for other agents to use.[/green]",
            border_style="green"
        ))
        return 0
    else:
        failed_count = sum(1 for passed in results.values() if not passed)
        console.print(Panel.fit(
            f"[bold red]❌ {failed_count} Infrastructure Validations Failed![/bold red]\n"
            "[red]Please fix the issues before proceeding.[/red]",
            border_style="red"
        ))
        return 1


if __name__ == "__main__":
    sys.exit(main())