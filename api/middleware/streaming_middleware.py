"""
Streaming middleware to override Agno's default stream=False behavior.
This middleware intercepts playground requests and sets stream=true as default.
"""

import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from urllib.parse import parse_qs


class StreamingDefaultMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set default streaming behavior for playground endpoints.
    
    This middleware intercepts requests to /playground/.../runs endpoints
    and ensures stream=true is set as default if not explicitly provided.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.default_stream_mode = os.getenv("DEFAULT_STREAM_MODE", "true").lower() == "true"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is a playground runs request
        if (request.method == "POST" and 
            request.url.path.startswith("/playground/") and 
            request.url.path.endswith("/runs")):
            
            # Check if request has multipart form data
            if request.headers.get("content-type", "").startswith("multipart/form-data"):
                # Read the body and check if stream parameter is present
                try:
                    form_data = await request.form()
                    
                    # If stream parameter is not provided, we need to modify the request
                    if "stream" not in form_data and self.default_stream_mode:
                        # Create a new request with stream=true added
                        # This is complex with multipart data, so we'll use a simpler approach
                        # by adding the stream parameter to the query string
                        
                        # Convert boolean to string for form data
                        stream_value = "true" if self.default_stream_mode else "false"
                        
                        # We can't easily modify multipart form data, so we'll use a different approach
                        # by setting a custom header that our custom router can read
                        request.headers.__dict__["_list"].append(
                            (b"x-default-stream", stream_value.encode())
                        )
                        
                        print(f"🔄 Added default streaming: {stream_value}")
                        
                except Exception as e:
                    print(f"⚠️ Error processing streaming middleware: {e}")
                    pass
        
        # Continue with the request
        response = await call_next(request)
        return response