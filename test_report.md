=================================================================================================== FAILURES ====================================================================================================
________________________________________________________________________________ TestCLICommandRouting.test_agent_start_command _________________________________________________________________________________
/usr/lib/python3.12/unittest/mock.py:955: in assert_called_once_with
    raise AssertionError(msg)
E   AssertionError: Expected 'serve' to be called once. Called 0 times.

During handling of the above exception, another exception occurred:
tests/integration/cli/test_main_cli_comprehensive.py:386: in test_agent_start_command
    mock_command_handlers["agent"].serve.assert_called_once_with(".")
E   AssertionError: Expected 'serve' to be called once. Called 0 times.
_______________________________________________________________________ TestCLIErrorHandling.test_all_command_failures_return_exit_code_1 _______________________________________________________________________
tests/integration/cli/test_main_cli_comprehensive.py:552: in test_all_command_failures_return_exit_code_1
    assert result == 1, (
E   AssertionError: Command ['--agent-start'] should return exit code 1 on failure
E   assert 0 == 1
______________________________________________________ TestMakefileUninstallComprehensive.test_uninstall_containers_only_comprehensive_stops_all_services _______________________________________________________
/home/namastex/workspace/automagik-hive/tests/integration/cli/test_makefile_uninstall.py:109: in test_uninstall_containers_only_comprehensive_stops_all_services
    assert "hive-agents-agent hive-agent-postgres" in makefile_content
E   AssertionError: assert 'hive-agents-agent hive-agent-postgres' in '# ===========================================\n# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile\n# =======...\\\n    else \\\n        $(call print_warning,Could not update .mcp.json - missing credentials); \\\n    fi\nendef\n\n'
______________________________________________________ TestMakefileUninstallComprehensive.test_uninstall_clean_comprehensive_removes_agent_infrastructure _______________________________________________________
/home/namastex/workspace/automagik-hive/tests/integration/cli/test_makefile_uninstall.py:119: in test_uninstall_clean_comprehensive_removes_agent_infrastructure
    assert "docker image rm automagik-hive-app" in makefile_content
E   AssertionError: assert 'docker image rm automagik-hive-app' in '# ===========================================\n# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile\n# =======...\\\n    else \\\n        $(call print_warning,Could not update .mcp.json - missing credentials); \\\n    fi\nendef\n\n'
____________________________________________________________ TestMakefileUninstallComprehensive.test_uninstall_purge_comprehensive_removes_all_data _____________________________________________________________
/home/namastex/workspace/automagik-hive/tests/integration/cli/test_makefile_uninstall.py:136: in test_uninstall_purge_comprehensive_removes_all_data
    assert "This will remove ALL containers, images, volumes, data, and environment files" in makefile_content
E   AssertionError: assert 'This will remove ALL containers, images, volumes, data, and environment files' in '# ===========================================\n# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile\n# =======...\\\n    else \\\n        $(call print_warning,Could not update .mcp.json - missing credentials); \\\n    fi\nendef\n\n'
____________________________________________________________________ TestAgentCommandsIntegration.test_agent_service_environment_integration ____________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:152: in test_agent_service_environment_integration
    env_path = environment.generate_env_agent()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AgentEnvironment' object has no attribute 'generate_env_agent'
______________________________________________________________________ TestFunctionalParityMakeVsUvx.test_agent_port_configuration_parity _______________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:358: in test_agent_port_configuration_parity
    env.generate_env_agent()
    ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AgentEnvironment' object has no attribute 'generate_env_agent'
_____________________________________________________________________ TestFunctionalParityMakeVsUvx.test_environment_file_generation_parity _____________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:385: in test_environment_file_generation_parity
    uvx_env_path = env.generate_env_agent()
                   ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AgentEnvironment' object has no attribute 'generate_env_agent'
_______________________________________________________________________ TestCrossPlatformCompatibility.test_linux_compatibility_patterns ________________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:669: in test_linux_compatibility_patterns
    assert result is True
E   assert False is True
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🚀 Installing and starting agent services in: /tmp/tmpoag26eg0
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
🚀 Starting both agent-postgres and agent-api containers...
✅ Both agent containers started successfully
✅ Agent environment installed successfully
❌ Agent environment validation failed
_______________________________________________________________________ TestCrossPlatformCompatibility.test_macos_compatibility_patterns ________________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:690: in test_macos_compatibility_patterns
    assert result is True
E   assert False is True
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🚀 Installing and starting agent services in: /tmp/tmp_d6_fi0f
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
🚀 Starting both agent-postgres and agent-api containers...
✅ Both agent containers started successfully
✅ Agent environment installed successfully
❌ Agent environment validation failed
_______________________________________________________________________ TestCrossPlatformCompatibility.test_environment_variable_handling _______________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:739: in test_environment_variable_handling
    assert result is True
E   assert False is True
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🚀 Installing and starting agent services in: /tmp/tmpc2_9c203
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
🚀 Starting both agent-postgres and agent-api containers...
✅ Both agent containers started successfully
✅ Agent environment installed successfully
❌ Agent environment validation failed
_______________________________________________________________________ TestPerformanceAndScalability.test_concurrent_command_performance _______________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:818: in test_concurrent_command_performance
    assert all(result[1] for result in results)
E   assert False
E    +  where False = all(<generator object TestPerformanceAndScalability.test_concurrent_command_performance.<locals>.<genexpr> at 0x743b6eb62dc0>)
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🚀 Installing and starting agent services in: /tmp/tmpzk68gr41
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
🚀 Installing and starting agent services in: /tmp/tmpzk68gr41
🚀 Installing and starting agent services in: /tmp/tmpzk68gr41
🚀 Starting both agent-postgres and agent-api containers...
🚀 Installing and starting agent services in: /tmp/tmpzk68gr41
✅ Both agent containers started successfully
🚀 Installing and starting agent services in: /tmp/tmpzk68gr41
✅ Agent environment installed successfully
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
❌ Agent environment validation failed
🚀 Starting both agent-postgres and agent-api containers...🚀 Starting both agent-postgres and agent-api containers...✅ Using ephemeral PostgreSQL storage - fresh database on each restart


✅ Using ephemeral PostgreSQL storage - fresh database on each restart
🚀 Starting both agent-postgres and agent-api containers...
🚀 Starting both agent-postgres and agent-api containers...
❌ Docker compose failed: time="2025-08-14T06:21:57-03:00" level=warning msg="/tmp/tmpzk68gr41/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
empty compose file

❌ Docker compose failed: time="2025-08-14T06:21:57-03:00" level=warning msg="/tmp/tmpzk68gr41/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
empty compose file
❌ Docker compose failed: time="2025-08-14T06:21:57-03:00" level=warning msg="/tmp/tmpzk68gr41/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
empty compose file


❌ Docker compose failed: time="2025-08-14T06:21:57-03:00" level=warning msg="/tmp/tmpzk68gr41/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
empty compose file

__________________________________________________________________________ TestPerformanceAndScalability.test_large_workspace_handling __________________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:841: in test_large_workspace_handling
    assert result is True
E   assert False is True
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🚀 Installing and starting agent services in: /tmp/tmp8jh_kpc3
✅ Using ephemeral PostgreSQL storage - fresh database on each restart
🚀 Starting both agent-postgres and agent-api containers...
✅ Both agent containers started successfully
✅ Agent environment installed successfully
❌ Agent environment validation failed
___________________________________________________________________________ TestPerformanceAndScalability.test_command_response_time ____________________________________________________________________________
tests/integration/e2e/test_agent_commands_integration.py:874: in test_command_response_time
    ("serve", commands.serve),
              ^^^^^^^^^^^^^^
E   AttributeError: 'AgentCommands' object has no attribute 'serve'
__________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-dev-planner] __________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-dev-designer] __________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-designer did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-dev-coder] ___________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-coder did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-dev-fixer] ___________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-fixer did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-testing-maker] _________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-maker did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-testing-fixer] _________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-fixer did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-quality-ruff] __________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-ruff did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-quality-mypy] __________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-mypy did not return valid JSON response
E   assert None is not None
_____________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-clone] _____________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-clone did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-self-learn] ___________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-self-learn did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-qa-tester] ___________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-qa-tester did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-claudemd] ____________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-claudemd did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-agent-creator] _________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-creator did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[genie-agent-enhancer] _________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-enhancer did not return valid JSON response
E   assert None is not None
_______________________________________________________________________ TestArtifactLifecycle.test_ideas_phase_artifact_creation[claude] ________________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:101: in test_ideas_phase_artifact_creation
    assert json_data is not None, (
E   AssertionError: Agent claude did not return valid JSON response
E   assert None is not None
_____________________________________________________________________ TestArtifactLifecycle.test_wishes_phase_migration[genie-dev-planner] ______________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:180: in test_wishes_phase_migration
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
_____________________________________________________________________ TestArtifactLifecycle.test_wishes_phase_migration[genie-dev-designer] _____________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:180: in test_wishes_phase_migration
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-designer did not return valid JSON response
E   assert None is not None
______________________________________________________________________ TestArtifactLifecycle.test_wishes_phase_migration[genie-dev-coder] _______________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:180: in test_wishes_phase_migration
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-coder did not return valid JSON response
E   assert None is not None
____________________________________________________________________ TestArtifactLifecycle.test_wishes_phase_migration[genie-testing-maker] _____________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:180: in test_wishes_phase_migration
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-maker did not return valid JSON response
E   assert None is not None
________________________________________________________________________ TestArtifactLifecycle.test_wishes_phase_migration[genie-clone] _________________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:180: in test_wishes_phase_migration
    assert json_data is not None, (
E   AssertionError: Agent genie-clone did not return valid JSON response
E   assert None is not None
____________________________________________________________________________ TestArtifactLifecycle.test_completion_protocol_deletion ____________________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:241: in test_completion_protocol_deletion
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
____________________________________________________________________________ TestArtifactLifecycle.test_no_direct_output_compliance _____________________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:287: in test_no_direct_output_compliance
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-designer did not return valid JSON response
E   assert None is not None
_____________________________________________________________________________ TestArtifactLifecycle.test_artifact_path_consistency ______________________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:338: in test_artifact_path_consistency
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
____________________________________________________________________________ TestArtifactLifecycle.test_lifecycle_state_progression _____________________________________________________________________________
tests/integration/workspace_protocol/test_artifact_lifecycle.py:389: in test_lifecycle_state_progression
    assert json_data1 is not None
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-dev-planner] ___________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-dev-designer] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-designer did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-dev-coder] ____________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-coder did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-dev-fixer] ____________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-fixer did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-testing-maker] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-maker did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-testing-fixer] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-fixer did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-quality-ruff] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-ruff did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-quality-mypy] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-mypy did not return valid JSON response
E   assert None is not None
_____________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-clone] ______________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-clone did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-self-learn] ___________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-self-learn did not return valid JSON response
E   assert None is not None
___________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-qa-tester] ____________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-qa-tester did not return valid JSON response
E   assert None is not None
____________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-claudemd] ____________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-claudemd did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-agent-creator] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-creator did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[genie-agent-enhancer] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-enhancer did not return valid JSON response
E   assert None is not None
________________________________________________________________________ TestContextIngestion.test_valid_context_file_processing[claude] ________________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:123: in test_valid_context_file_processing
    assert json_data is not None, (
E   AssertionError: Agent claude did not return valid JSON response
E   assert None is not None
_______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-dev-planner] ________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
_______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-dev-designer] _______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-designer did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-dev-coder] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-coder did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-dev-fixer] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-fixer did not return valid JSON response
E   assert None is not None
______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-testing-maker] _______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-maker did not return valid JSON response
E   assert None is not None
______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-testing-fixer] _______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-fixer did not return valid JSON response
E   assert None is not None
_______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-quality-ruff] _______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-ruff did not return valid JSON response
E   assert None is not None
_______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-quality-mypy] _______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-mypy did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-clone] ___________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-clone did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-self-learn] ________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-self-learn did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-qa-tester] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-qa-tester did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-claudemd] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-claudemd did not return valid JSON response
E   assert None is not None
______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-agent-creator] _______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-creator did not return valid JSON response
E   assert None is not None
______________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[genie-agent-enhancer] ______________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-enhancer did not return valid JSON response
E   assert None is not None
_____________________________________________________________________ TestContextIngestion.test_missing_context_file_error_handling[claude] _____________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:178: in test_missing_context_file_error_handling
    assert json_data is not None, (
E   AssertionError: Agent claude did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-dev-planner] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-planner did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-dev-designer] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-designer did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-dev-coder] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-coder did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-dev-fixer] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-dev-fixer did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-testing-maker] ________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-maker did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-testing-fixer] ________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-testing-fixer did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-quality-ruff] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-ruff did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-quality-mypy] _________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-quality-mypy did not return valid JSON response
E   assert None is not None
____________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-clone] ____________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-clone did not return valid JSON response
E   assert None is not None
_________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-self-learn] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-self-learn did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-qa-tester] __________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-qa-tester did not return valid JSON response
E   assert None is not None
__________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-claudemd] ___________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-claudemd did not return valid JSON response
E   assert None is not None
________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-agent-creator] ________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-creator did not return valid JSON response
E   assert None is not None
_______________________________________________________________ TestContextIngestion.test_multiple_context_file_management[genie-agent-enhancer] ________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent genie-agent-enhancer did not return valid JSON response
E   assert None is not None
______________________________________________________________________ TestContextIngestion.test_multiple_context_file_management[claude] _______________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:246: in test_multiple_context_file_management
    assert json_data is not None, (
E   AssertionError: Agent claude did not return valid JSON response
E   assert None is not None
_________________________________________________________________________ TestContextIngestion.test_context_content_integration_quality _________________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:337: in test_context_content_integration_quality
    assert marker_found, (
E   AssertionError: Agent genie-dev-planner did not demonstrate actual use of context file content
E   assert False
________________________________________________________________________ TestContextIngestion.test_context_file_access_validation_timing ________________________________________________________________________
tests/integration/workspace_protocol/test_context_ingestion.py:384: in test_context_file_access_validation_timing
    assert json_data is not None
E   assert None is not None
___________________________________________________________________________ TestConfigInheritanceManager.test_parameter_sets_complete ___________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:188: in test_parameter_sets_complete
    assert "model" in manager.INHERITABLE_PARAMETERS
E   AssertionError: assert 'model' in {'display': ['markdown', 'show_tool_calls', 'add_datetime_to_instructions', 'add_location_to_instructions', 'add_name_...n_summary_references', 'add_history_to_messages', 'num_history_runs', ...], 'storage': ['type', 'auto_upgrade_schema']}
E    +  where {'display': ['markdown', 'show_tool_calls', 'add_datetime_to_instructions', 'add_location_to_instructions', 'add_name_...n_summary_references', 'add_history_to_messages', 'num_history_runs', ...], 'storage': ['type', 'auto_upgrade_schema']} = <lib.utils.config_inheritance.ConfigInheritanceManager object at 0x743b18d6d550>.INHERITABLE_PARAMETERS
_______________________________________________________________________ TestConfigInheritanceManager.test_extract_team_defaults_complete ________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:199: in test_extract_team_defaults_complete
    assert "model" in defaults
E   AssertionError: assert 'model' in {'display': {'add_datetime_to_instructions': True, 'add_location_to_instructions': False, 'add_name_to_instructions': ...y_references': True, 'enable_agentic_memory': True, ...}, 'storage': {'auto_upgrade_schema': True, 'type': 'postgres'}}
________________________________________________________________________ TestConfigInheritanceManager.test_extract_team_defaults_partial ________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:230: in test_extract_team_defaults_partial
    assert "model" in defaults
E   AssertionError: assert 'model' in {'memory': {'enable_user_memories': True, 'num_history_runs': 15}}
___________________________________________________________________ TestConfigInheritanceManager.test_extract_team_defaults_empty_categories ____________________________________________________________________
tests/lib/utils/test_config_inheritance.py:250: in test_extract_team_defaults_empty_categories
    assert "model" in defaults  # Empty category creates empty dict
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AssertionError: assert 'model' in {'display': {'markdown': True, 'show_tool_calls': False}}
_____________________________________________________________________ TestConfigInheritanceManager.test_apply_inheritance_to_agent_complete _____________________________________________________________________
tests/lib/utils/test_config_inheritance.py:278: in test_apply_inheritance_to_agent_complete
    assert enhanced["model"]["provider"] == "anthropic"  # Inherited
           ^^^^^^^^^^^^^^^^^
E   KeyError: 'model'
___________________________________________________________________ TestConfigInheritanceManager.test_apply_inheritance_to_agent_no_overrides ___________________________________________________________________
tests/lib/utils/test_config_inheritance.py:304: in test_apply_inheritance_to_agent_no_overrides
    assert enhanced["model"]["provider"] == "anthropic"
           ^^^^^^^^^^^^^^^^^
E   KeyError: 'model'
_______________________________________________________________________ TestConfigInheritanceManager.test_apply_inheritance_full_workflow _______________________________________________________________________
tests/lib/utils/test_config_inheritance.py:343: in test_apply_inheritance_full_workflow
    assert agent1["model"]["provider"] == "anthropic"  # Inherited
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'provider'
_______________________________________________________________ TestConfigInheritanceManager.test_generate_inheritance_report_detailed_breakdown ________________________________________________________________
tests/lib/utils/test_config_inheritance.py:583: in test_generate_inheritance_report_detailed_breakdown
    assert "agent1(4)" in report  # 4 inherited parameters
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AssertionError: assert 'agent1(4)' in 'Configuration inheritance: 3 parameters inherited across 3 agents [agent1(2), agent2(1)]'
______________________________________________________________________ TestLoadTeamWithInheritance.test_load_team_with_inheritance_success ______________________________________________________________________
tests/lib/utils/test_config_inheritance.py:954: in test_load_team_with_inheritance_success
    assert agent1["model"]["provider"] == "anthropic"  # Inherited
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'provider'
_______________________________________________________________________ TestEdgeCasesAndPerformance.test_large_configuration_performance ________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:1112: in test_large_configuration_performance
    assert config["model"]["provider"] == "anthropic"  # Inherited
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'provider'
________________________________________________________________________ TestEdgeCasesAndPerformance.test_circular_reference_prevention _________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:1134: in test_circular_reference_prevention
    assert enhanced["model"]["provider"] == "anthropic"
           ^^^^^^^^^^^^^^^^^
E   KeyError: 'model'
________________________________________________________________________ TestEdgeCasesAndPerformance.test_unicode_and_special_characters ________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:1198: in test_unicode_and_special_characters
    assert enhanced_agent["model"]["id"] == "Handle special chars and emojis"
           ^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'model'
____________________________________________________________________________ TestEdgeCasesAndPerformance.test_empty_and_null_values _____________________________________________________________________________
tests/lib/utils/test_config_inheritance.py:1228: in test_empty_and_null_values
    assert model["max_tokens"] == 0  # Zero inherited
           ^^^^^^^^^^^^^^^^^^^
E   KeyError: 'max_tokens'
____________________________________________________________________ TestAGNOConfigMigrator.test_create_migration_plan_with_redundant_params ____________________________________________________________________
tests/lib/utils/test_config_migration.py:229: in test_create_migration_plan_with_redundant_params
    assert "model.provider" in removable
E   AssertionError: assert 'model.provider' in ['memory.enable_user_memories', 'memory.add_memory_references', 'display.markdown']
_____________________________________________________________________ TestConfigurationProcessing.test_process_config_with_custom_handlers ______________________________________________________________________
tests/lib/utils/test_proxy_agents.py:365: in test_process_config_with_custom_handlers
    assert "model" in result
E   AssertionError: assert 'model' in {'description': None, 'id': 'claude-sonnet-4-20250514', 'name': 'Test Agent', 'role': None, ...}
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🔍 TEMPLATE-AGENT MODEL CONFIG for test-agent: {'id': 'claude-sonnet-4-20250514', 'temperature': 0.7}
_____________________________________________________________________________ TestCustomParameterHandlers.test_handle_model_config ______________________________________________________________________________
/usr/lib/python3.12/unittest/mock.py:955: in assert_called_once_with
    raise AssertionError(msg)
E   AssertionError: Expected 'resolve_model' to be called once. Called 0 times.

During handling of the above exception, another exception occurred:
tests/lib/utils/test_proxy_agents.py:423: in test_handle_model_config
    mock_resolve_model.assert_called_once_with(model_id="claude-sonnet-4-20250514", **model_config)
E   AssertionError: Expected 'resolve_model' to be called once. Called 0 times.
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🔍 TEMPLATE-AGENT MODEL CONFIG for test-agent: {'id': 'claude-sonnet-4-20250514', 'temperature': 0.8, 'max_tokens': 3000, 'custom_param': 'value'}
_________________________________________________________________ TestCustomParameterHandlers.test_handle_knowledge_filter_warns_agent_csv_path _________________________________________________________________
tests/lib/utils/test_proxy_agents.py:602: in test_handle_knowledge_filter_warns_agent_csv_path
    assert (
E   AssertionError: assert <Mock name='RowBasedCSVKnowledgeBase()' id='127797165907488'> is None
________________________________________________________________________ TestComprehensiveIntegration.test_comprehensive_agent_creation _________________________________________________________________________
/usr/lib/python3.12/unittest/mock.py:923: in assert_called_once
    raise AssertionError(msg)
E   AssertionError: Expected 'resolve_model' to have been called once. Called 0 times.

During handling of the above exception, another exception occurred:
tests/lib/utils/test_proxy_agents.py:1159: in test_comprehensive_agent_creation
    mock_model.assert_called_once()
E   AssertionError: Expected 'resolve_model' to have been called once. Called 0 times.
--------------------------------------------------------------------------------------------- Captured stdout call ----------------------------------------------------------------------------------------------
🔍 TEMPLATE-AGENT MODEL CONFIG for comprehensive-test-agent: {'id': 'test-model-advanced', 'temperature': 0.9, 'max_tokens': 4000, 'custom_model_param': 'value'}
__________________________________________________________________ TestAgnoTeamProxyConfigurationProcessing.test_process_config_custom_params ___________________________________________________________________
/usr/lib/python3.12/unittest/mock.py:955: in assert_called_once_with
    raise AssertionError(msg)
E   AssertionError: Expected 'mock' to be called once. Called 0 times.
E   Calls: [call.__bool__()].

During handling of the above exception, another exception occurred:
tests/lib/utils/test_proxy_teams.py:361: in test_process_config_custom_params
    mock_model_class.assert_called_once_with(**{"id": "claude-3-sonnet"})
E   AssertionError: Expected 'mock' to be called once. Called 0 times.
E   Calls: [call.__bool__()].
__________________________________________________________________________ TestAgnoTeamProxyParameterHandlers.test_handle_model_config __________________________________________________________________________
/usr/lib/python3.12/unittest/mock.py:955: in assert_called_once_with
    raise AssertionError(msg)
E   AssertionError: Expected 'mock' to be called once. Called 0 times.
E   Calls: [call.__bool__()].

During handling of the above exception, another exception occurred:
tests/lib/utils/test_proxy_teams.py:480: in test_handle_model_config
    mock_model_class.assert_called_once_with(**filtered_config)
E   AssertionError: Expected 'mock' to be called once. Called 0 times.
E   Calls: [call.__bool__()].
_____________________________________________________________________ TestAgnoTeamProxyParameterHandlers.test_handle_model_config_defaults ______________________________________________________________________
/usr/lib/python3.12/unittest/mock.py:955: in assert_called_once_with
    raise AssertionError(msg)
E   AssertionError: Expected 'mock' to be called once. Called 0 times.
E   Calls: [call.__bool__()].

During handling of the above exception, another exception occurred:
tests/lib/utils/test_proxy_teams.py:519: in test_handle_model_config_defaults
    mock_model_class.assert_called_once_with(**model_config)
E   AssertionError: Expected 'mock' to be called once. Called 0 times.
E   Calls: [call.__bool__()].

🧪 CLI Comprehensive Test Suite Summary
==================================================
📊 Test Results:
   ✅ Passed: 2895
   ❌ Failed: 106
   ⏭️  Skipped: 375
   🚨 Errors: 0
   📈 Total: 3376
   🎯 Success Rate: 85.8%

🎯 Coverage Target: >95% for CLI components
🚀 Real Server Tests: Set TEST_REAL_AGENT_SERVER=true to enable
🐘 Real PostgreSQL Tests: Set TEST_REAL_POSTGRES=true to enable

============================================================================================ short test summary info ============================================================================================
SKIPPED [1] tests/cli/commands/test_workspace.py:15: Skipping workspace tests
SKIPPED [29] tests/cli/commands/test_genie.py: Big architectural changes needed - genie commands require major refactoring before test implementation
SKIPPED [1] tests/integration/api/test_serve_comprehensive.py:237: Dummy agent creation is unreachable due to ComponentLoadingError check at line 276-280 in production code
SKIPPED [1] tests/integration/api/test_serve_comprehensive.py:306: Complex mock chain needs refactoring - playground.get_async_router mock not working correctly
SKIPPED [1] tests/integration/api/test_serve_comprehensive.py:413: Complex ThreadPoolExecutor mock not working - implementation detail test needs refactoring
SKIPPED [1] tests/integration/auth/test_credential_service_mcp_sync.py:49: BLOCKED: Source fix needed - TASK-cd4d8f02-118d-4a62-b8ec-05ae6b220376
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:705: _apply_port_mappings method not implemented in docker-compose inheritance model
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:712: _apply_database_mappings method not implemented in docker-compose inheritance model
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:719: _apply_cors_mappings method not implemented in docker-compose inheritance model
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:726: _apply_agent_specific_config method not implemented in docker-compose inheritance model
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:861: validate_agent_environment convenience function not implemented yet
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:867: get_agent_ports convenience function not implemented yet
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:873: get_agent_ports convenience function not implemented yet
SKIPPED [1] tests/integration/cli/core/test_agent_environment_integration.py:886: cleanup_agent_environment convenience function not implemented yet
SKIPPED [25] tests/integration/cli/test_coverage_validation_comprehensive.py: CLI architecture refactored - old commands modules no longer exist
SKIPPED [1] tests/integration/cli/test_coverage_validation_comprehensive.py:353: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [1] tests/integration/cli/test_coverage_validation_comprehensive.py:369: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [1] tests/integration/cli/test_coverage_validation_comprehensive.py:402: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [1] tests/integration/cli/test_coverage_validation_comprehensive.py:427: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [40] tests/integration/cli/test_health_system_comprehensive.py: CLI architecture refactored - health commands consolidated
SKIPPED [4] tests/integration/cli/test_health_system_comprehensive.py:702: CLI architecture refactored - health commands consolidated
SKIPPED [1] tests/integration/cli/test_main_cli_comprehensive.py:96: BLOCKED: Production fix needed - TASK-20f49a9d-13c6-4026-b05e-1887d98a26fb
SKIPPED [27] tests/integration/cli/test_postgres_integration_comprehensive.py: CLI architecture refactored - postgres commands consolidated
SKIPPED [1] tests/integration/cli/test_postgres_integration_comprehensive.py:410: Real PostgreSQL container testing disabled. Set TEST_REAL_POSTGRES_CONTAINERS=true to enable.
SKIPPED [1] tests/integration/cli/test_postgres_integration_comprehensive.py:477: Real PostgreSQL container testing disabled. Set TEST_REAL_POSTGRES_CONTAINERS=true to enable.
SKIPPED [1] tests/integration/cli/test_postgres_integration_comprehensive.py:573: Real PostgreSQL container testing disabled. Set TEST_REAL_POSTGRES_CONTAINERS=true to enable.
SKIPPED [86] tests/integration/cli/test_service_management_comprehensive.py: CLI architecture refactored - service commands consolidated into DockerManager
SKIPPED [43] tests/integration/cli/test_workspace_commands_comprehensive.py: CLI architecture refactored - workspace commands consolidated into WorkspaceManager
SKIPPED [23] tests/integration/e2e/test_genie_integration.py: CLI architecture refactored - genie commands consolidated
SKIPPED [1] tests/integration/e2e/test_langwatch_integration.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/integration/e2e/test_langwatch_integration.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/integration/e2e/test_langwatch_integration.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/integration/e2e/test_uv_run_workflow_e2e.py:327: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [1] tests/integration/e2e/test_uv_run_workflow_e2e.py:344: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [1] tests/integration/e2e/test_uv_run_workflow_e2e.py:371: Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.
SKIPPED [1] tests/integration/e2e/test_uv_run_workflow_e2e.py:433: Real PostgreSQL testing disabled. Set TEST_REAL_POSTGRES=true to enable.
SKIPPED [1] tests/integration/e2e/test_uv_run_workflow_e2e.py:462: Real PostgreSQL testing disabled. Set TEST_REAL_POSTGRES=true to enable.
SKIPPED [1] tests/lib/auth/test_cli.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/auth/test_cli.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/auth/test_cli.py:43: Placeholder test - implement based on boundary conditions
SKIPPED [1] tests/lib/auth/test_cli.py:53: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/auth/test_dependencies.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/auth/test_dependencies.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/auth/test_dependencies.py:47: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/auth/test_init_service.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/auth/test_init_service.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/auth/test_init_service.py:47: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/config/test_provider_registry.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/config/test_provider_registry.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/config/test_provider_registry.py:47: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/config/test_schemas.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/config/test_schemas.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/config/test_schemas.py:47: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/config/test_server_config.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/config/test_server_config.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/config/test_server_config.py:47: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/config/test_yaml_parser.py:27: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/config/test_yaml_parser.py:37: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/config/test_yaml_parser.py:47: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/logging/test_config.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/logging/test_config.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/logging/test_config.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/logging/test_progress.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/logging/test_progress.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/logging/test_progress.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/logging/test_session_logger.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/logging/test_session_logger.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/logging/test_session_logger.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/memory/test_memory_factory.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/memory/test_memory_factory.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/memory/test_memory_factory.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/metrics/test_agno_metrics_bridge.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/metrics/test_agno_metrics_bridge.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/metrics/test_agno_metrics_bridge.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/metrics/test_async_metrics_service.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/metrics/test_async_metrics_service.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/metrics/test_async_metrics_service.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/metrics/test_config.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/metrics/test_config.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/metrics/test_config.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/middleware/test_error_handler.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/middleware/test_error_handler.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/middleware/test_error_handler.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/models/test_agent_metrics.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/models/test_agent_metrics.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/models/test_agent_metrics.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/models/test_base.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/models/test_base.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/models/test_base.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/models/test_component_versions.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/models/test_component_versions.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/models/test_component_versions.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/models/test_version_history.py:21: Placeholder test - implement based on actual module functionality
SKIPPED [1] tests/lib/models/test_version_history.py:31: Placeholder test - implement based on error conditions
SKIPPED [1] tests/lib/models/test_version_history.py:41: Placeholder test - implement based on integration needs
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:81: test_load_yaml_file_not_exists calls get_yaml which hangs
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:89: test_load_yaml_success causes hanging - likely infinite loop in _manage_cache_size
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:126: test_load_yaml_cache_hit causes hanging - same get_yaml issue
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:148: test_load_yaml_cache_invalidation calls get_yaml which hangs
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:184: test_load_yaml_invalid_yaml calls get_yaml which hangs
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:202: test_load_yaml_file_permission_error calls get_yaml which hangs
SKIPPED [1] tests/lib/utils/test_yaml_cache.py:342: Thread safety test causes hanging - needs redesign with proper locking
SKIPPED [4] tests/lib/utils/test_yaml_cache.py: All integration tests call get_yaml which hangs
FAILED tests/integration/cli/test_main_cli_comprehensive.py::TestCLICommandRouting::test_agent_start_command - AssertionError: Expected 'serve' to be called once. Called 0 times.
FAILED tests/integration/cli/test_main_cli_comprehensive.py::TestCLIErrorHandling::test_all_command_failures_return_exit_code_1 - AssertionError: Command ['--agent-start'] should return exit code 1 on failure
FAILED tests/integration/cli/test_makefile_uninstall.py::TestMakefileUninstallComprehensive::test_uninstall_containers_only_comprehensive_stops_all_services - AssertionError: assert 'hive-agents-agent hive-agent-postgres' in '# ===========================================\n# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile\n# =======...\\\n    else \\\...
FAILED tests/integration/cli/test_makefile_uninstall.py::TestMakefileUninstallComprehensive::test_uninstall_clean_comprehensive_removes_agent_infrastructure - AssertionError: assert 'docker image rm automagik-hive-app' in '# ===========================================\n# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile\n# =======...\\\n    else \\\n  ...
FAILED tests/integration/cli/test_makefile_uninstall.py::TestMakefileUninstallComprehensive::test_uninstall_purge_comprehensive_removes_all_data - AssertionError: assert 'This will remove ALL containers, images, volumes, data, and environment files' in '# ===========================================\n# 🐝 Automagik Hive Multi-Agent System - Simplifie...
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestAgentCommandsIntegration::test_agent_service_environment_integration - AttributeError: 'AgentEnvironment' object has no attribute 'generate_env_agent'
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestFunctionalParityMakeVsUvx::test_agent_port_configuration_parity - AttributeError: 'AgentEnvironment' object has no attribute 'generate_env_agent'
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestFunctionalParityMakeVsUvx::test_environment_file_generation_parity - AttributeError: 'AgentEnvironment' object has no attribute 'generate_env_agent'
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestCrossPlatformCompatibility::test_linux_compatibility_patterns - assert False is True
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestCrossPlatformCompatibility::test_macos_compatibility_patterns - assert False is True
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestCrossPlatformCompatibility::test_environment_variable_handling - assert False is True
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestPerformanceAndScalability::test_concurrent_command_performance - assert False
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestPerformanceAndScalability::test_large_workspace_handling - assert False is True
FAILED tests/integration/e2e/test_agent_commands_integration.py::TestPerformanceAndScalability::test_command_response_time - AttributeError: 'AgentCommands' object has no attribute 'serve'
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-dev-planner] - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-dev-designer] - AssertionError: Agent genie-dev-designer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-dev-coder] - AssertionError: Agent genie-dev-coder did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-dev-fixer] - AssertionError: Agent genie-dev-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-testing-maker] - AssertionError: Agent genie-testing-maker did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-testing-fixer] - AssertionError: Agent genie-testing-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-quality-ruff] - AssertionError: Agent genie-quality-ruff did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-quality-mypy] - AssertionError: Agent genie-quality-mypy did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-clone] - AssertionError: Agent genie-clone did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-self-learn] - AssertionError: Agent genie-self-learn did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-qa-tester] - AssertionError: Agent genie-qa-tester did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-claudemd] - AssertionError: Agent genie-claudemd did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-agent-creator] - AssertionError: Agent genie-agent-creator did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[genie-agent-enhancer] - AssertionError: Agent genie-agent-enhancer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_ideas_phase_artifact_creation[claude] - AssertionError: Agent claude did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_wishes_phase_migration[genie-dev-planner] - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_wishes_phase_migration[genie-dev-designer] - AssertionError: Agent genie-dev-designer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_wishes_phase_migration[genie-dev-coder] - AssertionError: Agent genie-dev-coder did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_wishes_phase_migration[genie-testing-maker] - AssertionError: Agent genie-testing-maker did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_wishes_phase_migration[genie-clone] - AssertionError: Agent genie-clone did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_completion_protocol_deletion - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_no_direct_output_compliance - AssertionError: Agent genie-dev-designer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_artifact_path_consistency - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_artifact_lifecycle.py::TestArtifactLifecycle::test_lifecycle_state_progression - assert None is not None
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-dev-planner] - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-dev-designer] - AssertionError: Agent genie-dev-designer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-dev-coder] - AssertionError: Agent genie-dev-coder did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-dev-fixer] - AssertionError: Agent genie-dev-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-testing-maker] - AssertionError: Agent genie-testing-maker did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-testing-fixer] - AssertionError: Agent genie-testing-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-quality-ruff] - AssertionError: Agent genie-quality-ruff did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-quality-mypy] - AssertionError: Agent genie-quality-mypy did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-clone] - AssertionError: Agent genie-clone did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-self-learn] - AssertionError: Agent genie-self-learn did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-qa-tester] - AssertionError: Agent genie-qa-tester did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-claudemd] - AssertionError: Agent genie-claudemd did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-agent-creator] - AssertionError: Agent genie-agent-creator did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[genie-agent-enhancer] - AssertionError: Agent genie-agent-enhancer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_valid_context_file_processing[claude] - AssertionError: Agent claude did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-dev-planner] - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-dev-designer] - AssertionError: Agent genie-dev-designer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-dev-coder] - AssertionError: Agent genie-dev-coder did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-dev-fixer] - AssertionError: Agent genie-dev-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-testing-maker] - AssertionError: Agent genie-testing-maker did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-testing-fixer] - AssertionError: Agent genie-testing-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-quality-ruff] - AssertionError: Agent genie-quality-ruff did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-quality-mypy] - AssertionError: Agent genie-quality-mypy did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-clone] - AssertionError: Agent genie-clone did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-self-learn] - AssertionError: Agent genie-self-learn did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-qa-tester] - AssertionError: Agent genie-qa-tester did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-claudemd] - AssertionError: Agent genie-claudemd did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-agent-creator] - AssertionError: Agent genie-agent-creator did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[genie-agent-enhancer] - AssertionError: Agent genie-agent-enhancer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_missing_context_file_error_handling[claude] - AssertionError: Agent claude did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-dev-planner] - AssertionError: Agent genie-dev-planner did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-dev-designer] - AssertionError: Agent genie-dev-designer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-dev-coder] - AssertionError: Agent genie-dev-coder did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-dev-fixer] - AssertionError: Agent genie-dev-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-testing-maker] - AssertionError: Agent genie-testing-maker did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-testing-fixer] - AssertionError: Agent genie-testing-fixer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-quality-ruff] - AssertionError: Agent genie-quality-ruff did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-quality-mypy] - AssertionError: Agent genie-quality-mypy did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-clone] - AssertionError: Agent genie-clone did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-self-learn] - AssertionError: Agent genie-self-learn did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-qa-tester] - AssertionError: Agent genie-qa-tester did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-claudemd] - AssertionError: Agent genie-claudemd did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-agent-creator] - AssertionError: Agent genie-agent-creator did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[genie-agent-enhancer] - AssertionError: Agent genie-agent-enhancer did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_multiple_context_file_management[claude] - AssertionError: Agent claude did not return valid JSON response
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_context_content_integration_quality - AssertionError: Agent genie-dev-planner did not demonstrate actual use of context file content
FAILED tests/integration/workspace_protocol/test_context_ingestion.py::TestContextIngestion::test_context_file_access_validation_timing - assert None is not None
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_parameter_sets_complete - AssertionError: assert 'model' in {'display': ['markdown', 'show_tool_calls', 'add_datetime_to_instructions', 'add_location_to_instructions', 'add_name_...n_summary_references', 'add_history_to_messages',...
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_extract_team_defaults_complete - AssertionError: assert 'model' in {'display': {'add_datetime_to_instructions': True, 'add_location_to_instructions': False, 'add_name_to_instructions': ...y_references': True, 'enable_agentic_memory': Tru...
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_extract_team_defaults_partial - AssertionError: assert 'model' in {'memory': {'enable_user_memories': True, 'num_history_runs': 15}}
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_extract_team_defaults_empty_categories - AssertionError: assert 'model' in {'display': {'markdown': True, 'show_tool_calls': False}}
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_apply_inheritance_to_agent_complete - KeyError: 'model'
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_apply_inheritance_to_agent_no_overrides - KeyError: 'model'
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_apply_inheritance_full_workflow - KeyError: 'provider'
FAILED tests/lib/utils/test_config_inheritance.py::TestConfigInheritanceManager::test_generate_inheritance_report_detailed_breakdown - AssertionError: assert 'agent1(4)' in 'Configuration inheritance: 3 parameters inherited across 3 agents [agent1(2), agent2(1)]'
FAILED tests/lib/utils/test_config_inheritance.py::TestLoadTeamWithInheritance::test_load_team_with_inheritance_success - KeyError: 'provider'
FAILED tests/lib/utils/test_config_inheritance.py::TestEdgeCasesAndPerformance::test_large_configuration_performance - KeyError: 'provider'
FAILED tests/lib/utils/test_config_inheritance.py::TestEdgeCasesAndPerformance::test_circular_reference_prevention - KeyError: 'model'
FAILED tests/lib/utils/test_config_inheritance.py::TestEdgeCasesAndPerformance::test_unicode_and_special_characters - KeyError: 'model'
FAILED tests/lib/utils/test_config_inheritance.py::TestEdgeCasesAndPerformance::test_empty_and_null_values - KeyError: 'max_tokens'
FAILED tests/lib/utils/test_config_migration.py::TestAGNOConfigMigrator::test_create_migration_plan_with_redundant_params - AssertionError: assert 'model.provider' in ['memory.enable_user_memories', 'memory.add_memory_references', 'display.markdown']
FAILED tests/lib/utils/test_proxy_agents.py::TestConfigurationProcessing::test_process_config_with_custom_handlers - AssertionError: assert 'model' in {'description': None, 'id': 'claude-sonnet-4-20250514', 'name': 'Test Agent', 'role': None, ...}
FAILED tests/lib/utils/test_proxy_agents.py::TestCustomParameterHandlers::test_handle_model_config - AssertionError: Expected 'resolve_model' to be called once. Called 0 times.
FAILED tests/lib/utils/test_proxy_agents.py::TestCustomParameterHandlers::test_handle_knowledge_filter_warns_agent_csv_path - AssertionError: assert <Mock name='RowBasedCSVKnowledgeBase()' id='127797165907488'> is None
FAILED tests/lib/utils/test_proxy_agents.py::TestComprehensiveIntegration::test_comprehensive_agent_creation - AssertionError: Expected 'resolve_model' to have been called once. Called 0 times.
FAILED tests/lib/utils/test_proxy_teams.py::TestAgnoTeamProxyConfigurationProcessing::test_process_config_custom_params - AssertionError: Expected 'mock' to be called once. Called 0 times.
FAILED tests/lib/utils/test_proxy_teams.py::TestAgnoTeamProxyParameterHandlers::test_handle_model_config - AssertionError: Expected 'mock' to be called once. Called 0 times.
FAILED tests/lib/utils/test_proxy_teams.py::TestAgnoTeamProxyParameterHandlers::test_handle_model_config_defaults - AssertionError: Expected 'mock' to be called once. Called 0 times.
==================================================================== 106 failed, 2895 passed, 375 skipped, 22 warnings in 148.83s (0:02:28) ==============================
