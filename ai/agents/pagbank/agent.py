from lib.utils.version_factory import create_agent


def get_pagbank_agent(**kwargs):
    """PagBank agent factory - add custom logic here if needed"""
    
    # Custom logic can go here:
    # if kwargs.get("user_context", {}).get("subscription") == "pro":
    #     kwargs["model_override"] = "claude-opus-3-20240229"
    
    return create_agent("pagbank", **kwargs)