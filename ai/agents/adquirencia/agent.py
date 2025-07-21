from lib.utils.version_factory import create_agent


async def get_adquirencia_agent(**kwargs):
    """Adquirencia agent factory - add custom logic here if needed"""
    
    # Custom logic can go here:
    # if kwargs.get("user_context", {}).get("subscription") == "pro":
    #     kwargs["model_override"] = "claude-opus-3-20240229"
    
    return await create_agent("adquirencia", **kwargs)