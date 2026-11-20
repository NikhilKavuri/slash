import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.main import app as fastapi_app

# Vercel ASGI path resolver middleware so rewrites preserve the requested URL path
class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            # Vercel forwards the real URL in x-forwarded-uri or x-matched-path
            uri = headers.get(b"x-forwarded-uri") or headers.get(b"x-matched-path")
            if uri:
                clean_path = uri.decode("utf-8").split("?")[0]
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")
        await self.app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
