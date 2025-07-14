#!/usr/bin/env python3
"""
Agent Version Manager CLI Tool

This script provides command-line interface for managing agent versions,
including migration, creation, activation, and A/B testing.
"""

import click
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from db.services.agent_version_service import AgentVersionService
from db.session import get_db
from agents.version_factory import agent_factory


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Agent Version Manager - CLI tool for managing agent versions."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['service'] = AgentVersionService(next(get_db()))


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier (e.g., pagbank-specialist)')
@click.option('--version', required=True, type=int, help='Version number to assign')
@click.option('--created-by', default='cli', help='User performing migration')
@click.option('--description', help='Description for this version')
@click.pass_context
def migrate(ctx, agent_id, version, created_by, description):
    """Migrate file-based agent configuration to database."""
    verbose = ctx.obj['verbose']
    
    click.echo(f"🔄 Migrating {agent_id} to database version {version}...")
    
    try:
        success = agent_factory.migrate_file_to_database(
            agent_id=agent_id,
            version=version,
            created_by=created_by
        )
        
        if success:
            click.echo(f"✅ Successfully migrated {agent_id} to version {version}")
            
            if verbose:
                # Show version details
                version_info = agent_factory.get_version_info(agent_id, version)
                click.echo(f"📋 Version details:")
                click.echo(f"   Created: {version_info['created_at']}")
                click.echo(f"   Created by: {version_info['created_by']}")
                click.echo(f"   Description: {version_info['description']}")
                click.echo(f"   Active: {version_info['is_active']}")
        else:
            click.echo(f"❌ Failed to migrate {agent_id}")
            
    except Exception as e:
        click.echo(f"❌ Error migrating {agent_id}: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--version', required=True, type=int, help='Version number')
@click.option('--config-file', type=click.Path(exists=True), help='Path to config file (YAML or JSON)')
@click.option('--config-json', help='Config as JSON string')
@click.option('--created-by', default='cli', help='User creating the version')
@click.option('--description', help='Description of changes')
@click.option('--activate', is_flag=True, help='Activate this version immediately')
@click.pass_context
def create(ctx, agent_id, version, config_file, config_json, created_by, description, activate):
    """Create a new agent version."""
    service = ctx.obj['service']
    verbose = ctx.obj['verbose']
    
    click.echo(f"🔨 Creating {agent_id} version {version}...")
    
    # Load configuration
    config = None
    if config_file:
        config_path = Path(config_file)
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        elif config_path.suffix.lower() == '.json':
            with open(config_path) as f:
                config = json.load(f)
        else:
            click.echo("❌ Config file must be YAML or JSON")
            return
    elif config_json:
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON: {e}")
            return
    else:
        click.echo("❌ Must provide either --config-file or --config-json")
        return
    
    try:
        new_version = service.create_version(
            agent_id=agent_id,
            version=version,
            config=config,
            created_by=created_by,
            description=description,
            is_active=activate
        )
        
        click.echo(f"✅ Created {agent_id} version {version}")
        
        if verbose:
            click.echo(f"📋 Version details:")
            click.echo(f"   ID: {new_version.id}")
            click.echo(f"   Created: {new_version.created_at}")
            click.echo(f"   Created by: {new_version.created_by}")
            click.echo(f"   Description: {new_version.description}")
            click.echo(f"   Active: {new_version.is_active}")
            
        if activate:
            click.echo(f"🟢 Version {version} is now active")
            
    except Exception as e:
        click.echo(f"❌ Error creating version: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--version', required=True, type=int, help='Version number to activate')
@click.option('--changed-by', default='cli', help='User making the change')
@click.option('--reason', help='Reason for activation')
@click.pass_context
def activate(ctx, agent_id, version, changed_by, reason):
    """Activate a specific agent version."""
    service = ctx.obj['service']
    verbose = ctx.obj['verbose']
    
    click.echo(f"🟢 Activating {agent_id} version {version}...")
    
    try:
        activated_version = service.activate_version(
            agent_id=agent_id,
            version=version,
            changed_by=changed_by,
            reason=reason
        )
        
        click.echo(f"✅ Activated {agent_id} version {version}")
        
        if verbose:
            click.echo(f"📋 Version details:")
            click.echo(f"   ID: {activated_version.id}")
            click.echo(f"   Description: {activated_version.description}")
            click.echo(f"   Created: {activated_version.created_at}")
            click.echo(f"   Created by: {activated_version.created_by}")
            
    except Exception as e:
        click.echo(f"❌ Error activating version: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--include-deprecated', is_flag=True, help='Include deprecated versions')
@click.pass_context
def list(ctx, agent_id, include_deprecated):
    """List all versions for an agent."""
    service = ctx.obj['service']
    verbose = ctx.obj['verbose']
    
    click.echo(f"📋 Listing versions for {agent_id}...")
    
    try:
        versions = service.list_versions(agent_id, include_deprecated)
        
        if not versions:
            click.echo(f"🔍 No versions found for {agent_id}")
            return
        
        click.echo(f"Found {len(versions)} versions:")
        
        for v in versions:
            status_icons = []
            if v.is_active:
                status_icons.append("🟢 ACTIVE")
            if v.is_deprecated:
                status_icons.append("🔴 DEPRECATED")
            
            status = f" ({', '.join(status_icons)})" if status_icons else ""
            
            click.echo(f"  v{v.version}{status}")
            
            if verbose:
                click.echo(f"    ID: {v.id}")
                click.echo(f"    Created: {v.created_at}")
                click.echo(f"    Created by: {v.created_by}")
                click.echo(f"    Description: {v.description}")
                click.echo()
                
    except Exception as e:
        click.echo(f"❌ Error listing versions: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--version', type=int, help='Specific version (default: active version)')
@click.option('--format', 'output_format', default='yaml', type=click.Choice(['yaml', 'json']), help='Output format')
@click.pass_context
def show(ctx, agent_id, version, output_format):
    """Show detailed information about a specific version."""
    service = ctx.obj['service']
    
    try:
        if version is not None:
            agent_version = service.get_version(agent_id, version)
            version_type = f"version {version}"
        else:
            agent_version = service.get_active_version(agent_id)
            version_type = "active version"
        
        if not agent_version:
            click.echo(f"❌ No {version_type} found for {agent_id}")
            return
        
        click.echo(f"📋 {agent_id} {version_type}:")
        click.echo(f"   Version: {agent_version.version}")
        click.echo(f"   Created: {agent_version.created_at}")
        click.echo(f"   Created by: {agent_version.created_by}")
        click.echo(f"   Active: {agent_version.is_active}")
        click.echo(f"   Deprecated: {agent_version.is_deprecated}")
        click.echo(f"   Description: {agent_version.description}")
        click.echo()
        
        click.echo("🔧 Configuration:")
        if output_format == 'yaml':
            click.echo(yaml.dump(agent_version.config, default_flow_style=False, sort_keys=False))
        else:
            click.echo(json.dumps(agent_version.config, indent=2))
            
    except Exception as e:
        click.echo(f"❌ Error showing version: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--source-version', required=True, type=int, help='Version to clone from')
@click.option('--target-version', required=True, type=int, help='New version number')
@click.option('--created-by', default='cli', help='User creating the clone')
@click.option('--description', help='Description for the new version')
@click.pass_context
def clone(ctx, agent_id, source_version, target_version, created_by, description):
    """Clone an existing version to create a new version."""
    service = ctx.obj['service']
    verbose = ctx.obj['verbose']
    
    click.echo(f"📋 Cloning {agent_id} v{source_version} → v{target_version}...")
    
    try:
        cloned_version = service.clone_version(
            agent_id=agent_id,
            source_version=source_version,
            target_version=target_version,
            created_by=created_by,
            description=description
        )
        
        click.echo(f"✅ Cloned {agent_id} v{source_version} → v{target_version}")
        
        if verbose:
            click.echo(f"📋 New version details:")
            click.echo(f"   ID: {cloned_version.id}")
            click.echo(f"   Created: {cloned_version.created_at}")
            click.echo(f"   Created by: {cloned_version.created_by}")
            click.echo(f"   Description: {cloned_version.description}")
            
    except Exception as e:
        click.echo(f"❌ Error cloning version: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--version', required=True, type=int, help='Version to deprecate')
@click.option('--changed-by', default='cli', help='User making the change')
@click.option('--reason', help='Reason for deprecation')
@click.pass_context
def deprecate(ctx, agent_id, version, changed_by, reason):
    """Mark a version as deprecated."""
    service = ctx.obj['service']
    verbose = ctx.obj['verbose']
    
    click.echo(f"🔴 Deprecating {agent_id} version {version}...")
    
    try:
        deprecated_version = service.deprecate_version(
            agent_id=agent_id,
            version=version,
            changed_by=changed_by,
            reason=reason
        )
        
        click.echo(f"✅ Deprecated {agent_id} version {version}")
        
        if verbose:
            click.echo(f"📋 Version details:")
            click.echo(f"   ID: {deprecated_version.id}")
            click.echo(f"   Description: {deprecated_version.description}")
            click.echo(f"   Deprecated: {deprecated_version.is_deprecated}")
            
    except Exception as e:
        click.echo(f"❌ Error deprecating version: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--version', type=int, help='Specific version (default: all versions)')
@click.option('--days', default=7, type=int, help='Number of days to look back')
@click.pass_context
def history(ctx, agent_id, version, days):
    """Show version history and changes."""
    service = ctx.obj['service']
    verbose = ctx.obj['verbose']
    
    click.echo(f"📅 Version history for {agent_id}:")
    
    try:
        history_records = service.get_version_history(agent_id, version)
        
        if not history_records:
            click.echo("🔍 No history found")
            return
        
        for record in history_records:
            click.echo(f"  📅 {record.changed_at} - {record.action.upper()}")
            click.echo(f"     Version: {record.version}")
            click.echo(f"     Changed by: {record.changed_by}")
            if record.reason:
                click.echo(f"     Reason: {record.reason}")
            
            if verbose and (record.previous_state or record.new_state):
                click.echo(f"     Changes:")
                if record.previous_state:
                    click.echo(f"       Previous: {json.dumps(record.previous_state, indent=8)}")
                if record.new_state:
                    click.echo(f"       New: {json.dumps(record.new_state, indent=8)}")
            
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Error getting history: {str(e)}")


@cli.command()
@click.pass_context
def list_agents(ctx):
    """List all available agents."""
    verbose = ctx.obj['verbose']
    
    click.echo("🤖 Available agents:")
    
    try:
        agents_info = agent_factory.list_available_agents()
        
        for agent_id, info in agents_info.items():
            source_icon = "💾" if info["source"] == "database" else "📁"
            click.echo(f"  {source_icon} {agent_id}")
            
            if verbose:
                click.echo(f"     Source: {info['source']}")
                if info["source"] == "database":
                    click.echo(f"     Versions: {info['versions']}")
                    click.echo(f"     Active: v{info['active_version']}" if info['active_version'] else "     Active: none")
                    click.echo(f"     Total versions: {info['total_versions']}")
                else:
                    click.echo(f"     Can migrate: {info.get('can_migrate', False)}")
                click.echo()
                
    except Exception as e:
        click.echo(f"❌ Error listing agents: {str(e)}")


@cli.command()
@click.option('--agent-id', required=True, help='Agent identifier')
@click.option('--message', required=True, help='Message to send to the agent')
@click.option('--version', type=int, help='Specific version to run (default: active version)')
@click.option('--session-id', help='Session ID for conversation tracking')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def test(ctx, agent_id, message, version, session_id, debug):
    """Test an agent version with a message."""
    verbose = ctx.obj['verbose']
    
    version_text = f"v{version}" if version else "active version"
    click.echo(f"🧪 Testing {agent_id} {version_text}...")
    
    try:
        from agents.version_factory import create_versioned_agent
        
        agent = create_versioned_agent(
            agent_id=agent_id,
            version=version,
            session_id=session_id,
            debug_mode=debug
        )
        
        click.echo(f"💬 Message: {message}")
        click.echo(f"🤖 Response:")
        
        response = agent.run(message)
        click.echo(response.content)
        
        if verbose:
            click.echo(f"\n📋 Agent metadata:")
            for key, value in agent.metadata.items():
                click.echo(f"   {key}: {value}")
                
    except Exception as e:
        click.echo(f"❌ Error testing agent: {str(e)}")


if __name__ == '__main__':
    cli()