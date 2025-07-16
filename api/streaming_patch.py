"""
Patch for Agno's default streaming behavior.
This module monkey-patches the Agno framework to default to stream=True.
"""

import os
from typing import List, Optional
from fastapi import Form


def patch_agno_streaming_default():
    """
    Monkey patch the Agno framework to change the default streaming behavior.
    
    This changes the default from stream=False to stream=True based on the
    DEFAULT_STREAM_MODE environment variable.
    """
    
    try:
        # Get the default streaming mode from environment
        default_stream_mode = os.getenv("DEFAULT_STREAM_MODE", "true").lower() == "true"
        
        if not default_stream_mode:
            print("🔄 DEFAULT_STREAM_MODE=false, keeping Agno default behavior")
            return
            
        print(f"🔄 Patching Agno streaming default to: {default_stream_mode}")
        
        # Import the Agno router module
        from agno.app.fastapi import async_router
        
        # Store the original get_async_router function
        original_get_async_router = async_router.get_async_router
        
        # Create a patched version
        def patched_get_async_router(
            agents: Optional[List] = None, 
            teams: Optional[List] = None, 
            workflows: Optional[List] = None
        ):
            # Get the original router
            router = original_get_async_router(agents=agents, teams=teams, workflows=workflows)
            
            # Find the /runs endpoint and patch it
            for route in router.routes:
                if hasattr(route, 'path') and route.path == "/runs" and hasattr(route, 'endpoint'):
                    # Get the original endpoint
                    original_endpoint = route.endpoint
                    
                    # Patch the endpoint's parameters by modifying the function signature
                    import inspect
                    from fastapi import Query, File
                    
                    # Get the original signature
                    sig = inspect.signature(original_endpoint)
                    
                    # Create new parameters with modified stream default
                    new_params = []
                    for param_name, param in sig.parameters.items():
                        if param_name == "stream":
                            # Change the default value for stream parameter
                            new_param = param.replace(default=Form(default_stream_mode))
                            new_params.append(new_param)
                        else:
                            new_params.append(param)
                    
                    # Create new signature
                    new_sig = sig.replace(parameters=new_params)
                    
                    # Apply the new signature to the original endpoint
                    original_endpoint.__signature__ = new_sig
                    
                    print(f"✅ Patched /runs endpoint with stream default: {default_stream_mode}")
                    break
            
            return router
        
        # Replace the original function
        async_router.get_async_router = patched_get_async_router
        
        print("✅ Agno streaming patch applied successfully")
        
    except Exception as e:
        print(f"⚠️ Failed to patch Agno streaming default: {e}")
        print("🔄 Continuing with original Agno behavior")


# Apply the patch when this module is imported
if __name__ != "__main__":
    patch_agno_streaming_default()