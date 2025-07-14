#!/usr/bin/env python3
"""
Agent Versioning System Validation Script

This script validates that all components of the agent versioning system
are properly implemented and integrated.
"""

import sys
import traceback
from typing import List, Dict, Any


def validate_imports() -> List[str]:
    """Validate all imports are working."""
    errors = []
    
    # Test database imports
    try:
        from db.tables.agent_versions import AgentVersion, AgentVersionHistory, AgentVersionMetrics
        print("✅ Database tables imported successfully")
    except Exception as e:
        errors.append(f"❌ Database tables import failed: {e}")
    
    # Test service imports
    try:
        from db.services.agent_version_service import AgentVersionService
        print("✅ Agent version service imported successfully")
    except Exception as e:
        errors.append(f"❌ Agent version service import failed: {e}")
    
    # Test factory imports
    try:
        from agents.version_factory import AgentVersionFactory, create_versioned_agent
        print("✅ Version factory imported successfully")
    except Exception as e:
        errors.append(f"❌ Version factory import failed: {e}")
    
    # Test A/B testing imports
    try:
        from agents.ab_testing import ABTestManager, create_ab_test
        print("✅ A/B testing imported successfully")
    except Exception as e:
        errors.append(f"❌ A/B testing import failed: {e}")
    
    # Test API imports
    try:
        from api.routes.agent_versions import agent_versions_router
        print("✅ API routes imported successfully")
    except Exception as e:
        errors.append(f"❌ API routes import failed: {e}")
    
    return errors


def validate_database_schema() -> List[str]:
    """Validate database schema is properly defined."""
    errors = []
    
    try:
        from db.tables.agent_versions import AgentVersion
        from sqlalchemy import inspect
        
        # Check table structure
        table = AgentVersion.__table__
        columns = [col.name for col in table.columns]
        
        required_columns = [
            'id', 'agent_id', 'version', 'config', 'created_at', 
            'created_by', 'is_active', 'is_deprecated', 'description'
        ]
        
        for col in required_columns:
            if col not in columns:
                errors.append(f"❌ Missing column: {col}")
        
        if not errors:
            print("✅ Database schema validation passed")
        
    except Exception as e:
        errors.append(f"❌ Database schema validation failed: {e}")
    
    return errors


def validate_api_endpoints() -> List[str]:
    """Validate API endpoints are properly defined."""
    errors = []
    
    try:
        from api.routes.agent_versions import router
        
        # Check router exists and has routes
        if not hasattr(router, 'routes'):
            errors.append("❌ Router has no routes")
        elif len(router.routes) == 0:
            errors.append("❌ Router has no routes defined")
        else:
            route_paths = [route.path for route in router.routes]
            print(f"✅ API router has {len(route_paths)} routes")
            
            # Check for key endpoints
            required_patterns = [
                '/agents/',
                '/agents/{agent_id}/versions',
                '/agents/{agent_id}/versions/{version}',
                '/agents/{agent_id}/run'
            ]
            
            for pattern in required_patterns:
                if not any(pattern in path for path in route_paths):
                    errors.append(f"❌ Missing endpoint pattern: {pattern}")
        
        if not errors:
            print("✅ API endpoints validation passed")
        
    except Exception as e:
        errors.append(f"❌ API endpoints validation failed: {e}")
    
    return errors


def validate_configuration_format() -> List[str]:
    """Validate configuration format is correct."""
    errors = []
    
    try:
        from agents.version_factory import AgentVersionFactory
        
        # Test sample configuration
        sample_config = {
            "agent": {
                "agent_id": "test-specialist",
                "version": 1,
                "name": "Test Specialist"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "instructions": "Test instructions",
            "tools": ["test_tool"],
            "storage": {
                "type": "postgres",
                "table_name": "test_specialist",
                "auto_upgrade_schema": True
            },
            "memory": {
                "add_history_to_messages": True,
                "num_history_runs": 5
            },
            "markdown": False,
            "show_tool_calls": True
        }
        
        factory = AgentVersionFactory()
        
        # Test model creation
        model = factory._create_model(sample_config["model"])
        if model is None:
            errors.append("❌ Model creation failed")
        else:
            print("✅ Model creation works")
        
        # Test storage creation
        storage = factory._create_storage(sample_config, "sqlite:///test.db")
        if storage is None:
            errors.append("❌ Storage creation failed")
        else:
            print("✅ Storage creation works")
        
    except Exception as e:
        errors.append(f"❌ Configuration format validation failed: {e}")
    
    return errors


def validate_cli_tools() -> List[str]:
    """Validate CLI tools are working."""
    errors = []
    
    try:
        from scripts.agent_version_manager import cli
        
        # Test CLI import
        if cli is None:
            errors.append("❌ CLI import failed")
        else:
            print("✅ CLI tools imported successfully")
        
    except Exception as e:
        errors.append(f"❌ CLI tools validation failed: {e}")
    
    return errors


def validate_ab_testing() -> List[str]:
    """Validate A/B testing functionality."""
    errors = []
    
    try:
        from agents.ab_testing import ABTestManager, ABTestConfig, ABTestStatus
        
        # Test A/B test manager creation
        manager = ABTestManager()
        if manager is None:
            errors.append("❌ ABTestManager creation failed")
        
        # Test configuration creation
        try:
            config = manager.create_test(
                test_id="test-ab",
                name="Test A/B Test",
                description="Test description",
                agent_id="test-specialist",
                control_version=1,
                test_versions=[2],
                traffic_distribution={1: 70, 2: 30}
            )
            
            if config.status != ABTestStatus.DRAFT:
                errors.append("❌ A/B test config creation failed")
            else:
                print("✅ A/B test configuration creation works")
        except Exception as e:
            errors.append(f"❌ A/B test configuration creation failed: {e}")
        
    except Exception as e:
        errors.append(f"❌ A/B testing validation failed: {e}")
    
    return errors


def validate_file_structure() -> List[str]:
    """Validate file structure is correct."""
    errors = []
    
    import os
    from pathlib import Path
    
    # Required files
    required_files = [
        "db/tables/agent_versions.py",
        "db/services/agent_version_service.py",
        "agents/version_factory.py",
        "agents/ab_testing.py",
        "api/routes/agent_versions.py",
        "scripts/agent_version_manager.py",
        "examples/agent_versioning_demo.py",
        "docs/AGENT_VERSIONING_SYSTEM.md"
    ]
    
    for file_path in required_files:
        full_path = Path(file_path)
        if not full_path.exists():
            errors.append(f"❌ Missing file: {file_path}")
    
    if not errors:
        print("✅ File structure validation passed")
    
    return errors


def main():
    """Run all validations."""
    print("🔍 Validating Agent Versioning System")
    print("=" * 50)
    
    all_errors = []
    
    # Run validations
    validations = [
        ("File Structure", validate_file_structure),
        ("Imports", validate_imports),
        ("Database Schema", validate_database_schema),
        ("API Endpoints", validate_api_endpoints),
        ("Configuration Format", validate_configuration_format),
        ("CLI Tools", validate_cli_tools),
        ("A/B Testing", validate_ab_testing)
    ]
    
    for name, validation_func in validations:
        print(f"\n📋 {name} Validation:")
        try:
            errors = validation_func()
            all_errors.extend(errors)
            
            if not errors:
                print(f"✅ {name} validation passed")
            else:
                for error in errors:
                    print(f"  {error}")
                    
        except Exception as e:
            error_msg = f"❌ {name} validation crashed: {e}"
            print(f"  {error_msg}")
            all_errors.append(error_msg)
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 50)
    if not all_errors:
        print("✅ All validations passed!")
        print("\n🚀 Agent Versioning System is ready to use!")
        print("\nNext steps:")
        print("1. Run database migrations: alembic upgrade head")
        print("2. Start API server: uv run python api/playground.py")
        print("3. Try the demo: python examples/agent_versioning_demo.py")
        print("4. Use CLI tools: python scripts/agent_version_manager.py --help")
        return 0
    else:
        print(f"❌ {len(all_errors)} validation errors found:")
        for error in all_errors:
            print(f"  {error}")
        print("\n🔧 Please fix these issues before using the system.")
        return 1


if __name__ == "__main__":
    sys.exit(main())