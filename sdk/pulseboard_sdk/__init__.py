"""
PulseBoard SDK
--------------
A lightweight Python middleware for FastAPI (and any ASGI/WSGI app)
that automatically tracks every API request and sends it to PulseBoard.

Usage:
    from pulseboard_sdk import PulseBoardMiddleware

    app = FastAPI()
    app.add_middleware(PulseBoardMiddleware, api_key="your-project-api-key")
"""

from .tracker import PulseBoardMiddleware, PulseBoardClient

__all__ = ["PulseBoardMiddleware", "PulseBoardClient"]
__version__ = "1.0.0"
