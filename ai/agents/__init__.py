"""AI Agents Package"""

import importlib

# Import agent submodules using importlib for hyphenated names
genie_debug = importlib.import_module('.genie-debug', __name__)
genie_dev = importlib.import_module('.genie-dev', __name__)
genie_quality = importlib.import_module('.genie-quality', __name__)
genie_testing = importlib.import_module('.genie-testing', __name__)
template_agent = importlib.import_module('.template-agent', __name__)
tools = importlib.import_module('.tools', __name__)

# Make agent functions available at package level using importlib
genie_debug_module = importlib.import_module('.genie-debug', __name__)
genie_dev_module = importlib.import_module('.genie-dev', __name__)
genie_quality_module = importlib.import_module('.genie-quality', __name__)
genie_testing_module = importlib.import_module('.genie-testing', __name__)
template_agent_module = importlib.import_module('.template-agent', __name__)

# Extract agent functions
get_genie_debug_agent = genie_debug_module.get_genie_debug_agent
get_genie_dev_agent = genie_dev_module.get_genie_dev_agent  
get_genie_quality_agent = genie_quality_module.get_genie_quality_agent
get_genie_testing = genie_testing_module.get_genie_testing
get_template_agent = template_agent_module.get_template_agent

__all__ = [
    # Submodules
    "genie_debug",
    "genie_dev", 
    "genie_quality",
    "genie_testing",
    "template_agent",
    "tools",
    # Agent functions
    "get_genie_debug_agent",
    "get_genie_dev_agent",
    "get_genie_quality_agent",
    "get_genie_testing", 
    "get_template_agent",
]
